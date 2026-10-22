"""
Question Distribution Service for Mentor AI Diagnostic Tests.

This service orchestrates the complete question distribution process for
diagnostic tests, integrating pattern loading, weightage calculation, and
difficulty/question type distribution.

Example Usage:
    >>> from services.question_distribution import QuestionDistributionService
    >>> 
    >>> service = QuestionDistributionService()
    >>> distribution_plan = service.create_distribution(
    ...     exam_type="JEE_MAIN",
    ...     student_id="student_12345"
    ... )
    >>> print(f"Total questions: {distribution_plan.total_questions}")
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator

# Import utilities (in production, these would be proper imports)
# from utils.pattern_loader import PatternLoader, ExamPattern
# from utils.weightage_calculator import WeightageCalculator
# from utils.firebase_config import get_firestore_client


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DifficultyLevel(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    """Question types."""
    MCQ = "MCQ"
    MSQ = "MSQ"
    NUMERICAL = "Numerical"
    INTEGER = "Integer"
    ASSERTION_REASON = "Assertion-Reason"


class TopicDistribution(BaseModel):
    """Distribution details for a single topic."""
    topic_id: str = Field(..., description="Unique topic identifier")
    topic_name: str = Field(..., description="Display name of the topic")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    question_count: int = Field(..., gt=0, description="Total questions for this topic")
    weightage: float = Field(..., ge=0, description="Topic weightage/importance")
    priority: int = Field(default=1, description="Topic priority (higher = more important)")
    
    # Difficulty split
    difficulty_split: Dict[str, int] = Field(
        default_factory=dict,
        description="Questions per difficulty level"
    )
    
    # Question type split
    question_type_split: Dict[str, int] = Field(
        default_factory=dict,
        description="Questions per question type"
    )
    
    class Config:
        use_enum_values = True


class DistributionPlan(BaseModel):
    """Complete question distribution plan for a diagnostic test."""
    plan_id: str = Field(..., description="Unique plan identifier")
    exam_type: str = Field(..., description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)")
    exam_name: str = Field(..., description="Display name of exam")
    student_id: Optional[str] = Field(None, description="Student ID if personalized")
    total_questions: int = Field(..., gt=0, description="Total questions in test")
    duration_minutes: int = Field(..., gt=0, description="Test duration")
    
    # Subject-level distribution
    subject_distribution: Dict[str, int] = Field(
        ...,
        description="Questions per subject"
    )
    
    # Topic-level distribution
    topic_distribution: List[TopicDistribution] = Field(
        ...,
        min_items=1,
        description="Detailed topic-wise distribution"
    )
    
    # Overall difficulty distribution
    difficulty_distribution: Dict[str, int] = Field(
        ...,
        description="Total questions per difficulty level"
    )
    
    # Overall question type distribution
    question_type_distribution: Dict[str, int] = Field(
        ...,
        description="Total questions per question type"
    )
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_valid: bool = Field(default=True, description="Whether distribution is valid")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    
    @validator('subject_distribution')
    def validate_subject_totals(cls, v, values):
        """Validate that subject totals match total_questions."""
        if 'total_questions' in values:
            total = sum(v.values())
            if total != values['total_questions']:
                raise ValueError(
                    f"Subject distribution total ({total}) must equal "
                    f"total_questions ({values['total_questions']})"
                )
        return v


class QuestionDistributionService:
    """
    Service for creating complete question distribution plans.
    
    This service orchestrates the entire distribution process:
    1. Loads exam patterns
    2. Retrieves student preferences and syllabus
    3. Calculates topic distribution
    4. Applies difficulty and question type splits
    5. Validates and returns complete distribution plan
    
    Attributes:
        pattern_loader: PatternLoader instance
        calculator: WeightageCalculator instance
        firestore_client: Firestore client for data access
        cache: Distribution plan cache
    """
    
    def __init__(
        self,
        pattern_loader=None,
        calculator=None,
        firestore_client=None,
        enable_cache: bool = True
    ):
        """
        Initialize the QuestionDistributionService.
        
        Args:
            pattern_loader: Optional PatternLoader instance
            calculator: Optional WeightageCalculator instance
            firestore_client: Optional Firestore client
            enable_cache: Whether to enable distribution caching
        """
        # In production, these would be actual imports
        # For now, we'll handle them as optional dependencies
        self.pattern_loader = pattern_loader
        self.calculator = calculator
        self.firestore_client = firestore_client
        self.enable_cache = enable_cache
        self._cache: Dict[str, DistributionPlan] = {}
        
        logger.info(
            f"QuestionDistributionService initialized "
            f"(cache={'enabled' if enable_cache else 'disabled'})"
        )
    
    def create_distribution(
        self,
        exam_type: str,
        student_id: Optional[str] = None,
        use_cache: bool = True
    ) -> DistributionPlan:
        """
        Create a complete question distribution plan.
        
        Args:
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            student_id: Optional student ID for personalization
            use_cache: Whether to use cached distribution if available
            
        Returns:
            DistributionPlan with complete distribution details
            
        Raises:
            ValueError: If exam_type is invalid or syllabus not found
        """
        logger.info(
            f"Creating distribution plan: exam_type={exam_type}, "
            f"student_id={student_id}"
        )
        
        # Check cache
        cache_key = f"{exam_type}_{student_id or 'default'}"
        if use_cache and self.enable_cache and cache_key in self._cache:
            logger.info(f"Returning cached distribution for {cache_key}")
            return self._cache[cache_key]
        
        # Step 1: Load exam pattern
        pattern = self._load_exam_pattern(exam_type)
        logger.info(f"Loaded pattern: {pattern.exam_name}")
        
        # Step 2: Get student preferences (if student_id provided)
        student_prefs = self._get_student_preferences(student_id) if student_id else {}
        
        # Step 3: Load syllabus
        syllabus = self._load_syllabus(exam_type, student_prefs)
        logger.info(f"Loaded syllabus with {len(syllabus)} topics")
        
        # Step 4: Calculate subject distribution from pattern
        subject_distribution = self._calculate_subject_distribution(pattern)
        
        # Step 5: Calculate topic distribution using WeightageCalculator
        topic_distributions = self._calculate_topic_distribution(
            syllabus, pattern, subject_distribution
        )
        
        # Step 6: Apply difficulty distribution to each topic
        topic_distributions = self._apply_difficulty_split(
            topic_distributions, pattern
        )
        
        # Step 7: Apply question type distribution
        topic_distributions = self._apply_question_type_split(
            topic_distributions, pattern
        )
        
        # Step 8: Calculate overall distributions
        difficulty_dist = self._calculate_overall_difficulty(topic_distributions)
        question_type_dist = self._calculate_overall_question_types(topic_distributions)
        
        # Step 9: Create DistributionPlan
        plan = DistributionPlan(
            plan_id=f"plan_{exam_type.lower()}_{datetime.utcnow().timestamp()}",
            exam_type=exam_type,
            exam_name=pattern.exam_name,
            student_id=student_id,
            total_questions=pattern.total_questions,
            duration_minutes=pattern.duration_minutes,
            subject_distribution=subject_distribution,
            topic_distribution=topic_distributions,
            difficulty_distribution=difficulty_dist,
            question_type_distribution=question_type_dist
        )
        
        # Step 10: Validate
        warnings = self._validate_distribution(plan, pattern)
        plan.warnings = warnings
        plan.is_valid = len(warnings) == 0
        
        # Cache the plan
        if self.enable_cache:
            self._cache[cache_key] = plan
            logger.info(f"Cached distribution plan: {cache_key}")
        
        logger.info(
            f"Distribution plan created: {plan.total_questions} questions, "
            f"{len(plan.topic_distribution)} topics, valid={plan.is_valid}"
        )
        
        return plan
    
    def _load_exam_pattern(self, exam_type: str):
        """Load exam pattern using PatternLoader."""
        if not self.pattern_loader:
            raise RuntimeError("PatternLoader not initialized")
        
        try:
            return self.pattern_loader.load_pattern(exam_type)
        except Exception as e:
            logger.error(f"Failed to load pattern for {exam_type}: {e}")
            raise ValueError(f"Invalid exam type: {exam_type}")
    
    def _get_student_preferences(self, student_id: str) -> Dict:
        """
        Get student preferences from Firestore.
        
        Args:
            student_id: Student identifier
            
        Returns:
            Dictionary with student preferences
        """
        if not self.firestore_client:
            logger.warning("Firestore client not available, using defaults")
            return {}
        
        try:
            # In production: fetch from Firestore
            # doc = self.firestore_client.collection('students').document(student_id).get()
            # return doc.to_dict() if doc.exists else {}
            logger.info(f"Fetching preferences for student: {student_id}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching student preferences: {e}")
            return {}
    
    def _load_syllabus(
        self,
        exam_type: str,
        student_prefs: Dict
    ) -> List[Dict]:
        """
        Load syllabus from Firestore or default source.
        
        Args:
            exam_type: Exam type
            student_prefs: Student preferences
            
        Returns:
            List of topic dictionaries
        """
        # In production, this would fetch from Firestore
        # For now, return sample syllabus based on exam type
        
        if exam_type == "JEE_MAIN":
            return self._get_jee_main_syllabus()
        elif exam_type == "JEE_ADVANCED":
            return self._get_jee_advanced_syllabus()
        elif exam_type == "NEET":
            return self._get_neet_syllabus()
        else:
            raise ValueError(f"Unknown exam type: {exam_type}")
    
    def _get_jee_main_syllabus(self) -> List[Dict]:
        """Get JEE Main syllabus."""
        return [
            # Physics
            {"topic_id": "phy_mechanics", "topic_name": "Mechanics", 
             "subject": "Physics", "chapter": "Mechanics", "weightage": 25, "priority": 1},
            {"topic_id": "phy_thermodynamics", "topic_name": "Thermodynamics",
             "subject": "Physics", "chapter": "Thermodynamics", "weightage": 15, "priority": 1},
            {"topic_id": "phy_electromagnetism", "topic_name": "Electromagnetism",
             "subject": "Physics", "chapter": "Electromagnetism", "weightage": 20, "priority": 1},
            {"topic_id": "phy_optics", "topic_name": "Optics",
             "subject": "Physics", "chapter": "Optics", "weightage": 12, "priority": 2},
            {"topic_id": "phy_modern", "topic_name": "Modern Physics",
             "subject": "Physics", "chapter": "Modern Physics", "weightage": 18, "priority": 1},
            {"topic_id": "phy_waves", "topic_name": "Waves",
             "subject": "Physics", "chapter": "Waves", "weightage": 10, "priority": 2},
            
            # Chemistry
            {"topic_id": "chem_physical", "topic_name": "Physical Chemistry",
             "subject": "Chemistry", "chapter": "Physical Chemistry", "weightage": 30, "priority": 1},
            {"topic_id": "chem_organic", "topic_name": "Organic Chemistry",
             "subject": "Chemistry", "chapter": "Organic Chemistry", "weightage": 33, "priority": 1},
            {"topic_id": "chem_inorganic", "topic_name": "Inorganic Chemistry",
             "subject": "Chemistry", "chapter": "Inorganic Chemistry", "weightage": 20, "priority": 2},
            
            # Mathematics
            {"topic_id": "math_calculus", "topic_name": "Calculus",
             "subject": "Mathematics", "chapter": "Calculus", "weightage": 40, "priority": 1},
            {"topic_id": "math_algebra", "topic_name": "Algebra",
             "subject": "Mathematics", "chapter": "Algebra", "weightage": 25, "priority": 1},
            {"topic_id": "math_coordinate", "topic_name": "Coordinate Geometry",
             "subject": "Mathematics", "chapter": "Coordinate Geometry", "weightage": 18, "priority": 2},
            {"topic_id": "math_vectors", "topic_name": "Vectors",
             "subject": "Mathematics", "chapter": "Vectors", "weightage": 12, "priority": 2},
        ]
    
    def _get_jee_advanced_syllabus(self) -> List[Dict]:
        """Get JEE Advanced syllabus (similar to JEE Main but more advanced)."""
        return self._get_jee_main_syllabus()  # Simplified for example
    
    def _get_neet_syllabus(self) -> List[Dict]:
        """Get NEET syllabus."""
        return [
            # Physics (45 questions)
            {"topic_id": "phy_mechanics", "topic_name": "Mechanics",
             "subject": "Physics", "chapter": "Mechanics", "weightage": 12, "priority": 1},
            {"topic_id": "phy_electricity", "topic_name": "Electricity",
             "subject": "Physics", "chapter": "Electricity", "weightage": 10, "priority": 1},
            {"topic_id": "phy_optics", "topic_name": "Optics",
             "subject": "Physics", "chapter": "Optics", "weightage": 8, "priority": 2},
            {"topic_id": "phy_thermodynamics", "topic_name": "Thermodynamics",
             "subject": "Physics", "chapter": "Thermodynamics", "weightage": 8, "priority": 2},
            {"topic_id": "phy_modern", "topic_name": "Modern Physics",
             "subject": "Physics", "chapter": "Modern Physics", "weightage": 7, "priority": 2},
            
            # Chemistry (45 questions)
            {"topic_id": "chem_organic", "topic_name": "Organic Chemistry",
             "subject": "Chemistry", "chapter": "Organic Chemistry", "weightage": 15, "priority": 1},
            {"topic_id": "chem_inorganic", "topic_name": "Inorganic Chemistry",
             "subject": "Chemistry", "chapter": "Inorganic Chemistry", "weightage": 12, "priority": 1},
            {"topic_id": "chem_physical", "topic_name": "Physical Chemistry",
             "subject": "Chemistry", "chapter": "Physical Chemistry", "weightage": 18, "priority": 1},
            
            # Botany (45 questions)
            {"topic_id": "bio_botany_plant", "topic_name": "Plant Physiology",
             "subject": "Botany", "chapter": "Plant Physiology", "weightage": 15, "priority": 1},
            {"topic_id": "bio_botany_genetics", "topic_name": "Genetics",
             "subject": "Botany", "chapter": "Genetics", "weightage": 12, "priority": 1},
            {"topic_id": "bio_botany_ecology", "topic_name": "Ecology",
             "subject": "Botany", "chapter": "Ecology", "weightage": 10, "priority": 2},
            {"topic_id": "bio_botany_morphology", "topic_name": "Plant Morphology",
             "subject": "Botany", "chapter": "Plant Morphology", "weightage": 8, "priority": 2},
            
            # Zoology (45 questions)
            {"topic_id": "bio_zoology_human", "topic_name": "Human Physiology",
             "subject": "Zoology", "chapter": "Human Physiology", "weightage": 15, "priority": 1},
            {"topic_id": "bio_zoology_evolution", "topic_name": "Evolution",
             "subject": "Zoology", "chapter": "Evolution", "weightage": 10, "priority": 2},
            {"topic_id": "bio_zoology_reproduction", "topic_name": "Reproduction",
             "subject": "Zoology", "chapter": "Reproduction", "weightage": 12, "priority": 1},
            {"topic_id": "bio_zoology_diversity", "topic_name": "Animal Diversity",
             "subject": "Zoology", "chapter": "Animal Diversity", "weightage": 8, "priority": 2},
        ]
    
    def _calculate_subject_distribution(self, pattern) -> Dict[str, int]:
        """Calculate subject distribution from pattern."""
        return {
            subject.name: subject.question_count
            for subject in pattern.subjects
        }
    
    def _calculate_topic_distribution(
        self,
        syllabus: List[Dict],
        pattern,
        subject_distribution: Dict[str, int]
    ) -> List[TopicDistribution]:
        """
        Calculate topic-wise distribution using WeightageCalculator.
        
        Args:
            syllabus: List of topics
            pattern: Exam pattern
            subject_distribution: Questions per subject
            
        Returns:
            List of TopicDistribution objects
        """
        if not self.calculator:
            raise RuntimeError("WeightageCalculator not initialized")
        
        topic_distributions = []
        
        # Group syllabus by subject
        by_subject = {}
        for topic in syllabus:
            subject = topic["subject"]
            if subject not in by_subject:
                by_subject[subject] = []
            by_subject[subject].append(topic)
        
        # Calculate distribution for each subject
        for subject, topics in by_subject.items():
            if subject not in subject_distribution:
                logger.warning(f"Subject {subject} not in pattern, skipping")
                continue
            
            subject_questions = subject_distribution[subject]
            
            # Calculate distribution
            result = self.calculator.calculate_distribution(
                syllabus=topics,
                total_questions=subject_questions,
                exam_pattern=pattern,
                subject=subject
            )
            
            # Convert to TopicDistribution objects
            for topic_id, count in result.topic_distribution.items():
                meta = result.metadata[topic_id]
                
                # Find original topic data
                topic_data = next(t for t in topics if t["topic_id"] == topic_id)
                
                topic_dist = TopicDistribution(
                    topic_id=topic_id,
                    topic_name=topic_data.get("topic_name", meta["chapter"]),
                    subject=meta["subject"],
                    chapter=meta["chapter"],
                    question_count=count,
                    weightage=meta["weightage"],
                    priority=topic_data.get("priority", 1),
                    difficulty_split={},
                    question_type_split={}
                )
                topic_distributions.append(topic_dist)
        
        return topic_distributions
    
    def _apply_difficulty_split(
        self,
        topic_distributions: List[TopicDistribution],
        pattern
    ) -> List[TopicDistribution]:
        """
        Apply difficulty distribution to each topic.
        
        Args:
            topic_distributions: List of topic distributions
            pattern: Exam pattern with difficulty distribution
            
        Returns:
            Updated topic distributions with difficulty splits
        """
        difficulty_dist = pattern.difficulty_distribution
        
        for topic_dist in topic_distributions:
            total = topic_dist.question_count
            
            # Calculate questions per difficulty
            easy = int(total * difficulty_dist.easy / 100)
            medium = int(total * difficulty_dist.medium / 100)
            hard = total - easy - medium  # Remainder goes to hard
            
            topic_dist.difficulty_split = {
                DifficultyLevel.EASY.value: easy,
                DifficultyLevel.MEDIUM.value: medium,
                DifficultyLevel.HARD.value: hard
            }
        
        return topic_distributions
    
    def _apply_question_type_split(
        self,
        topic_distributions: List[TopicDistribution],
        pattern
    ) -> List[TopicDistribution]:
        """
        Apply question type distribution to each topic.
        
        Args:
            topic_distributions: List of topic distributions
            pattern: Exam pattern with question types
            
        Returns:
            Updated topic distributions with question type splits
        """
        # Calculate total marks per question type
        type_marks = {}
        for qt in pattern.question_types:
            type_marks[qt.type] = qt.marks
        
        # For simplicity, distribute proportionally by count_per_subject
        # In production, this would be more sophisticated
        for topic_dist in topic_distributions:
            total = topic_dist.question_count
            
            # Simple distribution based on pattern
            if len(pattern.question_types) == 1:
                # All questions of one type
                qt = pattern.question_types[0]
                topic_dist.question_type_split = {qt.type: total}
            else:
                # Distribute proportionally
                type_split = {}
                remaining = total
                
                for i, qt in enumerate(pattern.question_types[:-1]):
                    # Calculate proportion
                    total_per_subject = sum(q.count_per_subject for q in pattern.question_types)
                    proportion = qt.count_per_subject / total_per_subject
                    count = int(total * proportion)
                    type_split[qt.type] = count
                    remaining -= count
                
                # Last type gets remainder
                last_type = pattern.question_types[-1].type
                type_split[last_type] = remaining
                
                topic_dist.question_type_split = type_split
        
        return topic_distributions
    
    def _calculate_overall_difficulty(
        self,
        topic_distributions: List[TopicDistribution]
    ) -> Dict[str, int]:
        """Calculate overall difficulty distribution."""
        difficulty_totals = {
            DifficultyLevel.EASY.value: 0,
            DifficultyLevel.MEDIUM.value: 0,
            DifficultyLevel.HARD.value: 0
        }
        
        for topic_dist in topic_distributions:
            for difficulty, count in topic_dist.difficulty_split.items():
                difficulty_totals[difficulty] += count
        
        return difficulty_totals
    
    def _calculate_overall_question_types(
        self,
        topic_distributions: List[TopicDistribution]
    ) -> Dict[str, int]:
        """Calculate overall question type distribution."""
        type_totals = {}
        
        for topic_dist in topic_distributions:
            for qtype, count in topic_dist.question_type_split.items():
                type_totals[qtype] = type_totals.get(qtype, 0) + count
        
        return type_totals
    
    def _validate_distribution(
        self,
        plan: DistributionPlan,
        pattern
    ) -> List[str]:
        """
        Validate the distribution plan.
        
        Args:
            plan: Distribution plan to validate
            pattern: Exam pattern
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Validate total questions
        topic_total = sum(t.question_count for t in plan.topic_distribution)
        if topic_total != plan.total_questions:
            warnings.append(
                f"Topic distribution total ({topic_total}) != "
                f"total_questions ({plan.total_questions})"
            )
        
        # Validate difficulty distribution
        difficulty_total = sum(plan.difficulty_distribution.values())
        if difficulty_total != plan.total_questions:
            warnings.append(
                f"Difficulty distribution total ({difficulty_total}) != "
                f"total_questions ({plan.total_questions})"
            )
        
        # Validate question type distribution
        qtype_total = sum(plan.question_type_distribution.values())
        if qtype_total != plan.total_questions:
            warnings.append(
                f"Question type distribution total ({qtype_total}) != "
                f"total_questions ({plan.total_questions})"
            )
        
        # Validate subject distribution matches pattern
        for subject in pattern.subjects:
            expected = subject.question_count
            actual = plan.subject_distribution.get(subject.name, 0)
            if actual != expected:
                warnings.append(
                    f"Subject {subject.name}: got {actual}, expected {expected}"
                )
        
        if warnings:
            logger.warning(f"Distribution validation warnings: {len(warnings)}")
            for warning in warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("✓ Distribution validation passed")
        
        return warnings
    
    def clear_cache(self) -> None:
        """Clear the distribution plan cache."""
        self._cache.clear()
        logger.info("Distribution cache cleared")
    
    def get_cached_plans(self) -> List[str]:
        """Get list of cached plan keys."""
        return list(self._cache.keys())
