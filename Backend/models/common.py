"""
Common Models

Shared primitives used by every eKlAVYA domain:
- Entity base with id/timestamps and repository collection binding
- Error envelope schemas
- Pagination envelope
- Syllabus context reference
- Audit entry
- Development identity and relationship records

Author: eKlAVYA Backend
Version: 1.0.0
"""

from datetime import datetime
from typing import Any, ClassVar, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from core.ids import new_id
from core.time import utcnow


class Entity(BaseModel):
    """
    Base class for persisted entities.

    Subclasses set ``__collection__``; the repository uses it to route
    storage. IDs are server-generated; timestamps are UTC.
    """

    __collection__: ClassVar[str] = "entities"

    model_config = ConfigDict(use_enum_values=False)

    id: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    @classmethod
    def new(cls, prefix: str, **kwargs):
        return cls(id=kwargs.pop("id", new_id(prefix)), **kwargs)

    def touch(self) -> None:
        self.updated_at = utcnow()


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class ErrorEnvelope(BaseModel):
    error: ErrorBody


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Cursor-paginated list response."""

    items: List[T] = Field(default_factory=list)
    next_cursor: Optional[str] = None


class SyllabusContext(BaseModel):
    """
    Optional syllabus binding for academic records.

    Validation rule: when a topic is supplied it must belong to the supplied
    chapter; the chapter to the subject; the subject to the syllabus. Services
    validate the full chain against the active syllabus.
    """

    syllabus_id: Optional[str] = None
    subject_id: Optional[str] = None
    chapter_id: Optional[str] = None
    topic_id: Optional[str] = None

    def is_empty(self) -> bool:
        return not any(
            [self.syllabus_id, self.subject_id, self.chapter_id, self.topic_id]
        )


class AuditEntry(Entity):
    """Record of an important action; never stores private bodies or secrets."""

    __collection__ = "audit_log"

    actor_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class Identity(Entity):
    """Development/test user record."""

    __collection__ = "identities"

    role: str
    name: str


class ClassRoom(Entity):
    """Teacher-to-student assignment through a class."""

    __collection__ = "classes"

    name: str
    teacher_ids: List[str] = Field(default_factory=list)
    student_ids: List[str] = Field(default_factory=list)


class ParentLink(Entity):
    """Parent-to-child linkage."""

    __collection__ = "parent_links"

    parent_id: str
    student_id: str
