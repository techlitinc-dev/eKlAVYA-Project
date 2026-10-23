"""
Hermes Daily Summary Service

Generates the idempotent daily summary (Requirement 12 of the Hermes spec,
adapted): one Gemini call producing TWO versions — a motivational one for
the student and a factual one for the parent — in the parent's selected
language (en/hi/mr).

Cost rules:
- Idempotent doc id {child_id}_{date}: re-runs return the existing summary.
- Quiet days (no chat turns, no quiz attempts) are served a localized
  static template with ZERO API calls.
- One Gemini call per active student per day, run off-peak by cron.

Author: Mentor AI Team
Version: 1.0.0
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from models.hermes_models import SummaryResponse
from services.feature_gating_service import FeatureGatingService
from services.hermes_agent_service import HERMES_MOCK, _extract_json
from services.micro_topic_service import MicroTopicService
from utils.firebase_config import get_firestore_client
from utils.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

SUMMARY_MAX_OUTPUT_TOKENS = int(os.getenv("HERMES_SUMMARY_MAX_TOKENS", "700"))
SUMMARIES_COLLECTION = "daily_summaries"

QUIET_DAY_TEMPLATES = {
    "en": (
        "No activity today. A rest day is fine — what matters is showing up tomorrow. "
        "Your mentor is ready when you are."
    ),
    "hi": (
        "आज कोई गतिविधि नहीं हुई। आराम करना भी ज़रूरी है — कल फिर से पढ़ाई शुरू करें। "
        "आपका मेंटर आपका इंतज़ार कर रहा है।"
    ),
    "mr": (
        "आज कोणतीही कामगिरी झाली नाही. विश्राम घेणेही गरजेचे आहे — उद्या पुन्हा अभ्यास सुरू करा. "
        "तुमचा मेंटर तुमची वाट पाहत आहे."
    ),
}

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "mr": "Marathi"}


class HermesSummaryService:
    def __init__(self):
        self.db = get_firestore_client()
        self.micro_topics = MicroTopicService()
        self.gating = FeatureGatingService()

    # ── Public API ───────────────────────────────────────────────────

    def get_summary(self, child_id: str, date_str: str, audience: str) -> Optional[SummaryResponse]:
        doc = (
            self.db.collection(SUMMARIES_COLLECTION)
            .document(self._doc_id(child_id, date_str))
            .get()
        )
        if not doc.exists:
            return None
        return self._to_response(doc.to_dict() or {}, audience)

    async def generate(self, child_id: str, date_str: str) -> SummaryResponse:
        """Idempotent: returns the existing summary if already generated."""
        existing = (
            self.db.collection(SUMMARIES_COLLECTION)
            .document(self._doc_id(child_id, date_str))
            .get()
        )
        if existing.exists:
            data = existing.to_dict() or {}
            return self._to_response(data, "parent")

        child = self.db.collection("children").document(child_id).get()
        if not child.exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Child not found")
        child_name = (child.to_dict() or {}).get("name", "Student")

        language = self._resolve_parent_language(child_id)
        usage = self._get_usage(child_id, date_str)
        quiet_day = usage.get("chat_turns", 0) == 0 and usage.get("quiz_attempts", 0) == 0
        progress = self.micro_topics.get_progress(child_id)

        if quiet_day:
            text = QUIET_DAY_TEMPLATES.get(language, QUIET_DAY_TEMPLATES["en"])
            versions = {"student_version": text, "parent_version": text}
            doc = self._write(child_id, date_str, language, versions, quiet_day=True, mock=False)
        else:
            versions = await self._generate_versions(
                child_name=child_name,
                language=language,
                date_str=date_str,
                usage=usage,
                progress=progress.model_dump(),
                locked_topics=progress.locked_topics,
            )
            doc = self._write(child_id, date_str, language, versions, quiet_day=False, mock=HERMES_MOCK)

        logger.info(f"Daily summary for {child_id} on {date_str}: quiet_day={quiet_day}")
        return self._to_response(doc, "parent")

    async def generate_for_all_children(self, date_str: str) -> Dict[str, Any]:
        """
        Nightly batch entry point (cron-friendly): generate the summary for
        every child. Existing summaries are skipped (idempotent); per-child
        failures are logged and counted, never aborting the batch.
        """
        stats: Dict[str, Any] = {
            "date": date_str,
            "generated": 0,
            "skipped_existing": 0,
            "skipped_not_entitled": 0,
            "failed": 0,
            "failures": [],
        }
        for doc in self.db.collection("children").stream():
            child_id = doc.id
            try:
                existing = (
                    self.db.collection(SUMMARIES_COLLECTION)
                    .document(self._doc_id(child_id, date_str))
                    .get()
                )
                if existing.exists:
                    stats["skipped_existing"] += 1
                    continue
                if not self.gating.get_entitlements(child_id).get("hermes_daily_summary"):
                    stats["skipped_not_entitled"] += 1
                    continue
                await self.generate(child_id, date_str)
                stats["generated"] += 1
            except Exception as e:
                stats["failed"] += 1
                stats["failures"].append({"child_id": child_id, "error": str(e)})
                logger.error(f"Daily summary failed for {child_id}: {e}")
        return stats

    # ── Internals ────────────────────────────────────────────────────

    def _doc_id(self, child_id: str, date_str: str) -> str:
        return f"{child_id}_{date_str}"

    def _to_response(self, data: dict, audience: str) -> SummaryResponse:
        return SummaryResponse(
            child_id=data.get("child_id", ""),
            date=data.get("date", ""),
            audience=audience,
            text=data.get(f"{audience}_version", ""),
            language=data.get("language", "en"),
            generated_at=data.get("generated_at", ""),
            quiet_day=data.get("quiet_day", False),
            mock=data.get("mock", False),
        )

    def _write(
        self,
        child_id: str,
        date_str: str,
        language: str,
        versions: dict,
        quiet_day: bool,
        mock: bool,
    ) -> dict:
        doc = {
            "child_id": child_id,
            "date": date_str,
            "language": language,
            "student_version": versions.get("student_version", ""),
            "parent_version": versions.get("parent_version", ""),
            "quiet_day": quiet_day,
            "mock": mock,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.db.collection(SUMMARIES_COLLECTION).document(self._doc_id(child_id, date_str)).set(doc)
        return doc

    def _get_usage(self, child_id: str, date_str: str) -> dict:
        doc = (
            self.db.collection("hermes_usage")
            .document(self._doc_id(child_id, date_str))
            .get()
        )
        return doc.to_dict() if doc.exists else {}

    def _resolve_parent_language(self, child_id: str) -> str:
        try:
            child = self.db.collection("children").document(child_id).get()
            parent_id = (child.to_dict() or {}).get("parent_id") if child.exists else None
            if parent_id:
                prefs = (
                    self.db.collection("parents")
                    .document(parent_id)
                    .collection("preferences")
                    .document("settings")
                    .get()
                )
                lang = (prefs.to_dict() or {}).get("language")
                if lang in LANGUAGE_NAMES:
                    return lang
        except Exception as e:
            logger.warning(f"Language resolution failed for {child_id}: {e}")
        return "en"

    async def _generate_versions(
        self,
        child_name: str,
        language: str,
        date_str: str,
        usage: dict,
        progress: dict,
        locked_topics: list,
    ) -> dict:
        if HERMES_MOCK:
            return {
                "student_version": (
                    "Mock mode: great work today! You practised consistently — "
                    "keep the streak alive tomorrow."
                ),
                "parent_version": (
                    "Mock mode: your child was active today. Chat and quiz activity recorded."
                ),
            }
        prompt = self._build_prompt(
            child_name, LANGUAGE_NAMES.get(language, "English"), date_str, usage, progress, locked_topics
        )
        try:
            client = get_gemini_client()
            raw = await client.generate_content_async(
                prompt=prompt,
                temperature=0.6,
                max_output_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
            )
            return json.loads(_extract_json(raw))
        except Exception as exc:
            logger.warning(f"Summary generation fallback ({exc})")
            turns = usage.get("chat_turns", 0)
            quizzes = usage.get("quiz_attempts", 0)
            pct = progress.get("completion_pct", 0)
            walls = ", ".join(locked_topics) if locked_topics else "None"
            return {
                "student_version": (
                    f"Great consistency today, {child_name}! You completed {turns} Socratic mentor turns "
                    f"and {quizzes} topic quiz attempts, bringing your overall syllabus mastery to {pct}%. "
                    f"Keep up the momentum tomorrow!"
                ),
                "parent_version": (
                    f"Daily Progress Report for {child_name} ({date_str}): Completed {turns} Socratic AI "
                    f"mentor interactions and {quizzes} mastery quizzes today. Overall syllabus completion "
                    f"stands at {pct}%. Active Concept Walls requiring revision: {walls}."
                ),
            }

    @staticmethod
    def _build_prompt(
        child_name: str,
        language_name: str,
        date_str: str,
        usage: dict,
        progress: dict,
        locked_topics: list,
    ) -> str:
        return f"""You write the daily progress summary for a JEE/NEET/CBSE coaching platform. Reply with ONLY a JSON object with exactly two keys: "student_version" and "parent_version".

Rules:
- Both versions must be entirely in {language_name}.
- "student_version": warm, motivating, 3-4 sentences for the student. Mention today's activity and one specific encouragement. Never shame.
- "parent_version": factual and calm, 3-4 sentences for the parent covering activity, quiz performance, syllabus completion, and anything needing attention.
- Do not invent numbers that are not provided below.

Student: {child_name}
Date: {date_str}
Today's activity: {usage.get('chat_turns', 0)} mentor chat turns, {usage.get('quiz_attempts', 0)} quiz attempts
Syllabus: {progress['completion_pct']}% complete ({progress['counts']})
Concept walls active: {', '.join(locked_topics) if locked_topics else 'none'}"""
