"""
Scan & Solve API Tests

Covers the scan state machine (create -> upload -> process -> confirm ->
execute), upload validation (type, size, page count), the grounded mock
answer for the sample question, safe handling of unsupported questions,
per-intent result schemas, and the idempotent result actions (note, mind
map, revision item).
"""

from datetime import timedelta

from core.config import get_settings
from core.time import today
from models.mindmaps import MapEdge, MapNode, MindMap
from models.notes import Note
from models.planner import RevisionItem
from tests.conftest import (
    STUDENT_AARAV,
    STUDENT_MEERA,
    SUBJECT_PHYSICS,
    SYLLABUS_ID,
    TOPIC_KINETIC_ENERGY,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = auth_headers(STUDENT_MEERA, "student", "Meera Iyer")

SEED_SCAN_MEERA = "scan_seed_meera"

SAMPLE_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64 + b"EKLAVYA_SAMPLE"
NON_SAMPLE_PNG = b"\x89PNG\r\n\x1a\n" + b"RANDOM_UNRECOGNIZED_BYTES_12345"
SAMPLE_QUESTION = (
    "A block of mass 2 kg moves at 3 m/s on a frictionless horizontal "
    "surface. Find its kinetic energy."
)
UNSUPPORTED_QUESTION = "What is the capital of France?"
GARBLED_QUESTION = "???"
SCAN_CONTEXT = {
    "syllabus_id": SYLLABUS_ID,
    "subject_id": SUBJECT_PHYSICS,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_scan(client, intent="solve", headers=AARAV, **fields):
    body = {"intent": intent}
    body.update(fields)
    return client.post("/api/v1/scans", json=body, headers=headers)


def _upload_page(client, scan_id, content=SAMPLE_PNG, headers=AARAV, page_number=None):
    files = {"file": ("page.png", content, "image/png")}
    params = {}
    if page_number is not None:
        params["page_number"] = page_number
    return client.post(
        f"/api/v1/scans/{scan_id}/pages", files=files, params=params, headers=headers
    )


def _process(client, scan_id, headers=AARAV):
    return client.post(f"/api/v1/scans/{scan_id}/process", headers=headers)


def _confirm(client, scan_id, text=SAMPLE_QUESTION, headers=AARAV):
    return client.put(
        f"/api/v1/scans/{scan_id}/ocr-confirmation", json={"text": text}, headers=headers
    )


def _execute(client, scan_id, headers=AARAV, **body):
    return client.post(f"/api/v1/scans/{scan_id}/execute", json=body, headers=headers)


def _ready_scan(client, intent="solve", content=SAMPLE_PNG, confirm_text=SAMPLE_QUESTION):
    """Create a scan, upload one page, process, and confirm OCR."""
    scan_id = _create_scan(client, intent=intent, **SCAN_CONTEXT).json()["id"]
    upload = _upload_page(client, scan_id, content=content)
    assert upload.status_code == 201
    process = _process(client, scan_id)
    assert process.status_code == 200
    confirm = _confirm(client, scan_id, text=confirm_text)
    assert confirm.status_code == 200
    return scan_id


# ---------------------------------------------------------------------------
# Creation, retrieval, authorization
# ---------------------------------------------------------------------------

def test_openapi_includes_scan_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    for path in (
        "/api/v1/scans",
        "/api/v1/scans/{scan_id}/pages",
        "/api/v1/scans/{scan_id}/process",
        "/api/v1/scans/{scan_id}/ocr",
        "/api/v1/scans/{scan_id}/ocr-confirmation",
        "/api/v1/scans/{scan_id}/execute",
        "/api/v1/scans/{scan_id}/result",
        "/api/v1/scans/{scan_id}/save-note",
        "/api/v1/scans/{scan_id}/create-mindmap",
        "/api/v1/scans/{scan_id}/schedule-revision",
    ):
        assert path in paths


def test_create_scan_and_owner_retrieval(client):
    response = _create_scan(
        client, intent="solve", chapter_id="ch_work_energy_power",
        topic_id=TOPIC_KINETIC_ENERGY,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["owner_id"] == STUDENT_AARAV
    assert body["intent"] == "solve"
    assert body["status"] == "created"
    assert body["page_count"] == 0
    assert body["topic_id"] == TOPIC_KINETIC_ENERGY

    fetched = client.get(f"/api/v1/scans/{body['id']}", headers=AARAV)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]


def test_missing_authentication_rejected(client):
    response = client.post("/api/v1/scans", json={"intent": "solve"})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_cross_student_scan_not_readable(client):
    response = client.get(f"/api/v1/scans/{SEED_SCAN_MEERA}", headers=AARAV)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    upload = _upload_page(client, SEED_SCAN_MEERA)
    assert upload.status_code == 404


def test_invalid_intent_rejected(client):
    response = client.post("/api/v1/scans", json={"intent": "translate"}, headers=AARAV)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_invalid_syllabus_context_rejected(client):
    response = _create_scan(client, topic_id="top_missing_topic")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"

    mismatched = _create_scan(
        client,
        subject_id=SUBJECT_PHYSICS,
        chapter_id="ch_chemical_bonding",
        topic_id=TOPIC_KINETIC_ENERGY,
    )
    assert mismatched.status_code == 422
    assert mismatched.json()["error"]["code"] == "SYLLABUS_CONTEXT_INVALID"


def test_scan_create_idempotency_key(client):
    body = {"intent": "solve", **SCAN_CONTEXT}
    first = client.post(
        "/api/v1/scans", json=body, headers={**AARAV, "Idempotency-Key": "scan-key-1"}
    )
    assert first.status_code == 201
    second = client.post(
        "/api/v1/scans", json=body, headers={**AARAV, "Idempotency-Key": "scan-key-1"}
    )
    assert second.status_code == 201
    assert second.json()["id"] == first.json()["id"]

    conflict = client.post(
        "/api/v1/scans",
        json={"intent": "summarize"},
        headers={**AARAV, "Idempotency-Key": "scan-key-1"},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


# ---------------------------------------------------------------------------
# Upload validation
# ---------------------------------------------------------------------------

def test_upload_valid_png_returns_asset_metadata(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    response = _upload_page(client, scan_id)
    assert response.status_code == 201
    body = response.json()
    assert body["page_number"] == 1
    assert body["content_type"] == "image/png"
    assert body["size_bytes"] == len(SAMPLE_PNG)
    assert len(body["checksum"]) == 64
    # Never expose a filesystem path or storage name.
    assert "storage_name" not in body
    assert "path" not in body
    assert "local_data" not in str(body)

    scan = client.get(f"/api/v1/scans/{scan_id}", headers=AARAV).json()
    assert scan["page_count"] == 1
    assert scan["status"] == "pages_uploaded"

    # Second upload without page_number gets the next sequential number.
    second = _upload_page(client, scan_id)
    assert second.status_code == 201
    assert second.json()["page_number"] == 2


def test_upload_invalid_type_rejected(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    response = _upload_page(client, scan_id, content=b"this is not an image")
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UPLOAD_TYPE_NOT_ALLOWED"


def test_upload_oversized_rejected(client):
    settings = get_settings()
    original = settings.max_upload_mb
    object.__setattr__(settings, "max_upload_mb", 1)
    try:
        scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
        big = b"\x89PNG\r\n\x1a\n" + b"\x00" * (2 * 1024 * 1024)
        response = _upload_page(client, scan_id, content=big)
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "UPLOAD_TOO_LARGE"
    finally:
        object.__setattr__(settings, "max_upload_mb", original)


def test_page_count_limit_rejected(client):
    settings = get_settings()
    original = settings.max_scan_pages
    object.__setattr__(settings, "max_scan_pages", 1)
    try:
        scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
        first = _upload_page(client, scan_id)
        assert first.status_code == 201
        second = _upload_page(client, scan_id)
        assert second.status_code == 422
        assert second.json()["error"]["code"] == "VALIDATION_ERROR"
        assert second.json()["error"]["details"]["code"] == "MAX_SCAN_PAGES"
    finally:
        object.__setattr__(settings, "max_scan_pages", original)


# ---------------------------------------------------------------------------
# OCR processing and confirmation state machine
# ---------------------------------------------------------------------------

def test_process_requires_pages(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    response = _process(client, scan_id)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_process_sample_sets_confirmation_required(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    _upload_page(client, scan_id)
    response = _process(client, scan_id)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmation_required"
    assert body["confirmation_required"] is True
    assert SAMPLE_QUESTION in (body["ocr_text"] or "")

    ocr = client.get(f"/api/v1/scans/{scan_id}/ocr", headers=AARAV)
    assert ocr.status_code == 200
    ocr_body = ocr.json()
    assert ocr_body["scan_id"] == scan_id
    assert ocr_body["text"] == body["ocr_text"]
    assert len(ocr_body["uncertain_regions"]) >= 1
    assert ocr_body["confirmation_required"] is True
    assert ocr_body["status"] == "confirmation_required"


def test_execute_before_confirmation_rejected(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    _upload_page(client, scan_id)
    assert _process(client, scan_id).status_code == 200

    response = _execute(client, scan_id)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "OCR_CONFIRMATION_REQUIRED"


def test_confirmation_requires_confirmation_state(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    early = _confirm(client, scan_id)
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    _upload_page(client, scan_id)
    assert _process(client, scan_id).status_code == 200
    empty = _confirm(client, scan_id, text="")
    assert empty.status_code == 422


def test_confirm_marks_scan_confirmed(client):
    scan_id = _ready_scan(client)
    scan = client.get(f"/api/v1/scans/{scan_id}", headers=AARAV).json()
    assert scan["status"] == "confirmed"
    assert scan["confirmation_required"] is False
    assert scan["confirmed_at"] is not None


# ---------------------------------------------------------------------------
# Execution: solve (sample + unsupported), intents, results
# ---------------------------------------------------------------------------

def test_execute_solve_sample_returns_grounded_answer(client):
    scan_id = _ready_scan(client)

    first = client.post(
        f"/api/v1/scans/{scan_id}/execute",
        json={},
        headers={**AARAV, "Idempotency-Key": "exec-key-1"},
    )
    assert first.status_code == 200
    body = first.json()
    assert body["scan_id"] == scan_id
    assert body["intent"] == "solve"
    assert body["status"] == "executed"
    assert body["payload"]["final_answer"] == "9 J"
    assert any("1/2 mv^2" in step for step in body["payload"]["steps"])
    assert "KE = 1/2 * 2 * (3)^2 = 9 J" in body["payload"]["steps"]
    assert body["payload"]["subject"] == "Physics"
    assert body["payload"]["chapter"] == "Work, Energy and Power"
    assert body["payload"]["topic"] == "Kinetic Energy"
    assert body["citations"][0]["approved"] is True
    assert body["grounding_status"] == "grounded"
    assert body["verification_status"] == "verified_by_mock_rule"

    # Idempotent replay returns the original stored result.
    replay = client.post(
        f"/api/v1/scans/{scan_id}/execute",
        json={},
        headers={**AARAV, "Idempotency-Key": "exec-key-1"},
    )
    assert replay.status_code == 200
    assert replay.json()["payload"] == body["payload"]


def test_execute_unsupported_input_never_invents_answer(client):
    scan_id = _ready_scan(
        client, content=NON_SAMPLE_PNG, confirm_text=UNSUPPORTED_QUESTION
    )
    response = _execute(client, scan_id)
    assert response.status_code == 200
    body = response.json()
    assert body["payload"]["final_answer"] is None
    assert body["payload"]["steps"] == []
    assert body["grounding_status"] == "ungrounded"
    assert body["verification_status"] in (
        "needs_clarification",
        "insufficient_sources",
    )
    assert body["verification_status"] == "insufficient_sources"

    # Garbled/empty content routes to needs_clarification.
    garbled_id = _ready_scan(
        client, content=NON_SAMPLE_PNG, confirm_text=GARBLED_QUESTION
    )
    garbled = _execute(client, garbled_id)
    assert garbled.status_code == 200
    assert garbled.json()["payload"]["final_answer"] is None
    assert garbled.json()["verification_status"] == "needs_clarification"


def test_check_steps_requires_steps_and_verifies(client):
    scan_id = _ready_scan(client, intent="check_steps")
    missing = _execute(client, scan_id)
    assert missing.status_code == 422

    ok = _execute(
        client,
        scan_id,
        steps=[
            "Kinetic energy: KE = 1/2 mv^2",
            "Mass m = 2 kg, speed v = 3 m/s",
            "KE = 1/2 * 2 * (3)^2 = 9 J",
        ],
    )
    assert ok.status_code == 200
    payload = ok.json()["payload"]
    assert payload["verdict"] == "correct"
    assert payload["issues"] == []
    assert len(payload["checked_steps"]) == 3

    bad = _execute(client, scan_id, steps=["Guess: KE = 6 J"])
    assert bad.status_code == 200
    bad_payload = bad.json()["payload"]
    assert bad_payload["verdict"] == "incorrect"
    assert bad_payload["issues"]


def test_every_intent_returns_its_own_schema(client):
    expectations = {
        "solve": lambda p: "final_answer" in p and "steps" in p,
        "check_steps": lambda p: "verdict" in p and "issues" in p,
        "digitize": lambda p: "text" in p and "language" in p and "page_count" in p,
        "summarize": lambda p: "summary" in p and "source_words" in p,
        "mindmap": lambda p: "root_label" in p and "branches" in p,
        "revision_tasks": lambda p: "tasks" in p and len(p["tasks"]) >= 2,
    }
    for intent, matches in expectations.items():
        if intent == "check_steps":
            scan_id = _ready_scan(client, intent=intent)
            response = _execute(client, scan_id, steps=["KE = 1/2 mv^2", "= 9 J"])
        else:
            scan_id = _ready_scan(client, intent=intent)
            response = _execute(client, scan_id)
        assert response.status_code == 200, intent
        body = response.json()
        assert body["intent"] == intent
        assert matches(body["payload"]), intent

    digitize = client.get(f"/api/v1/scans/{scan_id}/result", headers=AARAV)
    assert digitize.status_code == 200


def test_get_result_and_404_before_execution(client):
    scan_id = _create_scan(client, **SCAN_CONTEXT).json()["id"]
    missing = client.get(f"/api/v1/scans/{scan_id}/result", headers=AARAV)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    solved = _ready_scan(client)
    _execute(client, solved)
    result = client.get(f"/api/v1/scans/{solved}/result", headers=AARAV)
    assert result.status_code == 200
    assert result.json()["payload"]["final_answer"] == "9 J"
    assert result.json()["verification_status"] == "verified_by_mock_rule"

    other = client.get(f"/api/v1/scans/{solved}/result", headers=MEERA)
    assert other.status_code == 404


# ---------------------------------------------------------------------------
# Result actions
# ---------------------------------------------------------------------------

def test_save_note_idempotent(client, fresh_repository):
    scan_id = _ready_scan(client)
    _execute(client, scan_id)

    key = "note-key-1"
    first = client.post(
        f"/api/v1/scans/{scan_id}/save-note",
        headers={**AARAV, "Idempotency-Key": key},
    )
    assert first.status_code == 201
    note_id = first.json()["id"]
    assert first.json()["source"] == "scan"
    assert first.json()["source_id"] == scan_id
    assert first.json()["ocr_text"] == SAMPLE_QUESTION
    assert first.json()["owner_id"] == STUDENT_AARAV

    replay = client.post(
        f"/api/v1/scans/{scan_id}/save-note",
        headers={**AARAV, "Idempotency-Key": key},
    )
    assert replay.status_code == 201
    assert replay.json()["id"] == note_id

    without_key = client.post(f"/api/v1/scans/{scan_id}/save-note", headers=AARAV)
    assert without_key.status_code == 200
    assert without_key.json()["id"] == note_id

    notes = fresh_repository.find(Note, source="scan", source_id=scan_id)
    assert len(notes) == 1


def test_save_note_requires_executed_scan(client):
    scan_id = _ready_scan(client)
    response = client.post(f"/api/v1/scans/{scan_id}/save-note", headers=AARAV)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"


def test_create_mindmap_creates_map_root_and_dedups(client, fresh_repository):
    scan_id = _ready_scan(client)
    _execute(client, scan_id)

    first = client.post(f"/api/v1/scans/{scan_id}/create-mindmap", headers=AARAV)
    assert first.status_code == 201
    body = first.json()
    assert body["source"] == "scan"
    assert body["source_id"] == scan_id
    assert body["root_node_id"] is not None
    assert body["owner_id"] == STUDENT_AARAV

    nodes = fresh_repository.find(MapNode, map_id=body["id"])
    assert len(nodes) == 4  # root + 3 children
    root = next(n for n in nodes if n.id == body["root_node_id"])
    assert root.parent_id is None
    edges = fresh_repository.find(MapEdge, map_id=body["id"])
    assert len(edges) == 3

    second = client.post(f"/api/v1/scans/{scan_id}/create-mindmap", headers=AARAV)
    assert second.status_code == 200
    assert second.json()["id"] == body["id"]
    assert len(fresh_repository.find(MindMap, source="scan", source_id=scan_id)) == 1


def test_schedule_revision_creates_real_item_and_dedups(client, fresh_repository):
    scan_id = _ready_scan(client)
    _execute(client, scan_id)

    first = client.post(f"/api/v1/scans/{scan_id}/schedule-revision", headers=AARAV)
    assert first.status_code == 201
    body = first.json()
    assert body["student_id"] == STUDENT_AARAV
    assert body["source"] == "scan"
    assert body["source_id"] == scan_id

    items = fresh_repository.find(RevisionItem, source="scan", source_id=scan_id)
    assert len(items) == 1
    assert items[0].due_date == today() + timedelta(days=3)
    assert body["due_date"] == (today() + timedelta(days=3)).isoformat()

    second = client.post(f"/api/v1/scans/{scan_id}/schedule-revision", headers=AARAV)
    assert second.status_code == 200
    assert second.json()["id"] == body["id"]
    assert len(fresh_repository.find(RevisionItem, source="scan", source_id=scan_id)) == 1


def test_result_actions_require_executed_scan(client):
    scan_id = _ready_scan(client)
    for action in ("save-note", "create-mindmap", "schedule-revision"):
        response = client.post(f"/api/v1/scans/{scan_id}/{action}", headers=AARAV)
        assert response.status_code == 409, action
        assert response.json()["error"]["code"] == "INVALID_STATE_TRANSITION"
