"""
Schedule Context Builder for Gemini Scheduling Prompts - Mentor AI Platform.

This module builds structured context strings from analytics data, student profiles,
and scheduling constraints to create effective prompts for Gemini Flash AI model
for generating personalized study schedules.

Functions:
- build_student_context: Format student profile and exam information
- build_analytics_context: Format analytics summary with key insights
- build_priority_context: Format priority topics ranked by impact
- build_weightages_context: Format syllabus weightages by subject
- build_constraints_context: Format time and scheduling constraints
- build_complete_context: Combine all context sections into complete prompt
- format_topic_list: Helper to format topic lists consistently
- format_date: Helper to format dates in readable format

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from datetime import date
    >>> from utils.schedule_context_builder import (
    ...     build_student_context,
    ...     build_complete_context
    ... )
    >>> 
    >>> # Build student context
    >>> student_profile = {
    ...     "student_id": "student_123",
    ...     "exam_type": "JEE_MAIN",
    ...     "exam_date": date(2024, 4, 1),
    ...     "daily_study_hours": 5.0
    ... }
    >>> student_ctx = build_student_context(student_profile)
    >>> print(student_ctx)
    STUDENT PROFILE:
    - Student ID: student_123
    - Exam: JEE_MAIN
    - Exam Date: April 01, 2024 (75 days from now)
    - Daily Study Hours: 5.0 hours
    - Total Available Study Hours: 337.5 hours
    >>> 
    >>> # Build complete context for Gemini
    >>> complete_prompt = build_complete_context(
    ...     student_profile=student_profile,
    ...     analytics_data=analytics,
    ...     priority_topics=priorities,
    ...     weightages=weightages,
    ...     constraints=constraints
    ... )
    >>> # Send complete_prompt to Gemini Flash
"""

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class ContextSection(str, Enum):
    """Context section identifiers."""
    STUDENT = "student"
    ANALYTICS = "analytics"
    PRIORITIES = "priorities"
    WEIGHTAGES = "weightages"
    CONSTRAINTS = "constraints"
    TASK = "task"


def format_date(target_date: date, include_relative: bool = True) -> str:
    """
    Format date in readable format with optional relative time.
    
    Args:
        target_date: Date to format
        include_relative: Whether to include "X days from now" (default: True)
    
    Returns:
        Formatted date string
    
    Example:
        >>> from datetime import date, timedelta
        >>> future_date = date.today() + timedelta(days=75)
        >>> formatted = format_date(future_date)
        >>> print(formatted)
        April 01, 2024 (75 days from now)
        
        >>> formatted_simple = format_date(future_date, include_relative=False)
        >>> print(formatted_simple)
        April 01, 2024
    """
    # Format: "April 01, 2024"
    formatted = target_date.strftime("%B %d, %Y")
    
    if include_relative:
        # Calculate days from today
        days_diff = (target_date - date.today()).days
        
        if days_diff < 0:
            relative = f"{abs(days_diff)} days ago"
        elif days_diff == 0:
            relative = "today"
        elif days_diff == 1:
            relative = "tomorrow"
        else:
            relative = f"{days_diff} days from now"
        
        formatted = f"{formatted} ({relative})"
    
    return formatted


def format_topic_list(
    topics: List[Dict[str, Any]],
    max_topics: Optional[int] = None,
    include_metadata: bool = True,
    indent: int = 0
) -> str:
    """
    Format list of topics consistently with metadata.
    
    Args:
        topics: List of topic dicts with keys like 'topic', 'subject', 'accuracy', etc.
        max_topics: Maximum number of topics to include (None for all)
        include_metadata: Whether to include additional metadata (default: True)
        indent: Number of spaces to indent each line (default: 0)
    
    Returns:
        Formatted topic list string
    
    Example:
        >>> topics = [
        ...     {"topic": "Thermodynamics", "subject": "Physics", "accuracy": 25.0, "weightage": 4.0},
        ...     {"topic": "Calculus", "subject": "Math", "accuracy": 60.0, "weightage": 6.0}
        ... ]
        >>> formatted = format_topic_list(topics, max_topics=2)
        >>> print(formatted)
        1. Thermodynamics (Physics) - Accuracy: 25.0%, Weightage: 4.0%
        2. Calculus (Math) - Accuracy: 60.0%, Weightage: 6.0%
    """
    if not topics:
        return f"{' ' * indent}(No topics)"
    
    # Limit topics if specified
    display_topics = topics[:max_topics] if max_topics else topics
    truncated = len(topics) > len(display_topics) if max_topics else False
    
    lines = []
    indent_str = ' ' * indent
    
    for i, topic in enumerate(display_topics, 1):
        # Basic format: "1. Topic Name (Subject)"
        topic_name = topic.get('topic', 'Unknown Topic')
        subject = topic.get('subject', 'Unknown')
        line = f"{indent_str}{i}. {topic_name} ({subject})"
        
        # Add metadata if requested
        if include_metadata:
            metadata_parts = []
            
            if 'accuracy' in topic:
                metadata_parts.append(f"Accuracy: {topic['accuracy']:.1f}%")
            
            if 'current_accuracy' in topic:
                metadata_parts.append(f"Accuracy: {topic['current_accuracy']:.1f}%")
            
            if 'weightage' in topic:
                metadata_parts.append(f"Weightage: {topic['weightage']:.1f}%")
            
            if 'priority_score' in topic:
                metadata_parts.append(f"Priority: {topic['priority_score']:.0f}")
            
            if 'estimated_hours' in topic:
                metadata_parts.append(f"Est. Hours: {topic['estimated_hours']:.1f}h")
            
            if metadata_parts:
                line += f" - {', '.join(metadata_parts)}"
        
        lines.append(line)
    
    # Add truncation note if applicable
    if truncated:
        remaining = len(topics) - len(display_topics)
        lines.append(f"{indent_str}... and {remaining} more topics")
    
    return '\n'.join(lines)


def build_student_context(student_profile: Dict[str, Any]) -> str:
    """
    Build student profile context section.
    
    Args:
        student_profile: Dict with keys:
            - student_id: Student identifier
            - exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            - exam_date: Date of exam
            - daily_study_hours: Hours available per day
            - preferences: Optional dict of preferences
    
    Returns:
        Formatted student context string
    
    Example:
        >>> from datetime import date, timedelta
        >>> profile = {
        ...     "student_id": "student_123",
        ...     "exam_type": "JEE_MAIN",
        ...     "exam_date": date.today() + timedelta(days=75),
        ...     "daily_study_hours": 5.0,
        ...     "preferences": {"preferred_subjects": ["Physics"]}
        ... }
        >>> context = build_student_context(profile)
        >>> print(context)
        STUDENT PROFILE:
        - Student ID: student_123
        - Exam: JEE_MAIN
        - Exam Date: April 01, 2024 (75 days from now)
        - Days Until Exam: 75 days
        - Daily Study Hours: 5.0 hours
        - Total Available Study Hours: ~337.5 hours
        - Preferences: Preferred subjects: Physics
    """
    student_id = student_profile.get('student_id', 'Unknown')
    exam_type = student_profile.get('exam_type', 'Unknown')
    exam_date = student_profile.get('exam_date')
    daily_hours = student_profile.get('daily_study_hours', 0.0)
    preferences = student_profile.get('preferences', {})
    
    # Calculate days until exam
    days_until_exam = 0
    if exam_date:
        if isinstance(exam_date, str):
            exam_date = datetime.strptime(exam_date, "%Y-%m-%d").date()
        days_until_exam = (exam_date - date.today()).days
    
    # Calculate total available hours (with 10% buffer reduction)
    total_hours = days_until_exam * daily_hours * 0.9  # 10% buffer
    
    # Build context string
    lines = [
        "STUDENT PROFILE:",
        f"- Student ID: {student_id}",
        f"- Exam: {exam_type}",
    ]
    
    if exam_date:
        lines.append(f"- Exam Date: {format_date(exam_date)}")
        lines.append(f"- Days Until Exam: {days_until_exam} days")
    
    lines.extend([
        f"- Daily Study Hours: {daily_hours:.1f} hours",
        f"- Total Available Study Hours: ~{total_hours:.1f} hours (with 10% buffer)",
    ])
    
    # Add preferences if present
    if preferences:
        pref_parts = []
        if 'preferred_subjects' in preferences:
            subjects = ', '.join(preferences['preferred_subjects'])
            pref_parts.append(f"Preferred subjects: {subjects}")
        if 'morning_study' in preferences and preferences['morning_study']:
            pref_parts.append("Prefers morning study sessions")
        if 'avoid_evenings' in preferences and preferences['avoid_evenings']:
            pref_parts.append("Avoids evening study")
        
        if pref_parts:
            lines.append(f"- Preferences: {'; '.join(pref_parts)}")
    
    context = '\n'.join(lines)
    logger.info(f"Built student context for {student_id}")
    
    return context


def build_analytics_context(analytics_data: Dict[str, Any]) -> str:
    """
    Build analytics summary context section.
    
    Args:
        analytics_data: Dict with keys:
            - overall_score: Total score obtained
            - max_score: Maximum possible score
            - percentage: Overall percentage
            - accuracy: Overall accuracy
            - subject_scores: Dict of subject-wise scores
            - strong_topics: List of strong topic dicts
            - weak_topics: List of weak topic dicts
            - insights: Optional AI insights
    
    Returns:
        Formatted analytics context string
    
    Example:
        >>> analytics = {
        ...     "overall_score": 62,
        ...     "max_score": 120,
        ...     "percentage": 51.7,
        ...     "accuracy": 64.3,
        ...     "subject_scores": {"Physics": 45.0, "Chemistry": 52.0, "Math": 58.0},
        ...     "strong_topics": [{"topic": "Algebra", "subject": "Math", "accuracy": 85.0}],
        ...     "weak_topics": [{"topic": "Thermodynamics", "subject": "Physics", "accuracy": 25.0}]
        ... }
        >>> context = build_analytics_context(analytics)
        >>> print(context)
        ANALYTICS SUMMARY:
        - Overall Score: 62/120 (51.7%)
        - Overall Accuracy: 64.3%
        ...
    """
    overall_score = analytics_data.get('overall_score', 0)
    max_score = analytics_data.get('max_score', 100)
    percentage = analytics_data.get('percentage', 0.0)
    accuracy = analytics_data.get('accuracy', 0.0)
    subject_scores = analytics_data.get('subject_scores', {})
    strong_topics = analytics_data.get('strong_topics', [])
    weak_topics = analytics_data.get('weak_topics', [])
    insights = analytics_data.get('insights', '')
    
    lines = [
        "ANALYTICS SUMMARY:",
        f"- Overall Score: {overall_score}/{max_score} ({percentage:.1f}%)",
        f"- Overall Accuracy: {accuracy:.1f}%",
        ""
    ]
    
    # Add subject-wise performance
    if subject_scores:
        lines.append("Subject-wise Performance:")
        for subject, score in subject_scores.items():
            lines.append(f"  • {subject}: {score:.1f}%")
        lines.append("")
    
    # Add strong topics
    if strong_topics:
        lines.append(f"Strong Topics (Top {min(5, len(strong_topics))}):")
        formatted_strong = format_topic_list(
            strong_topics[:5],
            include_metadata=True,
            indent=2
        )
        lines.append(formatted_strong)
        lines.append("")
    
    # Add weak topics
    if weak_topics:
        lines.append(f"Weak Topics Requiring Attention (Top {min(10, len(weak_topics))}):")
        formatted_weak = format_topic_list(
            weak_topics[:10],
            include_metadata=True,
            indent=2
        )
        lines.append(formatted_weak)
        lines.append("")
    
    # Add AI insights if available
    if insights:
        lines.append("Key Insights:")
        lines.append(f"  {insights}")
    
    context = '\n'.join(lines)
    logger.info("Built analytics context")
    
    return context


def build_priority_context(priority_topics: List[Dict[str, Any]], top_n: int = 20) -> str:
    """
    Build priority topics context section.
    
    Args:
        priority_topics: List of priority topic dicts with keys:
            - topic: Topic name
            - subject: Subject name
            - priority_score: Priority score
            - priority_level: Priority level label
            - current_accuracy: Current accuracy
            - target_accuracy: Target accuracy
            - weightage: Exam weightage
            - estimated_hours: Estimated study hours
        top_n: Number of top topics to include (default: 20)
    
    Returns:
        Formatted priority topics context string
    
    Example:
        >>> priorities = [
        ...     {
        ...         "topic": "Thermodynamics",
        ...         "subject": "Physics",
        ...         "priority_score": 300.0,
        ...         "priority_level": "critical",
        ...         "current_accuracy": 25.0,
        ...         "weightage": 4.0,
        ...         "estimated_hours": 12.0
        ...     }
        ... ]
        >>> context = build_priority_context(priorities)
        >>> print(context)
        PRIORITY TOPICS (Ranked by Impact):
        These topics have been ranked by priority score...
    """
    if not priority_topics:
        return "PRIORITY TOPICS:\n  (No priority topics available)"
    
    # Limit to top N topics
    display_topics = priority_topics[:top_n]
    
    lines = [
        "PRIORITY TOPICS (Ranked by Impact):",
        f"These topics have been ranked by priority score (Weightage × Accuracy Gap × Difficulty).",
        f"Focus on high-priority topics first, especially those marked as CRITICAL or HIGH.",
        ""
    ]
    
    # Group by priority level
    critical = [t for t in display_topics if t.get('priority_level') == 'critical']
    high = [t for t in display_topics if t.get('priority_level') == 'high']
    medium = [t for t in display_topics if t.get('priority_level') == 'medium']
    low = [t for t in display_topics if t.get('priority_level') == 'low']
    
    # Add critical topics
    if critical:
        lines.append(f"CRITICAL PRIORITY ({len(critical)} topics):")
        for i, topic in enumerate(critical, 1):
            lines.append(
                f"  {i}. {topic['topic']} ({topic['subject']}) - "
                f"Accuracy: {topic.get('current_accuracy', 0):.1f}%, "
                f"Weightage: {topic.get('weightage', 0):.1f}%, "
                f"Priority Score: {topic['priority_score']:.0f}, "
                f"Est. Hours: {topic.get('estimated_hours', 0):.1f}h"
            )
        lines.append("")
    
    # Add high priority topics
    if high:
        lines.append(f"HIGH PRIORITY ({len(high)} topics):")
        for i, topic in enumerate(high, 1):
            lines.append(
                f"  {i}. {topic['topic']} ({topic['subject']}) - "
                f"Accuracy: {topic.get('current_accuracy', 0):.1f}%, "
                f"Weightage: {topic.get('weightage', 0):.1f}%, "
                f"Priority Score: {topic['priority_score']:.0f}, "
                f"Est. Hours: {topic.get('estimated_hours', 0):.1f}h"
            )
        lines.append("")
    
    # Add medium priority topics (condensed)
    if medium:
        lines.append(f"MEDIUM PRIORITY ({len(medium)} topics):")
        medium_topics_str = ", ".join([f"{t['topic']} ({t['subject']})" for t in medium[:5]])
        lines.append(f"  {medium_topics_str}")
        if len(medium) > 5:
            lines.append(f"  ... and {len(medium) - 5} more")
        lines.append("")
    
    # Add low priority topics (just count)
    if low:
        lines.append(f"LOW PRIORITY: {len(low)} topics (can be covered if time permits)")
        lines.append("")
    
    # Add summary statistics
    total_estimated_hours = sum(t.get('estimated_hours', 0) for t in display_topics)
    lines.append(f"Total Estimated Hours for Top {len(display_topics)} Topics: {total_estimated_hours:.1f}h")
    
    context = '\n'.join(lines)
    logger.info(f"Built priority context with {len(display_topics)} topics")
    
    return context


def build_weightages_context(weightages: Dict[str, Dict[str, Any]]) -> str:
    """
    Build syllabus weightages context section.
    
    Args:
        weightages: Dict mapping (subject, topic) to weightage info:
            {
                ("Physics", "Thermodynamics"): {"weightage": 4.0, "difficulty": "medium"},
                ...
            }
    
    Returns:
        Formatted weightages context string
    
    Example:
        >>> weightages = {
        ...     ("Physics", "Thermodynamics"): {"weightage": 4.0, "difficulty": "medium"},
        ...     ("Physics", "Mechanics"): {"weightage": 6.0, "difficulty": "hard"},
        ...     ("Chemistry", "Organic"): {"weightage": 5.0, "difficulty": "medium"}
        ... }
        >>> context = build_weightages_context(weightages)
        >>> print(context)
        SYLLABUS WEIGHTAGES:
        ...
    """
    if not weightages:
        return "SYLLABUS WEIGHTAGES:\n  (No weightage data available)"
    
    lines = [
        "SYLLABUS WEIGHTAGES:",
        "Distribution of topics by exam weightage (higher = more important).",
        ""
    ]
    
    # Group by subject
    subjects = {}
    for (subject, topic), info in weightages.items():
        if subject not in subjects:
            subjects[subject] = []
        subjects[subject].append({
            'topic': topic,
            'weightage': info.get('weightage', 0.0),
            'difficulty': info.get('difficulty', 'medium')
        })
    
    # Sort subjects alphabetically
    for subject in sorted(subjects.keys()):
        topics = subjects[subject]
        # Sort topics by weightage (descending)
        topics.sort(key=lambda x: x['weightage'], reverse=True)
        
        lines.append(f"{subject}:")
        
        # Show top topics with weightage
        for topic in topics[:10]:  # Top 10 per subject
            lines.append(
                f"  • {topic['topic']}: {topic['weightage']:.1f}% "
                f"(Difficulty: {topic['difficulty']})"
            )
        
        if len(topics) > 10:
            lines.append(f"  ... and {len(topics) - 10} more topics")
        
        lines.append("")
    
    context = '\n'.join(lines)
    logger.info(f"Built weightages context for {len(subjects)} subjects")
    
    return context


def build_constraints_context(constraints: Dict[str, Any]) -> str:
    """
    Build scheduling constraints context section.
    
    Args:
        constraints: Dict with keys:
            - total_days: Total days available
            - daily_hours: Daily study hours
            - total_hours: Total available hours
            - revision_days: List of revision day numbers
            - practice_test_days: List of practice test day numbers
            - buffer_days: List of buffer day numbers
            - must_cover_critical: Whether all critical topics must be covered
            - balance_subjects: Whether to balance subjects daily
    
    Returns:
        Formatted constraints context string
    
    Example:
        >>> constraints = {
        ...     "total_days": 75,
        ...     "daily_hours": 5.0,
        ...     "total_hours": 337.5,
        ...     "revision_days": [68, 69, 70, 71, 72, 73, 74, 75],
        ...     "practice_test_days": [7, 14, 21, 28, 35, 42, 49, 56, 63, 70],
        ...     "buffer_days": [30, 60],
        ...     "must_cover_critical": True,
        ...     "balance_subjects": True
        ... }
        >>> context = build_constraints_context(constraints)
        >>> print(context)
        SCHEDULING CONSTRAINTS:
        ...
    """
    total_days = constraints.get('total_days', 0)
    daily_hours = constraints.get('daily_hours', 0.0)
    total_hours = constraints.get('total_hours', 0.0)
    revision_days = constraints.get('revision_days', [])
    practice_test_days = constraints.get('practice_test_days', [])
    buffer_days = constraints.get('buffer_days', [])
    must_cover_critical = constraints.get('must_cover_critical', True)
    balance_subjects = constraints.get('balance_subjects', True)
    
    lines = [
        "SCHEDULING CONSTRAINTS:",
        ""
    ]
    
    # Time constraints
    lines.extend([
        "Time Allocation:",
        f"  • Total Days Available: {total_days} days",
        f"  • Daily Study Hours: {daily_hours:.1f} hours",
        f"  • Total Available Hours: {total_hours:.1f} hours",
        ""
    ])
    
    # Special days
    lines.append("Special Days:")
    
    if revision_days:
        rev_days_str = f"Days {min(revision_days)}-{max(revision_days)}" if len(revision_days) > 3 else ", ".join(map(str, revision_days))
        lines.append(f"  • Revision Days: {rev_days_str} ({len(revision_days)} days)")
    
    if practice_test_days:
        test_days_str = ", ".join(map(str, practice_test_days[:5]))
        if len(practice_test_days) > 5:
            test_days_str += f", ... ({len(practice_test_days)} total)"
        lines.append(f"  • Practice Test Days: {test_days_str}")
    
    if buffer_days:
        buffer_days_str = ", ".join(map(str, buffer_days))
        lines.append(f"  • Buffer Days: {buffer_days_str} (for catch-up)")
    
    lines.append("")
    
    # Scheduling rules
    lines.append("Scheduling Rules:")
    
    if must_cover_critical:
        lines.append("  • MUST cover all CRITICAL priority topics")
    
    lines.append("  • Prioritize topics with highest priority scores")
    
    if balance_subjects:
        lines.append("  • Balance subjects across days (mix Physics, Chemistry, Math/Biology)")
    
    lines.extend([
        "  • Allocate more time to weak topics (low accuracy)",
        "  • Space out similar topics (avoid topic fatigue)",
        "  • Place harder topics during peak hours",
        "  • Include regular practice and revision",
        "  • Build progressive difficulty (easier → harder)",
        ""
    ])
    
    # Additional guidelines
    lines.extend([
        "Schedule Quality Guidelines:",
        "  • Each day should have 2-4 different topics",
        "  • Topics should have clear, measurable goals",
        "  • Include practice problems and concept review",
        "  • Provide specific resources (chapters, question types)",
        "  • Ensure realistic time estimates per topic"
    ])
    
    context = '\n'.join(lines)
    logger.info("Built constraints context")
    
    return context


def build_complete_context(
    student_profile: Dict[str, Any],
    analytics_data: Dict[str, Any],
    priority_topics: List[Dict[str, Any]],
    weightages: Dict[str, Dict[str, Any]],
    constraints: Dict[str, Any],
    include_task_description: bool = True
) -> str:
    """
    Build complete context prompt for Gemini Flash.
    
    Combines all context sections in logical order and adds task description
    and output format requirements.
    
    Args:
        student_profile: Student profile information
        analytics_data: Analytics summary and insights
        priority_topics: Ranked priority topics
        weightages: Syllabus weightages
        constraints: Scheduling constraints
        include_task_description: Whether to include task and output format (default: True)
    
    Returns:
        Complete prompt string ready for Gemini Flash
    
    Example:
        >>> complete_prompt = build_complete_context(
        ...     student_profile=profile,
        ...     analytics_data=analytics,
        ...     priority_topics=priorities,
        ...     weightages=weightages,
        ...     constraints=constraints
        ... )
        >>> # Send to Gemini Flash for schedule generation
    """
    sections = []
    
    # Task description (if requested)
    if include_task_description:
        task_description = """
You are an AI study schedule generator for competitive exam preparation (JEE/NEET).
Your task is to create a personalized, day-by-day study schedule that maximizes 
the student's exam performance based on their current analytics and time constraints.

OBJECTIVE:
Generate an optimal study schedule that:
1. Prioritizes weak topics with high exam weightage
2. Ensures balanced subject coverage
3. Includes regular revision and practice tests
4. Fits within available time constraints
5. Follows evidence-based learning principles
"""
        sections.append(task_description.strip())
        sections.append("\n" + "="*80 + "\n")
    
    # Add context sections in logical order
    sections.append(build_student_context(student_profile))
    sections.append("\n" + "-"*80 + "\n")
    
    sections.append(build_analytics_context(analytics_data))
    sections.append("\n" + "-"*80 + "\n")
    
    sections.append(build_priority_context(priority_topics))
    sections.append("\n" + "-"*80 + "\n")
    
    sections.append(build_weightages_context(weightages))
    sections.append("\n" + "-"*80 + "\n")
    
    sections.append(build_constraints_context(constraints))
    
    # Output format requirements (if task description included)
    if include_task_description:
        output_format = """

================================================================================

OUTPUT FORMAT:

Generate a JSON schedule with the following structure:

{
  "schedule_metadata": {
    "total_days": <number>,
    "start_date": "<YYYY-MM-DD>",
    "end_date": "<YYYY-MM-DD>",
    "total_topics_covered": <number>,
    "estimated_completion_rate": "<percentage>"
  },
  "daily_schedule": [
    {
      "day_number": 1,
      "date": "<YYYY-MM-DD>",
      "subjects": ["Physics", "Chemistry"],
      "topics": [
        {
          "topic": "Thermodynamics",
          "subject": "Physics",
          "priority": "critical",
          "estimated_hours": 3.0,
          "goals": ["Understand laws of thermodynamics", "Solve 10 problems"],
          "resources": ["Chapter 12", "Previous year questions"],
          "subtopics": ["First Law", "Second Law", "Entropy"]
        }
      ],
      "total_hours": 5.0,
      "milestones": ["Complete thermodynamics basics"]
    }
  ],
  "revision_schedule": {
    "revision_days": [68, 69, 70, 71, 72, 73, 74, 75],
    "topics_to_revise": ["<topic1>", "<topic2>", ...]
  },
  "practice_tests": {
    "test_days": [7, 14, 21, 28, 35, 42, 49, 56, 63, 70],
    "test_type": "full_length" or "subject_wise"
  }
}

IMPORTANT:
- Ensure every critical priority topic is covered
- Balance subjects across days (don't focus on single subject for multiple days)
- Allocate time proportional to topic priority and difficulty
- Include specific, actionable goals for each topic
- Provide realistic time estimates
- Schedule should be comprehensive and ready to execute
"""
        sections.append(output_format)
    
    # Combine all sections
    complete_context = '\n'.join(sections)
    
    logger.info(
        f"Built complete context: {len(complete_context)} characters, "
        f"{len(complete_context.split())} words"
    )
    
    return complete_context
