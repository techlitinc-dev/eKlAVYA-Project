"""
Schedule Router for Mentor AI Platform.

This module defines FastAPI endpoints for schedule generation, management, and
progress tracking in the Mentor AI EdTech Platform.

Endpoints:
- POST /api/schedule/generate: Generate new study schedule
- GET /api/schedule/{schedule_id}: Retrieve schedule by ID
- GET /api/schedule/student/{student_id}: Get active student schedule
- GET /api/schedule/student/{student_id}/history: Get schedule history
- POST /api/schedule/{schedule_id}/regenerate: Regenerate remaining schedule
- PUT /api/schedule/{schedule_id}: Update schedule
- DELETE /api/schedule/{schedule_id}: Delete schedule
- POST /api/schedule/progress/update: Update daily progress
- GET /api/schedule/progress/{schedule_id}: Get progress summary
- GET /api/schedule/progress/today: Get today's tasks

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, Field

# Import models
from models.schedule_models import (
    Schedule,
    ScheduleRequest,
    ProgressUpdate,
    ScheduleStatus,
    DailyTopic
)

# Import services
from services.schedule_service import (
    ScheduleService,
    ScheduleNotFoundError,
    AnalyticsNotFoundError,
    StudentNotFoundError,
    ScheduleGenerationError,
    ScheduleServiceError
)
from services.adaptive_scheduler import (
    AdaptiveScheduler,
    AdaptiveSchedulerError
)
from services.progress_tracker import (
    ProgressTracker,
    ProgressTrackerError,
    DayNotFoundError,
    TopicNotFoundError
)

# Import authentication
from middleware.auth_middleware import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/schedule",
    tags=["Schedule"]
)


# ==================== Request/Response Models ====================


class RegenerateRequest(BaseModel):
    """Request model for schedule regeneration."""
    current_day: int = Field(
        ...,
        gt=0,
        description="Current day number from which to regenerate"
    )
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "current_day": 15
            }
        }


class UpdateScheduleRequest(BaseModel):
    """Request model for schedule updates."""
    updates: Dict[str, Any] = Field(
        ...,
        description="Dictionary of fields to update"
    )
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "updates": {
                    "status": "paused",
                    "notes": "Paused due to exams"
                }
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Success message")
    
    class ConfigDict:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Schedule deleted successfully"
            }
        }


# ==================== Dependency Functions ====================


def get_schedule_service():
    """Dependency to get schedule service instance."""
    return ScheduleService()


def get_adaptive_scheduler():
    """Dependency to get adaptive scheduler instance."""
    return AdaptiveScheduler()


def get_progress_tracker():
    """Dependency to get progress tracker instance."""
    return ProgressTracker()


# ==================== Endpoints ====================


@router.post(
    "/generate",
    response_model=Schedule,
    status_code=status.HTTP_201_CREATED,
    summary="Generate study schedule",
    description="""
    Generate a personalized AI-powered study schedule for a student.
    
    This endpoint triggers the complete schedule generation pipeline:
    1. Validates schedule request parameters
    2. Fetches student analytics and performance data
    3. Loads exam syllabus and weightages
    4. Calculates topic priorities based on performance
    5. Calculates time constraints and feasibility
    6. Builds context for Gemini AI
    7. Generates schedule using Gemini Flash 1.5
    8. Validates and parses AI response
    9. Saves schedule to Firestore
    10. Returns complete schedule
    
    **Process:**
    - Synchronous operation - returns complete schedule
    - Uses AI to optimize topic ordering and time allocation
    - Considers student's weak areas and exam weightages
    
    **Requirements:**
    - Valid analytics_id (student must have taken at least one test)
    - Exam date must be in the future
    - Daily study hours must be realistic (2-8 hours)
    """,
    responses={
        201: {
            "description": "Schedule created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "schedule_id": "schedule_student123_1234567890",
                        "student_id": "student_123",
                        "exam_type": "JEE_MAIN",
                        "status": "active",
                        "start_date": "2024-01-15",
                        "exam_date": "2024-03-31",
                        "daily_study_hours": 5.0,
                        "completion_percentage": 0.0,
                        "days": []
                    }
                }
            }
        },
        400: {"description": "Invalid request data"},
        404: {"description": "Analytics or student not found"},
        500: {"description": "Schedule generation failed"}
    }
)
async def generate_schedule(
    request: ScheduleRequest,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: str = Depends(get_current_user)
) -> Schedule:
    """
    Generate personalized study schedule.
    
    Args:
        request: ScheduleRequest with student_id, analytics_id, exam details
        service: ScheduleService instance (injected dependency)
        current_user: Authenticated user ID (from JWT token)
    
    Returns:
        Complete Schedule object
    
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 404 for missing analytics/student
        HTTPException: 500 for generation failures
    """
    try:
        logger.info(
            f"Schedule generation request for student={request.student_id}, "
            f"exam={request.exam_type}, date={request.exam_date}"
        )
        
        # Generate schedule
        schedule = service.generate_schedule(request)
        
        logger.info(f"Schedule generated successfully: {schedule.schedule_id}")
        
        return schedule
        
    except ValueError as e:
        logger.warning(f"Validation error in schedule request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except AnalyticsNotFoundError as e:
        logger.warning(f"Analytics not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except StudentNotFoundError as e:
        logger.warning(f"Student not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except ScheduleGenerationError as e:
        logger.error(f"Schedule generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate schedule: {str(e)}"
        )
    
    except Exception as e:
        logger.error(f"Error generating schedule: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate schedule. Please try again later."
        )


@router.get(
    "/{schedule_id}",
    response_model=Schedule,
    summary="Get schedule by ID",
    description="""
    Retrieve a complete schedule by its unique identifier.
    
    Returns the full schedule including:
    - Schedule metadata (dates, exam type, status)
    - Daily schedule with all topics
    - Completion percentage
    - All topic details (subtopics, resources, goals)
    """,
    responses={
        200: {"description": "Schedule retrieved successfully"},
        404: {"description": "Schedule not found"}
    }
)
async def get_schedule(
    schedule_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: str = Depends(get_current_user)
) -> Schedule:
    """
    Get schedule by ID.
    
    Args:
        schedule_id: Schedule identifier
        service: ScheduleService instance
        current_user: Authenticated user ID
    
    Returns:
        Schedule object
    
    Raises:
        HTTPException: 404 if schedule not found
    """
    try:
        logger.info(f"Getting schedule: {schedule_id}")
        
        schedule = service.get_schedule(schedule_id)
        
        logger.info(f"Schedule retrieved: {schedule_id}")
        
        return schedule
        
    except ScheduleNotFoundError as e:
        logger.warning(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error getting schedule: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule. Please try again later."
        )


@router.get(
    "/student/{student_id}",
    response_model=Optional[Schedule],
    summary="Get active student schedule",
    description="""
    Get the currently active schedule for a student.
    
    Returns the student's active schedule, or null if:
    - Student has no schedules
    - All schedules are completed/abandoned
    
    **Status Filter:**
    - Default: Returns only "active" schedules
    - Use status query param to filter by status
    """,
    responses={
        200: {"description": "Schedule retrieved (or null if none active)"}
    }
)
async def get_student_schedule(
    student_id: str,
    status_filter: Optional[str] = Query(
        default="active",
        description="Filter by schedule status (active, completed, abandoned, paused)"
    ),
    service: ScheduleService = Depends(get_schedule_service),
    current_user: str = Depends(get_current_user)
) -> Optional[Schedule]:
    """
    Get active schedule for student.
    
    Args:
        student_id: Student identifier
        status_filter: Status to filter by
        service: ScheduleService instance
        current_user: Authenticated user ID
    
    Returns:
        Schedule object or None
    """
    try:
        logger.info(f"Getting student schedule: {student_id}, status={status_filter}")
        
        schedules = service.get_student_schedules(student_id, status_filter=status_filter)
        
        # Return first schedule or None
        schedule = schedules[0] if schedules else None
        
        logger.info(f"Student schedule: {'found' if schedule else 'not found'}")
        
        return schedule
        
    except Exception as e:
        logger.error(f"Error getting student schedule: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule. Please try again later."
        )


@router.get(
    "/student/{student_id}/history",
    response_model=List[Schedule],
    summary="Get schedule history",
    description="""
    Get all schedules for a student, sorted by creation date (newest first).
    
    **Filters:**
    - limit: Maximum number of schedules to return (default: 10)
    
    **Use Cases:**
    - View past schedules
    - Track schedule changes over time
    - Analyze completion rates
    """,
    responses={
        200: {"description": "Schedule history retrieved"}
    }
)
async def get_schedule_history(
    student_id: str,
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of schedules"),
    service: ScheduleService = Depends(get_schedule_service),
    current_user: str = Depends(get_current_user)
) -> List[Schedule]:
    """
    Get schedule history for student.
    
    Args:
        student_id: Student identifier
        limit: Maximum schedules to return
        service: ScheduleService instance
        current_user: Authenticated user ID
    
    Returns:
        List of Schedule objects
    """
    try:
        logger.info(f"Getting schedule history: {student_id}, limit={limit}")
        
        schedules = service.get_schedule_history(student_id, limit=limit)
        
        logger.info(f"Found {len(schedules)} schedules")
        
        return schedules
        
    except Exception as e:
        logger.error(f"Error getting schedule history: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve schedule history. Please try again later."
        )


@router.post(
    "/{schedule_id}/regenerate",
    response_model=Schedule,
    summary="Regenerate remaining schedule",
    description="""
    Regenerate the remaining portion of a schedule from a specific day.
    
    This endpoint:
    1. Fetches existing schedule and progress
    2. Identifies incomplete topics
    3. Recalculates priorities based on current progress
    4. Calculates remaining days until exam
    5. Generates new schedule using Gemini AI
    6. Merges with completed days
    7. Saves updated schedule
    
    **Use Cases:**
    - Student fell behind schedule
    - Topics took longer than expected
    - Schedule adjustments needed mid-way
    - Performance improved/declined significantly
    """,
    responses={
        200: {"description": "Schedule regenerated successfully"},
        400: {"description": "Invalid current day"},
        404: {"description": "Schedule not found"}
    }
)
async def regenerate_schedule(
    schedule_id: str,
    request: RegenerateRequest,
    scheduler: AdaptiveScheduler = Depends(get_adaptive_scheduler),
    current_user: str = Depends(get_current_user)
) -> Schedule:
    """
    Regenerate remaining schedule from current day.
    
    Args:
        schedule_id: Schedule identifier
        request: RegenerateRequest with current_day
        scheduler: AdaptiveScheduler instance
        current_user: Authenticated user ID
    
    Returns:
        Updated Schedule object
    
    Raises:
        HTTPException: 400 for invalid day
        HTTPException: 404 if schedule not found
    """
    try:
        logger.info(
            f"Regenerating schedule: {schedule_id}, from day {request.current_day}"
        )
        
        updated_schedule = scheduler.regenerate_remaining_schedule(
            schedule_id,
            request.current_day
        )
        
        logger.info(f"Schedule regenerated successfully: {schedule_id}")
        
        return updated_schedule
        
    except ValueError as e:
        logger.warning(f"Invalid regenerate request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except ScheduleNotFoundError as e:
        logger.warning(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error regenerating schedule: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to regenerate schedule. Please try again later."
        )


@router.put(
    "/{schedule_id}",
    response_model=Schedule,
    summary="Update schedule",
    description="""
    Update schedule fields.
    
    **Updatable Fields:**
    - status: Change schedule status (active, paused, completed, abandoned)
    - notes: Add/update schedule notes
    - daily_study_hours: Adjust daily study hours
    
    **Restrictions:**
    - Cannot modify completed days
    - Cannot change exam_date (regenerate instead)
    - Cannot change exam_type
    """,
    responses={
        200: {"description": "Schedule updated successfully"},
        400: {"description": "Invalid updates"},
        404: {"description": "Schedule not found"}
    }
)
async def update_schedule(
    schedule_id: str,
    request: UpdateScheduleRequest,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: str = Depends(get_current_user)
) -> Schedule:
    """
    Update schedule fields.
    
    Args:
        schedule_id: Schedule identifier
        request: UpdateScheduleRequest with updates dict
        service: ScheduleService instance
        current_user: Authenticated user ID
    
    Returns:
        Updated Schedule object
    
    Raises:
        HTTPException: 400 for invalid updates
        HTTPException: 404 if schedule not found
    """
    try:
        logger.info(f"Updating schedule: {schedule_id}, updates={list(request.updates.keys())}")
        
        updated_schedule = service.update_schedule(schedule_id, request.updates)
        
        logger.info(f"Schedule updated successfully: {schedule_id}")
        
        return updated_schedule
        
    except ValueError as e:
        logger.warning(f"Invalid update request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except ScheduleNotFoundError as e:
        logger.warning(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error updating schedule: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update schedule. Please try again later."
        )


@router.delete(
    "/{schedule_id}",
    response_model=SuccessResponse,
    summary="Delete schedule",
    description="""
    Delete a schedule (soft delete - marks as abandoned).
    
    This operation:
    - Marks schedule status as "abandoned"
    - Preserves all data for historical records
    - Does not physically delete from database
    
    **Use Cases:**
    - Student wants to start fresh schedule
    - Schedule is no longer relevant
    - Exam was postponed/cancelled
    """,
    responses={
        200: {"description": "Schedule deleted successfully"},
        404: {"description": "Schedule not found"}
    }
)
async def delete_schedule(
    schedule_id: str,
    service: ScheduleService = Depends(get_schedule_service),
    current_user: str = Depends(get_current_user)
) -> SuccessResponse:
    """
    Delete schedule (soft delete).
    
    Args:
        schedule_id: Schedule identifier
        service: ScheduleService instance
        current_user: Authenticated user ID
    
    Returns:
        Success response
    
    Raises:
        HTTPException: 404 if schedule not found
    """
    try:
        logger.info(f"Deleting schedule: {schedule_id}")
        
        service.delete_schedule(schedule_id)
        
        logger.info(f"Schedule deleted successfully: {schedule_id}")
        
        return SuccessResponse(
            success=True,
            message=f"Schedule {schedule_id} deleted successfully"
        )
        
    except ScheduleNotFoundError as e:
        logger.warning(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error deleting schedule: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete schedule. Please try again later."
        )


@router.post(
    "/progress/update",
    response_model=ProgressUpdate,
    summary="Update daily progress",
    description="""
    Update progress for a specific day in the schedule.
    
    This endpoint:
    1. Validates day exists in schedule
    2. Updates completion status for day
    3. Stores progress in Firestore (subcollection)
    4. Updates schedule completion percentage
    5. Checks if rescheduling is needed
    6. Returns updated progress
    
    **Triggers Reschedule Check:**
    - Missed 2+ consecutive days
    - Topic took 50%+ more time than estimated
    - 3+ days behind schedule
    - Practice test accuracy < 50%
    """,
    responses={
        200: {"description": "Progress updated successfully"},
        400: {"description": "Invalid progress data"},
        404: {"description": "Schedule or day not found"}
    }
)
async def update_daily_progress(
    progress: ProgressUpdate,
    tracker: ProgressTracker = Depends(get_progress_tracker),
    current_user: str = Depends(get_current_user)
) -> ProgressUpdate:
    """
    Update daily progress for a schedule day.
    
    Args:
        progress: ProgressUpdate with completion data
        tracker: ProgressTracker instance
        current_user: Authenticated user ID
    
    Returns:
        Updated ProgressUpdate object
    
    Raises:
        HTTPException: 400 for invalid data
        HTTPException: 404 if schedule/day not found
    """
    try:
        logger.info(
            f"Updating progress: schedule={progress.schedule_id}, "
            f"day={progress.day_number}"
        )
        
        updated_progress = tracker.update_daily_progress(
            progress.schedule_id,
            progress.day_number,
            progress
        )
        
        logger.info(
            f"Progress updated: {progress.completion_percentage}% complete"
        )
        
        return updated_progress
        
    except ValueError as e:
        logger.warning(f"Invalid progress data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except (ScheduleNotFoundError, DayNotFoundError) as e:
        logger.warning(f"Schedule/day not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update progress. Please try again later."
        )


@router.get(
    "/progress/{schedule_id}",
    response_model=Dict[str, Any],
    summary="Get progress summary",
    description="""
    Get comprehensive progress summary for a schedule.
    
    **Returns:**
    - Total days completed
    - Total topics completed
    - Total hours studied
    - Completion percentage
    - Days ahead/behind schedule
    - Average daily study time
    - Current study streak
    - Days until exam
    
    **Use Cases:**
    - Dashboard overview
    - Progress tracking
    - Performance analytics
    """,
    responses={
        200: {"description": "Progress summary retrieved"}
    }
)
async def get_progress_summary(
    schedule_id: str,
    tracker: ProgressTracker = Depends(get_progress_tracker),
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get progress summary for schedule.
    
    Args:
        schedule_id: Schedule identifier
        tracker: ProgressTracker instance
        current_user: Authenticated user ID
    
    Returns:
        Progress summary dictionary
    """
    try:
        logger.info(f"Getting progress summary: {schedule_id}")
        
        summary = tracker.get_progress_summary(schedule_id)
        
        logger.info(
            f"Progress summary: {summary['completion_percentage']}% complete"
        )
        
        return summary
        
    except ScheduleNotFoundError as e:
        logger.warning(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error getting progress summary: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get progress summary. Please try again later."
        )


@router.get(
    "/progress/today",
    response_model=List[Dict[str, Any]],
    summary="Get today's tasks",
    description="""
    Get tasks scheduled for today.
    
    **Returns:**
    For each topic scheduled today:
    - topic: Topic name
    - subject: Subject name
    - estimated_hours: Time needed
    - subtopics: List of subtopics
    - resources: Recommended resources
    - goals: Daily learning goals
    - priority: Priority level
    - difficulty: Difficulty level
    
    **Use Cases:**
    - Daily task view
    - Study planner
    - Mobile app home screen
    """,
    responses={
        200: {"description": "Today's tasks retrieved"}
    }
)
async def get_today_tasks(
    schedule_id: str = Query(..., description="Schedule identifier"),
    tracker: ProgressTracker = Depends(get_progress_tracker),
    current_user: str = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Get today's tasks for schedule.
    
    Args:
        schedule_id: Schedule identifier
        tracker: ProgressTracker instance
        current_user: Authenticated user ID
    
    Returns:
        List of task dictionaries
    """
    try:
        logger.info(f"Getting today's tasks: {schedule_id}")
        
        tasks = tracker.get_today_tasks(schedule_id)
        
        logger.info(f"Found {len(tasks)} tasks for today")
        
        return tasks
        
    except ScheduleNotFoundError as e:
        logger.warning(f"Schedule not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error getting today's tasks: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get today's tasks. Please try again later."
        )
