"""
Providers Package

Deterministic local development providers for OCR, answering, and
internal decisions. Real providers can later be selected here behind the
same interfaces and feature flags.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging

from providers.base import (
    AnswerProvider,
    AnswerResult,
    Decision,
    DecisionProvider,
    OcrProvider,
    OcrResult,
    StepCheckResult,
    safe_decide,
)
from providers.mock_answer import MockAnswerProvider
from providers.mock_decision import MockDecisionProvider
from providers.mock_ocr import MockOcrProvider

logger = logging.getLogger(__name__)


def get_ocr_provider() -> OcrProvider:
    """Return the configured OCR provider (mock in local development)."""
    return MockOcrProvider()


def get_answer_provider() -> AnswerProvider:
    """Return the configured answer provider (mock in local development)."""
    return MockAnswerProvider()


def get_decision_provider() -> DecisionProvider:
    """Return the configured decision provider (mock in local development)."""
    return MockDecisionProvider()
