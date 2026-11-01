"""
Provider Interfaces

Small internal adapter boundaries for the deterministic local development
providers (OCR, answering, decisions). Real providers can later implement
the same interfaces behind feature flags.

Failure contract: callers use ``safe_decide`` for decision routes so a
provider exception degrades to a documented safe fallback and core CRUD
never depends on the provider.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider result types
# ---------------------------------------------------------------------------

class OcrResult(BaseModel):
    """Deterministic OCR output for one page."""

    text: str
    uncertain_regions: List[Dict[str, Any]] = Field(default_factory=list)


class AnswerResult(BaseModel):
    """
    Grounded (or safely ungrounded) answer for a question.

    Unsupported input never carries an invented confident answer:
    ``final_answer`` stays None and ``verification_status`` describes why.
    """

    final_answer: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    subject: Optional[str] = None
    chapter: Optional[str] = None
    topic: Optional[str] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    grounding_status: str = "ungrounded"
    verification_status: Optional[str] = None
    clarification: Optional[str] = None


class StepCheckResult(BaseModel):
    """Verdict for the check_steps intent."""

    verdict: str  # "correct" | "incorrect"
    issues: List[str] = Field(default_factory=list)


class Decision(BaseModel):
    """Outcome of an internal decision route."""

    outcome: str
    reason: str


# ---------------------------------------------------------------------------
# Provider interfaces
# ---------------------------------------------------------------------------

class OcrProvider(ABC):
    """Extract text (and uncertain regions) from one uploaded page."""

    @abstractmethod
    def extract_text(self, page_bytes: bytes, page_number: int) -> OcrResult:
        ...


class AnswerProvider(ABC):
    """Answer a question for a scan intent, grounded in approved sources."""

    @abstractmethod
    def answer_question(self, question_text: str, intent: str) -> AnswerResult:
        ...

    @abstractmethod
    def check_steps(self, steps: List[str]) -> StepCheckResult:
        ...


class DecisionProvider(ABC):
    """Small internal decision interface (never exposed as a public route)."""

    @abstractmethod
    def decide(self, route: str, payload: Dict[str, Any]) -> Decision:
        ...


def safe_decide(
    provider: DecisionProvider, route: str, payload: Dict[str, Any]
) -> Decision:
    """
    Run a decision route with the documented safe fallback.

    Provider exceptions produce Decision(outcome="fallback",
    reason="provider_unavailable") so core flows never crash on a provider.
    Hard permission rules must already have executed before this is called.
    """
    try:
        return provider.decide(route, payload)
    except Exception as exc:  # provider failure contract
        logger.warning(
            "Decision provider failed for route %s: %s", route, type(exc).__name__
        )
        return Decision(outcome="fallback", reason="provider_unavailable")
