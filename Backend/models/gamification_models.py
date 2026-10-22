"""
Gamification Models

This module defines Pydantic models for gamification features including
achievements, badges, daily challenges, streaks, and points.

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field, ConfigDict


class Achievement(BaseModel):
    """Student achievement/badge."""
    
    achievement_id: str = Field(..., description="Achievement identifier")
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="Achievement description")
    icon: str = Field(..., description="Achievement icon URL or emoji")
    category: Literal["streak", "questions", "tests", "topics", "special"] = Field(
        ...,
        description="Achievement category"
    )
    points: int = Field(..., ge=0, description="Points awarded")
    rarity: Literal["common", "rare", "epic", "legendary"] = Field(
        ...,
        description="Achievement rarity"
    )
    requirement: str = Field(..., description="Requirement to unlock")
    unlocked: bool = Field(default=False, description="Whether unlocked by student")
    unlocked_at: Optional[datetime] = Field(None, description="Unlock timestamp")
    progress: float = Field(default=0.0, ge=0, le=100, description="Progress percentage")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "achievement_id": "ach_7day_streak",
                "name": "Week Warrior",
                "description": "Study for 7 consecutive days",
                "icon": "🔥",
                "category": "streak",
                "points": 100,
                "rarity": "rare",
                "requirement": "7-day study streak",
                "unlocked": True,
                "unlocked_at": "2024-01-15T10:00:00Z",
                "progress": 100.0
            }
        }
    )


class StudentAchievements(BaseModel):
    """All achievements for a student."""
    
    student_id: str = Field(..., description="Student identifier")
    total_points: int = Field(..., ge=0, description="Total points earned")
    unlocked_count: int = Field(..., ge=0, description="Number of unlocked achievements")
    total_count: int = Field(..., ge=0, description="Total available achievements")
    achievements: List[Achievement] = Field(..., description="List of all achievements")
    recent_unlocks: List[Achievement] = Field(
        default_factory=list,
        description="Recently unlocked achievements"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "total_points": 850,
                "unlocked_count": 8,
                "total_count": 25,
                "achievements": [],
                "recent_unlocks": []
            }
        }
    )


class DailyChallenge(BaseModel):
    """Daily challenge question."""
    
    challenge_id: str = Field(..., description="Challenge identifier")
    challenge_date: date = Field(..., description="Challenge date")
    question: Dict = Field(..., description="Challenge question")
    difficulty: Literal["easy", "medium", "hard"] = Field(..., description="Difficulty level")
    points: int = Field(..., ge=0, description="Points for correct answer")
    bonus_points: int = Field(default=0, ge=0, description="Bonus points for streak")
    time_limit: int = Field(..., ge=0, description="Time limit in seconds")
    subject: str = Field(..., description="Subject")
    topic: str = Field(..., description="Topic")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "challenge_id": "challenge_20240115",
                "challenge_date": "2024-01-15",
                "question": {
                    "question_id": "q_daily_123",
                    "question_text": "What is the derivative of sin(2x)?",
                    "options": {"A": "cos(2x)", "B": "2cos(2x)", "C": "-2sin(2x)", "D": "2sin(2x)"},
                    "correct_answer": "B"
                },
                "difficulty": "medium",
                "points": 50,
                "bonus_points": 10,
                "time_limit": 180,
                "subject": "Mathematics",
                "topic": "Calculus"
            }
        }
    )


class DailyChallengeSubmission(BaseModel):
    """Submission for daily challenge."""
    
    student_id: str = Field(..., description="Student identifier")
    challenge_id: str = Field(..., description="Challenge identifier")
    answer: str = Field(..., description="Student's answer")
    time_taken: int = Field(..., ge=0, description="Time taken in seconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "challenge_id": "challenge_20240115",
                "answer": "B",
                "time_taken": 120
            }
        }
    )


class DailyChallengeResult(BaseModel):
    """Result of daily challenge submission."""
    
    challenge_id: str = Field(..., description="Challenge identifier")
    correct: bool = Field(..., description="Whether answer was correct")
    points_earned: int = Field(..., ge=0, description="Points earned")
    correct_answer: str = Field(..., description="Correct answer")
    explanation: str = Field(..., description="Explanation")
    rank: Optional[int] = Field(None, description="Rank on leaderboard")
    total_participants: int = Field(..., ge=0, description="Total participants today")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "challenge_id": "challenge_20240115",
                "correct": True,
                "points_earned": 60,
                "correct_answer": "B",
                "explanation": "Using chain rule: d/dx[sin(2x)] = cos(2x) × 2 = 2cos(2x)",
                "rank": 42,
                "total_participants": 150
            }
        }
    )


class Leaderboard(BaseModel):
    """Daily challenge leaderboard."""
    
    leaderboard_date: date = Field(..., description="Leaderboard date")
    entries: List[Dict[str, Any]] = Field(..., description="Leaderboard entries")
    student_rank: Optional[int] = Field(None, description="Current student's rank")
    total_participants: int = Field(..., ge=0, description="Total participants")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "leaderboard_date": "2024-01-15",
                "entries": [
                    {"rank": 1, "student_name": "Student A", "points": 60, "time": 95},
                    {"rank": 2, "student_name": "Student B", "points": 60, "time": 102},
                    {"rank": 3, "student_name": "Student C", "points": 50, "time": 85}
                ],
                "student_rank": 42,
                "total_participants": 150
            }
        }
    )


class StreakInfo(BaseModel):
    """Student streak information."""
    
    student_id: str = Field(..., description="Student identifier")
    current_streak: int = Field(..., ge=0, description="Current streak in days")
    longest_streak: int = Field(..., ge=0, description="Longest streak ever")
    streak_protection_available: bool = Field(
        default=False,
        description="Whether streak protection is available"
    )
    last_activity_date: date = Field(..., description="Last activity date")
    streak_milestones: List[int] = Field(
        default_factory=list,
        description="Streak milestones achieved"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "current_streak": 12,
                "longest_streak": 15,
                "streak_protection_available": True,
                "last_activity_date": "2024-01-15",
                "streak_milestones": [7, 10]
            }
        }
    )


class PointsHistory(BaseModel):
    """Points earning history."""
    
    student_id: str = Field(..., description="Student identifier")
    total_points: int = Field(..., ge=0, description="Total points earned")
    points_today: int = Field(..., ge=0, description="Points earned today")
    points_this_week: int = Field(..., ge=0, description="Points earned this week")
    points_this_month: int = Field(..., ge=0, description="Points earned this month")
    history: List[Dict[str, Any]] = Field(..., description="Points history entries")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "student_id": "student_123",
                "total_points": 2450,
                "points_today": 120,
                "points_this_week": 680,
                "points_this_month": 2450,
                "history": [
                    {
                        "date": "2024-01-15",
                        "activity": "Completed topic",
                        "points": 50,
                        "description": "Thermodynamics"
                    },
                    {
                        "date": "2024-01-15",
                        "activity": "Daily challenge",
                        "points": 60,
                        "description": "Correct answer"
                    }
                ]
            }
        }
    )
