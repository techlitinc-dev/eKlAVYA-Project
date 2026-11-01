"""
Syllabus Router

eKlAVYA syllabus catalogue, student syllabus profile, progress, and teacher
template endpoints. All paths are registered under /api/v1.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
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
from models.syllabus import (
    Chapter,
    Subject,
    Syllabus,
    SyllabusProfile,
    SyllabusProfileUpdate,
    SyllabusProgress,
    SyllabusTemplate,
    SyllabusTemplateCreate,
    Topic,
)
from repositories.base import Repository
from services import syllabus_core_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Syllabus"])


def _idem(request: Request, key: Optional[str]) -> Optional[str]:
    return key


@router.get(
    "/syllabi",
    response_model=Page[Syllabus],
    summary="List syllabi",
)
def list_syllabi(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[Syllabus]:
    items = service.list_syllabi(repo)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[Syllabus](items=page, next_cursor=next_cursor)


@router.get(
    "/syllabi/{syllabus_id}",
    response_model=Syllabus,
    summary="Get a syllabus",
)
def get_syllabus(
    syllabus_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> Syllabus:
    return service.get_syllabus(repo, syllabus_id)


@router.get(
    "/syllabi/{syllabus_id}/subjects",
    response_model=Page[Subject],
    summary="List subjects in a syllabus",
)
def list_subjects(
    syllabus_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[Subject]:
    items = service.list_subjects(repo, syllabus_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[Subject](items=page, next_cursor=next_cursor)


@router.get(
    "/subjects/{subject_id}/chapters",
    response_model=Page[Chapter],
    summary="List chapters in a subject",
)
def list_chapters(
    subject_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[Chapter]:
    items = service.list_chapters(repo, subject_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[Chapter](items=page, next_cursor=next_cursor)


@router.get(
    "/chapters/{chapter_id}/topics",
    response_model=Page[Topic],
    summary="List topics in a chapter",
)
def list_topics(
    chapter_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[Topic]:
    items = service.list_topics(repo, chapter_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[Topic](items=page, next_cursor=next_cursor)


@router.get(
    "/me/syllabus-profile",
    response_model=SyllabusProfile,
    summary="Get the active syllabus profile",
)
def get_profile(
    student_id: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> SyllabusProfile:
    return service.get_profile(repo, principal, student_id)


@router.put(
    "/me/syllabus-profile",
    response_model=SyllabusProfile,
    summary="Update the active syllabus profile",
)
def update_profile(
    payload: SyllabusProfileUpdate,
    student_id: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> SyllabusProfile:
    return service.update_profile(
        repo, principal, student_id, payload.model_dump(exclude={"version"}, exclude_none=True), payload.version
    )


@router.get(
    "/me/syllabus-progress",
    response_model=SyllabusProgress,
    summary="Get syllabus progress derived from task state",
)
def get_progress(
    student_id: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> SyllabusProgress:
    return SyllabusProgress(**service.get_progress(repo, principal, student_id))


@router.post(
    "/teacher/syllabus-templates",
    response_model=SyllabusTemplate,
    status_code=status.HTTP_201_CREATED,
    summary="Create a syllabus template (teacher/admin)",
)
def create_template(
    payload: SyllabusTemplateCreate,
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
        cached = manager.replay("syllabus_template.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    template = service.create_template(
        repo, principal, payload.name, payload.description, payload.payload
    )
    if idem_key:
        manager.store(
            "syllabus_template.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(template),
        )
    return template


@router.post(
    "/teacher/syllabus-templates/{template_id}/publish",
    response_model=SyllabusTemplate,
    summary="Publish a syllabus template (one-way, idempotent)",
)
def publish_template(
    template_id: str,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = {"template_id": template_id}
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("syllabus_template.publish", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    template = service.publish_template(repo, principal, template_id)
    if idem_key:
        manager.store(
            "syllabus_template.publish",
            idem_key,
            body,
            status.HTTP_200_OK,
            jsonable_encoder(template),
        )
    return template
