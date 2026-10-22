"""
Progress Tracker for Schedule Completion Monitoring - Mentor AI Platform.

This module provides comprehensive progress tracking services for monitoring
student schedule completion, calculating metrics, and triggering adaptive
adjustments when needed.

Functions:
- update_daily_progress: Update progress for a specific day
- mark_topic_complete: Mark individual topic as complete
- get_progress_summary: Get overall progress statistics
- get_today_tasks: Get tasks scheduled for today
- calculate_completion_percentage: Calculate overall completion
- get_progress_history: Get historical progress updates
- get_incomplete_topics: Find all incomplete topics
- calculate_study_streak: Calculate consecutive study days

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.progress_tracker import ProgressTracker
    >>> from models.schedule_models import ProgressUpdate
    >>> from datetime import date
    >>> 
    >>> # Initialize tracker
    >>> tracker = ProgressTracker()
    >>> 
    >>> # Update daily progress
    >>> progress = ProgressUpdate(
    ...     schedule_id="schedule_123",
    ...     day_number=1,
    ...     update_date=date.today(),
    ...     status="completed",
    ...     topics_completed=[
    ...         {
    ...             "topic": "Thermodynamics",
    ...             "time_spent": 2.5,
    ...             "completion_percentage": 100.0,
    ...             "notes": "Completed all subtopics"
    ...         }
    ...     ],
    ...     total_time_spent=5.0,
    ...     completion_percentage=100.0
    ... )
    >>> tracker.update_daily_progress("schedule_123", 1, progress)
    >>> 
    >>> # Get today's tasks
    >>> tasks = tracker.get_today_tasks("schedule_123")
    >>> print(f"Today: {len(tasks)} topics to study")
    >>> 
    >>> # Get progress summary
    >>> summary = tracker.get_progress_summary("schedule_123")
    >>> print(f"Completion: {summary['completion_percentage']}%")
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from google.cloud import firestore
from pydantic import ValidationError

from models.schedule_models import (
    Schedule,
    ScheduleDay,
    DailyTopic,
    ProgressUpdate,
    DayStatus,
    ScheduleStatus
)
from services.schedule_service import (
    fetch_schedule_from_firestore,
    save_schedule_to_firestore,
    ScheduleNotFoundError,
    ScheduleServiceError
)
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)

# Firestore collections
SCHEDULES_COLLECTION = "schedules"
PROGRESS_SUBCOLLECTION = "progress"


class ProgressTrackerError(Exception):
    """Base exception for Progress Tracker errors."""
    pass


class DayNotFoundError(ProgressTrackerError):
    """Exception raised when day is not found in schedule."""
    pass


class TopicNotFoundError(ProgressTrackerError):
    """Exception raised when topic is not found in day."""
    pass


# ==================== Firestore Helper Functions ====================


def save_progress_to_firestore(
    schedule_id: str,
    progress: ProgressUpdate
) -> bool:
    """
    Save progress update to Firestore as a subcollection of the schedule.
    
    Args:
        schedule_id: Schedule identifier
        progress: Progress update to save
    
    Returns:
        True if saved successfully
    
    Raises:
        ProgressTrackerError: If save fails
    
    Example:
        >>> progress = ProgressUpdate(...)
        >>> save_progress_to_firestore("schedule_123", progress)
        True
    """
    logger.info(f"Saving progress to Firestore: {schedule_id}, day {progress.day_number}")
    
    try:
        db = get_firestore_client()
        
        # Save to subcollection: schedules/{schedule_id}/progress/{day_number}
        progress_ref = (
            db.collection(SCHEDULES_COLLECTION)
            .document(schedule_id)
            .collection(PROGRESS_SUBCOLLECTION)
            .document(str(progress.day_number))
        )
        
        progress_dict = progress.model_dump(mode='json')
        progress_ref.set(progress_dict)
        
        logger.info(f"Successfully saved progress for day {progress.day_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving progress {schedule_id}: {str(e)}")
        raise ProgressTrackerError(f"Failed to save progress: {str(e)}")


def fetch_progress_from_firestore(
    schedule_id: str,
    day_number: int
) -> Optional[Dict[str, Any]]:
    """
    Fetch progress update for a specific day from Firestore.
    
    Args:
        schedule_id: Schedule identifier
        day_number: Day number to fetch
    
    Returns:
        Progress data dictionary, or None if not found
    
    Example:
        >>> progress = fetch_progress_from_firestore("schedule_123", 1)
        >>> print(progress["completion_percentage"])
    """
    logger.info(f"Fetching progress from Firestore: {schedule_id}, day {day_number}")
    
    try:
        db = get_firestore_client()
        
        progress_ref = (
            db.collection(SCHEDULES_COLLECTION)
            .document(schedule_id)
            .collection(PROGRESS_SUBCOLLECTION)
            .document(str(day_number))
        )
        
        doc = progress_ref.get()
        
        if not doc.exists:
            logger.info(f"No progress found for day {day_number}")
            return None
        
        progress_data = doc.to_dict()
        logger.info(f"Successfully fetched progress for day {day_number}")
        
        return progress_data
        
    except Exception as e:
        logger.error(f"Error fetching progress {schedule_id}, day {day_number}: {str(e)}")
        raise ProgressTrackerError(f"Failed to fetch progress: {str(e)}")


def fetch_all_progress(
    schedule_id: str,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch all progress updates for a schedule from Firestore.
    
    Args:
        schedule_id: Schedule identifier
        limit: Maximum number of records to fetch (None for all)
    
    Returns:
        List of progress data dictionaries sorted by date (newest first)
    
    Example:
        >>> all_progress = fetch_all_progress("schedule_123", limit=10)
        >>> print(f"Found {len(all_progress)} progress records")
    """
    logger.info(f"Fetching all progress from Firestore: {schedule_id}")
    
    try:
        db = get_firestore_client()
        
        progress_ref = (
            db.collection(SCHEDULES_COLLECTION)
            .document(schedule_id)
            .collection(PROGRESS_SUBCOLLECTION)
            .order_by('update_date', direction=firestore.Query.DESCENDING)
        )
        
        if limit:
            progress_ref = progress_ref.limit(limit)
        
        docs = progress_ref.stream()
        
        progress_list = []
        for doc in docs:
            progress_data = doc.to_dict()
            progress_list.append(progress_data)
        
        logger.info(f"Successfully fetched {len(progress_list)} progress records")
        return progress_list
        
    except Exception as e:
        logger.error(f"Error fetching all progress {schedule_id}: {str(e)}")
        raise ProgressTrackerError(f"Failed to fetch progress history: {str(e)}")


# ==================== Progress Tracker Class ====================


class ProgressTracker:
    """
    Progress tracking service for monitoring schedule completion and student progress.
    
    This service handles all progress-related operations including updating daily
    progress, marking topics complete, calculating metrics, and triggering
    adaptive adjustments when needed.
    
    Attributes:
        None (stateless service)
    
    Example:
        >>> tracker = ProgressTracker()
        >>> summary = tracker.get_progress_summary("schedule_123")
        >>> print(f"Completion: {summary['completion_percentage']}%")
    """
    
    def __init__(self):
        """Initialize the Progress Tracker."""
        logger.info("ProgressTracker initialized")
    
    def update_daily_progress(
        self,
        schedule_id: str,
        day_number: int,
        progress_data: ProgressUpdate
    ) -> ProgressUpdate:
        """
        Update progress for a specific day.
        
        This function:
        1. Validates day exists in schedule
        2. Updates completion status for day
        3. Stores progress in Firestore (subcollection "progress")
        4. Updates schedule completion percentage
        5. Checks if rescheduling needed
        6. Returns ProgressUpdate object
        
        Args:
            schedule_id: Schedule identifier
            day_number: Day number being updated
            progress_data: Progress update data
        
        Returns:
            Updated ProgressUpdate object
        
        Raises:
            ScheduleNotFoundError: If schedule not found
            DayNotFoundError: If day not found in schedule
            ProgressTrackerError: If update fails
        
        Example:
            >>> progress = ProgressUpdate(
            ...     schedule_id="schedule_123",
            ...     day_number=1,
            ...     update_date=date.today(),
            ...     status="completed",
            ...     topics_completed=[...],
            ...     total_time_spent=5.0,
            ...     completion_percentage=100.0
            ... )
            >>> tracker.update_daily_progress("schedule_123", 1, progress)
        """
        logger.info(f"Updating daily progress: {schedule_id}, day {day_number}")
        
        try:
            # Step 1: Fetch schedule from Firestore
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Step 2: Validate day exists
            if day_number > len(schedule.days):
                raise DayNotFoundError(
                    f"Day {day_number} not found in schedule (total: {len(schedule.days)})"
                )
            
            # Step 3: Get the day to update (0-indexed)
            day_to_update = schedule.days[day_number - 1]
            
            # Step 4: Update day status based on progress
            if progress_data.completion_percentage >= 100.0:
                day_to_update.status = DayStatus.COMPLETED
            elif progress_data.completion_percentage > 0.0:
                day_to_update.status = DayStatus.IN_PROGRESS
            else:
                day_to_update.status = DayStatus.SKIPPED
            
            # Step 5: Update topic completion in the day
            for topic_progress in progress_data.topics_completed:
                topic_name = topic_progress.get('topic')
                
                # Find and update the topic
                for topic in day_to_update.topics:
                    if topic.topic == topic_name:
                        topic.time_spent = topic_progress.get('time_spent', 0.0)
                        topic.completion_notes = topic_progress.get('notes', '')
                        break
            
            # Step 6: Save progress to Firestore subcollection
            save_progress_to_firestore(schedule_id, progress_data)
            
            # Step 7: Update schedule completion percentage
            completion_pct = self.calculate_completion_percentage(schedule_id)
            schedule.completion_percentage = completion_pct
            
            # Step 8: Save updated schedule
            save_schedule_to_firestore(schedule)
            
            # Step 9: Check if rescheduling needed
            self._check_reschedule_trigger(schedule_id, progress_data)
            
            logger.info(
                f"Successfully updated progress for day {day_number}, "
                f"completion: {progress_data.completion_percentage}%"
            )
            
            return progress_data
            
        except (ScheduleNotFoundError, DayNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating daily progress {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to update progress: {str(e)}")
    
    def mark_topic_complete(
        self,
        schedule_id: str,
        day_number: int,
        topic_name: str,
        time_spent: float,
        completion_notes: str = ""
    ) -> bool:
        """
        Mark an individual topic as complete.
        
        This function:
        1. Finds topic in schedule day
        2. Marks as complete
        3. Records time spent
        4. Adds notes
        5. Updates day completion percentage
        6. Saves to Firestore
        
        Args:
            schedule_id: Schedule identifier
            day_number: Day number containing the topic
            topic_name: Name of the topic to mark complete
            time_spent: Actual time spent on topic (hours)
            completion_notes: Optional notes about completion
        
        Returns:
            True if successful
        
        Raises:
            ScheduleNotFoundError: If schedule not found
            DayNotFoundError: If day not found
            TopicNotFoundError: If topic not found
        
        Example:
            >>> tracker.mark_topic_complete(
            ...     "schedule_123",
            ...     day_number=1,
            ...     topic_name="Thermodynamics",
            ...     time_spent=2.5,
            ...     completion_notes="Completed all subtopics successfully"
            ... )
            True
        """
        logger.info(
            f"Marking topic complete: {schedule_id}, day {day_number}, "
            f"topic: {topic_name}"
        )
        
        try:
            # Step 1: Fetch schedule
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Step 2: Validate day exists
            if day_number > len(schedule.days):
                raise DayNotFoundError(
                    f"Day {day_number} not found in schedule"
                )
            
            # Step 3: Get the day (0-indexed)
            day = schedule.days[day_number - 1]
            
            # Step 4: Find the topic
            topic_found = False
            for topic in day.topics:
                if topic.topic == topic_name:
                    # Step 5: Mark as complete
                    topic.time_spent = time_spent
                    topic.completion_notes = completion_notes
                    topic_found = True
                    logger.info(f"Topic '{topic_name}' marked complete")
                    break
            
            if not topic_found:
                raise TopicNotFoundError(
                    f"Topic '{topic_name}' not found in day {day_number}"
                )
            
            # Step 6: Update day completion percentage
            completed_topics = sum(
                1 for t in day.topics 
                if t.time_spent > 0 or t.completion_notes
            )
            total_topics = len(day.topics)
            day_completion = (completed_topics / total_topics * 100.0) if total_topics > 0 else 0.0
            
            # Step 7: Update day status
            if day_completion >= 100.0:
                day.status = DayStatus.COMPLETED
            elif day_completion > 0.0:
                day.status = DayStatus.IN_PROGRESS
            
            # Step 8: Save updated schedule to Firestore
            save_schedule_to_firestore(schedule)
            
            logger.info(
                f"Successfully marked topic complete, day completion: {day_completion}%"
            )
            
            return True
            
        except (ScheduleNotFoundError, DayNotFoundError, TopicNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error marking topic complete {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to mark topic complete: {str(e)}")
    
    def get_progress_summary(self, schedule_id: str) -> Dict[str, Any]:
        """
        Get comprehensive progress summary for a schedule.
        
        Calculates:
        a. Total days completed
        b. Total topics completed
        c. Total hours studied
        d. Completion percentage
        e. Days ahead/behind schedule
        f. Average daily study time
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            Dictionary with progress metrics
        
        Raises:
            ScheduleNotFoundError: If schedule not found
        
        Example:
            >>> summary = tracker.get_progress_summary("schedule_123")
            >>> print(f"Days completed: {summary['days_completed']}")
            >>> print(f"Topics completed: {summary['topics_completed']}")
            >>> print(f"Hours studied: {summary['total_hours_studied']}")
            >>> print(f"Completion: {summary['completion_percentage']}%")
            >>> print(f"Days behind: {summary['days_behind']}")
        """
        logger.info(f"Getting progress summary for: {schedule_id}")
        
        try:
            # Fetch schedule
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Fetch all progress updates
            all_progress = fetch_all_progress(schedule_id)
            
            # Initialize counters
            days_completed = 0
            topics_completed = 0
            total_hours_studied = 0.0
            
            # Calculate from progress updates
            for progress_dict in all_progress:
                if progress_dict.get('status') == 'completed':
                    days_completed += 1
                
                topics_completed += len(progress_dict.get('topics_completed', []))
                total_hours_studied += progress_dict.get('total_time_spent', 0.0)
            
            # Calculate completion percentage
            completion_percentage = self.calculate_completion_percentage(schedule_id)
            
            # Calculate days behind/ahead
            days_drift = self.calculate_schedule_drift(schedule_id, all_progress)
            
            # Calculate average daily study time
            avg_daily_time = (
                total_hours_studied / days_completed 
                if days_completed > 0 
                else 0.0
            )
            
            # Get current study streak
            study_streak = self.calculate_study_streak(schedule_id)
            
            # Get total days in schedule
            total_days = len(schedule.days)
            
            # Get total topics in schedule
            total_topics = sum(len(day.topics) for day in schedule.days)
            
            summary = {
                'schedule_id': schedule_id,
                'total_days': total_days,
                'days_completed': days_completed,
                'days_remaining': max(0, total_days - days_completed),
                'total_topics': total_topics,
                'topics_completed': topics_completed,
                'topics_remaining': max(0, total_topics - topics_completed),
                'total_hours_studied': round(total_hours_studied, 2),
                'completion_percentage': round(completion_percentage, 2),
                'days_behind': days_drift if days_drift > 0 else 0,
                'days_ahead': abs(days_drift) if days_drift < 0 else 0,
                'average_daily_study_time': round(avg_daily_time, 2),
                'current_study_streak': study_streak,
                'status': schedule.status.value,
                'exam_date': schedule.exam_date.isoformat(),
                'days_until_exam': (schedule.exam_date - date.today()).days
            }
            
            logger.info(
                f"Progress summary: {completion_percentage}% complete, "
                f"{days_completed}/{total_days} days, "
                f"{topics_completed}/{total_topics} topics"
            )
            
            return summary
            
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting progress summary {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to get progress summary: {str(e)}")
    
    def get_today_tasks(self, schedule_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks scheduled for today.
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            List of topics scheduled for today with:
            - topic: Topic name
            - subject: Subject name
            - estimated_hours: Estimated time needed
            - subtopics: List of subtopics
            - resources: List of recommended resources
            - goals: Daily learning goals
            
            Empty list if no tasks for today
        
        Example:
            >>> tasks = tracker.get_today_tasks("schedule_123")
            >>> for task in tasks:
            ...     print(f"{task['topic']}: {task['estimated_hours']} hours")
        """
        logger.info(f"Getting today's tasks for: {schedule_id}")
        
        try:
            # Fetch schedule
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Get current date
            today = date.today()
            
            # Find day matching today's date
            today_day = None
            for day in schedule.days:
                if day.schedule_date == today:
                    today_day = day
                    break
            
            # Return empty list if no tasks for today
            if not today_day:
                logger.info(f"No tasks scheduled for today: {today}")
                return []
            
            # Build task list
            tasks = []
            for topic in today_day.topics:
                task = {
                    'topic': topic.topic,
                    'subject': topic.subject.value,
                    'estimated_hours': topic.estimated_hours,
                    'subtopics': topic.subtopics,
                    'resources': topic.resources,
                    'goals': topic.daily_goals,
                    'priority': topic.priority,
                    'difficulty': topic.difficulty.value
                }
                tasks.append(task)
            
            logger.info(f"Found {len(tasks)} tasks for today")
            
            return tasks
            
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting today's tasks {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to get today's tasks: {str(e)}")
    
    def calculate_completion_percentage(self, schedule_id: str) -> float:
        """
        Calculate overall completion percentage.
        
        Weighted by estimated hours for each topic to give more accurate
        completion tracking.
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            Completion percentage (0-100)
        
        Example:
            >>> completion = tracker.calculate_completion_percentage("schedule_123")
            >>> print(f"Schedule is {completion}% complete")
        """
        logger.info(f"Calculating completion percentage for: {schedule_id}")
        
        try:
            # Fetch schedule
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Fetch all progress updates
            all_progress = fetch_all_progress(schedule_id)
            
            # Create map of completed topics with time spent
            completed_topics_map = {}
            for progress_dict in all_progress:
                for topic_data in progress_dict.get('topics_completed', []):
                    topic_name = topic_data.get('topic')
                    time_spent = topic_data.get('time_spent', 0.0)
                    
                    # Track time spent on each topic
                    if topic_name not in completed_topics_map:
                        completed_topics_map[topic_name] = time_spent
                    else:
                        completed_topics_map[topic_name] += time_spent
            
            # Calculate total estimated hours and completed hours
            total_estimated_hours = 0.0
            completed_hours = 0.0
            
            for day in schedule.days:
                for topic in day.topics:
                    total_estimated_hours += topic.estimated_hours
                    
                    # Check if topic is completed
                    if topic.topic in completed_topics_map:
                        # Use actual time spent or estimated hours (whichever is less)
                        # This prevents over-counting if topic took longer
                        time_to_count = min(
                            completed_topics_map[topic.topic],
                            topic.estimated_hours
                        )
                        completed_hours += time_to_count
            
            # Calculate percentage
            if total_estimated_hours > 0:
                completion_percentage = (completed_hours / total_estimated_hours) * 100.0
            else:
                completion_percentage = 0.0
            
            # Clamp to 0-100
            completion_percentage = max(0.0, min(100.0, completion_percentage))
            
            logger.info(
                f"Completion: {completion_percentage}% "
                f"({completed_hours}/{total_estimated_hours} hours)"
            )
            
            return round(completion_percentage, 2)
            
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            logger.error(
                f"Error calculating completion percentage {schedule_id}: {str(e)}"
            )
            raise ProgressTrackerError(
                f"Failed to calculate completion percentage: {str(e)}"
            )
    
    def get_progress_history(
        self,
        schedule_id: str,
        limit: Optional[int] = None
    ) -> List[ProgressUpdate]:
        """
        Get historical progress updates.
        
        Args:
            schedule_id: Schedule identifier
            limit: Maximum number of records to return (None for all)
        
        Returns:
            List of ProgressUpdate objects sorted by date (newest first)
        
        Example:
            >>> history = tracker.get_progress_history("schedule_123", limit=10)
            >>> for progress in history:
            ...     print(f"Day {progress.day_number}: {progress.completion_percentage}%")
        """
        logger.info(f"Getting progress history for: {schedule_id}, limit: {limit}")
        
        try:
            # Fetch all progress from Firestore
            all_progress_dicts = fetch_all_progress(schedule_id, limit=limit)
            
            # Convert to ProgressUpdate objects
            progress_updates = []
            for progress_dict in all_progress_dicts:
                try:
                    progress = ProgressUpdate(**progress_dict)
                    progress_updates.append(progress)
                except ValidationError as e:
                    logger.warning(
                        f"Skipping invalid progress record for day "
                        f"{progress_dict.get('day_number')}: {str(e)}"
                    )
            
            logger.info(f"Found {len(progress_updates)} progress records")
            
            return progress_updates
            
        except Exception as e:
            logger.error(f"Error getting progress history {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to get progress history: {str(e)}")
    
    def get_incomplete_topics(self, schedule_id: str) -> List[Dict[str, Any]]:
        """
        Find all incomplete topics.
        
        Includes topics from past days (overdue) and future days.
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            List of incomplete topics with:
            - topic: Topic name
            - subject: Subject name
            - day_number: Scheduled day number
            - schedule_date: Scheduled date
            - estimated_hours: Time needed
            - priority: Priority level
            - is_overdue: Whether the topic is from a past date
        
        Example:
            >>> incomplete = tracker.get_incomplete_topics("schedule_123")
            >>> overdue = [t for t in incomplete if t['is_overdue']]
            >>> print(f"Found {len(overdue)} overdue topics")
        """
        logger.info(f"Getting incomplete topics for: {schedule_id}")
        
        try:
            # Fetch schedule
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Fetch all progress updates
            all_progress = fetch_all_progress(schedule_id)
            
            # Build set of completed topics
            completed_topics = set()
            for progress_dict in all_progress:
                for topic_data in progress_dict.get('topics_completed', []):
                    topic_name = topic_data.get('topic')
                    day_num = progress_dict.get('day_number')
                    
                    # Store as (day_number, topic_name) to handle same topic on different days
                    completed_topics.add((day_num, topic_name))
            
            # Get current date
            today = date.today()
            
            # Find all incomplete topics
            incomplete_topics = []
            for day in schedule.days:
                for topic in day.topics:
                    # Check if topic is not completed
                    if (day.day_number, topic.topic) not in completed_topics:
                        is_overdue = day.schedule_date < today
                        
                        incomplete_topic = {
                            'topic': topic.topic,
                            'subject': topic.subject.value,
                            'day_number': day.day_number,
                            'schedule_date': day.schedule_date.isoformat(),
                            'estimated_hours': topic.estimated_hours,
                            'priority': topic.priority,
                            'difficulty': topic.difficulty.value,
                            'is_overdue': is_overdue,
                            'days_overdue': (today - day.schedule_date).days if is_overdue else 0
                        }
                        incomplete_topics.append(incomplete_topic)
            
            # Sort by priority (descending) and then by date
            incomplete_topics.sort(
                key=lambda x: (-x['priority'], x['schedule_date'])
            )
            
            logger.info(
                f"Found {len(incomplete_topics)} incomplete topics "
                f"({sum(1 for t in incomplete_topics if t['is_overdue'])} overdue)"
            )
            
            return incomplete_topics
            
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting incomplete topics {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to get incomplete topics: {str(e)}")
    
    def calculate_study_streak(self, schedule_id: str) -> int:
        """
        Calculate consecutive days with progress.
        
        Counts the current streak of consecutive days where the student
        logged any progress (even partial).
        
        Args:
            schedule_id: Schedule identifier
        
        Returns:
            Current study streak length (number of consecutive days)
        
        Example:
            >>> streak = tracker.calculate_study_streak("schedule_123")
            >>> print(f"Current streak: {streak} days")
        """
        logger.info(f"Calculating study streak for: {schedule_id}")
        
        try:
            # Fetch all progress updates (sorted newest first)
            all_progress = fetch_all_progress(schedule_id)
            
            if not all_progress:
                logger.info("No progress found, streak = 0")
                return 0
            
            # Convert to list of dates with progress
            progress_dates = []
            for progress_dict in all_progress:
                update_date_str = progress_dict.get('update_date')
                if update_date_str:
                    # Parse date string
                    if isinstance(update_date_str, str):
                        update_date = date.fromisoformat(update_date_str)
                    else:
                        update_date = update_date_str
                    
                    progress_dates.append(update_date)
            
            # Sort dates (newest first)
            progress_dates.sort(reverse=True)
            
            # Calculate streak starting from most recent
            streak = 0
            expected_date = date.today()
            
            for progress_date in progress_dates:
                # Check if this date matches expected (today or consecutive)
                if progress_date == expected_date:
                    streak += 1
                    expected_date = expected_date - timedelta(days=1)
                elif progress_date < expected_date:
                    # Gap found, streak broken
                    break
            
            logger.info(f"Study streak: {streak} days")
            
            return streak
            
        except Exception as e:
            logger.error(f"Error calculating study streak {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to calculate study streak: {str(e)}")
    
    def calculate_schedule_drift(
        self,
        schedule_id: str,
        progress_list: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        Calculate expected vs actual progress (days behind/ahead).
        
        Positive value = days behind
        Negative value = days ahead
        
        Args:
            schedule_id: Schedule identifier
            progress_list: Optional pre-fetched progress list
        
        Returns:
            Days behind (positive) or ahead (negative)
        
        Example:
            >>> drift = tracker.calculate_schedule_drift("schedule_123")
            >>> if drift > 0:
            ...     print(f"You are {drift} days behind schedule")
            >>> elif drift < 0:
            ...     print(f"You are {abs(drift)} days ahead of schedule")
        """
        logger.info(f"Calculating schedule drift for: {schedule_id}")
        
        try:
            # Fetch schedule
            schedule_dict = fetch_schedule_from_firestore(schedule_id)
            schedule = Schedule(**schedule_dict)
            
            # Fetch progress if not provided
            if progress_list is None:
                progress_list = fetch_all_progress(schedule_id)
            
            # Get current date
            today = date.today()
            
            # Calculate expected day number based on current date
            start_date = schedule.start_date
            days_since_start = (today - start_date).days
            
            # Expected day number (1-indexed)
            expected_day_number = days_since_start + 1
            
            # Find actual day number (highest completed day)
            actual_day_number = 0
            for progress_dict in progress_list:
                if progress_dict.get('status') == 'completed':
                    day_num = progress_dict.get('day_number', 0)
                    actual_day_number = max(actual_day_number, day_num)
            
            # Calculate drift
            drift = expected_day_number - actual_day_number
            
            logger.info(
                f"Schedule drift: {drift} days "
                f"(expected: day {expected_day_number}, actual: day {actual_day_number})"
            )
            
            return drift
            
        except ScheduleNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error calculating schedule drift {schedule_id}: {str(e)}")
            raise ProgressTrackerError(f"Failed to calculate schedule drift: {str(e)}")
    
    def _check_reschedule_trigger(
        self,
        schedule_id: str,
        progress_data: ProgressUpdate
    ) -> None:
        """
        Check if progress update triggers need for rescheduling.
        
        Internal method that checks triggers and logs warnings.
        Actual rescheduling should be initiated by AdaptiveScheduler.
        
        Args:
            schedule_id: Schedule identifier
            progress_data: Latest progress update
        """
        try:
            # Import here to avoid circular dependency
            from services.adaptive_scheduler import AdaptiveScheduler
            
            # Build progress dict for trigger detection
            progress_dict = {
                'days_completed': [],
                'time_spent': {}
            }
            
            # Fetch all progress to build complete picture
            all_progress = fetch_all_progress(schedule_id)
            for p in all_progress:
                if p.get('status') == 'completed':
                    progress_dict['days_completed'].append(p.get('day_number'))
                
                for topic in p.get('topics_completed', []):
                    topic_name = topic.get('topic')
                    progress_dict['time_spent'][topic_name] = topic.get('time_spent', 0.0)
            
            # Check triggers
            adaptive_scheduler = AdaptiveScheduler()
            needs_reschedule, reason, severity = adaptive_scheduler.detect_reschedule_triggers(
                schedule_id,
                progress_dict
            )
            
            if needs_reschedule:
                logger.warning(
                    f"Reschedule trigger detected for {schedule_id}: "
                    f"{reason} (severity: {severity})"
                )
            
        except Exception as e:
            logger.error(f"Error checking reschedule trigger: {str(e)}")
            # Don't raise - this is just a check, not critical
