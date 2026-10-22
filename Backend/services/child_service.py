"""
Child Profile Service Module

This module contains business logic for managing child profiles
in the Mentor AI EdTech Platform. It enforces the one-child-per-parent
restriction and handles all child profile operations in Firestore.

Classes:
- ChildService: Service class for child profile management

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException, status
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from utils.firebase_config import get_firestore_client, get_auth_client
from firebase_admin.auth import EmailAlreadyExistsError
from models.child_models import (
    ChildProfileRequest,
    ChildProfileResponse,
    ChildProfileUpdate
)

# Configure logging
logger = logging.getLogger(__name__)


class ChildService:
    """
    Service class for managing child profiles.
    
    This service handles all operations related to child profiles
    including creation, retrieval, updates, and deletion in Firestore.
    Enforces the one-child-per-parent business rule.
    """
    
    @staticmethod
    def has_child(parent_id: str) -> bool:
        """
        Check if a parent has any child profile.
        
        Queries Firestore to determine if the parent has created
        a child profile.
        
        Args:
            parent_id: Unique identifier for the parent
        
        Returns:
            bool: True if parent has a child, False otherwise
        
        Example:
            >>> service = ChildService()
            >>> has_child = service.has_child("parent_123")
            >>> print(has_child)
            False
        """
        try:
            logger.debug(f"Checking if parent {parent_id} has a child")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Query children collection for this parent
            children_ref = db.collection("children")
            query = children_ref.where("parent_id", "==", parent_id).limit(1)
            docs = list(query.stream())
            
            has_child = len(docs) > 0
            
            logger.debug(f"Parent {parent_id} has child: {has_child}")
            
            return has_child
        
        except Exception as e:
            logger.error(f"Error checking child existence for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            # Return False on error to be safe
            return False
    
    @staticmethod
    def create_child_profile(
        parent_id: str,
        profile: ChildProfileRequest
    ) -> ChildProfileResponse:
        """
        Create a new child profile for a parent.
        
        Enforces the one-child-per-parent restriction. Generates a unique
        child ID and stores the profile in Firestore.
        
        Args:
            parent_id: Unique identifier for the parent
            profile: ChildProfileRequest containing child information
        
        Returns:
            ChildProfileResponse: Created child profile with metadata
        
        Raises:
            HTTPException: 400 if parent already has a child
            HTTPException: 500 if creation fails
        
        Example:
            >>> service = ChildService()
            >>> request = ChildProfileRequest(
            ...     name="Rahul Sharma",
            ...     age=16,
            ...     grade=11,
            ...     current_level="intermediate"
            ... )
            >>> response = service.create_child_profile("parent_123", request)
        """
        try:
            logger.info(f"Creating child profile for parent: {parent_id}")
            
            # Check if parent already has a child (one-child restriction)
            if ChildService.has_child(parent_id):
                logger.warning(f"Parent {parent_id} already has a child profile")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent can only have one child profile. Delete existing profile to create a new one."
                )
            
            # Get Firebase Auth client
            auth_client = get_auth_client()
            
            # Create email for child - if username already contains @, use it directly
            if "@" in profile.username:
                child_email = profile.username
            else:
                child_email = f"{profile.username}@mentor-ai.local"
            
            # Create Firebase Auth user for child
            try:
                child_user = auth_client.create_user(
                    email=child_email,
                    password=profile.password,
                    email_verified=False,
                    disabled=False
                )
                logger.info(f"Child Firebase Auth user created successfully: {child_user.uid}")
            except EmailAlreadyExistsError:
                logger.warning(f"Child email already exists: {child_email}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username '{profile.username}' is already taken. Please choose a different username."
                )
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Generate unique child ID
            child_id = f"child_{uuid.uuid4().hex[:12]}"
            
            # Prepare child profile data
            child_data = {
                "child_id": child_id,
                "parent_id": parent_id,
                "firebase_uid": child_user.uid,  # Store Firebase Auth UID
                "name": profile.name,
                "age": profile.age,
                "grade": profile.grade,
                "current_level": profile.current_level,
                "username": profile.username,
                "email": child_email,  # Store child's email
                "password": profile.password,  # In production, this should be hashed
                "created_at": SERVER_TIMESTAMP,
                "updated_at": SERVER_TIMESTAMP
            }
            
            # Store child profile in Firestore
            children_ref = db.collection("children")
            children_ref.document(child_id).set(child_data)
            
            logger.info(f"Child profile created successfully: {child_id} for parent: {parent_id}")
            
            # Retrieve the created document to get server timestamps
            created_doc = children_ref.document(child_id).get()
            created_data = created_doc.to_dict()
            
            # Return response
            return ChildProfileResponse(
                child_id=child_id,
                parent_id=parent_id,
                name=created_data["name"],
                age=created_data["age"],
                grade=created_data["grade"],
                current_level=created_data["current_level"],
                username=created_data["username"],
                created_at=created_data["created_at"],
                updated_at=created_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error creating child profile for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create child profile. Please try again later."
            )
    
    @staticmethod
    def get_child_profile(parent_id: str) -> ChildProfileResponse:
        """
        Retrieve child profile for a parent.
        
        Queries Firestore for the child associated with the parent.
        
        Args:
            parent_id: Unique identifier for the parent
        
        Returns:
            ChildProfileResponse: Child profile with metadata
        
        Raises:
            HTTPException: 404 if child profile not found
            HTTPException: 500 if retrieval fails
        
        Example:
            >>> service = ChildService()
            >>> response = service.get_child_profile("parent_123")
            >>> print(response.name)
            'Rahul Sharma'
        """
        try:
            logger.info(f"Retrieving child profile for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Query children collection for this parent
            children_ref = db.collection("children")
            query = children_ref.where("parent_id", "==", parent_id).limit(1)
            docs = list(query.stream())
            
            if not docs:
                logger.warning(f"Child profile not found for parent: {parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Child profile not found for parent: {parent_id}"
                )
            
            # Get child data
            child_doc = docs[0]
            child_data = child_doc.to_dict()
            
            logger.info(f"Child profile retrieved successfully: {child_data['child_id']}")
            
            # Return response
            return ChildProfileResponse(
                child_id=child_data["child_id"],
                parent_id=child_data["parent_id"],
                name=child_data["name"],
                age=child_data["age"],
                grade=child_data["grade"],
                current_level=child_data["current_level"],
                username=child_data.get("username", ""),
                created_at=child_data["created_at"],
                updated_at=child_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error retrieving child profile for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve child profile. Please try again later."
            )
    
    @staticmethod
    def get_child_by_id(child_id: str) -> ChildProfileResponse:
        """
        Retrieve child profile by child ID.
        
        Directly fetches child profile using the child's unique identifier.
        
        Args:
            child_id: Unique identifier for the child
        
        Returns:
            ChildProfileResponse: Child profile with metadata
        
        Raises:
            HTTPException: 404 if child profile not found
            HTTPException: 500 if retrieval fails
        
        Example:
            >>> service = ChildService()
            >>> response = service.get_child_by_id("child_abc123")
            >>> print(response.name)
            'Priya Patel'
        """
        try:
            logger.info(f"Retrieving child profile by ID: {child_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Get child document
            child_ref = db.collection("children").document(child_id)
            child_doc = child_ref.get()
            
            if not child_doc.exists:
                logger.warning(f"Child profile not found: {child_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Child profile not found: {child_id}"
                )
            
            # Get child data
            child_data = child_doc.to_dict()
            
            logger.info(f"Child profile retrieved successfully: {child_id}")
            
            # Return response
            return ChildProfileResponse(
                child_id=child_data["child_id"],
                parent_id=child_data["parent_id"],
                name=child_data["name"],
                age=child_data["age"],
                grade=child_data["grade"],
                current_level=child_data["current_level"],
                username=child_data.get("username", ""),
                created_at=child_data["created_at"],
                updated_at=child_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error retrieving child profile {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve child profile. Please try again later."
            )
    
    @staticmethod
    def update_child_profile(
        child_id: str,
        parent_id: str,
        updates: ChildProfileUpdate
    ) -> ChildProfileResponse:
        """
        Update child profile (partial update).
        
        Updates only the fields provided in the updates object.
        Verifies parent ownership before allowing updates.
        
        Args:
            child_id: Unique identifier for the child
            parent_id: Unique identifier for the parent (for ownership verification)
            updates: ChildProfileUpdate with fields to update
        
        Returns:
            ChildProfileResponse: Updated child profile
        
        Raises:
            HTTPException: 404 if child profile not found
            HTTPException: 403 if parent doesn't own the child profile
            HTTPException: 400 if no fields to update
            HTTPException: 500 if update fails
        
        Example:
            >>> service = ChildService()
            >>> update = ChildProfileUpdate(
            ...     age=17,
            ...     grade=12,
            ...     current_level="advanced"
            ... )
            >>> response = service.update_child_profile("child_abc123", "parent_123", update)
        """
        try:
            logger.info(f"Updating child profile: {child_id} for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Get child document
            child_ref = db.collection("children").document(child_id)
            child_doc = child_ref.get()
            
            if not child_doc.exists:
                logger.warning(f"Child profile not found: {child_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Child profile not found: {child_id}"
                )
            
            # Verify parent ownership
            child_data = child_doc.to_dict()
            if child_data["parent_id"] != parent_id:
                logger.warning(f"Parent {parent_id} attempted to update child {child_id} owned by {child_data['parent_id']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update this child profile"
                )
            
            # Build update dictionary with only provided fields
            update_data = {}
            
            if updates.name is not None:
                update_data["name"] = updates.name
            
            if updates.age is not None:
                update_data["age"] = updates.age
            
            if updates.grade is not None:
                update_data["grade"] = updates.grade
            
            if updates.current_level is not None:
                update_data["current_level"] = updates.current_level
            
            # Check if there are any fields to update
            if not update_data:
                logger.warning(f"No fields to update for child: {child_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided to update"
                )
            
            # Always update the updated_at timestamp
            update_data["updated_at"] = SERVER_TIMESTAMP
            
            # Update child profile in Firestore
            child_ref.update(update_data)
            
            logger.info(f"Child profile updated successfully: {child_id}")
            
            # Retrieve updated profile
            updated_doc = child_ref.get()
            updated_data = updated_doc.to_dict()
            
            # Return response
            return ChildProfileResponse(
                child_id=updated_data["child_id"],
                parent_id=updated_data["parent_id"],
                name=updated_data["name"],
                age=updated_data["age"],
                grade=updated_data["grade"],
                current_level=updated_data["current_level"],
                username=updated_data.get("username", ""),
                created_at=updated_data["created_at"],
                updated_at=updated_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error updating child profile {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update child profile. Please try again later."
            )
    
    @staticmethod
    def delete_child_profile(
        child_id: str,
        parent_id: str
    ) -> Dict[str, str]:
        """
        Delete child profile.
        
        Permanently deletes the child profile from Firestore.
        Verifies parent ownership before allowing deletion.
        
        Args:
            child_id: Unique identifier for the child
            parent_id: Unique identifier for the parent (for ownership verification)
        
        Returns:
            Dict with success message
        
        Raises:
            HTTPException: 404 if child profile not found
            HTTPException: 403 if parent doesn't own the child profile
            HTTPException: 500 if deletion fails
        
        Example:
            >>> service = ChildService()
            >>> result = service.delete_child_profile("child_abc123", "parent_123")
            >>> print(result['message'])
            'Child profile deleted successfully'
        """
        try:
            logger.info(f"Deleting child profile: {child_id} for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Get child document
            child_ref = db.collection("children").document(child_id)
            child_doc = child_ref.get()
            
            if not child_doc.exists:
                logger.warning(f"Child profile not found: {child_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Child profile not found: {child_id}"
                )
            
            # Verify parent ownership
            child_data = child_doc.to_dict()
            if child_data["parent_id"] != parent_id:
                logger.warning(f"Parent {parent_id} attempted to delete child {child_id} owned by {child_data['parent_id']}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to delete this child profile"
                )
            
            # Delete child profile
            child_ref.delete()
            
            logger.info(f"Child profile deleted successfully: {child_id}")
            
            return {
                "message": "Child profile deleted successfully"
            }
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error deleting child profile {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete child profile. Please try again later."
            )
