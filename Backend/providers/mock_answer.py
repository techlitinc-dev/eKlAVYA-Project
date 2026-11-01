"""
Mock Answer Provider

Deterministic, offline answering for local development and tests.

Supported input (the canonical sample question) returns the grounded
kinetic-energy answer with approved mock citations. Unsupported input
never receives an invented confident numeric answer: the result is
ungrounded with a deterministic verification status
(``needs_clarification`` for empty/garbled text, ``insufficient_sources``
for recognized words outside the mock corpus) and a clarification note.
Teacher review routing is a decision-provider concern, not this provider.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
import re
from typing import List

from providers.base import AnswerProvider, AnswerResult, StepCheckResult

logger = logging.getLogger(__name__)

SAMPLE_ANSWER = AnswerResult(
    final_answer="9 J",
    steps=[
        "Kinetic energy: KE = 1/2 mv^2",
        "Mass m = 2 kg, speed v = 3 m/s",
        "KE = 1/2 * 2 * (3)^2 = 9 J",
    ],
    subject="Physics",
    chapter="Work, Energy and Power",
    topic="Kinetic Energy",
    citations=[
        {
            "id": "mock_res_physics_001",
            "title": "Mock Physics Reference (Work, Energy and Power)",
            "approved": True,
        }
    ],
    grounding_status="grounded",
    verification_status="verified_by_mock_rule",
    clarification=None,
)

_GARBLED_CLARIFICATION = (
    "The question text is empty or garbled; please re-scan the page or "
    "type the question manually."
)
_UNSUPPORTED_CLARIFICATION = (
    "No approved mock reference supports this question yet; the answer "
    "needs clarification or a teacher review."
)


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().split())


def _is_sample_question(normalized: str) -> bool:
    return (
        "2 kg" in normalized
        and "3 m/s" in normalized
        and "kinetic energy" in normalized
    )


class MockAnswerProvider(AnswerProvider):
    """Deterministic local answerer; never makes external calls."""

    def answer_question(self, question_text: str, intent: str) -> AnswerResult:
        normalized = _normalize(question_text)
        if _is_sample_question(normalized):
            return SAMPLE_ANSWER.model_copy(deep=True)

        word_count = len(re.findall(r"[a-z]+", normalized))
        if word_count < 3:
            return AnswerResult(
                final_answer=None,
                steps=[],
                grounding_status="ungrounded",
                verification_status="needs_clarification",
                citations=[],
                clarification=_GARBLED_CLARIFICATION,
            )
        return AnswerResult(
            final_answer=None,
            steps=[],
            grounding_status="ungrounded",
            verification_status="insufficient_sources",
            citations=[],
            clarification=_UNSUPPORTED_CLARIFICATION,
        )

    def check_steps(self, steps: List[str]) -> StepCheckResult:
        """Verify supplied steps against the same kinetic-energy mock rule."""
        joined = " ".join(step or "" for step in (steps or []))
        compact = joined.replace(" ", "").lower()
        has_formula = (
            "1/2" in joined or "½" in joined
        ) and ("mv^2" in compact or "mv2" in compact or "mv²" in joined)
        reaches_answer = "9" in joined

        if has_formula and reaches_answer:
            return StepCheckResult(verdict="correct", issues=[])
        issues = []
        if not has_formula:
            issues.append("Missing kinetic-energy formula KE = 1/2 mv^2.")
        if not reaches_answer:
            issues.append("The steps do not reach the verified value 9 J.")
        return StepCheckResult(verdict="incorrect", issues=issues)
