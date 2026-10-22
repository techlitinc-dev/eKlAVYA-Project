"""
Exam Selection Service Module

This module contains business logic for exam selection and diagnostic test
scheduling in the Mentor AI EdTech Platform. It handles JEE and NEET exam
selection, subject preferences, and diagnostic test management in Firestore.

Classes:
- ExamService: Service class for exam selection and diagnostic test management

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import uuid
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List

from fastapi import HTTPException, status
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from utils.firebase_config import get_firestore_client
from utils.date_utils import (
    calculate_days_until,
    validate_exam_date,
    get_available_exam_dates,
    format_date_for_display
)
from services.child_service import ChildService
from models.exam_models import (
    ExamSelectionRequest,
    ExamSelectionResponse,
    AvailableExam,
    AvailableExamsResponse,
    DiagnosticTestSchedule
)

# Configure logging
logger = logging.getLogger(__name__)


class ExamService:
    """
    Service class for managing exam selection and diagnostic tests.
    
    This service handles all operations related to exam selection,
    subject preferences, and diagnostic test scheduling in Firestore.
    """
    
    @staticmethod
    def get_available_exams() -> AvailableExamsResponse:
        """
        Get list of available exams with dates and subjects.
        
        Retrieves available exam dates for JEE Main, JEE Advanced, and NEET
        using the date utilities module.
        
        Returns:
            AvailableExamsResponse: List of available exams with details
        
        Example:
            >>> service = ExamService()
            >>> response = service.get_available_exams()
            >>> for exam in response.exams:
            ...     print(f"{exam.exam_name}: {exam.available_dates}")
        """
        try:
            logger.info("Retrieving available exams")
            
            # Get the directory path for data files
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            data_file_path = os.path.join(project_root, "data", "exam_dates.json")
            
            # Read exam dates from JSON file
            try:
                with open(data_file_path, 'r') as f:
                    exam_dates_data = json.load(f)
                logger.info(f"Successfully loaded exam dates from {data_file_path}")
            except FileNotFoundError:
                logger.error(f"Exam dates file not found at {data_file_path}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Exam dates configuration not found"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing exam dates JSON: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid exam dates configuration"
                )
            
            exams_list = []
            
            # Process JEE Main
            jee_main_dates = [item["date"] for item in exam_dates_data.get("JEE_MAIN", [])]
            jee_main = AvailableExam(
                exam_type="JEE_MAIN",
                exam_name="JEE Main",
                available_dates=jee_main_dates,
                subjects=["Physics", "Chemistry", "Mathematics"]
            )
            exams_list.append(jee_main)
            
            # Process JEE Advanced
            jee_adv_dates = [item["date"] for item in exam_dates_data.get("JEE_ADVANCED", [])]
            jee_advanced = AvailableExam(
                exam_type="JEE_ADVANCED",
                exam_name="JEE Advanced",
                available_dates=jee_adv_dates,
                subjects=["Physics", "Chemistry", "Mathematics"]
            )
            exams_list.append(jee_advanced)
            
            # Process JEE Combo (combine dates from both)
            jee_combo_dates = []
            jee_combo_dates.extend([item["date"] for item in exam_dates_data.get("JEE_MAIN", [])])
            jee_combo_dates.extend([item["date"] for item in exam_dates_data.get("JEE_ADVANCED", [])])
            
            jee_combo = AvailableExam(
                exam_type="JEE_COMBO",
                exam_name="JEE Main + Advanced",
                available_dates=jee_combo_dates,
                subjects=["Physics", "Chemistry", "Mathematics"]
            )
            exams_list.append(jee_combo)
            
            # Process NEET
            neet_dates = [item["date"] for item in exam_dates_data.get("NEET", [])]
            neet = AvailableExam(
                exam_type="NEET",
                exam_name="NEET",
                available_dates=neet_dates,
                subjects=["Physics", "Chemistry", "Biology"]
            )
            exams_list.append(neet)
            
            logger.info(f"Retrieved {len(exams_list)} available exams")
            
            return AvailableExamsResponse(exams=exams_list)
        
        except Exception as e:
            logger.error(f"Error retrieving available exams: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve available exams. Please try again later."
            )
    
    @staticmethod
    def create_diagnostic_test(
        child_id: str,
        exam_type: str
    ) -> DiagnosticTestSchedule:
        """
        Create a diagnostic test for a child.
        
        Generates a new diagnostic test with scheduling details and
        stores it in Firestore.
        
        Args:
            child_id: Unique identifier for the child
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        
        Returns:
            DiagnosticTestSchedule: Created diagnostic test with details
        
        Raises:
            HTTPException: 500 if test creation fails
        
        Example:
            >>> service = ExamService()
            >>> test = service.create_diagnostic_test("child_abc123", "JEE_MAIN")
            >>> print(test.test_id)
            'test_xyz789ghi012'
        """
        try:
            logger.info(f"Creating diagnostic test for child: {child_id}, exam type: {exam_type}")
            
            # Generate unique test ID
            test_id = f"test_{uuid.uuid4().hex[:12]}"
            
            # Set scheduled date to tomorrow
            scheduled_date = datetime.now(timezone.utc) + timedelta(days=1)
            
            # Prepare diagnostic test data
            test_data = {
                "test_id": test_id,
                "child_id": child_id,
                "exam_type": exam_type,
                "scheduled_date": scheduled_date,
                "duration_minutes": 180,  # 3 hours
                "total_questions": 200,
                "status": "scheduled",
                "created_at": SERVER_TIMESTAMP
            }
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Store diagnostic test in Firestore
            tests_ref = db.collection("diagnostic_tests")
            tests_ref.document(test_id).set(test_data)
            
            logger.info(f"Diagnostic test created successfully: {test_id}")
            
            # Return diagnostic test schedule
            return DiagnosticTestSchedule(
                test_id=test_id,
                child_id=child_id,
                exam_type=exam_type,
                scheduled_date=scheduled_date,
                duration_minutes=180,
                total_questions=200,
                status="scheduled"
            )
        
        except Exception as e:
            logger.error(f"Error creating diagnostic test for child {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create diagnostic test. Please try again later."
            )
    
    @staticmethod
    def select_exam(
        child_id: str,
        parent_id: str,
        selection: ExamSelectionRequest
    ) -> ExamSelectionResponse:
        """
        Select exam for a child with subject preferences.
        
        Validates child ownership, exam date, and subject preferences.
        Creates a diagnostic test and stores the exam selection in Firestore.
        
        Args:
            child_id: Unique identifier for the child
            parent_id: Unique identifier for the parent (for verification)
            selection: ExamSelectionRequest with exam details and preferences
        
        Returns:
            ExamSelectionResponse: Exam selection with diagnostic test ID
        
        Raises:
            HTTPException: 404 if child not found
            HTTPException: 403 if parent doesn't own the child
            HTTPException: 400 if validation fails
            HTTPException: 500 if selection fails
        
        Example:
            >>> service = ExamService()
            >>> request = ExamSelectionRequest(
            ...     exam_type="JEE_MAIN",
            ...     exam_date=datetime(2026, 1, 15),
            ...     subject_preferences={"Physics": 35, "Chemistry": 30, "Mathematics": 35}
            ... )
            >>> response = service.select_exam("child_abc123", "parent_xyz789", request)
        """
        try:
            logger.info(f"Selecting exam for child: {child_id}, parent: {parent_id}")
            
            # Verify child exists and belongs to parent
            child_service = ChildService()
            child_profile = child_service.get_child_by_id(child_id)
            
            if child_profile.parent_id != parent_id:
                logger.warning(f"Parent {parent_id} attempted to select exam for child {child_id} owned by {child_profile.parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to select exam for this child"
                )
            
            # Validate exam date is in the future
            if not validate_exam_date(selection.exam_date, min_days=30):
                logger.warning(f"Invalid exam date: {selection.exam_date}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Exam date must be at least 30 days in the future"
                )
            
            # Validate subject preferences sum to 100
            total_weight = sum(selection.subject_preferences.values())
            if total_weight != 100:
                logger.warning(f"Subject preferences do not sum to 100. Total: {total_weight}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject weightages must sum to 100. Current total: {total_weight}"
                )
            
            # Calculate days until exam
            days_until_exam = calculate_days_until(selection.exam_date)
            
            # Create diagnostic test
            diagnostic_test = ExamService.create_diagnostic_test(child_id, selection.exam_type)
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Prepare exam selection data
            selection_data = {
                "child_id": child_id,
                "parent_id": parent_id,
                "exam_type": selection.exam_type,
                "exam_date": selection.exam_date,
                "subject_preferences": selection.subject_preferences,
                "days_until_exam": days_until_exam,
                "diagnostic_test_id": diagnostic_test.test_id,
                "created_at": SERVER_TIMESTAMP
            }
            
            # Store exam selection in Firestore
            selections_ref = db.collection("exam_selections")
            selections_ref.document(child_id).set(selection_data)
            
            logger.info(f"Exam selected successfully for child: {child_id}")
            
            # Retrieve created selection to get server timestamp
            created_doc = selections_ref.document(child_id).get()
            created_data = created_doc.to_dict()
            
            # Return response
            return ExamSelectionResponse(
                child_id=child_id,
                exam_type=created_data["exam_type"],
                exam_date=created_data["exam_date"],
                subject_preferences=created_data["subject_preferences"],
                days_until_exam=days_until_exam,
                diagnostic_test_id=diagnostic_test.test_id,
                created_at=created_data["created_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error selecting exam for child {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to select exam. Please try again later."
            )
    
    @staticmethod
    def get_exam_selection(child_id: str) -> ExamSelectionResponse:
        """
        Retrieve exam selection for a child.
        
        Fetches the exam selection details from Firestore.
        
        Args:
            child_id: Unique identifier for the child
        
        Returns:
            ExamSelectionResponse: Exam selection with details
        
        Raises:
            HTTPException: 404 if exam selection not found
            HTTPException: 500 if retrieval fails
        
        Example:
            >>> service = ExamService()
            >>> response = service.get_exam_selection("child_abc123")
            >>> print(response.exam_type)
            'JEE_MAIN'
        """
        try:
            logger.info(f"Retrieving exam selection for child: {child_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Get exam selection document
            selection_ref = db.collection("exam_selections").document(child_id)
            selection_doc = selection_ref.get()
            
            if not selection_doc.exists:
                logger.warning(f"Exam selection not found for child: {child_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam selection not found for child: {child_id}"
                )
            
            # Get selection data
            selection_data = selection_doc.to_dict()
            
            logger.info(f"Exam selection retrieved successfully for child: {child_id}")
            
            # Recalculate days until exam (in case time has passed)
            try:
                days_until_exam = calculate_days_until(selection_data["exam_date"])
            except ValueError:
                # Exam date is in the past
                days_until_exam = 0
            
            # Return response
            return ExamSelectionResponse(
                child_id=selection_data["child_id"],
                exam_type=selection_data["exam_type"],
                exam_date=selection_data["exam_date"],
                subject_preferences=selection_data["subject_preferences"],
                days_until_exam=days_until_exam,
                diagnostic_test_id=selection_data["diagnostic_test_id"],
                created_at=selection_data["created_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error retrieving exam selection for child {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve exam selection. Please try again later."
            )
    
    @staticmethod
    def update_subject_preferences(
        child_id: str,
        parent_id: str,
        preferences: Dict[str, int]
    ) -> ExamSelectionResponse:
        """
        Update subject preferences for an exam selection.
        
        Validates parent ownership and ensures weightages sum to 100.
        
        Args:
            child_id: Unique identifier for the child
            parent_id: Unique identifier for the parent (for verification)
            preferences: Dictionary of subject weightages
        
        Returns:
            ExamSelectionResponse: Updated exam selection
        
        Raises:
            HTTPException: 404 if exam selection not found
            HTTPException: 403 if parent doesn't own the child
            HTTPException: 400 if weightages don't sum to 100
            HTTPException: 500 if update fails
        
        Example:
            >>> service = ExamService()
            >>> prefs = {"Physics": 40, "Chemistry": 35, "Mathematics": 25}
            >>> response = service.update_subject_preferences("child_abc123", "parent_xyz789", prefs)
        """
        try:
            logger.info(f"Updating subject preferences for child: {child_id}")
            
            # Verify child exists and belongs to parent
            child_service = ChildService()
            child_profile = child_service.get_child_by_id(child_id)
            
            if child_profile.parent_id != parent_id:
                logger.warning(f"Parent {parent_id} attempted to update preferences for child {child_id} owned by {child_profile.parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update preferences for this child"
                )
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Get exam selection document
            selection_ref = db.collection("exam_selections").document(child_id)
            selection_doc = selection_ref.get()
            
            if not selection_doc.exists:
                logger.warning(f"Exam selection not found for child: {child_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Exam selection not found for child: {child_id}"
                )
            
            # Validate weightages sum to 100
            total_weight = sum(preferences.values())
            if total_weight != 100:
                logger.warning(f"Subject preferences do not sum to 100. Total: {total_weight}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject weightages must sum to 100. Current total: {total_weight}"
                )
            
            # Update subject preferences
            selection_ref.update({
                "subject_preferences": preferences,
                "updated_at": SERVER_TIMESTAMP
            })
            
            logger.info(f"Subject preferences updated successfully for child: {child_id}")
            
            # Retrieve updated selection
            updated_doc = selection_ref.get()
            updated_data = updated_doc.to_dict()
            
            # Recalculate days until exam
            try:
                days_until_exam = calculate_days_until(updated_data["exam_date"])
            except ValueError:
                days_until_exam = 0
            
            # Return response
            return ExamSelectionResponse(
                child_id=updated_data["child_id"],
                exam_type=updated_data["exam_type"],
                exam_date=updated_data["exam_date"],
                subject_preferences=updated_data["subject_preferences"],
                days_until_exam=days_until_exam,
                diagnostic_test_id=updated_data["diagnostic_test_id"],
                created_at=updated_data["created_at"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error updating subject preferences for child {child_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subject preferences. Please try again later."
            )
    
    @staticmethod
    def get_diagnostic_test(test_id: str) -> DiagnosticTestSchedule:
        """
        Retrieve diagnostic test by test ID.
        
        Fetches diagnostic test details from Firestore.
        
        Args:
            test_id: Unique identifier for the diagnostic test
        
        Returns:
            DiagnosticTestSchedule: Diagnostic test details
        
        Raises:
            HTTPException: 404 if diagnostic test not found
            HTTPException: 500 if retrieval fails
        
        Example:
            >>> service = ExamService()
            >>> test = service.get_diagnostic_test("test_xyz789")
            >>> print(test.status)
            'scheduled'
        """
        try:
            logger.info(f"Retrieving diagnostic test: {test_id}")
            
            # Get Firestore client
            db = get_firestore_client()
            
            # Get diagnostic test document
            test_ref = db.collection("diagnostic_tests").document(test_id)
            test_doc = test_ref.get()
            
            if not test_doc.exists:
                logger.warning(f"Diagnostic test not found: {test_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Diagnostic test not found: {test_id}"
                )
            
            # Get test data
            test_data = test_doc.to_dict()
            
            logger.info(f"Diagnostic test retrieved successfully: {test_id}")
            
            # Return diagnostic test schedule
            return DiagnosticTestSchedule(
                test_id=test_data["test_id"],
                child_id=test_data["child_id"],
                exam_type=test_data["exam_type"],
                scheduled_date=test_data["scheduled_date"],
                duration_minutes=test_data["duration_minutes"],
                total_questions=test_data["total_questions"],
                status=test_data["status"]
            )
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            logger.error(f"Error retrieving diagnostic test {test_id}: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve diagnostic test. Please try again later."
            )
