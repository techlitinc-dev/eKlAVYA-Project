"""
Schedule Service for AI-Powered Study Schedule Generation - Mentor AI Platform.

This module provides the main orchestration service for complete schedule generation,
coordinating analytics retrieval, priority calculation, context building, AI generation,
parsing, validation, and storage.

Main Functions:
- generate_schedule: Complete workflow for generating personalized schedules
- get_schedule: Retrieve schedule by ID
- get_student_schedules: Get all schedules for a student
- get_schedule_history: Get schedule history for a student
- update_schedule: Update existing schedule
- delete_schedule: Soft delete (mark as abandoned)

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.schedule_service import ScheduleService
    >>> from models.schedule_models import ScheduleRequest
    >>> from datetime import date, timedelta
    >>> 
    >>> # Initialize service
    >>> service = ScheduleService()
    >>> 
    >>> # Create schedule request
    >>> request = ScheduleRequest(
    ...     student_id="student_123",
    ...     analytics_id="analytics_456",
    ...     exam_type="JEE_MAIN",
    ...     exam_date=date.today() + timedelta(days=75),
    ...     daily_study_hours=5.0
    ... )
    >>> 
    >>> # Generate complete schedule
    >>> schedule = service.generate_schedule(request)
    >>> print(f"Generated schedule: {schedule.schedule_id}")
    >>> print(f"Total days: {len(schedule.days)}")
    >>> 
    >>> # Retrieve schedule
    >>> retrieved = service.get_schedule(schedule.schedule_id)
    >>> print(f"Status: {retrieved.status}")
"""

import logging
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

from google.cloud import firestore
from pydantic import ValidationError

from models.schedule_models import (
    Schedule,
    ScheduleRequest,
    ScheduleDay,
    DailyTopic,
    TopicPriority as ScheduleTopicPriority,
    ExamType,
    ScheduleStatus
)
from models.analytics_models import AnalyticsReport
from services.priority_calculator import PriorityCalculator
from services.gemini_scheduler_service import GeminiSchedulerService
from utils.time_calculator import (
    calculate_available_days,
    calculate_total_study_hours,
    calculate_revision_days,
    calculate_practice_test_days,
    calculate_buffer_days,
    validate_time_feasibility
)
from utils.schedule_context_builder import build_complete_context
from utils.schedule_parser import parse_schedule_json
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)

# Firestore collections
SCHEDULES_COLLECTION = "schedules"
ANALYTICS_COLLECTION = "analytics"
STUDENTS_COLLECTION = "students"


class ScheduleServiceError(Exception):
    """Base exception for Schedule Service errors."""
    pass


class ScheduleNotFoundError(ScheduleServiceError):
    """Exception raised when schedule is not found."""
    pass


class AnalyticsNotFoundError(ScheduleServiceError):
    """Exception raised when analytics data is not found."""
    pass


class StudentNotFoundError(ScheduleServiceError):
    """Exception raised when student profile is not found."""
    pass


class ScheduleGenerationError(ScheduleServiceError):
    """Exception raised when schedule generation fails."""
    pass


def fetch_analytics_from_firestore(analytics_id: str) -> Dict[str, Any]:
    """
    Fetch analytics data from Firestore.
    
    Args:
        analytics_id: Analytics report identifier
    
    Returns:
        Analytics data dictionary
    
    Raises:
        AnalyticsNotFoundError: If analytics not found
    
    Example:
        >>> analytics = fetch_analytics_from_firestore("analytics_123")
        >>> print(analytics["overall_accuracy"])
    """
    logger.info(f"Fetching analytics from Firestore: {analytics_id}")
    
    try:
        db = get_firestore_client()
        doc_ref = db.collection(ANALYTICS_COLLECTION).document(analytics_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise AnalyticsNotFoundError(
                f"Analytics not found: {analytics_id}"
            )
        
        analytics_data = doc.to_dict()
        logger.info(f"Successfully fetched analytics: {analytics_id}")
        
        return analytics_data
        
    except AnalyticsNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics {analytics_id}: {str(e)}")
        raise ScheduleServiceError(f"Failed to fetch analytics: {str(e)}")


def fetch_student_profile_from_firestore(student_id: str) -> Dict[str, Any]:
    """
    Fetch student profile from Firestore.
    
    Args:
        student_id: Student identifier
    
    Returns:
        Student profile dictionary
    
    Raises:
        StudentNotFoundError: If student not found
    
    Example:
        >>> profile = fetch_student_profile_from_firestore("student_123")
        >>> print(profile["name"])
    """
    logger.info(f"Fetching student profile from Firestore: {student_id}")
    
    try:
        db = get_firestore_client()
        doc_ref = db.collection(STUDENTS_COLLECTION).document(student_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise StudentNotFoundError(
                f"Student not found: {student_id}"
            )
        
        profile_data = doc.to_dict()
        logger.info(f"Successfully fetched student profile: {student_id}")
        
        return profile_data
        
    except StudentNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching student {student_id}: {str(e)}")
        raise ScheduleServiceError(f"Failed to fetch student profile: {str(e)}")


def fetch_schedule_from_firestore(schedule_id: str) -> Dict[str, Any]:
    """
    Fetch schedule data from Firestore.
    
    Args:
        schedule_id: Schedule identifier
    
    Returns:
        Schedule data dictionary
    
    Raises:
        ScheduleNotFoundError: If schedule not found
    
    Example:
        >>> schedule_data = fetch_schedule_from_firestore("schedule_123")
        >>> print(schedule_data["total_days"])
    """
    logger.info(f"Fetching schedule from Firestore: {schedule_id}")
    
    try:
        db = get_firestore_client()
        doc_ref = db.collection(SCHEDULES_COLLECTION).document(schedule_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise ScheduleNotFoundError(
                f"Schedule not found: {schedule_id}"
            )
        
        schedule_data = doc.to_dict()
        logger.info(f"Successfully fetched schedule: {schedule_id}")
        
        return schedule_data
        
    except ScheduleNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error fetching schedule {schedule_id}: {str(e)}")
        raise ScheduleServiceError(f"Failed to fetch schedule: {str(e)}")


def save_schedule_to_firestore(schedule: Schedule) -> bool:
    """
    Save schedule to Firestore.
    
    Args:
        schedule: Schedule Pydantic model
    
    Returns:
        True if successful
    
    Raises:
        ScheduleServiceError: If save fails
    
    Example:
        >>> success = save_schedule_to_firestore(schedule)
        >>> print(f"Saved: {success}")
    """
    logger.info(f"Saving schedule to Firestore: {schedule.schedule_id}")
    
    try:
        db = get_firestore_client()
        doc_ref = db.collection(SCHEDULES_COLLECTION).document(schedule.schedule_id)
        
        # Convert schedule to dict (using Pydantic's dict method)
        schedule_dict = schedule.model_dump(mode='json')
        
        # Save to Firestore
        doc_ref.set(schedule_dict)
        
        logger.info(f"Successfully saved schedule: {schedule.schedule_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving schedule {schedule.schedule_id}: {str(e)}")
        raise ScheduleServiceError(f"Failed to save schedule: {str(e)}")


def load_syllabus_weightages(exam_type: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Load syllabus weightages for exam type.
    
    Args:
        exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
    
    Returns:
        Dictionary mapping (subject, topic) to weightage info
    
    Example:
        >>> weightages = load_syllabus_weightages("JEE_MAIN")
        >>> physics_thermo = weightages[("Physics", "Thermodynamics")]
        >>> print(physics_thermo["weightage"])
    """
    logger.info(f"Loading syllabus weightages for {exam_type}")
    
    # Determine subjects based on exam type
    if exam_type == "NEET":
        subjects = ["Physics", "Chemistry", "Biology"]
    else:  # JEE_MAIN or JEE_ADVANCED
        subjects = ["Physics", "Chemistry", "Mathematics"]
    
    weightages = {}
    data_dir = Path(__file__).parent.parent / "data" / "syllabus"
    
    for subject in subjects:
        file_path = data_dir / f"{exam_type}_{subject}.json"
        
        if not file_path.exists():
            logger.warning(f"Syllabus file not found: {file_path}")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                syllabus_data = json.load(f)
            
            # Extract weightages
            for chapter in syllabus_data.get("chapters", []):
                for topic in chapter.get("topics", []):
                    key = (subject, topic.get("topic_name"))
                    weightages[key] = {
                        "weightage": float(topic.get("weightage", 0.0)),
                        "difficulty": topic.get("difficulty", "medium"),
                        "chapter": chapter.get("chapter_name")
                    }
            
            logger.debug(f"Loaded {len(weightages)} weightages from {subject}")
            
        except Exception as e:
            logger.error(f"Error loading syllabus for {subject}: {str(e)}")
    
    logger.info(f"Loaded total {len(weightages)} topic weightages for {exam_type}")
    return weightages


class ScheduleService:
    """
    Main service for orchestrating AI-powered schedule generation.
    
    This service coordinates all components including analytics retrieval,
    priority calculation, context building, AI generation, parsing, and storage.
    
    Attributes:
        gemini_service: Gemini AI service for schedule generation
        priority_calculator: Service for calculating topic priorities
    
    Example:
        >>> service = ScheduleService()
        >>> schedule = service.generate_schedule(request)
        >>> print(f"Generated {len(schedule.days)} day schedule")
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize Schedule Service.
        
        Args:
            gemini_api_key: Optional Google API key for Gemini
        """
        logger.info("Initializing ScheduleService")
        
        # Initialize Gemini service
        self.gemini_service = GeminiSchedulerService(api_key=gemini_api_key)
        
        # Priority calculator will be initialized per request based on exam type
        self.priority_calculator = None
        
        logger.info("ScheduleService initialized successfully")
    
    def validate_schedule_request(
        self,
        request: ScheduleRequest
    ) -> Tuple[bool, List[str]]:
        """
        Validate schedule request before processing.
        
        Args:
            request: ScheduleRequest model
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        
        Example:
            >>> is_valid, errors = service.validate_schedule_request(request)
            >>> if not is_valid:
            ...     print(f"Errors: {errors}")
        """
        errors = []
        
        # Check exam_date is in future
        if request.exam_date <= date.today():
            errors.append(
                f"Exam date must be in the future. "
                f"Got: {request.exam_date}, Today: {date.today()}"
            )
        
        # Check daily_hours is reasonable
        if not 2.0 <= request.daily_study_hours <= 8.0:
            errors.append(
                f"Daily study hours must be between 2 and 8. "
                f"Got: {request.daily_study_hours}"
            )
        
        # Check analytics exists
        try:
            fetch_analytics_from_firestore(request.analytics_id)
        except AnalyticsNotFoundError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Error validating analytics: {str(e)}")
        
        # Check student exists
        try:
            fetch_student_profile_from_firestore(request.student_id)
        except StudentNotFoundError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Error validating student: {str(e)}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Schedule request validation passed for student {request.student_id}")
        else:
            logger.warning(f"Schedule request validation failed: {len(errors)} errors")
        
        return is_valid, errors
    
    def generate_schedule(self, request: ScheduleRequest) -> Schedule:
        """
        Generate complete personalized study schedule.
        
        This is the main orchestration function that coordinates all steps:
        1. Validate request
        2. Fetch analytics and student data
        3. Load syllabus weightages
        4. Calculate topic priorities
        5. Calculate time constraints
        6. Build context for Gemini
        7. Generate schedule with AI
        8. Parse and validate response
        9. Save to Firestore
        10. Return Schedule object
        
        Args:
            request: ScheduleRequest with student info and preferences
        
        Returns:
            Complete Schedule object
        
        Raises:
            ScheduleGenerationError: If any step fails
        
        Example:
            >>> request = ScheduleRequest(...)
            >>> schedule = service.generate_schedule(request)
            >>> print(f"Schedule ID: {schedule.schedule_id}")
        """
        logger.info(
            f"Starting schedule generation for student {request.student_id}, "
            f"exam: {request.exam_type}, date: {request.exam_date}"
        )
        
        start_time = datetime.now()
        
        try:
            # Step 1: Validate request
            logger.info("Step 1: Validating schedule request")
            is_valid, validation_errors = self.validate_schedule_request(request)
            if not is_valid:
                error_msg = f"Invalid request: {'; '.join(validation_errors)}"
                raise ScheduleGenerationError(error_msg)
            
            # Step 2: Fetch analytics from Firestore
            logger.info("Step 2: Fetching analytics data")
            analytics_data = fetch_analytics_from_firestore(request.analytics_id)
            
            # Step 3: Fetch student profile
            logger.info("Step 3: Fetching student profile")
            student_profile = fetch_student_profile_from_firestore(request.student_id)
            
            # Step 4: Load syllabus weightages
            logger.info("Step 4: Loading syllabus weightages")
            weightages = load_syllabus_weightages(request.exam_type.value)
            
            # Step 5: Initialize priority calculator for exam type
            logger.info("Step 5: Initializing priority calculator")
            self.priority_calculator = PriorityCalculator(exam_type=request.exam_type.value)
            
            # Step 6: Calculate topic priorities from analytics
            logger.info("Step 6: Calculating topic priorities")
            topic_performances = analytics_data.get("topic_analysis", [])
            
            priority_topics = []
            for topic_data in topic_performances:
                try:
                    priority = self.priority_calculator.calculate_topic_priority(
                        topic_name=topic_data.get("topic"),
                        subject=topic_data.get("subject"),
                        current_accuracy=topic_data.get("accuracy", 0.0),
                        difficulty=topic_data.get("difficulty", "medium")
                    )
                    # Convert to dict for context builder
                    priority_topics.append({
                        "topic": priority.topic,
                        "subject": priority.subject,
                        "priority_score": priority.priority_score,
                        "priority_level": priority.priority_label.value,
                        "current_accuracy": priority.current_accuracy,
                        "weightage": priority.weightage,
                        "estimated_hours": priority.estimated_hours
                    })
                except Exception as e:
                    logger.warning(f"Failed to calculate priority for topic: {str(e)}")
            
            # Sort by priority score
            priority_topics.sort(key=lambda x: x["priority_score"], reverse=True)
            logger.info(f"Calculated priorities for {len(priority_topics)} topics")
            
            # Step 7: Calculate time constraints
            logger.info("Step 7: Calculating time constraints")
            days_until_exam = (request.exam_date - date.today()).days
            available_days = calculate_available_days(
                date.today(),
                request.exam_date,
                exclude_weekends=False
            )
            
            total_hours = calculate_total_study_hours(
                available_days,
                request.daily_study_hours,
                apply_buffer=True
            )
            
            revision_days = calculate_revision_days(available_days)
            practice_test_days = calculate_practice_test_days(available_days)
            buffer_days = calculate_buffer_days(available_days)
            
            # Validate feasibility
            is_feasible, deficit, recommendations = validate_time_feasibility(
                priority_topics,
                total_hours
            )
            
            if not is_feasible:
                logger.warning(f"Schedule may not be feasible: {deficit}h deficit")
                logger.warning(f"Recommendations: {recommendations}")
            
            constraints = {
                "total_days": available_days,
                "daily_hours": request.daily_study_hours,
                "total_hours": total_hours,
                "revision_days": revision_days,
                "practice_test_days": practice_test_days,
                "buffer_days": buffer_days,
                "must_cover_critical": True,
                "balance_subjects": True
            }
            
            logger.info(
                f"Time constraints: {available_days} days, "
                f"{total_hours:.1f}h total, feasible: {is_feasible}"
            )
            
            # Step 8: Build context for Gemini
            logger.info("Step 8: Building context for Gemini")
            
            # Prepare student profile for context
            profile_for_context = {
                "student_id": request.student_id,
                "exam_type": request.exam_type.value,
                "exam_date": request.exam_date,
                "daily_study_hours": request.daily_study_hours,
                "preferences": request.preferences or {}
            }
            
            # Prepare analytics for context
            analytics_for_context = {
                "overall_score": analytics_data.get("total_score", 0),
                "max_score": analytics_data.get("max_score", 100),
                "percentage": analytics_data.get("percentage", 0.0),
                "accuracy": analytics_data.get("overall_accuracy", 0.0),
                "subject_scores": analytics_data.get("subject_scores", {}),
                "strong_topics": analytics_data.get("strong_topics", [])[:5],
                "weak_topics": analytics_data.get("weak_topics", [])[:10]
            }
            
            context = build_complete_context(
                student_profile=profile_for_context,
                analytics_data=analytics_for_context,
                priority_topics=priority_topics,
                weightages=weightages,
                constraints=constraints
            )
            
            logger.info(f"Built context: {len(context)} characters")
            
            # Step 9: Generate schedule with Gemini
            logger.info("Step 9: Generating schedule with Gemini AI")
            schedule = self.gemini_service.generate_schedule(
                context=context,
                student_id=request.student_id,
                analytics_id=request.analytics_id,
                exam_type=request.exam_type.value,
                exam_date=request.exam_date,
                daily_study_hours=request.daily_study_hours,
                enable_refinement=True
            )
            
            logger.info(
                f"Generated schedule: {schedule.schedule_id}, "
                f"{len(schedule.days)} days"
            )
            
            # Step 10: Save to Firestore
            logger.info("Step 10: Saving schedule to Firestore")
            save_schedule_to_firestore(schedule)
            
            # Calculate total time
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"Schedule generation completed successfully in {elapsed_time:.2f}s: "
                f"{schedule.schedule_id}"
            )
            
            return schedule
            
        except (AnalyticsNotFoundError, StudentNotFoundError, ScheduleGenerationError):
            raise
        except Exception as e:
            elapsed_time = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Schedule generation failed after {elapsed_time:.2f}s: {str(e)}",
                exc_info=True
            )
            raise ScheduleGenerationError(f"Failed to generate schedule: {str(e)}")
    
    def get_schedule(self, schedule_id: str) -> Schedule:
        """
        Retrieve schedule by ID.
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            Schedule object
        
        Raises:
            ScheduleNotFoundError: If schedule not found
        
        Example:
            >>> schedule = service.get_schedule("schedule_123")
            >>> print(f"Status: {schedule.status}")
        """
        logger.info(f"Retrieving schedule: {schedule_id}")
        
        try:
            # Fetch from Firestore
            schedule_data = fetch_schedule_from_firestore(schedule_id)
            
            # Parse to Schedule model
            # Note: We need to handle dates and datetimes
            if "exam_date" in schedule_data and isinstance(schedule_data["exam_date"], str):
                schedule_data["exam_date"] = datetime.fromisoformat(
                    schedule_data["exam_date"]
                ).date()
            
            if "generated_date" in schedule_data and isinstance(schedule_data["generated_date"], str):
                schedule_data["generated_date"] = datetime.fromisoformat(
                    schedule_data["generated_date"]
                )
            
            # Parse days
            if "days" in schedule_data:
                for day in schedule_data["days"]:
                    if "schedule_date" in day and isinstance(day["schedule_date"], str):
                        day["schedule_date"] = datetime.fromisoformat(
                            day["schedule_date"]
                        ).date()
            
            schedule = Schedule(**schedule_data)
            
            logger.info(f"Successfully retrieved schedule: {schedule_id}")
            return schedule
            
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving schedule {schedule_id}: {str(e)}")
            raise ScheduleServiceError(f"Failed to retrieve schedule: {str(e)}")
    
    def get_student_schedules(
        self,
        student_id: str,
        status_filter: Optional[str] = None
    ) -> List[Schedule]:
        """
        Get all schedules for a student.
        
        Args:
            student_id: Student identifier
            status_filter: Optional filter by status (active, completed, abandoned)
        
        Returns:
            List of Schedule objects
        
        Example:
            >>> schedules = service.get_student_schedules("student_123")
            >>> active = service.get_student_schedules("student_123", "active")
        """
        logger.info(f"Retrieving schedules for student: {student_id}")
        
        try:
            db = get_firestore_client()
            query = db.collection(SCHEDULES_COLLECTION).where(
                "student_id", "==", student_id
            )
            
            if status_filter:
                query = query.where("status", "==", status_filter)
            
            # Order by generated_date (newest first)
            query = query.order_by("generated_date", direction=firestore.Query.DESCENDING)
            
            docs = query.stream()
            
            schedules = []
            for doc in docs:
                schedule_data = doc.to_dict()
                
                # Parse dates
                if "exam_date" in schedule_data and isinstance(schedule_data["exam_date"], str):
                    schedule_data["exam_date"] = datetime.fromisoformat(
                        schedule_data["exam_date"]
                    ).date()
                
                if "generated_date" in schedule_data and isinstance(schedule_data["generated_date"], str):
                    schedule_data["generated_date"] = datetime.fromisoformat(
                        schedule_data["generated_date"]
                    )
                
                # Parse days
                if "days" in schedule_data:
                    for day in schedule_data["days"]:
                        if "schedule_date" in day and isinstance(day["schedule_date"], str):
                            day["schedule_date"] = datetime.fromisoformat(
                                day["schedule_date"]
                            ).date()
                
                try:
                    schedule = Schedule(**schedule_data)
                    schedules.append(schedule)
                except Exception as e:
                    logger.warning(f"Failed to parse schedule {doc.id}: {str(e)}")
            
            logger.info(f"Retrieved {len(schedules)} schedules for student {student_id}")
            return schedules
            
        except Exception as e:
            logger.error(f"Error retrieving student schedules: {str(e)}")
            raise ScheduleServiceError(f"Failed to retrieve student schedules: {str(e)}")
    
    def get_schedule_history(
        self,
        student_id: str,
        limit: int = 10
    ) -> List[Schedule]:
        """
        Get schedule history for a student.
        
        Args:
            student_id: Student identifier
            limit: Maximum number of schedules to return
        
        Returns:
            List of Schedule objects (newest first)
        
        Example:
            >>> history = service.get_schedule_history("student_123", limit=5)
            >>> print(f"Total schedules: {len(history)}")
        """
        logger.info(f"Retrieving schedule history for student: {student_id}")
        
        try:
            schedules = self.get_student_schedules(student_id)
            
            # Already sorted by generated_date (newest first)
            # Limit results
            return schedules[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving schedule history: {str(e)}")
            raise ScheduleServiceError(f"Failed to retrieve schedule history: {str(e)}")
    
    def update_schedule(
        self,
        schedule_id: str,
        updates: Dict[str, Any]
    ) -> Schedule:
        """
        Update existing schedule.
        
        Args:
            schedule_id: Schedule identifier
            updates: Dictionary of fields to update
        
        Returns:
            Updated Schedule object
        
        Example:
            >>> updates = {"status": "completed"}
            >>> schedule = service.update_schedule("schedule_123", updates)
        """
        logger.info(f"Updating schedule: {schedule_id}")
        
        try:
            # Fetch existing schedule
            schedule_data = fetch_schedule_from_firestore(schedule_id)
            
            # Merge updates
            schedule_data.update(updates)
            
            # Parse to Schedule model to validate
            # Handle date conversions
            if "exam_date" in schedule_data and isinstance(schedule_data["exam_date"], str):
                schedule_data["exam_date"] = datetime.fromisoformat(
                    schedule_data["exam_date"]
                ).date()
            
            if "generated_date" in schedule_data and isinstance(schedule_data["generated_date"], str):
                schedule_data["generated_date"] = datetime.fromisoformat(
                    schedule_data["generated_date"]
                )
            
            if "days" in schedule_data:
                for day in schedule_data["days"]:
                    if "schedule_date" in day and isinstance(day["schedule_date"], str):
                        day["schedule_date"] = datetime.fromisoformat(
                            day["schedule_date"]
                        ).date()
            
            schedule = Schedule(**schedule_data)
            
            # Save to Firestore
            save_schedule_to_firestore(schedule)
            
            logger.info(f"Successfully updated schedule: {schedule_id}")
            return schedule
            
        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
            raise ScheduleServiceError(f"Failed to update schedule: {str(e)}")
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Soft delete schedule (mark as abandoned).
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            True if successful
        
        Example:
            >>> success = service.delete_schedule("schedule_123")
            >>> print(f"Deleted: {success}")
        """
        logger.info(f"Deleting schedule (soft): {schedule_id}")
        
        try:
            # Update status to abandoned
            updates = {
                "status": ScheduleStatus.ABANDONED.value
            }
            
            self.update_schedule(schedule_id, updates)
            
            logger.info(f"Successfully deleted schedule: {schedule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting schedule {schedule_id}: {str(e)}")
            raise ScheduleServiceError(f"Failed to delete schedule: {str(e)}")

