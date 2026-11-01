"""
Notes Service

Business logic for the notes domain: CRUD with search and filters, optimistic
concurrency with version snapshots, restore, attachment upload with magic-byte
validation, note links, local export artifacts, sharing scopes, and
deterministic mock AI actions.

Every mutation records an audit entry without storing private note bodies.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
import re
import textwrap
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.access import assert_owner_access, assert_parent_read_only, is_admin
from core.errors import (
    NotFound,
    PermissionDenied,
    ResourceConflict,
    UploadTooLarge,
    UploadTypeNotAllowed,
    ValidationFailed,
)
from core.ids import new_id
from core.security import Principal
from core.time import today, utcnow
from models.common import SyllabusContext
from models.mindmaps import MapNode, MindMap
from models.notes import (
    Attachment,
    Note,
    NoteStatus,
    NoteVersion,
    ShareLevel,
    ShareScope,
)
from models.planner import PlannerTask, TaskSource, TaskStatus, TaskType
from models.syllabus import SyllabusProfile
from repositories.base import Repository
from services.audit_service import record_audit
from services.syllabus_core_service import validate_syllabus_context

logger = logging.getLogger(__name__)

AI_ACTIONS = (
    "summarize",
    "structure",
    "extract_formulas",
    "extract_mistakes",
    "generate_mindmap",
    "create_planner_tasks",
)

# Magic-byte content signatures accepted for attachments: (signature, ext, type)
_SIGNATURES: Tuple[Tuple[bytes, str, str], ...] = (
    (b"\x89PNG", "png", "image/png"),
    (b"\xff\xd8\xff", "jpg", "image/jpeg"),
    (b"%PDF", "pdf", "application/pdf"),
)


# ---------------------------------------------------------------------------
# Access helpers
# ---------------------------------------------------------------------------

def _get_owned_note(repo: Repository, principal: Principal, note_id: str) -> Note:
    """Fetch a note owned by the principal (admins allowed; others get 404)."""
    note = repo.get(Note, note_id)
    if note is None:
        raise NotFound("Note not found.")
    assert_owner_access(principal, note.owner_id)
    return note


def _can_read_note(principal: Principal, note: Note) -> bool:
    """Owner/admin always; audience members when the share scope is not private."""
    if is_admin(principal) or note.owner_id == principal.user_id:
        return True
    scope = note.share_scope
    return scope.level != ShareLevel.private and principal.user_id in scope.audience


def _snapshot(note: Note, created_by: str, reason: Optional[str]) -> NoteVersion:
    """Build a NoteVersion snapshot of the note's CURRENT content."""
    return NoteVersion.new(
        "notever",
        note_id=note.id,
        version=note.version,
        title=note.title,
        body=note.body,
        created_by=created_by,
        reason=reason,
    )


def _owner_profile(repo: Repository, owner_id: str) -> Optional[SyllabusProfile]:
    return repo.first(SyllabusProfile, student_id=owner_id)


# ---------------------------------------------------------------------------
# CRUD and search
# ---------------------------------------------------------------------------

def create_note(repo: Repository, principal: Principal, data: Dict[str, Any]) -> Note:
    if principal.role == "parent":
        raise PermissionDenied("Parents cannot create or modify notes.")

    context = SyllabusContext(
        syllabus_id=data.get("syllabus_id"),
        subject_id=data.get("subject_id"),
        chapter_id=data.get("chapter_id"),
        topic_id=data.get("topic_id"),
    )
    validate_syllabus_context(repo, context, _owner_profile(repo, principal.user_id))

    note = Note.new(
        "note",
        owner_id=principal.user_id,
        title=data["title"].strip(),
        body=data.get("body") or "",
        tags=list(data.get("tags") or []),
        ocr_text=data.get("ocr_text"),
        syllabus_id=context.syllabus_id,
        subject_id=context.subject_id,
        chapter_id=context.chapter_id,
        topic_id=context.topic_id,
        source=data.get("source") or "manual",
    )
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.create",
        "note",
        note.id,
        details={"title": note.title},
    )
    return note


def list_notes(
    repo: Repository,
    principal: Principal,
    query: Optional[str] = None,
    topic_id: Optional[str] = None,
    tag: Optional[str] = None,
) -> List[Note]:
    """Owner-only listing (admins see all); only active notes by default."""
    if is_admin(principal):
        notes = repo.all(Note)
    else:
        notes = repo.find(Note, owner_id=principal.user_id)
    notes = [n for n in notes if n.status == NoteStatus.active]

    if topic_id:
        notes = [n for n in notes if n.topic_id == topic_id]
    if tag:
        notes = [n for n in notes if tag in n.tags]
    if query:
        needle = query.lower()

        def matches(note: Note) -> bool:
            return (
                needle in note.title.lower()
                or needle in (note.body or "").lower()
                or needle in (note.ocr_text or "").lower()
                or any(needle in t.lower() for t in note.tags)
            )

        notes = [n for n in notes if matches(n)]

    notes.sort(key=lambda n: (n.updated_at, n.id), reverse=True)
    return notes


def get_note(repo: Repository, principal: Principal, note_id: str) -> Note:
    """Owner or admin may read; archived notes stay retrievable."""
    return _get_owned_note(repo, principal, note_id)


def update_note(
    repo: Repository,
    principal: Principal,
    note_id: str,
    data: Dict[str, Any],
) -> Note:
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)

    expected_version = data["version"]
    if expected_version != note.version:
        raise ResourceConflict(
            details={"expected_version": expected_version, "current_version": note.version},
            message="The note was modified by another request.",
        )

    updates = {k: v for k, v in data.items() if k != "version" and v is not None}
    if not updates:
        return note

    # Snapshot the PREVIOUS content before any mutation is applied.
    repo.put(_snapshot(note, principal.user_id, "edit"))

    context_keys = ("syllabus_id", "subject_id", "chapter_id", "topic_id")
    if any(key in updates for key in context_keys):
        context = SyllabusContext(
            syllabus_id=updates.get("syllabus_id", note.syllabus_id),
            subject_id=updates.get("subject_id", note.subject_id),
            chapter_id=updates.get("chapter_id", note.chapter_id),
            topic_id=updates.get("topic_id", note.topic_id),
        )
        validate_syllabus_context(repo, context, _owner_profile(repo, note.owner_id))
        note.syllabus_id = context.syllabus_id
        note.subject_id = context.subject_id
        note.chapter_id = context.chapter_id
        note.topic_id = context.topic_id

    if "title" in updates:
        note.title = updates["title"]
    if "body" in updates:
        note.body = updates["body"]
    if "tags" in updates:
        note.tags = list(updates["tags"])
    if "status" in updates:
        note.status = updates["status"]

    note.version += 1
    note.touch()
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.update",
        "note",
        note.id,
        details={"version": note.version},
    )
    return note


def archive_note(repo: Repository, principal: Principal, note_id: str) -> None:
    """Soft delete: mark the note archived."""
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)
    note.status = NoteStatus.archived
    note.touch()
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.delete",
        "note",
        note.id,
        details={"status": NoteStatus.archived.value},
    )


# ---------------------------------------------------------------------------
# Versions and restore
# ---------------------------------------------------------------------------

def list_versions(repo: Repository, principal: Principal, note_id: str) -> List[NoteVersion]:
    note = _get_owned_note(repo, principal, note_id)
    versions = repo.find(NoteVersion, note_id=note.id)
    versions.sort(key=lambda v: v.version, reverse=True)
    return versions


def restore_note(
    repo: Repository,
    principal: Principal,
    note_id: str,
    target_version: int,
) -> Note:
    """Restore content from an older NoteVersion; history is never erased."""
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)
    target = repo.first(NoteVersion, note_id=note.id, version=target_version)
    if target is None:
        raise NotFound(
            details={"version": target_version},
            message="No saved version with that number for this note.",
        )

    repo.put(_snapshot(note, principal.user_id, f"restore:{target_version}"))
    note.title = target.title
    note.body = target.body
    note.version += 1
    note.touch()
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.restore",
        "note",
        note.id,
        details={"version": note.version, "restored_from": target_version},
    )
    return note


# ---------------------------------------------------------------------------
# Attachments
# ---------------------------------------------------------------------------

def add_attachment(
    repo: Repository,
    settings,
    principal: Principal,
    note_id: str,
    filename: Optional[str],
    data: bytes,
) -> Attachment:
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise UploadTooLarge(
            details={"max_upload_mb": settings.max_upload_mb, "size_bytes": len(data)}
        )

    detected = next(
        ((ext, ctype) for sig, ext, ctype in _SIGNATURES if data[: len(sig)] == sig),
        None,
    )
    if detected is None:
        raise UploadTypeNotAllowed(
            details={"filename": filename or "unknown"},
            message="Only PNG, JPEG, and PDF uploads are allowed.",
        )
    ext, content_type = detected

    attachment_id = new_id("att")
    storage_name = f"note_{note.id}_{attachment_id}.{ext}"
    settings.ensure_local_dirs()
    Path(settings.local_upload_dir, storage_name).write_bytes(data)

    attachment = Attachment(
        id=attachment_id,
        filename=filename or storage_name,
        content_type=content_type,
        size_bytes=len(data),
        storage_name=storage_name,
        uploaded_at=utcnow(),
    )
    note.attachments.append(attachment)
    note.touch()
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.attach.attach",
        "note",
        note.id,
        details={"attachment_id": attachment.id, "size_bytes": len(data)},
    )
    return attachment


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------

def add_link(
    repo: Repository,
    principal: Principal,
    note_id: str,
    linked_note_id: str,
) -> Note:
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)

    if linked_note_id == note.id:
        raise ValidationFailed(
            details={"linked_note_id": linked_note_id},
            message="A note cannot link to itself.",
        )
    linked = repo.get(Note, linked_note_id)
    if linked is None or not _can_read_note(principal, linked):
        raise NotFound("The linked note was not found.")
    if linked_note_id in note.links:
        raise ResourceConflict(
            details={"linked_note_id": linked_note_id},
            message="This note is already linked.",
        )

    note.links.append(linked_note_id)
    note.touch()
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.link.create",
        "note",
        note.id,
        details={"linked_note_id": linked_note_id},
    )
    return note


def remove_link(
    repo: Repository,
    principal: Principal,
    note_id: str,
    linked_note_id: str,
) -> None:
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)
    if linked_note_id in note.links:
        note.links = [link for link in note.links if link != linked_note_id]
        note.touch()
        repo.put(note)
        record_audit(
            repo,
            principal.user_id,
            "note.link.delete",
            "note",
            note.id,
            details={"linked_note_id": linked_note_id},
        )
    # Missing links are ignored: deletion is idempotent.


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_note(
    repo: Repository,
    settings,
    principal: Principal,
    note_id: str,
    fmt: str,
) -> Dict[str, Any]:
    note = _get_owned_note(repo, principal, note_id)

    if fmt == "txt":
        payload = (
            f"eKlAVYA Note Export (plain-text)\nTitle: {note.title}\n\n{note.body}"
        ).encode("utf-8")
        labelled_plain_text = True
    elif fmt == "pdf":
        payload = _build_pdf(note.title, note.body)
        labelled_plain_text = False
    else:
        raise ValidationFailed(details={"field": "format", "allowed": ["txt", "pdf"]})

    settings.ensure_local_dirs()
    exported_at = utcnow()
    storage_name = f"note_{note.id}_{new_id('exp')}.{fmt}"
    Path(settings.local_media_dir, storage_name).write_bytes(payload)

    record_audit(
        repo,
        principal.user_id,
        "note.export",
        "note",
        note.id,
        details={"format": fmt, "size_bytes": len(payload)},
    )
    return {
        "format": fmt,
        "labelled_plain_text": labelled_plain_text,
        "storage_name": storage_name,
        "size_bytes": len(payload),
        "exported_at": exported_at,
    }


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _build_pdf(title: str, body: str) -> bytes:
    """Construct a minimal but valid single-page PDF (Helvetica, Letter)."""
    lines = ["eKlAVYA export", f"Title: {title}"]
    lines.extend(textwrap.wrap(body or "", width=95) or [""])

    commands = ["BT", "/F1 12 Tf", "72 740 Td", "16 TL"]
    for index, line in enumerate(lines):
        if index:
            commands.append("T*")
        commands.append(f"({_pdf_escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode("ascii") + obj + b"\nendobj\n"

    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF"
    ).encode("ascii")
    return bytes(out)


# ---------------------------------------------------------------------------
# Sharing
# ---------------------------------------------------------------------------

def share_note(
    repo: Repository,
    principal: Principal,
    note_id: str,
    level: ShareLevel,
    audience: List[str],
) -> Note:
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)

    token = new_id("share") if level == ShareLevel.link else None
    note.share_scope = ShareScope(level=level, audience=list(audience or []), token=token)
    note.touch()
    repo.put(note)
    record_audit(
        repo,
        principal.user_id,
        "note.share",
        "note",
        note.id,
        details={"level": level.value, "audience_count": len(audience or [])},
    )
    return note


# ---------------------------------------------------------------------------
# Deterministic mock AI actions
# ---------------------------------------------------------------------------

def run_ai_action(
    repo: Repository,
    principal: Principal,
    note_id: str,
    action: str,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    assert_parent_read_only(principal)
    note = _get_owned_note(repo, principal, note_id)
    if action not in AI_ACTIONS:
        raise ValidationFailed(details={"field": "action", "allowed": list(AI_ACTIONS)})

    created: Dict[str, Any] = {}
    preview = ""

    if action == "summarize":
        preview = _summarize(note.body)
        _apply_ai_edit(repo, principal, note, action, preview)
    elif action == "structure":
        preview = _structure(note)
        _apply_ai_edit(repo, principal, note, action, preview)
    elif action == "extract_formulas":
        preview = _extract_formulas(note.body)
        _apply_ai_edit(repo, principal, note, action, preview)
    elif action == "extract_mistakes":
        preview = _extract_mistakes(note)
        _apply_ai_edit(repo, principal, note, action, preview)
    elif action == "generate_mindmap":
        repo.put(_snapshot(note, principal.user_id, f"ai_action:{action}"))
        mindmap, root = _build_mindmap(note)
        repo.put(mindmap)
        repo.put(root)
        created["mindmap_id"] = mindmap.id
        preview = f"Created mind map '{mindmap.title}' with root node '{root.label}'."
    elif action == "create_planner_tasks":
        repo.put(_snapshot(note, principal.user_id, f"ai_action:{action}"))
        tasks = _build_planner_tasks(repo, principal, note)
        created["task_ids"] = [task.id for task in tasks]
        preview = f"Created {len(tasks)} planner tasks from '{note.title}'."

    record_audit(
        repo,
        principal.user_id,
        "note.ai_action",
        "note",
        note.id,
        details={"action": action},
    )
    return {
        "action": action,
        "note_version": note.version,
        "created": created,
        "result_preview": preview,
    }


def _apply_ai_edit(
    repo: Repository,
    principal: Principal,
    note: Note,
    action: str,
    output: str,
) -> None:
    """Snapshot current content, then append a clearly-marked AI section."""
    repo.put(_snapshot(note, principal.user_id, f"ai_action:{action}"))
    note.body = f"{note.body}\n\n---\nAI action ({action}):\n{output}"
    note.version += 1
    note.touch()
    repo.put(note)


def _summarize(body: str) -> str:
    text = body or ""
    first = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0].strip()
    return f"{first} ({len(text.split())} words)"


def _structure(note: Note) -> str:
    lines = [f"# {note.title}"]
    for line in (note.body or "").splitlines()[:3]:
        if line.strip():
            lines.append(f"- {line.strip()}")
    return "\n".join(lines)


def _extract_formulas(body: str) -> str:
    markers = ("=", "\\frac", "^", "d/d")
    found = [
        line.strip()
        for line in (body or "").splitlines()
        if line.strip() and any(marker in line for marker in markers)
    ]
    if not found:
        return "No formula-like lines found."
    return "\n".join(f"- {line}" for line in found)


def _extract_mistakes(note: Note) -> str:
    return "\n".join(
        [
            f'Common mistakes to review in "{note.title}":',
            "- Misreading the given quantities or units",
            "- Skipping the unit and dimension check in calculations",
            "- Forgetting special cases and boundary conditions",
        ]
    )


def _build_mindmap(note: Note) -> Tuple[MindMap, MapNode]:
    mindmap = MindMap.new(
        "map",
        owner_id=note.owner_id,
        title=f"{note.title} (mind map)",
        syllabus_id=note.syllabus_id,
        subject_id=note.subject_id,
        chapter_id=note.chapter_id,
        topic_id=note.topic_id,
        source="ai_action",
        source_id=note.id,
    )
    root = MapNode.new("node", map_id=mindmap.id, label=note.title, parent_id=None)
    mindmap.root_node_id = root.id
    return mindmap, root


def _build_planner_tasks(
    repo: Repository,
    principal: Principal,
    note: Note,
    count: int = 3,
) -> List[PlannerTask]:
    tasks = []
    base_day = today()
    for index in range(count):
        task = PlannerTask.new(
            "task",
            student_id=note.owner_id,
            title=f"{note.title}: review part {index + 1}",
            task_type=TaskType.revision,
            status=TaskStatus.pending,
            syllabus_id=note.syllabus_id,
            subject_id=note.subject_id,
            chapter_id=note.chapter_id,
            topic_id=note.topic_id,
            scheduled_date=base_day + timedelta(days=index + 1),
            start_minute=9 * 60 + index * 60,
            duration_minutes=30 + index * 5,
            source=TaskSource.generated,
            source_id=note.id,
            created_by=principal.user_id,
        )
        repo.put(task)
        tasks.append(task)
    return tasks
