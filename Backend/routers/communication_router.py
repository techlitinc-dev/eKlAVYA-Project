"""
Communication Router

Simulated one-way in-app calls, per-recipient delivery actions, and the
message inbox. All paths are registered under /api/v1 by the eKlAVYA
registry. This API is an in-app audio announcement only: no telephony,
phone numbers, WebRTC, microphone endpoints, or outbound-call statuses.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, Response, status
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
from models.common import Page, SyllabusContext
from models.communication import (
    CallCreate,
    CallOut,
    DeliveryOut,
    MessageOut,
    MyDeliveryOut,
)
from repositories.base import Repository
from services import simulated_call_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Communication"])


@router.post(
    "/simulated-calls",
    response_model=CallOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a simulated call (teacher/admin sender)",
)
def create_simulated_call(
    payload: CallCreate,
    response: Response,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached = manager.replay("simulated_call.create", idem_key, body)
        if cached:
            return JSONResponse(status_code=cached.status_code, content=cached.response)

    context = SyllabusContext(
        syllabus_id=payload.syllabus_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        topic_id=payload.topic_id,
    )
    call, deliveries, created = service.create_call(
        repo,
        settings,
        principal,
        recipient_ids=payload.recipient_ids,
        title=payload.title,
        subject=payload.subject,
        transcript=payload.transcript,
        speech_asset_id=payload.speech_asset_id,
        sender_type=payload.sender_type,
        context=context,
    )
    call_out = service.build_call_out(call, deliveries, deduplicated=not created)
    status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    if idem_key:
        manager.store(
            "simulated_call.create",
            idem_key,
            body,
            status_code,
            jsonable_encoder(call_out),
        )
    response.status_code = status_code
    return call_out


@router.get(
    "/simulated-calls",
    response_model=Page[CallOut],
    summary="List simulated calls (sender's own; admin sees all)",
)
def list_simulated_calls(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
):
    calls = service.list_calls(repo, principal)
    items = [service.build_call_out(call, deliveries) for call, deliveries in calls]
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[CallOut](items=page, next_cursor=next_cursor)


@router.get(
    "/simulated-calls/{call_id}",
    response_model=CallOut,
    summary="Get a simulated call (sender, admin, or recipient)",
)
def get_simulated_call(
    call_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    call, deliveries = service.get_call_for_principal(repo, principal, call_id)
    return service.build_call_out(call, deliveries)


@router.post(
    "/simulated-calls/{call_id}/cancel",
    response_model=CallOut,
    summary="Cancel a simulated call (sender or admin; no-op when nothing is scheduled)",
)
def cancel_simulated_call(
    call_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    call, deliveries, _changed = service.cancel_call(repo, principal, call_id)
    return service.build_call_out(call, deliveries)


@router.get(
    "/me/simulated-calls",
    response_model=Page[MyDeliveryOut],
    summary="List the caller's own call deliveries",
)
def list_my_deliveries(
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
):
    items = service.list_my_deliveries(repo, principal)
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[MyDeliveryOut](items=page, next_cursor=next_cursor)


@router.post(
    "/me/simulated-calls/{delivery_id}/accept",
    response_model=DeliveryOut,
    summary="Accept a delivery (allowed from scheduled or ringing)",
)
def accept_delivery(
    delivery_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    delivery = service.apply_recipient_action(repo, principal, delivery_id, "accept")
    return service.build_delivery_out(delivery)


@router.post(
    "/me/simulated-calls/{delivery_id}/dismiss",
    response_model=DeliveryOut,
    summary="Dismiss a delivery; records call-history message",
)
def dismiss_delivery(
    delivery_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    delivery = service.apply_recipient_action(repo, principal, delivery_id, "dismiss")
    return service.build_delivery_out(delivery)


@router.post(
    "/me/simulated-calls/{delivery_id}/playback-started",
    response_model=DeliveryOut,
    summary="Mark playback started (accepted -> playing)",
)
def start_playback(
    delivery_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    delivery = service.apply_recipient_action(
        repo, principal, delivery_id, "playback-started"
    )
    return service.build_delivery_out(delivery)


@router.post(
    "/me/simulated-calls/{delivery_id}/complete",
    response_model=DeliveryOut,
    summary="Complete playback (idempotent)",
)
def complete_delivery(
    delivery_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    delivery = service.complete_delivery(repo, principal, delivery_id)
    return service.build_delivery_out(delivery)


@router.get(
    "/messages",
    response_model=Page[MessageOut],
    summary="List the caller's messages (newest first; optional unread filter)",
)
def list_messages(
    unread: Optional[bool] = Query(None),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    pagination: PaginationParams = Depends(get_pagination),
):
    items = [
        MessageOut(**message.model_dump())
        for message in service.list_messages(repo, principal, unread_only=bool(unread))
    ]
    page, next_cursor = paginate(items, pagination.limit, pagination.cursor)
    return Page[MessageOut](items=page, next_cursor=next_cursor)


@router.post(
    "/messages/{message_id}/read",
    response_model=MessageOut,
    summary="Mark a message read (idempotent; owner only)",
)
def mark_message_read(
    message_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
):
    return service.mark_message_read(repo, principal, message_id)
