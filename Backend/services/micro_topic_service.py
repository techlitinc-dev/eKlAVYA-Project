"""
Micro-Topic Service (Hermes)

Deterministic syllabus state machine (Requirement 8/9/26 of the Hermes spec):

- Micro-topics are seeded from the static syllabus files in data/syllabus/
  (no LLM involvement, no RAG dependency) into Firestore collection
  "micro_topics", merged across exams by (subject, subtopic).
- Per-student Micro-State lives in micro_states/{child_id}/topics/{micro_topic_id}:
  UNTOUCHED -> LEARNING -> MASTERED.
- Mastery: score >= threshold on 2 consecutive attempts.
- Concept Wall: 3 consecutive failures locks the topic and blocks quiz attempts
  on other topics until the locked topic is revised and a follow-up quiz is passed.

RAG and embeddings are deliberately NOT used here — scope checks are
deterministic and the mentor's syllabus boundary is injected into the prompt.

Author: Mentor AI Team
Version: 1.0.0
"""

import glob
import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status

from models.hermes_models import (
    HermesProgress,
    MicroTopicItem,
    QuizAttemptResult,
    SeedResult,
)
from services.hermes_gamification_service import HermesGamificationService
from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

MASTERY_THRESHOLD = float(os.getenv("HERMES_MASTERY_THRESHOLD", "70"))
PASSES_FOR_MASTERY = 2
FAILS_FOR_WALL = 3
SYLLABUS_GLOB = os.getenv("HERMES_SYLLABUS_GLOB", "data/syllabus/*.json")

TOPICS_COLLECTION = "micro_topics"
STATES_COLLECTION = "micro_states"
ATTEMPTS_COLLECTION = "quiz_attempts"
SEED_META_DOC = ("hermes_meta", "micro_topics_seed")
DEFAULT_EXAM = "JEE_MAIN"


def compute_transition(
    current_state: str,
    consecutive_passes: int,
    consecutive_failures: int,
    wall_locked: bool,
    score_pct: float,
    mastery_threshold: float = MASTERY_THRESHOLD,
    revision_mode: bool = False,
) -> Tuple[str, int, int, bool, List[str]]:
    """
    Pure Micro-State transition logic (unit-testable, no I/O).

    Returns (new_state, consecutive_passes, consecutive_failures, wall_locked, events).
    """
    passed = score_pct >= mastery_threshold
    events: List[str] = []
    new_state = current_state

    if passed:
        consecutive_passes += 1
        consecutive_failures = 0
        if revision_mode and wall_locked:
            wall_locked = False
            events.append("concept_wall_cleared")
        if consecutive_passes >= PASSES_FOR_MASTERY:
            if new_state != "MASTERED":
                events.append("mastered")
            new_state = "MASTERED"
        elif new_state == "UNTOUCHED":
            new_state = "LEARNING"
    else:
        consecutive_failures += 1
        consecutive_passes = 0
        if new_state != "MASTERED":
            new_state = "LEARNING"
        if consecutive_failures >= FAILS_FOR_WALL and not wall_locked:
            wall_locked = True
            events.append("concept_wall_locked")

    return new_state, consecutive_passes, consecutive_failures, wall_locked, events


def load_syllabus_topics(pattern: str = SYLLABUS_GLOB) -> Dict[str, dict]:
    """
    Aggregate micro-topics from syllabus JSON files, merging exam codes for
    identical (subject, subtopic) pairs. Pure file I/O — no Firestore.
    """
    topics: Dict[str, dict] = {}
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Skipping syllabus file {path}: {e}")
            continue

        exam = data.get("exam", "")
        subject = data.get("subject", "")
        for chapter in data.get("chapters", []):
            for topic in chapter.get("topics", []):
                for sub in topic.get("subtopics", []):
                    name = (sub.get("subtopic_name") or "").strip()
                    if not name:
                        continue
                    key = f"{subject}|{name}"
                    if key not in topics:
                        doc_id = "mt_" + hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
                        topics[key] = {
                            "micro_topic_id": doc_id,
                            "name": name,
                            "subject": subject,
                            "chapter": chapter.get("chapter_name", ""),
                            "topic": topic.get("topic_name", ""),
                            "exam_codes": [exam] if exam else [],
                            "weightage": topic.get("weightage", 0),
                        }
                    elif exam and exam not in topics[key]["exam_codes"]:
                        topics[key]["exam_codes"].append(exam)
    return topics


class MicroTopicService:
    """Firestore-backed micro-topic state machine."""

    def __init__(self):
        self.db = get_firestore_client()
        self.gamification = HermesGamificationService()

    # ── Seeding ──────────────────────────────────────────────────────

    def seed_micro_topics(self, force: bool = False) -> SeedResult:
        meta_ref = self.db.collection(SEED_META_DOC[0]).document(SEED_META_DOC[1])
        meta = meta_ref.get()
        if meta.exists and not force:
            data = meta.to_dict() or {}
            return SeedResult(
                already_seeded=True,
                micro_topics_count=data.get("count", 0),
                exams=data.get("exams", []),
            )

        topics = load_syllabus_topics()
        batch = self.db.batch()
        for topic in topics.values():
            ref = self.db.collection(TOPICS_COLLECTION).document(topic["micro_topic_id"])
            batch.set(ref, topic)
        exams = sorted({e for t in topics.values() for e in t["exam_codes"]})
        batch.set(meta_ref, {
            "count": len(topics),
            "exams": exams,
            "seeded_at": datetime.now(timezone.utc).isoformat(),
        })
        batch.commit()
        logger.info(f"Seeded {len(topics)} micro-topics across exams: {exams}")
        return SeedResult(already_seeded=False, micro_topics_count=len(topics), exams=exams)

    # ── Scope & lookup ───────────────────────────────────────────────

    def get_exam_scope(self, child_id: str) -> List[str]:
        doc = self.db.collection("exam_selections").document(child_id).get()
        if not doc.exists:
            return [DEFAULT_EXAM]
        data = doc.to_dict() or {}
        exams = data.get("exam_types") or data.get("exam_type") or [DEFAULT_EXAM]
        if isinstance(exams, str):
            exams = [exams]
        return [str(e).upper() for e in exams]

    def get_in_scope_topics(self, child_id: str) -> List[dict]:
        exams = self.get_exam_scope(child_id)
        seen: Dict[str, dict] = {}
        for exam in exams[:10]:  # Firestore array-contains-any limit
            query = self.db.collection(TOPICS_COLLECTION).where("exam_codes", "array_contains", exam)
            for doc in query.stream():
                topic = doc.to_dict() or {}
                seen[doc.id] = topic
        return list(seen.values())

    def get_student_state(self, child_id: str, micro_topic_id: str) -> dict:
        ref = (
            self.db.collection(STATES_COLLECTION)
            .document(child_id)
            .collection("topics")
            .document(micro_topic_id)
        )
        doc = ref.get()
        if not doc.exists:
            return {
                "state": "UNTOUCHED",
                "consecutive_passes": 0,
                "consecutive_failures": 0,
                "wall_locked": False,
            }
        return doc.to_dict() or {}

    def list_topics(self, child_id: str) -> List[MicroTopicItem]:
        topics = self.get_in_scope_topics(child_id)
        items = []
        for t in topics:
            state = self.get_student_state(child_id, t["micro_topic_id"])
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
        items.sort(key=lambda x: (x.subject, x.chapter, x.name))
        return items

    def get_progress(self, child_id: str) -> HermesProgress:
        topics = self.get_in_scope_topics(child_id)
        counts = {"UNTOUCHED": 0, "LEARNING": 0, "MASTERED": 0}
        locked: List[str] = []
        for t in topics:
            state = self.get_student_state(child_id, t["micro_topic_id"])
            current = state.get("state", "UNTOUCHED")
            counts[current] = counts.get(current, 0) + 1
            if state.get("wall_locked"):
                locked.append(t.get("name", t["micro_topic_id"]))
        total = len(topics)
        mastered = counts.get("MASTERED", 0)
        return HermesProgress(
            child_id=child_id,
            exam_scope=self.get_exam_scope(child_id),
            total_in_scope=total,
            counts=counts,
            completion_pct=round((mastered / total * 100) if total else 0.0, 2),
            locked_topics=locked,
        )

    def get_chapter_scope_summary(self, child_id: str) -> Dict[str, List[str]]:
        """Subject -> chapter names, for prompt injection (Exam Scope boundary)."""
        summary: Dict[str, set] = {}
        for t in self.get_in_scope_topics(child_id):
            summary.setdefault(t.get("subject", "General"), set()).add(t.get("chapter", ""))
        return {k: sorted(v) for k, v in summary.items()}

    def get_locked_topic_name(self, child_id: str) -> Optional[str]:
        states_ref = (
            self.db.collection(STATES_COLLECTION)
            .document(child_id)
            .collection("topics")
            .where("wall_locked", "==", True)
            .limit(1)
        )
        for doc in states_ref.stream():
            topic_doc = self.db.collection(TOPICS_COLLECTION).document(doc.id).get()
            name = topic_doc.to_dict().get("name") if topic_doc.exists else doc.id
            return name
        return None

    # ── Quiz attempts & transitions ──────────────────────────────────

    def record_quiz_attempt(
        self,
        child_id: str,
        micro_topic_id: str,
        score_pct: float,
        total_questions: int,
    ) -> QuizAttemptResult:
        locked_name = self.get_locked_topic_name(child_id)
        revision_mode = False
        if locked_name:
            locked_doc_id = (
                self.db.collection(STATES_COLLECTION)
                .document(child_id)
                .collection("topics")
                .where("wall_locked", "==", True)
                .limit(1)
                .stream()
            )
            locked_ids = [d.id for d in locked_doc_id]
            if micro_topic_id not in locked_ids:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Concept Wall is active for '{locked_name}'. "
                        "Complete the mandatory revision and pass its follow-up quiz first."
                    ),
                )
            revision_mode = True

        topic_ref = self.db.collection(TOPICS_COLLECTION).document(micro_topic_id)
        if not topic_ref.get().exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Micro-topic not found: {micro_topic_id}",
            )

        current = self.get_student_state(child_id, micro_topic_id)
        new_state, passes, fails, wall, events = compute_transition(
            current_state=current.get("state", "UNTOUCHED"),
            consecutive_passes=current.get("consecutive_passes", 0),
            consecutive_failures=current.get("consecutive_failures", 0),
            wall_locked=current.get("wall_locked", False),
            score_pct=score_pct,
            revision_mode=revision_mode,
        )

        now = datetime.now(timezone.utc)
        state_ref = (
            self.db.collection(STATES_COLLECTION)
            .document(child_id)
            .collection("topics")
            .document(micro_topic_id)
        )
        state_ref.set({
            "state": new_state,
            "consecutive_passes": passes,
            "consecutive_failures": fails,
            "wall_locked": wall,
            "updated_at": now.isoformat(),
        }, merge=True)

        passed = score_pct >= MASTERY_THRESHOLD
        self.db.collection(ATTEMPTS_COLLECTION).add({
            "child_id": child_id,
            "micro_topic_id": micro_topic_id,
            "score_pct": score_pct,
            "total_questions": total_questions,
            "passed": passed,
            "revision_mode": revision_mode,
            "created_at": now,
        })

        # Denormalized daily activity counter (read by the summary service)
        day = now.strftime("%Y-%m-%d")
        usage_ref = self.db.collection("hermes_usage").document(f"{child_id}_{day}")
        usage_ref.set({
            "child_id": child_id,
            "date": day,
            "quiz_attempts": firestore_increment(1),
        }, merge=True)

        # XP awards (best-effort: never block a quiz result on gamification)
        try:
            self.gamification.award_activity(child_id, "quiz_attempt")
            if passed:
                self.gamification.award_activity(child_id, "quiz_pass")
            if "mastered" in events:
                self.gamification.award_activity(child_id, "topic_mastered")
            if "concept_wall_cleared" in events:
                self.gamification.award_activity(child_id, "wall_cleared")
        except Exception as e:
            logger.warning(f"Gamification award failed for {child_id}: {e}")

        return QuizAttemptResult(
            micro_topic_id=micro_topic_id,
            passed=passed,
            state=new_state,
            consecutive_passes=passes,
            consecutive_failures=fails,
            concept_wall_locked=wall,
            events=events,
        )


def firestore_increment(n: int):
    from firebase_admin import firestore as fs
    return fs.Increment(n)
