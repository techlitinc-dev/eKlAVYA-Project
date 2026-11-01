"""
Planner Router

Planner tasks, today's progress, deterministic plan generation/replanning,
study sessions, and revision items. All paths are registered under /api/v1.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.config import Settings, get_settings
from core.security import Principal, get_current_principal
from dependencies import (
    IdempotencyManager,
    PaginationParams,
    get_pagination,
    get_repository,
    paginate,
)
from models.common import Page
from models.planner import (
    CompleteTaskIn,
    GenerateIn,
    GenerationJobOut,
    ReplanIn,
    RescheduleIn,
    RevisionItemOut,
    SessionCreate,
    SessionOut,
    SessionPatch,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    TodayOut,
)
from repositories.base import Repository
from services import planner_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Planner"])


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@router.get(
    "/planner/today",
    response_model=TodayOut,
    summary="Get today's tasks and progress",
)
def get_today(
    student_id: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> TodayOut:
    return TodayOut(**service.get_today(repo, principal, student_id))


@router.get(
    "/planner/tasks",
    response_model=Page[TaskOut],
    summary="List planner tasks with composable filters",
)
def list_tasks(
    student_id: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None, alias="from"),
    to_date: Optional[date] = Query(None, alias="to"),
    status_filter: Optional[str] = Query(None, alias="status"),
    subject_id: Optional[str] = Query(None, alias="subjectId"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[TaskOut]:
    items = service.list_tasks(
        repo, principal, student_id, from_date, to_date, status_filter, subject_id
    )
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[TaskOut](items=page, next_cursor=next_cursor)


@router.post(
    "/planner/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a planner task",
)
def create_task(
    payload: TaskCreate,
    request: Request,
    response: Response,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    student_id: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("planner.task.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    task = service.create_task(repo, principal, body, student_id or payload.student_id)
    if idem_key:
        manager.store(
            "planner.task.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(task),
        )
    return task


@router.get(
    "/planner/tasks/{task_id}",
    response_model=TaskOut,
    summary="Get a planner task",
)
def get_task(
    task_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> TaskOut:
    return service.get_task(repo, principal, task_id)


@router.patch(
    "/planner/tasks/{task_id}",
    response_model=TaskOut,
    summary="Update a planner task (optimistic concurrency)",
)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> TaskOut:
    return service.update_task(repo, principal, task_id, payload.model_dump())


@router.post(
    "/planner/tasks/{task_id}/complete",
    response_model=TaskOut,
    summary="Mark a planner task completed",
)
def complete_task(
    task_id: str,
    payload: Optional[CompleteTaskIn] = None,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump() if payload is not None else {}
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("planner.task.complete", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    task = service.complete_task(
        repo, principal, task_id, payload.actual_minutes if payload else None
    )
    if idem_key:
        manager.store(
            "planner.task.complete",
            idem_key,
            body,
            status.HTTP_200_OK,
            jsonable_encoder(task),
        )
    return task


@router.post(
    "/planner/tasks/{task_id}/reschedule",
    response_model=TaskOut,
    summary="Reschedule a planner task",
)
def reschedule_task(
    task_id: str,
    payload: RescheduleIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> TaskOut:
    return service.reschedule_task(repo, principal, task_id, payload.model_dump())


# ---------------------------------------------------------------------------
# Generation / replanning
# ---------------------------------------------------------------------------

@router.post(
    "/planner/generate",
    response_model=GenerationJobOut,
    summary="Generate a deterministic study plan",
)
def generate(
    payload: GenerateIn,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("planner.generate", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    job = service.generate(repo, principal, payload.days)
    if idem_key:
        manager.store(
            "planner.generate",
            idem_key,
            body,
            status.HTTP_200_OK,
            jsonable_encoder(job),
        )
    return job


@router.post(
    "/planner/replan",
    response_model=GenerationJobOut,
    summary="Re-pack eligible pending tasks forward",
)
def replan(
    payload: ReplanIn,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("planner.replan", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    job = service.replan(repo, principal, payload.from_date)
    if idem_key:
        manager.store(
            "planner.replan",
            idem_key,
            body,
            status.HTTP_200_OK,
            jsonable_encoder(job),
        )
    return job


@router.get(
    "/planner/generation-jobs/{job_id}",
    response_model=GenerationJobOut,
    summary="Get a generation job",
)
def get_generation_job(
    job_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> GenerationJobOut:
    return service.get_generation_job(repo, principal, job_id)


# ---------------------------------------------------------------------------
# Study sessions
# ---------------------------------------------------------------------------

@router.post(
    "/study-sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a study session",
)
def create_session(
    payload: SessionCreate,
    request: Request,
    response: Response,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("session.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    session = service.create_session(repo, principal, payload.task_id)
    if idem_key:
        manager.store(
            "session.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(session),
        )
    return session


@router.patch(
    "/study-sessions/{session_id}",
    response_model=SessionOut,
    summary="Drive a study session state machine",
)
def patch_session(
    session_id: str,
    payload: SessionPatch,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> SessionOut:
    return service.patch_session(repo, principal, session_id, payload.action.value)


# ---------------------------------------------------------------------------
# Revision items
# ---------------------------------------------------------------------------

@router.get(
    "/revision/due",
    response_model=Page[RevisionItemOut],
    summary="List due revision items",
)
def list_due_revisions(
    student_id: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[RevisionItemOut]:
    items = service.list_due_revisions(repo, principal, student_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[RevisionItemOut](items=page, next_cursor=next_cursor)


@router.post(
    "/revision/{revision_id}/complete",
    response_model=RevisionItemOut,
    summary="Mark a revision item completed",
)
def complete_revision(
    revision_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> RevisionItemOut:
    return service.complete_revision(repo, principal, revision_id)
