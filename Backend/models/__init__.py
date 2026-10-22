"""
Models package for Mentor AI Platform.

This package contains all Pydantic models for the application.
"""

# Analytics Models
from models.analytics_models import (
    AnalyticsStatus,
    ChartType,
    QuestionAnswer,
    AnalyticsRequest,
    AnalyticsOverview,
    SubjectAnalysis,
    TopicAnalysis,
    AnalyticsInsights,
    ChartData,
    VisualizationData,
    PriorityTopic,
    AnalyticsReport,
    AnalyticsResponse
)

# Score Models
from models.score_models import (
    MarkingScheme,
    QuestionScore,
    TopicScore,
    SubjectScore,
    TestScore
)

# Performance Models
from models.performance_models import (
    PerformanceLevel,
    PriorityLevel,
    DifficultyLevel,
    PatternType,
    TopicPerformance,
    StrengthArea,
    WeaknessArea,
    DifficultyPerformance,
    QuestionTypePerformance,
    TimeManagementAnalysis,
    LearningPattern,
    TopicRecommendation,
    PerformanceAnalysis
)

# Diagnostic Test Models
from models.diagnostic_test_models import (
    Question,
    DiagnosticTest,
    QuestionType,
    ExamType
)

__all__ = [
    # Analytics Models
    "AnalyticsStatus",
    "ChartType",
    "QuestionAnswer",
    "AnalyticsRequest",
    "AnalyticsOverview",
    "SubjectAnalysis",
    "TopicAnalysis",
    "AnalyticsInsights",
    "ChartData",
    "VisualizationData",
    "PriorityTopic",
    "AnalyticsReport",
    "AnalyticsResponse",
    
    # Score Models
    "MarkingScheme",
    "QuestionScore",
    "TopicScore",
    "SubjectScore",
    "TestScore",
    
    # Performance Models
    "PerformanceLevel",
    "PriorityLevel",
    "DifficultyLevel",
    "PatternType",
    "TopicPerformance",
    "StrengthArea",
    "WeaknessArea",
    "DifficultyPerformance",
    "QuestionTypePerformance",
    "TimeManagementAnalysis",
    "LearningPattern",
    "TopicRecommendation",
    "PerformanceAnalysis",
    
    # Diagnostic Test Models
    "Question",
    "DiagnosticTest",
    "QuestionType",
    "ExamType"
]
