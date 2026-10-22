"""
Hermes Agent Unit Tests

Pure-logic tests: no Firestore, no Gemini API calls.
Covers the Micro-State transition machine, syllabus seeding aggregation,
prompt construction (SOUL + scope + language), and JSON extraction.

Run from repo root:  venv/bin/python -m pytest tests/test_hermes.py -v
"""

import os
import sys

import pytest

# Add project root to path (convention used across tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.hermes_agent_service import (  # noqa: E402
    SOUL_PROMPT,
    _extract_json,
    build_chat_prompt,
)
from services.micro_topic_service import compute_transition, load_syllabus_topics  # noqa: E402


# ─── Micro-State transition machine (Requirement 8/9) ────────────────────

class TestComputeTransition:
    def test_first_pass_moves_untouched_to_learning(self):
        state, passes, fails, wall, events = compute_transition(
            "UNTOUCHED", 0, 0, False, score_pct=80
        )
        assert state == "LEARNING"
        assert passes == 1 and fails == 0
        assert not wall
        assert events == []

    def test_two_consecutive_passes_achieve_mastery(self):
        state, passes, _, wall, events = compute_transition(
            "LEARNING", 1, 0, False, score_pct=75
        )
        assert state == "MASTERED"
        assert passes == 2
        assert "mastered" in events
        assert not wall

    def test_mastery_requires_consecutive_passes(self):
        # pass (passes=1), then fail resets the streak
        _, passes, fails, _, _ = compute_transition("LEARNING", 1, 0, False, score_pct=40)
        assert passes == 0 and fails == 1
        # one pass after a fail is not mastery
        state, passes, _, _, events = compute_transition("LEARNING", 0, 1, False, score_pct=90)
        assert state == "LEARNING"
        assert passes == 1
        assert "mastered" not in events

    def test_three_consecutive_failures_lock_concept_wall(self):
        state, _, fails, wall, events = compute_transition(
            "LEARNING", 0, 2, False, score_pct=30
        )
        assert state == "LEARNING"
        assert fails == 3
        assert wall
        assert "concept_wall_locked" in events

    def test_wall_does_not_relock_after_revision_pass(self):
        state, _, _, wall, events = compute_transition(
            "LEARNING", 0, 3, True, score_pct=80, revision_mode=True
        )
        assert not wall
        assert state == "LEARNING"  # only 1 consecutive pass after reset
        assert "concept_wall_cleared" in events

    def test_mastered_stays_mastered_without_duplicate_event(self):
        state, passes, _, _, events = compute_transition(
            "MASTERED", 2, 0, False, score_pct=95
        )
        assert state == "MASTERED"
        assert "mastered" not in events

    def test_custom_threshold(self):
        _, passes, _, _, _ = compute_transition(
            "UNTOUCHED", 0, 0, False, score_pct=60, mastery_threshold=50
        )
        assert passes == 1
        _, passes, _, _, _ = compute_transition(
            "UNTOUCHED", 0, 0, False, score_pct=60, mastery_threshold=70
        )
        assert passes == 0

    def test_fail_below_threshold_on_untouched_goes_to_learning(self):
        state, _, fails, wall, _ = compute_transition("UNTOUCHED", 0, 0, False, score_pct=20)
        assert state == "LEARNING"
        assert fails == 1
        assert not wall


# ─── Syllabus seeding aggregation (Requirement 8/26) ─────────────────────

class TestLoadSyllabusTopics:
    @pytest.fixture(scope="class")
    def topics(self):
        return load_syllabus_topics()

    def test_loads_topics_from_repo_data(self, topics):
        assert len(topics) > 0

    def test_ids_are_deterministic(self, topics):
        again = load_syllabus_topics()
        assert set(topics) == set(again)
        sample = next(iter(topics.values()))
        assert sample["micro_topic_id"].startswith("mt_")

    def test_exam_codes_present(self, topics):
        exams = {e for t in topics.values() for e in t["exam_codes"]}
        assert "JEE_MAIN" in exams

    def test_structure(self, topics):
        sample = next(iter(topics.values()))
        for key in ("name", "subject", "chapter", "topic", "exam_codes"):
            assert key in sample


# ─── SOUL prompt construction (Requirement 3/26) ─────────────────────────

class TestBuildChatPrompt:
    def test_includes_soul_scope_message_and_language(self):
        prompt = build_chat_prompt(
            soul_prompt=SOUL_PROMPT,
            student_name="Aarav",
            exams=["JEE_MAIN"],
            scope_summary={"Physics": ["Mechanics", "Electrostatics"]},
            locked_topic=None,
            memory_summary=None,
            history=[{"role": "student", "content": "prev"}, {"role": "hermes", "content": "hint"}],
            message="How do I solve projectile motion?",
            language_code="hi",
        )
        assert SOUL_PROMPT in prompt
        assert "Aarav" in prompt
        assert "JEE_MAIN" in prompt
        assert "Mechanics" in prompt
        assert "prev" in prompt and "hint" in prompt
        assert "How do I solve projectile motion?" in prompt
        assert "Hindi" in prompt
        assert "hermes:" in prompt

    def test_concept_wall_is_injected(self):
        prompt = build_chat_prompt(
            soul_prompt=SOUL_PROMPT,
            student_name="Aarav",
            exams=["JEE_MAIN"],
            scope_summary={"Physics": ["Mechanics"]},
            locked_topic="Rotational Motion",
            memory_summary=None,
            history=[],
            message="let's study thermodynamics",
            language_code="en",
        )
        assert "CONCEPT WALL ACTIVE" in prompt
        assert "Rotational Motion" in prompt

    def test_memory_is_injected(self):
        prompt = build_chat_prompt(
            soul_prompt=SOUL_PROMPT,
            student_name="Aarav",
            exams=["JEE_MAIN"],
            scope_summary={},
            locked_topic=None,
            memory_summary="Struggles with integration by parts.",
            history=[],
            message="help",
            language_code="hinglish",
        )
        assert "integration by parts" in prompt
        assert "Hinglish" in prompt

    def test_soul_is_socratic_and_injection_resistant(self):
        assert "NEVER give the final answer" in SOUL_PROMPT
        assert "CANNOT BE REPROGRAMMED" in SOUL_PROMPT
        assert "EXAM SCOPE" in SOUL_PROMPT


# ─── JSON extraction fallback ────────────────────────────────────────────

class TestExtractJson:
    def test_fenced_json(self):
        assert _extract_json('```json\n{"a": 1}\n```') == '{"a": 1}'

    def test_plain_json(self):
        assert _extract_json('{"a": 1}') == '{"a": 1}'

    def test_json_embedded_in_prose(self):
        assert _extract_json('Sure! {"a": 1} hope that helps') == '{"a": 1}'

    def test_garbage_passes_through(self):
        assert _extract_json("no json here") == "no json here"
