"""
Performance Analyzer Service for Diagnostic Test System - Mentor AI Platform.

This service analyzes test performance to identify strengths, weaknesses, learning
patterns, and generate personalized recommendations for students.

Features:
- Identify strong/moderate/weak topics
- Analyze difficulty-wise performance
- Detect time management issues
- Find learning patterns (question type/difficulty preferences)
- Calculate topic priorities
- Compare against benchmarks
- Generate personalized recommendations

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.performance_analyzer import PerformanceAnalyzer
    >>> from services.score_calculator import ScoreCalculator
    >>> 
    >>> calculator = ScoreCalculator()
    >>> test_score = calculator.calculate_test_score(...)
    >>> 
    >>> analyzer = PerformanceAnalyzer()
    >>> analysis = analyzer.analyze_performance(test_score)
    >>> 
    >>> print(f"Strong Topics: {len(analysis.strong_topics)}")
    >>> print(f"Weak Topics: {len(analysis.weak_topics)}")
    >>> print(f"Recommendations: {len(analysis.recommendations)}")
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

from models.score_models import TestScore, SubjectScore, TopicScore, QuestionScore
from models.performance_models import (
    PerformanceAnalysis,
    TopicPerformance,
    DifficultyPerformance,
    QuestionTypePerformance,
    TimeManagementAnalysis,
    LearningPattern,
    TopicRecommendation,
    PerformanceLevel,
    PriorityLevel,
    DifficultyLevel
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    Analyze test performance and generate insights.
    
    This class analyzes test scores to identify learning patterns, strengths,
    weaknesses, and generates personalized recommendations.
    
    Attributes:
        strong_threshold: Accuracy threshold for strong topics (default: 80%)
        weak_threshold: Accuracy threshold for weak topics (default: 40%)
        min_questions_threshold: Minimum questions needed for analysis (default: 3)
    
    Example:
        >>> analyzer = PerformanceAnalyzer()
        >>> analysis = analyzer.analyze_performance(test_score)
        >>> print(f"Weak topics: {[t.topic for t in analysis.weak_topics]}")
    """
    
    def __init__(
        self,
        strong_threshold: float = 80.0,
        weak_threshold: float = 40.0,
        min_questions_threshold: int = 3
    ):
        """
        Initialize performance analyzer.
        
        Args:
            strong_threshold: Accuracy threshold for strong classification
            weak_threshold: Accuracy threshold for weak classification
            min_questions_threshold: Minimum questions for valid analysis
        """
        self.strong_threshold = strong_threshold
        self.weak_threshold = weak_threshold
        self.min_questions_threshold = min_questions_threshold
        
        # Benchmark accuracies by exam type and difficulty
        self.benchmarks = self._initialize_benchmarks()
        
        logger.info(
            f"PerformanceAnalyzer initialized with thresholds: "
            f"strong={strong_threshold}%, weak={weak_threshold}%"
        )
    
    def _initialize_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize benchmark accuracies.
        
        Returns:
            Dict: Benchmark accuracies by exam type and difficulty
        """
        return {
            "JEE_MAIN": {
                "overall": 70.0,
                "easy": 85.0,
                "medium": 65.0,
                "hard": 45.0
            },
            "JEE_ADVANCED": {
                "overall": 60.0,
                "easy": 75.0,
                "medium": 55.0,
                "hard": 35.0
            },
            "NEET": {
                "overall": 75.0,
                "easy": 90.0,
                "medium": 70.0,
                "hard": 50.0
            }
        }
    
    def analyze_performance(
        self,
        test_score: TestScore,
        include_time_analysis: bool = True
    ) -> PerformanceAnalysis:
        """
        Perform complete performance analysis.
        
        Args:
            test_score: TestScore object from ScoreCalculator
            include_time_analysis: Whether to include time management analysis
        
        Returns:
            PerformanceAnalysis: Complete performance analysis
        
        Example:
            >>> analyzer = PerformanceAnalyzer()
            >>> analysis = analyzer.analyze_performance(test_score)
            >>> print(analysis.weak_topics)
        """
        logger.info(
            f"Starting performance analysis for test {test_score.test_id}, "
            f"student {test_score.student_id}"
        )
        
        # Analyze topics
        strong_topics, moderate_topics, weak_topics = self._analyze_topics(
            test_score
        )
        
        # Analyze difficulty levels
        difficulty_performance = self._analyze_difficulty(test_score)
        
        # Analyze question types
        question_type_performance = self._analyze_question_types(test_score)
        
        # Analyze time management
        time_management = None
        if include_time_analysis and test_score.time_taken:
            time_management = self._analyze_time_management(test_score)
        
        # Detect learning patterns
        learning_patterns = self._detect_learning_patterns(
            test_score,
            difficulty_performance,
            question_type_performance
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            weak_topics,
            moderate_topics,
            test_score.exam_type
        )
        
        # Calculate subject strengths
        subject_strengths = {
            subject: score.accuracy
            for subject, score in test_score.subject_scores.items()
        }
        
        # Prioritize topics
        priority_topics = [
            topic.topic for topic in weak_topics
        ] + [
            topic.topic for topic in moderate_topics
            if topic.accuracy < 60.0
        ]
        
        # Create analysis object
        analysis = PerformanceAnalysis(
            test_id=test_score.test_id,
            student_id=test_score.student_id,
            exam_type=test_score.exam_type,
            analysis_date=datetime.utcnow(),
            overall_accuracy=test_score.accuracy,
            overall_marks=test_score.total_marks_obtained,
            overall_max_marks=test_score.total_max_marks,
            strong_topics=strong_topics,
            moderate_topics=moderate_topics,
            weak_topics=weak_topics,
            difficulty_performance=difficulty_performance,
            question_type_performance=question_type_performance,
            time_management=time_management,
            learning_patterns=learning_patterns,
            recommendations=recommendations,
            subject_strengths=subject_strengths,
            priority_topics=priority_topics
        )
        
        logger.info(
            f"Analysis complete: {len(strong_topics)} strong, "
            f"{len(moderate_topics)} moderate, {len(weak_topics)} weak topics"
        )
        
        return analysis
    
    def _analyze_topics(
        self,
        test_score: TestScore
    ) -> Tuple[List[TopicPerformance], List[TopicPerformance], List[TopicPerformance]]:
        """
        Analyze topics and classify by performance level.
        
        Args:
            test_score: TestScore object
        
        Returns:
            Tuple: (strong_topics, moderate_topics, weak_topics)
        """
        strong_topics = []
        moderate_topics = []
        weak_topics = []
        
        # Get benchmark for exam type
        exam_benchmark = self.benchmarks.get(
            test_score.exam_type,
            {"overall": 70.0}
        )
        
        # Analyze each subject's topics
        for subject, subject_score in test_score.subject_scores.items():
            for topic_name, topic_score in subject_score.topic_scores.items():
                # Skip if not enough questions
                if topic_score.total_questions < self.min_questions_threshold:
                    continue
                
                # Classify performance level
                if topic_score.accuracy >= self.strong_threshold:
                    performance_level = PerformanceLevel.STRONG
                    priority_level = PriorityLevel.LOW
                elif topic_score.accuracy >= self.weak_threshold:
                    performance_level = PerformanceLevel.MODERATE
                    priority_level = PriorityLevel.MEDIUM
                else:
                    performance_level = PerformanceLevel.WEAK
                    priority_level = PriorityLevel.HIGH
                
                # Calculate gap from benchmark
                benchmark = exam_benchmark.get("overall", 70.0)
                gap = topic_score.accuracy - benchmark
                
                # Create TopicPerformance object
                topic_perf = TopicPerformance(
                    topic=topic_name,
                    subject=subject,
                    performance_level=performance_level,
                    priority_level=priority_level,
                    total_questions=topic_score.total_questions,
                    correct=topic_score.correct,
                    incorrect=topic_score.incorrect,
                    accuracy=topic_score.accuracy,
                    marks_obtained=topic_score.marks_obtained,
                    max_marks=topic_score.max_marks,
                    average_time_per_question=(
                        topic_score.time_taken / topic_score.attempted
                        if topic_score.time_taken and topic_score.attempted > 0
                        else None
                    ),
                    benchmark_accuracy=benchmark,
                    gap_from_benchmark=round(gap, 2)
                )
                
                # Classify into appropriate list
                if performance_level == PerformanceLevel.STRONG:
                    strong_topics.append(topic_perf)
                elif performance_level == PerformanceLevel.MODERATE:
                    moderate_topics.append(topic_perf)
                else:
                    weak_topics.append(topic_perf)
        
        # Sort by accuracy
        strong_topics.sort(key=lambda x: x.accuracy, reverse=True)
        moderate_topics.sort(key=lambda x: x.accuracy)
        weak_topics.sort(key=lambda x: x.accuracy)
        
        return strong_topics, moderate_topics, weak_topics
    
    def _analyze_difficulty(
        self,
        test_score: TestScore
    ) -> Dict[str, DifficultyPerformance]:
        """
        Analyze performance by difficulty level.
        
        Args:
            test_score: TestScore object
        
        Returns:
            Dict: Difficulty-wise performance mapping
        """
        difficulty_stats: Dict[str, Dict[str, int]] = {
            "easy": {"total": 0, "correct": 0, "incorrect": 0, "time": 0},
            "medium": {"total": 0, "correct": 0, "incorrect": 0, "time": 0},
            "hard": {"total": 0, "correct": 0, "incorrect": 0, "time": 0}
        }
        
        # Aggregate statistics by difficulty
        for q_score in test_score.question_scores:
            if q_score.student_answer is None:
                continue
            
            diff = q_score.difficulty.lower()
            if diff not in difficulty_stats:
                continue
            
            difficulty_stats[diff]["total"] += 1
            if q_score.is_correct:
                difficulty_stats[diff]["correct"] += 1
            else:
                difficulty_stats[diff]["incorrect"] += 1
            
            if q_score.time_taken:
                difficulty_stats[diff]["time"] += q_score.time_taken
        
        # Create DifficultyPerformance objects
        difficulty_performance = {}
        for diff_level in ["easy", "medium", "hard"]:
            stats = difficulty_stats[diff_level]
            
            if stats["total"] == 0:
                continue
            
            accuracy = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
            avg_time = (stats["time"] / stats["total"]) if stats["total"] > 0 else None
            
            difficulty_performance[diff_level] = DifficultyPerformance(
                difficulty=DifficultyLevel(diff_level),
                total_questions=stats["total"],
                correct=stats["correct"],
                incorrect=stats["incorrect"],
                accuracy=round(accuracy, 2),
                average_time=round(avg_time, 2) if avg_time else None
            )
        
        return difficulty_performance
    
    def _analyze_question_types(
        self,
        test_score: TestScore
    ) -> Dict[str, QuestionTypePerformance]:
        """
        Analyze performance by question type.
        
        Args:
            test_score: TestScore object
        
        Returns:
            Dict: Question type performance mapping
        """
        type_stats: Dict[str, Dict[str, int]] = {}
        
        # Aggregate statistics by question type
        for q_score in test_score.question_scores:
            q_type = q_score.question_type
            
            if q_type not in type_stats:
                type_stats[q_type] = {
                    "total": 0,
                    "attempted": 0,
                    "correct": 0,
                    "incorrect": 0
                }
            
            type_stats[q_type]["total"] += 1
            
            if q_score.student_answer is not None:
                type_stats[q_type]["attempted"] += 1
                if q_score.is_correct:
                    type_stats[q_type]["correct"] += 1
                else:
                    type_stats[q_type]["incorrect"] += 1
        
        # Create QuestionTypePerformance objects
        question_type_performance = {}
        for q_type, stats in type_stats.items():
            if stats["attempted"] == 0:
                continue
            
            accuracy = (stats["correct"] / stats["attempted"] * 100) if stats["attempted"] > 0 else 0.0
            attempt_rate = (stats["attempted"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
            
            # Preference score: weighted combination of accuracy and attempt rate
            preference_score = (accuracy * 0.7) + (attempt_rate * 0.3)
            
            question_type_performance[q_type] = QuestionTypePerformance(
                question_type=q_type,
                total_questions=stats["attempted"],
                correct=stats["correct"],
                incorrect=stats["incorrect"],
                accuracy=round(accuracy, 2),
                preference_score=round(preference_score, 2)
            )
        
        return question_type_performance
    
    def _analyze_time_management(
        self,
        test_score: TestScore
    ) -> TimeManagementAnalysis:
        """
        Analyze time management patterns.
        
        Args:
            test_score: TestScore object
        
        Returns:
            TimeManagementAnalysis: Time management insights
        """
        # Calculate average time per question
        attempted = test_score.attempted
        avg_time = test_score.time_taken / attempted if attempted > 0 else 0.0
        
        # Expected time based on exam type
        expected_times = {
            "JEE_MAIN": 54.0,      # 180 min / 200 questions
            "JEE_ADVANCED": 54.0,   # 180 min / 200 questions
            "NEET": 54.0            # 180 min / 200 questions
        }
        expected_avg = expected_times.get(test_score.exam_type, 60.0)
        
        # Calculate time efficiency
        time_efficiency = min(100.0, (expected_avg / avg_time * 100)) if avg_time > 0 else 0.0
        
        # Analyze question-level timing
        too_fast = 0      # < 30 seconds
        too_slow = 0      # > 5 minutes (300 seconds)
        optimal = 0       # 30s - 5min
        
        for q_score in test_score.question_scores:
            if q_score.time_taken is None or q_score.student_answer is None:
                continue
            
            if q_score.time_taken < 30:
                too_fast += 1
            elif q_score.time_taken > 300:
                too_slow += 1
            else:
                optimal += 1
        
        # Generate recommendations
        recommendations = []
        
        if too_fast > attempted * 0.2:  # More than 20% too fast
            recommendations.append(
                "You're rushing through questions. Slow down to avoid careless mistakes."
            )
        
        if too_slow > attempted * 0.15:  # More than 15% too slow
            recommendations.append(
                "Practice solving complex problems within time limits. "
                "Consider skipping very difficult questions initially."
            )
        
        if time_efficiency < 80:
            recommendations.append(
                "Work on improving your solving speed through regular timed practice."
            )
        
        if time_efficiency > 120:
            recommendations.append(
                "You're solving too fast. Spend more time reviewing your answers."
            )
        
        return TimeManagementAnalysis(
            total_time_taken=test_score.time_taken,
            average_time_per_question=round(avg_time, 2),
            expected_average_time=expected_avg,
            time_efficiency=round(time_efficiency, 2),
            too_fast_questions=too_fast,
            too_slow_questions=too_slow,
            optimal_pace_questions=optimal,
            recommendations=recommendations
        )
    
    def _detect_learning_patterns(
        self,
        test_score: TestScore,
        difficulty_perf: Dict[str, DifficultyPerformance],
        question_type_perf: Dict[str, QuestionTypePerformance]
    ) -> List[LearningPattern]:
        """
        Detect learning patterns and preferences.
        
        Args:
            test_score: TestScore object
            difficulty_perf: Difficulty performance mapping
            question_type_perf: Question type performance mapping
        
        Returns:
            List[LearningPattern]: Detected patterns
        """
        patterns = []
        
        # Pattern 1: Question type preference
        if len(question_type_perf) >= 2:
            type_accuracies = {
                q_type: perf.accuracy
                for q_type, perf in question_type_perf.items()
            }
            
            max_type = max(type_accuracies, key=type_accuracies.get)
            min_type = min(type_accuracies, key=type_accuracies.get)
            
            gap = type_accuracies[max_type] - type_accuracies[min_type]
            
            if gap > 20:  # Significant gap
                patterns.append(LearningPattern(
                    pattern_type="question_type_preference",
                    description=f"Strong preference for {max_type} questions",
                    confidence=min(95.0, 60.0 + gap),
                    evidence=f"{max_type}: {type_accuracies[max_type]:.1f}%, "
                             f"{min_type}: {type_accuracies[min_type]:.1f}%",
                    recommendation=f"Balance your practice by focusing more on {min_type} questions"
                ))
        
        # Pattern 2: Difficulty preference
        if len(difficulty_perf) >= 2:
            # Check if performance inversely correlates with difficulty
            easy_acc = difficulty_perf.get("easy")
            medium_acc = difficulty_perf.get("medium")
            hard_acc = difficulty_perf.get("hard")
            
            if easy_acc and hard_acc:
                if easy_acc.accuracy > 80 and hard_acc.accuracy < 40:
                    patterns.append(LearningPattern(
                        pattern_type="difficulty_gap",
                        description="Strong on easy questions but struggling with hard ones",
                        confidence=80.0,
                        evidence=f"Easy: {easy_acc.accuracy:.1f}%, Hard: {hard_acc.accuracy:.1f}%",
                        recommendation="Gradually increase problem difficulty in practice sessions"
                    ))
            
            # Check if medium difficulty is weaker than expected
            if medium_acc and easy_acc:
                if medium_acc.accuracy < easy_acc.accuracy - 25:
                    patterns.append(LearningPattern(
                        pattern_type="medium_difficulty_weakness",
                        description="Unexpected weakness in medium difficulty questions",
                        confidence=75.0,
                        evidence=f"Easy: {easy_acc.accuracy:.1f}%, Medium: {medium_acc.accuracy:.1f}%",
                        recommendation="Focus on medium-level problems to build conceptual understanding"
                    ))
        
        # Pattern 3: Subject strength pattern
        subject_accuracies = {
            subject: score.accuracy
            for subject, score in test_score.subject_scores.items()
        }
        
        if len(subject_accuracies) >= 2:
            max_subject = max(subject_accuracies, key=subject_accuracies.get)
            min_subject = min(subject_accuracies, key=subject_accuracies.get)
            
            gap = subject_accuracies[max_subject] - subject_accuracies[min_subject]
            
            if gap > 25:
                patterns.append(LearningPattern(
                    pattern_type="subject_imbalance",
                    description=f"{max_subject} much stronger than {min_subject}",
                    confidence=min(90.0, 65.0 + gap),
                    evidence=f"{max_subject}: {subject_accuracies[max_subject]:.1f}%, "
                             f"{min_subject}: {subject_accuracies[min_subject]:.1f}%",
                    recommendation=f"Dedicate more study time to {min_subject} to balance your preparation"
                ))
        
        # Pattern 4: Consistency pattern
        topic_accuracies = []
        for subject_score in test_score.subject_scores.values():
            for topic_score in subject_score.topic_scores.values():
                if topic_score.total_questions >= self.min_questions_threshold:
                    topic_accuracies.append(topic_score.accuracy)
        
        if len(topic_accuracies) >= 5:
            import statistics
            std_dev = statistics.stdev(topic_accuracies)
            
            if std_dev < 10:
                patterns.append(LearningPattern(
                    pattern_type="consistent_performance",
                    description="Very consistent performance across topics",
                    confidence=85.0,
                    evidence=f"Low variation in topic scores (std dev: {std_dev:.1f})",
                    recommendation="Good consistency! Focus on overall score improvement"
                ))
            elif std_dev > 25:
                patterns.append(LearningPattern(
                    pattern_type="inconsistent_performance",
                    description="High variation in performance across topics",
                    confidence=80.0,
                    evidence=f"High variation in topic scores (std dev: {std_dev:.1f})",
                    recommendation="Work on building consistent understanding across all topics"
                ))
        
        return patterns
    
    def _generate_recommendations(
        self,
        weak_topics: List[TopicPerformance],
        moderate_topics: List[TopicPerformance],
        exam_type: str
    ) -> List[TopicRecommendation]:
        """
        Generate topic-specific recommendations.
        
        Args:
            weak_topics: List of weak topics
            moderate_topics: List of moderate topics
            exam_type: Type of exam
        
        Returns:
            List[TopicRecommendation]: Recommendations
        """
        recommendations = []
        
        # Generate recommendations for weak topics (high priority)
        for topic_perf in weak_topics:
            improvement_needed = 70.0 - topic_perf.accuracy
            
            action_items = [
                f"Review fundamental concepts of {topic_perf.topic}",
                f"Solve at least 50 practice problems on {topic_perf.topic}",
                f"Watch video lectures covering {topic_perf.topic}",
                "Take topic-specific practice tests"
            ]
            
            # Estimate effort based on gap
            effort_hours = max(5.0, improvement_needed / 5.0)
            
            recommendations.append(TopicRecommendation(
                topic=topic_perf.topic,
                subject=topic_perf.subject,
                priority=PriorityLevel.HIGH,
                current_accuracy=topic_perf.accuracy,
                target_accuracy=70.0,
                improvement_needed=improvement_needed,
                action_items=action_items[:3],  # Top 3 items
                estimated_effort=round(effort_hours, 1)
            ))
        
        # Generate recommendations for moderate topics needing improvement
        for topic_perf in moderate_topics:
            if topic_perf.accuracy < 60.0:  # Below satisfactory
                improvement_needed = 75.0 - topic_perf.accuracy
                
                action_items = [
                    f"Practice {topic_perf.topic} problems of medium difficulty",
                    f"Identify and fix conceptual gaps in {topic_perf.topic}",
                    "Solve previous year questions"
                ]
                
                effort_hours = max(3.0, improvement_needed / 7.0)
                
                recommendations.append(TopicRecommendation(
                    topic=topic_perf.topic,
                    subject=topic_perf.subject,
                    priority=PriorityLevel.MEDIUM,
                    current_accuracy=topic_perf.accuracy,
                    target_accuracy=75.0,
                    improvement_needed=improvement_needed,
                    action_items=action_items,
                    estimated_effort=round(effort_hours, 1)
                ))
        
        # Sort by priority and improvement needed
        recommendations.sort(
            key=lambda x: (
                0 if x.priority == PriorityLevel.HIGH else 1,
                -x.improvement_needed
            )
        )
        
        # Limit to top 10 recommendations
        return recommendations[:10]
    
    def get_overall_insights(
        self,
        analysis: PerformanceAnalysis
    ) -> Dict[str, any]:
        """
        Get high-level insights from analysis.
        
        Args:
            analysis: PerformanceAnalysis object
        
        Returns:
            Dict: Summary insights
        
        Example:
            >>> insights = analyzer.get_overall_insights(analysis)
            >>> print(insights["readiness_score"])
        """
        # Calculate readiness score (0-100)
        readiness_score = min(100.0, (
            analysis.overall_accuracy * 0.6 +
            (len(analysis.strong_topics) / max(1, len(analysis.strong_topics) + len(analysis.weak_topics)) * 40)
        ))
        
        # Identify primary focus area
        if analysis.weak_topics:
            primary_focus = analysis.weak_topics[0].topic
        elif analysis.moderate_topics:
            primary_focus = analysis.moderate_topics[0].topic
        else:
            primary_focus = "Advanced problem solving"
        
        # Calculate preparation status
        if readiness_score >= 80:
            status = "Excellent"
        elif readiness_score >= 60:
            status = "Good"
        elif readiness_score >= 40:
            status = "Needs Improvement"
        else:
            status = "Requires Significant Work"
        
        return {
            "readiness_score": round(readiness_score, 2),
            "preparation_status": status,
            "primary_focus_area": primary_focus,
            "total_topics_analyzed": (
                len(analysis.strong_topics) +
                len(analysis.moderate_topics) +
                len(analysis.weak_topics)
            ),
            "improvement_areas_count": len(analysis.weak_topics),
            "strengths_count": len(analysis.strong_topics),
            "estimated_study_hours": sum(r.estimated_effort for r in analysis.recommendations)
        }


# Example usage
if __name__ == "__main__":
    """
    Example usage of PerformanceAnalyzer.
    """
    print("PerformanceAnalyzer - Example Usage")
    print("=" * 60)
    print("\nThis service analyzes test performance to generate insights.")
    print("\nExample workflow:")
    print("1. Calculate test score using ScoreCalculator")
    print("2. Analyze performance using PerformanceAnalyzer")
    print("3. Get insights and recommendations")
    print("\nSample code:")
    print("""
    from services.score_calculator import ScoreCalculator
    from services.performance_analyzer import PerformanceAnalyzer
    
    # Calculate score
    calculator = ScoreCalculator()
    test_score = calculator.calculate_test_score(...)
    
    # Analyze performance
    analyzer = PerformanceAnalyzer()
    analysis = analyzer.analyze_performance(test_score)
    
    # Get insights
    insights = analyzer.get_overall_insights(analysis)
    
    print(f"Readiness Score: {insights['readiness_score']}")
    print(f"Status: {insights['preparation_status']}")
    print(f"Weak Topics: {len(analysis.weak_topics)}")
    """)
    print("=" * 60)
