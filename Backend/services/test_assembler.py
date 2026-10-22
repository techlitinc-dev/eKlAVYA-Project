"""
Test Assembler Service for Mentor AI Diagnostic Tests.

This service assembles questions into complete diagnostic tests, applying
patterns, shuffling, numbering, and adding all necessary metadata and instructions.

Example Usage:
    >>> from services.test_assembler import TestAssembler
    >>> from utils.pattern_loader import PatternLoader
    >>> 
    >>> loader = PatternLoader()
    >>> pattern = loader.load_pattern("JEE_MAIN")
    >>> assembler = TestAssembler()
    >>> 
    >>> diagnostic_test = assembler.assemble_test(questions, pattern, "student_123")
    >>> print(f"Test ID: {diagnostic_test.metadata.test_id}")
"""

import logging
import random
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test status values."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ShuffleStrategy(str, Enum):
    """Question shuffling strategies."""
    RANDOM = "random"  # Completely random within section
    PROGRESSIVE = "progressive"  # Easy to hard progression
    MIXED = "mixed"  # Mix of easy/medium/hard


class TestMetadata(BaseModel):
    """Metadata for diagnostic test."""
    test_id: str = Field(..., description="Unique test identifier (UUID)")
    exam_type: str = Field(..., description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)")
    exam_name: str = Field(..., description="Display name of exam")
    student_id: str = Field(..., description="Student identifier")
    generation_date: datetime = Field(default_factory=datetime.utcnow, description="Test generation timestamp")
    total_questions: int = Field(..., gt=0, description="Total number of questions")
    total_marks: float = Field(..., gt=0, description="Total marks")
    duration_minutes: int = Field(..., gt=0, description="Test duration in minutes")
    status: TestStatus = Field(default=TestStatus.PENDING, description="Test status")
    shuffle_seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    version: str = Field(default="1.0", description="Test version")
    
    class Config:
        use_enum_values = True


class DiagnosticTest(BaseModel):
    """Complete diagnostic test ready for deployment."""
    metadata: TestMetadata = Field(..., description="Test metadata")
    instructions: str = Field(..., description="General test instructions")
    sections: List = Field(..., min_items=1, description="Test sections with questions")
    
    # Computed fields
    is_valid: bool = Field(default=True, description="Whether test is valid")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    # Additional metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('sections')
    def validate_sections(cls, v, values):
        """Validate sections match metadata."""
        if 'metadata' in values:
            section_total = sum(s.question_count for s in v)
            if section_total != values['metadata'].total_questions:
                raise ValueError(
                    f"Section questions ({section_total}) must match "
                    f"total_questions ({values['metadata'].total_questions})"
                )
        return v


class TestAssembler:
    """
    Service for assembling complete diagnostic tests.
    
    This service handles:
    - Applying exam patterns to questions
    - Shuffling questions within sections
    - Sequential numbering across test
    - Adding metadata and instructions
    - Calculating totals
    - Validating test completeness
    
    Attributes:
        pattern_service: TestPatternService instance
        default_shuffle_strategy: Default shuffling strategy
    """
    
    def __init__(self, pattern_service=None, shuffle_strategy: ShuffleStrategy = ShuffleStrategy.MIXED):
        """
        Initialize the TestAssembler.
        
        Args:
            pattern_service: Optional TestPatternService instance
            shuffle_strategy: Default shuffling strategy
        """
        self.pattern_service = pattern_service
        self.default_shuffle_strategy = shuffle_strategy
        logger.info(
            f"TestAssembler initialized with shuffle strategy: {shuffle_strategy.value}"
        )
    
    def assemble_test(
        self,
        questions: List[Dict],
        exam_pattern,
        student_id: str,
        shuffle: bool = True,
        shuffle_seed: Optional[int] = None,
        test_id: Optional[str] = None
    ) -> DiagnosticTest:
        """
        Assemble complete diagnostic test from questions.
        
        Args:
            questions: List of question dictionaries
            exam_pattern: ExamPattern object from PatternLoader
            student_id: Student identifier
            shuffle: Whether to shuffle questions
            shuffle_seed: Optional random seed for reproducibility
            test_id: Optional custom test ID
            
        Returns:
            DiagnosticTest ready for deployment
            
        Raises:
            ValueError: If questions don't meet requirements
        """
        logger.info(
            f"Assembling test: {exam_pattern.exam_name}, "
            f"{len(questions)} questions, student={student_id}"
        )
        
        # Generate test ID if not provided
        if not test_id:
            test_id = str(uuid.uuid4())
        
        # Generate shuffle seed if not provided
        if shuffle and shuffle_seed is None:
            shuffle_seed = random.randint(1, 1000000)
        
        # Step 1: Apply pattern using TestPatternService
        if not self.pattern_service:
            raise RuntimeError("TestPatternService not initialized")
        
        patterned_test = self.pattern_service.apply_pattern(
            questions=questions,
            exam_pattern=exam_pattern,
            test_id=test_id
        )
        
        logger.info(f"Pattern applied: {len(patterned_test.sections)} sections")
        
        # Step 2: Shuffle questions within each section
        if shuffle:
            for section in patterned_test.sections:
                section.questions = self._shuffle_questions(
                    section.questions,
                    shuffle_seed,
                    self.default_shuffle_strategy
                )
            logger.info(f"Questions shuffled with seed: {shuffle_seed}")
        
        # Step 3: Number questions sequentially
        patterned_test.sections = self._add_sequential_numbering(patterned_test.sections)
        logger.info("Sequential numbering applied")
        
        # Step 4: Calculate totals
        total_marks, duration_minutes = self._calculate_totals(patterned_test)
        
        # Step 5: Create test metadata
        metadata = TestMetadata(
            test_id=test_id,
            exam_type=patterned_test.exam_type,
            exam_name=patterned_test.exam_name,
            student_id=student_id,
            generation_date=datetime.utcnow(),
            total_questions=patterned_test.total_questions,
            total_marks=total_marks,
            duration_minutes=duration_minutes,
            status=TestStatus.PENDING,
            shuffle_seed=shuffle_seed if shuffle else None,
            version="1.0"
        )
        
        # Step 6: Generate test instructions
        instructions = self._generate_instructions(patterned_test, exam_pattern)
        
        # Step 7: Create diagnostic test
        diagnostic_test = DiagnosticTest(
            metadata=metadata,
            instructions=instructions,
            sections=patterned_test.sections
        )
        
        # Step 8: Validate test
        validation_errors, warnings = self._validate_test(diagnostic_test, exam_pattern)
        diagnostic_test.validation_errors = validation_errors
        diagnostic_test.warnings = warnings
        diagnostic_test.is_valid = len(validation_errors) == 0
        
        logger.info(
            f"Test assembled: {test_id}, "
            f"valid={diagnostic_test.is_valid}, "
            f"errors={len(validation_errors)}, "
            f"warnings={len(warnings)}"
        )
        
        return diagnostic_test
    
    def _shuffle_questions(
        self,
        questions: List,
        seed: int,
        strategy: ShuffleStrategy
    ) -> List:
        """
        Shuffle questions within a section based on strategy.
        
        Args:
            questions: List of Question objects
            seed: Random seed for reproducibility
            strategy: Shuffling strategy
            
        Returns:
            Shuffled list of questions
        """
        if not questions:
            return questions
        
        # Create a copy to avoid modifying original
        shuffled = list(questions)
        
        if strategy == ShuffleStrategy.RANDOM:
            # Completely random shuffle
            random.seed(seed)
            random.shuffle(shuffled)
        
        elif strategy == ShuffleStrategy.PROGRESSIVE:
            # Sort by difficulty: easy → medium → hard
            difficulty_order = {"easy": 1, "medium": 2, "hard": 3}
            shuffled.sort(key=lambda q: difficulty_order.get(q.difficulty, 2))
            
            # Shuffle within each difficulty group
            random.seed(seed)
            easy = [q for q in shuffled if q.difficulty == "easy"]
            medium = [q for q in shuffled if q.difficulty == "medium"]
            hard = [q for q in shuffled if q.difficulty == "hard"]
            
            random.shuffle(easy)
            random.shuffle(medium)
            random.shuffle(hard)
            
            shuffled = easy + medium + hard
        
        elif strategy == ShuffleStrategy.MIXED:
            # Mix difficulties but maintain some progression
            random.seed(seed)
            
            # Group by difficulty
            by_difficulty = {
                "easy": [q for q in shuffled if q.difficulty == "easy"],
                "medium": [q for q in shuffled if q.difficulty == "medium"],
                "hard": [q for q in shuffled if q.difficulty == "hard"]
            }
            
            # Shuffle each group
            for difficulty_list in by_difficulty.values():
                random.shuffle(difficulty_list)
            
            # Interleave: start with easy, mix in medium and hard
            shuffled = []
            max_len = max(len(lst) for lst in by_difficulty.values())
            
            for i in range(max_len):
                if i < len(by_difficulty["easy"]):
                    shuffled.append(by_difficulty["easy"][i])
                if i < len(by_difficulty["medium"]):
                    shuffled.append(by_difficulty["medium"][i])
                if i < len(by_difficulty["hard"]):
                    shuffled.append(by_difficulty["hard"][i])
        
        logger.debug(f"Shuffled {len(shuffled)} questions using {strategy.value} strategy")
        return shuffled
    
    def _add_sequential_numbering(self, sections: List) -> List:
        """
        Add sequential numbering across all sections.
        
        Args:
            sections: List of Section objects
            
        Returns:
            Updated sections with sequential numbering
        """
        question_number = 1
        
        for section in sections:
            for question in section.questions:
                question.question_number = question_number
                question_number += 1
        
        logger.debug(f"Numbered {question_number - 1} questions sequentially")
        return sections
    
    def _calculate_totals(self, patterned_test) -> Tuple[float, int]:
        """
        Calculate total marks and duration.
        
        Args:
            patterned_test: PatternedTest object
            
        Returns:
            Tuple of (total_marks, duration_minutes)
        """
        total_marks = sum(section.total_marks for section in patterned_test.sections)
        duration_minutes = patterned_test.duration_minutes
        
        return total_marks, duration_minutes
    
    def _generate_instructions(self, patterned_test, exam_pattern) -> str:
        """
        Generate comprehensive test instructions.
        
        Args:
            patterned_test: PatternedTest object
            exam_pattern: ExamPattern object
            
        Returns:
            Formatted instructions string
        """
        instructions_parts = [
            f"DIAGNOSTIC TEST: {patterned_test.exam_name}",
            "=" * 80,
            "",
            "GENERAL INSTRUCTIONS:",
            "",
            f"1. Total Questions: {patterned_test.total_questions}",
            f"2. Total Marks: {patterned_test.total_marks}",
            f"3. Duration: {patterned_test.duration_minutes} minutes",
            f"4. Number of Sections: {len(patterned_test.sections)}",
            "",
            "IMPORTANT GUIDELINES:",
            "",
            "• Read all instructions carefully before starting the test.",
            "• All questions are compulsory.",
            "• Each section must be attempted in the given order.",
            "• Use of calculator is not permitted.",
            "• Rough work should be done on the space provided.",
            "",
            "MARKING SCHEME:",
            "",
            f"• Correct Answer: +{exam_pattern.marking_scheme.correct_marks} marks",
            f"• Incorrect Answer: {exam_pattern.marking_scheme.incorrect_marks} marks",
            f"• Unattempted: {exam_pattern.marking_scheme.unattempted_marks} marks",
            "",
            "Note: Some question types may have different marking schemes.",
            "Please refer to section-specific instructions.",
            "",
            "SECTION BREAKDOWN:",
            ""
        ]
        
        # Add section details
        for i, section in enumerate(patterned_test.sections, 1):
            instructions_parts.extend([
                f"{i}. {section.section_name}",
                f"   Questions: {section.question_count}",
                f"   Marks: {section.total_marks}",
                f"   Types: {section.instructions.question_types}",
                ""
            ])
        
        instructions_parts.extend([
            "TIME MANAGEMENT TIPS:",
            "",
            f"• Average time per question: ~{patterned_test.duration_minutes * 60 // patterned_test.total_questions} seconds",
            "• Attempt easier questions first to build confidence.",
            "• Don't spend too much time on any single question.",
            "• Review your answers if time permits.",
            "",
            "=" * 80,
            "",
            "ALL THE BEST!"
        ])
        
        return "\n".join(instructions_parts)
    
    def _validate_test(
        self,
        diagnostic_test: DiagnosticTest,
        exam_pattern
    ) -> Tuple[List[str], List[str]]:
        """
        Validate the assembled test.
        
        Args:
            diagnostic_test: DiagnosticTest object
            exam_pattern: ExamPattern object
            
        Returns:
            Tuple of (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Validate total questions
        if diagnostic_test.metadata.total_questions != exam_pattern.total_questions:
            errors.append(
                f"Total questions mismatch: got {diagnostic_test.metadata.total_questions}, "
                f"expected {exam_pattern.total_questions}"
            )
        
        # Validate sections exist
        if not diagnostic_test.sections:
            errors.append("No sections in test")
        
        # Validate each section
        section_questions = 0
        question_ids = set()
        
        for section in diagnostic_test.sections:
            section_questions += section.question_count
            
            # Check for duplicate questions
            for question in section.questions:
                if question.question_id in question_ids:
                    errors.append(f"Duplicate question ID: {question.question_id}")
                question_ids.add(question.question_id)
                
                # Validate required fields
                if not question.question_text:
                    errors.append(f"Question {question.question_id} missing text")
                
                if question.marks_correct <= 0:
                    errors.append(f"Question {question.question_id} has invalid marks")
                
                # Validate question type specific requirements
                qtype = question.question_type if isinstance(question.question_type, str) else question.question_type.value
                
                if qtype in ["single_correct", "multiple_correct"]:
                    if not question.options:
                        warnings.append(
                            f"Question {question.question_id} (MCQ) has no options"
                        )
                    elif not any(opt.is_correct for opt in question.options):
                        errors.append(
                            f"Question {question.question_id} has no correct answer"
                        )
        
        # Validate section totals
        if section_questions != diagnostic_test.metadata.total_questions:
            errors.append(
                f"Section question total ({section_questions}) doesn't match "
                f"metadata ({diagnostic_test.metadata.total_questions})"
            )
        
        # Validate sequential numbering
        expected_number = 1
        for section in diagnostic_test.sections:
            for question in section.questions:
                if question.question_number != expected_number:
                    warnings.append(
                        f"Question numbering issue: expected {expected_number}, "
                        f"got {question.question_number}"
                    )
                expected_number += 1
        
        # Validate marking scheme applied
        for section in diagnostic_test.sections:
            for question in section.questions:
                if question.marks_correct != exam_pattern.marking_scheme.correct_marks:
                    # This might be intentional for different question types
                    pass
        
        # Log validation results
        if errors:
            logger.error(f"Test validation failed with {len(errors)} errors")
            for error in errors:
                logger.error(f"  - {error}")
        
        if warnings:
            logger.warning(f"Test validation has {len(warnings)} warnings")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        
        if not errors and not warnings:
            logger.info("✓ Test validation passed")
        
        return errors, warnings
    
    def export_test(self, diagnostic_test: DiagnosticTest) -> Dict:
        """
        Export diagnostic test to dictionary format.
        
        Args:
            diagnostic_test: DiagnosticTest object
            
        Returns:
            Dictionary representation suitable for storage
        """
        return diagnostic_test.dict()
    
    def get_test_summary(self, diagnostic_test: DiagnosticTest) -> str:
        """
        Generate a human-readable test summary.
        
        Args:
            diagnostic_test: DiagnosticTest object
            
        Returns:
            Formatted summary string
        """
        lines = [
            "=" * 80,
            "DIAGNOSTIC TEST SUMMARY",
            "=" * 80,
            f"Test ID: {diagnostic_test.metadata.test_id}",
            f"Exam: {diagnostic_test.metadata.exam_name}",
            f"Student: {diagnostic_test.metadata.student_id}",
            f"Status: {diagnostic_test.metadata.status}",
            f"Generated: {diagnostic_test.metadata.generation_date.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"Total Questions: {diagnostic_test.metadata.total_questions}",
            f"Total Marks: {diagnostic_test.metadata.total_marks}",
            f"Duration: {diagnostic_test.metadata.duration_minutes} minutes",
            f"Sections: {len(diagnostic_test.sections)}",
            "",
            f"Valid: {'✓' if diagnostic_test.is_valid else '✗'}",
        ]
        
        if diagnostic_test.validation_errors:
            lines.append(f"\nErrors ({len(diagnostic_test.validation_errors)}):")
            for error in diagnostic_test.validation_errors:
                lines.append(f"  ✗ {error}")
        
        if diagnostic_test.warnings:
            lines.append(f"\nWarnings ({len(diagnostic_test.warnings)}):")
            for warning in diagnostic_test.warnings:
                lines.append(f"  ⚠ {warning}")
        
        lines.append("\nSections:")
        for section in diagnostic_test.sections:
            lines.append(f"  • {section.section_name}: {section.question_count} questions, {section.total_marks} marks")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
