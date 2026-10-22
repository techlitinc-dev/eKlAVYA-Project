"""
Parent Preferences Data Models

This module defines Pydantic models for parent preferences management
in the Mentor AI EdTech Platform. These models handle notification settings,
language preferences, and teaching involvement levels.

Models:
- PreferencesRequest: Request model for creating/updating preferences
- PreferencesResponse: Response model with timestamp information
- PreferencesUpdate: Partial update model with optional fields

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class PreferencesRequest(BaseModel):
    """
    Request model for parent preferences.
    
    This model validates parent preference settings including language,
    notification preferences, and teaching involvement level.
    
    Attributes:
        language: Preferred language for communication (en/hi/mr)
        email_notifications: Enable email notifications
        sms_notifications: Enable SMS notifications
        push_notifications: Enable push notifications
        teaching_involvement: Level of parental teaching involvement
    
    Example:
        >>> request = PreferencesRequest(
        ...     language="en",
        ...     email_notifications=True,
        ...     sms_notifications=False,
        ...     push_notifications=True,
        ...     teaching_involvement="medium"
        ... )
    """
    
    language: Literal["en", "hi", "mr"] = Field(
        ...,
        description="Preferred language: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)"
    )
    
    email_notifications: bool = Field(
        default=True,
        description="Enable email notifications for updates and alerts"
    )
    
    sms_notifications: bool = Field(
        default=True,
        description="Enable SMS notifications for important updates"
    )
    
    push_notifications: bool = Field(
        default=True,
        description="Enable push notifications in the mobile app"
    )
    
    teaching_involvement: Literal["high", "medium", "low"] = Field(
        ...,
        description="Level of parental teaching involvement: 'high', 'medium', or 'low'"
    )
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """
        Validate language field.
        
        Ensures language is one of the supported options.
        
        Args:
            v: Language value to validate
        
        Returns:
            str: Validated language value
        
        Raises:
            ValueError: If language is not supported
        """
        valid_languages = ["en", "hi", "mr"]
        if v not in valid_languages:
            raise ValueError(
                f"Invalid language: '{v}'. Must be one of: {', '.join(valid_languages)}"
            )
        return v
    
    @field_validator("teaching_involvement")
    @classmethod
    def validate_teaching_involvement(cls, v: str) -> str:
        """
        Validate teaching involvement field.
        
        Ensures teaching involvement is one of the supported levels.
        
        Args:
            v: Teaching involvement level to validate
        
        Returns:
            str: Validated teaching involvement level
        
        Raises:
            ValueError: If level is not supported
        """
        valid_levels = ["high", "medium", "low"]
        if v not in valid_levels:
            raise ValueError(
                f"Invalid teaching involvement level: '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "language": "en",
                "email_notifications": True,
                "sms_notifications": True,
                "push_notifications": True,
                "teaching_involvement": "medium"
            }
        }
    )


class PreferencesResponse(BaseModel):
    """
    Response model for parent preferences.
    
    This model represents the complete preference data including
    all settings and metadata such as timestamps.
    
    Attributes:
        parent_id: Unique identifier for the parent account
        language: Preferred language for communication
        email_notifications: Email notification setting
        sms_notifications: SMS notification setting
        push_notifications: Push notification setting
        teaching_involvement: Level of parental teaching involvement
        created_at: Timestamp when preferences were created
        updated_at: Timestamp when preferences were last updated
    
    Example:
        >>> response = PreferencesResponse(
        ...     parent_id="parent_123abc",
        ...     language="en",
        ...     email_notifications=True,
        ...     sms_notifications=False,
        ...     push_notifications=True,
        ...     teaching_involvement="high",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """
    
    parent_id: str = Field(
        ...,
        description="Unique identifier for the parent account"
    )
    
    language: Literal["en", "hi", "mr"] = Field(
        ...,
        description="Preferred language: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)"
    )
    
    email_notifications: bool = Field(
        ...,
        description="Email notification setting"
    )
    
    sms_notifications: bool = Field(
        ...,
        description="SMS notification setting"
    )
    
    push_notifications: bool = Field(
        ...,
        description="Push notification setting"
    )
    
    teaching_involvement: Literal["high", "medium", "low"] = Field(
        ...,
        description="Level of parental teaching involvement"
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when preferences were created"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Timestamp when preferences were last updated"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "parent_id": "parent_123abc456def",
                "language": "en",
                "email_notifications": True,
                "sms_notifications": True,
                "push_notifications": True,
                "teaching_involvement": "medium",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z"
            }
        }
    )


class PreferencesUpdate(BaseModel):
    """
    Partial update model for parent preferences.
    
    This model allows partial updates to preferences where all fields
    are optional. Only provided fields will be updated.
    
    Attributes:
        language: Preferred language (optional)
        email_notifications: Email notification setting (optional)
        sms_notifications: SMS notification setting (optional)
        push_notifications: Push notification setting (optional)
        teaching_involvement: Teaching involvement level (optional)
    
    Example:
        >>> update = PreferencesUpdate(
        ...     email_notifications=False,
        ...     teaching_involvement="high"
        ... )
        # Only updates email_notifications and teaching_involvement
    """
    
    language: Optional[Literal["en", "hi", "mr"]] = Field(
        default=None,
        description="Preferred language: 'en' (English), 'hi' (Hindi), 'mr' (Marathi)"
    )
    
    email_notifications: Optional[bool] = Field(
        default=None,
        description="Enable email notifications for updates and alerts"
    )
    
    sms_notifications: Optional[bool] = Field(
        default=None,
        description="Enable SMS notifications for important updates"
    )
    
    push_notifications: Optional[bool] = Field(
        default=None,
        description="Enable push notifications in the mobile app"
    )
    
    teaching_involvement: Optional[Literal["high", "medium", "low"]] = Field(
        default=None,
        description="Level of parental teaching involvement: 'high', 'medium', or 'low'"
    )
    
    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate language field if provided.
        
        Args:
            v: Language value to validate
        
        Returns:
            Optional[str]: Validated language value or None
        
        Raises:
            ValueError: If language is provided but not supported
        """
        if v is None:
            return v
        
        valid_languages = ["en", "hi", "mr"]
        if v not in valid_languages:
            raise ValueError(
                f"Invalid language: '{v}'. Must be one of: {', '.join(valid_languages)}"
            )
        return v
    
    @field_validator("teaching_involvement")
    @classmethod
    def validate_teaching_involvement(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate teaching involvement field if provided.
        
        Args:
            v: Teaching involvement level to validate
        
        Returns:
            Optional[str]: Validated teaching involvement level or None
        
        Raises:
            ValueError: If level is provided but not supported
        """
        if v is None:
            return v
        
        valid_levels = ["high", "medium", "low"]
        if v not in valid_levels:
            raise ValueError(
                f"Invalid teaching involvement level: '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "language": "hi",
                "sms_notifications": False,
                "teaching_involvement": "high"
            }
        }
    )
