"""
Communication Domain Models

Simulated one-way in-app calls, per-recipient deliveries, messages, and
communication preferences. No telephony, WebRTC, or microphone handling.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from models.common import Entity


class CallSenderType(str, Enum):
    teacher = "teacher"
    ai_agent = "ai_agent"
    admin = "admin"


class CallStatus(str, Enum):
    active = "active"
    cancelled = "cancelled"


class SimulatedCall(Entity):
    __collection__ = "simulated_calls"

    sender_id: str
    sender_type: CallSenderType
    recipient_ids: List[str] = Field(default_factory=list)
    title: str
    subject: Optional[str] = None
    transcript: str
    speech_asset_id: Optional[str] = None

    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None

    content_hash: str
    status: CallStatus = CallStatus.active
    quiet_hours_deferred: bool = False
    deduplicated_from: Optional[str] = None
    created_by: str


class DeliveryState(str, Enum):
    scheduled = "scheduled"
    ringing = "ringing"
    accepted = "accepted"
    playing = "playing"
    completed = "completed"
    dismissed = "dismissed"
    missed = "missed"
    failed = "failed"
    cancelled = "cancelled"


class CallDelivery(Entity):
    __collection__ = "call_deliveries"

    call_id: str
    recipient_id: str
    state: DeliveryState = DeliveryState.scheduled
    event_version: int = 0
    state_timestamps: Dict[str, datetime] = Field(default_factory=dict)


class MessageKind(str, Enum):
    call_delivery = "call_delivery"
    call_history = "call_history"
    announcement = "announcement"
    system = "system"


class Message(Entity):
    __collection__ = "messages"

    recipient_id: str
    sender_id: Optional[str] = None
    kind: MessageKind = MessageKind.system
    title: str
    body: str = ""
    call_id: Optional[str] = None
    delivery_id: Optional[str] = None
    read: bool = False
    read_at: Optional[datetime] = None


class CommunicationPreferences(Entity):
    __collection__ = "communication_preferences"

    user_id: str
    quiet_hours_enabled: bool = True
    quiet_hours_start: int = 21
    quiet_hours_end: int = 7
    max_calls_per_day: int = 5
    allow_ai_calls: bool = True


# ---------------------------------------------------------------------------
# API schemas (requests and responses)
# ---------------------------------------------------------------------------

from datetime import date  # noqa: E402

from pydantic import BaseModel  # noqa: E402

from models.planner import TaskType  # noqa: E402


class CallCreate(BaseModel):
    """POST /simulated-calls request body (transcript-only in-app announcement)."""

    recipient_ids: List[str] = Field(..., min_length=1, max_length=50)
    title: str
    subject: Optional[str] = None
    transcript: str
    speech_asset_id: Optional[str] = None
    sender_type: CallSenderType = CallSenderType.teacher
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None


class DeliveryRef(BaseModel):
    """Compact delivery view embedded in call responses."""

    delivery_id: str
    recipient_id: str
    state: DeliveryState


class DeliveryOut(BaseModel):
    """Full per-recipient delivery view returned by /me transition endpoints."""

    delivery_id: str
    call_id: str
    recipient_id: str
    state: DeliveryState
    event_version: int
    state_timestamps: Dict[str, datetime] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CallOut(BaseModel):
    """Simulated call with its per-recipient deliveries."""

    id: str
    sender_id: str
    sender_type: CallSenderType
    recipient_ids: List[str] = Field(default_factory=list)
    title: str
    subject: Optional[str] = None
    transcript: str
    speech_asset_id: Optional[str] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    status: CallStatus
    deduplicated: bool = False
    deduplicated_from: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deliveries: List[DeliveryRef] = Field(default_factory=list)


class MyDeliveryOut(BaseModel):
    """Recipient-scoped delivery row for GET /me/simulated-calls."""

    delivery_id: str
    call_id: str
    title: str
    state: DeliveryState
    event_version: int
    sender_id: str
    speech_asset_id: Optional[str] = None
    updated_at: datetime


class MessageOut(BaseModel):
    id: str
    recipient_id: str
    sender_id: Optional[str] = None
    kind: MessageKind
    title: str
    body: str = ""
    call_id: Optional[str] = None
    delivery_id: Optional[str] = None
    read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime


class TeacherTaskCreate(BaseModel):
    """POST /teacher/classes/{classId}/tasks request body."""

    title: str
    task_type: Optional[TaskType] = None
    duration_minutes: Optional[int] = None
    scheduled_date: Optional[date] = None
    topic_id: Optional[str] = None
    student_ids: Optional[List[str]] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None


class CreatedTaskRef(BaseModel):
    student_id: str
    task_id: str


class TeacherTaskCreateOut(BaseModel):
    created: List[CreatedTaskRef] = Field(default_factory=list)


class ResourceShareIn(BaseModel):
    """POST /teacher/classes/{classId}/resources request body."""

    title: str = ""
    body: Optional[str] = None
    note_id: Optional[str] = None


class ResourceShareOut(BaseModel):
    note_id: str
    title: str
    scope: str = "class"
    class_id: str


class ProgressSummaryOut(BaseModel):
    student_id: str
    name: str
    topics_total: int
    topics_covered: int
    percent: float


class ReviewOut(BaseModel):
    review_id: str
    kind: str
    student_id: str
    scan_id: str
    verification_status: str
    created_at: datetime


class ReviewResolveIn(BaseModel):
    resolution: str
    correction: Optional[str] = None


class ReviewResolveOut(BaseModel):
    review_id: str
    resolved: bool
    resolved_at: datetime


class ChildOut(BaseModel):
    student_id: str
    name: str
    target_exam: Optional[str] = None
    target_year: Optional[int] = None
    percent: float


class SubjectTaskSummary(BaseModel):
    subject_id: str
    tasks_total: int
    tasks_completed: int


class ReportOut(BaseModel):
    student_id: str
    period_days: int = 7
    generated_at: datetime
    tasks_total: int
    tasks_completed: int
    completion_percent: float
    minutes_planned: int
    minutes_completed: int
    per_subject: List[SubjectTaskSummary] = Field(default_factory=list)


class PrefsOut(BaseModel):
    user_id: str
    quiet_hours_enabled: bool
    quiet_hours_start: int
    quiet_hours_end: int
    max_calls_per_day: int
    allow_ai_calls: bool


class PrefsUpdate(BaseModel):
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[int] = Field(None, ge=0, le=23)
    quiet_hours_end: Optional[int] = Field(None, ge=0, le=23)
    max_calls_per_day: Optional[int] = Field(None, ge=1, le=20)
    allow_ai_calls: Optional[bool] = None
