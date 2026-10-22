"""
Preferences Service Module

This module contains business logic for managing parent preferences
in the Mentor AI EdTech Platform. It handles preference creation, retrieval,
and updates in Firestore.

Classes:
- PreferencesService: Service class for preferences management

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from utils.firebase_config import get_firestore_client
from models.preferences_models import (
    PreferencesRequest,
    PreferencesResponse,
    PreferencesUpdate
)

# Configure logging
logger = logging.getLogger(__name__)


class PreferencesService:
    """
    Service class for managing parent preferences.
    
    This service handles all operations related to parent preferences
    including creation, retrieval, and updates in Firestore.
    """
    
    @staticmethod
    def create_preferences(
        parent_id: str,
        preferences: PreferencesRequest
    ) -> PreferencesResponse:
        """
        Create new preferences for a parent.
        
        Stores preference settings in Firestore under the parent's document.
        Creates timestamps for creation and last update.
        
        Args:
            parent_id: Unique identifier for the parent
            preferences: PreferencesRequest containing preference settings
        
        Returns:
            PreferencesResponse: Created preferences with metadata
        
        Raises:
            HTTPException: 400 if preferences already exist
            HTTPException: 500 if creation fails
        
        Example:
            >>> service = PreferencesService()
            >>> request = PreferencesRequest(
            ...     language="en",
            ...     email_notifications=True,
            ...     sms_notifications=True,
            ...     push_notifications=True,
            ...     teaching_involvement="medium"
            ... )
            >>> response = service.create_preferences("parent_123", request)
        """
        try:
            logger.info(f"Creating preferences for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Check if preferences already exist
            prefs_ref = db.collection("parents").document(parent_id).collection("preferences").document("settings")
            prefs_doc = prefs_ref.get()
            
            if prefs_doc.exists:
                logger.warning(f"Preferences already exist for parent: {parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Preferences already exist for this parent. Use update endpoint to modify."
                )
            
            # Prepare preferences data
            now = datetime.utcnow()
            preferences_data = {
                "parent_id": parent_id,
                "language": preferences.language,
                "email_notifications": preferences.email_notifications,
                "sms_notifications": preferences.sms_notifications,
                "push_notifications": preferences.push_notifications,
                "teaching_involvement": preferences.teaching_involvement,
                "created_at": SERVER_TIMESTAMP,
                "updated_at": SERVER_TIMESTAMP
            }
            
            # Store preferences in Firestore
            prefs_ref.set(preferences_data)
            
            logger.info(f"Preferences created successfully for parent: {parent_id}")
            
            # Retrieve the created document to get server timestamps
            created_doc = prefs_ref.get()
            created_data = created_doc.to_dict()
            
            # Return response
            return PreferencesResponse(
                parent_id=parent_id,
                language=created_data["language"],
                email_notifications=created_data["email_notifications"],
                sms_notifications=created_data["sms_notifications"],
                push_notifications=created_data["push_notifications"],
                teaching_involvement=created_data["teaching_involvement"],
                created_at=created_data["created_at"],
                updated_at=created_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error creating preferences for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create preferences. Please try again later."
            )
    
    @staticmethod
    def get_preferences(parent_id: str) -> PreferencesResponse:
        """
        Retrieve preferences for a parent.
        
        Fetches preference settings from Firestore for the specified parent.
        
        Args:
            parent_id: Unique identifier for the parent
        
        Returns:
            PreferencesResponse: Parent's preferences with metadata
        
        Raises:
            HTTPException: 404 if preferences not found
            HTTPException: 500 if retrieval fails
        
        Example:
            >>> service = PreferencesService()
            >>> response = service.get_preferences("parent_123")
            >>> print(response.language)
            'en'
        """
        try:
            logger.info(f"Retrieving preferences for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Retrieve preferences from Firestore
            prefs_ref = db.collection("parents").document(parent_id).collection("preferences").document("settings")
            prefs_doc = prefs_ref.get()
            
            if not prefs_doc.exists:
                logger.warning(f"Preferences not found for parent: {parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preferences not found for parent: {parent_id}"
                )
            
            # Get preferences data
            prefs_data = prefs_doc.to_dict()
            
            logger.info(f"Preferences retrieved successfully for parent: {parent_id}")
            
            # Return response
            return PreferencesResponse(
                parent_id=parent_id,
                language=prefs_data["language"],
                email_notifications=prefs_data["email_notifications"],
                sms_notifications=prefs_data["sms_notifications"],
                push_notifications=prefs_data["push_notifications"],
                teaching_involvement=prefs_data["teaching_involvement"],
                created_at=prefs_data["created_at"],
                updated_at=prefs_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error retrieving preferences for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve preferences. Please try again later."
            )
    
    @staticmethod
    def update_preferences(
        parent_id: str,
        updates: PreferencesUpdate
    ) -> PreferencesResponse:
        """
        Update preferences for a parent (partial update).
        
        Updates only the fields provided in the updates object.
        Automatically updates the updated_at timestamp.
        
        Args:
            parent_id: Unique identifier for the parent
            updates: PreferencesUpdate with fields to update
        
        Returns:
            PreferencesResponse: Updated preferences
        
        Raises:
            HTTPException: 404 if preferences not found
            HTTPException: 400 if no fields to update
            HTTPException: 500 if update fails
        
        Example:
            >>> service = PreferencesService()
            >>> update = PreferencesUpdate(
            ...     language="hi",
            ...     sms_notifications=False
            ... )
            >>> response = service.update_preferences("parent_123", update)
        """
        try:
            logger.info(f"Updating preferences for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Check if preferences exist
            prefs_ref = db.collection("parents").document(parent_id).collection("preferences").document("settings")
            prefs_doc = prefs_ref.get()
            
            if not prefs_doc.exists:
                logger.warning(f"Preferences not found for parent: {parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preferences not found for parent: {parent_id}. Create preferences first."
                )
            
            # Build update dictionary with only provided fields
            update_data = {}
            
            if updates.language is not None:
                update_data["language"] = updates.language
            
            if updates.email_notifications is not None:
                update_data["email_notifications"] = updates.email_notifications
            
            if updates.sms_notifications is not None:
                update_data["sms_notifications"] = updates.sms_notifications
            
            if updates.push_notifications is not None:
                update_data["push_notifications"] = updates.push_notifications
            
            if updates.teaching_involvement is not None:
                update_data["teaching_involvement"] = updates.teaching_involvement
            
            # Check if there are any fields to update
            if not update_data:
                logger.warning(f"No fields to update for parent: {parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided to update"
                )
            
            # Always update the updated_at timestamp
            update_data["updated_at"] = SERVER_TIMESTAMP
            
            # Update preferences in Firestore
            prefs_ref.update(update_data)
            
            logger.info(f"Preferences updated successfully for parent: {parent_id}")
            
            # Retrieve updated preferences
            updated_doc = prefs_ref.get()
            updated_data = updated_doc.to_dict()
            
            # Return response
            return PreferencesResponse(
                parent_id=parent_id,
                language=updated_data["language"],
                email_notifications=updated_data["email_notifications"],
                sms_notifications=updated_data["sms_notifications"],
                push_notifications=updated_data["push_notifications"],
                teaching_involvement=updated_data["teaching_involvement"],
                created_at=updated_data["created_at"],
                updated_at=updated_data["updated_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error updating preferences for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences. Please try again later."
            )
    
    @staticmethod
    def preferences_exist(parent_id: str) -> bool:
        """
        Check if preferences exist for a parent.
        
        Queries Firestore to determine if preference settings have been
        created for the specified parent.
        
        Args:
            parent_id: Unique identifier for the parent
        
        Returns:
            bool: True if preferences exist, False otherwise
        
        Example:
            >>> service = PreferencesService()
            >>> exists = service.preferences_exist("parent_123")
            >>> print(exists)
            True
        """
        try:
            logger.debug(f"Checking if preferences exist for parent: {parent_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Check if preferences document exists
            prefs_ref = db.collection("parents").document(parent_id).collection("preferences").document("settings")
            prefs_doc = prefs_ref.get()
            
            exists = prefs_doc.exists
            
            logger.debug(f"Preferences exist for parent {parent_id}: {exists}")
            
            return exists
        
        except Exception as e:
            logger.error(f"Error checking preferences existence for parent {parent_id}: {e}")
            logger.exception("Full traceback:")
            # Return False on error to be safe
            return False
