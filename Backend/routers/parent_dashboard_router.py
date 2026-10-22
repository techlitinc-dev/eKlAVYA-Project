"""
Parent Dashboard Router

This module defines FastAPI endpoints for parent-facing features including
dashboards, reports, notifications, and goal tracking.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import List
from datetime import date

from fastapi import APIRouter, HTTPException, Depends, Query, status

from models.parent_models import (
    ChildDashboard,
    WeeklyReport,
    EmailScheduleRequest,
    NotificationSettings,
    Goal,
    GoalRequest,
    GoalUpdateRequest
)
from services.parent_dashboard_service import ParentDashboardService
from middleware.testing_auth import get_current_user_testing as get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/parent",
    tags=["Parent Dashboard"]
)


def get_parent_service():
    """Dependency to get parent dashboard service."""
    return ParentDashboardService()


@router.get(
    "/dashboard/{child_id}",
    response_model=ChildDashboard,
    summary="Get child dashboard",
    description="Get comprehensive dashboard overview for a child's progress"
)
async def get_child_dashboard(
    child_id: str,
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Get dashboard overview for a child."""
    try:
        dashboard = service.get_child_dashboard(child_id)
        return dashboard
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard"
        )


@router.get(
    "/reports/weekly/{child_id}",
    response_model=WeeklyReport,
    summary="Get weekly progress report",
    description="Get detailed weekly progress report for a child"
)
async def get_weekly_report(
    child_id: str,
    week_start: date = Query(None, description="Week start date (defaults to current week)"),
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Get weekly progress report for a child."""
    try:
        report = service.get_weekly_report(child_id, week_start)
        return report
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting weekly report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get weekly report"
        )


@router.post(
    "/reports/email-schedule",
    status_code=status.HTTP_201_CREATED,
    summary="Schedule email reports",
    description="Schedule automated email reports for parent"
)
async def schedule_email_reports(
    request: EmailScheduleRequest,
    current_user: str = Depends(get_current_user)
):
    """Schedule automated email reports."""
    # This would integrate with an email service
    return {
        "success": True,
        "message": f"Email reports scheduled for {request.email}",
        "frequency": request.frequency
    }


@router.get(
    "/notifications/settings",
    response_model=NotificationSettings,
    summary="Get notification settings",
    description="Get notification preferences for parent"
)
async def get_notification_settings(
    parent_id: str = Query(..., description="Parent identifier"),
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Get notification settings for a parent."""
    try:
        settings = service.get_notification_settings(parent_id)
        return settings
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notification settings"
        )


@router.put(
    "/notifications/settings",
    response_model=NotificationSettings,
    summary="Update notification settings",
    description="Update notification preferences for parent"
)
async def update_notification_settings(
    settings: NotificationSettings,
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Update notification settings for a parent."""
    try:
        updated_settings = service.update_notification_settings(
            settings.parent_id,
            settings
        )
        return updated_settings
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )


@router.post(
    "/goals/{child_id}",
    response_model=Goal,
    status_code=status.HTTP_201_CREATED,
    summary="Create goal",
    description="Create a new goal for a child"
)
async def create_goal(
    child_id: str,
    request: GoalRequest,
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Create a new goal for a child."""
    try:
        # Ensure child_id matches
        request.child_id = child_id
        goal = service.create_goal(current_user, request)
        return goal
    except Exception as e:
        logger.error(f"Error creating goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create goal"
        )


@router.get(
    "/goals/{child_id}",
    response_model=List[Goal],
    summary="Get goals",
    description="Get all goals for a child"
)
async def get_goals(
    child_id: str,
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Get all goals for a child."""
    try:
        goals = service.get_goals(child_id)
        return goals
    except Exception as e:
        logger.error(f"Error getting goals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get goals"
        )


@router.put(
    "/goals/{child_id}/{goal_id}",
    response_model=Goal,
    summary="Update goal",
    description="Update an existing goal"
)
async def update_goal(
    child_id: str,
    goal_id: str,
    updates: GoalUpdateRequest,
    service: ParentDashboardService = Depends(get_parent_service),
    current_user: str = Depends(get_current_user)
):
    """Update an existing goal."""
    try:
        goal = service.update_goal(goal_id, updates)
        return goal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating goal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update goal"
        )
