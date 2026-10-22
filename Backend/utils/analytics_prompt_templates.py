"""
Analytics Prompt Templates for Gemini Flash Analysis - Mentor AI Platform.

This module provides prompt templates for generating educational analytics
using Gemini Flash. It creates structured prompts that guide the AI to analyze
test performance and generate actionable insights.

Features:
- Exam-specific analytics (JEE Main, JEE Advanced, NEET)
- Structured JSON output format
- Actionable recommendations with study hour estimates
- Learning pattern detection
- Priority-based improvement strategies
- Educational psychology principles

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from utils.analytics_prompt_templates import build_analytics_prompt
    >>> 
    >>> prompt = build_analytics_prompt(
    ...     context=formatted_test_context,
    ...     exam_type="JEE_MAIN",
    ...     student_name="Rahul"
    ... )
    >>> 
    >>> # Use with Gemini client
    >>> from utils.gemini_client import GeminiClient
    >>> client = GeminiClient()
    >>> response = client.generate_content(prompt)
"""

import json
from typing import Dict, List, Optional, Literal

# Type definitions
ExamType = Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]


class AnalyticsPromptError(Exception):
    """Exception raised for analytics prompt template errors."""
    pass


def build_analytics_prompt(
    context: str,
    exam_type: ExamType = "JEE_MAIN",
    student_name: Optional[str] = None,
    include_examples: bool = True,
    max_strengths: int = 5,
    max_weaknesses: int = 8
) -> str:
    """
    Build comprehensive analytics prompt for Gemini Flash.
    
    Creates a structured prompt that guides the AI to analyze test performance
    and generate actionable insights with specific recommendations and study plans.
    
    Args:
        context: Formatted test results context from AnalyticsContextBuilder
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        student_name: Optional student name for personalization
        include_examples: Whether to include example analytics
        max_strengths: Maximum number of strengths to identify
        max_weaknesses: Maximum number of weaknesses to identify
    
    Returns:
        Complete prompt string for Gemini Flash
    
    Raises:
        AnalyticsPromptError: If context is empty or invalid
    
    Example:
        >>> prompt = build_analytics_prompt(
        ...     context=test_context,
        ...     exam_type="JEE_MAIN",
        ...     student_name="Priya"
        ... )
    """
    if not context or not context.strip():
        raise AnalyticsPromptError("Context cannot be empty")
    
    # Get exam-specific instructions
    exam_instructions = _get_exam_specific_instructions(exam_type)
    
    # Build personalization
    student_reference = f"the student {student_name}" if student_name else "the student"
    
    # Build system section
    system_section = _build_system_section()
    
    # Build context section
    context_section = _build_context_section(context)
    
    # Build task section
    task_section = _build_task_section(student_reference, exam_type)
    
    # Build output format section
    output_format_section = _build_output_format_section(max_strengths, max_weaknesses)
    
    # Build guidelines section
    guidelines_section = _build_guidelines_section(exam_instructions)
    
    # Build examples section
    examples_section = ""
    if include_examples:
        examples_section = _build_examples_section(exam_type)
    
    # Build validation section
    validation_section = _build_validation_section()
    
    # Combine all sections
    prompt = f"""{system_section}

{context_section}

{task_section}

{output_format_section}

{guidelines_section}

{examples_section}

{validation_section}

NOW GENERATE THE ANALYTICS:
Ensure the output is valid JSON with no additional text before or after. Do not include markdown code blocks or explanatory text. Start directly with the JSON object."""
    
    return prompt


def _build_system_section() -> str:
    """Build the system role and context section."""
    return """=== SYSTEM ROLE ===

You are an expert educational analytics specialist for the Mentor AI EdTech platform. Your expertise includes:

• Educational Psychology: Understanding learning patterns and cognitive development
• Exam Strategy: Deep knowledge of JEE and NEET exam patterns, weightages, and strategies
• Data Analysis: Identifying trends, strengths, and improvement areas from test performance
• Personalized Learning: Creating actionable, student-specific study recommendations
• Time Management: Estimating realistic study hours and priorities
• Motivation: Crafting encouraging yet realistic assessments

Your goal is to analyze student test performance and provide actionable insights that help students improve their exam preparation efficiently."""


def _build_context_section(context: str) -> str:
    """Build the context section with test results."""
    return f"""=== TEST PERFORMANCE CONTEXT ===

Below is the student's test performance data. Analyze this carefully to generate insights:

{context}"""


def _build_task_section(student_reference: str, exam_type: str) -> str:
    """Build the task description section."""
    return f"""=== YOUR TASK ===

Analyze the test performance data above and generate comprehensive analytics for {student_reference}. Your analysis should:

1. **Identify Strengths**: Recognize topics where {student_reference} performed well (>75% accuracy)
   - Explain WHY they performed well (conceptual clarity, practice, natural aptitude)
   - Provide recommendations to maintain and leverage these strengths

2. **Identify Weaknesses**: Pinpoint areas needing improvement (<60% accuracy)
   - Explain the ROOT CAUSE of poor performance (conceptual gaps, calculation errors, time management)
   - Assign priority levels (HIGH/MEDIUM/LOW) based on topic weightage in {exam_type}
   - Estimate realistic study hours needed for improvement
   - Provide SPECIFIC, actionable recommendations

3. **Detect Learning Patterns**: Find recurring patterns in the student's performance
   - Question type preferences (MCQ vs Numerical)
   - Difficulty-wise performance trends (Easy vs Hard questions)
   - Time management patterns (rushing vs spending too much time)
   - Subject-wise consistency or gaps
   - Careless mistakes vs conceptual errors

4. **Overall Assessment**: Provide a holistic evaluation
   - Current preparation level
   - Comparison with expected benchmarks
   - Readiness for the actual exam
   - Key areas requiring immediate attention

5. **Study Strategy**: Create a prioritized study plan
   - Short-term focus areas (next 2-4 weeks)
   - Long-term preparation strategy
   - Resource recommendations (if applicable)
   - Practice frequency and type"""


def _build_output_format_section(max_strengths: int, max_weaknesses: int) -> str:
    """Build the output format specification section."""
    return f"""=== OUTPUT FORMAT (STRICT JSON STRUCTURE) ===

Return a valid JSON object with the following structure:

{{
  "strengths": [
    {{
      "topic": "Topic name (e.g., 'Calculus - Differentiation')",
      "subject": "Subject name (e.g., 'Mathematics')",
      "accuracy": 85.5,
      "reason": "Clear explanation of why this is a strength (2-3 sentences)",
      "recommendation": "Specific recommendation to maintain/leverage this strength (1-2 sentences)"
    }}
    // Include up to {max_strengths} strengths, prioritized by accuracy and topic importance
  ],
  
  "weaknesses": [
    {{
      "topic": "Topic name",
      "subject": "Subject name",
      "accuracy": 35.0,
      "reason": "Root cause analysis of the weakness (2-3 sentences)",
      "priority": "HIGH",  // HIGH, MEDIUM, or LOW based on exam weightage
      "estimated_study_hours": 12.0,  // Realistic hours needed for improvement
      "recommendation": "Specific, actionable steps to improve (2-3 sentences with concrete actions)"
    }}
    // Include up to {max_weaknesses} weaknesses, prioritized by severity and exam importance
  ],
  
  "learning_patterns": [
    "Pattern 1: Clear description of observed learning pattern with evidence",
    "Pattern 2: Another pattern with supporting data",
    "Pattern 3: Time management or strategy-related pattern"
    // Include 3-5 significant patterns observed in the performance
  ],
  
  "overall_assessment": "Comprehensive 3-4 sentence assessment covering: (1) Current preparation level, (2) Strengths to build upon, (3) Critical gaps to address, (4) Overall readiness and trajectory",
  
  "study_strategy": "Detailed, prioritized study plan (4-6 sentences) including: (1) Immediate focus areas for next 2-4 weeks, (2) Topic-wise time allocation, (3) Practice recommendations (daily/weekly), (4) Long-term preparation approach, (5) Specific study techniques or resources if applicable"
}}

CRITICAL OUTPUT REQUIREMENTS:
• Must be valid, parseable JSON (use double quotes, escape special characters)
• All fields are REQUIRED (do not omit any)
• accuracy values must be numbers (0-100)
• estimated_study_hours must be realistic numbers (0.5 to 40 hours typically)
• priority must be exactly "HIGH", "MEDIUM", or "LOW"
• Be specific and actionable in all text fields
• No placeholder text like "Topic 1" - use actual topic names from the context"""


def _build_guidelines_section(exam_instructions: str) -> str:
    """Build the analysis guidelines section."""
    return f"""=== ANALYSIS GUIDELINES ===

**General Principles:**
1. **Be Evidence-Based**: Every insight must be supported by data from the test performance
2. **Be Specific**: Avoid generic advice. Use actual topic names, specific concepts, and concrete actions
3. **Be Realistic**: Study hour estimates should be achievable (typically 2-15 hours per weak topic)
4. **Be Encouraging**: Balance honesty with motivation. Highlight progress potential
5. **Be Actionable**: Every recommendation should have clear, implementable steps

**Priority Assignment Rules:**
• **HIGH Priority**: Weak topics (<40% accuracy) with high exam weightage (>15% of paper)
• **MEDIUM Priority**: Moderate topics (40-60% accuracy) or weak topics with medium weightage
• **LOW Priority**: Topics with >60% accuracy or very low exam weightage

**Study Hour Estimation Guidelines:**
• Weak topic (0-40% accuracy): 10-20 hours (conceptual learning + practice)
• Moderate topic (40-60% accuracy): 5-10 hours (targeted practice + problem-solving)
• Refinement (60-75% accuracy): 2-5 hours (advanced problems + speed improvement)
• Very weak foundational topic: 15-25 hours (basics to advanced)

{exam_instructions}

**Pattern Detection Tips:**
• Compare accuracy across difficulty levels (Easy vs Hard)
• Compare accuracy across question types (MCQ vs Numerical)
• Look for time management issues (too fast = careless, too slow = concept gaps)
• Identify subject-specific trends
• Note consistency patterns (consistent vs erratic performance)"""


def _get_exam_specific_instructions(exam_type: ExamType) -> str:
    """Get exam-specific analysis instructions."""
    if exam_type == "JEE_MAIN":
        return """**JEE Main Specific Guidelines:**
• JEE Main weightage: Physics (30), Chemistry (30), Mathematics (30) - equal importance
• Focus on fundamental concepts and direct applications
• Single correct MCQs require speed and accuracy balance
• Negative marking (-1 for wrong answer) - consider attempt strategy
• Key high-weightage topics:
  - Mathematics: Calculus (30%), Algebra (25%), Coordinate Geometry (20%)
  - Physics: Mechanics (35%), Electromagnetism (25%), Modern Physics (15%)
  - Chemistry: Physical Chemistry (35%), Inorganic Chemistry (35%), Organic Chemistry (30%)
• Recommend daily practice of 20-30 questions per subject
• Typical preparation timeline: 6-12 months for thorough coverage"""
    
    elif exam_type == "JEE_ADVANCED":
        return """**JEE Advanced Specific Guidelines:**
• JEE Advanced requires deep conceptual understanding and problem-solving skills
• Multiple question types: Single correct, Multiple correct, Numerical, Matrix match
• Emphasis on multi-concept integration and complex scenarios
• Negative marking varies by question type (mention in recommendations)
• Key challenging topics:
  - Mathematics: Calculus applications, 3D Geometry, Complex Numbers
  - Physics: Mechanics (advanced), Electromagnetism (circuit analysis), Thermodynamics
  - Chemistry: Physical Chemistry (numerical), Organic reactions, Coordination compounds
• Recommend solving previous years' papers and mock tests
• Focus on conceptual clarity before attempting difficult problems
• Typical preparation timeline: 12-18 months with strong foundation"""
    
    elif exam_type == "NEET":
        return """**NEET Specific Guidelines:**
• NEET weightage: Physics (45), Chemistry (45), Biology (90) - Biology is 50% of paper
• Focus on NCERT mastery (especially Biology)
• Single correct MCQs with negative marking (-1 for wrong answer)
• Key high-weightage topics:
  - Biology: Human Physiology (25%), Genetics & Evolution (20%), Plant Physiology (15%)
  - Chemistry: Organic Chemistry (40%), Physical Chemistry (35%), Inorganic Chemistry (25%)
  - Physics: Mechanics (30%), Electrodynamics (25%), Optics & Modern Physics (25%)
• Biology requires extensive memorization + concept clarity
• Recommend NCERT multiple readings and diagram practice
• Typical preparation timeline: 12-18 months with Biology focus"""
    
    else:
        return "**General Guidelines:**\n• Focus on exam-specific patterns and weightages\n• Provide topic-specific recommendations"


def _build_examples_section(exam_type: ExamType) -> str:
    """Build the examples section with sample analytics."""
    example1 = {
        "strengths": [
            {
                "topic": "Calculus - Differentiation",
                "subject": "Mathematics",
                "accuracy": 92.5,
                "reason": "Strong conceptual understanding of derivative rules and chain rule applications. Consistent performance across all difficulty levels shows mastery of fundamentals and problem-solving skills.",
                "recommendation": "Leverage this strength by attempting advanced JEE Advanced level problems involving multiple concepts. Practice application of calculus in physics problems to strengthen inter-subject connections."
            },
            {
                "topic": "Mechanics - Newton's Laws",
                "subject": "Physics",
                "accuracy": 87.5,
                "reason": "Excellent grasp of fundamental concepts with good application skills in free body diagrams and force analysis. Quick problem-solving indicates strong practice.",
                "recommendation": "Maintain this strength through regular practice of 5-10 mechanics problems weekly. Focus on time optimization to solve problems in under 2 minutes."
            }
        ],
        "weaknesses": [
            {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "accuracy": 28.5,
                "reason": "Significant conceptual gaps in understanding the first and second laws of thermodynamics. Struggled with heat engine problems and entropy calculations, indicating weak foundation in the topic.",
                "priority": "HIGH",
                "estimated_study_hours": 15.0,
                "recommendation": "Start with NCERT basics on laws of thermodynamics. Watch 3-4 video lectures on heat engines and entropy. Solve 100+ graded problems starting from basic to advanced. Create formula sheets and concept maps. Dedicate 2 hours daily for next 2 weeks."
            },
            {
                "topic": "Coordination Compounds",
                "subject": "Chemistry",
                "accuracy": 45.0,
                "reason": "Moderate understanding with confusion in nomenclature, isomerism, and bonding theories. Careless mistakes in identifying oxidation states and geometry.",
                "priority": "MEDIUM",
                "estimated_study_hours": 8.0,
                "recommendation": "Revise IUPAC nomenclature rules thoroughly. Practice 50 problems on isomerism identification. Create flashcards for common ligands and their properties. Focus on CFT and VBT theory differences. Daily practice of 10-15 questions for 1 week."
            }
        ],
        "learning_patterns": [
            "Strong preference for calculus-based questions with 85% accuracy, but struggles with geometry and vectors (45% accuracy). This indicates comfort with analytical thinking but need for spatial visualization practice.",
            "Time management issue detected: Spending too much time on difficult questions (>5 minutes) while rushing through easy questions (<1 minute). This led to careless mistakes in easy questions and incomplete hard questions.",
            "Subject consistency: Mathematics shows stable performance (75-90%), but Physics varies widely (25-85%) across topics, indicating uneven preparation in Physics.",
            "Difficulty pattern: Easy questions accuracy is 95%, but drops sharply to 35% for hard questions. This suggests need for conceptual depth and advanced problem-solving practice rather than just formula memorization."
        ],
        "overall_assessment": "Currently at intermediate preparation level with strong foundations in Mathematics (especially Calculus) and moderate Physics understanding. Chemistry preparation is uneven with significant gaps in coordination chemistry and organic reactions. Critical weakness in Thermodynamics needs immediate attention as it carries 10-12% weightage in JEE. Overall trajectory is positive, but requires focused effort on identified weak areas in next 2-3 months to reach competitive scores.",
        "study_strategy": "Immediate priority (Next 2-4 weeks): Dedicate 60% time to Thermodynamics and Coordination Compounds with daily practice of 20-30 problems. Allocate 30% time to maintaining Mathematics strength through JEE Advanced level problems. Remaining 10% for quick revision of strong topics. Medium-term (Next 2-3 months): Balance preparation across all three subjects with 40% Physics (focus on weak topics), 30% Chemistry (organic reactions + physical chemistry numericals), 30% Mathematics (geometry and vectors improvement). Daily routine: 2 hours Physics (including 1 hour Thermodynamics), 1.5 hours Chemistry, 1.5 hours Mathematics, plus 1 hour for mock tests and revision. Weekly: Attempt 2 full-length mock tests and analyze mistakes thoroughly. Monthly: Review progress in weak topics and adjust study hours accordingly."
    }
    
    return f"""=== EXAMPLES (for reference - adapt to actual student data) ===

Example Analytics Output for {exam_type}:

```json
{json.dumps(example1, indent=2)}
```

KEY OBSERVATIONS IN THIS EXAMPLE:
• Strengths: Specific topics with accuracy, clear reasons, actionable recommendations
• Weaknesses: Root cause analysis, realistic study hours (15h for critical gap, 8h for moderate), specific action steps
• Patterns: Evidence-based observations with data support
• Assessment: Holistic view covering current level, trajectory, and critical priorities
• Strategy: Detailed timeline (immediate vs medium-term), specific time allocations, daily/weekly/monthly breakdown

YOUR OUTPUT SHOULD FOLLOW THIS STRUCTURE but with insights from the actual test data provided above."""


def _build_validation_section() -> str:
    """Build the self-validation checklist section."""
    return """=== VALIDATION CHECKLIST (Review before finalizing) ===

Before generating output, verify:

✓ **Data Accuracy:**
  - All topic names match those in the test context
  - Accuracy percentages are from actual test data
  - Subject names are correct (Physics, Chemistry, Mathematics, Biology)

✓ **Completeness:**
  - All required JSON fields are present
  - No placeholder or generic text remains
  - 3-5 strengths and 5-8 weaknesses identified
  - 3-5 learning patterns detected
  - Overall assessment is 3-4 sentences
  - Study strategy is 4-6 sentences with timeline

✓ **Specificity:**
  - Recommendations are actionable (not generic)
  - Study hours are realistic and topic-specific
  - Priorities align with exam weightage
  - Examples of specific problems/resources mentioned where applicable

✓ **Quality:**
  - Language is encouraging yet honest
  - Evidence supports every claim
  - Recommendations are implementable
  - JSON is properly formatted and parseable

✓ **Consistency:**
  - Priority levels match severity and exam importance
  - Study hours align with weakness severity
  - Patterns are consistent with raw data
  - No contradictions between sections"""


# Helper function for quick analytics generation
def build_quick_analytics_prompt(
    context: str,
    exam_type: ExamType = "JEE_MAIN"
) -> str:
    """
    Build a simplified analytics prompt without examples for faster generation.
    
    Use this for quick analytics when token limits are tight or when
    examples are not needed.
    
    Args:
        context: Formatted test results context
        exam_type: Type of exam
    
    Returns:
        Simplified prompt string
    
    Example:
        >>> prompt = build_quick_analytics_prompt(context, "NEET")
    """
    return build_analytics_prompt(
        context=context,
        exam_type=exam_type,
        student_name=None,
        include_examples=False,
        max_strengths=3,
        max_weaknesses=5
    )


# Helper function to get expected output schema
def get_analytics_output_schema() -> Dict:
    """
    Get the expected JSON schema for analytics output.
    
    Useful for validation and documentation.
    
    Returns:
        Dictionary representing the expected JSON structure
    
    Example:
        >>> schema = get_analytics_output_schema()
        >>> print(json.dumps(schema, indent=2))
    """
    return {
        "strengths": [
            {
                "topic": "string",
                "subject": "string",
                "accuracy": "number (0-100)",
                "reason": "string (2-3 sentences)",
                "recommendation": "string (1-2 sentences)"
            }
        ],
        "weaknesses": [
            {
                "topic": "string",
                "subject": "string",
                "accuracy": "number (0-100)",
                "reason": "string (2-3 sentences)",
                "priority": "string (HIGH|MEDIUM|LOW)",
                "estimated_study_hours": "number (0.5-40)",
                "recommendation": "string (2-3 sentences)"
            }
        ],
        "learning_patterns": [
            "string (pattern description with evidence)"
        ],
        "overall_assessment": "string (3-4 sentences)",
        "study_strategy": "string (4-6 sentences with timeline)"
    }


# Validation function
def validate_analytics_output(analytics_json: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate analytics output against expected schema.
    
    Args:
        analytics_json: Parsed JSON analytics output
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if valid, False otherwise
        - error_message: None if valid, error description if invalid
    
    Example:
        >>> is_valid, error = validate_analytics_output(response_json)
        >>> if not is_valid:
        ...     print(f"Validation error: {error}")
    """
    # Check required top-level keys
    required_keys = [
        "strengths", "weaknesses", "learning_patterns",
        "overall_assessment", "study_strategy"
    ]
    
    for key in required_keys:
        if key not in analytics_json:
            return False, f"Missing required field: {key}"
    
    # Validate strengths
    if not isinstance(analytics_json["strengths"], list):
        return False, "'strengths' must be a list"
    
    for i, strength in enumerate(analytics_json["strengths"]):
        required_fields = ["topic", "subject", "accuracy", "reason", "recommendation"]
        for field in required_fields:
            if field not in strength:
                return False, f"Strength {i}: Missing field '{field}'"
        
        if not isinstance(strength["accuracy"], (int, float)):
            return False, f"Strength {i}: 'accuracy' must be a number"
        
        if not 0 <= strength["accuracy"] <= 100:
            return False, f"Strength {i}: 'accuracy' must be between 0 and 100"
    
    # Validate weaknesses
    if not isinstance(analytics_json["weaknesses"], list):
        return False, "'weaknesses' must be a list"
    
    for i, weakness in enumerate(analytics_json["weaknesses"]):
        required_fields = [
            "topic", "subject", "accuracy", "reason",
            "priority", "estimated_study_hours", "recommendation"
        ]
        for field in required_fields:
            if field not in weakness:
                return False, f"Weakness {i}: Missing field '{field}'"
        
        if not isinstance(weakness["accuracy"], (int, float)):
            return False, f"Weakness {i}: 'accuracy' must be a number"
        
        if not 0 <= weakness["accuracy"] <= 100:
            return False, f"Weakness {i}: 'accuracy' must be between 0 and 100"
        
        if weakness["priority"] not in ["HIGH", "MEDIUM", "LOW"]:
            return False, f"Weakness {i}: 'priority' must be HIGH, MEDIUM, or LOW"
        
        if not isinstance(weakness["estimated_study_hours"], (int, float)):
            return False, f"Weakness {i}: 'estimated_study_hours' must be a number"
        
        if weakness["estimated_study_hours"] < 0:
            return False, f"Weakness {i}: 'estimated_study_hours' must be non-negative"
    
    # Validate learning patterns
    if not isinstance(analytics_json["learning_patterns"], list):
        return False, "'learning_patterns' must be a list"
    
    # Validate text fields
    if not isinstance(analytics_json["overall_assessment"], str):
        return False, "'overall_assessment' must be a string"
    
    if not isinstance(analytics_json["study_strategy"], str):
        return False, "'study_strategy' must be a string"
    
    return True, None
