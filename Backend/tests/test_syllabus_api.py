"""
Syllabus API Tests

Covers the catalogue, profile updates with optimistic concurrency, progress
calculation from task state, and teacher templates with idempotent publish.
"""

from tests.conftest import (
    STUDENT_AARAV,
    STUDENT_MEERA,
    SUBJECT_PHYSICS,
    SYLLABUS_ID,
    TEACHER_RAO,
    TOPIC_KINETIC_ENERGY,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
RAO = auth_headers(TEACHER_RAO, "teacher", "Mrs. Rao")


def test_openapi_includes_syllabus_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    assert "/api/v1/syllabi" in paths
    assert "/api/v1/me/syllabus-profile" in paths
    assert "/api/v1/me/syllabus-progress" in paths
    assert "/api/v1/teacher/syllabus-templates" in paths


def test_missing_authentication_rejected(client):
    response = client.get("/api/v1/syllabi")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_list_syllabi(client):
    response = client.get("/api/v1/syllabi", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] is None
    ids = [item["id"] for item in body["items"]]
    assert SYLLABUS_ID in ids


def test_get_syllabus_and_subjects(client):
    response = client.get(f"/api/v1/syllabi/{SYLLABUS_ID}", headers=AARAV)
    assert response.status_code == 200
    assert response.json()["version"] == "1.0"

    subjects = client.get(f"/api/v1/syllabi/{SYLLABUS_ID}/subjects", headers=AARAV)
    assert subjects.status_code == 200
    names = {item["name"] for item in subjects.json()["items"]}
    assert {"Physics", "Chemistry", "Mathematics"} == names


def test_chapters_and_topics_hierarchy(client):
    chapters = client.get(f"/api/v1/subjects/{SUBJECT_PHYSICS}/chapters", headers=AARAV)
    assert chapters.status_code == 200
    chapter_ids = {item["id"] for item in chapters.json()["items"]}
    assert "ch_work_energy_power" in chapter_ids

    topics = client.get("/api/v1/chapters/ch_work_energy_power/topics", headers=AARAV)
    assert topics.status_code == 200
    topic_ids = {item["id"] for item in topics.json()["items"]}
    assert TOPIC_KINETIC_ENERGY in topic_ids


def test_unknown_catalogue_ids_return_404(client):
    response = client.get("/api/v1/syllabi/syl_missing", headers=AARAV)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_pagination_limit_enforced(client):
    response = client.get("/api/v1/chapters/ch_rotational_motion/topics?limit=2", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["next_cursor"] is not None

    too_large = client.get("/api/v1/chapters/ch_rotational_motion/topics?limit=101", headers=AARAV)
    assert too_large.status_code == 422
    assert too_large.json()["error"]["code"] == "VALIDATION_ERROR"


def test_get_syllabus_profile(client):
    response = client.get("/api/v1/me/syllabus-profile", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == STUDENT_AARAV
    assert body["syllabus_id"] == SYLLABUS_ID
    assert SUBJECT_PHYSICS in body["subjects"]


def test_update_profile_and_version_conflict(client):
    update = {
        "version": 1,
        "availability": {"minutes_per_day": 240, "days_per_week": 6},
        "preferences": {"buffer_ratio": 0.2},
    }
    response = client.put("/api/v1/me/syllabus-profile", json=update, headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 2
    assert body["availability"]["minutes_per_day"] == 240

    stale = client.put("/api/v1/me/syllabus-profile", json=update, headers=AARAV)
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "RESOURCE_CONFLICT"


def test_update_profile_rejects_subject_outside_syllabus(client):
    response = client.put(
        "/api/v1/me/syllabus-profile",
        json={"version": 1, "subjects": ["sub_biology"]},
        headers=AARAV,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"


def test_progress_computed_from_task_state(client):
    response = client.get("/api/v1/me/syllabus-progress", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    # task_seed_3 completed the Moment of Inertia topic, so Rotational
    # Motion contributes exactly one covered topic.
    physics = next(s for s in body["subjects"] if s["subject_id"] == SUBJECT_PHYSICS)
    assert physics["topics_covered"] == 1
    assert 0 < body["percent"] < 100


def test_progress_access_denied_for_unassigned_student(client):
    # Meera is not in Mrs. Rao's class.
    response = client.get(
        f"/api/v1/me/syllabus-progress?student_id={STUDENT_MEERA}",
        headers=RAO,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_teacher_can_read_assigned_student_progress(client):
    response = client.get(
        f"/api/v1/me/syllabus-progress?student_id={STUDENT_AARAV}",
        headers=RAO,
    )
    assert response.status_code == 200
    assert response.json()["student_id"] == STUDENT_AARAV


def test_student_cannot_create_template(client):
    response = client.post(
        "/api/v1/teacher/syllabus-templates",
        json={"name": "Nope"},
        headers=AARAV,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


def test_template_create_publish_and_idempotency(client):
    create = client.post(
        "/api/v1/teacher/syllabus-templates",
        json={"name": "Class 12-A Physics Plan", "payload": {"units": ["Rotational Motion"]}},
        headers=RAO,
    )
    assert create.status_code == 201
    template_id = create.json()["id"]
    assert create.json()["status"] == "draft"

    publish = client.post(
        f"/api/v1/teacher/syllabus-templates/{template_id}/publish", headers=RAO
    )
    assert publish.status_code == 200
    assert publish.json()["status"] == "published"
    assert publish.json()["published_at"] is not None

    # Re-publishing is a safe no-op.
    again = client.post(
        f"/api/v1/teacher/syllabus-templates/{template_id}/publish", headers=RAO
    )
    assert again.status_code == 200
    assert again.json()["published_at"] == publish.json()["published_at"]


def test_template_publish_other_teacher_hidden(client):
    create = client.post(
        "/api/v1/teacher/syllabus-templates",
        json={"name": "Mine"},
        headers=RAO,
    )
    template_id = create.json()["id"]
    other = client.post(
        f"/api/v1/teacher/syllabus-templates/{template_id}/publish",
        headers=auth_headers("teacher_other", "teacher", "Other Teacher"),
    )
    assert other.status_code == 404


def test_template_creation_idempotency_key(client):
    body = {"name": "Idempotent Plan"}
    key = "tmpl-key-1"
    first = client.post(
        "/api/v1/teacher/syllabus-templates",
        json=body,
        headers={**RAO, "Idempotency-Key": key},
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/teacher/syllabus-templates",
        json=body,
        headers={**RAO, "Idempotency-Key": key},
    )
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    conflict = client.post(
        "/api/v1/teacher/syllabus-templates",
        json={"name": "Different"},
        headers={**RAO, "Idempotency-Key": key},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
