"""
Gamification Router

This module defines FastAPI endpoints for gamification features including
achievements, daily challenges, streaks, and points.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import List
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Query, status

from models.gamification_models import (
    Achievement,
    StudentAchievements,
    DailyChallenge,
    DailyChallengeSubmission,
    DailyChallengeResult,
    Leaderboard,
    StreakInfo,
    PointsHistory
)
from middleware.testing_auth import get_current_user_testing as get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/gamification",
    tags=["Gamification"]
)


@router.get(
    "/achievements",
    response_model=StudentAchievements,
    summary="Get achievements",
    description="Get all achievements for a student with unlock status"
)
async def get_achievements(
    student_id: str = Query(..., description="Student identifier"),
    current_user: str = Depends(get_current_user)
):
    """Get all achievements for a student."""
    # Mock data - would fetch from database
    achievements = StudentAchievements(
        student_id=student_id,
        total_points=850,
        unlocked_count=8,
        total_count=25,
        achievements=[
            Achievement(
                achievement_id="ach_7day_streak",
                name="Week Warrior",
                description="Study for 7 consecutive days",
                icon="🔥",
                category="streak",
                points=100,
                rarity="rare",
                requirement="7-day study streak",
                unlocked=True,
                progress=100.0
            ),
            Achievement(
                achievement_id="ach_100_questions",
                name="Century",
                description="Solve 100 questions",
                icon="💯",
                category="questions",
                points=150,
                rarity="epic",
                requirement="100 questions solved",
                unlocked=False,
                progress=75.0
            )
        ],
        recent_unlocks=[]
    )
    return achievements


@router.post(
    "/achievements/claim/{achievement_id}",
    summary="Claim achievement",
    description="Claim an unlocked achievement"
)
async def claim_achievement(
    achievement_id: str,
    student_id: str = Query(..., description="Student identifier"),
    current_user: str = Depends(get_current_user)
):
    """Claim an unlocked achievement."""
    return {
        "success": True,
        "message": f"Achievement claimed: {achievement_id}",
        "points_earned": 100
    }


@router.get(
    "/challenge/daily",
    response_model=DailyChallenge,
    summary="Get daily challenge",
    description="Get today's daily challenge question"
)
async def get_daily_challenge(
    current_user: str = Depends(get_current_user)
):
    """Get today's daily challenge."""
    challenge = DailyChallenge(
        challenge_id=f"challenge_{date.today().isoformat()}",
        date=date.today(),
        question={
            "question_id": "q_daily_123",
            "question_text": "What is the derivative of sin(2x)?",
            "options": {
                "A": "cos(2x)",
                "B": "2cos(2x)",
                "C": "-2sin(2x)",
                "D": "2sin(2x)"
            },
            "correct_answer": "B"
        },
        difficulty="medium",
        points=50,
        bonus_points=10,
        time_limit=180,
        subject="Mathematics",
        topic="Calculus"
    )
    return challenge


@router.post(
    "/challenge/daily/submit",
    response_model=DailyChallengeResult,
    summary="Submit daily challenge",
    description="Submit answer for today's daily challenge"
)
async def submit_daily_challenge(
    submission: DailyChallengeSubmission,
    current_user: str = Depends(get_current_user)
):
    """Submit daily challenge answer."""
    # Check answer and calculate points
    correct = submission.answer.upper() == "B"
    points = 60 if correct else 0
    
    result = DailyChallengeResult(
        challenge_id=submission.challenge_id,
        correct=correct,
        points_earned=points,
        correct_answer="B",
        explanation="Using chain rule: d/dx[sin(2x)] = cos(2x) × 2 = 2cos(2x)",
        rank=42 if correct else None,
        total_participants=150
    )
    return result


@router.get(
    "/challenge/leaderboard",
    response_model=Leaderboard,
    summary="Get challenge leaderboard",
    description="Get daily challenge leaderboard"
)
async def get_challenge_leaderboard(
    challenge_date: date = Query(None, description="Challenge date (defaults to today)"),
    current_user: str = Depends(get_current_user)
):
    """Get daily challenge leaderboard."""
    if challenge_date is None:
        challenge_date = date.today()
    
    leaderboard = Leaderboard(
        date=challenge_date,
        entries=[
            {"rank": 1, "student_name": "Student A", "points": 60, "time": 95},
            {"rank": 2, "student_name": "Student B", "points": 60, "time": 102},
            {"rank": 3, "student_name": "Student C", "points": 50, "time": 85}
        ],
        student_rank=42,
        total_participants=150
    )
    return leaderboard


@router.get(
    "/streak",
    response_model=StreakInfo,
    summary="Get streak info",
    description="Get student's study streak information"
)
async def get_streak_info(
    student_id: str = Query(..., description="Student identifier"),
    current_user: str = Depends(get_current_user)
):
    """Get streak information for a student."""
    streak = StreakInfo(
        student_id=student_id,
        current_streak=12,
        longest_streak=15,
        streak_protection_available=True,
        last_activity_date=date.today(),
        streak_milestones=[7, 10]
    )
    return streak


@router.get(
    "/points/history",
    response_model=PointsHistory,
    summary="Get points history",
    description="Get points earning history for a student"
)
async def get_points_history(
    student_id: str = Query(..., description="Student identifier"),
    current_user: str = Depends(get_current_user)
):
    """Get points history for a student."""
    history = PointsHistory(
        student_id=student_id,
        total_points=2450,
        points_today=120,
        points_this_week=680,
        points_this_month=2450,
        history=[
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
    )
    return history
