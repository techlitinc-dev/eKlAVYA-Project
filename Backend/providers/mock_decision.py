"""
Mock Decision Provider

Deterministic internal decisions for the documented routes:
syllabus relevance, OCR confirmation, answer review routing, and
communication approval. Hard permission rules always execute before any
of these decisions (enforced in service code order).

Author: eKlAVYA Backend
Version: 1.0.0
"""

import logging
from typing import Any, Dict

from providers.base import Decision, DecisionProvider

logger = logging.getLogger(__name__)


class MockDecisionProvider(DecisionProvider):
    """Deterministic local decisions; never makes external calls."""

    def decide(self, route: str, payload: Dict[str, Any]) -> Decision:
        payload = payload or {}

        if route == "syllabus_relevance":
            if payload.get("syllabus_id"):
                return Decision(
                    outcome="relevant", reason="mock_syllabus_relevance"
                )
            return Decision(
                outcome="undetermined", reason="missing_syllabus_context"
            )

        if route == "ocr_confirmation":
            regions = payload.get("uncertain_regions") or []
            if regions:
                return Decision(
                    outcome="confirmation_required",
                    reason="uncertain_regions_present",
                )
            return Decision(outcome="confirmed", reason="no_uncertain_regions")

        if route == "answer_review_routing":
            if payload.get("verification_status") == "verified_by_mock_rule":
                return Decision(
                    outcome="auto_approved", reason="verified_by_mock_rule"
                )
            return Decision(
                outcome="teacher_review_required",
                reason="answer_not_verified_by_mock_rule",
            )

        if route == "communication_approval":
            return Decision(
                outcome="approved", reason="mock_communication_approval"
            )

        return Decision(outcome="fallback", reason=f"unknown_route:{route}")
