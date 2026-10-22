"""
Gemini Scheduler Service for AI-Powered Study Schedule Generation - Mentor AI Platform.

This module provides a service for generating personalized study schedules using
Google's Gemini Flash 1.5 model. It analyzes student performance, exam constraints,
and topic priorities to create optimal day-by-day study plans.

Features:
- Schedule generation with structured JSON output
- Retry logic with exponential backoff for API failures
- Response validation and parsing
- JSON extraction from markdown code blocks
- Comprehensive error handling
- Timeout management
- Request/response logging
- Schedule validation and refinement
- Cost tracking and usage statistics

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.gemini_scheduler_service import GeminiSchedulerService
    >>> from utils.schedule_context_builder import build_complete_context
    >>> 
    >>> # Initialize service
    >>> service = GeminiSchedulerService()
    >>> 
    >>> # Build context
    >>> context = build_complete_context(
    ...     student_profile=profile,
    ...     analytics_data=analytics,
    ...     priority_topics=priorities,
    ...     weightages=weightages,
    ...     constraints=constraints
    ... )
    >>> 
    >>> # Generate schedule
    >>> schedule = service.generate_schedule(context)
    >>> print(f"Generated {len(schedule.days)} day schedule")
    >>> 
    >>> # Check usage stats
    >>> stats = service.get_usage_stats()
    >>> print(f"Total API calls: {stats['total_calls']}")
"""

import os
import json
import time
import logging
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core import exceptions as google_exceptions
from pydantic import ValidationError

from models.schedule_models import (
    Schedule,
    ScheduleDay,
    DailyTopic,
    TopicPriority,
    ExamType,
    PriorityLevel,
    ScheduleStatus
)

# Configure logging
logger = logging.getLogger(__name__)

# Gemini Flash pricing (as of 2024)
# Input: $0.000125 per 1K tokens (up to 128K context)
# Output: $0.000375 per 1K tokens
GEMINI_INPUT_COST_PER_1K = 0.000125
GEMINI_OUTPUT_COST_PER_1K = 0.000375

# API configuration
DEFAULT_TIMEOUT = 60  # seconds (longer for schedule generation)
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2  # seconds
RETRY_BACKOFF_FACTOR = 2  # exponential backoff
MAX_REFINEMENT_ATTEMPTS = 2

# Generation parameters
GENERATION_CONFIG = {
    "temperature": 0.7,  # Balanced creativity and consistency
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 8000,  # Longer for complete schedules
}


class GeminiSchedulerError(Exception):
    """Base exception for Gemini Scheduler Service errors."""
    pass


class SchedulerAPIError(GeminiSchedulerError):
    """Exception raised for API-related errors."""
    pass


class SchedulerParsingError(GeminiSchedulerError):
    """Exception raised for response parsing errors."""
    pass


class SchedulerValidationError(GeminiSchedulerError):
    """Exception raised for schedule validation errors."""
    pass


class SchedulerTimeoutError(GeminiSchedulerError):
    """Exception raised when API call times out."""
    pass


def log_execution_time(func):
    """Decorator to log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed_time:.2f}s")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed_time:.2f}s: {str(e)}")
            raise
    return wrapper


def initialize_gemini_client(
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash-lite"
) -> genai.GenerativeModel:
    """
    Initialize and configure Gemini client.
    
    Args:
        api_key: Google API key (reads from GOOGLE_API_KEY env if None)
        model_name: Gemini model name (default: gemini-2.5-flash-lite)
    
    Returns:
        Configured GenerativeModel instance
    
    Raises:
        ValueError: If API key is not provided or found in environment
        SchedulerAPIError: If initialization fails
    
    Example:
        >>> model = initialize_gemini_client()
        >>> print(f"Model initialized: {model.model_name}")
        Model initialized: gemini-2.5-flash-lite
    """
    logger.info("Initializing Gemini client for schedule generation")
    
    # Get API key
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "Google API key not provided. Set GOOGLE_API_KEY environment "
            "variable or pass api_key parameter."
        )
    
    # Configure Gemini
    try:
        genai.configure(api_key=api_key)
        logger.info("Gemini API configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        raise SchedulerAPIError(f"Failed to configure Gemini API: {str(e)}")
    
    # Initialize model
    try:
        model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini model initialized: {model_name}")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Gemini model: {str(e)}")
        raise SchedulerAPIError(f"Failed to initialize model: {str(e)}")


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from text that may contain markdown code blocks.
    
    This function handles responses that wrap JSON in markdown blocks like:
    ```json
    {...}
    ```
    
    Args:
        text: Text containing JSON (with or without markdown)
    
    Returns:
        Parsed JSON as dictionary
    
    Raises:
        SchedulerParsingError: If no valid JSON found
    
    Example:
        >>> text = '```json\\n{"key": "value"}\\n```'
        >>> data = extract_json_from_text(text)
        >>> print(data["key"])
        value
        
        >>> plain = '{"key": "value"}'
        >>> data = extract_json_from_text(plain)
        >>> print(data["key"])
        value
    """
    if not text or not text.strip():
        raise SchedulerParsingError("Empty response text")
    
    # Try to find JSON in markdown code blocks
    json_pattern = r'```(?:json)?\s*\n(.*?)\n```'
    matches = re.findall(json_pattern, text, re.DOTALL)
    
    if matches:
        # Use the first JSON block found
        json_str = matches[0].strip()
        logger.debug(f"Found JSON in markdown block: {len(json_str)} chars")
    else:
        # No markdown blocks, try to use the entire text
        json_str = text.strip()
        logger.debug(f"No markdown blocks found, parsing entire text: {len(json_str)} chars")
    
    # Parse JSON
    try:
        data = json.loads(json_str)
        logger.info(f"Successfully parsed JSON with {len(str(data))} chars")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {str(e)}")
        logger.debug(f"Failed JSON string (first 500 chars): {json_str[:500]}")
        raise SchedulerParsingError(f"Invalid JSON in response: {str(e)}")


def validate_gemini_output(schedule_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate Gemini-generated schedule data.
    
    Checks for required fields, sequential day numbers, total hours,
    and topic completeness.
    
    Args:
        schedule_data: Schedule data dictionary from Gemini
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    
    Example:
        >>> schedule = {
        ...     "daily_schedule": [
        ...         {"day_number": 1, "topics": [...], "total_hours": 5.0}
        ...     ]
        ... }
        >>> is_valid, errors = validate_gemini_output(schedule)
        >>> if not is_valid:
        ...     print(f"Validation errors: {errors}")
    """
    errors = []
    
    # Check for daily_schedule
    if "daily_schedule" not in schedule_data:
        errors.append("Missing 'daily_schedule' field")
        return False, errors
    
    daily_schedule = schedule_data.get("daily_schedule", [])
    
    if not daily_schedule:
        errors.append("Empty daily_schedule")
        return False, errors
    
    # Validate day numbers are sequential
    expected_day = 1
    for day in daily_schedule:
        if not isinstance(day, dict):
            errors.append(f"Day entry is not a dictionary: {type(day)}")
            continue
        
        day_number = day.get("day_number")
        if day_number != expected_day:
            errors.append(
                f"Non-sequential day number: expected {expected_day}, got {day_number}"
            )
        
        # Check required day fields
        if "topics" not in day:
            errors.append(f"Day {day_number} missing 'topics' field")
        
        if "total_hours" not in day:
            errors.append(f"Day {day_number} missing 'total_hours' field")
        
        # Validate topics
        topics = day.get("topics", [])
        if not topics:
            errors.append(f"Day {day_number} has no topics")
        else:
            for i, topic in enumerate(topics):
                if not isinstance(topic, dict):
                    errors.append(f"Day {day_number} topic {i} is not a dictionary")
                    continue
                
                # Check required topic fields
                required_topic_fields = ["topic", "subject", "priority", "estimated_hours"]
                for field in required_topic_fields:
                    if field not in topic:
                        errors.append(
                            f"Day {day_number} topic {i} missing '{field}' field"
                        )
        
        expected_day += 1
    
    # Check total days consistency
    if "schedule_metadata" in schedule_data:
        metadata = schedule_data["schedule_metadata"]
        if "total_days" in metadata:
            expected_total = metadata["total_days"]
            actual_total = len(daily_schedule)
            if expected_total != actual_total:
                errors.append(
                    f"Metadata total_days ({expected_total}) doesn't match "
                    f"actual days ({actual_total})"
                )
    
    is_valid = len(errors) == 0
    
    if is_valid:
        logger.info(f"Schedule validation passed: {len(daily_schedule)} days")
    else:
        logger.warning(f"Schedule validation failed with {len(errors)} errors")
    
    return is_valid, errors


def parse_gemini_schedule_response(
    response: Any,
    student_id: str,
    analytics_id: str,
    exam_type: str,
    exam_date: date,
    daily_study_hours: float
) -> Schedule:
    """
    Parse Gemini API response into Schedule Pydantic model.
    
    Args:
        response: Gemini API response object
        student_id: Student identifier
        analytics_id: Analytics report ID
        exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        exam_date: Exam date
        daily_study_hours: Daily study hours
    
    Returns:
        Schedule Pydantic model instance
    
    Raises:
        SchedulerParsingError: If parsing fails
        SchedulerValidationError: If validation fails
    
    Example:
        >>> response = model.generate_content(prompt)
        >>> schedule = parse_gemini_schedule_response(
        ...     response, "student_123", "analytics_456",
        ...     "JEE_MAIN", date(2024, 4, 1), 5.0
        ... )
        >>> print(f"Schedule has {len(schedule.days)} days")
    """
    logger.info("Parsing Gemini response into Schedule model")
    
    # Extract text from response
    try:
        response_text = response.text
        logger.debug(f"Response text length: {len(response_text)} chars")
    except Exception as e:
        raise SchedulerParsingError(f"Failed to extract text from response: {str(e)}")
    
    # Extract JSON from text
    schedule_data = extract_json_from_text(response_text)
    
    # Validate JSON structure
    is_valid, validation_errors = validate_gemini_output(schedule_data)
    if not is_valid:
        error_msg = f"Schedule validation failed: {'; '.join(validation_errors)}"
        logger.error(error_msg)
        raise SchedulerValidationError(error_msg)
    
    # Parse into Schedule model
    try:
        # Extract daily schedule
        daily_schedule_data = schedule_data.get("daily_schedule", [])
        
        # Parse each day
        schedule_days = []
        start_date = date.today()
        
        for day_data in daily_schedule_data:
            # Parse topics for this day
            day_topics = []
            for topic_data in day_data.get("topics", []):
                daily_topic = DailyTopic(
                    topic=topic_data.get("topic", "Unknown"),
                    subject=topic_data.get("subject", "Unknown"),
                    priority=PriorityLevel(topic_data.get("priority", "medium")),
                    estimated_hours=float(topic_data.get("estimated_hours", 1.0)),
                    subtopics=topic_data.get("subtopics", []),
                    resources=topic_data.get("resources", []),
                    goals=topic_data.get("goals", [])
                )
                day_topics.append(daily_topic)
            
            # Calculate schedule date
            day_number = day_data.get("day_number", 1)
            schedule_date = start_date + timedelta(days=day_number - 1)
            
            # Create ScheduleDay
            schedule_day = ScheduleDay(
                day_number=day_number,
                schedule_date=schedule_date,
                subjects=day_data.get("subjects", []),
                topics=day_topics,
                total_hours=float(day_data.get("total_hours", 0.0)),
                milestones=day_data.get("milestones", []),
                completed=False,
                completion_percentage=0.0
            )
            schedule_days.append(schedule_day)
        
        # Extract metadata
        metadata = schedule_data.get("schedule_metadata", {})
        total_days = metadata.get("total_days", len(schedule_days))
        
        # Extract revision and practice test days
        revision_data = schedule_data.get("revision_schedule", {})
        revision_days = revision_data.get("revision_days", [])
        
        practice_data = schedule_data.get("practice_tests", {})
        practice_test_days = practice_data.get("test_days", [])
        
        # Generate schedule ID
        timestamp = int(datetime.now().timestamp())
        schedule_id = f"schedule_{student_id}_{analytics_id}_{timestamp}"
        
        # Create Schedule model
        schedule = Schedule(
            schedule_id=schedule_id,
            student_id=student_id,
            analytics_id=analytics_id,
            exam_type=ExamType(exam_type),
            exam_date=exam_date,
            generated_date=datetime.utcnow(),
            total_days=total_days,
            daily_study_hours=daily_study_hours,
            status=ScheduleStatus.ACTIVE,
            days=schedule_days,
            revision_days=revision_days,
            practice_test_days=practice_test_days,
            buffer_days=[],  # Will be calculated if needed
            priority_topics=[]  # Will be populated from analytics
        )
        
        logger.info(
            f"Successfully parsed schedule: {schedule_id}, "
            f"{len(schedule_days)} days, {len(revision_days)} revision days"
        )
        
        return schedule
        
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {str(e)}")
        raise SchedulerValidationError(f"Schedule model validation failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error parsing schedule: {str(e)}")
        raise SchedulerParsingError(f"Failed to parse schedule: {str(e)}")


class GeminiSchedulerService:
    """
    Service for generating AI-powered study schedules using Gemini Flash.
    
    This service manages schedule generation with robust error handling,
    retry logic, validation, refinement, and cost tracking.
    
    Attributes:
        model: Gemini Flash model instance
        generation_config: Model generation configuration
        timeout: Request timeout in seconds
        usage_stats: Dictionary tracking API usage and costs
    
    Example:
        >>> service = GeminiSchedulerService()
        >>> schedule = service.generate_schedule(context_string)
        >>> print(f"Generated {len(schedule.days)} day schedule")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        model_name: str = "gemini-2.5-flash-lite"
    ):
        """
        Initialize Gemini Scheduler Service.
        
        Args:
            api_key: Google API key (reads from GOOGLE_API_KEY env if None)
            timeout: Request timeout in seconds (default: 60)
            model_name: Gemini model name (default: gemini-2.5-flash-lite)
        
        Raises:
            ValueError: If API key is not provided or found in environment
            SchedulerAPIError: If initialization fails
        """
        logger.info("Initializing GeminiSchedulerService")
        
        # Initialize Gemini client
        self.model = initialize_gemini_client(api_key, model_name)
        self.model_name = model_name
        
        # Generation configuration
        self.generation_config = GenerationConfig(**GENERATION_CONFIG)
        
        # Request configuration
        self.timeout = timeout
        
        # Usage statistics
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "validation_errors": 0,
            "parsing_errors": 0,
            "refinement_attempts": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
        }
        
        logger.info("GeminiSchedulerService initialized successfully")
    
    @log_execution_time
    def generate_schedule_with_gemini(
        self,
        context: str,
        student_id: str,
        analytics_id: str,
        exam_type: str,
        exam_date: date,
        daily_study_hours: float,
        max_retries: int = MAX_RETRIES
    ) -> Schedule:
        """
        Generate schedule using Gemini API with retry logic.
        
        Args:
            context: Formatted context string from context builder
            student_id: Student identifier
            analytics_id: Analytics report ID
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            exam_date: Exam date
            daily_study_hours: Daily study hours
            max_retries: Maximum retry attempts (default: 3)
        
        Returns:
            Schedule Pydantic model
        
        Raises:
            SchedulerAPIError: If API call fails after retries
            SchedulerParsingError: If response parsing fails
            SchedulerValidationError: If validation fails
            SchedulerTimeoutError: If request times out
        
        Example:
            >>> context = build_complete_context(...)
            >>> schedule = service.generate_schedule_with_gemini(
            ...     context, "student_123", "analytics_456",
            ...     "JEE_MAIN", date(2024, 4, 1), 5.0
            ... )
        """
        logger.info(
            f"Generating schedule for student {student_id}, "
            f"exam: {exam_type}, context length: {len(context)} chars"
        )
        
        self.usage_stats["total_calls"] += 1
        
        retry_count = 0
        retry_delay = INITIAL_RETRY_DELAY
        last_error = None
        
        while retry_count <= max_retries:
            try:
                # Log prompt (truncated)
                logger.debug(f"Sending prompt to Gemini (attempt {retry_count + 1}/{max_retries + 1})")
                logger.debug(f"Prompt preview: {context[:500]}...")
                
                # Call Gemini API
                start_time = time.time()
                response = self.model.generate_content(
                    context,
                    generation_config=self.generation_config,
                    request_options={"timeout": self.timeout}
                )
                api_time = time.time() - start_time
                
                logger.info(f"Gemini API call completed in {api_time:.2f}s")
                logger.debug(f"Response preview: {response.text[:500]}...")
                
                # Track tokens and cost
                if hasattr(response, 'usage_metadata'):
                    input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                    output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                    
                    self.usage_stats["total_input_tokens"] += input_tokens
                    self.usage_stats["total_output_tokens"] += output_tokens
                    
                    # Calculate cost
                    input_cost = (input_tokens / 1000) * GEMINI_INPUT_COST_PER_1K
                    output_cost = (output_tokens / 1000) * GEMINI_OUTPUT_COST_PER_1K
                    total_cost = input_cost + output_cost
                    self.usage_stats["total_cost"] += total_cost
                    
                    logger.info(
                        f"Token usage: {input_tokens} in, {output_tokens} out, "
                        f"cost: ${total_cost:.4f}"
                    )
                
                # Parse response
                schedule = parse_gemini_schedule_response(
                    response,
                    student_id,
                    analytics_id,
                    exam_type,
                    exam_date,
                    daily_study_hours
                )
                
                self.usage_stats["successful_calls"] += 1
                logger.info(f"Schedule generated successfully: {schedule.schedule_id}")
                
                return schedule
                
            except google_exceptions.DeadlineExceeded as e:
                last_error = e
                logger.warning(f"Request timeout (attempt {retry_count + 1}): {str(e)}")
                
                if retry_count < max_retries:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                    retry_count += 1
                else:
                    self.usage_stats["failed_calls"] += 1
                    raise SchedulerTimeoutError(f"Request timed out after {max_retries + 1} attempts")
            
            except google_exceptions.ResourceExhausted as e:
                last_error = e
                logger.warning(f"Rate limit exceeded (attempt {retry_count + 1}): {str(e)}")
                
                if retry_count < max_retries:
                    # Longer wait for rate limits
                    wait_time = retry_delay * 2
                    logger.info(f"Waiting {wait_time}s for rate limit...")
                    time.sleep(wait_time)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                    retry_count += 1
                else:
                    self.usage_stats["failed_calls"] += 1
                    raise SchedulerAPIError(f"Rate limit exceeded after {max_retries + 1} attempts")
            
            except (SchedulerParsingError, SchedulerValidationError) as e:
                last_error = e
                logger.error(f"Parsing/validation error: {str(e)}")
                
                if isinstance(e, SchedulerParsingError):
                    self.usage_stats["parsing_errors"] += 1
                else:
                    self.usage_stats["validation_errors"] += 1
                
                if retry_count < max_retries:
                    logger.info(f"Retrying with adjusted prompt in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                    retry_count += 1
                else:
                    self.usage_stats["failed_calls"] += 1
                    raise
            
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error (attempt {retry_count + 1}): {str(e)}")
                
                if retry_count < max_retries:
                    logger.info(f"Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                    retry_count += 1
                else:
                    self.usage_stats["failed_calls"] += 1
                    raise SchedulerAPIError(f"Failed after {max_retries + 1} attempts: {str(e)}")
        
        # Should not reach here, but just in case
        self.usage_stats["failed_calls"] += 1
        raise SchedulerAPIError(f"Failed to generate schedule: {str(last_error)}")
    
    def retry_with_refinement(
        self,
        original_context: str,
        validation_issues: List[str],
        student_id: str,
        analytics_id: str,
        exam_type: str,
        exam_date: date,
        daily_study_hours: float,
        max_attempts: int = MAX_REFINEMENT_ATTEMPTS
    ) -> Optional[Schedule]:
        """
        Retry schedule generation with refinement based on validation issues.
        
        Args:
            original_context: Original prompt context
            validation_issues: List of validation error messages
            student_id: Student identifier
            analytics_id: Analytics report ID
            exam_type: Exam type
            exam_date: Exam date
            daily_study_hours: Daily study hours
            max_attempts: Maximum refinement attempts (default: 2)
        
        Returns:
            Refined Schedule or None if all attempts fail
        
        Example:
            >>> is_valid, errors = validate_gemini_output(data)
            >>> if not is_valid:
            ...     schedule = service.retry_with_refinement(
            ...         context, errors, "student_123", ...
            ...     )
        """
        logger.info(f"Attempting refinement with {len(validation_issues)} issues")
        
        issues_text = "\n".join(f"- {issue}" for issue in validation_issues)
        
        refinement_prompt = f"""
The previous schedule generation had the following issues:
{issues_text}

Please regenerate the schedule addressing ALL these issues. Ensure:
1. All required fields are present
2. Day numbers are sequential starting from 1
3. Each day has topics with complete information
4. Total hours are realistic and match constraints
5. JSON structure is valid and complete

{original_context}
"""
        
        for attempt in range(max_attempts):
            try:
                logger.info(f"Refinement attempt {attempt + 1}/{max_attempts}")
                self.usage_stats["refinement_attempts"] += 1
                
                schedule = self.generate_schedule_with_gemini(
                    refinement_prompt,
                    student_id,
                    analytics_id,
                    exam_type,
                    exam_date,
                    daily_study_hours,
                    max_retries=1  # Fewer retries for refinement
                )
                
                logger.info(f"Refinement successful on attempt {attempt + 1}")
                return schedule
                
            except Exception as e:
                logger.warning(f"Refinement attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(2)  # Wait before next attempt
                continue
        
        logger.error(f"All {max_attempts} refinement attempts failed")
        return None
    
    def generate_schedule(
        self,
        context: str,
        student_id: str,
        analytics_id: str,
        exam_type: str,
        exam_date: date,
        daily_study_hours: float,
        enable_refinement: bool = True
    ) -> Schedule:
        """
        Generate schedule with automatic refinement if needed.
        
        This is the main entry point for schedule generation. It will
        automatically retry with refinement if the first attempt has
        validation issues.
        
        Args:
            context: Formatted context from context builder
            student_id: Student identifier
            analytics_id: Analytics report ID
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            exam_date: Exam date
            daily_study_hours: Daily study hours
            enable_refinement: Whether to enable automatic refinement (default: True)
        
        Returns:
            Schedule Pydantic model
        
        Raises:
            SchedulerError: If schedule generation fails
        
        Example:
            >>> from utils.schedule_context_builder import build_complete_context
            >>> context = build_complete_context(...)
            >>> schedule = service.generate_schedule(
            ...     context, "student_123", "analytics_456",
            ...     "JEE_MAIN", date(2024, 4, 1), 5.0
            ... )
            >>> print(f"Schedule ID: {schedule.schedule_id}")
        """
        try:
            # First attempt
            schedule = self.generate_schedule_with_gemini(
                context,
                student_id,
                analytics_id,
                exam_type,
                exam_date,
                daily_study_hours
            )
            return schedule
            
        except SchedulerValidationError as e:
            logger.warning(f"Initial generation had validation errors: {str(e)}")
            
            if not enable_refinement:
                raise
            
            # Extract validation issues
            validation_issues = str(e).split("; ")
            
            # Try refinement
            refined_schedule = self.retry_with_refinement(
                context,
                validation_issues,
                student_id,
                analytics_id,
                exam_type,
                exam_date,
                daily_study_hours
            )
            
            if refined_schedule:
                return refined_schedule
            else:
                raise SchedulerError("Schedule generation failed even after refinement")
        
        except Exception as e:
            logger.error(f"Schedule generation failed: {str(e)}")
            raise
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage metrics and costs
        
        Example:
            >>> stats = service.get_usage_stats()
            >>> print(f"Total cost: ${stats['total_cost']:.4f}")
            >>> print(f"Success rate: {stats['success_rate']:.1f}%")
        """
        total_calls = self.usage_stats["total_calls"]
        successful_calls = self.usage_stats["successful_calls"]
        
        success_rate = (
            (successful_calls / total_calls * 100)
            if total_calls > 0
            else 0.0
        )
        
        return {
            **self.usage_stats,
            "success_rate": round(success_rate, 2),
            "average_cost_per_call": (
                self.usage_stats["total_cost"] / total_calls
                if total_calls > 0
                else 0.0
            )
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        logger.info("Resetting usage statistics")
        for key in self.usage_stats:
            if isinstance(self.usage_stats[key], (int, float)):
                self.usage_stats[key] = 0 if isinstance(self.usage_stats[key], int) else 0.0
