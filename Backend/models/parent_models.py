"""
Parent Dashboard and Reporting Models

This module defines Pydantic models for parent-facing features including
dashboards, reports, notifications, and goal tracking.

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ChildDashboard(BaseModel):
    """Dashboard overview for a child's progress."""
    
    child_id: str = Field(..., description="Child identifier")
    child_name: str = Field(..., description="Child's name")
    overall_progress: float = Field(..., ge=0, le=100, description="Overall progress percentage")
    current_streak: int = Field(..., ge=0, description="Current study streak in days")
    hours_studied_today: float = Field(..., ge=0, description="Hours studied today")
    hours_studied_week: float = Field(..., ge=0, description="Hours studied this week")
    schedule_status: Literal["on_track", "behind", "ahead"] = Field(..., description="Schedule status")
    days_until_exam: int = Field(..., ge=0, description="Days remaining until exam")
    weak_areas: List[Dict[str, str]] = Field(default_factory=list, description="Topics needing attention")
    upcoming_tasks: List[Dict[str, str]] = Field(default_factory=list, description="Upcoming schedule items")
    recent_test_score: Optional[float] = Field(None, description="Most recent test score percentage")
    last_active: datetime = Field(..., description="Last activity timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "child_id": "child_123",
                "child_name": "Rahul Sharma",
                "overall_progress": 67.5,
                "current_streak": 5,
                "hours_studied_today": 3.5,
                "hours_studied_week": 22.0,
                "schedule_status": "on_track",
                "days_until_exam": 45,
                "weak_areas": [
                    {"subject": "Physics", "topic": "Thermodynamics", "accuracy": "45%"},
                    {"subject": "Chemistry", "topic": "Organic Chemistry", "accuracy": "52%"}
                ],
                "upcoming_tasks": [
                    {"date": "2024-01-16", "topic": "Calculus - Integration", "duration": "2 hours"},
                    {"date": "2024-01-17", "topic": "Physics - Optics", "duration": "1.5 hours"}
                ],
                "recent_test_score": 78.5,
                "last_active": "2024-01-15T18:30:00Z"
            }
        }
    )


class WeeklyReport(BaseModel):
    """Weekly progress report for a child."""
    
    child_id: str = Field(..., description="Child identifier")
    week_start: date = Field(..., description="Week start date")
    week_end: date = Field(..., description="Week end date")
    total_hours_studied: float = Field(..., ge=0, description="Total hours studied this week")
    previous_week_hours: float = Field(..., ge=0, description="Previous week hours for comparison")
    topics_completed: int = Field(..., ge=0, description="Number of topics completed")
    tests_taken: int = Field(..., ge=0, description="Number of tests taken")
    average_test_score: Optional[float] = Field(None, description="Average test score percentage")
    attendance_rate: float = Field(..., ge=0, le=100, description="Study attendance percentage")
    subject_breakdown: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Subject-wise hours and scores"
    )
    achievements: List[str] = Field(default_factory=list, description="Achievements this week")
    areas_of_concern: List[str] = Field(default_factory=list, description="Areas needing attention")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "child_id": "child_123",
                "week_start": "2024-01-08",
                "week_end": "2024-01-14",
                "total_hours_studied": 28.5,
                "previous_week_hours": 25.0,
                "topics_completed": 12,
                "tests_taken": 3,
                "average_test_score": 76.5,
                "attendance_rate": 85.7,
                "subject_breakdown": {
                    "Physics": {"hours": 10.0, "score": 72.0},
                    "Chemistry": {"hours": 9.5, "score": 78.0},
                    "Mathematics": {"hours": 9.0, "score": 80.0}
                },
                "achievements": ["7-day streak", "Completed Calculus chapter"],
                "areas_of_concern": ["Low accuracy in Thermodynamics"]
            }
        }
    )


class EmailScheduleRequest(BaseModel):
    """Request to schedule weekly email reports."""
    
    parent_id: str = Field(..., description="Parent identifier")
    child_id: str = Field(..., description="Child identifier")
    email: str = Field(..., description="Email address for reports")
    frequency: Literal["daily", "weekly", "monthly"] = Field(
        default="weekly",
        description="Report frequency"
    )
    day_of_week: Optional[int] = Field(
        None,
        ge=0,
        le=6,
        description="Day of week for weekly reports (0=Monday, 6=Sunday)"
    )
    enabled: bool = Field(default=True, description="Whether email reports are enabled")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_id": "parent_123",
                "child_id": "child_123",
                "email": "parent@example.com",
                "frequency": "weekly",
                "day_of_week": 6,
                "enabled": True
            }
        }
    )


class NotificationSettings(BaseModel):
    """Parent notification preferences."""
    
    parent_id: str = Field(..., description="Parent identifier")
    missed_days_alert: bool = Field(default=True, description="Alert when child misses 2+ days")
    daily_summary: bool = Field(default=False, description="Daily progress summary")
    test_completion: bool = Field(default=True, description="Test completion notifications")
    schedule_milestones: bool = Field(default=True, description="Schedule milestone alerts")
    weekly_report: bool = Field(default=True, description="Weekly progress report")
    low_performance_alert: bool = Field(default=True, description="Alert on low test scores")
    achievement_notifications: bool = Field(default=True, description="Achievement unlocked notifications")
    email_notifications: bool = Field(default=True, description="Enable email notifications")
    push_notifications: bool = Field(default=False, description="Enable push notifications")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_id": "parent_123",
                "missed_days_alert": True,
                "daily_summary": False,
                "test_completion": True,
                "schedule_milestones": True,
                "weekly_report": True,
                "low_performance_alert": True,
                "achievement_notifications": True,
                "email_notifications": True,
                "push_notifications": False
            }
        }
    )


class Goal(BaseModel):
    """Parent-set goal for child."""
    
    goal_id: str = Field(..., description="Goal identifier")
    child_id: str = Field(..., description="Child identifier")
    goal_type: Literal["target_score", "daily_hours", "topic_completion", "test_count"] = Field(
        ...,
        description="Type of goal"
    )
    target_value: float = Field(..., description="Target value to achieve")
    current_value: float = Field(default=0.0, description="Current progress value")
    deadline: Optional[date] = Field(None, description="Goal deadline")
    status: Literal["active", "completed", "failed", "cancelled"] = Field(
        default="active",
        description="Goal status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target_value == 0:
            return 0.0
        return min(100.0, (self.current_value / self.target_value) * 100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goal_id": "goal_123",
                "child_id": "child_123",
                "goal_type": "target_score",
                "target_value": 85.0,
                "current_value": 78.5,
                "deadline": "2024-03-31",
                "status": "active",
                "created_at": "2024-01-15T10:00:00Z",
                "completed_at": None
            }
        }
    )


class GoalRequest(BaseModel):
    """Request to create a new goal."""
    
    child_id: str = Field(..., description="Child identifier")
    goal_type: Literal["target_score", "daily_hours", "topic_completion", "test_count"] = Field(
        ...,
        description="Type of goal"
    )
    target_value: float = Field(..., gt=0, description="Target value to achieve")
    deadline: Optional[date] = Field(None, description="Goal deadline")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "child_id": "child_123",
                "goal_type": "target_score",
                "target_value": 85.0,
                "deadline": "2024-03-31"
            }
        }
    )


class GoalUpdateRequest(BaseModel):
    """Request to update a goal."""
    
    target_value: Optional[float] = Field(None, gt=0, description="New target value")
    deadline: Optional[date] = Field(None, description="New deadline")
    status: Optional[Literal["active", "completed", "failed", "cancelled"]] = Field(
        None,
        description="New status"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_value": 90.0,
                "deadline": "2024-04-15",
                "status": "active"
            }
        }
    )
