"""
Pydantic Models for Diagnostic Test API - Mentor AI Platform.

This module defines all data models for diagnostic test operations including
test generation, submission, results, and async job tracking.

Example Usage:
    >>> from models.diagnostic_test_models import TestGenerationRequest
    >>> 
    >>> request = TestGenerationRequest(
    ...     exam_type="JEE_MAIN",
    ...     student_id="student_123"
    ... )
    >>> print(request.exam_type)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# ENUMS
# ============================================================================

class ExamType(str, Enum):
    """Supported exam types."""
    JEE_MAIN = "JEE_MAIN"
    JEE_ADVANCED = "JEE_ADVANCED"
    NEET = "NEET"


class TestStatus(str, Enum):
    """Test status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class GenerationStatus(str, Enum):
    """Test generation job status."""
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class QuestionType(str, Enum):
    """Question types."""
    SINGLE_CORRECT = "single_correct"
    MULTIPLE_CORRECT = "multiple_correct"
    NUMERICAL = "numerical"
    INTEGER = "integer"


class Difficulty(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ============================================================================
# REQUEST MODELS
# ============================================================================

class TestGenerationRequest(BaseModel):
    """
    Request model for generating a diagnostic test.
    
    Attributes:
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        student_id: Unique student identifier
        async_generation: Whether to generate asynchronously
        custom_distribution: Optional custom question distribution
    """
    exam_type: ExamType = Field(
        ...,
        description="Type of exam to generate"
    )
    student_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique student identifier"
    )
    async_generation: bool = Field(
        default=False,
        description="Generate test asynchronously"
    )
    custom_distribution: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Custom question distribution (optional)"
    )
    
    @field_validator('student_id')
    @classmethod
    def validate_student_id(cls, v):
        """Validate student ID is not empty."""
        if not v or not v.strip():
            raise ValueError("student_id cannot be empty")
        return v.strip()
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "exam_type": "JEE_MAIN",
                "student_id": "student_12345",
                "async_generation": False,
                "custom_distribution": None
            }
        }


class TestSubmission(BaseModel):
    """
    Model for test submission.
    
    Attributes:
        test_id: Unique test identifier
        student_id: Student identifier
        answers: Question number to answer mapping
        time_taken: Time taken in seconds
        submission_time: Timestamp of submission
    """
    test_id: str = Field(..., description="Unique test identifier")
    student_id: str = Field(..., description="Student identifier")
    answers: Dict[int, str] = Field(
        ...,
        description="Question number to answer mapping"
    )
    time_taken: int = Field(
        ...,
        ge=0,
        description="Time taken in seconds"
    )
    submission_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Submission timestamp"
    )
    
    @field_validator('answers')
    @classmethod
    def validate_answers(cls, v):
        """Validate answer format."""
        for q_num, answer in v.items():
            if not isinstance(q_num, int) or q_num <= 0:
                raise ValueError(f"Invalid question number: {q_num}")
            
            # Answer can be A/B/C/D or a number
            if isinstance(answer, str):
                answer_upper = answer.upper().strip()
                if answer_upper not in ['A', 'B', 'C', 'D', ''] and not answer.replace('.', '').replace('-', '').isdigit():
                    raise ValueError(f"Invalid answer format: {answer}")
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "test_uuid_123",
                "student_id": "student_12345",
                "answers": {
                    1: "B",
                    2: "A",
                    3: "42.5",
                    4: "C"
                },
                "time_taken": 5400,
                "submission_time": "2024-01-15T10:30:00"
            }
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TestGenerationResult(BaseModel):
    """
    Result of test generation.
    
    Attributes:
        test_id: Generated test identifier
        status: Generation status
        questions_generated: Number of questions generated
        total_questions: Total questions required
        generation_time: Time taken to generate (seconds)
        errors: List of errors encountered
        warnings: List of warnings
    """
    test_id: str = Field(..., description="Generated test identifier")
    status: str = Field(
        ...,
        description="Generation status (success, partial_success, failed)"
    )
    questions_generated: int = Field(
        ...,
        ge=0,
        description="Number of questions generated"
    )
    total_questions: int = Field(
        ...,
        gt=0,
        description="Total questions required"
    )
    generation_time: float = Field(
        ...,
        ge=0,
        description="Generation time in seconds"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Errors encountered"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate status value."""
        valid_statuses = ['success', 'partial_success', 'failed']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "test_uuid_123",
                "status": "success",
                "questions_generated": 90,
                "total_questions": 90,
                "generation_time": 2.5,
                "errors": [],
                "warnings": []
            }
        }


class GenerationStatusResponse(BaseModel):
    """
    Status of async test generation job.
    
    Attributes:
        job_id: Unique job identifier
        status: Current job status
        progress: Progress percentage (0-100)
        current_step: Current generation step
        test_id: Test ID if completed
        error: Error message if failed
    """
    job_id: str = Field(..., description="Unique job identifier")
    status: GenerationStatus = Field(..., description="Current job status")
    progress: int = Field(
        ...,
        ge=0,
        le=100,
        description="Progress percentage"
    )
    current_step: str = Field(..., description="Current generation step")
    test_id: Optional[str] = Field(
        default=None,
        description="Test ID if completed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "job_id": "job_uuid_456",
                "status": "in_progress",
                "progress": 65,
                "current_step": "Generating questions",
                "test_id": None,
                "error": None
            }
        }


# ============================================================================
# TEST STRUCTURE MODELS
# ============================================================================

class TestMetadata(BaseModel):
    """
    Metadata for diagnostic test.
    
    Attributes:
        test_id: Unique test identifier
        exam_type: Type of exam
        student_id: Student identifier
        generation_date: Test generation timestamp
        start_date: Test start timestamp
        submission_date: Test submission timestamp
        status: Current test status
    """
    test_id: str = Field(..., description="Unique test identifier")
    exam_type: ExamType = Field(..., description="Type of exam")
    student_id: str = Field(..., description="Student identifier")
    generation_date: datetime = Field(
        default_factory=datetime.utcnow,
        description="Test generation timestamp"
    )
    start_date: Optional[datetime] = Field(
        default=None,
        description="Test start timestamp"
    )
    submission_date: Optional[datetime] = Field(
        default=None,
        description="Test submission timestamp"
    )
    status: TestStatus = Field(
        default=TestStatus.PENDING,
        description="Current test status"
    )
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "test_id": "test_uuid_123",
                "exam_type": "JEE_MAIN",
                "student_id": "student_12345",
                "generation_date": "2024-01-15T09:00:00",
                "start_date": None,
                "submission_date": None,
                "status": "pending"
            }
        }


class Question(BaseModel):
    """
    Individual question model.
    
    Attributes:
        question_id: Unique question identifier
        question_number: Question number in test
        question_text: Question text/statement
        options: Answer options (A, B, C, D)
        correct_answer: Correct answer
        question_type: Type of question
        marks: Marks for correct answer
        negative_marks: Marks deducted for incorrect
        difficulty: Question difficulty level
        topic: Topic name
        subject: Subject name
    """
    question_id: str = Field(..., description="Unique question identifier")
    question_number: int = Field(
        ...,
        gt=0,
        description="Question number in test"
    )
    question_text: str = Field(
        ...,
        min_length=10,
        description="Question text"
    )
    options: Dict[str, str] = Field(
        default_factory=dict,
        description="Answer options (A, B, C, D)"
    )
    correct_answer: str = Field(..., description="Correct answer")
    question_type: QuestionType = Field(..., description="Type of question")
    marks: int = Field(..., gt=0, description="Marks for correct answer")
    negative_marks: int = Field(
        default=0,
        le=0,
        description="Marks deducted for incorrect"
    )
    difficulty: Difficulty = Field(..., description="Question difficulty")
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    
    @model_validator(mode='after')
    def validate_question(self):
        """Validate options and correct answer for MCQ questions."""
        if self.question_type in [QuestionType.SINGLE_CORRECT, QuestionType.MULTIPLE_CORRECT]:
            if not self.options:
                raise ValueError("MCQ questions must have options")
            
            expected_keys = {'A', 'B', 'C', 'D'}
            if set(self.options.keys()) != expected_keys:
                raise ValueError(f"Options must have keys A, B, C, D. Got: {set(self.options.keys())}")
            
            for key, value in self.options.items():
                if not value or not value.strip():
                    raise ValueError(f"Option {key} cannot be empty")
            
            # Validate correct answer
            if self.correct_answer.upper() not in ['A', 'B', 'C', 'D']:
                raise ValueError(f"Correct answer must be A, B, C, or D for MCQ. Got: {self.correct_answer}")
        
        return self
    
    class Config:
        use_enum_values = True
        schema_extra = {
            "example": {
                "question_id": "q_001",
                "question_number": 1,
                "question_text": "What is the acceleration due to gravity on Earth?",
                "options": {
                    "A": "9.8 m/s²",
                    "B": "10 m/s²",
                    "C": "8.9 m/s²",
                    "D": "11 m/s²"
                },
                "correct_answer": "A",
                "question_type": "single_correct",
                "marks": 4,
                "negative_marks": -1,
                "difficulty": "easy",
                "topic": "Mechanics",
                "subject": "Physics"
            }
        }


class Section(BaseModel):
    """
    Test section model.
    
    Attributes:
        section_name: Name of section
        subject: Subject name
        questions: List of questions
        total_marks: Total marks for section
        duration_minutes: Section duration
        instructions: Section-specific instructions
    """
    section_name: str = Field(..., description="Name of section")
    subject: str = Field(..., description="Subject name")
    questions: List[Question] = Field(
        ...,
        min_items=1,
        description="List of questions"
    )
    total_marks: int = Field(..., gt=0, description="Total marks for section")
    duration_minutes: int = Field(
        ...,
        gt=0,
        description="Section duration in minutes"
    )
    instructions: str = Field(..., description="Section instructions")
    
    @model_validator(mode='after')
    def validate_section(self):
        """Validate total marks match questions."""
        if self.questions:
            calculated_marks = sum(q.marks for q in self.questions)
            if calculated_marks != self.total_marks:
                raise ValueError(
                    f"Total marks ({self.total_marks}) must match sum of question marks ({calculated_marks})"
                )
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "section_name": "Section A - Physics",
                "subject": "Physics",
                "questions": [],  # List of Question objects
                "total_marks": 120,
                "duration_minutes": 60,
                "instructions": "Attempt all questions. Each correct answer: +4 marks."
            }
        }


class DiagnosticTest(BaseModel):
    """
    Complete diagnostic test model.
    
    Attributes:
        test_id: Unique test identifier
        metadata: Test metadata
        instructions: General test instructions
        sections: List of test sections
        total_marks: Total marks for test
        duration_minutes: Total test duration
    """
    test_id: str = Field(..., description="Unique test identifier")
    metadata: TestMetadata = Field(..., description="Test metadata")
    instructions: str = Field(..., description="General test instructions")
    sections: List[Section] = Field(
        ...,
        min_items=1,
        description="List of test sections"
    )
    total_marks: int = Field(..., gt=0, description="Total marks for test")
    duration_minutes: int = Field(
        ...,
        gt=0,
        description="Total test duration in minutes"
    )
    
    @model_validator(mode='after')
    def validate_test(self):
        """Validate total marks match sections."""
        if self.sections:
            calculated_marks = sum(s.total_marks for s in self.sections)
            if calculated_marks != self.total_marks:
                raise ValueError(
                    f"Total marks ({self.total_marks}) must match sum of section marks ({calculated_marks})"
                )
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "test_uuid_123",
                "metadata": {
                    "test_id": "test_uuid_123",
                    "exam_type": "JEE_MAIN",
                    "student_id": "student_12345",
                    "generation_date": "2024-01-15T09:00:00",
                    "status": "pending"
                },
                "instructions": "Read all instructions carefully...",
                "sections": [],  # List of Section objects
                "total_marks": 360,
                "duration_minutes": 180
            }
        }


# ============================================================================
# RESULTS MODELS
# ============================================================================

class SectionScore(BaseModel):
    """
    Score details for a section.
    
    Attributes:
        section_name: Name of section
        score: Score obtained
        total_marks: Total marks possible
        correct: Number of correct answers
        incorrect: Number of incorrect answers
        unattempted: Number of unattempted questions
    """
    section_name: str = Field(..., description="Name of section")
    score: int = Field(..., ge=0, description="Score obtained")
    total_marks: int = Field(..., gt=0, description="Total marks possible")
    correct: int = Field(..., ge=0, description="Number of correct answers")
    incorrect: int = Field(..., ge=0, description="Number of incorrect answers")
    unattempted: int = Field(..., ge=0, description="Number of unattempted")
    
    @model_validator(mode='after')
    def validate_section_score(self):
        """Validate score doesn't exceed total marks."""
        if self.score > self.total_marks:
            raise ValueError(f"Score ({self.score}) cannot exceed total marks ({self.total_marks})")
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "section_name": "Section A - Physics",
                "score": 96,
                "total_marks": 120,
                "correct": 25,
                "incorrect": 3,
                "unattempted": 2
            }
        }


class TestResults(BaseModel):
    """
    Complete test results.
    
    Attributes:
        test_id: Test identifier
        student_id: Student identifier
        total_score: Total score obtained
        total_marks: Total marks possible
        percentage: Percentage score
        section_scores: Section-wise scores
        correct_count: Total correct answers
        incorrect_count: Total incorrect answers
        unattempted_count: Total unattempted questions
    """
    test_id: str = Field(..., description="Test identifier")
    student_id: str = Field(..., description="Student identifier")
    total_score: int = Field(..., ge=0, description="Total score obtained")
    total_marks: int = Field(..., gt=0, description="Total marks possible")
    percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage score"
    )
    section_scores: Dict[str, SectionScore] = Field(
        ...,
        description="Section-wise scores"
    )
    correct_count: int = Field(..., ge=0, description="Total correct answers")
    incorrect_count: int = Field(..., ge=0, description="Total incorrect answers")
    unattempted_count: int = Field(..., ge=0, description="Total unattempted")
    
    @model_validator(mode='after')
    def validate_results(self):
        """Validate percentage and total score."""
        # Validate total score doesn't exceed total marks
        if self.total_score > self.total_marks:
            raise ValueError(f"Total score ({self.total_score}) cannot exceed total marks ({self.total_marks})")
        
        # Validate percentage calculation
        expected_percentage = (self.total_score / self.total_marks) * 100
        if abs(self.percentage - expected_percentage) > 0.1:  # Allow small floating point errors
            raise ValueError(
                f"Percentage ({self.percentage}) doesn't match calculated value ({expected_percentage:.2f})"
            )
        
        return self
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "test_uuid_123",
                "student_id": "student_12345",
                "total_score": 280,
                "total_marks": 360,
                "percentage": 77.78,
                "section_scores": {
                    "Physics": {
                        "section_name": "Section A - Physics",
                        "score": 96,
                        "total_marks": 120,
                        "correct": 25,
                        "incorrect": 3,
                        "unattempted": 2
                    }
                },
                "correct_count": 72,
                "incorrect_count": 10,
                "unattempted_count": 8
            }
        }


# ============================================================================
# UTILITY MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "Test not found",
                "detail": "No test found with ID: test_uuid_123",
                "timestamp": "2024-01-15T10:30:00"
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response."""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Test generated successfully",
                "data": {"test_id": "test_uuid_123"},
                "timestamp": "2024-01-15T10:30:00"
            }
        }
