"""
Syllabus Service

Business logic for the syllabus catalogue, student syllabus profiles with
optimistic concurrency, progress calculation, and teacher templates.

Progress is derived from topic/task state, never a hard-coded percentage.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional

from core.access import assert_teacher_or_admin
from core.errors import NotFound, ResourceConflict, SyllabusContextInvalid, ValidationFailed
from core.security import Principal
from core.time import utcnow
from models.common import SyllabusContext
from models.planner import PlannerTask, RevisionItem, TaskStatus
from models.syllabus import (
    Chapter,
    Subject,
    Syllabus,
    SyllabusProfile,
    SyllabusTemplate,
    TemplateStatus,
    Topic,
)
from repositories.base import Repository
from services.audit_service import record_audit

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def list_syllabi(repo: Repository) -> List[Syllabus]:
    syllabi = repo.all(Syllabus)
    syllabi.sort(key=lambda s: (s.name, s.version))
    return syllabi


def get_syllabus(repo: Repository, syllabus_id: str) -> Syllabus:
    syllabus = repo.get(Syllabus, syllabus_id)
    if syllabus is None:
        raise NotFound("Syllabus not found.")
    return syllabus


def list_subjects(repo: Repository, syllabus_id: str) -> List[Subject]:
    get_syllabus(repo, syllabus_id)
    subjects = repo.find(Subject, syllabus_id=syllabus_id)
    subjects.sort(key=lambda s: s.name)
    return subjects


def list_chapters(repo: Repository, subject_id: str) -> List[Chapter]:
    subject = repo.get(Subject, subject_id)
    if subject is None:
        raise NotFound("Subject not found.")
    chapters = repo.find(Chapter, subject_id=subject_id)
    chapters.sort(key=lambda c: (c.order_index, c.name))
    return chapters


def list_topics(repo: Repository, chapter_id: str) -> List[Topic]:
    chapter = repo.get(Chapter, chapter_id)
    if chapter is None:
        raise NotFound("Chapter not found.")
    topics = repo.find(Topic, chapter_id=chapter_id)
    topics.sort(key=lambda t: t.name)
    return topics


# ---------------------------------------------------------------------------
# Context validation (shared across academic domains)
# ---------------------------------------------------------------------------

def validate_syllabus_context(
    repo: Repository,
    context: SyllabusContext,
    profile: Optional[SyllabusProfile] = None,
) -> None:
    """
    Validate the parent-child hierarchy of a syllabus reference.

    When a profile is supplied, the context must belong to that profile's
    active syllabus (and selected subjects, when a subject is given).
    """
    if context is None or context.is_empty():
        return

    if context.topic_id:
        topic = repo.get(Topic, context.topic_id)
        if topic is None:
            raise SyllabusContextInvalid(details={"topic_id": context.topic_id})
        if context.chapter_id and topic.chapter_id != context.chapter_id:
            raise SyllabusContextInvalid(
                details={"topic_id": context.topic_id, "chapter_id": context.chapter_id},
                message="The selected topic does not belong to the supplied chapter.",
            )
        if context.subject_id and topic.subject_id != context.subject_id:
            raise SyllabusContextInvalid(
                details={"topic_id": context.topic_id, "subject_id": context.subject_id},
                message="The selected topic does not belong to the supplied subject.",
            )
        if context.syllabus_id and topic.syllabus_id != context.syllabus_id:
            raise SyllabusContextInvalid(
                details={"topic_id": context.topic_id, "syllabus_id": context.syllabus_id},
                message="The selected topic does not belong to the supplied syllabus.",
            )
        effective_syllabus = topic.syllabus_id
        effective_subject = topic.subject_id
    elif context.chapter_id:
        chapter = repo.get(Chapter, context.chapter_id)
        if chapter is None:
            raise SyllabusContextInvalid(details={"chapter_id": context.chapter_id})
        if context.subject_id and chapter.subject_id != context.subject_id:
            raise SyllabusContextInvalid(
                details={"chapter_id": context.chapter_id, "subject_id": context.subject_id},
                message="The selected chapter does not belong to the supplied subject.",
            )
        if context.syllabus_id and chapter.syllabus_id != context.syllabus_id:
            raise SyllabusContextInvalid(
                details={"chapter_id": context.chapter_id, "syllabus_id": context.syllabus_id},
                message="The selected chapter does not belong to the supplied syllabus.",
            )
        effective_syllabus = chapter.syllabus_id
        effective_subject = chapter.subject_id
    elif context.subject_id:
        subject = repo.get(Subject, context.subject_id)
        if subject is None:
            raise SyllabusContextInvalid(details={"subject_id": context.subject_id})
        if context.syllabus_id and subject.syllabus_id != context.syllabus_id:
            raise SyllabusContextInvalid(
                details={"subject_id": context.subject_id, "syllabus_id": context.syllabus_id},
                message="The selected subject does not belong to the supplied syllabus.",
            )
        effective_syllabus = subject.syllabus_id
        effective_subject = subject.id
    else:
        if context.syllabus_id and repo.get(Syllabus, context.syllabus_id) is None:
            raise SyllabusContextInvalid(details={"syllabus_id": context.syllabus_id})
        return

    if profile is not None:
        if effective_syllabus != profile.syllabus_id:
            raise SyllabusContextInvalid(
                message="The reference does not belong to the active syllabus.",
            )
        if (
            effective_subject
            and profile.subjects
            and effective_subject not in profile.subjects
        ):
            raise SyllabusContextInvalid(
                message="The reference is outside the profile's selected subjects.",
            )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def get_profile(repo: Repository, principal: Principal, student_id: Optional[str] = None) -> SyllabusProfile:
    from core.access import resolve_student_scope

    effective_student = resolve_student_scope(repo, principal, student_id)
    profile = repo.first(SyllabusProfile, student_id=effective_student)
    if profile is None:
        raise NotFound("No syllabus profile found for this student.")
    return profile


def update_profile(
    repo: Repository,
    principal: Principal,
    student_id: Optional[str],
    data: dict,
    expected_version: int,
) -> SyllabusProfile:
    from core.access import assert_parent_read_only, resolve_student_scope

    assert_parent_read_only(principal)
    effective_student = resolve_student_scope(repo, principal, student_id)

    profile = repo.first(SyllabusProfile, student_id=effective_student)
    if profile is None:
        raise NotFound("No syllabus profile found for this student.")

    if expected_version != profile.version:
        raise ResourceConflict(
            details={"expected_version": expected_version, "current_version": profile.version},
            message="The profile was modified by another request.",
        )

    updates = data or {}
    if "subjects" in updates:
        for subject_id in updates["subjects"]:
            subject = repo.get(Subject, subject_id)
            if subject is None or subject.syllabus_id != profile.syllabus_id:
                raise SyllabusContextInvalid(
                    details={"subject_id": subject_id},
                    message="Selected subject does not belong to the active syllabus.",
                )
        profile.subjects = list(updates["subjects"])
    if "availability" in updates and updates["availability"] is not None:
        availability = dict(updates["availability"])
        minutes = int(availability.get("minutes_per_day", profile.availability.get("minutes_per_day", 180)))
        days = int(availability.get("days_per_week", profile.availability.get("days_per_week", 6)))
        if minutes <= 0 or minutes > 24 * 60:
            raise ValidationFailed(details={"field": "availability.minutes_per_day"})
        if days <= 0 or days > 7:
            raise ValidationFailed(details={"field": "availability.days_per_week"})
        profile.availability = {"minutes_per_day": minutes, "days_per_week": days}
    if "target_date" in updates:
        profile.target_date = updates["target_date"]
    if "target_exam" in updates and updates["target_exam"]:
        profile.target_exam = updates["target_exam"]
    if "target_year" in updates and updates["target_year"]:
        profile.target_year = int(updates["target_year"])
    if "preferences" in updates and updates["preferences"] is not None:
        profile.preferences = dict(updates["preferences"])

    profile.version += 1
    profile.touch()
    repo.put(profile)
    record_audit(
        repo,
        principal.user_id,
        "syllabus_profile.update",
        "syllabus_profile",
        profile.id,
        details={"student_id": effective_student, "version": profile.version},
    )
    return profile


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

def get_progress(repo: Repository, principal: Principal, student_id: Optional[str] = None) -> Dict:
    """
    Compute syllabus progress for a student from task/revision state.

    A topic counts as covered when it has at least one completed task or a
    completed revision item.
    """
    from core.access import resolve_student_scope

    effective_student = resolve_student_scope(repo, principal, student_id)
    profile = repo.first(SyllabusProfile, student_id=effective_student)
    if profile is None:
        raise NotFound("No syllabus profile found for this student.")

    completed_task_topics = {
        task.topic_id
        for task in repo.find(PlannerTask, student_id=effective_student, status=TaskStatus.completed)
        if task.topic_id
    }
    completed_revision_topics = {
        item.topic_id
        for item in repo.find(RevisionItem, student_id=effective_student, status="completed")
        if item.topic_id
    }
    subjects_out = []
    total_topics = 0
    covered_topics = 0
    for subject_id in profile.subjects:
        subject = repo.get(Subject, subject_id)
        if subject is None:
            continue
        chapters = repo.find(Chapter, subject_id=subject_id)
        subject_total = 0
        subject_covered = 0
        covered_chapters = set()
        for chapter in chapters:
            topics = repo.find(Topic, chapter_id=chapter.id)
            chapter_covered = False
            for topic in topics:
                covered = (
                    topic.id in completed_task_topics
                    or topic.id in completed_revision_topics
                )
                subject_total += 1
                subject_covered += 1 if covered else 0
                chapter_covered = chapter_covered or covered
            if chapter_covered:
                covered_chapters.add(chapter.id)
        total_topics += subject_total
        covered_topics += subject_covered
        subjects_out.append(
            {
                "subject_id": subject_id,
                "name": subject.name if subject else subject_id,
                "topics_total": subject_total,
                "topics_covered": subject_covered,
                "percent": round(100 * subject_covered / subject_total, 1) if subject_total else 0.0,
                "chapters_covered": len(covered_chapters),
                "chapters_total": len(chapters),
            }
        )

    return {
        "student_id": effective_student,
        "syllabus_id": profile.syllabus_id,
        "topics_total": total_topics,
        "topics_covered": covered_topics,
        "percent": round(100 * covered_topics / total_topics, 1) if total_topics else 0.0,
        "subjects": subjects_out,
    }


# ---------------------------------------------------------------------------
# Teacher templates
# ---------------------------------------------------------------------------

def create_template(
    repo: Repository,
    principal: Principal,
    name: str,
    description: str,
    payload: dict,
) -> SyllabusTemplate:
    assert_teacher_or_admin(principal)
    if not name or not name.strip():
        raise ValidationFailed(details={"field": "name"})

    template = SyllabusTemplate.new(
        "tmpl",
        teacher_id=principal.user_id,
        name=name.strip(),
        description=description or "",
        payload=payload or {},
    )
    repo.put(template)
    record_audit(
        repo,
        principal.user_id,
        "syllabus_template.create",
        "syllabus_template",
        template.id,
        details={"name": template.name},
    )
    return template


def publish_template(repo: Repository, principal: Principal, template_id: str) -> SyllabusTemplate:
    assert_teacher_or_admin(principal)
    template = repo.get(SyllabusTemplate, template_id)
    if template is None:
        raise NotFound("Template not found.")
    if template.teacher_id != principal.user_id and principal.role != "admin":
        raise NotFound("Template not found.")

    if template.status == TemplateStatus.published:
        # Publishing is one-way and idempotent; a repeat publish is a no-op.
        return template

    template.status = TemplateStatus.published
    template.published_at = utcnow()
    template.touch()
    repo.put(template)
    record_audit(
        repo,
        principal.user_id,
        "syllabus_template.publish",
        "syllabus_template",
        template.id,
        details={"name": template.name},
    )
    return template
