#!/usr/bin/env python3
"""
Simple test script for batch API functionality
"""

import asyncio
import logging
from services.gemini_batch_service import GeminiBatchService, BatchRequest, RequestType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_batch_basic():
    """Test basic batch functionality."""
    print("Testing basic batch functionality...")
    
    try:
        # Create batch service
        service = GeminiBatchService(batch_size=3, auto_flush=False)
        
        # Add test requests
        for i in range(3):
            request = BatchRequest(
                request_id=f"test_{i}",
                prompt=f"Generate question {i}",
                request_type=RequestType.QUESTION_GENERATION
            )
            service.add_request(request)
            print(f"Added request {i} to queue")
        
        # Get queue status
        status = service.get_queue_status()
        print(f"Queue status: {status}")
        
        # Process batch
        print("Processing batch...")
        result = await service.process_batch(force_flush=True)
        
        if result:
            print(f"✓ Batch processed: {len(result.requests_processed)} requests")
            print(f"✓ Cost savings: ${result.cost_savings:.4f}")
            print(f"✓ Success: {result.success}")
            
            # Get cost savings
            savings = service.get_cost_savings()
            print(f"✓ Total savings: ${savings['total_cost_savings']:.4f}")
        else:
            print("✗ No batch processed")
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()

async def test_enhanced_service():
    """Test enhanced service."""
    print("\nTesting enhanced service...")
    
    try:
        from services.enhanced_gemini_service import EnhancedGeminiService
        
        # Create enhanced service
        service = EnhancedGeminiService(batch_enabled=True)
        
        # Test cost tracking
        savings = service.get_cost_savings()
        print(f"✓ Initial cost savings: {savings}")
        
        # Test service status
        status = service.get_service_status()
        print(f"✓ Service status: {status.get('service_type', 'Unknown')}")
        print(f"✓ Batch enabled: {status.get('batch_enabled', False)}")
        
    except Exception as e:
        print(f"✗ Enhanced service test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("=== Batch API Simple Test ===\n")
    
    await test_batch_basic()
    await test_enhanced_service()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(main())