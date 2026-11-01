"""
Grounding Service

Wraps the answer provider so scan execution always produces a safe,
auditable result:

- Ungrounded answers are stored as state (the execution result), never
  raised, so clients can see *why* no answer was produced.
- Provider exceptions (including core.errors.ProviderUnavailable) are
  caught inside and converted to a safe fallback result so core flows
  never crash on a provider.
- Every grounding attempt records a "scan.grounding" audit entry with
  only the verification status — never the full question text.

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Optional

from core.errors import ProviderUnavailable
from providers import get_answer_provider
from providers.base import AnswerProvider, AnswerResult
from repositories.base import Repository
from services.audit_service import record_audit

logger = logging.getLogger(__name__)

FALLBACK_CLARIFICATION = "Provider unavailable; safe fallback applied."


def ground(
    repo: Repository,
    question_text: str,
    intent: str,
    provider: Optional[AnswerProvider] = None,
    actor_id: Optional[str] = None,
) -> AnswerResult:
    """
    Answer a question through the configured provider, safely.

    Returns:
        AnswerResult: grounded answer, ungrounded state, or the documented
        safe fallback when the provider is unavailable.
    """
    answer_provider = provider or get_answer_provider()
    try:
        result = answer_provider.answer_question(question_text or "", intent)
    except ProviderUnavailable as exc:
        logger.warning("Answer provider unavailable: %s", exc)
        result = _fallback_result()
    except Exception as exc:  # provider failure contract
        logger.warning(
            "Answer provider failed (%s); safe fallback applied.",
            type(exc).__name__,
        )
        result = _fallback_result()

    record_audit(
        repo,
        actor_id,
        "scan.grounding",
        "scan_answer",
        details={"verification_status": result.verification_status},
    )
    return result


def _fallback_result() -> AnswerResult:
    return AnswerResult(
        final_answer=None,
        steps=[],
        grounding_status="ungrounded",
        verification_status="insufficient_sources",
        citations=[],
        clarification=FALLBACK_CLARIFICATION,
    )
