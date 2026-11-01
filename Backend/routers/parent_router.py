"""
Parent Router

Parent-scoped endpoints over linked children only: child summaries, read-only
progress, persisted-state weekly reports, and communication preferences that
are honored by subsequent simulated-call scheduling. All paths are registered
under /api/v1 by the eKlAVYA registry.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging

from fastapi import APIRouter, Depends

from core.config import Settings, get_settings
from core.security import Principal, get_current_principal
from dependencies import (
    PaginationParams,
    get_pagination,
    get_repository,
    paginate,
)
from models.common import Page
from models.communication import (
    ChildOut,
    PrefsOut,
    PrefsUpdate,
    ReportOut,
)
from models.syllabus import SyllabusProgress
from repositories.base import Repository
from services import simulated_call_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Parent"])


@router.get(
    "/parent/children",
    response_model=Page[ChildOut],
    summary="Linked children with profile and progress summary",
)
def list_children(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
):
    items = service.parent_children(repo, principal)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[ChildOut](items=page, next_cursor=next_cursor)


@router.get(
    "/parent/children/{student_id}/progress",
    response_model=SyllabusProgress,
    summary="Read-only syllabus progress for a linked child",
)
def child_progress(
    student_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    progress = service.parent_child_progress(repo, principal, student_id)
    return SyllabusProgress(**progress)


@router.get(
    "/parent/children/{student_id}/reports",
    response_model=ReportOut,
    summary="Weekly report generated from persisted task state",
)
def child_report(
    student_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    return service.parent_child_report(repo, principal, student_id)


@router.get(
    "/parent/communication-preferences",
    response_model=PrefsOut,
    summary="Get the parent's communication preferences (created with defaults if absent)",
)
def get_preferences(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    return service.parent_get_prefs(repo, settings, principal)


@router.put(
    "/parent/communication-preferences",
    response_model=PrefsOut,
    summary="Update the parent's communication preferences",
)
def update_preferences(
    payload: PrefsUpdate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    return service.parent_update_prefs(repo, settings, principal, payload)
