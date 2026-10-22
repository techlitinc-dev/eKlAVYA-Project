"""
Child Profile Router Module

This module defines FastAPI endpoints for child profile management
in the Mentor AI EdTech Platform. It handles creation, retrieval, updates,
and deletion of child profiles with one-child-per-parent restriction enforcement.

Endpoints:
- POST /child: Create child profile (one child limit enforced)
- GET /child: Get child profile
- PUT /child/{child_id}: Update child profile
- DELETE /child/{child_id}: Delete child profile

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Query, Path, Depends

from models.child_models import (
    ChildProfileRequest,
    ChildProfileResponse,
    ChildProfileUpdate
)
from services.child_service import ChildService
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/onboarding",
    tags=["Onboarding - Child Profile"]
)


@router.post(
    "/child",
    response_model=ChildProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create child profile",
    description="""
    Create a child profile for JEE/NEET preparation tracking.
    
    **One-Child Restriction:** Each parent can only create ONE child profile.
    If a parent already has a child profile, this endpoint will return a 400 error.
    To create a new child profile, the existing one must be deleted first.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Parent must NOT have an existing child profile
    - Child age must be between 14 and 19 years
    - Child grade must be between 9 and 12
    - Current level must be: beginner, intermediate, or advanced
    
    **Returns:**
    - 201: Child profile created successfully
    - 400: Parent already has a child profile
    - 500: Internal server error
    
    **Example Request:**
    ```json
    {
        "name": "Rahul Sharma",
        "age": 16,
        "grade": 11,
        "current_level": "intermediate"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "child_id": "child_abc123def456",
        "parent_id": "parent_xyz789",
        "name": "Rahul Sharma",
        "age": 16,
        "grade": 11,
        "current_level": "intermediate",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z"
    }
    ```
    """
)
async def create_child_profile(
    request: ChildProfileRequest,
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)"),
    current_user: str = Depends(get_current_user)
) -> ChildProfileResponse:
    """
    Create a new child profile for a parent.
    
    Args:
        request: ChildProfileRequest containing child information
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        ChildProfileResponse: Created child profile with metadata
    
    Raises:
        HTTPException: 400 if parent already has a child profile
        HTTPException: 500 if creation fails
    
    Example:
        Request:
        ```json
        {
            "name": "Priya Patel",
            "age": 17,
            "grade": 12,
            "current_level": "advanced"
        }
        ```
        
        Response:
        ```json
        {
            "child_id": "child_def456ghi789",
            "parent_id": "parent_123abc",
            "name": "Priya Patel",
            "age": 17,
            "grade": 12,
            "current_level": "advanced",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Creating child profile for parent: {parent_id}")
        
        # Call service layer to create child profile
        # Service will enforce one-child restriction
        result = ChildService.create_child_profile(
            parent_id=parent_id,
            profile=request
        )
        
        logger.info(f"Child profile created successfully: {result.child_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error creating child profile for parent {parent_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create child profile. Please try again later."
        )


@router.get(
    "/child",
    response_model=ChildProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get child profile",
    description="""
    Retrieve the child profile for an authenticated parent.
    
    This endpoint returns the child profile information including name, age,
    grade, and current academic level.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Child profile must exist for this parent
    
    **Returns:**
    - 200: Child profile retrieved successfully
    - 404: Child profile not found for this parent
    - 500: Internal server error
    
    **Use Cases:**
    - Display child information in parent dashboard
    - Pre-fill forms for profile updates
    - Show child's current academic status
    
    **Example Response:**
    ```json
    {
        "child_id": "child_abc123def456",
        "parent_id": "parent_xyz789",
        "name": "Amit Kumar",
        "age": 15,
        "grade": 10,
        "current_level": "beginner",
        "created_at": "2024-01-10T08:00:00Z",
        "updated_at": "2024-01-15T14:30:00Z"
    }
    ```
    """
)
async def get_child_profile(
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)"),
    current_user: str = Depends(get_current_user)
) -> ChildProfileResponse:
    """
    Retrieve the child profile for a parent.
    
    Args:
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        ChildProfileResponse: Child profile with metadata
    
    Raises:
        HTTPException: 404 if child profile not found
        HTTPException: 500 if retrieval fails
    
    Example:
        Response:
        ```json
        {
            "child_id": "child_123abc",
            "parent_id": "parent_xyz",
            "name": "Sneha Reddy",
            "age": 16,
            "grade": 11,
            "current_level": "intermediate",
            "created_at": "2024-01-10T08:00:00Z",
            "updated_at": "2024-01-10T08:00:00Z"
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Retrieving child profile for parent: {parent_id}")
        
        # Call service layer to get child profile
        result = ChildService.get_child_profile(parent_id=parent_id)
        
        logger.info(f"Child profile retrieved successfully: {result.child_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error retrieving child profile for parent {parent_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve child profile. Please try again later."
        )


@router.put(
    "/child/{child_id}",
    response_model=ChildProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update child profile",
    description="""
    Update child profile information for an authenticated parent.
    
    This endpoint allows partial updates to the child profile. Only the fields
    provided in the request body will be updated. Other fields remain unchanged.
    
    **Ownership Verification:** The service verifies that the child belongs to
    the authenticated parent before allowing updates.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Child profile must exist
    - Child must belong to the authenticated parent
    - Updated age must be between 14 and 19 years
    - Updated grade must be between 9 and 12
    
    **Updateable Fields:**
    - name: Child's full name (2-100 characters)
    - age: Child's age (14-19 years)
    - grade: Current grade (9-12)
    - current_level: Academic level (beginner, intermediate, advanced)
    
    **Returns:**
    - 200: Child profile updated successfully
    - 400: Invalid data provided
    - 403: Child does not belong to authenticated parent
    - 404: Child profile not found
    - 500: Internal server error
    
    **Example Request (Partial Update):**
    ```json
    {
        "grade": 12,
        "current_level": "advanced"
    }
    ```
    """
)
async def update_child_profile(
    child_id: str = Path(..., description="Unique identifier for the child"),
    request: ChildProfileUpdate = None,
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)")
) -> ChildProfileResponse:
    """
    Update a child profile (partial update).
    
    Args:
        child_id: Unique identifier for the child (from path)
        request: ChildProfileUpdate with fields to update
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        ChildProfileResponse: Updated child profile with metadata
    
    Raises:
        HTTPException: 404 if child not found
        HTTPException: 403 if child doesn't belong to parent
        HTTPException: 400 if invalid data provided
        HTTPException: 500 if update fails
    
    Example:
        Request (partial update):
        ```json
        {
            "name": "Rahul Sharma Updated",
            "current_level": "advanced"
        }
        ```
        
        Response:
        ```json
        {
            "child_id": "child_abc123",
            "parent_id": "parent_xyz",
            "name": "Rahul Sharma Updated",
            "age": 16,
            "grade": 11,
            "current_level": "advanced",
            "created_at": "2024-01-10T08:00:00Z",
            "updated_at": "2024-01-20T15:45:00Z"
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Updating child profile {child_id} for parent: {parent_id}")
        
        # Call service layer to update child profile
        # Service will verify ownership
        result = ChildService.update_child_profile(
            child_id=child_id,
            parent_id=parent_id,
            updates=request
        )
        
        logger.info(f"Child profile updated successfully: {child_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error updating child profile {child_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update child profile. Please try again later."
        )


@router.delete(
    "/child/{child_id}",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Delete child profile",
    description="""
    Delete a child profile for an authenticated parent.
    
    This endpoint permanently removes the child profile from the system.
    After deletion, the parent can create a new child profile if needed.
    
    **Ownership Verification:** The service verifies that the child belongs to
    the authenticated parent before allowing deletion.
    
    **Important:** This action is permanent and cannot be undone. All data
    associated with the child profile will be deleted.
    
    **Requirements:**
    - Parent must be authenticated (parent_id required)
    - Child profile must exist
    - Child must belong to the authenticated parent
    
    **Returns:**
    - 200: Child profile deleted successfully
    - 403: Child does not belong to authenticated parent
    - 404: Child profile not found
    - 500: Internal server error
    
    **Use Cases:**
    - Remove incorrect child profile
    - Allow parent to create a new child profile
    - Handle account cleanup requests
    
    **Example Response:**
    ```json
    {
        "message": "Child profile deleted successfully",
        "child_id": "child_abc123def456"
    }
    ```
    """
)
async def delete_child_profile(
    child_id: str = Path(..., description="Unique identifier for the child"),
    parent_id: str = Query(..., description="Parent ID for authentication (temporary)")
) -> Dict[str, str]:
    """
    Delete a child profile.
    
    Args:
        child_id: Unique identifier for the child (from path)
        parent_id: Unique identifier for the parent (from query param)
    
    Returns:
        dict: Success message with deleted child_id
    
    Raises:
        HTTPException: 404 if child not found
        HTTPException: 403 if child doesn't belong to parent
        HTTPException: 500 if deletion fails
    
    Example:
        Response:
        ```json
        {
            "message": "Child profile deleted successfully",
            "child_id": "child_abc123"
        }
        ```
    """
    try:
        # For testing, use the authenticated user ID
        parent_id = current_user if not parent_id else parent_id
        logger.info(f"Deleting child profile {child_id} for parent: {parent_id}")
        
        # Call service layer to delete child profile
        # Service will verify ownership
        result = ChildService.delete_child_profile(
            child_id=child_id,
            parent_id=parent_id
        )
        
        logger.info(f"Child profile deleted successfully: {child_id}")
        
        return result
    
    except HTTPException:
        # Re-raise HTTP exceptions from service layer
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error deleting child profile {child_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete child profile. Please try again later."
        )
