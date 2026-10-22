"""
Exam and Diagnostic Test Data Models

This module defines Pydantic models for exam selection and diagnostic test
scheduling in the Mentor AI EdTech Platform. These models handle JEE and NEET
exam management including subject preferences and test scheduling.

Models:
- ExamSelectionRequest: Request model for selecting exam and preferences
- ExamSelectionResponse: Response with exam details and diagnostic test info
- AvailableExam: Model for available exam information
- AvailableExamsResponse: List of available exams
- DiagnosticTestSchedule: Model for diagnostic test scheduling

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime, timezone
from typing import List, Dict, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ExamSelectionRequest(BaseModel):
    """
    Request model for exam selection and subject preferences.
    
    This model validates exam type, target exam date, and subject
    weightage preferences for personalized study plans.
    
    Attributes:
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, or NEET)
        exam_date: Target exam date
        subject_preferences: Subject weightages (must sum to 100)
    
    Example:
        >>> request = ExamSelectionRequest(
        ...     exam_type="JEE_MAIN",
        ...     exam_date=datetime(2026, 1, 15),
        ...     subject_preferences={
        ...         "Physics": 35,
        ...         "Chemistry": 30,
        ...         "Mathematics": 35
        ...     }
        ... )
    """
    
    exam_type: Literal["JEE_MAIN", "JEE_ADVANCED", "JEE_COMBO", "NEET"] = Field(
        ...,
        description="Type of entrance exam: JEE_MAIN, JEE_ADVANCED, JEE_COMBO, or NEET"
    )
    
    exam_date: datetime = Field(
        ...,
        description="Target exam date (must be in the future)"
    )
    
    subject_preferences: Dict[str, int] = Field(
        ...,
        description="Subject weightages in percentage (must sum to 100). "
                   "JEE: Physics, Chemistry, Mathematics. "
                   "NEET: Physics, Chemistry, Biology"
    )
    
    @field_validator("exam_type")
    @classmethod
    def validate_exam_type(cls, v: str) -> str:
        """
        Validate exam type.
        
        Args:
            v: Exam type to validate
        
        Returns:
            str: Validated exam type
        
        Raises:
            ValueError: If exam type is not supported
        """
        valid_types = ["JEE_MAIN", "JEE_ADVANCED", "JEE_COMBO", "NEET"]
        if v not in valid_types:
            raise ValueError(
                f"Invalid exam type: '{v}'. Must be one of: {', '.join(valid_types)}"
            )
        return v
    
    @field_validator("exam_date")
    @classmethod
    def validate_exam_date(cls, v: datetime) -> datetime:
        """
        Validate exam date is in the future.
        
        Args:
            v: Exam date to validate
        
        Returns:
            datetime: Validated exam date
        
        Raises:
            ValueError: If exam date is in the past
        """
        # Ensure timezone awareness
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        
        if v <= now:
            raise ValueError(
                f"Exam date must be in the future. Got: {v.strftime('%Y-%m-%d')}"
            )
        
        return v
    
    @field_validator("subject_preferences")
    @classmethod
    def validate_subject_preferences(cls, v: Dict[str, int], info) -> Dict[str, int]:
        """
        Validate subject preferences and weightages.
        
        Ensures:
        1. Weightages sum to 100
        2. Subjects match exam type
        3. All weightages are non-negative
        
        Args:
            v: Subject preferences dictionary
            info: Validation context with other field values
        
        Returns:
            Dict[str, int]: Validated subject preferences
        
        Raises:
            ValueError: If weightages don't sum to 100 or subjects are invalid
        """
        # Check that all weightages are non-negative
        for subject, weight in v.items():
            if weight < 0:
                raise ValueError(
                    f"Subject weightage cannot be negative. {subject}: {weight}"
                )
        
        # Check that weightages sum to 100
        total_weight = sum(v.values())
        if total_weight != 100:
            raise ValueError(
                f"Subject weightages must sum to 100. Current total: {total_weight}"
            )
        
        # Validate subjects based on exam type (if available in context)
        exam_type = info.data.get("exam_type")
        if exam_type:
            if exam_type in ["JEE_MAIN", "JEE_ADVANCED", "JEE_COMBO"]:
                expected_subjects = {"Physics", "Chemistry", "Mathematics"}
            elif exam_type == "NEET":
                expected_subjects = {"Physics", "Chemistry", "Biology"}
            else:
                expected_subjects = set()
            
            actual_subjects = set(v.keys())
            
            if expected_subjects and actual_subjects != expected_subjects:
                raise ValueError(
                    f"Invalid subjects for {exam_type}. "
                    f"Expected: {', '.join(sorted(expected_subjects))}. "
                    f"Got: {', '.join(sorted(actual_subjects))}"
                )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exam_type": "JEE_MAIN",
                "exam_date": "2026-01-15T00:00:00Z",
                "subject_preferences": {
                    "Physics": 35,
                    "Chemistry": 30,
                    "Mathematics": 35
                }
            }
        }
    )


class ExamSelectionResponse(BaseModel):
    """
    Response model for exam selection.
    
    This model includes all exam selection details plus calculated
    information such as days until exam and diagnostic test ID.
    
    Attributes:
        child_id: Unique identifier for the child
        exam_type: Type of exam selected
        exam_date: Target exam date
        subject_preferences: Subject weightages
        days_until_exam: Number of days until exam
        diagnostic_test_id: ID of the scheduled diagnostic test
        created_at: Timestamp when selection was made
    
    Example:
        >>> response = ExamSelectionResponse(
        ...     child_id="child_abc123",
        ...     exam_type="JEE_MAIN",
        ...     exam_date=datetime(2026, 1, 15),
        ...     subject_preferences={"Physics": 35, "Chemistry": 30, "Mathematics": 35},
        ...     days_until_exam=450,
        ...     diagnostic_test_id="test_xyz789",
        ...     created_at=datetime.now()
        ... )
    """
    
    child_id: str = Field(
        ...,
        description="Unique identifier for the child profile"
    )
    
    exam_type: str = Field(
        ...,
        description="Type of entrance exam selected"
    )
    
    exam_date: datetime = Field(
        ...,
        description="Target exam date"
    )
    
    subject_preferences: Dict[str, int] = Field(
        ...,
        description="Subject weightages in percentage"
    )
    
    days_until_exam: int = Field(
        ...,
        description="Number of days from now until the exam"
    )
    
    diagnostic_test_id: str = Field(
        ...,
        description="Unique identifier for the scheduled diagnostic test"
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when exam selection was created"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "child_id": "child_abc123def456",
                "exam_type": "JEE_MAIN",
                "exam_date": "2026-01-15T00:00:00Z",
                "subject_preferences": {
                    "Physics": 35,
                    "Chemistry": 30,
                    "Mathematics": 35
                },
                "days_until_exam": 450,
                "diagnostic_test_id": "test_xyz789ghi012",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class AvailableExam(BaseModel):
    """
    Model for available exam information.
    
    This model represents information about an available entrance exam
    including exam type, name, dates, and subjects.
    
    Attributes:
        exam_type: Type identifier for the exam
        exam_name: Human-readable exam name
        available_dates: List of available exam dates (YYYY-MM-DD format)
        subjects: List of subjects covered in the exam
    
    Example:
        >>> exam = AvailableExam(
        ...     exam_type="JEE_MAIN",
        ...     exam_name="JEE Main 2026",
        ...     available_dates=["2026-01-15", "2026-04-15"],
        ...     subjects=["Physics", "Chemistry", "Mathematics"]
        ... )
    """
    
    exam_type: str = Field(
        ...,
        description="Type identifier for the exam"
    )
    
    exam_name: str = Field(
        ...,
        description="Human-readable name of the exam"
    )
    
    available_dates: List[str] = Field(
        ...,
        description="List of available exam dates in YYYY-MM-DD format"
    )
    
    subjects: List[str] = Field(
        ...,
        description="List of subjects covered in this exam"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exam_type": "JEE_MAIN",
                "exam_name": "JEE Main 2026",
                "available_dates": ["2026-01-15", "2026-04-15"],
                "subjects": ["Physics", "Chemistry", "Mathematics"]
            }
        }
    )


class AvailableExamsResponse(BaseModel):
    """
    Response model for available exams list.
    
    This model contains a list of all available entrance exams
    with their respective details.
    
    Attributes:
        exams: List of available exam objects
    
    Example:
        >>> response = AvailableExamsResponse(
        ...     exams=[
        ...         AvailableExam(
        ...             exam_type="JEE_MAIN",
        ...             exam_name="JEE Main 2026",
        ...             available_dates=["2026-01-15", "2026-04-15"],
        ...             subjects=["Physics", "Chemistry", "Mathematics"]
        ...         ),
        ...         AvailableExam(
        ...             exam_type="NEET",
        ...             exam_name="NEET 2026",
        ...             available_dates=["2026-05-05"],
        ...             subjects=["Physics", "Chemistry", "Biology"]
        ...         )
        ...     ]
        ... )
    """
    
    exams: List[AvailableExam] = Field(
        ...,
        description="List of available entrance exams"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exams": [
                    {
                        "exam_type": "JEE_MAIN",
                        "exam_name": "JEE Main 2026",
                        "available_dates": ["2026-01-15", "2026-04-15"],
                        "subjects": ["Physics", "Chemistry", "Mathematics"]
                    },
                    {
                        "exam_type": "JEE_ADVANCED",
                        "exam_name": "JEE Advanced 2026",
                        "available_dates": ["2026-05-25"],
                        "subjects": ["Physics", "Chemistry", "Mathematics"]
                    },
                    {
                        "exam_type": "NEET",
                        "exam_name": "NEET 2026",
                        "available_dates": ["2026-05-05"],
                        "subjects": ["Physics", "Chemistry", "Biology"]
                    }
                ]
            }
        }
    )


class DiagnosticTestSchedule(BaseModel):
    """
    Model for diagnostic test scheduling.
    
    This model represents a scheduled diagnostic test including
    test metadata, scheduling details, and status.
    
    Attributes:
        test_id: Unique identifier for the diagnostic test
        child_id: ID of the child taking the test
        exam_type: Type of exam this test prepares for
        scheduled_date: Date and time when test is scheduled
        duration_minutes: Test duration in minutes (default: 180)
        total_questions: Total number of questions (default: 200)
        status: Current status of the test
    
    Example:
        >>> schedule = DiagnosticTestSchedule(
        ...     test_id="test_abc123",
        ...     child_id="child_xyz789",
        ...     exam_type="JEE_MAIN",
        ...     scheduled_date=datetime(2024, 1, 20, 10, 0),
        ...     duration_minutes=180,
        ...     total_questions=200,
        ...     status="scheduled"
        ... )
    """
    
    test_id: str = Field(
        ...,
        description="Unique identifier for the diagnostic test"
    )
    
    child_id: str = Field(
        ...,
        description="Unique identifier of the child taking the test"
    )
    
    exam_type: str = Field(
        ...,
        description="Type of exam this diagnostic test prepares for"
    )
    
    scheduled_date: datetime = Field(
        ...,
        description="Date and time when the test is scheduled"
    )
    
    duration_minutes: int = Field(
        default=180,
        description="Duration of the test in minutes (default: 180)"
    )
    
    total_questions: int = Field(
        default=200,
        description="Total number of questions in the test (default: 200)"
    )
    
    status: Literal["scheduled", "in_progress", "completed"] = Field(
        ...,
        description="Current status of the test: scheduled, in_progress, or completed"
    )
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """
        Validate test status.
        
        Args:
            v: Status to validate
        
        Returns:
            str: Validated status
        
        Raises:
            ValueError: If status is not supported
        """
        valid_statuses = ["scheduled", "in_progress", "completed"]
        if v not in valid_statuses:
            raise ValueError(
                f"Invalid test status: '{v}'. Must be one of: {', '.join(valid_statuses)}"
            )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "test_id": "test_abc123def456",
                "child_id": "child_xyz789ghi012",
                "exam_type": "JEE_MAIN",
                "scheduled_date": "2024-01-20T10:00:00Z",
                "duration_minutes": 180,
                "total_questions": 200,
                "status": "scheduled"
            }
        }
    )
