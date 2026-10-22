"""
Analytics Models for Mentor AI Platform.

This module defines Pydantic models for analytics reports, including requests,
responses, and comprehensive analytics data structures for frontend display.

Models:
- QuestionAnswer: Student answer for a question
- AnalyticsRequest: Request to generate analytics
- AnalyticsOverview: High-level test overview
- SubjectAnalysis: Per-subject analysis with AI insights
- TopicAnalysis: Per-topic analysis with priorities
- AnalyticsInsights: AI-generated insights
- VisualizationData: Chart data for frontend
- ChartData: Generic chart data structure
- PriorityTopic: Priority topic for study plan
- AnalyticsReport: Complete analytics report
- AnalyticsResponse: API response for analytics generation
- AnalyticsStatus: Status enum for analytics generation

Author: Mentor AI Team
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class AnalyticsStatus(str, Enum):
    """Status of analytics generation."""
    PENDING = "pending"           # Analytics generation in progress
    COMPLETED = "completed"       # Analytics generation completed
    FAILED = "failed"             # Analytics generation failed
    CACHED = "cached"             # Analytics retrieved from cache


class ChartType(str, Enum):
    """Types of charts for visualization."""
    PIE = "pie"                   # Pie chart
    BAR = "bar"                   # Bar chart
    LINE = "line"                 # Line chart
    RADAR = "radar"               # Radar chart
    DONUT = "donut"               # Donut chart


class QuestionAnswer(BaseModel):
    """
    Student answer for a single question.
    
    Attributes:
        question_number: Question number (1-indexed)
        answer: Student's answer (can be option letter, number, or text)
        time_taken: Time taken for this question in seconds
    
    Example:
        >>> answer = QuestionAnswer(
        ...     question_number=1,
        ...     answer="B",
        ...     time_taken=120
        ... )
    """
    question_number: int = Field(
        ...,
        gt=0,
        description="Question number (1-indexed)"
    )
    answer: str = Field(
        ...,
        description="Student's answer (option letter, number, or text)"
    )
    time_taken: Optional[int] = Field(
        default=None,
        ge=0,
        description="Time taken for this question in seconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_number": 1,
                "answer": "B",
                "time_taken": 120
            }
        }


class AnalyticsRequest(BaseModel):
    """
    Request to generate analytics report.
    
    Attributes:
        test_id: Unique test identifier
        student_id: Student identifier
        answers: List of student answers or dict mapping question number to answer
        include_ai_insights: Whether to generate AI insights (default: True)
        use_cache: Whether to use cached results if available (default: True)
    
    Example:
        >>> request = AnalyticsRequest(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     answers=[
        ...         QuestionAnswer(question_number=1, answer="B"),
        ...         QuestionAnswer(question_number=2, answer="A")
        ...     ],
        ...     include_ai_insights=True
        ... )
    """
    test_id: str = Field(
        ...,
        min_length=1,
        description="Unique test identifier"
    )
    student_id: str = Field(
        ...,
        min_length=1,
        description="Student identifier"
    )
    answers: Union[List[QuestionAnswer], Dict[int, str]] = Field(
        ...,
        description="Student answers (list of QuestionAnswer or dict {question_number: answer})"
    )
    include_ai_insights: bool = Field(
        default=True,
        description="Whether to generate AI insights"
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached results if available"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "test_123",
                "student_id": "student_456",
                "answers": [
                    {"question_number": 1, "answer": "B", "time_taken": 120},
                    {"question_number": 2, "answer": "A", "time_taken": 90}
                ],
                "include_ai_insights": True,
                "use_cache": True
            }
        }


class AnalyticsOverview(BaseModel):
    """
    High-level analytics overview.
    
    Attributes:
        test_id: Test identifier
        student_id: Student identifier
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        total_score: Total marks obtained
        max_score: Maximum marks possible
        percentage: Overall percentage (0-100)
        percentile: Estimated percentile (0-100)
        accuracy: Overall accuracy (0-100)
        time_taken: Total time taken in seconds
        total_questions: Total number of questions
        attempted: Questions attempted
        correct: Correct answers
        incorrect: Incorrect answers
        unattempted: Unattempted questions
    
    Example:
        >>> overview = AnalyticsOverview(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     exam_type="JEE_MAIN",
        ...     total_score=62,
        ...     max_score=120,
        ...     percentage=51.67,
        ...     percentile=72.5,
        ...     accuracy=64.3
        ... )
    """
    test_id: str = Field(..., description="Test identifier")
    student_id: str = Field(..., description="Student identifier")
    exam_type: str = Field(..., description="Type of exam")
    total_score: int = Field(..., description="Total marks obtained")
    max_score: int = Field(..., gt=0, description="Maximum marks possible")
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall percentage (0-100)"
    )
    percentile: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Estimated percentile (0-100)"
    )
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall accuracy (0-100)"
    )
    time_taken: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total time taken in seconds"
    )
    total_questions: int = Field(..., gt=0, description="Total questions")
    attempted: int = Field(..., ge=0, description="Questions attempted")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    unattempted: int = Field(..., ge=0, description="Unattempted questions")
    
    @field_validator('percentage', 'accuracy')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Percentage must be between 0 and 100, got {v}")
        return round(v, 2)
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "test_123",
                "student_id": "student_456",
                "exam_type": "JEE_MAIN",
                "total_score": 62,
                "max_score": 120,
                "percentage": 51.67,
                "percentile": 72.5,
                "accuracy": 64.3,
                "time_taken": 5400,
                "total_questions": 30,
                "attempted": 28,
                "correct": 18,
                "incorrect": 10,
                "unattempted": 2
            }
        }


class SubjectAnalysis(BaseModel):
    """
    Per-subject analysis with AI insights.
    
    Attributes:
        subject: Subject name
        score: Marks obtained
        max_score: Maximum marks possible
        percentage: Subject percentage (0-100)
        accuracy: Subject accuracy (0-100)
        total_questions: Total questions in subject
        attempted: Questions attempted
        correct: Correct answers
        incorrect: Incorrect answers
        strengths: List of strong topics in this subject
        weaknesses: List of weak topics in this subject
        ai_insights: AI-generated insights for this subject
        top_topics: Top performing topics (max 3)
        weak_topics: Weakest performing topics (max 3)
    
    Example:
        >>> analysis = SubjectAnalysis(
        ...     subject="Physics",
        ...     score=20,
        ...     max_score=40,
        ...     percentage=50.0,
        ...     accuracy=50.0,
        ...     strengths=["Mechanics"],
        ...     weaknesses=["Thermodynamics"]
        ... )
    """
    subject: str = Field(..., description="Subject name")
    score: int = Field(..., description="Marks obtained")
    max_score: int = Field(..., gt=0, description="Maximum marks possible")
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Subject percentage (0-100)"
    )
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Subject accuracy (0-100)"
    )
    total_questions: int = Field(..., gt=0, description="Total questions")
    attempted: int = Field(..., ge=0, description="Questions attempted")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    strengths: List[str] = Field(
        default_factory=list,
        description="List of strong topics"
    )
    weaknesses: List[str] = Field(
        default_factory=list,
        description="List of weak topics"
    )
    ai_insights: Optional[str] = Field(
        default=None,
        description="AI-generated insights for this subject"
    )
    top_topics: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Top performing topics (max 3)"
    )
    weak_topics: List[str] = Field(
        default_factory=list,
        max_length=3,
        description="Weakest performing topics (max 3)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Physics",
                "score": 20,
                "max_score": 40,
                "percentage": 50.0,
                "accuracy": 50.0,
                "total_questions": 10,
                "attempted": 10,
                "correct": 5,
                "incorrect": 5,
                "strengths": ["Mechanics", "Kinematics"],
                "weaknesses": ["Thermodynamics", "Modern Physics"],
                "ai_insights": "Strong conceptual understanding in mechanics, but needs practice in thermodynamics.",
                "top_topics": ["Mechanics", "Kinematics", "Optics"],
                "weak_topics": ["Thermodynamics", "Modern Physics", "Waves"]
            }
        }


class TopicAnalysis(BaseModel):
    """
    Per-topic analysis with priority and recommendations.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        accuracy: Topic accuracy (0-100)
        total_questions: Total questions in topic
        correct: Correct answers
        incorrect: Incorrect answers
        priority: Priority level (HIGH, MEDIUM, LOW)
        estimated_hours: Estimated study hours needed
        recommendation: Specific recommendation for this topic
        performance_level: Performance classification (strong, moderate, weak)
        gap_from_benchmark: Gap from expected benchmark
    
    Example:
        >>> analysis = TopicAnalysis(
        ...     topic="Thermodynamics",
        ...     subject="Physics",
        ...     accuracy=25.0,
        ...     priority="HIGH",
        ...     estimated_hours=12.0,
        ...     recommendation="Review fundamental concepts and practice problems"
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Topic accuracy (0-100)"
    )
    total_questions: int = Field(..., ge=0, description="Total questions")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    priority: str = Field(
        ...,
        description="Priority level (HIGH, MEDIUM, LOW)"
    )
    estimated_hours: float = Field(
        ...,
        ge=0.0,
        description="Estimated study hours needed"
    )
    recommendation: str = Field(
        ...,
        description="Specific recommendation for this topic"
    )
    performance_level: Optional[str] = Field(
        default=None,
        description="Performance classification (strong, moderate, weak)"
    )
    gap_from_benchmark: Optional[float] = Field(
        default=None,
        description="Gap from expected benchmark"
    )
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate and normalize priority level."""
        v_upper = v.upper()
        if v_upper not in ['HIGH', 'MEDIUM', 'LOW']:
            raise ValueError(f"Priority must be HIGH, MEDIUM, or LOW, got {v}")
        return v_upper
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "accuracy": 25.0,
                "total_questions": 8,
                "correct": 2,
                "incorrect": 6,
                "priority": "HIGH",
                "estimated_hours": 12.0,
                "recommendation": "Review fundamental concepts and practice 50+ problems",
                "performance_level": "weak",
                "gap_from_benchmark": -45.0
            }
        }


class AnalyticsInsights(BaseModel):
    """
    AI-generated analytics insights.
    
    Attributes:
        strengths: List of identified strengths with details
        weaknesses: List of identified weaknesses with priorities
        learning_patterns: Detected learning patterns
        overall_assessment: Overall performance assessment
        study_strategy: Recommended study strategy with timeline
    
    Example:
        >>> insights = AnalyticsInsights(
        ...     strengths=[
        ...         {"topic": "Mechanics", "reason": "Consistent high accuracy"}
        ...     ],
        ...     weaknesses=[
        ...         {"topic": "Thermodynamics", "priority": "HIGH", "estimated_hours": 12.0}
        ...     ],
        ...     overall_assessment="Good foundation but needs work on advanced topics"
        ... )
    """
    strengths: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of identified strengths with details"
    )
    weaknesses: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of identified weaknesses with priorities"
    )
    learning_patterns: List[str] = Field(
        default_factory=list,
        description="Detected learning patterns"
    )
    overall_assessment: str = Field(
        default="",
        description="Overall performance assessment (3-4 sentences)"
    )
    study_strategy: str = Field(
        default="",
        description="Recommended study strategy with timeline (4-6 sentences)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "strengths": [
                    {
                        "topic": "Mechanics",
                        "subject": "Physics",
                        "accuracy": 85.5,
                        "reason": "Consistent high accuracy across all question types",
                        "recommendation": "Maintain practice with advanced problems"
                    }
                ],
                "weaknesses": [
                    {
                        "topic": "Thermodynamics",
                        "subject": "Physics",
                        "accuracy": 25.0,
                        "reason": "Weak fundamental understanding of heat transfer concepts",
                        "priority": "HIGH",
                        "estimated_study_hours": 12.0,
                        "recommendation": "Review NCERT chapters, solve 50+ practice problems"
                    }
                ],
                "learning_patterns": [
                    "Strong preference for mechanics-based problems",
                    "Struggles with conceptual questions in thermodynamics"
                ],
                "overall_assessment": "Good foundation in mechanics and mathematics, but significant gaps in thermodynamics and modern physics. Time management is adequate.",
                "study_strategy": "Focus next 2 weeks on thermodynamics fundamentals. Allocate 12 hours for concept review and problem practice. Then move to modern physics."
            }
        }


class ChartData(BaseModel):
    """
    Generic chart data structure.
    
    Attributes:
        chart_type: Type of chart (pie, bar, line, radar, donut)
        labels: Chart labels (x-axis or categories)
        datasets: List of datasets with values and styling
        title: Chart title
        options: Additional chart options
    
    Example:
        >>> chart = ChartData(
        ...     chart_type="pie",
        ...     labels=["Physics", "Chemistry", "Mathematics"],
        ...     datasets=[
        ...         {
        ...             "label": "Score",
        ...             "data": [20, 25, 30],
        ...             "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
        ...         }
        ...     ],
        ...     title="Subject-wise Score Distribution"
        ... )
    """
    chart_type: ChartType = Field(..., description="Type of chart")
    labels: List[str] = Field(..., description="Chart labels")
    datasets: List[Dict[str, Any]] = Field(
        ...,
        description="List of datasets with values and styling"
    )
    title: str = Field(..., description="Chart title")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional chart options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "pie",
                "labels": ["Physics", "Chemistry", "Mathematics"],
                "datasets": [
                    {
                        "label": "Score",
                        "data": [20, 25, 30],
                        "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
                    }
                ],
                "title": "Subject-wise Score Distribution",
                "options": {
                    "responsive": True,
                    "maintainAspectRatio": False
                }
            }
        }


class VisualizationData(BaseModel):
    """
    Chart data for frontend visualization.
    
    Attributes:
        subject_chart: Subject-wise performance chart (pie/donut)
        topic_chart: Topic-wise performance chart (bar)
        difficulty_chart: Difficulty-wise performance chart (bar/line)
        time_chart: Time management chart (line/bar)
        accuracy_chart: Accuracy trends chart (line)
    
    Example:
        >>> viz_data = VisualizationData(
        ...     subject_chart=ChartData(...),
        ...     topic_chart=ChartData(...),
        ...     difficulty_chart=ChartData(...)
        ... )
    """
    subject_chart: Optional[ChartData] = Field(
        default=None,
        description="Subject-wise performance chart (pie/donut)"
    )
    topic_chart: Optional[ChartData] = Field(
        default=None,
        description="Topic-wise performance chart (bar)"
    )
    difficulty_chart: Optional[ChartData] = Field(
        default=None,
        description="Difficulty-wise performance chart (bar/line)"
    )
    time_chart: Optional[ChartData] = Field(
        default=None,
        description="Time management chart (line/bar)"
    )
    accuracy_chart: Optional[ChartData] = Field(
        default=None,
        description="Accuracy trends chart (line)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject_chart": {
                    "chart_type": "pie",
                    "labels": ["Physics", "Chemistry", "Mathematics"],
                    "datasets": [
                        {
                            "label": "Percentage",
                            "data": [50.0, 62.5, 75.0],
                            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
                        }
                    ],
                    "title": "Subject-wise Performance"
                },
                "topic_chart": {
                    "chart_type": "bar",
                    "labels": ["Mechanics", "Thermodynamics", "Optics"],
                    "datasets": [
                        {
                            "label": "Accuracy (%)",
                            "data": [85.5, 25.0, 60.0],
                            "backgroundColor": "#36A2EB"
                        }
                    ],
                    "title": "Topic-wise Accuracy"
                }
            }
        }


class PriorityTopic(BaseModel):
    """
    Priority topic for study plan.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        priority: Priority level (HIGH, MEDIUM, LOW)
        reason: Reason for prioritization
        estimated_hours: Estimated study hours needed
        current_accuracy: Current accuracy percentage
        target_accuracy: Target accuracy percentage
        action_items: List of recommended actions
    
    Example:
        >>> priority = PriorityTopic(
        ...     topic="Thermodynamics",
        ...     subject="Physics",
        ...     priority="HIGH",
        ...     reason="Very low accuracy (25%) with high exam weightage",
        ...     estimated_hours=12.0
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    priority: str = Field(..., description="Priority level (HIGH, MEDIUM, LOW)")
    reason: str = Field(..., description="Reason for prioritization")
    estimated_hours: float = Field(
        ...,
        ge=0.0,
        description="Estimated study hours needed"
    )
    current_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current accuracy percentage"
    )
    target_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Target accuracy percentage"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="List of recommended actions"
    )
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate and normalize priority level."""
        v_upper = v.upper()
        if v_upper not in ['HIGH', 'MEDIUM', 'LOW']:
            raise ValueError(f"Priority must be HIGH, MEDIUM, or LOW, got {v}")
        return v_upper
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "priority": "HIGH",
                "reason": "Very low accuracy (25%) with high exam weightage (15%)",
                "estimated_hours": 12.0,
                "current_accuracy": 25.0,
                "target_accuracy": 70.0,
                "action_items": [
                    "Review NCERT chapters on heat transfer",
                    "Solve 50 practice problems",
                    "Watch video lectures on thermodynamic processes"
                ]
            }
        }


class AnalyticsReport(BaseModel):
    """
    Complete analytics report.
    
    Attributes:
        analytics_id: Unique analytics report identifier
        overview: High-level test overview
        subject_analysis: List of per-subject analyses
        topic_analysis: List of per-topic analyses
        ai_insights: AI-generated insights (optional)
        priority_topics: Priority topics for study plan (top 10)
        visualization_data: Chart data for frontend
        metadata: Additional metadata (generated_at, test_id, student_id, etc.)
        generated_at: Report generation timestamp
    
    Example:
        >>> report = AnalyticsReport(
        ...     analytics_id="analytics_test123_student456_1234567890",
        ...     overview=AnalyticsOverview(...),
        ...     subject_analysis=[SubjectAnalysis(...)],
        ...     topic_analysis=[TopicAnalysis(...)]
        ... )
    """
    analytics_id: Optional[str] = Field(
        default=None,
        description="Unique analytics report identifier"
    )
    overview: AnalyticsOverview = Field(..., description="High-level test overview")
    subject_analysis: List[SubjectAnalysis] = Field(
        ...,
        description="List of per-subject analyses"
    )
    topic_analysis: List[TopicAnalysis] = Field(
        ...,
        description="List of per-topic analyses"
    )
    ai_insights: Optional[AnalyticsInsights] = Field(
        default=None,
        description="AI-generated insights (optional)"
    )
    priority_topics: List[PriorityTopic] = Field(
        default_factory=list,
        max_length=10,
        description="Priority topics for study plan (top 10)"
    )
    visualization_data: Optional[VisualizationData] = Field(
        default=None,
        description="Chart data for frontend"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Report generation timestamp"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "analytics_id": "analytics_test123_student456_1234567890",
                "overview": {
                    "test_id": "test_123",
                    "student_id": "student_456",
                    "exam_type": "JEE_MAIN",
                    "total_score": 62,
                    "max_score": 120,
                    "percentage": 51.67,
                    "percentile": 72.5,
                    "accuracy": 64.3,
                    "total_questions": 30,
                    "attempted": 28,
                    "correct": 18,
                    "incorrect": 10,
                    "unattempted": 2
                },
                "subject_analysis": [],
                "topic_analysis": [],
                "priority_topics": [],
                "metadata": {
                    "test_id": "test_123",
                    "student_id": "student_456",
                    "generated_at": "2024-01-15T10:30:00Z",
                    "ai_insights_included": True
                }
            }
        }


class AnalyticsResponse(BaseModel):
    """
    API response for analytics generation.
    
    Attributes:
        analytics_id: Unique analytics report identifier
        status: Status of analytics generation
        message: Status message
        report: Complete analytics report (only when status=COMPLETED)
        error: Error details (only when status=FAILED)
        progress: Progress information (only when status=PENDING)
    
    Example:
        >>> response = AnalyticsResponse(
        ...     analytics_id="analytics_test123_student456_1234567890",
        ...     status="COMPLETED",
        ...     message="Analytics generated successfully"
        ... )
    """
    analytics_id: str = Field(..., description="Unique analytics report identifier")
    status: AnalyticsStatus = Field(..., description="Status of analytics generation")
    message: str = Field(..., description="Status message")
    report: Optional[AnalyticsReport] = Field(
        default=None,
        description="Complete analytics report (only when status=COMPLETED)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error details (only when status=FAILED)"
    )
    progress: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Progress information (only when status=PENDING)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "analytics_id": "analytics_test123_student456_1234567890",
                "status": "COMPLETED",
                "message": "Analytics generated successfully",
                "report": None
            }
        }
