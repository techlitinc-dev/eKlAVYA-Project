"""
Hermes Router

API surface for the 1-to-1 AI mentor (Hermes agent):

- Chat with the Socratic mentor (student token)
- Session listing/history/end
- Quiz attempts driving the Micro-State machine (student token)
- In-scope micro-topics and progress (student or owning parent)
- Idempotent daily summaries, student and parent audiences
- One-time syllabus seeding from data/syllabus/*.json

Auth reuses get_current_user (JWT); ownership is checked against the
children/parents Firestore collections.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status

from middleware.auth_middleware import get_current_user
from models.hermes_models import (
    GamificationState,
    GenerateSummaryRequest,
    HermesChatRequest,
    HermesChatResponse,
    HermesMessage,
    HermesProgress,
    HermesSessionInfo,
    MicroTopicItem,
    ParentOverview,
    ParentWeeklyReport,
    QuizAttemptRequest,
    QuizAttemptResult,
    ScorePrediction,
    SeedResult,
    SummaryResponse,
    TodayResponse,
)
from services.feature_gating_service import FeatureGatingService
from services.hermes_agent_service import HermesAgentService
from services.hermes_gamification_service import HermesGamificationService
from services.hermes_insights_service import HermesInsightsService
from services.hermes_summary_service import HermesSummaryService
from services.micro_topic_service import MicroTopicService
from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/hermes", tags=["Hermes AI Mentor"])

_agent_service: Optional[HermesAgentService] = None
_summary_service: Optional[HermesSummaryService] = None
_topic_service: Optional[MicroTopicService] = None


def get_agent_service() -> HermesAgentService:
    global _agent_service
    if _agent_service is None:
        _agent_service = HermesAgentService()
    return _agent_service


def get_summary_service() -> HermesSummaryService:
    global _summary_service
    if _summary_service is None:
        _summary_service = HermesSummaryService()
    return _summary_service


def get_topic_service() -> MicroTopicService:
    global _topic_service
    if _topic_service is None:
        _topic_service = MicroTopicService()
    return _topic_service


_insights_service: Optional[HermesInsightsService] = None
_gamification_service: Optional[HermesGamificationService] = None
_gating_service: Optional[FeatureGatingService] = None


def get_insights_service() -> HermesInsightsService:
    global _insights_service
    if _insights_service is None:
        _insights_service = HermesInsightsService()
    return _insights_service


def get_gamification_service() -> HermesGamificationService:
    global _gamification_service
    if _gamification_service is None:
        _gamification_service = HermesGamificationService()
    return _gamification_service


def get_gating_service() -> FeatureGatingService:
    global _gating_service
    if _gating_service is None:
        _gating_service = FeatureGatingService()
    return _gating_service


def resolve_child_access(user_id: str, child_id_param: Optional[str]) -> Tuple[str, str]:
    """
    Resolve the acting child_id and the caller's role.

    A child token (user_id is a children doc) acts as itself. A parent token
    must pass child_id and own it. Returns (child_id, role).
    """
    db = get_firestore_client()
    child_doc = db.collection("children").document(user_id).get()
    if child_doc.exists:
        return user_id, "student"
    parent_doc = db.collection("parents").document(user_id).get()
    if not parent_doc.exists:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown user")
    if not child_id_param:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="child_id query parameter required for parent access",
        )
    child_doc = db.collection("children").document(child_id_param).get()
    if not child_doc.exists or (child_doc.to_dict() or {}).get("parent_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this child",
        )
    return child_id_param, "parent"


def today_ist() -> str:
    # Cron passes explicit dates; default is server-local date.
    return datetime.now().strftime("%Y-%m-%d")


# ─── Chat ────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=HermesChatResponse,
    summary="Chat with the Hermes mentor",
    description="Socratic 1-to-1 mentor: hints, not answers. Student token only; parents get 403.",
)
async def chat(
    request: HermesChatRequest,
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesAgentService = Depends(get_agent_service),
) -> HermesChatResponse:
    resolved_child_id, role = resolve_child_access(current_user, child_id)
    if role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the student can chat with the mentor",
        )
    return await service.chat(
        child_id=resolved_child_id,
        message=request.message,
        session_id=request.session_id,
        micro_topic_id=request.micro_topic_id,
        language_override=request.language,
    )


@router.get(
    "/sessions",
    response_model=List[HermesSessionInfo],
    summary="List mentor sessions",
)
def list_sessions(
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesAgentService = Depends(get_agent_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    return service.list_sessions(resolved_child_id)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=List[HermesMessage],
    summary="Get session chat history",
)
def get_messages(
    session_id: str,
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesAgentService = Depends(get_agent_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    return service.get_messages(session_id, resolved_child_id)


@router.post(
    "/sessions/{session_id}/end",
    summary="End a session and roll up tutor memory",
)
def end_session(
    session_id: str,
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesAgentService = Depends(get_agent_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    service.end_session(session_id, resolved_child_id)
    return {"status": "ended", "session_id": session_id}


# ─── Micro-topics & quiz attempts ────────────────────────────────────────

@router.post(
    "/quiz/attempt",
    response_model=QuizAttemptResult,
    summary="Record a quiz attempt and update Micro-State",
    description="Drives UNTOUCHED -> LEARNING -> MASTERED and the Concept Wall.",
)
def record_quiz_attempt(
    request: QuizAttemptRequest,
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: MicroTopicService = Depends(get_topic_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    return service.record_quiz_attempt(
        child_id=resolved_child_id,
        micro_topic_id=request.micro_topic_id,
        score_pct=request.score_pct,
        total_questions=request.total_questions,
    )


@router.get(
    "/topics",
    response_model=List[MicroTopicItem],
    summary="List in-scope micro-topics with student state",
)
def list_topics(
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: MicroTopicService = Depends(get_topic_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    return service.list_topics(resolved_child_id)


@router.get(
    "/progress",
    response_model=HermesProgress,
    summary="Syllabus completion and Concept Wall status",
)
def get_progress(
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: MicroTopicService = Depends(get_topic_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    return service.get_progress(resolved_child_id)


@router.post(
    "/admin/seed-topics",
    response_model=SeedResult,
    summary="Seed micro-topics from data/syllabus (idempotent)",
)
def seed_topics(
    force: bool = Query(default=False),
    current_user: str = Depends(get_current_user),
    service: MicroTopicService = Depends(get_topic_service),
):
    return service.seed_micro_topics(force=force)


# ─── Daily summaries ─────────────────────────────────────────────────────

@router.post(
    "/summary/generate/{child_id}",
    response_model=SummaryResponse,
    summary="Generate today's summary (idempotent; cron-callable)",
)
async def generate_summary(
    child_id: str,
    request: Optional[GenerateSummaryRequest] = None,
    date: Optional[str] = Query(default=None, description="YYYY-MM-DD, default today"),
    current_user: str = Depends(get_current_user),
    service: HermesSummaryService = Depends(get_summary_service),
    gating: FeatureGatingService = Depends(get_gating_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    gating.require(resolved_child_id, "hermes_daily_summary")
    date_str = date or (request.date if request else None) or today_ist()
    return await service.generate(resolved_child_id, date_str)


@router.get(
    "/summary/{child_id}",
    response_model=SummaryResponse,
    summary="Get a generated daily summary",
)
def get_summary(
    child_id: str,
    date: str = Query(default=None, description="YYYY-MM-DD, default today"),
    audience: str = Query(default="student", pattern="^(student|parent)$"),
    current_user: str = Depends(get_current_user),
    service: HermesSummaryService = Depends(get_summary_service),
    gating: FeatureGatingService = Depends(get_gating_service),
):
    resolved_child_id, _ = resolve_child_access(current_user, child_id)
    gating.require(resolved_child_id, "hermes_daily_summary")
    summary = service.get_summary(resolved_child_id, date or today_ist(), audience)
    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not generated yet. Call POST /summary/generate first.",
        )
    return summary


# ─── Student insights ────────────────────────────────────────────────────

def _require_student_role(child_id: str, role: str):
    if role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for the student portal",
        )


@router.get(
    "/today",
    response_model=TodayResponse,
    summary="Student home: countdown, targets, streak, plan usage",
)
def get_today(
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesInsightsService = Depends(get_insights_service),
):
    resolved_child_id, role = resolve_child_access(current_user, child_id)
    _require_student_role(resolved_child_id, role)
    return TodayResponse(**service.today(resolved_child_id))


@router.get(
    "/gamification",
    response_model=GamificationState,
    summary="XP, streak, and badges",
)
def get_gamification(
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesGamificationService = Depends(get_gamification_service),
):
    resolved_child_id, role = resolve_child_access(current_user, child_id)
    _require_student_role(resolved_child_id, role)
    return GamificationState(**service.get_state(resolved_child_id))


@router.get(
    "/score-prediction",
    response_model=ScorePrediction,
    summary="JEE marks estimate from mastery (Premium)",
)
def get_score_prediction(
    child_id: Optional[str] = Query(default=None),
    current_user: str = Depends(get_current_user),
    service: HermesInsightsService = Depends(get_insights_service),
    gating: FeatureGatingService = Depends(get_gating_service),
):
    resolved_child_id, role = resolve_child_access(current_user, child_id)
    _require_student_role(resolved_child_id, role)
    gating.require(resolved_child_id, "hermes_score_prediction")
    return ScorePrediction(**service.score_prediction(resolved_child_id))


# ─── Parent insights ─────────────────────────────────────────────────────

def _require_parent_role(role: str):
    if role != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is for the parent portal",
        )


@router.get(
    "/parent/overview",
    response_model=ParentOverview,
    summary="7-day activity, progress, attention flags",
)
def get_parent_overview(
    child_id: str = Query(..., description="Child ID (parent token required)"),
    current_user: str = Depends(get_current_user),
    service: HermesInsightsService = Depends(get_insights_service),
):
    resolved_child_id, role = resolve_child_access(current_user, child_id)
    _require_parent_role(role)
    return ParentOverview(**service.parent_overview(resolved_child_id))


@router.get(
    "/parent/weekly",
    response_model=ParentWeeklyReport,
    summary="Weekly report with per-day breakdown (Premium)",
)
def get_parent_weekly(
    child_id: str = Query(..., description="Child ID (parent token required)"),
    date: Optional[str] = Query(default=None, description="Week-ending date, YYYY-MM-DD"),
    current_user: str = Depends(get_current_user),
    service: HermesInsightsService = Depends(get_insights_service),
    gating: FeatureGatingService = Depends(get_gating_service),
):
    resolved_child_id, role = resolve_child_access(current_user, child_id)
    _require_parent_role(role)
    gating.require(resolved_child_id, "hermes_weekly_report")
    return ParentWeeklyReport(**service.parent_weekly(resolved_child_id, date or today_ist()))
