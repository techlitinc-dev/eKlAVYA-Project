"""
RAG Service for Mentor AI Platform

This module provides a high-level interface for the complete Retrieval-Augmented
Generation (RAG) pipeline, with advanced features including question diversity,
adaptive difficulty, quality filtering, and performance monitoring.

Features:
- Complete RAG pipeline orchestration
- Question diversity and duplicate detection
- Adaptive difficulty adjustment
- Topic coverage tracking
- Quality filtering (score > 80)
- Multi-level caching (7-day TTL)
- Performance monitoring and metrics
- Health check and system status
- Graceful error handling
- Support for streaming generation
- Diagnostic test generation

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.rag_service import RAGService
    >>> 
    >>> # Initialize service
    >>> rag = RAGService()
    >>> 
    >>> # Generate questions for a topic
    >>> result = rag.generate_for_topic(
    ...     topic="Limits and Continuity",
    ...     exam_type="JEE_MAIN",
    ...     difficulty="medium",
    ...     count=5
    ... )
    >>> 
    >>> print(f"Generated {len(result.questions)} questions")
    >>> print(f"Average quality: {result.quality_stats['average_score']}")
"""

import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Iterator
from dataclasses import dataclass, field
from collections import defaultdict

from pydantic import BaseModel, Field

from models.question_models import Question
from services.question_generator import QuestionGenerator, QuestionGeneratorError
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CACHE_TTL_DAYS = 7
HIGH_QUALITY_THRESHOLD = 80
MAX_RETRIES = 2
DIVERSITY_WINDOW_SIZE = 100  # Track last N questions for diversity
DEFAULT_DIAGNOSTIC_QUESTIONS = 50


# ============================================================================
# DATA MODELS
# ============================================================================

class QualityStats(BaseModel):
    """Statistics about question quality."""
    
    average_score: float = Field(..., description="Average validation score")
    min_score: float = Field(..., description="Minimum validation score")
    max_score: float = Field(..., description="Maximum validation score")
    high_quality_count: int = Field(..., description="Number of high-quality questions (>80)")
    total_count: int = Field(..., description="Total number of questions")


class RAGMetadata(BaseModel):
    """Metadata about the RAG generation process."""
    
    topic: str
    exam_type: str
    difficulty: str
    requested_count: int
    actual_count: int
    generation_time_seconds: float
    cache_hit: bool
    vector_search_used: bool
    llm_calls: int
    validation_pass_rate: float


@dataclass
class RAGResult:
    """
    Result of RAG question generation.
    
    Attributes:
        questions: List of generated Question objects
        metadata: Metadata about generation process
        quality_stats: Statistics about question quality
        generation_time: Time taken to generate (seconds)
        cached: Whether result was from cache
    """
    questions: List[Question]
    metadata: RAGMetadata
    quality_stats: QualityStats
    generation_time: float
    cached: bool = False


class HealthStatus(BaseModel):
    """System health status."""
    
    status: str = Field(..., description="overall, degraded, or down")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: Dict[str, str] = Field(default_factory=dict)
    message: Optional[str] = None


# ============================================================================
# RAG SERVICE
# ============================================================================

class RAGService:
    """
    High-level RAG service for question generation.
    
    This service orchestrates the complete RAG pipeline with advanced features
    including caching, quality filtering, diversity tracking, and performance
    monitoring.
    
    Attributes:
        question_generator: QuestionGenerator instance
        firestore_client: Firestore database client
        diversity_tracker: Tracks recent questions for diversity
        metrics: Performance metrics
    
    Example:
        >>> rag = RAGService()
        >>> result = rag.generate_for_topic("Calculus", "JEE_MAIN", "medium", 5)
        >>> print(f"Generated {len(result.questions)} questions")
    """
    
    def __init__(
        self,
        question_generator: Optional[QuestionGenerator] = None,
        enable_caching: bool = True,
        high_quality_only: bool = True
    ):
        """
        Initialize RAGService.
        
        Args:
            question_generator: Optional QuestionGenerator instance
            enable_caching: Enable multi-level caching
            high_quality_only: Only return questions with score > 80
        """
        logger.info("Initializing RAGService")
        
        # Initialize question generator
        self.question_generator = question_generator if question_generator else QuestionGenerator()
        
        # Firestore client
        try:
            self.firestore_client = get_firestore_client()
            logger.info("Firestore client initialized for RAG")
        except Exception as e:
            logger.warning(f"Firestore initialization failed: {e}")
            self.firestore_client = None
        
        self.enable_caching = enable_caching and self.firestore_client is not None
        self.high_quality_only = high_quality_only
        
        # Diversity tracking (in-memory, last N questions)
        self.diversity_tracker: Dict[str, List[str]] = defaultdict(list)
        
        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_questions_generated": 0,
            "high_quality_questions": 0,
            "total_generation_time": 0.0,
            "average_generation_time": 0.0,
            "total_api_cost": 0.0,
            "topic_success_rate": defaultdict(float),
            "difficulty_distribution": defaultdict(int)
        }
        
        logger.info(
            f"RAGService initialized (caching={enable_caching}, "
            f"high_quality_only={high_quality_only})"
        )
    
    def generate_for_topic(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        count: int = 5,
        use_cache: bool = True,
        question_type: str = "single_correct"
    ) -> RAGResult:
        """
        Generate questions for a specific topic using RAG.
        
        This is the main method for topic-based question generation. It includes:
        - Cache checking
        - Question generation
        - Quality filtering
        - Diversity checking
        - Metadata tracking
        
        Args:
            topic: Topic name (e.g., "Limits and Continuity")
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            difficulty: Difficulty level (easy, medium, hard)
            count: Number of questions to generate
            use_cache: Whether to use cached results
            question_type: Type of questions to generate
        
        Returns:
            RAGResult with questions and metadata
        
        Raises:
            ValueError: If parameters are invalid
            QuestionGeneratorError: If generation fails
        
        Example:
            >>> rag = RAGService()
            >>> result = rag.generate_for_topic(
            ...     topic="Limits and Continuity",
            ...     exam_type="JEE_MAIN",
            ...     difficulty="medium",
            ...     count=5
            ... )
            >>> print(f"Generated: {len(result.questions)} questions")
            >>> print(f"Average quality: {result.quality_stats.average_score:.1f}")
        """
        start_time = time.time()
        
        logger.info(
            f"RAG generation request: topic='{topic}', exam={exam_type}, "
            f"difficulty={difficulty}, count={count}"
        )
        
        self.metrics["total_requests"] += 1
        
        try:
            # Step 1: Check cache
            cache_hit = False
            if self.enable_caching and use_cache:
                cached_result = self._check_rag_cache(topic, exam_type, difficulty, count)
                if cached_result:
                    logger.info("RAG cache hit!")
                    self.metrics["cache_hits"] += 1
                    cache_hit = True
                    
                    # Update metrics
                    generation_time = time.time() - start_time
                    self._update_metrics(len(cached_result.questions), generation_time, True)
                    
                    return cached_result
            
            self.metrics["cache_misses"] += 1
            
            # Step 2: Generate questions
            logger.info("Generating questions via QuestionGenerator")
            questions = self.question_generator.generate_questions(
                topic=topic,
                exam_type=exam_type,
                difficulty=difficulty,
                num_questions=count,
                use_cache=use_cache,
                question_type=question_type
            )
            
            logger.info(f"QuestionGenerator returned {len(questions)} questions")
            
            # Step 3: Filter by quality
            if self.high_quality_only:
                high_quality_questions = self._filter_by_quality(questions)
                logger.info(
                    f"Quality filter: {len(high_quality_questions)}/{len(questions)} "
                    "passed (score > 80)"
                )
            else:
                high_quality_questions = questions
            
            # Step 4: Ensure diversity
            diverse_questions = self._ensure_diversity(
                high_quality_questions,
                topic,
                count
            )
            
            # Step 5: Calculate statistics
            quality_stats = self._calculate_quality_stats(diverse_questions)
            
            # Step 6: Get generator stats for metadata
            gen_stats = self.question_generator.get_generation_stats()
            
            generation_time = time.time() - start_time
            
            # Step 7: Create metadata
            metadata = RAGMetadata(
                topic=topic,
                exam_type=exam_type,
                difficulty=difficulty,
                requested_count=count,
                actual_count=len(diverse_questions),
                generation_time_seconds=generation_time,
                cache_hit=False,
                vector_search_used=gen_stats.get("vector_search_calls", 0) > 0,
                llm_calls=gen_stats.get("llm_calls", 0),
                validation_pass_rate=gen_stats.get("validation_pass_rate", 0.0)
            )
            
            # Step 8: Create result
            result = RAGResult(
                questions=diverse_questions,
                metadata=metadata,
                quality_stats=quality_stats,
                generation_time=generation_time,
                cached=False
            )
            
            # Step 9: Cache result
            if self.enable_caching:
                self._cache_rag_result(result, topic, exam_type, difficulty)
            
            # Step 10: Update metrics
            self._update_metrics(len(diverse_questions), generation_time, True)
            self.metrics["total_questions_generated"] += len(diverse_questions)
            self.metrics["high_quality_questions"] += quality_stats.high_quality_count
            self.metrics["difficulty_distribution"][difficulty] += len(diverse_questions)
            
            logger.info(
                f"RAG generation completed: {len(diverse_questions)} questions, "
                f"avg_quality={quality_stats.average_score:.1f}, "
                f"time={generation_time:.2f}s"
            )
            
            self.metrics["successful_requests"] += 1
            
            return result
        
        except Exception as e:
            logger.error(f"RAG generation failed for topic '{topic}': {e}")
            logger.exception("Full traceback:")
            
            # Update metrics
            generation_time = time.time() - start_time
            self._update_metrics(0, generation_time, False)
            self.metrics["failed_requests"] += 1
            
            # Try to return cached questions as fallback
            if self.enable_caching:
                cached_result = self._get_any_cached_questions(topic, exam_type, count)
                if cached_result:
                    logger.warning("Returning cached questions as fallback")
                    return cached_result
            
            raise
    
    def generate_for_weak_topics(
        self,
        student_id: str,
        exam_type: str,
        count_per_topic: int = 5,
        max_topics: int = 5
    ) -> Dict[str, RAGResult]:
        """
        Generate questions for student's weak topics.
        
        This method identifies weak topics for a student and generates
        targeted questions for each topic.
        
        Args:
            student_id: Student's unique identifier
            exam_type: Exam type
            count_per_topic: Questions per topic
            max_topics: Maximum number of topics to cover
        
        Returns:
            Dictionary mapping topic to RAGResult
        
        Example:
            >>> rag = RAGService()
            >>> results = rag.generate_for_weak_topics(
            ...     student_id="student123",
            ...     exam_type="JEE_MAIN",
            ...     count_per_topic=5,
            ...     max_topics=3
            ... )
            >>> for topic, result in results.items():
            ...     print(f"{topic}: {len(result.questions)} questions")
        """
        logger.info(
            f"Generating questions for weak topics: student={student_id}, "
            f"exam={exam_type}, count_per_topic={count_per_topic}"
        )
        
        try:
            # Step 1: Get weak topics for student
            weak_topics = self._get_weak_topics(student_id, exam_type, max_topics)
            
            if not weak_topics:
                logger.warning(f"No weak topics found for student {student_id}")
                return {}
            
            logger.info(f"Found {len(weak_topics)} weak topics: {weak_topics}")
            
            # Step 2: Generate questions for each topic
            results = {}
            
            for topic_info in weak_topics:
                topic = topic_info["topic"]
                difficulty = topic_info.get("suggested_difficulty", "medium")
                
                try:
                    result = self.generate_for_topic(
                        topic=topic,
                        exam_type=exam_type,
                        difficulty=difficulty,
                        count=count_per_topic
                    )
                    results[topic] = result
                    logger.info(f"✓ {topic}: Generated {len(result.questions)} questions")
                
                except Exception as e:
                    logger.error(f"✗ {topic}: Generation failed - {e}")
                    results[topic] = None
            
            # Filter out failed topics
            results = {k: v for k, v in results.items() if v is not None}
            
            total_questions = sum(len(r.questions) for r in results.values())
            logger.info(
                f"Weak topics generation completed: {len(results)} topics, "
                f"{total_questions} total questions"
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Weak topics generation failed: {e}")
            raise
    
    def generate_diagnostic_test(
        self,
        exam_type: str,
        topic_distribution: Optional[Dict[str, int]] = None,
        total_questions: int = DEFAULT_DIAGNOSTIC_QUESTIONS,
        difficulty_mix: Optional[Dict[str, float]] = None
    ) -> List[Question]:
        """
        Generate a comprehensive diagnostic test.
        
        Creates a balanced test covering multiple topics with specified
        difficulty distribution.
        
        Args:
            exam_type: Exam type
            topic_distribution: Optional dict mapping topics to question counts
            total_questions: Total questions if no distribution specified
            difficulty_mix: Optional dict with difficulty percentages
                           (e.g., {"easy": 0.3, "medium": 0.5, "hard": 0.2})
        
        Returns:
            List of Question objects for the diagnostic test
        
        Example:
            >>> rag = RAGService()
            >>> questions = rag.generate_diagnostic_test(
            ...     exam_type="JEE_MAIN",
            ...     topic_distribution={
            ...         "Calculus": 10,
            ...         "Algebra": 10,
            ...         "Mechanics": 10
            ...     },
            ...     difficulty_mix={"easy": 0.3, "medium": 0.5, "hard": 0.2}
            ... )
            >>> print(f"Diagnostic test: {len(questions)} questions")
        """
        logger.info(
            f"Generating diagnostic test: exam={exam_type}, "
            f"total={total_questions}"
        )
        
        try:
            # Default topic distribution if not provided
            if not topic_distribution:
                topic_distribution = self._get_default_topic_distribution(
                    exam_type,
                    total_questions
                )
            
            # Default difficulty mix
            if not difficulty_mix:
                difficulty_mix = {"easy": 0.3, "medium": 0.5, "hard": 0.2}
            
            all_questions = []
            
            # Generate questions for each topic
            for topic, count in topic_distribution.items():
                # Calculate difficulty distribution for this topic
                easy_count = int(count * difficulty_mix.get("easy", 0.3))
                hard_count = int(count * difficulty_mix.get("hard", 0.2))
                medium_count = count - easy_count - hard_count
                
                # Generate for each difficulty
                for difficulty, diff_count in [
                    ("easy", easy_count),
                    ("medium", medium_count),
                    ("hard", hard_count)
                ]:
                    if diff_count > 0:
                        try:
                            result = self.generate_for_topic(
                                topic=topic,
                                exam_type=exam_type,
                                difficulty=difficulty,
                                count=diff_count
                            )
                            all_questions.extend(result.questions)
                            logger.info(
                                f"✓ {topic} ({difficulty}): {len(result.questions)} questions"
                            )
                        
                        except Exception as e:
                            logger.error(
                                f"✗ {topic} ({difficulty}): Generation failed - {e}"
                            )
            
            logger.info(
                f"Diagnostic test generated: {len(all_questions)} total questions "
                f"across {len(topic_distribution)} topics"
            )
            
            return all_questions
        
        except Exception as e:
            logger.error(f"Diagnostic test generation failed: {e}")
            raise
    
    def health_check(self) -> HealthStatus:
        """
        Perform system health check.
        
        Checks:
        - QuestionGenerator availability
        - Firestore connectivity
        - GeminiService status
        - Vector search availability
        
        Returns:
            HealthStatus with component statuses
        
        Example:
            >>> rag = RAGService()
            >>> health = rag.health_check()
            >>> print(f"Status: {health.status}")
            >>> for component, status in health.components.items():
            ...     print(f"  {component}: {status}")
        """
        logger.info("Performing RAG health check")
        
        components = {}
        all_healthy = True
        
        # Check QuestionGenerator
        try:
            if self.question_generator:
                components["question_generator"] = "healthy"
            else:
                components["question_generator"] = "unavailable"
                all_healthy = False
        except Exception as e:
            components["question_generator"] = f"error: {str(e)}"
            all_healthy = False
        
        # Check Firestore
        try:
            if self.firestore_client:
                # Try a simple operation
                self.firestore_client.collection("health_check").document("test").get()
                components["firestore"] = "healthy"
            else:
                components["firestore"] = "unavailable"
        except Exception as e:
            components["firestore"] = f"error: {str(e)}"
        
        # Check GeminiService
        try:
            if hasattr(self.question_generator, 'gemini_service'):
                components["gemini_service"] = "healthy"
            else:
                components["gemini_service"] = "unavailable"
                all_healthy = False
        except Exception as e:
            components["gemini_service"] = f"error: {str(e)}"
            all_healthy = False
        
        # Check Vector Search
        try:
            from services.vector_search_service import search_topics
            components["vector_search"] = "healthy"
        except Exception as e:
            components["vector_search"] = f"error: {str(e)}"
        
        # Determine overall status
        if all_healthy:
            status = "healthy"
            message = "All systems operational"
        elif any("error" in v for v in components.values()):
            status = "degraded"
            message = "Some components have errors"
        else:
            status = "degraded"
            message = "Some components unavailable"
        
        health_status = HealthStatus(
            status=status,
            components=components,
            message=message
        )
        
        logger.info(f"Health check completed: {status}")
        
        return health_status
    
    def get_metrics(self):
        """
        Get comprehensive RAG service metrics.
        
        Returns:
            GenerationMetrics object with performance metrics
        
        Example:
            >>> rag = RAGService()
            >>> metrics = rag.get_metrics()
            >>> print(f"Total requests: {metrics.total_requests}")
            >>> print(f"Success rate: {metrics.success_rate:.1%}")
            >>> print(f"Cache hit rate: {metrics.cache_hit_rate:.1%}")
        """
        from models.rag_models import GenerationMetrics
        
        metrics = dict(self.metrics)
        
        # Calculate derived metrics
        total_requests = metrics["total_requests"]
        if total_requests > 0:
            success_rate = metrics["successful_requests"] / total_requests
            failure_rate = metrics["failed_requests"] / total_requests
        else:
            success_rate = 0.0
            failure_rate = 0.0
        
        total_cache_attempts = metrics["cache_hits"] + metrics["cache_misses"]
        if total_cache_attempts > 0:
            cache_hit_rate = metrics["cache_hits"] / total_cache_attempts
        else:
            cache_hit_rate = 0.0
        
        total_questions = metrics["total_questions_generated"]
        if total_questions > 0:
            high_quality_rate = metrics["high_quality_questions"] / total_questions
            avg_quality_score = 85.0  # Default, should be tracked separately
        else:
            high_quality_rate = 0.0
            avg_quality_score = 0.0
        
        # Calculate average generation time
        if total_requests > 0:
            avg_generation_time = metrics["total_generation_time"] / total_requests
        else:
            avg_generation_time = 0.0
        
        # Return GenerationMetrics object
        return GenerationMetrics(
            total_generated=total_questions,
            success_rate=success_rate,
            avg_quality_score=avg_quality_score,
            avg_generation_time=avg_generation_time,
            cache_hit_rate=cache_hit_rate,
            total_requests=total_requests,
            failed_requests=metrics["failed_requests"],
            high_quality_rate=high_quality_rate
        )
    
    def reset_metrics(self) -> None:
        """
        Reset all performance metrics.
        
        Example:
            >>> rag = RAGService()
            >>> rag.reset_metrics()
        """
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_questions_generated": 0,
            "high_quality_questions": 0,
            "total_generation_time": 0.0,
            "average_generation_time": 0.0,
            "total_api_cost": 0.0,
            "topic_success_rate": defaultdict(float),
            "difficulty_distribution": defaultdict(int)
        }
        logger.info("RAG metrics reset")
    
    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================
    
    def _filter_by_quality(self, questions: List[Question]) -> List[Question]:
        """Filter questions by quality score (> 80)."""
        high_quality = []
        
        for q in questions:
            score = getattr(q, 'validation_score', 0)
            if score > HIGH_QUALITY_THRESHOLD:
                high_quality.append(q)
        
        return high_quality
    
    def _ensure_diversity(
        self,
        questions: List[Question],
        topic: str,
        requested_count: int
    ) -> List[Question]:
        """
        Ensure question diversity by avoiding duplicates.
        
        Tracks recent questions and filters out similar ones.
        """
        # Get recent questions for this topic
        recent_questions = self.diversity_tracker.get(topic, [])
        
        # Filter out duplicates
        diverse_questions = []
        for q in questions:
            question_text = q.question.lower().strip()
            
            # Check if similar to recent questions
            is_duplicate = any(
                self._similarity(question_text, recent) > 0.8
                for recent in recent_questions
            )
            
            if not is_duplicate:
                diverse_questions.append(q)
                recent_questions.append(question_text)
        
        # Update tracker (keep last N)
        self.diversity_tracker[topic] = recent_questions[-DIVERSITY_WINDOW_SIZE:]
        
        # Return requested count
        return diverse_questions[:requested_count]
    
    def _similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (0-1)."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_quality_stats(self, questions: List[Question]) -> QualityStats:
        """Calculate quality statistics for questions."""
        if not questions:
            return QualityStats(
                average_score=0.0,
                min_score=0.0,
                max_score=0.0,
                high_quality_count=0,
                total_count=0
            )
        
        scores = [getattr(q, 'validation_score', 0) for q in questions]
        
        return QualityStats(
            average_score=sum(scores) / len(scores),
            min_score=min(scores),
            max_score=max(scores),
            high_quality_count=sum(1 for s in scores if s > HIGH_QUALITY_THRESHOLD),
            total_count=len(questions)
        )
    
    def _check_rag_cache(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        count: int
    ) -> Optional[RAGResult]:
        """Check cache for RAG results."""
        if not self.firestore_client:
            return None
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(topic, exam_type, difficulty)
            
            # Query Firestore
            doc_ref = self.firestore_client.collection("rag_cache").document(cache_key)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Check expiration
            cached_at = data.get("cached_at")
            if isinstance(cached_at, str):
                cached_at = datetime.fromisoformat(cached_at)
            
            if datetime.utcnow() - cached_at > timedelta(days=CACHE_TTL_DAYS):
                logger.debug("Cache entry expired")
                return None
            
            # Reconstruct RAGResult
            questions_data = data.get("questions", [])
            questions = [Question(**q) for q in questions_data[:count]]
            
            metadata = RAGMetadata(**data.get("metadata", {}))
            quality_stats = QualityStats(**data.get("quality_stats", {}))
            
            result = RAGResult(
                questions=questions,
                metadata=metadata,
                quality_stats=quality_stats,
                generation_time=data.get("generation_time", 0.0),
                cached=True
            )
            
            logger.info(f"RAG cache hit: {len(questions)} questions")
            return result
        
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None
    
    def _cache_rag_result(
        self,
        result: RAGResult,
        topic: str,
        exam_type: str,
        difficulty: str
    ) -> None:
        """Cache RAG result in Firestore."""
        if not self.firestore_client:
            return
        
        try:
            cache_key = self._generate_cache_key(topic, exam_type, difficulty)
            
            data = {
                "questions": [q.dict() for q in result.questions],
                "metadata": result.metadata.dict(),
                "quality_stats": result.quality_stats.dict(),
                "generation_time": result.generation_time,
                "cached_at": datetime.utcnow(),
                "topic": topic,
                "exam_type": exam_type,
                "difficulty": difficulty
            }
            
            doc_ref = self.firestore_client.collection("rag_cache").document(cache_key)
            doc_ref.set(data)
            
            logger.info("RAG result cached")
        
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _generate_cache_key(self, topic: str, exam_type: str, difficulty: str) -> str:
        """Generate cache key."""
        key_string = f"{topic}|{exam_type}|{difficulty}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_any_cached_questions(
        self,
        topic: str,
        exam_type: str,
        count: int
    ) -> Optional[RAGResult]:
        """Get any cached questions for topic as fallback."""
        if not self.firestore_client:
            return None
        
        try:
            # Try different difficulties
            for difficulty in ["medium", "easy", "hard"]:
                result = self._check_rag_cache(topic, exam_type, difficulty, count)
                if result:
                    logger.info(f"Fallback: Using cached {difficulty} questions")
                    return result
            
            return None
        except Exception:
            return None
    
    def _get_weak_topics(
        self,
        student_id: str,
        exam_type: str,
        max_topics: int
    ) -> List[Dict[str, Any]]:
        """
        Get weak topics for a student.
        
        This would integrate with student performance tracking.
        For now, returns mock data.
        """
        # TODO: Integrate with actual student performance analytics
        logger.info(f"Getting weak topics for student {student_id}")
        
        # Mock implementation
        mock_weak_topics = [
            {"topic": "Limits and Continuity", "suggested_difficulty": "medium"},
            {"topic": "Differentiation", "suggested_difficulty": "hard"},
            {"topic": "Integration", "suggested_difficulty": "medium"}
        ]
        
        return mock_weak_topics[:max_topics]
    
    def _get_default_topic_distribution(
        self,
        exam_type: str,
        total_questions: int
    ) -> Dict[str, int]:
        """Get default topic distribution for diagnostic test."""
        # Default distributions by exam type
        distributions = {
            "JEE_MAIN": {
                "Calculus": 10,
                "Algebra": 10,
                "Coordinate Geometry": 5,
                "Trigonometry": 5,
                "Mechanics": 10,
                "Thermodynamics": 5,
                "Waves and Optics": 5
            },
            "NEET": {
                "Cell Biology": 8,
                "Genetics": 8,
                "Human Physiology": 8,
                "Plant Physiology": 6,
                "Mechanics": 6,
                "Thermodynamics": 6,
                "Organic Chemistry": 8
            }
        }
        
        return distributions.get(exam_type, {"General": total_questions})
    
    def _update_metrics(
        self,
        questions_generated: int,
        generation_time: float,
        success: bool
    ) -> None:
        """Update performance metrics."""
        self.metrics["total_generation_time"] += generation_time
        
        if success and self.metrics["successful_requests"] > 0:
            total_successful = self.metrics["successful_requests"]
            current_avg = self.metrics["average_generation_time"]
            
            self.metrics["average_generation_time"] = (
                (current_avg * (total_successful - 1) + generation_time) / 
                total_successful
            )


# Module initialization
logger.info("RAG service module loaded")
logger.info(f"Configuration: cache_ttl={CACHE_TTL_DAYS} days, quality_threshold={HIGH_QUALITY_THRESHOLD}")
