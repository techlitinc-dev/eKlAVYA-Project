"""
Verification Data Models

This module defines Pydantic models for verification-related API requests
and responses in the Mentor AI EdTech Platform. These models provide data
validation, serialization, and documentation for email and phone verification endpoints.

Models:
- SendEmailVerificationRequest: Request to send email verification code
- ConfirmEmailVerificationRequest: Request to confirm email with verification code
- SendPhoneOTPRequest: Request to send phone OTP
- ConfirmPhoneOTPRequest: Request to confirm phone with OTP
- VerificationResponse: Unified verification response

Author: Mentor AI Team
Version: 1.0.0
"""

import re
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class SendEmailVerificationRequest(BaseModel):
    """
    Request model for sending email verification code.
    
    This model validates the request to send a verification code to the
    parent's email address. The verification code will be sent via email
    and must be confirmed to verify the email address.
    
    Attributes:
        email: Parent's email address to send verification code
    
    Example:
        >>> request = SendEmailVerificationRequest(
        ...     email="parent@example.com"
        ... )
    """
    
    email: EmailStr = Field(
        ...,
        description="Parent's email address to send verification code"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "parent@example.com"
            }
        }
    )


class ConfirmEmailVerificationRequest(BaseModel):
    """
    Request model for confirming email verification with code.
    
    This model validates the request to confirm an email address using
    a 6-character verification code that was sent to the email.
    
    Attributes:
        email: Parent's email address being verified
        code: 6-character verification code sent to email
    
    Example:
        >>> request = ConfirmEmailVerificationRequest(
        ...     email="parent@example.com",
        ...     code="ABC123"
        ... )
    """
    
    email: EmailStr = Field(
        ...,
        description="Parent's email address being verified"
    )
    
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        description="6-character verification code sent to email"
    )
    
    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """
        Validate verification code format.
        
        Ensures code is exactly 6 alphanumeric characters (uppercase).
        
        Args:
            v: Verification code string to validate
        
        Returns:
            str: Validated and uppercase verification code
        
        Raises:
            ValueError: If code format is invalid
        """
        # Convert to uppercase for consistency
        v = v.upper().strip()
        
        # Check if code is exactly 6 alphanumeric characters
        if not re.match(r"^[A-Z0-9]{6}$", v):
            raise ValueError(
                "Verification code must be exactly 6 alphanumeric characters"
            )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "parent@example.com",
                "code": "ABC123"
            }
        }
    )


class SendPhoneOTPRequest(BaseModel):
    """
    Request model for sending phone OTP.
    
    This model validates the request to send a one-time password (OTP)
    to the parent's phone number via SMS.
    
    Attributes:
        phone: Parent's phone number in +91XXXXXXXXXX format
    
    Example:
        >>> request = SendPhoneOTPRequest(
        ...     phone="+919876543210"
        ... )
    """
    
    phone: str = Field(
        ...,
        description="Parent's phone number in format +91XXXXXXXXXX (Indian mobile number)"
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
                "phone": "+919876543210"
            }
        }
    )


class ConfirmPhoneOTPRequest(BaseModel):
    """
    Request model for confirming phone number with OTP.
    
    This model validates the request to confirm a phone number using
    a 6-digit OTP that was sent via SMS.
    
    Attributes:
        phone: Parent's phone number being verified
        otp: 6-digit one-time password sent via SMS
    
    Example:
        >>> request = ConfirmPhoneOTPRequest(
        ...     phone="+919876543210",
        ...     otp="123456"
        ... )
    """
    
    phone: str = Field(
        ...,
        description="Parent's phone number in format +91XXXXXXXXXX (Indian mobile number)"
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


class VerificationResponse(BaseModel):
    """
    Unified response model for verification endpoints.
    
    This model represents the response returned after verification
    operations (email or phone). It indicates whether the verification
    was successful and provides a human-readable message.
    
    Attributes:
        verified: Whether the verification was successful
        message: Human-readable status message
    
    Example:
        >>> response = VerificationResponse(
        ...     verified=True,
        ...     message="Email verified successfully"
        ... )
    """
    
    verified: bool = Field(
        ...,
        description="Indicates whether the verification was successful"
    )
    
    message: str = Field(
        ...,
        description="Human-readable message about the verification status"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "verified": True,
                "message": "Email verified successfully"
            }
        }
    )
