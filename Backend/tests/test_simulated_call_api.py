"""
Simulated Call, Message, Teacher, and Parent API Tests

Covers section 21.6 (simulated calls and messages) plus the teacher/parent
endpoints from section 18 and the communication parts of the permission
matrix from section 21.2.
"""

from datetime import date, datetime, timedelta

import pytest

from tests.conftest import (
    ADMIN_LOCAL,
    PARENT_RAJESH,
    STUDENT_AARAV,
    STUDENT_MEERA,
    SUBJECT_CHEMISTRY,
    SUBJECT_PHYSICS,
    SYLLABUS_ID,
    TEACHER_RAO,
    TOPIC_KINETIC_ENERGY,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = auth_headers(STUDENT_MEERA, "student", "Meera Iyer")
RAO = auth_headers(TEACHER_RAO, "teacher", "Mrs. Rao")
RAJESH = auth_headers(PARENT_RAJESH, "parent", "Rajesh Sharma")
ADMIN = auth_headers(ADMIN_LOCAL, "admin", "Local Admin")

CLASS_12A = "class_12a"


@pytest.fixture(autouse=True)
def _neutralize_quiet_hours(fresh_repository):
    """Deterministic scheduling regardless of the local hour; the dedicated
    quiet-hours tests re-enable windows explicitly."""
    from models.communication import CommunicationPreferences

    for user_id in (STUDENT_AARAV, PARENT_RAJESH):
        prefs = fresh_repository.first(CommunicationPreferences, user_id=user_id)
        if prefs is None:
            prefs = CommunicationPreferences.new("commpref", user_id=user_id)
        prefs.quiet_hours_enabled = False
        fresh_repository.put(prefs)


def _create_call(client, headers, recipients, **overrides):
    body = {
        "recipient_ids": recipients,
        "title": "Physics revision plan",
        "transcript": "Please review rotational motion today.",
    }
    body.update(overrides)
    return client.post("/api/v1/simulated-calls", json=body, headers=headers)


def _delivery_id_for(call_body, recipient_id):
    for delivery in call_body["deliveries"]:
        if delivery["recipient_id"] == recipient_id:
            return delivery["delivery_id"]
    raise AssertionError(f"no delivery for {recipient_id}")


# ---------------------------------------------------------------------------
# OpenAPI and authentication
# ---------------------------------------------------------------------------

def test_openapi_includes_communication_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    for expected in (
        "/api/v1/simulated-calls",
        "/api/v1/simulated-calls/{call_id}",
        "/api/v1/simulated-calls/{call_id}/cancel",
        "/api/v1/me/simulated-calls",
        "/api/v1/me/simulated-calls/{delivery_id}/accept",
        "/api/v1/me/simulated-calls/{delivery_id}/dismiss",
        "/api/v1/me/simulated-calls/{delivery_id}/playback-started",
        "/api/v1/me/simulated-calls/{delivery_id}/complete",
        "/api/v1/messages",
        "/api/v1/messages/{message_id}/read",
        "/api/v1/teacher/classes/{class_id}/progress",
        "/api/v1/teacher/classes/{class_id}/tasks",
        "/api/v1/teacher/classes/{class_id}/resources",
        "/api/v1/teacher/reviews",
        "/api/v1/teacher/reviews/{review_id}/resolve",
        "/api/v1/parent/children",
        "/api/v1/parent/children/{student_id}/progress",
        "/api/v1/parent/children/{student_id}/reports",
        "/api/v1/parent/communication-preferences",
    ):
        assert expected in paths, expected


def test_missing_authentication_rejected(client):
    response = client.post(
        "/api/v1/simulated-calls",
        json={"recipient_ids": [STUDENT_AARAV], "title": "T", "transcript": "X"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    messages = client.get("/api/v1/messages")
    assert messages.status_code == 401


# ---------------------------------------------------------------------------
# Call creation rules
# ---------------------------------------------------------------------------

def test_teacher_creates_call_for_assigned_student_and_linked_parent(client, fresh_repository):
    response = _create_call(client, RAO, [STUDENT_AARAV, PARENT_RAJESH])
    assert response.status_code == 201
    body = response.json()
    assert body["sender_id"] == TEACHER_RAO
    assert set(body["recipient_ids"]) == {STUDENT_AARAV, PARENT_RAJESH}
    assert body["status"] == "active"
    assert body["deduplicated"] is False
    assert len(body["deliveries"]) == 2
    assert {d["state"] for d in body["deliveries"]} == {"scheduled"}

    from models.common import AuditEntry

    audits = fresh_repository.find(AuditEntry, action="simulated_call.create")
    assert len(audits) == 1
    assert audits[0].details == {"recipient_count": 2}
    assert "transcript" not in audits[0].details


def test_student_cannot_create_teacher_call(client):
    response = _create_call(client, AARAV, [STUDENT_AARAV])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_teacher_call_to_unassigned_student_forbidden(client):
    response = _create_call(client, RAO, [STUDENT_MEERA])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_ai_agent_sender_requires_admin(client):
    as_teacher = _create_call(
        client, RAO, [STUDENT_AARAV], sender_type="ai_agent"
    )
    assert as_teacher.status_code == 403

    as_admin = _create_call(
        client, ADMIN, [STUDENT_AARAV], sender_type="ai_agent"
    )
    assert as_admin.status_code == 201
    assert as_admin.json()["sender_type"] == "ai_agent"


def test_unknown_or_unsupported_recipient_rejected(client):
    response = _create_call(client, RAO, ["ghost_user"])
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    teacher_recipient = _create_call(client, RAO, [TEACHER_RAO])
    assert teacher_recipient.status_code == 422


def test_empty_title_or_transcript_rejected(client):
    assert _create_call(client, RAO, [STUDENT_AARAV], title="  ").status_code == 422
    assert (
        _create_call(client, RAO, [STUDENT_AARAV], transcript="").status_code == 422
    )


def test_syllabus_context_validated_on_creation(client):
    bad = _create_call(
        client,
        RAO,
        [STUDENT_AARAV],
        topic_id=TOPIC_KINETIC_ENERGY,
        subject_id=SUBJECT_CHEMISTRY,
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"

    good = _create_call(
        client, RAO, [STUDENT_AARAV], topic_id=TOPIC_KINETIC_ENERGY
    )
    assert good.status_code == 201
    assert good.json()["topic_id"] == TOPIC_KINETIC_ENERGY
    assert good.json()["syllabus_id"] == SYLLABUS_ID


def test_speech_asset_must_exist_and_be_owned_by_sender(client, fresh_repository):
    from models.speech import SpeechAsset

    fresh_repository.put(
        SpeechAsset(
            id="speech_rao_1",
            owner_id=TEACHER_RAO,
            source_type="transcript",
            transcript="hello",
            content_hash="abc",
            media_storage_name="media/mock.wav",
        )
    )
    ok = _create_call(
        client, RAO, [STUDENT_AARAV], speech_asset_id="speech_rao_1"
    )
    assert ok.status_code == 201
    assert ok.json()["speech_asset_id"] == "speech_rao_1"

    missing = _create_call(
        client, RAO, [STUDENT_AARAV], speech_asset_id="speech_missing"
    )
    assert missing.status_code == 404

    fresh_repository.put(
        SpeechAsset(
            id="speech_aarav_1",
            owner_id=STUDENT_AARAV,
            source_type="transcript",
            transcript="hi",
            content_hash="def",
            media_storage_name="media/mock2.wav",
        )
    )
    foreign = _create_call(
        client, RAO, [STUDENT_AARAV], speech_asset_id="speech_aarav_1"
    )
    assert foreign.status_code == 404


def test_quiet_hours_enforced_via_parent_preferences(client):
    hour = datetime.now().hour
    put = client.put(
        "/api/v1/parent/communication-preferences",
        json={
            "quiet_hours_enabled": True,
            "quiet_hours_start": hour,
            "quiet_hours_end": (hour + 1) % 24,
        },
        headers=RAJESH,
    )
    assert put.status_code == 200

    response = _create_call(client, RAO, [STUDENT_AARAV, PARENT_RAJESH])
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["message"] == "Quiet hours are active for one or more recipients."
    assert error["details"]["recipients"] == [PARENT_RAJESH]


def test_deduplication_returns_existing_active_call(client):
    first = _create_call(client, RAO, [STUDENT_AARAV, PARENT_RAJESH])
    assert first.status_code == 201
    first_id = first.json()["id"]

    second = _create_call(client, RAO, [PARENT_RAJESH, STUDENT_AARAV])
    assert second.status_code == 200
    body = second.json()
    assert body["id"] == first_id
    assert body["deduplicated"] is True
    assert body["deduplicated_from"] == first_id

    # A different transcript is a new call.
    third = _create_call(
        client, RAO, [STUDENT_AARAV], transcript="Different announcement."
    )
    assert third.status_code == 201
    assert third.json()["id"] != first_id


def test_frequency_limit_per_sender(client):
    from core.config import get_settings

    settings = get_settings()
    original = settings.max_simulated_calls_per_day
    object.__setattr__(settings, "max_simulated_calls_per_day", 1)
    try:
        first = _create_call(client, RAO, [STUDENT_AARAV])
        assert first.status_code == 201
        second = _create_call(
            client, RAO, [STUDENT_AARAV], transcript="Another announcement."
        )
        assert second.status_code == 429
        assert second.json()["error"]["code"] == "RATE_LIMITED"
    finally:
        object.__setattr__(settings, "max_simulated_calls_per_day", original)


def test_call_creation_idempotency_key(client):
    body = {
        "recipient_ids": [STUDENT_AARAV],
        "title": "Idempotent call",
        "transcript": "Same body, same key.",
    }
    first = client.post(
        "/api/v1/simulated-calls", json=body, headers={**RAO, "Idempotency-Key": "call-key-1"}
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/simulated-calls", json=body, headers={**RAO, "Idempotency-Key": "call-key-1"}
    )
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    conflict = client.post(
        "/api/v1/simulated-calls",
        json={**body, "transcript": "Changed."},
        headers={**RAO, "Idempotency-Key": "call-key-1"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


# ---------------------------------------------------------------------------
# Delivery state machine
# ---------------------------------------------------------------------------

def _create_and_fetch(client, recipients=None):
    recipients = recipients or [STUDENT_AARAV, PARENT_RAJESH]
    created = _create_call(client, RAO, recipients)
    assert created.status_code == 201
    return created.json()


def test_recipient_accepts_starts_playback_and_completes(client, fresh_repository):
    call = _create_and_fetch(client)
    delivery_id = _delivery_id_for(call, STUDENT_AARAV)

    accepted = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/accept", headers=AARAV
    )
    assert accepted.status_code == 200
    assert accepted.json()["state"] == "accepted"
    assert accepted.json()["event_version"] == 1

    playing = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/playback-started", headers=AARAV
    )
    assert playing.status_code == 200
    assert playing.json()["state"] == "playing"
    assert playing.json()["event_version"] == 2

    completed = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/complete", headers=AARAV
    )
    assert completed.status_code == 200
    assert completed.json()["state"] == "completed"
    assert completed.json()["event_version"] == 3

    # Completing again is idempotent: no version bump, still 200.
    again = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/complete", headers=AARAV
    )
    assert again.status_code == 200
    assert again.json()["state"] == "completed"
    assert again.json()["event_version"] == 3

    from models.communication import Message, MessageKind

    history = fresh_repository.first(
        Message,
        recipient_id=STUDENT_AARAV,
        kind=MessageKind.call_history,
        title="Call completed: Physics revision plan",
    )
    assert history is not None
    assert history.call_id == call["id"]
    assert history.delivery_id == delivery_id


def test_dismiss_creates_call_history_message(client, fresh_repository):
    call = _create_and_fetch(client)
    delivery_id = _delivery_id_for(call, PARENT_RAJESH)

    dismissed = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/dismiss", headers=RAJESH
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["state"] == "dismissed"

    from models.communication import Message, MessageKind

    messages = fresh_repository.find(
        Message,
        recipient_id=PARENT_RAJESH,
        kind=MessageKind.call_history,
        delivery_id=delivery_id,
    )
    assert len(messages) == 1
    assert messages[0].title == "Call dismissed: Physics revision plan"
    assert messages[0].call_id == call["id"]


def test_invalid_state_transitions_rejected(client):
    call = _create_and_fetch(client)
    delivery_id = _delivery_id_for(call, STUDENT_AARAV)

    # playback-started requires accepted.
    early = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/playback-started", headers=AARAV
    )
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    # complete requires playing.
    client.post(f"/api/v1/me/simulated-calls/{delivery_id}/accept", headers=AARAV)
    too_early = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/complete", headers=AARAV
    )
    assert too_early.status_code == 409

    client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/playback-started", headers=AARAV
    )
    client.post(f"/api/v1/me/simulated-calls/{delivery_id}/complete", headers=AARAV)

    # accept from completed is invalid.
    late = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/accept", headers=AARAV
    )
    assert late.status_code == 409
    assert late.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_recipient_cannot_mutate_another_recipients_delivery(client):
    call = _create_and_fetch(client)
    aarav_delivery = _delivery_id_for(call, STUDENT_AARAV)

    response = client.post(
        f"/api/v1/me/simulated-calls/{aarav_delivery}/accept", headers=RAJESH
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_cancel_affects_only_scheduled_deliveries(client):
    call = _create_and_fetch(client)

    cancelled = client.post(
        f"/api/v1/simulated-calls/{call['id']}/cancel", headers=RAO
    )
    assert cancelled.status_code == 200
    assert {d["state"] for d in cancelled.json()["deliveries"]} == {"cancelled"}
    assert cancelled.json()["status"] == "cancelled"

    # Accepting after cancel is an invalid transition.
    aarav_delivery = _delivery_id_for(call, STUDENT_AARAV)
    accept = client.post(
        f"/api/v1/me/simulated-calls/{aarav_delivery}/accept", headers=AARAV
    )
    assert accept.status_code == 409

    # A second cancel is a documented no-op returning the current state.
    again = client.post(
        f"/api/v1/simulated-calls/{call['id']}/cancel", headers=RAO
    )
    assert again.status_code == 200
    assert {d["state"] for d in again.json()["deliveries"]} == {"cancelled"}


def test_cancel_hides_other_teachers_calls(client):
    call = _create_and_fetch(client)
    other = auth_headers("teacher_other", "teacher", "Other Teacher")
    response = client.post(
        f"/api/v1/simulated-calls/{call['id']}/cancel", headers=other
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Call and delivery visibility
# ---------------------------------------------------------------------------

def test_list_calls_limited_to_sender_or_admin(client):
    _create_and_fetch(client)

    as_teacher = client.get("/api/v1/simulated-calls", headers=RAO)
    assert as_teacher.status_code == 200
    assert len(as_teacher.json()["items"]) == 1

    as_admin = client.get("/api/v1/simulated-calls", headers=ADMIN)
    assert as_admin.status_code == 200
    assert len(as_admin.json()["items"]) == 1

    as_student = client.get("/api/v1/simulated-calls", headers=AARAV)
    assert as_student.status_code == 403


def test_get_call_visibility_rules(client):
    call = _create_and_fetch(client)

    sender = client.get(f"/api/v1/simulated-calls/{call['id']}", headers=RAO)
    assert sender.status_code == 200

    recipient = client.get(f"/api/v1/simulated-calls/{call['id']}", headers=AARAV)
    assert recipient.status_code == 200
    # Recipients see only their own delivery.
    assert len(recipient.json()["deliveries"]) == 1
    assert recipient.json()["deliveries"][0]["recipient_id"] == STUDENT_AARAV

    outsider = client.get(f"/api/v1/simulated-calls/{call['id']}", headers=MEERA)
    assert outsider.status_code == 404


def test_me_simulated_calls_returns_only_own_deliveries(client):
    _create_and_fetch(client)

    aarav = client.get("/api/v1/me/simulated-calls", headers=AARAV)
    assert aarav.status_code == 200
    items = aarav.json()["items"]
    assert len(items) == 1
    assert items[0]["sender_id"] == TEACHER_RAO
    assert items[0]["title"] == "Physics revision plan"
    assert items[0]["state"] == "scheduled"

    rajesh = client.get("/api/v1/me/simulated-calls", headers=RAJESH)
    assert len(rajesh.json()["items"]) == 1

    meera = client.get("/api/v1/me/simulated-calls", headers=MEERA)
    assert meera.json()["items"] == []


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

def test_messages_list_filter_and_read(client):
    rajesh_messages = client.get("/api/v1/messages", headers=RAJESH)
    assert rajesh_messages.status_code == 200
    rajesh_ids = {m["id"] for m in rajesh_messages.json()["items"]}
    assert "msg_seed_1" in rajesh_ids
    assert "msg_seed_2" not in rajesh_ids

    unread = client.get("/api/v1/messages?unread=true", headers=AARAV)
    assert unread.status_code == 200
    unread_ids = {m["id"] for m in unread.json()["items"]}
    assert {"msg_seed_2", "msg_seed_3"} <= unread_ids

    read = client.post("/api/v1/messages/msg_seed_2/read", headers=AARAV)
    assert read.status_code == 200
    assert read.json()["read"] is True
    assert read.json()["read_at"] is not None

    # Reading again is idempotent.
    again = client.post("/api/v1/messages/msg_seed_2/read", headers=AARAV)
    assert again.status_code == 200
    assert again.json()["read_at"] == read.json()["read_at"]

    remaining = client.get("/api/v1/messages?unread=true", headers=AARAV)
    remaining_ids = {m["id"] for m in remaining.json()["items"]}
    assert "msg_seed_2" not in remaining_ids
    assert "msg_seed_3" in remaining_ids


def test_message_read_forbidden_for_other_users(client):
    response = client.post("/api/v1/messages/msg_seed_2/read", headers=RAJESH)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Teacher endpoints
# ---------------------------------------------------------------------------

def test_teacher_class_progress(client):
    response = client.get(
        f"/api/v1/teacher/classes/{CLASS_12A}/progress", headers=RAO
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    summary = items[0]
    assert summary["student_id"] == STUDENT_AARAV
    assert summary["name"] == "Aarav Sharma"
    # task_seed_3 completed the Moment of Inertia topic (1 of 10 topics).
    assert summary["topics_covered"] == 1
    assert summary["percent"] == 10.0


def test_teacher_class_progress_other_teacher_hidden(client):
    other = auth_headers("teacher_other", "teacher", "Other Teacher")
    response = client.get(
        f"/api/v1/teacher/classes/{CLASS_12A}/progress", headers=other
    )
    assert response.status_code == 404


def test_teacher_task_creation_for_class(client, fresh_repository):
    response = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/tasks",
        json={
            "title": "Homework: Kinetic Energy",
            "topic_id": TOPIC_KINETIC_ENERGY,
            "student_ids": [STUDENT_AARAV],
        },
        headers=RAO,
    )
    assert response.status_code == 201
    created = response.json()["created"]
    assert created == [{"student_id": STUDENT_AARAV, "task_id": created[0]["task_id"]}]

    from models.planner import PlannerTask, TaskSource

    task = fresh_repository.get(PlannerTask, created[0]["task_id"])
    assert task.student_id == STUDENT_AARAV
    assert task.locked is True
    assert task.locked_by == TEACHER_RAO
    assert task.source == TaskSource.teacher
    assert task.created_by == TEACHER_RAO
    assert set(task.teacher_fields) == {
        "title",
        "scheduled_date",
        "duration_minutes",
        "locked",
        "teacher_fields",
    }
    assert task.scheduled_date == date.today() + timedelta(days=1)
    assert task.duration_minutes == 45
    assert task.task_type == "homework"
    assert task.topic_id == TOPIC_KINETIC_ENERGY
    assert task.syllabus_id == SYLLABUS_ID
    assert task.subject_id == SUBJECT_PHYSICS

    from models.common import AuditEntry

    audit = fresh_repository.first(AuditEntry, action="teacher.task.create")
    assert audit is not None


def test_teacher_task_creation_defaults_to_whole_class(client, fresh_repository):
    response = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/tasks",
        json={"title": "Class-wide assignment"},
        headers=RAO,
    )
    assert response.status_code == 201
    created = response.json()["created"]
    assert {c["student_id"] for c in created} == {STUDENT_AARAV}


def test_teacher_task_creation_rejects_students_outside_class(client):
    response = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/tasks",
        json={"title": "Nope", "student_ids": [STUDENT_MEERA]},
        headers=RAO,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_parent_cannot_create_teacher_tasks(client):
    response = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/tasks",
        json={"title": "Sneaky"},
        headers=RAJESH,
    )
    assert response.status_code == 403


def test_teacher_task_creation_idempotency_key(client):
    body = {"title": "Idempotent task"}
    first = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/tasks",
        json=body,
        headers={**RAO, "Idempotency-Key": "task-key-1"},
    )
    assert first.status_code == 201
    second = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/tasks",
        json=body,
        headers={**RAO, "Idempotency-Key": "task-key-1"},
    )
    assert second.status_code == 201
    assert second.json() == first.json()


def test_teacher_resource_share_creates_class_scoped_note(client, fresh_repository):
    response = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/resources",
        json={"title": "Rotational Motion guide", "body": "Key formulas inside."},
        headers=RAO,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["scope"] == "class"
    assert body["class_id"] == CLASS_12A

    from models.notes import Note

    note = fresh_repository.get(Note, body["note_id"])
    assert note.owner_id == TEACHER_RAO
    assert note.title == "Rotational Motion guide"
    assert note.share_scope.level == "class"
    assert note.share_scope.audience == [CLASS_12A]
    assert note.source == "manual"


def test_teacher_resource_share_existing_note(client, fresh_repository):
    from models.notes import Note

    fresh_repository.put(
        Note(id="note_rao_1", owner_id=TEACHER_RAO, title="Teacher note", body="B")
    )
    response = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/resources",
        json={"note_id": "note_rao_1"},
        headers=RAO,
    )
    assert response.status_code == 201
    assert response.json()["note_id"] == "note_rao_1"

    note = fresh_repository.get(Note, "note_rao_1")
    assert note.share_scope.level == "class"
    assert note.share_scope.audience == [CLASS_12A]

    other = auth_headers("teacher_other", "teacher", "Other Teacher")
    forbidden = client.post(
        f"/api/v1/teacher/classes/{CLASS_12A}/resources",
        json={"note_id": "note_rao_1"},
        headers=other,
    )
    assert forbidden.status_code == 404


def _seed_review_scan(repo, scan_id, result_id, owner):
    from models.scans import Scan, ScanIntent, ScanResult, ScanStatus

    repo.put(
        Scan(
            id=scan_id,
            owner_id=owner,
            intent=ScanIntent.solve,
            status=ScanStatus.executed,
        )
    )
    repo.put(
        ScanResult(
            id=result_id,
            scan_id=scan_id,
            intent=ScanIntent.solve,
            verification_status="teacher_review_required",
        )
    )


def test_teacher_reviews_and_resolve_flow(client, fresh_repository):
    _seed_review_scan(fresh_repository, "scan_aarav_1", "sr_aarav_1", STUDENT_AARAV)
    _seed_review_scan(fresh_repository, "scan_meera_1", "sr_meera_1", STUDENT_MEERA)

    reviews = client.get("/api/v1/teacher/reviews", headers=RAO)
    assert reviews.status_code == 200
    reviews_by_id = {r["review_id"]: r for r in reviews.json()["items"]}
    assert "review_sr_aarav_1" in reviews_by_id
    assert "review_sr_meera_1" not in reviews_by_id
    review = reviews_by_id["review_sr_aarav_1"]
    assert review["kind"] == "scan_answer"
    assert review["student_id"] == STUDENT_AARAV
    assert review["scan_id"] == "scan_aarav_1"
    assert review["verification_status"] == "teacher_review_required"

    resolution = "accepted_with_correction"
    resolved = client.post(
        f"/api/v1/teacher/reviews/review_sr_aarav_1/resolve",
        json={"resolution": resolution, "correction": "Fix step 2."},
        headers=RAO,
    )
    assert resolved.status_code == 200
    assert resolved.json()["review_id"] == "review_sr_aarav_1"
    assert resolved.json()["resolved"] is True
    assert resolved.json()["resolved_at"] is not None

    # The review is gone from the pending list.
    after = client.get("/api/v1/teacher/reviews", headers=RAO)
    assert "review_sr_aarav_1" not in {
        r["review_id"] for r in after.json()["items"]
    }

    # The audit entry records resolution length only (never correction text).
    from models.common import AuditEntry

    entry = fresh_repository.first(
        AuditEntry, action="teacher.review.resolve", resource_id="sr_aarav_1"
    )
    assert entry is not None
    assert entry.details == {"resolution_length": len(resolution)}
    assert "correction" not in entry.details
    assert "Fix step 2" not in str(entry.details)

    # Resolving again is 404 (already resolved).
    again = client.post(
        f"/api/v1/teacher/reviews/review_sr_aarav_1/resolve",
        json={"resolution": "again"},
        headers=RAO,
    )
    assert again.status_code == 404


def test_teacher_review_resolution_hidden_for_other_teachers(client, fresh_repository):
    _seed_review_scan(fresh_repository, "scan_aarav_1", "sr_aarav_1", STUDENT_AARAV)
    other = auth_headers("teacher_other", "teacher", "Other Teacher")
    response = client.post(
        f"/api/v1/teacher/reviews/review_sr_aarav_1/resolve",
        json={"resolution": "accepted"},
        headers=other,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Parent endpoints
# ---------------------------------------------------------------------------

def test_parent_children_lists_linked_children(client):
    response = client.get("/api/v1/parent/children", headers=RAJESH)
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    child = items[0]
    assert child["student_id"] == STUDENT_AARAV
    assert child["name"] == "Aarav Sharma"
    assert child["target_exam"] == "JEE Main 2027"
    assert child["target_year"] == 2027
    assert child["percent"] == 10.0


def test_parent_child_progress_read_only_and_linked_only(client):
    ok = client.get(
        f"/api/v1/parent/children/{STUDENT_AARAV}/progress", headers=RAJESH
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["student_id"] == STUDENT_AARAV
    assert body["topics_covered"] == 1
    assert body["percent"] == 10.0

    denied = client.get(
        f"/api/v1/parent/children/{STUDENT_MEERA}/progress", headers=RAJESH
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"


def test_parent_child_report_from_persisted_task_state(client):
    response = client.get(
        f"/api/v1/parent/children/{STUDENT_AARAV}/reports", headers=RAJESH
    )
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == STUDENT_AARAV
    assert body["period_days"] == 7
    assert body["generated_at"] is not None
    assert body["tasks_total"] == 3
    assert body["tasks_completed"] == 1
    assert body["completion_percent"] == 33.3
    assert body["minutes_planned"] == 165
    assert body["minutes_completed"] == 55
    per_subject = {s["subject_id"]: s for s in body["per_subject"]}
    assert per_subject[SUBJECT_PHYSICS]["tasks_total"] == 2
    assert per_subject[SUBJECT_PHYSICS]["tasks_completed"] == 1
    assert per_subject[SUBJECT_CHEMISTRY]["tasks_total"] == 1
    assert per_subject[SUBJECT_CHEMISTRY]["tasks_completed"] == 0


def test_parent_communication_preferences_roundtrip(client):
    prefs = client.get("/api/v1/parent/communication-preferences", headers=RAJESH)
    assert prefs.status_code == 200
    assert prefs.json()["user_id"] == PARENT_RAJESH

    updated = client.put(
        "/api/v1/parent/communication-preferences",
        json={
            "quiet_hours_enabled": True,
            "quiet_hours_start": 22,
            "quiet_hours_end": 6,
            "max_calls_per_day": 3,
            "allow_ai_calls": False,
        },
        headers=RAJESH,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["quiet_hours_start"] == 22
    assert body["quiet_hours_end"] == 6
    assert body["max_calls_per_day"] == 3
    assert body["allow_ai_calls"] is False

    invalid = client.put(
        "/api/v1/parent/communication-preferences",
        json={"quiet_hours_start": 25},
        headers=RAJESH,
    )
    assert invalid.status_code == 422
