"""
Enhanced Gemini Service with Batch API Integration - Mentor AI Platform

This module provides an enhanced version of the Gemini service that automatically
utilizes batch processing for cost optimization while maintaining backward compatibility.

Features:
- Automatic batch processing for cost optimization
- Fallback to individual API calls when needed
- Transparent integration with existing code
- Intelligent request routing based on cost/benefit analysis
- Real-time cost tracking and savings
- Priority-based request handling
- Comprehensive error handling and retries

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.enhanced_gemini_service import EnhancedGeminiService
    >>> 
    >>> # Initialize enhanced service
    >>> service = EnhancedGeminiService()
    >>> 
    >>> # Use like regular GeminiService (with automatic batching)
    >>> questions = service.generate_questions(prompt, num_questions=5)
    >>> 
    >>> # Get cost savings
    >>> savings = service.get_cost_savings()
    >>> print(f"Saved ${savings['total_savings']:.4f}")
"""

import time
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from functools import wraps

from models.question_models import Question
from services.gemini_service import GeminiService
from services.gemini_batch_service import (
    GeminiBatchService, 
    BatchRequest, 
    RequestType, 
    RequestPriority,
    get_gemini_batch_service
)
from services.batch_queue_manager import get_batch_queue_manager
from services.batch_monitor_service import get_batch_monitor_service
from config.batch_config import get_batch_settings

# Configure logging
logger = logging.getLogger(__name__)

# Cost analysis thresholds
BATCH_COST_THRESHOLD = 0.01  # Minimum cost to justify batching
URGENT_REQUEST_THRESHOLD = 0.8  # Urgent if cost > 80% of average

class EnhancedGeminiService(GeminiService):
    """
    Enhanced Gemini service with automatic batch processing.
    
    This service extends GeminiService to automatically utilize batch processing
    for cost optimization while maintaining full backward compatibility.
    
    Attributes:
        batch_service: Underlying batch processing service
        queue_manager: Request queue manager
        monitor_service: Batch monitoring service
        batch_enabled: Whether to use batch processing
        cost_analysis: Cost analysis and decision making
    
    Example:
        >>> service = EnhancedGeminiService(batch_enabled=True)
        >>> questions = service.generate_questions(prompt, num_questions=5)
        >>> savings = service.get_cost_savings()
    """
    
    def __init__(
        self,
        batch_enabled: bool = True,
        auto_batch_threshold: int = 3,
        **kwargs
    ):
        """
        Initialize Enhanced Gemini Service.
        
        Args:
            batch_enabled: Enable automatic batch processing
            auto_batch_threshold: Minimum requests to trigger batching
            **kwargs: Arguments to pass to GeminiService
        """
        logger.info("Initializing EnhancedGeminiService")
        
        # Initialize parent service
        super().__init__(**kwargs)
        
        # Batch processing configuration
        self.batch_enabled = batch_enabled
        self.auto_batch_threshold = auto_batch_threshold
        
        # Initialize batch services
        if self.batch_enabled:
            try:
                self.batch_service = get_gemini_batch_service()
                self.queue_manager = get_batch_queue_manager()
                self.monitor_service = get_batch_monitor_service()
                
                logger.info("Batch services initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize batch services: {e}")
                self.batch_enabled = False
                self.batch_service = None
                self.queue_manager = None
                self.monitor_service = None
        else:
            self.batch_service = None
            self.queue_manager = None
            self.monitor_service = None
        
        # Cost analysis
        self.cost_analysis = {
            "individual_calls": 0,
            "batch_calls": 0,
            "total_individual_cost": 0.0,
            "total_batch_cost": 0.0,
            "cost_savings": 0.0,
            "requests_bypassed": 0
        }
        
        logger.info(
            f"EnhancedGeminiService initialized (batch_enabled={batch_enabled}, "
            f"auto_batch_threshold={auto_batch_threshold})"
        )
    
    def generate_questions(
        self,
        prompt: str,
        num_questions: int,
        use_cache: bool = True,
        retry_on_insufficient: bool = True,
        force_individual: bool = False
    ) -> List[Question]:
        """
        Generate questions with automatic batch optimization.
        
        This method automatically determines whether to use batch processing
        based on cost analysis and current conditions.
        
        Args:
            prompt: Complete prompt for Gemini
            num_questions: Expected number of questions
            use_cache: Use cached response if available
            retry_on_insufficient: Retry if insufficient questions
            force_individual: Force individual API call (bypass batching)
        
        Returns:
            List of validated Question objects
        
        Example:
            >>> service = EnhancedGeminiService()
            >>> questions = service.generate_questions(prompt, num_questions=5)
            >>> print(f"Generated {len(questions)} questions")
        """
        # Check if we should use batch processing
        if self.batch_enabled and not force_individual:
            should_batch, priority = self._analyze_request_for_batching(
                prompt, num_questions
            )
            
            if should_batch:
                return self._generate_questions_batch(
                    prompt, num_questions, priority, use_cache, retry_on_insufficient
                )
        
        # Fall back to individual processing
        return self._generate_questions_individual(
            prompt, num_questions, use_cache, retry_on_insufficient
        )
    
    async def generate_questions_async(
        self,
        prompt: str,
        num_questions: int,
        use_cache: bool = True,
        retry_on_insufficient: bool = True,
        force_individual: bool = False
    ) -> List[Question]:
        """
        Asynchronously generate questions with batch optimization.
        
        Args:
            prompt: Complete prompt for Gemini
            num_questions: Expected number of questions
            use_cache: Use cached response if available
            retry_on_insufficient: Retry if insufficient questions
            force_individual: Force individual API call
        
        Returns:
            List of validated Question objects
        """
        if self.batch_enabled and not force_individual:
            should_batch, priority = self._analyze_request_for_batching(
                prompt, num_questions
            )
            
            if should_batch:
                return await self._generate_questions_batch_async(
                    prompt, num_questions, priority, use_cache, retry_on_insufficient
                )
        
        return await super().generate_questions_async(
            prompt, num_questions, use_cache, retry_on_insufficient
        )
    
    def _analyze_request_for_batching(
        self, 
        prompt: str, 
        num_questions: int
    ) -> tuple[bool, RequestPriority]:
        """
        Analyze request to determine if batching is beneficial.
        
        Args:
            prompt: Request prompt
            num_questions: Number of questions requested
        
        Returns:
            Tuple of (should_batch, priority)
        """
        # Estimate cost of individual request
        estimated_cost = self._estimate_request_cost(prompt, num_questions)
        
        # Check queue load
        queue_status = self.queue_manager.get_queue_status() if self.queue_manager else {}
        queue_utilization = queue_status.get("utilization", 0.0)
        
        # Ensure queue_utilization is a number
        try:
            queue_utilization = float(queue_utilization)
        except (TypeError, ValueError):
            queue_utilization = 0.0
        
        # Determine priority based on cost and queue conditions
        if estimated_cost > URGENT_REQUEST_THRESHOLD:
            priority = RequestPriority.URGENT
        elif queue_utilization > 0.8:
            priority = RequestPriority.HIGH
        else:
            priority = RequestPriority.NORMAL
        
        # Decide on batching
        should_batch = (
            self.batch_enabled and
            estimated_cost >= BATCH_COST_THRESHOLD and
            queue_utilization < 0.95 and  # Don't batch if queue is full
            num_questions >= self.auto_batch_threshold
        )
        
        logger.debug(
            f"Batch analysis: cost=${estimated_cost:.4f}, "
            f"priority={priority.value}, should_batch={should_batch}"
        )
        
        return should_batch, priority
    
    def _generate_questions_batch(
        self,
        prompt: str,
        num_questions: int,
        priority: RequestPriority,
        use_cache: bool,
        retry_on_insufficient: bool
    ) -> List[Question]:
        """
        Generate questions using batch processing.
        
        Args:
            prompt: Request prompt
            num_questions: Number of questions
            priority: Request priority
            use_cache: Use cache
            retry_on_insufficient: Retry on insufficient
        
        Returns:
            List of generated questions
        """
        logger.info(f"Using batch processing for {num_questions} questions")
        
        # Create batch request
        request_id = f"question_gen_{int(time.time())}_{num_questions}"
        batch_request = BatchRequest(
            request_id=request_id,
            prompt=prompt,
            request_type=RequestType.QUESTION_GENERATION,
            priority=priority,
            metadata={
                "num_questions": num_questions,
                "use_cache": use_cache,
                "retry_on_insufficient": retry_on_insufficient,
                "original_service": "enhanced_gemini_service"
            },
            callback=self._handle_batch_response
        )
        
        # Add to queue
        if self.queue_manager:
            success = self.queue_manager.enqueue_request(batch_request)
            if not success:
                logger.warning("Queue full, falling back to individual processing")
                return self._generate_questions_individual(
                    prompt, num_questions, use_cache, retry_on_insufficient
                )
        else:
            # Process batch directly
            return self._process_single_batch(batch_request)
    
    async def _generate_questions_batch_async(
        self,
        prompt: str,
        num_questions: int,
        priority: RequestPriority,
        use_cache: bool,
        retry_on_insufficient: bool
    ) -> List[Question]:
        """Async version of batch question generation."""
        logger.info(f"Using async batch processing for {num_questions} questions")
        
        # Create batch request
        request_id = f"question_gen_async_{int(time.time())}_{num_questions}"
        batch_request = BatchRequest(
            request_id=request_id,
            prompt=prompt,
            request_type=RequestType.QUESTION_GENERATION,
            priority=priority,
            metadata={
                "num_questions": num_questions,
                "use_cache": use_cache,
                "retry_on_insufficient": retry_on_insufficient,
                "original_service": "enhanced_gemini_service_async"
            }
        )
        
        # Add to queue and process
        if self.queue_manager:
            success = self.queue_manager.enqueue_request(batch_request)
            if not success:
                logger.warning("Queue full, falling back to individual processing")
                return await super().generate_questions_async(
                    prompt, num_questions, use_cache, retry_on_insufficient
                )
        else:
            # Process batch directly
            return await self._process_single_batch_async(batch_request)
    
    def _generate_questions_individual(
        self,
        prompt: str,
        num_questions: int,
        use_cache: bool,
        retry_on_insufficient: bool
    ) -> List[Question]:
        """
        Generate questions using individual API call.
        
        Args:
            prompt: Request prompt
            num_questions: Number of questions
            use_cache: Use cache
            retry_on_insufficient: Retry on insufficient
        
        Returns:
            List of generated questions
        """
        logger.info(f"Using individual processing for {num_questions} questions")
        
        # Track individual call
        self.cost_analysis["individual_calls"] += 1
        
        # Call parent method
        start_time = time.time()
        questions = super().generate_questions(
            prompt, num_questions, use_cache, retry_on_insufficient
        )
        
        # Track cost
        processing_time = time.time() - start_time
        estimated_cost = self._estimate_request_cost(prompt, num_questions)
        self.cost_analysis["total_individual_cost"] += estimated_cost
        
        # Update cost savings
        self._update_cost_savings()
        
        # Track in monitor if available
        if self.monitor_service:
            self.monitor_service.track_queue_metrics({
                "current_queue_size": 0,
                "utilization": 0.0,
                "average_wait_time": 0.0,
                "total_enqueued": 0,
                "total_processed": 1
            })
        
        logger.debug(
            f"Individual processing completed: {len(questions)} questions, "
            f"cost=${estimated_cost:.4f}, time={processing_time:.2f}s"
        )
        
        return questions
    
    def _process_single_batch(self, batch_request: BatchRequest) -> List[Question]:
        """Process a single batch request."""
        try:
            # Process batch
            batch_result = asyncio.run(
                self.batch_service.process_batch(force_flush=True)
            )
            
            if batch_result and batch_request.request_id in batch_result.results:
                result = batch_result.results[batch_request.request_id]
                
                if result.get("success", False):
                    # Parse questions from batch result
                    content = result.get("content", "")
                    questions = self._parse_batch_response(content, batch_request)
                    
                    # Update cost tracking
                    self.cost_analysis["batch_calls"] += 1
                    self.cost_analysis["total_batch_cost"] += batch_result.cost_batch
                    
                    # Track in monitor
                    if self.monitor_service:
                        self.monitor_service.track_batch_processing(batch_result)
                    
                    return questions
                else:
                    logger.error(f"Batch processing failed: {result.get('error')}")
                    return []
            else:
                logger.warning(f"No result found for request {batch_request.request_id}")
                return []
                
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return []
    
    async def _process_single_batch_async(self, batch_request: BatchRequest) -> List[Question]:
        """Async version of single batch processing."""
        try:
            # Process batch
            batch_result = await self.batch_service.process_batch(force_flush=True)
            
            if batch_result and batch_request.request_id in batch_result.results:
                result = batch_result.results[batch_request.request_id]
                
                if result.get("success", False):
                    # Parse questions from batch result
                    content = result.get("content", "")
                    questions = self._parse_batch_response(content, batch_request)
                    
                    # Update cost tracking
                    self.cost_analysis["batch_calls"] += 1
                    self.cost_analysis["total_batch_cost"] += batch_result.cost_batch
                    
                    # Track in monitor
                    if self.monitor_service:
                        self.monitor_service.track_batch_processing(batch_result)
                    
                    return questions
                else:
                    logger.error(f"Batch processing failed: {result.get('error')}")
                    return []
            else:
                logger.warning(f"No result found for request {batch_request.request_id}")
                return []
                
        except Exception as e:
            logger.error(f"Async batch processing error: {e}")
            return []
    
    def _handle_batch_response(self, result: Dict[str, Any]):
        """Handle batch response callback."""
        if result.get("success", False):
            logger.info(f"Batch response received: {result.get('request_id')}")
        else:
            logger.error(f"Batch response failed: {result.get('error')}")
    
    def _parse_batch_response(self, content: str, batch_request: BatchRequest) -> List[Question]:
        """Parse batch response content into questions."""
        try:
            # Use existing response parser from parent service
            num_questions = batch_request.metadata.get("num_questions", 5)
            questions, parse_stats = self.parser.parse_response(content, num_questions)
            
            logger.info(
                f"Parsed {len(questions)} questions from batch response "
                f"(valid: {parse_stats['valid']}, invalid: {parse_stats['invalid']})"
            )
            
            return questions
            
        except Exception as e:
            logger.error(f"Failed to parse batch response: {e}")
            return []
    
    def _estimate_request_cost(self, prompt: str, num_questions: int) -> float:
        """Estimate cost for a request."""
        # Rough estimation: 1 token ≈ 4 characters
        input_tokens = len(prompt) // 4
        # Estimate output tokens (typically 50 tokens per question)
        output_tokens = num_questions * 50
        
        # Use same pricing as parent service
        input_cost = (input_tokens / 1000) * 0.000125
        output_cost = (output_tokens / 1000) * 0.000375
        
        return input_cost + output_cost
    
    def _update_cost_savings(self):
        """Update cost savings calculations."""
        if self.cost_analysis["total_individual_cost"] > 0:
            potential_individual_cost = (
                self.cost_analysis["total_individual_cost"] + 
                self.cost_analysis["total_batch_cost"]
            )
            actual_cost = (
                self.cost_analysis["total_individual_cost"] + 
                self.cost_analysis["total_batch_cost"]
            )
            
            self.cost_analysis["cost_savings"] = (
                potential_individual_cost - actual_cost
            )
    
    def get_cost_savings(self) -> Dict[str, Any]:
        """
        Get comprehensive cost savings analysis.
        
        Returns:
            Dictionary with cost savings metrics
        
        Example:
            >>> service = EnhancedGeminiService()
            >>> savings = service.get_cost_savings()
            >>> print(f"Total saved: ${savings['total_savings']:.4f}")
        """
        self._update_cost_savings()
        
        total_calls = (
            self.cost_analysis["individual_calls"] + 
            self.cost_analysis["batch_calls"]
        )
        
        if total_calls > 0:
            batch_efficiency = self.cost_analysis["batch_calls"] / total_calls
        else:
            batch_efficiency = 0.0
        
        return {
            "individual_calls": self.cost_analysis["individual_calls"],
            "batch_calls": self.cost_analysis["batch_calls"],
            "total_individual_cost": self.cost_analysis["total_individual_cost"],
            "total_batch_cost": self.cost_analysis["total_batch_cost"],
            "total_cost": (
                self.cost_analysis["total_individual_cost"] + 
                self.cost_analysis["total_batch_cost"]
            ),
            "total_savings": self.cost_analysis["cost_savings"],
            "savings_percentage": (
                self.cost_analysis["cost_savings"] / 
                max(self.cost_analysis["total_individual_cost"], 0.001) * 100
            ),
            "batch_efficiency": batch_efficiency,
            "average_cost_per_call": (
                (self.cost_analysis["total_individual_cost"] + 
                 self.cost_analysis["total_batch_cost"]) / 
                max(total_calls, 1)
            )
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get comprehensive service status.
        
        Returns:
            Dictionary with service status and metrics
        
        Example:
            >>> service = EnhancedGeminiService()
            >>> status = service.get_service_status()
            >>> print(f"Batch enabled: {status['batch_enabled']}")
        """
        status = {
            "batch_enabled": self.batch_enabled,
            "auto_batch_threshold": self.auto_batch_threshold,
            "services_initialized": {
                "batch_service": self.batch_service is not None,
                "queue_manager": self.queue_manager is not None,
                "monitor_service": self.monitor_service is not None
            },
            "cost_analysis": self.get_cost_savings(),
            "parent_stats": self.get_usage_stats()
        }
        
        # Add queue status if available
        if self.queue_manager:
            status["queue_status"] = self.queue_manager.get_queue_status()
        
        # Add batch service status if available
        if self.batch_service:
            status["batch_service_status"] = self.batch_service.get_queue_status()
        
        return status
    
    def enable_batch_processing(self, enabled: bool = True):
        """
        Enable or disable batch processing.
        
        Args:
            enabled: Whether to enable batch processing
        
        Example:
            >>> service = EnhancedGeminiService()
            >>> service.enable_batch_processing(False)
        """
        self.batch_enabled = enabled
        logger.info(f"Batch processing {'enabled' if enabled else 'disabled'}")
    
    def set_batch_threshold(self, threshold: int):
        """
        Set minimum requests for automatic batching.
        
        Args:
            threshold: Minimum requests to trigger batching
        
        Example:
            >>> service = EnhancedGeminiService()
            >>> service.set_batch_threshold(5)
        """
        self.auto_batch_threshold = max(1, threshold)
        logger.info(f"Batch threshold set to {self.auto_batch_threshold}")

# Factory function for easy migration
def create_enhanced_gemini_service(
    batch_enabled: bool = True,
    **kwargs
) -> EnhancedGeminiService:
    """
    Create enhanced Gemini service with optimal configuration.
    
    Args:
        batch_enabled: Enable batch processing
        **kwargs: Additional arguments for service
    
    Returns:
        Configured EnhancedGeminiService instance
    
    Example:
        >>> service = create_enhanced_gemini_service(
        ...     batch_enabled=True, 
        ...     auto_batch_threshold=3
        ... )
    """
    # Get batch configuration
    batch_settings = get_batch_settings()
    
    # Configure service based on batch settings
    service_kwargs = {
        "batch_enabled": batch_enabled,
        "auto_batch_threshold": batch_settings.batch_size,
        **kwargs
    }
    
    return EnhancedGeminiService(**service_kwargs)

# Module initialization
logger.info("Enhanced Gemini service module loaded")
logger.info(f"Batch cost threshold: ${BATCH_COST_THRESHOLD}")
logger.info(f"Auto-batch threshold: {3} requests")