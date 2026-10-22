"""
Test Pattern Service for Mentor AI Diagnostic Tests.

This service applies exam-specific patterns to generated questions, organizing
them into sections, applying marking schemes, and adding appropriate metadata.

Example Usage:
    >>> from services.test_pattern_service import TestPatternService
    >>> from utils.pattern_loader import PatternLoader
    >>> 
    >>> loader = PatternLoader()
    >>> pattern = loader.load_pattern("JEE_MAIN")
    >>> service = TestPatternService()
    >>> 
    >>> patterned_test = service.apply_pattern(questions, pattern)
    >>> print(f"Sections: {len(patterned_test.sections)}")
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuestionType(str, Enum):
    """Question types supported."""
    SINGLE_CORRECT = "single_correct"
    MULTIPLE_CORRECT = "multiple_correct"
    NUMERICAL = "numerical"
    INTEGER = "integer"
    MATRIX_MATCH = "matrix_match"
    ASSERTION_REASON = "assertion_reason"


class MarkingSchemeType(str, Enum):
    """Marking scheme types."""
    STANDARD = "standard"  # Fixed marks
    PARTIAL = "partial"  # Partial marking for multiple correct
    NO_NEGATIVE = "no_negative"  # No negative marking


class QuestionOption(BaseModel):
    """Single option for a question."""
    option_id: str = Field(..., description="Option identifier (A, B, C, D)")
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(default=False, description="Whether this option is correct")


class Question(BaseModel):
    """Individual question with pattern applied."""
    question_id: str = Field(..., description="Unique question identifier")
    question_number: int = Field(..., gt=0, description="Question number in section")
    subject: str = Field(..., description="Subject name")
    topic: str = Field(..., description="Topic name")
    chapter: str = Field(..., description="Chapter name")
    difficulty: str = Field(..., description="Difficulty level (easy, medium, hard)")
    
    # Question content
    question_text: str = Field(..., description="Question text/statement")
    question_type: QuestionType = Field(..., description="Type of question")
    options: List[QuestionOption] = Field(default_factory=list, description="Answer options")
    correct_answer: Optional[Any] = Field(None, description="Correct answer (for numerical)")
    
    # Marking scheme
    marks_correct: float = Field(..., description="Marks for correct answer")
    marks_incorrect: float = Field(..., description="Marks for incorrect answer")
    marks_unattempted: float = Field(default=0.0, description="Marks for unattempted")
    marking_scheme_type: MarkingSchemeType = Field(
        default=MarkingSchemeType.STANDARD,
        description="Type of marking scheme"
    )
    
    # Metadata
    time_allocation: Optional[int] = Field(None, description="Suggested time in seconds")
    tags: List[str] = Field(default_factory=list, description="Question tags")
    
    class Config:
        use_enum_values = True


class SectionInstructions(BaseModel):
    """Instructions for a test section."""
    marking_scheme: str = Field(..., description="Marking scheme explanation")
    question_types: str = Field(..., description="Question types in this section")
    time_management: str = Field(..., description="Time management tips")
    general_instructions: List[str] = Field(
        default_factory=list,
        description="General instructions"
    )


class Section(BaseModel):
    """Test section with questions."""
    section_id: str = Field(..., description="Section identifier")
    section_name: str = Field(..., description="Section display name")
    subject: str = Field(..., description="Subject for this section")
    question_count: int = Field(..., gt=0, description="Number of questions")
    total_marks: float = Field(..., gt=0, description="Total marks for section")
    duration_minutes: Optional[int] = Field(None, description="Section duration")
    
    # Questions
    questions: List[Question] = Field(..., min_items=1, description="Questions in section")
    
    # Instructions
    instructions: SectionInstructions = Field(..., description="Section instructions")
    
    # Metadata
    order: int = Field(..., description="Section order in test")
    
    @validator('question_count')
    def validate_question_count(cls, v, values):
        """Validate question count matches actual questions."""
        if 'questions' in values and len(values['questions']) != v:
            raise ValueError(
                f"Question count ({v}) must match number of questions "
                f"({len(values['questions'])})"
            )
        return v


class PatternedTest(BaseModel):
    """Complete test with pattern applied."""
    test_id: str = Field(..., description="Unique test identifier")
    exam_type: str = Field(..., description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)")
    exam_name: str = Field(..., description="Display name of exam")
    total_questions: int = Field(..., gt=0, description="Total questions in test")
    total_marks: float = Field(..., gt=0, description="Total marks")
    duration_minutes: int = Field(..., gt=0, description="Total test duration")
    
    # Sections
    sections: List[Section] = Field(..., min_items=1, description="Test sections")
    
    # Overall instructions
    general_instructions: List[str] = Field(
        default_factory=list,
        description="General test instructions"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_valid: bool = Field(default=True, description="Whether test is valid")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    @validator('total_questions')
    def validate_total_questions(cls, v, values):
        """Validate total questions match sections."""
        if 'sections' in values:
            section_total = sum(s.question_count for s in values['sections'])
            if section_total != v:
                raise ValueError(
                    f"Total questions ({v}) must match sum of section questions "
                    f"({section_total})"
                )
        return v


class TestPatternService:
    """
    Service for applying exam patterns to questions.
    
    This service handles:
    - Organizing questions into sections by subject
    - Applying appropriate marking schemes
    - Setting question types and formats
    - Adding section instructions and metadata
    - Validating pattern compliance
    
    Attributes:
        section_names: Mapping of subjects to section names
        default_time_per_question: Default time allocation per question
    """
    
    # Section name mappings
    SECTION_NAMES = {
        "Physics": "Section A - Physics",
        "Chemistry": "Section B - Chemistry",
        "Mathematics": "Section C - Mathematics",
        "Botany": "Section C - Botany",
        "Zoology": "Section D - Zoology"
    }
    
    # Default time per question (seconds)
    DEFAULT_TIME_PER_QUESTION = {
        QuestionType.SINGLE_CORRECT: 120,  # 2 minutes
        QuestionType.MULTIPLE_CORRECT: 180,  # 3 minutes
        QuestionType.NUMERICAL: 150,  # 2.5 minutes
        QuestionType.INTEGER: 150,
        QuestionType.MATRIX_MATCH: 240,  # 4 minutes
        QuestionType.ASSERTION_REASON: 120
    }
    
    def __init__(self):
        """Initialize the TestPatternService."""
        logger.info("TestPatternService initialized")
    
    def apply_pattern(
        self,
        questions: List[Dict],
        exam_pattern,
        test_id: Optional[str] = None
    ) -> PatternedTest:
        """
        Apply exam pattern to questions.
        
        Args:
            questions: List of question dictionaries
            exam_pattern: ExamPattern object from PatternLoader
            test_id: Optional test identifier
            
        Returns:
            PatternedTest with pattern applied
            
        Raises:
            ValueError: If questions don't match pattern requirements
        """
        logger.info(
            f"Applying pattern: {exam_pattern.exam_name}, "
            f"{len(questions)} questions"
        )
        
        # Generate test ID if not provided
        if not test_id:
            test_id = f"test_{exam_pattern.exam_name.lower().replace(' ', '_')}_{datetime.utcnow().timestamp()}"
        
        # Organize questions into sections
        sections = self._organize_sections(questions, exam_pattern)
        
        # Apply marking scheme to each question
        for section in sections:
            for i, question in enumerate(section.questions):
                section.questions[i] = self._apply_marking_scheme(
                    question, exam_pattern, section.subject
                )
        
        # Add section instructions
        for i, section in enumerate(sections):
            sections[i] = self._add_section_instructions(section, exam_pattern)
        
        # Calculate totals
        total_marks = sum(s.total_marks for s in sections)
        
        # Create patterned test
        patterned_test = PatternedTest(
            test_id=test_id,
            exam_type=exam_pattern.exam_name.upper().replace(" ", "_"),
            exam_name=exam_pattern.exam_name,
            total_questions=exam_pattern.total_questions,
            total_marks=total_marks,
            duration_minutes=exam_pattern.duration_minutes,
            sections=sections,
            general_instructions=self._get_general_instructions(exam_pattern)
        )
        
        # Validate
        warnings = self._validate_pattern_compliance(patterned_test, exam_pattern)
        patterned_test.warnings = warnings
        patterned_test.is_valid = len(warnings) == 0
        
        logger.info(
            f"Pattern applied: {len(sections)} sections, "
            f"{total_marks} marks, valid={patterned_test.is_valid}"
        )
        
        return patterned_test
    
    def _organize_sections(
        self,
        questions: List[Dict],
        exam_pattern
    ) -> List[Section]:
        """
        Organize questions into sections by subject.
        
        Args:
            questions: List of question dictionaries
            exam_pattern: ExamPattern object
            
        Returns:
            List of Section objects
        """
        # Group questions by subject
        by_subject = {}
        for question in questions:
            subject = question.get("subject", "Unknown")
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(question)
        
        # Create sections
        sections = []
        section_order = 1
        
        for subject_pattern in exam_pattern.subjects:
            subject = subject_pattern.name
            subject_questions = by_subject.get(subject, [])
            
            if not subject_questions:
                logger.warning(f"No questions found for subject: {subject}")
                continue
            
            # Convert to Question objects
            question_objects = []
            for i, q in enumerate(subject_questions, 1):
                question_obj = self._create_question_object(q, i)
                question_objects.append(question_obj)
            
            # Calculate section marks
            section_marks = sum(q.marks_correct for q in question_objects)
            
            # Create section
            section = Section(
                section_id=f"section_{subject.lower()}",
                section_name=self.SECTION_NAMES.get(subject, f"Section - {subject}"),
                subject=subject,
                question_count=len(question_objects),
                total_marks=section_marks,
                duration_minutes=None,  # Will be calculated if needed
                questions=question_objects,
                instructions=SectionInstructions(
                    marking_scheme="",
                    question_types="",
                    time_management="",
                    general_instructions=[]
                ),
                order=section_order
            )
            
            sections.append(section)
            section_order += 1
        
        logger.info(f"Organized {len(sections)} sections")
        return sections
    
    def _create_question_object(
        self,
        question_dict: Dict,
        question_number: int
    ) -> Question:
        """
        Create Question object from dictionary.
        
        Args:
            question_dict: Question data dictionary
            question_number: Question number in section
            
        Returns:
            Question object
        """
        # Determine question type
        q_type = question_dict.get("question_type", "MCQ")
        if q_type in ["MCQ", "single_correct"]:
            question_type = QuestionType.SINGLE_CORRECT
        elif q_type in ["MSQ", "multiple_correct"]:
            question_type = QuestionType.MULTIPLE_CORRECT
        elif q_type in ["Numerical", "numerical"]:
            question_type = QuestionType.NUMERICAL
        elif q_type in ["Integer", "integer"]:
            question_type = QuestionType.INTEGER
        else:
            question_type = QuestionType.SINGLE_CORRECT
        
        # Create options if MCQ
        options = []
        if question_type in [QuestionType.SINGLE_CORRECT, QuestionType.MULTIPLE_CORRECT]:
            option_data = question_dict.get("options", [])
            if not option_data:
                # Generate default options
                option_data = [
                    {"option_id": "A", "text": "Option A", "is_correct": False},
                    {"option_id": "B", "text": "Option B", "is_correct": True},
                    {"option_id": "C", "text": "Option C", "is_correct": False},
                    {"option_id": "D", "text": "Option D", "is_correct": False}
                ]
            
            for opt in option_data:
                options.append(QuestionOption(
                    option_id=opt.get("option_id", "A"),
                    text=opt.get("text", ""),
                    is_correct=opt.get("is_correct", False)
                ))
        
        # Create question
        return Question(
            question_id=question_dict.get("question_id", f"q_{question_number}"),
            question_number=question_number,
            subject=question_dict.get("subject", "Unknown"),
            topic=question_dict.get("topic", "Unknown"),
            chapter=question_dict.get("chapter", "Unknown"),
            difficulty=question_dict.get("difficulty", "medium"),
            question_text=question_dict.get("question_text", f"Question {question_number}"),
            question_type=question_type,
            options=options,
            correct_answer=question_dict.get("correct_answer"),
            marks_correct=4.0,  # Default, will be updated
            marks_incorrect=-1.0,  # Default, will be updated
            marks_unattempted=0.0,
            time_allocation=self.DEFAULT_TIME_PER_QUESTION.get(question_type, 120),
            tags=question_dict.get("tags", [])
        )
    
    def _apply_marking_scheme(
        self,
        question: Question,
        exam_pattern,
        subject: str
    ) -> Question:
        """
        Apply marking scheme to question based on pattern.
        
        Args:
            question: Question object
            exam_pattern: ExamPattern object
            subject: Subject name
            
        Returns:
            Updated Question object
        """
        # Get marking scheme from pattern
        marking = exam_pattern.marking_scheme
        
        # Determine marking based on question type and exam
        if exam_pattern.exam_name == "JEE Main":
            if question.question_type == QuestionType.NUMERICAL:
                # JEE Main numerical: no negative marking
                question.marks_correct = marking.correct_marks
                question.marks_incorrect = 0.0
                question.marks_unattempted = marking.unattempted_marks
                question.marking_scheme_type = MarkingSchemeType.NO_NEGATIVE
            else:
                # JEE Main MCQ: standard marking
                question.marks_correct = marking.correct_marks
                question.marks_incorrect = marking.incorrect_marks
                question.marks_unattempted = marking.unattempted_marks
                question.marking_scheme_type = MarkingSchemeType.STANDARD
        
        elif exam_pattern.exam_name == "JEE Advanced":
            if question.question_type == QuestionType.MULTIPLE_CORRECT:
                # JEE Advanced MSQ: partial marking
                question.marks_correct = marking.correct_marks
                question.marks_incorrect = marking.incorrect_marks
                question.marks_unattempted = marking.unattempted_marks
                question.marking_scheme_type = MarkingSchemeType.PARTIAL
            else:
                # Standard marking
                question.marks_correct = marking.correct_marks
                question.marks_incorrect = marking.incorrect_marks
                question.marks_unattempted = marking.unattempted_marks
                question.marking_scheme_type = MarkingSchemeType.STANDARD
        
        elif exam_pattern.exam_name == "NEET":
            # NEET: standard marking for all
            question.marks_correct = marking.correct_marks
            question.marks_incorrect = marking.incorrect_marks
            question.marks_unattempted = marking.unattempted_marks
            question.marking_scheme_type = MarkingSchemeType.STANDARD
        
        else:
            # Default marking
            question.marks_correct = marking.correct_marks
            question.marks_incorrect = marking.incorrect_marks
            question.marks_unattempted = marking.unattempted_marks
            question.marking_scheme_type = MarkingSchemeType.STANDARD
        
        return question
    
    def _add_section_instructions(
        self,
        section: Section,
        exam_pattern
    ) -> Section:
        """
        Add instructions to section.
        
        Args:
            section: Section object
            exam_pattern: ExamPattern object
            
        Returns:
            Updated Section object
        """
        # Get question types in section
        question_types = set(q.question_type for q in section.questions)
        
        # Build marking scheme explanation
        marking_parts = []
        for q in section.questions[:1]:  # Sample first question
            if q.marking_scheme_type == MarkingSchemeType.NO_NEGATIVE:
                marking_parts.append(
                    f"Numerical questions: +{q.marks_correct} for correct, "
                    f"0 for incorrect"
                )
            elif q.marking_scheme_type == MarkingSchemeType.PARTIAL:
                marking_parts.append(
                    f"Multiple correct questions: +{q.marks_correct} for fully correct, "
                    f"partial marks for partially correct, "
                    f"{q.marks_incorrect} for incorrect"
                )
            else:
                marking_parts.append(
                    f"+{q.marks_correct} for correct, "
                    f"{q.marks_incorrect} for incorrect, "
                    f"{q.marks_unattempted} for unattempted"
                )
        
        marking_scheme = "; ".join(marking_parts) if marking_parts else "Standard marking"
        
        # Build question types description
        type_descriptions = []
        if QuestionType.SINGLE_CORRECT in question_types:
            type_descriptions.append("Single Correct Answer (MCQ)")
        if QuestionType.MULTIPLE_CORRECT in question_types:
            type_descriptions.append("Multiple Correct Answers (MSQ)")
        if QuestionType.NUMERICAL in question_types:
            type_descriptions.append("Numerical Answer Type")
        if QuestionType.INTEGER in question_types:
            type_descriptions.append("Integer Answer Type")
        
        question_types_desc = ", ".join(type_descriptions) if type_descriptions else "Mixed"
        
        # Time management tips
        avg_time = section.total_marks / len(section.questions) * 30  # ~30 sec per mark
        time_management = (
            f"Suggested time: ~{int(avg_time)} seconds per question. "
            f"Attempt easier questions first."
        )
        
        # General instructions
        general_instructions = [
            f"This section contains {section.question_count} questions.",
            f"Total marks for this section: {section.total_marks}",
            "Read each question carefully before answering.",
            "Mark your answers clearly on the answer sheet."
        ]
        
        # Update section instructions
        section.instructions = SectionInstructions(
            marking_scheme=marking_scheme,
            question_types=question_types_desc,
            time_management=time_management,
            general_instructions=general_instructions
        )
        
        return section
    
    def _get_general_instructions(self, exam_pattern) -> List[str]:
        """Get general test instructions."""
        instructions = [
            f"Total Questions: {exam_pattern.total_questions}",
            f"Total Duration: {exam_pattern.duration_minutes} minutes",
            f"Maximum Marks: {exam_pattern.total_questions * exam_pattern.marking_scheme.correct_marks}",
            "",
            "General Instructions:",
            "1. Read all instructions carefully before starting the test.",
            "2. All questions are compulsory.",
            "3. Use of calculator is not permitted.",
            "4. Rough work should be done on the space provided in the test booklet.",
            "5. Mark your answers on the OMR sheet using HB pencil only.",
            "",
            f"Marking Scheme:",
            f"- Correct Answer: +{exam_pattern.marking_scheme.correct_marks} marks",
            f"- Incorrect Answer: {exam_pattern.marking_scheme.incorrect_marks} marks",
            f"- Unattempted: {exam_pattern.marking_scheme.unattempted_marks} marks"
        ]
        
        return instructions
    
    def _validate_pattern_compliance(
        self,
        patterned_test: PatternedTest,
        exam_pattern
    ) -> List[str]:
        """
        Validate that patterned test complies with exam pattern.
        
        Args:
            patterned_test: PatternedTest object
            exam_pattern: ExamPattern object
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Validate total questions
        if patterned_test.total_questions != exam_pattern.total_questions:
            warnings.append(
                f"Total questions mismatch: got {patterned_test.total_questions}, "
                f"expected {exam_pattern.total_questions}"
            )
        
        # Validate section counts
        for subject_pattern in exam_pattern.subjects:
            section = next(
                (s for s in patterned_test.sections if s.subject == subject_pattern.name),
                None
            )
            if not section:
                warnings.append(f"Missing section for subject: {subject_pattern.name}")
            elif section.question_count != subject_pattern.question_count:
                warnings.append(
                    f"Section {subject_pattern.name}: got {section.question_count} questions, "
                    f"expected {subject_pattern.question_count}"
                )
        
        # Validate marking scheme applied
        for section in patterned_test.sections:
            for question in section.questions:
                if question.marks_correct <= 0:
                    warnings.append(
                        f"Question {question.question_id} has invalid positive marks"
                    )
        
        if warnings:
            logger.warning(f"Pattern compliance warnings: {len(warnings)}")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("✓ Pattern compliance validated")
        
        return warnings
    
    def export_to_dict(self, patterned_test: PatternedTest) -> Dict:
        """
        Export patterned test to dictionary format.
        
        Args:
            patterned_test: PatternedTest object
            
        Returns:
            Dictionary representation
        """
        return patterned_test.dict()
