"""
Planner Domain Models

Planner tasks, study sessions, deterministic generation jobs, and revision
items.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from models.common import Entity


class TaskType(str, Enum):
    learn = "learn"
    practice = "practice"
    revision = "revision"
    test = "test"
    homework = "homework"
    other = "other"


class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    skipped = "skipped"
    cancelled = "cancelled"


class TaskSource(str, Enum):
    manual = "manual"
    generated = "generated"
    teacher = "teacher"
    scan = "scan"
    system = "system"


class PlannerTask(Entity):
    __collection__ = "planner_tasks"

    student_id: str
    title: str
    task_type: TaskType = TaskType.practice
    status: TaskStatus = TaskStatus.pending

    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None

    scheduled_date: date
    start_minute: int = 0  # minutes after local midnight
    duration_minutes: int = 60

    locked: bool = False
    locked_by: Optional[str] = None
    teacher_fields: List[str] = Field(default_factory=list)

    completed_at: Optional[datetime] = None
    actual_minutes: Optional[int] = None

    version: int = 1
    source: TaskSource = TaskSource.manual
    source_id: Optional[str] = None
    created_by: str = ""
    reschedule_history: List[Dict] = Field(default_factory=list)


class SessionStatus(str, Enum):
    not_started = "not_started"
    active = "active"
    paused = "paused"
    finished = "finished"


class StudySession(Entity):
    __collection__ = "study_sessions"

    student_id: str
    task_id: Optional[str] = None
    status: SessionStatus = SessionStatus.not_started
    intervals: List[Dict] = Field(default_factory=list)  # {started_at, ended_at?}
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_seconds: int = 0
    completion_linked: bool = False


class GenerationJob(Entity):
    __collection__ = "generation_jobs"

    student_id: str
    kind: str  # "generate" | "replan"
    status: str = "pending"  # pending | running | completed | failed
    explanation: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    result: Dict = Field(default_factory=dict)
    completed_at: Optional[datetime] = None


class RevisionStatus(str, Enum):
    due = "due"
    completed = "completed"


class RevisionItem(Entity):
    __collection__ = "revision_items"

    student_id: str
    title: str
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    due_date: date
    status: RevisionStatus = RevisionStatus.due
    completed_at: Optional[datetime] = None
    source: TaskSource = TaskSource.manual
    source_id: Optional[str] = None
    linked_task_id: Optional[str] = None


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------

from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    """POST /planner/tasks request body."""

    title: str = Field(..., min_length=1, max_length=200)
    task_type: TaskType = TaskType.practice
    scheduled_date: date
    start_minute: int = Field(0, ge=0, le=24 * 60 - 1)
    duration_minutes: int = Field(..., ge=1, le=720)
    student_id: Optional[str] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None
    locked: bool = False
    locked_by: Optional[str] = None
    teacher_fields: List[str] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    """PATCH /planner/tasks/{taskId} request body (optimistic concurrency)."""

    version: int = Field(..., ge=1)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    task_type: Optional[TaskType] = None
    scheduled_date: Optional[date] = None
    start_minute: Optional[int] = Field(None, ge=0, le=24 * 60 - 1)
    duration_minutes: Optional[int] = Field(None, ge=1, le=720)
    status: Optional[TaskStatus] = None
    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None


class TaskOut(PlannerTask):
    """API view of a planner task (mirrors the stored entity)."""

    model_config = ConfigDict(from_attributes=True)


class CompleteTaskIn(BaseModel):
    """POST /planner/tasks/{taskId}/complete request body."""

    actual_minutes: Optional[int] = Field(None, ge=0)


class RescheduleIn(BaseModel):
    """POST /planner/tasks/{taskId}/reschedule request body."""

    scheduled_date: date
    start_minute: Optional[int] = Field(None, ge=0, le=24 * 60 - 1)
    reason: Optional[str] = None


class GenerateIn(BaseModel):
    """POST /planner/generate request body."""

    days: int = Field(7, ge=1, le=30)


class ReplanIn(BaseModel):
    """POST /planner/replan request body."""

    from_date: Optional[date] = None


class TodayProgress(BaseModel):
    total: int
    completed: int
    percent: float
    minutes_planned: int
    minutes_completed: int


class TodayOut(BaseModel):
    date: date
    progress: TodayProgress
    tasks: List[TaskOut] = Field(default_factory=list)


class SessionCreate(BaseModel):
    """POST /study-sessions request body."""

    task_id: Optional[str] = None


class SessionAction(str, Enum):
    start = "start"
    pause = "pause"
    resume = "resume"
    finish = "finish"


class SessionPatch(BaseModel):
    """PATCH /study-sessions/{sessionId} request body."""

    action: SessionAction
    version: Optional[int] = None


class SessionOut(StudySession):
    """API view of a study session (mirrors the stored entity)."""

    model_config = ConfigDict(from_attributes=True)


class GenerationJobOut(GenerationJob):
    """API view of a generation job (mirrors the stored entity)."""

    model_config = ConfigDict(from_attributes=True)


class RevisionItemOut(RevisionItem):
    """API view of a revision item (mirrors the stored entity)."""

    model_config = ConfigDict(from_attributes=True)
