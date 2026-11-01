"""
Permission and Cross-Cutting API Tests

Implements the section 21.2 permission matrix and general contract checks
(21.1): OpenAPI completeness, authentication enforcement, the common error
envelope, pagination limits, idempotency, and optimistic concurrency.

Policy under test:
- Students can access only their own records (cross-student -> 404).
- Mrs. Rao reaches Aarav only through the assigned class relationship.
- Rajesh (parent) has read-only access to linked-child progress.
- Students cannot create teacher/AI simulated calls (403).
- Speech assets and playback URLs enforce ownership.
"""

import tests.conftest as c


# ---------------------------------------------------------------------------
# 21.1 General
# ---------------------------------------------------------------------------

REQUIRED_ROUTES = {
    "GET": [
        "/api/v1/syllabi",
        "/api/v1/syllabi/{syllabus_id}",
        "/api/v1/syllabi/{syllabus_id}/subjects",
        "/api/v1/subjects/{subject_id}/chapters",
        "/api/v1/chapters/{chapter_id}/topics",
        "/api/v1/me/syllabus-profile",
        "/api/v1/me/syllabus-progress",
        "/api/v1/planner/today",
        "/api/v1/planner/tasks",
        "/api/v1/planner/tasks/{task_id}",
        "/api/v1/planner/generation-jobs/{job_id}",
        "/api/v1/revision/due",
        "/api/v1/notes",
        "/api/v1/notes/{note_id}",
        "/api/v1/notes/{note_id}/versions",
        "/api/v1/mindmaps",
        "/api/v1/mindmaps/{map_id}",
        "/api/v1/mindmaps/{map_id}/revisions",
        "/api/v1/scans/{scan_id}",
        "/api/v1/scans/{scan_id}/ocr",
        "/api/v1/scans/{scan_id}/result",
        "/api/v1/speech/{speech_asset_id}",
        "/api/v1/speech/{speech_asset_id}/playback-url",
        "/api/v1/simulated-calls",
        "/api/v1/simulated-calls/{call_id}",
        "/api/v1/me/simulated-calls",
        "/api/v1/messages",
        "/api/v1/teacher/classes/{class_id}/progress",
        "/api/v1/teacher/reviews",
        "/api/v1/parent/children",
        "/api/v1/parent/children/{student_id}/progress",
        "/api/v1/parent/children/{student_id}/reports",
        "/api/v1/parent/communication-preferences",
    ],
    "POST": [
        "/api/v1/teacher/syllabus-templates",
        "/api/v1/teacher/syllabus-templates/{template_id}/publish",
        "/api/v1/planner/tasks",
        "/api/v1/planner/tasks/{task_id}/complete",
        "/api/v1/planner/tasks/{task_id}/reschedule",
        "/api/v1/planner/generate",
        "/api/v1/planner/replan",
        "/api/v1/study-sessions",
        "/api/v1/revision/{revision_id}/complete",
        "/api/v1/notes",
        "/api/v1/notes/{note_id}/restore",
        "/api/v1/notes/{note_id}/attachments",
        "/api/v1/notes/{note_id}/links",
        "/api/v1/notes/{note_id}/export",
        "/api/v1/notes/{note_id}/share",
        "/api/v1/notes/{note_id}/ai-actions",
        "/api/v1/mindmaps",
        "/api/v1/mindmaps/{map_id}/nodes",
        "/api/v1/mindmaps/{map_id}/edges",
        "/api/v1/mindmaps/{map_id}/generate",
        "/api/v1/mindmaps/{map_id}/regenerate-branch",
        "/api/v1/mindmaps/{map_id}/export",
        "/api/v1/scans",
        "/api/v1/scans/{scan_id}/pages",
        "/api/v1/scans/{scan_id}/process",
        "/api/v1/scans/{scan_id}/execute",
        "/api/v1/scans/{scan_id}/save-note",
        "/api/v1/scans/{scan_id}/create-mindmap",
        "/api/v1/scans/{scan_id}/schedule-revision",
        "/api/v1/speech",
        "/api/v1/simulated-calls",
        "/api/v1/simulated-calls/{call_id}/cancel",
        "/api/v1/me/simulated-calls/{delivery_id}/accept",
        "/api/v1/me/simulated-calls/{delivery_id}/dismiss",
        "/api/v1/me/simulated-calls/{delivery_id}/playback-started",
        "/api/v1/me/simulated-calls/{delivery_id}/complete",
        "/api/v1/messages/{message_id}/read",
        "/api/v1/teacher/classes/{class_id}/tasks",
        "/api/v1/teacher/classes/{class_id}/resources",
        "/api/v1/teacher/reviews/{review_id}/resolve",
    ],
    "PUT": [
        "/api/v1/me/syllabus-profile",
        "/api/v1/scans/{scan_id}/ocr-confirmation",
        "/api/v1/parent/communication-preferences",
    ],
    "PATCH": [
        "/api/v1/planner/tasks/{task_id}",
        "/api/v1/study-sessions/{session_id}",
        "/api/v1/notes/{note_id}",
        "/api/v1/mindmaps/{map_id}",
        "/api/v1/mindmaps/{map_id}/nodes/{node_id}",
    ],
    "DELETE": [
        "/api/v1/notes/{note_id}",
        "/api/v1/notes/{note_id}/links/{linked_note_id}",
        "/api/v1/mindmaps/{map_id}",
        "/api/v1/mindmaps/{map_id}/nodes/{node_id}",
        "/api/v1/mindmaps/{map_id}/edges/{edge_id}",
    ],
}


def test_openapi_includes_all_required_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    missing = []
    for method, routes in REQUIRED_ROUTES.items():
        for route in routes:
            if route not in paths or method.lower() not in paths[route]:
                missing.append(f"{method} {route}")
    assert not missing, f"Missing routes: {missing}"


def test_authentication_required_across_domains(client):
    for method, url in [
        ("GET", "/api/v1/notes"),
        ("GET", "/api/v1/planner/today"),
        ("GET", "/api/v1/mindmaps"),
        ("POST", "/api/v1/scans"),
        ("POST", "/api/v1/speech"),
        ("GET", "/api/v1/me/simulated-calls"),
        ("GET", "/api/v1/messages"),
        ("GET", "/api/v1/parent/children"),
    ]:
        response = client.request(method, url)
        assert response.status_code == 401, url
        assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED", url


def test_error_envelope_shape(client):
    response = client.get("/api/v1/syllabi/syl_missing", headers=c.auth_headers(c.STUDENT_AARAV))
    assert response.status_code == 404
    error = response.json()["error"]
    assert set(error.keys()) == {"code", "message", "details", "request_id"}
    assert error["code"] == "NOT_FOUND"
    assert error["request_id"].startswith("req_")
    assert "X-Request-Id" in response.headers


def test_validation_error_envelope(client):
    response = client.post(
        "/api/v1/planner/tasks",
        json={"title": "", "duration_minutes": 0},
        headers=c.auth_headers(c.STUDENT_AARAV),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_pagination_limit_cap(client):
    response = client.get("/api/v1/notes?limit=500", headers=c.auth_headers(c.STUDENT_AARAV))
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_idempotency_conflict_code(client):
    headers = c.auth_headers(c.STUDENT_AARAV)
    key = "perm-idem-1"
    body = {"title": "Idem note", "body": "x"}
    first = client.post("/api/v1/notes", json=body, headers={**headers, "Idempotency-Key": key})
    assert first.status_code == 201
    conflict = client.post(
        "/api/v1/notes", json={"title": "Other"}, headers={**headers, "Idempotency-Key": key}
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_optimistic_concurrency_conflict(client):
    headers = c.auth_headers(c.STUDENT_AARAV)
    note = client.post("/api/v1/notes", json={"title": "v1"}, headers=headers).json()
    stale = client.patch(
        f"/api/v1/notes/{note['id']}", json={"title": "v2", "version": 99}, headers=headers
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_CONFLICT"


# ---------------------------------------------------------------------------
# 21.2 Permissions
# ---------------------------------------------------------------------------

AARAV = c.auth_headers(c.STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = c.auth_headers(c.STUDENT_MEERA, "student", "Meera Iyer")
RAO = c.auth_headers(c.TEACHER_RAO, "teacher", "Mrs. Rao")
RAJESH = c.auth_headers(c.PARENT_RAJESH, "parent", "Rajesh Sharma")


def test_aarav_reads_own_note(client):
    response = client.get("/api/v1/notes/note_seed_1", headers=AARAV)
    assert response.status_code == 200
    assert response.json()["owner_id"] == c.STUDENT_AARAV


def test_aarav_cannot_read_meeras_note(client):
    response = client.get("/api/v1/notes/note_seed_meera", headers=AARAV)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_aarav_cannot_read_meeras_scan(client):
    response = client.get("/api/v1/scans/scan_seed_meera", headers=AARAV)
    assert response.status_code == 404


def test_aarav_cannot_create_teacher_simulated_call(client):
    response = client.post(
        "/api/v1/simulated-calls",
        json={
            "recipient_ids": [c.STUDENT_AARAV],
            "title": "Fake",
            "transcript": "hello",
        },
        headers=AARAV,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_rao_accesses_assigned_class_progress(client):
    response = client.get(
        f"/api/v1/teacher/classes/{c.CLASS_12A}/progress", headers=RAO
    )
    assert response.status_code == 200
    rows = response.json()["items"]
    student_ids = [row["student_id"] for row in rows]
    assert c.STUDENT_AARAV in student_ids


def test_rao_cannot_access_unassigned_student(client):
    response = client.get(
        f"/api/v1/me/syllabus-progress?student_id={c.STUDENT_MEERA}", headers=RAO
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_rajesh_reads_aarav_progress(client):
    response = client.get(
        f"/api/v1/parent/children/{c.STUDENT_AARAV}/progress", headers=RAJESH
    )
    assert response.status_code == 200
    assert response.json()["student_id"] == c.STUDENT_AARAV


def test_rajesh_cannot_modify_aaravs_tasks(client):
    patch = client.patch(
        "/api/v1/planner/tasks/task_seed_1",
        json={"title": "hacked", "version": 1},
        headers=RAJESH,
    )
    assert patch.status_code == 403

    complete = client.post("/api/v1/planner/tasks/task_seed_1/complete", headers=RAJESH)
    assert complete.status_code in (403, 404)

    create = client.post(
        "/api/v1/planner/tasks",
        json={"title": "nope", "scheduled_date": "2026-11-02", "duration_minutes": 30},
        headers=RAJESH,
    )
    assert create.status_code == 403


def test_rajesh_cannot_read_other_child_progress(client):
    response = client.get(
        f"/api/v1/parent/children/{c.STUDENT_MEERA}/progress", headers=RAJESH
    )
    assert response.status_code == 403


def test_speech_playback_enforces_ownership(client):
    created = client.post(
        "/api/v1/speech",
        json={"source_type": "transcript", "transcript": "Hello Aarav"},
        headers=AARAV,
    )
    assert created.status_code == 201
    asset_id = created.json()["id"]

    denied = client.get(f"/api/v1/speech/{asset_id}", headers=MEERA)
    assert denied.status_code == 404

    denied_url = client.get(f"/api/v1/speech/{asset_id}/playback-url", headers=MEERA)
    assert denied_url.status_code == 404

    allowed = client.get(f"/api/v1/speech/{asset_id}/playback-url", headers=AARAV)
    assert allowed.status_code == 200
    assert allowed.json()["url"].startswith("/api/v1/speech/")
    assert allowed.json()["is_mock"] is True


def test_cross_student_task_hidden(client):
    response = client.get("/api/v1/planner/tasks/task_seed_meera", headers=AARAV)
    assert response.status_code == 404
