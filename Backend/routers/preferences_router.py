"""
Preferences Router Module

This module defines FastAPI endpoints for parent preferences management
in the Mentor AI EdTech Platform. It handles creation, retrieval, and
updates of preference settings including language, notifications, and
teaching involvement.

Endpoints:
- POST /preferences: Create parent preferences
- GET /preferences: Get parent preferences
- PUT /preferences: Update parent preferences

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Query

from models.preferences_models import (
    PreferencesRequest,
    PreferencesResponse,
    PreferencesUpdate
)
from services.preferences_service import PreferencesService

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/onboarding",
    tags=["Onboarding - Preferences"]
)


@router.post(
    "/preferences",
    response_model=PreferencesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create parent preferences",
    description="""
    Create preference settings for a parent account.
    
    This endpoint allows parents to set their initial preferences including:
    - Preferred language for communication (English, Hindi, or Marathi)
    - Notification preferences (email, SMS, push notifications)
    - Teaching involvement level (high, medium, or low)
    
    **Note:** Each parent can only create preferences once. Use the PUT endpoint
    to update existing preferences.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - All required fields must be provided
    - Language must be one of: en, hi, mr
    - Teaching involvement must be one of: high, medium, low
    
    **Returns:**
    - 201: Preferences created successfully
    - 400: Preferences already exist for this parent
    - 500: Internal server error
    
    **Example Request:**
    ```json
    {
        "language": "en",
        "email_notifications": true,
        "sms_notifications": true,
        "push_notifications": true,
        "teaching_involvement": "medium"
    }
    ```
    """
)
async def create_preferences(
    request: PreferencesRequest,
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)")
) -> PreferencesResponse:
    """
    Create new preferences for a parent.
    
    Args:
        request: PreferencesRequest containing preference settings
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        PreferencesResponse: Created preferences with metadata
    
    Raises:
        HTTPException: 400 if preferences already exist
        HTTPException: 500 if creation fails
    
    Example:
        Request:
        ```json
        {
            "language": "en",
            "email_notifications": true,
            "sms_notifications": false,
            "push_notifications": true,
            "teaching_involvement": "high"
        }
        ```
        
        Response:
        ```json
        {
            "parent_id": "parent_123abc456def",
            "language": "en",
            "email_notifications": true,
            "sms_notifications": false,
            "push_notifications": true,
            "teaching_involvement": "high",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        logger.info(f"Creating preferences for parent: {parent_id}")
        
        # Call service layer to create preferences
        result = PreferencesService.create_preferences(
            parent_id=parent_id,
            preferences=request
        )
        
        logger.info(f"Preferences created successfully for parent: {parent_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error creating preferences for parent {parent_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create preferences. Please try again later."
        )


@router.get(
    "/preferences",
    response_model=PreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get parent preferences",
    description="""
    Retrieve current preference settings for an authenticated parent.
    
    This endpoint returns all preference settings including language,
    notification preferences, and teaching involvement level.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Preferences must have been created previously
    
    **Returns:**
    - 200: Preferences retrieved successfully
    - 404: Preferences not found for this parent
    - 500: Internal server error
    
    **Use Cases:**
    - Display current settings in user profile
    - Pre-fill forms for preference updates
    - Customize app experience based on preferences
    
    **Example Response:**
    ```json
    {
        "parent_id": "parent_123abc456def",
        "language": "hi",
        "email_notifications": true,
        "sms_notifications": true,
        "push_notifications": false,
        "teaching_involvement": "medium",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-20T14:45:00Z"
    }
    ```
    """
)
async def get_preferences(
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)")
) -> PreferencesResponse:
    """
    Retrieve preferences for a parent.
    
    Args:
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        PreferencesResponse: Parent's preferences with metadata
    
    Raises:
        HTTPException: 404 if preferences not found
        HTTPException: 500 if retrieval fails
    
    Example:
        Response:
        ```json
        {
            "parent_id": "parent_123abc",
            "language": "en",
            "email_notifications": true,
            "sms_notifications": true,
            "push_notifications": true,
            "teaching_involvement": "medium",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        logger.info(f"Retrieving preferences for parent: {parent_id}")
        
        # Call service layer to get preferences
        result = PreferencesService.get_preferences(parent_id=parent_id)
        
        logger.info(f"Preferences retrieved successfully for parent: {parent_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error retrieving preferences for parent {parent_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve preferences. Please try again later."
        )


@router.put(
    "/preferences",
    response_model=PreferencesResponse,
    status_code=status.HTTP_200_OK,
    summary="Update parent preferences",
    description="""
    Update one or more preference fields for an authenticated parent.
    
    This endpoint allows partial updates to preferences. Only the fields
    provided in the request body will be updated. Other fields remain unchanged.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Preferences must have been created previously
    - At least one field must be provided for update
    
    **Updateable Fields:**
    - language: Preferred communication language (en, hi, mr)
    - email_notifications: Enable/disable email notifications
    - sms_notifications: Enable/disable SMS notifications
    - push_notifications: Enable/disable push notifications
    - teaching_involvement: Level of involvement (high, medium, low)
    
    **Returns:**
    - 200: Preferences updated successfully
    - 400: No fields provided to update
    - 404: Preferences not found for this parent
    - 500: Internal server error
    
    **Partial Update Example:**
    You can update just one or two fields without affecting others.
    
    **Example Request (Update only language and SMS):**
    ```json
    {
        "language": "hi",
        "sms_notifications": false
    }
    ```
    """
)
async def update_preferences(
    request: PreferencesUpdate,
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)")
) -> PreferencesResponse:
    """
    Update preferences for a parent (partial update).
    
    Args:
        request: PreferencesUpdate with fields to update
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        PreferencesResponse: Updated preferences with metadata
    
    Raises:
        HTTPException: 404 if preferences not found
        HTTPException: 400 if no fields to update
        HTTPException: 500 if update fails
    
    Example:
        Request (partial update):
        ```json
        {
            "language": "hi",
            "teaching_involvement": "high"
        }
        ```
        
        Response:
        ```json
        {
            "parent_id": "parent_123abc",
            "language": "hi",
            "email_notifications": true,
            "sms_notifications": true,
            "push_notifications": true,
            "teaching_involvement": "high",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-20T14:45:00Z"
        }
        ```
    """
    try:
        logger.info(f"Updating preferences for parent: {parent_id}")
        
        # Call service layer to update preferences
        result = PreferencesService.update_preferences(
            parent_id=parent_id,
            updates=request
        )
        
        logger.info(f"Preferences updated successfully for parent: {parent_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error updating preferences for parent {parent_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences. Please try again later."
        )
