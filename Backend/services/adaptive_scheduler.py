"""
Adaptive Scheduler for Dynamic Schedule Adjustments - Mentor AI Platform.

This module provides intelligent schedule adaptation based on student progress,
detecting when rescheduling is needed and automatically adjusting plans to keep
students on track for their exam preparation goals.

Functions:
- detect_reschedule_triggers: Detect when schedule needs adjustment
- regenerate_remaining_schedule: Regenerate schedule for remaining days
- adjust_for_missed_sessions: Handle missed study days
- adjust_for_topic_overrun: Adjust when topics take longer than expected
- calculate_catch_up_plan: Create plan to catch up when behind
- handle_student_request: Process student-initiated changes
- calculate_schedule_drift: Measure progress deviation
- prioritize_remaining_topics: Reprioritize incomplete topics

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.adaptive_scheduler import AdaptiveScheduler
    >>> from datetime import date
    >>> 
    >>> # Initialize adaptive scheduler
    >>> scheduler = AdaptiveScheduler()
    >>> 
    >>> # Check if rescheduling needed
    >>> needs_reschedule, reason, severity = scheduler.detect_reschedule_triggers(
    ...     schedule_id="schedule_123",
    ...     progress_data={"completed_days": 5, "missed_days": [3, 4]}
    ... )
    >>> 
    >>> if needs_reschedule:
    ...     # Regenerate remaining schedule
    ...     updated = scheduler.regenerate_remaining_schedule(
    ...         schedule_id="schedule_123",
    ...         current_day_number=5
    ...     )
    ...     print(f"Schedule adjusted: {updated.schedule_id}")
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum

from models.schedule_models import (
    Schedule,
    ScheduleDay,
    DailyTopic,
    TopicPriority,
    ExamType,
    PriorityLevel,
    ScheduleStatus,
    RescheduleReason
)
from services.schedule_service import (
    ScheduleService,
    fetch_schedule_from_firestore,
    save_schedule_to_firestore
)
from services.gemini_scheduler_service import GeminiSchedulerService
from services.priority_calculator import PriorityCalculator
from utils.schedule_context_builder import build_complete_context
from utils.time_calculator import calculate_available_days, calculate_total_study_hours

# Configure logging
logger = logging.getLogger(__name__)


class RescheduleSeverity(str, Enum):
    """Severity levels for reschedule triggers."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action needed soon
    MEDIUM = "medium"      # Minor adjustments
    LOW = "low"            # Optional optimization


class AdaptiveSchedulerError(Exception):
    """Base exception for adaptive scheduler errors."""
    pass


class InfeasibleAdjustmentError(AdaptiveSchedulerError):
    """Exception raised when adjustment is not feasible."""
    pass


def calculate_schedule_drift(
    schedule: Schedule,
    current_day_number: int,
    completed_days: List[int]
) -> int:
    """
    Calculate schedule drift (days behind or ahead).
    
    Args:
        schedule: Schedule object
        current_day_number: Current day in schedule
        completed_days: List of completed day numbers
    
    Returns:
        Days behind (positive) or ahead (negative)
    
    Example:
        >>> drift = calculate_schedule_drift(schedule, 10, [1, 2, 3, 5, 6])
        >>> print(f"Days behind: {drift}")
        4
    """
    # Expected: all days from 1 to current_day_number should be completed
    expected_completed = set(range(1, current_day_number + 1))
    actual_completed = set(completed_days)
    
    # Calculate missing days
    missing_days = expected_completed - actual_completed
    days_behind = len(missing_days)
    
    # Check if ahead (completed days beyond current)
    days_ahead = len([d for d in actual_completed if d > current_day_number])
    
    # Net drift (positive = behind, negative = ahead)
    drift = days_behind - days_ahead
    
    logger.info(
        f"Schedule drift calculated: {drift} days "
        f"(behind: {days_behind}, ahead: {days_ahead})"
    )
    
    return drift


def prioritize_remaining_topics(
    incomplete_topics: List[Dict[str, Any]],
    remaining_days: int,
    exam_date: date
) -> List[Dict[str, Any]]:
    """
    Reprioritize incomplete topics based on remaining time.
    
    Considers:
    - Original priority score
    - Time remaining until exam
    - Topic dependencies
    - Urgency factor
    
    Args:
        incomplete_topics: List of topic dicts with priority info
        remaining_days: Days remaining in schedule
        exam_date: Date of exam
    
    Returns:
        Sorted list of topics (highest priority first)
    
    Example:
        >>> topics = [{"topic": "Topic A", "priority_score": 200, ...}]
        >>> sorted_topics = prioritize_remaining_topics(topics, 30, exam_date)
    """
    logger.info(f"Reprioritizing {len(incomplete_topics)} topics for {remaining_days} days")
    
    days_to_exam = (exam_date - date.today()).days
    urgency_factor = max(0.5, min(2.0, 75.0 / days_to_exam))  # Higher when closer to exam
    
    prioritized = []
    for topic in incomplete_topics:
        # Calculate adjusted priority
        base_priority = topic.get("priority_score", 100)
        
        # Apply urgency multiplier
        adjusted_priority = base_priority * urgency_factor
        
        # Boost critical topics
        if topic.get("priority_level") == "critical":
            adjusted_priority *= 1.5
        
        topic_copy = topic.copy()
        topic_copy["adjusted_priority"] = adjusted_priority
        prioritized.append(topic_copy)
    
    # Sort by adjusted priority (descending)
    prioritized.sort(key=lambda x: x["adjusted_priority"], reverse=True)
    
    logger.info(
        f"Reprioritized topics: urgency_factor={urgency_factor:.2f}, "
        f"top priority={prioritized[0]['adjusted_priority']:.0f}"
    )
    
    return prioritized


class AdaptiveScheduler:
    """
    Adaptive scheduler for dynamic schedule adjustments.
    
    This service monitors student progress and automatically adjusts schedules
    when needed, handling missed sessions, topic overruns, and student requests.
    
    Attributes:
        schedule_service: Main schedule service
        gemini_service: Gemini AI service for regeneration
        priority_calculator: Priority calculation service
    
    Example:
        >>> scheduler = AdaptiveScheduler()
        >>> needs_adjust, reason, severity = scheduler.detect_reschedule_triggers(...)
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize Adaptive Scheduler.
        
        Args:
            gemini_api_key: Optional Google API key for Gemini
        """
        logger.info("Initializing AdaptiveScheduler")
        
        self.schedule_service = ScheduleService(gemini_api_key=gemini_api_key)
        self.gemini_service = GeminiSchedulerService(api_key=gemini_api_key)
        self.priority_calculator = None  # Initialized per exam type
        
        logger.info("AdaptiveScheduler initialized successfully")
    
    def detect_reschedule_triggers(
        self,
        schedule_id: str,
        progress_data: Dict[str, Any]
    ) -> Tuple[bool, str, str]:
        """
        Detect if schedule needs adjustment based on progress.
        
        Triggers:
        - Missed 2+ consecutive days (HIGH)
        - Topic took 50%+ more time than estimated (MEDIUM)
        - More than 3 days behind schedule (CRITICAL)
        - Practice test accuracy < 50% (HIGH)
        - Requested by student (varies)
        
        Args:
            schedule_id: Schedule identifier
            progress_data: Dict with progress information:
                - completed_days: List of completed day numbers
                - missed_days: List of missed day numbers
                - current_day: Current day number
                - topic_overruns: List of topics that took longer
                - practice_test_scores: Dict of test scores
        
        Returns:
            Tuple of (needs_reschedule, reason, severity)
        
        Example:
            >>> needs, reason, severity = scheduler.detect_reschedule_triggers(
            ...     "schedule_123",
            ...     {"completed_days": [1, 2, 5], "current_day": 7}
            ... )
            >>> if needs:
            ...     print(f"{severity}: {reason}")
        """
        logger.info(f"Detecting reschedule triggers for schedule: {schedule_id}")
        
        # Fetch schedule
        schedule = self.schedule_service.get_schedule(schedule_id)
        
        completed_days = progress_data.get("completed_days", [])
        missed_days = progress_data.get("missed_days", [])
        current_day = progress_data.get("current_day", 1)
        topic_overruns = progress_data.get("topic_overruns", [])
        practice_scores = progress_data.get("practice_test_scores", {})
        
        # Trigger 1: Check for consecutive missed days
        if len(missed_days) >= 2:
            # Check if consecutive
            sorted_missed = sorted(missed_days)
            consecutive_count = 1
            max_consecutive = 1
            
            for i in range(1, len(sorted_missed)):
                if sorted_missed[i] == sorted_missed[i-1] + 1:
                    consecutive_count += 1
                    max_consecutive = max(max_consecutive, consecutive_count)
                else:
                    consecutive_count = 1
            
            if max_consecutive >= 2:
                reason = f"Missed {max_consecutive} consecutive days"
                severity = RescheduleSeverity.HIGH.value
                logger.warning(f"Trigger detected - {reason}: {severity}")
                return True, reason, severity
        
        # Trigger 2: Check schedule drift (days behind)
        drift = calculate_schedule_drift(schedule, current_day, completed_days)
        if drift >= 3:
            reason = f"{drift} days behind schedule"
            severity = RescheduleSeverity.CRITICAL.value
            logger.warning(f"Trigger detected - {reason}: {severity}")
            return True, reason, severity
        elif drift >= 2:
            reason = f"{drift} days behind schedule"
            severity = RescheduleSeverity.HIGH.value
            logger.warning(f"Trigger detected - {reason}: {severity}")
            return True, reason, severity
        
        # Trigger 3: Check for topic overruns
        if topic_overruns:
            significant_overruns = [
                t for t in topic_overruns
                if t.get("actual_hours", 0) > t.get("estimated_hours", 0) * 1.5
            ]
            
            if significant_overruns:
                reason = f"{len(significant_overruns)} topics took 50%+ longer than estimated"
                severity = RescheduleSeverity.MEDIUM.value
                logger.warning(f"Trigger detected - {reason}: {severity}")
                return True, reason, severity
        
        # Trigger 4: Check practice test scores
        if practice_scores:
            low_scores = [
                score for score in practice_scores.values()
                if score < 50.0
            ]
            
            if low_scores and len(low_scores) >= 2:
                reason = f"{len(low_scores)} practice tests scored below 50%"
                severity = RescheduleSeverity.HIGH.value
                logger.warning(f"Trigger detected - {reason}: {severity}")
                return True, reason, severity
        
        logger.info("No reschedule triggers detected")
        return False, "No adjustment needed", RescheduleSeverity.LOW.value
    
    def regenerate_remaining_schedule(
        self,
        schedule_id: str,
        current_day_number: int
    ) -> Schedule:
        """
        Regenerate schedule for remaining days.
        
        Workflow:
        1. Fetch existing schedule
        2. Identify completed days and topics
        3. Calculate incomplete topics
        4. Recalculate priorities
        5. Calculate remaining time
        6. Generate new schedule using Gemini
        7. Merge with completed days
        8. Save updated schedule
        
        Args:
            schedule_id: Schedule identifier
            current_day_number: Current day number in schedule
        
        Returns:
            Updated Schedule object
        
        Example:
            >>> updated = scheduler.regenerate_remaining_schedule(
            ...     "schedule_123",
            ...     current_day_number=15
            ... )
            >>> print(f"Regenerated from day {current_day_number}")
        """
        logger.info(
            f"Regenerating remaining schedule: {schedule_id} from day {current_day_number}"
        )
        
        # Fetch existing schedule
        schedule = self.schedule_service.get_schedule(schedule_id)
        
        # Separate completed and remaining days
        completed_days = [day for day in schedule.days if day.day_number < current_day_number]
        
        # Identify incomplete topics from remaining days
        incomplete_topics = []
        for day in schedule.days:
            if day.day_number >= current_day_number:
                for topic in day.topics:
                    incomplete_topics.append({
                        "topic": topic.topic,
                        "subject": topic.subject,
                        "priority": topic.priority.value,
                        "estimated_hours": topic.estimated_hours,
                        "priority_score": 100,  # Will be recalculated
                        "priority_level": topic.priority.value
                    })
        
        # Calculate remaining days
        days_to_exam = (schedule.exam_date - date.today()).days
        remaining_days = max(1, days_to_exam)
        
        # Reprioritize topics
        prioritized_topics = prioritize_remaining_topics(
            incomplete_topics,
            remaining_days,
            schedule.exam_date
        )
        
        logger.info(
            f"Regenerating for {len(prioritized_topics)} topics over {remaining_days} days"
        )
        
        # Build context for Gemini
        student_profile = {
            "student_id": schedule.student_id,
            "exam_type": schedule.exam_type.value,
            "exam_date": schedule.exam_date,
            "daily_study_hours": schedule.daily_study_hours
        }
        
        # Simplified analytics (based on incomplete topics)
        analytics_data = {
            "overall_score": 0,
            "max_score": 100,
            "percentage": 0.0,
            "accuracy": 0.0,
            "subject_scores": {},
            "strong_topics": [],
            "weak_topics": prioritized_topics[:10]
        }
        
        # Load weightages (dummy for regeneration)
        weightages = {}
        
        # Calculate constraints
        available_days = calculate_available_days(
            date.today(),
            schedule.exam_date,
            exclude_weekends=False
        )
        
        total_hours = calculate_total_study_hours(
            available_days,
            schedule.daily_study_hours,
            apply_buffer=True
        )
        
        constraints = {
            "total_days": available_days,
            "daily_hours": schedule.daily_study_hours,
            "total_hours": total_hours,
            "revision_days": schedule.revision_days,
            "practice_test_days": schedule.practice_test_days,
            "buffer_days": schedule.buffer_days,
            "must_cover_critical": True,
            "balance_subjects": True
        }
        
        # Build context
        context = build_complete_context(
            student_profile=student_profile,
            analytics_data=analytics_data,
            priority_topics=prioritized_topics,
            weightages=weightages,
            constraints=constraints
        )
        
        # Generate new schedule for remaining days
        logger.info("Generating new schedule with Gemini")
        new_schedule = self.gemini_service.generate_schedule(
            context=context,
            student_id=schedule.student_id,
            analytics_id=schedule.analytics_id,
            exam_type=schedule.exam_type.value,
            exam_date=schedule.exam_date,
            daily_study_hours=schedule.daily_study_hours
        )
        
        # Merge with completed days
        # Renumber new days to start from current_day_number
        for i, day in enumerate(new_schedule.days):
            day.day_number = current_day_number + i
            day.schedule_date = date.today() + timedelta(days=i)
        
        # Combine
        schedule.days = completed_days + new_schedule.days
        schedule.total_days = len(schedule.days)
        
        # Save updated schedule
        save_schedule_to_firestore(schedule)
        
        logger.info(f"Successfully regenerated schedule: {schedule_id}")
        return schedule
    
    def adjust_for_missed_sessions(
        self,
        schedule: Schedule,
        missed_day_numbers: List[int]
    ) -> Schedule:
        """
        Adjust schedule for missed study days.
        
        Strategy:
        - Redistribute missed topics to future days
        - Increase daily hours slightly if needed (max +1 hour)
        - Prioritize critical topics
        
        Args:
            schedule: Schedule object
            missed_day_numbers: List of missed day numbers
        
        Returns:
            Adjusted Schedule object
        
        Example:
            >>> adjusted = scheduler.adjust_for_missed_sessions(
            ...     schedule,
            ...     missed_day_numbers=[3, 4, 7]
            ... )
        """
        logger.info(f"Adjusting schedule for {len(missed_day_numbers)} missed days")
        
        # Collect topics from missed days
        missed_topics = []
        for day in schedule.days:
            if day.day_number in missed_day_numbers:
                missed_topics.extend(day.topics)
        
        if not missed_topics:
            logger.info("No topics to redistribute")
            return schedule
        
        # Sort missed topics by priority
        missed_topics.sort(
            key=lambda t: 0 if t.priority == PriorityLevel.CRITICAL else
                         1 if t.priority == PriorityLevel.HIGH else
                         2 if t.priority == PriorityLevel.MEDIUM else 3,
        )
        
        # Find future days to redistribute to
        future_days = [
            day for day in schedule.days
            if day.day_number > max(missed_day_numbers) and not day.completed
        ]
        
        if not future_days:
            logger.warning("No future days available for redistribution")
            return schedule
        
        # Redistribute topics
        topic_index = 0
        for day in future_days:
            if topic_index >= len(missed_topics):
                break
            
            # Add 1-2 topics to each day
            topics_to_add = min(2, len(missed_topics) - topic_index)
            
            for _ in range(topics_to_add):
                if topic_index < len(missed_topics):
                    day.topics.append(missed_topics[topic_index])
                    day.total_hours += missed_topics[topic_index].estimated_hours
                    topic_index += 1
            
            # Cap at reasonable daily hours
            if day.total_hours > schedule.daily_study_hours + 1:
                logger.warning(
                    f"Day {day.day_number} exceeds max hours: {day.total_hours:.1f}h"
                )
        
        logger.info(f"Redistributed {topic_index} topics to {len(future_days)} days")
        
        return schedule
    
    def adjust_for_topic_overrun(
        self,
        schedule: Schedule,
        topic_name: str,
        actual_hours: float
    ) -> Schedule:
        """
        Adjust schedule when a topic takes longer than estimated.
        
        Strategy:
        - Update estimated hours for similar topics
        - Adjust remaining schedule
        - May remove low-priority topics if needed
        
        Args:
            schedule: Schedule object
            topic_name: Topic that took longer
            actual_hours: Actual hours spent
        
        Returns:
            Adjusted Schedule object
        
        Example:
            >>> adjusted = scheduler.adjust_for_topic_overrun(
            ...     schedule,
            ...     topic_name="Thermodynamics",
            ...     actual_hours=8.0
            ... )
        """
        logger.info(
            f"Adjusting schedule for topic overrun: {topic_name} took {actual_hours:.1f}h"
        )
        
        # Find similar topics in remaining days
        similar_topics_updated = 0
        
        for day in schedule.days:
            if day.completed:
                continue
            
            for topic in day.topics:
                # Simple similarity check (same topic name or subject)
                if topic.topic == topic_name or topic.subject in topic_name:
                    # Increase estimated hours by 25%
                    original = topic.estimated_hours
                    topic.estimated_hours = min(
                        topic.estimated_hours * 1.25,
                        actual_hours
                    )
                    
                    day.total_hours += (topic.estimated_hours - original)
                    similar_topics_updated += 1
        
        logger.info(f"Updated {similar_topics_updated} similar topics")
        
        # Check if schedule is still feasible
        total_estimated = sum(
            day.total_hours for day in schedule.days if not day.completed
        )
        
        remaining_days = len([day for day in schedule.days if not day.completed])
        
        if total_estimated > remaining_days * (schedule.daily_study_hours + 1):
            logger.warning("Schedule may no longer be feasible, consider removing low-priority topics")
        
        return schedule
    
    def calculate_catch_up_plan(
        self,
        schedule: Schedule,
        days_behind: int
    ) -> Tuple[Dict[str, Any], Schedule]:
        """
        Calculate plan to catch up when behind schedule.
        
        Options (in order of preference):
        1. Increase daily hours (up to +1 hour)
        2. Remove low-priority topics
        3. Reduce revision days
        4. Extend schedule (if possible)
        
        Args:
            schedule: Schedule object
            days_behind: Number of days behind schedule
        
        Returns:
            Tuple of (recommendations_dict, adjusted_schedule)
        
        Example:
            >>> recs, adjusted = scheduler.calculate_catch_up_plan(schedule, 3)
            >>> print(recs["primary_action"])
        """
        logger.info(f"Calculating catch-up plan for {days_behind} days behind")
        
        recommendations = {
            "days_behind": days_behind,
            "primary_action": None,
            "adjustments": [],
            "removed_topics": [],
            "feasibility": "unknown"
        }
        
        # Calculate deficit hours
        deficit_hours = days_behind * schedule.daily_study_hours
        
        # Option 1: Increase daily hours
        remaining_days = len([day for day in schedule.days if not day.completed])
        
        if remaining_days > 0:
            extra_hours_per_day = deficit_hours / remaining_days
            
            if extra_hours_per_day <= 1.0:
                # Feasible to catch up by increasing daily hours
                new_daily_hours = schedule.daily_study_hours + extra_hours_per_day
                
                if new_daily_hours <= 8.0:
                    recommendations["primary_action"] = "increase_daily_hours"
                    recommendations["adjustments"].append({
                        "type": "increase_hours",
                        "from": schedule.daily_study_hours,
                        "to": new_daily_hours,
                        "extra_per_day": extra_hours_per_day
                    })
                    
                    # Apply adjustment
                    for day in schedule.days:
                        if not day.completed:
                            day.total_hours += extra_hours_per_day
                    
                    schedule.daily_study_hours = new_daily_hours
                    recommendations["feasibility"] = "high"
        
        # Option 2: Remove low-priority topics
        if recommendations["primary_action"] is None:
            low_priority_topics = []
            
            for day in schedule.days:
                if day.completed:
                    continue
                
                for topic in day.topics:
                    if topic.priority == PriorityLevel.LOW:
                        low_priority_topics.append((day, topic))
            
            if low_priority_topics:
                # Remove enough low-priority topics to cover deficit
                hours_removed = 0
                
                for day, topic in low_priority_topics:
                    if hours_removed >= deficit_hours:
                        break
                    
                    day.topics.remove(topic)
                    day.total_hours -= topic.estimated_hours
                    hours_removed += topic.estimated_hours
                    recommendations["removed_topics"].append(topic.topic)
                
                recommendations["primary_action"] = "remove_low_priority"
                recommendations["adjustments"].append({
                    "type": "remove_topics",
                    "count": len(recommendations["removed_topics"]),
                    "hours_saved": hours_removed
                })
                recommendations["feasibility"] = "medium"
        
        # Option 3: Reduce revision days
        if recommendations["primary_action"] is None and schedule.revision_days:
            # Remove some revision days
            days_to_remove = min(days_behind, len(schedule.revision_days) // 2)
            schedule.revision_days = schedule.revision_days[days_to_remove:]
            
            recommendations["primary_action"] = "reduce_revision"
            recommendations["adjustments"].append({
                "type": "reduce_revision",
                "days_removed": days_to_remove
            })
            recommendations["feasibility"] = "low"
        
        # If still no solution, mark as infeasible
        if recommendations["primary_action"] is None:
            recommendations["feasibility"] = "infeasible"
            recommendations["primary_action"] = "regenerate_schedule"
        
        logger.info(
            f"Catch-up plan: {recommendations['primary_action']}, "
            f"feasibility: {recommendations['feasibility']}"
        )
        
        return recommendations, schedule
    
    def handle_student_request(
        self,
        schedule_id: str,
        request_type: str,
        request_data: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Schedule]]:
        """
        Handle student-initiated schedule changes.
        
        Request types:
        - "more_time": Student needs more time for a topic
        - "skip_topic": Student wants to skip a topic
        - "change_order": Student wants to change topic order
        
        Args:
            schedule_id: Schedule identifier
            request_type: Type of request
            request_data: Request-specific data
        
        Returns:
            Tuple of (success, message, updated_schedule or None)
        
        Example:
            >>> success, msg, schedule = scheduler.handle_student_request(
            ...     "schedule_123",
            ...     "more_time",
            ...     {"topic": "Thermodynamics", "extra_hours": 2}
            ... )
        """
        logger.info(f"Handling student request: {request_type} for {schedule_id}")
        
        try:
            schedule = self.schedule_service.get_schedule(schedule_id)
            
            if request_type == "more_time":
                # Student needs more time for a topic
                topic_name = request_data.get("topic")
                extra_hours = request_data.get("extra_hours", 0)
                
                # Find topic and add extra hours
                topic_found = False
                for day in schedule.days:
                    if day.completed:
                        continue
                    
                    for topic in day.topics:
                        if topic.topic == topic_name:
                            topic.estimated_hours += extra_hours
                            day.total_hours += extra_hours
                            topic_found = True
                            break
                    
                    if topic_found:
                        break
                
                if not topic_found:
                    return False, f"Topic not found: {topic_name}", None
                
                # Save updated schedule
                save_schedule_to_firestore(schedule)
                
                return True, f"Added {extra_hours}h to {topic_name}", schedule
            
            elif request_type == "skip_topic":
                # Student wants to skip a topic
                topic_name = request_data.get("topic")
                
                # Remove topic from schedule
                topic_found = False
                for day in schedule.days:
                    if day.completed:
                        continue
                    
                    for topic in day.topics:
                        if topic.topic == topic_name:
                            day.topics.remove(topic)
                            day.total_hours -= topic.estimated_hours
                            topic_found = True
                            break
                    
                    if topic_found:
                        break
                
                if not topic_found:
                    return False, f"Topic not found: {topic_name}", None
                
                # Save updated schedule
                save_schedule_to_firestore(schedule)
                
                return True, f"Removed {topic_name} from schedule", schedule
            
            elif request_type == "change_order":
                # Student wants to change topic order
                return False, "Change order not yet implemented", None
            
            else:
                return False, f"Unknown request type: {request_type}", None
        
        except Exception as e:
            logger.error(f"Error handling student request: {str(e)}")
            return False, f"Error: {str(e)}", None
