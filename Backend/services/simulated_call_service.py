"""
Simulated Call Service

Business logic for the simulated one-way in-app call domain plus the
teacher/parent communication endpoints. This module is the only service
surface for the communication routers.

Call creation applies, in order:
  1. Hard sender-permission rules (teacher/ai_agent senders, role-gated).
  2. Recipient resolution and relationship authorization.
  3. Soft content checks (title/transcript, syllabus context, speech asset).
  4. Quiet-hours enforcement per recipient.
  5. Per-sender daily frequency limit.
  6. Active-call deduplication (same content hash + same recipient set).

Delivery state machine (exactly):
  scheduled -> ringing -> accepted -> playing -> completed
  scheduled -> cancelled (caller cancel)
  scheduled -> accepted (dev flow auto-rings; accept is allowed from both
              scheduled and ringing so the local workflow never stalls)
  ringing   -> dismissed | missed | failed
  accepted  -> failed
  playing   -> failed

Cancel semantics: deliveries still in ``scheduled`` move to ``cancelled``;
deliveries already past scheduled are left untouched, and when no delivery
was eligible the cancel is a no-op returning the current call state (200).

Reviews are derived from persisted state only: ScanResult records with
verification_status "teacher_review_required" whose scan owner is a student
of one of the teacher's classes, minus results already carrying a
"teacher.review.resolve" audit entry.

Quiet-hours rejections use 422 VALIDATION_ERROR with the affected recipient
ids in details, per the documented contract.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import hashlib
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from core.access import (
    is_admin,
    parent_can_access_student,
    teacher_can_access_student,
)
from core.config import Settings
from core.errors import (
    InvalidStateTransition,
    NotFound,
    PermissionDenied,
    RateLimited,
    SyllabusContextInvalid,
    ValidationFailed,
)
from core.security import Principal
from core.time import today, utcnow

from models.common import AuditEntry, ClassRoom, Identity, ParentLink, SyllabusContext
from models.communication import (
    CallDelivery,
    CallOut,
    CallSenderType,
    CallStatus,
    ChildOut,
    CommunicationPreferences,
    DeliveryOut,
    DeliveryRef,
    DeliveryState,
    Message,
    MessageKind,
    MyDeliveryOut,
    ProgressSummaryOut,
    ReportOut,
    ResourceShareOut,
    ReviewOut,
    SubjectTaskSummary,
    SimulatedCall,
)
from models.notes import Note, ShareLevel, ShareScope
from models.planner import PlannerTask, TaskSource, TaskStatus, TaskType
from models.scans import Scan, ScanResult
from models.common import AuditEntry
from models.speech import SpeechAsset
from models.syllabus import SyllabusProfile, Topic
from repositories.base import Repository
from services import syllabus_core_service
from services.audit_service import record_audit

logger = logging.getLogger(__name__)

TEACHER_TASK_FIELDS = ["title", "scheduled_date", "duration_minutes", "locked", "teacher_fields"]

# Accept/dismiss are allowed from scheduled as well as ringing: the local
# development flow auto-rings, so a recipient must never be stuck unable to
# act on a freshly scheduled delivery.
_RECIPIENT_ACTIONS: Dict[str, Tuple[DeliveryState, Tuple[DeliveryState, ...]]] = {
    "accept": (DeliveryState.accepted, (DeliveryState.scheduled, DeliveryState.ringing)),
    "dismiss": (DeliveryState.dismissed, (DeliveryState.scheduled, DeliveryState.ringing)),
    "playback-started": (DeliveryState.playing, (DeliveryState.accepted,)),
}


def content_hash(transcript: str) -> str:
    return hashlib.sha256(transcript.encode("utf-8")).hexdigest()


def build_call_out(
    call: SimulatedCall,
    deliveries: List[CallDelivery],
    deduplicated: bool = False,
) -> CallOut:
    refs = [
        DeliveryRef(delivery_id=d.id, recipient_id=d.recipient_id, state=d.state)
        for d in sorted(deliveries, key=lambda d: d.created_at)
    ]
    return CallOut(
        id=call.id,
        sender_id=call.sender_id,
        sender_type=call.sender_type,
        recipient_ids=list(call.recipient_ids),
        title=call.title,
        subject=call.subject,
        transcript=call.transcript,
        speech_asset_id=call.speech_asset_id,
        syllabus_id=call.syllabus_id,
        subject_id=call.subject_id,
        chapter_id=call.chapter_id,
        topic_id=call.topic_id,
        status=call.status,
        deduplicated=deduplicated,
        deduplicated_from=call.id if deduplicated else None,
        created_at=call.created_at,
        updated_at=call.updated_at,
        deliveries=refs,
    )


def build_delivery_out(delivery: CallDelivery) -> DeliveryOut:
    return DeliveryOut(
        delivery_id=delivery.id,
        call_id=delivery.call_id,
        recipient_id=delivery.recipient_id,
        state=delivery.state,
        event_version=delivery.event_version,
        state_timestamps=dict(delivery.state_timestamps),
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )


# ---------------------------------------------------------------------------
# Call creation
# ---------------------------------------------------------------------------

def create_call(
    repo: Repository,
    settings: Settings,
    principal: Principal,
    *,
    recipient_ids: List[str],
    title: str,
    subject: Optional[str],
    transcript: str,
    speech_asset_id: Optional[str],
    sender_type: CallSenderType,
    context: SyllabusContext,
) -> Tuple[SimulatedCall, List[CallDelivery], bool]:
    """
    Create one SimulatedCall plus one scheduled CallDelivery per recipient.

    Returns:
        (call, deliveries, created); created is False when an active call
        with identical content and recipients already existed (dedup hit).

    Raises (in contract order):
        PermissionDenied, ValidationFailed, NotFound, RateLimited.
    """
    # 1. Hard permission rules before any soft check.
    if sender_type == CallSenderType.teacher:
        if principal.role not in ("teacher", "admin"):
            raise PermissionDenied(
                message=f"{principal.name} cannot create a teacher simulated call."
            )
    elif sender_type == CallSenderType.ai_agent:
        if principal.role != "admin":
            raise PermissionDenied(
                message=f"{principal.name} cannot create an ai_agent simulated call."
            )
    else:  # CallSenderType.admin
        if principal.role != "admin":
            raise PermissionDenied(
                message=f"{principal.name} cannot create an admin simulated call."
            )

    # 2. Recipient resolution and relationship authorization.
    recipients = list(dict.fromkeys(recipient_ids))
    student_recipients: List[str] = []
    parent_recipients: List[str] = []
    bad_ids: List[str] = []
    for rid in recipients:
        identity = repo.get(Identity, rid)
        if identity is None or identity.role not in ("student", "parent"):
            bad_ids.append(rid)
        elif identity.role == "student":
            student_recipients.append(rid)
        else:
            parent_recipients.append(rid)
    if bad_ids:
        raise ValidationFailed(
            details={"recipient_ids": bad_ids},
            message="One or more recipients are unknown or unsupported.",
        )

    if not is_admin(principal):
        for sid in student_recipients:
            if not teacher_can_access_student(repo, principal.user_id, sid):
                raise PermissionDenied(
                    details={"recipient_id": sid},
                    message="You are not assigned to this student.",
                )
        for pid in parent_recipients:
            if not any(
                parent_can_access_student(repo, pid, sid) for sid in student_recipients
            ):
                raise PermissionDenied(
                    details={"recipient_id": pid},
                    message="The parent is not linked to any student recipient.",
                )

    # 3a. Soft content checks.
    if not title or not title.strip():
        raise ValidationFailed(details={"field": "title"}, message="Title must not be empty.")
    if not transcript or not transcript.strip():
        raise ValidationFailed(
            details={"field": "transcript"}, message="Transcript must not be empty."
        )
    title = title.strip()

    # 3b. Syllabus context when supplied (or when a free-text subject is
    #     set). A supplied topic completes any missing parent fields.
    if context.topic_id:
        topic = repo.get(Topic, context.topic_id)
        if topic is None:
            raise SyllabusContextInvalid(details={"topic_id": context.topic_id})
        context = SyllabusContext(
            syllabus_id=context.syllabus_id or topic.syllabus_id,
            subject_id=context.subject_id or topic.subject_id,
            chapter_id=context.chapter_id or topic.chapter_id,
            topic_id=context.topic_id,
        )
    if not context.is_empty() or (subject and subject.strip()):
        syllabus_core_service.validate_syllabus_context(repo, context)

    # 4. Speech asset must exist and belong to the sender (transcript-only
    #    mode when omitted).
    if speech_asset_id:
        asset = repo.get(SpeechAsset, speech_asset_id)
        if asset is None or asset.owner_id != principal.user_id:
            raise NotFound("Speech asset not found.")

    # 5. Quiet hours per recipient (recipient prefs, else settings defaults).
    now_hour = datetime.now().hour
    quiet_recipients: List[str] = []
    for rid in recipients:
        prefs = repo.first(CommunicationPreferences, user_id=rid)
        if prefs is None:
            enabled = True
            window_start, window_end = (
                settings.quiet_hours_start,
                settings.quiet_hours_end,
            )
        else:
            enabled = prefs.quiet_hours_enabled
            window_start, window_end = prefs.quiet_hours_start, prefs.quiet_hours_end
        if enabled and _hour_in_window(now_hour, window_start, window_end):
            quiet_recipients.append(rid)
    if quiet_recipients:
        raise ValidationFailed(
            message="Quiet hours are active for one or more recipients.",
            details={"recipients": quiet_recipients},
        )

    # 6. Per-sender daily frequency limit.
    todays_date = utcnow().date()
    created_today = sum(
        1
        for call in repo.find(SimulatedCall, sender_id=principal.user_id)
        if call.created_at.date() == todays_date
    )
    if created_today >= settings.max_simulated_calls_per_day:
        raise RateLimited(
            details={
                "max_simulated_calls_per_day": settings.max_simulated_calls_per_day
            },
            message="The simulated-call frequency limit for today has been reached.",
        )

    # 7. Deduplication against an active call with the same content and set.
    hash_value = content_hash(transcript)
    sorted_recipients = sorted(recipients)
    for existing in repo.find(
        SimulatedCall,
        sender_id=principal.user_id,
        content_hash=hash_value,
        status=CallStatus.active,
    ):
        if sorted(existing.recipient_ids) == sorted_recipients:
            deliveries = repo.find(CallDelivery, call_id=existing.id)
            return existing, deliveries, False

    # 8. Persist the call and its deliveries.
    call = SimulatedCall.new(
        "call",
        sender_id=principal.user_id,
        sender_type=sender_type,
        recipient_ids=recipients,
        title=title,
        subject=subject,
        transcript=transcript,
        speech_asset_id=speech_asset_id,
        syllabus_id=context.syllabus_id,
        subject_id=context.subject_id,
        chapter_id=context.chapter_id,
        topic_id=context.topic_id,
        content_hash=hash_value,
        status=CallStatus.active,
        created_by=principal.user_id,
    )
    repo.put(call)
    deliveries: List[CallDelivery] = []
    for rid in recipients:
        delivery = CallDelivery.new(
            "dlv",
            call_id=call.id,
            recipient_id=rid,
            state=DeliveryState.scheduled,
            event_version=0,
            state_timestamps={"scheduled": utcnow()},
        )
        repo.put(delivery)
        deliveries.append(delivery)

    record_audit(
        repo,
        principal.user_id,
        "simulated_call.create",
        "simulated_call",
        call.id,
        details={"recipient_count": len(recipients)},
    )
    return call, deliveries, True


def _hour_in_window(hour: int, start: int, end: int) -> bool:
    """True when ``hour`` lies in [start, end), supporting wrap-around
    windows such as 21 -> 7. An empty window (start == end) disables the
    check."""
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


# ---------------------------------------------------------------------------
# Delivery state machine
# ---------------------------------------------------------------------------

def _get_own_delivery(
    repo: Repository, principal: Principal, delivery_id: str
) -> CallDelivery:
    """Fetch a delivery scoped to its recipient; anything else is hidden."""
    delivery = repo.get(CallDelivery, delivery_id)
    if delivery is None or delivery.recipient_id != principal.user_id:
        raise NotFound("The requested resource was not found.")
    return delivery


def _get_call(repo: Repository, call_id: str) -> SimulatedCall:
    call = repo.get(SimulatedCall, call_id)
    if call is None:
        raise NotFound("The requested resource was not found.")
    return call


def _record_transition(
    repo: Repository,
    principal: Principal,
    delivery: CallDelivery,
    target: DeliveryState,
) -> CallDelivery:
    previous = delivery.state
    delivery.state = target
    delivery.state_timestamps[target.value] = utcnow()
    delivery.event_version += 1
    delivery.touch()
    repo.put(delivery)
    record_audit(
        repo,
        principal.user_id,
        "call.transition",
        "call_delivery",
        delivery.id,
        details={
            "delivery_id": delivery.id,
            "from": previous.value,
            "to": target.value,
        },
    )
    return delivery


def _ensure_call_history_message(
    repo: Repository, call: SimulatedCall, delivery: CallDelivery, verb: str
) -> Message:
    """Create the call-history message for a delivery action once."""
    title = f"Call {verb}: {call.title}"
    existing = repo.first(
        Message,
        recipient_id=delivery.recipient_id,
        kind=MessageKind.call_history,
        delivery_id=delivery.id,
        title=title,
    )
    if existing is not None:
        return existing
    message = Message.new(
        "msg",
        recipient_id=delivery.recipient_id,
        sender_id=call.sender_id,
        kind=MessageKind.call_history,
        title=title,
        body=(
            f"Simulated call '{call.title}' from {call.sender_id} was {verb}."
        ),
        call_id=call.id,
        delivery_id=delivery.id,
    )
    repo.put(message)
    return message


def apply_recipient_action(
    repo: Repository, principal: Principal, delivery_id: str, action: str
) -> CallDelivery:
    """Accept, dismiss, or start playback on the caller's own delivery."""
    target, allowed = _RECIPIENT_ACTIONS[action]
    delivery = _get_own_delivery(repo, principal, delivery_id)
    if delivery.state not in allowed:
        raise InvalidStateTransition(
            details={
                "delivery_id": delivery.id,
                "state": delivery.state.value,
                "target": target.value,
            },
            message=(
                f"Cannot {action} a delivery in state {delivery.state.value}."
            ),
        )
    delivery = _record_transition(repo, principal, delivery, target)
    if action == "dismiss":
        call = _get_call(repo, delivery.call_id)
        _ensure_call_history_message(repo, call, delivery, "dismissed")
    return delivery


def complete_delivery(
    repo: Repository, principal: Principal, delivery_id: str
) -> CallDelivery:
    """
    playing -> completed. Completing an already-completed delivery is
    idempotent: the current delivery is returned with no version bump and
    no duplicate history message.
    """
    delivery = _get_own_delivery(repo, principal, delivery_id)
    if delivery.state == DeliveryState.completed:
        return delivery
    if delivery.state != DeliveryState.playing:
        raise InvalidStateTransition(
            details={
                "delivery_id": delivery.id,
                "state": delivery.state.value,
                "target": DeliveryState.completed.value,
            },
            message=(
                f"Cannot complete a delivery in state {delivery.state.value}."
            ),
        )
    delivery = _record_transition(repo, principal, delivery, DeliveryState.completed)
    call = _get_call(repo, delivery.call_id)
    _ensure_call_history_message(repo, call, delivery, "completed")
    return delivery


# ---------------------------------------------------------------------------
# Cancel, listing, retrieval
# ---------------------------------------------------------------------------

def cancel_call(
    repo: Repository, principal: Principal, call_id: str
) -> Tuple[SimulatedCall, List[CallDelivery], bool]:
    """
    Cancel deliveries still in ``scheduled`` state.

    Deliveries already past scheduled are left unchanged; when none were
    eligible the cancel is a documented no-op returning 200 with the
    current call state. Caller must be the sender or an admin (other
    senders' calls are hidden with 404).

    Returns:
        (call, deliveries, cancelled_anything).
    """
    call = repo.get(SimulatedCall, call_id)
    if call is None or (call.sender_id != principal.user_id and not is_admin(principal)):
        raise NotFound("The requested resource was not found.")

    changed = False
    for delivery in repo.find(CallDelivery, call_id=call.id):
        if delivery.state == DeliveryState.scheduled:
            _record_transition(repo, principal, delivery, DeliveryState.cancelled)
            changed = True
    if changed:
        call.status = CallStatus.cancelled
        call.touch()
        repo.put(call)
    return call, repo.find(CallDelivery, call_id=call.id), changed


def list_calls(repo: Repository, principal: Principal) -> List[Tuple[SimulatedCall, List[CallDelivery]]]:
    """Sender-owned calls (admin sees all). Recipients use /me/simulated-calls."""
    if is_admin(principal):
        calls = repo.all(SimulatedCall)
    elif principal.role == "teacher":
        calls = repo.find(SimulatedCall, sender_id=principal.user_id)
    else:
        raise PermissionDenied(
            message="Only call senders and admins can list simulated calls."
        )
    calls.sort(key=lambda c: c.created_at, reverse=True)
    return [(call, repo.find(CallDelivery, call_id=call.id)) for call in calls]


def get_call_for_principal(
    repo: Repository, principal: Principal, call_id: str
) -> Tuple[SimulatedCall, List[CallDelivery]]:
    """Sender/admin see every delivery; a recipient sees only their own."""
    call = repo.get(SimulatedCall, call_id)
    if call is None:
        raise NotFound("The requested resource was not found.")
    if is_admin(principal) or call.sender_id == principal.user_id:
        return call, repo.find(CallDelivery, call_id=call.id)
    if principal.user_id in call.recipient_ids:
        own = repo.first(
            CallDelivery, call_id=call.id, recipient_id=principal.user_id
        )
        return call, [own] if own else []
    raise NotFound("The requested resource was not found.")


def list_my_deliveries(
    repo: Repository, principal: Principal
) -> List[MyDeliveryOut]:
    deliveries = repo.find(CallDelivery, recipient_id=principal.user_id)
    deliveries.sort(key=lambda d: d.updated_at, reverse=True)
    out: List[MyDeliveryOut] = []
    for delivery in deliveries:
        call = repo.get(SimulatedCall, delivery.call_id)
        if call is None:
            continue
        out.append(
            MyDeliveryOut(
                delivery_id=delivery.id,
                call_id=delivery.call_id,
                title=call.title,
                state=delivery.state,
                event_version=delivery.event_version,
                sender_id=call.sender_id,
                speech_asset_id=call.speech_asset_id,
                updated_at=delivery.updated_at,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def list_messages(
    repo: Repository, principal: Principal, unread_only: bool = False
) -> List[Message]:
    messages = repo.find(Message, recipient_id=principal.user_id)
    if unread_only:
        messages = [m for m in messages if not m.read]
    messages.sort(key=lambda m: m.created_at, reverse=True)
    return messages


def mark_message_read(
    repo: Repository, principal: Principal, message_id: str
) -> Message:
    message = repo.get(Message, message_id)
    if message is None or message.recipient_id != principal.user_id:
        raise NotFound("The requested resource was not found.")
    if not message.read:
        message.read = True
        message.read_at = utcnow()
        repo.put(message)
    return message


# ---------------------------------------------------------------------------
# Teacher endpoints
# ---------------------------------------------------------------------------

def get_teacher_class(
    repo: Repository, principal: Principal, class_id: str
) -> ClassRoom:
    """Class access check: teacher in class teacher_ids or admin, else 404."""
    classroom = repo.get(ClassRoom, class_id)
    if classroom is None or (
        principal.user_id not in classroom.teacher_ids and not is_admin(principal)
    ):
        raise NotFound("The requested resource was not found.")
    return classroom


def _student_progress_dict(repo: Repository, student_id: str) -> Dict:
    principal = Principal(user_id=student_id, role="student", name=student_id)
    return syllabus_core_service.get_progress(repo, principal, student_id)


def teacher_class_progress(
    repo: Repository, principal: Principal, class_id: str
) -> List[ProgressSummaryOut]:
    classroom = get_teacher_class(repo, principal, class_id)
    out: List[ProgressSummaryOut] = []
    for student_id in classroom.student_ids:
        identity = repo.get(Identity, student_id)
        try:
            progress = _student_progress_dict(repo, student_id)
        except NotFound:
            continue  # student without an active profile contributes nothing
        out.append(
            ProgressSummaryOut(
                student_id=student_id,
                name=identity.name if identity else student_id,
                topics_total=progress["topics_total"],
                topics_covered=progress["topics_covered"],
                percent=progress["percent"],
            )
        )
    return out


def teacher_create_tasks(
    repo: Repository,
    principal: Principal,
    class_id: str,
    *,
    title: str,
    task_type: Optional[TaskType],
    duration_minutes: Optional[int],
    scheduled_date: Optional[date],
    topic_id: Optional[str],
    student_ids: Optional[List[str]],
    syllabus_id: Optional[str],
    subject_id: Optional[str],
    chapter_id: Optional[str],
) -> List[Dict[str, str]]:
    classroom = get_teacher_class(repo, principal, class_id)

    if not title or not title.strip():
        raise ValidationFailed(details={"field": "title"}, message="Title must not be empty.")

    targets = list(student_ids) if student_ids else list(classroom.student_ids)
    not_in_class = [sid for sid in targets if sid not in classroom.student_ids]
    if not_in_class:
        raise ValidationFailed(
            details={"student_ids": not_in_class},
            message="Every student must belong to the class.",
        )

    # Syllabus context: an explicit topic is validated and completes any
    # missing parent context fields.
    context_kwargs: Dict[str, Optional[str]] = {
        "syllabus_id": syllabus_id,
        "subject_id": subject_id,
        "chapter_id": chapter_id,
        "topic_id": topic_id,
    }
    if topic_id:
        topic = repo.get(Topic, topic_id)
        if topic is None:
            raise SyllabusContextInvalid(details={"topic_id": topic_id})
        context_kwargs["syllabus_id"] = context_kwargs["syllabus_id"] or topic.syllabus_id
        context_kwargs["subject_id"] = context_kwargs["subject_id"] or topic.subject_id
        context_kwargs["chapter_id"] = context_kwargs["chapter_id"] or topic.chapter_id
    context = SyllabusContext(**context_kwargs)
    if not context.is_empty():
        syllabus_core_service.validate_syllabus_context(repo, context)

    duration = duration_minutes if duration_minutes is not None else 45
    if duration <= 0 or duration > 24 * 60:
        raise ValidationFailed(details={"field": "duration_minutes"})
    scheduled = scheduled_date or (today() + timedelta(days=1))
    effective_type = task_type or TaskType.homework

    created: List[Dict[str, str]] = []
    for student_id in targets:
        task = PlannerTask.new(
            "task",
            student_id=student_id,
            title=title.strip(),
            task_type=effective_type,
            status=TaskStatus.pending,
            syllabus_id=context.syllabus_id,
            subject_id=context.subject_id,
            chapter_id=context.chapter_id,
            topic_id=context.topic_id,
            scheduled_date=scheduled,
            start_minute=0,
            duration_minutes=duration,
            locked=True,
            locked_by=principal.user_id,
            teacher_fields=list(TEACHER_TASK_FIELDS),
            source=TaskSource.teacher,
            created_by=principal.user_id,
        )
        repo.put(task)
        created.append({"student_id": student_id, "task_id": task.id})

    record_audit(
        repo,
        principal.user_id,
        "teacher.task.create",
        "planner_task",
        None,
        details={"class_id": class_id, "student_count": len(created)},
    )
    return created


def teacher_share_resource(
    repo: Repository,
    principal: Principal,
    class_id: str,
    *,
    title: str,
    body: Optional[str],
    note_id: Optional[str],
) -> ResourceShareOut:
    get_teacher_class(repo, principal, class_id)

    if note_id:
        note = repo.get(Note, note_id)
        if note is None or note.owner_id != principal.user_id:
            raise NotFound("The requested resource was not found.")
        note.share_scope = ShareScope(level=ShareLevel.class_share, audience=[class_id])
        note.touch()
        repo.put(note)
    else:
        if not title or not title.strip():
            raise ValidationFailed(details={"field": "title"}, message="Title must not be empty.")
        note = Note.new(
            "note",
            owner_id=principal.user_id,
            title=title.strip(),
            body=body or "",
            share_scope=ShareScope(level=ShareLevel.class_share, audience=[class_id]),
            source="manual",
        )
        repo.put(note)

    record_audit(
        repo,
        principal.user_id,
        "teacher.resource.share",
        "note",
        note.id,
        details={"class_id": class_id},
    )
    return ResourceShareOut(
        note_id=note.id, title=note.title, scope="class", class_id=class_id
    )


_RESOLVED_REVIEW_ACTIONS = "teacher.review.resolve"


def _resolved_review_ids(repo: Repository) -> set:
    return {
        entry.resource_id
        for entry in repo.all(AuditEntry)
        if entry.action == _RESOLVED_REVIEW_ACTIONS and entry.resource_id
    }


def teacher_list_reviews(
    repo: Repository, principal: Principal
) -> List[ReviewOut]:
    resolved = _resolved_review_ids(repo)
    out: List[ReviewOut] = []
    for result in repo.all(ScanResult):
        if result.verification_status != "teacher_review_required":
            continue
        if result.id in resolved:
            continue
        scan = repo.get(Scan, result.scan_id)
        if scan is None:
            continue
        if not is_admin(principal) and not teacher_can_access_student(
            repo, principal.user_id, scan.owner_id
        ):
            continue
        out.append(
            ReviewOut(
                review_id=f"review_{result.id}",
                kind="scan_answer",
                student_id=scan.owner_id,
                scan_id=scan.id,
                verification_status=result.verification_status,
                created_at=result.created_at,
            )
        )
    out.sort(key=lambda r: r.created_at)
    return out


def teacher_resolve_review(
    repo: Repository,
    principal: Principal,
    review_id: str,
    resolution: str,
    correction: Optional[str],
) -> Tuple[str, datetime]:
    """
    Resolve a pending review. Existence, pending status, and class ownership
    are all enforced with 404 so private records are never exposed. The
    audit details carry only the resolution length — never the correction
    text, which may contain student content.
    """
    if not review_id.startswith("review_"):
        raise NotFound("The requested resource was not found.")
    result = repo.get(ScanResult, review_id[len("review_"):])
    if result is None:
        raise NotFound("The requested resource was not found.")

    if result.id in _resolved_review_ids(repo):
        raise NotFound("The requested resource was not found.")

    scan = repo.get(Scan, result.scan_id)
    if scan is None:
        raise NotFound("The requested resource was not found.")
    if not is_admin(principal) and not teacher_can_access_student(
        repo, principal.user_id, scan.owner_id
    ):
        raise NotFound("The requested resource was not found.")

    if not resolution or not resolution.strip():
        raise ValidationFailed(details={"field": "resolution"})

    resolved_at = utcnow()
    record_audit(
        repo,
        principal.user_id,
        _RESOLVED_REVIEW_ACTIONS,
        "scan_result",
        result.id,
        details={"resolution_length": len(resolution)},
    )
    return review_id, resolved_at


# ---------------------------------------------------------------------------
# Parent endpoints
# ---------------------------------------------------------------------------

def assert_parent_or_admin(principal: Principal) -> None:
    if principal.role not in ("parent", "admin"):
        raise PermissionDenied(
            message="This endpoint requires a parent or admin role."
        )


def _linked_children(repo: Repository, parent_id: str) -> List[str]:
    return [
        link.student_id
        for link in repo.all(ParentLink)
        if link.parent_id == parent_id
    ]


def parent_children(repo: Repository, principal: Principal) -> List[ChildOut]:
    assert_parent_or_admin(principal)
    out: List[ChildOut] = []
    for student_id in _linked_children(repo, principal.user_id):
        identity = repo.get(Identity, student_id)
        profile = repo.first(SyllabusProfile, student_id=student_id)
        try:
            percent = _student_progress_dict(repo, student_id)["percent"]
        except NotFound:
            percent = 0.0
        out.append(
            ChildOut(
                student_id=student_id,
                name=identity.name if identity else student_id,
                target_exam=profile.target_exam if profile else None,
                target_year=profile.target_year if profile else None,
                percent=percent,
            )
        )
    return out


def _assert_linked_child(repo: Repository, principal: Principal, student_id: str) -> None:
    assert_parent_or_admin(principal)
    if not parent_can_access_student(repo, principal.user_id, student_id):
        raise PermissionDenied(
            details={"student_id": student_id},
            message="You are not linked to this student.",
        )


def parent_child_progress(
    repo: Repository, principal: Principal, student_id: str
) -> Dict:
    _assert_linked_child(repo, principal, student_id)
    return _student_progress_dict(repo, student_id)


def parent_child_report(
    repo: Repository, principal: Principal, student_id: str, period_days: int = 7
) -> ReportOut:
    _assert_linked_child(repo, principal, student_id)
    cutoff = today() - timedelta(days=period_days)
    tasks = [
        task
        for task in repo.find(PlannerTask, student_id=student_id)
        if task.scheduled_date >= cutoff
    ]
    completed = [t for t in tasks if t.status == TaskStatus.completed]

    per_subject: Dict[str, Dict[str, int]] = {}
    for task in tasks:
        if not task.subject_id:
            continue
        bucket = per_subject.setdefault(
            task.subject_id, {"tasks_total": 0, "tasks_completed": 0}
        )
        bucket["tasks_total"] += 1
        if task.status == TaskStatus.completed:
            bucket["tasks_completed"] += 1

    minutes_planned = sum(t.duration_minutes for t in tasks)
    minutes_completed = sum(
        t.actual_minutes if t.actual_minutes is not None else t.duration_minutes
        for t in completed
    )

    return ReportOut(
        student_id=student_id,
        period_days=period_days,
        generated_at=utcnow(),
        tasks_total=len(tasks),
        tasks_completed=len(completed),
        completion_percent=(
            round(100 * len(completed) / len(tasks), 1) if tasks else 0.0
        ),
        minutes_planned=minutes_planned,
        minutes_completed=minutes_completed,
        per_subject=[
            SubjectTaskSummary(subject_id=sid, **counts)
            for sid, counts in sorted(per_subject.items())
        ],
    )


def parent_get_prefs(
    repo: Repository, settings: Settings, principal: Principal
) -> CommunicationPreferences:
    assert_parent_or_admin(principal)
    prefs = repo.first(CommunicationPreferences, user_id=principal.user_id)
    if prefs is None:
        prefs = CommunicationPreferences.new(
            "commpref",
            user_id=principal.user_id,
            quiet_hours_enabled=True,
            quiet_hours_start=settings.quiet_hours_start,
            quiet_hours_end=settings.quiet_hours_end,
            max_calls_per_day=5,
            allow_ai_calls=True,
        )
        repo.put(prefs)
    return prefs


def parent_update_prefs(
    repo: Repository,
    settings: Settings,
    principal: Principal,
    updates,
) -> CommunicationPreferences:
    assert_parent_or_admin(principal)
    prefs = parent_get_prefs(repo, settings, principal)
    for key, value in updates.model_dump(exclude_none=True).items():
        setattr(prefs, key, value)
    prefs.touch()
    repo.put(prefs)
    return prefs
