"""
Weightage Calculator for Diagnostic Test Question Distribution.

This module calculates how many questions to generate per topic based on
topic weightages, exam patterns, and various constraints to ensure balanced
and comprehensive test coverage.

Example Usage:
    >>> from utils.pattern_loader import PatternLoader
    >>> from utils.weightage_calculator import WeightageCalculator
    >>> 
    >>> loader = PatternLoader()
    >>> pattern = loader.load_pattern("JEE_MAIN")
    >>> 
    >>> calculator = WeightageCalculator()
    >>> syllabus = [
    ...     {"topic_id": "phy_mechanics", "subject": "Physics", 
    ...      "chapter": "Mechanics", "weightage": 25},
    ...     {"topic_id": "phy_thermodynamics", "subject": "Physics",
    ...      "chapter": "Thermodynamics", "weightage": 15}
    ... ]
    >>> 
    >>> distribution = calculator.calculate_distribution(
    ...     syllabus=syllabus,
    ...     total_questions=30,
    ...     exam_pattern=pattern,
    ...     subject="Physics"
    ... )
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TopicInfo:
    """Information about a topic for question distribution."""
    topic_id: str
    subject: str
    chapter: str
    weightage: float  # Marks/importance
    min_questions: int = 2
    max_questions: Optional[int] = None
    priority: int = 1  # Higher priority = more important


@dataclass
class DistributionResult:
    """Result of question distribution calculation."""
    topic_distribution: Dict[str, int]  # topic_id -> question_count
    subject_totals: Dict[str, int]  # subject -> total_questions
    metadata: Dict[str, Dict]  # topic_id -> topic metadata
    total_questions: int
    is_valid: bool
    warnings: List[str]


class WeightageCalculator:
    """
    Calculates question distribution based on topic weightages and constraints.
    
    This class implements intelligent question distribution that:
    - Respects topic weightages proportionally
    - Ensures minimum and maximum question constraints
    - Balances coverage across all topics
    - Uses largest remainder method for rounding
    - Validates final distribution against requirements
    
    Attributes:
        min_questions_per_topic (int): Minimum questions per topic if included
        max_questions_per_topic (int): Maximum questions per topic
        high_weightage_threshold (float): Threshold for mandatory inclusion
    """
    
    def __init__(
        self,
        min_questions_per_topic: int = 2,
        max_questions_per_topic: int = 20,
        high_weightage_threshold: float = 10.0
    ):
        """
        Initialize the WeightageCalculator.
        
        Args:
            min_questions_per_topic: Minimum questions per topic (default: 2)
            max_questions_per_topic: Maximum questions per topic (default: 20)
            high_weightage_threshold: Weightage threshold for mandatory inclusion (default: 10.0)
        """
        self.min_questions_per_topic = min_questions_per_topic
        self.max_questions_per_topic = max_questions_per_topic
        self.high_weightage_threshold = high_weightage_threshold
        logger.info(
            f"WeightageCalculator initialized: min={min_questions_per_topic}, "
            f"max={max_questions_per_topic}, threshold={high_weightage_threshold}"
        )
    
    def calculate_distribution(
        self,
        syllabus: List[Dict],
        total_questions: int,
        exam_pattern: Optional[object] = None,
        subject: Optional[str] = None,
        subject_distribution: Optional[Dict[str, int]] = None
    ) -> DistributionResult:
        """
        Calculate question distribution across topics.
        
        Args:
            syllabus: List of topic dictionaries with keys:
                     - topic_id: str
                     - subject: str
                     - chapter: str
                     - weightage: float (marks/importance)
                     - min_questions: int (optional)
                     - max_questions: int (optional)
            total_questions: Total number of questions to distribute
            exam_pattern: Optional ExamPattern object for additional constraints
            subject: Optional subject filter (distribute only for this subject)
            subject_distribution: Optional dict mapping subjects to question counts
            
        Returns:
            DistributionResult containing the calculated distribution and metadata
        """
        logger.info(
            f"Calculating distribution for {total_questions} questions "
            f"across {len(syllabus)} topics"
        )
        
        # Convert syllabus to TopicInfo objects
        topics = self._parse_syllabus(syllabus)
        
        # Filter by subject if specified
        if subject:
            topics = [t for t in topics if t.subject == subject]
            logger.info(f"Filtered to {len(topics)} topics for subject: {subject}")
        
        # Validate inputs
        if not topics:
            logger.error("No topics provided for distribution")
            return DistributionResult(
                topic_distribution={},
                subject_totals={},
                metadata={},
                total_questions=0,
                is_valid=False,
                warnings=["No topics provided"]
            )
        
        if total_questions < len(topics) * self.min_questions_per_topic:
            logger.warning(
                f"Total questions ({total_questions}) may be insufficient for "
                f"{len(topics)} topics with minimum {self.min_questions_per_topic} each"
            )
        
        # Calculate proportional distribution
        distribution = self._proportional_distribution(topics, total_questions)
        
        # Apply constraints
        distribution = self._apply_constraints(distribution, topics, total_questions)
        
        # Balance distribution using largest remainder method
        distribution = self._balance_distribution(distribution, topics, total_questions)
        
        # Build result
        result = self._build_result(distribution, topics, total_questions)
        
        # Validate
        validation_warnings = self._validate_distribution(
            result, total_questions, subject_distribution
        )
        result.warnings.extend(validation_warnings)
        
        logger.info(
            f"Distribution calculated: {result.total_questions} questions "
            f"across {len(result.topic_distribution)} topics"
        )
        
        return result
    
    def _parse_syllabus(self, syllabus: List[Dict]) -> List[TopicInfo]:
        """Parse syllabus dictionaries into TopicInfo objects."""
        topics = []
        for item in syllabus:
            topic = TopicInfo(
                topic_id=item.get("topic_id", ""),
                subject=item.get("subject", ""),
                chapter=item.get("chapter", ""),
                weightage=float(item.get("weightage", 0)),
                min_questions=item.get("min_questions", self.min_questions_per_topic),
                max_questions=item.get("max_questions", self.max_questions_per_topic),
                priority=item.get("priority", 1)
            )
            topics.append(topic)
        return topics
    
    def _proportional_distribution(
        self,
        topics: List[TopicInfo],
        total_questions: int
    ) -> Dict[str, float]:
        """
        Calculate proportional distribution based on weightages.
        
        Args:
            topics: List of TopicInfo objects
            total_questions: Total questions to distribute
            
        Returns:
            Dictionary mapping topic_id to fractional question count
        """
        # Calculate total weightage
        total_weightage = sum(t.weightage for t in topics)
        
        if total_weightage == 0:
            logger.warning("Total weightage is 0, using equal distribution")
            equal_share = total_questions / len(topics)
            return {t.topic_id: equal_share for t in topics}
        
        # Calculate proportional distribution
        distribution = {}
        for topic in topics:
            proportion = topic.weightage / total_weightage
            questions = proportion * total_questions
            distribution[topic.topic_id] = questions
            logger.debug(
                f"Topic {topic.topic_id}: weightage={topic.weightage}, "
                f"proportion={proportion:.2%}, questions={questions:.2f}"
            )
        
        return distribution
    
    def _apply_constraints(
        self,
        distribution: Dict[str, float],
        topics: List[TopicInfo],
        total_questions: int
    ) -> Dict[str, float]:
        """
        Apply minimum and maximum constraints to distribution.
        
        Args:
            distribution: Current fractional distribution
            topics: List of TopicInfo objects
            total_questions: Total questions available
            
        Returns:
            Adjusted distribution respecting constraints
        """
        topic_map = {t.topic_id: t for t in topics}
        adjusted = distribution.copy()
        
        # Apply minimum constraints for high-weightage topics
        for topic_id, count in distribution.items():
            topic = topic_map[topic_id]
            
            # Ensure high-weightage topics get minimum questions
            if topic.weightage >= self.high_weightage_threshold:
                if count < topic.min_questions:
                    logger.info(
                        f"Adjusting {topic_id} from {count:.2f} to minimum "
                        f"{topic.min_questions} (high weightage: {topic.weightage})"
                    )
                    adjusted[topic_id] = float(topic.min_questions)
            
            # Apply maximum constraints
            if topic.max_questions and count > topic.max_questions:
                logger.info(
                    f"Capping {topic_id} at maximum {topic.max_questions} "
                    f"(was {count:.2f})"
                )
                adjusted[topic_id] = float(topic.max_questions)
        
        return adjusted
    
    def _balance_distribution(
        self,
        distribution: Dict[str, float],
        topics: List[TopicInfo],
        total_questions: int
    ) -> Dict[str, int]:
        """
        Balance distribution using largest remainder method.
        
        This ensures the total exactly matches requirements while
        distributing rounding errors fairly.
        
        Args:
            distribution: Fractional distribution
            topics: List of TopicInfo objects
            total_questions: Target total questions
            
        Returns:
            Integer distribution that sums to total_questions
        """
        topic_map = {t.topic_id: t for t in topics}
        
        # Floor all values and calculate remainders
        floored = {}
        remainders = {}
        
        for topic_id, count in distribution.items():
            topic = topic_map[topic_id]
            floor_val = int(count)
            
            # Apply max constraint during flooring
            if topic.max_questions:
                floor_val = min(floor_val, topic.max_questions)
            
            # Apply min constraint
            floor_val = max(floor_val, topic.min_questions)
            
            floored[topic_id] = floor_val
            remainders[topic_id] = count - int(count)  # Fractional part only
        
        # Calculate how many questions we need to add
        current_total = sum(floored.values())
        needed = total_questions - current_total
        
        logger.debug(
            f"After flooring: {current_total} questions, need {needed} more"
        )
        
        if needed > 0:
            # Sort by remainder (largest first), then by weightage
            sorted_topics = sorted(
                remainders.items(),
                key=lambda x: (x[1], topic_map[x[0]].weightage, topic_map[x[0]].priority),
                reverse=True
            )
            
            # Distribute extra questions
            added = 0
            attempts = 0
            max_attempts = len(sorted_topics) * 2
            
            while added < needed and attempts < max_attempts:
                for topic_id, _ in sorted_topics:
                    if added >= needed:
                        break
                    
                    topic = topic_map[topic_id]
                    
                    # Check max constraint
                    if topic.max_questions and floored[topic_id] >= topic.max_questions:
                        continue
                    
                    floored[topic_id] += 1
                    added += 1
                    logger.debug(f"Added 1 question to {topic_id} (remainder method)")
                
                attempts += 1
        
        elif needed < 0:
            # Remove excess questions from lowest-weightage topics
            sorted_topics = sorted(
                topics,
                key=lambda t: (t.weightage, t.priority)
            )
            
            removed = 0
            for topic in sorted_topics:
                if removed >= abs(needed):
                    break
                if floored[topic.topic_id] > topic.min_questions:
                    reduction = min(
                        floored[topic.topic_id] - topic.min_questions,
                        abs(needed) - removed
                    )
                    floored[topic.topic_id] -= reduction
                    removed += reduction
                    logger.debug(
                        f"Removed {reduction} question(s) from {topic.topic_id}"
                    )
        
        return floored
    
    def _build_result(
        self,
        distribution: Dict[str, int],
        topics: List[TopicInfo],
        total_questions: int
    ) -> DistributionResult:
        """Build the final DistributionResult object."""
        topic_map = {t.topic_id: t for t in topics}
        
        # Calculate subject totals
        subject_totals = defaultdict(int)
        for topic_id, count in distribution.items():
            topic = topic_map[topic_id]
            subject_totals[topic.subject] += count
        
        # Build metadata
        metadata = {}
        for topic_id, count in distribution.items():
            topic = topic_map[topic_id]
            metadata[topic_id] = {
                "subject": topic.subject,
                "chapter": topic.chapter,
                "weightage": topic.weightage,
                "question_count": count,
                "percentage": (count / total_questions * 100) if total_questions > 0 else 0
            }
        
        actual_total = sum(distribution.values())
        
        return DistributionResult(
            topic_distribution=distribution,
            subject_totals=dict(subject_totals),
            metadata=metadata,
            total_questions=actual_total,
            is_valid=(actual_total == total_questions),
            warnings=[]
        )
    
    def _validate_distribution(
        self,
        result: DistributionResult,
        expected_total: int,
        subject_distribution: Optional[Dict[str, int]] = None
    ) -> List[str]:
        """
        Validate the distribution against requirements.
        
        Args:
            result: DistributionResult to validate
            expected_total: Expected total questions
            subject_distribution: Optional expected subject distribution
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check total
        if result.total_questions != expected_total:
            warnings.append(
                f"Total questions mismatch: got {result.total_questions}, "
                f"expected {expected_total}"
            )
            logger.error(warnings[-1])
        
        # Check subject distribution if provided
        if subject_distribution:
            for subject, expected_count in subject_distribution.items():
                actual_count = result.subject_totals.get(subject, 0)
                if actual_count != expected_count:
                    warnings.append(
                        f"Subject {subject} mismatch: got {actual_count}, "
                        f"expected {expected_count}"
                    )
                    logger.warning(warnings[-1])
        
        # Check for topics with 0 questions
        zero_topics = [
            tid for tid, count in result.topic_distribution.items()
            if count == 0
        ]
        if zero_topics:
            warnings.append(
                f"{len(zero_topics)} topics have 0 questions: {zero_topics[:3]}"
            )
            logger.warning(warnings[-1])
        
        # Check for topics exceeding reasonable limits
        high_count_topics = [
            (tid, count) for tid, count in result.topic_distribution.items()
            if count > self.max_questions_per_topic
        ]
        if high_count_topics:
            warnings.append(
                f"{len(high_count_topics)} topics exceed max questions"
            )
            logger.warning(warnings[-1])
        
        if not warnings:
            logger.info("✓ Distribution validation passed")
        
        return warnings
    
    def get_distribution_summary(self, result: DistributionResult) -> str:
        """
        Generate a human-readable summary of the distribution.
        
        Args:
            result: DistributionResult to summarize
            
        Returns:
            Formatted string summary
        """
        lines = [
            "=" * 70,
            "QUESTION DISTRIBUTION SUMMARY",
            "=" * 70,
            f"Total Questions: {result.total_questions}",
            f"Valid: {'✓' if result.is_valid else '✗'}",
            ""
        ]
        
        if result.warnings:
            lines.append("Warnings:")
            for warning in result.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")
        
        lines.append("Subject Distribution:")
        for subject, count in sorted(result.subject_totals.items()):
            percentage = (count / result.total_questions * 100) if result.total_questions > 0 else 0
            lines.append(f"  {subject}: {count} questions ({percentage:.1f}%)")
        
        lines.append("\nTopic Distribution:")
        sorted_topics = sorted(
            result.metadata.items(),
            key=lambda x: (x[1]['subject'], -x[1]['weightage'])
        )
        
        for topic_id, meta in sorted_topics:
            lines.append(
                f"  {topic_id}: {meta['question_count']} questions "
                f"(weightage: {meta['weightage']}, {meta['percentage']:.1f}%)"
            )
        
        lines.append("=" * 70)
        
        return "\n".join(lines)
