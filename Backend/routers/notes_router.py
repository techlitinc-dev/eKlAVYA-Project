"""
Notes Router

Note CRUD with search and filters, optimistic-concurrency updates, version
history and restore, attachment upload with magic-byte validation, note links,
local export artifacts, sharing scopes, and deterministic mock AI actions.

All paths are absolute and registered under /api/v1 by the router registry.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    Query,
    Response,
    UploadFile,
    status,
)
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
from models.notes import (
    AiActionIn,
    AiActionOut,
    Attachment,
    ExportIn,
    ExportOut,
    LinkIn,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    NoteVersion,
    RestoreIn,
    ShareIn,
)
from repositories.base import Repository
from services import notes_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Notes"])


@router.get(
    "/notes",
    response_model=Page[NoteOut],
    summary="List notes",
)
def list_notes(
    query: Optional[str] = Query(None),
    topic_id: Optional[str] = Query(None, alias="topicId"),
    tag: Optional[str] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[NoteOut]:
    items = service.list_notes(repo, principal, query=query, topic_id=topic_id, tag=tag)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[NoteOut](items=[NoteOut(**n.model_dump()) for n in page], next_cursor=next_cursor)


@router.post(
    "/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a note",
)
def create_note(
    payload: NoteCreate,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("note.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    note = service.create_note(repo, principal, body)
    out = NoteOut(**note.model_dump())
    if idem_key:
        manager.store(
            "note.create",
            idem_key,
            body,
            status.HTTP_201_CREATED,
            jsonable_encoder(out),
        )
    return out


@router.get(
    "/notes/{note_id}",
    response_model=NoteOut,
    summary="Get a note",
)
def get_note(
    note_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> NoteOut:
    note = service.get_note(repo, principal, note_id)
    return NoteOut(**note.model_dump())


@router.patch(
    "/notes/{note_id}",
    response_model=NoteOut,
    summary="Update a note (optimistic concurrency)",
)
def update_note(
    note_id: str,
    payload: NoteUpdate,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> NoteOut:
    note = service.update_note(
        repo,
        principal,
        note_id,
        {**payload.model_dump(exclude={"version"}, exclude_none=True), "version": payload.version},
    )
    return NoteOut(**note.model_dump())


@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a note (soft delete)",
)
def delete_note(
    note_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> Response:
    service.archive_note(repo, principal, note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/notes/{note_id}/versions",
    response_model=Page[NoteVersion],
    summary="List note versions (newest first)",
)
def list_versions(
    note_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
) -> Page[NoteVersion]:
    items = service.list_versions(repo, principal, note_id)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[NoteVersion](items=page, next_cursor=next_cursor)


@router.post(
    "/notes/{note_id}/restore",
    response_model=NoteOut,
    summary="Restore note content from a saved version",
)
def restore_note(
    note_id: str,
    payload: RestoreIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> NoteOut:
    note = service.restore_note(repo, principal, note_id, payload.version)
    return NoteOut(**note.model_dump())


@router.post(
    "/notes/{note_id}/attachments",
    response_model=Attachment,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an attachment (PNG/JPEG/PDF)",
)
def upload_attachment(
    note_id: str,
    file: UploadFile = File(...),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> Attachment:
    data = file.file.read()
    return service.add_attachment(repo, settings, principal, note_id, file.filename, data)


@router.post(
    "/notes/{note_id}/links",
    response_model=NoteOut,
    summary="Link this note to another note",
)
def add_link(
    note_id: str,
    payload: LinkIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> NoteOut:
    note = service.add_link(repo, principal, note_id, payload.linked_note_id)
    return NoteOut(**note.model_dump())


@router.delete(
    "/notes/{note_id}/links/{linked_note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a note link (idempotent)",
)
def remove_link(
    note_id: str,
    linked_note_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> Response:
    service.remove_link(repo, principal, note_id, linked_note_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/notes/{note_id}/export",
    response_model=ExportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Export a note as txt or pdf artifact",
)
def export_note(
    note_id: str,
    payload: ExportIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
) -> ExportOut:
    result = service.export_note(repo, settings, principal, note_id, payload.format)
    return ExportOut(**result)


@router.post(
    "/notes/{note_id}/share",
    response_model=NoteOut,
    summary="Set the sharing scope of a note",
)
def share_note(
    note_id: str,
    payload: ShareIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> NoteOut:
    note = service.share_note(repo, principal, note_id, payload.level, payload.audience)
    return NoteOut(**note.model_dump())


@router.post(
    "/notes/{note_id}/ai-actions",
    response_model=AiActionOut,
    summary="Run a deterministic mock AI action on a note",
)
def run_ai_action(
    note_id: str,
    payload: AiActionIn,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> AiActionOut:
    result = service.run_ai_action(repo, principal, note_id, payload.action, payload.language)
    return AiActionOut(**result)
