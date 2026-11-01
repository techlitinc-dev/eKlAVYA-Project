"""
Speech Router

Mock speech asset endpoints, all registered under /api/v1:

- POST /speech                              create (or cache-reuse) an asset
- GET  /speech/{speech_asset_id}            retrieve an asset (owner/admin)
- GET  /speech/{speech_asset_id}/playback-url  authorized local playback route

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from core.config import Settings, get_settings
from core.security import Principal, get_current_principal
from dependencies import IdempotencyManager, get_repository
from models.speech import PlaybackUrlOut, SpeechAssetOut, SpeechCreate
from repositories.base import Repository
from services import speech_service as service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Speech"])

IDEMPOTENCY_SCOPE = "speech.create"


@router.post(
    "/speech",
    response_model=SpeechAssetOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a mock speech asset (cached by content hash)",
)
def create_speech_asset(
    payload: SpeechCreate,
    request: Request,
    idem_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
    settings: Settings = Depends(get_settings),
):
    body = payload.model_dump()
    manager = IdempotencyManager(repo, settings, principal)
    if idem_key:
        cached_record = manager.replay(IDEMPOTENCY_SCOPE, idem_key, body)
        if cached_record is not None:
            return JSONResponse(
                status_code=cached_record.status_code,
                content=cached_record.response,
            )

    asset, created = service.create_speech_asset(
        repo, settings, principal, payload
    )
    output = service.to_asset_out(asset, cached=not created)
    status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK

    if idem_key:
        manager.store(
            IDEMPOTENCY_SCOPE,
            idem_key,
            body,
            status_code,
            jsonable_encoder(output),
        )
    if created:
        return output
    return JSONResponse(status_code=status_code, content=jsonable_encoder(output))


@router.get(
    "/speech/{speech_asset_id}",
    response_model=SpeechAssetOut,
    summary="Get a speech asset (owner or admin)",
)
def get_speech_asset(
    speech_asset_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> SpeechAssetOut:
    asset = service.get_asset(repo, principal, speech_asset_id)
    return service.to_asset_out(asset)


@router.get(
    "/speech/{speech_asset_id}/playback-url",
    response_model=PlaybackUrlOut,
    summary="Get an authorized local playback URL (owner or admin)",
)
def get_playback_url(
    speech_asset_id: str,
    repo: Repository = Depends(get_repository),
    principal: Principal = Depends(get_current_principal),
) -> PlaybackUrlOut:
    asset = service.get_asset(repo, principal, speech_asset_id)
    return PlaybackUrlOut(**service.playback_url(asset))
