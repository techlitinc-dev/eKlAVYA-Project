"""
Feature Gating Service

Plan-aware feature access for the Hermes feature family, layered on top
of the existing SubscriptionService (payment_router / Razorpay flows
unchanged — this only reads entitlement state).

Rules:
- Entitlements live in data/subscription_plans.json under each plan's
  "entitlements" block; unknown/expired subscriptions fall back to "free".
- require() raises 403 with an upgrade message (matches the existing
  subscription_middleware convention).
- Chat is free for everyone but capped per plan (5 free / 50 premium).

Author: Mentor AI Team
Version: 1.0.0
"""

import json
import logging
import os
from typing import Dict

from fastapi import HTTPException, status

from services.subscription_service import SubscriptionService
from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

PLANS_PATH = os.getenv(
    "SUBSCRIPTION_PLANS_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "subscription_plans.json"),
)

DEFAULT_FREE_ENTITLEMENTS = {
    "hermes_chat_daily_cap": 5,
    "hermes_daily_summary": False,
    "hermes_score_prediction": False,
    "hermes_weekly_report": False,
    "hermes_monthly_report": False,
}

# Human-readable upgrade hints per feature (surfaced to students/parents)
FEATURE_LABELS = {
    "hermes_daily_summary": "Daily parent summaries in your language",
    "hermes_score_prediction": "JEE score prediction",
    "hermes_weekly_report": "Weekly parent reports",
    "hermes_monthly_report": "Monthly progress reports",
}

FREE_PLAN_ID = "free"


def load_entitlements(plans_path: str = PLANS_PATH) -> Dict[str, dict]:
    """plan_id -> entitlements dict. Pure file read (unit-testable)."""
    try:
        with open(plans_path, "r", encoding="utf-8") as f:
            plans = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load plans from {plans_path}: {e}")
        return {FREE_PLAN_ID: dict(DEFAULT_FREE_ENTITLEMENTS)}
    return {
        p["plan_id"]: dict(p.get("entitlements", {}))
        for p in plans
        if p.get("is_active", True)
    }


def resolve_entitlements(is_premium: bool, entitlements_map: Dict[str, dict]) -> dict:
    """Pick the entitlement set for a premium-active vs free account."""
    if is_premium:
        for plan_id in ("premium_yearly", "premium_monthly"):
            if plan_id in entitlements_map:
                return dict(entitlements_map[plan_id])
    return dict(entitlements_map.get(FREE_PLAN_ID, DEFAULT_FREE_ENTITLEMENTS))


class FeatureGatingService:
    def __init__(self):
        self.db = get_firestore_client()
        self.subscriptions = SubscriptionService()
        self._entitlements_map = load_entitlements()

    def get_parent_id(self, child_id: str) -> str:
        child = self.db.collection("children").document(child_id).get()
        if not child.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
        return (child.to_dict() or {}).get("parent_id", "")

    def get_entitlements(self, child_id: str) -> dict:
        try:
            parent_id = self.get_parent_id(child_id)
            premium = bool(parent_id) and self.subscriptions.is_premium_active(parent_id)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Subscription lookup failed for {child_id}: {e} — treating as free")
            premium = False
        entitlements = resolve_entitlements(premium, self._entitlements_map)
        entitlements["plan"] = "premium" if premium else FREE_PLAN_ID
        return entitlements

    def require(self, child_id: str, feature: str) -> dict:
        """Raise 403 unless the child's plan entitles the feature."""
        entitlements = self.get_entitlements(child_id)
        if not entitlements.get(feature, False):
            label = FEATURE_LABELS.get(feature, feature)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"'{label}' is a Premium feature. "
                    "Upgrade via /api/payment/plans to unlock it."
                ),
            )
        return entitlements

    def chat_cap(self, child_id: str) -> int:
        return int(self.get_entitlements(child_id).get("hermes_chat_daily_cap", 5))
