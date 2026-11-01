"""
Notes Domain Models

Notes with versioning, attachments, links, sharing scope, and OCR text.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from models.common import Entity


class NoteStatus(str, Enum):
    active = "active"
    archived = "archived"


class ShareLevel(str, Enum):
    private = "private"
    class_share = "class"
    link = "link"


class ShareScope(BaseModel):
    level: ShareLevel = ShareLevel.private
    audience: List[str] = Field(default_factory=list)
    token: Optional[str] = None


class Attachment(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_name: str
    uploaded_at: datetime


class Note(Entity):
    __collection__ = "notes"

    owner_id: str
    title: str
    body: str = ""
    tags: List[str] = Field(default_factory=list)
    ocr_text: Optional[str] = None

    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None

    status: NoteStatus = NoteStatus.active
    version: int = 1
    attachments: List[Attachment] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    share_scope: ShareScope = Field(default_factory=ShareScope)

    source: str = "manual"  # manual | scan | ai_action
    source_id: Optional[str] = None


class NoteVersion(Entity):
    __collection__ = "note_versions"

    note_id: str
    version: int
    title: str
    body: str
    created_by: str
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# API schemas (request/response contracts)
# ---------------------------------------------------------------------------

AI_ACTION_LITERAL = Literal[
    "summarize",
    "structure",
    "extract_formulas",
    "extract_mistakes",
    "generate_mindmap",
    "create_planner_tasks",
]


class NoteCreate(BaseModel):
    """POST /notes request body."""

    title: str = Field(..., min_length=1)
    body: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    ocr_text: Optional[str] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    source: Optional[Literal["manual", "scan", "ai_action"]] = None


class NoteUpdate(BaseModel):
    """PATCH /notes/{noteId} request body (optimistic concurrency)."""

    version: int = Field(..., ge=1)
    title: Optional[str] = Field(None, min_length=1)
    body: Optional[str] = None
    tags: Optional[List[str]] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    status: Optional[NoteStatus] = None


class NoteOut(BaseModel):
    """Safe API projection of a Note (mirrors the entity, no internal bits)."""

    id: str
    created_at: datetime
    updated_at: datetime
    owner_id: str
    title: str
    body: str
    tags: List[str]
    ocr_text: Optional[str] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    status: NoteStatus
    version: int
    attachments: List[Attachment] = Field(default_factory=list)
    links: List[str] = Field(default_factory=list)
    share_scope: ShareScope = Field(default_factory=ShareScope)
    source: str = "manual"
    source_id: Optional[str] = None


class RestoreIn(BaseModel):
    """POST /notes/{noteId}/restore request body."""

    version: int = Field(..., ge=1)


class LinkIn(BaseModel):
    """POST /notes/{noteId}/links request body."""

    linked_note_id: str = Field(..., min_length=1)


class ExportIn(BaseModel):
    """POST /notes/{noteId}/export request body."""

    format: Literal["txt", "pdf"] = "txt"


class ExportOut(BaseModel):
    """POST /notes/{noteId}/export response (never exposes filesystem paths)."""

    format: str
    labelled_plain_text: bool
    storage_name: str
    size_bytes: int
    exported_at: datetime


class ShareIn(BaseModel):
    """POST /notes/{noteId}/share request body."""

    level: ShareLevel
    audience: List[str] = Field(default_factory=list)


class AiActionIn(BaseModel):
    """POST /notes/{noteId}/ai-actions request body."""

    action: AI_ACTION_LITERAL
    language: Optional[str] = None


class AiActionOut(BaseModel):
    """POST /notes/{noteId}/ai-actions response."""

    action: str
    note_version: int
    created: Dict[str, Any] = Field(default_factory=dict)
    result_preview: str
