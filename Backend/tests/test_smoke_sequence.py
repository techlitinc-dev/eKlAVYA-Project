"""
End-to-End Smoke Sequence

Implements the 24-step verification sequence from endpoint_instructions.md
section 24 against a live TestClient instance of the real application.
"""

import io

import tests.conftest as c
from models.communication import CommunicationPreferences
from models.common import AuditEntry

SAMPLE_PNG = b"\x89PNG\r\n\x1a\n" + b"EKLAVYA_SAMPLE" + b"\x00" * 64

AARAV = c.auth_headers(c.STUDENT_AARAV, "student", "Aarav Sharma")
RAO = c.auth_headers(c.TEACHER_RAO, "teacher", "Mrs. Rao")
RAJESH = c.auth_headers(c.PARENT_RAJESH, "parent", "Rajesh Sharma")


def _disable_quiet_hours(fresh_repository, user_id: str) -> None:
    fresh_repository.put(
        CommunicationPreferences(
            id=f"commpref_{user_id}", user_id=user_id, quiet_hours_enabled=False
        )
    )


def test_smoke_sequence(client, fresh_repository):
    # 1. Authenticate as student_aarav using development headers.
    # (headers are attached per-request below)

    # 2. Get the active syllabus profile.
    profile = client.get("/api/v1/me/syllabus-profile", headers=AARAV)
    assert profile.status_code == 200
    assert profile.json()["syllabus_id"] == c.SYLLABUS_ID

    # 3. List Physics chapters and select a valid topic.
    chapters = client.get(f"/api/v1/subjects/{c.SUBJECT_PHYSICS}/chapters", headers=AARAV)
    assert chapters.status_code == 200
    topics = client.get(
        f"/api/v1/chapters/{c.CHAPTER_WORK_ENERGY}/topics", headers=AARAV
    )
    assert topics.status_code == 200
    assert c.TOPIC_KINETIC_ENERGY in {t["id"] for t in topics.json()["items"]}

    # 4. Create a planner task for that topic.
    today = client.get("/api/v1/planner/today", headers=AARAV).json()["date"]
    task = client.post(
        "/api/v1/planner/tasks",
        json={
            "title": "Smoke: Kinetic Energy practice",
            "task_type": "practice",
            "scheduled_date": today,
            "duration_minutes": 30,
            "topic_id": c.TOPIC_KINETIC_ENERGY,
            "chapter_id": c.CHAPTER_WORK_ENERGY,
            "subject_id": c.SUBJECT_PHYSICS,
            "syllabus_id": c.SYLLABUS_ID,
        },
        headers=AARAV,
    )
    assert task.status_code == 201, task.text
    task_id = task.json()["id"]

    # 5. Complete the task.
    complete = client.post(f"/api/v1/planner/tasks/{task_id}/complete", headers=AARAV)
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"

    # 6. Today progress reflects the completion.
    today_after = client.get("/api/v1/planner/today", headers=AARAV)
    assert today_after.status_code == 200
    assert today_after.json()["progress"]["completed"] >= 1

    # 7. Create a note.
    note = client.post(
        "/api/v1/notes",
        json={"title": "Smoke Note", "body": "Kinetic energy notes."},
        headers=AARAV,
    )
    assert note.status_code == 201
    note_id = note.json()["id"]

    # 8. Update the note; version increments.
    updated = client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Smoke Note v2", "body": "More detail.", "version": 1},
        headers=AARAV,
    )
    assert updated.status_code == 200
    assert updated.json()["version"] == 2

    # 9. Create a mind map and add a child node linked to the note.
    mindmap = client.post(
        "/api/v1/mindmaps",
        json={"title": "Smoke Map", "root_label": "Kinetic Energy"},
        headers=AARAV,
    )
    assert mindmap.status_code == 201
    map_id = mindmap.json()["id"]
    child = client.post(
        f"/api/v1/mindmaps/{map_id}/nodes",
        json={"label": "From note", "parent_id": mindmap.json()["root_node_id"], "note_id": note_id},
        headers=AARAV,
    )
    assert child.status_code == 201

    # 10. Create a scan and upload the sample page.
    scan = client.post(
        "/api/v1/scans",
        json={"intent": "solve", "subject_id": c.SUBJECT_PHYSICS},
        headers=AARAV,
    )
    assert scan.status_code == 201
    scan_id = scan.json()["id"]
    page = client.post(
        f"/api/v1/scans/{scan_id}/pages",
        files={"file": ("page.png", io.BytesIO(SAMPLE_PNG), "image/png")},
        headers=AARAV,
    )
    assert page.status_code == 201, page.text

    # 11. Process the scan and retrieve OCR.
    process = client.post(f"/api/v1/scans/{scan_id}/process", headers=AARAV)
    assert process.status_code == 200
    ocr = client.get(f"/api/v1/scans/{scan_id}/ocr", headers=AARAV)
    assert ocr.status_code == 200
    assert "A block of mass 2 kg" in ocr.json()["text"]

    # 12. Confirm OCR.
    confirm = client.put(
        f"/api/v1/scans/{scan_id}/ocr-confirmation",
        json={"text": ocr.json()["text"]},
        headers=AARAV,
    )
    assert confirm.status_code == 200

    # 13. Execute Solve and verify the answer is 9 J.
    execute = client.post(f"/api/v1/scans/{scan_id}/execute", headers=AARAV)
    assert execute.status_code == 200
    payload = execute.json()["payload"]
    assert payload["final_answer"] == "9 J"
    assert any("1/2" in step and "mv" in step.replace(" ", "") for step in payload["steps"])
    assert execute.json()["grounding_status"] == "grounded"

    # 14. Save the result to Notes.
    saved = client.post(f"/api/v1/scans/{scan_id}/save-note", headers=AARAV)
    assert saved.status_code == 201
    saved_again = client.post(f"/api/v1/scans/{scan_id}/save-note", headers=AARAV)
    assert saved_again.status_code == 200
    assert saved_again.json()["id"] == saved.json()["id"]

    # 15. Schedule revision.
    revision = client.post(f"/api/v1/scans/{scan_id}/schedule-revision", headers=AARAV)
    assert revision.status_code == 201
    revision_again = client.post(f"/api/v1/scans/{scan_id}/schedule-revision", headers=AARAV)
    assert revision_again.json()["id"] == revision.json()["id"]

    # 16. Authenticate as teacher_rao and create a simulated call for Aarav.
    _disable_quiet_hours(fresh_repository, c.STUDENT_AARAV)
    call = client.post(
        "/api/v1/simulated-calls",
        json={
            "recipient_ids": [c.STUDENT_AARAV],
            "title": "Smoke call",
            "subject": "Physics",
            "transcript": "Great work on kinetic energy today.",
        },
        headers=RAO,
    )
    assert call.status_code == 201, call.text
    deliveries = call.json()["deliveries"]
    assert len(deliveries) == 1
    delivery_id = deliveries[0]["delivery_id"]

    # 17-21. Aarav: list deliveries, accept, playback started, complete.
    mine = client.get("/api/v1/me/simulated-calls", headers=AARAV)
    assert mine.status_code == 200
    assert delivery_id in {d["delivery_id"] for d in mine.json()["items"]}

    accept = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/accept", headers=AARAV
    )
    assert accept.status_code == 200
    playing = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/playback-started", headers=AARAV
    )
    assert playing.status_code == 200
    done = client.post(
        f"/api/v1/me/simulated-calls/{delivery_id}/complete", headers=AARAV
    )
    assert done.status_code == 200
    assert done.json()["state"] == "completed"

    # 22. Messages show completed history.
    messages = client.get("/api/v1/messages", headers=AARAV)
    assert messages.status_code == 200
    assert any(
        "completed" in m["title"].lower() and m.get("delivery_id") == delivery_id
        for m in messages.json()["items"]
    )

    # Audit trail captured the important actions.
    actions = {e.action for e in fresh_repository.all(AuditEntry)}
    assert "call.transition" in actions
    assert "task.complete" in actions
    assert "scan.execute" in actions
    assert "note.create" in actions

    # 23. Rajesh verifies Aarav's read-only progress.
    progress = client.get(
        f"/api/v1/parent/children/{c.STUDENT_AARAV}/progress", headers=RAJESH
    )
    assert progress.status_code == 200

    # 24. Meera's records are denied.
    denied_note = client.get("/api/v1/notes/note_seed_meera", headers=AARAV)
    assert denied_note.status_code == 404
    denied_progress = client.get(
        f"/api/v1/parent/children/{c.STUDENT_MEERA}/progress", headers=RAJESH
    )
    assert denied_progress.status_code == 403
