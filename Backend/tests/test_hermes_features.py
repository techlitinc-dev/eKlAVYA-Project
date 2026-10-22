"""
Unit tests for the Hermes feature layer: gamification, feature gating,
and deterministic insights logic. Pure functions only — no Firestore,
no Gemini, no network.

Run from repo root:  venv/bin/python -m pytest tests/test_hermes_features.py -v
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.feature_gating_service import (  # noqa: E402
    DEFAULT_FREE_ENTITLEMENTS,
    load_entitlements,
    resolve_entitlements,
)
from services.hermes_gamification_service import (  # noqa: E402
    XP_VALUES,
    evaluate_badges,
    next_streak,
)
from services.hermes_insights_service import (  # noqa: E402
    build_attention_flags,
    predict_score_from_mastery,
)


# ─── Streaks ─────────────────────────────────────────────────────────────

class TestNextStreak:
    def test_first_activity(self):
        assert next_streak(None, "2026-10-21") == 1

    def test_same_day_keeps_streak(self):
        assert next_streak("2026-10-21", "2026-10-21") == -1

    def test_consecutive_day_increments(self):
        assert next_streak("2026-10-20", "2026-10-21") == -2

    def test_gap_resets(self):
        assert next_streak("2026-10-15", "2026-10-21") == 1

    def test_invalid_date_resets(self):
        assert next_streak("not-a-date", "2026-10-21") == 1


# ─── Badges ──────────────────────────────────────────────────────────────

class TestEvaluateBadges:
    def test_first_steps(self):
        assert "first_steps" in evaluate_badges({"chat_turns": 1}, 1)

    def test_quiz_10_passed_threshold(self):
        assert "quiz_10_passed" not in evaluate_badges({"quiz_passes": 9}, 1)
        assert "quiz_10_passed" in evaluate_badges({"quiz_passes": 10}, 1)

    def test_first_mastered_and_wall_breaker(self):
        badges = evaluate_badges({"masteries": 1, "walls_cleared": 1}, 1)
        assert "first_mastered" in badges
        assert "wall_breaker" in badges

    def test_streak_badges(self):
        assert "streak_7" not in evaluate_badges({}, 6)
        assert "streak_7" in evaluate_badges({}, 7)
        assert "streak_30" in evaluate_badges({}, 30)

    def test_nothing_earned_by_default(self):
        assert evaluate_badges({}, 0) == []

    def test_xp_values_present(self):
        for key in ("chat_turn", "quiz_attempt", "quiz_pass", "topic_mastered", "wall_cleared"):
            assert key in XP_VALUES and XP_VALUES[key] > 0


# ─── Score prediction ────────────────────────────────────────────────────

class TestPredictScore:
    def test_full_mastery(self):
        stats = {s: {"mastered_weight": 10, "total_weight": 10} for s in
                 ("Physics", "Chemistry", "Mathematics")}
        result = predict_score_from_mastery(stats)
        assert result["predicted_total"] == 300
        assert result["total_high"] == 300  # capped at max
        assert result["total_low"] == 270
        assert result["subjects"]["Physics"]["mastery_pct"] == 100.0

    def test_half_mastery(self):
        stats = {"Physics": {"mastered_weight": 5, "total_weight": 10}}
        result = predict_score_from_mastery(stats)
        assert result["subjects"]["Physics"]["predicted_marks"] == 50
        assert result["subjects"]["Physics"]["low"] == 45
        assert result["subjects"]["Physics"]["high"] == 55
        assert result["max_marks"] == 100

    def test_empty_scope(self):
        result = predict_score_from_mastery({})
        assert result["predicted_total"] == 0
        assert result["max_marks"] == 0

    def test_zero_total_weight_is_safe(self):
        result = predict_score_from_mastery(
            {"Physics": {"mastered_weight": 0, "total_weight": 0}}
        )
        assert result["subjects"]["Physics"]["predicted_marks"] == 0


# ─── Attention flags ─────────────────────────────────────────────────────

class TestAttentionFlags:
    def test_inactive_48h(self):
        flags = build_attention_flags({}, {}, 0, [])
        assert "inactive_48h" in flags

    def test_active_today_clears_inactive(self):
        flags = build_attention_flags({"chat_turns": 1}, {}, 0, [])
        assert "inactive_48h" not in flags

    def test_streak_at_risk(self):
        flags = build_attention_flags({}, {"quiz_attempts": 1}, 5, [])
        assert "streak_at_risk" in flags

    def test_no_streak_at_risk_below_3(self):
        flags = build_attention_flags({}, {"quiz_attempts": 1}, 2, [])
        assert "streak_at_risk" not in flags

    def test_concept_wall_flag(self):
        flags = build_attention_flags({"chat_turns": 1}, {"chat_turns": 1}, 0, ["Rotational Motion"])
        assert "concept_wall_active" in flags


# ─── Entitlements / gating ───────────────────────────────────────────────

class TestEntitlements:
    @pytest.fixture(scope="class")
    def plans(self):
        return load_entitlements()

    def test_plans_file_loads(self, plans):
        assert "free" in plans
        assert plans["free"]["hermes_chat_daily_cap"] == 5
        assert plans["free"]["hermes_daily_summary"] is False

    def test_premium_entitlements(self, plans):
        premium = plans["premium_monthly"]
        assert premium["hermes_chat_daily_cap"] == 50
        assert premium["hermes_daily_summary"] is True
        assert premium["hermes_score_prediction"] is True
        assert premium["hermes_weekly_report"] is True

    def test_yearly_gets_monthly_report(self, plans):
        assert plans["premium_yearly"]["hermes_monthly_report"] is True
        assert plans["premium_monthly"]["hermes_monthly_report"] is False

    def test_resolve_free(self, plans):
        ent = resolve_entitlements(False, plans)
        assert ent["hermes_chat_daily_cap"] == 5
        assert ent["hermes_daily_summary"] is False

    def test_resolve_premium_prefers_yearly(self, plans):
        ent = resolve_entitlements(True, plans)
        assert ent["hermes_chat_daily_cap"] == 50
        assert ent["hermes_daily_summary"] is True

    def test_resolve_premium_monthly_only(self):
        plans = {
            "free": {"hermes_chat_daily_cap": 5},
            "premium_monthly": {"hermes_chat_daily_cap": 50},
        }
        assert resolve_entitlements(True, plans)["hermes_chat_daily_cap"] == 50

    def test_missing_file_falls_back_to_defaults(self, tmp_path):
        ent = load_entitlements(str(tmp_path / "nope.json"))
        assert ent["free"] == DEFAULT_FREE_ENTITLEMENTS
