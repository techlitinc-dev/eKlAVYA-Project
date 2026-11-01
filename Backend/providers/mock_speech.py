"""
Mock Speech Provider

Deterministic, stdlib-only local provider for speech synthesis. It produces a
short valid silent WAV so the full speech workflow (asset record + media file
+ playback route) can run without external services.

Every result is explicitly marked as mock output. A real provider (for
example a Sarvam adapter) can be added later behind the same SpeechProvider
interface; providers/base.py does not exist yet, so the interface lives here.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import io
import logging
import wave
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

SAMPLE_RATE_HZ = 8000
MAX_DURATION_SECONDS = 2
MIN_DURATION_SECONDS = 1


@dataclass(frozen=True)
class SynthesisResult:
    """Provider output for one synthesis request."""

    audio_bytes: bytes
    content_type: str = "audio/wav"
    duration_seconds: int = MIN_DURATION_SECONDS
    is_mock: bool = True


@runtime_checkable
class SpeechProvider(Protocol):
    """Interface implemented by every speech provider (mock or real)."""

    def synthesize(
        self,
        text: str,
        language: str,
        voice_settings: Optional[Mapping[str, Any]] = None,
    ) -> SynthesisResult:
        """Render text to audio bytes, or raise an exception on failure."""
        ...


class MockSpeechProvider:
    """
    Deterministic local provider.

    Generates silent 16-bit mono PCM WAV audio whose (capped) length scales
    with the transcript length. The output is a silent placeholder and is
    always flagged with ``is_mock=True``.
    """

    def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_settings: Optional[Mapping[str, Any]] = None,
    ) -> SynthesisResult:
        duration_seconds = self._duration_for(text)
        audio_bytes = self._silent_wav(duration_seconds, SAMPLE_RATE_HZ)
        return SynthesisResult(
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            duration_seconds=duration_seconds,
            is_mock=True,
        )

    @staticmethod
    def _duration_for(text: str) -> int:
        return min(MAX_DURATION_SECONDS, max(MIN_DURATION_SECONDS, len(text) // 200))

    @staticmethod
    def _silent_wav(duration_seconds: int, sample_rate: int) -> bytes:
        """Build a valid silent mono 16-bit PCM WAV in memory."""
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit samples
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00\x00" * (sample_rate * duration_seconds))
        return buffer.getvalue()
