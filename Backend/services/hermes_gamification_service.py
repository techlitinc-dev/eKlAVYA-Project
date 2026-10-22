"""
Hermes Gamification Service

XP, daily streaks, and milestone badges for Hermes activity (Requirement 21
of the Hermes spec, scoped to the mentor feature family). Deterministic —
no LLM, no randomness.

XP values (configurable here, kept in code for simplicity):
    chat_turn        +2
    quiz_attempt     +5
    quiz_pass        +10
    topic_mastered   +25
    wall_cleared     +15

Badges are derived from lifetime counters, so they survive data resets of
other collections and are cheap to evaluate on every activity.

Note: the legacy gamification_router (achievements/challenges) is a
separate, older system — merging the two trackers is future work.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

XP_VALUES = {
    "chat_turn": 2,
    "quiz_attempt": 5,
    "quiz_pass": 10,
    "topic_mastered": 25,
    "wall_cleared": 15,
}

ACTIVITY_COUNTERS = (
    "chat_turns",
    "quiz_attempts",
    "quiz_passes",
    "masteries",
    "walls_cleared",
)

BADGE_RULES = [
    ("first_steps", "First activity on Hermes"),
    ("quiz_10_passed", "10 quizzes passed"),
    ("first_mastered", "First topic mastered"),
    ("wall_breaker", "Cleared a Concept Wall"),
    ("streak_7", "7-day streak"),
    ("streak_30", "30-day streak"),
]

COLLECTION = "hermes_gamification"


def next_streak(last_active_date: Optional[str], today: str) -> int:
    """
    Pure streak calculation. Dates are 'YYYY-MM-DD' strings.
    - no prior activity        -> 1
    - already active today     -> unchanged (caller passes current streak)
    - active yesterday         -> +1
    - gap of 2+ days           -> reset to 1
    """
    if not last_active_date:
        return 1
    if last_active_date == today:
        return -1  # sentinel: caller keeps existing streak
    try:
        last = datetime.strptime(last_active_date, "%Y-%m-%d").date()
        today_d = datetime.strptime(today, "%Y-%m-%d").date()
    except ValueError:
        return 1
    if last == today_d - timedelta(days=1):
        return -2  # sentinel: caller increments
    return 1


def evaluate_badges(counters: Dict[str, int], streak_days: int) -> List[str]:
    """Pure badge eligibility from lifetime counters + current streak."""
    earned = []
    if counters.get("chat_turns", 0) + counters.get("quiz_attempts", 0) >= 1:
        earned.append("first_steps")
    if counters.get("quiz_passes", 0) >= 10:
        earned.append("quiz_10_passed")
    if counters.get("masteries", 0) >= 1:
        earned.append("first_mastered")
    if counters.get("walls_cleared", 0) >= 1:
        earned.append("wall_breaker")
    if streak_days >= 7:
        earned.append("streak_7")
    if streak_days >= 30:
        earned.append("streak_30")
    return earned


class HermesGamificationService:
    def __init__(self):
        self.db = get_firestore_client()

    def _ref(self, child_id: str):
        return self.db.collection(COLLECTION).document(child_id)

    def _defaults(self, child_id: str) -> dict:
        return {
            "child_id": child_id,
            "xp": 0,
            "streak_days": 0,
            "last_active_date": None,
            "counters": {c: 0 for c in ACTIVITY_COUNTERS},
            "badges": [],
        }

    def get_state(self, child_id: str) -> dict:
        doc = self._ref(child_id).get()
        state = self._defaults(child_id)
        if doc.exists:
            stored = doc.to_dict() or {}
            state.update({k: v for k, v in stored.items() if k in state})
            counters = stored.get("counters", {})
            state["counters"] = {c: int(counters.get(c, 0)) for c in ACTIVITY_COUNTERS}
        return state

    def award_activity(self, child_id: str, activity_type: str) -> dict:
        """
        Record one activity: adds XP, updates the streak, evaluates badges.
        Returns the award summary (new_badges for notifications).
        """
        if activity_type not in XP_VALUES:
            raise ValueError(f"Unknown activity type: {activity_type}")

        state = self.get_state(child_id)
        today = datetime.now().strftime("%Y-%m-%d")

        streak = next_streak(state["last_active_date"], today)
        if streak == -1:
            streak = state["streak_days"] or 1
        elif streak == -2:
            streak = state["streak_days"] + 1
        # else streak == 1 (new or reset)

        counter_keys = {
            "chat_turn": "chat_turns",
            "quiz_attempt": "quiz_attempts",
            "quiz_pass": "quiz_passes",
            "topic_mastered": "masteries",
            "wall_cleared": "walls_cleared",
        }
        counters = state["counters"]
        counters_key = counter_keys[activity_type]
        counters[counters_key] = counters.get(counters_key, 0) + 1

        xp = state["xp"] + XP_VALUES[activity_type]
        badges = list(state["badges"])
        new_badges = [
            b for b in evaluate_badges(counters, streak)
            if b not in badges
        ]
        badges.extend(new_badges)

        self._ref(child_id).set({
            "child_id": child_id,
            "xp": xp,
            "streak_days": streak,
            "last_active_date": today,
            "counters": counters,
            "badges": badges,
            "updated_at": datetime.now().isoformat(),
        })

        return {
            "child_id": child_id,
            "activity_type": activity_type,
            "xp_awarded": XP_VALUES[activity_type],
            "xp_total": xp,
            "streak_days": streak,
            "new_badges": new_badges,
            "badges": badges,
            "counters": counters,
        }
