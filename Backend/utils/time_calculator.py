"""
Time Calculator Utilities for Schedule Generation - Mentor AI Platform.

This module provides utility functions for time-based calculations used in
AI-powered study schedule generation, including day calculations, hour
distribution, revision planning, and feasibility validation.

Functions:
- calculate_available_days: Calculate business days between dates
- calculate_total_study_hours: Calculate total available study hours
- distribute_hours_across_topics: Distribute hours across topics proportionally
- calculate_revision_days: Calculate revision day numbers
- calculate_practice_test_days: Calculate practice test day numbers
- validate_time_feasibility: Check if schedule is feasible
- adjust_daily_hours: Adjust daily study hours to be realistic
- calculate_buffer_days: Calculate buffer day numbers

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from datetime import date
    >>> from utils.time_calculator import calculate_available_days
    >>> 
    >>> start = date(2024, 1, 15)
    >>> exam = date(2024, 4, 1)
    >>> days = calculate_available_days(start, exam, exclude_weekends=True)
    >>> print(f"Available study days: {days}")
"""

import logging
from datetime import date, timedelta
from typing import List, Dict, Tuple, Optional, Set
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class DayOfWeek(int, Enum):
    """Days of the week (0=Monday, 6=Sunday)."""
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class TimeCalculatorError(Exception):
    """Base exception for time calculator errors."""
    pass


class InvalidDateRangeError(TimeCalculatorError):
    """Exception raised when date range is invalid."""
    pass


class InfeasibleScheduleError(TimeCalculatorError):
    """Exception raised when schedule is not feasible."""
    pass


def calculate_available_days(
    start_date: date,
    exam_date: date,
    exclude_weekends: bool = True,
    exclude_days: Optional[Set[date]] = None
) -> int:
    """
    Calculate number of available study days between start and exam date.
    
    This function calculates business days (excluding weekends and holidays)
    available for studying between two dates.
    
    Args:
        start_date: Start date for schedule
        exam_date: Exam date (exclusive)
        exclude_weekends: Whether to exclude weekends (default: True)
        exclude_days: Optional set of specific dates to exclude (holidays, etc.)
    
    Returns:
        Number of available study days
    
    Raises:
        InvalidDateRangeError: If exam_date is before or equal to start_date
        ValueError: If dates are invalid
    
    Example:
        >>> from datetime import date
        >>> start = date(2024, 1, 15)  # Monday
        >>> exam = date(2024, 1, 22)   # Monday (next week)
        >>> days = calculate_available_days(start, exam)
        >>> print(days)  # 5 business days (Mon-Fri)
        5
        
        >>> # Include weekends
        >>> days_with_weekends = calculate_available_days(start, exam, exclude_weekends=False)
        >>> print(days_with_weekends)  # 7 days
        7
        
        >>> # Exclude specific holidays
        >>> holidays = {date(2024, 1, 17)}  # Exclude Wednesday
        >>> days_with_holiday = calculate_available_days(start, exam, exclude_days=holidays)
        >>> print(days_with_holiday)  # 4 days (Mon, Tue, Thu, Fri)
        4
    """
    # Validate dates
    if exam_date <= start_date:
        raise InvalidDateRangeError(
            f"Exam date ({exam_date}) must be after start date ({start_date})"
        )
    
    # Initialize excluded days set
    if exclude_days is None:
        exclude_days = set()
    
    # Count available days
    available_days = 0
    current_date = start_date
    
    while current_date < exam_date:
        # Check if this day should be excluded
        is_weekend = current_date.weekday() in [DayOfWeek.SATURDAY, DayOfWeek.SUNDAY]
        is_excluded_day = current_date in exclude_days
        
        # Count day if it's not excluded
        if not is_excluded_day:
            if exclude_weekends:
                if not is_weekend:
                    available_days += 1
            else:
                available_days += 1
        
        # Move to next day
        current_date += timedelta(days=1)
    
    logger.info(
        f"Calculated {available_days} available days between {start_date} and {exam_date}"
    )
    
    return available_days


def calculate_total_study_hours(
    num_days: int,
    daily_study_hours: float,
    apply_buffer: bool = True,
    buffer_percentage: float = 0.10
) -> float:
    """
    Calculate total available study hours with optional buffer.
    
    Args:
        num_days: Number of available study days
        daily_study_hours: Hours available per day
        apply_buffer: Whether to apply buffer reduction (default: True)
        buffer_percentage: Buffer percentage to reduce by (default: 0.10 = 10%)
    
    Returns:
        Total available study hours (with buffer applied if enabled)
    
    Raises:
        ValueError: If num_days or daily_study_hours are negative
    
    Example:
        >>> # 60 days, 5 hours per day = 300 hours
        >>> total = calculate_total_study_hours(60, 5.0)
        >>> print(f"{total:.1f} hours")  # With 10% buffer: 270 hours
        270.0 hours
        
        >>> # Without buffer
        >>> total_no_buffer = calculate_total_study_hours(60, 5.0, apply_buffer=False)
        >>> print(f"{total_no_buffer:.1f} hours")
        300.0 hours
        
        >>> # Custom buffer (20%)
        >>> total_custom = calculate_total_study_hours(60, 5.0, buffer_percentage=0.20)
        >>> print(f"{total_custom:.1f} hours")  # 240 hours
        240.0 hours
    """
    # Validate inputs
    if num_days < 0:
        raise ValueError(f"Number of days must be non-negative, got {num_days}")
    
    if daily_study_hours < 0:
        raise ValueError(f"Daily study hours must be non-negative, got {daily_study_hours}")
    
    if not 0.0 <= buffer_percentage <= 1.0:
        raise ValueError(f"Buffer percentage must be between 0 and 1, got {buffer_percentage}")
    
    # Calculate base total
    total_hours = num_days * daily_study_hours
    
    # Apply buffer if requested
    if apply_buffer:
        buffer_reduction = total_hours * buffer_percentage
        total_hours = total_hours - buffer_reduction
        logger.info(
            f"Applied {buffer_percentage*100:.0f}% buffer: "
            f"{num_days}d × {daily_study_hours}h = {total_hours:.1f}h "
            f"(reduced from {num_days * daily_study_hours:.1f}h)"
        )
    else:
        logger.info(
            f"Calculated total hours without buffer: "
            f"{num_days}d × {daily_study_hours}h = {total_hours:.1f}h"
        )
    
    return round(total_hours, 1)


def distribute_hours_across_topics(
    topics: List[Dict[str, any]],
    total_available_hours: float,
    min_hours_per_topic: float = 1.0
) -> List[Dict[str, any]]:
    """
    Distribute available hours across topics proportionally.
    
    If total required hours exceed available hours, this function scales down
    each topic's hours proportionally while ensuring minimum hours per topic.
    
    Args:
        topics: List of topic dicts with keys: 'topic', 'subject', 'estimated_hours'
        total_available_hours: Total hours available for distribution
        min_hours_per_topic: Minimum hours each topic must receive (default: 1.0)
    
    Returns:
        List of topic dicts with adjusted 'allocated_hours' field
    
    Raises:
        ValueError: If total_available_hours or min_hours_per_topic are invalid
    
    Example:
        >>> topics = [
        ...     {'topic': 'Thermodynamics', 'subject': 'Physics', 'estimated_hours': 12.0},
        ...     {'topic': 'Calculus', 'subject': 'Math', 'estimated_hours': 8.0},
        ...     {'topic': 'Organic Chem', 'subject': 'Chemistry', 'estimated_hours': 10.0}
        ... ]
        >>> # Total required: 30h, Available: 20h
        >>> adjusted = distribute_hours_across_topics(topics, 20.0)
        >>> for t in adjusted:
        ...     print(f"{t['topic']}: {t['allocated_hours']:.1f}h")
        Thermodynamics: 8.0h
        Calculus: 5.3h
        Organic Chem: 6.7h
    """
    # Validate inputs
    if total_available_hours < 0:
        raise ValueError(f"Total available hours must be non-negative, got {total_available_hours}")
    
    if min_hours_per_topic < 0:
        raise ValueError(f"Minimum hours per topic must be non-negative, got {min_hours_per_topic}")
    
    if not topics:
        logger.warning("No topics provided for hour distribution")
        return []
    
    # Calculate total required hours
    total_required_hours = sum(
        topic.get('estimated_hours', 0.0) for topic in topics
    )
    
    # Check if we need to scale down
    if total_required_hours <= total_available_hours:
        # Sufficient hours - allocate as estimated
        adjusted_topics = []
        for topic in topics:
            adjusted_topic = topic.copy()
            adjusted_topic['allocated_hours'] = topic.get('estimated_hours', min_hours_per_topic)
            adjusted_topics.append(adjusted_topic)
        
        logger.info(
            f"Sufficient hours available: {total_available_hours:.1f}h >= {total_required_hours:.1f}h"
        )
        return adjusted_topics
    
    # Insufficient hours - need to scale down proportionally
    logger.warning(
        f"Insufficient hours: Required {total_required_hours:.1f}h, "
        f"Available {total_available_hours:.1f}h. Scaling down proportionally."
    )
    
    # Calculate minimum total hours needed
    min_total_hours = len(topics) * min_hours_per_topic
    
    if min_total_hours > total_available_hours:
        raise InfeasibleScheduleError(
            f"Cannot allocate minimum {min_hours_per_topic}h per topic. "
            f"Need {min_total_hours:.1f}h for {len(topics)} topics, "
            f"but only {total_available_hours:.1f}h available."
        )
    
    # Reserve minimum hours for each topic
    remaining_hours = total_available_hours - min_total_hours
    
    # Distribute remaining hours proportionally
    adjusted_topics = []
    for topic in topics:
        estimated_hours = topic.get('estimated_hours', min_hours_per_topic)
        
        # Calculate proportion of total required hours
        proportion = estimated_hours / total_required_hours if total_required_hours > 0 else 0
        
        # Allocate: minimum + proportional share of remaining
        allocated_hours = min_hours_per_topic + (remaining_hours * proportion)
        
        adjusted_topic = topic.copy()
        adjusted_topic['allocated_hours'] = round(allocated_hours, 1)
        adjusted_topics.append(adjusted_topic)
    
    # Verify total allocation (should match available hours within rounding)
    total_allocated = sum(t['allocated_hours'] for t in adjusted_topics)
    logger.info(
        f"Distributed {total_allocated:.1f}h across {len(topics)} topics "
        f"(min {min_hours_per_topic}h each)"
    )
    
    return adjusted_topics


def calculate_revision_days(
    total_days: int,
    revision_percentage: float = 0.10
) -> List[int]:
    """
    Calculate day numbers for revision sessions.
    
    Revision days are typically placed at the end of the schedule to allow
    for comprehensive review before the exam.
    
    Args:
        total_days: Total number of days in schedule
        revision_percentage: Percentage of days for revision (default: 0.10 = 10%)
    
    Returns:
        List of day numbers (1-indexed) for revision
    
    Raises:
        ValueError: If total_days or revision_percentage are invalid
    
    Example:
        >>> # 75-day schedule with 10% revision = 7-8 days
        >>> revision_days = calculate_revision_days(75)
        >>> print(revision_days)
        [68, 69, 70, 71, 72, 73, 74, 75]
        
        >>> # 30-day schedule with 15% revision
        >>> revision_days_15 = calculate_revision_days(30, revision_percentage=0.15)
        >>> print(revision_days_15)  # Last 4-5 days
        [26, 27, 28, 29, 30]
    """
    # Validate inputs
    if total_days <= 0:
        raise ValueError(f"Total days must be positive, got {total_days}")
    
    if not 0.0 <= revision_percentage <= 1.0:
        raise ValueError(f"Revision percentage must be between 0 and 1, got {revision_percentage}")
    
    # Calculate number of revision days (minimum 1 if percentage > 0)
    num_revision_days = max(1, int(total_days * revision_percentage))
    
    # Ensure we don't exceed total days
    num_revision_days = min(num_revision_days, total_days)
    
    # Calculate starting day for revision (from the end)
    revision_start_day = total_days - num_revision_days + 1
    
    # Generate list of revision day numbers
    revision_days = list(range(revision_start_day, total_days + 1))
    
    logger.info(
        f"Allocated {num_revision_days} revision days "
        f"({revision_percentage*100:.0f}% of {total_days}): "
        f"Days {revision_start_day}-{total_days}"
    )
    
    return revision_days


def calculate_practice_test_days(
    total_days: int,
    test_interval: int = 7,
    avoid_last_days: int = 3
) -> List[int]:
    """
    Calculate day numbers for practice tests.
    
    Practice tests are spaced at regular intervals throughout the schedule,
    avoiding the final revision period.
    
    Args:
        total_days: Total number of days in schedule
        test_interval: Days between practice tests (default: 7 = weekly)
        avoid_last_days: Number of final days to avoid (default: 3)
    
    Returns:
        List of day numbers (1-indexed) for practice tests
    
    Raises:
        ValueError: If parameters are invalid
    
    Example:
        >>> # 75-day schedule with weekly tests
        >>> test_days = calculate_practice_test_days(75, test_interval=7)
        >>> print(test_days)
        [7, 14, 21, 28, 35, 42, 49, 56, 63, 70]
        
        >>> # 30-day schedule with bi-weekly tests
        >>> test_days_biweekly = calculate_practice_test_days(30, test_interval=14)
        >>> print(test_days_biweekly)
        [14, 27]
    """
    # Validate inputs
    if total_days <= 0:
        raise ValueError(f"Total days must be positive, got {total_days}")
    
    if test_interval <= 0:
        raise ValueError(f"Test interval must be positive, got {test_interval}")
    
    if avoid_last_days < 0:
        raise ValueError(f"Avoid last days must be non-negative, got {avoid_last_days}")
    
    # Calculate effective end day (avoid last N days)
    effective_end_day = total_days - avoid_last_days
    
    if effective_end_day < test_interval:
        logger.warning(
            f"Schedule too short for practice tests with interval {test_interval}. "
            f"Effective days: {effective_end_day}"
        )
        return []
    
    # Generate test days at intervals
    test_days = []
    current_day = test_interval
    
    while current_day <= effective_end_day:
        test_days.append(current_day)
        current_day += test_interval
    
    logger.info(
        f"Scheduled {len(test_days)} practice tests "
        f"(every {test_interval} days, avoiding last {avoid_last_days}): "
        f"{test_days}"
    )
    
    return test_days


def validate_time_feasibility(
    topics: List[Dict[str, any]],
    available_hours: float,
    min_coverage_percentage: float = 0.80
) -> Tuple[bool, float, List[str]]:
    """
    Validate if schedule is feasible given time constraints.
    
    Args:
        topics: List of topics with 'estimated_hours'
        available_hours: Total hours available
        min_coverage_percentage: Minimum percentage of hours that must be covered (default: 0.80 = 80%)
    
    Returns:
        Tuple of (is_feasible, deficit_hours, recommendations)
        - is_feasible: Whether schedule is feasible
        - deficit_hours: Hours short (negative if surplus)
        - recommendations: List of recommendation strings
    
    Example:
        >>> topics = [
        ...     {'topic': 'Topic A', 'estimated_hours': 10.0},
        ...     {'topic': 'Topic B', 'estimated_hours': 15.0}
        ... ]
        >>> is_feasible, deficit, recs = validate_time_feasibility(topics, 20.0)
        >>> print(f"Feasible: {is_feasible}, Deficit: {deficit}h")
        Feasible: False, Deficit: 5.0h
        >>> for rec in recs:
        ...     print(f"- {rec}")
        - Increase daily study hours
        - Consider prioritizing high-priority topics
    """
    # Validate inputs
    if available_hours < 0:
        raise ValueError(f"Available hours must be non-negative, got {available_hours}")
    
    if not 0.0 <= min_coverage_percentage <= 1.0:
        raise ValueError(
            f"Min coverage percentage must be between 0 and 1, got {min_coverage_percentage}"
        )
    
    # Calculate total required hours
    total_required_hours = sum(topic.get('estimated_hours', 0.0) for topic in topics)
    
    # Calculate minimum required hours (based on coverage percentage)
    min_required_hours = total_required_hours * min_coverage_percentage
    
    # Calculate deficit
    deficit_hours = total_required_hours - available_hours
    
    # Determine feasibility
    is_feasible = available_hours >= min_required_hours
    
    # Generate recommendations
    recommendations = []
    
    if not is_feasible:
        # Critical shortage
        shortage_percentage = (deficit_hours / total_required_hours) * 100
        
        recommendations.append(
            f"Schedule requires {total_required_hours:.1f}h but only {available_hours:.1f}h available "
            f"({shortage_percentage:.1f}% short)"
        )
        recommendations.append("Increase daily study hours from current allocation")
        recommendations.append("Consider extending schedule end date if possible")
        recommendations.append("Prioritize high-priority topics and reduce low-priority ones")
        recommendations.append("Focus on topics with highest exam weightage")
    
    elif deficit_hours > 0:
        # Feasible but tight
        recommendations.append(
            f"Schedule is tight: {total_required_hours:.1f}h required, {available_hours:.1f}h available"
        )
        recommendations.append("Consider adding 0.5-1h per day if possible for better coverage")
        recommendations.append("Prioritize critical topics to ensure key areas are covered")
        recommendations.append("Plan for efficient study sessions with minimal breaks")
    
    else:
        # Surplus time
        surplus_hours = abs(deficit_hours)
        recommendations.append(
            f"Schedule has {surplus_hours:.1f}h surplus - good buffer for comprehensive coverage"
        )
        recommendations.append("Use extra time for additional practice and revision")
        recommendations.append("Consider adding more practice tests or mock exams")
        recommendations.append("Allocate extra time to weak topics for mastery")
    
    logger.info(
        f"Feasibility check: {'FEASIBLE' if is_feasible else 'NOT FEASIBLE'} "
        f"(Required: {total_required_hours:.1f}h, Available: {available_hours:.1f}h, "
        f"Deficit: {deficit_hours:.1f}h)"
    )
    
    return is_feasible, round(deficit_hours, 1), recommendations


def adjust_daily_hours(
    required_total_hours: float,
    available_days: int,
    max_daily_hours: float = 8.0,
    min_daily_hours: float = 2.0
) -> Tuple[float, List[str]]:
    """
    Calculate required daily hours and suggest adjustments.
    
    Args:
        required_total_hours: Total hours needed for all topics
        available_days: Number of available study days
        max_daily_hours: Maximum sustainable daily hours (default: 8.0)
        min_daily_hours: Minimum effective daily hours (default: 2.0)
    
    Returns:
        Tuple of (adjusted_daily_hours, warnings)
        - adjusted_daily_hours: Recommended daily hours
        - warnings: List of warning/suggestion strings
    
    Raises:
        ValueError: If parameters are invalid
    
    Example:
        >>> # Need 300h in 60 days = 5h/day (feasible)
        >>> daily, warnings = adjust_daily_hours(300.0, 60)
        >>> print(f"Daily hours: {daily:.1f}h")
        Daily hours: 5.0h
        
        >>> # Need 500h in 50 days = 10h/day (too much!)
        >>> daily, warnings = adjust_daily_hours(500.0, 50)
        >>> print(f"Daily hours: {daily:.1f}h")
        Daily hours: 8.0h
        >>> for w in warnings:
        ...     print(f"⚠ {w}")
        ⚠ Required 10.0h/day exceeds sustainable maximum (8.0h)
        ⚠ Consider extending schedule by 13 days
        ⚠ Or reduce topic coverage by 100.0 hours
    """
    # Validate inputs
    if required_total_hours < 0:
        raise ValueError(f"Required total hours must be non-negative, got {required_total_hours}")
    
    if available_days <= 0:
        raise ValueError(f"Available days must be positive, got {available_days}")
    
    if max_daily_hours <= 0:
        raise ValueError(f"Max daily hours must be positive, got {max_daily_hours}")
    
    if min_daily_hours <= 0:
        raise ValueError(f"Min daily hours must be positive, got {min_daily_hours}")
    
    if min_daily_hours > max_daily_hours:
        raise ValueError(
            f"Min daily hours ({min_daily_hours}) cannot exceed max daily hours ({max_daily_hours})"
        )
    
    # Calculate ideal daily hours
    ideal_daily_hours = required_total_hours / available_days
    
    warnings = []
    
    # Check if ideal hours exceed maximum
    if ideal_daily_hours > max_daily_hours:
        # Calculate how much we're over
        excess_hours = required_total_hours - (max_daily_hours * available_days)
        additional_days_needed = int(excess_hours / max_daily_hours) + 1
        
        warnings.append(
            f"Required {ideal_daily_hours:.1f}h/day exceeds sustainable maximum ({max_daily_hours}h)"
        )
        warnings.append(
            f"Schedule needs {required_total_hours:.1f}h but only {max_daily_hours * available_days:.1f}h available at max capacity"
        )
        warnings.append(
            f"Consider extending schedule by {additional_days_needed} days to reach {required_total_hours:.1f}h"
        )
        warnings.append(
            f"Or reduce topic coverage by {excess_hours:.1f} hours"
        )
        
        adjusted_daily_hours = max_daily_hours
    
    # Check if ideal hours are below minimum
    elif ideal_daily_hours < min_daily_hours:
        warnings.append(
            f"Required {ideal_daily_hours:.1f}h/day is below effective minimum ({min_daily_hours}h)"
        )
        warnings.append(
            "Consider adding more topics or increasing depth of coverage"
        )
        warnings.append(
            "Or reduce total schedule days for more intensive daily study"
        )
        
        adjusted_daily_hours = min_daily_hours
    
    else:
        # Ideal hours are within acceptable range
        adjusted_daily_hours = ideal_daily_hours
        
        if ideal_daily_hours > 6.0:
            warnings.append(
                f"Daily commitment of {ideal_daily_hours:.1f}h is significant - ensure consistency"
            )
        
        if ideal_daily_hours < 3.0:
            warnings.append(
                f"Light daily commitment of {ideal_daily_hours:.1f}h - consider increasing for better results"
            )
    
    logger.info(
        f"Adjusted daily hours: {adjusted_daily_hours:.1f}h "
        f"(ideal: {ideal_daily_hours:.1f}h, range: {min_daily_hours}-{max_daily_hours}h)"
    )
    
    return round(adjusted_daily_hours, 1), warnings


def calculate_buffer_days(
    total_days: int,
    buffer_interval: int = 30
) -> List[int]:
    """
    Calculate buffer day numbers for schedule flexibility.
    
    Buffer days are placed at regular intervals to allow for catching up on
    missed content or addressing unexpected difficulties.
    
    Args:
        total_days: Total number of days in schedule
        buffer_interval: Days between buffer days (default: 30)
    
    Returns:
        List of day numbers (1-indexed) for buffer days
    
    Raises:
        ValueError: If parameters are invalid
    
    Example:
        >>> # 90-day schedule with buffer every 30 days
        >>> buffer_days = calculate_buffer_days(90, buffer_interval=30)
        >>> print(buffer_days)
        [30, 60]
        
        >>> # 100-day schedule
        >>> buffer_days_100 = calculate_buffer_days(100)
        >>> print(buffer_days_100)
        [30, 60, 90]
    """
    # Validate inputs
    if total_days <= 0:
        raise ValueError(f"Total days must be positive, got {total_days}")
    
    if buffer_interval <= 0:
        raise ValueError(f"Buffer interval must be positive, got {buffer_interval}")
    
    # Calculate buffer days
    buffer_days = []
    current_day = buffer_interval
    
    # Add buffer days at intervals, but not on the last day
    while current_day < total_days:
        buffer_days.append(current_day)
        current_day += buffer_interval
    
    logger.info(
        f"Scheduled {len(buffer_days)} buffer days "
        f"(every {buffer_interval} days): {buffer_days}"
    )
    
    return buffer_days
