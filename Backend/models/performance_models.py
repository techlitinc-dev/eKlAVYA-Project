"""
Performance Analysis Models for Diagnostic Test System - Mentor AI Platform.

This module defines Pydantic models for performance analysis, including strength/weakness
identification, learning patterns, and personalized recommendations.

Models:
- PerformanceLevel: Enum for performance classification
- PriorityLevel: Enum for topic priority (HIGH, MEDIUM, LOW)
- DifficultyLevel: Enum for difficulty levels
- PatternType: Enum for learning pattern types (TIME_MANAGEMENT, DIFFICULTY_PREFERENCE, etc.)
- TopicPerformance: Performance details for a single topic
- StrengthArea: Identified strength with reason and recommendation
- WeaknessArea: Identified weakness with priority and study hours estimate
- DifficultyPerformance: Performance by difficulty level
- QuestionTypePerformance: Performance by question type
- TimeManagementAnalysis: Time management insights
- LearningPattern: Detected learning patterns with impact analysis
- TopicRecommendation: Personalized topic recommendations
- PerformanceAnalysis: Complete performance analysis report

Author: Mentor AI Team
Version: 2.0.0
"""

from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


class PerformanceLevel(str, Enum):
    """Performance classification levels."""
    STRONG = "strong"           # Accuracy > 80%
    MODERATE = "moderate"       # Accuracy 40-80%
    WEAK = "weak"              # Accuracy < 40%
    INSUFFICIENT = "insufficient"  # Not enough data


class PriorityLevel(str, Enum):
    """Priority levels for topic improvement."""
    HIGH = "high"       # Weak topics that need immediate attention
    MEDIUM = "medium"   # Moderate topics that need improvement
    LOW = "low"         # Strong topics for maintenance


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PatternType(str, Enum):
    """Learning pattern types."""
    TIME_MANAGEMENT = "time_management"           # Time usage patterns
    DIFFICULTY_PREFERENCE = "difficulty_preference"  # Preference for certain difficulty levels
    QUESTION_TYPE = "question_type"               # Question type preferences
    CONCEPTUAL_GAP = "conceptual_gap"             # Gaps in conceptual understanding


class TopicPerformance(BaseModel):
    """
    Performance analysis for a single topic.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        performance_level: Performance classification
        priority_level: Priority for improvement
        total_questions: Total questions attempted
        correct: Correct answers
        incorrect: Incorrect answers
        accuracy: Accuracy percentage
        marks_obtained: Marks obtained
        max_marks: Maximum possible marks
        average_time_per_question: Average time per question (seconds)
        benchmark_accuracy: Expected benchmark accuracy
        gap_from_benchmark: Gap from benchmark (positive means above)
    
    Example:
        >>> perf = TopicPerformance(
        ...     topic="Mechanics",
        ...     subject="Physics",
        ...     performance_level="moderate",
        ...     priority_level="medium",
        ...     total_questions=10,
        ...     correct=6,
        ...     incorrect=4,
        ...     accuracy=60.0,
        ...     marks_obtained=20,
        ...     max_marks=40
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    performance_level: PerformanceLevel = Field(
        ...,
        description="Performance classification"
    )
    priority_level: PriorityLevel = Field(
        ...,
        description="Priority for improvement"
    )
    total_questions: int = Field(..., ge=0, description="Total questions")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage (0-100)"
    )
    marks_obtained: int = Field(..., description="Marks obtained")
    max_marks: int = Field(..., gt=0, description="Maximum marks")
    time_spent: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total time spent on topic in seconds"
    )
    average_time_per_question: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Average time per question in seconds"
    )
    weightage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Topic weightage in exam (%)"
    )
    benchmark_accuracy: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Expected benchmark accuracy"
    )
    gap_from_benchmark: float = Field(
        default=0.0,
        description="Gap from benchmark (positive = above benchmark)"
    )
    
    @field_validator('accuracy')
    @classmethod
    def validate_accuracy(cls, v: float) -> float:
        """Validate accuracy is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Accuracy must be between 0 and 100, got {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Mechanics",
                "subject": "Physics",
                "performance_level": "moderate",
                "priority_level": "medium",
                "total_questions": 10,
                "correct": 6,
                "incorrect": 4,
                "accuracy": 60.0,
                "marks_obtained": 20,
                "max_marks": 40,
                "time_spent": 1080,
                "average_time_per_question": 180.0,
                "weightage": 15.0,
                "benchmark_accuracy": 70.0,
                "gap_from_benchmark": -10.0
            }
        }


class DifficultyPerformance(BaseModel):
    """
    Performance analysis by difficulty level.
    
    Attributes:
        difficulty: Difficulty level
        total_questions: Total questions
        correct: Correct answers
        incorrect: Incorrect answers
        accuracy: Accuracy percentage
        average_time: Average time per question
    
    Example:
        >>> perf = DifficultyPerformance(
        ...     difficulty="medium",
        ...     total_questions=50,
        ...     correct=35,
        ...     incorrect=15,
        ...     accuracy=70.0
        ... )
    """
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    total_questions: int = Field(..., ge=0, description="Total questions")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage"
    )
    average_time: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Average time per question in seconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "difficulty": "medium",
                "total_questions": 50,
                "correct": 35,
                "incorrect": 15,
                "accuracy": 70.0,
                "average_time": 180.0
            }
        }


class QuestionTypePerformance(BaseModel):
    """
    Performance analysis by question type.
    
    Attributes:
        question_type: Type of question
        total_questions: Total questions
        correct: Correct answers
        incorrect: Incorrect answers
        accuracy: Accuracy percentage
        preference_score: Preference score (0-100)
    
    Example:
        >>> perf = QuestionTypePerformance(
        ...     question_type="single_correct",
        ...     total_questions=80,
        ...     correct=60,
        ...     incorrect=20,
        ...     accuracy=75.0,
        ...     preference_score=80.0
        ... )
    """
    question_type: str = Field(..., description="Type of question")
    total_questions: int = Field(..., ge=0, description="Total questions")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage"
    )
    preference_score: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Preference score based on accuracy and attempt rate"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_type": "single_correct",
                "total_questions": 80,
                "correct": 60,
                "incorrect": 20,
                "accuracy": 75.0,
                "preference_score": 80.0
            }
        }


class TimeManagementAnalysis(BaseModel):
    """
    Time management analysis.
    
    Attributes:
        total_time_taken: Total time taken for test (seconds)
        average_time_per_question: Average time per question
        expected_average_time: Expected average time per question
        time_efficiency: Time efficiency percentage
        too_fast_questions: Number of questions solved too fast
        too_slow_questions: Number of questions solved too slow
        optimal_pace_questions: Questions solved at optimal pace
        recommendations: Time management recommendations
    
    Example:
        >>> analysis = TimeManagementAnalysis(
        ...     total_time_taken=10800,
        ...     average_time_per_question=54.0,
        ...     expected_average_time=60.0,
        ...     time_efficiency=90.0,
        ...     too_fast_questions=10,
        ...     too_slow_questions=15,
        ...     optimal_pace_questions=175
        ... )
    """
    total_time_taken: int = Field(..., ge=0, description="Total time in seconds")
    average_time_per_question: float = Field(
        ...,
        ge=0.0,
        description="Average time per question"
    )
    expected_average_time: float = Field(
        default=60.0,
        ge=0.0,
        description="Expected average time per question"
    )
    time_efficiency: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Time efficiency percentage"
    )
    too_fast_questions: int = Field(
        default=0,
        ge=0,
        description="Questions solved too fast (< 30s)"
    )
    too_slow_questions: int = Field(
        default=0,
        ge=0,
        description="Questions solved too slow (> 5min)"
    )
    optimal_pace_questions: int = Field(
        default=0,
        ge=0,
        description="Questions at optimal pace"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Time management recommendations"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_time_taken": 10800,
                "average_time_per_question": 54.0,
                "expected_average_time": 60.0,
                "time_efficiency": 90.0,
                "too_fast_questions": 10,
                "too_slow_questions": 15,
                "optimal_pace_questions": 175,
                "recommendations": [
                    "Slow down on easy questions to avoid careless mistakes",
                    "Practice time-bound solving for complex problems"
                ]
            }
        }


class StrengthArea(BaseModel):
    """
    Strength area identification.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        accuracy: Accuracy percentage
        reason: Reason for strength
        recommendation: Recommendation for maintaining/leveraging strength
    
    Example:
        >>> strength = StrengthArea(
        ...     topic="Calculus",
        ...     subject="Mathematics",
        ...     accuracy=92.5,
        ...     reason="Consistent high performance across all difficulty levels",
        ...     recommendation="Use as foundation for advanced topics"
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage (0-100)"
    )
    reason: str = Field(..., description="Reason for strength")
    recommendation: str = Field(
        ...,
        description="Recommendation for maintaining/leveraging strength"
    )
    
    @field_validator('accuracy')
    @classmethod
    def validate_accuracy(cls, v: float) -> float:
        """Validate accuracy is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Accuracy must be between 0 and 100, got {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Calculus",
                "subject": "Mathematics",
                "accuracy": 92.5,
                "reason": "Consistent high performance across all difficulty levels",
                "recommendation": "Use as foundation for advanced problem-solving"
            }
        }


class WeaknessArea(BaseModel):
    """
    Weakness area identification.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        accuracy: Accuracy percentage
        reason: Reason for weakness
        priority: Priority level for improvement
        estimated_study_hours: Estimated hours needed for improvement
        recommendation: Specific recommendation for improvement
    
    Example:
        >>> weakness = WeaknessArea(
        ...     topic="Thermodynamics",
        ...     subject="Physics",
        ...     accuracy=28.5,
        ...     reason="Poor conceptual understanding",
        ...     priority="high",
        ...     estimated_study_hours=12.0,
        ...     recommendation="Review fundamental laws and solve practice problems"
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage (0-100)"
    )
    reason: str = Field(..., description="Reason for weakness")
    priority: PriorityLevel = Field(
        ...,
        description="Priority level for improvement"
    )
    estimated_study_hours: float = Field(
        ...,
        ge=0.0,
        description="Estimated study hours needed"
    )
    recommendation: str = Field(
        ...,
        description="Specific recommendation for improvement"
    )
    
    @field_validator('accuracy')
    @classmethod
    def validate_accuracy(cls, v: float) -> float:
        """Validate accuracy is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Accuracy must be between 0 and 100, got {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "accuracy": 28.5,
                "reason": "Poor understanding of fundamental laws",
                "priority": "high",
                "estimated_study_hours": 12.0,
                "recommendation": "Review first and second laws, solve 100 practice problems"
            }
        }


class LearningPattern(BaseModel):
    """
    Detected learning patterns.
    
    Attributes:
        pattern_type: Type of pattern
        description: Pattern description
        confidence: Confidence score (0-100)
        evidence: Supporting evidence
        impact: Impact on overall performance
        recommendation: Recommendation based on pattern
    
    Example:
        >>> pattern = LearningPattern(
        ...     pattern_type="question_type",
        ...     description="Strong preference for MCQ questions",
        ...     confidence=85.0,
        ...     evidence="MCQ accuracy: 80%, Numerical accuracy: 55%",
        ...     impact="Limiting overall score potential",
        ...     recommendation="Practice more numerical questions"
        ... )
    """
    pattern_type: PatternType = Field(..., description="Type of pattern")
    description: str = Field(..., description="Pattern description")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Confidence score (0-100)"
    )
    evidence: str = Field(..., description="Supporting evidence")
    impact: str = Field(..., description="Impact on performance")
    recommendation: Optional[str] = Field(
        default=None,
        description="Recommendation based on pattern"
    )
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Validate confidence is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Confidence must be between 0 and 100, got {v}")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "pattern_type": "question_type",
                "description": "Strong preference for MCQ questions",
                "confidence": 85.0,
                "evidence": "MCQ accuracy: 80%, Numerical accuracy: 55%",
                "impact": "Limiting overall score potential in numerical sections",
                "recommendation": "Practice more numerical questions to balance skills"
            }
        }


class TopicRecommendation(BaseModel):
    """
    Topic-specific recommendation.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        priority: Priority level
        current_accuracy: Current accuracy
        target_accuracy: Target accuracy
        improvement_needed: Improvement percentage needed
        action_items: List of action items
        estimated_effort: Estimated effort (hours)
    
    Example:
        >>> rec = TopicRecommendation(
        ...     topic="Thermodynamics",
        ...     subject="Physics",
        ...     priority="high",
        ...     current_accuracy=35.0,
        ...     target_accuracy=70.0,
        ...     improvement_needed=35.0,
        ...     action_items=["Review basic concepts", "Solve 50 practice problems"],
        ...     estimated_effort=10.0
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    priority: PriorityLevel = Field(..., description="Priority level")
    current_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current accuracy"
    )
    target_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Target accuracy"
    )
    improvement_needed: float = Field(
        ...,
        ge=0.0,
        description="Improvement percentage needed"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="List of action items"
    )
    estimated_effort: float = Field(
        default=5.0,
        ge=0.0,
        description="Estimated effort in hours"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "priority": "high",
                "current_accuracy": 35.0,
                "target_accuracy": 70.0,
                "improvement_needed": 35.0,
                "action_items": [
                    "Review first and second laws of thermodynamics",
                    "Solve 50 practice problems",
                    "Watch video lectures on heat engines"
                ],
                "estimated_effort": 10.0
            }
        }


class PerformanceAnalysis(BaseModel):
    """
    Complete performance analysis report.
    
    Attributes:
        test_id: Test identifier
        student_id: Student identifier
        exam_type: Type of exam
        analysis_date: Analysis timestamp
        overall_accuracy: Overall accuracy percentage
        overall_marks: Overall marks obtained
        overall_max_marks: Overall maximum marks
        strong_topics: List of strong topics
        moderate_topics: List of moderate topics
        weak_topics: List of weak topics
        difficulty_performance: Performance by difficulty
        question_type_performance: Performance by question type
        time_management: Time management analysis
        learning_patterns: Detected learning patterns
        recommendations: Topic recommendations
        subject_strengths: Subject-wise strengths
        priority_topics: Topics prioritized for improvement
    
    Example:
        >>> analysis = PerformanceAnalysis(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     exam_type="JEE_MAIN",
        ...     overall_accuracy=65.0,
        ...     overall_marks=520,
        ...     overall_max_marks=800,
        ...     strong_topics=[],
        ...     moderate_topics=[],
        ...     weak_topics=[]
        ... )
    """
    test_id: str = Field(..., description="Test identifier")
    student_id: str = Field(..., description="Student identifier")
    exam_type: str = Field(..., description="Type of exam")
    analysis_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Analysis timestamp"
    )
    overall_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall accuracy"
    )
    overall_marks: int = Field(..., description="Overall marks obtained")
    overall_max_marks: int = Field(..., gt=0, description="Overall max marks")
    strengths: List[StrengthArea] = Field(
        default_factory=list,
        description="Identified strength areas"
    )
    weaknesses: List[WeaknessArea] = Field(
        default_factory=list,
        description="Identified weakness areas"
    )
    strong_topics: List[TopicPerformance] = Field(
        default_factory=list,
        description="Strong topics (accuracy > 80%)"
    )
    moderate_topics: List[TopicPerformance] = Field(
        default_factory=list,
        description="Moderate topics (accuracy 40-80%)"
    )
    weak_topics: List[TopicPerformance] = Field(
        default_factory=list,
        description="Weak topics (accuracy < 40%)"
    )
    patterns: List[LearningPattern] = Field(
        default_factory=list,
        description="Detected learning patterns"
    )
    overall_assessment: Optional[str] = Field(
        default=None,
        description="Overall performance assessment summary"
    )
    difficulty_performance: Dict[str, DifficultyPerformance] = Field(
        default_factory=dict,
        description="Performance by difficulty level"
    )
    question_type_performance: Dict[str, QuestionTypePerformance] = Field(
        default_factory=dict,
        description="Performance by question type"
    )
    time_management: Optional[TimeManagementAnalysis] = Field(
        default=None,
        description="Time management analysis"
    )
    learning_patterns: List[LearningPattern] = Field(
        default_factory=list,
        description="Detected learning patterns"
    )
    recommendations: List[TopicRecommendation] = Field(
        default_factory=list,
        description="Topic recommendations"
    )
    subject_strengths: Dict[str, float] = Field(
        default_factory=dict,
        description="Subject-wise accuracy percentages"
    )
    priority_topics: List[str] = Field(
        default_factory=list,
        description="Topics prioritized for improvement"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "test_123",
                "student_id": "student_456",
                "exam_type": "JEE_MAIN",
                "analysis_date": "2024-11-28T10:30:00",
                "overall_accuracy": 65.0,
                "overall_marks": 520,
                "overall_max_marks": 800,
                "strengths": [],
                "weaknesses": [],
                "strong_topics": [],
                "moderate_topics": [],
                "weak_topics": [],
                "patterns": [],
                "overall_assessment": "Good performance with room for improvement in conceptual areas",
                "difficulty_performance": {},
                "question_type_performance": {},
                "time_management": None,
                "learning_patterns": [],
                "recommendations": [],
                "subject_strengths": {"Physics": 70.0, "Chemistry": 65.0, "Math": 60.0},
                "priority_topics": ["Thermodynamics", "Calculus"]
            }
        }
