"""
Exam Pattern Loader for Mentor AI Diagnostic Test Generation.

This module provides functionality to load, validate, and cache exam patterns
from JSON files for different competitive exams (JEE Main, JEE Advanced, NEET).

Example Usage:
    >>> from utils.pattern_loader import PatternLoader
    >>> loader = PatternLoader()
    >>> jee_pattern = loader.load_pattern("JEE_MAIN")
    >>> print(f"Total questions: {jee_pattern.total_questions}")
    >>> all_patterns = loader.get_all_patterns()
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExamType(str, Enum):
    """Supported exam types."""
    JEE_MAIN = "JEE_MAIN"
    JEE_ADVANCED = "JEE_ADVANCED"
    NEET = "NEET"


class SubjectPattern(BaseModel):
    """Subject-specific pattern configuration."""
    name: str = Field(..., description="Subject name (e.g., Physics, Chemistry)")
    question_count: int = Field(..., gt=0, description="Number of questions for this subject")
    weightage: float = Field(..., ge=0, le=100, description="Percentage weightage of subject")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Subject name cannot be empty")
        return v.strip()


class QuestionTypePattern(BaseModel):
    """Question type configuration."""
    type: str = Field(..., description="Question type (e.g., MCQ, Numerical, Integer)")
    count_per_subject: int = Field(..., ge=0, description="Count of this type per subject")
    marks: float = Field(..., gt=0, description="Marks per question of this type")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed_types = ["MCQ", "Numerical", "Integer", "MSQ", "Assertion-Reason"]
        if v not in allowed_types:
            logger.warning(f"Question type '{v}' is not in standard types: {allowed_types}")
        return v


class MarkingScheme(BaseModel):
    """Marking scheme configuration."""
    correct_marks: float = Field(..., gt=0, description="Marks for correct answer")
    incorrect_marks: float = Field(..., le=0, description="Marks deducted for incorrect answer")
    unattempted_marks: float = Field(default=0.0, description="Marks for unattempted question")

    @field_validator('incorrect_marks')
    @classmethod
    def validate_negative_marking(cls, v):
        if v > 0:
            raise ValueError("Incorrect marks should be negative or zero")
        return v


class DifficultyDistribution(BaseModel):
    """Difficulty level distribution."""
    easy: float = Field(..., ge=0, le=100, description="Percentage of easy questions")
    medium: float = Field(..., ge=0, le=100, description="Percentage of medium questions")
    hard: float = Field(..., ge=0, le=100, description="Percentage of hard questions")

    @model_validator(mode='after')
    def validate_total_percentage(self):
        total = self.easy + self.medium + self.hard
        if abs(total - 100.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Difficulty percentages must sum to 100, got {total}")
        return self


class ExamPattern(BaseModel):
    """Complete exam pattern specification."""
    exam_name: str = Field(..., description="Name of the exam")
    total_questions: int = Field(..., gt=0, description="Total number of questions")
    subjects: List[SubjectPattern] = Field(..., min_items=1, description="Subject-wise breakdown")
    question_types: List[QuestionTypePattern] = Field(..., min_items=1, description="Question type breakdown")
    marking_scheme: MarkingScheme = Field(..., description="Marking scheme details")
    duration_minutes: int = Field(..., gt=0, description="Exam duration in minutes")
    difficulty_distribution: DifficultyDistribution = Field(..., description="Difficulty level distribution")

    @model_validator(mode='after')
    def validate_pattern_consistency(self):
        """Validate that all counts and percentages are consistent."""
        # Validate subject question counts sum to total
        subject_total = sum(s.question_count for s in self.subjects)
        if subject_total != self.total_questions:
            raise ValueError(
                f"Sum of subject questions ({subject_total}) must equal total_questions ({self.total_questions})"
            )
        
        # Validate subject weightages sum to 100
        weightage_total = sum(s.weightage for s in self.subjects)
        if abs(weightage_total - 100.0) > 0.01:
            raise ValueError(
                f"Sum of subject weightages ({weightage_total}) must equal 100"
            )
        
        return self

    class Config:
        use_enum_values = True


class PatternLoader:
    """
    Loads and manages exam patterns from JSON files.
    
    This class handles loading exam patterns from the data/exam_patterns/ directory,
    validates them using Pydantic models, and caches them for efficient access.
    
    Attributes:
        patterns_dir (Path): Directory containing pattern JSON files
        _cache (Dict[str, ExamPattern]): Cache of loaded patterns
    """

    def __init__(self, patterns_dir: Optional[str] = None):
        """
        Initialize the PatternLoader.
        
        Args:
            patterns_dir: Optional custom directory path for pattern files.
                         Defaults to 'data/exam_patterns/'
        """
        if patterns_dir:
            self.patterns_dir = Path(patterns_dir)
        else:
            self.patterns_dir = Path(__file__).parent.parent / "data" / "exam_patterns"
        
        self._cache: Dict[str, ExamPattern] = {}
        logger.info(f"PatternLoader initialized with directory: {self.patterns_dir}")
        
        # Create directory if it doesn't exist
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def _load_from_file(self, filename: str) -> dict:
        """
        Load pattern data from a JSON file.
        
        Args:
            filename: Name of the JSON file (with or without .json extension)
            
        Returns:
            Dictionary containing the pattern data
            
        Raises:
            FileNotFoundError: If the pattern file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        file_path = self.patterns_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Pattern file not found: {file_path}. "
                f"Please ensure the file exists in {self.patterns_dir}"
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Successfully loaded pattern from: {filename}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {filename}: {e}")
            raise ValueError(f"Invalid JSON format in {filename}: {e}")

    def validate_pattern(self, pattern: dict) -> bool:
        """
        Validate a pattern dictionary against the ExamPattern model.
        
        Args:
            pattern: Dictionary containing pattern data
            
        Returns:
            True if pattern is valid
            
        Raises:
            ValueError: If pattern validation fails
        """
        try:
            ExamPattern(**pattern)
            logger.info(f"Pattern validation successful for: {pattern.get('exam_name', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Pattern validation failed: {e}")
            raise ValueError(f"Pattern validation error: {e}")

    def load_pattern(self, exam_type: str) -> ExamPattern:
        """
        Load an exam pattern by exam type.
        
        Args:
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            
        Returns:
            ExamPattern object containing the pattern specification
            
        Raises:
            ValueError: If exam_type is invalid or pattern is malformed
            FileNotFoundError: If pattern file doesn't exist
        """
        # Normalize exam type
        exam_type = exam_type.upper()
        
        # Validate exam type
        try:
            ExamType(exam_type)
        except ValueError:
            valid_types = [e.value for e in ExamType]
            raise ValueError(
                f"Invalid exam type: {exam_type}. Must be one of {valid_types}"
            )
        
        # Check cache first
        if exam_type in self._cache:
            logger.info(f"Returning cached pattern for: {exam_type}")
            return self._cache[exam_type]
        
        # Load from file
        filename = f"{exam_type.lower()}.json"
        try:
            pattern_data = self._load_from_file(filename)
            pattern = ExamPattern(**pattern_data)
            
            # Cache the pattern
            self._cache[exam_type] = pattern
            logger.info(f"Pattern loaded and cached for: {exam_type}")
            
            return pattern
        except FileNotFoundError:
            logger.error(f"Pattern file not found for exam type: {exam_type}")
            raise
        except Exception as e:
            logger.error(f"Error loading pattern for {exam_type}: {e}")
            raise ValueError(f"Failed to load pattern for {exam_type}: {e}")

    def get_all_patterns(self) -> Dict[str, ExamPattern]:
        """
        Load all available exam patterns.
        
        Returns:
            Dictionary mapping exam types to their ExamPattern objects
        """
        patterns = {}
        
        for exam_type in ExamType:
            try:
                pattern = self.load_pattern(exam_type.value)
                patterns[exam_type.value] = pattern
            except FileNotFoundError:
                logger.warning(f"Pattern file not found for: {exam_type.value}, skipping")
            except Exception as e:
                logger.error(f"Error loading pattern for {exam_type.value}: {e}")
        
        logger.info(f"Loaded {len(patterns)} exam patterns")
        return patterns

    def clear_cache(self) -> None:
        """Clear the pattern cache, forcing reload on next access."""
        self._cache.clear()
        logger.info("Pattern cache cleared")

    def reload_pattern(self, exam_type: str) -> ExamPattern:
        """
        Force reload a pattern from file, bypassing cache.
        
        Args:
            exam_type: Type of exam to reload
            
        Returns:
            Freshly loaded ExamPattern object
        """
        exam_type = exam_type.upper()
        if exam_type in self._cache:
            del self._cache[exam_type]
        return self.load_pattern(exam_type)
