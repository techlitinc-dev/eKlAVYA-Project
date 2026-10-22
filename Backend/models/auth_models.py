"""
Authentication Data Models

This module defines Pydantic models for authentication-related API requests
and responses in the Mentor AI EdTech Platform. These models provide data
validation, serialization, and documentation for authentication endpoints.

Models:
- ParentEmailRegisterRequest: Email-based parent registration
- ParentPhoneRegisterRequest: Phone-based parent registration
- ParentGoogleRegisterRequest: Google OAuth-based parent registration
- AuthResponse: Unified authentication response

Author: Mentor AI Team
Version: 1.0.0
"""

import re
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class ParentEmailRegisterRequest(BaseModel):
    """
    Request model for parent registration using email and password.
    
    This model validates parent registration data when using email
    as the primary authentication method. It ensures email format,
    password strength, and language preference are valid.
    
    Attributes:
        email: Parent's email address (must be valid email format)
        password: Account password (minimum 8 characters)
        language: Preferred language for communication (en/hi/mr)
    
    Example:
        >>> request = ParentEmailRegisterRequest(
        ...     email="parent@example.com",
        ...     password="SecurePass123",
        ...     language="en"
        ... )
    """
    
    email: EmailStr = Field(
        ...,
        description="Parent's email address for registration and login"
    )
    
    password: str = Field(
        ...,
        min_length=8,
        description="Account password (minimum 8 characters, should contain letters and numbers)"
    )
    
    language: Literal["en", "hi", "mr"] = Field(
        default="en",
        description="Preferred language: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)"
    )
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength requirements.
        
        Ensures password contains at least one letter and one number
        for better security.
        
        Args:
            v: Password string to validate
        
        Returns:
            str: Validated password
        
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "parent@example.com",
                "password": "SecurePass123",
                "language": "en"
            }
        }
    )


class ParentPhoneRegisterRequest(BaseModel):
    """
    Request model for parent registration using phone number.
    
    This model validates parent registration data when using phone
    number as the primary authentication method. Phone verification
    via OTP will be required after registration.
    
    Attributes:
        phone: Parent's phone number in +91XXXXXXXXXX format
        language: Preferred language for communication (en/hi/mr)
    
    Example:
        >>> request = ParentPhoneRegisterRequest(
        ...     phone="+919876543210",
        ...     language="hi"
        ... )
    """
    
    phone: str = Field(
        ...,
        description="Parent's phone number in format +91XXXXXXXXXX (Indian mobile number)"
    )
    
    language: Literal["en", "hi", "mr"] = Field(
        default="en",
        description="Preferred language: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)"
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
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "phone": "+919876543210",
                "language": "hi"
            }
        }
    )


class ParentGoogleRegisterRequest(BaseModel):
    """
    Request model for parent registration using Google OAuth.
    
    This model validates parent registration data when using Google
    Sign-In as the authentication method. The id_token is provided
    by Google OAuth and will be verified on the backend.
    
    Attributes:
        id_token: Google OAuth ID token for verification
        language: Preferred language for communication (en/hi/mr)
    
    Example:
        >>> request = ParentGoogleRegisterRequest(
        ...     id_token="eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...",
        ...     language="en"
        ... )
    """
    
    id_token: str = Field(
        ...,
        description="Google OAuth ID token obtained from Google Sign-In"
    )
    
    language: Literal["en", "hi", "mr"] = Field(
        default="en",
        description="Preferred language: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)"
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
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhYzRlMWY2MmI4YWQxN2FkZGU0MzVmNDZhNGUyOTIzODJlNzMwN2YiLCJ0eXAiOiJKV1QifQ...",
                "language": "en"
            }
        }
    )


class AuthResponse(BaseModel):
    """
    Unified response model for authentication endpoints.
    
    This model represents the response returned after successful
    parent registration or login. It includes parent identification,
    contact information, and verification status.
    
    Attributes:
        parent_id: Unique identifier for the parent account
        email: Parent's email address (if registered via email)
        phone: Parent's phone number (if registered via phone)
        verification_required: Whether email/phone verification is needed
        message: Human-readable status message
    
    Example:
        >>> response = AuthResponse(
        ...     parent_id="parent_123abc",
        ...     email="parent@example.com",
        ...     phone=None,
        ...     verification_required=True,
        ...     message="Registration successful. Please verify your email."
        ... )
    """
    
    parent_id: str = Field(
        ...,
        description="Unique identifier for the parent account in Firebase"
    )
    
    email: Optional[str] = Field(
        default=None,
        description="Parent's email address (if registered via email or Google)"
    )
    
    phone: Optional[str] = Field(
        default=None,
        description="Parent's phone number (if registered via phone)"
    )
    
    verification_required: bool = Field(
        default=False,
        description="Indicates if email/phone verification is required"
    )
    
    message: str = Field(
        ...,
        description="Human-readable message about the authentication status"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_id": "parent_123abc456def",
                "email": "parent@example.com",
                "phone": None,
                "verification_required": True,
                "message": "Registration successful. Please verify your email to continue."
            }
        }
    )
