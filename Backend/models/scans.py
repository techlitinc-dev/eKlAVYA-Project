"""
Scan & Solve Domain Models

Scans, uploaded pages, and per-intent execution results.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from models.common import Entity


class ScanIntent(str, Enum):
    solve = "solve"
    check_steps = "check_steps"
    digitize = "digitize"
    summarize = "summarize"
    mindmap = "mindmap"
    revision_tasks = "revision_tasks"


class ScanStatus(str, Enum):
    created = "created"
    pages_uploaded = "pages_uploaded"
    processing = "processing"
    confirmation_required = "confirmation_required"
    confirmed = "confirmed"
    executed = "executed"
    failed = "failed"


class Scan(Entity):
    __collection__ = "scans"

    owner_id: str
    intent: ScanIntent
    status: ScanStatus = ScanStatus.created

    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None

    page_count: int = 0
    ocr_text: Optional[str] = None
    ocr_regions: List[Dict] = Field(default_factory=list)  # uncertain regions
    confirmation_required: bool = False
    confirmed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    content_hash: Optional[str] = None


class ScanPage(Entity):
    __collection__ = "scan_pages"

    scan_id: str
    page_number: int
    storage_name: str
    content_type: str
    size_bytes: int
    checksum: str


class ScanResult(Entity):
    __collection__ = "scan_results"

    scan_id: str
    intent: ScanIntent
    payload: Dict = Field(default_factory=dict)
    grounding_status: Optional[str] = None
    verification_status: Optional[str] = None
    citations: List[Dict] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API schemas (request/response contracts)
# ---------------------------------------------------------------------------

class ScanCreate(BaseModel):
    intent: ScanIntent
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None


class ScanOut(BaseModel):
    id: str
    owner_id: str
    intent: ScanIntent
    status: ScanStatus
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    page_count: int = 0
    ocr_text: Optional[str] = None
    confirmation_required: bool = False
    confirmed_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PageOut(BaseModel):
    """Asset metadata for an uploaded page (never a filesystem path)."""

    page_number: int
    content_type: str
    size_bytes: int
    checksum: str


class OcrOut(BaseModel):
    scan_id: str
    text: Optional[str] = None
    uncertain_regions: List[Dict] = Field(default_factory=list)
    confirmation_required: bool = False
    status: ScanStatus


class OcrConfirmIn(BaseModel):
    text: str = Field(min_length=1)


class ExecuteIn(BaseModel):
    steps: Optional[List[str]] = None


class ExecutionOut(BaseModel):
    scan_id: str
    intent: ScanIntent
    status: ScanStatus
    payload: Dict = Field(default_factory=dict)
    grounding_status: Optional[str] = None
    verification_status: Optional[str] = None
    citations: List[Dict] = Field(default_factory=list)


class ResultOut(BaseModel):
    scan_id: str
    intent: ScanIntent
    payload: Dict = Field(default_factory=dict)
    grounding_status: Optional[str] = None
    verification_status: Optional[str] = None
    citations: List[Dict] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
