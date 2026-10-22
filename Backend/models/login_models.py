"""
Login Data Models

This module defines Pydantic models for login-related API requests and responses
in the Mentor AI EdTech Platform. These models provide data validation,
serialization, and documentation for authentication and session management endpoints.

Models:
- EmailLoginRequest: Email and password login
- PhoneLoginRequest: Phone number and OTP login
- GoogleLoginRequest: Google OAuth login
- TokenRefreshRequest: JWT token refresh
- LoginResponse: Comprehensive login response with tokens
- TokenResponse: Token refresh response
- LogoutResponse: Logout confirmation

Author: Mentor AI Team
Version: 1.0.0
"""

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class EmailLoginRequest(BaseModel):
    """
    Request model for parent login using email and password.
    
    This model validates login credentials when a parent attempts to
    authenticate using their email address and password.
    
    Attributes:
        email: Parent's registered email address
        password: Account password (minimum 8 characters)
    
    Example:
        >>> request = EmailLoginRequest(
        ...     email="parent@example.com",
        ...     password="SecurePass123"
        ... )
    """
    
    email: EmailStr = Field(
        ...,
        description="Parent's registered email address"
    )
    
    password: str = Field(
        ...,
        min_length=8,
        description="Account password (minimum 8 characters)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "parent@example.com",
                "password": "SecurePass123"
            }
        }
    )


class PhoneLoginRequest(BaseModel):
    """
    Request model for parent login using phone number and OTP.
    
    This model validates login credentials when a parent attempts to
    authenticate using their phone number and a one-time password (OTP)
    received via SMS.
    
    Attributes:
        phone: Parent's registered phone number in +91XXXXXXXXXX format
        otp: 6-digit one-time password sent via SMS
    
    Example:
        >>> request = PhoneLoginRequest(
        ...     phone="+919876543210",
        ...     otp="123456"
        ... )
    """
    
    phone: str = Field(
        ...,
        description="Parent's registered phone number in format +91XXXXXXXXXX"
    )
    
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-digit one-time password sent via SMS"
    )
    
    @field_validator("phone")
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        """
        Validate phone number format for Indian mobile numbers.
        
        Ensures phone number follows the format +91XXXXXXXXXX where X is a digit.
        The number must have exactly 10 digits after the +91 country code.
        
        Args:
            v: Phone number string to validate
        
        Returns:
            str: Validated phone number
        
        Raises:
            ValueError: If phone number format is invalid
        """
        # Check if phone matches +91 followed by exactly 10 digits
        pattern = r"^\+91[6-9]\d{9}$"
        
        if not re.match(pattern, v):
            raise ValueError(
                "Phone number must be in format +91XXXXXXXXXX where X is a digit. "
                "Indian mobile numbers start with 6, 7, 8, or 9 and have 10 digits total."
            )
        
        return v
    
    @field_validator("otp")
    @classmethod
    def validate_otp_format(cls, v: str) -> str:
        """
        Validate OTP format.
        
        Ensures OTP is exactly 6 numeric digits.
        
        Args:
            v: OTP string to validate
        
        Returns:
            str: Validated OTP
        
        Raises:
            ValueError: If OTP format is invalid
        """
        # Remove any whitespace
        v = v.strip()
        
        # Check if OTP is exactly 6 digits
        if not re.match(r"^\d{6}$", v):
            raise ValueError(
                "OTP must be exactly 6 numeric digits"
            )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "+919876543210",
                "otp": "123456"
            }
        }
    )


class GoogleLoginRequest(BaseModel):
    """
    Request model for parent login using Google OAuth.
    
    This model validates login credentials when a parent attempts to
    authenticate using Google Sign-In. The id_token is provided by
    Google OAuth and will be verified on the backend.
    
    Attributes:
        id_token: Google OAuth ID token for verification
    
    Example:
        >>> request = GoogleLoginRequest(
        ...     id_token="eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY..."
        ... )
    """
    
    id_token: str = Field(
        ...,
        description="Google OAuth ID token obtained from Google Sign-In"
    )
    
    @field_validator("id_token")
    @classmethod
    def validate_id_token(cls, v: str) -> str:
        """
        Validate Google ID token format.
        
        Ensures the ID token is not empty and has a reasonable length.
        Full token verification happens in the service layer using Firebase.
        
        Args:
            v: Google ID token string to validate
        
        Returns:
            str: Validated ID token
        
        Raises:
            ValueError: If ID token format is invalid
        """
        if not v or len(v.strip()) == 0:
            raise ValueError("Google ID token cannot be empty")
        
        if len(v) < 50:
            raise ValueError("Invalid Google ID token format")
        
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhYzRlMWY2MmI4YWQxN2FkZGU0MzVmNDZhNGUyOTIzODJlNzMwN2YiLCJ0eXAiOiJKV1QifQ..."
            }
        }
    )


class TokenRefreshRequest(BaseModel):
    """
    Request model for refreshing JWT access token.
    
    This model validates the request to refresh an expired access token
    using a valid refresh token. This allows users to maintain their
    session without re-authenticating.
    
    Attributes:
        refresh_token: Valid JWT refresh token
    
    Example:
        >>> request = TokenRefreshRequest(
        ...     refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        ... )
    """
    
    refresh_token: str = Field(
        ...,
        description="Valid JWT refresh token to obtain a new access token"
    )
    
    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        """
        Validate refresh token format.
        
        Ensures the refresh token is not empty. Full token verification
        happens in the service layer.
        
        Args:
            v: Refresh token string to validate
        
        Returns:
            str: Validated refresh token
        
        Raises:
            ValueError: If refresh token is empty
        """
        if not v or len(v.strip()) == 0:
            raise ValueError("Refresh token cannot be empty")
        
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJlbnRfMTIzYWJjIiwiZXhwIjoxNjM..."
            }
        }
    )


class LoginResponse(BaseModel):
    """
    Comprehensive response model for successful login.
    
    This model represents the response returned after successful parent
    login via any authentication method (email, phone, or Google OAuth).
    It includes JWT tokens for session management and parent information.
    
    Attributes:
        token: JWT access token for API authentication
        refresh_token: JWT refresh token for obtaining new access tokens
        parent_id: Unique identifier for the parent account
        email: Parent's email address (if registered via email or Google)
        phone: Parent's phone number (if registered via phone)
        expires_in: Token expiration time in seconds
    
    Example:
        >>> response = LoginResponse(
        ...     token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     parent_id="parent_123abc456def",
        ...     email="parent@example.com",
        ...     phone=None,
        ...     expires_in=3600
        ... )
    """
    
    token: str = Field(
        ...,
        description="JWT access token for authenticating API requests"
    )
    
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens when expired"
    )
    
    parent_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the parent account"
    )
    
    email: Optional[str] = Field(
        default=None,
        description="Parent's email address (if registered via email or Google)"
    )
    
    phone: Optional[str] = Field(
        default=None,
        description="Parent's phone number (if registered via phone)"
    )
    
    expires_in: int = Field(
        default=86400,
        description="Token expiration time in seconds (typically 86400 for 24 hours)"
    )
    
    # Student-specific fields
    student_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the student account (for student logins)"
    )
    
    child_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the child profile (for student logins)"
    )
    
    username: Optional[str] = Field(
        default=None,
        description="Student username (for student logins)"
    )
    
    name: Optional[str] = Field(
        default=None,
        description="Student or parent name"
    )
    
    is_student: Optional[bool] = Field(
        default=False,
        description="Flag indicating if this is a student login"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Additional message or status information"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJlbnRfMTIzYWJjIiwiZXhwIjoxNjM...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJlbnRfMTIzYWJjIiwiZXhwIjoxNjM...",
                "parent_id": "parent_123abc456def",
                "email": "parent@example.com",
                "phone": None,
                "expires_in": 3600
            }
        }
    )


class TokenResponse(BaseModel):
    """
    Response model for token refresh endpoint.
    
    This model represents the response returned after successfully
    refreshing an access token using a valid refresh token.
    
    Attributes:
        token: New JWT access token
        refresh_token: New JWT refresh token (may be rotated)
        expires_in: Token expiration time in seconds
    
    Example:
        >>> response = TokenResponse(
        ...     token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     refresh_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        ...     expires_in=3600
        ... )
    """
    
    token: str = Field(
        ...,
        description="New JWT access token for authenticating API requests"
    )
    
    refresh_token: str = Field(
        ...,
        description="New JWT refresh token (may be same or rotated)"
    )
    
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds (typically 3600 for 1 hour)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJlbnRfMTIzYWJjIiwiZXhwIjoxNjM...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJlbnRfMTIzYWJjIiwiZXhwIjoxNjM...",
                "expires_in": 3600
            }
        }
    )


class LogoutResponse(BaseModel):
    """
    Response model for logout endpoint.
    
    This model represents the response returned after successfully
    logging out a parent. It provides confirmation that the session
    has been terminated.
    
    Attributes:
        message: Human-readable confirmation message
    
    Example:
        >>> response = LogoutResponse(
        ...     message="Logged out successfully"
        ... )
    """
    
    message: str = Field(
        ...,
        description="Human-readable confirmation message"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Logged out successfully"
            }
        }
    )


class ChildLoginRequest(BaseModel):
    """
    Request model for child/student login using username and password.
    
    This model validates login credentials when a child attempts to
    authenticate using their username and password provided by their parent.
    
    Attributes:
        username: Child's login username (3-30 characters)
        password: Child's login password (8-50 characters)
    
    Example:
        >>> request = ChildLoginRequest(
        ...     username="rahul123",
        ...     password="SecurePass123"
        ... )
    """
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Child's login username (3-30 characters)"
    )
    
    password: str = Field(
        ...,
        min_length=8,
        max_length=50,
        description="Child's login password (8-50 characters)"
    )
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Validate child's username.
        
        Ensures username is alphanumeric and contains no special characters.
        
        Args:
            v: Username to validate
        
        Returns:
            str: Validated username
        
        Raises:
            ValueError: If username contains invalid characters
        """
        # Strip leading/trailing whitespace
        v = v.strip()
        
        # Check if username is empty after stripping
        if not v:
            raise ValueError("Username cannot be empty or only whitespace")
        
        # Check minimum length after stripping
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters long")
        
        # Check for valid characters (alphanumeric, underscores, @, and .)
        import re
        if not re.match(r'^[a-zA-Z0-9_@.]+$', v):
            raise ValueError("Username can contain letters, numbers, underscores, @, and .")
        
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate child's password.
        
        Ensures password meets minimum security requirements.
        
        Args:
            v: Password to validate
        
        Returns:
            str: Validated password
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        # Check minimum length
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one letter and one number
        import re
        if not re.search(r'[a-zA-Z]', v):
            raise ValueError("Password must contain at least one letter")
        
        if not re.search(r'[0-9]', v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "rahul123",
                "password": "SecurePass123"
            }
        }
    )
