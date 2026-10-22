"""
Study Center AI Prompt Templates

This module provides prompt building functions for generating AI-powered
learning materials using Google's Gemini Flash model in the Study Center
Learning Journey feature.

Functions:
- build_notes_prompt: Generate comprehensive study notes
- build_mindmap_prompt: Generate structured mind map in JSON format
- build_teaching_prompt: Generate teaching content with examples

Author: Mentor AI Team
Version: 1.0.0
"""

from typing import Dict, Any, List


def build_notes_prompt(topic: str, exam_type: str, syllabus_context: str) -> str:
    """
    Build prompt for generating comprehensive study notes.
    
    Creates a detailed prompt for Gemini to generate study notes
    that include key concepts, formulas, examples, and exam tips.
    
    Args:
        topic: Name of the topic to generate notes for
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        syllabus_context: Context from syllabus about the topic
    
    Returns:
        Complete prompt string for Gemini API
    
    Example:
        >>> prompt = build_notes_prompt(
        ...     "Kinematics",
        ...     "JEE_MAIN",
        ...     "Motion in straight line and plane..."
        ... )
    """
    return f"""You are an expert {exam_type} tutor. Generate comprehensive study notes for the topic: {topic}

Syllabus Context:
{syllabus_context}

Generate detailed notes that include:
1. Introduction and overview
2. Key concepts and definitions
3. Important formulas and equations
4. Conceptual explanations
5. Common misconceptions
6. Exam-specific tips for {exam_type}

Format the notes in clear markdown with proper headings, bullet points, and emphasis.
Focus on clarity and exam relevance. Include 2-3 worked examples with step-by-step solutions.

Make sure content is:
- Accurate and aligned with {exam_type} syllabus
- Easy to understand for students
- Focused on important concepts for exams
- Structured logically for effective learning

Notes:"""


def build_mindmap_prompt(topic: str, exam_type: str, syllabus_context: str) -> str:
    """
    Build prompt for generating structured mind map.
    
    Creates a prompt for Gemini to generate a hierarchical mind map
    in JSON format with central concept, main branches, and connections.
    
    Args:
        topic: Name of the topic to generate mind map for
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        syllabus_context: Context from syllabus about the topic
    
    Returns:
        Complete prompt string for Gemini API
    
    Example:
        >>> prompt = build_mindmap_prompt(
        ...     "Thermodynamics",
        ...     "JEE_MAIN",
        ...     "Laws of thermodynamics..."
        ... )
    """
    return f"""You are an expert {exam_type} tutor. Create a structured mind map for: {topic}

Syllabus Context:
{syllabus_context}

Generate a mind map in JSON format with the following structure:
{{
    "central_concept": "Main topic name",
    "main_branches": [
        {{
            "name": "Branch 1",
            "sub_branches": ["Sub 1.1", "Sub 1.2", "Sub 1.3"]
        }},
        {{
            "name": "Branch 2",
            "sub_branches": ["Sub 2.1", "Sub 2.2"]
        }}
    ],
    "connections": [
        {{"from": "Concept A", "to": "Concept B", "type": "implies"}},
        {{"from": "Concept C", "to": "Concept D", "type": "requires"}}
    ]
}}

Requirements:
1. Include at least 4-6 main branches
2. Each branch should have 3-5 sub-branches
3. Show important relationships between concepts
4. Use clear, concise naming for concepts
5. Ensure logical organization for {exam_type} preparation
6. Focus on concepts that frequently appear in exams

The mind map should help students:
- Visualize the topic structure
- Understand relationships between concepts
- Identify key areas to focus on
- Remember information better through visual organization

Mind Map JSON:"""


def build_teaching_prompt(topic: str, exam_type: str, difficulty: str) -> str:
    """
    Build prompt for generating teaching content with examples.
    
    Creates a prompt for Gemini to generate comprehensive teaching
    material with introduction, concepts, examples, and summary.
    
    Args:
        topic: Name of the topic to generate teaching content for
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        difficulty: Difficulty level (easy, medium, hard)
    
    Returns:
        Complete prompt string for Gemini API
    
    Example:
        >>> prompt = build_teaching_prompt(
        ...     "Calculus",
        ...     "JEE_MAIN",
        ...     "medium"
        ... )
    """
    return f"""You are an expert {exam_type} tutor teaching: {topic}

Difficulty Level: {difficulty}

Create comprehensive teaching content with:

1. INTRODUCTION (2-3 paragraphs)
   - What is this topic about?
   - Why is it important for {exam_type}?
   - Real-world applications and relevance

2. KEY CONCEPTS (4-6 concepts)
   For each concept:
   - Concept name
   - Clear explanation in simple terms
   - Visual description or analogy if applicable
   - Common mistakes to avoid

3. WORKED EXAMPLES (minimum 2)
   For each example:
   - Problem statement (similar to {exam_type} questions)
   - Step-by-step solution with reasoning
   - Key insights and exam tips
   - Alternative approaches if applicable

4. SUMMARY
   - Main takeaways from the topic
   - Important formulas to remember
   - Common mistakes students make
   - Quick revision tips for exams

Teaching style guidelines:
- Use clear, accessible language
- Include visual descriptions for abstract concepts
- Provide mnemonics or memory aids where helpful
- Emphasize concepts frequently tested in {exam_type}
- Adapt complexity to {difficulty} level
- Include practical problem-solving strategies

Format in clear markdown with proper headings and structure.
Be thorough but concise - focus on what students need to know for exams.

Teaching Content:"""


def build_syllabus_context(topic_data: Dict[str, Any]) -> str:
    """
    Build syllabus context string from topic data.
    
    Extracts relevant information from syllabus JSON to provide
    context for AI generation.
    
    Args:
        topic_data: Dictionary containing topic information from syllabus
    
    Returns:
        Formatted context string
    
    Example:
        >>> context = build_syllabus_context({
        ...     "topic_name": "Kinematics",
        ...     "description": "Motion in straight line...",
        ...     "subtopics": [...]
        ... })
    """
    context_parts = []
    
    # Add topic description
    if "description" in topic_data:
        context_parts.append(f"Topic Description: {topic_data['description']}")
    
    # Add subtopics
    if "subtopics" in topic_data:
        subtopics = topic_data["subtopics"]
        context_parts.append("Subtopics:")
        for subtopic in subtopics:
            subtopic_name = subtopic.get("subtopic_name", "")
            subtopic_content = subtopic.get("content", "")
            context_parts.append(f"- {subtopic_name}: {subtopic_content}")
    
    # Add key concepts
    if "subtopics" in topic_data:
        all_concepts = []
        for subtopic in topic_data["subtopics"]:
            if "key_concepts" in subtopic:
                all_concepts.extend(subtopic["key_concepts"])
        
        if all_concepts:
            context_parts.append(f"Key Concepts: {', '.join(all_concepts)}")
    
    # Add formulas
    if "subtopics" in topic_data:
        all_formulas = []
        for subtopic in topic_data["subtopics"]:
            if "formulas" in subtopic:
                all_formulas.extend(subtopic["formulas"])
        
        if all_formulas:
            context_parts.append(f"Important Formulas: {', '.join(all_formulas)}")
    
    return "\n\n".join(context_parts)


def build_prerequisite_check_prompt(completed_topics: List[str], current_topic: str) -> str:
    """
    Build prompt for checking topic prerequisites.
    
    Creates a prompt to verify if a student has completed
    necessary prerequisites before studying a topic.
    
    Args:
        completed_topics: List of completed topic IDs
        current_topic: Topic ID being checked
    
    Returns:
        Complete prompt string for Gemini API
    
    Example:
        >>> prompt = build_prerequisite_check_prompt(
        ...     ["T01", "T02"],
        ...     "T03"
        ... )
    """
    return f"""You are an academic advisor checking if a student is ready to study a new topic.

Completed Topics: {', '.join(completed_topics)}
Current Topic: {current_topic}

Based on typical learning sequences for JEE/NEET preparation:

1. Identify which topics from the completed list are prerequisites for {current_topic}
2. Check if any critical prerequisites are missing
3. Assess if the student is ready to proceed
4. Provide recommendations if prerequisites are incomplete

Respond with a JSON structure:
{{
    "ready_to_study": true/false,
    "missing_prerequisites": ["topic_id1", "topic_id2"],
    "completed_prerequisites": ["topic_id3", "topic_id4"],
    "recommendation": "Specific advice for the student"
}}

Consider:
- Logical dependencies between concepts
- Progressive difficulty levels
- Common learning sequences
- Essential foundations needed

Prerequisite Check:"""


def build_motivational_message(
    progress_percentage: float,
    topics_completed: int,
    total_topics: int,
    current_streak: int,
    recent_activity: str
) -> str:
    """
    Build motivational message based on student progress.
    
    Creates a personalized motivational message considering
    progress, streak, and recent activity.
    
    Args:
        progress_percentage: Overall completion percentage
        topics_completed: Number of completed topics
        total_topics: Total number of topics
        current_streak: Current study streak in days
        recent_activity: Description of recent activity
    
    Returns:
        Motivational message string
    
    Example:
        >>> message = build_motivational_message(
        ...     24.0, 12, 50, 7, "Completed Kinematics"
        ... )
    """
    if progress_percentage >= 80:
        base_message = f"Excellent work! You're {progress_percentage}% through your syllabus with {total_topics - topics_completed} topics to go!"
    elif progress_percentage >= 50:
        base_message = f"Great progress! You've completed {topics_completed} out of {total_topics} topics ({progress_percentage}%)."
    elif progress_percentage >= 25:
        base_message = f"Good start! You're making steady progress with {topics_completed} topics completed ({progress_percentage}%)."
    else:
        base_message = f"You're on your way! {topics_completed} topics completed so far. Keep building momentum!"
    
    if current_streak >= 7:
        streak_message = f" Amazing {current_streak}-day study streak! 🎉"
    elif current_streak >= 3:
        streak_message = f" Nice {current_streak}-day streak! Keep it up!"
    else:
        streak_message = ""
    
    if recent_activity:
        activity_message = f" Recently you {recent_activity.lower()}."
    else:
        activity_message = " Time to get back to studying!"
    
    motivational_message = f"{base_message}{streak_message}{activity_message}"
    
    # Add specific encouragement based on next milestone
    if progress_percentage < 25 and topics_completed > 0:
        motivational_message += " You're building a strong foundation!"
    elif 25 <= progress_percentage < 50:
        motivational_message += " Halfway to your goal is in sight!"
    elif 50 <= progress_percentage < 75:
        motivational_message += " The finish line is getting closer!"
    elif progress_percentage >= 75:
        motivational_message += " Final push to excellence!"
    
    return motivational_message


def build_parent_recommendations(
    child_progress: float,
    study_consistency: float,
    weak_areas: List[str],
    strong_areas: List[str]
) -> List[str]:
    """
    Build recommendations for parents based on child's progress.
    
    Creates actionable recommendations for parents to support
    their child's learning journey.
    
    Args:
        child_progress: Overall completion percentage
        study_consistency: Consistency score (0-1)
        weak_areas: List of topics needing attention
        strong_areas: List of topics where child excels
    
    Returns:
        List of recommendation strings
    
    Example:
        >>> recommendations = build_parent_recommendations(
        ...     24.0, 0.8, ["Thermodynamics"], ["Mechanics"]
        ... )
    """
    recommendations = []
    
    # Progress-based recommendations
    if child_progress < 25:
        recommendations.append(
            "Encourage your child to complete at least 2-3 topics per week to build momentum"
        )
    elif child_progress < 50:
        recommendations.append(
            "Your child is making good progress. Help them maintain consistent study habits"
        )
    elif child_progress < 75:
        recommendations.append(
            "Your child is advancing well. Support them in tackling more challenging topics"
        )
    else:
        recommendations.append(
            "Excellent progress! Help your child focus on revision and practice tests"
        )
    
    # Consistency-based recommendations
    if study_consistency < 0.5:
        recommendations.append(
            "Consider establishing a fixed daily study time to improve consistency"
        )
    elif study_consistency < 0.8:
        recommendations.append(
            "Good consistency! Small adjustments could make study sessions more effective"
        )
    else:
        recommendations.append(
            "Outstanding consistency! Your child has developed excellent study habits"
        )
    
    # Topic-specific recommendations
    if weak_areas:
        weak_areas_str = ", ".join(weak_areas[:2])  # Limit to 2 areas
        recommendations.append(
            f"Offer additional support for {weak_areas_str} - consider practice questions or tutoring"
        )
    
    if strong_areas:
        recommendations.append(
            f"Recognize your child's strength in {strong_areas[0]} - this builds confidence!"
        )
    
    # General recommendations
    recommendations.extend([
        "Celebrate small milestones to maintain motivation",
        "Ensure your child takes regular breaks to avoid burnout",
        "Discuss what they're learning to reinforce understanding"
    ])
    
    return recommendations[:5]  # Return top 5 recommendations