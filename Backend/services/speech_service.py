"""
Speech Service

Business logic for mock speech assets: source authorization, content-hash
caching, provider invocation with a documented safe fallback, retrieval, and
playback URL issuance.

Contract highlights:
- Source authorization grants access only to the owner (or an admin); other
  roles receive 404 so private sources are not exposed.
- Repeated identical requests (same transcript, language, and voice settings
  for the same user) reuse the cached asset instead of generating a new one.
- When the provider fails, the asset record is still persisted with
  ``media_storage_name=None`` so the transcript remains retrievable, and the
  caller receives ProviderUnavailable (503).

Author: eKlAVYA Backend
Version: 1.0.0
"""

import hashlib
import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Optional, Tuple

from core.access import assert_owner_access
from core.config import Settings
from core.errors import NotFound, ProviderUnavailable, ValidationFailed
from core.ids import new_id
from core.security import Principal
from core.time import utcnow
from models.notes import Note
from models.scans import Scan
from models.speech import (
    MOCK_SPEECH_DISCLAIMER,
    SpeechAsset,
    SpeechAssetOut,
    SpeechCreate,
)
from providers.mock_speech import MockSpeechProvider, SpeechProvider
from repositories.base import Repository
from services.audit_service import record_audit

logger = logging.getLogger(__name__)

SOURCE_TYPES = ("note", "scan", "transcript")
PLAYBACK_URL_TTL_SECONDS = 3600


class SpeechAssetRecord(SpeechAsset):
    """
    Repository read model for speech assets.

    The frozen SpeechAsset entity declares ``media_storage_name: str``, but
    the documented provider-failure fallback persists the asset with
    ``media_storage_name=None`` so the transcript stays retrievable, and the
    repository re-validates records on every read. This widened subclass is a
    SpeechAsset in every other respect and keeps those fallback records
    readable; healthy assets behave identically through it.
    """

    __collection__ = "speech_assets"

    media_storage_name: Optional[str] = None


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------

def compute_content_hash(transcript: str, language: str, voice_settings: dict) -> str:
    """
    Cache key for a synthesis request: SHA-256 over the canonical JSON of
    {transcript, language, voice_settings} with sorted keys.
    """
    payload = {
        "transcript": transcript,
        "language": language,
        "voice_settings": voice_settings or {},
    }
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Source authorization
# ---------------------------------------------------------------------------

def authorize_source(
    repo: Repository,
    principal: Principal,
    source_type: str,
    source_id: Optional[str],
) -> None:
    """
    Ensure the principal may access the source content.

    Rules:
    - "note":    the note must exist and be owned by the principal (or caller
                 is an admin); otherwise 404.
    - "scan":    the scan must exist and be owned by the principal (or caller
                 is an admin); otherwise 404.
    - "transcript": always allowed for authenticated users.
    - anything else: 422 ValidationFailed.

    Teachers and parents are intentionally not granted access here.
    """
    if source_type == "transcript":
        return

    if source_type == "note":
        if not source_id:
            raise ValidationFailed(
                details={"field": "source_id"},
                message="source_id is required when source_type is 'note'.",
            )
        note = repo.get(Note, source_id)
        if note is None:
            raise NotFound("The requested resource was not found.")
        if note.owner_id != principal.user_id and principal.role != "admin":
            raise NotFound("The requested resource was not found.")
        return

    if source_type == "scan":
        if not source_id:
            raise ValidationFailed(
                details={"field": "source_id"},
                message="source_id is required when source_type is 'scan'.",
            )
        scan = repo.get(Scan, source_id)
        if scan is None:
            raise NotFound("The requested resource was not found.")
        if scan.owner_id != principal.user_id and principal.role != "admin":
            raise NotFound("The requested resource was not found.")
        return

    raise ValidationFailed(
        details={"field": "source_type", "allowed": list(SOURCE_TYPES)},
        message=f"Unsupported source_type '{source_type}'.",
    )


# ---------------------------------------------------------------------------
# Asset creation
# ---------------------------------------------------------------------------

def create_speech_asset(
    repo: Repository,
    settings: Settings,
    principal: Principal,
    payload: SpeechCreate,
    provider: Optional[SpeechProvider] = None,
) -> Tuple[SpeechAsset, bool]:
    """
    Authorize the source, apply the content-hash cache, and generate the
    asset through the provider.

    Returns:
        (asset, created): ``created`` is False when a cached asset was reused.

    Safe fallback: if the provider raises, the asset record is still stored
    with ``media_storage_name=None`` (transcript preserved) and
    ProviderUnavailable is re-raised so the client receives 503 while the
    transcript remains retrievable via GET.
    """
    authorize_source(repo, principal, payload.source_type, payload.source_id)
    content_hash = compute_content_hash(
        payload.transcript, payload.language, payload.voice_settings
    )

    cached = repo.first(
        SpeechAssetRecord,
        owner_id=principal.user_id,
        content_hash=content_hash,
    )
    if cached is not None:
        record_audit(
            repo,
            principal.user_id,
            "speech.generate",
            "speech_asset",
            cached.id,
            details={
                "source_type": payload.source_type,
                "cached": True,
                "is_mock": cached.is_mock,
            },
        )
        return cached, False

    provider = provider or MockSpeechProvider()
    try:
        result = provider.synthesize(
            payload.transcript,
            payload.language,
            payload.voice_settings or {},
        )
    except Exception as exc:
        fallback = SpeechAssetRecord.new(
            "sp",
            owner_id=principal.user_id,
            source_type=payload.source_type,
            source_id=payload.source_id,
            transcript=payload.transcript,
            language=payload.language,
            voice_settings=payload.voice_settings or {},
            content_hash=content_hash,
            media_storage_name=None,
            media_content_type="audio/wav",
            duration_seconds=None,
            is_mock=True,
            mock_disclaimer=MOCK_SPEECH_DISCLAIMER,
        )
        repo.put(fallback)
        record_audit(
            repo,
            principal.user_id,
            "speech.generate",
            "speech_asset",
            fallback.id,
            details={
                "source_type": payload.source_type,
                "cached": False,
                "is_mock": True,
                "provider_error": type(exc).__name__,
            },
        )
        logger.warning(
            "Speech provider failed for user %s: %s",
            principal.user_id,
            type(exc).__name__,
        )
        raise ProviderUnavailable(
            message=(
                "The speech provider is temporarily unavailable; no audio was "
                f"generated. The transcript has been preserved and remains "
                f"retrievable via GET /api/v1/speech/{fallback.id}."
            ),
            details={"asset_id": fallback.id, "media_available": False},
        ) from exc

    media_dir = Path(settings.local_media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)
    asset_id = new_id("sp")
    media_storage_name = f"speech_{asset_id}.wav"
    (media_dir / media_storage_name).write_bytes(result.audio_bytes)

    asset = SpeechAsset(
        id=asset_id,
        owner_id=principal.user_id,
        source_type=payload.source_type,
        source_id=payload.source_id,
        transcript=payload.transcript,
        language=payload.language,
        voice_settings=payload.voice_settings or {},
        content_hash=content_hash,
        media_storage_name=media_storage_name,
        media_content_type=result.content_type,
        duration_seconds=result.duration_seconds,
        is_mock=bool(result.is_mock),
        mock_disclaimer=MOCK_SPEECH_DISCLAIMER,
    )
    repo.put(asset)
    record_audit(
        repo,
        principal.user_id,
        "speech.generate",
        "speech_asset",
        asset.id,
        details={
            "source_type": payload.source_type,
            "cached": False,
            "is_mock": asset.is_mock,
        },
    )
    return asset, True


# ---------------------------------------------------------------------------
# Retrieval and playback
# ---------------------------------------------------------------------------

def get_asset(repo: Repository, principal: Principal, asset_id: str) -> SpeechAsset:
    """Fetch an asset owned by the principal (or an admin); 404 otherwise."""
    asset = repo.get(SpeechAssetRecord, asset_id)
    if asset is None:
        raise NotFound("The requested resource was not found.")
    assert_owner_access(principal, asset.owner_id)
    return asset


def playback_url(asset: SpeechAsset) -> dict:
    """Local authorized playback route (signed-style development URL)."""
    return {
        "asset_id": asset.id,
        "url": f"/api/v1/speech/{asset.id}",
        "authorization": "bearer-or-dev-headers-required",
        "expires_at": (utcnow() + timedelta(seconds=PLAYBACK_URL_TTL_SECONDS)).isoformat(),
        "is_mock": True,
        "disclaimer": asset.mock_disclaimer,
        "media_available": asset.media_storage_name is not None,
    }


def to_asset_out(asset: SpeechAsset, cached: bool = False) -> SpeechAssetOut:
    """Map an entity to its API representation (never exposes storage paths)."""
    return SpeechAssetOut(
        id=asset.id,
        owner_id=asset.owner_id,
        source_type=asset.source_type,
        source_id=asset.source_id,
        transcript=asset.transcript,
        language=asset.language,
        voice_settings=asset.voice_settings,
        content_hash=asset.content_hash,
        media_content_type=asset.media_content_type,
        duration_seconds=asset.duration_seconds,
        is_mock=asset.is_mock,
        mock_disclaimer=asset.mock_disclaimer,
        media_available=asset.media_storage_name is not None,
        created_at=asset.created_at,
        cached=cached,
    )
