"""
Student Dashboard and Learning Models

This module defines Pydantic models for student-facing features including
daily plans, practice modes, doubts, bookmarks, and achievements.

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TodaysPlan(BaseModel):
    """Today's study plan for a student."""
    
    student_id: str = Field(..., description="Student identifier")
    plan_date: date = Field(..., description="Plan date")
    topics: List[Dict[str, Any]] = Field(..., description="Topics to study today")
    total_estimated_hours: float = Field(..., ge=0, description="Total estimated hours")
    pending_from_yesterday: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Pending items from yesterday"
    )
    current_streak: int = Field(..., ge=0, description="Current study streak")
    completion_percentage: float = Field(..., ge=0, le=100, description="Today's completion %")
    motivational_message: str = Field(..., description="Personalized motivational message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "plan_date": "2024-01-15",
                "topics": [
                    {
                        "subject": "Physics",
                        "topic": "Thermodynamics",
                        "estimated_hours": 2.0,
                        "priority": "high",
                        "completed": False
                    },
                    {
                        "subject": "Mathematics",
                        "topic": "Integration",
                        "estimated_hours": 1.5,
                        "priority": "medium",
                        "completed": False
                    }
                ],
                "total_estimated_hours": 3.5,
                "pending_from_yesterday": [
                    {"topic": "Organic Chemistry", "reason": "incomplete"}
                ],
                "current_streak": 5,
                "completion_percentage": 0.0,
                "motivational_message": "Great job on your 5-day streak! Keep it up!"
            }
        }
    )


class TopicResources(BaseModel):
    """Resources for a specific topic."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    videos: List[Dict[str, str]] = Field(default_factory=list, description="Video resources")
    formula_sheets: List[Dict[str, str]] = Field(default_factory=list, description="Formula sheets")
    revision_notes: List[Dict[str, str]] = Field(default_factory=list, description="Revision notes")
    reference_links: List[Dict[str, str]] = Field(default_factory=list, description="Reference links")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "topic_123",
                "topic_name": "Thermodynamics",
                "videos": [
                    {"title": "Laws of Thermodynamics", "url": "https://youtube.com/...", "duration": "15:30"},
                    {"title": "Heat Engines", "url": "https://youtube.com/...", "duration": "12:45"}
                ],
                "formula_sheets": [
                    {"title": "Thermodynamics Formulas", "url": "https://example.com/formulas.pdf"}
                ],
                "revision_notes": [
                    {"title": "Quick Revision - Thermodynamics", "content": "Key concepts..."}
                ],
                "reference_links": [
                    {"title": "NCERT Chapter", "url": "https://ncert.nic.in/..."}
                ]
            }
        }
    )


class QuickPracticeRequest(BaseModel):
    """Request for quick practice session."""
    
    student_id: str = Field(..., description="Student identifier")
    subject: Optional[str] = Field(None, description="Subject filter")
    duration_minutes: int = Field(..., ge=5, le=60, description="Practice duration in minutes")
    focus: Literal["weak_topics", "revision", "random", "specific_topic"] = Field(
        ...,
        description="Practice focus area"
    )
    specific_topic: Optional[str] = Field(None, description="Specific topic if focus is 'specific_topic'")
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(
        None,
        description="Difficulty level"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "subject": "Physics",
                "duration_minutes": 15,
                "focus": "weak_topics",
                "specific_topic": None,
                "difficulty": "medium"
            }
        }
    )


class QuickPracticeResponse(BaseModel):
    """Response with quick practice questions."""
    
    practice_id: str = Field(..., description="Practice session identifier")
    questions: List[Dict[str, Any]] = Field(..., description="Practice questions")
    total_questions: int = Field(..., description="Total number of questions")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    focus_area: str = Field(..., description="Focus area of practice")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "practice_id": "practice_123",
                "questions": [],
                "total_questions": 5,
                "estimated_duration": 15,
                "focus_area": "weak_topics"
            }
        }
    )


class Doubt(BaseModel):
    """Student doubt/question."""
    
    doubt_id: str = Field(..., description="Doubt identifier")
    student_id: str = Field(..., description="Student identifier")
    question_id: Optional[str] = Field(None, description="Related question ID if from test")
    subject: str = Field(..., description="Subject")
    topic: str = Field(..., description="Topic")
    doubt_text: str = Field(..., min_length=10, description="Doubt description")
    status: Literal["open", "explained", "understood", "still_confused"] = Field(
        default="open",
        description="Doubt status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doubt_id": "doubt_123",
                "student_id": "student_123",
                "question_id": "q_456",
                "subject": "Physics",
                "topic": "Thermodynamics",
                "doubt_text": "I don't understand why entropy increases in irreversible processes",
                "status": "open",
                "created_at": "2024-01-15T14:30:00Z",
                "resolved_at": None
            }
        }
    )


class DoubtRequest(BaseModel):
    """Request to create a doubt."""
    
    student_id: str = Field(..., description="Student identifier")
    question_id: Optional[str] = Field(None, description="Related question ID")
    subject: str = Field(..., description="Subject")
    topic: str = Field(..., description="Topic")
    doubt_text: str = Field(..., min_length=10, description="Doubt description")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "question_id": "q_456",
                "subject": "Physics",
                "topic": "Thermodynamics",
                "doubt_text": "I don't understand why entropy increases in irreversible processes"
            }
        }
    )


class DoubtExplanation(BaseModel):
    """AI-generated explanation for a doubt."""
    
    doubt_id: str = Field(..., description="Doubt identifier")
    explanation: str = Field(..., description="Detailed explanation")
    key_concepts: List[str] = Field(default_factory=list, description="Key concepts covered")
    examples: List[str] = Field(default_factory=list, description="Examples")
    similar_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Similar practice questions"
    )
    resources: List[Dict[str, str]] = Field(default_factory=list, description="Additional resources")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "doubt_id": "doubt_123",
                "explanation": "Entropy increases in irreversible processes because...",
                "key_concepts": ["Second Law of Thermodynamics", "Entropy", "Irreversibility"],
                "examples": ["Example 1: Heat transfer...", "Example 2: Gas expansion..."],
                "similar_questions": [],
                "resources": [
                    {"title": "Entropy Explained", "url": "https://example.com/entropy"}
                ]
            }
        }
    )


class RevisionItem(BaseModel):
    """Topic due for revision."""
    
    topic_id: str = Field(..., description="Topic identifier")
    topic_name: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject")
    last_studied: date = Field(..., description="Last study date")
    due_date: date = Field(..., description="Revision due date")
    priority: Literal["high", "medium", "low"] = Field(..., description="Revision priority")
    estimated_time: float = Field(..., ge=0, description="Estimated revision time in hours")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "topic_123",
                "topic_name": "Thermodynamics",
                "subject": "Physics",
                "last_studied": "2024-01-08",
                "due_date": "2024-01-15",
                "priority": "high",
                "estimated_time": 1.5
            }
        }
    )


class PerformanceInsights(BaseModel):
    """Student performance insights."""
    
    student_id: str = Field(..., description="Student identifier")
    best_time_of_day: str = Field(..., description="Best performing time of day")
    average_time_per_question: Dict[str, float] = Field(
        ...,
        description="Average time per question by subject"
    )
    accuracy_trend: Literal["improving", "stable", "declining"] = Field(
        ...,
        description="Accuracy trend"
    )
    accuracy_change: float = Field(..., description="Accuracy change percentage")
    predicted_score: float = Field(..., ge=0, le=100, description="Predicted exam score")
    confidence_interval: Dict[str, float] = Field(
        ...,
        description="Prediction confidence interval"
    )
    strengths: List[str] = Field(default_factory=list, description="Strong areas")
    weaknesses: List[str] = Field(default_factory=list, description="Weak areas")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "best_time_of_day": "Morning (9 AM - 12 PM)",
                "average_time_per_question": {
                    "Physics": 2.5,
                    "Chemistry": 2.2,
                    "Mathematics": 3.0
                },
                "accuracy_trend": "improving",
                "accuracy_change": 5.2,
                "predicted_score": 78.5,
                "confidence_interval": {"lower": 75.0, "upper": 82.0},
                "strengths": ["Calculus", "Organic Chemistry"],
                "weaknesses": ["Thermodynamics", "Electromagnetism"],
                "recommendations": [
                    "Focus more on Thermodynamics",
                    "Practice more numerical problems in Physics"
                ]
            }
        }
    )


class Bookmark(BaseModel):
    """Bookmarked item."""
    
    bookmark_id: str = Field(..., description="Bookmark identifier")
    student_id: str = Field(..., description="Student identifier")
    item_type: Literal["question", "topic", "resource", "note"] = Field(
        ...,
        description="Type of bookmarked item"
    )
    item_id: str = Field(..., description="Item identifier")
    title: str = Field(..., description="Bookmark title")
    subject: Optional[str] = Field(None, description="Subject")
    tags: List[str] = Field(default_factory=list, description="Custom tags")
    notes: Optional[str] = Field(None, description="Personal notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bookmark_id": "bookmark_123",
                "student_id": "student_123",
                "item_type": "question",
                "item_id": "q_456",
                "title": "Challenging thermodynamics problem",
                "subject": "Physics",
                "tags": ["difficult", "important"],
                "notes": "Review this before exam",
                "created_at": "2024-01-15T10:00:00Z"
            }
        }
    )


class BookmarkRequest(BaseModel):
    """Request to create a bookmark."""
    
    student_id: str = Field(..., description="Student identifier")
    item_type: Literal["question", "topic", "resource", "note"] = Field(
        ...,
        description="Type of item to bookmark"
    )
    item_id: str = Field(..., description="Item identifier")
    title: str = Field(..., description="Bookmark title")
    subject: Optional[str] = Field(None, description="Subject")
    tags: List[str] = Field(default_factory=list, description="Custom tags")
    notes: Optional[str] = Field(None, description="Personal notes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "item_type": "question",
                "item_id": "q_456",
                "title": "Challenging thermodynamics problem",
                "subject": "Physics",
                "tags": ["difficult", "important"],
                "notes": "Review this before exam"
            }
        }
    )


class PeerComparison(BaseModel):
    """Anonymous peer comparison data."""
    
    student_id: str = Field(..., description="Student identifier")
    overall_percentile: float = Field(..., ge=0, le=100, description="Overall percentile")
    subject_percentiles: Dict[str, float] = Field(..., description="Subject-wise percentiles")
    rank_range: str = Field(..., description="Estimated rank range")
    total_students: int = Field(..., description="Total students in comparison pool")
    performance_category: Literal["top_10", "top_25", "top_50", "below_50"] = Field(
        ...,
        description="Performance category"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "overall_percentile": 78.5,
                "subject_percentiles": {
                    "Physics": 75.0,
                    "Chemistry": 82.0,
                    "Mathematics": 79.0
                },
                "rank_range": "2000-2500",
                "total_students": 10000,
                "performance_category": "top_25"
            }
        }
    )
