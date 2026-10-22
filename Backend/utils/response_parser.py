"""
Response Parser for Gemini LLM Outputs

This module provides parsing and validation of LLM-generated question responses
in the Mentor AI EdTech Platform. It handles various response formats, extracts
JSON content, and validates questions against strict requirements.

Features:
- Parse JSON from various formats (pure JSON, markdown blocks, mixed text)
- Extract JSON using regex patterns
- Validate questions with comprehensive field checking
- Clean and normalize text content
- Handle errors gracefully with detailed logging
- Return statistics about parsing results

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from utils.response_parser import ResponseParser
    >>> from utils.gemini_client import GeminiClient
    >>> 
    >>> # Generate questions with Gemini
    >>> client = GeminiClient()
    >>> response = client.generate_content(prompt)
    >>> 
    >>> # Parse response
    >>> parser = ResponseParser()
    >>> questions, stats = parser.parse_response(response)
    >>> 
    >>> print(f"Valid questions: {stats['valid']}/{stats['total']}")
    >>> for question in questions:
    ...     print(f"- {question.topic}: {question.difficulty}")
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from pydantic import ValidationError

from models.question_models import Question, QuestionOptions

# Configure logging
logger = logging.getLogger(__name__)


class ResponseParserError(Exception):
    """Base exception for response parser errors."""
    pass


class ResponseParser:
    """
    Parser for Gemini LLM question generation responses.
    
    This class handles parsing and validation of LLM responses that contain
    generated questions. It can handle various response formats including
    pure JSON, markdown-wrapped JSON, and JSON mixed with text.
    
    Attributes:
        strict_mode: If True, raises exceptions on parsing errors (default: False)
        log_invalid: If True, logs details of invalid questions (default: True)
    
    Example:
        >>> parser = ResponseParser(strict_mode=False, log_invalid=True)
        >>> questions, stats = parser.parse_response(llm_response)
        >>> print(f"Parsed {stats['valid']} valid questions")
    """
    
    def __init__(self, strict_mode: bool = False, log_invalid: bool = True):
        """
        Initialize ResponseParser.
        
        Args:
            strict_mode: If True, raises exceptions on parsing errors (default: False)
            log_invalid: If True, logs details of invalid questions (default: True)
        """
        self.strict_mode = strict_mode
        self.log_invalid = log_invalid
        logger.info(f"ResponseParser initialized (strict_mode={strict_mode}, log_invalid={log_invalid})")
    
    def parse_response(
        self,
        response_text: str,
        expected_count: Optional[int] = None
    ) -> Tuple[List[Question], Dict[str, int]]:
        """
        Parse LLM response and extract valid questions.
        
        This is the main entry point for parsing. It handles various response
        formats, extracts JSON, validates questions, and returns statistics.
        
        Args:
            response_text: Raw response text from LLM
            expected_count: Expected number of questions (optional, for validation)
        
        Returns:
            Tuple containing:
            - List of validated Question objects
            - Statistics dict with keys: total, valid, invalid
        
        Raises:
            ResponseParserError: If strict_mode=True and parsing fails
        
        Example:
            >>> parser = ResponseParser()
            >>> questions, stats = parser.parse_response(
            ...     response_text='[{"question": "...", "options": {...}}]',
            ...     expected_count=5
            ... )
            >>> print(f"Got {len(questions)} questions")
        """
        logger.info("Starting response parsing")
        
        # Validate input
        if not response_text or not response_text.strip():
            logger.error("Empty response text provided")
            if self.strict_mode:
                raise ResponseParserError("Response text cannot be empty")
            return [], {"total": 0, "valid": 0, "invalid": 0}
        
        try:
            # Step 1: Extract JSON from response
            json_text = self._extract_json(response_text)
            logger.info(f"Extracted JSON text: {json_text[:200]}...")
            if not json_text:
                logger.error("Failed to extract JSON from response")
                if self.strict_mode:
                    raise ResponseParserError("Could not extract JSON from response")
                return [], {"total": 0, "valid": 0, "invalid": 0}
            
            # Step 1.5: Fix common LaTeX JSON issues
            json_text = self._fix_latex_json_issues(json_text)
            
            # Step 2: Parse JSON
            try:
                data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                # Try again with more aggressive fixing
                json_text = self._fix_latex_json_issues(json_text, aggressive=True)
                try:
                    data = json.loads(json_text)
                    logger.info("JSON parsing succeeded with aggressive fixing")
                except json.JSONDecodeError as e2:
                    logger.error(f"Aggressive JSON parsing also failed: {e2}")
                    if self.strict_mode:
                        raise ResponseParserError(f"Invalid JSON format: {e2}")
                    return [], {"total": 0, "valid": 0, "invalid": 0}
            
            # Step 3: Ensure data is a list
            if not isinstance(data, list):
                logger.error(f"Expected JSON array, got {type(data).__name__}")
                if self.strict_mode:
                    raise ResponseParserError("Response must be a JSON array")
                return [], {"total": 0, "valid": 0, "invalid": 0}
            
            total_count = len(data)
            logger.info(f"Parsed JSON array with {total_count} items")
            
            # Step 4: Validate each question
            valid_questions = []
            invalid_count = 0
            
            for idx, item in enumerate(data):
                logger.debug(f"Validating question {idx + 1}/{total_count}")
                
                validated_question = self._validate_question(item, idx + 1)
                
                if validated_question:
                    valid_questions.append(validated_question)
                else:
                    invalid_count += 1
            
            # Step 5: Check expected count
            if expected_count is not None and len(valid_questions) != expected_count:
                logger.warning(
                    f"Expected {expected_count} questions, got {len(valid_questions)} valid questions"
                )
            
            # Step 6: Compile statistics
            stats = {
                "total": total_count,
                "valid": len(valid_questions),
                "invalid": invalid_count
            }
            
            logger.info(
                f"Parsing complete: {stats['valid']} valid, {stats['invalid']} invalid "
                f"out of {stats['total']} total"
            )
            
            return valid_questions, stats
        
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}")
            logger.exception("Full traceback:")
            
            if self.strict_mode:
                raise ResponseParserError(f"Failed to parse response: {e}")
            
            return [], {"total": 0, "valid": 0, "invalid": 0}
    
    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract JSON content from various text formats.
        
        Handles:
        1. Pure JSON (array or object)
        2. JSON wrapped in markdown code blocks (```json...```)
        3. JSON with text before/after
        4. Malformed responses with partial JSON
        
        Args:
            text: Raw text containing JSON
        
        Returns:
            Extracted JSON string, or None if extraction fails
        
        Example:
            >>> parser = ResponseParser()
            >>> json_str = parser._extract_json('```json\\n[{"q": "test"}]\\n```')
            >>> print(json_str)
            '[{"q": "test"}]'
        """
        if not text:
            return None
        
        text = text.strip()
        
        # Method 1: Check for markdown code blocks
        markdown_patterns = [
            r'```json\s*\n(.*?)\n```',  # ```json\n...\n```
            r'```\s*\n(.*?)\n```',      # ```\n...\n```
            r'```json(.*?)```',          # ```json...```
            r'```(.*?)```'               # ```...```
        ]
        
        # Method 0: Check for JSON array first (most common for question generation)
        array_pattern = r'\[\s*\{.*?\}\s*\]'
        array_match = re.search(array_pattern, text, re.DOTALL)
        if array_match:
            extracted = array_match.group(0)
            logger.debug("Extracted JSON array using regex pattern")
            return extracted
        
        # Method 1: Check for JSON object first (before markdown blocks)
        object_pattern = r'\{[^{}]*\}'
        object_match = re.search(object_pattern, text, re.DOTALL)
        if object_match:
            # Extract the complete JSON object
            json_start = object_match.start()
            json_end = object_match.end()
            # Find the matching closing brace
            brace_count = 0
            for i in range(json_start, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_end = i + 1
                        break
            
            if json_end > json_start:
                json_text = text[json_start:json_end]
                logger.debug(f"Extracted JSON object (before markdown): {json_text[:200]}...")
                return json_text
        
        # Method 2: Try to find JSON array pattern
        # Look for content between [ and ]
        array_pattern = r'\[\s*\{.*?\}\s*\]'
        match = re.search(array_pattern, text, re.DOTALL)
        if match:
            extracted = match.group(0)
            logger.debug("Extracted JSON array using regex pattern")
            return extracted
        
        # Method 3: Try to find JSON object pattern
        object_pattern = r'\{\s*".*?"\s*:.*?\}'
        match = re.search(object_pattern, text, re.DOTALL)
        if match:
            extracted = match.group(0)
            logger.debug("Extracted JSON object using regex pattern")
            # Wrap single object in array
            return f"[{extracted}]"
        
        # Method 4: Check if entire text is valid JSON
        try:
            json.loads(text)
            logger.debug("Entire text is valid JSON")
            return text
        except json.JSONDecodeError:
            pass
        
        # Method 5: Try to extract from specific line patterns
        # Sometimes LLMs add explanatory text before/after JSON
        lines = text.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        bracket_count = 0
        
        for line in lines:
            # Check if this line starts JSON
            if not in_json and (line.strip().startswith('[') or line.strip().startswith('{')):
                in_json = True
            
            if in_json:
                json_lines.append(line)
                # Count braces to detect end
                brace_count += line.count('{') - line.count('}')
                bracket_count += line.count('[') - line.count(']')
                
                # Check if JSON is complete
                if brace_count == 0 and bracket_count == 0 and len(json_lines) > 0:
                    potential_json = '\n'.join(json_lines)
                    try:
                        json.loads(potential_json)
                        logger.debug("Extracted JSON by line-by-line parsing")
                        return potential_json
                    except json.JSONDecodeError:
                        pass
        
        logger.warning("Failed to extract JSON from text")
        return None
    
    def _validate_question(
        self,
        data: Dict[str, Any],
        question_number: int = 0
    ) -> Optional[Question]:
        """
        Validate a single question dictionary.
        
        Performs comprehensive validation:
        1. Check required fields exist
        2. Validate field types
        3. Clean and normalize text
        4. Validate options are distinct
        5. Create Question object with Pydantic validation
        
        Args:
            data: Dictionary containing question data
            question_number: Question number for logging (optional)
        
        Returns:
            Validated Question object, or None if invalid
        
        Example:
            >>> parser = ResponseParser()
            >>> question_dict = {
            ...     "question": "What is 2+2?",
            ...     "options": {"A": "3", "B": "4", "C": "5", "D": "6"},
            ...     "correct_answer": "B",
            ...     "explanation": "Basic addition: 2+2=4",
            ...     "difficulty": "easy",
            ...     "topic": "Arithmetic"
            ... }
            >>> question = parser._validate_question(question_dict)
            >>> print(question.correct_answer)
            'B'
        """
        try:
            # Check if data is a dictionary
            if not isinstance(data, dict):
                if self.log_invalid:
                    logger.warning(f"Question {question_number}: Not a dictionary, got {type(data).__name__}")
                return None
            
            # Check required fields
            required_fields = ["question", "correct_answer", "explanation", "difficulty", "topic"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                if self.log_invalid:
                    logger.warning(
                        f"Question {question_number}: Missing required fields: {', '.join(missing_fields)}"
                    )
                return None
            
            # Clean text fields
            cleaned_data = {}
            
            # Clean question text
            cleaned_data["question"] = self._clean_text(data["question"])
            if not cleaned_data["question"]:
                if self.log_invalid:
                    logger.warning(f"Question {question_number}: Question text is empty after cleaning")
                return None
            
            # Clean explanation
            cleaned_data["explanation"] = self._clean_text(data["explanation"])
            if not cleaned_data["explanation"]:
                if self.log_invalid:
                    logger.warning(f"Question {question_number}: Explanation is empty after cleaning")
                return None
            
            # Clean topic
            cleaned_data["topic"] = self._clean_text(data["topic"])
            if not cleaned_data["topic"]:
                if self.log_invalid:
                    logger.warning(f"Question {question_number}: Topic is empty after cleaning")
                return None
            
            # Validate difficulty
            cleaned_data["difficulty"] = data["difficulty"].strip().lower()
            if cleaned_data["difficulty"] not in ["easy", "medium", "hard"]:
                if self.log_invalid:
                    logger.warning(
                        f"Question {question_number}: Invalid difficulty '{data['difficulty']}', "
                        "must be easy/medium/hard"
                    )
                return None
            
            # Handle options (if present)
            if "options" in data:
                options = data["options"]
                
                if isinstance(options, dict):
                    # Clean option values
                    cleaned_options = {}
                    for key in ["A", "B", "C", "D"]:
                        if key not in options:
                            if self.log_invalid:
                                logger.warning(f"Question {question_number}: Missing option {key}")
                            return None
                        
                        cleaned_value = self._clean_text(str(options[key]))
                        if not cleaned_value:
                            if self.log_invalid:
                                logger.warning(f"Question {question_number}: Option {key} is empty")
                            return None
                        
                        cleaned_options[key] = cleaned_value
                    
                    # Check for duplicate options (case-insensitive)
                    option_values = [v.lower() for v in cleaned_options.values()]
                    if len(option_values) != len(set(option_values)):
                        if self.log_invalid:
                            logger.warning(f"Question {question_number}: Duplicate options detected")
                        return None
                    
                    cleaned_data["options"] = cleaned_options
                else:
                    if self.log_invalid:
                        logger.warning(f"Question {question_number}: Options must be a dictionary")
                    return None
            
            # Handle correct_answer
            cleaned_data["correct_answer"] = data["correct_answer"]
            
            # Add required fields with defaults if missing
            if "exam_type" not in cleaned_data:
                cleaned_data["exam_type"] = "JEE_MAIN"  # Default value
            
            if "subject" not in cleaned_data:
                cleaned_data["subject"] = "Physics"  # Default value
            
            # Copy optional fields
            if "question_type" in data:
                cleaned_data["question_type"] = data["question_type"]
            else:
                cleaned_data["question_type"] = "single_correct"  # Default value
            
            if "marks" in data:
                cleaned_data["marks"] = data["marks"]
            
            if "estimated_time_minutes" in data:
                cleaned_data["estimated_time_minutes"] = data["estimated_time_minutes"]
            
            # Create and validate Question object
            try:
                question = Question(**cleaned_data)
                logger.debug(f"Question {question_number}: Validated successfully")
                return question
            
            except ValidationError as e:
                if self.log_invalid:
                    logger.warning(f"Question {question_number}: Pydantic validation failed: {e}")
                return None
        
        except Exception as e:
            if self.log_invalid:
                logger.warning(f"Question {question_number}: Unexpected validation error: {e}")
            return None
    
    def _clean_text(self, text: Any) -> str:
        """
        Clean and normalize text content.
        
        Performs:
        1. Convert to string
        2. Remove extra whitespace
        3. Normalize line breaks
        4. Remove leading/trailing whitespace
        
        Args:
            text: Text to clean (any type, will be converted to string)
        
        Returns:
            Cleaned text string
        
        Example:
            >>> parser = ResponseParser()
            >>> cleaned = parser._clean_text("  Hello   \\n\\n  World  ")
            >>> print(cleaned)
            'Hello World'
        """
        if text is None:
            return ""
        
        # Convert to string
        text_str = str(text)
        
        # Remove leading/trailing whitespace
        text_str = text_str.strip()
        
        # Replace multiple spaces with single space
        text_str = re.sub(r' +', ' ', text_str)
        
        # Replace multiple newlines with single newline
        text_str = re.sub(r'\n+', '\n', text_str)
        
        # Replace tab characters with space
        text_str = text_str.replace('\t', ' ')
        
        # Final trim
        text_str = text_str.strip()
        
        return text_str
    
    def _fix_latex_json_issues(self, json_text: str, aggressive: bool = False) -> str:
        """
        Fix common LaTeX-related JSON parsing issues.
        
        Gemini often generates invalid JSON with unescaped backslashes in LaTeX.
        This method fixes these common issues.
        
        Args:
            json_text: JSON text that may have LaTeX issues
            
        Returns:
            Fixed JSON text
        """
        if not json_text:
            return json_text
        
        # Simple approach: fix the most common issue - unescaped backslashes in LaTeX
        # Replace common LaTeX patterns with properly escaped versions
        fixed_text = json_text
        
        # Fix backslashes before Greek letters and common LaTeX commands
        latex_patterns = [
            r'(?<!\\)\\mu',      # \mu -> \\mu (but not already escaped \\mu)
            r'(?<!\\)\\alpha',  # \alpha -> \\alpha
            r'(?<!\\)\\beta',   # \beta -> \\beta
            r'(?<!\\)\\gamma',  # \gamma -> \\gamma
            r'(?<!\\)\\delta',  # \delta -> \\delta
            r'(?<!\\)\\theta',  # \theta -> \\theta
            r'(?<!\\)\\lambda', # \lambda -> \\lambda
            r'(?<!\\)\\sigma',  # \sigma -> \\sigma
            r'(?<!\\)\\phi',    # \phi -> \\phi
            r'(?<!\\)\\omega',  # \omega -> \\omega
            r'(?<!\\)\\pi',    # \pi -> \\pi
            r'(?<!\\)\\infty', # \infty -> \\infty
            r'(?<!\\)\\sum',   # \sum -> \\sum
            r'(?<!\\)\\int',   # \int -> \\int
            r'(?<!\\)\\frac',  # \frac -> \\frac
            r'(?<!\\)\\sqrt',  # \sqrt -> \\sqrt
            r'(?<!\\)\\sin',   # \sin -> \\sin
            r'(?<!\\)\\cos',   # \cos -> \\cos
            r'(?<!\\)\\tan',   # \tan -> \\tan
            r'(?<!\\)\\log',   # \log -> \\log
            r'(?<!\\)\\ln',    # \ln -> \\ln
        ]
        
        for pattern in latex_patterns:
            fixed_text = re.sub(pattern, r'\\\\\g<0>', fixed_text)
        
        return fixed_text
    
    def parse_single_question(self, data: Dict[str, Any]) -> Optional[Question]:
        """
        Parse and validate a single question dictionary.
        
        Convenience method for parsing individual questions.
        
        Args:
            data: Dictionary containing question data
        
        Returns:
            Validated Question object, or None if invalid
        
        Example:
            >>> parser = ResponseParser()
            >>> question = parser.parse_single_question({
            ...     "question": "What is the speed of light?",
            ...     "options": {"A": "3×10⁸ m/s", "B": "3×10⁶ m/s", "C": "3×10⁹ m/s", "D": "3×10⁷ m/s"},
            ...     "correct_answer": "A",
            ...     "explanation": "The speed of light in vacuum is approximately 3×10⁸ m/s",
            ...     "difficulty": "easy",
            ...     "topic": "Physics - Light"
            ... })
        """
        return self._validate_question(data)
    
    def get_statistics(self, questions: List[Question]) -> Dict[str, Any]:
        """
        Get statistics about a list of questions.
        
        Args:
            questions: List of Question objects
        
        Returns:
            Dictionary with statistics
        
        Example:
            >>> parser = ResponseParser()
            >>> stats = parser.get_statistics(questions)
            >>> print(stats)
            {
                'total': 10,
                'by_difficulty': {'easy': 3, 'medium': 5, 'hard': 2},
                'by_type': {'single_correct': 8, 'multiple_correct': 2},
                'topics': ['Calculus', 'Algebra', 'Trigonometry']
            }
        """
        stats = {
            "total": len(questions),
            "by_difficulty": {"easy": 0, "medium": 0, "hard": 0},
            "by_type": {},
            "topics": []
        }
        
        topics_set = set()
        
        for question in questions:
            # Count by difficulty
            stats["by_difficulty"][question.difficulty] += 1
            
            # Count by type
            qtype = question.question_type
            stats["by_type"][qtype] = stats["by_type"].get(qtype, 0) + 1
            
            # Collect topics
            topics_set.add(question.topic)
        
        stats["topics"] = sorted(list(topics_set))
        
        return stats


# Convenience function
def parse_llm_response(
    response_text: str,
    strict_mode: bool = False,
    expected_count: Optional[int] = None
) -> Tuple[List[Question], Dict[str, int]]:
    """
    Convenience function to parse LLM response.
    
    This is a shortcut for creating a ResponseParser and parsing in one call.
    
    Args:
        response_text: Raw response text from LLM
        strict_mode: If True, raises exceptions on errors (default: False)
        expected_count: Expected number of questions (optional)
    
    Returns:
        Tuple containing list of questions and statistics
    
    Example:
        >>> from utils.response_parser import parse_llm_response
        >>> questions, stats = parse_llm_response(llm_response, expected_count=5)
        >>> print(f"Parsed {stats['valid']} questions")
    """
    parser = ResponseParser(strict_mode=strict_mode)
    return parser.parse_response(response_text, expected_count=expected_count)


# Module initialization
logger.info("Response parser module loaded")
