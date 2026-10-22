"""
Hermes Agent Models

Pydantic request/response models for the Hermes 1-to-1 AI mentor:
chat, micro-topic progress, quiz attempts, and daily summaries.

Author: Mentor AI Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field


SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "hinglish": "Hinglish (Hindi-English mix)",
}

MICRO_STATES = ("UNTOUCHED", "LEARNING", "MASTERED")


# ─── Chat ────────────────────────────────────────────────────────────────

class HermesChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = Field(
        default=None,
        description="Existing session to continue; a new session is created when omitted"
    )
    micro_topic_id: Optional[str] = Field(
        default=None,
        description="Topic this doubt belongs to; drives Concept Wall revision mode"
    )
    language: Optional[str] = Field(
        default=None,
        description="Response language override: en, hi, mr, or hinglish"
    )


class HermesChatResponse(BaseModel):
    message_id: str
    session_id: str
    answer: str
    language: str
    tokens_used: int = 0
    mock: bool = False


class HermesSessionInfo(BaseModel):
    session_id: str
    child_id: str
    created_at: str
    updated_at: str
    message_count: int
    status: Literal["active", "ended"]


class HermesMessage(BaseModel):
    message_id: str
    session_id: str
    role: Literal["student", "hermes"]
    content: str
    created_at: str


# ─── Micro-topics & quiz attempts ────────────────────────────────────────

class QuizAttemptRequest(BaseModel):
    micro_topic_id: str = Field(..., min_length=1)
    score_pct: float = Field(..., ge=0, le=100)
    total_questions: int = Field(default=10, ge=1)


class QuizAttemptResult(BaseModel):
    micro_topic_id: str
    passed: bool
    state: str
    consecutive_passes: int
    consecutive_failures: int
    concept_wall_locked: bool
    events: List[str] = Field(default_factory=list)


class MicroTopicItem(BaseModel):
    micro_topic_id: str
    name: str
    subject: str
    chapter: str
    topic: str
    exam_codes: List[str]
    state: str = "UNTOUCHED"
    concept_wall_locked: bool = False


class HermesProgress(BaseModel):
    child_id: str
    exam_scope: List[str]
    total_in_scope: int
    counts: Dict[str, int]
    completion_pct: float
    locked_topics: List[str] = Field(default_factory=list)


class SeedResult(BaseModel):
    already_seeded: bool
    micro_topics_count: int
    exams: List[str]


# ─── Daily summaries ─────────────────────────────────────────────────────

class SummaryResponse(BaseModel):
    child_id: str
    date: str
    audience: Literal["student", "parent"]
    text: str
    language: str
    generated_at: str
    quiet_day: bool = False
    mock: bool = False


class GenerateSummaryRequest(BaseModel):
    date: Optional[str] = Field(
        default=None,
        description="YYYY-MM-DD; defaults to today (IST)"
    )


# ─── Gamification (XP / streaks / badges) ────────────────────────────────

class GamificationState(BaseModel):
    child_id: str
    xp: int = 0
    streak_days: int = 0
    last_active_date: Optional[str] = None
    counters: Dict[str, int] = Field(default_factory=dict)
    badges: List[str] = Field(default_factory=list)


class ActivityAward(BaseModel):
    child_id: str
    activity_type: str
    xp_awarded: int
    xp_total: int
    streak_days: int
    new_badges: List[str] = Field(default_factory=list)
    badges: List[str] = Field(default_factory=list)
    counters: Dict[str, int] = Field(default_factory=dict)


# ─── Insights (student & parent) ─────────────────────────────────────────

class TodayResponse(BaseModel):
    child_id: str
    name: str
    exam_scope: List[str]
    days_until_exam: Optional[int] = None
    chat_turns_today: int = 0
    chat_daily_cap: int = 5
    plan: str = "free"
    targets: List[MicroTopicItem] = Field(default_factory=list)
    locked_topics: List[str] = Field(default_factory=list)
    completion_pct: float = 0.0
    streak_days: int = 0
    xp: int = 0
    badges: List[str] = Field(default_factory=list)
    summary_available: bool = False
    score_prediction_available: bool = False


class ScorePrediction(BaseModel):
    child_id: str
    subjects: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    predicted_total: float = 0.0
    total_low: float = 0.0
    total_high: float = 0.0
    max_marks: int = 300
    generated_at: str


class ParentDayActivity(BaseModel):
    date: str
    chat_turns: int = 0
    quiz_attempts: int = 0


class ParentOverview(BaseModel):
    child_id: str
    window_days: int = 7
    active_days: int = 0
    chat_turns: int = 0
    quiz_attempts: int = 0
    completion_pct: float = 0.0
    counts: Dict[str, int] = Field(default_factory=dict)
    locked_topics: List[str] = Field(default_factory=list)
    streak_days: int = 0
    xp: int = 0
    badges: List[str] = Field(default_factory=list)
    attention_flags: List[str] = Field(default_factory=list)
    plan: str = "free"


class ParentWeeklyReport(ParentOverview):
    week_start: str
    week_end: str
    days: List[ParentDayActivity] = Field(default_factory=list)
