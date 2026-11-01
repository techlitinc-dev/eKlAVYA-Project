"""
Mock OCR Provider

Deterministic, offline text extraction for local development and tests.
Recognizes the eKlAVYA sample fixture by content marker (or the literal
sample question) and otherwise returns a deterministic
"content requires confirmation" placeholder with the whole text marked
uncertain.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging

from providers.base import OcrProvider, OcrResult

logger = logging.getLogger(__name__)

SAMPLE_MARKER = b"EKLAVYA_SAMPLE"
SAMPLE_QUESTION = (
    "A block of mass 2 kg moves at 3 m/s on a frictionless horizontal "
    "surface. Find its kinetic energy."
)
_SAMPLE_REGION = {
    "page": 1,
    "start": 0,
    "end": 20,
    "reason": "mock_low_confidence",
}


class MockOcrProvider(OcrProvider):
    """Deterministic local OCR; never makes external calls."""

    def extract_text(self, page_bytes: bytes, page_number: int) -> OcrResult:
        content = page_bytes or b""
        if SAMPLE_MARKER in content or SAMPLE_QUESTION.encode("utf-8") in content:
            return OcrResult(
                text=SAMPLE_QUESTION,
                uncertain_regions=[dict(_SAMPLE_REGION)],
            )

        text = (
            f"Mock OCR page {page_number}: {len(content)} bytes captured. "
            "Content requires confirmation."
        )
        return OcrResult(
            text=text,
            uncertain_regions=[
                {
                    "page": page_number,
                    "start": 0,
                    "end": len(text),
                    "reason": "mock_unrecognized_content",
                }
            ],
        )
