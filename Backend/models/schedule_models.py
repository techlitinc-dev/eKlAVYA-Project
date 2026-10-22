"""
Schedule Models for Mentor AI Platform.

This module defines Pydantic models for AI-powered study schedule generation,
progress tracking, and dynamic rescheduling for JEE/NEET exam preparation.

Models:
- ScheduleRequest: Request to generate a personalized study schedule
- TopicPriority: Priority and metadata for a topic in schedule
- DailyTopic: Topic details for a specific day in schedule
- ScheduleDay: Complete plan for a single day
- Schedule: Complete study schedule with all days and metadata
- ProgressUpdate: Daily progress tracking and completion data
- RescheduleRequest: Request to regenerate/adjust schedule

Author: Mentor AI Team
Version: 1.0.0
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Literal
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class ExamType(str, Enum):
    """Supported exam types."""
    JEE_MAIN = "JEE_MAIN"
    JEE_ADVANCED = "JEE_ADVANCED"
    NEET = "NEET"


class DifficultyLevel(str, Enum):
    """Topic difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PriorityLevel(str, Enum):
    """Priority level labels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ScheduleStatus(str, Enum):
    """Schedule status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DayStatus(str, Enum):
    """Daily progress status."""
    COMPLETED = "completed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RescheduleReason(str, Enum):
    """Reasons for rescheduling."""
    MISSED_SESSIONS = "missed_sessions"
    TOPIC_OVERRUN = "topic_overrun"
    LOW_PERFORMANCE = "low_performance"
    STUDENT_REQUEST = "student_request"


class ScheduleRequest(BaseModel):
    """
    Request to generate a personalized study schedule.
    
    This model captures all necessary information to generate an AI-powered
    study schedule tailored to the student's performance, exam date, and
    study capacity.
    
    Attributes:
        student_id: Unique student identifier
        analytics_id: Analytics report ID to base schedule on
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        exam_date: Date of the exam
        daily_study_hours: Hours available for study per day (2-8)
        preferences: Optional study preferences (subject focus, time slots, etc.)
    
    Example:
        >>> request = ScheduleRequest(
        ...     student_id="student_456",
        ...     analytics_id="analytics_123",
        ...     exam_type="JEE_MAIN",
        ...     exam_date=date(2024, 4, 1),
        ...     daily_study_hours=5.0,
        ...     preferences={"preferred_subjects": ["Physics"], "morning_study": True}
        ... )
    """
    student_id: str = Field(
        ...,
        min_length=1,
        description="Unique student identifier"
    )
    analytics_id: str = Field(
        ...,
        min_length=1,
        description="Analytics report ID to base schedule on"
    )
    exam_type: ExamType = Field(
        ...,
        description="Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)"
    )
    exam_date: date = Field(
        ...,
        description="Date of the exam"
    )
    daily_study_hours: float = Field(
        default=4.0,
        ge=2.0,
        le=8.0,
        description="Hours available for study per day (2-8)"
    )
    preferences: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional study preferences (subject focus, time slots, etc.)"
    )
    
    @field_validator('exam_date')
    @classmethod
    def validate_exam_date(cls, v: date) -> date:
        """Validate that exam date is in the future."""
        if v <= date.today():
            raise ValueError(
                f"Exam date must be in the future. Got: {v}, Today: {date.today()}"
            )
        return v
    
    @field_validator('daily_study_hours')
    @classmethod
    def validate_daily_hours(cls, v: float) -> float:
        """Validate daily study hours is within realistic range."""
        if not 2.0 <= v <= 8.0:
            raise ValueError(
                f"Daily study hours must be between 2 and 8 hours, got {v}"
            )
        return round(v, 1)
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "student_id": "student_456",
                "analytics_id": "analytics_test123_student456_1234567890",
                "exam_type": "JEE_MAIN",
                "exam_date": "2024-04-01",
                "daily_study_hours": 5.0,
                "preferences": {
                    "preferred_subjects": ["Physics", "Mathematics"],
                    "morning_study": True,
                    "avoid_evenings": False
                }
            }
        }


class TopicPriority(BaseModel):
    """
    Priority and metadata for a topic in the schedule.
    
    This model represents a single topic with its priority score, current
    performance, target goals, and estimated study requirements.
    
    Attributes:
        topic: Topic name
        subject: Subject name (Physics, Chemistry, Mathematics, Biology)
        priority_score: Calculated priority score (higher = more urgent)
        current_accuracy: Current accuracy percentage (0-100)
        target_accuracy: Target accuracy percentage (default: 80)
        weightage: Topic weightage in exam (percentage)
        estimated_hours: Estimated study hours needed
        difficulty: Difficulty level (easy, medium, hard)
        priority_level: Priority classification (critical, high, medium, low)
    
    Example:
        >>> priority = TopicPriority(
        ...     topic="Thermodynamics",
        ...     subject="Physics",
        ...     priority_score=300.0,
        ...     current_accuracy=25.0,
        ...     target_accuracy=70.0,
        ...     weightage=4.0,
        ...     estimated_hours=12.0,
        ...     difficulty="medium",
        ...     priority_level="critical"
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    priority_score: float = Field(
        ...,
        ge=0.0,
        description="Calculated priority score (higher = more urgent)"
    )
    current_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current accuracy percentage (0-100)"
    )
    target_accuracy: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Target accuracy percentage"
    )
    weightage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Topic weightage in exam (percentage)"
    )
    estimated_hours: float = Field(
        ...,
        ge=0.0,
        description="Estimated study hours needed"
    )
    difficulty: DifficultyLevel = Field(
        ...,
        description="Difficulty level"
    )
    priority_level: PriorityLevel = Field(
        ...,
        description="Priority classification"
    )
    
    @field_validator('current_accuracy', 'target_accuracy', 'weightage')
    @classmethod
    def validate_percentage(cls, v: float) -> float:
        """Validate percentage values are between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Percentage must be between 0 and 100, got {v}")
        return round(v, 2)
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "priority_score": 300.0,
                "current_accuracy": 25.0,
                "target_accuracy": 70.0,
                "weightage": 4.0,
                "estimated_hours": 12.0,
                "difficulty": "medium",
                "priority_level": "critical"
            }
        }


class DailyTopic(BaseModel):
    """
    Topic details for a specific day in the schedule.
    
    This model defines what should be studied on a particular day, including
    subtopics to cover, resources to use, and learning goals to achieve.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        priority: Priority level (critical, high, medium, low)
        estimated_hours: Estimated hours to spend on this topic
        subtopics: List of specific subtopics to cover
        resources: List of study resources (videos, readings, practice sets)
        goals: List of daily learning objectives for this topic
    
    Example:
        >>> daily_topic = DailyTopic(
        ...     topic="Thermodynamics",
        ...     subject="Physics",
        ...     priority="critical",
        ...     estimated_hours=3.0,
        ...     subtopics=["First Law", "Second Law", "Entropy"],
        ...     resources=["NCERT Chapter 12", "HC Verma Problems", "Video Lecture Series"],
        ...     goals=["Understand first law applications", "Solve 20 numerical problems"]
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    priority: PriorityLevel = Field(..., description="Priority level")
    estimated_hours: float = Field(
        ...,
        ge=0.0,
        description="Estimated hours to spend on this topic"
    )
    subtopics: List[str] = Field(
        default_factory=list,
        description="List of specific subtopics to cover"
    )
    resources: List[str] = Field(
        default_factory=list,
        description="List of study resources (videos, readings, practice sets)"
    )
    goals: List[str] = Field(
        default_factory=list,
        description="List of daily learning objectives for this topic"
    )
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "priority": "critical",
                "estimated_hours": 3.0,
                "subtopics": [
                    "First Law of Thermodynamics",
                    "Second Law of Thermodynamics",
                    "Entropy and Reversibility"
                ],
                "resources": [
                    "NCERT Physics Chapter 12",
                    "HC Verma: Concepts of Physics Vol 2",
                    "Video: Thermodynamics Fundamentals",
                    "Practice Set: 50 Problems"
                ],
                "goals": [
                    "Understand first law and its applications",
                    "Solve 20 numerical problems on heat engines",
                    "Master entropy calculations"
                ]
            }
        }


class ScheduleDay(BaseModel):
    """
    Complete study plan for a single day.
    
    This model represents everything planned for one day of study, including
    all topics, resources, time allocation, and progress tracking.
    
    Attributes:
        day_number: Day number in schedule (1-indexed)
        schedule_date: Calendar date for this day
        subjects: List of subjects to study this day
        topics: List of topics with details for this day
        total_hours: Total study hours planned for this day
        milestones: List of key milestones to achieve this day
        completed: Whether this day has been completed
        completion_percentage: Percentage of day's plan completed (0-100)
    
    Example:
        >>> day = ScheduleDay(
        ...     day_number=1,
        ...     date=date(2024, 1, 15),
        ...     subjects=["Physics", "Mathematics"],
        ...     topics=[DailyTopic(...)],
        ...     total_hours=5.0,
        ...     milestones=["Complete Thermodynamics basics", "Solve 30 problems"],
        ...     completed=False,
        ...     completion_percentage=0.0
        ... )
    """
    day_number: int = Field(
        ...,
        gt=0,
        description="Day number in schedule (1-indexed)"
    )
    schedule_date: date = Field(..., description="Calendar date for this day")
    subjects: List[str] = Field(
        default_factory=list,
        description="List of subjects to study this day"
    )
    topics: List[DailyTopic] = Field(
        default_factory=list,
        description="List of topics with details for this day"
    )
    total_hours: float = Field(
        ...,
        ge=0.0,
        description="Total study hours planned for this day"
    )
    milestones: List[str] = Field(
        default_factory=list,
        description="List of key milestones to achieve this day"
    )
    completed: bool = Field(
        default=False,
        description="Whether this day has been completed"
    )
    completion_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Percentage of day's plan completed (0-100)"
    )
    
    @field_validator('day_number')
    @classmethod
    def validate_day_number(cls, v: int) -> int:
        """Validate day number is positive."""
        if v <= 0:
            raise ValueError(f"Day number must be positive, got {v}")
        return v
    
    @field_validator('completion_percentage')
    @classmethod
    def validate_completion(cls, v: float) -> float:
        """Validate completion percentage is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Completion percentage must be between 0 and 100, got {v}")
        return round(v, 2)
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "day_number": 1,
                "schedule_date": "2024-01-15",
                "subjects": ["Physics", "Mathematics"],
                "topics": [
                    {
                        "topic": "Thermodynamics",
                        "subject": "Physics",
                        "priority": "critical",
                        "estimated_hours": 3.0,
                        "subtopics": ["First Law", "Second Law"],
                        "resources": ["NCERT Chapter 12"],
                        "goals": ["Understand laws of thermodynamics"]
                    }
                ],
                "total_hours": 5.0,
                "milestones": [
                    "Complete Thermodynamics fundamentals",
                    "Solve 30 practice problems",
                    "Take topic quiz"
                ],
                "completed": False,
                "completion_percentage": 0.0
            }
        }


class Schedule(BaseModel):
    """
    Complete AI-generated study schedule with all days and metadata.
    
    This is the main schedule model that contains the entire study plan from
    now until the exam date, with daily breakdowns, priority topics, and
    special days for revision and practice tests.
    
    Attributes:
        schedule_id: Unique schedule identifier
        student_id: Student identifier
        analytics_id: Analytics report ID used to generate this schedule
        exam_type: Type of exam
        exam_date: Date of the exam
        generated_date: When this schedule was generated
        total_days: Total number of study days in schedule
        daily_study_hours: Average daily study hours
        status: Schedule status (active, completed, abandoned)
        days: List of all daily schedules
        revision_days: Day numbers reserved for revision
        practice_test_days: Day numbers for full-length practice tests
        buffer_days: Day numbers kept as buffer for adjustments
        priority_topics: All topics sorted by priority
    
    Example:
        >>> schedule = Schedule(
        ...     schedule_id="schedule_123",
        ...     student_id="student_456",
        ...     analytics_id="analytics_789",
        ...     exam_type="JEE_MAIN",
        ...     exam_date=date(2024, 4, 1),
        ...     generated_date=datetime.utcnow(),
        ...     total_days=75,
        ...     daily_study_hours=5.0,
        ...     status="active",
        ...     days=[...],
        ...     revision_days=[70, 71, 72],
        ...     practice_test_days=[73, 74],
        ...     buffer_days=[25, 50],
        ...     priority_topics=[...]
        ... )
    """
    schedule_id: str = Field(..., description="Unique schedule identifier")
    student_id: str = Field(..., description="Student identifier")
    analytics_id: str = Field(
        ...,
        description="Analytics report ID used to generate this schedule"
    )
    exam_type: ExamType = Field(..., description="Type of exam")
    exam_date: date = Field(..., description="Date of the exam")
    generated_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this schedule was generated"
    )
    total_days: int = Field(
        ...,
        gt=0,
        description="Total number of study days in schedule"
    )
    daily_study_hours: float = Field(
        ...,
        ge=2.0,
        le=8.0,
        description="Average daily study hours"
    )
    status: ScheduleStatus = Field(
        default=ScheduleStatus.ACTIVE,
        description="Schedule status"
    )
    days: List[ScheduleDay] = Field(
        default_factory=list,
        description="List of all daily schedules"
    )
    revision_days: List[int] = Field(
        default_factory=list,
        description="Day numbers reserved for revision"
    )
    practice_test_days: List[int] = Field(
        default_factory=list,
        description="Day numbers for full-length practice tests"
    )
    buffer_days: List[int] = Field(
        default_factory=list,
        description="Day numbers kept as buffer for adjustments"
    )
    priority_topics: List[TopicPriority] = Field(
        default_factory=list,
        description="All topics sorted by priority"
    )
    
    @field_validator('exam_date')
    @classmethod
    def validate_exam_date(cls, v: date) -> date:
        """Validate that exam date is in the future."""
        if v <= date.today():
            raise ValueError(
                f"Exam date must be in the future. Got: {v}, Today: {date.today()}"
            )
        return v
    
    @field_validator('total_days')
    @classmethod
    def validate_total_days(cls, v: int) -> int:
        """Validate total days is positive."""
        if v <= 0:
            raise ValueError(f"Total days must be positive, got {v}")
        return v
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "schedule_id": "schedule_student456_1234567890",
                "student_id": "student_456",
                "analytics_id": "analytics_test123_student456_1234567890",
                "exam_type": "JEE_MAIN",
                "exam_date": "2024-04-01",
                "generated_date": "2024-01-15T10:30:00Z",
                "total_days": 75,
                "daily_study_hours": 5.0,
                "status": "active",
                "days": [],
                "revision_days": [70, 71, 72],
                "practice_test_days": [73, 74],
                "buffer_days": [25, 50],
                "priority_topics": []
            }
        }


class ProgressUpdate(BaseModel):
    """
    Daily progress tracking and completion data.
    
    This model captures a student's actual progress on a scheduled day,
    including what was completed, time spent, and any adjustments needed
    for future days.
    
    Attributes:
        schedule_id: Schedule identifier
        day_number: Day number being updated
        update_date: Date of the progress update
        status: Completion status (completed, partial, skipped)
        topics_completed: List of topics with completion details
        total_time_spent: Total actual study time spent (hours)
        completion_percentage: Overall completion percentage for the day (0-100)
        next_day_adjustments: Suggestions for adjusting upcoming days
    
    Example:
        >>> progress = ProgressUpdate(
        ...     schedule_id="schedule_123",
        ...     day_number=1,
        ...     date=date(2024, 1, 15),
        ...     status="partial",
        ...     topics_completed=[
        ...         {
        ...             "topic": "Thermodynamics",
        ...             "time_spent": 2.5,
        ...             "completion_percentage": 60.0,
        ...             "notes": "Need more practice on entropy"
        ...         }
        ...     ],
        ...     total_time_spent=4.0,
        ...     completion_percentage=75.0,
        ...     next_day_adjustments=["Add 1 hour for Thermodynamics completion"]
        ... )
    """
    schedule_id: str = Field(..., description="Schedule identifier")
    day_number: int = Field(
        ...,
        gt=0,
        description="Day number being updated"
    )
    update_date: date = Field(..., description="Date of the progress update")
    status: DayStatus = Field(
        ...,
        description="Completion status"
    )
    topics_completed: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of topics with completion details (topic, time_spent, completion_percentage, notes)"
    )
    total_time_spent: float = Field(
        ...,
        ge=0.0,
        description="Total actual study time spent (hours)"
    )
    completion_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall completion percentage for the day (0-100)"
    )
    next_day_adjustments: List[str] = Field(
        default_factory=list,
        description="Suggestions for adjusting upcoming days"
    )
    
    @field_validator('day_number')
    @classmethod
    def validate_day_number(cls, v: int) -> int:
        """Validate day number is positive."""
        if v <= 0:
            raise ValueError(f"Day number must be positive, got {v}")
        return v
    
    @field_validator('completion_percentage')
    @classmethod
    def validate_completion(cls, v: float) -> float:
        """Validate completion percentage is between 0 and 100."""
        if not 0.0 <= v <= 100.0:
            raise ValueError(f"Completion percentage must be between 0 and 100, got {v}")
        return round(v, 2)
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "schedule_id": "schedule_student456_1234567890",
                "day_number": 1,
                "update_date": "2024-01-15",
                "status": "partial",
                "topics_completed": [
                    {
                        "topic": "Thermodynamics",
                        "time_spent": 2.5,
                        "completion_percentage": 60.0,
                        "notes": "Completed First Law, need more time for Second Law"
                    },
                    {
                        "topic": "Calculus",
                        "time_spent": 1.5,
                        "completion_percentage": 100.0,
                        "notes": "All goals achieved"
                    }
                ],
                "total_time_spent": 4.0,
                "completion_percentage": 75.0,
                "next_day_adjustments": [
                    "Add 1 hour for Thermodynamics Second Law",
                    "Reduce Calculus time by 0.5 hours"
                ]
            }
        }


class RescheduleRequest(BaseModel):
    """
    Request to regenerate or adjust the study schedule.
    
    This model is used when the student needs to adjust their schedule due to
    missed sessions, topics taking longer than expected, low performance, or
    other reasons requiring schedule modification.
    
    Attributes:
        schedule_id: Schedule identifier to reschedule
        reason: Reason for rescheduling
        current_day: Current day number in the schedule
        notes: Optional additional notes about why rescheduling is needed
    
    Example:
        >>> reschedule = RescheduleRequest(
        ...     schedule_id="schedule_123",
        ...     reason="topic_overrun",
        ...     current_day=15,
        ...     notes="Thermodynamics took 5 extra hours, need to adjust remaining days"
        ... )
    """
    schedule_id: str = Field(
        ...,
        description="Schedule identifier to reschedule"
    )
    reason: RescheduleReason = Field(
        ...,
        description="Reason for rescheduling"
    )
    current_day: int = Field(
        ...,
        gt=0,
        description="Current day number in the schedule"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional additional notes about why rescheduling is needed"
    )
    
    @field_validator('current_day')
    @classmethod
    def validate_current_day(cls, v: int) -> int:
        """Validate current day is positive."""
        if v <= 0:
            raise ValueError(f"Current day must be positive, got {v}")
        return v
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "schedule_id": "schedule_student456_1234567890",
                "reason": "topic_overrun",
                "current_day": 15,
                "notes": "Thermodynamics took 5 extra hours due to conceptual difficulties. Need to redistribute remaining topics."
            }
        }
