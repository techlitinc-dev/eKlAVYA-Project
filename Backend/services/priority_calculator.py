"""
Priority Calculator Service for AI-Powered Study Schedule Generator.

This service calculates priority scores for topics based on student performance,
syllabus weightages, and difficulty levels to power intelligent study scheduling.

The priority calculation considers:
- Current accuracy and gap from target
- Syllabus weightage of topics
- Difficulty level of topics
- Estimated time required for improvement

Formula:
    Priority Score = Weightage × (100 - Current Accuracy) × Difficulty Multiplier
    
    Difficulty Multipliers:
    - Easy: 0.8
    - Medium: 1.0
    - Hard: 1.2
    
    Study Time Estimation:
    Hours = Base Hours × Difficulty Factor × Weakness Factor
    
    Weakness Factors:
    - High accuracy (>70%): 0.5
    - Medium accuracy (40-70%): 1.0
    - Low accuracy (<40%): 1.5

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.priority_calculator import PriorityCalculator
    >>> from models.analytics_models import TopicAnalysis
    >>> 
    >>> calculator = PriorityCalculator(exam_type="JEE_MAIN")
    >>> 
    >>> # Calculate priority for a single topic
    >>> topic_data = {
    ...     "topic": "Thermodynamics",
    ...     "subject": "Physics",
    ...     "accuracy": 25.0,
    ...     "total_questions": 10,
    ...     "correct": 2,
    ...     "incorrect": 8
    ... }
    >>> 
    >>> priority = calculator.calculate_topic_priority(
    ...     topic_name="Thermodynamics",
    ...     subject="Physics",
    ...     current_accuracy=25.0,
    ...     difficulty="medium"
    ... )
    >>> print(f"Priority Score: {priority.priority_score:.2f}")
    >>> print(f"Estimated Hours: {priority.estimated_hours:.1f}")
    >>> 
    >>> # Rank all topics from analytics
    >>> ranked_topics = calculator.rank_topics(
    ...     topic_performances=[topic_data],  # List of topic performance data
    ...     top_n=10
    ... )
    >>> 
    >>> # Filter high-priority topics
    >>> critical_topics = calculator.get_high_priority_topics(
    ...     ranked_topics,
    ...     threshold=200
    ... )
"""

import logging
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# Configure logging
logger = logging.getLogger(__name__)


class DifficultyLevel(str, Enum):
    """Difficulty level of a topic."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class PriorityLabel(str, Enum):
    """Priority level labels for topics."""
    CRITICAL = "critical"    # Priority score > 300
    HIGH = "high"            # Priority score 200-300
    MEDIUM = "medium"        # Priority score 100-200
    LOW = "low"             # Priority score < 100


class TopicPriority(BaseModel):
    """
    Priority calculation result for a single topic.
    
    Attributes:
        topic: Topic name
        subject: Subject name
        current_accuracy: Current accuracy percentage (0-100)
        target_accuracy: Target accuracy percentage (default: 70.0)
        weightage: Topic weightage in exam (0-100)
        difficulty: Difficulty level (easy, medium, hard)
        priority_score: Calculated priority score
        priority_label: Priority level label (critical, high, medium, low)
        estimated_hours: Estimated study hours needed
        improvement_needed: Accuracy points needed to reach target
    """
    topic: str = Field(..., description="Topic name")
    subject: str = Field(..., description="Subject name")
    current_accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Current accuracy percentage"
    )
    target_accuracy: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Target accuracy percentage"
    )
    weightage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Topic weightage in exam"
    )
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    priority_score: float = Field(..., ge=0.0, description="Calculated priority score")
    priority_label: PriorityLabel = Field(..., description="Priority level label")
    estimated_hours: float = Field(
        ...,
        ge=0.5,
        le=20.0,
        description="Estimated study hours needed"
    )
    improvement_needed: float = Field(
        ...,
        description="Accuracy points needed to reach target"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "topic": "Thermodynamics",
                "subject": "Physics",
                "current_accuracy": 25.0,
                "target_accuracy": 70.0,
                "weightage": 4.0,
                "difficulty": "medium",
                "priority_score": 300.0,
                "priority_label": "critical",
                "estimated_hours": 12.0,
                "improvement_needed": 45.0
            }
        }


class PriorityCalculatorError(Exception):
    """Base exception for priority calculator errors."""
    pass


class WeightageNotFoundError(PriorityCalculatorError):
    """Exception raised when topic weightage not found in syllabus."""
    pass


class InvalidInputError(PriorityCalculatorError):
    """Exception raised for invalid input data."""
    pass


class PriorityCalculator:
    """
    Calculate priority scores and rank topics for study scheduling.
    
    This service integrates student performance data with syllabus weightages
    to generate intelligent priority rankings for study planning.
    
    Attributes:
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        weightages: Loaded syllabus weightages for the exam
        difficulty_multipliers: Multipliers for different difficulty levels
        weakness_factors: Factors based on accuracy ranges
        base_study_hours: Base study hours for topics
    
    Example:
        >>> calculator = PriorityCalculator(exam_type="JEE_MAIN")
        >>> priority = calculator.calculate_topic_priority(
        ...     topic_name="Mechanics",
        ...     subject="Physics",
        ...     current_accuracy=60.0,
        ...     difficulty="medium"
        ... )
    """
    
    # Difficulty multipliers for priority calculation
    DIFFICULTY_MULTIPLIERS = {
        DifficultyLevel.EASY: 0.8,
        DifficultyLevel.MEDIUM: 1.0,
        DifficultyLevel.HARD: 1.2
    }
    
    # Difficulty factors for study time estimation
    DIFFICULTY_FACTORS = {
        DifficultyLevel.EASY: 0.8,
        DifficultyLevel.MEDIUM: 1.0,
        DifficultyLevel.HARD: 1.3
    }
    
    # Base study hours per topic (hours)
    BASE_STUDY_HOURS = 8.0
    
    def __init__(
        self,
        exam_type: str = "JEE_MAIN",
        data_dir: Optional[Path] = None
    ):
        """
        Initialize priority calculator with exam-specific data.
        
        Args:
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            data_dir: Optional path to data directory (default: ./data)
        
        Raises:
            FileNotFoundError: If syllabus data files not found
            ValueError: If invalid exam type
        """
        self.exam_type = exam_type.upper()
        
        # Validate exam type
        valid_exam_types = ["JEE_MAIN", "JEE_ADVANCED", "NEET"]
        if self.exam_type not in valid_exam_types:
            raise ValueError(
                f"Invalid exam type: {exam_type}. "
                f"Must be one of {valid_exam_types}"
            )
        
        # Set data directory
        if data_dir is None:
            # Default to data/syllabus relative to project root
            current_file = Path(__file__)
            project_root = current_file.parent.parent
            self.data_dir = project_root / "data" / "syllabus"
        else:
            self.data_dir = Path(data_dir)
        
        # Load syllabus weightages
        self.weightages = self._load_weightages()
        
        logger.info(
            f"PriorityCalculator initialized for {self.exam_type} "
            f"with {len(self.weightages)} topics"
        )
    
    def _load_weightages(self) -> Dict[str, Dict[str, any]]:
        """
        Load syllabus weightages from JSON files.
        
        Returns:
            Dict mapping (subject, topic) to weightage and difficulty
        
        Raises:
            FileNotFoundError: If syllabus files not found
        """
        weightages = {}
        
        # Subjects to load based on exam type
        if self.exam_type in ["JEE_MAIN", "JEE_ADVANCED"]:
            subjects = ["Physics", "Chemistry", "Mathematics"]
        else:  # NEET
            subjects = ["Physics", "Chemistry", "Biology"]
        
        for subject in subjects:
            file_path = self.data_dir / f"{self.exam_type}_{subject}.json"
            
            if not file_path.exists():
                logger.warning(f"Syllabus file not found: {file_path}")
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    syllabus_data = json.load(f)
                
                # Extract topic weightages
                for chapter in syllabus_data.get("chapters", []):
                    for topic in chapter.get("topics", []):
                        topic_name = topic.get("topic_name")
                        weightage = topic.get("weightage", 0.0)
                        difficulty = topic.get("difficulty", "medium")
                        
                        if topic_name:
                            key = (subject, topic_name)
                            weightages[key] = {
                                "weightage": float(weightage),
                                "difficulty": difficulty,
                                "chapter": chapter.get("chapter_name")
                            }
                
                logger.info(f"Loaded {len(weightages)} topics from {subject}")
                
            except Exception as e:
                logger.error(f"Error loading syllabus for {subject}: {e}")
                continue
        
        if not weightages:
            logger.warning(
                f"No weightages loaded for {self.exam_type}. "
                "Using default weightages."
            )
        
        return weightages
    
    def get_topic_weightage(
        self,
        topic_name: str,
        subject: str
    ) -> Tuple[float, str]:
        """
        Get weightage and difficulty for a topic.
        
        Args:
            topic_name: Topic name
            subject: Subject name
        
        Returns:
            Tuple of (weightage, difficulty)
        
        Raises:
            WeightageNotFoundError: If topic not found in syllabus
        """
        key = (subject, topic_name)
        
        if key not in self.weightages:
            # Try case-insensitive match
            for (subj, topic), data in self.weightages.items():
                if (subj.lower() == subject.lower() and 
                    topic.lower() == topic_name.lower()):
                    return data["weightage"], data["difficulty"]
            
            logger.warning(
                f"Topic weightage not found: {subject} - {topic_name}. "
                "Using default weightage."
            )
            # Return default values
            return 5.0, "medium"
        
        topic_data = self.weightages[key]
        return topic_data["weightage"], topic_data["difficulty"]
    
    def calculate_priority_score(
        self,
        current_accuracy: float,
        weightage: float,
        difficulty: str
    ) -> float:
        """
        Calculate priority score for a topic.
        
        Formula:
            Priority Score = Weightage × (100 - Current Accuracy) × Difficulty Multiplier
        
        Args:
            current_accuracy: Current accuracy percentage (0-100)
            weightage: Topic weightage in exam (0-100)
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            Priority score (0+)
        
        Raises:
            InvalidInputError: If input values are invalid
        """
        # Validate inputs
        if not 0.0 <= current_accuracy <= 100.0:
            raise InvalidInputError(
                f"Accuracy must be between 0 and 100, got {current_accuracy}"
            )
        
        if not 0.0 <= weightage <= 100.0:
            raise InvalidInputError(
                f"Weightage must be between 0 and 100, got {weightage}"
            )
        
        # Normalize difficulty
        try:
            diff_level = DifficultyLevel(difficulty.lower())
        except ValueError:
            logger.warning(
                f"Invalid difficulty level: {difficulty}. Using 'medium'."
            )
            diff_level = DifficultyLevel.MEDIUM
        
        # Get difficulty multiplier
        multiplier = self.DIFFICULTY_MULTIPLIERS[diff_level]
        
        # Calculate accuracy gap (clamped to 0-100)
        accuracy_gap = max(0.0, min(100.0, 100.0 - current_accuracy))
        
        # Calculate priority score
        priority_score = weightage * accuracy_gap * multiplier
        
        return max(0.0, priority_score)
    
    def estimate_study_hours(
        self,
        current_accuracy: float,
        target_accuracy: float,
        difficulty: str
    ) -> float:
        """
        Estimate study hours needed to improve from current to target accuracy.
        
        Formula:
            Hours = Base Hours × Difficulty Factor × Weakness Factor
        
        Weakness Factors:
            - High accuracy (>70%): 0.5
            - Medium accuracy (40-70%): 1.0
            - Low accuracy (<40%): 1.5
        
        Args:
            current_accuracy: Current accuracy percentage (0-100)
            target_accuracy: Target accuracy percentage (0-100)
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            Estimated study hours (0.5-20.0)
        
        Raises:
            InvalidInputError: If input values are invalid
        """
        # Validate inputs
        if not 0.0 <= current_accuracy <= 100.0:
            raise InvalidInputError(
                f"Current accuracy must be between 0 and 100, got {current_accuracy}"
            )
        
        if not 0.0 <= target_accuracy <= 100.0:
            raise InvalidInputError(
                f"Target accuracy must be between 0 and 100, got {target_accuracy}"
            )
        
        # If already at or above target, minimal hours needed
        if current_accuracy >= target_accuracy:
            return 0.5
        
        # Normalize difficulty
        try:
            diff_level = DifficultyLevel(difficulty.lower())
        except ValueError:
            diff_level = DifficultyLevel.MEDIUM
        
        # Get difficulty factor
        difficulty_factor = self.DIFFICULTY_FACTORS[diff_level]
        
        # Determine weakness factor based on current accuracy
        if current_accuracy > 70.0:
            weakness_factor = 0.5  # Strong, just needs refinement
        elif current_accuracy >= 40.0:
            weakness_factor = 1.0  # Moderate, needs practice
        else:
            weakness_factor = 1.5  # Weak, needs significant work
        
        # Calculate improvement percentage needed
        improvement_needed = target_accuracy - current_accuracy
        improvement_factor = improvement_needed / 100.0  # Normalize to 0-1
        
        # Calculate base hours
        hours = (
            self.BASE_STUDY_HOURS *
            difficulty_factor *
            weakness_factor *
            improvement_factor * 2.0  # Scale factor
        )
        
        # Clamp to realistic range
        hours = max(0.5, min(20.0, hours))
        
        return round(hours, 1)
    
    def get_priority_label(self, priority_score: float) -> PriorityLabel:
        """
        Get priority label based on priority score.
        
        Args:
            priority_score: Calculated priority score
        
        Returns:
            Priority label (critical, high, medium, low)
        """
        if priority_score >= 300:
            return PriorityLabel.CRITICAL
        elif priority_score >= 200:
            return PriorityLabel.HIGH
        elif priority_score >= 100:
            return PriorityLabel.MEDIUM
        else:
            return PriorityLabel.LOW
    
    def calculate_topic_priority(
        self,
        topic_name: str,
        subject: str,
        current_accuracy: float,
        difficulty: Optional[str] = None,
        target_accuracy: float = 70.0
    ) -> TopicPriority:
        """
        Calculate complete priority data for a single topic.
        
        Args:
            topic_name: Topic name
            subject: Subject name
            current_accuracy: Current accuracy percentage (0-100)
            difficulty: Optional difficulty level (uses syllabus if not provided)
            target_accuracy: Target accuracy percentage (default: 70.0)
        
        Returns:
            TopicPriority with all calculated data
        
        Raises:
            InvalidInputError: If input values are invalid
        """
        # Get weightage and difficulty from syllabus
        weightage, syllabus_difficulty = self.get_topic_weightage(
            topic_name,
            subject
        )
        
        # Use provided difficulty or syllabus difficulty
        final_difficulty = difficulty if difficulty else syllabus_difficulty
        
        # Calculate priority score
        priority_score = self.calculate_priority_score(
            current_accuracy=current_accuracy,
            weightage=weightage,
            difficulty=final_difficulty
        )
        
        # Get priority label
        priority_label = self.get_priority_label(priority_score)
        
        # Estimate study hours
        estimated_hours = self.estimate_study_hours(
            current_accuracy=current_accuracy,
            target_accuracy=target_accuracy,
            difficulty=final_difficulty
        )
        
        # Calculate improvement needed
        improvement_needed = max(0.0, target_accuracy - current_accuracy)
        
        return TopicPriority(
            topic=topic_name,
            subject=subject,
            current_accuracy=current_accuracy,
            target_accuracy=target_accuracy,
            weightage=weightage,
            difficulty=DifficultyLevel(final_difficulty.lower()),
            priority_score=priority_score,
            priority_label=priority_label,
            estimated_hours=estimated_hours,
            improvement_needed=improvement_needed
        )
    
    def rank_topics(
        self,
        topic_performances: List[Dict[str, any]],
        target_accuracy: float = 70.0,
        top_n: Optional[int] = None
    ) -> List[TopicPriority]:
        """
        Rank topics by priority score from performance data.
        
        Args:
            topic_performances: List of topic performance dicts with keys:
                - topic: Topic name
                - subject: Subject name
                - accuracy: Current accuracy percentage
                - difficulty: Optional difficulty level
            target_accuracy: Target accuracy for all topics (default: 70.0)
            top_n: Optional limit for top N topics
        
        Returns:
            List of TopicPriority sorted by priority score (highest first)
        
        Example:
            >>> topics = [
            ...     {"topic": "Mechanics", "subject": "Physics", "accuracy": 60.0},
            ...     {"topic": "Thermodynamics", "subject": "Physics", "accuracy": 25.0}
            ... ]
            >>> ranked = calculator.rank_topics(topics, top_n=10)
        """
        priorities = []
        
        for topic_data in topic_performances:
            try:
                # Extract required fields
                topic_name = topic_data.get("topic")
                subject = topic_data.get("subject")
                accuracy = topic_data.get("accuracy")
                difficulty = topic_data.get("difficulty")
                
                if not all([topic_name, subject, accuracy is not None]):
                    logger.warning(f"Skipping incomplete topic data: {topic_data}")
                    continue
                
                # Calculate priority
                priority = self.calculate_topic_priority(
                    topic_name=topic_name,
                    subject=subject,
                    current_accuracy=float(accuracy),
                    difficulty=difficulty,
                    target_accuracy=target_accuracy
                )
                
                priorities.append(priority)
                
            except Exception as e:
                logger.error(f"Error calculating priority for topic: {e}")
                continue
        
        # Sort by priority score (highest first)
        priorities.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Limit to top N if specified
        if top_n:
            priorities = priorities[:top_n]
        
        logger.info(
            f"Ranked {len(priorities)} topics by priority score"
        )
        
        return priorities
    
    def get_high_priority_topics(
        self,
        ranked_topics: List[TopicPriority],
        threshold: float = 200.0,
        top_n: Optional[int] = None
    ) -> List[TopicPriority]:
        """
        Filter topics above a priority threshold.
        
        Args:
            ranked_topics: List of TopicPriority objects (sorted)
            threshold: Minimum priority score (default: 200.0)
            top_n: Optional limit for top N topics
        
        Returns:
            List of high-priority topics
        
        Example:
            >>> critical_topics = calculator.get_high_priority_topics(
            ...     ranked_topics,
            ...     threshold=200
            ... )
        """
        # Filter by threshold
        high_priority = [
            topic for topic in ranked_topics
            if topic.priority_score >= threshold
        ]
        
        # Limit to top N if specified
        if top_n:
            high_priority = high_priority[:top_n]
        
        logger.info(
            f"Filtered {len(high_priority)} high-priority topics "
            f"(threshold: {threshold})"
        )
        
        return high_priority
    
    def get_critical_topics(
        self,
        ranked_topics: List[TopicPriority]
    ) -> List[TopicPriority]:
        """
        Get critical priority topics (priority score >= 300).
        
        Args:
            ranked_topics: List of TopicPriority objects
        
        Returns:
            List of critical topics
        """
        return [
            topic for topic in ranked_topics
            if topic.priority_label == PriorityLabel.CRITICAL
        ]
    
    def calculate_total_study_time(
        self,
        topics: List[TopicPriority]
    ) -> float:
        """
        Calculate total estimated study time for a list of topics.
        
        Args:
            topics: List of TopicPriority objects
        
        Returns:
            Total estimated hours
        """
        total_hours = sum(topic.estimated_hours for topic in topics)
        return round(total_hours, 1)
    
    def get_subject_priorities(
        self,
        ranked_topics: List[TopicPriority]
    ) -> Dict[str, Dict[str, any]]:
        """
        Get priority statistics grouped by subject.
        
        Args:
            ranked_topics: List of TopicPriority objects
        
        Returns:
            Dict mapping subject to statistics:
                - total_topics: Total topics in subject
                - critical_topics: Number of critical topics
                - high_topics: Number of high priority topics
                - total_hours: Total estimated hours
                - avg_priority: Average priority score
        """
        subject_stats = {}
        
        for topic in ranked_topics:
            subject = topic.subject
            
            if subject not in subject_stats:
                subject_stats[subject] = {
                    "total_topics": 0,
                    "critical_topics": 0,
                    "high_topics": 0,
                    "medium_topics": 0,
                    "low_topics": 0,
                    "total_hours": 0.0,
                    "priority_scores": []
                }
            
            stats = subject_stats[subject]
            stats["total_topics"] += 1
            stats["total_hours"] += topic.estimated_hours
            stats["priority_scores"].append(topic.priority_score)
            
            # Count by priority label
            if topic.priority_label == PriorityLabel.CRITICAL:
                stats["critical_topics"] += 1
            elif topic.priority_label == PriorityLabel.HIGH:
                stats["high_topics"] += 1
            elif topic.priority_label == PriorityLabel.MEDIUM:
                stats["medium_topics"] += 1
            else:
                stats["low_topics"] += 1
        
        # Calculate averages
        for subject, stats in subject_stats.items():
            if stats["priority_scores"]:
                stats["avg_priority"] = round(
                    sum(stats["priority_scores"]) / len(stats["priority_scores"]),
                    2
                )
            else:
                stats["avg_priority"] = 0.0
            
            # Remove temporary priority_scores list
            del stats["priority_scores"]
            
            # Round total hours
            stats["total_hours"] = round(stats["total_hours"], 1)
        
        return subject_stats
