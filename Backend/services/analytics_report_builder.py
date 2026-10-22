"""
Analytics Report Builder for Mentor AI Platform.

This module assembles complete analytics reports from test scores, performance analysis,
and AI-generated insights. It creates frontend-ready reports with all necessary
sections, visualizations, and recommendations.

Features:
- Comprehensive report assembly from multiple data sources
- Frontend-ready data structures
- Visualization data preparation (charts, graphs)
- Percentile calculations based on benchmarks
- Priority topic identification and sorting
- Study hour estimations
- Error handling and validation

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.analytics_report_builder import AnalyticsReportBuilder
    >>> 
    >>> builder = AnalyticsReportBuilder()
    >>> report = builder.build_report(
    ...     score_result=test_score,
    ...     performance_analysis=performance_data,
    ...     ai_insights=gemini_insights,
    ...     test_metadata=metadata
    ... )
    >>> 
    >>> print(f"Overall Score: {report.overview.percentage}%")
    >>> print(f"Priority Topics: {len(report.priority_topics)}")
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field

from models.score_models import TestScore, SubjectScore, TopicScore
from models.performance_models import (
    PerformanceAnalysis,
    TopicPerformance,
    PriorityLevel
)
from utils.analytics_parser import AnalyticsInsights, AnalyticsWeakness

# Configure logging
logger = logging.getLogger(__name__)


class ReportBuilderError(Exception):
    """Base exception for report builder errors."""
    pass


# ===== Report Models =====

class OverviewSection(BaseModel):
    """Test overview section."""
    test_id: str
    student_id: str
    exam_type: str
    total_questions: int
    attempted: int
    correct: int
    incorrect: int
    unattempted: int
    total_marks: int
    max_marks: int
    percentage: float
    accuracy: float
    percentile: Optional[float] = None
    time_taken: Optional[int] = None  # seconds
    submission_time: Optional[datetime] = None


class SubjectAnalysisItem(BaseModel):
    """Subject-wise analysis with AI insights."""
    subject: str
    score: int
    max_score: int
    percentage: float
    accuracy: float
    attempted: int
    correct: int
    incorrect: int
    unattempted: int
    time_taken: Optional[int] = None
    top_topics: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    ai_insight: Optional[str] = None


class TopicAnalysisItem(BaseModel):
    """Topic-wise analysis with priorities."""
    topic: str
    subject: str
    accuracy: float
    correct: int
    total: int
    marks_obtained: int
    max_marks: int
    performance_level: str
    priority: str
    benchmark_gap: float
    improvement_potential: float  # Percentage points to gain
    estimated_study_hours: float
    recommendation: Optional[str] = None


class AIInsightsSection(BaseModel):
    """AI-generated insights section."""
    strengths: List[Dict[str, Any]] = Field(default_factory=list)
    weaknesses: List[Dict[str, Any]] = Field(default_factory=list)
    learning_patterns: List[str] = Field(default_factory=list)
    overall_assessment: str = ""
    study_strategy: str = ""


class RecommendationItem(BaseModel):
    """Actionable study recommendation."""
    topic: str
    subject: str
    priority: str
    current_accuracy: float
    target_accuracy: float
    estimated_hours: float
    action_items: List[str] = Field(default_factory=list)


class PriorityTopicItem(BaseModel):
    """Priority topic for study plan."""
    rank: int
    topic: str
    subject: str
    priority: str
    accuracy: float
    improvement_potential: float
    estimated_hours: float
    urgency_score: float  # Combined metric for sorting


class ChartDataPoint(BaseModel):
    """Generic chart data point."""
    label: str
    value: float
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VisualizationData(BaseModel):
    """Data prepared for frontend charts."""
    subject_pie_chart: List[ChartDataPoint] = Field(default_factory=list)
    topic_bar_chart: List[ChartDataPoint] = Field(default_factory=list)
    difficulty_line_chart: List[ChartDataPoint] = Field(default_factory=list)
    priority_heatmap: List[Dict[str, Any]] = Field(default_factory=list)


class AnalyticsReport(BaseModel):
    """Complete analytics report."""
    overview: OverviewSection
    subject_analysis: List[SubjectAnalysisItem] = Field(default_factory=list)
    topic_analysis: List[TopicAnalysisItem] = Field(default_factory=list)
    ai_insights: AIInsightsSection
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    priority_topics: List[PriorityTopicItem] = Field(default_factory=list)
    visualization_data: VisualizationData
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ===== Builder Class =====

class AnalyticsReportBuilder:
    """
    Builder for comprehensive analytics reports.
    
    Assembles data from multiple sources (scores, performance analysis, AI insights)
    into a complete, frontend-ready report with visualizations and recommendations.
    
    Attributes:
        default_benchmark: Default benchmark percentile (default: 70.0)
        max_priority_topics: Maximum priority topics to include (default: 10)
    
    Example:
        >>> builder = AnalyticsReportBuilder()
        >>> report = builder.build_report(
        ...     score_result=test_score,
        ...     performance_analysis=perf_analysis,
        ...     ai_insights=insights
        ... )
    """
    
    def __init__(
        self,
        default_benchmark: float = 70.0,
        max_priority_topics: int = 10
    ):
        """
        Initialize AnalyticsReportBuilder.
        
        Args:
            default_benchmark: Default benchmark accuracy percentage
            max_priority_topics: Maximum number of priority topics
        """
        self.default_benchmark = default_benchmark
        self.max_priority_topics = max_priority_topics
        
        logger.info(
            f"AnalyticsReportBuilder initialized (benchmark={default_benchmark}, "
            f"max_priority={max_priority_topics})"
        )
    
    def build_report(
        self,
        score_result: TestScore,
        performance_analysis: Optional[PerformanceAnalysis] = None,
        ai_insights: Optional[AnalyticsInsights] = None,
        test_metadata: Optional[Dict[str, Any]] = None
    ) -> AnalyticsReport:
        """
        Build complete analytics report from multiple data sources.
        
        Args:
            score_result: Test score results (required)
            performance_analysis: Performance analysis data (optional)
            ai_insights: AI-generated insights from Gemini (optional)
            test_metadata: Additional test metadata (optional)
        
        Returns:
            Complete AnalyticsReport object ready for frontend
        
        Raises:
            ReportBuilderError: If required data is missing or invalid
        
        Example:
            >>> report = builder.build_report(
            ...     score_result=test_score,
            ...     performance_analysis=perf_data,
            ...     ai_insights=insights,
            ...     test_metadata={"percentile": 85.5}
            ... )
        """
        if not score_result:
            raise ReportBuilderError("score_result is required")
        
        logger.info(f"Building analytics report for test {score_result.test_id}")
        
        try:
            # Build overview section
            overview = self._build_overview(score_result, test_metadata)
            
            # Build subject analysis
            subject_analysis = self._build_subject_analysis(
                score_result,
                ai_insights
            )
            
            # Build topic analysis
            topic_analysis = self._build_topic_analysis(
                score_result,
                performance_analysis,
                ai_insights
            )
            
            # Build AI insights section
            ai_insights_section = self._build_ai_insights_section(ai_insights)
            
            # Build recommendations
            recommendations = self._build_recommendations(
                topic_analysis,
                ai_insights
            )
            
            # Build priority topics
            priority_topics = self._build_priority_topics(
                topic_analysis,
                self.max_priority_topics
            )
            
            # Build visualization data
            visualization_data = self._build_visualization_data(
                score_result,
                performance_analysis,
                topic_analysis
            )
            
            # Build metadata
            metadata = self._build_metadata(
                score_result,
                performance_analysis,
                ai_insights,
                test_metadata
            )
            
            # Assemble report
            report = AnalyticsReport(
                overview=overview,
                subject_analysis=subject_analysis,
                topic_analysis=topic_analysis,
                ai_insights=ai_insights_section,
                recommendations=recommendations,
                priority_topics=priority_topics,
                visualization_data=visualization_data,
                metadata=metadata,
                generated_at=datetime.utcnow()
            )
            
            logger.info(
                f"Report built successfully: {len(subject_analysis)} subjects, "
                f"{len(topic_analysis)} topics, {len(priority_topics)} priority topics"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to build report: {str(e)}")
            raise ReportBuilderError(f"Report building failed: {str(e)}")
    
    def _build_overview(
        self,
        score_result: TestScore,
        test_metadata: Optional[Dict[str, Any]]
    ) -> OverviewSection:
        """Build overview section."""
        # Calculate percentile
        percentile = None
        if test_metadata and 'percentile' in test_metadata:
            percentile = test_metadata['percentile']
        else:
            # Estimate percentile based on percentage
            percentile = self._estimate_percentile(score_result.percentage)
        
        return OverviewSection(
            test_id=score_result.test_id,
            student_id=score_result.student_id,
            exam_type=score_result.exam_type,
            total_questions=score_result.total_questions,
            attempted=score_result.attempted,
            correct=score_result.correct,
            incorrect=score_result.incorrect,
            unattempted=score_result.unattempted,
            total_marks=score_result.total_marks_obtained,
            max_marks=score_result.total_max_marks,
            percentage=score_result.percentage,
            accuracy=score_result.accuracy,
            percentile=percentile,
            time_taken=score_result.time_taken,
            submission_time=score_result.submission_time
        )
    
    def _build_subject_analysis(
        self,
        score_result: TestScore,
        ai_insights: Optional[AnalyticsInsights]
    ) -> List[SubjectAnalysisItem]:
        """Build subject-wise analysis."""
        subject_items = []
        
        for subject_name, subject_score in score_result.subject_scores.items():
            # Get top and weak topics
            top_topics = []
            weak_topics = []
            
            if subject_score.topic_scores:
                sorted_topics = sorted(
                    subject_score.topic_scores.items(),
                    key=lambda x: x[1].accuracy,
                    reverse=True
                )
                
                top_topics = [t[0] for t in sorted_topics[:3] if t[1].accuracy > 75]
                weak_topics = [t[0] for t in sorted_topics if t[1].accuracy < 50][-3:]
            
            # Get AI insight for subject
            ai_insight = self._get_subject_ai_insight(
                subject_name,
                ai_insights
            )
            
            subject_items.append(SubjectAnalysisItem(
                subject=subject_name,
                score=subject_score.marks_obtained,
                max_score=subject_score.max_marks,
                percentage=(subject_score.marks_obtained / subject_score.max_marks * 100),
                accuracy=subject_score.accuracy,
                attempted=subject_score.attempted,
                correct=subject_score.correct,
                incorrect=subject_score.incorrect,
                unattempted=subject_score.unattempted,
                time_taken=subject_score.time_taken,
                top_topics=top_topics,
                weak_topics=weak_topics,
                ai_insight=ai_insight
            ))
        
        return subject_items
    
    def _build_topic_analysis(
        self,
        score_result: TestScore,
        performance_analysis: Optional[PerformanceAnalysis],
        ai_insights: Optional[AnalyticsInsights]
    ) -> List[TopicAnalysisItem]:
        """Build topic-wise analysis."""
        topic_items = []
        
        # Collect all topics from score result
        for subject_score in score_result.subject_scores.values():
            for topic_name, topic_score in subject_score.topic_scores.items():
                # Get performance data if available
                perf_data = self._get_topic_performance(
                    topic_name,
                    subject_score.subject,
                    performance_analysis
                )
                
                # Get AI recommendation
                recommendation = self._get_topic_recommendation(
                    topic_name,
                    subject_score.subject,
                    ai_insights
                )
                
                # Calculate improvement potential
                improvement_potential = max(0, self.default_benchmark - topic_score.accuracy)
                
                # Get estimated study hours
                estimated_hours = self._estimate_study_hours(
                    topic_score.accuracy,
                    ai_insights,
                    topic_name
                )
                
                # Determine priority
                priority = self._determine_priority(topic_score.accuracy, improvement_potential)
                
                # Determine performance level
                performance_level = self._get_performance_level(topic_score.accuracy)
                
                # Get benchmark gap
                benchmark_gap = topic_score.accuracy - self.default_benchmark
                
                topic_items.append(TopicAnalysisItem(
                    topic=topic_name,
                    subject=subject_score.subject,
                    accuracy=topic_score.accuracy,
                    correct=topic_score.correct,
                    total=topic_score.total_questions,
                    marks_obtained=topic_score.marks_obtained,
                    max_marks=topic_score.max_marks,
                    performance_level=performance_level,
                    priority=priority,
                    benchmark_gap=benchmark_gap,
                    improvement_potential=improvement_potential,
                    estimated_study_hours=estimated_hours,
                    recommendation=recommendation
                ))
        
        return topic_items
    
    def _build_ai_insights_section(
        self,
        ai_insights: Optional[AnalyticsInsights]
    ) -> AIInsightsSection:
        """Build AI insights section."""
        if not ai_insights:
            return AIInsightsSection()
        
        # Convert strengths to dict format
        strengths = [
            {
                "topic": s.topic,
                "subject": s.subject,
                "accuracy": s.accuracy,
                "reason": s.reason,
                "recommendation": s.recommendation
            }
            for s in ai_insights.strengths
        ]
        
        # Convert weaknesses to dict format
        weaknesses = [
            {
                "topic": w.topic,
                "subject": w.subject,
                "accuracy": w.accuracy,
                "reason": w.reason,
                "priority": w.priority.value,
                "estimated_study_hours": w.estimated_study_hours,
                "recommendation": w.recommendation
            }
            for w in ai_insights.weaknesses
        ]
        
        return AIInsightsSection(
            strengths=strengths,
            weaknesses=weaknesses,
            learning_patterns=ai_insights.learning_patterns,
            overall_assessment=ai_insights.overall_assessment,
            study_strategy=ai_insights.study_strategy
        )
    
    def _build_recommendations(
        self,
        topic_analysis: List[TopicAnalysisItem],
        ai_insights: Optional[AnalyticsInsights]
    ) -> List[RecommendationItem]:
        """Build actionable recommendations."""
        recommendations = []
        
        # Get weak topics (accuracy < 60%)
        weak_topics = [t for t in topic_analysis if t.accuracy < 60]
        
        # Sort by priority and improvement potential
        weak_topics.sort(key=lambda t: (
            0 if t.priority == "HIGH" else 1 if t.priority == "MEDIUM" else 2,
            -t.improvement_potential
        ))
        
        for topic in weak_topics[:8]:  # Top 8 recommendations
            # Target accuracy: aim for benchmark or 20% improvement
            target_accuracy = min(
                self.default_benchmark,
                topic.accuracy + max(20, topic.improvement_potential * 0.6)
            )
            
            # Get action items from AI insights
            action_items = self._get_action_items(
                topic.topic,
                topic.subject,
                ai_insights
            )
            
            recommendations.append(RecommendationItem(
                topic=topic.topic,
                subject=topic.subject,
                priority=topic.priority,
                current_accuracy=topic.accuracy,
                target_accuracy=target_accuracy,
                estimated_hours=topic.estimated_study_hours,
                action_items=action_items
            ))
        
        return recommendations
    
    def _build_priority_topics(
        self,
        topic_analysis: List[TopicAnalysisItem],
        max_topics: int
    ) -> List[PriorityTopicItem]:
        """Build sorted priority topics list."""
        # Calculate urgency score for each topic
        scored_topics = []
        
        for topic in topic_analysis:
            # Urgency score combines:
            # 1. Priority level (HIGH=3, MEDIUM=2, LOW=1)
            # 2. Improvement potential (more = higher urgency)
            # 3. Inverse of accuracy (lower accuracy = higher urgency)
            
            priority_weight = 3 if topic.priority == "HIGH" else 2 if topic.priority == "MEDIUM" else 1
            improvement_weight = topic.improvement_potential / 100
            accuracy_penalty = (100 - topic.accuracy) / 100
            
            urgency_score = (
                priority_weight * 40 +
                improvement_weight * 35 +
                accuracy_penalty * 25
            )
            
            scored_topics.append((topic, urgency_score))
        
        # Sort by urgency score (descending)
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        
        # Create priority topic items
        priority_topics = []
        for rank, (topic, urgency) in enumerate(scored_topics[:max_topics], 1):
            priority_topics.append(PriorityTopicItem(
                rank=rank,
                topic=topic.topic,
                subject=topic.subject,
                priority=topic.priority,
                accuracy=topic.accuracy,
                improvement_potential=topic.improvement_potential,
                estimated_hours=topic.estimated_study_hours,
                urgency_score=urgency
            ))
        
        return priority_topics
    
    def _build_visualization_data(
        self,
        score_result: TestScore,
        performance_analysis: Optional[PerformanceAnalysis],
        topic_analysis: List[TopicAnalysisItem]
    ) -> VisualizationData:
        """Build data for frontend visualizations."""
        # Subject pie chart
        subject_pie = []
        colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6"]
        
        for idx, (subject, score) in enumerate(score_result.subject_scores.items()):
            subject_pie.append(ChartDataPoint(
                label=subject,
                value=score.accuracy,
                color=colors[idx % len(colors)],
                metadata={
                    "marks": score.marks_obtained,
                    "max_marks": score.max_marks,
                    "percentage": (score.marks_obtained / score.max_marks * 100)
                }
            ))
        
        # Topic bar chart (top 10 topics by accuracy)
        sorted_topics = sorted(topic_analysis, key=lambda t: t.accuracy, reverse=True)[:10]
        topic_bar = [
            ChartDataPoint(
                label=f"{t.topic} ({t.subject})",
                value=t.accuracy,
                color="#3B82F6" if t.accuracy > 80 else "#F59E0B" if t.accuracy > 50 else "#EF4444",
                metadata={
                    "correct": t.correct,
                    "total": t.total,
                    "priority": t.priority
                }
            )
            for t in sorted_topics
        ]
        
        # Difficulty line chart
        difficulty_line = []
        if performance_analysis and performance_analysis.difficulty_performance:
            for difficulty, perf in performance_analysis.difficulty_performance.items():
                difficulty_line.append(ChartDataPoint(
                    label=difficulty.value if hasattr(difficulty, 'value') else str(difficulty),
                    value=perf.accuracy,
                    metadata={
                        "correct": perf.correct,
                        "total": perf.total_questions
                    }
                ))
        
        # Priority heatmap
        priority_heatmap = []
        for topic in topic_analysis:
            priority_heatmap.append({
                "topic": topic.topic,
                "subject": topic.subject,
                "accuracy": topic.accuracy,
                "priority": topic.priority,
                "urgency": "high" if topic.priority == "HIGH" and topic.accuracy < 40 else "medium" if topic.priority in ["HIGH", "MEDIUM"] else "low"
            })
        
        return VisualizationData(
            subject_pie_chart=subject_pie,
            topic_bar_chart=topic_bar,
            difficulty_line_chart=difficulty_line,
            priority_heatmap=priority_heatmap
        )
    
    def _build_metadata(
        self,
        score_result: TestScore,
        performance_analysis: Optional[PerformanceAnalysis],
        ai_insights: Optional[AnalyticsInsights],
        test_metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build report metadata."""
        metadata = {
            "report_version": "1.0",
            "has_performance_analysis": performance_analysis is not None,
            "has_ai_insights": ai_insights is not None,
            "exam_type": score_result.exam_type,
            "total_study_hours_needed": self._calculate_total_study_hours(ai_insights),
            "data_sources": []
        }
        
        if score_result:
            metadata["data_sources"].append("score_calculation")
        if performance_analysis:
            metadata["data_sources"].append("performance_analysis")
        if ai_insights:
            metadata["data_sources"].append("ai_insights")
        
        if test_metadata:
            metadata.update(test_metadata)
        
        return metadata
    
    # ===== Helper Methods =====
    
    def _estimate_percentile(self, percentage: float) -> float:
        """Estimate percentile based on percentage score."""
        # Simple linear mapping (can be improved with actual distribution data)
        if percentage >= 90:
            return 95.0
        elif percentage >= 80:
            return 85.0
        elif percentage >= 70:
            return 70.0
        elif percentage >= 60:
            return 55.0
        elif percentage >= 50:
            return 40.0
        else:
            return 25.0
    
    def _get_subject_ai_insight(
        self,
        subject: str,
        ai_insights: Optional[AnalyticsInsights]
    ) -> Optional[str]:
        """Get AI insight for a specific subject."""
        if not ai_insights:
            return None
        
        # Check strengths and weaknesses for subject-related insights
        for strength in ai_insights.strengths:
            if strength.subject == subject:
                return f"Strength: {strength.reason}"
        
        for weakness in ai_insights.weaknesses:
            if weakness.subject == subject:
                return f"Needs improvement: {weakness.reason}"
        
        return None
    
    def _get_topic_performance(
        self,
        topic: str,
        subject: str,
        performance_analysis: Optional[PerformanceAnalysis]
    ) -> Optional[TopicPerformance]:
        """Get performance data for a specific topic."""
        if not performance_analysis:
            return None
        
        # Search in all topic lists
        all_topics = (
            performance_analysis.strong_topics +
            performance_analysis.moderate_topics +
            performance_analysis.weak_topics
        )
        
        for topic_perf in all_topics:
            if topic_perf.topic == topic and topic_perf.subject == subject:
                return topic_perf
        
        return None
    
    def _get_topic_recommendation(
        self,
        topic: str,
        subject: str,
        ai_insights: Optional[AnalyticsInsights]
    ) -> Optional[str]:
        """Get AI recommendation for a specific topic."""
        if not ai_insights:
            return None
        
        # Check weaknesses for topic recommendation
        for weakness in ai_insights.weaknesses:
            if weakness.topic == topic and weakness.subject == subject:
                return weakness.recommendation
        
        return None
    
    def _estimate_study_hours(
        self,
        accuracy: float,
        ai_insights: Optional[AnalyticsInsights],
        topic: str
    ) -> float:
        """Estimate study hours needed for a topic."""
        # Check AI insights first
        if ai_insights:
            for weakness in ai_insights.weaknesses:
                if weakness.topic == topic:
                    return weakness.estimated_study_hours
        
        # Fallback to accuracy-based estimation
        if accuracy < 30:
            return 15.0
        elif accuracy < 50:
            return 10.0
        elif accuracy < 70:
            return 5.0
        else:
            return 2.0
    
    def _determine_priority(self, accuracy: float, improvement_potential: float) -> str:
        """Determine priority level for a topic."""
        if accuracy < 40 and improvement_potential > 30:
            return "HIGH"
        elif accuracy < 60 or improvement_potential > 20:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_performance_level(self, accuracy: float) -> str:
        """Get performance level classification."""
        if accuracy > 80:
            return "strong"
        elif accuracy > 40:
            return "moderate"
        else:
            return "weak"
    
    def _get_action_items(
        self,
        topic: str,
        subject: str,
        ai_insights: Optional[AnalyticsInsights]
    ) -> List[str]:
        """Get action items for a topic."""
        if ai_insights:
            for weakness in ai_insights.weaknesses:
                if weakness.topic == topic and weakness.subject == subject:
                    # Parse recommendation into action items
                    rec = weakness.recommendation
                    # Simple split by sentences or common delimiters
                    items = [s.strip() for s in rec.split('.') if s.strip()]
                    return items[:3] if items else [rec]
        
        # Default action items
        return [
            f"Review fundamental concepts in {topic}",
            "Practice 20-30 problems daily",
            "Solve previous year questions"
        ]
    
    def _calculate_total_study_hours(self, ai_insights: Optional[AnalyticsInsights]) -> float:
        """Calculate total study hours needed."""
        if not ai_insights or not ai_insights.weaknesses:
            return 0.0
        
        return sum(w.estimated_study_hours for w in ai_insights.weaknesses)
