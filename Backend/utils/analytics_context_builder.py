"""
Analytics Context Builder for Gemini Flash Analysis - Mentor AI Platform.

This module provides utilities to format test results and performance analysis
into structured, LLM-readable context for Gemini Flash model analysis.

Classes:
- AnalyticsContextBuilder: Formats test results for Gemini analysis

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from models.score_models import TestScore, SubjectScore, TopicScore, QuestionScore
from models.performance_models import (
    PerformanceAnalysis,
    TopicPerformance,
    StrengthArea,
    WeaknessArea,
    DifficultyPerformance,
    QuestionTypePerformance,
    TimeManagementAnalysis,
    LearningPattern
)

logger = logging.getLogger(__name__)


class AnalyticsContextBuilder:
    """
    Formats test results and performance analysis into structured context for Gemini Flash.
    
    This class builds LLM-readable context from test scores and performance analysis,
    prioritizing the most relevant information within token limits.
    
    Attributes:
        max_tokens: Maximum tokens for context (default 3000)
        chars_per_token: Approximate characters per token (default 4)
        max_chars: Maximum characters based on token limit
    
    Example:
        >>> builder = AnalyticsContextBuilder(max_tokens=3000)
        >>> context = builder.build_context(
        ...     test_score=test_score,
        ...     performance_analysis=performance_analysis
        ... )
    """
    
    def __init__(self, max_tokens: int = 3000):
        """
        Initialize the AnalyticsContextBuilder.
        
        Args:
            max_tokens: Maximum tokens for context (default 3000)
        """
        self.max_tokens = max_tokens
        self.chars_per_token = 4  # Approximate ratio
        self.max_chars = max_tokens * self.chars_per_token
        
        logger.info(f"AnalyticsContextBuilder initialized with max_tokens={max_tokens}")
    
    def build_context(
        self,
        test_score: Optional[TestScore] = None,
        performance_analysis: Optional[PerformanceAnalysis] = None,
        include_questions: bool = False,
        prioritize_weak_topics: bool = True
    ) -> str:
        """
        Build structured context from test results for Gemini analysis.
        
        Args:
            test_score: Test score data
            performance_analysis: Performance analysis data
            include_questions: Whether to include question-level details
            prioritize_weak_topics: Prioritize weak topics in context
        
        Returns:
            Formatted context string for LLM
        
        Raises:
            ValueError: If both test_score and performance_analysis are None
        
        Example:
            >>> context = builder.build_context(
            ...     test_score=test_score,
            ...     performance_analysis=performance_analysis,
            ...     prioritize_weak_topics=True
            ... )
        """
        if test_score is None and performance_analysis is None:
            raise ValueError("At least one of test_score or performance_analysis must be provided")
        
        logger.info("Building analytics context for Gemini Flash analysis")
        
        sections = []
        
        try:
            # Section 1: Overview
            overview = self._build_overview_section(test_score, performance_analysis)
            sections.append(overview)
            
            # Section 2: Subject Analysis
            if test_score and test_score.subject_scores:
                subject_analysis = self._build_subject_analysis_section(test_score)
                sections.append(subject_analysis)
            
            # Section 3: Topic Performance
            if performance_analysis:
                topic_performance = self._build_topic_performance_section(
                    performance_analysis,
                    prioritize_weak_topics
                )
                sections.append(topic_performance)
            elif test_score and test_score.subject_scores:
                # Build from test score if no performance analysis
                topic_performance = self._build_topic_performance_from_score(
                    test_score,
                    prioritize_weak_topics
                )
                sections.append(topic_performance)
            
            # Section 4: Strengths and Weaknesses
            if performance_analysis and (performance_analysis.strengths or performance_analysis.weaknesses):
                strengths_weaknesses = self._build_strengths_weaknesses_section(performance_analysis)
                sections.append(strengths_weaknesses)
            
            # Section 5: Question Patterns
            if performance_analysis:
                patterns = self._build_question_patterns_section(performance_analysis)
                sections.append(patterns)
            
            # Section 6: Learning Patterns
            if performance_analysis and performance_analysis.patterns:
                learning_patterns = self._build_learning_patterns_section(performance_analysis)
                sections.append(learning_patterns)
            
            # Section 7: Time Management
            if performance_analysis and performance_analysis.time_management:
                time_mgmt = self._build_time_management_section(performance_analysis.time_management)
                sections.append(time_mgmt)
            
            # Section 8: Question Details (if requested and available)
            if include_questions and test_score and test_score.question_scores:
                question_details = self._build_question_details_section(
                    test_score.question_scores,
                    limit=10  # Limit to top 10 to save tokens
                )
                sections.append(question_details)
            
            # Combine sections
            context = "\n\n".join(sections)
            
            # Trim if exceeds max length
            if len(context) > self.max_chars:
                context = self._trim_context(context, sections)
            
            logger.info(f"Context built successfully: {len(context)} characters, ~{len(context)//self.chars_per_token} tokens")
            return context
            
        except Exception as e:
            logger.error(f"Error building analytics context: {str(e)}", exc_info=True)
            # Return minimal context on error
            return self._build_minimal_context(test_score, performance_analysis)
    
    def _build_overview_section(
        self,
        test_score: Optional[TestScore],
        performance_analysis: Optional[PerformanceAnalysis]
    ) -> str:
        """Build the overview section with key metrics."""
        lines = ["=== TEST PERFORMANCE OVERVIEW ===\n"]
        
        try:
            if test_score:
                lines.append(f"📊 Exam Type: {test_score.exam_type}")
                lines.append(f"📝 Total Questions: {test_score.total_questions}")
                lines.append(f"✅ Attempted: {test_score.attempted} ({test_score.attempted/test_score.total_questions*100:.1f}%)")
                lines.append(f"🎯 Correct: {test_score.correct} ({test_score.accuracy:.1f}% accuracy)")
                lines.append(f"❌ Incorrect: {test_score.incorrect}")
                if test_score.partial > 0:
                    lines.append(f"⚠️ Partial: {test_score.partial}")
                lines.append(f"⏭️ Unattempted: {test_score.unattempted}")
                lines.append(f"\n💯 Score: {test_score.total_marks_obtained}/{test_score.total_max_marks} ({test_score.percentage:.2f}%)")
                
                if test_score.time_taken:
                    hours = test_score.time_taken // 3600
                    minutes = (test_score.time_taken % 3600) // 60
                    lines.append(f"⏱️ Time Taken: {hours}h {minutes}m")
                    avg_time = test_score.time_taken / test_score.attempted if test_score.attempted > 0 else 0
                    lines.append(f"⏳ Avg Time/Question: {avg_time:.0f}s")
            
            elif performance_analysis:
                lines.append(f"📊 Exam Type: {performance_analysis.exam_type}")
                lines.append(f"🎯 Overall Accuracy: {performance_analysis.overall_accuracy:.1f}%")
                lines.append(f"💯 Score: {performance_analysis.overall_marks}/{performance_analysis.overall_max_marks}")
        
        except Exception as e:
            logger.warning(f"Error building overview section: {str(e)}")
            lines.append("⚠️ Error loading overview data")
        
        return "\n".join(lines)
    
    def _build_subject_analysis_section(self, test_score: TestScore) -> str:
        """Build subject-wise analysis section."""
        lines = ["=== SUBJECT-WISE ANALYSIS ===\n"]
        
        try:
            for subject_name, subject_score in test_score.subject_scores.items():
                lines.append(f"📚 {subject_name}:")
                lines.append(f"   • Score: {subject_score.marks_obtained}/{subject_score.max_marks} ({subject_score.accuracy:.1f}% accuracy)")
                lines.append(f"   • Questions: {subject_score.correct}✓ / {subject_score.incorrect}✗ / {subject_score.unattempted}⏭️")
                
                if subject_score.time_taken:
                    minutes = subject_score.time_taken // 60
                    lines.append(f"   • Time: {minutes}m")
                
                # Add top 3 topics if available
                if subject_score.topic_scores:
                    sorted_topics = sorted(
                        subject_score.topic_scores.items(),
                        key=lambda x: x[1].accuracy,
                        reverse=True
                    )[:3]
                    if sorted_topics:
                        lines.append("   • Top Topics:")
                        for topic_name, topic_score in sorted_topics:
                            lines.append(f"      - {topic_name}: {topic_score.accuracy:.1f}%")
                
                lines.append("")
        
        except Exception as e:
            logger.warning(f"Error building subject analysis: {str(e)}")
            lines.append("⚠️ Error loading subject data")
        
        return "\n".join(lines)
    
    def _build_topic_performance_section(
        self,
        performance_analysis: PerformanceAnalysis,
        prioritize_weak: bool
    ) -> str:
        """Build topic performance section from performance analysis."""
        lines = ["=== TOPIC PERFORMANCE ANALYSIS ===\n"]
        
        try:
            # Strong Topics
            if performance_analysis.strong_topics:
                lines.append("🌟 STRONG TOPICS (Accuracy > 80%):")
                for topic_perf in performance_analysis.strong_topics[:5]:  # Top 5
                    lines.append(
                        f"   • {topic_perf.subject} - {topic_perf.topic}: "
                        f"{topic_perf.accuracy:.1f}% "
                        f"({topic_perf.correct}/{topic_perf.total_questions})"
                    )
                    if topic_perf.gap_from_benchmark > 0:
                        lines.append(f"      ↗️ {topic_perf.gap_from_benchmark:.1f}% above benchmark")
                lines.append("")
            
            # Weak Topics (prioritized)
            if performance_analysis.weak_topics:
                lines.append("⚠️ WEAK TOPICS (Accuracy < 40%) - NEEDS IMMEDIATE ATTENTION:")
                topics_to_show = performance_analysis.weak_topics if prioritize_weak else performance_analysis.weak_topics[:5]
                for topic_perf in topics_to_show:
                    lines.append(
                        f"   • {topic_perf.subject} - {topic_perf.topic}: "
                        f"{topic_perf.accuracy:.1f}% "
                        f"({topic_perf.correct}/{topic_perf.total_questions}) "
                        f"[{topic_perf.priority_level.value.upper()} Priority]"
                    )
                    if topic_perf.gap_from_benchmark < 0:
                        lines.append(f"      ↘️ {abs(topic_perf.gap_from_benchmark):.1f}% below benchmark")
                lines.append("")
            
            # Moderate Topics
            if performance_analysis.moderate_topics:
                lines.append("📈 MODERATE TOPICS (Accuracy 40-80%):")
                for topic_perf in performance_analysis.moderate_topics[:5]:  # Top 5
                    lines.append(
                        f"   • {topic_perf.subject} - {topic_perf.topic}: "
                        f"{topic_perf.accuracy:.1f}% "
                        f"({topic_perf.correct}/{topic_perf.total_questions})"
                    )
                lines.append("")
        
        except Exception as e:
            logger.warning(f"Error building topic performance: {str(e)}")
            lines.append("⚠️ Error loading topic data")
        
        return "\n".join(lines)
    
    def _build_topic_performance_from_score(
        self,
        test_score: TestScore,
        prioritize_weak: bool
    ) -> str:
        """Build topic performance section from test score."""
        lines = ["=== TOPIC PERFORMANCE ===\n"]
        
        try:
            all_topics = []
            for subject_score in test_score.subject_scores.values():
                for topic_name, topic_score in subject_score.topic_scores.items():
                    all_topics.append((subject_score.subject, topic_score))
            
            # Sort by accuracy
            all_topics.sort(key=lambda x: x[1].accuracy)
            
            # Weak topics
            weak_topics = [(s, t) for s, t in all_topics if t.accuracy < 40]
            if weak_topics:
                lines.append("⚠️ WEAK TOPICS (< 40%):")
                for subject, topic in weak_topics:
                    lines.append(
                        f"   • {subject} - {topic.topic}: {topic.accuracy:.1f}% "
                        f"({topic.correct}/{topic.total_questions})"
                    )
                lines.append("")
            
            # Strong topics
            strong_topics = [(s, t) for s, t in all_topics if t.accuracy > 80]
            if strong_topics:
                lines.append("🌟 STRONG TOPICS (> 80%):")
                for subject, topic in strong_topics[-5:]:  # Top 5
                    lines.append(
                        f"   • {subject} - {topic.topic}: {topic.accuracy:.1f}% "
                        f"({topic.correct}/{topic.total_questions})"
                    )
                lines.append("")
        
        except Exception as e:
            logger.warning(f"Error building topic performance from score: {str(e)}")
            lines.append("⚠️ Error loading topic data")
        
        return "\n".join(lines)
    
    def _build_strengths_weaknesses_section(self, performance_analysis: PerformanceAnalysis) -> str:
        """Build strengths and weaknesses section."""
        lines = ["=== KEY STRENGTHS & WEAKNESSES ===\n"]
        
        try:
            # Strengths
            if performance_analysis.strengths:
                lines.append("💪 STRENGTHS:")
                for strength in performance_analysis.strengths[:5]:  # Top 5
                    lines.append(f"   • {strength.subject} - {strength.topic} ({strength.accuracy:.1f}%)")
                    lines.append(f"      Reason: {strength.reason}")
                    lines.append(f"      Recommendation: {strength.recommendation}")
                    lines.append("")
            
            # Weaknesses
            if performance_analysis.weaknesses:
                lines.append("🎯 AREAS FOR IMPROVEMENT:")
                for weakness in performance_analysis.weaknesses:  # All weaknesses
                    lines.append(
                        f"   • {weakness.subject} - {weakness.topic} ({weakness.accuracy:.1f}%) "
                        f"[{weakness.priority.value.upper()}]"
                    )
                    lines.append(f"      Issue: {weakness.reason}")
                    lines.append(f"      Action: {weakness.recommendation}")
                    lines.append(f"      Estimated Study: {weakness.estimated_study_hours:.1f} hours")
                    lines.append("")
        
        except Exception as e:
            logger.warning(f"Error building strengths/weaknesses: {str(e)}")
            lines.append("⚠️ Error loading strengths/weaknesses data")
        
        return "\n".join(lines)
    
    def _build_question_patterns_section(self, performance_analysis: PerformanceAnalysis) -> str:
        """Build question patterns section (difficulty and type analysis)."""
        lines = ["=== QUESTION PATTERNS ANALYSIS ===\n"]
        
        try:
            # Difficulty Performance
            if performance_analysis.difficulty_performance:
                lines.append("📊 Performance by Difficulty:")
                for difficulty, perf in performance_analysis.difficulty_performance.items():
                    lines.append(
                        f"   • {difficulty.upper()}: {perf.accuracy:.1f}% accuracy "
                        f"({perf.correct}/{perf.total_questions} correct)"
                    )
                    if perf.average_time:
                        lines.append(f"      Avg time: {perf.average_time:.0f}s/question")
                lines.append("")
            
            # Question Type Performance
            if performance_analysis.question_type_performance:
                lines.append("📝 Performance by Question Type:")
                for q_type, perf in performance_analysis.question_type_performance.items():
                    lines.append(
                        f"   • {q_type}: {perf.accuracy:.1f}% accuracy "
                        f"({perf.correct}/{perf.total_questions})"
                    )
                    if perf.preference_score != 50.0:
                        pref = "Strong preference" if perf.preference_score > 70 else "Low preference" if perf.preference_score < 30 else "Moderate preference"
                        lines.append(f"      {pref} ({perf.preference_score:.1f}/100)")
                lines.append("")
        
        except Exception as e:
            logger.warning(f"Error building question patterns: {str(e)}")
            lines.append("⚠️ Error loading pattern data")
        
        return "\n".join(lines)
    
    def _build_learning_patterns_section(self, performance_analysis: PerformanceAnalysis) -> str:
        """Build learning patterns section."""
        lines = ["=== LEARNING PATTERNS DETECTED ===\n"]
        
        try:
            # Use patterns field (new schema)
            patterns = performance_analysis.patterns or performance_analysis.learning_patterns
            
            if patterns:
                for pattern in patterns[:5]:  # Top 5 patterns
                    lines.append(f"🔍 {pattern.pattern_type.value.upper().replace('_', ' ')} Pattern:")
                    lines.append(f"   Description: {pattern.description}")
                    lines.append(f"   Confidence: {pattern.confidence:.1f}%")
                    lines.append(f"   Evidence: {pattern.evidence}")
                    lines.append(f"   Impact: {pattern.impact}")
                    if pattern.recommendation:
                        lines.append(f"   💡 Recommendation: {pattern.recommendation}")
                    lines.append("")
            else:
                lines.append("No significant learning patterns detected.")
        
        except Exception as e:
            logger.warning(f"Error building learning patterns: {str(e)}")
            lines.append("⚠️ Error loading learning patterns")
        
        return "\n".join(lines)
    
    def _build_time_management_section(self, time_mgmt: TimeManagementAnalysis) -> str:
        """Build time management section."""
        lines = ["=== TIME MANAGEMENT ANALYSIS ===\n"]
        
        try:
            hours = time_mgmt.total_time_taken // 3600
            minutes = (time_mgmt.total_time_taken % 3600) // 60
            
            lines.append(f"⏱️ Total Time: {hours}h {minutes}m")
            lines.append(f"⏳ Average Time/Question: {time_mgmt.average_time_per_question:.0f}s")
            lines.append(f"🎯 Expected Average: {time_mgmt.expected_average_time:.0f}s")
            lines.append(f"📊 Time Efficiency: {time_mgmt.time_efficiency:.1f}%")
            lines.append("")
            
            lines.append("⚡ Pacing Analysis:")
            lines.append(f"   • Too Fast (< 30s): {time_mgmt.too_fast_questions} questions")
            lines.append(f"   • Optimal Pace: {time_mgmt.optimal_pace_questions} questions")
            lines.append(f"   • Too Slow (> 5min): {time_mgmt.too_slow_questions} questions")
            lines.append("")
            
            if time_mgmt.recommendations:
                lines.append("💡 Recommendations:")
                for rec in time_mgmt.recommendations:
                    lines.append(f"   • {rec}")
        
        except Exception as e:
            logger.warning(f"Error building time management: {str(e)}")
            lines.append("⚠️ Error loading time management data")
        
        return "\n".join(lines)
    
    def _build_question_details_section(
        self,
        question_scores: List[QuestionScore],
        limit: int = 10
    ) -> str:
        """Build question details section."""
        lines = ["=== SAMPLE QUESTION DETAILS ===\n"]
        
        try:
            # Sort by marks obtained (lowest first - focus on mistakes)
            sorted_questions = sorted(question_scores, key=lambda q: q.marks_obtained)[:limit]
            
            lines.append(f"Showing {len(sorted_questions)} questions (prioritizing incorrect answers):\n")
            
            for q in sorted_questions:
                status = "✓" if q.is_correct else "⚠️" if q.is_partial else "✗"
                lines.append(
                    f"{status} Q{q.question_number} [{q.subject} - {q.topic}] "
                    f"({q.difficulty}, {q.question_type})"
                )
                lines.append(f"   Marks: {q.marks_obtained}/{q.max_marks}")
                lines.append(f"   Your answer: {q.student_answer or 'Not attempted'}")
                lines.append(f"   Correct answer: {q.correct_answer}")
                if q.time_taken:
                    lines.append(f"   Time: {q.time_taken}s")
                lines.append("")
        
        except Exception as e:
            logger.warning(f"Error building question details: {str(e)}")
            lines.append("⚠️ Error loading question details")
        
        return "\n".join(lines)
    
    def _trim_context(self, context: str, sections: List[str]) -> str:
        """Trim context to fit within max_chars by removing lower-priority sections."""
        logger.warning(f"Context exceeds max length ({len(context)} > {self.max_chars}), trimming...")
        
        # Priority order (higher index = lower priority, removed first)
        section_priorities = [
            "SAMPLE QUESTION DETAILS",
            "LEARNING PATTERNS",
            "TIME MANAGEMENT",
            "QUESTION PATTERNS",
            "KEY STRENGTHS",
            "TOPIC PERFORMANCE",
            "SUBJECT-WISE",
            "OVERVIEW"
        ]
        
        # Remove sections from lowest priority until within limit
        remaining_sections = sections.copy()
        
        for priority_section in section_priorities:
            if len("\n\n".join(remaining_sections)) <= self.max_chars:
                break
            
            # Find and remove section
            for i, section in enumerate(remaining_sections):
                if priority_section in section:
                    logger.info(f"Removing section: {priority_section}")
                    remaining_sections.pop(i)
                    break
        
        trimmed_context = "\n\n".join(remaining_sections)
        
        # If still too long, truncate
        if len(trimmed_context) > self.max_chars:
            trimmed_context = trimmed_context[:self.max_chars - 100] + "\n\n[Context truncated to fit token limit]"
        
        return trimmed_context
    
    def _build_minimal_context(
        self,
        test_score: Optional[TestScore],
        performance_analysis: Optional[PerformanceAnalysis]
    ) -> str:
        """Build minimal context on error."""
        lines = ["=== TEST PERFORMANCE (MINIMAL) ===\n"]
        
        try:
            if test_score:
                lines.append(f"Exam: {test_score.exam_type}")
                lines.append(f"Score: {test_score.total_marks_obtained}/{test_score.total_max_marks} ({test_score.percentage:.1f}%)")
                lines.append(f"Accuracy: {test_score.accuracy:.1f}%")
            elif performance_analysis:
                lines.append(f"Exam: {performance_analysis.exam_type}")
                lines.append(f"Accuracy: {performance_analysis.overall_accuracy:.1f}%")
                lines.append(f"Score: {performance_analysis.overall_marks}/{performance_analysis.overall_max_marks}")
        except Exception as e:
            logger.error(f"Error building minimal context: {str(e)}")
            lines.append("Error loading test data")
        
        return "\n".join(lines)
    
    def estimate_tokens(self, context: str) -> int:
        """
        Estimate token count for a context string.
        
        Args:
            context: Context string
        
        Returns:
            Estimated token count
        """
        return len(context) // self.chars_per_token
    
    def get_max_tokens(self) -> int:
        """Get the maximum token limit."""
        return self.max_tokens
    
    def set_max_tokens(self, max_tokens: int) -> None:
        """
        Set new maximum token limit.
        
        Args:
            max_tokens: New maximum tokens
        """
        self.max_tokens = max_tokens
        self.max_chars = max_tokens * self.chars_per_token
        logger.info(f"Max tokens updated to {max_tokens}")
