"""
Score Models for Diagnostic Test System - Mentor AI Platform.

This module defines Pydantic models for test scoring, including subject-wise,
topic-wise, and overall score calculations with support for different marking schemes.

Models:
- SubjectScore: Score details for a single subject
- TopicScore: Score details for a single topic
- QuestionScore: Score details for a single question
- TestScore: Complete test score with all analytics
- MarkingScheme: Marking scheme configuration

Author: Mentor AI Team
Version: 1.0.0
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class MarkingScheme(BaseModel):
    """
    Marking scheme for a question type.
    
    Attributes:
        correct_marks: Marks awarded for correct answer
        incorrect_marks: Marks deducted for incorrect answer (negative value)
        partial_marks: Marks awarded for partial correct (for multiple correct)
        unattempted_marks: Marks for unattempted (usually 0)
    
    Example:
        >>> scheme = MarkingScheme(
        ...     correct_marks=4,
        ...     incorrect_marks=-1,
        ...     partial_marks=0,
        ...     unattempted_marks=0
        ... )
    """
    correct_marks: int = Field(
        ...,
        gt=0,
        description="Marks for correct answer"
    )
    incorrect_marks: int = Field(
        ...,
        le=0,
        description="Marks deducted for incorrect answer"
    )
    partial_marks: int = Field(
        default=0,
        ge=0,
        description="Marks for partial correct answer"
    )
    unattempted_marks: int = Field(
        default=0,
        description="Marks for unattempted question"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "correct_marks": 4,
                "incorrect_marks": -1,
                "partial_marks": 1,
                "unattempted_marks": 0
            }
        }


class QuestionScore(BaseModel):
    """
    Score details for a single question.
    
    Attributes:
        question_id: Unique question identifier
        question_number: Question number in test
        question_type: Type of question
        subject: Subject name
        topic: Topic name
        difficulty: Question difficulty
        student_answer: Student's answer
        correct_answer: Correct answer
        is_correct: Whether answer is correct
        is_partial: Whether answer is partially correct
        marks_obtained: Marks obtained for this question
        max_marks: Maximum marks possible
        time_taken: Time taken for this question (seconds)
    
    Example:
        >>> score = QuestionScore(
        ...     question_id="q_001",
        ...     question_number=1,
        ...     question_type="single_correct",
        ...     subject="Physics",
        ...     topic="Mechanics",
        ...     difficulty="medium",
        ...     student_answer="B",
        ...     correct_answer="B",
        ...     is_correct=True,
        ...     is_partial=False,
        ...     marks_obtained=4,
        ...     max_marks=4
        ... )
    """
    question_id: str = Field(..., description="Unique question identifier")
    question_number: int = Field(..., gt=0, description="Question number")
    question_type: str = Field(..., description="Type of question")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    difficulty: str = Field(..., description="Question difficulty")
    student_answer: Optional[str] = Field(
        default=None,
        description="Student's answer"
    )
    correct_answer: str = Field(..., description="Correct answer")
    is_correct: bool = Field(..., description="Whether answer is correct")
    is_partial: bool = Field(
        default=False,
        description="Whether answer is partially correct"
    )
    marks_obtained: int = Field(..., description="Marks obtained")
    max_marks: int = Field(..., gt=0, description="Maximum marks possible")
    time_taken: Optional[int] = Field(
        default=None,
        ge=0,
        description="Time taken in seconds"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question_id": "q_001",
                "question_number": 1,
                "question_type": "single_correct",
                "subject": "Physics",
                "topic": "Mechanics",
                "difficulty": "medium",
                "student_answer": "B",
                "correct_answer": "B",
                "is_correct": True,
                "is_partial": False,
                "marks_obtained": 4,
                "max_marks": 4,
                "time_taken": 120
            }
        }


class TopicScore(BaseModel):
    """
    Score details for a topic.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        total_questions: Total questions in topic
        attempted: Questions attempted
        correct: Correct answers
        incorrect: Incorrect answers
        partial: Partially correct answers
        unattempted: Unattempted questions
        marks_obtained: Total marks obtained
        max_marks: Maximum marks possible
        accuracy: Accuracy percentage (0-100)
        time_taken: Total time taken (seconds)
    
    Example:
        >>> score = TopicScore(
        ...     topic="Mechanics",
        ...     subject="Physics",
        ...     total_questions=10,
        ...     attempted=9,
        ...     correct=7,
        ...     incorrect=2,
        ...     partial=0,
        ...     unattempted=1,
        ...     marks_obtained=26,
        ...     max_marks=40,
        ...     accuracy=77.78
        ... )
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    total_questions: int = Field(..., ge=0, description="Total questions")
    attempted: int = Field(..., ge=0, description="Questions attempted")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    partial: int = Field(default=0, ge=0, description="Partially correct")
    unattempted: int = Field(..., ge=0, description="Unattempted questions")
    marks_obtained: int = Field(..., description="Marks obtained")
    max_marks: int = Field(..., gt=0, description="Maximum marks possible")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage"
    )
    time_taken: Optional[int] = Field(
        default=None,
        ge=0,
        description="Time taken in seconds"
    )
    
    @model_validator(mode='after')
    def validate_topic_score(self):
        """Validate question counts and accuracy."""
        # Validate question counts
        if self.attempted + self.unattempted != self.total_questions:
            raise ValueError(
                f"Attempted ({self.attempted}) + Unattempted ({self.unattempted}) "
                f"must equal Total ({self.total_questions})"
            )
        
        if self.correct + self.incorrect + self.partial != self.attempted:
            raise ValueError(
                f"Correct ({self.correct}) + Incorrect ({self.incorrect}) + "
                f"Partial ({self.partial}) must equal Attempted ({self.attempted})"
            )
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Mechanics",
                "subject": "Physics",
                "total_questions": 10,
                "attempted": 9,
                "correct": 7,
                "incorrect": 2,
                "partial": 0,
                "unattempted": 1,
                "marks_obtained": 26,
                "max_marks": 40,
                "accuracy": 77.78,
                "time_taken": 900
            }
        }


class SubjectScore(BaseModel):
    """
    Score details for a subject.
    
    Attributes:
        subject: Subject name
        total_questions: Total questions in subject
        attempted: Questions attempted
        correct: Correct answers
        incorrect: Incorrect answers
        partial: Partially correct answers
        unattempted: Unattempted questions
        marks_obtained: Total marks obtained
        max_marks: Maximum marks possible
        accuracy: Accuracy percentage (0-100)
        topic_scores: Topic-wise scores
        time_taken: Total time taken (seconds)
    
    Example:
        >>> score = SubjectScore(
        ...     subject="Physics",
        ...     total_questions=60,
        ...     attempted=55,
        ...     correct=45,
        ...     incorrect=10,
        ...     partial=0,
        ...     unattempted=5,
        ...     marks_obtained=170,
        ...     max_marks=240,
        ...     accuracy=81.82,
        ...     topic_scores={}
        ... )
    """
    subject: str = Field(..., description="Subject name")
    total_questions: int = Field(..., ge=0, description="Total questions")
    attempted: int = Field(..., ge=0, description="Questions attempted")
    correct: int = Field(..., ge=0, description="Correct answers")
    incorrect: int = Field(..., ge=0, description="Incorrect answers")
    partial: int = Field(default=0, ge=0, description="Partially correct")
    unattempted: int = Field(..., ge=0, description="Unattempted questions")
    marks_obtained: int = Field(..., description="Marks obtained")
    max_marks: int = Field(..., gt=0, description="Maximum marks possible")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Accuracy percentage"
    )
    topic_scores: Dict[str, TopicScore] = Field(
        default_factory=dict,
        description="Topic-wise scores"
    )
    time_taken: Optional[int] = Field(
        default=None,
        ge=0,
        description="Time taken in seconds"
    )
    
    @model_validator(mode='after')
    def validate_subject_score(self):
        """Validate question counts and accuracy."""
        # Validate question counts
        if self.attempted + self.unattempted != self.total_questions:
            raise ValueError(
                f"Attempted ({self.attempted}) + Unattempted ({self.unattempted}) "
                f"must equal Total ({self.total_questions})"
            )
        
        if self.correct + self.incorrect + self.partial != self.attempted:
            raise ValueError(
                f"Correct ({self.correct}) + Incorrect ({self.incorrect}) + "
                f"Partial ({self.partial}) must equal Attempted ({self.attempted})"
            )
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Physics",
                "total_questions": 60,
                "attempted": 55,
                "correct": 45,
                "incorrect": 10,
                "partial": 0,
                "unattempted": 5,
                "marks_obtained": 170,
                "max_marks": 240,
                "accuracy": 81.82,
                "topic_scores": {},
                "time_taken": 3600
            }
        }


class TestScore(BaseModel):
    """
    Complete test score with all analytics.
    
    Attributes:
        test_id: Test identifier
        student_id: Student identifier
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        total_questions: Total questions in test
        attempted: Total attempted questions
        correct: Total correct answers
        incorrect: Total incorrect answers
        partial: Total partially correct answers
        unattempted: Total unattempted questions
        total_marks_obtained: Total marks obtained
        total_max_marks: Total maximum marks
        percentage: Overall percentage (0-100)
        accuracy: Overall accuracy percentage (0-100)
        subject_scores: Subject-wise scores
        question_scores: Individual question scores
        submission_time: When test was submitted
        time_taken: Total time taken (seconds)
    
    Example:
        >>> score = TestScore(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     exam_type="JEE_MAIN",
        ...     total_questions=200,
        ...     attempted=180,
        ...     correct=150,
        ...     incorrect=30,
        ...     partial=0,
        ...     unattempted=20,
        ...     total_marks_obtained=570,
        ...     total_max_marks=800,
        ...     percentage=71.25,
        ...     accuracy=83.33,
        ...     subject_scores={},
        ...     question_scores=[]
        ... )
    """
    test_id: str = Field(..., description="Test identifier")
    student_id: str = Field(..., description="Student identifier")
    exam_type: str = Field(..., description="Type of exam")
    total_questions: int = Field(..., ge=0, description="Total questions")
    attempted: int = Field(..., ge=0, description="Total attempted")
    correct: int = Field(..., ge=0, description="Total correct")
    incorrect: int = Field(..., ge=0, description="Total incorrect")
    partial: int = Field(default=0, ge=0, description="Total partial correct")
    unattempted: int = Field(..., ge=0, description="Total unattempted")
    total_marks_obtained: int = Field(..., description="Total marks obtained")
    total_max_marks: int = Field(..., gt=0, description="Total max marks")
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall percentage"
    )
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall accuracy percentage"
    )
    subject_scores: Dict[str, SubjectScore] = Field(
        default_factory=dict,
        description="Subject-wise scores"
    )
    question_scores: List[QuestionScore] = Field(
        default_factory=list,
        description="Individual question scores"
    )
    submission_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="Submission timestamp"
    )
    time_taken: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total time taken in seconds"
    )
    
    @model_validator(mode='after')
    def validate_test_score(self):
        """Validate question counts, percentage, and accuracy."""
        # Validate question counts
        if self.attempted + self.unattempted != self.total_questions:
            raise ValueError(
                f"Attempted ({self.attempted}) + Unattempted ({self.unattempted}) "
                f"must equal Total ({self.total_questions})"
            )
        
        if self.correct + self.incorrect + self.partial != self.attempted:
            raise ValueError(
                f"Correct ({self.correct}) + Incorrect ({self.incorrect}) + "
                f"Partial ({self.partial}) must equal Attempted ({self.attempted})"
            )
        
        # Validate percentage calculation
        expected_percentage = (self.total_marks_obtained / self.total_max_marks) * 100
        if abs(self.percentage - expected_percentage) > 0.1:
            raise ValueError(
                f"Percentage ({self.percentage}) doesn't match calculated "
                f"value ({expected_percentage:.2f})"
            )
        
        # Validate accuracy calculation (only for attempted questions)
        if self.attempted > 0:
            expected_accuracy = ((self.correct + (self.partial * 0.5)) / self.attempted) * 100
            if abs(self.accuracy - expected_accuracy) > 0.1:
                raise ValueError(
                    f"Accuracy ({self.accuracy}) doesn't match calculated "
                    f"value ({expected_accuracy:.2f})"
                )
        
        return self
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "test_123",
                "student_id": "student_456",
                "exam_type": "JEE_MAIN",
                "total_questions": 200,
                "attempted": 180,
                "correct": 150,
                "incorrect": 30,
                "partial": 0,
                "unattempted": 20,
                "total_marks_obtained": 570,
                "total_max_marks": 800,
                "percentage": 71.25,
                "accuracy": 83.33,
                "subject_scores": {},
                "question_scores": [],
                "submission_time": "2024-11-28T10:30:00",
                "time_taken": 10800
            }
        }
