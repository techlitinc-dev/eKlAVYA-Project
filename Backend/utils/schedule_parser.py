"""
Schedule Parser for Gemini Responses - Mentor AI Platform.

This module provides parsing and validation functions to convert Gemini-generated
JSON responses into validated Schedule Pydantic models. It handles data extraction,
validation, and automatic fixing of common issues in AI-generated schedules.

Functions:
- parse_schedule_json: Main parser converting JSON dict to Schedule model
- parse_schedule_day: Parse individual day data into ScheduleDay model
- parse_daily_topic: Parse topic data into DailyTopic model
- validate_schedule_structure: Validate JSON structure before parsing
- validate_topic_data: Validate individual topic data
- fix_common_issues: Automatically fix common issues in schedule data
- convert_dates: Parse date strings in various formats

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from utils.schedule_parser import parse_schedule_json
    >>> 
    >>> # Gemini response JSON
    >>> gemini_json = {
    ...     "schedule_metadata": {"total_days": 2},
    ...     "daily_schedule": [
    ...         {
    ...             "day_number": 1,
    ...             "date": "2024-01-15",
    ...             "topics": [{"topic": "Thermodynamics", ...}],
    ...             "total_hours": 5.0
    ...         }
    ...     ]
    ... }
    >>> 
    >>> # Parse to Schedule model
    >>> schedule = parse_schedule_json(
    ...     gemini_json,
    ...     schedule_id="schedule_123",
    ...     student_id="student_456",
    ...     analytics_id="analytics_789",
    ...     exam_type="JEE_MAIN",
    ...     exam_date=date(2024, 4, 1),
    ...     daily_study_hours=5.0
    ... )
    >>> print(f"Parsed {len(schedule.days)} days")
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Tuple, Optional
from pydantic import ValidationError

from models.schedule_models import (
    Schedule,
    ScheduleDay,
    DailyTopic,
    TopicPriority,
    ExamType,
    PriorityLevel,
    ScheduleStatus,
    DifficultyLevel
)

# Configure logging
logger = logging.getLogger(__name__)

# Allowed subjects for validation
ALLOWED_SUBJECTS = {
    "Physics",
    "Chemistry", 
    "Mathematics",
    "Biology",
    "Math",  # Alias for Mathematics
    "Maths"  # Alias for Mathematics
}

# Subject name normalization
SUBJECT_ALIASES = {
    "Math": "Mathematics",
    "Maths": "Mathematics"
}


class ScheduleParserError(Exception):
    """Base exception for schedule parsing errors."""
    pass


class ScheduleValidationError(ScheduleParserError):
    """Exception raised when schedule validation fails."""
    pass


class DateParsingError(ScheduleParserError):
    """Exception raised when date parsing fails."""
    pass


def convert_dates(date_str: str) -> date:
    """
    Parse date string in various formats to date object.
    
    Supports formats:
    - ISO format: "2024-01-15"
    - European format: "15-01-2024"
    - US format: "01-15-2024"
    - Month name: "Jan 15, 2024"
    
    Args:
        date_str: Date string in supported format
    
    Returns:
        date object
    
    Raises:
        DateParsingError: If date string format is not recognized
    
    Example:
        >>> convert_dates("2024-01-15")
        date(2024, 1, 15)
        
        >>> convert_dates("15-01-2024")
        date(2024, 1, 15)
        
        >>> convert_dates("Jan 15, 2024")
        date(2024, 1, 15)
    """
    if not date_str:
        raise DateParsingError("Empty date string")
    
    # List of date formats to try
    formats = [
        "%Y-%m-%d",       # 2024-01-15 (ISO)
        "%d-%m-%Y",       # 15-01-2024 (European)
        "%m-%d-%Y",       # 01-15-2024 (US)
        "%Y/%m/%d",       # 2024/01/15
        "%d/%m/%Y",       # 15/01/2024
        "%m/%d/%Y",       # 01/15/2024 (fixed typo)
        "%b %d, %Y",      # Jan 15, 2024
        "%B %d, %Y",      # January 15, 2024
        "%d %b %Y",       # 15 Jan 2024
        "%d %B %Y",       # 15 January 2024
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    # If no format worked, raise error
    raise DateParsingError(
        f"Unable to parse date '{date_str}'. Supported formats: "
        f"YYYY-MM-DD, DD-MM-YYYY, MM-DD-YYYY, 'Jan 15, 2024'"
    )


def validate_topic_data(topic_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate individual topic data.
    
    Checks:
    - Required fields: topic, subject, estimated_hours
    - Hours between 0.5 and 8
    - Subject in allowed list
    
    Args:
        topic_data: Topic dictionary
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Example:
        >>> topic = {
        ...     "topic": "Thermodynamics",
        ...     "subject": "Physics",
        ...     "estimated_hours": 3.0
        ... }
        >>> is_valid, errors = validate_topic_data(topic)
        >>> print(is_valid)
        True
    """
    errors = []
    
    # Check required fields
    required_fields = ["topic", "subject", "estimated_hours"]
    for field in required_fields:
        if field not in topic_data:
            errors.append(f"Missing required field: '{field}'")
    
    # Validate estimated_hours
    if "estimated_hours" in topic_data:
        hours = topic_data["estimated_hours"]
        try:
            hours = float(hours)
            if not 0.5 <= hours <= 8.0:
                errors.append(
                    f"Estimated hours {hours} out of range (0.5-8.0)"
                )
        except (ValueError, TypeError):
            errors.append(
                f"Invalid estimated_hours: {hours} (must be numeric)"
            )
    
    # Validate subject
    if "subject" in topic_data:
        subject = topic_data["subject"]
        if subject not in ALLOWED_SUBJECTS:
            # Check if it's close to an allowed subject
            close_match = None
            subject_lower = subject.lower()
            for allowed in ALLOWED_SUBJECTS:
                if subject_lower == allowed.lower():
                    close_match = allowed
                    break
            
            if close_match:
                # It's just a case mismatch, not an error
                logger.debug(f"Subject case mismatch: '{subject}' -> '{close_match}'")
            else:
                errors.append(
                    f"Invalid subject: '{subject}'. Allowed: {', '.join(ALLOWED_SUBJECTS)}"
                )
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_schedule_structure(schedule_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate schedule JSON structure before parsing.
    
    Checks:
    - Required top-level fields
    - Days is list and not empty
    - Each day has required fields
    
    Args:
        schedule_data: Schedule data dictionary from Gemini
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Example:
        >>> schedule = {"daily_schedule": [{"day_number": 1, ...}]}
        >>> is_valid, errors = validate_schedule_structure(schedule)
        >>> if not is_valid:
        ...     print(f"Errors: {errors}")
    """
    errors = []
    
    # Check for daily_schedule
    if "daily_schedule" not in schedule_data:
        errors.append("Missing required field: 'daily_schedule'")
        return False, errors
    
    daily_schedule = schedule_data["daily_schedule"]
    
    # Check daily_schedule is list
    if not isinstance(daily_schedule, list):
        errors.append(
            f"'daily_schedule' must be a list, got {type(daily_schedule).__name__}"
        )
        return False, errors
    
    # Check daily_schedule is not empty
    if not daily_schedule:
        errors.append("'daily_schedule' is empty")
        return False, errors
    
    # Validate each day
    for i, day in enumerate(daily_schedule):
        if not isinstance(day, dict):
            errors.append(
                f"Day {i} is not a dictionary: {type(day).__name__}"
            )
            continue
        
        # Check required day fields
        required_day_fields = ["day_number", "topics"]
        for field in required_day_fields:
            if field not in day:
                errors.append(f"Day {i}: missing required field '{field}'")
        
        # Validate topics
        if "topics" in day:
            topics = day["topics"]
            if not isinstance(topics, list):
                errors.append(
                    f"Day {i}: 'topics' must be a list, got {type(topics).__name__}"
                )
            elif not topics:
                errors.append(f"Day {i}: 'topics' is empty")
            else:
                # Validate each topic
                for j, topic in enumerate(topics):
                    if not isinstance(topic, dict):
                        errors.append(
                            f"Day {i} topic {j}: not a dictionary"
                        )
                        continue
                    
                    # Quick validation
                    topic_valid, topic_errors = validate_topic_data(topic)
                    if not topic_valid:
                        for error in topic_errors:
                            errors.append(f"Day {i} topic {j}: {error}")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info(f"Schedule structure validation passed: {len(daily_schedule)} days")
    else:
        logger.warning(f"Schedule structure validation failed: {len(errors)} errors")
    
    return is_valid, errors


def fix_common_issues(schedule_data: Dict[str, Any], start_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Automatically fix common issues in Gemini-generated schedules.
    
    Fixes:
    - Missing day_numbers (assign sequential)
    - Missing dates (calculate from start date)
    - Missing total_hours (sum topic hours)
    - Empty subtopics (use topic name)
    - Empty resources (add default)
    - Subject name normalization
    
    Args:
        schedule_data: Schedule data with potential issues
        start_date: Start date for calculating dates (default: today)
    
    Returns:
        Fixed schedule data dictionary
    
    Example:
        >>> data = {"daily_schedule": [{"topics": [...]}]}  # Missing day_number
        >>> fixed = fix_common_issues(data)
        >>> print(fixed["daily_schedule"][0]["day_number"])
        1
    """
    logger.info("Applying automatic fixes to schedule data")
    
    if start_date is None:
        start_date = date.today()
    
    if "daily_schedule" not in schedule_data:
        logger.warning("No daily_schedule found, cannot apply fixes")
        return schedule_data
    
    daily_schedule = schedule_data["daily_schedule"]
    fixes_applied = 0
    
    for day_idx, day in enumerate(daily_schedule):
        # Fix 1: Missing day_number
        if "day_number" not in day or day["day_number"] is None:
            day["day_number"] = day_idx + 1
            logger.debug(f"Fixed missing day_number: {day['day_number']}")
            fixes_applied += 1
        
        # Fix 2: Missing date
        if "date" not in day or day["date"] is None:
            day_number = day.get("day_number", day_idx + 1)
            calculated_date = start_date + timedelta(days=day_number - 1)
            day["date"] = calculated_date.isoformat()
            logger.debug(f"Fixed missing date for day {day_number}: {day['date']}")
            fixes_applied += 1
        
        # Fix 3: Missing or empty subjects list
        if "subjects" not in day or not day["subjects"]:
            subjects = set()
            for topic in day.get("topics", []):
                if "subject" in topic:
                    subjects.add(topic["subject"])
            day["subjects"] = list(subjects)
            logger.debug(f"Fixed subjects for day {day.get('day_number')}: {day['subjects']}")
            fixes_applied += 1
        
        # Fix 4: Missing total_hours
        if "total_hours" not in day or day["total_hours"] is None:
            total_hours = 0.0
            for topic in day.get("topics", []):
                total_hours += float(topic.get("estimated_hours", 0))
            day["total_hours"] = round(total_hours, 1)
            logger.debug(f"Fixed total_hours for day {day.get('day_number')}: {day['total_hours']}")
            fixes_applied += 1
        
        # Fix 5: Topic-level fixes
        for topic in day.get("topics", []):
            # Fix empty subtopics
            if "subtopics" not in topic or not topic["subtopics"]:
                topic["subtopics"] = [topic.get("topic", "Study topic")]
                fixes_applied += 1
            
            # Fix empty resources
            if "resources" not in topic or not topic["resources"]:
                topic["resources"] = ["Study from textbook and notes"]
                fixes_applied += 1
            
            # Fix empty goals
            if "goals" not in topic or not topic["goals"]:
                topic["goals"] = [f"Complete {topic.get('topic', 'topic')} basics"]
                fixes_applied += 1
            
            # Normalize subject name
            if "subject" in topic:
                original_subject = topic["subject"]
                # Normalize case
                for allowed in ALLOWED_SUBJECTS:
                    if original_subject.lower() == allowed.lower():
                        topic["subject"] = allowed
                        if original_subject != allowed:
                            fixes_applied += 1
                        break
                
                # Apply aliases
                if topic["subject"] in SUBJECT_ALIASES:
                    topic["subject"] = SUBJECT_ALIASES[topic["subject"]]
                    fixes_applied += 1
            
            # Fix missing priority
            if "priority" not in topic or topic["priority"] is None:
                topic["priority"] = "medium"
                fixes_applied += 1
    
    logger.info(f"Applied {fixes_applied} automatic fixes to schedule data")
    
    return schedule_data


def parse_daily_topic(topic_data: Dict[str, Any]) -> DailyTopic:
    """
    Parse topic data dict into DailyTopic model.
    
    Args:
        topic_data: Topic dictionary with fields like topic, subject, hours, etc.
    
    Returns:
        DailyTopic Pydantic model instance
    
    Raises:
        ValueError: If required fields are missing or invalid
    
    Example:
        >>> topic_data = {
        ...     "topic": "Thermodynamics",
        ...     "subject": "Physics",
        ...     "priority": "critical",
        ...     "estimated_hours": 3.0,
        ...     "subtopics": ["First Law", "Second Law"],
        ...     "resources": ["NCERT Chapter 12"],
        ...     "goals": ["Understand thermodynamic laws"]
        ... }
        >>> topic = parse_daily_topic(topic_data)
        >>> print(topic.topic)
        Thermodynamics
    """
    # Validate topic data first
    is_valid, errors = validate_topic_data(topic_data)
    if not is_valid:
        error_msg = f"Invalid topic data: {'; '.join(errors)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Extract fields with defaults
    topic_name = topic_data.get("topic", "Unknown Topic")
    subject = topic_data.get("subject", "Unknown")
    
    # Normalize subject
    if subject in SUBJECT_ALIASES:
        subject = SUBJECT_ALIASES[subject]
    
    priority_str = topic_data.get("priority", "medium")
    try:
        priority = PriorityLevel(priority_str.lower())
    except ValueError:
        logger.warning(f"Invalid priority '{priority_str}', defaulting to 'medium'")
        priority = PriorityLevel.MEDIUM
    
    estimated_hours = float(topic_data.get("estimated_hours", 1.0))
    
    # Validate hours
    if estimated_hours <= 0:
        raise ValueError(f"Estimated hours must be > 0, got {estimated_hours}")
    
    if estimated_hours > 8.0:
        logger.warning(f"Estimated hours {estimated_hours} exceeds 8h, may be unrealistic")
    
    subtopics = topic_data.get("subtopics", [])
    resources = topic_data.get("resources", [])
    goals = topic_data.get("goals", [])
    
    # Create DailyTopic model
    try:
        daily_topic = DailyTopic(
            topic=topic_name,
            subject=subject,
            priority=priority,
            estimated_hours=estimated_hours,
            subtopics=subtopics,
            resources=resources,
            goals=goals
        )
        return daily_topic
    except ValidationError as e:
        logger.error(f"Pydantic validation failed for topic: {str(e)}")
        raise ValueError(f"Failed to create DailyTopic model: {str(e)}")


def parse_schedule_day(
    day_data: Dict[str, Any],
    start_date: Optional[date] = None
) -> ScheduleDay:
    """
    Parse day data dict into ScheduleDay model.
    
    Args:
        day_data: Day dictionary with fields like day_number, topics, etc.
        start_date: Schedule start date for calculating dates (default: today)
    
    Returns:
        ScheduleDay Pydantic model instance
    
    Raises:
        ValueError: If required fields are missing or invalid
    
    Example:
        >>> day_data = {
        ...     "day_number": 1,
        ...     "date": "2024-01-15",
        ...     "subjects": ["Physics"],
        ...     "topics": [...],
        ...     "total_hours": 5.0,
        ...     "milestones": ["Complete thermodynamics"]
        ... }
        >>> day = parse_schedule_day(day_data)
        >>> print(day.day_number)
        1
    """
    if start_date is None:
        start_date = date.today()
    
    # Extract day_number
    day_number = day_data.get("day_number")
    if day_number is None:
        raise ValueError("Missing required field: 'day_number'")
    
    try:
        day_number = int(day_number)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid day_number: {day_number} (must be integer)")
    
    if day_number <= 0:
        raise ValueError(f"day_number must be positive, got {day_number}")
    
    # Parse date
    if "date" in day_data and day_data["date"]:
        date_str = day_data["date"]
        if isinstance(date_str, str):
            schedule_date = convert_dates(date_str)
        elif isinstance(date_str, date):
            schedule_date = date_str
        else:
            logger.warning(f"Unexpected date type: {type(date_str)}, calculating from day_number")
            schedule_date = start_date + timedelta(days=day_number - 1)
    else:
        # Calculate from day_number
        schedule_date = start_date + timedelta(days=day_number - 1)
        logger.debug(f"Calculated date for day {day_number}: {schedule_date}")
    
    # Extract subjects
    subjects = day_data.get("subjects", [])
    
    # Parse topics
    topics_data = day_data.get("topics", [])
    if not topics_data:
        raise ValueError(f"Day {day_number} has no topics")
    
    topics = []
    for topic_data in topics_data:
        try:
            topic = parse_daily_topic(topic_data)
            topics.append(topic)
        except ValueError as e:
            logger.error(f"Failed to parse topic in day {day_number}: {str(e)}")
            raise ValueError(f"Day {day_number} topic parsing failed: {str(e)}")
    
    # Extract total_hours
    total_hours = day_data.get("total_hours")
    if total_hours is None:
        # Calculate from topics
        total_hours = sum(t.estimated_hours for t in topics)
        logger.debug(f"Calculated total_hours for day {day_number}: {total_hours}")
    else:
        total_hours = float(total_hours)
    
    # Extract milestones
    milestones = day_data.get("milestones", [])
    
    # Create ScheduleDay model
    try:
        schedule_day = ScheduleDay(
            day_number=day_number,
            schedule_date=schedule_date,
            subjects=subjects,
            topics=topics,
            total_hours=total_hours,
            milestones=milestones,
            completed=False,
            completion_percentage=0.0
        )
        return schedule_day
    except ValidationError as e:
        logger.error(f"Pydantic validation failed for day {day_number}: {str(e)}")
        raise ValueError(f"Failed to create ScheduleDay model: {str(e)}")


def parse_schedule_json(
    schedule_data: Dict[str, Any],
    schedule_id: str,
    student_id: str,
    analytics_id: str,
    exam_type: str,
    exam_date: date,
    daily_study_hours: float,
    auto_fix: bool = True
) -> Schedule:
    """
    Parse Gemini JSON response into Schedule Pydantic model.
    
    This is the main parsing function that coordinates validation, fixing,
    and model creation.
    
    Args:
        schedule_data: Raw JSON dict from Gemini response
        schedule_id: Unique schedule identifier
        student_id: Student identifier
        analytics_id: Analytics report ID
        exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        exam_date: Exam date
        daily_study_hours: Daily study hours
        auto_fix: Whether to automatically fix common issues (default: True)
    
    Returns:
        Schedule Pydantic model instance
    
    Raises:
        ScheduleValidationError: If validation fails
        ValueError: If parsing fails
    
    Example:
        >>> gemini_json = {
        ...     "daily_schedule": [
        ...         {"day_number": 1, "topics": [...], ...}
        ...     ],
        ...     "revision_schedule": {"revision_days": [70, 71, 72]},
        ...     "practice_tests": {"test_days": [73, 74]}
        ... }
        >>> schedule = parse_schedule_json(
        ...     gemini_json,
        ...     "schedule_123",
        ...     "student_456",
        ...     "analytics_789",
        ...     "JEE_MAIN",
        ...     date(2024, 4, 1),
        ...     5.0
        ... )
    """
    logger.info(
        f"Parsing schedule JSON for student {student_id}, "
        f"exam: {exam_type}, auto_fix: {auto_fix}"
    )
    
    # Apply auto-fixes if enabled
    if auto_fix:
        start_date = date.today()
        schedule_data = fix_common_issues(schedule_data, start_date)
    
    # Validate structure
    is_valid, validation_errors = validate_schedule_structure(schedule_data)
    if not is_valid:
        error_msg = f"Schedule validation failed: {'; '.join(validation_errors)}"
        logger.error(error_msg)
        raise ScheduleValidationError(error_msg)
    
    # Extract daily schedule
    daily_schedule_data = schedule_data.get("daily_schedule", [])
    
    # Parse each day
    schedule_days = []
    start_date = date.today()
    
    for day_data in daily_schedule_data:
        try:
            schedule_day = parse_schedule_day(day_data, start_date)
            schedule_days.append(schedule_day)
        except ValueError as e:
            logger.error(f"Failed to parse day: {str(e)}")
            raise ValueError(f"Day parsing failed: {str(e)}")
    
    # Extract metadata
    metadata = schedule_data.get("schedule_metadata", {})
    total_days = metadata.get("total_days", len(schedule_days))
    
    # Extract revision days
    revision_data = schedule_data.get("revision_schedule", {})
    revision_days = revision_data.get("revision_days", [])
    
    # Extract practice test days
    practice_data = schedule_data.get("practice_tests", {})
    practice_test_days = practice_data.get("test_days", [])
    
    # Extract buffer days (if present)
    buffer_days = schedule_data.get("buffer_days", [])
    
    # Parse exam_type
    try:
        exam_type_enum = ExamType(exam_type)
    except ValueError:
        logger.error(f"Invalid exam_type: {exam_type}")
        raise ValueError(f"Invalid exam_type: {exam_type}. Must be one of {list(ExamType)}")
    
    # Create Schedule model
    try:
        schedule = Schedule(
            schedule_id=schedule_id,
            student_id=student_id,
            analytics_id=analytics_id,
            exam_type=exam_type_enum,
            exam_date=exam_date,
            generated_date=datetime.utcnow(),
            total_days=total_days,
            daily_study_hours=daily_study_hours,
            status=ScheduleStatus.ACTIVE,
            days=schedule_days,
            revision_days=revision_days,
            practice_test_days=practice_test_days,
            buffer_days=buffer_days,
            priority_topics=[]  # Will be populated separately if needed
        )
        
        logger.info(
            f"Successfully parsed schedule: {schedule_id}, "
            f"{len(schedule_days)} days, {len(revision_days)} revision days, "
            f"{len(practice_test_days)} test days"
        )
        
        return schedule
        
    except ValidationError as e:
        logger.error(f"Pydantic validation failed for Schedule: {str(e)}")
        raise ValueError(f"Failed to create Schedule model: {str(e)}")
