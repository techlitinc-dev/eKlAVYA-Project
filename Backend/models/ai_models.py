"""
AI-Powered Feature Models

This module defines Pydantic models for AI-powered features including
AI tutor chat, smart recommendations, exam readiness, and mistake analysis.

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class AITutorMessage(BaseModel):
    """Message in AI tutor chat."""
    
    message_id: str = Field(..., description="Message identifier")
    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_123",
                "role": "user",
                "content": "Can you explain the second law of thermodynamics?",
                "timestamp": "2024-01-15T14:30:00Z",
                "context": {"subject": "Physics", "topic": "Thermodynamics"}
            }
        }
    )


class AITutorRequest(BaseModel):
    """Request to AI tutor."""
    
    student_id: str = Field(..., description="Student identifier")
    question: str = Field(..., min_length=5, description="Student's question")
    subject: Optional[str] = Field(None, description="Subject context")
    topic: Optional[str] = Field(None, description="Topic context")
    include_examples: bool = Field(default=True, description="Include examples in response")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "question": "Can you explain the second law of thermodynamics?",
                "subject": "Physics",
                "topic": "Thermodynamics",
                "include_examples": True
            }
        }
    )


class AITutorResponse(BaseModel):
    """Response from AI tutor."""
    
    message_id: str = Field(..., description="Message identifier")
    answer: str = Field(..., description="AI tutor's answer")
    key_points: List[str] = Field(default_factory=list, description="Key points")
    examples: List[str] = Field(default_factory=list, description="Examples")
    related_topics: List[str] = Field(default_factory=list, description="Related topics")
    practice_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Suggested practice questions"
    )
    resources: List[Dict[str, str]] = Field(default_factory=list, description="Additional resources")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "msg_124",
                "answer": "The second law of thermodynamics states that...",
                "key_points": [
                    "Entropy always increases in isolated systems",
                    "Heat flows from hot to cold spontaneously"
                ],
                "examples": [
                    "Ice melting in warm water",
                    "Gas expanding into vacuum"
                ],
                "related_topics": ["Entropy", "Heat Engines", "Carnot Cycle"],
                "practice_questions": [],
                "resources": [
                    {"title": "Thermodynamics Video", "url": "https://example.com/video"}
                ]
            }
        }
    )


class ChatHistory(BaseModel):
    """Chat history with AI tutor."""
    
    student_id: str = Field(..., description="Student identifier")
    messages: List[AITutorMessage] = Field(..., description="Chat messages")
    total_messages: int = Field(..., ge=0, description="Total message count")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "messages": [],
                "total_messages": 0
            }
        }
    )


class TopicRecommendation(BaseModel):
    """AI-recommended topic to study."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject")
    priority: Literal["critical", "high", "medium", "low"] = Field(
        ...,
        description="Priority level"
    )
    reason: str = Field(..., description="Reason for recommendation")
    estimated_hours: float = Field(..., ge=0, description="Estimated study hours")
    current_accuracy: float = Field(..., ge=0, le=100, description="Current accuracy %")
    target_accuracy: float = Field(..., ge=0, le=100, description="Target accuracy %")
    weightage: float = Field(..., ge=0, description="Exam weightage")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "topic_123",
                "topic_name": "Thermodynamics",
                "subject": "Physics",
                "priority": "high",
                "reason": "Low accuracy (45%) on high-weightage topic (8%)",
                "estimated_hours": 6.0,
                "current_accuracy": 45.0,
                "target_accuracy": 75.0,
                "weightage": 8.0
            }
        }
    )


class ResourceRecommendation(BaseModel):
    """AI-recommended resource for a topic."""
    
    resource_id: str = Field(..., description="Resource identifier")
    title: str = Field(..., description="Resource title")
    type: Literal["video", "article", "practice", "notes", "book"] = Field(
        ...,
        description="Resource type"
    )
    url: Optional[str] = Field(None, description="Resource URL")
    description: str = Field(..., description="Resource description")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        ...,
        description="Difficulty level"
    )
    duration: Optional[str] = Field(None, description="Duration/length")
    rating: float = Field(..., ge=0, le=5, description="Resource rating")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance to student")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resource_id": "res_123",
                "title": "Thermodynamics Explained",
                "type": "video",
                "url": "https://youtube.com/watch?v=...",
                "description": "Comprehensive explanation of thermodynamics laws",
                "difficulty": "intermediate",
                "duration": "25:30",
                "rating": 4.5,
                "relevance_score": 0.92
            }
        }
    )


class ExamReadiness(BaseModel):
    """Exam readiness assessment."""
    
    student_id: str = Field(..., description="Student identifier")
    overall_readiness: float = Field(..., ge=0, le=100, description="Overall readiness %")
    readiness_level: Literal["not_ready", "needs_work", "good", "excellent"] = Field(
        ...,
        description="Readiness level"
    )
    subject_readiness: Dict[str, float] = Field(..., description="Subject-wise readiness %")
    topic_coverage: float = Field(..., ge=0, le=100, description="Topic coverage %")
    practice_score: float = Field(..., ge=0, le=100, description="Practice test average")
    consistency_score: float = Field(..., ge=0, le=100, description="Study consistency score")
    predicted_rank_range: str = Field(..., description="Predicted rank range")
    confidence: float = Field(..., ge=0, le=100, description="Prediction confidence %")
    gaps: List[Dict[str, Any]] = Field(default_factory=list, description="Knowledge gaps")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    days_to_exam: int = Field(..., ge=0, description="Days until exam")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "overall_readiness": 72.5,
                "readiness_level": "good",
                "subject_readiness": {
                    "Physics": 68.0,
                    "Chemistry": 75.0,
                    "Mathematics": 74.5
                },
                "topic_coverage": 78.0,
                "practice_score": 71.5,
                "consistency_score": 85.0,
                "predicted_rank_range": "2000-2500",
                "confidence": 78.0,
                "gaps": [
                    {
                        "subject": "Physics",
                        "topic": "Thermodynamics",
                        "severity": "high",
                        "hours_needed": 6.0
                    }
                ],
                "recommendations": [
                    "Focus 6 more hours on Thermodynamics",
                    "Take 2 more full-length practice tests",
                    "Revise Organic Chemistry formulas"
                ],
                "days_to_exam": 45
            }
        }
    )


class MistakePattern(BaseModel):
    """Pattern in student's mistakes."""
    
    pattern_type: Literal["calculation", "conceptual", "silly", "time_management", "incomplete"] = Field(
        ...,
        description="Type of mistake pattern"
    )
    frequency: int = Field(..., ge=0, description="Number of occurrences")
    percentage: float = Field(..., ge=0, le=100, description="Percentage of total mistakes")
    subjects_affected: List[str] = Field(..., description="Affected subjects")
    topics_affected: List[str] = Field(..., description="Affected topics")
    examples: List[Dict[str, str]] = Field(default_factory=list, description="Example mistakes")
    impact: Literal["high", "medium", "low"] = Field(..., description="Impact on score")
    recommendation: str = Field(..., description="How to fix this pattern")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "pattern_type": "calculation",
                "frequency": 12,
                "percentage": 35.3,
                "subjects_affected": ["Physics", "Chemistry"],
                "topics_affected": ["Thermodynamics", "Chemical Kinetics"],
                "examples": [
                    {"question": "Q15", "mistake": "Decimal point error in calculation"}
                ],
                "impact": "high",
                "recommendation": "Double-check calculations and use calculator for complex computations"
            }
        }
    )


class MistakeAnalysis(BaseModel):
    """Comprehensive mistake analysis."""
    
    student_id: str = Field(..., description="Student identifier")
    total_mistakes: int = Field(..., ge=0, description="Total mistakes analyzed")
    analysis_period: str = Field(..., description="Analysis period")
    patterns: List[MistakePattern] = Field(..., description="Identified patterns")
    most_common_pattern: str = Field(..., description="Most common mistake type")
    improvement_potential: float = Field(
        ...,
        ge=0,
        le=100,
        description="Potential score improvement %"
    )
    priority_actions: List[str] = Field(..., description="Priority actions to take")
    subject_wise_mistakes: Dict[str, int] = Field(..., description="Mistakes by subject")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "total_mistakes": 34,
                "analysis_period": "Last 30 days",
                "patterns": [],
                "most_common_pattern": "calculation",
                "improvement_potential": 12.5,
                "priority_actions": [
                    "Practice more calculation-heavy problems",
                    "Use calculator for complex computations",
                    "Review conceptual understanding of Thermodynamics"
                ],
                "subject_wise_mistakes": {
                    "Physics": 15,
                    "Chemistry": 10,
                    "Mathematics": 9
                }
            }
        }
    )
