"""
Question Validator Service for Mentor AI Platform

This module provides comprehensive validation of generated exam questions,
checking structure, quality, and contextual accuracy. It ensures questions
meet educational standards and are fair, clear, and pedagogically sound.

Features:
- Structural validation (format, fields, correctness)
- Quality validation (clarity, plausibility, grammar)
- Contextual validation (syllabus alignment, difficulty)
- Common issue detection (trick questions, ambiguity)
- Quality scoring (0-100)
- Configurable validation rules

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.question_validator import QuestionValidator
    >>> from models.question_models import Question
    >>> 
    >>> validator = QuestionValidator()
    >>> question = Question(...)
    >>> result = validator.validate(question, syllabus_context="...")
    >>> 
    >>> if result.is_valid:
    ...     print(f"✓ Valid question (score: {result.quality_score})")
    >>> else:
    ...     print(f"✗ Invalid: {result.issues}")
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field

from models.question_models import Question, QuestionOptions

# Configure logging
logger = logging.getLogger(__name__)

# Validation thresholds
MIN_QUESTION_LENGTH = 20
MAX_QUESTION_LENGTH = 500
MIN_EXPLANATION_LENGTH = 30
MAX_EXPLANATION_LENGTH = 2000
MIN_OPTION_LENGTH = 1
MAX_OPTION_LENGTH = 200

# Quality scoring weights
WEIGHT_STRUCTURE = 40
WEIGHT_QUALITY = 40
WEIGHT_CONTEXT = 20

# Common placeholder patterns
PLACEHOLDER_PATTERNS = [
    r'\[insert.*?\]',
    r'\[.*?here\]',
    r'xxx+',
    r'placeholder',
    r'todo',
    r'\.\.\.',
]

# Common trick question indicators
TRICK_INDICATORS = [
    'all of the above',
    'none of the above',
    'both a and b',
    'all are correct',
    'all are incorrect',
]

# LaTeX pattern
LATEX_PATTERN = r'\$.*?\$|\\\(.*?\\\)|\\\[.*?\\\]'


@dataclass
class ValidationResult:
    """
    Result of question validation.
    
    Attributes:
        is_valid: Whether question passes validation
        issues: List of critical issues that make question invalid
        warnings: List of non-critical concerns
        quality_score: Overall quality score (0-100)
        category_scores: Scores by category (structure, quality, context)
    
    Example:
        >>> result = ValidationResult(
        ...     is_valid=True,
        ...     issues=[],
        ...     warnings=["Question could be clearer"],
        ...     quality_score=85,
        ...     category_scores={"structure": 100, "quality": 80, "context": 75}
        ... )
    """
    is_valid: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    quality_score: int = 0
    category_scores: Dict[str, int] = field(default_factory=dict)
    
    def __str__(self) -> str:
        """String representation of validation result."""
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        return f"{status} (Score: {self.quality_score}/100, Issues: {len(self.issues)}, Warnings: {len(self.warnings)})"


class QuestionValidator:
    """
    Validator for generated exam questions.
    
    This class performs comprehensive validation of questions including
    structural correctness, quality checks, and contextual alignment.
    
    Attributes:
        strict_mode: If True, warnings are treated as errors
        enable_grammar_check: If True, perform basic grammar checks
        enable_latex_check: If True, validate LaTeX formulas
        min_quality_score: Minimum quality score to pass (0-100)
    
    Example:
        >>> validator = QuestionValidator(
        ...     strict_mode=False,
        ...     min_quality_score=70
        ... )
        >>> result = validator.validate(question, context="...")
        >>> if result.is_valid:
        ...     print("Question is valid!")
    """
    
    def __init__(
        self,
        strict_mode: bool = False,
        enable_grammar_check: bool = True,
        enable_latex_check: bool = True,
        min_quality_score: int = 60
    ):
        """
        Initialize QuestionValidator.
        
        Args:
            strict_mode: Treat warnings as errors (default: False)
            enable_grammar_check: Perform grammar checks (default: True)
            enable_latex_check: Validate LaTeX formulas (default: True)
            min_quality_score: Minimum score to pass (default: 60)
        """
        self.strict_mode = strict_mode
        self.enable_grammar_check = enable_grammar_check
        self.enable_latex_check = enable_latex_check
        self.min_quality_score = min_quality_score
        
        logger.info(
            f"QuestionValidator initialized (strict={strict_mode}, "
            f"min_score={min_quality_score})"
        )
    
    def validate(
        self,
        question: Question,
        syllabus_context: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a question comprehensively.
        
        This is the main validation method that performs all checks:
        - Structural validation
        - Quality validation
        - Contextual validation (if context provided)
        - Quality scoring
        
        Args:
            question: Question object to validate
            syllabus_context: Optional syllabus context for validation
        
        Returns:
            ValidationResult with validation status and details
        
        Example:
            >>> validator = QuestionValidator()
            >>> question = Question(...)
            >>> result = validator.validate(question, "Calculus syllabus...")
            >>> print(result)
            ✓ VALID (Score: 85/100, Issues: 0, Warnings: 2)
        """
        logger.info(f"Validating question: {question.topic} ({question.difficulty})")
        
        issues: List[str] = []
        warnings: List[str] = []
        category_scores: Dict[str, int] = {}
        
        # 1. Structural validation
        structure_issues = self._validate_structure(question)
        issues.extend(structure_issues)
        category_scores["structure"] = self._calculate_category_score(
            structure_issues,
            []
        )
        
        # 2. Quality validation
        quality_issues, quality_warnings = self._validate_quality(question)
        issues.extend(quality_issues)
        warnings.extend(quality_warnings)
        category_scores["quality"] = self._calculate_category_score(
            quality_issues,
            quality_warnings
        )
        
        # 3. Contextual validation (if context provided)
        if syllabus_context:
            context_issues, context_warnings = self._validate_against_context(
                question,
                syllabus_context
            )
            issues.extend(context_issues)
            warnings.extend(context_warnings)
            category_scores["context"] = self._calculate_category_score(
                context_issues,
                context_warnings
            )
        else:
            category_scores["context"] = 100  # No context, assume valid
        
        # 4. Calculate overall quality score
        quality_score = self._calculate_quality_score(
            category_scores,
            len(issues),
            len(warnings)
        )
        
        # 5. Determine validity
        is_valid = (
            len(issues) == 0 and
            quality_score >= self.min_quality_score and
            (not self.strict_mode or len(warnings) == 0)
        )
        
        result = ValidationResult(
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            quality_score=quality_score,
            category_scores=category_scores
        )
        
        logger.info(f"Validation complete: {result}")
        
        return result
    
    def _validate_structure(self, question: Question) -> List[str]:
        """
        Validate question structure.
        
        Checks:
        - Question text length and presence
        - Options (A, B, C, D) presence and format
        - Correct answer validity
        - Explanation presence and length
        - Difficulty and topic presence
        - Field types and formats
        
        Args:
            question: Question to validate
        
        Returns:
            List of structural issues found
        """
        issues: List[str] = []
        
        # Validate question text
        if not question.question or len(question.question.strip()) < MIN_QUESTION_LENGTH:
            issues.append(
                f"Question text too short (min {MIN_QUESTION_LENGTH} chars)"
            )
        
        if len(question.question) > MAX_QUESTION_LENGTH:
            issues.append(
                f"Question text too long (max {MAX_QUESTION_LENGTH} chars)"
            )
        
        # Validate options (for MCQ types)
        if question.question_type in ["single_correct", "multiple_correct"]:
            if question.options is None:
                issues.append("Options are required for MCQ questions")
            else:
                # Check all options present
                if isinstance(question.options, QuestionOptions):
                    options_dict = {
                        "A": question.options.A,
                        "B": question.options.B,
                        "C": question.options.C,
                        "D": question.options.D
                    }
                elif isinstance(question.options, dict):
                    options_dict = question.options
                else:
                    issues.append("Options format is invalid")
                    options_dict = {}
                
                # Validate each option
                for key in ["A", "B", "C", "D"]:
                    if key not in options_dict:
                        issues.append(f"Missing option {key}")
                    else:
                        option_text = str(options_dict[key]).strip()
                        
                        if len(option_text) < MIN_OPTION_LENGTH:
                            issues.append(f"Option {key} is empty")
                        
                        if len(option_text) > MAX_OPTION_LENGTH:
                            issues.append(
                                f"Option {key} too long (max {MAX_OPTION_LENGTH} chars)"
                            )
        
        # Validate correct answer
        if question.question_type == "single_correct":
            if not isinstance(question.correct_answer, str):
                issues.append("Correct answer must be a string (A/B/C/D)")
            elif question.correct_answer.upper() not in ["A", "B", "C", "D"]:
                issues.append(
                    f"Invalid correct answer: {question.correct_answer} (must be A/B/C/D)"
                )
        
        elif question.question_type == "multiple_correct":
            if not isinstance(question.correct_answer, list):
                issues.append("Correct answer must be a list for multiple correct")
            elif len(question.correct_answer) == 0:
                issues.append("Multiple correct answer list is empty")
            else:
                for ans in question.correct_answer:
                    if ans.upper() not in ["A", "B", "C", "D"]:
                        issues.append(f"Invalid answer in list: {ans}")
        
        elif question.question_type == "numerical":
            if not isinstance(question.correct_answer, (int, float)):
                issues.append("Numerical answer must be a number")
            elif question.correct_answer < 0 or question.correct_answer > 9999:
                issues.append("Numerical answer must be between 0 and 9999")
        
        # Validate explanation
        if not question.explanation or len(question.explanation.strip()) < MIN_EXPLANATION_LENGTH:
            issues.append(
                f"Explanation too short (min {MIN_EXPLANATION_LENGTH} chars)"
            )
        
        if len(question.explanation) > MAX_EXPLANATION_LENGTH:
            issues.append(
                f"Explanation too long (max {MAX_EXPLANATION_LENGTH} chars)"
            )
        
        # Validate difficulty
        if question.difficulty not in ["easy", "medium", "hard"]:
            issues.append(f"Invalid difficulty: {question.difficulty}")
        
        # Validate topic
        if not question.topic or len(question.topic.strip()) < 3:
            issues.append("Topic is missing or too short")
        
        return issues
    
    def _validate_quality(self, question: Question) -> tuple[List[str], List[str]]:
        """
        Validate question quality.
        
        Checks:
        - Options are distinct (no duplicates)
        - No placeholder text
        - LaTeX formulas are valid
        - Basic grammar checks
        - Question clarity
        - Option plausibility
        
        Args:
            question: Question to validate
        
        Returns:
            Tuple of (issues, warnings)
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        # Check for duplicate options
        if question.options:
            if isinstance(question.options, QuestionOptions):
                option_values = [
                    question.options.A,
                    question.options.B,
                    question.options.C,
                    question.options.D
                ]
            elif isinstance(question.options, dict):
                option_values = list(question.options.values())
            else:
                option_values = []
            
            # Case-insensitive duplicate check
            lower_values = [str(v).lower().strip() for v in option_values]
            if len(lower_values) != len(set(lower_values)):
                issues.append("Options contain duplicates")
        
        # Check for placeholder text
        all_text = f"{question.question} {question.explanation}"
        if question.options:
            all_text += " " + " ".join(str(v) for v in option_values)
        
        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, all_text, re.IGNORECASE):
                issues.append(f"Contains placeholder text: {pattern}")
        
        # Check for LaTeX validation
        if self.enable_latex_check:
            latex_issues = self._validate_latex(all_text)
            issues.extend(latex_issues)
        
        # Check for trick question indicators
        question_lower = question.question.lower()
        if question.options:
            for option_val in option_values:
                option_lower = str(option_val).lower()
                for indicator in TRICK_INDICATORS:
                    if indicator in option_lower:
                        warnings.append(
                            f"Possible trick question: contains '{indicator}'"
                        )
        
        # Basic grammar checks
        if self.enable_grammar_check:
            grammar_warnings = self._check_grammar(question)
            warnings.extend(grammar_warnings)
        
        # Check question clarity
        clarity_warnings = self._check_clarity(question)
        warnings.extend(clarity_warnings)
        
        # Check option plausibility
        if question.options and question.question_type == "single_correct":
            plausibility_warnings = self._check_option_plausibility(question)
            warnings.extend(plausibility_warnings)
        
        return issues, warnings
    
    def _validate_against_context(
        self,
        question: Question,
        syllabus_context: str
    ) -> tuple[List[str], List[str]]:
        """
        Validate question against syllabus context.
        
        Checks:
        - Topic mentioned in context
        - Key concepts from question are in syllabus
        - Difficulty matches content complexity
        
        Args:
            question: Question to validate
            syllabus_context: Syllabus content
        
        Returns:
            Tuple of (issues, warnings)
        """
        issues: List[str] = []
        warnings: List[str] = []
        
        if not syllabus_context or len(syllabus_context.strip()) < 10:
            warnings.append("Insufficient syllabus context for validation")
            return issues, warnings
        
        context_lower = syllabus_context.lower()
        
        # Check if topic is mentioned in context
        topic_lower = question.topic.lower()
        
        # Extract key words from topic (remove common words)
        topic_words = set(
            word for word in re.findall(r'\w+', topic_lower)
            if len(word) > 3 and word not in ['with', 'and', 'the', 'for']
        )
        
        # Check if at least one key word from topic is in context
        if topic_words and not any(word in context_lower for word in topic_words):
            warnings.append(
                f"Topic '{question.topic}' may not be covered in provided syllabus"
            )
        
        # Check difficulty alignment (very basic heuristic)
        if question.difficulty == "easy":
            # Easy questions should use simple language
            if len(question.question.split()) > 40:
                warnings.append(
                    "Question marked as 'easy' but has complex wording"
                )
        
        elif question.difficulty == "hard":
            # Hard questions should be more complex
            if len(question.question.split()) < 15:
                warnings.append(
                    "Question marked as 'hard' but seems too simple"
                )
        
        return issues, warnings
    
    def _validate_latex(self, text: str) -> List[str]:
        """
        Validate LaTeX formulas in text.
        
        Args:
            text: Text containing potential LaTeX
        
        Returns:
            List of LaTeX-related issues
        """
        issues: List[str] = []
        
        # Find all LaTeX expressions
        latex_matches = re.findall(LATEX_PATTERN, text, re.DOTALL)
        
        for latex in latex_matches:
            # Check for unmatched braces
            if latex.count('{') != latex.count('}'):
                issues.append("Unmatched braces in LaTeX formula")
            
            if latex.count('[') != latex.count(']'):
                issues.append("Unmatched brackets in LaTeX formula")
            
            # Check for common LaTeX errors
            if '\\frac' in latex and ('{' not in latex or '}' not in latex):
                issues.append("Incomplete \\frac command in LaTeX")
            
            if latex.strip() in ['$', '$$', '\\(', '\\)', '\\[', '\\]']:
                issues.append("Empty LaTeX formula")
        
        return issues
    
    def _check_grammar(self, question: Question) -> List[str]:
        """
        Perform basic grammar checks.
        
        Args:
            question: Question to check
        
        Returns:
            List of grammar warnings
        """
        warnings: List[str] = []
        
        # Check if question ends with question mark
        if not question.question.rstrip().endswith('?'):
            warnings.append("Question text should end with a question mark")
        
        # Check for double spaces
        if '  ' in question.question:
            warnings.append("Question contains double spaces")
        
        # Check for proper capitalization
        if question.question and not question.question[0].isupper():
            warnings.append("Question should start with capital letter")
        
        # Check explanation starts with capital
        if question.explanation and not question.explanation[0].isupper():
            warnings.append("Explanation should start with capital letter")
        
        return warnings
    
    def _check_clarity(self, question: Question) -> List[str]:
        """
        Check question clarity and readability.
        
        Args:
            question: Question to check
        
        Returns:
            List of clarity warnings
        """
        warnings: List[str] = []
        
        # Check for very long sentences (> 50 words)
        words = question.question.split()
        if len(words) > 50:
            warnings.append(
                f"Question is very long ({len(words)} words) and may be unclear"
            )
        
        # Check for ambiguous language
        ambiguous_terms = [
            'may', 'might', 'possibly', 'probably', 'sometimes',
            'usually', 'generally', 'often'
        ]
        
        question_lower = question.question.lower()
        for term in ambiguous_terms:
            if f' {term} ' in f' {question_lower} ':
                warnings.append(
                    f"Question contains ambiguous term: '{term}'"
                )
        
        # Check for double negatives
        if 'not' in question_lower:
            negative_words = ['no', 'never', 'neither', 'none', 'nothing']
            for word in negative_words:
                if word in question_lower:
                    warnings.append(
                        "Question may contain double negative, which is confusing"
                    )
                    break
        
        return warnings
    
    def _check_option_plausibility(self, question: Question) -> List[str]:
        """
        Check if all options are plausible.
        
        Args:
            question: Question to check
        
        Returns:
            List of plausibility warnings
        """
        warnings: List[str] = []
        
        if not question.options:
            return warnings
        
        if isinstance(question.options, QuestionOptions):
            options = [
                question.options.A,
                question.options.B,
                question.options.C,
                question.options.D
            ]
        elif isinstance(question.options, dict):
            options = list(question.options.values())
        else:
            return warnings
        
        # Check for options that are too similar
        for i, opt1 in enumerate(options):
            for j, opt2 in enumerate(options[i+1:], i+1):
                # Calculate simple similarity
                opt1_lower = str(opt1).lower()
                opt2_lower = str(opt2).lower()
                
                # If options differ only by one word, they might be too similar
                words1 = set(opt1_lower.split())
                words2 = set(opt2_lower.split())
                
                if len(words1) > 1 and len(words2) > 1:
                    common_words = words1 & words2
                    if len(common_words) / max(len(words1), len(words2)) > 0.8:
                        warnings.append(
                            f"Options are very similar and may cause confusion"
                        )
                        break
        
        # Check for obviously wrong options (too short, nonsensical)
        for i, opt in enumerate(options):
            opt_str = str(opt).strip()
            
            # Option is just a single character or number
            if len(opt_str) <= 2 and opt_str.lower() not in ['a', 'b', 'c', 'd', 'e']:
                # This might be valid for some questions (e.g., "0", "1", "π")
                # but could indicate lazy option creation
                pass
        
        return warnings
    
    def _calculate_category_score(
        self,
        issues: List[str],
        warnings: List[str]
    ) -> int:
        """
        Calculate score for a validation category.
        
        Args:
            issues: List of issues (critical problems)
            warnings: List of warnings (minor problems)
        
        Returns:
            Score from 0-100
        """
        # Start with perfect score
        score = 100
        
        # Deduct points for issues and warnings
        score -= len(issues) * 20  # Each issue: -20 points
        score -= len(warnings) * 5  # Each warning: -5 points
        
        # Clamp to 0-100
        return max(0, min(100, score))
    
    def _calculate_quality_score(
        self,
        category_scores: Dict[str, int],
        num_issues: int,
        num_warnings: int
    ) -> int:
        """
        Calculate overall quality score.
        
        Uses weighted average of category scores with penalties
        for issues and warnings.
        
        Args:
            category_scores: Scores by category
            num_issues: Total number of critical issues
            num_warnings: Total number of warnings
        
        Returns:
            Overall quality score (0-100)
        """
        # Calculate weighted average
        structure_score = category_scores.get("structure", 100)
        quality_score = category_scores.get("quality", 100)
        context_score = category_scores.get("context", 100)
        
        weighted_score = (
            structure_score * WEIGHT_STRUCTURE / 100 +
            quality_score * WEIGHT_QUALITY / 100 +
            context_score * WEIGHT_CONTEXT / 100
        )
        
        # Apply penalties
        # Any critical issue results in max 50 score
        if num_issues > 0:
            weighted_score = min(weighted_score, 50)
        
        # Additional penalty for multiple issues/warnings
        penalty = num_issues * 10 + num_warnings * 2
        final_score = weighted_score - penalty
        
        return max(0, min(100, int(final_score)))


def validate_question(
    question: Question,
    syllabus_context: Optional[str] = None,
    min_quality_score: int = 60
) -> ValidationResult:
    """
    Convenience function to validate a question.
    
    Args:
        question: Question to validate
        syllabus_context: Optional syllabus context
        min_quality_score: Minimum quality score to pass
    
    Returns:
        ValidationResult
    
    Example:
        >>> result = validate_question(question, context="...", min_quality_score=70)
        >>> print(f"Valid: {result.is_valid}, Score: {result.quality_score}")
    """
    validator = QuestionValidator(min_quality_score=min_quality_score)
    return validator.validate(question, syllabus_context)


# Module initialization
logger.info("Question validator module loaded")
logger.info(f"Quality score weights: structure={WEIGHT_STRUCTURE}%, quality={WEIGHT_QUALITY}%, context={WEIGHT_CONTEXT}%")
