"""
Teacher Router

Class-scoped teacher endpoints: per-student progress, task creation,
resource sharing, and scan-answer review resolution. Every endpoint
verifies class access (teacher in class teacher_ids or admin, else 404).
All paths are registered under /api/v1 by the eKlAVYA registry.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.config import Settings, get_settings
from core.errors import PermissionDenied
from core.security import Principal, get_current_principal
from dependencies import (
    IdempotencyManager,
    PaginationParams,
    get_pagination,
    get_repository,
    paginate,
)
from models.common import Page
from models.communication import (
    CreatedTaskRef,
    ProgressSummaryOut,
    ResourceShareIn,
    ResourceShareOut,
    ReviewOut,
    ReviewResolveIn,
    ReviewResolveOut,
    TeacherTaskCreate,
    TeacherTaskCreateOut,
)
from repositories.base import Repository
from services import simulated_call_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Teacher"])


def _assert_teacher_or_admin(principal: Principal) -> None:
    if principal.role not in ("teacher", "admin"):
        raise PermissionDenied("This action requires a teacher or admin role.")


@router.get(
    "/teacher/classes/{class_id}/progress",
    response_model=Page[ProgressSummaryOut],
    summary="Per-student syllabus progress for a class",
)
def class_progress(
    class_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
):
    _assert_teacher_or_admin(principal)
    items = service.teacher_class_progress(repo, principal, class_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[ProgressSummaryOut](items=page, next_cursor=next_cursor)


@router.post(
    "/teacher/classes/{class_id}/tasks",
    response_model=TeacherTaskCreateOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create locked planner tasks for class students (teacher)",
)
def create_class_tasks(
    class_id: str,
    payload: TeacherTaskCreate,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    _assert_teacher_or_admin(principal)
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("teacher.task.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    created = service.teacher_create_tasks(
        repo,
        principal,
        class_id,
        title=payload.title,
        task_type=payload.task_type,
        duration_minutes=payload.duration_minutes,
        scheduled_date=payload.scheduled_date,
        topic_id=payload.topic_id,
        student_ids=payload.student_ids,
        syllabus_id=payload.syllabus_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
    )
    out = TeacherTaskCreateOut(
        created=[CreatedTaskRef(**item) for item in created]
    )
    if idem_key:
        manager.store(
            "teacher.task.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(out),
        )
    return out


@router.post(
    "/teacher/classes/{class_id}/resources",
    response_model=ResourceShareOut,
    status_code=status.HTTP_201_CREATED,
    summary="Share a class-scoped resource (note) with a class",
)
def share_class_resource(
    class_id: str,
    payload: ResourceShareIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    _assert_teacher_or_admin(principal)
    return service.teacher_share_resource(
        repo,
        principal,
        class_id,
        title=payload.title,
        body=payload.body,
        note_id=payload.note_id,
    )


@router.get(
    "/teacher/reviews",
    response_model=Page[ReviewOut],
    summary="Pending scan-answer reviews for the teacher's students",
)
def list_reviews(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
):
    _assert_teacher_or_admin(principal)
    items = service.teacher_list_reviews(repo, principal)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[ReviewOut](items=page, next_cursor=next_cursor)


@router.post(
    "/teacher/reviews/{review_id}/resolve",
    response_model=ReviewResolveOut,
    summary="Resolve a pending review",
)
def resolve_review(
    review_id: str,
    payload: ReviewResolveIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    _assert_teacher_or_admin(principal)
    resolved_id, resolved_at = service.teacher_resolve_review(
        repo, principal, review_id, payload.resolution, payload.correction
    )
    return ReviewResolveOut(
        review_id=resolved_id, resolved=True, resolved_at=resolved_at
    )
