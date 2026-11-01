"""
Syllabus Domain Models

Syllabus catalogue (syllabus -> subject -> chapter -> topic), student syllabus
profiles, and teacher syllabus templates.

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from models.common import Entity


class SyllabusStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Syllabus(Entity):
    __collection__ = "syllabi"

    name: str
    version: str
    exam: str
    status: SyllabusStatus = SyllabusStatus.published


class Subject(Entity):
    __collection__ = "subjects"

    syllabus_id: str
    name: str
    code: str


class Chapter(Entity):
    __collection__ = "chapters"

    syllabus_id: str
    subject_id: str
    name: str
    order_index: int = 0


class Topic(Entity):
    __collection__ = "topics"

    syllabus_id: str
    subject_id: str
    chapter_id: str
    name: str
    estimated_minutes: int = 60
    prerequisites: List[str] = Field(default_factory=list)


class SyllabusProfile(Entity):
    """A student's active syllabus selection and study constraints."""

    __collection__ = "syllabus_profiles"

    student_id: str
    syllabus_id: str
    target_exam: str
    target_year: int
    target_date: Optional[date] = None
    subjects: List[str] = Field(default_factory=list)
    availability: Dict[str, int] = Field(
        default_factory=lambda: {"minutes_per_day": 180, "days_per_week": 6}
    )
    preferences: Dict[str, object] = Field(default_factory=dict)
    version: int = 1


class TemplateStatus(str, Enum):
    draft = "draft"
    published = "published"


class SyllabusTemplate(Entity):
    """Teacher-authored syllabus template; publish is one-way."""

    __collection__ = "syllabus_templates"

    teacher_id: str
    name: str
    description: str = ""
    status: TemplateStatus = TemplateStatus.draft
    payload: Dict[str, object] = Field(default_factory=dict)
    published_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# API schemas
# ---------------------------------------------------------------------------


class SyllabusProfileUpdate(BaseModel):
    """PUT /me/syllabus-profile request body (optimistic concurrency)."""

    version: int = Field(..., ge=1)
    target_exam: Optional[str] = None
    target_year: Optional[int] = None
    target_date: Optional[date] = None
    subjects: Optional[List[str]] = None
    availability: Optional[Dict[str, int]] = None
    preferences: Optional[Dict[str, object]] = None


class TopicProgress(BaseModel):
    topic_id: str
    name: str
    covered: bool


class SubjectProgress(BaseModel):
    subject_id: str
    name: str
    topics_total: int
    topics_covered: int
    chapters_total: int
    chapters_covered: int
    percent: float


class SyllabusProgress(BaseModel):
    student_id: str
    syllabus_id: str
    topics_total: int
    topics_covered: int
    percent: float
    subjects: List[SubjectProgress]


class SyllabusTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    payload: Dict[str, object] = Field(default_factory=dict)
