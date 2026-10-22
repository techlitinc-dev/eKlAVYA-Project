"""
Date Utility Functions

This module provides date and time utility functions for the Mentor AI EdTech
platform exam scheduling system. It includes functions for date validation,
calculation, formatting, and exam-specific date handling.

Functions:
- calculate_days_until: Calculate days between today and target date
- validate_exam_date: Validate if exam date is sufficiently in future
- get_available_exam_dates: Get valid exam dates for JEE/NEET
- format_date_for_display: Format datetime for user display
- parse_date_string: Parse string to datetime object

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime, timedelta, timezone
from typing import List


def calculate_days_until(target_date: datetime) -> int:
    """
    Calculate number of days from today to target date.
    
    Calculates the difference between the current date (UTC) and the
    target date. Returns the number of days remaining until the target date.
    
    Args:
        target_date: The target datetime object
    
    Returns:
        int: Number of days until target date (positive integer)
    
    Raises:
        ValueError: If target date is in the past
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> future_date = datetime.now() + timedelta(days=100)
        >>> days = calculate_days_until(future_date)
        >>> print(days)
        100
    """
    # Get current date in UTC (normalize to start of day)
    now = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Ensure target_date is timezone-aware
    if target_date.tzinfo is None:
        target_date = target_date.replace(tzinfo=timezone.utc)
    
    # Normalize target date to start of day
    target_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate difference
    delta = target_date - now
    days = delta.days
    
    # Raise error if date is in the past
    if days < 0:
        raise ValueError(f"Target date {target_date.strftime('%Y-%m-%d')} is in the past")
    
    return days


def validate_exam_date(exam_date: datetime, min_days: int = 30) -> bool:
    """
    Validate if exam date is at least min_days in the future.
    
    Checks if the provided exam date is sufficiently far in the future
    to allow for adequate preparation time.
    
    Args:
        exam_date: The proposed exam datetime
        min_days: Minimum number of days required (default: 30)
    
    Returns:
        bool: True if exam date is valid, False otherwise
    
    Example:
        >>> from datetime import datetime, timedelta
        >>> future_date = datetime.now() + timedelta(days=45)
        >>> is_valid = validate_exam_date(future_date, min_days=30)
        >>> print(is_valid)
        True
    """
    try:
        days_until = calculate_days_until(exam_date)
        return days_until >= min_days
    except ValueError:
        # Date is in the past
        return False


def get_available_exam_dates(exam_type: str) -> List[datetime]:
    """
    Get list of valid exam dates for JEE or NEET exams.
    
    Returns upcoming exam dates based on the exam type. Only future
    dates are included in the returned list.
    
    JEE Exam Dates:
    - January 15 (Session 1)
    - April 15 (Session 2)
    
    NEET Exam Dates:
    - May 5
    
    Args:
        exam_type: Type of exam ("JEE" or "NEET")
    
    Returns:
        List[datetime]: List of valid future exam dates
    
    Raises:
        ValueError: If exam_type is not "JEE" or "NEET"
    
    Example:
        >>> dates = get_available_exam_dates("JEE")
        >>> for date in dates:
        ...     print(format_date_for_display(date))
        15 Jan 2026
        15 Apr 2026
    """
    exam_type = exam_type.upper().strip()
    
    if exam_type not in ["JEE", "NEET"]:
        raise ValueError(f"Invalid exam type: {exam_type}. Must be 'JEE' or 'NEET'")
    
    # Get current date
    now = datetime.now(timezone.utc)
    current_year = now.year
    
    available_dates = []
    
    if exam_type == "JEE":
        # JEE has two sessions: January 15 and April 15
        jee_dates = [
            (1, 15),   # January 15
            (4, 15),   # April 15
        ]
        
        for month, day in jee_dates:
            # Check current year
            exam_date = datetime(current_year, month, day, tzinfo=timezone.utc)
            if exam_date > now:
                available_dates.append(exam_date)
            
            # Check next year
            next_year_date = datetime(current_year + 1, month, day, tzinfo=timezone.utc)
            available_dates.append(next_year_date)
    
    elif exam_type == "NEET":
        # NEET has one session: May 5
        neet_date = datetime(current_year, 5, 5, tzinfo=timezone.utc)
        
        if neet_date > now:
            available_dates.append(neet_date)
        
        # Add next year's date
        next_year_date = datetime(current_year + 1, 5, 5, tzinfo=timezone.utc)
        available_dates.append(next_year_date)
    
    # Sort dates chronologically
    available_dates.sort()
    
    return available_dates


def format_date_for_display(date: datetime) -> str:
    """
    Format datetime object for user-friendly display.
    
    Converts a datetime object to a readable string format suitable
    for displaying to users in the application.
    
    Args:
        date: Datetime object to format
    
    Returns:
        str: Formatted date string in "DD MMM YYYY" format
    
    Example:
        >>> from datetime import datetime
        >>> date = datetime(2026, 1, 15)
        >>> formatted = format_date_for_display(date)
        >>> print(formatted)
        15 Jan 2026
    """
    return date.strftime("%d %b %Y")


def parse_date_string(date_str: str) -> datetime:
    """
    Parse date string to datetime object.
    
    Converts a date string in "YYYY-MM-DD" format to a timezone-aware
    datetime object (UTC).
    
    Args:
        date_str: Date string in "YYYY-MM-DD" format
    
    Returns:
        datetime: Parsed datetime object with UTC timezone
    
    Raises:
        ValueError: If date string format is invalid
    
    Example:
        >>> date = parse_date_string("2026-01-15")
        >>> print(date)
        2026-01-15 00:00:00+00:00
    """
    try:
        # Parse the date string
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # Add UTC timezone
        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
        
        return parsed_date
    
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD (e.g., '2026-01-15')"
        ) from e


# Example usage (for testing purposes)
if __name__ == "__main__":
    # Example 1: Calculate days until a future date
    print("Example 1: Calculate days until exam")
    future_exam = datetime(2026, 5, 5, tzinfo=timezone.utc)
    days = calculate_days_until(future_exam)
    print(f"Days until exam: {days}")
    print()
    
    # Example 2: Validate exam date
    print("Example 2: Validate exam date")
    is_valid = validate_exam_date(future_exam, min_days=30)
    print(f"Is exam date valid (30+ days away)? {is_valid}")
    print()
    
    # Example 3: Get available JEE dates
    print("Example 3: Get available JEE dates")
    jee_dates = get_available_exam_dates("JEE")
    print("Available JEE exam dates:")
    for date in jee_dates:
        print(f"  - {format_date_for_display(date)}")
    print()
    
    # Example 4: Get available NEET dates
    print("Example 4: Get available NEET dates")
    neet_dates = get_available_exam_dates("NEET")
    print("Available NEET exam dates:")
    for date in neet_dates:
        print(f"  - {format_date_for_display(date)}")
    print()
    
    # Example 5: Parse date string
    print("Example 5: Parse date string")
    date_str = "2026-01-15"
    parsed = parse_date_string(date_str)
    print(f"Parsed date: {parsed}")
    print(f"Formatted: {format_date_for_display(parsed)}")
