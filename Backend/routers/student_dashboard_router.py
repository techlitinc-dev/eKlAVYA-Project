"""
Student Dashboard Router

This module defines FastAPI endpoints for student-facing features including
daily plans, practice modes, doubts, bookmarks, and performance insights.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query, status

from models.student_models import (
    TodaysPlan,
    TopicResources,
    QuickPracticeRequest,
    QuickPracticeResponse,
    Doubt,
    DoubtRequest,
    DoubtExplanation,
    RevisionItem,
    PerformanceInsights,
    Bookmark,
    BookmarkRequest,
    PeerComparison
)
from services.student_dashboard_service import StudentDashboardService
from middleware.testing_auth import get_current_user_testing as get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/student",
    tags=["Student Dashboard"]
)


def get_student_service():
    """Dependency to get student dashboard service."""
    return StudentDashboardService()


@router.get(
    "/today/{student_id}",
    response_model=TodaysPlan,
    summary="Get today's study plan",
    description="Get personalized study plan for today with pending items and motivational message"
)
async def get_todays_plan(
    student_id: str,
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Get today's study plan for a student."""
    try:
        plan = service.get_todays_plan(student_id)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting today's plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get today's plan"
        )


@router.get(
    "/topic/{topic_id}/resources",
    response_model=TopicResources,
    summary="Get topic resources",
    description="Get curated learning resources for a specific topic"
)
async def get_topic_resources(
    topic_id: str,
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Get resources for a specific topic."""
    try:
        resources = service.get_topic_resources(topic_id)
        return resources
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting topic resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get topic resources"
        )


@router.post(
    "/practice/quick",
    response_model=QuickPracticeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate quick practice",
    description="Generate a quick practice session based on duration and focus area"
)
async def generate_quick_practice(
    request: QuickPracticeRequest,
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Generate quick practice session."""
    try:
        practice = service.generate_quick_practice(request)
        return practice
    except Exception as e:
        logger.error(f"Error generating quick practice: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quick practice"
        )


@router.post(
    "/doubts",
    response_model=Doubt,
    status_code=status.HTTP_201_CREATED,
    summary="Create doubt",
    description="Save a doubt/question for later explanation"
)
async def create_doubt(
    request: DoubtRequest,
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Create a new doubt."""
    try:
        doubt = service.create_doubt(request)
        return doubt
    except Exception as e:
        logger.error(f"Error creating doubt: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create doubt"
        )


@router.get(
    "/doubts/{doubt_id}/explanation",
    response_model=DoubtExplanation,
    summary="Get doubt explanation",
    description="Get AI-generated detailed explanation for a doubt"
)
async def get_doubt_explanation(
    doubt_id: str,
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Get AI-generated explanation for a doubt."""
    try:
        explanation = service.get_doubt_explanation(doubt_id)
        return explanation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting doubt explanation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get doubt explanation"
        )


@router.get(
    "/revision/due",
    response_model=List[RevisionItem],
    summary="Get revision items",
    description="Get topics due for revision based on spaced repetition"
)
async def get_revision_due(
    student_id: str = Query(..., description="Student identifier"),
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Get topics due for revision."""
    try:
        items = service.get_revision_due(student_id)
        return items
    except Exception as e:
        logger.error(f"Error getting revision items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get revision items"
        )


@router.post(
    "/revision/mark-complete/{topic_id}",
    summary="Mark revision complete",
    description="Mark a topic revision as complete"
)
async def mark_revision_complete(
    topic_id: str,
    student_id: str = Query(..., description="Student identifier"),
    current_user: str = Depends(get_current_user)
):
    """Mark a topic revision as complete."""
    # This would update the revision tracking
    return {
        "success": True,
        "message": f"Revision marked complete for topic: {topic_id}"
    }


@router.post(
    "/bookmarks",
    response_model=Bookmark,
    status_code=status.HTTP_201_CREATED,
    summary="Create bookmark",
    description="Bookmark a question, topic, or resource for later"
)
async def create_bookmark(
    request: BookmarkRequest,
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Create a bookmark."""
    try:
        bookmark = service.create_bookmark(request)
        return bookmark
    except Exception as e:
        logger.error(f"Error creating bookmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bookmark"
        )


@router.get(
    "/bookmarks",
    response_model=List[Bookmark],
    summary="Get bookmarks",
    description="Get all bookmarks for a student"
)
async def get_bookmarks(
    student_id: str = Query(..., description="Student identifier"),
    service: StudentDashboardService = Depends(get_student_service),
    current_user: str = Depends(get_current_user)
):
    """Get all bookmarks for a student."""
    try:
        bookmarks = service.get_bookmarks(student_id)
        return bookmarks
    except Exception as e:
        logger.error(f"Error getting bookmarks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bookmarks"
        )


@router.delete(
    "/bookmarks/{bookmark_id}",
    summary="Delete bookmark",
    description="Delete a bookmark"
)
async def delete_bookmark(
    bookmark_id: str,
    current_user: str = Depends(get_current_user)
):
    """Delete a bookmark."""
    # This would delete from Firestore
    return {
        "success": True,
        "message": f"Bookmark deleted: {bookmark_id}"
    }


@router.get(
    "/insights/{student_id}",
    response_model=PerformanceInsights,
    summary="Get performance insights",
    description="Get AI-powered performance insights and recommendations"
)
async def get_performance_insights(
    student_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get performance insights for a student."""
    # This would analyze performance data and generate insights
    insights = PerformanceInsights(
        student_id=student_id,
        best_time_of_day="Morning (9 AM - 12 PM)",
        average_time_per_question={
            "Physics": 2.5,
            "Chemistry": 2.2,
            "Mathematics": 3.0
        },
        accuracy_trend="improving",
        accuracy_change=5.2,
        predicted_score=78.5,
        confidence_interval={"lower": 75.0, "upper": 82.0},
        strengths=["Calculus", "Organic Chemistry"],
        weaknesses=["Thermodynamics", "Electromagnetism"],
        recommendations=[
            "Focus more on Thermodynamics",
            "Practice more numerical problems in Physics"
        ]
    )
    return insights


@router.get(
    "/compare/percentile",
    response_model=PeerComparison,
    summary="Get peer comparison",
    description="Get anonymous peer comparison and percentile ranking"
)
async def get_peer_comparison(
    student_id: str = Query(..., description="Student identifier"),
    current_user: str = Depends(get_current_user)
):
    """Get peer comparison data."""
    # This would calculate percentiles from all students
    comparison = PeerComparison(
        student_id=student_id,
        overall_percentile=78.5,
        subject_percentiles={
            "Physics": 75.0,
            "Chemistry": 82.0,
            "Mathematics": 79.0
        },
        rank_range="2000-2500",
        total_students=10000,
        performance_category="top_25"
    )
    return comparison
