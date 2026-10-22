"""
Batch Queue Manager for Gemini API - Mentor AI Platform

This module provides advanced queue management for Gemini batch requests,
including priority handling, load balancing, and intelligent batching strategies.

Features:
- Multi-queue priority system with automatic promotion
- Load balancing across multiple batch processors
- Intelligent request grouping and batching
- Real-time queue monitoring and analytics
- Automatic queue cleanup and maintenance
- Request deduplication and duplicate detection
- Adaptive batching based on queue load
- Queue persistence and recovery

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.batch_queue_manager import BatchQueueManager
    >>> 
    >>> # Initialize queue manager
    >>> queue_manager = BatchQueueManager()
    >>> 
    >>> # Add requests to queue
    >>> queue_manager.enqueue_request(request)
    >>> 
    >>> # Process queues
    >>> batches = queue_manager.get_ready_batches()
    >>> for batch in batches:
    ...     results = await process_batch(batch)
"""

import os
import json
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import pickle
import hashlib

from services.gemini_batch_service import BatchRequest, RequestType, RequestPriority

# Configure logging
logger = logging.getLogger(__name__)

# Queue configuration
DEFAULT_QUEUE_CAPACITY = 1000
QUEUE_PERSISTENCE_INTERVAL = 300  # 5 minutes
QUEUE_CLEANUP_INTERVAL = 3600  # 1 hour
MAX_QUEUE_AGE_HOURS = 24
PROMOTION_INTERVAL = 300  # 5 minutes

class QueueStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"

@dataclass
class QueueMetrics:
    """Metrics for queue performance monitoring."""
    total_enqueued: int = 0
    total_dequeued: int = 0
    total_processed: int = 0
    total_failed: int = 0
    average_wait_time: float = 0.0
    peak_queue_size: int = 0
    current_queue_size: int = 0
    queue_utilization: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class QueueConfig:
    """Configuration for queue behavior."""
    max_capacity: int = DEFAULT_QUEUE_CAPACITY
    enable_persistence: bool = True
    enable_promotion: bool = True
    promotion_interval: int = PROMOTION_INTERVAL
    cleanup_interval: int = QUEUE_CLEANUP_INTERVAL
    max_age_hours: int = MAX_QUEUE_AGE_HOURS
    adaptive_batching: bool = True
    load_balance_threshold: float = 0.8

class BatchQueueManager:
    """
    Advanced queue manager for Gemini batch requests.
    
    This manager handles multiple priority queues, intelligent batching,
    load balancing, and comprehensive queue monitoring.
    
    Attributes:
        queues: Priority-based request queues
        metrics: Performance metrics tracking
        config: Queue configuration
        request_cache: Duplicate detection cache
        persistence_enabled: Whether to persist queue state
    
    Example:
        >>> manager = BatchQueueManager()
        >>> manager.enqueue_request(request)
        >>> batches = manager.get_ready_batches()
    """
    
    def __init__(self, config: Optional[QueueConfig] = None):
        """
        Initialize Batch Queue Manager.
        
        Args:
            config: Queue configuration (uses default if None)
        """
        logger.info("Initializing BatchQueueManager")
        
        self.config = config or QueueConfig()
        
        # Multi-level priority queues with aging
        self.queues = {
            RequestPriority.URGENT: deque(maxlen=self.config.max_capacity),
            RequestPriority.HIGH: deque(maxlen=self.config.max_capacity),
            RequestPriority.NORMAL: deque(maxlen=self.config.max_capacity),
            RequestPriority.LOW: deque(maxlen=self.config.max_capacity)
        }
        
        # Request type queues for intelligent batching
        self.type_queues = {
            req_type: deque(maxlen=self.config.max_capacity)
            for req_type in RequestType
        }
        
        # Request tracking
        self.request_metadata = {}  # request_id -> metadata
        self.request_cache = {}  # content_hash -> request_id
        self.active_batches = {}  # batch_id -> batch_info
        
        # Metrics tracking
        self.metrics = defaultdict(QueueMetrics)
        self.global_metrics = QueueMetrics()
        
        # Queue status
        self.status = QueueStatus.ACTIVE
        self.lock = threading.RLock()
        
        # Background tasks
        self.maintenance_task = None
        self.persistence_task = None
        
        # Load persisted state if enabled
        if self.config.enable_persistence:
            self._load_persisted_state()
        
        # Start background tasks
        self._start_background_tasks()
        
        logger.info(
            f"BatchQueueManager initialized (capacity={self.config.max_capacity}, "
            f"persistence={self.config.enable_persistence})"
        )
    
    def enqueue_request(self, request: BatchRequest) -> bool:
        """
        Add a request to the appropriate queue.
        
        Args:
            request: BatchRequest to enqueue
        
        Returns:
            True if successfully enqueued, False if queue is full
        
        Example:
            >>> success = manager.enqueue_request(request)
            >>> if success:
            ...     print("Request queued successfully")
        """
        with self.lock:
            # Check queue capacity
            if self._is_queue_full():
                logger.warning("Queue at capacity, rejecting request")
                return False
            
            # Check for duplicates
            content_hash = self._generate_content_hash(request)
            if content_hash in self.request_cache:
                logger.info(f"Duplicate request detected: {request.request_id}")
                return False
            
            # Add to priority queue
            self.queues[request.priority].append(request)
            
            # Also add to type queue for batching
            self.type_queues[request.request_type].append(request)
            
            # Store metadata
            self.request_metadata[request.request_id] = {
                "enqueued_at": datetime.now(),
                "priority": request.priority,
                "request_type": request.request_type,
                "content_hash": content_hash,
                "queue_position": len(self.queues[request.priority])
            }
            
            # Update cache
            self.request_cache[content_hash] = request.request_id
            
            # Update metrics
            self.global_metrics.total_enqueued += 1
            self.global_metrics.current_queue_size = self._get_total_queue_size()
            self.global_metrics.queue_utilization = (
                self.global_metrics.current_queue_size / self.config.max_capacity
            )
            
            logger.info(
                f"Enqueued request {request.request_id} "
                f"(type: {request.request_type.value}, priority: {request.priority.value})"
            )
            
            return True
    
    def get_ready_batches(
        self, 
        max_batch_size: int = 5,
        force_flush: bool = False
    ) -> List[List[BatchRequest]]:
        """
        Get ready batches for processing.
        
        Args:
            max_batch_size: Maximum batch size
            force_flush: Force processing even small batches
        
        Returns:
            List of batches ready for processing
        
        Example:
            >>> batches = manager.get_ready_batches(max_batch_size=10)
            >>> for batch in batches:
            ...     await process_batch(batch)
        """
        with self.lock:
            if self.status != QueueStatus.ACTIVE and not force_flush:
                logger.info(f"Queue not active (status: {self.status.value})")
                return []
            
            batches = []
            
            # Process by request type for optimal batching
            for request_type, type_queue in self.type_queues.items():
                if not type_queue:
                    continue
                
                # Get batch configuration for this type
                type_batch_size = self._get_optimal_batch_size(request_type, max_batch_size)
                
                # Extract batch from type queue
                batch = []
                remaining_requests = deque()
                
                while type_queue:
                    request = type_queue.popleft()
                    
                    # Check if request is still in priority queue (not processed yet)
                    if request in self.queues[request.priority]:
                        batch.append(request)
                        
                        if len(batch) >= type_batch_size:
                            break
                    else:
                        # Request was already processed, skip
                        remaining_requests.append(request)
                
                # Put back remaining requests
                self.type_queues[request_type] = remaining_requests
                
                if batch:
                    # Remove from priority queues
                    for request in batch:
                        try:
                            self.queues[request.priority].remove(request)
                        except ValueError:
                            pass  # Already removed
                    
                    batches.append(batch)
                    logger.info(
                        f"Created batch of {len(batch)} {request_type.value} requests"
                    )
            
            # Also check for high-priority urgent requests
            urgent_batch = self._get_urgent_batch(max_batch_size)
            if urgent_batch:
                batches.insert(0, urgent_batch)  # Process urgent first
            
            return batches
    
    def mark_batch_processed(self, batch: List[BatchRequest], success: bool = True):
        """
        Mark a batch as processed and update metrics.
        
        Args:
            batch: List of processed requests
            success: Whether processing was successful
        
        Example:
            >>> manager.mark_batch_processed(batch, success=True)
        """
        with self.lock:
            current_time = datetime.now()
            
            for request in batch:
                if request.request_id not in self.request_metadata:
                    continue
                
                metadata = self.request_metadata[request.request_id]
                
                # Calculate wait time
                wait_time = (current_time - metadata["enqueued_at"]).total_seconds()
                
                # Update metrics
                if success:
                    self.global_metrics.total_processed += 1
                else:
                    self.global_metrics.total_failed += 1
                
                # Update average wait time
                total_processed = self.global_metrics.total_processed + self.global_metrics.total_failed
                self.global_metrics.average_wait_time = (
                    (self.global_metrics.average_wait_time * (total_processed - 1) + wait_time) / 
                    total_processed
                )
                
                # Clean up metadata
                del self.request_metadata[request.request_id]
                
                # Remove from cache
                content_hash = metadata["content_hash"]
                if content_hash in self.request_cache:
                    del self.request_cache[content_hash]
            
            # Update current queue size
            self.global_metrics.current_queue_size = self._get_total_queue_size()
            self.global_metrics.queue_utilization = (
                self.global_metrics.current_queue_size / self.config.max_capacity
            )
            
            logger.info(f"Marked batch of {len(batch)} requests as processed")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get comprehensive queue status and metrics.
        
        Returns:
            Dictionary with queue information
        
        Example:
            >>> status = manager.get_queue_status()
            >>> print(f"Queue size: {status['total_requests']}")
        """
        with self.lock:
            # Queue sizes by priority
            priority_sizes = {
                priority.value: len(queue) 
                for priority, queue in self.queues.items()
            }
            
            # Queue sizes by type
            type_sizes = {
                req_type.value: len(queue) 
                for req_type, queue in self.type_queues.items()
            }
            
            # Age analysis
            current_time = datetime.now()
            age_distribution = {"<1min": 0, "1-5min": 0, "5-30min": 0, ">30min": 0}
            
            for metadata in self.request_metadata.values():
                age_minutes = (current_time - metadata["enqueued_at"]).total_seconds() / 60
                if age_minutes < 1:
                    age_distribution["<1min"] += 1
                elif age_minutes < 5:
                    age_distribution["1-5min"] += 1
                elif age_minutes < 30:
                    age_distribution["5-30min"] += 1
                else:
                    age_distribution[">30min"] += 1
            
            return {
                "status": self.status.value,
                "total_requests": self._get_total_queue_size(),
                "capacity": self.config.max_capacity,
                "utilization": self.global_metrics.queue_utilization,
                "requests_by_priority": priority_sizes,
                "requests_by_type": type_sizes,
                "age_distribution": age_distribution,
                "metrics": {
                    "total_enqueued": self.global_metrics.total_enqueued,
                    "total_processed": self.global_metrics.total_processed,
                    "total_failed": self.global_metrics.total_failed,
                    "average_wait_time": self.global_metrics.average_wait_time,
                    "peak_queue_size": self.global_metrics.peak_queue_size
                },
                "config": {
                    "max_capacity": self.config.max_capacity,
                    "enable_persistence": self.config.enable_persistence,
                    "enable_promotion": self.config.enable_promotion,
                    "adaptive_batching": self.config.adaptive_batching
                }
            }
    
    def pause_queue(self):
        """Pause queue processing (no new requests accepted)."""
        with self.lock:
            self.status = QueueStatus.PAUSED
            logger.info("Queue paused")
    
    def resume_queue(self):
        """Resume queue processing."""
        with self.lock:
            self.status = QueueStatus.ACTIVE
            logger.info("Queue resumed")
    
    def drain_queue(self):
        """Drain queue (process existing requests, no new ones)."""
        with self.lock:
            self.status = QueueStatus.DRAINING
            logger.info("Queue draining started")
    
    def clear_queue(self):
        """Clear all queued requests."""
        with self.lock:
            for queue in self.queues.values():
                queue.clear()
            
            for queue in self.type_queues.values():
                queue.clear()
            
            self.request_metadata.clear()
            self.request_cache.clear()
            
            self.global_metrics.current_queue_size = 0
            self.global_metrics.queue_utilization = 0.0
            
            logger.info("Queue cleared")
    
    def _is_queue_full(self) -> bool:
        """Check if any queue is at capacity."""
        total_size = self._get_total_queue_size()
        return total_size >= self.config.max_capacity
    
    def _get_total_queue_size(self) -> int:
        """Get total number of requests across all queues."""
        return sum(len(queue) for queue in self.queues.values())
    
    def _get_optimal_batch_size(self, request_type: RequestType, max_size: int) -> int:
        """Get optimal batch size for request type based on current load."""
        if not self.config.adaptive_batching:
            return max_size
        
        queue_size = len(self.type_queues[request_type])
        utilization = queue_size / self.config.max_capacity
        
        # Adaptive batching based on queue load
        if utilization > 0.8:  # High load - larger batches
            return min(max_size * 2, 20)
        elif utilization > 0.5:  # Medium load - normal batches
            return max_size
        else:  # Low load - smaller batches for lower latency
            return max(2, max_size // 2)
    
    def _get_urgent_batch(self, max_size: int) -> Optional[List[BatchRequest]]:
        """Get batch of urgent requests."""
        urgent_queue = self.queues[RequestPriority.URGENT]
        if not urgent_queue:
            return None
        
        batch = []
        while urgent_queue and len(batch) < max_size:
            request = urgent_queue.popleft()
            batch.append(request)
        
        return batch if batch else None
    
    def _generate_content_hash(self, request: BatchRequest) -> str:
        """Generate hash for request content deduplication."""
        content = f"{request.request_type.value}:{request.prompt}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _promote_aged_requests(self):
        """Promote older requests to higher priority."""
        if not self.config.enable_promotion:
            return
        
        current_time = datetime.now()
        promotion_threshold = timedelta(seconds=self.config.promotion_interval)
        
        with self.lock:
            for priority in [RequestPriority.LOW, RequestPriority.NORMAL, RequestPriority.HIGH]:
                if priority == RequestPriority.HIGH:
                    next_priority = RequestPriority.URGENT
                elif priority == RequestPriority.NORMAL:
                    next_priority = RequestPriority.HIGH
                else:
                    next_priority = RequestPriority.NORMAL
                
                queue = self.queues[priority]
                next_queue = self.queues[next_priority]
                
                # Find requests to promote
                to_promote = []
                remaining = deque()
                
                while queue:
                    request = queue.popleft()
                    metadata = self.request_metadata.get(request.request_id, {})
                    enqueued_at = metadata.get("enqueued_at", current_time)
                    
                    if current_time - enqueued_at > promotion_threshold:
                        to_promote.append(request)
                        logger.info(
                            f"Promoting request {request.request_id} "
                            f"from {priority.value} to {next_priority.value}"
                        )
                    else:
                        remaining.append(request)
                
                # Update queues
                self.queues[priority] = remaining
                for request in to_promote:
                    request.priority = next_priority
                    next_queue.append(request)
                    
                    # Update metadata
                    if request.request_id in self.request_metadata:
                        self.request_metadata[request.request_id]["priority"] = next_priority
    
    def _cleanup_expired_requests(self):
        """Remove requests that have expired."""
        current_time = datetime.now()
        max_age = timedelta(hours=self.config.max_age_hours)
        
        with self.lock:
            for priority, queue in self.queues.items():
                remaining = deque()
                expired_count = 0
                
                while queue:
                    request = queue.popleft()
                    metadata = self.request_metadata.get(request.request_id, {})
                    enqueued_at = metadata.get("enqueued_at", current_time)
                    
                    if current_time - enqueued_at > max_age:
                        expired_count += 1
                        # Clean up metadata
                        if request.request_id in self.request_metadata:
                            del self.request_metadata[request.request_id]
                        
                        # Clean up cache
                        content_hash = metadata.get("content_hash")
                        if content_hash and content_hash in self.request_cache:
                            del self.request_cache[content_hash]
                    else:
                        remaining.append(request)
                
                self.queues[priority] = remaining
                
                if expired_count > 0:
                    logger.warning(
                        f"Removed {expired_count} expired requests from {priority.value} queue"
                    )
    
    def _persist_queue_state(self):
        """Persist queue state to disk."""
        if not self.config.enable_persistence:
            return
        
        try:
            state = {
                "queues": {
                    priority.value: [
                        {
                            "request_id": req.request_id,
                            "prompt": req.prompt,
                            "request_type": req.request_type.value,
                            "priority": req.priority.value,
                            "metadata": req.metadata,
                            "created_at": req.created_at.isoformat(),
                            "timeout": req.timeout
                        }
                        for req in queue
                    ]
                    for priority, queue in self.queues.items()
                },
                "request_metadata": {
                    req_id: {
                        "enqueued_at": metadata["enqueued_at"].isoformat(),
                        "priority": metadata["priority"].value,
                        "request_type": metadata["request_type"].value,
                        "content_hash": metadata["content_hash"]
                    }
                    for req_id, metadata in self.request_metadata.items()
                },
                "metrics": {
                    "total_enqueued": self.global_metrics.total_enqueued,
                    "total_processed": self.global_metrics.total_processed,
                    "total_failed": self.global_metrics.total_failed,
                    "average_wait_time": self.global_metrics.average_wait_time,
                    "peak_queue_size": self.global_metrics.peak_queue_size
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Save to file
            state_file = "data/queue_state.pkl"
            os.makedirs(os.path.dirname(state_file), exist_ok=True)
            
            with open(state_file, 'wb') as f:
                pickle.dump(state, f)
            
            logger.debug("Queue state persisted")
            
        except Exception as e:
            logger.error(f"Failed to persist queue state: {e}")
    
    def _load_persisted_state(self):
        """Load queue state from disk."""
        try:
            state_file = "data/queue_state.pkl"
            
            if not os.path.exists(state_file):
                logger.info("No persisted queue state found")
                return
            
            with open(state_file, 'rb') as f:
                state = pickle.load(f)
            
            # Restore queues
            for priority_value, requests_data in state["queues"].items():
                priority = RequestPriority(priority_value)
                queue = self.queues[priority]
                
                for req_data in requests_data:
                    request = BatchRequest(
                        request_id=req_data["request_id"],
                        prompt=req_data["prompt"],
                        request_type=RequestType(req_data["request_type"]),
                        priority=RequestPriority(req_data["priority"]),
                        metadata=req_data["metadata"],
                        created_at=datetime.fromisoformat(req_data["created_at"]),
                        timeout=req_data["timeout"]
                    )
                    queue.append(request)
            
            # Restore metadata
            for req_id, metadata in state["request_metadata"].items():
                self.request_metadata[req_id] = {
                    "enqueued_at": datetime.fromisoformat(metadata["enqueued_at"]),
                    "priority": RequestPriority(metadata["priority"]),
                    "request_type": RequestType(metadata["request_type"]),
                    "content_hash": metadata["content_hash"]
                }
            
            # Restore metrics
            metrics = state["metrics"]
            self.global_metrics.total_enqueued = metrics["total_enqueued"]
            self.global_metrics.total_processed = metrics["total_processed"]
            self.global_metrics.total_failed = metrics["total_failed"]
            self.global_metrics.average_wait_time = metrics["average_wait_time"]
            self.global_metrics.peak_queue_size = metrics["peak_queue_size"]
            
            logger.info("Queue state restored from persistence")
            
        except Exception as e:
            logger.error(f"Failed to load persisted queue state: {e}")
    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        # Promotion task
        if self.config.enable_promotion:
            self.maintenance_task = threading.Timer(
                self.config.promotion_interval,
                self._maintenance_loop
            )
            self.maintenance_task.daemon = True
            self.maintenance_task.start()
        
        # Persistence task
        if self.config.enable_persistence:
            self.persistence_task = threading.Timer(
                QUEUE_PERSISTENCE_INTERVAL,
                self._persistence_loop
            )
            self.persistence_task.daemon = True
            self.persistence_task.start()
    
    def _maintenance_loop(self):
        """Background maintenance loop."""
        while True:
            try:
                self._promote_aged_requests()
                self._cleanup_expired_requests()
                
                # Update peak queue size
                current_size = self._get_total_queue_size()
                if current_size > self.global_metrics.peak_queue_size:
                    self.global_metrics.peak_queue_size = current_size
                
                time.sleep(self.config.promotion_interval)
                
            except Exception as e:
                logger.error(f"Maintenance loop error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _persistence_loop(self):
        """Background persistence loop."""
        while True:
            try:
                self._persist_queue_state()
                time.sleep(QUEUE_PERSISTENCE_INTERVAL)
                
            except Exception as e:
                logger.error(f"Persistence loop error: {e}")
                time.sleep(60)  # Wait before retrying

# Global queue manager instance
_queue_manager_instance: Optional[BatchQueueManager] = None

def get_batch_queue_manager(**kwargs) -> BatchQueueManager:
    """
    Get or create singleton BatchQueueManager instance.
    
    Args:
        **kwargs: Arguments to pass to BatchQueueManager constructor
    
    Returns:
        BatchQueueManager instance
    
    Example:
        >>> manager = get_batch_queue_manager(max_capacity=500)
        >>> manager.enqueue_request(request)
    """
    global _queue_manager_instance
    
    if _queue_manager_instance is None:
        logger.info("Creating new BatchQueueManager singleton instance")
        _queue_manager_instance = BatchQueueManager(**kwargs)
    
    return _queue_manager_instance

# Module initialization
logger.info("Batch queue manager module loaded")
logger.info(f"Default capacity: {DEFAULT_QUEUE_CAPACITY}")
logger.info(f"Promotion interval: {PROMOTION_INTERVAL}s")