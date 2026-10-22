"""
Prompt Templates Module for Question Generation

This module provides reusable prompt templates for generating exam questions
using Gemini Flash in the Mentor AI EdTech Platform. It includes templates for
different exam types (JEE Main, JEE Advanced, NEET) with proper formatting,
examples, and validation requirements.

Features:
- Exam-specific templates (JEE Main, JEE Advanced, NEET)
- Few-shot learning with examples
- Structured JSON output format
- Difficulty-based generation
- Syllabus-constrained content
- Type hints and comprehensive documentation

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from utils.prompt_templates import build_prompt
    >>> 
    >>> # Generate JEE Main questions
    >>> prompt = build_prompt(
    ...     exam_type="JEE_MAIN",
    ...     topic="Limits and Continuity",
    ...     syllabus_context="Chapter content about limits...",
    ...     difficulty="medium",
    ...     num_questions=5
    ... )
    >>> 
    >>> # Use with Gemini client
    >>> from utils.gemini_client import GeminiClient
    >>> client = GeminiClient()
    >>> response = client.generate_content(prompt)
"""

import json
from typing import Dict, List, Optional, Literal
from enum import Enum

# Type definitions
ExamType = Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]
Difficulty = Literal["easy", "medium", "hard"]
QuestionType = Literal["single_correct", "multiple_correct", "numerical", "matrix_match"]


class PromptTemplateError(Exception):
    """Exception raised for prompt template errors."""
    pass


def get_jee_main_template() -> str:
    """
    Get prompt template for JEE Main single correct MCQ questions.
    
    JEE Main focuses on fundamental concepts with single correct answer
    multiple choice questions. Template includes system instructions,
    output format, and examples.
    
    Returns:
        Formatted prompt template string with placeholders
    
    Example:
        >>> template = get_jee_main_template()
        >>> prompt = template.format(
        ...     topic="Calculus",
        ...     syllabus_context="Differentiation rules...",
        ...     difficulty="medium",
        ...     num_questions=5
        ... )
    """
    return """You are an expert JEE Main question generator for the Mentor AI EdTech platform. Your role is to create high-quality, exam-standard multiple choice questions (MCQs) based STRICTLY on the provided syllabus content.

EXAM CONTEXT:
- Exam: JEE Main (Joint Entrance Examination - Main)
- Format: Single Correct Answer MCQs
- Time per question: ~3 minutes
- Difficulty: {difficulty}
- Topic: {topic}

SYLLABUS CONTENT (USE ONLY THIS INFORMATION):
{syllabus_context}

TASK:
Generate {num_questions} high-quality JEE Main MCQs on the topic "{topic}" with {difficulty} difficulty level.

STRICT REQUIREMENTS:
1. Use ONLY concepts, formulas, and information from the provided syllabus content above
2. DO NOT introduce external concepts or advanced topics not mentioned in the syllabus
3. Each question must have EXACTLY 4 options (A, B, C, D)
4. EXACTLY ONE option must be correct
5. All incorrect options (distractors) must be plausible but clearly wrong
6. Include a detailed explanation showing why the correct answer is right and others are wrong
7. Questions should test conceptual understanding, not just memorization
8. Difficulty level guidelines:
   - easy: Direct application of formulas, straightforward concepts
   - medium: Multi-step problems, concept combinations, moderate calculations
   - hard: Complex scenarios, multiple concepts, challenging calculations
9. Ensure mathematical notation is clear and unambiguous
10. Avoid ambiguous or trick questions

OUTPUT FORMAT:
Return a valid JSON array containing {num_questions} question objects. Each object must have this EXACT structure:

[
  {{
    "question": "Clear, concise question text with proper mathematical notation",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": "A",
    "explanation": "Detailed step-by-step explanation of the solution, showing why the correct answer is right and why other options are incorrect",
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "exam_type": "{exam_type}",
    "subject": "{subject}",
    "question_type": "single_correct",
    "marks": 4,
    "estimated_time_minutes": 3
  }}
]

EXAMPLES (for reference only - generate new questions based on provided syllabus):

Example 1 (Medium difficulty):
{{
  "question": "If f(x) = x³ - 6x² + 11x - 6, then the number of critical points of f(x) is:",
  "options": {{
    "A": "0",
    "B": "1",
    "C": "2",
    "D": "3"
  }},
  "correct_answer": "C",
  "explanation": "To find critical points, we need to find where f'(x) = 0. Taking derivative: f'(x) = 3x² - 12x + 11. For critical points: 3x² - 12x + 11 = 0. Using discriminant: D = 144 - 132 = 12 > 0. Since discriminant is positive, the quadratic has 2 real roots, meaning 2 critical points. Option A is wrong (function is cubic, must have critical points). Option B is wrong (quadratic can't have just 1 root with positive discriminant). Option D is wrong (derivative is quadratic, can have at most 2 roots).",
  "difficulty": "medium",
  "topic": "Calculus - Application of Derivatives",
  "exam_type": "JEE_MAIN",
  "subject": "Math",
  "question_type": "single_correct",
  "marks": 4,
  "estimated_time_minutes": 3
}}

Example 2 (Easy difficulty):
{{
  "question": "What is the derivative of sin(2x) with respect to x?",
  "options": {{
    "A": "cos(2x)",
    "B": "2cos(2x)",
    "C": "-2sin(2x)",
    "D": "2sin(2x)"
  }},
  "correct_answer": "B",
  "explanation": "Using chain rule: d/dx[sin(2x)] = cos(2x) × d/dx(2x) = cos(2x) × 2 = 2cos(2x). Option A is incorrect because it misses the chain rule factor of 2. Option C is incorrect as it has wrong sign and function. Option D is incorrect as it has wrong trigonometric function.",
  "difficulty": "easy",
  "topic": "Calculus - Differentiation",
  "exam_type": "JEE_MAIN",
  "subject": "Math",
  "question_type": "single_correct",
  "marks": 4,
  "estimated_time_minutes": 2
}}

NOW GENERATE {num_questions} NEW QUESTIONS:
Ensure the output is a valid JSON array with no additional text before or after. Do not include markdown code blocks or explanatory text."""


def get_jee_advanced_template(question_type: QuestionType = "single_correct") -> str:
    """
    Get prompt template for JEE Advanced questions.
    
    JEE Advanced includes multiple question types: single correct, multiple correct,
    numerical answer, and matrix match. This template adapts based on question type.
    
    Args:
        question_type: Type of question to generate
            - "single_correct": One correct answer (default)
            - "multiple_correct": One or more correct answers
            - "numerical": Integer numerical answer (0-9999)
            - "matrix_match": Match items from two columns
    
    Returns:
        Formatted prompt template string with placeholders
    
    Example:
        >>> template = get_jee_advanced_template("multiple_correct")
        >>> prompt = template.format(
        ...     topic="Thermodynamics",
        ...     syllabus_context="Laws of thermodynamics...",
        ...     difficulty="hard",
        ...     num_questions=3
        ... )
    """
    if question_type == "multiple_correct":
        return """You are an expert JEE Advanced question generator for the Mentor AI EdTech platform. Your role is to create high-quality, advanced multiple correct answer questions based STRICTLY on the provided syllabus content.

EXAM CONTEXT:
- Exam: JEE Advanced (Joint Entrance Examination - Advanced)
- Format: Multiple Correct Answer MCQs
- Time per question: ~4-5 minutes
- Difficulty: {difficulty}
- Topic: {topic}

SYLLABUS CONTENT (USE ONLY THIS INFORMATION):
{syllabus_context}

TASK:
Generate {num_questions} high-quality JEE Advanced multiple correct answer questions on "{topic}" with {difficulty} difficulty.

STRICT REQUIREMENTS:
1. Use ONLY concepts from the provided syllabus content
2. Each question must have EXACTLY 4 options (A, B, C, D)
3. ONE OR MORE options must be correct (minimum 1, maximum 4)
4. Clearly state in the question: "One or more options may be correct"
5. All options must be non-trivial and require careful analysis
6. Include detailed explanation for each option
7. Questions must test deep conceptual understanding
8. Difficulty guidelines:
   - medium: 2-3 correct answers, moderate complexity
   - hard: Multiple correct answers, complex scenarios, advanced concepts
9. Avoid questions where all options are correct (too easy to guess)
10. Ensure options are independent (selecting one doesn't reveal others)

OUTPUT FORMAT (JSON):
[
  {{
    "question": "Question text (include: 'One or more options may be correct')",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": ["A", "C"],
    "explanation": "Detailed explanation for EACH option: (A) Why correct/incorrect... (B) Why correct/incorrect... (C) Why correct/incorrect... (D) Why correct/incorrect...",
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "exam_type": "{exam_type}",
    "subject": "{subject}",
    "question_type": "multiple_correct",
    "marks": 4,
    "estimated_time_minutes": 5
  }}
]

EXAMPLE:
{{
  "question": "For the reaction 2A + B → Products, the following statements are made. One or more options may be correct:",
  "options": {{
    "A": "If the rate law is r = k[A]²[B], then doubling [A] quadruples the rate",
    "B": "If the rate law is r = k[A][B], then doubling both [A] and [B] doubles the rate",
    "C": "The order of reaction can be determined from stoichiometry",
    "D": "If rate = k[A]²[B], the overall order is 3"
  }},
  "correct_answer": ["A", "D"],
  "explanation": "(A) CORRECT: If r = k[A]²[B], doubling [A] makes it (2A)² = 4A², so rate becomes 4 times. (B) INCORRECT: If r = k[A][B], doubling both gives k(2A)(2B) = 4k[A][B], which is 4 times, not 2 times. (C) INCORRECT: Order must be determined experimentally, not from stoichiometric coefficients. (D) CORRECT: Order = sum of exponents = 2 + 1 = 3.",
  "difficulty": "medium",
  "topic": "Chemical Kinetics",
  "exam_type": "JEE_ADVANCED",
  "subject": "Chemistry",
  "question_type": "multiple_correct",
  "marks": 4,
  "estimated_time_minutes": 5
}}

NOW GENERATE {num_questions} NEW QUESTIONS (JSON only, no extra text):"""

    elif question_type == "numerical":
        return """You are an expert JEE Advanced question generator for the Mentor AI EdTech platform. Your role is to create high-quality, numerical answer type questions based STRICTLY on the provided syllabus content.

EXAM CONTEXT:
- Exam: JEE Advanced
- Format: Numerical Answer Type (0-9999)
- Time per question: ~5 minutes
- Difficulty: {difficulty}
- Topic: {topic}

SYLLABUS CONTENT (USE ONLY THIS INFORMATION):
{syllabus_context}

TASK:
Generate {num_questions} numerical answer type questions on "{topic}" with {difficulty} difficulty.

STRICT REQUIREMENTS:
1. Use ONLY concepts from the provided syllabus content
2. Answer must be a NON-NEGATIVE INTEGER between 0 and 9999
3. Question must be designed so the numerical answer falls in this range
4. NO options to choose from - student enters the number directly
5. Include detailed step-by-step solution
6. Ensure calculations are accurate and answer is unambiguous
7. Difficulty guidelines:
   - medium: Multi-step calculations, 2-3 concepts
   - hard: Complex calculations, multiple concepts, careful analysis
8. Avoid decimal answers - if needed, ask for nearest integer or specific units

OUTPUT FORMAT (JSON):
[
  {{
    "question": "Question text clearly stating what to calculate and any rounding instructions",
    "correct_answer": 42,
    "explanation": "Step-by-step solution with all calculations shown",
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "exam_type": "{exam_type}",
    "subject": "{subject}",
    "question_type": "numerical",
    "marks": 4,
    "estimated_time_minutes": 5
  }}
]

EXAMPLE:
{{
  "question": "A particle moves along a straight line such that its displacement s (in meters) at time t (in seconds) is given by s = 2t³ - 9t² + 12t + 1. Find the time (in seconds) when the velocity of the particle is zero. If there are multiple times, enter the sum of all such times.",
  "correct_answer": 3,
  "explanation": "Velocity v = ds/dt = 6t² - 18t + 12. Setting v = 0: 6t² - 18t + 12 = 0. Dividing by 6: t² - 3t + 2 = 0. Factoring: (t-1)(t-2) = 0. Therefore t = 1 or t = 2. Sum = 1 + 2 = 3 seconds.",
  "difficulty": "medium",
  "topic": "Calculus - Application of Derivatives",
  "exam_type": "JEE_ADVANCED",
  "subject": "Math",
  "question_type": "numerical",
  "marks": 4,
  "estimated_time_minutes": 4
}}

NOW GENERATE {num_questions} NEW QUESTIONS (JSON only, no extra text):"""

    else:  # single_correct (default)
        return """You are an expert JEE Advanced question generator for the Mentor AI EdTech platform. Your role is to create high-quality, advanced single correct answer questions based STRICTLY on the provided syllabus content.

EXAM CONTEXT:
- Exam: JEE Advanced
- Format: Single Correct Answer MCQs
- Time per question: ~4 minutes
- Difficulty: {difficulty}
- Topic: {topic}

SYLLABUS CONTENT (USE ONLY THIS INFORMATION):
{syllabus_context}

TASK:
Generate {num_questions} high-quality JEE Advanced single correct questions on "{topic}" with {difficulty} difficulty.

STRICT REQUIREMENTS:
1. Use ONLY concepts from the provided syllabus content
2. Each question must have EXACTLY 4 options (A, B, C, D)
3. EXACTLY ONE option must be correct
4. Questions must be significantly more challenging than JEE Main level
5. Test deep conceptual understanding and problem-solving
6. Include multi-step reasoning or concept integration
7. Detailed explanation with complete solution
8. Difficulty guidelines:
   - medium: Multi-concept integration, 3-4 steps
   - hard: Advanced concepts, complex scenarios, 5+ steps, tricky insights
9. Avoid purely computational questions - focus on concepts

OUTPUT FORMAT (JSON):
[
  {{
    "question": "Question text with clear problem statement",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": "B",
    "explanation": "Comprehensive step-by-step solution",
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "exam_type": "{exam_type}",
    "subject": "{subject}",
    "question_type": "single_correct",
    "marks": 4,
    "estimated_time_minutes": 4
  }}
]

EXAMPLE:
{{
  "question": "A function f: R → R satisfies f(x+y) = f(x) + f(y) for all x, y ∈ R and f(1) = 3. If f is differentiable at x = 0, then f'(5) equals:",
  "options": {{
    "A": "0",
    "B": "3",
    "C": "5",
    "D": "15"
  }},
  "correct_answer": "B",
  "explanation": "From f(x+y) = f(x) + f(y), setting y = 0: f(x) = f(x) + f(0), so f(0) = 0. For differentiability: f'(0) = lim(h→0)[f(h) - f(0)]/h = lim(h→0)f(h)/h. Now, f(x) = f(1·x) = f(1+1+...+1) = xf(1) = 3x (for integers, extends to all reals by continuity). So f(x) = 3x. Therefore f'(x) = 3 for all x, including x = 5. Answer: B.",
  "difficulty": "hard",
  "topic": "Calculus - Continuity and Differentiability",
  "exam_type": "JEE_ADVANCED",
  "subject": "Math",
  "question_type": "single_correct",
  "marks": 4,
  "estimated_time_minutes": 5
}}

NOW GENERATE {num_questions} NEW QUESTIONS (JSON only, no extra text):"""


def get_neet_template() -> str:
    """
    Get prompt template for NEET single correct MCQ questions.
    
    NEET focuses on Biology, Physics, and Chemistry for medical entrance.
    Questions emphasize conceptual clarity, factual knowledge, and application
    to biological/medical contexts.
    
    Returns:
        Formatted prompt template string with placeholders
    
    Example:
        >>> template = get_neet_template()
        >>> prompt = template.format(
        ...     topic="Cell Structure",
        ...     syllabus_context="Cell organelles and functions...",
        ...     difficulty="medium",
        ...     num_questions=5
        ... )
    """
    return """You are an expert NEET question generator for the Mentor AI EdTech platform. Your role is to create high-quality, NEET-standard medical entrance exam questions based STRICTLY on the provided syllabus content.

EXAM CONTEXT:
- Exam: NEET (National Eligibility cum Entrance Test)
- Format: Single Correct Answer MCQs
- Time per question: ~45-60 seconds
- Difficulty: {difficulty}
- Topic: {topic}
- Focus: Biology, Physics, Chemistry for medical entrance

SYLLABUS CONTENT (USE ONLY THIS INFORMATION):
{syllabus_context}

TASK:
Generate {num_questions} high-quality NEET MCQs on the topic "{topic}" with {difficulty} difficulty level.

STRICT REQUIREMENTS:
1. Use ONLY concepts, facts, and information from the provided syllabus content above
2. DO NOT introduce concepts not covered in the syllabus
3. Each question must have EXACTLY 4 options (A, B, C, D)
4. EXACTLY ONE option must be correct
5. Questions should be factually accurate and medically/scientifically precise
6. For Biology: Focus on conceptual understanding, not just memorization
7. For Physics/Chemistry: Include relevant medical/biological applications where appropriate
8. Include clear, educational explanations
9. Difficulty level guidelines:
   - easy: Direct recall, basic concepts, simple applications
   - medium: Concept application, connecting ideas, moderate analysis
   - hard: Complex scenarios, multiple concept integration, critical thinking
10. Use proper scientific terminology and nomenclature
11. Avoid ambiguous or controversial questions

OUTPUT FORMAT:
Return a valid JSON array containing {num_questions} question objects. Each object must have this EXACT structure:

[
  {{
    "question": "Clear question text with proper scientific terminology",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": "C",
    "explanation": "Detailed explanation showing why the correct answer is right and why other options are incorrect, with relevant scientific reasoning",
    "difficulty": "{difficulty}",
    "topic": "{topic}",
    "exam_type": "{exam_type}",
    "subject": "{subject}",
    "question_type": "single_correct",
    "marks": 4,
    "estimated_time_minutes": 1
  }}
]

EXAMPLES (for reference only - generate new questions based on provided syllabus):

Example 1 (Biology - Medium difficulty):
{{
  "question": "During which phase of the cell cycle does DNA replication occur?",
  "options": {{
    "A": "G1 phase",
    "B": "S phase",
    "C": "G2 phase",
    "D": "M phase"
  }},
  "correct_answer": "B",
  "explanation": "DNA replication occurs during the S (Synthesis) phase of interphase. During S phase, the cell duplicates its DNA content, going from 2n to 4n DNA content while maintaining 2n chromosome number. G1 phase (option A) is for cell growth before DNA synthesis. G2 phase (option C) is for preparation after DNA synthesis. M phase (option D) is for mitosis/cell division.",
  "difficulty": "medium",
  "topic": "Cell Cycle and Cell Division",
  "exam_type": "NEET",
  "subject": "Biology",
  "question_type": "single_correct",
  "marks": 4,
  "estimated_time_minutes": 1
}}

Example 2 (Biology - Easy difficulty):
{{
  "question": "Which cell organelle is known as the 'powerhouse of the cell'?",
  "options": {{
    "A": "Ribosome",
    "B": "Mitochondria",
    "C": "Endoplasmic reticulum",
    "D": "Golgi apparatus"
  }},
  "correct_answer": "B",
  "explanation": "Mitochondria are called the 'powerhouse of the cell' because they produce ATP through cellular respiration, which is the main energy currency of the cell. Ribosomes (option A) synthesize proteins. Endoplasmic reticulum (option C) helps in protein and lipid synthesis. Golgi apparatus (option D) packages and modifies proteins.",
  "difficulty": "easy",
  "topic": "Cell Structure and Function",
  "exam_type": "NEET",
  "subject": "Biology",
  "question_type": "single_correct",
  "marks": 4,
  "estimated_time_minutes": 1
}}

Example 3 (Physics - Medium difficulty):
{{
  "question": "A person cannot see objects clearly beyond 2 meters. What is the power of the lens required to correct this defect?",
  "options": {{
    "A": "+0.5 D",
    "B": "-0.5 D",
    "C": "+2.0 D",
    "D": "-2.0 D"
  }},
  "correct_answer": "B",
  "explanation": "The person has myopia (near-sightedness) with far point at 2 m. To correct this, a concave lens is needed. The focal length f = -2 m (negative for concave). Power P = 1/f = 1/(-2) = -0.5 D. Option A is wrong (convex lens, would worsen myopia). Option C and D have wrong magnitudes.",
  "difficulty": "medium",
  "topic": "Ray Optics - Human Eye",
  "exam_type": "NEET",
  "subject": "Physics",
  "question_type": "single_correct",
  "marks": 4,
  "estimated_time_minutes": 1
}}

NOW GENERATE {num_questions} NEW QUESTIONS:
Ensure the output is a valid JSON array with no additional text before or after. Do not include markdown code blocks or explanatory text."""


def build_prompt(
    exam_type: ExamType,
    topic: str,
    syllabus_context: str,
    difficulty: Difficulty = "medium",
    num_questions: int = 5,
    question_type: QuestionType = "single_correct",
    subject: str = "Physics"
) -> str:
    """
    Build a complete prompt for question generation using appropriate template.
    
    This function selects the appropriate template based on exam type and
    fills in all placeholders with provided parameters.
    
    Args:
        exam_type: Type of exam ("JEE_MAIN", "JEE_ADVANCED", "NEET")
        topic: Topic name for question generation
        syllabus_context: Relevant syllabus content from vector search
        difficulty: Difficulty level ("easy", "medium", "hard")
        num_questions: Number of questions to generate (default: 5)
        question_type: Type of question for JEE Advanced (default: "single_correct")
        subject: Subject for the question (default: "Physics")
    
    Returns:
        Complete formatted prompt ready to send to Gemini
    
    Raises:
        PromptTemplateError: If invalid exam_type or parameters provided
        ValueError: If num_questions < 1 or > 20
    
    Example:
        >>> prompt = build_prompt(
        ...     exam_type="JEE_MAIN",
        ...     topic="Limits and Continuity",
        ...     syllabus_context="Limits: Definition, theorems...",
        ...     difficulty="medium",
        ...     num_questions=5
        ... )
        >>> # Use with Gemini
        >>> from utils.gemini_client import GeminiClient
        >>> client = GeminiClient()
        >>> response = client.generate_content(prompt)
    """
    # Validate inputs
    if exam_type not in ["JEE_MAIN", "JEE_ADVANCED", "NEET"]:
        raise PromptTemplateError(
            f"Invalid exam_type: {exam_type}. Must be 'JEE_MAIN', 'JEE_ADVANCED', or 'NEET'"
        )
    
    if difficulty not in ["easy", "medium", "hard"]:
        raise PromptTemplateError(
            f"Invalid difficulty: {difficulty}. Must be 'easy', 'medium', or 'hard'"
        )
    
    if num_questions < 1 or num_questions > 20:
        raise ValueError("num_questions must be between 1 and 20")
    
    if not topic or not topic.strip():
        raise PromptTemplateError("Topic cannot be empty")
    
    if not syllabus_context or not syllabus_context.strip():
        raise PromptTemplateError("Syllabus context cannot be empty")
    
    # Select appropriate template
    if exam_type == "JEE_MAIN":
        template = get_jee_main_template()
    elif exam_type == "JEE_ADVANCED":
        template = get_jee_advanced_template(question_type)
    else:  # NEET
        template = get_neet_template()
    
    # Fill in placeholders
    prompt = template.format(
        topic=topic.strip(),
        syllabus_context=syllabus_context.strip(),
        difficulty=difficulty,
        num_questions=num_questions,
        exam_type=exam_type,
        subject=subject
    )
    
    return prompt


def validate_question_response(response: str) -> bool:
    """
    Validate that the Gemini response is properly formatted JSON.
    
    Args:
        response: Raw response from Gemini
    
    Returns:
        True if response is valid JSON array, False otherwise
    
    Example:
        >>> response = '[{"question": "...", "options": {...}}]'
        >>> is_valid = validate_question_response(response)
        >>> print(is_valid)
        True
    """
    try:
        # Try to parse as JSON
        data = json.loads(response.strip())
        
        # Check if it's a list
        if not isinstance(data, list):
            return False
        
        # Check if list is not empty
        if len(data) == 0:
            return False
        
        # Validate each question has required fields
        required_fields = {"question", "correct_answer", "explanation", "difficulty", "topic"}
        
        for item in data:
            if not isinstance(item, dict):
                return False
            
            # Check required fields
            if not required_fields.issubset(item.keys()):
                return False
            
            # For MCQ, check options exist
            if "options" in item:
                if not isinstance(item["options"], dict):
                    return False
        
        return True
    
    except json.JSONDecodeError:
        return False
    except Exception:
        return False


def extract_json_from_response(response: str) -> str:
    """
    Extract JSON from Gemini response, removing markdown code blocks if present.
    
    Sometimes Gemini wraps JSON in markdown code blocks (```json...```).
    This function extracts the actual JSON content.
    
    Args:
        response: Raw response from Gemini
    
    Returns:
        Cleaned JSON string
    
    Example:
        >>> response = '```json\\n[{"question": "..."}]\\n```'
        >>> json_str = extract_json_from_response(response)
        >>> print(json_str)
        '[{"question": "..."}]'
    """
    # Remove markdown code blocks
    cleaned = response.strip()
    
    # Check for markdown code block with json
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]  # Remove ```json
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]  # Remove ```
    
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]  # Remove trailing ```
    
    # Remove any leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


def get_template_info(exam_type: ExamType) -> Dict[str, any]:
    """
    Get information about available templates for an exam type.
    
    Args:
        exam_type: Type of exam
    
    Returns:
        Dictionary with template information
    
    Example:
        >>> info = get_template_info("JEE_ADVANCED")
        >>> print(info["question_types"])
        ['single_correct', 'multiple_correct', 'numerical']
    """
    templates = {
        "JEE_MAIN": {
            "question_types": ["single_correct"],
            "time_per_question": 3,
            "marks_per_question": 4,
            "difficulty_levels": ["easy", "medium", "hard"]
        },
        "JEE_ADVANCED": {
            "question_types": ["single_correct", "multiple_correct", "numerical"],
            "time_per_question": 4,
            "marks_per_question": 4,
            "difficulty_levels": ["medium", "hard"]
        },
        "NEET": {
            "question_types": ["single_correct"],
            "time_per_question": 1,
            "marks_per_question": 4,
            "difficulty_levels": ["easy", "medium", "hard"]
        }
    }
    
    return templates.get(exam_type, {})


# Module initialization
if __name__ == "__main__":
    # Example usage
    print("Prompt Templates Module - Example Usage\n")
    
    # Example 1: JEE Main
    print("=" * 80)
    print("Example 1: JEE Main Prompt")
    print("=" * 80)
    prompt = build_prompt(
        exam_type="JEE_MAIN",
        topic="Limits and Continuity",
        syllabus_context="Limits: Left-hand limit, right-hand limit, and their equality. Fundamental theorems on limits. Continuity of a function at a point and in an interval.",
        difficulty="medium",
        num_questions=3
    )
    print(f"Prompt length: {len(prompt)} characters")
    print(f"First 500 chars: {prompt[:500]}...")
    
    # Example 2: JEE Advanced (Multiple Correct)
    print("\n" + "=" * 80)
    print("Example 2: JEE Advanced (Multiple Correct) Prompt")
    print("=" * 80)
    prompt = build_prompt(
        exam_type="JEE_ADVANCED",
        topic="Chemical Kinetics",
        syllabus_context="Rate of reaction, order and molecularity, rate law, rate constant, half-life.",
        difficulty="hard",
        num_questions=2,
        question_type="multiple_correct"
    )
    print(f"Prompt length: {len(prompt)} characters")
    
    # Example 3: NEET
    print("\n" + "=" * 80)
    print("Example 3: NEET Prompt")
    print("=" * 80)
    prompt = build_prompt(
        exam_type="NEET",
        topic="Cell Structure",
        syllabus_context="Cell theory, prokaryotic and eukaryotic cells, plant and animal cells. Cell organelles: mitochondria, chloroplasts, ribosomes, ER, Golgi apparatus, lysosomes.",
        difficulty="medium",
        num_questions=5
    )
    print(f"Prompt length: {len(prompt)} characters")
    
    print("\n" + "=" * 80)
    print("✓ Prompt Templates Module Ready!")
    print("=" * 80)
