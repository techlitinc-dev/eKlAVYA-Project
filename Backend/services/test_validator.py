"""
Test Validator Service for Mentor AI Diagnostic Tests.

This service validates complete diagnostic tests before storage, checking
structure, counts, question quality, and pattern compliance.

Example Usage:
    >>> from services.test_validator import TestValidator, ValidationLevel
    >>> from utils.pattern_loader import PatternLoader
    >>> 
    >>> loader = PatternLoader()
    >>> pattern = loader.load_pattern("JEE_MAIN")
    >>> validator = TestValidator()
    >>> 
    >>> result = validator.validate_test(diagnostic_test, pattern)
    >>> if result.is_valid:
    ...     print("Test is valid!")
"""

import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    STRICT = "strict"  # All checks must pass
    NORMAL = "normal"  # Allow minor warnings
    LENIENT = "lenient"  # Only check critical issues


class ValidationCategory(str, Enum):
    """Validation check categories."""
    STRUCTURE = "structure"
    COUNTS = "counts"
    QUESTIONS = "questions"
    PATTERN_COMPLIANCE = "pattern_compliance"
    QUALITY = "quality"


class TestValidationResult(BaseModel):
    """Result of test validation."""
    is_valid: bool = Field(..., description="Whether test passed validation")
    validation_level: ValidationLevel = Field(..., description="Validation level used")
    
    # Issues
    errors: List[str] = Field(default_factory=list, description="Blocking errors")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking warnings")
    
    # Quality metrics
    quality_score: int = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    
    # Statistics
    statistics: Dict = Field(default_factory=dict, description="Test statistics")
    
    # Validation details by category
    validation_details: Dict[str, Dict] = Field(
        default_factory=dict,
        description="Detailed validation results by category"
    )
    
    # Timestamp
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class TestValidator:
    """
    Service for validating diagnostic tests.
    
    This service performs comprehensive validation including:
    - Structure validation (fields, types, UUIDs)
    - Count validation (questions, sections, subjects)
    - Question validation (duplicates, options, answers)
    - Pattern compliance (marking, types, difficulty)
    - Quality validation (scores, completeness)
    
    Attributes:
        min_quality_score: Minimum acceptable quality score
        avg_quality_threshold: Minimum average quality
        difficulty_tolerance: Tolerance for difficulty distribution (%)
    """
    
    def __init__(
        self,
        min_quality_score: int = 60,
        avg_quality_threshold: int = 75,
        difficulty_tolerance: float = 5.0
    ):
        """
        Initialize the TestValidator.
        
        Args:
            min_quality_score: Minimum quality score per question
            avg_quality_threshold: Minimum average quality score
            difficulty_tolerance: Tolerance for difficulty distribution (%)
        """
        self.min_quality_score = min_quality_score
        self.avg_quality_threshold = avg_quality_threshold
        self.difficulty_tolerance = difficulty_tolerance
        
        logger.info(
            f"TestValidator initialized: min_quality={min_quality_score}, "
            f"avg_threshold={avg_quality_threshold}, tolerance={difficulty_tolerance}%"
        )
    
    def validate_test(
        self,
        test,
        exam_pattern,
        validation_level: ValidationLevel = ValidationLevel.NORMAL
    ) -> TestValidationResult:
        """
        Validate complete diagnostic test.
        
        Args:
            test: DiagnosticTest object to validate
            exam_pattern: ExamPattern object for compliance checking
            validation_level: Strictness level for validation
            
        Returns:
            TestValidationResult with validation details
        """
        logger.info(
            f"Validating test: {getattr(test.metadata, 'test_id', 'unknown')}, "
            f"level={validation_level.value}"
        )
        
        errors = []
        warnings = []
        validation_details = {}
        
        # 1. Structure validation
        structure_errors, structure_warnings = self._validate_structure(test)
        errors.extend(structure_errors)
        warnings.extend(structure_warnings)
        validation_details[ValidationCategory.STRUCTURE.value] = {
            "errors": len(structure_errors),
            "warnings": len(structure_warnings)
        }
        
        # 2. Count validation
        count_errors, count_warnings = self._validate_counts(test, exam_pattern)
        errors.extend(count_errors)
        warnings.extend(count_warnings)
        validation_details[ValidationCategory.COUNTS.value] = {
            "errors": len(count_errors),
            "warnings": len(count_warnings)
        }
        
        # 3. Question validation
        question_errors, question_warnings = self._validate_questions(test)
        errors.extend(question_errors)
        warnings.extend(question_warnings)
        validation_details[ValidationCategory.QUESTIONS.value] = {
            "errors": len(question_errors),
            "warnings": len(question_warnings)
        }
        
        # 4. Pattern compliance validation
        compliance_errors, compliance_warnings = self._validate_pattern_compliance(
            test, exam_pattern
        )
        errors.extend(compliance_errors)
        warnings.extend(compliance_warnings)
        validation_details[ValidationCategory.PATTERN_COMPLIANCE.value] = {
            "errors": len(compliance_errors),
            "warnings": len(compliance_warnings)
        }
        
        # 5. Quality validation
        quality_score, quality_errors, quality_warnings = self._validate_quality(test)
        errors.extend(quality_errors)
        warnings.extend(quality_warnings)
        validation_details[ValidationCategory.QUALITY.value] = {
            "score": quality_score,
            "errors": len(quality_errors),
            "warnings": len(quality_warnings)
        }
        
        # Calculate statistics
        statistics = self._calculate_statistics(test)
        
        # Determine if valid based on level
        is_valid = self._determine_validity(
            errors, warnings, quality_score, validation_level
        )
        
        # Create result
        result = TestValidationResult(
            is_valid=is_valid,
            validation_level=validation_level,
            errors=errors,
            warnings=warnings,
            quality_score=quality_score,
            statistics=statistics,
            validation_details=validation_details
        )
        
        logger.info(
            f"Validation complete: valid={is_valid}, "
            f"errors={len(errors)}, warnings={len(warnings)}, "
            f"quality={quality_score}"
        )
        
        return result
    
    def _validate_structure(self, test) -> Tuple[List[str], List[str]]:
        """
        Validate test structure.
        
        Args:
            test: DiagnosticTest object
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check metadata exists
        if not hasattr(test, 'metadata'):
            errors.append("Test missing metadata")
            return errors, warnings
        
        metadata = test.metadata
        
        # Validate test_id is valid UUID
        try:
            UUID(metadata.test_id)
        except (ValueError, AttributeError):
            errors.append(f"Invalid test_id: {getattr(metadata, 'test_id', 'missing')}")
        
        # Check required metadata fields
        required_fields = [
            'exam_type', 'exam_name', 'student_id', 'total_questions',
            'total_marks', 'duration_minutes', 'status'
        ]
        
        for field in required_fields:
            if not hasattr(metadata, field):
                errors.append(f"Metadata missing required field: {field}")
            elif getattr(metadata, field) is None:
                errors.append(f"Metadata field is None: {field}")
        
        # Validate numeric fields
        if hasattr(metadata, 'total_questions') and metadata.total_questions <= 0:
            errors.append(f"Invalid total_questions: {metadata.total_questions}")
        
        if hasattr(metadata, 'total_marks') and metadata.total_marks <= 0:
            errors.append(f"Invalid total_marks: {metadata.total_marks}")
        
        if hasattr(metadata, 'duration_minutes') and metadata.duration_minutes <= 0:
            errors.append(f"Invalid duration_minutes: {metadata.duration_minutes}")
        
        # Check sections exist
        if not hasattr(test, 'sections') or not test.sections:
            errors.append("Test has no sections")
        
        # Check instructions exist
        if not hasattr(test, 'instructions') or not test.instructions:
            warnings.append("Test missing instructions")
        
        logger.debug(f"Structure validation: {len(errors)} errors, {len(warnings)} warnings")
        return errors, warnings
    
    def _validate_counts(self, test, exam_pattern) -> Tuple[List[str], List[str]]:
        """
        Validate question and section counts.
        
        Args:
            test: DiagnosticTest object
            exam_pattern: ExamPattern object
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not hasattr(test, 'sections'):
            return errors, warnings
        
        # Validate total questions
        actual_total = sum(section.question_count for section in test.sections)
        expected_total = exam_pattern.total_questions
        
        if actual_total != expected_total:
            errors.append(
                f"Total questions mismatch: got {actual_total}, expected {expected_total}"
            )
        
        # Validate section counts
        for pattern_subject in exam_pattern.subjects:
            section = next(
                (s for s in test.sections if s.subject == pattern_subject.name),
                None
            )
            
            if not section:
                errors.append(f"Missing section for subject: {pattern_subject.name}")
            elif section.question_count != pattern_subject.question_count:
                errors.append(
                    f"Section {pattern_subject.name}: got {section.question_count} questions, "
                    f"expected {pattern_subject.question_count}"
                )
        
        # Validate actual question counts match declared counts
        for section in test.sections:
            actual_count = len(section.questions)
            declared_count = section.question_count
            
            if actual_count != declared_count:
                errors.append(
                    f"Section {section.section_name}: has {actual_count} questions, "
                    f"declares {declared_count}"
                )
        
        logger.debug(f"Count validation: {len(errors)} errors, {len(warnings)} warnings")
        return errors, warnings
    
    def _validate_questions(self, test) -> Tuple[List[str], List[str]]:
        """
        Validate individual questions.
        
        Args:
            test: DiagnosticTest object
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not hasattr(test, 'sections'):
            return errors, warnings
        
        seen_ids = set()
        seen_texts = set()
        
        for section in test.sections:
            for question in section.questions:
                # Check for duplicate IDs
                if question.question_id in seen_ids:
                    errors.append(f"Duplicate question ID: {question.question_id}")
                seen_ids.add(question.question_id)
                
                # Check for duplicate text (potential duplicate questions)
                q_text = question.question_text.strip().lower()
                if q_text in seen_texts:
                    warnings.append(
                        f"Potential duplicate question text: {question.question_id}"
                    )
                seen_texts.add(q_text)
                
                # Validate question text
                if not question.question_text or len(question.question_text.strip()) < 10:
                    errors.append(
                        f"Question {question.question_id} has invalid or too short text"
                    )
                
                # Validate question type specific requirements
                qtype = question.question_type if isinstance(question.question_type, str) else question.question_type.value
                
                if qtype in ["single_correct", "multiple_correct"]:
                    # MCQ validation
                    if not question.options:
                        errors.append(
                            f"MCQ question {question.question_id} has no options"
                        )
                    elif len(question.options) != 4:
                        warnings.append(
                            f"Question {question.question_id} has {len(question.options)} options, "
                            f"expected 4"
                        )
                    else:
                        # Validate options
                        option_ids = [opt.option_id for opt in question.options]
                        expected_ids = ['A', 'B', 'C', 'D']
                        
                        if set(option_ids) != set(expected_ids):
                            errors.append(
                                f"Question {question.question_id} has invalid option IDs: {option_ids}"
                            )
                        
                        # Check for correct answer
                        correct_options = [opt for opt in question.options if opt.is_correct]
                        
                        if not correct_options:
                            errors.append(
                                f"Question {question.question_id} has no correct answer"
                            )
                        elif qtype == "single_correct" and len(correct_options) > 1:
                            errors.append(
                                f"Single correct question {question.question_id} has "
                                f"{len(correct_options)} correct answers"
                            )
                        
                        # Check option text
                        for opt in question.options:
                            if not opt.text or len(opt.text.strip()) < 1:
                                warnings.append(
                                    f"Question {question.question_id} option {opt.option_id} "
                                    f"has empty text"
                                )
                
                elif qtype in ["numerical", "integer"]:
                    # Numerical validation
                    if question.correct_answer is None:
                        errors.append(
                            f"Numerical question {question.question_id} has no correct answer"
                        )
                
                # Validate marks
                if question.marks_correct <= 0:
                    errors.append(
                        f"Question {question.question_id} has invalid positive marks: "
                        f"{question.marks_correct}"
                    )
                
                # Check for explanation (warning only)
                if not hasattr(question, 'explanation') or not question.explanation:
                    # This is optional, so just a warning
                    pass
        
        logger.debug(f"Question validation: {len(errors)} errors, {len(warnings)} warnings")
        return errors, warnings
    
    def _validate_pattern_compliance(
        self,
        test,
        exam_pattern
    ) -> Tuple[List[str], List[str]]:
        """
        Validate compliance with exam pattern.
        
        Args:
            test: DiagnosticTest object
            exam_pattern: ExamPattern object
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        if not hasattr(test, 'sections'):
            return errors, warnings
        
        # Collect all questions
        all_questions = []
        for section in test.sections:
            all_questions.extend(section.questions)
        
        if not all_questions:
            return errors, warnings
        
        # Validate marking scheme
        expected_correct = exam_pattern.marking_scheme.correct_marks
        expected_incorrect = exam_pattern.marking_scheme.incorrect_marks
        
        for question in all_questions:
            qtype = question.question_type if isinstance(question.question_type, str) else question.question_type.value
            
            # Check marking (allow some flexibility for different question types)
            if qtype not in ["numerical", "integer"]:
                if question.marks_correct != expected_correct:
                    warnings.append(
                        f"Question {question.question_id} has non-standard positive marks: "
                        f"{question.marks_correct} (expected {expected_correct})"
                    )
        
        # Validate difficulty distribution
        difficulty_counts = {"easy": 0, "medium": 0, "hard": 0}
        for question in all_questions:
            difficulty = question.difficulty.lower()
            if difficulty in difficulty_counts:
                difficulty_counts[difficulty] += 1
        
        total = len(all_questions)
        if total > 0:
            actual_easy_pct = (difficulty_counts["easy"] / total) * 100
            actual_medium_pct = (difficulty_counts["medium"] / total) * 100
            actual_hard_pct = (difficulty_counts["hard"] / total) * 100
            
            expected_easy = exam_pattern.difficulty_distribution.easy
            expected_medium = exam_pattern.difficulty_distribution.medium
            expected_hard = exam_pattern.difficulty_distribution.hard
            
            tolerance = self.difficulty_tolerance
            
            if abs(actual_easy_pct - expected_easy) > tolerance:
                warnings.append(
                    f"Easy difficulty distribution off: {actual_easy_pct:.1f}% "
                    f"(expected {expected_easy}% ±{tolerance}%)"
                )
            
            if abs(actual_medium_pct - expected_medium) > tolerance:
                warnings.append(
                    f"Medium difficulty distribution off: {actual_medium_pct:.1f}% "
                    f"(expected {expected_medium}% ±{tolerance}%)"
                )
            
            if abs(actual_hard_pct - expected_hard) > tolerance:
                warnings.append(
                    f"Hard difficulty distribution off: {actual_hard_pct:.1f}% "
                    f"(expected {expected_hard}% ±{tolerance}%)"
                )
        
        # Validate question types match pattern
        expected_types = {qt.type for qt in exam_pattern.question_types}
        actual_types = set()
        
        for question in all_questions:
            qtype = question.question_type if isinstance(question.question_type, str) else question.question_type.value
            # Map to pattern types
            if qtype in ["single_correct", "multiple_correct"]:
                actual_types.add("MCQ")
            elif qtype in ["numerical", "integer"]:
                actual_types.add("Numerical")
            else:
                actual_types.add(qtype)
        
        # This is informational, not an error
        if actual_types != expected_types:
            logger.debug(f"Question types: expected {expected_types}, got {actual_types}")
        
        logger.debug(f"Compliance validation: {len(errors)} errors, {len(warnings)} warnings")
        return errors, warnings
    
    def _validate_quality(self, test) -> Tuple[int, List[str], List[str]]:
        """
        Validate test quality.
        
        Args:
            test: DiagnosticTest object
            
        Returns:
            Tuple of (quality_score, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(test)
        
        # Check against thresholds
        if quality_score < self.avg_quality_threshold:
            warnings.append(
                f"Average quality score {quality_score} below threshold "
                f"{self.avg_quality_threshold}"
            )
        
        # Check individual question quality (if available)
        if hasattr(test, 'sections'):
            low_quality_questions = []
            
            for section in test.sections:
                for question in section.questions:
                    # Calculate individual question quality
                    q_quality = self._calculate_question_quality(question)
                    
                    if q_quality < self.min_quality_score:
                        low_quality_questions.append(
                            (question.question_id, q_quality)
                        )
            
            if low_quality_questions:
                warnings.append(
                    f"{len(low_quality_questions)} questions below minimum quality "
                    f"score {self.min_quality_score}"
                )
                
                # List first few
                for qid, score in low_quality_questions[:3]:
                    warnings.append(f"  - Question {qid}: quality score {score}")
        
        logger.debug(f"Quality validation: score={quality_score}, {len(errors)} errors, {len(warnings)} warnings")
        return quality_score, errors, warnings
    
    def _calculate_quality_score(self, test) -> int:
        """
        Calculate overall test quality score.
        
        Args:
            test: DiagnosticTest object
            
        Returns:
            Quality score (0-100)
        """
        if not hasattr(test, 'sections') or not test.sections:
            return 0
        
        scores = []
        
        for section in test.sections:
            for question in section.questions:
                q_score = self._calculate_question_quality(question)
                scores.append(q_score)
        
        if not scores:
            return 0
        
        return int(sum(scores) / len(scores))
    
    def _calculate_question_quality(self, question) -> int:
        """
        Calculate individual question quality score.
        
        Args:
            question: Question object
            
        Returns:
            Quality score (0-100)
        """
        score = 100
        
        # Deduct for missing or poor question text
        if not question.question_text:
            score -= 50
        elif len(question.question_text.strip()) < 20:
            score -= 20
        elif len(question.question_text.strip()) < 50:
            score -= 10
        
        # Check options quality (for MCQ)
        qtype = question.question_type if isinstance(question.question_type, str) else question.question_type.value
        
        if qtype in ["single_correct", "multiple_correct"]:
            if not question.options:
                score -= 30
            elif len(question.options) != 4:
                score -= 15
            else:
                # Check option text quality
                for opt in question.options:
                    if not opt.text or len(opt.text.strip()) < 2:
                        score -= 5
                
                # Check for correct answer
                if not any(opt.is_correct for opt in question.options):
                    score -= 20
        
        # Check for explanation (bonus)
        if hasattr(question, 'explanation') and question.explanation:
            score = min(100, score + 5)
        
        return max(0, score)
    
    def _calculate_statistics(self, test) -> Dict:
        """
        Calculate test statistics.
        
        Args:
            test: DiagnosticTest object
            
        Returns:
            Dictionary of statistics
        """
        stats = {
            "total_questions": 0,
            "total_sections": 0,
            "difficulty_distribution": {"easy": 0, "medium": 0, "hard": 0},
            "question_types": {},
            "subjects": {},
            "average_marks_per_question": 0.0
        }
        
        if not hasattr(test, 'sections'):
            return stats
        
        stats["total_sections"] = len(test.sections)
        
        all_questions = []
        for section in test.sections:
            all_questions.extend(section.questions)
            
            # Count by subject
            stats["subjects"][section.subject] = section.question_count
        
        stats["total_questions"] = len(all_questions)
        
        if all_questions:
            # Difficulty distribution
            for question in all_questions:
                difficulty = question.difficulty.lower()
                if difficulty in stats["difficulty_distribution"]:
                    stats["difficulty_distribution"][difficulty] += 1
            
            # Question types
            for question in all_questions:
                qtype = question.question_type if isinstance(question.question_type, str) else question.question_type.value
                stats["question_types"][qtype] = stats["question_types"].get(qtype, 0) + 1
            
            # Average marks
            total_marks = sum(q.marks_correct for q in all_questions)
            stats["average_marks_per_question"] = total_marks / len(all_questions)
        
        return stats
    
    def _determine_validity(
        self,
        errors: List[str],
        warnings: List[str],
        quality_score: int,
        level: ValidationLevel
    ) -> bool:
        """
        Determine if test is valid based on validation level.
        
        Args:
            errors: List of errors
            warnings: List of warnings
            quality_score: Quality score
            level: Validation level
            
        Returns:
            True if test is valid
        """
        if level == ValidationLevel.STRICT:
            # No errors or warnings allowed
            return len(errors) == 0 and len(warnings) == 0 and quality_score >= self.avg_quality_threshold
        
        elif level == ValidationLevel.NORMAL:
            # No errors, warnings allowed
            return len(errors) == 0 and quality_score >= self.min_quality_score
        
        elif level == ValidationLevel.LENIENT:
            # Only critical errors block
            critical_keywords = ["missing", "duplicate", "invalid", "no correct answer"]
            critical_errors = [
                e for e in errors
                if any(keyword in e.lower() for keyword in critical_keywords)
            ]
            return len(critical_errors) == 0
        
        return False
    
    def get_validation_summary(self, result: TestValidationResult) -> str:
        """
        Generate human-readable validation summary.
        
        Args:
            result: TestValidationResult object
            
        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 80,
            "TEST VALIDATION SUMMARY",
            "=" * 80,
            f"Validation Level: {result.validation_level}",
            f"Valid: {'✓' if result.is_valid else '✗'}",
            f"Quality Score: {result.quality_score}/100",
            f"Validated At: {result.validated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Statistics
        if result.statistics:
            lines.append("Statistics:")
            lines.append(f"  Total Questions: {result.statistics.get('total_questions', 0)}")
            lines.append(f"  Total Sections: {result.statistics.get('total_sections', 0)}")
            
            if 'subjects' in result.statistics:
                lines.append("  Subjects:")
                for subject, count in result.statistics['subjects'].items():
                    lines.append(f"    • {subject}: {count} questions")
            
            lines.append("")
        
        # Errors
        if result.errors:
            lines.append(f"Errors ({len(result.errors)}):")
            for error in result.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")
        
        # Warnings
        if result.warnings:
            lines.append(f"Warnings ({len(result.warnings)}):")
            for warning in result.warnings[:10]:  # Limit to first 10
                lines.append(f"  ⚠ {warning}")
            if len(result.warnings) > 10:
                lines.append(f"  ... and {len(result.warnings) - 10} more")
            lines.append("")
        
        # Validation details
        if result.validation_details:
            lines.append("Validation Details:")
            for category, details in result.validation_details.items():
                lines.append(f"  {category}:")
                for key, value in details.items():
                    lines.append(f"    {key}: {value}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
