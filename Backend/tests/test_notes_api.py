"""
Notes API Tests

Covers note CRUD and search, filters, optimistic concurrency with version
snapshots, restore, attachments with magic-byte validation, links, archive
(soft delete), export artifacts, sharing scopes with audit entries, and the
deterministic mock AI actions (including history preservation).
"""

from pathlib import Path

from core.config import get_settings
from models.common import AuditEntry
from models.mindmaps import MapNode, MindMap
from models.notes import Note, NoteVersion
from models.planner import PlannerTask, TaskSource
from tests.conftest import (
    CHAPTER_CHEM_BONDING,
    PARENT_RAJESH,
    STUDENT_AARAV,
    STUDENT_MEERA,
    SUBJECT_CHEMISTRY,
    SYLLABUS_ID,
    TOPIC_CHEMICAL_BONDING,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = auth_headers(STUDENT_MEERA, "student", "Meera Iyer")
RAJESH = auth_headers(PARENT_RAJESH, "parent", "Rajesh Sharma")

NOTE_SEED_1 = "note_seed_1"
NOTE_SEED_MEERA = "note_seed_meera"

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG_BYTES = b"\xff\xd8\xff\xe0" + b"\x00" * 64


# ---------------------------------------------------------------------------
# OpenAPI and authentication
# ---------------------------------------------------------------------------

def test_openapi_includes_notes_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    for path in (
        "/api/v1/notes",
        "/api/v1/notes/{note_id}",
        "/api/v1/notes/{note_id}/versions",
        "/api/v1/notes/{note_id}/restore",
        "/api/v1/notes/{note_id}/attachments",
        "/api/v1/notes/{note_id}/links",
        "/api/v1/notes/{note_id}/links/{linked_note_id}",
        "/api/v1/notes/{note_id}/export",
        "/api/v1/notes/{note_id}/share",
        "/api/v1/notes/{note_id}/ai-actions",
    ):
        assert path in paths


def test_missing_authentication_rejected(client):
    response = client.get("/api/v1/notes")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ---------------------------------------------------------------------------
# Create and retrieve
# ---------------------------------------------------------------------------

def test_create_note_and_retrieve(client):
    payload = {
        "title": "Thermodynamics cheat sheet",
        "body": "dS >= dQ/T for reversible processes.",
        "tags": ["chemistry"],
        "syllabus_id": SYLLABUS_ID,
        "subject_id": SUBJECT_CHEMISTRY,
        "chapter_id": CHAPTER_CHEM_BONDING,
        "topic_id": TOPIC_CHEMICAL_BONDING,
    }
    created = client.post("/api/v1/notes", json=payload, headers=AARAV)
    assert created.status_code == 201
    body = created.json()
    note_id = body["id"]
    assert note_id != NOTE_SEED_1
    assert body["owner_id"] == STUDENT_AARAV
    assert body["title"] == payload["title"]
    assert body["body"] == payload["body"]
    assert body["tags"] == ["chemistry"]
    assert body["topic_id"] == TOPIC_CHEMICAL_BONDING
    assert body["status"] == "active"
    assert body["version"] == 1

    fetched = client.get(f"/api/v1/notes/{note_id}", headers=AARAV)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == note_id
    assert fetched.json()["body"] == payload["body"]


def test_create_note_validates_syllabus_context(client):
    response = client.post(
        "/api/v1/notes",
        json={"title": "Bad context", "topic_id": "top_does_not_exist"},
        headers=AARAV,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"


def test_create_note_idempotency_key(client):
    payload = {"title": "Idempotent note", "body": "same body"}
    key = "note-create-key-1"

    first = client.post("/api/v1/notes", json=payload, headers={**AARAV, "Idempotency-Key": key})
    assert first.status_code == 201
    second = client.post("/api/v1/notes", json=payload, headers={**AARAV, "Idempotency-Key": key})
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    conflict = client.post(
        "/api/v1/notes",
        json={"title": "Different"},
        headers={**AARAV, "Idempotency-Key": key},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_parent_cannot_create_note(client):
    response = client.post(
        "/api/v1/notes",
        json={"title": "Note for Aarav"},
        headers=RAJESH,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"


# ---------------------------------------------------------------------------
# List and search
# ---------------------------------------------------------------------------

def test_list_notes_returns_only_own_active_notes(client):
    response = client.get("/api/v1/notes", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["next_cursor"] is None
    ids = {item["id"] for item in body["items"]}
    assert {NOTE_SEED_1, "note_seed_2", "note_seed_3"} <= ids
    assert NOTE_SEED_MEERA not in ids


def test_search_matches_title_body_and_tags(client):
    by_title = client.get("/api/v1/notes?query=formula", headers=AARAV)
    assert by_title.status_code == 200
    assert {n["id"] for n in by_title.json()["items"]} == {NOTE_SEED_1}

    by_body = client.get("/api/v1/notes?query=SIGMA", headers=AARAV)
    assert {n["id"] for n in by_body.json()["items"]} == {"note_seed_2"}

    by_tag = client.get("/api/v1/notes?query=formulas", headers=AARAV)
    assert {n["id"] for n in by_tag.json()["items"]} == {NOTE_SEED_1}

    no_match = client.get("/api/v1/notes?query=zzzznotfound", headers=AARAV)
    assert no_match.json()["items"] == []


def test_topic_and_tag_filters_compose_with_query(client):
    by_topic = client.get(f"/api/v1/notes?topicId={TOPIC_CHEMICAL_BONDING}", headers=AARAV)
    assert {n["id"] for n in by_topic.json()["items"]} == {"note_seed_2"}

    topic_and_tag = client.get(
        f"/api/v1/notes?topicId={TOPIC_CHEMICAL_BONDING}&tag=chemistry", headers=AARAV
    )
    assert {n["id"] for n in topic_and_tag.json()["items"]} == {"note_seed_2"}

    topic_wrong_tag = client.get(
        f"/api/v1/notes?topicId={TOPIC_CHEMICAL_BONDING}&tag=physics", headers=AARAV
    )
    assert topic_wrong_tag.json()["items"] == []

    query_and_tag = client.get("/api/v1/notes?query=energy&tag=physics", headers=AARAV)
    assert {n["id"] for n in query_and_tag.json()["items"]} == {"note_seed_3"}


# ---------------------------------------------------------------------------
# Update, versions, restore, concurrency
# ---------------------------------------------------------------------------

def test_update_increments_version_and_versions_endpoint_lists_history(client):
    updated = client.patch(
        f"/api/v1/notes/{NOTE_SEED_1}",
        json={"version": 1, "body": "Updated: K = 1/2 I omega^2 only."},
        headers=AARAV,
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2
    assert updated.json()["body"] == "Updated: K = 1/2 I omega^2 only."

    versions = client.get(f"/api/v1/notes/{NOTE_SEED_1}/versions", headers=AARAV)
    assert versions.status_code == 200
    items = versions.json()["items"]
    assert [v["version"] for v in items] == [1]
    assert items[0]["body"].startswith("tau = dL/dt")
    assert items[0]["title"] == "Rotational Motion Formula Sheet"

    second = client.patch(
        f"/api/v1/notes/{NOTE_SEED_1}",
        json={"version": 2, "title": "Rotational formulas v2"},
        headers=AARAV,
    )
    assert second.json()["version"] == 3
    items = client.get(f"/api/v1/notes/{NOTE_SEED_1}/versions", headers=AARAV).json()["items"]
    assert [v["version"] for v in items] == [2, 1]


def test_stale_version_update_conflicts(client):
    response = client.patch(
        f"/api/v1/notes/{NOTE_SEED_1}",
        json={"version": 99, "body": "stale write"},
        headers=AARAV,
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESOURCE_CONFLICT"

    unchanged = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV)
    assert unchanged.json()["version"] == 1


def test_restore_from_older_version_preserves_history(client):
    created = client.post(
        "/api/v1/notes",
        json={"title": "Restore me", "body": "original body"},
        headers=AARAV,
    )
    note_id = created.json()["id"]

    client.patch(f"/api/v1/notes/{note_id}", json={"version": 1, "body": "second body"}, headers=AARAV)
    client.patch(f"/api/v1/notes/{note_id}", json={"version": 2, "body": "third body"}, headers=AARAV)

    before = client.get(f"/api/v1/notes/{note_id}/versions", headers=AARAV).json()["items"]
    assert [v["version"] for v in before] == [2, 1]

    restored = client.post(
        f"/api/v1/notes/{note_id}/restore", json={"version": 1}, headers=AARAV
    )
    assert restored.status_code == 200
    assert restored.json()["version"] == 4
    assert restored.json()["body"] == "original body"
    assert restored.json()["title"] == "Restore me"

    after = client.get(f"/api/v1/notes/{note_id}/versions", headers=AARAV).json()["items"]
    assert [v["version"] for v in after] == [3, 2, 1]
    version_one = next(v for v in after if v["version"] == 1)
    assert version_one["body"] == "original body"


def test_restore_unknown_version_not_found(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/restore", json={"version": 42}, headers=AARAV
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Archive (soft delete)
# ---------------------------------------------------------------------------

def test_delete_archives_note_and_owner_can_still_read_it(client):
    deleted = client.delete(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV)
    assert deleted.status_code == 204
    assert deleted.content == b""

    fetched = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "archived"

    listed = client.get("/api/v1/notes", headers=AARAV)
    assert NOTE_SEED_1 not in {n["id"] for n in listed.json()["items"]}

    unarchived = client.patch(
        f"/api/v1/notes/{NOTE_SEED_1}",
        json={"version": fetched.json()["version"], "status": "active"},
        headers=AARAV,
    )
    assert unarchived.status_code == 200
    assert unarchived.json()["status"] == "active"


# ---------------------------------------------------------------------------
# Cross-student access and links
# ---------------------------------------------------------------------------

def test_cross_student_read_hidden(client):
    response = client.get(f"/api/v1/notes/{NOTE_SEED_MEERA}", headers=AARAV)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_cross_student_versions_hidden(client):
    response = client.get(f"/api/v1/notes/{NOTE_SEED_MEERA}/versions", headers=AARAV)
    assert response.status_code == 404


def test_self_link_rejected(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/links",
        json={"linked_note_id": NOTE_SEED_1},
        headers=AARAV,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_link_to_nonexistent_note_not_found(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/links",
        json={"linked_note_id": "note_does_not_exist"},
        headers=AARAV,
    )
    assert response.status_code == 404


def test_link_to_other_student_note_hidden(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/links",
        json={"linked_note_id": NOTE_SEED_MEERA},
        headers=AARAV,
    )
    assert response.status_code == 404


def test_link_create_and_idempotent_remove(client):
    created = client.post("/api/v1/notes", json={"title": "Link target"}, headers=AARAV)
    target_id = created.json()["id"]

    linked = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/links",
        json={"linked_note_id": target_id},
        headers=AARAV,
    )
    assert linked.status_code == 200
    assert target_id in linked.json()["links"]

    duplicate = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/links",
        json={"linked_note_id": target_id},
        headers=AARAV,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "RESOURCE_CONFLICT"

    removed = client.delete(f"/api/v1/notes/{NOTE_SEED_1}/links/{target_id}", headers=AARAV)
    assert removed.status_code == 204
    assert target_id not in client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV).json()["links"]

    # Removing again is a safe no-op.
    again = client.delete(f"/api/v1/notes/{NOTE_SEED_1}/links/{target_id}", headers=AARAV)
    assert again.status_code == 204


def test_shared_note_link_allowed_for_audience(client):
    # Meera shares her note with Aarav via a class-level scope.
    shared = client.post(
        f"/api/v1/notes/{NOTE_SEED_MEERA}/share",
        json={"level": "class", "audience": [STUDENT_AARAV]},
        headers=MEERA,
    )
    assert shared.status_code == 200

    linked = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/links",
        json={"linked_note_id": NOTE_SEED_MEERA},
        headers=AARAV,
    )
    assert linked.status_code == 200
    assert NOTE_SEED_MEERA in linked.json()["links"]


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

def test_attachment_upload_validates_signature_and_size(client):
    ok = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/attachments",
        files={"file": ("diagram.png", PNG_BYTES, "image/png")},
        headers=AARAV,
    )
    assert ok.status_code == 201
    meta = ok.json()
    assert meta["filename"] == "diagram.png"
    assert meta["content_type"] == "image/png"
    assert meta["size_bytes"] == len(PNG_BYTES)
    assert meta["storage_name"].startswith(f"note_{NOTE_SEED_1}_att_")
    assert not meta["storage_name"].startswith("/")

    settings = get_settings()
    stored = Path(settings.local_upload_dir, meta["storage_name"])
    assert stored.exists()
    assert stored.read_bytes() == PNG_BYTES

    note = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV).json()
    assert meta["id"] in {a["id"] for a in note["attachments"]}

    jpeg = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/attachments",
        files={"file": ("photo.jpg", JPEG_BYTES, "image/jpeg")},
        headers=AARAV,
    )
    assert jpeg.status_code == 201
    assert jpeg.json()["storage_name"].endswith(".jpg")

    bad_type = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/attachments",
        files={"file": ("evil.exe", b"MZ\x90\x00executable", "application/octet-stream")},
        headers=AARAV,
    )
    assert bad_type.status_code == 415
    assert bad_type.json()["error"]["code"] == "UPLOAD_TYPE_NOT_ALLOWED"

    oversized = b"\x89PNG" + b"\x00" * (get_settings().max_upload_mb * 1024 * 1024 + 1)
    too_large = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/attachments",
        files={"file": ("big.png", oversized, "image/png")},
        headers=AARAV,
    )
    assert too_large.status_code == 413
    assert too_large.json()["error"]["code"] == "UPLOAD_TOO_LARGE"


def test_attachment_upload_never_uses_original_filename(client):
    ok = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/attachments",
        files={"file": ("../../sneaky.png", PNG_BYTES, "image/png")},
        headers=AARAV,
    )
    assert ok.status_code == 201
    meta = ok.json()
    # Original name is metadata only; storage uses the generated name.
    assert meta["filename"] == "../../sneaky.png"
    assert ".." not in meta["storage_name"]
    assert "/" not in meta["storage_name"]


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def test_export_txt_creates_labelled_plain_text_artifact(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/export", json={"format": "txt"}, headers=AARAV
    )
    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "txt"
    assert body["labelled_plain_text"] is True
    assert body["size_bytes"] > 0
    assert body["exported_at"]

    storage_name = body["storage_name"]
    assert not storage_name.startswith("/")

    settings = get_settings()
    absolute_media_dir = str(Path(settings.local_media_dir).resolve())
    assert absolute_media_dir not in storage_name
    assert absolute_media_dir not in response.text

    artifact = Path(settings.local_media_dir, storage_name)
    assert artifact.exists()
    content = artifact.read_text(encoding="utf-8")
    assert content.startswith("eKlAVYA Note Export (plain-text)")
    assert "Title: Rotational Motion Formula Sheet" in content
    assert "tau = dL/dt" in content


def test_export_pdf_writes_valid_pdf_bytes(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/export", json={"format": "pdf"}, headers=AARAV
    )
    assert response.status_code == 201
    body = response.json()
    assert body["format"] == "pdf"
    assert body["labelled_plain_text"] is False

    artifact = Path(get_settings().local_media_dir, body["storage_name"])
    data = artifact.read_bytes()
    assert data.startswith(b"%PDF")
    assert data.rstrip().endswith(b"%%EOF")
    assert b"eKlAVYA export" in data
    assert b"Rotational Motion Formula Sheet" in data


def test_export_invalid_format_rejected(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/export", json={"format": "docx"}, headers=AARAV
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------------------------
# Sharing and audit
# ---------------------------------------------------------------------------

def test_share_sets_scope_and_records_audit(client, fresh_repository):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/share",
        json={"level": "class", "audience": [STUDENT_MEERA]},
        headers=AARAV,
    )
    assert response.status_code == 200
    scope = response.json()["share_scope"]
    assert scope["level"] == "class"
    assert scope["audience"] == [STUDENT_MEERA]

    entries = fresh_repository.find(AuditEntry, action="note.share", resource_id=NOTE_SEED_1)
    assert len(entries) == 1
    assert entries[0].actor_id == STUDENT_AARAV
    assert entries[0].details["level"] == "class"
    assert entries[0].details["audience_count"] == 1
    assert "body" not in entries[0].details


def test_share_link_level_generates_token(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/share",
        json={"level": "link"},
        headers=AARAV,
    )
    assert response.status_code == 200
    scope = response.json()["share_scope"]
    assert scope["level"] == "link"
    assert scope["token"] is not None
    assert scope["token"].startswith("share_")


# ---------------------------------------------------------------------------
# Mock AI actions
# ---------------------------------------------------------------------------

def test_ai_action_summarize_preserves_history(client, fresh_repository):
    original = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV).json()
    assert original["version"] == 1

    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "summarize"},
        headers=AARAV,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["action"] == "summarize"
    assert body["note_version"] == 2
    assert body["created"] == {}
    assert body["result_preview"].endswith(" words)")

    after = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV).json()
    assert after["version"] == 2
    assert "AI action (summarize):" in after["body"]
    # The original content is still present above the marked AI section.
    assert after["body"].startswith(original["body"])

    versions = client.get(f"/api/v1/notes/{NOTE_SEED_1}/versions", headers=AARAV).json()["items"]
    reasons = {v["reason"] for v in versions}
    assert "ai_action:summarize" in reasons
    snapshot = next(v for v in versions if v["version"] == 1)
    assert snapshot["body"] == original["body"]

    audit = fresh_repository.find(AuditEntry, action="note.ai_action", resource_id=NOTE_SEED_1)
    assert len(audit) == 1
    assert audit[0].details["action"] == "summarize"
    assert "body" not in audit[0].details


def test_ai_action_structure_and_formulas_mark_body(client):
    structured = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "structure"},
        headers=AARAV,
    )
    assert structured.status_code == 200
    preview = structured.json()["result_preview"]
    assert preview.startswith("# Rotational Motion Formula Sheet")
    assert "AI action (structure):" in client.get(
        f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV
    ).json()["body"]

    formulas = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "extract_formulas"},
        headers=AARAV,
    )
    assert formulas.status_code == 200
    assert formulas.json()["result_preview"].startswith("- ")

    mistakes = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "extract_mistakes"},
        headers=AARAV,
    )
    assert mistakes.status_code == 200
    assert "Rotational Motion Formula Sheet" in mistakes.json()["result_preview"]


def test_ai_action_generate_mindmap_creates_linked_map(client, fresh_repository):
    original = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV).json()

    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "generate_mindmap"},
        headers=AARAV,
    )
    assert response.status_code == 200
    body = response.json()
    map_id = body["created"]["mindmap_id"]
    assert map_id

    mindmap = fresh_repository.get(MindMap, map_id)
    assert mindmap is not None
    assert mindmap.owner_id == STUDENT_AARAV
    assert mindmap.title == "Rotational Motion Formula Sheet (mind map)"
    assert mindmap.source == "ai_action"
    assert mindmap.source_id == NOTE_SEED_1
    assert mindmap.topic_id is None

    root = fresh_repository.get(MapNode, mindmap.root_node_id)
    assert root is not None
    assert root.parent_id is None
    assert root.map_id == map_id

    # Body is not touched and the version does not change.
    after = client.get(f"/api/v1/notes/{NOTE_SEED_1}", headers=AARAV).json()
    assert after["body"] == original["body"]
    assert after["version"] == original["version"]

    versions = client.get(f"/api/v1/notes/{NOTE_SEED_1}/versions", headers=AARAV).json()["items"]
    assert "ai_action:generate_mindmap" in {v["reason"] for v in versions}


def test_ai_action_create_planner_tasks(client, fresh_repository):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "create_planner_tasks"},
        headers=AARAV,
    )
    assert response.status_code == 200
    body = response.json()
    task_ids = body["created"]["task_ids"]
    assert len(task_ids) == 3

    tasks = fresh_repository.find(PlannerTask, source_id=NOTE_SEED_1)
    assert {t.id for t in tasks} == set(task_ids)
    assert all(t.source == TaskSource.generated for t in tasks)
    assert all(t.student_id == STUDENT_AARAV for t in tasks)
    assert all(t.title.startswith("Rotational Motion Formula Sheet:") for t in tasks)
    assert all(30 <= t.duration_minutes <= 45 for t in tasks)


def test_ai_action_unknown_rejected(client):
    response = client.post(
        f"/api/v1/notes/{NOTE_SEED_1}/ai-actions",
        json={"action": "translate"},
        headers=AARAV,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_note_entity_unchanged_schema_imports(client):
    # Sanity: seeded notes remain queryable through the repository contract.
    from seed import bootstrap_development_data

    from repositories.memory import InMemoryRepository

    repo = InMemoryRepository()
    bootstrap_development_data(repo)
    note = repo.get(Note, NOTE_SEED_1)
    assert note is not None
    assert note.version == 1
    assert repo.count(NoteVersion, note_id=NOTE_SEED_1) == 0
