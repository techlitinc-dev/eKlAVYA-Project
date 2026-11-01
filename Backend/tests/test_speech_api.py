"""
Speech API Tests

Covers section 21.6 (speech) and the speech authorization rules: mock asset
creation and labelling, source authorization (note/scan/transcript),
content-hash caching, idempotency, retrieval and playback-url ownership,
the WAV artifact, and the provider-failure safe fallback.
"""

from pathlib import Path

import pytest

from core.config import get_settings
from core.errors import ProviderUnavailable
from core.security import Principal
from models.common import AuditEntry
from models.speech import MOCK_SPEECH_DISCLAIMER, SpeechCreate
from services import speech_service
from services.speech_service import SpeechAssetRecord
from tests.conftest import (
    ADMIN_LOCAL,
    STUDENT_AARAV,
    STUDENT_MEERA,
    TEACHER_RAO,
    auth_headers,
)

AARAV = auth_headers(STUDENT_AARAV, "student", "Aarav Sharma")
MEERA = auth_headers(STUDENT_MEERA, "student", "Meera Iyer")
RAO = auth_headers(TEACHER_RAO, "teacher", "Mrs. Rao")
ADMIN = auth_headers(ADMIN_LOCAL, "admin", "Local Admin")

NOTE_AARAV_1 = "note_seed_1"
SCAN_MEERA = "scan_seed_meera"

TRANSCRIPT_BODY = {
    "source_type": "transcript",
    "transcript": "Rotational motion summary for today's revision session.",
}


class _FailingProvider:
    """Stub provider that always fails, to exercise the safe fallback."""

    def synthesize(self, text, language, voice_settings=None):
        raise RuntimeError("provider down")


def _create(client, body, headers, **extra_headers):
    return client.post("/api/v1/speech", json=body, headers={**headers, **extra_headers})


# ---------------------------------------------------------------------------
# OpenAPI and authentication
# ---------------------------------------------------------------------------

def test_openapi_includes_speech_routes(client):
    spec = client.get("/api/openapi.json")
    assert spec.status_code == 200
    paths = spec.json()["paths"]
    assert "/api/v1/speech" in paths
    assert "/api/v1/speech/{speech_asset_id}" in paths
    assert "/api/v1/speech/{speech_asset_id}/playback-url" in paths


def test_missing_authentication_rejected(client):
    response = client.post("/api/v1/speech", json=TRANSCRIPT_BODY)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

    response = client.get("/api/v1/speech/sp_missing")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ---------------------------------------------------------------------------
# Creation, mock labelling, and media artifact
# ---------------------------------------------------------------------------

def test_create_from_transcript_returns_mock_asset(client):
    response = _create(client, TRANSCRIPT_BODY, AARAV)
    assert response.status_code == 201
    body = response.json()

    assert body["owner_id"] == STUDENT_AARAV
    assert body["source_type"] == "transcript"
    assert body["transcript"] == TRANSCRIPT_BODY["transcript"]
    assert body["language"] == "en"
    assert body["voice_settings"] == {}

    # Explicitly marked as mock and never described as synthesized speech.
    assert body["is_mock"] is True
    assert body["mock_disclaimer"] == MOCK_SPEECH_DISCLAIMER
    assert "mock" in body["mock_disclaimer"].lower()
    assert "not synthesized speech" in body["mock_disclaimer"]

    assert body["media_available"] is True
    assert body["media_content_type"] == "audio/wav"
    assert isinstance(body["duration_seconds"], int)
    assert body["duration_seconds"] >= 1
    assert body["cached"] is False
    assert body["content_hash"]

    # Storage paths are never exposed to clients.
    assert "media_storage_name" not in body


def test_wav_file_exists_with_riff_header(client):
    response = _create(client, TRANSCRIPT_BODY, AARAV)
    assert response.status_code == 201
    asset_id = response.json()["id"]

    media_dir = Path(get_settings().local_media_dir)
    wav_path = media_dir / f"speech_{asset_id}.wav"
    assert wav_path.exists()
    assert wav_path.stat().st_size > 44  # WAV header plus audio frames

    with wav_path.open("rb") as handle:
        magic = handle.read(4)
    assert magic == b"RIFF"

    # The file is a structurally valid single-channel WAV.
    import wave

    with wave.open(str(wav_path), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 8000
        assert wav_file.getnframes() > 0


# ---------------------------------------------------------------------------
# Source authorization
# ---------------------------------------------------------------------------

def test_create_from_own_note_source_authorized(client):
    body = {
        "source_type": "note",
        "source_id": NOTE_AARAV_1,
        "transcript": "Rotational Motion formula sheet readout.",
    }
    response = _create(client, body, AARAV)
    assert response.status_code == 201
    assert response.json()["source_type"] == "note"
    assert response.json()["source_id"] == NOTE_AARAV_1


def test_create_from_other_student_note_hidden(client):
    body = {
        "source_type": "note",
        "source_id": NOTE_AARAV_1,
        "transcript": "Trying to read Aarav's note.",
    }
    response = _create(client, body, MEERA)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_create_from_own_scan_source_authorized(client):
    body = {
        "source_type": "scan",
        "source_id": SCAN_MEERA,
        "transcript": "Meera's own scan transcript.",
    }
    response = _create(client, body, MEERA)
    assert response.status_code == 201
    assert response.json()["source_type"] == "scan"
    assert response.json()["source_id"] == SCAN_MEERA


def test_create_from_other_student_scan_hidden(client):
    body = {
        "source_type": "scan",
        "source_id": SCAN_MEERA,
        "transcript": "Trying to read Meera's scan.",
    }
    response = _create(client, body, AARAV)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_create_validation_errors(client):
    empty = _create(client, {"source_type": "transcript", "transcript": ""}, AARAV)
    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "VALIDATION_ERROR"

    bad_type = _create(client, {"source_type": "message", "transcript": "hi"}, AARAV)
    assert bad_type.status_code == 422
    assert bad_type.json()["error"]["code"] == "VALIDATION_ERROR"

    missing_source = _create(
        client, {"source_type": "note", "transcript": "no source id"}, AARAV
    )
    assert missing_source.status_code == 422
    assert missing_source.json()["error"]["code"] == "VALIDATION_ERROR"

    unknown_note = _create(
        client,
        {"source_type": "note", "source_id": "note_missing", "transcript": "ghost"},
        AARAV,
    )
    assert unknown_note.status_code == 404
    assert unknown_note.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Content-hash cache
# ---------------------------------------------------------------------------

def test_identical_request_uses_cache(client, fresh_repository):
    first = _create(client, TRANSCRIPT_BODY, AARAV)
    assert first.status_code == 201
    first_id = first.json()["id"]

    second = _create(client, TRANSCRIPT_BODY, AARAV)
    assert second.status_code == 200
    assert second.json()["id"] == first_id
    assert second.json()["cached"] is True
    assert second.json()["media_available"] is True

    # Only one asset was stored for the repeated request.
    assert fresh_repository.count(SpeechAssetRecord, owner_id=STUDENT_AARAV) == 1


def test_different_voice_settings_creates_new_asset(client, fresh_repository):
    first = _create(client, TRANSCRIPT_BODY, AARAV)
    assert first.status_code == 201

    varied = _create(
        client,
        {**TRANSCRIPT_BODY, "voice_settings": {"pace": "slow"}},
        AARAV,
    )
    assert varied.status_code == 201
    assert varied.json()["id"] != first.json()["id"]
    assert varied.json()["cached"] is False
    assert varied.json()["voice_settings"] == {"pace": "slow"}

    assert fresh_repository.count(SpeechAssetRecord, owner_id=STUDENT_AARAV) == 2


# ---------------------------------------------------------------------------
# Idempotency-Key
# ---------------------------------------------------------------------------

def test_idempotency_key_replays_original_and_conflicts(client):
    body = {"source_type": "transcript", "transcript": "Idempotent speech request."}
    key = "speech-key-1"

    first = _create(client, body, AARAV, **{"Idempotency-Key": key})
    assert first.status_code == 201
    first_id = first.json()["id"]

    replay = _create(client, body, AARAV, **{"Idempotency-Key": key})
    assert replay.status_code == 201
    assert replay.json()["id"] == first_id

    conflict = _create(
        client,
        {"source_type": "transcript", "transcript": "A different body."},
        AARAV,
        **{"Idempotency-Key": key},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


# ---------------------------------------------------------------------------
# Retrieval authorization
# ---------------------------------------------------------------------------

def _create_asset(client, headers=AARAV, body=None):
    response = _create(client, body or TRANSCRIPT_BODY, headers)
    assert response.status_code == 201
    return response.json()["id"]


def test_get_asset_owner_ok(client):
    asset_id = _create_asset(client)
    response = client.get(f"/api/v1/speech/{asset_id}", headers=AARAV)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == asset_id
    assert body["transcript"] == TRANSCRIPT_BODY["transcript"]
    assert body["is_mock"] is True
    assert body["media_available"] is True


def test_get_asset_other_student_hidden(client):
    asset_id = _create_asset(client)
    response = client.get(f"/api/v1/speech/{asset_id}", headers=MEERA)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_get_asset_teacher_not_owner_hidden(client):
    asset_id = _create_asset(client)
    response = client.get(f"/api/v1/speech/{asset_id}", headers=RAO)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_get_asset_admin_ok(client):
    asset_id = _create_asset(client)
    response = client.get(f"/api/v1/speech/{asset_id}", headers=ADMIN)
    assert response.status_code == 200
    assert response.json()["id"] == asset_id


def test_get_unknown_asset_404(client):
    response = client.get("/api/v1/speech/sp_does_not_exist", headers=AARAV)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# Playback URL
# ---------------------------------------------------------------------------

def test_playback_url_owner_authorized_local_route(client):
    asset_id = _create_asset(client)
    response = client.get(f"/api/v1/speech/{asset_id}/playback-url", headers=AARAV)
    assert response.status_code == 200
    body = response.json()

    assert body["asset_id"] == asset_id
    assert body["url"].startswith("/api/v1/speech/")
    assert body["url"] == f"/api/v1/speech/{asset_id}"
    assert body["authorization"] == "bearer-or-dev-headers-required"
    assert body["expires_at"]
    assert body["is_mock"] is True
    assert body["disclaimer"] == MOCK_SPEECH_DISCLAIMER
    assert body["media_available"] is True


def test_playback_url_enforces_ownership(client):
    asset_id = _create_asset(client)
    response = client.get(f"/api/v1/speech/{asset_id}/playback-url", headers=MEERA)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"

    admin = client.get(f"/api/v1/speech/{asset_id}/playback-url", headers=ADMIN)
    assert admin.status_code == 200


# ---------------------------------------------------------------------------
# Audit contract
# ---------------------------------------------------------------------------

def test_audit_recorded_without_transcript(client, fresh_repository):
    _create_asset(client)
    entries = fresh_repository.find(AuditEntry, action="speech.generate")
    assert len(entries) == 1
    details = entries[0].details
    assert details["source_type"] == "transcript"
    assert details["cached"] is False
    assert details["is_mock"] is True
    assert TRANSCRIPT_BODY["transcript"] not in str(details)


# ---------------------------------------------------------------------------
# Provider failure safe fallback
# ---------------------------------------------------------------------------

def test_provider_failure_returns_503_and_keeps_transcript(
    client, monkeypatch, fresh_repository
):
    monkeypatch.setattr(
        speech_service, "MockSpeechProvider", lambda: _FailingProvider()
    )

    response = _create(client, TRANSCRIPT_BODY, AARAV)
    assert response.status_code == 503
    envelope = response.json()["error"]
    assert envelope["code"] == "PROVIDER_UNAVAILABLE"
    assert "preserved" in envelope["message"]

    asset_id = envelope["details"]["asset_id"]
    assert envelope["details"]["media_available"] is False

    # The persisted asset remains retrievable with its transcript intact.
    fetched = client.get(f"/api/v1/speech/{asset_id}", headers=AARAV)
    assert fetched.status_code == 200
    assert fetched.json()["transcript"] == TRANSCRIPT_BODY["transcript"]
    assert fetched.json()["media_available"] is False
    assert fetched.json()["is_mock"] is True


def test_provider_failure_persists_medialess_record(fresh_repository):
    principal = Principal(
        user_id=STUDENT_AARAV, role="student", name="Aarav Sharma"
    )
    payload = SpeechCreate(
        source_type="transcript", transcript="Preserve this transcript."
    )

    with pytest.raises(ProviderUnavailable) as exc_info:
        speech_service.create_speech_asset(
            fresh_repository,
            get_settings(),
            principal,
            payload,
            provider=_FailingProvider(),
        )

    error = exc_info.value
    assert error.status_code == 503
    assert error.code == "PROVIDER_UNAVAILABLE"

    record = fresh_repository.get(SpeechAssetRecord, error.details["asset_id"])
    assert record is not None
    assert record.media_storage_name is None
    assert record.transcript == "Preserve this transcript."
    assert record.is_mock is True
    assert record.mock_disclaimer == MOCK_SPEECH_DISCLAIMER

    # Owner can still retrieve it through the service layer.
    asset = speech_service.get_asset(fresh_repository, principal, record.id)
    output = speech_service.to_asset_out(asset)
    assert output.media_available is False
    assert output.transcript == "Preserve this transcript."
