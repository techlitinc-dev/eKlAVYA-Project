"""
MARKS & SATHEE Platform Models

Pydantic data contracts for:
1. Chapter-wise PYQ Bank (CPYQB) & Single-Question Practice Mode
2. Multi-Step Custom Test Generator (CTG) & CBT Report Card
3. Revision Flash Cards (RFC) & Formula Cards
4. Smart Notebooks, Bookmarking & Automated Error Notebook
5. Teacher / Parent Homework Assignments & Classroom Analytics
6. Daily Goals, Monthly Activity Heatmaps, Daily Dose 5-Q Sprint & Weekly Leagues
7. NEET NCERT Line-by-Line Modules & Revision Zones
8. AI Hub: Vision OCR, SSE Streaming Doubt Solver, Similar Question Generator,
   Physical OMR Sheet Grader, AI Rank & Percentile Predictor, College Cutoffs

Author: Mentor AI Team
Version: 1.0.0
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── 1. Chapter-wise PYQ Bank (CPYQB) & Practice Mode ─────────────────────

class PYQOption(BaseModel):
    key: str
    html: str


class UserAttemptState(BaseModel):
    status: str = Field(default="unattempted", description="unattempted | correct | incorrect")
    selectedOption: Optional[str] = None
    numericalAnswer: Optional[float] = None
    isStarred: bool = False


class PYQQuestionItem(BaseModel):
    id: str
    questionNumber: int
    examId: str
    exam: str
    subjectId: str
    subject: str
    chapterId: str
    chapter: str
    topicId: str
    topic: str
    year: int
    shift: str
    type: str = Field(..., description="MCQ or NAT")
    difficulty: str = Field(default="medium", description="easy | medium | hard")
    revisionZone: str = Field(default="high_yield", description="high_yield | must_revise | trap_zone")
    ncertPages: Optional[str] = None
    statementHtml: str
    options: List[PYQOption] = Field(default_factory=list)
    hasVideoSolution: bool = False
    videoContentId: Optional[str] = None
    userAttempt: UserAttemptState = Field(default_factory=UserAttemptState)


class PYQQuestionListResponse(BaseModel):
    status: bool = True
    code: int = 200
    message: str = "Questions loaded"
    totalCount: int
    questions: List[PYQQuestionItem]


class PracticeAttemptRequest(BaseModel):
    questionId: str = Field(..., min_length=1)
    selectedOption: Optional[str] = Field(default=None, description="Option key (A, B, C, D) for MCQ")
    numericalAnswer: Optional[float] = Field(default=None, description="Decimal/integer value for NAT")
    timeSpentSeconds: int = Field(default=30, ge=0)
    mistakeTag: Optional[str] = Field(
        default=None,
        description="Optional override: formula_mixup | calculation | conceptual | silly",
    )


class PracticeAttemptResponse(BaseModel):
    status: bool = True
    code: int = 200
    message: str = "Answer verified"
    questionId: str
    isCorrect: bool
    correctOption: Optional[str] = None
    correctNumericalAnswer: Optional[float] = None
    marksAwarded: int
    solutionHtml: str
    userPointsEarned: int
    loggedToErrorNotebook: bool = False
    errorId: Optional[str] = None


# ─── 2. Custom Test Generator (CTG) ──────────────────────────────────────

class CTGSubjectSummary(BaseModel):
    id: str
    name: str
    availableQuestions: int


class CTGExamSummary(BaseModel):
    id: str
    name: str
    subjects: List[CTGSubjectSummary]


class CTGStep1Response(BaseModel):
    status: bool = True
    code: int = 200
    exams: List[CTGExamSummary]


class CTGStep2Request(BaseModel):
    examId: str = Field(default="jee_main")
    subjectIds: List[str] = Field(..., min_length=1)


class CTGChapterInfo(BaseModel):
    id: str
    name: str
    subject: str
    totalQuestions: int


class CTGStep2Response(BaseModel):
    status: bool = True
    code: int = 200
    chapters: List[CTGChapterInfo]
    suggestedTimeDurations: List[int] = Field(default_factory=lambda: [30, 45, 60, 90, 180])


class CTGChapterAllocation(BaseModel):
    chapterId: str
    questionCount: int = Field(default=5, ge=1, le=50)


class CTGGenerateRequest(BaseModel):
    examId: str = Field(default="jee_main")
    title: Optional[str] = None
    subjectIds: List[str] = Field(..., min_length=1)
    chapterAllocations: List[CTGChapterAllocation] = Field(default_factory=list)
    durationMinutes: int = Field(default=60, ge=10, le=240)
    difficulty: Optional[str] = Field(default=None, description="easy | medium | hard | mixed")


class CTGGeneratedTestResponse(BaseModel):
    status: bool = True
    code: int = 200
    message: str = "Custom test synthesized"
    testId: str
    title: str
    examId: str
    durationMinutes: int
    totalQuestions: int
    totalMarks: int
    questions: List[PYQQuestionItem]


class CTGQuestionResponseItem(BaseModel):
    questionId: str
    selectedOption: Optional[str] = None
    numericalValue: Optional[float] = None
    status: str = Field(default="answered", description="answered | marked_for_review | unattempted")
    timeTaken: int = Field(default=60, ge=0)


class CTGSubmitRequest(BaseModel):
    testId: str
    timeTakenSeconds: int = Field(..., ge=0)
    responses: List[CTGQuestionResponseItem]


class CTGSubmitResponse(BaseModel):
    status: bool = True
    code: int = 200
    message: str = "Custom test graded"
    attemptId: str
    testId: str
    totalMarks: int
    score: int
    totalQuestions: int
    attempted: int
    correct: int
    incorrect: int
    unattempted: int
    accuracy: float
    percentile: float
    subjectBreakdown: Dict[str, Dict[str, Any]]
    weakTopics: List[Dict[str, Any]]
    strongTopics: List[Dict[str, Any]]


# ─── 3. Revision Flash Cards (RFC) & Formula Cards ───────────────────────

class FlashCardItem(BaseModel):
    cardId: str
    subjectId: str
    chapterId: str
    chapterName: str
    topicName: str
    title: str
    frontText: str
    backFormulaHtml: str
    keyTakeaways: List[str]
    userMasteryLevel: str = Field(default="unseen", description="unseen | needs_revision | mastered")


class FlashCardDeckResponse(BaseModel):
    status: bool = True
    code: int = 200
    subjectId: str
    chapterId: str
    totalCards: int
    masteredCount: int
    needsRevisionCount: int
    cards: List[FlashCardItem]


class FlashCardMasteryRequest(BaseModel):
    cardId: str
    masteryLevel: str = Field(..., pattern="^(mastered|needs_revision)$")


# ─── 4. Smart Notebooks & Error Notebook ─────────────────────────────────

class CreateNotebookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    colorHex: str = Field(default="#1589EE")
    subjectId: Optional[str] = None


class UpdateNotebookRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    colorHex: Optional[str] = None
    isPinned: Optional[bool] = None
    isArchived: Optional[bool] = None


class NotebookItem(BaseModel):
    notebookId: str
    title: str
    colorHex: str
    subjectId: Optional[str] = None
    questionCount: int = 0
    isPinned: bool = False
    isArchived: bool = False
    createdAt: str


class BookmarkToNotebookRequest(BaseModel):
    questionId: str
    notebookIds: List[str] = Field(..., min_length=1)
    studentNote: Optional[str] = None


class ErrorNotebookEntry(BaseModel):
    errorId: str
    questionId: str
    testName: str
    subject: str
    chapter: str
    topic: str
    questionText: str
    studentSelectedOption: Optional[str] = None
    correctOption: Optional[str] = None
    solutionText: str
    mistakeType: str = Field(default="conceptual", description="formula_mixup | calculation | conceptual | silly")
    attemptCount: int = 1
    isMastered: bool = False
    createdAt: str


class ErrorNotebookListResponse(BaseModel):
    success: bool = True
    status: int = 200
    totalCount: int
    page: int
    items: List[ErrorNotebookEntry]


# ─── 5. Teacher / Parent Homework Assignments ────────────────────────────

class CreateAssignmentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    subjectId: str
    questionIds: List[str] = Field(..., min_length=1)
    dueDate: str
    timeLimitMinutes: int = Field(default=45, ge=5, le=240)


class CreateAssignmentResponse(BaseModel):
    status: bool = True
    code: int = 200
    message: str = "Assignment created"
    assignmentId: str
    joinCode: str
    shareUrl: str
    title: str
    questionCount: int
    timeLimitMinutes: int
    dueDate: str


class AssignmentSubmitRequest(BaseModel):
    timeTakenSeconds: int = Field(..., ge=0)
    responses: List[CTGQuestionResponseItem]


class AssignmentClassroomAnalytics(BaseModel):
    status: bool = True
    code: int = 200
    assignmentId: str
    title: str
    joinCode: str
    totalSubmissions: int
    averageScore: float
    highestScore: int
    averageTimeSeconds: float
    questionErrorRates: List[Dict[str, Any]]
    leaderboard: List[Dict[str, Any]]


# ─── 6. Daily Goals, Monthly Heatmap, Daily Dose & Leagues ───────────────

class UpdateDailyGoalRequest(BaseModel):
    dailyTargetQuestions: int = Field(..., ge=5, le=200)


class HeatmapDayItem(BaseModel):
    date: str
    solvedCount: int
    targetMet: bool


class MonthlyHeatmapResponse(BaseModel):
    status: bool = True
    code: int = 200
    month: str
    dailyTargetQuestions: int
    days: List[HeatmapDayItem]
    longestStreak: int
    currentStreak: int
    totalSolvedInMonth: int


class DailyDoseSubmitRequest(BaseModel):
    date: Optional[str] = None
    responses: List[CTGQuestionResponseItem]


class LeaderboardLeaguesResponse(BaseModel):
    status: bool = True
    code: int = 200
    currentLeague: str = Field(..., description="Bronze | Silver | Gold | Diamond | Master")
    userRank: int
    totalCompetitors: int
    weeklyPoints: int
    nextLeagueThreshold: Optional[int] = None
    topRankers: List[Dict[str, Any]]


# ─── 7. NEET NCERT Line-by-Line Modules ──────────────────────────────────

class NcertModuleItem(BaseModel):
    moduleId: str
    subjectId: str
    book: str
    chapterId: str
    chapterName: str
    ncertPages: str
    totalQuestions: int
    completedQuestions: int
    highYieldCount: int
    mustReviseCount: int
    trapZoneCount: int


class NcertModuleListResponse(BaseModel):
    status: bool = True
    code: int = 200
    subjectId: str
    modules: List[NcertModuleItem]


# ─── 8. AI Hub & Admissions (SATHEE / Mentor AI) ─────────────────────────

class OCRResponse(BaseModel):
    success: bool = True
    status: int = 200
    message: str = "OCR text extraction completed."
    ocrText: str
    confidence: float
    hasEquations: bool
    detectedSubject: str
    boundingBoxes: List[Dict[str, Any]]


class StreamingDoubtRequest(BaseModel):
    query: str = Field(..., min_length=1)
    subject: str = Field(default="Physics")
    exam: str = Field(default="jee")
    language: str = Field(default="en")
    conversationId: Optional[str] = None
    mode: str = Field(default="step_by_step", description="step_by_step | socratic_hint")


class GenerateSimilarQuestionsRequest(BaseModel):
    questionText: str = Field(..., min_length=5)
    subject: str = Field(default="Physics")
    topic: str = Field(default="Mechanics")
    difficulty: str = Field(default="medium")
    count: int = Field(default=3, ge=1, le=5)


class GeneratedSimilarQuestion(BaseModel):
    id: str
    questionText: str
    options: List[Dict[str, str]]
    correctOption: str
    explanation: str


class GenerateSimilarQuestionsResponse(BaseModel):
    success: bool = True
    status: int = 200
    message: str = "Similar questions generated successfully."
    questions: List[GeneratedSimilarQuestion]


class RankPredictRequest(BaseModel):
    exam: str = Field(default="jee_main", description="jee_main | jee_advanced | neet")
    rawMarks: float = Field(..., ge=-75, le=720)
    maxMarks: float = Field(default=300, gt=0)
    category: str = Field(default="General", description="General | OBC-NCL | SC | ST | EWS")
    state: Optional[str] = Field(default="Maharashtra")
    shiftDifficulty: str = Field(default="moderate", description="easy | moderate | tough")
    session: str = Field(default="session_1")


class RankPredictResponse(BaseModel):
    success: bool = True
    status: int = 200
    message: str = "Rank prediction successful."
    exam: str
    predictedPercentile: float
    predictedAIR: int
    airRange: Dict[str, int]
    category: str
    categoryRank: int
    confidenceScore: float
    historicalTrend: List[Dict[str, Any]]


class OMREvaluateResponse(BaseModel):
    success: bool = True
    status: int = 200
    message: str = "OMR processed successfully."
    templateId: str
    detectedRollNumber: str
    confidenceScore: float
    totalBubblesDetected: int
    totalAttempted: int
    correctCount: int
    incorrectCount: int
    marksCalculated: int
    maxMarks: int
    scannedAnswers: Dict[str, str]
