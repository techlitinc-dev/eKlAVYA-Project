"""
Study Center Data Models

This module defines Pydantic models for the Study Center Learning Journey feature
in the Mentor AI EdTech Platform. These models provide data validation,
serialization, and documentation for study center endpoints.

Models:
- Topic: Syllabus topic with progress information
- LearningMaterials: Complete learning materials for a topic
- MindMap: Structured mind map data
- TeachingContent: AI-generated teaching materials
- LearningSession: Student learning session tracking
- ProgressSummary: Student's overall learning progress
- LearningJourney: Recommended learning sequence
- ParentInsights: Progress insights for parents

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class Topic(BaseModel):
    """
    Syllabus topic with progress information.
    
    Represents a single topic from the exam syllabus with associated
    progress tracking and metadata for the Study Center feature.
    
    Attributes:
        topic_id: Unique identifier for the topic
        topic_name: Name of the topic
        subject: Subject area (Physics, Chemistry, Mathematics, etc.)
        chapter: Chapter name containing this topic
        difficulty: Difficulty level (easy, medium, hard)
        estimated_hours: Estimated study time in hours
        prerequisites: List of prerequisite topic IDs
        is_completed: Whether the topic is completed
        completion_percentage: Progress percentage (0-100)
    
    Example:
        >>> topic = Topic(
        ...     topic_id="T02",
        ...     topic_name="Kinematics",
        ...     subject="Physics",
        ...     chapter="Mechanics",
        ...     difficulty="medium",
        ...     estimated_hours=8.5,
        ...     prerequisites=["T01"],
        ...     is_completed=False,
        ...     completion_percentage=45.0
        ... )
    """
    
    topic_id: str = Field(
        ...,
        description="Unique identifier for the topic from syllabus"
    )
    
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    
    subject: str = Field(
        ...,
        description="Subject area (Physics, Chemistry, Mathematics, etc.)"
    )
    
    chapter: str = Field(
        ...,
        description="Chapter name containing this topic"
    )
    
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Difficulty level of the topic"
    )
    
    estimated_hours: float = Field(
        ...,
        ge=0.1,
        description="Estimated study time in hours"
    )
    
    prerequisites: List[str] = Field(
        default_factory=list,
        description="List of prerequisite topic IDs"
    )
    
    is_completed: bool = Field(
        default=False,
        description="Whether the topic is completed"
    )
    
    completion_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Progress percentage (0-100)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "T02",
                "topic_name": "Kinematics",
                "subject": "Physics",
                "chapter": "Mechanics",
                "difficulty": "medium",
                "estimated_hours": 8.5,
                "prerequisites": ["T01"],
                "is_completed": False,
                "completion_percentage": 45.0
            }
        }
    )


class MindMap(BaseModel):
    """
    Structured mind map data for a topic.
    
    Represents a hierarchical mind map with central concept,
    main branches, sub-branches, and connections between concepts.
    
    Attributes:
        mindmap_id: Unique identifier for the mind map
        topic_id: ID of the associated topic
        structure: Hierarchical structure of the mind map
        text_representation: Markdown text representation
        generated_at: Timestamp when mind map was generated
    
    Example:
        >>> mindmap = MindMap(
        ...     mindmap_id="mm_123",
        ...     topic_id="T02",
        ...     structure={
        ...         "central_concept": "Kinematics",
        ...         "main_branches": [...]
        ...     },
        ...     text_representation="# Kinematics\n## Motion...",
        ...     generated_at=datetime.now()
        ... )
    """
    
    mindmap_id: str = Field(
        ...,
        description="Unique identifier for the mind map"
    )
    
    topic_id: str = Field(
        ...,
        description="ID of the associated topic"
    )
    
    structure: Dict[str, Any] = Field(
        ...,
        description="Hierarchical structure of the mind map"
    )
    
    text_representation: str = Field(
        ...,
        description="Markdown text representation of the mind map"
    )
    
    generated_at: datetime = Field(
        ...,
        description="Timestamp when mind map was generated"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "mindmap_id": "mm_123abc456",
                "topic_id": "T02",
                "structure": {
                    "central_concept": "Kinematics",
                    "main_branches": [
                        {
                            "name": "Motion in Straight Line",
                            "sub_branches": [
                                "Uniform Motion",
                                "Accelerated Motion",
                                "Relative Motion"
                            ]
                        }
                    ],
                    "connections": [
                        {"from": "Uniform Motion", "to": "Velocity", "type": "defines"}
                    ]
                },
                "text_representation": "# Kinematics\n## Motion in Straight Line...",
                "generated_at": "2024-01-15T10:00:00Z"
            }
        }
    )


class TeachingContent(BaseModel):
    """
    AI-generated teaching content for a topic.
    
    Comprehensive teaching material including introduction,
    key concepts, worked examples, and summary.
    
    Attributes:
        topic_id: ID of the associated topic
        introduction: Introduction to the topic
        key_concepts: List of key concepts with explanations
        examples: List of worked examples
        summary: Topic summary
        difficulty_level: Difficulty level of the content
    
    Example:
        >>> content = TeachingContent(
        ...     topic_id="T02",
        ...     introduction="Kinematics is the study of motion...",
        ...     key_concepts=[...],
        ...     examples=[...],
        ...     summary="Key takeaways from kinematics...",
        ...     difficulty_level="medium"
        ... )
    """
    
    topic_id: str = Field(
        ...,
        description="ID of the associated topic"
    )
    
    introduction: str = Field(
        ...,
        description="Introduction to the topic"
    )
    
    key_concepts: List[Dict[str, str]] = Field(
        ...,
        description="List of key concepts with explanations"
    )
    
    examples: List[Dict[str, str]] = Field(
        ...,
        min_items=2,
        description="List of worked examples (minimum 2)"
    )
    
    summary: str = Field(
        ...,
        description="Topic summary with key takeaways"
    )
    
    difficulty_level: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Difficulty level of the content"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "T02",
                "introduction": "Kinematics is the branch of mechanics that describes the motion of objects without considering the causes of motion.",
                "key_concepts": [
                    {
                        "name": "Displacement",
                        "explanation": "Change in position of an object, a vector quantity"
                    },
                    {
                        "name": "Velocity",
                        "explanation": "Rate of change of displacement with respect to time"
                    }
                ],
                "examples": [
                    {
                        "problem": "A car travels from rest with constant acceleration of 2 m/s². Find its velocity after 5 seconds.",
                        "solution": "Given: u = 0, a = 2 m/s², t = 5s\nUsing v = u + at\nv = 0 + 2 × 5 = 10 m/s"
                    }
                ],
                "summary": "Kinematics provides mathematical tools to describe and analyze motion using concepts like displacement, velocity, and acceleration.",
                "difficulty_level": "medium"
            }
        }
    )


class LearningMaterials(BaseModel):
    """
    Complete learning materials for a topic.
    
    Aggregates all available learning materials including notes,
    mind maps, and teaching content for a specific topic.
    
    Attributes:
        topic_id: ID of the associated topic
        topic_name: Name of the topic
        notes: AI-generated study notes
        mind_map: Structured mind map (optional)
        teaching_content: Teaching materials (optional)
        cached: Whether materials were retrieved from cache
        generated_at: Timestamp when materials were generated
    
    Example:
        >>> materials = LearningMaterials(
        ...     topic_id="T02",
        ...     topic_name="Kinematics",
        ...     notes="Kinematics is the study of motion...",
        ...     mind_map=mindmap,
        ...     teaching_content=content,
        ...     cached=False,
        ...     generated_at=datetime.now()
        ... )
    """
    
    topic_id: str = Field(
        ...,
        description="ID of the associated topic"
    )
    
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    
    notes: Optional[str] = Field(
        default=None,
        description="AI-generated study notes"
    )
    
    mind_map: Optional[MindMap] = Field(
        default=None,
        description="Structured mind map for the topic"
    )
    
    teaching_content: Optional[TeachingContent] = Field(
        default=None,
        description="AI-generated teaching content"
    )
    
    cached: bool = Field(
        default=False,
        description="Whether materials were retrieved from cache"
    )
    
    generated_at: datetime = Field(
        ...,
        description="Timestamp when materials were generated"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic_id": "T02",
                "topic_name": "Kinematics",
                "notes": "# Kinematics\n\nKinematics is the study of motion...",
                "mind_map": None,
                "teaching_content": None,
                "cached": True,
                "generated_at": "2024-01-15T10:00:00Z"
            }
        }
    )


class LearningSession(BaseModel):
    """
    Student learning session tracking.
    
    Records a learning session with timestamps, duration,
    and materials viewed by the student.
    
    Attributes:
        session_id: Unique identifier for the session
        student_id: ID of the student
        topic_id: ID of the topic being studied
        topic_name: Name of the topic
        subject: Subject area
        start_time: Session start timestamp
        end_time: Session end timestamp (optional)
        duration_minutes: Session duration in minutes (optional)
        materials_viewed: List of materials accessed
        completed: Whether the session was marked as completed
    
    Example:
        >>> session = LearningSession(
        ...     session_id="sess_123",
        ...     student_id="student_456",
        ...     topic_id="T02",
        ...     topic_name="Kinematics",
        ...     subject="Physics",
        ...     start_time=datetime.now(),
        ...     materials_viewed=["notes", "mind_map"],
        ...     completed=False
        ... )
    """
    
    session_id: str = Field(
        ...,
        description="Unique identifier for the session"
    )
    
    student_id: str = Field(
        ...,
        description="ID of the student"
    )
    
    topic_id: str = Field(
        ...,
        description="ID of the topic being studied"
    )
    
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    
    subject: str = Field(
        ...,
        description="Subject area"
    )
    
    start_time: datetime = Field(
        ...,
        description="Session start timestamp"
    )
    
    end_time: Optional[datetime] = Field(
        default=None,
        description="Session end timestamp"
    )
    
    duration_minutes: Optional[int] = Field(
        default=None,
        ge=0,
        description="Session duration in minutes"
    )
    
    materials_viewed: List[str] = Field(
        default_factory=list,
        description="List of materials accessed during session"
    )
    
    completed: bool = Field(
        default=False,
        description="Whether the session was marked as completed"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "session_id": "sess_123abc456",
                "student_id": "student_789def",
                "topic_id": "T02",
                "topic_name": "Kinematics",
                "subject": "Physics",
                "start_time": "2024-01-15T14:00:00Z",
                "end_time": "2024-01-15T15:30:00Z",
                "duration_minutes": 90,
                "materials_viewed": ["notes", "mind_map"],
                "completed": True
            }
        }
    )


class ProgressSummary(BaseModel):
    """
    Student's overall learning progress summary.
    
    Aggregates progress data across all topics with statistics
    on completion, study time, and streaks.
    
    Attributes:
        student_id: ID of the student
        total_topics: Total number of topics in syllabus
        completed_topics: Number of completed topics
        completion_percentage: Overall completion percentage
        total_study_time_hours: Total study time in hours
        current_streak_days: Current consecutive study days
        topics_by_subject: Progress breakdown by subject
    
    Example:
        >>> summary = ProgressSummary(
        ...     student_id="student_456",
        ...     total_topics=50,
        ...     completed_topics=12,
        ...     completion_percentage=24.0,
        ...     total_study_time_hours=45.5,
        ...     current_streak_days=7,
        ...     topics_by_subject={"Physics": {"completed": 8, "total": 20}}
        ... )
    """
    
    student_id: str = Field(
        ...,
        description="ID of the student"
    )
    
    total_topics: int = Field(
        ...,
        ge=0,
        description="Total number of topics in syllabus"
    )
    
    completed_topics: int = Field(
        ...,
        ge=0,
        description="Number of completed topics"
    )
    
    completion_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall completion percentage"
    )
    
    total_study_time_hours: float = Field(
        ...,
        ge=0.0,
        description="Total study time in hours"
    )
    
    current_streak_days: int = Field(
        ...,
        ge=0,
        description="Current consecutive study days"
    )
    
    topics_by_subject: Dict[str, Dict[str, int]] = Field(
        ...,
        description="Progress breakdown by subject"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_789def",
                "total_topics": 50,
                "completed_topics": 12,
                "completion_percentage": 24.0,
                "total_study_time_hours": 45.5,
                "current_streak_days": 7,
                "topics_by_subject": {
                    "Physics": {"completed": 8, "total": 20},
                    "Chemistry": {"completed": 4, "total": 15},
                    "Mathematics": {"completed": 0, "total": 15}
                }
            }
        }
    )


class LearningJourney(BaseModel):
    """
    Recommended learning sequence for a student.
    
    Provides a structured learning path with prerequisites,
    next steps, and motivational elements.
    
    Attributes:
        student_id: ID of the student
        recommended_sequence: Ordered list of topics to study
        next_topic: Next recommended topic
        prerequisites_pending: Topics that need completion first
        motivational_message: Encouraging message for student
    
    Example:
        >>> journey = LearningJourney(
        ...     student_id="student_456",
        ...     recommended_sequence=[topic1, topic2],
        ...     next_topic=topic1,
        ...     prerequisites_pending=[],
        ...     motivational_message="Great progress! Keep going!"
        ... )
    """
    
    student_id: str = Field(
        ...,
        description="ID of the student"
    )
    
    recommended_sequence: List[Topic] = Field(
        ...,
        description="Ordered list of topics to study"
    )
    
    next_topic: Topic = Field(
        ...,
        description="Next recommended topic"
    )
    
    prerequisites_pending: List[Topic] = Field(
        default_factory=list,
        description="Topics that need completion first"
    )
    
    motivational_message: str = Field(
        ...,
        description="Encouraging message for student"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_789def",
                "recommended_sequence": [
                    {
                        "topic_id": "T01",
                        "topic_name": "Units and Measurements",
                        "subject": "Physics",
                        "chapter": "Mechanics",
                        "difficulty": "easy",
                        "estimated_hours": 3.0,
                        "prerequisites": [],
                        "is_completed": True,
                        "completion_percentage": 100.0
                    }
                ],
                "next_topic": {
                    "topic_id": "T02",
                    "topic_name": "Kinematics",
                    "subject": "Physics",
                    "chapter": "Mechanics",
                    "difficulty": "medium",
                    "estimated_hours": 8.5,
                    "prerequisites": ["T01"],
                    "is_completed": False,
                    "completion_percentage": 0.0
                },
                "prerequisites_pending": [],
                "motivational_message": "Great job completing Units and Measurements! Let's move on to Kinematics."
            }
        }
    )


class ParentInsights(BaseModel):
    """
    Progress insights for parents.
    
    Comprehensive view of child's learning progress with
    analytics, patterns, and recommendations.
    
    Attributes:
        child_id: ID of the child student
        child_name: Name of the child
        overall_progress: Overall completion percentage
        topics_completed: Number of completed topics
        total_topics: Total number of topics
        daily_average_minutes: Average daily study time (7 days)
        weekly_average_minutes: Average weekly study time (30 days)
        most_studied_topics: Top 3 most studied topics
        least_studied_topics: Top 3 least studied topics
        current_streak: Current study streak in days
        last_study_session: Timestamp of last study session
        recommendations: Actionable recommendations for parents
    
    Example:
        >>> insights = ParentInsights(
        ...     child_id="student_456",
        ...     child_name="John Doe",
        ...     overall_progress=24.0,
        ...     topics_completed=12,
        ...     total_topics=50,
        ...     daily_average_minutes=65.0,
        ...     weekly_average_minutes=455.0,
        ...     most_studied_topics=[...],
        ...     least_studied_topics=[...],
        ...     current_streak=7,
        ...     last_study_session=datetime.now(),
        ...     recommendations=["Encourage consistent daily study"]
        ... )
    """
    
    child_id: str = Field(
        ...,
        description="ID of the child student"
    )
    
    child_name: str = Field(
        ...,
        description="Name of the child"
    )
    
    overall_progress: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall completion percentage"
    )
    
    topics_completed: int = Field(
        ...,
        ge=0,
        description="Number of completed topics"
    )
    
    total_topics: int = Field(
        ...,
        ge=0,
        description="Total number of topics"
    )
    
    daily_average_minutes: float = Field(
        ...,
        ge=0.0,
        description="Average daily study time (past 7 days)"
    )
    
    weekly_average_minutes: float = Field(
        ...,
        ge=0.0,
        description="Average weekly study time (past 30 days)"
    )
    
    most_studied_topics: List[Dict[str, Any]] = Field(
        ...,
        min_items=0,
        max_items=3,
        description="Top 3 most studied topics"
    )
    
    least_studied_topics: List[Dict[str, Any]] = Field(
        ...,
        min_items=0,
        max_items=3,
        description="Top 3 least studied topics"
    )
    
    current_streak: int = Field(
        ...,
        ge=0,
        description="Current study streak in days"
    )
    
    last_study_session: datetime = Field(
        ...,
        description="Timestamp of last study session"
    )
    
    recommendations: List[str] = Field(
        ...,
        description="Actionable recommendations for parents"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "child_id": "student_789def",
                "child_name": "John Doe",
                "overall_progress": 24.0,
                "topics_completed": 12,
                "total_topics": 50,
                "daily_average_minutes": 65.0,
                "weekly_average_minutes": 455.0,
                "most_studied_topics": [
                    {
                        "topic_name": "Units and Measurements",
                        "time_spent_minutes": 180,
                        "sessions_count": 5
                    }
                ],
                "least_studied_topics": [
                    {
                        "topic_name": "Thermodynamics",
                        "time_spent_minutes": 30,
                        "sessions_count": 1
                    }
                ],
                "current_streak": 7,
                "last_study_session": "2024-01-15T16:00:00Z",
                "recommendations": [
                    "Encourage consistent daily study sessions",
                    "Focus on completing Thermodynamics topic",
                    "Maintain the current 7-day study streak"
                ]
            }
        }
    )


# Request/Response Models for API Endpoints

class TopicListRequest(BaseModel):
    """Request model for getting topics list."""
    student_id: str = Field(..., description="ID of the student")
    subject: Optional[str] = Field(None, description="Filter by subject")


class MaterialRequest(BaseModel):
    """Request model for getting learning materials."""
    student_id: str = Field(..., description="ID of the student")
    topic_id: str = Field(..., description="ID of the topic")


class GenerateMaterialRequest(BaseModel):
    """Request model for generating new materials."""
    student_id: str = Field(..., description="ID of the student")
    topic_id: str = Field(..., description="ID of the topic")
    material_type: Literal["notes", "mind_map", "teaching_content", "all"] = Field(
        default="all",
        description="Type of material to generate"
    )


class SessionStartRequest(BaseModel):
    """Request model for starting a learning session."""
    student_id: str = Field(..., description="ID of the student")
    topic_id: str = Field(..., description="ID of the topic")


class SessionCompleteRequest(BaseModel):
    """Request model for completing a learning session."""
    student_id: str = Field(..., description="ID of the student")
    topic_id: str = Field(..., description="ID of the topic")
    session_id: str = Field(..., description="ID of the session to complete")


# Response Models

class APIResponse(BaseModel):
    """Base API response model."""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")