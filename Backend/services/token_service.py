"""
JWT Token Service Module

This module handles JWT token generation and validation for session management
in the Mentor AI EdTech Platform. It provides functions to create access tokens,
refresh tokens, and verify token authenticity.

Functions:
- generate_access_token: Create JWT access token (24 hours expiry)
- generate_refresh_token: Create JWT refresh token (30 days expiry)
- verify_token: Verify and decode JWT token
- decode_token_without_verification: Decode token without verification
- get_token_expiry_seconds: Get token expiry time in seconds

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Token expiry constants (in seconds)
ACCESS_TOKEN_EXPIRY = 86400  # 24 hours
REFRESH_TOKEN_EXPIRY = 2592000  # 30 days

# JWT algorithm
JWT_ALGORITHM = "HS256"


def _get_jwt_secret() -> str:
    """
    Get JWT secret key from environment variables.
    
    Returns:
        str: JWT secret key
    
    Raises:
        ValueError: If JWT_SECRET environment variable is not set
    """
    # JWT_SECRET is the canonical name; JWT_SECRET_KEY is the legacy
    # name used in .env.example — accept both so login works either way.
    jwt_secret = os.getenv("JWT_SECRET") or os.getenv("JWT_SECRET_KEY")

    if not jwt_secret:
        error_msg = (
            "JWT_SECRET environment variable is not set. "
            "Please configure it in your .env file for token generation."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return jwt_secret


def generate_access_token(
    parent_id: str,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> str:
    """
    Generate JWT access token for parent authentication.
    
    Creates a JWT access token with 24-hour expiry containing parent
    identification information. This token is used to authenticate
    API requests.
    
    Args:
        parent_id: Unique identifier for the parent account
        email: Parent's email address (optional)
        phone: Parent's phone number (optional)
    
    Returns:
        str: Encoded JWT access token
    
    Raises:
        ValueError: If JWT_SECRET is not configured
        Exception: If token generation fails
    
    Example:
        >>> token = generate_access_token(
        ...     parent_id="parent_123abc",
        ...     email="parent@example.com"
        ... )
        >>> print(token[:20])
        'eyJhbGciOiJIUzI1NiIs'
    """
    try:
        logger.info(f"Generating access token for parent: {parent_id}")
        
        # Get JWT secret
        jwt_secret = _get_jwt_secret()
        
        # Get current timestamp
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        
        # Build token payload
        payload: Dict[str, Any] = {
            "parent_id": parent_id,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiry
            "type": "access"
        }
        
        # Add optional fields if provided
        if email:
            payload["email"] = email
        
        if phone:
            payload["phone"] = phone
        
        # Generate JWT token
        token = jwt.encode(
            payload=payload,
            key=jwt_secret,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"Access token generated successfully for parent: {parent_id}")
        logger.debug(f"Token expires at: {expiry.isoformat()}")
        
        return token
    
    except ValueError as e:
        logger.error(f"Configuration error during access token generation: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error generating access token: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to generate access token: {str(e)}")


def generate_refresh_token(parent_id: str) -> str:
    """
    Generate JWT refresh token for obtaining new access tokens.
    
    Creates a JWT refresh token with 30-day expiry. This token is used
    to obtain new access tokens without requiring re-authentication.
    
    Args:
        parent_id: Unique identifier for the parent account
    
    Returns:
        str: Encoded JWT refresh token
    
    Raises:
        ValueError: If JWT_SECRET is not configured
        Exception: If token generation fails
    
    Example:
        >>> token = generate_refresh_token(parent_id="parent_123abc")
        >>> print(token[:20])
        'eyJhbGciOiJIUzI1NiIs'
    """
    try:
        logger.info(f"Generating refresh token for parent: {parent_id}")
        
        # Get JWT secret
        jwt_secret = _get_jwt_secret()
        
        # Get current timestamp
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=REFRESH_TOKEN_EXPIRY)
        
        # Build token payload
        payload: Dict[str, Any] = {
            "parent_id": parent_id,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiry
            "type": "refresh"
        }
        
        # Generate JWT token
        token = jwt.encode(
            payload=payload,
            key=jwt_secret,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"Refresh token generated successfully for parent: {parent_id}")
        logger.debug(f"Token expires at: {expiry.isoformat()}")
        
        return token
    
    except ValueError as e:
        logger.error(f"Configuration error during refresh token generation: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error generating refresh token: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to generate refresh token: {str(e)}")


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token.
    
    Validates the JWT token signature, expiry, and required fields.
    Returns the decoded payload if the token is valid.
    
    Args:
        token: JWT token string to verify
    
    Returns:
        Dict containing decoded token payload with parent_id and other claims
    
    Raises:
        ValueError: If JWT_SECRET is not configured
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or malformed
        Exception: If verification fails
    
    Example:
        >>> payload = verify_token(token)
        >>> print(payload['parent_id'])
        'parent_123abc'
    """
    try:
        logger.debug("Verifying JWT token")
        
        # Get JWT secret
        jwt_secret = _get_jwt_secret()
        
        # Decode and verify token
        payload = jwt.decode(
            jwt=token,
            key=jwt_secret,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Validate required fields - check for either parent_id or child_id
        is_student = payload.get("is_student", False)
        if is_student:
            if "child_id" not in payload and "student_id" not in payload:
                logger.error("Student token payload missing required field: child_id or student_id")
                raise jwt.InvalidTokenError("Invalid token: missing child_id or student_id")
            logger.info(f"Token verified successfully for student: {payload.get('username', 'unknown')}")
        else:
            if "parent_id" not in payload:
                logger.error("Token payload missing required field: parent_id")
                raise jwt.InvalidTokenError("Invalid token: missing parent_id")
            logger.info(f"Token verified successfully for parent: {payload['parent_id']}")
        
        logger.debug(f"Token type: {payload.get('type', 'unknown')}")
        
        return payload
    
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Token has expired: {e}")
        raise jwt.ExpiredSignatureError("Token has expired. Please login again.")
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise jwt.InvalidTokenError(f"Invalid token: {str(e)}")
    
    except ValueError as e:
        logger.error(f"Configuration error during token verification: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to verify token: {str(e)}")


def decode_token_without_verification(token: str) -> Dict[str, Any]:
    """
    Decode JWT token without verification.
    
    Decodes the token payload without verifying the signature or expiry.
    This is useful for debugging, logging, or extracting information from
    expired tokens. Should NOT be used for authentication.
    
    Args:
        token: JWT token string to decode
    
    Returns:
        Dict containing decoded token payload
    
    Raises:
        Exception: If decoding fails
    
    Example:
        >>> payload = decode_token_without_verification(expired_token)
        >>> print(payload['parent_id'])
        'parent_123abc'
    
    Warning:
        This function does NOT verify the token. Do not use for authentication.
    """
    try:
        logger.debug("Decoding token without verification (for debugging)")
        
        # Decode token without verification
        payload = jwt.decode(
            jwt=token,
            options={"verify_signature": False, "verify_exp": False}
        )
        
        logger.debug(f"Token decoded: parent_id={payload.get('parent_id')}, type={payload.get('type')}")
        
        return payload
    
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        raise Exception(f"Failed to decode token: {str(e)}")


def get_token_expiry_seconds(token_type: str = "access") -> int:
    """
    Get token expiry time in seconds.
    
    Returns the expiry time for access or refresh tokens in seconds.
    
    Args:
        token_type: Type of token ("access" or "refresh"), defaults to "access"
    
    Returns:
        int: Expiry time in seconds
    
    Example:
        >>> expiry = get_token_expiry_seconds("access")
        >>> print(expiry)
        86400
        >>> expiry = get_token_expiry_seconds("refresh")
        >>> print(expiry)
        2592000
    """
    if token_type == "refresh":
        return REFRESH_TOKEN_EXPIRY
    else:
        return ACCESS_TOKEN_EXPIRY


def extract_parent_id_from_token(token: str) -> Optional[str]:
    """
    Extract parent_id from token without full verification.
    
    Safely extracts the parent_id from a token for logging or debugging
    purposes. Returns None if extraction fails.
    
    Args:
        token: JWT token string
    
    Returns:
        Optional[str]: Parent ID if found, None otherwise
    
    Example:
        >>> parent_id = extract_parent_id_from_token(token)
        >>> print(parent_id)
        'parent_123abc'
    """
    try:
        payload = decode_token_without_verification(token)
        return payload.get("parent_id")
    except Exception as e:
        logger.warning(f"Failed to extract parent_id from token: {e}")
        return None



def generate_student_access_token(
    child_id: str,
    username: str,
    name: Optional[str] = None
) -> str:
    """
    Generate JWT access token for student authentication.
    
    Creates a JWT access token with 24-hour expiry containing student
    identification information. This token is used to authenticate
    API requests from students.
    
    Args:
        child_id: Unique identifier for the student/child account
        username: Student's username
        name: Student's name (optional)
    
    Returns:
        str: Encoded JWT access token
    
    Raises:
        ValueError: If JWT_SECRET is not configured
        Exception: If token generation fails
    
    Example:
        >>> token = generate_student_access_token(
        ...     child_id="child_123abc",
        ...     username="student1"
        ... )
        >>> print(token[:20])
        'eyJhbGciOiJIUzI1NiIs'
    """
    try:
        logger.info(f"Generating access token for student: {username}")
        
        # Get JWT secret
        jwt_secret = _get_jwt_secret()
        
        # Get current timestamp
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=ACCESS_TOKEN_EXPIRY)
        
        # Build token payload
        payload: Dict[str, Any] = {
            "child_id": child_id,
            "student_id": child_id,
            "username": username,
            "is_student": True,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiry
            "type": "access"
        }
        
        # Add optional fields if provided
        if name:
            payload["name"] = name
        
        # Generate JWT token
        token = jwt.encode(
            payload=payload,
            key=jwt_secret,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"Access token generated successfully for student: {username}")
        logger.debug(f"Token expires at: {expiry.isoformat()}")
        
        return token
    
    except ValueError as e:
        logger.error(f"Configuration error during student access token generation: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error generating student access token: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to generate student access token: {str(e)}")


def generate_student_refresh_token(child_id: str, username: str) -> str:
    """
    Generate JWT refresh token for students to obtain new access tokens.
    
    Creates a JWT refresh token with 30-day expiry. This token is used
    to obtain new access tokens without requiring re-authentication.
    
    Args:
        child_id: Unique identifier for the student/child account
        username: Student's username
    
    Returns:
        str: Encoded JWT refresh token
    
    Raises:
        ValueError: If JWT_SECRET is not configured
        Exception: If token generation fails
    
    Example:
        >>> token = generate_student_refresh_token(
        ...     child_id="child_123abc",
        ...     username="student1"
        ... )
        >>> print(token[:20])
        'eyJhbGciOiJIUzI1NiIs'
    """
    try:
        logger.info(f"Generating refresh token for student: {username}")
        
        # Get JWT secret
        jwt_secret = _get_jwt_secret()
        
        # Get current timestamp
        now = datetime.utcnow()
        expiry = now + timedelta(seconds=REFRESH_TOKEN_EXPIRY)
        
        # Build token payload
        payload: Dict[str, Any] = {
            "child_id": child_id,
            "student_id": child_id,
            "username": username,
            "is_student": True,
            "iat": int(now.timestamp()),  # Issued at
            "exp": int(expiry.timestamp()),  # Expiry
            "type": "refresh"
        }
        
        # Generate JWT token
        token = jwt.encode(
            payload=payload,
            key=jwt_secret,
            algorithm=JWT_ALGORITHM
        )
        
        logger.info(f"Refresh token generated successfully for student: {username}")
        logger.debug(f"Token expires at: {expiry.isoformat()}")
        
        return token
    
    except ValueError as e:
        logger.error(f"Configuration error during student refresh token generation: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error generating student refresh token: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to generate student refresh token: {str(e)}")


def verify_student_refresh_token(refresh_token: str) -> Dict[str, Any]:
    """
    Verify and decode student refresh token.
    
    Validates student refresh token signature, expiry, and required fields.
    Returns decoded payload if token is valid.
    
    Args:
        refresh_token: JWT refresh token string to verify
    
    Returns:
        Dict containing decoded token payload with child_id and other claims
    
    Raises:
        ValueError: If JWT_SECRET is not configured
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or malformed
        Exception: If verification fails
    
    Example:
        >>> payload = verify_student_refresh_token(refresh_token)
        >>> print(payload['child_id'])
        'child_123abc'
    """
    try:
        logger.debug("Verifying student refresh token")
        
        # Get JWT secret
        jwt_secret = _get_jwt_secret()
        
        # Decode and verify token
        payload = jwt.decode(
            jwt=refresh_token,
            key=jwt_secret,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Validate required fields for student tokens
        is_student = payload.get("is_student", False)
        if not is_student:
            logger.error("Token is not a student token")
            raise jwt.InvalidTokenError("Invalid token: not a student token")
        
        if "child_id" not in payload and "student_id" not in payload:
            logger.error("Student refresh token payload missing required field: child_id or student_id")
            raise jwt.InvalidTokenError("Invalid token: missing child_id or student_id")
        
        # Validate token type
        token_type = payload.get("type")
        if token_type != "refresh":
            logger.error(f"Invalid token type for refresh: {token_type}")
            raise jwt.InvalidTokenError("Invalid token: expected refresh token")
        
        logger.info(f"Student refresh token verified successfully for: {payload.get('username', 'unknown')}")
        logger.debug(f"Token expires at: {datetime.fromtimestamp(payload['exp']).isoformat()}")
        
        return payload
    
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"Student refresh token has expired: {e}")
        raise jwt.ExpiredSignatureError("Student refresh token has expired. Please login again.")
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid student refresh token: {e}")
        raise jwt.InvalidTokenError(f"Invalid student refresh token: {str(e)}")
    
    except ValueError as e:
        logger.error(f"Configuration error during student refresh token verification: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error verifying student refresh token: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to verify student refresh token: {str(e)}")
