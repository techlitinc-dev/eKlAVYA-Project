"""
Enhanced Analytics Service with Batch API Integration - Mentor AI Platform

This module provides an enhanced version of the analytics service that automatically
utilizes batch processing for cost optimization while maintaining backward compatibility.

Features:
- Automatic batch processing for multiple analytics requests
- Cost optimization through intelligent request grouping
- Backward compatibility with existing AnalyticsService
- Real-time cost tracking and savings analytics
- Fallback to individual processing when needed

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.enhanced_analytics_service import EnhancedAnalyticsService
    >>> 
    >>> # Initialize enhanced service
    >>> service = EnhancedAnalyticsService(batch_enabled=True)
    >>> 
    >>> # Use like regular AnalyticsService (with automatic batching)
    >>> analytics_id = service.generate_analytics(
    ...     test_id="test_123",
    ...     student_id="student_456",
    ...     answers={1: "B", 2: "A"}
    ... )
"""

import logging
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor

from services.analytics_service import (
    AnalyticsService,
    AnalyticsServiceError,
    PipelineStepError
)
from services.gemini_batch_service import (
    GeminiBatchService,
    BatchRequest,
    RequestType,
    RequestPriority,
    get_gemini_batch_service
)
from services.batch_queue_manager import get_batch_queue_manager

# Configure logging
logger = logging.getLogger(__name__)

# Batch configuration
BATCH_COST_THRESHOLD = 0.01  # Minimum cost to trigger batching
DEFAULT_BATCH_SIZE = 10  # Default batch size for analytics


class EnhancedAnalyticsService(AnalyticsService):
    """
    Enhanced analytics service with automatic batch processing.
    
    This service extends AnalyticsService to automatically utilize batch processing
    for cost optimization while maintaining full backward compatibility.
    
    Attributes:
        batch_service: GeminiBatchService instance
        batch_enabled: Whether batch processing is enabled
        auto_batch_threshold: Minimum requests to trigger batching
        queue_manager: BatchQueueManager instance
        cost_savings: Track cost savings from batching
    
    Example:
        >>> service = EnhancedAnalyticsService(batch_enabled=True)
        >>> analytics_id = service.generate_analytics(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     answers={1: "B", 2: "A"}
        ... )
    """
    
    def __init__(
        self,
        batch_enabled: bool = True,
        auto_batch_threshold: int = 3,
        **kwargs
    ):
        """
        Initialize Enhanced Analytics Service.
        
        Args:
            batch_enabled: Enable batch processing (default: True)
            auto_batch_threshold: Minimum requests to trigger batching (default: 3)
            **kwargs: Arguments to pass to AnalyticsService
        """
        logger.info("Initializing EnhancedAnalyticsService")
        
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
            f"EnhancedAnalyticsService initialized (batch_enabled={batch_enabled}, "
            f"auto_batch_threshold={auto_batch_threshold})"
        )
    
    def generate_analytics(
        self,
        test_id: str,
        student_id: str,
        answers: Dict[int, str],
        test_metadata: Optional[Dict[str, Any]] = None,
        include_ai_insights: bool = True,
        use_cache: bool = True,
        force_individual: bool = False
    ) -> str:
        """
        Generate analytics with automatic batch processing.
        
        Args:
            test_id: Test identifier
            student_id: Student identifier
            answers: Student answers dict {question_number: answer}
            test_metadata: Additional test metadata
            include_ai_insights: Whether to generate AI insights
            use_cache: Whether to use cached results
            force_individual: Force individual processing (skip batching)
        
        Returns:
            analytics_id: Unique analytics report identifier
        
        Example:
            >>> analytics_id = service.generate_analytics(
            ...     test_id="test_123",
            ...     student_id="student_456",
            ...     answers={1: "B", 2: "A"},
            ...     include_ai_insights=True
            ... )
        """
        if not self.batch_enabled or force_individual or not include_ai_insights:
            # Use regular processing
            self.cost_savings["requests_individual"] += 1
            return super().generate_analytics(
                test_id=test_id,
                student_id=student_id,
                answers=answers,
                test_metadata=test_metadata,
                include_ai_insights=include_ai_insights,
                use_cache=use_cache
            )
        
        # Check if we should use batch processing
        queue_size = self.queue_manager.get_queue_size() if self.queue_manager else 0
        
        if queue_size < self.auto_batch_threshold:
            # Not enough requests for batching, process individually
            self.cost_savings["requests_individual"] += 1
            return super().generate_analytics(
                test_id=test_id,
                student_id=student_id,
                answers=answers,
                test_metadata=test_metadata,
                include_ai_insights=include_ai_insights,
                use_cache=use_cache
            )
        
        # Add to batch queue
        request_id = f"analytics_{test_id}_{student_id}_{int(time.time())}"
        
        # Create batch request
        batch_request = BatchRequest(
            request_id=request_id,
            prompt=self._build_analytics_prompt(test_id, student_id, answers),
            request_type=RequestType.ANALYTICS_INSIGHTS,
            priority=RequestPriority.NORMAL,
            metadata={
                "test_id": test_id,
                "student_id": student_id,
                "answers": answers,
                "test_metadata": test_metadata,
                "include_ai_insights": include_ai_insights,
                "use_cache": use_cache,
                "callback": self._process_analytics_result
            }
        )
        
        # Add to batch queue
        self.queue_manager.add_request(batch_request)
        self.cost_savings["requests_batched"] += 1
        
        logger.info(f"Added analytics request to batch: {request_id}")
        
        # Process batch if ready
        if queue_size >= self.auto_batch_threshold:
            logger.info("Triggering batch processing")
            asyncio.create_task(self._process_analytics_batch())
        
        return request_id
    
    async def generate_analytics_async(
        self,
        test_id: str,
        student_id: str,
        answers: Dict[int, str],
        test_metadata: Optional[Dict[str, Any]] = None,
        include_ai_insights: bool = True,
        use_cache: bool = True,
        force_individual: bool = False
    ) -> str:
        """
        Asynchronously generate analytics with batch processing.
        
        Args:
            test_id: Test identifier
            student_id: Student identifier
            answers: Student answers dict {question_number: answer}
            test_metadata: Additional test metadata
            include_ai_insights: Whether to generate AI insights
            use_cache: Whether to use cached results
            force_individual: Force individual processing (skip batching)
        
        Returns:
            analytics_id: Unique analytics report identifier
        """
        if not self.batch_enabled or force_individual or not include_ai_insights:
            # Use regular processing
            self.cost_savings["requests_individual"] += 1
            
            # Run synchronous method in executor
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                super().generate_analytics,
                test_id,
                student_id,
                answers,
                test_metadata,
                include_ai_insights,
                use_cache
            )
        
        # Add to batch queue
        request_id = f"analytics_{test_id}_{student_id}_{int(time.time())}"
        
        # Create batch request
        batch_request = BatchRequest(
            request_id=request_id,
            prompt=self._build_analytics_prompt(test_id, student_id, answers),
            request_type=RequestType.ANALYTICS_INSIGHTS,
            priority=RequestPriority.NORMAL,
            metadata={
                "test_id": test_id,
                "student_id": student_id,
                "answers": answers,
                "test_metadata": test_metadata,
                "include_ai_insights": include_ai_insights,
                "use_cache": use_cache,
                "callback": self._process_analytics_result
            }
        )
        
        # Add to batch queue
        self.queue_manager.add_request(batch_request)
        self.cost_savings["requests_batched"] += 1
        
        logger.info(f"Added analytics request to batch: {request_id}")
        
        # Process batch if ready
        queue_size = self.queue_manager.get_queue_size()
        if queue_size >= self.auto_batch_threshold:
            logger.info("Triggering batch processing")
            await self._process_analytics_batch()
        
        return request_id
    
    def _build_analytics_prompt(self, test_id: str, student_id: str, answers: Dict[int, str]) -> str:
        """Build analytics prompt for batch processing."""
        return f"""
        Generate analytics insights for:
        Test ID: {test_id}
        Student ID: {student_id}
        Answers: {answers}
        
        Provide comprehensive analysis including:
        - Performance strengths
        - Areas for improvement
        - Study recommendations
        - Learning patterns
        """
    
    def _process_analytics_result(self, result: Dict[str, Any]):
        """Process analytics result from batch."""
        try:
            if result.get("success"):
                # Extract analytics data and store in Firestore
                analytics_data = result.get("insights", "")
                metadata = result.get("metadata", {})
                
                # Store the result using the original analytics pipeline
                analytics_id = self._store_batch_result(
                    analytics_data,
                    metadata
                )
                
                logger.info(f"Processed batch analytics result: {analytics_id}")
            else:
                logger.error(f"Batch analytics failed: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"Error processing analytics result: {e}")
    
    def _store_batch_result(self, analytics_data: str, metadata: Dict[str, Any]) -> str:
        """Store batch-generated analytics result."""
        try:
            # Create analytics report structure
            from services.analytics_report_builder import AnalyticsReport
            
            # Generate analytics ID
            test_id = metadata.get("test_id", "unknown")
            student_id = metadata.get("student_id", "unknown")
            analytics_id = f"analytics_{test_id}_{student_id}_{int(time.time())}"
            
            # Create basic report structure
            report_data = {
                "analytics_id": analytics_id,
                "test_id": test_id,
                "student_id": student_id,
                "ai_insights": analytics_data,
                "batch_generated": True,
                "created_at": datetime.utcnow(),
                "metadata": metadata
            }
            
            # Store in Firestore
            if self.db:
                analytics_ref = self.db.collection(self.analytics_collection).document(analytics_id)
                analytics_ref.set(report_data)
            
            return analytics_id
            
        except Exception as e:
            logger.error(f"Failed to store batch result: {e}")
            raise
    
    async def _process_analytics_batch(self):
        """Process a batch of analytics requests."""
        try:
            # Get batch from queue
            requests = self.queue_manager.get_batch(DEFAULT_BATCH_SIZE)
            
            if not requests:
                return
            
            logger.info(f"Processing analytics batch of {len(requests)} requests")
            
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
                    f"Analytics batch processed: ${batch_result.cost_savings:.4f} saved, "
                    f"{len(requests)} requests"
                )
            else:
                logger.warning("Analytics batch processing failed")
        
        except Exception as e:
            logger.error(f"Error processing analytics batch: {e}")
    
    def generate_batch_analytics(
        self,
        analytics_requests: List[Dict[str, Any]],
        force_batch: bool = True
    ) -> List[str]:
        """
        Generate analytics for multiple students in batch.
        
        Args:
            analytics_requests: List of analytics request dictionaries
            force_batch: Force batch processing even for small batches
        
        Returns:
            List of analytics IDs
        
        Example:
            >>> requests = [
            ...     {"test_id": "test_1", "student_id": "student_1", "answers": {1: "A"}},
            ...     {"test_id": "test_2", "student_id": "student_2", "answers": {1: "B"}}
            ... ]
            >>> analytics_ids = service.generate_batch_analytics(requests)
        """
        if not self.batch_enabled or not force_batch:
            # Process individually
            analytics_ids = []
            for req in analytics_requests:
                analytics_id = super().generate_analytics(**req)
                analytics_ids.append(analytics_id)
            return analytics_ids
        
        # Create batch requests
        batch_requests = []
        analytics_ids = []
        
        for req_data in analytics_requests:
            request_id = f"analytics_{req_data['test_id']}_{req_data['student_id']}_{int(time.time())}"
            analytics_ids.append(request_id)
            
            batch_request = BatchRequest(
                request_id=request_id,
                prompt=self._build_analytics_prompt(
                    req_data["test_id"],
                    req_data["student_id"],
                    req_data["answers"]
                ),
                request_type=RequestType.ANALYTICS_INSIGHTS,
                priority=RequestPriority.NORMAL,
                metadata={
                    **req_data,
                    "callback": self._process_analytics_result
                }
            )
            batch_requests.append(batch_request)
        
        # Add all to queue
        for request in batch_requests:
            self.queue_manager.add_request(request)
            self.cost_savings["requests_batched"] += 1
        
        # Process batch
        asyncio.create_task(self._process_analytics_batch())
        
        logger.info(f"Added {len(batch_requests)} analytics requests to batch")
        return analytics_ids
    
    def get_cost_savings(self) -> Dict[str, Any]:
        """
        Get comprehensive cost savings statistics.
        
        Returns:
            Dictionary with cost analysis and savings
        
        Example:
            >>> service = EnhancedAnalyticsService()
            >>> savings = service.get_cost_savings()
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
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get comprehensive service status.
        
        Returns:
            Dictionary with service status and statistics
        
        Example:
            >>> service = EnhancedAnalyticsService()
            >>> status = service.get_service_status()
            >>> print(f"Batch enabled: {status['batch_enabled']}")
        """
        base_status = {
            "service_type": "EnhancedAnalyticsService",
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
        base_status["analytics_service_stats"] = self.get_service_stats()
        
        return base_status
    
    def enable_batch_processing(self, enabled: bool = True):
        """
        Enable or disable batch processing.
        
        Args:
            enabled: Whether to enable batch processing
        
        Example:
            >>> service = EnhancedAnalyticsService()
            >>> service.enable_batch_processing(False)
        """
        self.batch_enabled = enabled
        logger.info(f"Batch processing {'enabled' if enabled else 'disabled'}")
    
    def set_batch_threshold(self, threshold: int):
        """
        Set automatic batch threshold.
        
        Args:
            threshold: Minimum requests to trigger batching
        
        Example:
            >>> service = EnhancedAnalyticsService()
            >>> service.set_batch_threshold(5)
        """
        if threshold < 2:
            raise ValueError("Batch threshold must be at least 2")
        
        self.auto_batch_threshold = threshold
        logger.info(f"Batch threshold set to {threshold}")


# Factory function for easy migration
def create_enhanced_analytics_service(
    batch_enabled: bool = True,
    auto_batch_threshold: int = 3,
    **kwargs
) -> EnhancedAnalyticsService:
    """
    Create enhanced analytics service with optimal configuration.
    
    Args:
        batch_enabled: Enable batch processing
        auto_batch_threshold: Minimum requests for batching
        **kwargs: Additional arguments for AnalyticsService
    
    Returns:
        Configured EnhancedAnalyticsService instance
    
    Example:
        >>> service = create_enhanced_analytics_service(
        ...     batch_enabled=True,
        ...     auto_batch_threshold=5
        ... )
    """
    service_kwargs = {
        "batch_enabled": batch_enabled,
        "auto_batch_threshold": auto_batch_threshold,
        **kwargs
    }
    
    return EnhancedAnalyticsService(**service_kwargs)


# Module initialization
logger.info("Enhanced analytics service module loaded")
logger.info(f"Batch cost threshold: ${BATCH_COST_THRESHOLD}")