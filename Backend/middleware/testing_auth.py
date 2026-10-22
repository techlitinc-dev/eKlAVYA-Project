"""
Testing Authentication Middleware

This module provides a testing authentication bypass for development
and testing purposes. It should only be used in development environments.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, status

# Configure logging
logger = logging.getLogger(__name__)


async def get_current_user_testing(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Testing dependency function to bypass authentication.
    
    This function provides a mock user ID for testing purposes.
    In production, this should be replaced with the actual get_current_user.
    
    Args:
        authorization: Authorization header (ignored in testing)
    
    Returns:
        str: Mock user ID for testing
    
    Example:
        >>> @router.get("/profile")
        >>> async def get_profile(user_id: str = Depends(get_current_user_testing)):
        ...     return {"user_id": user_id}
    """
    # For testing, always return a valid test user
    logger.debug("Using testing authentication bypass")
    return "test_parent_123"


async def get_current_student_testing(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Testing dependency function to bypass authentication for students.
    
    This function provides a mock student ID for testing purposes.
    
    Args:
        authorization: Authorization header (ignored in testing)
    
    Returns:
        str: Mock student ID for testing
    """
    logger.debug("Using testing student authentication bypass")
    return "test_student_123"
