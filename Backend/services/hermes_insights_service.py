"""
Hermes Insights Service

Deterministic, read-only feature assembly for students and parents — no
LLM calls, so these endpoints are cheap enough to sit on home screens:

- today(): exam countdown, today's study targets (weakest LEARNING
  micro-topics by weightage, or the Concept-Wall topic if one is locked),
  streak/XP, chat usage vs plan cap, summary availability.
- score_prediction(): JEE Main marks estimate from mastery ratio weighted
  by topic weightage (Requirement 23, deterministic heuristic).
- parent_overview(): 7-day activity, progress, and attention flags
  (48h inactivity, streak at risk, active Concept Walls — Requirement 10
  without WhatsApp: flags surface in the parent portal instead).
- parent_weekly(): 7-day per-day breakdown for the weekly report.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models.hermes_models import MicroTopicItem
from services.feature_gating_service import FeatureGatingService
from services.hermes_gamification_service import HermesGamificationService
from services.micro_topic_service import MicroTopicService
from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

# JEE Main per-subject maximum marks (Req 23 uses a 300-mark frame)
SUBJECT_MAX_MARKS = {"Physics": 100, "Chemistry": 100, "Mathematics": 100}
DEFAULT_SUBJECT_MAX = 100
USAGE_COLLECTION = "hermes_usage"
SUMMARIES_COLLECTION = "daily_summaries"


def predict_score_from_mastery(subject_stats: Dict[str, dict]) -> Dict[str, dict]:
    """
    Pure score prediction. Input: {subject: {mastered_weight, total_weight}}.
    Output per subject: mastery_pct, predicted marks, and a +/-10% range,
    capped at the subject maximum. Totals sum the per-subject ranges.
    """
    subjects = {}
    total_low = total_high = total_predicted = 0
    for subject, stats in subject_stats.items():
        total_weight = stats.get("total_weight", 0)
        mastered_weight = stats.get("mastered_weight", 0)
        pct = (mastered_weight / total_weight) if total_weight else 0.0
        max_marks = SUBJECT_MAX_MARKS.get(subject, DEFAULT_SUBJECT_MAX)
        predicted = round(pct * max_marks, 1)
        low = round(max(0.0, predicted * 0.9), 1)
        high = round(min(float(max_marks), predicted * 1.1), 1)
        subjects[subject] = {
            "mastery_pct": round(pct * 100, 2),
            "predicted_marks": predicted,
            "low": low,
            "high": high,
            "max_marks": max_marks,
        }
        total_predicted += predicted
        total_low += low
        total_high += high
    max_total = sum(
        SUBJECT_MAX_MARKS.get(s, DEFAULT_SUBJECT_MAX) for s in subject_stats
    )
    return {
        "subjects": subjects,
        "predicted_total": round(total_predicted, 1),
        "total_low": round(total_low, 1),
        "total_high": round(total_high, 1),
        "max_marks": max_total,
    }


def build_attention_flags(
    usage_today: dict,
    usage_yesterday: dict,
    streak_days: int,
    locked_topics: List[str],
) -> List[str]:
    """Pure flag logic (unit-testable)."""
    flags = []
    inactive_today = usage_today.get("chat_turns", 0) == 0 and usage_today.get("quiz_attempts", 0) == 0
    inactive_yesterday = usage_yesterday.get("chat_turns", 0) == 0 and usage_yesterday.get("quiz_attempts", 0) == 0
    if inactive_today and inactive_yesterday:
        flags.append("inactive_48h")
    if streak_days >= 3 and inactive_today:
        flags.append("streak_at_risk")
    if locked_topics:
        flags.append("concept_wall_active")
    return flags


class HermesInsightsService:
    def __init__(self):
        self.db = get_firestore_client()
        self.topics = MicroTopicService()
        self.gamification = HermesGamificationService()
        self.gating = FeatureGatingService()

    # ── internals ────────────────────────────────────────────────────

    def _usage(self, child_id: str, date_str: str) -> dict:
        doc = self.db.collection(USAGE_COLLECTION).document(f"{child_id}_{date_str}").get()
        return doc.to_dict() if doc.exists else {}

    def _days_until_exam(self, child_id: str) -> Optional[int]:
        doc = self.db.collection("exam_selections").document(child_id).get()
        if not doc.exists:
            return None
        exam_date = (doc.to_dict() or {}).get("exam_date")
        if not exam_date:
            return None
        try:
            exam = datetime.strptime(str(exam_date)[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
        return (exam - datetime.now().date()).days

    def _topics_with_state(self, child_id: str) -> List[MicroTopicItem]:
        items = []
        for t in self.topics.get_in_scope_topics(child_id):
            state = self.topics.get_student_state(child_id, t["micro_topic_id"])
            items.append(MicroTopicItem(
                micro_topic_id=t["micro_topic_id"],
                name=t.get("name", ""),
                subject=t.get("subject", ""),
                chapter=t.get("chapter", ""),
                topic=t.get("topic", ""),
                exam_codes=t.get("exam_codes", []),
                state=state.get("state", "UNTOUCHED"),
                concept_wall_locked=state.get("wall_locked", False),
            ))
        return items

    def _pick_targets(self, items: List[MicroTopicItem]) -> List[MicroTopicItem]:
        locked = [i for i in items if i.concept_wall_locked]
        if locked:
            return locked[:3]
        learning = [i for i in items if i.state == "LEARNING"]
        if learning:
            return learning[:3]
        untouched = [i for i in items if i.state == "UNTOUCHED"]
        return untouched[:3]

    # ── student ──────────────────────────────────────────────────────

    def today(self, child_id: str) -> dict:
        child = self.db.collection("children").document(child_id).get()
        child_name = (child.to_dict() or {}).get("name", "Student") if child.exists else "Student"
        today_str = datetime.now().strftime("%Y-%m-%d")
        progress = self.topics.get_progress(child_id)
        gamification = self.gamification.get_state(child_id)
        entitlements = self.gating.get_entitlements(child_id)
        usage_today = self._usage(child_id, today_str)
        summary = (
            self.db.collection(SUMMARIES_COLLECTION)
            .document(f"{child_id}_{today_str}").get()
        )

        items = self._topics_with_state(child_id)
        targets = self._pick_targets(items)
        weight_map = {
            t["micro_topic_id"]: t.get("weightage", 0)
            for t in self.topics.get_in_scope_topics(child_id)
        }
        targets = sorted(targets, key=lambda i: weight_map.get(i.micro_topic_id, 0), reverse=True)

        return {
            "child_id": child_id,
            "name": child_name,
            "exam_scope": progress.exam_scope,
            "days_until_exam": self._days_until_exam(child_id),
            "chat_turns_today": usage_today.get("chat_turns", 0),
            "chat_daily_cap": entitlements.get("hermes_chat_daily_cap", 5),
            "plan": entitlements.get("plan", "free"),
            "targets": [t.model_dump() for t in targets],
            "locked_topics": progress.locked_topics,
            "completion_pct": progress.completion_pct,
            "streak_days": gamification["streak_days"],
            "xp": gamification["xp"],
            "badges": gamification["badges"],
            "summary_available": summary.exists,
            "score_prediction_available": bool(entitlements.get("hermes_score_prediction")),
        }

    def score_prediction(self, child_id: str) -> dict:
        items = self.topics.get_in_scope_topics(child_id)
        stats: Dict[str, dict] = {}
        for t in items:
            subject = t.get("subject", "General")
            bucket = stats.setdefault(subject, {"mastered_weight": 0, "total_weight": 0})
            weight = t.get("weightage", 0) or 1
            bucket["total_weight"] += weight
            state = self.topics.get_student_state(child_id, t["micro_topic_id"])
            if state.get("state") == "MASTERED":
                bucket["mastered_weight"] += weight
        prediction = predict_score_from_mastery(stats)
        prediction["child_id"] = child_id
        prediction["generated_at"] = datetime.now().isoformat()
        return prediction

    # ── parent ───────────────────────────────────────────────────────

    def _window(self, child_id: str, end_date: str, days: int) -> List[dict]:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        out = []
        for i in range(days):
            d = (end - timedelta(days=i)).strftime("%Y-%m-%d")
            usage = self._usage(child_id, d)
            out.append({
                "date": d,
                "chat_turns": usage.get("chat_turns", 0),
                "quiz_attempts": usage.get("quiz_attempts", 0),
            })
        return out

    def _flags(self, child_id: str, streak_days: int, locked_topics: List[str]) -> List[str]:
        today_str = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now().date() - timedelta(days=1)).strftime("%Y-%m-%d")
        return build_attention_flags(
            self._usage(child_id, today_str),
            self._usage(child_id, yesterday),
            streak_days,
            locked_topics,
        )

    def parent_overview(self, child_id: str) -> dict:
        progress = self.topics.get_progress(child_id)
        gamification = self.gamification.get_state(child_id)
        entitlements = self.gating.get_entitlements(child_id)
        week = self._window(child_id, datetime.now().strftime("%Y-%m-%d"), 7)
        active_days = sum(
            1 for d in week if d["chat_turns"] or d["quiz_attempts"]
        )
        return {
            "child_id": child_id,
            "window_days": 7,
            "active_days": active_days,
            "chat_turns": sum(d["chat_turns"] for d in week),
            "quiz_attempts": sum(d["quiz_attempts"] for d in week),
            "completion_pct": progress.completion_pct,
            "counts": progress.counts,
            "locked_topics": progress.locked_topics,
            "streak_days": gamification["streak_days"],
            "xp": gamification["xp"],
            "badges": gamification["badges"],
            "attention_flags": self._flags(child_id, gamification["streak_days"], progress.locked_topics),
            "plan": entitlements.get("plan", "free"),
        }

    def parent_weekly(self, child_id: str, end_date: str) -> dict:
        progress = self.topics.get_progress(child_id)
        gamification = self.gamification.get_state(child_id)
        days = self._window(child_id, end_date, 7)
        active_days = sum(1 for d in days if d["chat_turns"] or d["quiz_attempts"])
        return {
            "child_id": child_id,
            "week_start": days[-1]["date"],
            "week_end": days[0]["date"],
            "days": days,
            "active_days": active_days,
            "chat_turns": sum(d["chat_turns"] for d in days),
            "quiz_attempts": sum(d["quiz_attempts"] for d in days),
            "completion_pct": progress.completion_pct,
            "counts": progress.counts,
            "locked_topics": progress.locked_topics,
            "streak_days": gamification["streak_days"],
            "xp": gamification["xp"],
            "attention_flags": self._flags(child_id, gamification["streak_days"], progress.locked_topics),
        }
