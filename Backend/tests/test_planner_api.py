"""
Planner API Tests

Covers task CRUD with validation, today progress, idempotent completion,
reschedule history, optimistic concurrency, teacher-locked fields,
deterministic generation (non-overlap, warnings), replan preservation rules,
study-session state machine with one-time task completion, and revision items.

Section 21.3 of endpoint_instructions.md.
"""

from datetime import date, timedelta

from tests.conftest import (
    CHAPTER_CHEM_BONDING,
    CHAPTER_WORK_ENERGY,
    PARENT_RAJESH,
    STUDENT_AARAV,
    STUDENT_MEERA,
    SUBJECT_CHEMISTRY,
    SUBJECT_PHYSICS,
    TEACHER_RAO,
    TOPIC_KINETIC_ENERGY,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = auth_headers(STUDENT_MEERA, "student", "Meera Iyer")
RAO = auth_headers(TEACHER_RAO, "teacher", "Mrs. Rao")
RAJESH = auth_headers(PARENT_RAJESH, "parent", "Rajesh Sharma")

TODAY = date.today()
TOMORROW = TODAY + timedelta(days=1)
YESTERDAY = TODAY - timedelta(days=1)


def _task_payload(**overrides):
    payload = {
        "title": "Practice problems",
        "task_type": "practice",
        "scheduled_date": TODAY.isoformat(),
        "duration_minutes": 60,
        "subject_id": SUBJECT_PHYSICS,
        "chapter_id": CHAPTER_WORK_ENERGY,
        "topic_id": TOPIC_KINETIC_ENERGY,
    }
    payload.update(overrides)
    return payload


def _create_task(client, headers, **overrides):
    return client.post("/api/v1/planner/tasks", json=_task_payload(**overrides), headers=headers)


# ---------------------------------------------------------------------------
# OpenAPI / auth
# ---------------------------------------------------------------------------

def test_openapi_includes_planner_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    for path in (
        "/api/v1/planner/today",
        "/api/v1/planner/tasks",
        "/api/v1/planner/tasks/{task_id}",
        "/api/v1/planner/tasks/{task_id}/complete",
        "/api/v1/planner/tasks/{task_id}/reschedule",
        "/api/v1/planner/generate",
        "/api/v1/planner/replan",
        "/api/v1/planner/generation-jobs/{job_id}",
        "/api/v1/study-sessions",
        "/api/v1/study-sessions/{session_id}",
        "/api/v1/revision/due",
        "/api/v1/revision/{revision_id}/complete",
    ):
        assert path in paths


def test_missing_authentication_rejected(client):
    response = client.get("/api/v1/planner/today")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ---------------------------------------------------------------------------
# Task creation / retrieval / validation
# ---------------------------------------------------------------------------

def test_create_and_retrieve_task(client):
    created = _create_task(client, AARAV, title="Kinetic Energy drill")
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Kinetic Energy drill"
    assert body["student_id"] == STUDENT_AARAV
    assert body["status"] == "pending"
    assert body["version"] == 1
    assert body["source"] == "manual"
    assert body["created_by"] == STUDENT_AARAV
    assert body["topic_id"] == TOPIC_KINETIC_ENERGY
    assert body["scheduled_date"] == TODAY.isoformat()

    fetched = client.get(f"/api/v1/planner/tasks/{body['id']}", headers=AARAV)
    assert fetched.status_code == 200
    assert fetched.json() == body


def test_create_task_validation_failures(client):
    bad_type = _create_task(client, AARAV, task_type="bogus")
    assert bad_type.status_code == 422
    assert bad_type.json()["error"]["code"] == "VALIDATION_ERROR"

    zero_duration = _create_task(client, AARAV, duration_minutes=0)
    assert zero_duration.status_code == 422
    assert zero_duration.json()["error"]["code"] == "VALIDATION_ERROR"

    empty_title = _create_task(client, AARAV, title="")
    assert empty_title.status_code == 422
    assert empty_title.json()["error"]["code"] == "VALIDATION_ERROR"

    wrong_chapter = _create_task(
        client, AARAV, chapter_id=CHAPTER_CHEM_BONDING, subject_id=SUBJECT_CHEMISTRY
    )
    assert wrong_chapter.status_code == 422
    assert wrong_chapter.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"

    unknown_subject = _create_task(client, AARAV, subject_id="sub_biology")
    assert unknown_subject.status_code == 422
    assert unknown_subject.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"


def test_create_task_idempotency(client):
    body = _task_payload(title="Idempotent task")
    key = "planner-create-1"
    first = client.post(
        "/api/v1/planner/tasks", json=body, headers={**AARAV, "Idempotency-Key": key}
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/planner/tasks", json=body, headers={**AARAV, "Idempotency-Key": key}
    )
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    conflict = client.post(
        "/api/v1/planner/tasks",
        json=_task_payload(title="Different"),
        headers={**AARAV, "Idempotency-Key": key},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"

    listed = client.get(
        f"/api/v1/planner/tasks?from={TODAY.isoformat()}&status=pending&limit=100",
        headers=AARAV,
    )
    titles = [t["title"] for t in listed.json()["items"]]
    assert titles.count("Idempotent task") == 1


# ---------------------------------------------------------------------------
# Today / filters / progress
# ---------------------------------------------------------------------------

def test_today_reflects_seeded_tasks(client):
    response = client.get("/api/v1/planner/today", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["date"] == TODAY.isoformat()

    progress = body["progress"]
    assert progress["total"] == 2
    assert progress["completed"] == 0
    assert progress["percent"] == 0.0
    assert progress["minutes_planned"] == 105
    assert progress["minutes_completed"] == 0

    ids = {t["id"] for t in body["tasks"]}
    assert {"task_seed_1", "task_seed_2"} <= ids


def test_task_filters_compose(client):
    physics = _create_task(
        client, AARAV, title="Physics tomorrow", scheduled_date=TOMORROW.isoformat()
    )
    chem = _create_task(
        client,
        AARAV,
        title="Chemistry tomorrow",
        scheduled_date=TOMORROW.isoformat(),
        subject_id=SUBJECT_CHEMISTRY,
        chapter_id=CHAPTER_CHEM_BONDING,
        topic_id=None,
    )
    assert physics.status_code == 201 and chem.status_code == 201

    filtered = client.get(
        f"/api/v1/planner/tasks?from={TOMORROW.isoformat()}"
        f"&status=pending&subjectId={SUBJECT_PHYSICS}",
        headers=AARAV,
    )
    assert filtered.status_code == 200
    items = filtered.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == physics.json()["id"]

    yesterday_only = client.get(
        f"/api/v1/planner/tasks?to={YESTERDAY.isoformat()}", headers=AARAV
    )
    assert yesterday_only.status_code == 200
    assert [t["id"] for t in yesterday_only.json()["items"]] == ["task_seed_3"]

    completed = client.get("/api/v1/planner/tasks?status=completed", headers=AARAV)
    assert completed.status_code == 200
    assert [t["id"] for t in completed.json()["items"]] == ["task_seed_3"]

    bad_status = client.get("/api/v1/planner/tasks?status=bogus", headers=AARAV)
    assert bad_status.status_code == 422
    assert bad_status.json()["error"]["code"] == "VALIDATION_ERROR"

    too_large = client.get("/api/v1/planner/tasks?limit=101", headers=AARAV)
    assert too_large.status_code == 422
    assert too_large.json()["error"]["code"] == "VALIDATION_ERROR"


def test_complete_task_updates_today_progress(client):
    before = client.get("/api/v1/planner/today", headers=AARAV).json()["progress"]
    assert before["completed"] == 0

    done = client.post(
        "/api/v1/planner/tasks/task_seed_1/complete",
        json={"actual_minutes": 50},
        headers=AARAV,
    )
    assert done.status_code == 200
    body = done.json()
    assert body["status"] == "completed"
    assert body["actual_minutes"] == 50
    assert body["completed_at"] is not None
    assert body["version"] == 2

    after = client.get("/api/v1/planner/today", headers=AARAV).json()
    assert after["progress"]["completed"] == 1
    assert after["progress"]["percent"] == 50.0
    assert after["progress"]["minutes_completed"] == 50

    progress = client.get("/api/v1/me/syllabus-progress", headers=AARAV)
    assert progress.status_code == 200
    physics = next(s for s in progress.json()["subjects"] if s["subject_id"] == SUBJECT_PHYSICS)
    assert physics["topics_covered"] == 2  # Moment of Inertia + Kinetic Energy


def test_complete_task_idempotency_key_no_double_count(client):
    key = "complete-key-1"
    headers = {**AARAV, "Idempotency-Key": key}
    first = client.post(
        "/api/v1/planner/tasks/task_seed_1/complete",
        json={"actual_minutes": 50},
        headers=headers,
    )
    assert first.status_code == 200
    second = client.post(
        "/api/v1/planner/tasks/task_seed_1/complete",
        json={"actual_minutes": 50},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json() == first.json()

    today = client.get("/api/v1/planner/today", headers=AARAV).json()["progress"]
    assert today["completed"] == 1
    assert today["minutes_completed"] == 50


def test_complete_task_without_key_is_safe_retry(client):
    first = client.post("/api/v1/planner/tasks/task_seed_1/complete", headers=AARAV)
    assert first.status_code == 200
    second = client.post("/api/v1/planner/tasks/task_seed_1/complete", headers=AARAV)
    assert second.status_code == 200
    assert second.json()["completed_at"] == first.json()["completed_at"]

    done = client.post("/api/v1/planner/tasks/task_seed_2/complete", headers=AARAV)
    assert done.status_code == 200

    today = client.get("/api/v1/planner/today", headers=AARAV).json()["progress"]
    assert today["completed"] == 2
    assert today["minutes_completed"] == 105  # 60 + 45, counted exactly once


# ---------------------------------------------------------------------------
# Reschedule / concurrency / locked fields
# ---------------------------------------------------------------------------

def test_reschedule_records_history(client):
    response = client.post(
        "/api/v1/planner/tasks/task_seed_1/reschedule",
        json={"scheduled_date": TOMORROW.isoformat(), "start_minute": 600, "reason": "Clash"},
        headers=AARAV,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["scheduled_date"] == TOMORROW.isoformat()
    assert body["start_minute"] == 600
    assert body["version"] == 2

    assert len(body["reschedule_history"]) == 1
    entry = body["reschedule_history"][0]
    assert entry["from_date"] == TODAY.isoformat()
    assert entry["from_start"] == 540
    assert entry["to_date"] == TOMORROW.isoformat()
    assert entry["to_start"] == 600
    assert entry["reason"] == "Clash"
    assert entry["moved_by"] == STUDENT_AARAV
    assert entry["at"]


def test_reschedule_completed_task_fails(client):
    response = client.post(
        "/api/v1/planner/tasks/task_seed_3/reschedule",
        json={"scheduled_date": TOMORROW.isoformat()},
        headers=AARAV,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_patch_optimistic_concurrency(client):
    updated = client.patch(
        "/api/v1/planner/tasks/task_seed_2",
        json={"version": 1, "title": "Renamed revision"},
        headers=AARAV,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Renamed revision"
    assert updated.json()["version"] == 2

    stale = client.patch(
        "/api/v1/planner/tasks/task_seed_2",
        json={"version": 1, "title": "Stale write"},
        headers=AARAV,
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_CONFLICT"

    missing_version = client.patch(
        "/api/v1/planner/tasks/task_seed_2", json={"title": "No version"}, headers=AARAV
    )
    assert missing_version.status_code == 422

    invalid_status = client.patch(
        "/api/v1/planner/tasks/task_seed_2",
        json={"version": 2, "status": "completed"},
        headers=AARAV,
    )
    assert invalid_status.status_code == 422


def test_teacher_can_create_task_for_assigned_student(client):
    created = client.post(
        "/api/v1/planner/tasks?student_id=student_aarav",
        json=_task_payload(
            title="Teacher locked drill",
            duration_minutes=30,
            locked=True,
            teacher_fields=["scheduled_date"],
        ),
        headers=RAO,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["student_id"] == STUDENT_AARAV
    assert body["locked"] is True
    assert body["locked_by"] == TEACHER_RAO
    assert body["teacher_fields"] == ["scheduled_date"]
    assert body["source"] == "teacher"
    assert body["created_by"] == TEACHER_RAO

    # Mrs. Rao is not assigned to Meera.
    denied = client.post(
        "/api/v1/planner/tasks?student_id=student_meera",
        json=_task_payload(title="Nope"),
        headers=RAO,
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    # Teacher can read the assigned student's task.
    fetched = client.get(f"/api/v1/planner/tasks/{body['id']}", headers=RAO)
    assert fetched.status_code == 200


def test_student_cannot_modify_teacher_locked_fields(client):
    created = client.post(
        "/api/v1/planner/tasks?student_id=student_aarav",
        json=_task_payload(title="Locked task", duration_minutes=30, locked=True),
        headers=RAO,
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    locked_change = client.patch(
        f"/api/v1/planner/tasks/{task_id}",
        json={"version": 1, "scheduled_date": TOMORROW.isoformat()},
        headers=AARAV,
    )
    assert locked_change.status_code == 403
    assert locked_change.json()["error"]["code"] == "PERMISSION_DENIED"

    locked_reschedule = client.post(
        f"/api/v1/planner/tasks/{task_id}/reschedule",
        json={"scheduled_date": TOMORROW.isoformat()},
        headers=AARAV,
    )
    assert locked_reschedule.status_code == 403

    # Teachers can reschedule the locked task.
    teacher_reschedule = client.post(
        f"/api/v1/planner/tasks/{task_id}/reschedule",
        json={"scheduled_date": TOMORROW.isoformat(), "reason": "Shifted"},
        headers=RAO,
    )
    assert teacher_reschedule.status_code == 200
    assert teacher_reschedule.json()["scheduled_date"] == TOMORROW.isoformat()


def test_teacher_fields_block_only_listed_fields(client):
    created = client.post(
        "/api/v1/planner/tasks?student_id=student_aarav",
        json=_task_payload(
            title="Partially locked", duration_minutes=30, teacher_fields=["scheduled_date"]
        ),
        headers=RAO,
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    blocked = client.patch(
        f"/api/v1/planner/tasks/{task_id}",
        json={"version": 1, "scheduled_date": TOMORROW.isoformat()},
        headers=AARAV,
    )
    assert blocked.status_code == 403

    allowed = client.patch(
        f"/api/v1/planner/tasks/{task_id}",
        json={"version": 1, "title": "Renamed by student"},
        headers=AARAV,
    )
    assert allowed.status_code == 200
    assert allowed.json()["title"] == "Renamed by student"


# ---------------------------------------------------------------------------
# Generate / replan
# ---------------------------------------------------------------------------

def test_generate_produces_non_overlapping_tasks(client):
    response = client.post("/api/v1/planner/generate", json={"days": 3}, headers=AARAV)
    assert response.status_code == 200
    job = response.json()
    assert job["kind"] == "generate"
    assert job["status"] == "completed"
    assert job["completed_at"] is not None
    assert job["result"]["created_task_ids"]

    fetched = client.get(f"/api/v1/planner/generation-jobs/{job['id']}", headers=AARAV)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == job["id"]

    end = TODAY + timedelta(days=2)
    listed = client.get(
        f"/api/v1/planner/tasks?from={TODAY.isoformat()}&to={end.isoformat()}&limit=100",
        headers=AARAV,
    )
    assert listed.status_code == 200
    by_date = {}
    for task in listed.json()["items"]:
        by_date.setdefault(task["scheduled_date"], []).append(task)

    generated = 0
    for day, tasks in by_date.items():
        intervals = sorted((t["start_minute"], t["start_minute"] + t["duration_minutes"]) for t in tasks)
        for (start_a, end_a), (start_b, end_b) in zip(intervals, intervals[1:]):
            assert end_a <= start_b, f"overlapping tasks on {day}"
    for task in listed.json()["items"]:
        if task["source"] == "generated":
            generated += 1
            assert task["source_id"] == job["id"]
    assert generated == len(job["result"]["created_task_ids"])


def test_generate_idempotent_replay(client):
    key = "gen-key-1"
    headers = {**AARAV, "Idempotency-Key": key}
    first = client.post("/api/v1/planner/generate", json={"days": 3}, headers=headers)
    assert first.status_code == 200
    second = client.post("/api/v1/planner/generate", json={"days": 3}, headers=headers)
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    listed = client.get(
        f"/api/v1/planner/tasks?from={TODAY.isoformat()}&limit=100", headers=AARAV
    )
    generated = [t for t in listed.json()["items"] if t["source"] == "generated"]
    assert len(generated) == len(first.json()["result"]["created_task_ids"])


def test_generate_insufficient_capacity_warns(client):
    update = client.put(
        "/api/v1/me/syllabus-profile",
        json={"version": 1, "availability": {"minutes_per_day": 30, "days_per_week": 6}},
        headers=AARAV,
    )
    assert update.status_code == 200

    response = client.post("/api/v1/planner/generate", json={"days": 2}, headers=AARAV)
    assert response.status_code == 200
    job = response.json()
    assert job["status"] == "completed"
    assert job["warnings"], "expected warnings when topics cannot fit"

    end = TODAY + timedelta(days=1)
    listed = client.get(
        f"/api/v1/planner/tasks?from={TODAY.isoformat()}&to={end.isoformat()}&limit=100",
        headers=AARAV,
    )
    study_tasks = [
        t for t in listed.json()["items"]
        if t["source"] == "generated" and t["title"].startswith("Study:")
    ]
    assert 0 < len(study_tasks) < 7


def test_generate_requires_profile(client):
    stranger = auth_headers("student_new", "student", "New Student")
    response = client.post("/api/v1/planner/generate", json={"days": 2}, headers=stranger)
    assert response.status_code == 404


def test_replan_preserves_locked_and_completed(client):
    # Teacher places a locked task tomorrow; Aarav completes task_seed_1.
    locked = client.post(
        "/api/v1/planner/tasks?student_id=student_aarav",
        json=_task_payload(
            title="Locked commitment",
            scheduled_date=TOMORROW.isoformat(),
            start_minute=600,
            duration_minutes=45,
            locked=True,
        ),
        headers=RAO,
    )
    assert locked.status_code == 201
    locked_id = locked.json()["id"]

    done = client.post("/api/v1/planner/tasks/task_seed_1/complete", headers=AARAV)
    assert done.status_code == 200

    key = "replan-key-1"
    headers = {**AARAV, "Idempotency-Key": key}
    first = client.post(
        "/api/v1/planner/replan", json={"from_date": TODAY.isoformat()}, headers=headers
    )
    assert first.status_code == 200
    job = first.json()
    assert job["kind"] == "replan"
    assert job["status"] == "completed"
    assert "Moved 1 task(s); 3 task(s) preserved." == job["explanation"]

    # Replay returns the original job without re-planning.
    replay = client.post(
        "/api/v1/planner/replan", json={"from_date": TODAY.isoformat()}, headers=headers
    )
    assert replay.status_code == 200
    assert replay.json()["id"] == job["id"]

    # Locked task untouched.
    locked_after = client.get(f"/api/v1/planner/tasks/{locked_id}", headers=AARAV).json()
    assert locked_after["scheduled_date"] == TOMORROW.isoformat()
    assert locked_after["start_minute"] == 600
    assert locked_after["version"] == 1

    # Completed task untouched (completion bumped it to version 2).
    completed = client.get("/api/v1/planner/tasks/task_seed_1", headers=AARAV).json()
    assert completed["status"] == "completed"
    assert completed["start_minute"] == 540
    assert completed["version"] == 2

    # The pending task was re-packed and carries a replan history entry.
    moved = client.get("/api/v1/planner/tasks/task_seed_2", headers=AARAV).json()
    assert moved["start_minute"] == 480
    reasons = [h["reason"] for h in moved["reschedule_history"]]
    assert reasons.count("replan") == 1  # replay did not double-record
    assert moved["reschedule_history"][0]["moved_by"] == STUDENT_AARAV


# ---------------------------------------------------------------------------
# Study sessions
# ---------------------------------------------------------------------------

def test_study_session_lifecycle_and_invalid_transitions(client):
    created = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_1"}, headers=AARAV)
    assert created.status_code == 201
    session = created.json()
    session_id = session["id"]
    assert session["status"] == "not_started"
    assert session["task_id"] == "task_seed_1"

    started = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "start"}, headers=AARAV
    )
    assert started.status_code == 200
    assert started.json()["status"] == "active"
    assert started.json()["started_at"] is not None
    assert len(started.json()["intervals"]) == 1

    paused = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "pause"}, headers=AARAV
    )
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    assert paused.json()["intervals"][0]["ended_at"] is not None

    double_pause = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "pause"}, headers=AARAV
    )
    assert double_pause.status_code == 409
    assert double_pause.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    resumed = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "resume"}, headers=AARAV
    )
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "active"
    assert len(resumed.json()["intervals"]) == 2

    finished = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "finish"}, headers=AARAV
    )
    assert finished.status_code == 200
    body = finished.json()
    assert body["status"] == "finished"
    assert body["finished_at"] is not None

    # Finishing the task bumped its version exactly once.
    task = client.get("/api/v1/planner/tasks/task_seed_1", headers=AARAV).json()
    assert task["status"] == "completed"
    assert task["completed_at"] is not None
    assert task["version"] == 2

    finish_again = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "finish"}, headers=AARAV
    )
    assert finish_again.status_code == 409
    assert finish_again.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    start_finished = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "start"}, headers=AARAV
    )
    assert start_finished.status_code == 409

    bad_action = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "rewind"}, headers=AARAV
    )
    assert bad_action.status_code == 422


def test_session_finish_completes_linked_task_once(client):
    first = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_2"}, headers=AARAV)
    assert first.status_code == 201
    first_id = first.json()["id"]
    client.patch(f"/api/v1/study-sessions/{first_id}", json={"action": "start"}, headers=AARAV)
    done = client.patch(
        f"/api/v1/study-sessions/{first_id}", json={"action": "finish"}, headers=AARAV
    )
    assert done.status_code == 200
    assert done.json()["completion_linked"] is True

    task_after_first = client.get("/api/v1/planner/tasks/task_seed_2", headers=AARAV).json()
    assert task_after_first["status"] == "completed"
    assert task_after_first["version"] == 2

    # A second session on the same task must not complete it again.
    second = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_2"}, headers=AARAV)
    assert second.status_code == 201
    second_id = second.json()["id"]
    client.patch(f"/api/v1/study-sessions/{second_id}", json={"action": "start"}, headers=AARAV)
    finished = client.patch(
        f"/api/v1/study-sessions/{second_id}", json={"action": "finish"}, headers=AARAV
    )
    assert finished.status_code == 200
    assert finished.json()["completion_linked"] is True

    task_after_second = client.get("/api/v1/planner/tasks/task_seed_2", headers=AARAV).json()
    assert task_after_second["status"] == "completed"
    assert task_after_second["version"] == 2  # no duplicate completion


def test_session_create_requires_owned_task(client):
    missing = client.post("/api/v1/study-sessions", json={"task_id": "task_missing"}, headers=AARAV)
    assert missing.status_code == 404

    foreign = client.post(
        "/api/v1/study-sessions", json={"task_id": "task_seed_meera"}, headers=AARAV
    )
    assert foreign.status_code == 404

    denied = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_1"}, headers=RAJESH)
    assert denied.status_code == 403


def test_session_create_idempotency(client):
    key = "session-key-1"
    headers = {**AARAV, "Idempotency-Key": key}
    first = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_1"}, headers=headers)
    assert first.status_code == 201
    second = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_1"}, headers=headers)
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]


def test_session_cross_student_hidden(client):
    created = client.post("/api/v1/study-sessions", json={"task_id": "task_seed_meera"}, headers=MEERA)
    assert created.status_code == 201
    session_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/study-sessions/{session_id}", json={"action": "start"}, headers=AARAV
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Revision items
# ---------------------------------------------------------------------------

def test_revision_due_and_complete(client):
    due = client.get("/api/v1/revision/due", headers=AARAV)
    assert due.status_code == 200
    ids = [item["id"] for item in due.json()["items"]]
    assert "rev_seed_1" in ids

    done = client.post("/api/v1/revision/rev_seed_1/complete", headers=AARAV)
    assert done.status_code == 200
    body = done.json()
    assert body["status"] == "completed"
    assert body["completed_at"] is not None

    # Repeating the completion is a safe no-op.
    again = client.post("/api/v1/revision/rev_seed_1/complete", headers=AARAV)
    assert again.status_code == 200
    assert again.json()["completed_at"] == body["completed_at"]

    due_after = client.get("/api/v1/revision/due", headers=AARAV)
    assert "rev_seed_1" not in [item["id"] for item in due_after.json()["items"]]


# ---------------------------------------------------------------------------
# Permissions / scope
# ---------------------------------------------------------------------------

def test_meera_task_not_visible_to_aarav(client):
    fetched = client.get("/api/v1/planner/tasks/task_seed_meera", headers=AARAV)
    assert fetched.status_code == 404
    assert fetched.json()["error"]["code"] == "NOT_FOUND"

    patched = client.patch(
        "/api/v1/planner/tasks/task_seed_meera",
        json={"version": 1, "title": "Hijack"},
        headers=AARAV,
    )
    assert patched.status_code == 404

    completed = client.post("/api/v1/planner/tasks/task_seed_meera/complete", headers=AARAV)
    assert completed.status_code == 404

    today = client.get(f"/api/v1/planner/today?student_id={STUDENT_MEERA}", headers=AARAV)
    assert today.status_code == 404


def test_parent_read_only_access(client):
    # Rajesh can read his linked child's data...
    today = client.get("/api/v1/planner/today", headers=RAJESH)
    assert today.status_code == 200
    assert today.json()["progress"]["total"] == 2

    task = client.get("/api/v1/planner/tasks/task_seed_1", headers=RAJESH)
    assert task.status_code == 200

    # ...but never modify it.
    created = client.post("/api/v1/planner/tasks", json=_task_payload(), headers=RAJESH)
    assert created.status_code == 403
    assert created.json()["error"]["code"] == "PERMISSION_DENIED"

    patched = client.patch(
        "/api/v1/planner/tasks/task_seed_1", json={"version": 1, "title": "Nope"}, headers=RAJESH
    )
    assert patched.status_code == 403

    rescheduled = client.post(
        "/api/v1/planner/tasks/task_seed_1/reschedule",
        json={"scheduled_date": TOMORROW.isoformat()},
        headers=RAJESH,
    )
    assert rescheduled.status_code == 403

    completed = client.post("/api/v1/planner/tasks/task_seed_1/complete", headers=RAJESH)
    assert completed.status_code == 404

    # Rajesh is not linked to Meera.
    meera_today = client.get(f"/api/v1/planner/today?student_id={STUDENT_MEERA}", headers=RAJESH)
    assert meera_today.status_code == 403


def test_teacher_can_read_assigned_student_today(client):
    response = client.get(f"/api/v1/planner/today?student_id={STUDENT_AARAV}", headers=RAO)
    assert response.status_code == 200
    assert response.json()["progress"]["total"] == 2

    unassigned = client.get(f"/api/v1/planner/today?student_id={STUDENT_MEERA}", headers=RAO)
    assert unassigned.status_code == 403
