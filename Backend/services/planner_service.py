"""
Planner Service

Business logic for planner tasks, today's progress, deterministic plan
generation and replanning, study sessions, and revision items.

The generator is a deterministic local planner: it never calls an AI or
external provider. Plans are derived from the student's syllabus profile,
topic estimates, prerequisites, and fixed (locked/existing) commitments.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
import math
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

from core.access import (
    assert_owner_access,
    assert_parent_read_only,
    resolve_student_scope,
)
from core.errors import (
    InvalidStateTransition,
    NotFound,
    PermissionDenied,
    ResourceConflict,
    SyllabusContextInvalid,
    ValidationFailed,
)
from core.security import Principal
from core.time import today as local_today
from core.time import utcnow
from models.common import SyllabusContext
from models.planner import (
    GenerationJob,
    PlannerTask,
    RevisionItem,
    RevisionStatus,
    SessionStatus,
    StudySession,
    TaskSource,
    TaskStatus,
    TaskType,
)
from models.syllabus import Chapter, SyllabusProfile, Topic
from repositories.base import Repository
from services import syllabus_core_service
from services.audit_service import record_audit

logger = logging.getLogger(__name__)

DAY_START_MINUTE = 8 * 60  # generated plans start at 08:00 local
BLOCKING_STATUSES = (TaskStatus.pending, TaskStatus.in_progress, TaskStatus.completed)

MUTABLE_TASK_FIELDS = (
    "title",
    "task_type",
    "scheduled_date",
    "start_minute",
    "duration_minutes",
    "status",
    "syllabus_id",
    "subject_id",
    "chapter_id",
    "topic_id",
)

CONTEXT_FIELDS = ("syllabus_id", "subject_id", "chapter_id", "topic_id")

STUDENT_SETTABLE_STATUSES = (TaskStatus.pending, TaskStatus.in_progress, TaskStatus.cancelled)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _active_profile(repo: Repository, student_id: str) -> Optional[SyllabusProfile]:
    return repo.first(SyllabusProfile, student_id=student_id)


def _get_task(repo: Repository, task_id: str) -> PlannerTask:
    task = repo.get(PlannerTask, task_id)
    if task is None:
        raise NotFound("Task not found.")
    return task


def _assert_record_access(repo: Repository, principal: Principal, student_id: str) -> None:
    """Owner/admin directly; teacher/parent through scope on the record's student."""
    resolve_student_scope(repo, principal, student_id)


def _next_free_slot(cursor: int, length: int, intervals: Sequence[Tuple[int, int]]) -> int:
    """
    Return the earliest start >= cursor where [start, start+length) does not
    overlap any occupied (start, end) interval. Intervals may be unsorted.
    """
    moved = True
    while moved:
        moved = False
        for start, end in intervals:
            if start < cursor + length and cursor < end:
                cursor = max(cursor, end)
                moved = True
    return cursor


def _append_history(
    task: PlannerTask,
    to_date: date,
    to_start: int,
    reason: Optional[str],
    moved_by: str,
) -> None:
    task.reschedule_history.append(
        {
            "from_date": task.scheduled_date.isoformat(),
            "from_start": task.start_minute,
            "to_date": to_date.isoformat(),
            "to_start": to_start,
            "reason": reason,
            "moved_by": moved_by,
            "at": utcnow().isoformat(),
        }
    )


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

def get_today(
    repo: Repository,
    principal: Principal,
    student_id: Optional[str] = None,
) -> Dict:
    """Tasks and progress for the student's current date."""
    effective = resolve_student_scope(repo, principal, student_id)
    current = local_today()
    tasks = repo.find(PlannerTask, student_id=effective, scheduled_date=current)
    tasks.sort(key=lambda t: (t.start_minute, t.title))

    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.completed)
    minutes_planned = sum(t.duration_minutes for t in tasks)
    minutes_completed = sum(
        (t.actual_minutes if t.actual_minutes is not None else t.duration_minutes)
        for t in tasks
        if t.status == TaskStatus.completed
    )
    percent = round(100 * completed / total, 1) if total else 0.0
    return {
        "date": current,
        "progress": {
            "total": total,
            "completed": completed,
            "percent": percent,
            "minutes_planned": minutes_planned,
            "minutes_completed": minutes_completed,
        },
        "tasks": tasks,
    }


def list_tasks(
    repo: Repository,
    principal: Principal,
    student_id: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    status: Optional[str] = None,
    subject_id: Optional[str] = None,
) -> List[PlannerTask]:
    effective = resolve_student_scope(repo, principal, student_id)
    tasks = repo.find(PlannerTask, student_id=effective)

    if from_date is not None:
        tasks = [t for t in tasks if t.scheduled_date >= from_date]
    if to_date is not None:
        tasks = [t for t in tasks if t.scheduled_date <= to_date]
    if status is not None:
        try:
            status_enum = TaskStatus(status)
        except ValueError:
            raise ValidationFailed(details={"field": "status", "value": status})
        tasks = [t for t in tasks if t.status == status_enum]
    if subject_id is not None:
        tasks = [t for t in tasks if t.subject_id == subject_id]

    tasks.sort(key=lambda t: (t.scheduled_date, t.start_minute, t.title))
    return tasks


def create_task(
    repo: Repository,
    principal: Principal,
    data: Dict,
    student_id: Optional[str] = None,
) -> PlannerTask:
    assert_parent_read_only(principal)
    effective = resolve_student_scope(repo, principal, student_id or data.get("student_id"))

    title = (data.get("title") or "").strip()
    if not title:
        raise ValidationFailed(details={"field": "title"})

    context = SyllabusContext(
        syllabus_id=data.get("syllabus_id"),
        subject_id=data.get("subject_id"),
        chapter_id=data.get("chapter_id"),
        topic_id=data.get("topic_id"),
    )
    if not context.is_empty():
        profile = _active_profile(repo, effective)
        if profile is None:
            raise SyllabusContextInvalid(
                message="The student has no active syllabus profile."
            )
        syllabus_core_service.validate_syllabus_context(repo, context, profile)

    privileged = principal.role in ("teacher", "admin")
    task = PlannerTask.new(
        "task",
        student_id=effective,
        title=title,
        task_type=data.get("task_type") or TaskType.practice,
        status=TaskStatus.pending,
        syllabus_id=context.syllabus_id,
        subject_id=context.subject_id,
        chapter_id=context.chapter_id,
        topic_id=context.topic_id,
        scheduled_date=data["scheduled_date"],
        start_minute=data.get("start_minute", 0),
        duration_minutes=data["duration_minutes"],
        locked=bool(data.get("locked")) and privileged,
        locked_by=(principal.user_id if data.get("locked") and privileged else None),
        teacher_fields=(list(data.get("teacher_fields") or []) if privileged else []),
        source=TaskSource.teacher if privileged else TaskSource.manual,
        created_by=principal.user_id,
    )
    repo.put(task)
    record_audit(
        repo,
        principal.user_id,
        "task.create",
        "planner_task",
        task.id,
        details={"student_id": effective, "title": task.title},
    )
    return task


def get_task(repo: Repository, principal: Principal, task_id: str) -> PlannerTask:
    task = _get_task(repo, task_id)
    _assert_record_access(repo, principal, task.student_id)
    return task


def update_task(
    repo: Repository,
    principal: Principal,
    task_id: str,
    data: Dict,
) -> PlannerTask:
    task = _get_task(repo, task_id)
    _assert_record_access(repo, principal, task.student_id)
    assert_parent_read_only(principal)

    expected_version = data.get("version")
    if expected_version is None:
        raise ValidationFailed(details={"field": "version"})
    if expected_version != task.version:
        raise ResourceConflict(
            details={
                "expected_version": expected_version,
                "current_version": task.version,
            },
            message="The task was modified by another request.",
        )

    changes = {
        field: data[field]
        for field in MUTABLE_TASK_FIELDS
        if data.get(field) is not None and getattr(task, field) != data[field]
    }

    if principal.role == "student":
        blocked = [f for f in changes if f in set(task.teacher_fields)]
        if task.locked:
            blocked = list(changes.keys())
        if blocked:
            raise PermissionDenied(
                details={"locked_fields": sorted(set(task.teacher_fields))},
                message="This task is locked by your teacher; locked fields cannot be modified.",
            )

    new_status = changes.get("status")
    if new_status is not None and new_status not in STUDENT_SETTABLE_STATUSES:
        raise ValidationFailed(
            details={"field": "status", "value": str(new_status)},
            message="Status can only be changed to pending, in_progress, or cancelled here.",
        )

    if any(field in changes for field in CONTEXT_FIELDS):
        merged = SyllabusContext(
            syllabus_id=changes.get("syllabus_id", task.syllabus_id),
            subject_id=changes.get("subject_id", task.subject_id),
            chapter_id=changes.get("chapter_id", task.chapter_id),
            topic_id=changes.get("topic_id", task.topic_id),
        )
        profile = _active_profile(repo, task.student_id)
        syllabus_core_service.validate_syllabus_context(repo, merged, profile)

    for field, value in changes.items():
        setattr(task, field, value)
    task.version += 1
    task.touch()
    repo.put(task)
    record_audit(
        repo,
        principal.user_id,
        "task.update",
        "planner_task",
        task.id,
        details={
            "student_id": task.student_id,
            "fields": sorted(changes.keys()),
            "version": task.version,
        },
    )
    return task


def complete_task(
    repo: Repository,
    principal: Principal,
    task_id: str,
    actual_minutes: Optional[int] = None,
) -> PlannerTask:
    task = _get_task(repo, task_id)
    assert_owner_access(principal, task.student_id)

    if task.status == TaskStatus.completed:
        # Idempotent retry without a key: return current state, no double count.
        return task

    task.status = TaskStatus.completed
    task.completed_at = utcnow()
    task.actual_minutes = (
        actual_minutes if actual_minutes is not None else task.duration_minutes
    )
    task.version += 1
    task.touch()
    repo.put(task)
    record_audit(
        repo,
        principal.user_id,
        "task.complete",
        "planner_task",
        task.id,
        details={"student_id": task.student_id, "actual_minutes": task.actual_minutes},
    )
    return task


def reschedule_task(
    repo: Repository,
    principal: Principal,
    task_id: str,
    data: Dict,
) -> PlannerTask:
    task = _get_task(repo, task_id)
    _assert_record_access(repo, principal, task.student_id)
    assert_parent_read_only(principal)

    if task.status in (TaskStatus.completed, TaskStatus.cancelled, TaskStatus.skipped):
        raise InvalidStateTransition(
            message=f"Tasks with status '{task.status.value}' cannot be rescheduled."
        )
    if task.locked and principal.role == "student":
        raise PermissionDenied("Locked tasks cannot be rescheduled by students.")

    new_date = data["scheduled_date"]
    new_start = data.get("start_minute")
    if new_start is None:
        new_start = task.start_minute

    _append_history(task, new_date, new_start, data.get("reason"), principal.user_id)
    task.scheduled_date = new_date
    task.start_minute = new_start
    task.version += 1
    task.touch()
    repo.put(task)
    record_audit(
        repo,
        principal.user_id,
        "task.reschedule",
        "planner_task",
        task.id,
        details={"student_id": task.student_id, "to_date": new_date.isoformat()},
    )
    return task


# ---------------------------------------------------------------------------
# Deterministic generation / replanning
# ---------------------------------------------------------------------------

def _profile_topics(repo: Repository, profile: SyllabusProfile) -> List[Topic]:
    """Topics from the profile's subjects in deterministic syllabus order."""
    ordered: List[Topic] = []
    for subject_id in profile.subjects:
        chapters = repo.find(Chapter, subject_id=subject_id)
        chapters.sort(key=lambda c: (c.order_index, c.name))
        for chapter in chapters:
            topics = repo.find(Topic, chapter_id=chapter.id)
            topics.sort(key=lambda t: t.name)
            ordered.extend(topics)
    return ordered


def _topic_states(repo: Repository, student_id: str) -> Tuple[set, set]:
    """(covered_topic_ids, scheduled_topic_ids) from the student's tasks."""
    covered, scheduled = set(), set()
    for task in repo.find(PlannerTask, student_id=student_id):
        if not task.topic_id:
            continue
        if task.status == TaskStatus.completed:
            covered.add(task.topic_id)
        elif task.status in (TaskStatus.pending, TaskStatus.in_progress):
            scheduled.add(task.topic_id)
    return covered, scheduled


def _order_candidates(candidates: List[Topic], covered: set, scheduled: set) -> Tuple[List[Topic], List[str]]:
    """
    Topologically order candidates so prerequisites come first. Topics whose
    prerequisites can never be satisfied in this run are deferred with a
    warning each.
    """
    ordered: List[Topic] = []
    planned: set = set()
    pool = list(candidates)
    warnings: List[str] = []

    while pool:
        progressed = False
        for topic in list(pool):
            if all(
                p in covered or p in scheduled or p in planned
                for p in topic.prerequisites
            ):
                ordered.append(topic)
                planned.add(topic.id)
                pool.remove(topic)
                progressed = True
        if not progressed:
            for topic in pool:
                missing = [
                    p for p in topic.prerequisites
                    if not (p in covered or p in scheduled or p in planned)
                ]
                missing_names = ", ".join(f"'{m}'" for m in missing)
                warnings.append(
                    f"Topic '{topic.name}' deferred: prerequisite {missing_names} is not yet covered."
                )
            break
    return ordered, warnings


def _day_intervals(tasks: Sequence[PlannerTask], day: date) -> List[Tuple[int, int]]:
    return sorted(
        (t.start_minute, t.start_minute + t.duration_minutes)
        for t in tasks
        if t.scheduled_date == day and t.status in BLOCKING_STATUSES
    )


def generate(repo: Repository, principal: Principal, days: int) -> GenerationJob:
    effective_student = resolve_student_scope(repo, principal, None)
    assert_parent_read_only(principal)
    profile = _active_profile(repo, effective_student)
    if profile is None:
        raise NotFound("No syllabus profile found for this student.")

    start = local_today()
    dates = [start + timedelta(days=i) for i in range(days)]
    capacity = int(profile.availability.get("minutes_per_day", 180))
    buffer_ratio = float(profile.preferences.get("buffer_ratio", 0.1) or 0.0)
    buffer_minutes = int(round(capacity * buffer_ratio)) if buffer_ratio > 0 else 0

    existing = repo.find(PlannerTask, student_id=effective_student)
    blocking = [
        t for t in existing
        if t.status in BLOCKING_STATUSES and start <= t.scheduled_date <= dates[-1]
    ]

    covered, scheduled = _topic_states(repo, effective_student)
    candidates = [
        topic for topic in _profile_topics(repo, profile)
        if topic.id not in covered and topic.id not in scheduled
    ]
    ordered, warnings = _order_candidates(candidates, covered, scheduled)

    job = GenerationJob.new(
        "job", student_id=effective_student, kind="generate", status="running"
    )
    repo.put(job)

    created: List[PlannerTask] = []
    planned_minutes = 0
    idx = 0
    for day in dates:
        intervals = _day_intervals(blocking, day)
        day_end = DAY_START_MINUTE + capacity
        remaining = max(capacity - buffer_minutes, 0)
        cursor = DAY_START_MINUTE

        while idx < len(ordered) and remaining > 0:
            topic = ordered[idx]
            block = min(topic.estimated_minutes, remaining)
            if block <= 0:
                break
            slot = _next_free_slot(cursor, block, intervals)
            if slot + block > day_end:
                break
            task = PlannerTask.new(
                "task",
                student_id=effective_student,
                title=f"Study: {topic.name}",
                task_type=TaskType.learn,
                status=TaskStatus.pending,
                syllabus_id=topic.syllabus_id,
                subject_id=topic.subject_id,
                chapter_id=topic.chapter_id,
                topic_id=topic.id,
                scheduled_date=day,
                start_minute=slot,
                duration_minutes=block,
                source=TaskSource.generated,
                source_id=job.id,
                created_by=effective_student,
            )
            repo.put(task)
            created.append(task)
            planned_minutes += block
            intervals.append((slot, slot + block))
            intervals.sort()
            cursor = slot + block
            remaining -= block
            idx += 1

        if buffer_minutes > 0:
            slot = _next_free_slot(cursor, buffer_minutes, intervals)
            if slot + buffer_minutes <= day_end:
                buffer_task = PlannerTask.new(
                    "task",
                    student_id=effective_student,
                    title="Buffer / catch-up",
                    task_type=TaskType.other,
                    status=TaskStatus.pending,
                    scheduled_date=day,
                    start_minute=slot,
                    duration_minutes=buffer_minutes,
                    source=TaskSource.generated,
                    source_id=job.id,
                    created_by=effective_student,
                )
                repo.put(buffer_task)
                created.append(buffer_task)
                planned_minutes += buffer_minutes

    for topic in ordered[idx:]:
        warnings.append(
            f"Topic '{topic.name}' could not be scheduled within {days} day(s)."
        )

    job.status = "completed"
    job.completed_at = utcnow()
    job.warnings = warnings
    job.result = {
        "created_task_ids": [t.id for t in created],
        "planned_minutes": planned_minutes,
    }
    job.touch()
    repo.put(job)
    record_audit(
        repo,
        principal.user_id,
        "planner.generate",
        "generation_job",
        job.id,
        details={
            "student_id": effective_student,
            "days": days,
            "created": len(created),
            "warnings": len(warnings),
        },
    )
    return job


def replan(
    repo: Repository,
    principal: Principal,
    from_date: Optional[date] = None,
) -> GenerationJob:
    effective_student = resolve_student_scope(repo, principal, None)
    assert_parent_read_only(principal)
    profile = _active_profile(repo, effective_student)
    if profile is None:
        raise NotFound("No syllabus profile found for this student.")

    start = from_date or local_today()
    capacity = int(profile.availability.get("minutes_per_day", 180))

    tasks = repo.find(PlannerTask, student_id=effective_student)
    eligible = [
        t for t in tasks
        if t.scheduled_date >= start
        and t.status == TaskStatus.pending
        and not t.locked
    ]
    eligible.sort(key=lambda t: (t.scheduled_date, t.start_minute, t.title))
    eligible_ids = {t.id for t in eligible}
    anchored = [
        t for t in tasks
        if t.id not in eligible_ids
        and t.scheduled_date >= start
        and t.status in BLOCKING_STATUSES
    ]

    occupied: Dict[date, List[Tuple[int, int]]] = defaultdict(list)
    for t in anchored:
        occupied[t.scheduled_date].append((t.start_minute, t.start_minute + t.duration_minutes))

    job = GenerationJob.new(
        "job", student_id=effective_student, kind="replan", status="running"
    )
    repo.put(job)

    moved = 0
    warnings: List[str] = []
    idx = 0
    day = start
    safety = 0
    while idx < len(eligible) and safety < 370:
        safety += 1
        intervals = sorted(occupied[day])
        day_end = DAY_START_MINUTE + capacity
        cursor = DAY_START_MINUTE
        placed_on_day = False

        while idx < len(eligible):
            task = eligible[idx]
            length = task.duration_minutes
            slot = _next_free_slot(cursor, length, intervals)
            if slot + length > day_end:
                break
            _append_history(task, day, slot, "replan", principal.user_id)
            task.scheduled_date = day
            task.start_minute = slot
            task.version += 1
            task.touch()
            repo.put(task)
            record_audit(
                repo,
                principal.user_id,
                "task.reschedule",
                "planner_task",
                task.id,
                details={"student_id": effective_student, "reason": "replan"},
            )
            intervals.append((slot, slot + length))
            intervals.sort()
            occupied[day] = intervals
            cursor = slot + length
            idx += 1
            moved += 1
            placed_on_day = True

        if idx < len(eligible) or not placed_on_day:
            day = day + timedelta(days=1)

    if idx < len(eligible):
        for task in eligible[idx:]:
            warnings.append(
                f"Task '{task.title}' could not be placed within the planning horizon."
            )

    preserved = len(tasks) - moved
    job.status = "completed"
    job.completed_at = utcnow()
    job.explanation = f"Moved {moved} task(s); {preserved} task(s) preserved."
    job.warnings = warnings
    job.result = {
        "created_task_ids": [],
        "moved_task_ids": [t.id for t in eligible[:idx]],
        "planned_minutes": 0,
    }
    job.touch()
    repo.put(job)
    record_audit(
        repo,
        principal.user_id,
        "planner.replan",
        "generation_job",
        job.id,
        details={"student_id": effective_student, "moved": moved},
    )
    return job


def get_generation_job(
    repo: Repository, principal: Principal, job_id: str
) -> GenerationJob:
    job = repo.get(GenerationJob, job_id)
    if job is None:
        raise NotFound("Generation job not found.")
    _assert_record_access(repo, principal, job.student_id)
    return job


# ---------------------------------------------------------------------------
# Study sessions
# ---------------------------------------------------------------------------

def create_session(
    repo: Repository,
    principal: Principal,
    task_id: Optional[str] = None,
) -> StudySession:
    effective = resolve_student_scope(repo, principal, None)
    assert_parent_read_only(principal)
    if task_id:
        task = repo.get(PlannerTask, task_id)
        if task is None or task.student_id != effective:
            raise NotFound("Task not found.")
    session = StudySession.new(
        "sess",
        student_id=effective,
        task_id=task_id,
        status=SessionStatus.not_started,
    )
    repo.put(session)
    record_audit(
        repo,
        principal.user_id,
        "session.create",
        "study_session",
        session.id,
        details={"student_id": effective, "task_id": task_id},
    )
    return session


def _close_open_interval(session: StudySession, now: datetime) -> None:
    for interval in reversed(session.intervals):
        if interval.get("ended_at") is None:
            started = datetime.fromisoformat(interval["started_at"])
            interval["ended_at"] = now.isoformat()
            session.total_seconds += max(0, int((now - started).total_seconds()))
            break


def patch_session(
    repo: Repository,
    principal: Principal,
    session_id: str,
    action: str,
) -> StudySession:
    session = repo.get(StudySession, session_id)
    if session is None:
        raise NotFound("Session not found.")
    assert_owner_access(principal, session.student_id)

    now = utcnow()
    if action == "start":
        if session.status != SessionStatus.not_started:
            raise InvalidStateTransition("Only a not-started session can be started.")
        session.status = SessionStatus.active
        session.started_at = now
        session.intervals.append({"started_at": now.isoformat()})
    elif action == "pause":
        if session.status != SessionStatus.active:
            raise InvalidStateTransition("Only an active session can be paused.")
        _close_open_interval(session, now)
        session.status = SessionStatus.paused
    elif action == "resume":
        if session.status != SessionStatus.paused:
            raise InvalidStateTransition("Only a paused session can be resumed.")
        session.status = SessionStatus.active
        session.intervals.append({"started_at": now.isoformat()})
    elif action == "finish":
        if session.status not in (SessionStatus.active, SessionStatus.paused):
            raise InvalidStateTransition(
                "Only an active or paused session can be finished."
            )
        if session.status == SessionStatus.active:
            _close_open_interval(session, now)
        session.status = SessionStatus.finished
        session.finished_at = now
        if session.task_id and not session.completion_linked:
            task = repo.get(PlannerTask, session.task_id)
            if task is not None and task.student_id == session.student_id:
                if task.status != TaskStatus.completed:
                    task.status = TaskStatus.completed
                    task.completed_at = now
                    task.actual_minutes = math.ceil(session.total_seconds / 60)
                    task.version += 1
                    task.touch()
                    repo.put(task)
            session.completion_linked = True
        record_audit(
            repo,
            principal.user_id,
            "session.finish",
            "study_session",
            session.id,
            details={"student_id": session.student_id, "task_id": session.task_id},
        )
    else:
        raise ValidationFailed(details={"field": "action", "value": action})

    session.touch()
    repo.put(session)
    return session


# ---------------------------------------------------------------------------
# Revision items
# ---------------------------------------------------------------------------

def list_due_revisions(
    repo: Repository,
    principal: Principal,
    student_id: Optional[str] = None,
) -> List[RevisionItem]:
    effective = resolve_student_scope(repo, principal, student_id)
    current = local_today()
    items = [
        item
        for item in repo.find(RevisionItem, student_id=effective, status=RevisionStatus.due)
        if item.due_date <= current
    ]
    items.sort(key=lambda i: (i.due_date, i.title))
    return items


def complete_revision(
    repo: Repository,
    principal: Principal,
    revision_id: str,
) -> RevisionItem:
    item = repo.get(RevisionItem, revision_id)
    if item is None:
        raise NotFound("Revision item not found.")
    assert_owner_access(principal, item.student_id)

    if item.status == RevisionStatus.completed:
        return item  # idempotent retry: return current state

    item.status = RevisionStatus.completed
    item.completed_at = utcnow()
    item.touch()
    repo.put(item)
    record_audit(
        repo,
        principal.user_id,
        "revision.complete",
        "revision_item",
        item.id,
        details={"student_id": item.student_id},
    )

    if item.linked_task_id:
        task = repo.get(PlannerTask, item.linked_task_id)
        if (
            task is not None
            and task.student_id == item.student_id
            and task.status != TaskStatus.completed
        ):
            task.status = TaskStatus.completed
            task.completed_at = utcnow()
            if task.actual_minutes is None:
                task.actual_minutes = task.duration_minutes
            task.version += 1
            task.touch()
            repo.put(task)
    return item
