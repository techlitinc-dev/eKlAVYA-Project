"""
Exam Selection Router Module

This module defines FastAPI endpoints for exam selection and onboarding status
tracking in the Mentor AI EdTech Platform. It handles JEE/NEET exam selection,
diagnostic test scheduling, and onboarding completion tracking.

Endpoints:
- GET /exams/available: List available exams with dates
- POST /exam/select: Select exam and schedule diagnostic test
- GET /exam/preferences: Get exam selection and preferences
- PUT /exam/preferences: Update subject preferences
- GET /status: Get onboarding completion status

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Query, Depends

from models.exam_models import (
    ExamSelectionRequest,
    ExamSelectionResponse,
    AvailableExamsResponse
)
from services.exam_service import ExamService
from services.preferences_service import PreferencesService
from services.child_service import ChildService
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/onboarding",
    tags=["Onboarding - Exam Selection"]
)


@router.get(
    "/exams/available",
    response_model=AvailableExamsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get available exams",
    description="""
    List all available competitive exams with their dates and subjects.
    
    This endpoint provides information about JEE (Main & Advanced) and NEET
    exams, including available exam dates and subject requirements.
    
    **No Authentication Required** - This is a public endpoint for browsing
    available exam options before registration.
    
    **Available Exams:**
    - **JEE Main**: Physics, Chemistry, Mathematics (January 15 & April 15)
    - **JEE Advanced**: Physics, Chemistry, Mathematics (May 25)
    - **NEET**: Physics, Chemistry, Biology (May 5)
    
    **Returns:**
    - 200: List of available exams with dates and subjects
    - 500: Internal server error
    
    **Example Response:**
    ```json
    {
        "exams": [
            {
                "exam_type": "JEE_MAIN",
                "exam_name": "JEE Main",
                "available_dates": ["2025-01-15", "2025-04-15"],
                "subjects": ["Physics", "Chemistry", "Mathematics"]
            },
            {
                "exam_type": "NEET",
                "exam_name": "NEET",
                "available_dates": ["2025-05-05"],
                "subjects": ["Physics", "Chemistry", "Biology"]
            }
        ]
    }
    ```
    """
)
async def get_available_exams() -> AvailableExamsResponse:
    """
    Retrieve list of available competitive exams.
    
    Returns:
        AvailableExamsResponse: List of available exams with dates and subjects
    
    Raises:
        HTTPException: 500 if retrieval fails
    
    Example:
        Response:
        ```json
        {
            "exams": [
                {
                    "exam_type": "JEE_MAIN",
                    "exam_name": "JEE Main",
                    "available_dates": ["2025-01-15", "2025-04-15"],
                    "subjects": ["Physics", "Chemistry", "Mathematics"]
                }
            ]
        }
        ```
    """
    try:
        logger.info("Retrieving available exams")
        
        # Call service layer to get available exams
        result = ExamService.get_available_exams()
        
        logger.info(f"Retrieved {len(result.exams)} available exams")
        
        return result
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error retrieving available exams: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available exams. Please try again later."
        )


@router.post(
    "/exam/select",
    response_model=ExamSelectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Select exam and schedule diagnostic test",
    description="""
    Select target exam with date and subject preferences, and automatically
    schedule a diagnostic test.
    
    This endpoint allows parents to choose the target competitive exam for
    their child and set subject preference weightages. A diagnostic test
    is automatically created and scheduled for tomorrow.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Child profile must exist (child_id required)
    - Child must belong to the authenticated parent
    - Exam date must be in the future
    - Subject preferences must sum to exactly 100
    
    **Subject Preferences:**
    - For JEE: {"Physics": int, "Chemistry": int, "Mathematics": int}
    - For NEET: {"Physics": int, "Chemistry": int, "Biology": int}
    - Weightages must sum to 100 (e.g., 40 + 30 + 30 = 100)
    
    **Diagnostic Test:**
    - Automatically scheduled for tomorrow
    - Duration: 180 minutes (3 hours)
    - Total questions: 200
    - Status: "scheduled"
    
    **Returns:**
    - 201: Exam selected and diagnostic test scheduled
    - 400: Invalid exam date or subject preferences
    - 404: Child profile not found
    - 403: Child doesn't belong to parent
    - 500: Internal server error
    
    **Example Request:**
    ```json
    {
        "exam_type": "JEE_MAIN",
        "exam_date": "2025-04-15T00:00:00Z",
        "subject_preferences": {
            "Physics": 40,
            "Chemistry": 30,
            "Mathematics": 30
        }
    }
    ```
    """
)
async def select_exam(
    request: ExamSelectionRequest,
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)"),
    child_id: str = Query(..., description="Child ID for exam selection"),
    current_user: str = Depends(get_current_user)
) -> ExamSelectionResponse:
    """
    Select exam and create diagnostic test for a child.
    
    Args:
        request: ExamSelectionRequest with exam type, date, and preferences
        parent_id: Unique identifier for the parent (from query param)
        child_id: Unique identifier for the child (from query param)
    
    Returns:
        ExamSelectionResponse: Exam selection with diagnostic test details
    
    Raises:
        HTTPException: 404 if child not found
        HTTPException: 403 if child doesn't belong to parent
        HTTPException: 400 if invalid date or preferences
        HTTPException: 500 if selection fails
    
    Example:
        Request:
        ```json
        {
            "exam_type": "NEET",
            "exam_date": "2025-05-05T00:00:00Z",
            "subject_preferences": {
                "Physics": 35,
                "Chemistry": 35,
                "Biology": 30
            }
        }
        ```
        
        Response:
        ```json
        {
            "child_id": "child_abc123",
            "exam_type": "NEET",
            "exam_date": "2025-05-05T00:00:00Z",
            "subject_preferences": {
                "Physics": 35,
                "Chemistry": 35,
                "Biology": 30
            },
            "days_until_exam": 162,
            "diagnostic_test_id": "test_def456",
            "created_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Selecting exam for child {child_id}, parent {parent_id}")
        
        # Call service layer to select exam
        # Service will verify child ownership and create diagnostic test
        result = ExamService.select_exam(
            child_id=child_id,
            parent_id=parent_id,
            selection=request
        )
        
        logger.info(f"Exam selected successfully for child {child_id}, diagnostic test: {result.diagnostic_test_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error selecting exam for child {child_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to select exam. Please try again later."
        )


@router.get(
    "/exam/preferences",
    response_model=ExamSelectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get exam selection",
    description="""
    Retrieve exam selection and subject preferences for a child.
    
    This endpoint returns the child's selected exam type, target exam date,
    subject preference weightages, days until exam, and diagnostic test ID.
    
    **Requirements:**
    - Child ID must be provided
    - Exam selection must exist for this child
    
    **Returns:**
    - 200: Exam selection retrieved successfully
    - 404: Exam selection not found for this child
    - 500: Internal server error
    
    **Use Cases:**
    - Display selected exam in dashboard
    - Show countdown to exam date
    - Display subject focus preferences
    - Link to diagnostic test
    
    **Example Response:**
    ```json
    {
        "child_id": "child_abc123",
        "exam_type": "JEE_MAIN",
        "exam_date": "2025-01-15T00:00:00Z",
        "subject_preferences": {
            "Physics": 40,
            "Chemistry": 30,
            "Mathematics": 30
        },
        "days_until_exam": 52,
        "diagnostic_test_id": "test_xyz789",
        "created_at": "2024-01-10T08:00:00Z"
    }
    ```
    """
)
async def get_exam_selection(
    child_id: str = Query(..., description="Child ID to retrieve exam selection for")
) -> ExamSelectionResponse:
    """
    Retrieve exam selection for a child.
    
    Args:
        child_id: Unique identifier for the child (from query param)
    
    Returns:
        ExamSelectionResponse: Exam selection with preferences and diagnostic test ID
    
    Raises:
        HTTPException: 404 if exam selection not found
        HTTPException: 500 if retrieval fails
    
    Example:
        Response:
        ```json
        {
            "child_id": "child_123",
            "exam_type": "NEET",
            "exam_date": "2025-05-05T00:00:00Z",
            "subject_preferences": {
                "Physics": 35,
                "Chemistry": 35,
                "Biology": 30
            },
            "days_until_exam": 162,
            "diagnostic_test_id": "test_456",
            "created_at": "2024-01-10T08:00:00Z"
        }
        ```
    """
    try:
        logger.info(f"Retrieving exam selection for child: {child_id}")
        
        # Call service layer to get exam selection
        result = ExamService.get_exam_selection(child_id=child_id)
        
        logger.info(f"Exam selection retrieved successfully for child: {child_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error retrieving exam selection for child {child_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exam selection. Please try again later."
        )


@router.put(
    "/exam/preferences",
    response_model=ExamSelectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update subject preferences",
    description="""
    Update subject preference weightages for a child's exam selection.
    
    This endpoint allows parents to adjust how much focus should be given
    to each subject in the study plan and content recommendations.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Child must belong to authenticated parent
    - Exam selection must exist for this child
    - Subject preferences must sum to exactly 100
    
    **Subject Preferences Format:**
    - For JEE: {"Physics": int, "Chemistry": int, "Mathematics": int}
    - For NEET: {"Physics": int, "Chemistry": int, "Biology": int}
    - Weightages must sum to 100
    
    **Returns:**
    - 200: Subject preferences updated successfully
    - 400: Invalid preferences (don't sum to 100 or wrong subjects)
    - 403: Child doesn't belong to parent
    - 404: Exam selection not found
    - 500: Internal server error
    
    **Example Request:**
    ```json
    {
        "Physics": 50,
        "Chemistry": 25,
        "Mathematics": 25
    }
    ```
    """
)
async def update_subject_preferences(
    preferences: Dict[str, int],
    child_id: str = Query(..., description="Child ID to update preferences for"),
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)"),
    current_user: str = Depends(get_current_user)
) -> ExamSelectionResponse:
    """
    Update subject preferences for a child's exam selection.
    
    Args:
        preferences: Dictionary of subject weightages (must sum to 100)
        child_id: Unique identifier for the child (from query param)
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        ExamSelectionResponse: Updated exam selection with new preferences
    
    Raises:
        HTTPException: 404 if exam selection not found
        HTTPException: 403 if child doesn't belong to parent
        HTTPException: 400 if preferences don't sum to 100
        HTTPException: 500 if update fails
    
    Example:
        Request:
        ```json
        {
            "Physics": 45,
            "Chemistry": 30,
            "Biology": 25
        }
        ```
        
        Response:
        ```json
        {
            "child_id": "child_abc123",
            "exam_type": "NEET",
            "exam_date": "2025-05-05T00:00:00Z",
            "subject_preferences": {
                "Physics": 45,
                "Chemistry": 30,
                "Biology": 25
            },
            "days_until_exam": 162,
            "diagnostic_test_id": "test_xyz789",
            "created_at": "2024-01-10T08:00:00Z"
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Updating subject preferences for child {child_id}, parent {parent_id}")
        
        # Call service layer to update preferences
        # Service will verify ownership and validate weightages
        result = ExamService.update_subject_preferences(
            child_id=child_id,
            parent_id=parent_id,
            preferences=preferences
        )
        
        logger.info(f"Subject preferences updated successfully for child: {child_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error updating subject preferences for child {child_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update subject preferences. Please try again later."
        )


@router.get(
    "/status",
    response_model=Dict[str, bool],
    status_code=status.HTTP_200_OK,
    summary="Get onboarding completion status",
    description="""
    Check which onboarding steps have been completed by a parent.
    
    This endpoint tracks the parent's progress through the onboarding flow
    and indicates which steps remain to complete the setup process.
    
    **Onboarding Steps:**
    1. **Preferences**: Set language and notification preferences
    2. **Child Profile**: Add child information (name, age, grade, level)
    3. **Exam Selection**: Choose target exam and subject preferences
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    
    **Returns:**
    - 200: Onboarding status retrieved successfully
    - 500: Internal server error
    
    **Response Fields:**
    - `preferences_completed`: Whether preferences have been set
    - `child_profile_completed`: Whether child profile has been created
    - `exam_selected`: Whether exam has been selected
    - `onboarding_complete`: Whether all three steps are completed
    
    **Use Cases:**
    - Display onboarding progress to users
    - Redirect users to incomplete steps
    - Show completion checklist
    - Enable/disable features based on completion
    
    **Example Response:**
    ```json
    {
        "preferences_completed": true,
        "child_profile_completed": true,
        "exam_selected": false,
        "onboarding_complete": false
    }
    ```
    """
)
async def get_onboarding_status(
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)"),
    current_user: str = Depends(get_current_user)
) -> Dict[str, bool]:
    """
    Get onboarding completion status for a parent.
    
    Args:
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        dict: Completion status for each onboarding step
    
    Raises:
        HTTPException: 500 if status check fails
    
    Example:
        Response:
        ```json
        {
            "preferences_completed": true,
            "child_profile_completed": true,
            "exam_selected": true,
            "onboarding_complete": true
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Checking onboarding status for parent: {parent_id}")
        
        # Check each onboarding step
        preferences_completed = False
        child_profile_completed = False
        exam_selected = False
        
        # Check if preferences exist
        try:
            PreferencesService.get_preferences(parent_id=parent_id)
            preferences_completed = True
            logger.debug(f"Preferences completed for parent: {parent_id}")
        except HTTPException:
            # Preferences not found - step not completed
            logger.debug(f"Preferences not completed for parent: {parent_id}")
            pass
        
        # Check if child profile exists
        try:
            child = ChildService.get_child_profile(parent_id=parent_id)
            child_profile_completed = True
            logger.debug(f"Child profile completed for parent: {parent_id}")
            
            # If child exists, check if exam is selected
            try:
                ExamService.get_exam_selection(child_id=child.child_id)
                exam_selected = True
                logger.debug(f"Exam selected for child: {child.child_id}")
            except HTTPException:
                # Exam not selected - step not completed
                logger.debug(f"Exam not selected for child: {child.child_id}")
                pass
        except HTTPException:
            # Child profile not found - step not completed
            logger.debug(f"Child profile not completed for parent: {parent_id}")
            pass
        
        # Determine overall completion status
        onboarding_complete = (
            preferences_completed and 
            child_profile_completed and 
            exam_selected
        )
        
        status = {
            "preferences_completed": preferences_completed,
            "child_profile_completed": child_profile_completed,
            "exam_selected": exam_selected,
            "onboarding_complete": onboarding_complete
        }
        
        logger.info(f"Onboarding status for parent {parent_id}: {status}")
        
        return status
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error checking onboarding status for parent {parent_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check onboarding status. Please try again later."
        )
