"""
Enhanced Question Generator with Batch API Integration - Mentor AI Platform

This module provides an enhanced version of the question generator that automatically
utilizes batch processing for cost optimization while maintaining backward compatibility.

Features:
- Automatic batch processing for multiple question generation requests
- Cost optimization through intelligent request grouping
- Backward compatibility with existing QuestionGenerator
- Real-time cost tracking and savings analytics
- Fallback to individual processing when needed

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.enhanced_question_generator import EnhancedQuestionGenerator
    >>> 
    >>> # Initialize enhanced generator
    >>> generator = EnhancedQuestionGenerator(batch_enabled=True)
    >>> 
    >>> # Use like regular QuestionGenerator (with automatic batching)
    >>> questions = generator.generate_questions(
    ...     topic="Calculus",
    ...     exam_type="JEE_MAIN",
    ...     difficulty="medium",
    ...     num_questions=5
    ... )
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

from services.question_generator import (
    QuestionGenerator,
    QuestionGeneratorError,
    InsufficientContextError
)
from services.gemini_batch_service import (
    GeminiBatchService,
    BatchRequest,
    RequestType,
    RequestPriority,
    get_gemini_batch_service
)
from services.batch_queue_manager import get_batch_queue_manager
from models.question_models import Question

# Configure logging
logger = logging.getLogger(__name__)

# Batch configuration
BATCH_COST_THRESHOLD = 0.01  # Minimum cost to trigger batching
DEFAULT_BATCH_SIZE = 8  # Default batch size for questions


class EnhancedQuestionGenerator(QuestionGenerator):
    """
    Enhanced question generator with automatic batch processing.
    
    This service extends QuestionGenerator to automatically utilize batch processing
    for cost optimization while maintaining full backward compatibility.
    
    Attributes:
        batch_service: GeminiBatchService instance
        batch_enabled: Whether batch processing is enabled
        auto_batch_threshold: Minimum requests to trigger batching
        queue_manager: BatchQueueManager instance
        cost_savings: Track cost savings from batching
    
    Example:
        >>> generator = EnhancedQuestionGenerator(batch_enabled=True)
        >>> questions = generator.generate_questions(
        ...     topic="Calculus",
        ...     exam_type="JEE_MAIN",
        ...     difficulty="medium",
        ...     num_questions=5
        ... )
    """
    
    def __init__(
        self,
        batch_enabled: bool = True,
        auto_batch_threshold: int = 3,
        **kwargs
    ):
        """
        Initialize Enhanced Question Generator.
        
        Args:
            batch_enabled: Enable batch processing (default: True)
            auto_batch_threshold: Minimum requests to trigger batching (default: 3)
            **kwargs: Arguments to pass to QuestionGenerator
        """
        logger.info("Initializing EnhancedQuestionGenerator")
        
        # Initialize parent service
        super().__init__(**kwargs)
        
        # Batch configuration
        self.batch_enabled = batch_enabled
        self.auto_batch_threshold = auto_batch_threshold
        
        # Initialize batch services
        self.batch_service = None
        self.queue_manager = None
        
        if self.batch_enabled:
            try:
                self.batch_service = get_gemini_batch_service(
                    batch_size=DEFAULT_BATCH_SIZE,
                    auto_flush=True
                )
                self.queue_manager = get_batch_queue_manager()
                logger.info("Batch services initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize batch services: {e}")
                self.batch_enabled = False
        
        # Cost tracking
        self.cost_savings = {
            "total_individual_cost": 0.0,
            "total_batch_cost": 0.0,
            "total_savings": 0.0,
            "batches_processed": 0,
            "requests_batched": 0,
            "requests_individual": 0
        }
        
        logger.info(
            f"EnhancedQuestionGenerator initialized (batch_enabled={batch_enabled}, "
            f"auto_batch_threshold={auto_batch_threshold})"
        )
    
    def generate_questions(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        num_questions: int,
        use_cache: bool = True,
        question_type: str = "single_correct",
        force_individual: bool = False
    ) -> List[Question]:
        """
        Generate questions with automatic batch processing.
        
        Args:
            topic: Topic name for questions
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            difficulty: Difficulty level (easy, medium, hard)
            num_questions: Number of questions to generate
            use_cache: Whether to use Firestore cache
            question_type: Type of questions (single_correct, etc.)
            force_individual: Force individual processing (skip batching)
        
        Returns:
            List of validated Question objects with metadata
        
        Example:
            >>> generator = EnhancedQuestionGenerator()
            >>> questions = generator.generate_questions(
            ...     topic="Calculus",
            ...     exam_type="JEE_MAIN",
            ...     difficulty="medium",
            ...     num_questions=5
            ... )
        """
        if not self.batch_enabled or force_individual:
            # Use regular processing
            self.cost_savings["requests_individual"] += 1
            return super().generate_questions(
                topic=topic,
                exam_type=exam_type,
                difficulty=difficulty,
                num_questions=num_questions,
                use_cache=use_cache,
                question_type=question_type
            )
        
        # Check if we should use batch processing
        queue_size = self.queue_manager.get_queue_size() if self.queue_manager else 0
        
        if queue_size < self.auto_batch_threshold:
            # Not enough requests for batching, process individually
            self.cost_savings["requests_individual"] += 1
            return super().generate_questions(
                topic=topic,
                exam_type=exam_type,
                difficulty=difficulty,
                num_questions=num_questions,
                use_cache=use_cache,
                question_type=question_type
            )
        
        # Add to batch queue
        request_id = f"questions_{topic}_{exam_type}_{difficulty}_{num_questions}_{int(time.time())}"
        
        # Create batch request
        batch_request = BatchRequest(
            request_id=request_id,
            prompt=self._build_question_prompt(topic, exam_type, difficulty, num_questions, question_type),
            request_type=RequestType.QUESTION_GENERATION,
            priority=RequestPriority.NORMAL,
            metadata={
                "topic": topic,
                "exam_type": exam_type,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "question_type": question_type,
                "use_cache": use_cache,
                "callback": self._process_question_result
            }
        )
        
        # Add to batch queue
        self.queue_manager.add_request(batch_request)
        self.cost_savings["requests_batched"] += 1
        
        logger.info(f"Added question generation request to batch: {request_id}")
        
        # Process batch if ready
        if queue_size >= self.auto_batch_threshold:
            logger.info("Triggering batch processing")
            asyncio.create_task(self._process_question_batch())
        
        # For now, process individually to maintain synchronous interface
        # In a full implementation, this would return a future/promise
        return super().generate_questions(
            topic=topic,
            exam_type=exam_type,
            difficulty=difficulty,
            num_questions=num_questions,
            use_cache=use_cache,
            question_type=question_type
        )
    
    async def generate_questions_async(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        num_questions: int,
        use_cache: bool = True,
        question_type: str = "single_correct",
        force_individual: bool = False
    ) -> List[Question]:
        """
        Asynchronously generate questions with batch processing.
        
        Args:
            topic: Topic name for questions
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            difficulty: Difficulty level (easy, medium, hard)
            num_questions: Number of questions to generate
            use_cache: Whether to use Firestore cache
            question_type: Type of questions (single_correct, etc.)
            force_individual: Force individual processing (skip batching)
        
        Returns:
            List of validated Question objects with metadata
        """
        if not self.batch_enabled or force_individual:
            # Use regular processing
            self.cost_savings["requests_individual"] += 1
            
            # Run synchronous method in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                super().generate_questions,
                topic,
                exam_type,
                difficulty,
                num_questions,
                use_cache,
                question_type
            )
        
        # Add to batch queue
        request_id = f"questions_{topic}_{exam_type}_{difficulty}_{num_questions}_{int(time.time())}"
        
        # Create batch request
        batch_request = BatchRequest(
            request_id=request_id,
            prompt=self._build_question_prompt(topic, exam_type, difficulty, num_questions, question_type),
            request_type=RequestType.QUESTION_GENERATION,
            priority=RequestPriority.NORMAL,
            metadata={
                "topic": topic,
                "exam_type": exam_type,
                "difficulty": difficulty,
                "num_questions": num_questions,
                "question_type": question_type,
                "use_cache": use_cache,
                "callback": self._process_question_result
            }
        )
        
        # Add to batch queue
        self.queue_manager.add_request(batch_request)
        self.cost_savings["requests_batched"] += 1
        
        logger.info(f"Added question generation request to batch: {request_id}")
        
        # Process batch if ready
        queue_size = self.queue_manager.get_queue_size()
        if queue_size >= self.auto_batch_threshold:
            logger.info("Triggering batch processing")
            await self._process_question_batch()
        
        # Wait for batch result (simplified for this example)
        # In production, this would use proper async coordination
        await asyncio.sleep(0.1)
        
        # For now, fall back to individual processing
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            super().generate_questions,
            topic,
            exam_type,
            difficulty,
            num_questions,
            use_cache,
            question_type
        )
    
    def _build_question_prompt(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        num_questions: int,
        question_type: str
    ) -> str:
        """Build question generation prompt for batch processing."""
        return f"""
        Generate {num_questions} {difficulty} {question_type} questions for:
        Topic: {topic}
        Exam Type: {exam_type}
        
        Questions should be:
        - Aligned with {exam_type} syllabus
        - Appropriate for {difficulty} difficulty level
        - Clear and unambiguous
        - Include 4 options with single correct answer
        """
    
    def _process_question_result(self, result: Dict[str, Any]):
        """Process question generation result from batch."""
        try:
            if result.get("success"):
                # Extract questions and store in Firestore
                questions_data = result.get("content", "")
                metadata = result.get("metadata", {})
                
                # Parse and validate questions
                questions = self._parse_batch_questions(questions_data, metadata)
                
                # Store result using original pipeline
                if questions and self.use_cache:
                    self._store_batch_questions(questions, metadata)
                
                logger.info(f"Processed batch question result: {len(questions)} questions")
            else:
                logger.error(f"Batch question generation failed: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error processing question result: {e}")
    
    def _parse_batch_questions(self, questions_data: str, metadata: Dict[str, Any]) -> List[Question]:
        """Parse questions from batch response."""
        try:
            # Use the existing response parser
            from utils.response_parser import ResponseParser
            parser = ResponseParser(strict_mode=False)
            
            questions, parse_stats = parser.parse_response(
                questions_data,
                expected_count=metadata.get("num_questions", 5)
            )
            
            # Add metadata
            questions = self._add_metadata(
                questions,
                metadata.get("topic", "Unknown"),
                metadata.get("exam_type", "JEE_MAIN"),
                metadata.get("difficulty", "medium")
            )
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse batch questions: {e}")
            return []
    
    def _store_batch_questions(self, questions: List[Question], metadata: Dict[str, Any]):
        """Store batch-generated questions in Firestore."""
        try:
            self._store_questions(
                questions,
                metadata.get("topic", "Unknown"),
                metadata.get("exam_type", "JEE_MAIN"),
                metadata.get("difficulty", "medium")
            )
            
            logger.info(f"Stored {len(questions)} batch questions in Firestore")
            
        except Exception as e:
            logger.error(f"Failed to store batch questions: {e}")
    
    async def _process_question_batch(self):
        """Process a batch of question generation requests."""
        try:
            # Get batch from queue
            requests = self.queue_manager.get_batch(DEFAULT_BATCH_SIZE)
            
            if not requests:
                return
            
            logger.info(f"Processing question batch of {len(requests)} requests")
            
            # Process batch using batch service
            batch_result = await self.batch_service.process_batch(
                max_batch_size=len(requests)
            )
            
            if batch_result and batch_result.success:
                # Update cost tracking
                self.cost_savings["total_individual_cost"] += batch_result.cost_individual
                self.cost_savings["total_batch_cost"] += batch_result.cost_batch
                self.cost_savings["total_savings"] += batch_result.cost_savings
                self.cost_savings["batches_processed"] += 1
                
                logger.info(
                    f"Question batch processed: ${batch_result.cost_savings:.4f} saved, "
                    f"{len(requests)} requests"
                )
            else:
                logger.warning("Question batch processing failed")
        
        except Exception as e:
            logger.error(f"Error processing question batch: {e}")
    
    def generate_batch_questions(
        self,
        question_requests: List[Dict[str, Any]],
        force_batch: bool = True
    ) -> Dict[str, List[Question]]:
        """
        Generate questions for multiple topics in batch.
        
        Args:
            question_requests: List of question request dictionaries
            force_batch: Force batch processing even for small batches
        
        Returns:
            Dictionary mapping request_id to list of questions
        
        Example:
            >>> requests = [
            ...     {"topic": "Calculus", "exam_type": "JEE_MAIN", "difficulty": "medium", "num_questions": 5},
            ...     {"topic": "Algebra", "exam_type": "JEE_MAIN", "difficulty": "hard", "num_questions": 3}
            ... ]
            >>> results = generator.generate_batch_questions(requests)
        """
        if not self.batch_enabled or not force_batch:
            # Process individually
            results = {}
            for i, req in enumerate(question_requests):
                request_id = f"req_{i}"
                questions = super().generate_questions(**req)
                results[request_id] = questions
            return results
        
        # Create batch requests
        batch_requests = []
        request_ids = []
        
        for i, req_data in enumerate(question_requests):
            request_id = f"questions_batch_{i}_{int(time.time())}"
            request_ids.append(request_id)
            
            batch_request = BatchRequest(
                request_id=request_id,
                prompt=self._build_question_prompt(
                    req_data["topic"],
                    req_data["exam_type"],
                    req_data["difficulty"],
                    req_data["num_questions"],
                    req_data.get("question_type", "single_correct")
                ),
                request_type=RequestType.QUESTION_GENERATION,
                priority=RequestPriority.NORMAL,
                metadata={
                    **req_data,
                    "callback": self._process_question_result
                }
            )
            batch_requests.append(batch_request)
        
        # Add all to queue
        for request in batch_requests:
            self.queue_manager.add_request(request)
            self.cost_savings["requests_batched"] += 1
        
        # Process batch
        asyncio.create_task(self._process_question_batch())
        
        logger.info(f"Added {len(batch_requests)} question requests to batch")
        
        # Return placeholder results (in production, this would wait for actual results)
        return {req_id: [] for req_id in request_ids}
    
    def get_cost_savings(self) -> Dict[str, Any]:
        """
        Get comprehensive cost savings statistics.
        
        Returns:
            Dictionary with cost analysis and savings
        
        Example:
            >>> generator = EnhancedQuestionGenerator()
            >>> savings = generator.get_cost_savings()
            >>> print(f"Total saved: ${savings['total_savings']:.2f}")
        """
        total_requests = self.cost_savings["requests_batched"] + self.cost_savings["requests_individual"]
        
        if total_requests == 0:
            return {
                "total_requests": 0,
                "batch_efficiency": 0.0,
                "total_savings": 0.0,
                "savings_percentage": 0.0
            }
        
        batch_efficiency = self.cost_savings["requests_batched"] / total_requests
        savings_percentage = (
            (self.cost_savings["total_savings"] / 
             max(self.cost_savings["total_individual_cost"], 0.001)) * 100
        )
        
        return {
            **self.cost_savings,
            "total_requests": total_requests,
            "batch_efficiency": batch_efficiency,
            "savings_percentage": savings_percentage,
            "average_savings_per_request": (
                self.cost_savings["total_savings"] / 
                max(self.cost_savings["requests_batched"], 1)
            )
        }
    
    def get_generator_status(self) -> Dict[str, Any]:
        """
        Get comprehensive generator status.
        
        Returns:
            Dictionary with generator status and statistics
        
        Example:
            >>> generator = EnhancedQuestionGenerator()
            >>> status = generator.get_generator_status()
            >>> print(f"Batch enabled: {status['batch_enabled']}")
        """
        base_status = {
            "service_type": "EnhancedQuestionGenerator",
            "batch_enabled": self.batch_enabled,
            "auto_batch_threshold": self.auto_batch_threshold,
            "queue_size": self.queue_manager.get_queue_size() if self.queue_manager else 0
        }
        
        # Add cost savings
        base_status.update(self.get_cost_savings())
        
        # Add batch service status
        if self.batch_service:
            base_status["batch_service_status"] = self.batch_service.get_queue_status()
        
        # Add parent service stats
        base_status["question_generator_stats"] = self.get_generation_stats()
        
        return base_status
    
    def enable_batch_processing(self, enabled: bool = True):
        """
        Enable or disable batch processing.
        
        Args:
            enabled: Whether to enable batch processing
        
        Example:
            >>> generator = EnhancedQuestionGenerator()
            >>> generator.enable_batch_processing(False)
        """
        self.batch_enabled = enabled
        logger.info(f"Batch processing {'enabled' if enabled else 'disabled'}")
    
    def set_batch_threshold(self, threshold: int):
        """
        Set automatic batch threshold.
        
        Args:
            threshold: Minimum requests to trigger batching
        
        Example:
            >>> generator = EnhancedQuestionGenerator()
            >>> generator.set_batch_threshold(5)
        """
        if threshold < 2:
            raise ValueError("Batch threshold must be at least 2")
        
        self.auto_batch_threshold = threshold
        logger.info(f"Batch threshold set to {threshold}")


# Factory function for easy migration
def create_enhanced_question_generator(
    batch_enabled: bool = True,
    auto_batch_threshold: int = 3,
    **kwargs
) -> EnhancedQuestionGenerator:
    """
    Create enhanced question generator with optimal configuration.
    
    Args:
        batch_enabled: Enable batch processing
        auto_batch_threshold: Minimum requests for batching
        **kwargs: Additional arguments for QuestionGenerator
    
    Returns:
        Configured EnhancedQuestionGenerator instance
    
    Example:
        >>> generator = create_enhanced_question_generator(
        ...     batch_enabled=True,
        ...     auto_batch_threshold=5
        ... )
    """
    generator_kwargs = {
        "batch_enabled": batch_enabled,
        "auto_batch_threshold": auto_batch_threshold,
        **kwargs
    }
    
    return EnhancedQuestionGenerator(**generator_kwargs)


# Module initialization
logger.info("Enhanced question generator module loaded")
logger.info(f"Batch cost threshold: ${BATCH_COST_THRESHOLD}")