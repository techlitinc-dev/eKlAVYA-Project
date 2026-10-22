"""
Utility modules for Mentor AI Platform.

This package contains utility functions and helper modules for various
operations including time calculations, data processing, and validation.

Modules:
- time_calculator: Time-based calculations for schedule generation
- schedule_context_builder: Context building for Gemini scheduling prompts
- schedule_parser: Parser for Gemini schedule responses

Author: Mentor AI Team
Version: 1.0.0
"""

from utils.time_calculator import (
    calculate_available_days,
    calculate_total_study_hours,
    distribute_hours_across_topics,
    calculate_revision_days,
    calculate_practice_test_days,
    validate_time_feasibility,
    adjust_daily_hours,
    calculate_buffer_days,
    TimeCalculatorError,
    InvalidDateRangeError,
    InfeasibleScheduleError,
)

from utils.schedule_context_builder import (
    build_student_context,
    build_analytics_context,
    build_priority_context,
    build_weightages_context,
    build_constraints_context,
    build_complete_context,
    format_topic_list,
    format_date,
)

from utils.schedule_parser import (
    parse_schedule_json,
    parse_schedule_day,
    parse_daily_topic,
    validate_schedule_structure,
    validate_topic_data,
    fix_common_issues,
    convert_dates,
    ScheduleParserError,
    ScheduleValidationError,
    DateParsingError,
)

__all__ = [
    # Time calculator functions
    "calculate_available_days",
    "calculate_total_study_hours",
    "distribute_hours_across_topics",
    "calculate_revision_days",
    "calculate_practice_test_days",
    "validate_time_feasibility",
    "adjust_daily_hours",
    "calculate_buffer_days",
    # Time calculator exceptions
    "TimeCalculatorError",
    "InvalidDateRangeError",
    "InfeasibleScheduleError",
    # Schedule context builder functions
    "build_student_context",
    "build_analytics_context",
    "build_priority_context",
    "build_weightages_context",
    "build_constraints_context",
    "build_complete_context",
    "format_topic_list",
    "format_date",
    # Schedule parser functions
    "parse_schedule_json",
    "parse_schedule_day",
    "parse_daily_topic",
    "validate_schedule_structure",
    "validate_topic_data",
    "fix_common_issues",
    "convert_dates",
    # Schedule parser exceptions
    "ScheduleParserError",
    "ScheduleValidationError",
    "DateParsingError",
]
