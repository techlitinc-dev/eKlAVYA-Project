"""
Scan & Solve Service

Business logic for the scan state machine: scan creation with syllabus
context validation, private page uploads (magic-byte validation, size and
page-count limits, generated storage names), mock OCR processing with
confirmation flow, deterministic per-intent execution, and the result
actions (save note, create mind map, schedule revision) with scan+action
dedup.

Hard permission and validation rules always execute before any provider
decision; provider failures degrade to documented safe fallbacks and core
CRUD never depends on a provider.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import hashlib
import logging
import re
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from core.access import assert_parent_read_only, get_owned_record
from core.config import Settings
from core.errors import (
    InvalidStateTransition,
    NotFound,
    OcrConfirmationRequired,
    UploadTooLarge,
    UploadTypeNotAllowed,
    ValidationFailed,
)
from core.security import Principal
from core.time import today, utcnow
from models.common import SyllabusContext
from models.mindmaps import MapEdge, MapNode, MindMap
from models.notes import Note
from models.planner import RevisionItem, TaskSource
from models.scans import (
    Scan,
    ScanCreate,
    ScanIntent,
    ScanPage,
    ScanResult,
    ScanStatus,
)
from models.syllabus import SyllabusProfile
from providers import get_answer_provider, get_decision_provider, get_ocr_provider
from providers.base import AnswerProvider, DecisionProvider, OcrProvider, safe_decide
from repositories.base import Repository
from services import grounding_service
from services.audit_service import record_audit
from services.syllabus_core_service import validate_syllabus_context

logger = logging.getLogger(__name__)

# Magic-byte signatures for accepted upload content.
_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "image/png", "png"),
    (b"\xff\xd8\xff", "image/jpeg", "jpg"),
    (b"%PDF", "application/pdf", "pdf"),
)

_MINDMAP_BRANCH_LABELS = ("Key Concepts", "Formulas", "Worked Examples")

_PROCESSABLE_STATUSES = (
    ScanStatus.pages_uploaded,
    ScanStatus.confirmation_required,
    ScanStatus.confirmed,
)


# ---------------------------------------------------------------------------
# Creation and retrieval
# ---------------------------------------------------------------------------

def create_scan(repo: Repository, principal: Principal, payload: ScanCreate) -> Scan:
    assert_parent_read_only(principal)
    owner_id = principal.user_id

    context = SyllabusContext(
        syllabus_id=payload.syllabus_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        topic_id=payload.topic_id,
    )
    profile = repo.first(SyllabusProfile, student_id=owner_id)
    # Hard validation rule executes before any provider decision.
    validate_syllabus_context(repo, context, profile)

    scan = Scan.new(
        "scan",
        owner_id=owner_id,
        intent=payload.intent,
        syllabus_id=payload.syllabus_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        topic_id=payload.topic_id,
    )
    repo.put(scan)

    relevance = safe_decide(
        get_decision_provider(),
        "syllabus_relevance",
        {"syllabus_id": payload.syllabus_id, "subject_id": payload.subject_id},
    )
    record_audit(
        repo,
        principal.user_id,
        "scan.create",
        "scan",
        scan.id,
        details={"intent": scan.intent.value, "syllabus_relevance": relevance.outcome},
    )
    return scan


def get_scan(repo: Repository, principal: Principal, scan_id: str) -> Scan:
    return get_owned_record(repo, Scan, scan_id, principal)


# ---------------------------------------------------------------------------
# Page upload
# ---------------------------------------------------------------------------

def _detect_content_type(content: bytes) -> Optional[Tuple[str, str]]:
    """Return (content_type, extension) from magic bytes, or None."""
    for magic, content_type, extension in _SIGNATURES:
        if content.startswith(magic):
            return content_type, extension
    return None


def upload_page(
    repo: Repository,
    principal: Principal,
    settings: Settings,
    scan_id: str,
    content: bytes,
    page_number: Optional[int] = None,
) -> ScanPage:
    scan = get_owned_record(repo, Scan, scan_id, principal)

    detected = _detect_content_type(content or b"")
    if detected is None:
        raise UploadTypeNotAllowed(
            details={"allowed": ["image/png", "image/jpeg", "application/pdf"]},
            message="Uploaded content is not a recognized PNG, JPEG, or PDF.",
        )
    content_type, extension = detected

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise UploadTooLarge(
            details={"size_bytes": len(content), "max_bytes": max_bytes},
        )

    if scan.page_count >= settings.max_scan_pages:
        raise ValidationFailed(
            message="MAX_SCAN_PAGES",
            details={
                "code": "MAX_SCAN_PAGES",
                "max_scan_pages": settings.max_scan_pages,
            },
        )

    if page_number is None:
        page_number = scan.page_count + 1
    if page_number < 1:
        raise ValidationFailed(details={"field": "page_number"})

    upload_dir = Path(settings.local_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    storage_name = (
        f"scan_{scan.id}_p{page_number}_{secrets.token_hex(4)}.{extension}"
    )
    (upload_dir / storage_name).write_bytes(content)

    page = ScanPage.new(
        "pg",
        scan_id=scan.id,
        page_number=page_number,
        storage_name=storage_name,
        content_type=content_type,
        size_bytes=len(content),
        checksum=hashlib.sha256(content).hexdigest(),
    )
    repo.put(page)

    scan.page_count += 1
    if scan.status == ScanStatus.created:
        scan.status = ScanStatus.pages_uploaded
    scan.touch()
    repo.put(scan)

    record_audit(
        repo,
        principal.user_id,
        "scan.page.upload",
        "scan",
        scan.id,
        details={"page_number": page_number, "size_bytes": len(content)},
    )
    return page


# ---------------------------------------------------------------------------
# OCR processing and confirmation
# ---------------------------------------------------------------------------

def _run_ocr(
    repo: Repository,
    settings: Settings,
    scan: Scan,
    provider: Optional[OcrProvider] = None,
) -> Tuple[str, List[Dict]]:
    ocr = provider or get_ocr_provider()
    pages = repo.find(ScanPage, scan_id=scan.id)
    pages.sort(key=lambda page: page.page_number)

    texts: List[str] = []
    regions: List[Dict] = []
    upload_dir = Path(settings.local_upload_dir)
    for page in pages:
        path = upload_dir / page.storage_name
        data = path.read_bytes() if path.exists() else b""
        result = ocr.extract_text(data, page.page_number)
        texts.append(result.text)
        regions.extend(result.uncertain_regions)
    return "\n\n".join(texts), regions


def _apply_ocr_outcome(scan: Scan, regions: List[Dict], decision_outcome: str) -> None:
    if decision_outcome == "confirmation_required" or regions:
        scan.status = ScanStatus.confirmation_required
        scan.confirmation_required = True
    else:
        scan.status = ScanStatus.confirmed
        scan.confirmation_required = False


def process_scan(
    repo: Repository,
    principal: Principal,
    settings: Settings,
    scan_id: str,
    provider: Optional[OcrProvider] = None,
) -> Scan:
    scan = get_owned_record(repo, Scan, scan_id, principal)

    if scan.page_count < 1:
        raise ValidationFailed(message="Scan has no pages to process.")
    if scan.status not in _PROCESSABLE_STATUSES:
        raise InvalidStateTransition(
            details={"status": scan.status.value},
            message="This scan cannot be processed in its current state.",
        )

    scan.status = ScanStatus.processing
    repo.put(scan)

    text, regions = _run_ocr(repo, settings, scan, provider)
    scan.ocr_text = text
    scan.ocr_regions = regions

    decision = safe_decide(
        get_decision_provider(),
        "ocr_confirmation",
        {"scan_id": scan.id, "uncertain_regions": regions},
    )
    _apply_ocr_outcome(scan, regions, decision.outcome)
    scan.touch()
    repo.put(scan)

    record_audit(
        repo,
        principal.user_id,
        "scan.process",
        "scan",
        scan.id,
        details={
            "page_count": scan.page_count,
            "confirmation_required": scan.confirmation_required,
            "decision": decision.outcome,
        },
    )
    return scan


def get_ocr(repo: Repository, principal: Principal, scan_id: str) -> Dict:
    scan = get_owned_record(repo, Scan, scan_id, principal)
    return {
        "scan_id": scan.id,
        "text": scan.ocr_text,
        "uncertain_regions": scan.ocr_regions,
        "confirmation_required": scan.confirmation_required,
        "status": scan.status,
    }


def confirm_ocr(
    repo: Repository, principal: Principal, scan_id: str, text: str
) -> Scan:
    scan = get_owned_record(repo, Scan, scan_id, principal)

    if scan.status != ScanStatus.confirmation_required:
        raise InvalidStateTransition(
            details={"status": scan.status.value},
            message="OCR output can only be confirmed when confirmation is required.",
        )

    scan.ocr_text = text
    scan.confirmation_required = False
    scan.status = ScanStatus.confirmed
    scan.confirmed_at = utcnow()
    scan.touch()
    repo.put(scan)

    record_audit(
        repo,
        principal.user_id,
        "scan.confirm",
        "scan",
        scan.id,
        details={"status": scan.status.value},
    )
    return scan


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _require_executable(scan: Scan) -> None:
    if scan.confirmation_required or scan.status == ScanStatus.confirmation_required:
        raise OcrConfirmationRequired(
            details={"scan_id": scan.id},
            message="OCR output must be confirmed before this scan can be executed.",
        )
    if scan.status not in (ScanStatus.confirmed, ScanStatus.executed):
        raise InvalidStateTransition(
            details={"status": scan.status.value},
            message="Scan must be confirmed before execution.",
        )


def _summarize(text: str) -> Dict:
    stripped = (text or "").strip()
    sentences = re.split(r"(?<=[.!?])\s+", stripped) if stripped else []
    summary = sentences[0] if sentences and sentences[0] else stripped
    return {"summary": summary, "source_words": len(stripped.split())}


def execute_scan(
    repo: Repository,
    principal: Principal,
    settings: Settings,
    scan_id: str,
    steps: Optional[List[str]] = None,
    answer_provider: Optional[AnswerProvider] = None,
    decision_provider: Optional[DecisionProvider] = None,
) -> Tuple[Scan, ScanResult]:
    scan = get_owned_record(repo, Scan, scan_id, principal)

    if scan.status == ScanStatus.pages_uploaded:
        text, regions = _run_ocr(repo, settings, scan)
        scan.ocr_text = text
        scan.ocr_regions = regions
        decision = safe_decide(
            decision_provider or get_decision_provider(),
            "ocr_confirmation",
            {"scan_id": scan.id, "uncertain_regions": regions},
        )
        _apply_ocr_outcome(scan, regions, decision.outcome)
        scan.touch()
        repo.put(scan)

    _require_executable(scan)

    ocr_text = scan.ocr_text or ""
    grounding_status: Optional[str] = None
    verification_status: Optional[str] = None
    citations: List[Dict] = []

    if scan.intent == ScanIntent.solve:
        answer = grounding_service.ground(
            repo, ocr_text, "solve", provider=answer_provider, actor_id=principal.user_id
        )
        payload = {
            "question": scan.ocr_text,
            "final_answer": answer.final_answer,
            "steps": answer.steps,
            "subject": answer.subject,
            "chapter": answer.chapter,
            "topic": answer.topic,
            "clarification": answer.clarification,
        }
        grounding_status = answer.grounding_status
        verification_status = answer.verification_status
        citations = answer.citations
    elif scan.intent == ScanIntent.check_steps:
        if not steps:
            raise ValidationFailed(
                details={"field": "steps"},
                message="check_steps requires a non-empty steps list.",
            )
        checked = (answer_provider or get_answer_provider()).check_steps(steps)
        payload = {
            "verdict": checked.verdict,
            "issues": checked.issues,
            "checked_steps": list(steps),
        }
        verification_status = "checked_by_mock_rule"
    elif scan.intent == ScanIntent.digitize:
        payload = {
            "text": scan.ocr_text,
            "page_count": scan.page_count,
            "language": "en",
        }
    elif scan.intent == ScanIntent.summarize:
        payload = _summarize(ocr_text)
    elif scan.intent == ScanIntent.mindmap:
        payload = {
            "root_label": ocr_text[:40],
            "branches": list(_MINDMAP_BRANCH_LABELS) + ["Common Mistakes"],
        }
    elif scan.intent == ScanIntent.revision_tasks:
        root = ocr_text[:40] or scan.intent.value
        payload = {
            "tasks": [
                {
                    "title": f"Revise: {root}",
                    "due_in_days": 1,
                    "duration_minutes": 30,
                },
                {
                    "title": "Practice similar problems",
                    "due_in_days": 3,
                    "duration_minutes": 45,
                },
                {
                    "title": "Attempt a timed checkpoint quiz",
                    "due_in_days": 7,
                    "duration_minutes": 20,
                },
            ]
        }
    else:  # pragma: no cover - ScanIntent is exhaustive
        raise ValidationFailed(details={"intent": str(scan.intent)})

    scan.status = ScanStatus.executed
    scan.executed_at = utcnow()
    scan.touch()
    repo.put(scan)

    # Replace any previous result for the same scan + intent.
    for previous in repo.find(ScanResult, scan_id=scan.id, intent=scan.intent):
        repo.delete(ScanResult, previous.id)
    result = ScanResult.new(
        "scres",
        scan_id=scan.id,
        intent=scan.intent,
        payload=payload,
        grounding_status=grounding_status,
        verification_status=verification_status,
        citations=citations,
    )
    repo.put(result)

    record_audit(
        repo,
        principal.user_id,
        "scan.execute",
        "scan",
        scan.id,
        details={
            "intent": scan.intent.value,
            "verification_status": verification_status,
        },
    )
    return scan, result


def get_result(repo: Repository, principal: Principal, scan_id: str) -> ScanResult:
    scan = get_owned_record(repo, Scan, scan_id, principal)
    results = repo.find(ScanResult, scan_id=scan.id)
    if not results:
        raise NotFound("No execution result exists for this scan.")
    return max(results, key=lambda item: (item.updated_at, item.created_at))


# ---------------------------------------------------------------------------
# Result actions (each creates at most one resource per scan)
# ---------------------------------------------------------------------------

def _require_executed(scan: Scan) -> None:
    if scan.status != ScanStatus.executed:
        raise InvalidStateTransition(
            details={"status": scan.status.value},
            message="Scan must be executed before this action.",
        )


def _latest_result(repo: Repository, scan: Scan) -> Optional[ScanResult]:
    results = repo.find(ScanResult, scan_id=scan.id)
    if not results:
        return None
    return max(results, key=lambda item: (item.updated_at, item.created_at))


def _format_result_body(scan: Scan, result: Optional[ScanResult]) -> str:
    lines = [f"# Scan result: {scan.intent.value}", ""]
    if result is not None:
        for key, value in result.payload.items():
            lines.append(f"**{key}**: {value}")
            lines.append("")
    return "\n".join(lines).strip()


def save_note(repo: Repository, principal: Principal, scan_id: str) -> Tuple[Note, bool]:
    scan = get_owned_record(repo, Scan, scan_id, principal)
    _require_executed(scan)

    existing = repo.first(Note, source="scan", source_id=scan.id)
    if existing is not None:
        return existing, False

    result = _latest_result(repo, scan)
    base = (scan.ocr_text or "").strip().replace("\n", " ")[:60]
    title = f"{scan.intent.value}: {base}" if base else f"Scan note ({scan.intent.value})"
    note = Note.new(
        "note",
        owner_id=scan.owner_id,
        title=title,
        body=_format_result_body(scan, result),
        ocr_text=scan.ocr_text,
        source="scan",
        source_id=scan.id,
        syllabus_id=scan.syllabus_id,
        subject_id=scan.subject_id,
        chapter_id=scan.chapter_id,
        topic_id=scan.topic_id,
    )
    repo.put(note)

    record_audit(
        repo,
        principal.user_id,
        "scan.save_note",
        "note",
        note.id,
        details={"scan_id": scan.id, "intent": scan.intent.value},
    )
    return note, True


def create_mindmap(
    repo: Repository, principal: Principal, scan_id: str
) -> Tuple[MindMap, bool]:
    scan = get_owned_record(repo, Scan, scan_id, principal)
    _require_executed(scan)

    existing = repo.first(MindMap, source="scan", source_id=scan.id)
    if existing is not None:
        return existing, False

    root_label = (scan.ocr_text or "").strip()[:40] or "Scan"
    mind_map = MindMap.new(
        "map",
        owner_id=scan.owner_id,
        title=f"Scan mind map: {root_label}",
        source="scan",
        source_id=scan.id,
        syllabus_id=scan.syllabus_id,
        subject_id=scan.subject_id,
        chapter_id=scan.chapter_id,
        topic_id=scan.topic_id,
    )
    root = MapNode.new("node", map_id=mind_map.id, label=root_label, parent_id=None)
    mind_map.root_node_id = root.id
    repo.put(mind_map)
    repo.put(root)

    for label in _MINDMAP_BRANCH_LABELS:
        child = MapNode.new(
            "node", map_id=mind_map.id, label=label, parent_id=root.id
        )
        repo.put(child)
        repo.put(
            MapEdge.new(
                "edge",
                map_id=mind_map.id,
                source_node_id=root.id,
                target_node_id=child.id,
            )
        )

    record_audit(
        repo,
        principal.user_id,
        "scan.create_mindmap",
        "mindmap",
        mind_map.id,
        details={"scan_id": scan.id},
    )
    return mind_map, True


def schedule_revision(
    repo: Repository, principal: Principal, scan_id: str
) -> Tuple[RevisionItem, bool]:
    scan = get_owned_record(repo, Scan, scan_id, principal)
    _require_executed(scan)

    existing = repo.first(RevisionItem, source="scan", source_id=scan.id)
    if existing is not None:
        return existing, False

    root_label = (scan.ocr_text or "").strip()[:40] or scan.intent.value
    item = RevisionItem.new(
        "rev",
        student_id=scan.owner_id,
        title=f"Revise scan: {root_label}",
        due_date=today() + timedelta(days=3),
        source=TaskSource.scan,
        source_id=scan.id,
        syllabus_id=scan.syllabus_id,
        subject_id=scan.subject_id,
        chapter_id=scan.chapter_id,
        topic_id=scan.topic_id,
    )
    repo.put(item)

    record_audit(
        repo,
        principal.user_id,
        "scan.schedule_revision",
        "revision_item",
        item.id,
        details={"scan_id": scan.id, "due_date": item.due_date.isoformat()},
    )
    return item, True
