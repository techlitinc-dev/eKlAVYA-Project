"""
Child Profile Data Models

This module defines Pydantic models for child profile management
in the Mentor AI EdTech Platform. These models handle student information
including academic level, age, and learning progress.

Models:
- ChildProfileRequest: Request model for creating child profiles
- ChildProfileResponse: Response model with metadata
- ChildProfileUpdate: Partial update model with optional fields

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ChildProfileRequest(BaseModel):
    """
    Request model for creating a child profile.
    
    This model validates child information including name, age, grade,
    current learning level, and login credentials for JEE/NEET preparation.
    
    Attributes:
        name: Child's full name (2-100 characters)
        age: Child's age (14-19 years)
        grade: Current grade/class (9-12)
        current_level: Current learning level (beginner/intermediate/advanced)
        username: Child's login username (3-30 characters)
        password: Child's login password (8-50 characters)
    
    Example:
        >>> request = ChildProfileRequest(
        ...     name="Rahul Sharma",
        ...     age=16,
        ...     grade=11,
        ...     current_level="intermediate",
        ...     username="rahul123",
        ...     password="SecurePass123"
        ... )
    """
    
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Child's full name (2-100 characters)"
    )
    
    age: int = Field(
        ...,
        ge=14,
        le=19,
        description="Child's age (must be between 14 and 19 years)"
    )
    
    grade: int = Field(
        ...,
        ge=9,
        le=12,
        description="Current grade/class (must be between 9 and 12)"
    )
    
    current_level: Literal["beginner", "intermediate", "advanced"] = Field(
        ...,
        description="Current learning level: 'beginner', 'intermediate', or 'advanced'"
    )
    
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
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate and sanitize child's name.
        
        Strips whitespace and ensures name is not empty after stripping.
        
        Args:
            v: Name string to validate
        
        Returns:
            str: Validated and stripped name
        
        Raises:
            ValueError: If name is empty after stripping whitespace
        """
        # Strip leading/trailing whitespace
        v = v.strip()
        
        # Check if name is empty after stripping
        if not v:
            raise ValueError("Name cannot be empty or only whitespace")
        
        # Check minimum length after stripping
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long")
        
        return v
    
    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        """
        Validate child's age range.
        
        Ensures age is appropriate for JEE/NEET preparation (14-19 years).
        
        Args:
            v: Age value to validate
        
        Returns:
            int: Validated age
        
        Raises:
            ValueError: If age is outside the valid range
        """
        if v < 14 or v > 19:
            raise ValueError(
                f"Age must be between 14 and 19 years. Got: {v}"
            )
        return v
    
    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: int) -> int:
        """
        Validate child's grade/class.
        
        Ensures grade is within valid range for JEE/NEET students (9-12).
        
        Args:
            v: Grade value to validate
        
        Returns:
            int: Validated grade
        
        Raises:
            ValueError: If grade is outside the valid range
        """
        if v < 9 or v > 12:
            raise ValueError(
                f"Grade must be between 9 and 12. Got: {v}"
            )
        return v
    
    @field_validator("current_level")
    @classmethod
    def validate_current_level(cls, v: str) -> str:
        """
        Validate current learning level.
        
        Ensures learning level is one of the supported options.
        
        Args:
            v: Learning level to validate
        
        Returns:
            str: Validated learning level
        
        Raises:
            ValueError: If learning level is not supported
        """
        valid_levels = ["beginner", "intermediate", "advanced"]
        if v not in valid_levels:
            raise ValueError(
                f"Invalid learning level: '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v
    
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
                "name": "Rahul Sharma",
                "age": 16,
                "grade": 11,
                "current_level": "intermediate",
                "username": "rahul123",
                "password": "SecurePass123"
            }
        }
    )


class ChildProfileResponse(BaseModel):
    """
    Response model for child profile data.
    
    This model represents the complete child profile including all
    information and metadata such as IDs and timestamps.
    
    Attributes:
        child_id: Unique identifier for the child profile
        parent_id: ID of the parent who owns this profile
        name: Child's full name
        age: Child's age (14-19 years)
        grade: Current grade/class (9-12)
        current_level: Current learning level
        username: Child's login username
        created_at: Timestamp when profile was created
        updated_at: Timestamp when profile was last updated
    
    Example:
        >>> response = ChildProfileResponse(
        ...     child_id="child_abc123",
        ...     parent_id="parent_xyz789",
        ...     name="Priya Patel",
        ...     age=17,
        ...     grade=12,
        ...     current_level="advanced",
        ...     username="priya123",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
    """
    
    child_id: str = Field(
        ...,
        description="Unique identifier for the child profile"
    )
    
    parent_id: str = Field(
        ...,
        description="Unique identifier of the parent who owns this profile"
    )
    
    name: str = Field(
        ...,
        description="Child's full name"
    )
    
    age: int = Field(
        ...,
        description="Child's age (14-19 years)"
    )
    
    grade: int = Field(
        ...,
        description="Current grade/class (9-12)"
    )
    
    current_level: Literal["beginner", "intermediate", "advanced"] = Field(
        ...,
        description="Current learning level"
    )
    
    username: str = Field(
        ...,
        description="Child's login username"
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when profile was created"
    )
    
    updated_at: datetime = Field(
        ...,
        description="Timestamp when profile was last updated"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "child_id": "child_abc123def456",
                "parent_id": "parent_xyz789ghi012",
                "name": "Priya Patel",
                "age": 17,
                "grade": 12,
                "current_level": "advanced",
                "username": "priya123",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-20T14:45:00Z"
            }
        }
    )


class ChildProfileUpdate(BaseModel):
    """
    Partial update model for child profiles.
    
    This model allows partial updates to child profiles where all fields
    are optional. Only provided fields will be updated.
    
    Attributes:
        name: Child's full name (optional)
        age: Child's age (optional)
        grade: Current grade/class (optional)
        current_level: Current learning level (optional)
        username: Child's login username (optional)
        password: Child's login password (optional)
    
    Example:
        >>> update = ChildProfileUpdate(
        ...     age=17,
        ...     grade=12,
        ...     current_level="advanced",
        ...     username="new_username123"
        ... )
        # Only updates provided fields
    """
    
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="Child's full name (2-100 characters)"
    )
    
    age: Optional[int] = Field(
        default=None,
        ge=14,
        le=19,
        description="Child's age (must be between 14 and 19 years)"
    )
    
    grade: Optional[int] = Field(
        default=None,
        ge=9,
        le=12,
        description="Current grade/class (must be between 9 and 12)"
    )
    
    current_level: Optional[Literal["beginner", "intermediate", "advanced"]] = Field(
        default=None,
        description="Current learning level: 'beginner', 'intermediate', or 'advanced'"
    )
    
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=30,
        description="Child's login username (3-30 characters)"
    )
    
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=50,
        description="Child's login password (8-50 characters)"
    )
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and sanitize child's name if provided.
        
        Args:
            v: Name string to validate
        
        Returns:
            Optional[str]: Validated and stripped name or None
        
        Raises:
            ValueError: If name is provided but empty after stripping
        """
        if v is None:
            return v
        
        # Strip leading/trailing whitespace
        v = v.strip()
        
        # Check if name is empty after stripping
        if not v:
            raise ValueError("Name cannot be empty or only whitespace")
        
        # Check minimum length after stripping
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters long")
        
        return v
    
    @field_validator("age")
    @classmethod
    def validate_age(cls, v: Optional[int]) -> Optional[int]:
        """
        Validate child's age range if provided.
        
        Args:
            v: Age value to validate
        
        Returns:
            Optional[int]: Validated age or None
        
        Raises:
            ValueError: If age is provided but outside valid range
        """
        if v is None:
            return v
        
        if v < 14 or v > 19:
            raise ValueError(
                f"Age must be between 14 and 19 years. Got: {v}"
            )
        return v
    
    @field_validator("grade")
    @classmethod
    def validate_grade(cls, v: Optional[int]) -> Optional[int]:
        """
        Validate child's grade/class if provided.
        
        Args:
            v: Grade value to validate
        
        Returns:
            Optional[int]: Validated grade or None
        
        Raises:
            ValueError: If grade is provided but outside valid range
        """
        if v is None:
            return v
        
        if v < 9 or v > 12:
            raise ValueError(
                f"Grade must be between 9 and 12. Got: {v}"
            )
        return v
    
    @field_validator("current_level")
    @classmethod
    def validate_current_level(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate current learning level if provided.
        
        Args:
            v: Learning level to validate
        
        Returns:
            Optional[str]: Validated learning level or None
        
        Raises:
            ValueError: If level is provided but not supported
        """
        if v is None:
            return v
        
        valid_levels = ["beginner", "intermediate", "advanced"]
        if v not in valid_levels:
            raise ValueError(
                f"Invalid learning level: '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate child's username if provided.
        
        Args:
            v: Username to validate
        
        Returns:
            Optional[str]: Validated username or None
        
        Raises:
            ValueError: If username is provided but contains invalid characters
        """
        if v is None:
            return v
        
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
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate child's password if provided.
        
        Args:
            v: Password to validate
        
        Returns:
            Optional[str]: Validated password or None
        
        Raises:
            ValueError: If password is provided but doesn't meet requirements
        """
        if v is None:
            return v
        
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
                "age": 17,
                "grade": 12,
                "current_level": "advanced",
                "username": "new_username123"
            }
        }
    )
