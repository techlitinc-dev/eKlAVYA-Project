"""
Score Calculator Service for Diagnostic Test System - Mentor AI Platform.

This service calculates test scores with different marking schemes for various
exam types (JEE Main, JEE Advanced, NEET). Supports negative marking, partial
marking, and comprehensive analytics.

Features:
- Multiple marking schemes (JEE Main, JEE Advanced, NEET)
- Subject-wise and topic-wise score calculation
- Accuracy and percentage calculations
- Detailed question-level analytics
- Comprehensive error handling

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> calculator = ScoreCalculator()
    >>> test_score = calculator.calculate_test_score(
    ...     test_id="test_123",
    ...     student_id="student_456",
    ...     exam_type="JEE_MAIN",
    ...     questions=questions_list,
    ...     student_answers=answers_dict
    ... )
    >>> print(f"Total Score: {test_score.total_marks_obtained}/{test_score.total_max_marks}")
    >>> print(f"Percentage: {test_score.percentage}%")
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from models.score_models import (
    TestScore,
    SubjectScore,
    TopicScore,
    QuestionScore,
    MarkingScheme
)
from models.diagnostic_test_models import Question, QuestionType


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScoreCalculator:
    """
    Calculate test scores with different marking schemes.
    
    This class handles score calculation for different exam types with their
    respective marking schemes, including negative marking and partial marking.
    
    Attributes:
        marking_schemes: Dictionary of marking schemes by exam type and question type
    
    Example:
        >>> calculator = ScoreCalculator()
        >>> score = calculator.calculate_test_score(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     exam_type="JEE_MAIN",
        ...     questions=questions,
        ...     student_answers={"1": "B", "2": "A"}
        ... )
    """
    
    def __init__(self):
        """Initialize score calculator with marking schemes."""
        self.marking_schemes = self._initialize_marking_schemes()
    
    def _initialize_marking_schemes(self) -> Dict[str, Dict[str, MarkingScheme]]:
        """
        Initialize marking schemes for different exam types.
        
        Returns:
            Dict[str, Dict[str, MarkingScheme]]: Nested dict of marking schemes
        
        Marking Schemes:
            JEE Main:
                - Single Correct MCQ: +4 / -1
                - Numerical: +4 / 0
            
            JEE Advanced:
                - Single Correct MCQ: +3 / -1
                - Multiple Correct MCQ: +4 (full), +1 (partial), -2 (wrong)
                - Numerical: +4 / 0
                - Matrix Match: +3 (full), +1 (partial), 0 (wrong)
            
            NEET:
                - Single Correct MCQ: +4 / -1
        """
        return {
            "JEE_MAIN": {
                "single_correct": MarkingScheme(
                    correct_marks=4,
                    incorrect_marks=-1,
                    partial_marks=0,
                    unattempted_marks=0
                ),
                "numerical": MarkingScheme(
                    correct_marks=4,
                    incorrect_marks=0,
                    partial_marks=0,
                    unattempted_marks=0
                ),
                "integer": MarkingScheme(
                    correct_marks=4,
                    incorrect_marks=0,
                    partial_marks=0,
                    unattempted_marks=0
                )
            },
            "JEE_ADVANCED": {
                "single_correct": MarkingScheme(
                    correct_marks=3,
                    incorrect_marks=-1,
                    partial_marks=0,
                    unattempted_marks=0
                ),
                "multiple_correct": MarkingScheme(
                    correct_marks=4,
                    incorrect_marks=-2,
                    partial_marks=1,
                    unattempted_marks=0
                ),
                "numerical": MarkingScheme(
                    correct_marks=4,
                    incorrect_marks=0,
                    partial_marks=0,
                    unattempted_marks=0
                ),
                "matrix_match": MarkingScheme(
                    correct_marks=3,
                    incorrect_marks=0,
                    partial_marks=1,
                    unattempted_marks=0
                )
            },
            "NEET": {
                "single_correct": MarkingScheme(
                    correct_marks=4,
                    incorrect_marks=-1,
                    partial_marks=0,
                    unattempted_marks=0
                )
            }
        }
    
    def calculate_test_score(
        self,
        test_id: str,
        student_id: str,
        exam_type: str,
        questions: List[Question],
        student_answers: Dict[int, str],
        time_taken: Optional[int] = None,
        submission_time: Optional[datetime] = None
    ) -> TestScore:
        """
        Calculate complete test score with all analytics.
        
        Args:
            test_id: Unique test identifier
            student_id: Student identifier
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            questions: List of Question objects
            student_answers: Dict mapping question_number to student answer
            time_taken: Total time taken in seconds (optional)
            submission_time: Submission timestamp (optional)
        
        Returns:
            TestScore: Complete test score with analytics
        
        Raises:
            ValueError: If exam_type is invalid or questions list is empty
            KeyError: If marking scheme not found for question type
        
        Example:
            >>> questions = [q1, q2, q3]  # List of Question objects
            >>> answers = {1: "B", 2: "A", 3: "42"}
            >>> score = calculator.calculate_test_score(
            ...     test_id="test_123",
            ...     student_id="student_456",
            ...     exam_type="JEE_MAIN",
            ...     questions=questions,
            ...     student_answers=answers
            ... )
        """
        # Validate inputs
        if not questions:
            raise ValueError("Questions list cannot be empty")
        
        exam_type_upper = exam_type.upper()
        if exam_type_upper not in self.marking_schemes:
            raise ValueError(
                f"Invalid exam type: {exam_type}. "
                f"Must be one of {list(self.marking_schemes.keys())}"
            )
        
        logger.info(
            f"Calculating score for test {test_id}, "
            f"student {student_id}, exam {exam_type_upper}"
        )
        
        # Calculate question-level scores
        question_scores = []
        for question in questions:
            try:
                q_score = self._calculate_question_score(
                    question=question,
                    student_answer=student_answers.get(question.question_number),
                    exam_type=exam_type_upper
                )
                question_scores.append(q_score)
            except Exception as e:
                logger.error(
                    f"Error calculating score for question {question.question_number}: {e}"
                )
                # Add zero score for error cases
                question_scores.append(
                    self._create_zero_question_score(question)
                )
        
        # Calculate subject-wise scores
        subject_scores = self._calculate_subject_scores(question_scores)
        
        # Calculate overall statistics
        total_questions = len(questions)
        attempted = sum(1 for qs in question_scores if qs.student_answer is not None)
        correct = sum(1 for qs in question_scores if qs.is_correct and not qs.is_partial)
        incorrect = sum(
            1 for qs in question_scores 
            if not qs.is_correct and qs.student_answer is not None and not qs.is_partial
        )
        partial = sum(1 for qs in question_scores if qs.is_partial)
        unattempted = total_questions - attempted
        
        total_marks_obtained = sum(qs.marks_obtained for qs in question_scores)
        total_max_marks = sum(qs.max_marks for qs in question_scores)
        
        # Calculate percentage
        percentage = (total_marks_obtained / total_max_marks * 100) if total_max_marks > 0 else 0.0
        
        # Calculate accuracy (only for attempted questions)
        if attempted > 0:
            accuracy = ((correct + (partial * 0.5)) / attempted) * 100
        else:
            accuracy = 0.0
        
        # Create TestScore object
        test_score = TestScore(
            test_id=test_id,
            student_id=student_id,
            exam_type=exam_type_upper,
            total_questions=total_questions,
            attempted=attempted,
            correct=correct,
            incorrect=incorrect,
            partial=partial,
            unattempted=unattempted,
            total_marks_obtained=total_marks_obtained,
            total_max_marks=total_max_marks,
            percentage=round(percentage, 2),
            accuracy=round(accuracy, 2),
            subject_scores=subject_scores,
            question_scores=question_scores,
            submission_time=submission_time or datetime.utcnow(),
            time_taken=time_taken
        )
        
        logger.info(
            f"Score calculation complete. Total: {total_marks_obtained}/{total_max_marks} "
            f"({percentage:.2f}%), Accuracy: {accuracy:.2f}%"
        )
        
        return test_score
    
    def _calculate_question_score(
        self,
        question: Question,
        student_answer: Optional[str],
        exam_type: str
    ) -> QuestionScore:
        """
        Calculate score for a single question.
        
        Args:
            question: Question object
            student_answer: Student's answer (None if unattempted)
            exam_type: Type of exam
        
        Returns:
            QuestionScore: Score details for the question
        
        Raises:
            KeyError: If marking scheme not found for question type
        """
        question_type = question.question_type
        
        # Get marking scheme
        if question_type not in self.marking_schemes[exam_type]:
            logger.warning(
                f"No marking scheme found for {exam_type}/{question_type}. "
                f"Using default scheme."
            )
            # Use default scheme
            scheme = MarkingScheme(
                correct_marks=4,
                incorrect_marks=-1,
                partial_marks=0,
                unattempted_marks=0
            )
        else:
            scheme = self.marking_schemes[exam_type][question_type]
        
        # Handle unattempted
        if student_answer is None or student_answer == "" or student_answer.strip() == "":
            return QuestionScore(
                question_id=question.question_id,
                question_number=question.question_number,
                question_type=question_type,
                subject=question.subject,
                topic=question.topic,
                difficulty=question.difficulty,
                student_answer=None,
                correct_answer=str(question.correct_answer),
                is_correct=False,
                is_partial=False,
                marks_obtained=scheme.unattempted_marks,
                max_marks=question.marks
            )
        
        # Evaluate answer
        is_correct, is_partial = self._evaluate_answer(
            question=question,
            student_answer=student_answer,
            question_type=question_type
        )
        
        # Calculate marks
        if is_correct and not is_partial:
            marks = scheme.correct_marks
        elif is_partial:
            marks = scheme.partial_marks
        else:
            marks = scheme.incorrect_marks
        
        return QuestionScore(
            question_id=question.question_id,
            question_number=question.question_number,
            question_type=question_type,
            subject=question.subject,
            topic=question.topic,
            difficulty=question.difficulty,
            student_answer=student_answer,
            correct_answer=str(question.correct_answer),
            is_correct=is_correct,
            is_partial=is_partial,
            marks_obtained=marks,
            max_marks=question.marks
        )
    
    def _evaluate_answer(
        self,
        question: Question,
        student_answer: str,
        question_type: str
    ) -> Tuple[bool, bool]:
        """
        Evaluate if student answer is correct or partially correct.
        
        Args:
            question: Question object
            student_answer: Student's answer
            question_type: Type of question
        
        Returns:
            Tuple[bool, bool]: (is_correct, is_partial)
        
        Example:
            >>> is_correct, is_partial = self._evaluate_answer(
            ...     question=q,
            ...     student_answer="B",
            ...     question_type="single_correct"
            ... )
        """
        correct_answer = question.correct_answer
        
        # Handle different question types
        if question_type in ["single_correct", "numerical", "integer"]:
            # Exact match required
            return (
                self._normalize_answer(student_answer) == 
                self._normalize_answer(str(correct_answer)),
                False
            )
        
        elif question_type == "multiple_correct":
            # For multiple correct, check if it's fully or partially correct
            if isinstance(correct_answer, list):
                correct_set = set(ans.upper().strip() for ans in correct_answer)
            else:
                correct_set = set([str(correct_answer).upper().strip()])
            
            # Parse student answer (could be comma-separated or list)
            if isinstance(student_answer, list):
                student_set = set(ans.upper().strip() for ans in student_answer)
            else:
                student_set = set(
                    ans.upper().strip() 
                    for ans in student_answer.replace(" ", "").split(",")
                    if ans.strip()
                )
            
            # Check if fully correct
            if student_set == correct_set:
                return (True, False)
            
            # Check if partially correct (some correct, no incorrect)
            if student_set.issubset(correct_set) and len(student_set) > 0:
                return (False, True)
            
            # Incorrect (has wrong answers or no correct answers)
            return (False, False)
        
        else:
            # Default: exact match
            return (
                self._normalize_answer(student_answer) == 
                self._normalize_answer(str(correct_answer)),
                False
            )
    
    def _normalize_answer(self, answer: str) -> str:
        """
        Normalize answer for comparison.
        
        Args:
            answer: Answer string to normalize
        
        Returns:
            str: Normalized answer (uppercase, stripped, no spaces)
        
        Example:
            >>> self._normalize_answer("  b ")
            'B'
            >>> self._normalize_answer("42.5")
            '42.5'
        """
        if answer is None:
            return ""
        return str(answer).upper().strip().replace(" ", "")
    
    def _calculate_subject_scores(
        self,
        question_scores: List[QuestionScore]
    ) -> Dict[str, SubjectScore]:
        """
        Calculate subject-wise scores from question scores.
        
        Args:
            question_scores: List of QuestionScore objects
        
        Returns:
            Dict[str, SubjectScore]: Subject-wise scores
        
        Example:
            >>> subject_scores = self._calculate_subject_scores(question_scores)
            >>> physics_score = subject_scores["Physics"]
        """
        subject_data: Dict[str, List[QuestionScore]] = {}
        
        # Group questions by subject
        for qs in question_scores:
            if qs.subject not in subject_data:
                subject_data[qs.subject] = []
            subject_data[qs.subject].append(qs)
        
        # Calculate scores for each subject
        subject_scores = {}
        for subject, qs_list in subject_data.items():
            # Calculate topic scores
            topic_scores = self._calculate_topic_scores(qs_list)
            
            # Calculate subject statistics
            total_questions = len(qs_list)
            attempted = sum(1 for qs in qs_list if qs.student_answer is not None)
            correct = sum(1 for qs in qs_list if qs.is_correct and not qs.is_partial)
            incorrect = sum(
                1 for qs in qs_list 
                if not qs.is_correct and qs.student_answer is not None and not qs.is_partial
            )
            partial = sum(1 for qs in qs_list if qs.is_partial)
            unattempted = total_questions - attempted
            
            marks_obtained = sum(qs.marks_obtained for qs in qs_list)
            max_marks = sum(qs.max_marks for qs in qs_list)
            
            # Calculate accuracy
            if attempted > 0:
                accuracy = ((correct + (partial * 0.5)) / attempted) * 100
            else:
                accuracy = 0.0
            
            subject_scores[subject] = SubjectScore(
                subject=subject,
                total_questions=total_questions,
                attempted=attempted,
                correct=correct,
                incorrect=incorrect,
                partial=partial,
                unattempted=unattempted,
                marks_obtained=marks_obtained,
                max_marks=max_marks,
                accuracy=round(accuracy, 2),
                topic_scores=topic_scores
            )
        
        return subject_scores
    
    def _calculate_topic_scores(
        self,
        question_scores: List[QuestionScore]
    ) -> Dict[str, TopicScore]:
        """
        Calculate topic-wise scores from question scores.
        
        Args:
            question_scores: List of QuestionScore objects for a subject
        
        Returns:
            Dict[str, TopicScore]: Topic-wise scores
        
        Example:
            >>> topic_scores = self._calculate_topic_scores(physics_questions)
            >>> mechanics_score = topic_scores["Mechanics"]
        """
        topic_data: Dict[str, List[QuestionScore]] = {}
        
        # Group questions by topic
        for qs in question_scores:
            if qs.topic not in topic_data:
                topic_data[qs.topic] = []
            topic_data[qs.topic].append(qs)
        
        # Calculate scores for each topic
        topic_scores = {}
        for topic, qs_list in topic_data.items():
            total_questions = len(qs_list)
            attempted = sum(1 for qs in qs_list if qs.student_answer is not None)
            correct = sum(1 for qs in qs_list if qs.is_correct and not qs.is_partial)
            incorrect = sum(
                1 for qs in qs_list 
                if not qs.is_correct and qs.student_answer is not None and not qs.is_partial
            )
            partial = sum(1 for qs in qs_list if qs.is_partial)
            unattempted = total_questions - attempted
            
            marks_obtained = sum(qs.marks_obtained for qs in qs_list)
            max_marks = sum(qs.max_marks for qs in qs_list)
            
            # Calculate accuracy
            if attempted > 0:
                accuracy = ((correct + (partial * 0.5)) / attempted) * 100
            else:
                accuracy = 0.0
            
            # Get subject from first question
            subject = qs_list[0].subject if qs_list else ""
            
            topic_scores[topic] = TopicScore(
                topic=topic,
                subject=subject,
                total_questions=total_questions,
                attempted=attempted,
                correct=correct,
                incorrect=incorrect,
                partial=partial,
                unattempted=unattempted,
                marks_obtained=marks_obtained,
                max_marks=max_marks,
                accuracy=round(accuracy, 2)
            )
        
        return topic_scores
    
    def _create_zero_question_score(self, question: Question) -> QuestionScore:
        """
        Create a zero score for a question (used in error cases).
        
        Args:
            question: Question object
        
        Returns:
            QuestionScore: Question score with zero marks
        """
        return QuestionScore(
            question_id=question.question_id,
            question_number=question.question_number,
            question_type=question.question_type,
            subject=question.subject,
            topic=question.topic,
            difficulty=question.difficulty,
            student_answer=None,
            correct_answer=str(question.correct_answer),
            is_correct=False,
            is_partial=False,
            marks_obtained=0,
            max_marks=question.marks
        )
    
    def get_marking_scheme(
        self,
        exam_type: str,
        question_type: str
    ) -> Optional[MarkingScheme]:
        """
        Get marking scheme for a specific exam and question type.
        
        Args:
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            question_type: Type of question
        
        Returns:
            Optional[MarkingScheme]: Marking scheme or None if not found
        
        Example:
            >>> scheme = calculator.get_marking_scheme("JEE_MAIN", "single_correct")
            >>> print(f"Correct: +{scheme.correct_marks}, Incorrect: {scheme.incorrect_marks}")
        """
        exam_type_upper = exam_type.upper()
        
        if exam_type_upper not in self.marking_schemes:
            logger.warning(f"Invalid exam type: {exam_type}")
            return None
        
        if question_type not in self.marking_schemes[exam_type_upper]:
            logger.warning(
                f"No marking scheme for {exam_type_upper}/{question_type}"
            )
            return None
        
        return self.marking_schemes[exam_type_upper][question_type]
    
    def calculate_percentile(
        self,
        score: int,
        all_scores: List[int]
    ) -> float:
        """
        Calculate percentile rank for a score.
        
        Args:
            score: Student's score
            all_scores: List of all scores in the cohort
        
        Returns:
            float: Percentile rank (0-100)
        
        Example:
            >>> percentile = calculator.calculate_percentile(
            ...     score=570,
            ...     all_scores=[450, 500, 550, 570, 600, 650]
            ... )
            >>> print(f"Percentile: {percentile}%")
        """
        if not all_scores:
            return 0.0
        
        # Count scores below the given score
        below = sum(1 for s in all_scores if s < score)
        
        # Calculate percentile
        percentile = (below / len(all_scores)) * 100
        
        return round(percentile, 2)


# Example usage and testing
if __name__ == "__main__":
    """
    Example usage of ScoreCalculator.
    """
    from models.diagnostic_test_models import Question, QuestionType, Difficulty
    
    # Create sample questions
    questions = [
        Question(
            question_id="q_001",
            question_number=1,
            question_text="What is Newton's first law?",
            options={"A": "Law of inertia", "B": "F=ma", "C": "Action-reaction", "D": "Gravity"},
            correct_answer="A",
            question_type=QuestionType.SINGLE_CORRECT,
            marks=4,
            negative_marks=-1,
            difficulty=Difficulty.EASY,
            topic="Mechanics",
            subject="Physics"
        ),
        Question(
            question_id="q_002",
            question_number=2,
            question_text="Calculate 2+2",
            options={},
            correct_answer="4",
            question_type=QuestionType.NUMERICAL,
            marks=4,
            negative_marks=0,
            difficulty=Difficulty.EASY,
            topic="Arithmetic",
            subject="Mathematics"
        )
    ]
    
    # Student answers
    student_answers = {
        1: "A",  # Correct
        2: "5"   # Incorrect
    }
    
    # Calculate score
    calculator = ScoreCalculator()
    test_score = calculator.calculate_test_score(
        test_id="test_123",
        student_id="student_456",
        exam_type="JEE_MAIN",
        questions=questions,
        student_answers=student_answers
    )
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Test Score Results")
    print(f"{'='*60}")
    print(f"Total Score: {test_score.total_marks_obtained}/{test_score.total_max_marks}")
    print(f"Percentage: {test_score.percentage}%")
    print(f"Accuracy: {test_score.accuracy}%")
    print(f"Attempted: {test_score.attempted}/{test_score.total_questions}")
    print(f"Correct: {test_score.correct}")
    print(f"Incorrect: {test_score.incorrect}")
    print(f"Unattempted: {test_score.unattempted}")
    print(f"{'='*60}\n")
