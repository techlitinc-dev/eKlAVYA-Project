"""
Test Suite for Gemini Batch API - Mentor AI Platform

This module provides comprehensive testing for the Gemini batch processing
implementation, including unit tests, integration tests, and performance tests.

Features:
- Unit tests for all batch components
- Integration tests for end-to-end workflows
- Performance benchmarks and load testing
- Cost savings validation
- Error handling and edge case testing
- Configuration testing
- Monitoring and analytics validation

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> python -m pytest tests/test_batch_api.py -v
    >>> 
    >>> # Run specific test categories
    >>> python -m pytest tests/test_batch_api.py::TestBatchService -v
    >>> 
    >>> # Run performance tests
    >>> python -m pytest tests/test_batch_api.py::TestPerformance -v -s
"""

import os
import sys
import time
import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.gemini_batch_service import (
    GeminiBatchService, 
    BatchRequest, 
    RequestType, 
    RequestPriority,
    get_gemini_batch_service
)
from services.batch_queue_manager import (
    BatchQueueManager, 
    QueueConfig, 
    get_batch_queue_manager
)
from services.batch_monitor_service import (
    BatchMonitorService, 
    AlertLevel, 
    MetricType,
    get_batch_monitor_service
)
from services.enhanced_gemini_service import (
    EnhancedGeminiService,
    create_enhanced_gemini_service
)
from config.batch_config import (
    BatchConfigManager,
    OptimizationStrategy,
    get_batch_config
)

# Test configuration
TEST_API_KEY = "test_api_key_12345"
TEST_BATCH_SIZE = 3
TEST_TIMEOUT = 30

class MockGeminiClient:
    """Mock Gemini client for testing."""
    
    def __init__(self, *args, **kwargs):
        self.call_count = 0
        self.responses = {}
        self.delays = []
    
    def generate_content(self, prompt: str, **kwargs):
        """Mock generate content with configurable delays."""
        self.call_count += 1
        
        # Add delay if configured
        if self.delays:
            delay = self.delays[min(self.call_count - 1, len(self.delays) - 1)]
            time.sleep(delay)
        
        # Generate mock response based on prompt content
        if "QUESTION_" in prompt:
            return self._generate_question_response(prompt)
        elif "ANALYTICS_" in prompt:
            return self._generate_analytics_response(prompt)
        elif "SCHEDULE_" in prompt:
            return self._generate_schedule_response(prompt)
        else:
            return "Mock response for generic prompt"
    
    def _generate_question_response(self, prompt: str) -> str:
        """Generate mock question response."""
        responses = []
        
        # Extract request IDs from prompt
        import re
        request_ids = re.findall(r'REQUEST_(\d+):', prompt)
        
        for req_id in request_ids:
            response = f"""REQUEST_{req_id}_RESPONSE: [
    {{
        "question": "Mock question {req_id}",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "explanation": "Mock explanation {req_id}",
        "topic": "Mock topic {req_id}",
        "difficulty": "medium"
    }}
]"""
            responses.append(response)
        
        return "\n\n".join(responses)
    
    def _generate_analytics_response(self, prompt: str) -> str:
        """Generate mock analytics response."""
        responses = []
        
        import re
        request_ids = re.findall(r'ANALYTICS_(\d+):', prompt)
        
        for req_id in request_ids:
            response = f"""ANALYTICS_{req_id}_INSIGHTS: {{
    "strengths": ["Mock strength {req_id}"],
    "weaknesses": ["Mock weakness {req_id}"],
    "learning_patterns": ["Mock pattern {req_id}"],
    "overall_assessment": "Mock assessment {req_id}",
    "study_strategy": "Mock strategy {req_id}"
}}"""
            responses.append(response)
        
        return "\n\n".join(responses)
    
    def _generate_schedule_response(self, prompt: str) -> str:
        """Generate mock schedule response."""
        responses = []
        
        import re
        request_ids = re.findall(r'SCHEDULE_(\d+):', prompt)
        
        for req_id in request_ids:
            response = f"""SCHEDULE_{req_id}_SCHEDULE: {{
    "daily_schedule": [
        {{
            "day_number": 1,
            "topics": [
                {{
                    "topic": "Mock topic {req_id}",
                    "subject": "Physics",
                    "priority": "high",
                    "estimated_hours": 2.0
                }}
            ],
            "total_hours": 6.0
        }}
    ],
    "schedule_metadata": {{
        "total_days": 30,
        "created_by": "AI_Scheduler"
    }}
}}"""
            responses.append(response)
        
        return "\n\n".join(responses)

class TestBatchService:
    """Test cases for GeminiBatchService."""
    
    @pytest.fixture
    def batch_service(self):
        """Create test batch service."""
        mock_client = MockGeminiClient()
        service = GeminiBatchService(
            gemini_client=mock_client,
            batch_size=TEST_BATCH_SIZE,
            batch_timeout=TEST_TIMEOUT,
            auto_flush=False
        )
        return service
    
    def test_batch_service_initialization(self, batch_service):
        """Test batch service initialization."""
        assert batch_service.batch_size == TEST_BATCH_SIZE
        assert batch_service.batch_timeout == TEST_TIMEOUT
        assert not batch_service.auto_flush_enabled
        assert batch_service.queue is not None
        assert batch_service.cost_tracker is not None
    
    def test_add_request(self, batch_service):
        """Test adding requests to batch."""
        request = BatchRequest(
            request_id="test_req_1",
            prompt="Generate 5 physics questions",
            request_type=RequestType.QUESTION_GENERATION,
            priority=RequestPriority.NORMAL
        )
        
        request_id = batch_service.add_request(request)
        assert request_id == "test_req_1"
        assert batch_service.queue.size() == 1
    
    def test_batch_processing(self, batch_service):
        """Test batch processing."""
        # Add multiple requests
        requests = [
            BatchRequest(
                request_id=f"test_req_{i}",
                prompt=f"Generate {i+1} questions",
                request_type=RequestType.QUESTION_GENERATION,
                priority=RequestPriority.NORMAL
            )
            for i in range(TEST_BATCH_SIZE)
        ]
        
        for request in requests:
            batch_service.add_request(request)
        
        # Process batch
        import asyncio
        result = asyncio.run(batch_service.process_batch(force_flush=True))
        
        assert result is not None
        assert result.success
        assert len(result.requests_processed) == TEST_BATCH_SIZE
        assert result.cost_savings > 0
    
    def test_cost_calculation(self, batch_service):
        """Test cost calculation and savings."""
        request = BatchRequest(
            request_id="cost_test",
            prompt="Generate questions for cost testing",
            request_type=RequestType.QUESTION_GENERATION
        )
        
        # Add and process
        batch_service.add_request(request)
        result = asyncio.run(batch_service.process_batch(force_flush=True))
        
        assert result is not None
        assert result.cost_individual > 0
        assert result.cost_batch > 0
        assert result.cost_savings >= 0
    
    def test_request_prioritization(self, batch_service):
        """Test request prioritization."""
        # Add requests with different priorities
        priorities = [
            RequestPriority.LOW,
            RequestPriority.URGENT,
            RequestPriority.HIGH,
            RequestPriority.NORMAL
        ]
        
        for i, priority in enumerate(priorities):
            request = BatchRequest(
                request_id=f"priority_test_{i}",
                prompt=f"Test request {i}",
                request_type=RequestType.QUESTION_GENERATION,
                priority=priority
            )
            batch_service.add_request(request)
        
        # Process batch - urgent should come first
        result = asyncio.run(batch_service.process_batch(force_flush=True))
        
        assert result is not None
        assert len(result.requests_processed) > 0

class TestQueueManager:
    """Test cases for BatchQueueManager."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create test queue manager."""
        config = QueueConfig(
            max_capacity=100,
            enable_persistence=False,  # Disable for testing
            enable_promotion=False
        )
        return BatchQueueManager(config)
    
    def test_queue_manager_initialization(self, queue_manager):
        """Test queue manager initialization."""
        assert queue_manager.config.max_capacity == 100
        assert not queue_manager.config.enable_persistence
        assert queue_manager.status.value == "active"
    
    def test_enqueue_request(self, queue_manager):
        """Test enqueuing requests."""
        request = BatchRequest(
            request_id="queue_test_1",
            prompt="Test queue request",
            request_type=RequestType.QUESTION_GENERATION
        )
        
        success = queue_manager.enqueue_request(request)
        assert success
        assert queue_manager.get_queue_status()["total_requests"] == 1
    
    def test_queue_capacity_limit(self, queue_manager):
        """Test queue capacity limits."""
        # Fill queue to capacity
        for i in range(queue_manager.config.max_capacity):
            request = BatchRequest(
                request_id=f"capacity_test_{i}",
                prompt=f"Test request {i}",
                request_type=RequestType.QUESTION_GENERATION
            )
            queue_manager.enqueue_request(request)
        
        # Try to add one more
        overflow_request = BatchRequest(
            request_id="overflow_request",
            prompt="This should be rejected",
            request_type=RequestType.QUESTION_GENERATION
        )
        
        success = queue_manager.enqueue_request(overflow_request)
        assert not success
    
    def test_batch_creation(self, queue_manager):
        """Test batch creation from queue."""
        # Add requests
        for i in range(5):
            request = BatchRequest(
                request_id=f"batch_test_{i}",
                prompt=f"Test request {i}",
                request_type=RequestType.QUESTION_GENERATION
            )
            queue_manager.enqueue_request(request)
        
        # Get ready batches
        batches = queue_manager.get_ready_batches(max_batch_size=3)
        
        assert len(batches) >= 1
        assert len(batches[0]) <= 3

class TestMonitorService:
    """Test cases for BatchMonitorService."""
    
    @pytest.fixture
    def monitor_service(self):
        """Create test monitor service."""
        return BatchMonitorService(
            retention_hours=1,  # Short retention for testing
            alert_thresholds={
                "cost_per_hour": 5.0,
                "batch_failure_rate": 0.2,
                "average_wait_time": 100
            }
        )
    
    def test_monitor_initialization(self, monitor_service):
        """Test monitor service initialization."""
        assert monitor_service.retention_hours == 1
        assert monitor_service.thresholds["cost_per_hour"] == 5.0
        assert monitor_service.real_time_metrics is not None
    
    def test_batch_tracking(self, monitor_service):
        """Test batch result tracking."""
        from services.gemini_batch_service import BatchResult
        
        # Create mock batch result
        batch_result = BatchResult(
            batch_id="test_batch",
            requests_processed=["req1", "req2"],
            results={"req1": {"success": True}, "req2": {"success": True}},
            cost_individual=0.10,
            cost_batch=0.06,
            cost_savings=0.04,
            processing_time=2.5,
            tokens_saved=100,
            success=True
        )
        
        # Track batch
        monitor_service.track_batch_processing(batch_result)
        
        # Check metrics
        dashboard = monitor_service.get_real_time_dashboard()
        assert dashboard["real_time_metrics"]["current_cost_savings"] == 0.04
        assert dashboard["real_time_metrics"]["current_batch_size"] == 2
    
    def test_alert_creation(self, monitor_service):
        """Test alert creation and management."""
        # Create alert
        alert = monitor_service.create_alert(
            AlertLevel.WARNING,
            MetricType.COST,
            "Test cost alert",
            15.0,
            10.0
        )
        
        assert alert.level == AlertLevel.WARNING
        assert alert.metric_type == MetricType.COST
        assert alert.value == 15.0
        assert alert.threshold == 10.0
        
        # Check active alerts
        alerts = monitor_service.get_alerts(level=AlertLevel.WARNING)
        assert len(alerts) >= 1
    
    def test_cost_analytics(self, monitor_service):
        """Test cost analytics generation."""
        from services.gemini_batch_service import BatchResult
        
        # Add some test data
        for i in range(3):
            batch_result = BatchResult(
                batch_id=f"test_batch_{i}",
                requests_processed=[f"req{i}"],
                results={f"req{i}": {"success": True}},
                cost_individual=0.10,
                cost_batch=0.06,
                cost_savings=0.04,
                processing_time=2.0,
                tokens_saved=100,
                success=True
            )
            monitor_service.track_batch_processing(batch_result)
        
        # Get analytics
        analytics = monitor_service.get_cost_analytics(time_window_hours=1)
        
        assert analytics.total_cost_savings == 0.12  # 3 * 0.04
        assert analytics.savings_percentage > 0

class TestConfiguration:
    """Test cases for batch configuration."""
    
    @pytest.fixture
    def config_manager(self):
        """Create test config manager."""
        return BatchConfigManager(
            config_file="test_config.json",
            auto_reload=False
        )
    
    def test_config_loading(self, config_manager):
        """Test configuration loading."""
        config = config_manager.get_config()
        assert config is not None
        assert hasattr(config, 'batch_size')
        assert hasattr(config, 'batch_timeout')
    
    def test_optimal_batch_size(self, config_manager):
        """Test optimal batch size calculation."""
        # Test different strategies
        cost_optimal = config_manager.get_optimal_batch_size(
            RequestType.QUESTION_GENERATION,
            current_load=0.5,
            strategy=OptimizationStrategy.COST_OPTIMIZED
        )
        
        latency_optimal = config_manager.get_optimal_batch_size(
            RequestType.QUESTION_GENERATION,
            current_load=0.5,
            strategy=OptimizationStrategy.LATENCY_OPTIMIZED
        )
        
        # Cost-optimized should have larger batch size
        assert cost_optimal >= latency_optimal
    
    def test_configuration_validation(self, config_manager):
        """Test configuration validation."""
        # Get valid config
        config = config_manager.get_config()
        errors = config_manager.validate_configuration()
        
        # Should be valid
        assert len(errors) == 0
        
        # Test invalid config
        config.batch_size = -1
        errors = config_manager.validate_configuration()
        assert len(errors) > 0

class TestEnhancedService:
    """Test cases for EnhancedGeminiService."""
    
    @pytest.fixture
    def enhanced_service(self):
        """Create test enhanced service."""
        mock_client = MockGeminiClient()
        
        with patch('services.enhanced_gemini_service.get_gemini_batch_service') as mock_batch:
            with patch('services.enhanced_gemini_service.get_batch_queue_manager') as mock_queue:
                with patch('services.enhanced_gemini_service.get_batch_monitor_service') as mock_monitor:
                    enhanced_service = EnhancedGeminiService(
                        batch_enabled=True,
                        auto_batch_threshold=2,
                        gemini_client=mock_client
                    )
                    return enhanced_service
    
    def test_enhanced_service_initialization(self, enhanced_service):
        """Test enhanced service initialization."""
        assert enhanced_service.batch_enabled == True
        assert enhanced_service.auto_batch_threshold == 2
        assert enhanced_service.cost_analysis is not None
    
    def test_batch_decision_logic(self, enhanced_service):
        """Test batch vs individual decision logic."""
        # Test request that should be batched
        should_batch, priority = enhanced_service._analyze_request_for_batching(
            "Generate 10 questions", 10
        )
        assert should_batch == True
        
        # Test request that should be individual
        should_batch, priority = enhanced_service._analyze_request_for_batching(
            "Generate 1 question", 1
        )
        assert should_batch == False
    
    def test_cost_tracking(self, enhanced_service):
        """Test cost tracking in enhanced service."""
        # Generate questions (should use batch)
        questions = enhanced_service.generate_questions(
            "Generate 5 physics questions",
            5,
            force_individual=False
        )
        
        assert len(questions) > 0
        
        # Check cost analysis
        savings = enhanced_service.get_cost_savings()
        assert "total_savings" in savings
        assert "batch_efficiency" in savings

class TestPerformance:
    """Performance tests for batch processing."""
    
    @pytest.fixture
    def performance_service(self):
        """Create service for performance testing."""
        mock_client = MockGeminiClient()
        # Add delays to simulate real API
        mock_client.delays = [0.1, 0.2, 0.15]  # Simulate varying response times
        
        return GeminiBatchService(
            gemini_client=mock_client,
            batch_size=10,
            auto_flush=False
        )
    
    def test_batch_throughput(self, performance_service):
        """Test batch processing throughput."""
        num_requests = 50
        start_time = time.time()
        
        # Add requests
        for i in range(num_requests):
            request = BatchRequest(
                request_id=f"perf_test_{i}",
                prompt=f"Performance test request {i}",
                request_type=RequestType.QUESTION_GENERATION
            )
            performance_service.add_request(request)
        
        # Process all batches
        total_processed = 0
        while total_processed < num_requests:
            result = asyncio.run(performance_service.process_batch(force_flush=True))
            if result:
                total_processed += len(result.requests_processed)
            else:
                break
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput
        throughput = total_processed / total_time
        
        assert throughput > 5  # Should process at least 5 requests per second
        assert total_processed == num_requests
    
    def test_cost_savings_validation(self, performance_service):
        """Test that cost savings are actually achieved."""
        # Process batches and compare costs
        individual_costs = []
        batch_costs = []
        
        for i in range(10):
            # Add requests
            for j in range(5):
                request = BatchRequest(
                    request_id=f"cost_test_{i}_{j}",
                    prompt=f"Cost test request {i}_{j}",
                    request_type=RequestType.QUESTION_GENERATION
                )
                performance_service.add_request(request)
            
            # Process batch
            result = asyncio.run(performance_service.process_batch(force_flush=True))
            
            if result:
                individual_costs.append(result.cost_individual)
                batch_costs.append(result.cost_batch)
        
        # Calculate total costs
        total_individual = sum(individual_costs)
        total_batch = sum(batch_costs)
        
        # Should have cost savings
        savings = total_individual - total_batch
        assert savings > 0
        assert (savings / total_individual) > 0.1  # At least 10% savings

class TestIntegration:
    """Integration tests for end-to-end workflows."""
    
    def test_end_to_end_batch_workflow(self):
        """Test complete batch processing workflow."""
        # Create services
        mock_client = MockGeminiClient()
        batch_service = GeminiBatchService(gemini_client=mock_client)
        queue_manager = BatchQueueManager(
            QueueConfig(enable_persistence=False, enable_promotion=False)
        )
        monitor_service = BatchMonitorService(retention_hours=1)
        
        # Create enhanced service
        with patch('services.enhanced_gemini_service.get_gemini_batch_service', return_value=batch_service):
            with patch('services.enhanced_gemini_service.get_batch_queue_manager', return_value=queue_manager):
                with patch('services.enhanced_gemini_service.get_batch_monitor_service', return_value=monitor_service):
                    enhanced_service = EnhancedGeminiService(batch_enabled=True)
                    
                    # Generate questions (should use batch)
                    questions = enhanced_service.generate_questions(
                        "Generate 5 physics questions about motion",
                        5
                    )
                    
                    # Verify results
                    assert len(questions) > 0
                    
                    # Check cost savings
                    savings = enhanced_service.get_cost_savings()
                    assert savings["total_savings"] >= 0
                    
                    # Check monitoring
                    dashboard = monitor_service.get_real_time_dashboard()
                    assert dashboard["aggregated_metrics"]["total_requests"] > 0
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        # Create service with failing client
        class FailingGeminiClient:
            def __init__(self):
                self.call_count = 0
            
            def generate_content(self, prompt, **kwargs):
                self.call_count += 1
                if self.call_count <= 2:
                    raise Exception("Simulated API failure")
                return "Success after failures"
        
        failing_client = FailingGeminiClient()
        batch_service = GeminiBatchService(
            gemini_client=failing_client,
            batch_size=2
        )
        
        # Add requests
        for i in range(4):
            request = BatchRequest(
                request_id=f"error_test_{i}",
                prompt=f"Error test request {i}",
                request_type=RequestType.QUESTION_GENERATION
            )
            batch_service.add_request(request)
        
        # Process batch (should handle failures)
        result = asyncio.run(batch_service.process_batch(force_flush=True))
        
        # Should eventually succeed
        assert result is not None
        assert failing_client.call_count > 2  # Should have retried

# Test utilities
def create_test_batch_requests(count: int, request_type: RequestType = RequestType.QUESTION_GENERATION) -> List[BatchRequest]:
    """Create test batch requests."""
    return [
        BatchRequest(
            request_id=f"test_req_{i}",
            prompt=f"Test request {i}",
            request_type=request_type,
            priority=RequestPriority.NORMAL
        )
        for i in range(count)
]

def assert_cost_savings_valid(savings: Dict[str, Any]):
    """Assert that cost savings are valid."""
    assert "total_savings" in savings
    assert "savings_percentage" in savings
    assert savings["total_savings"] >= 0
    assert 0 <= savings["savings_percentage"] <= 100

def assert_batch_result_valid(result):
    """Assert that batch result is valid."""
    assert result is not None
    assert hasattr(result, 'requests_processed')
    assert hasattr(result, 'cost_savings')
    assert hasattr(result, 'processing_time')
    assert len(result.requests_processed) > 0

# Performance benchmark
def run_performance_benchmark():
    """Run comprehensive performance benchmark."""
    print("Running performance benchmark...")
    
    # Test different batch sizes
    batch_sizes = [1, 3, 5, 10, 15]
    results = {}
    
    for batch_size in batch_sizes:
        print(f"\nTesting batch size: {batch_size}")
        
        mock_client = MockGeminiClient()
        batch_service = GeminiBatchService(
            gemini_client=mock_client,
            batch_size=batch_size,
            auto_flush=False
        )
        
        # Process 100 requests
        start_time = time.time()
        total_requests = 100
        
        for i in range(0, total_requests, batch_size):
            # Add batch
            requests = create_test_batch_requests(batch_size)
            for request in requests:
                batch_service.add_request(request)
            
            # Process batch
            result = asyncio.run(batch_service.process_batch(force_flush=True))
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Get metrics
        savings = batch_service.get_cost_savings()
        
        results[batch_size] = {
            "total_time": total_time,
            "throughput": total_requests / total_time,
            "cost_savings": savings["total_savings"],
            "savings_percentage": savings["savings_percentage"],
            "average_batch_efficiency": savings["batch_efficiency"]
        }
        
        print(f"  Time: {total_time:.2f}s")
        print(f"  Throughput: {results[batch_size]['throughput']:.2f} req/s")
        print(f"  Cost savings: ${results[batch_size]['cost_savings']:.4f}")
        print(f"  Savings %: {results[batch_size]['savings_percentage']:.1f}%")
    
    # Find optimal batch size
    optimal_size = max(results.keys(), key=lambda k: results[k]["cost_savings"])
    print(f"\nOptimal batch size: {optimal_size}")
    print(f"Maximum cost savings: ${results[optimal_size]['cost_savings']:.4f}")
    
    return results

if __name__ == "__main__":
    # Run performance benchmark
    run_performance_benchmark()