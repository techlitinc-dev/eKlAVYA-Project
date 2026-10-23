"""
MARKS Ecosystem Router

Exposes production endpoints inspired by the reverse-engineered MARKS application:
- Domain 2: Chapter-wise PYQ Bank (CPYQB) & Single-Question Practice Mode
- Domain 3: Multi-Step Custom Test Generator (CTG) & Examination Report Card
- Domain 4: Revision Flash Cards (RFC) & Formula Cards
- Domain 5: Smart Notebooks, Bookmarking & Automated Error Notebook
- Domain 8: Teacher / Parent Homework Assignments & Classroom Analytics
- Domain 9: Daily Goals, Monthly Activity Heatmap, Daily Dose & Weekly Leagues
- Domain 10: Medical / NEET NCERT Line-by-Line Modules & Revision Zones

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, Query, status

from models.marks_sathee_models import (
    AssignmentClassroomAnalytics,
    AssignmentSubmitRequest,
    BookmarkToNotebookRequest,
    CTGGeneratedTestResponse,
    CTGGenerateRequest,
    CTGStep1Response,
    CTGStep2Request,
    CTGStep2Response,
    CTGSubmitRequest,
    CTGSubmitResponse,
    CreateAssignmentRequest,
    CreateAssignmentResponse,
    CreateNotebookRequest,
    DailyDoseSubmitRequest,
    ErrorNotebookListResponse,
    FlashCardDeckResponse,
    FlashCardMasteryRequest,
    LeaderboardLeaguesResponse,
    MonthlyHeatmapResponse,
    NcertModuleListResponse,
    NotebookItem,
    PYQQuestionListResponse,
    PracticeAttemptRequest,
    PracticeAttemptResponse,
    UpdateDailyGoalRequest,
    UpdateNotebookRequest,
)
from services.cpyqb_ctg_service import CPYQBAndCTGService
from services.rfc_notebook_assignment_service import MarksEcosystemService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["MARKS Competitive Ecosystem"])

_ecosystem_service: Optional[MarksEcosystemService] = None
_cpyqb_service: Optional[CPYQBAndCTGService] = None


def get_ecosystem_service() -> MarksEcosystemService:
    global _ecosystem_service
    if _ecosystem_service is None:
        _ecosystem_service = MarksEcosystemService()
    return _ecosystem_service


def get_cpyqb_service() -> CPYQBAndCTGService:
    global _cpyqb_service
    if _cpyqb_service is None:
        eco = get_ecosystem_service()
        _cpyqb_service = CPYQBAndCTGService(
            error_recorder=eco.record_error,
            heatmap_recorder=eco.record_daily_questions_solved,
        )
    return _cpyqb_service


async def resolve_acting_user(
    student_id: Optional[str] = Query(default=None, description="Optional student ID"),
    authorization: Optional[str] = Header(default=None),
) -> str:
    """
    Resolve acting student/user ID from explicit query parameter, JWT Bearer token,
    or fallback test user for development convenience.
    """
    if student_id:
        return student_id
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        try:
            from services import token_service
            payload = token_service.verify_token(token)
            uid = payload.get("sub") or payload.get("user_id") or payload.get("student_id")
            if uid:
                return str(uid)
        except Exception:
            if token and len(token) < 64:
                return token
    return "student_default_01"


# ─── Domain 2: Chapter-wise PYQ Bank (CPYQB) & Practice Mode ─────────────

@router.get(
    "/cpyqb/exam/{exam_id}/subject/{subject_id}/chapter/{chapter_id}/topic/{topic_id}/questions",
    response_model=PYQQuestionListResponse,
    summary="Get Chapter & Topic PYQ Questions",
)
async def get_topic_pyq_questions(
    exam_id: str,
    subject_id: str,
    chapter_id: str,
    topic_id: str,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    pyqFilter: str = Query(
        default="all",
        description="all | unattempted | incorrect | correct | starred",
    ),
    years: Optional[str] = Query(default=None, description="Comma-separated years, e.g. 2024,2023"),
    qType: Optional[str] = Query(default=None, description="MCQ or NAT"),
    difficulty: Optional[str] = Query(default=None, description="easy | medium | hard"),
    revisionZone: Optional[str] = Query(
        default=None, description="high_yield | must_revise | trap_zone"
    ),
    user_id: str = Depends(resolve_acting_user),
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> PYQQuestionListResponse:
    return service.list_questions(
        student_id=user_id,
        exam_id=exam_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        topic_id=topic_id,
        pyq_filter=pyqFilter,
        years=years,
        q_type=qType,
        difficulty=difficulty,
        revision_zone=revisionZone,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/cpyqb/questions",
    response_model=PYQQuestionListResponse,
    summary="Filter PYQ Repository Across Exams, Subjects, Chapters & Zones",
)
async def filter_pyq_questions(
    examId: Optional[str] = Query(default=None),
    subjectId: Optional[str] = Query(default=None),
    chapterId: Optional[str] = Query(default=None),
    topicId: Optional[str] = Query(default=None),
    pyqFilter: str = Query(default="all"),
    years: Optional[str] = Query(default=None),
    qType: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    revisionZone: Optional[str] = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(resolve_acting_user),
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> PYQQuestionListResponse:
    return service.list_questions(
        student_id=user_id,
        exam_id=examId,
        subject_id=subjectId,
        chapter_id=chapterId,
        topic_id=topicId,
        pyq_filter=pyqFilter,
        years=years,
        q_type=qType,
        difficulty=difficulty,
        revision_zone=revisionZone,
        offset=offset,
        limit=limit,
    )


@router.post(
    "/solving-modes/practice/start",
    response_model=PracticeAttemptResponse,
    summary="Submit Single-Question Practice Attempt",
    description="Verifies MCQ/NAT answer immediately, awards points, updates heatmap, and logs mistakes to Error Notebook.",
)
async def submit_practice_question(
    request: PracticeAttemptRequest,
    user_id: str = Depends(resolve_acting_user),
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> PracticeAttemptResponse:
    return service.submit_practice_attempt(student_id=user_id, request=request)


# ─── Domain 3: Custom Test Generator (CTG) ───────────────────────────────

@router.get(
    "/custom-test/build/step1",
    response_model=CTGStep1Response,
    summary="CTG Step 1: Fetch Available Exams & Subjects",
)
async def get_ctg_step1(
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> CTGStep1Response:
    return service.get_ctg_step1()


@router.post(
    "/custom-test/build/step2",
    response_model=CTGStep2Response,
    summary="CTG Step 2: Fetch Chapters & Suggested Durations for Selected Subjects",
)
async def get_ctg_step2(
    request: CTGStep2Request,
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> CTGStep2Response:
    return service.get_ctg_step2(request)


@router.post(
    "/custom-test/generate",
    response_model=CTGGeneratedTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Synthesize Timed CBT Custom Test",
)
async def generate_custom_test(
    request: CTGGenerateRequest,
    user_id: str = Depends(resolve_acting_user),
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> CTGGeneratedTestResponse:
    return service.generate_custom_test(student_id=user_id, request=request)


@router.post(
    "/custom-test/submit",
    response_model=CTGSubmitResponse,
    summary="Submit Custom Test Attempt & Grade CBT Responses",
)
async def submit_custom_test(
    request: CTGSubmitRequest,
    user_id: str = Depends(resolve_acting_user),
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> CTGSubmitResponse:
    return service.submit_custom_test(student_id=user_id, request=request)


@router.get(
    "/custom-test/analysis/{test_id}",
    summary="Get Custom Test Diagnostic Report Card & Topper Comparison",
)
async def get_custom_test_analysis(
    test_id: str,
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> Dict[str, Any]:
    return service.get_custom_test_analysis(test_id)


# ─── Domain 4: Revision Flash Cards (RFC) & Formula Cards ────────────────

@router.get(
    "/rfc/subject/{subject_id}/chapter/{chapter_id}/cards",
    response_model=FlashCardDeckResponse,
    summary="Fetch Revision Flash Cards & Formula Deck for Chapter",
)
async def get_chapter_flashcards(
    subject_id: str,
    chapter_id: str,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> FlashCardDeckResponse:
    return service.get_chapter_cards(
        student_id=user_id, subject_id=subject_id, chapter_id=chapter_id
    )


@router.get(
    "/rfc/subject/{subject_id}/chapter/{chapter_id}/card/{card_id}",
    summary="Fetch Single Revision Flash Card Details",
)
async def get_single_flashcard(
    subject_id: str,
    chapter_id: str,
    card_id: str,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.get_single_card(
        student_id=user_id,
        subject_id=subject_id,
        chapter_id=chapter_id,
        card_id=card_id,
    )


@router.post(
    "/rfc/mastery",
    summary="Update Revision Flash Card Mastery Level",
)
async def update_flashcard_mastery(
    request: FlashCardMasteryRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.update_card_mastery(student_id=user_id, request=request)


# ─── Domain 5: Smart Notebooks, Bookmarking & Error Notebook ─────────────

@router.post(
    "/notebook",
    response_model=NotebookItem,
    status_code=status.HTTP_201_CREATED,
    summary="Create Custom Smart Notebook",
)
async def create_notebook(
    request: CreateNotebookRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> NotebookItem:
    return service.create_notebook(student_id=user_id, request=request)


@router.get(
    "/notebook/smart",
    response_model=List[NotebookItem],
    summary="List Student's Smart Notebooks",
)
async def list_notebooks(
    includeArchived: bool = Query(default=False),
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> List[NotebookItem]:
    return service.list_notebooks(student_id=user_id, include_archived=includeArchived)


@router.patch(
    "/notebook/{notebook_id}",
    response_model=NotebookItem,
    summary="Pin, Archive, or Rename Smart Notebook",
)
async def update_notebook(
    notebook_id: str,
    request: UpdateNotebookRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> NotebookItem:
    return service.update_notebook(
        student_id=user_id, notebook_id=notebook_id, request=request
    )


@router.post(
    "/notebook/question",
    summary="Bookmark Question into Smart Notebooks with Personal Note",
)
async def bookmark_question_to_notebook(
    request: BookmarkToNotebookRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.bookmark_question(student_id=user_id, request=request)


@router.get(
    "/notebook/{notebook_id}/questions",
    summary="Get All Bookmarked Questions in a Smart Notebook",
)
async def get_notebook_questions(
    notebook_id: str,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.get_notebook_questions(
        student_id=user_id, notebook_id=notebook_id
    )


@router.get(
    "/notebook/errors",
    response_model=ErrorNotebookListResponse,
    summary="Fetch Automated Error Notebook",
    description="Retrieves historical mistakes aggregated across Practice Mode, Custom Tests, and Assignments.",
)
async def get_error_notebook(
    subject: Optional[str] = Query(default=None),
    status_filter: str = Query(
        default="unresolved", alias="status", description="unresolved | mastered | all"
    ),
    mistakeType: Optional[str] = Query(
        default=None, description="formula_mixup | calculation | conceptual | silly"
    ),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> ErrorNotebookListResponse:
    return service.get_error_notebook(
        student_id=user_id,
        subject=subject,
        status_filter=status_filter,
        mistake_type=mistakeType,
        page=page,
        limit=limit,
    )


@router.post(
    "/notebook/errors/{error_id}/resolve",
    summary="Mark Error Notebook Mistake as Mastered",
)
async def resolve_error_notebook_entry(
    error_id: str,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.resolve_error(student_id=user_id, error_id=error_id)


# ─── Domain 8: Teacher & Student Homework Assignments ────────────────────

@router.post(
    "/assignment/teacher/create",
    response_model=CreateAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Teacher/Parent Homework Assignment with Shareable Join Code",
)
async def create_teacher_assignment(
    request: CreateAssignmentRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> CreateAssignmentResponse:
    return service.create_assignment(creator_id=user_id, request=request)


@router.get(
    "/assignment/student/id/{identifier}",
    summary="Fetch Assignment Details by Assignment ID or 6-Character Join Code",
)
async def get_student_assignment(
    identifier: str,
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.get_assignment(identifier)


@router.post(
    "/assignment/student/id/{identifier}/submit",
    summary="Submit Student Assignment Attempt",
)
async def submit_student_assignment(
    identifier: str,
    request: AssignmentSubmitRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.submit_assignment(
        student_id=user_id, assignment_id=identifier, request=request
    )


@router.get(
    "/assignment/student/id/{identifier}/analysis",
    response_model=AssignmentClassroomAnalytics,
    summary="Get Classroom Performance Analytics & Question Error Rates",
)
async def get_assignment_analytics(
    identifier: str,
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> AssignmentClassroomAnalytics:
    return service.get_assignment_analytics(identifier)


# ─── Domain 9: Daily Goals, Heatmaps, Daily Dose & Weekly Leagues ────────

@router.post(
    "/targets/update",
    summary="Configure Daily Question Target",
)
async def update_daily_target(
    request: UpdateDailyGoalRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.update_daily_goal(
        student_id=user_id, daily_target=request.dailyTargetQuestions
    )


@router.get(
    "/targets/heatmap",
    response_model=MonthlyHeatmapResponse,
    summary="Fetch GitHub-Style Monthly Question Solving Heatmap",
)
async def get_targets_heatmap(
    month: Optional[str] = Query(default=None, description="Month in YYYY-MM format"),
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> MonthlyHeatmapResponse:
    return service.get_monthly_heatmap(student_id=user_id, month=month)


@router.get(
    "/targets/daily-dose",
    summary="Fetch Daily Dose 5-Question Sprint Challenge",
)
async def get_daily_dose(
    examId: str = Query(default="jee_main"),
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.get_daily_dose(student_id=user_id, exam_id=examId)


@router.post(
    "/targets/daily-dose/submit",
    summary="Submit Daily Dose 5-Question Sprint & Claim Streak Bonus",
)
async def submit_daily_dose(
    request: DailyDoseSubmitRequest,
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> Dict[str, Any]:
    return service.submit_daily_dose(student_id=user_id, request=request)


@router.get(
    "/leaderboard/achievements",
    response_model=LeaderboardLeaguesResponse,
    summary="Fetch Weekly League Standings (Bronze to Master)",
)
async def get_leaderboard_leagues(
    user_id: str = Depends(resolve_acting_user),
    service: MarksEcosystemService = Depends(get_ecosystem_service),
) -> LeaderboardLeaguesResponse:
    return service.get_leaderboard_leagues(student_id=user_id)


# ─── Domain 10: Medical / NEET Ecosystem ─────────────────────────────────

@router.get(
    "/neet/ncert/subject/{subject_id}/modules",
    response_model=NcertModuleListResponse,
    summary="Fetch NEET NCERT Line-by-Line Modules & Revision Zones",
)
async def get_ncert_modules(
    subject_id: str,
    user_id: str = Depends(resolve_acting_user),
    service: CPYQBAndCTGService = Depends(get_cpyqb_service),
) -> NcertModuleListResponse:
    return service.get_ncert_modules(student_id=user_id, subject_id=subject_id)
