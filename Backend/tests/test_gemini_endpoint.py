#!/usr/bin/env python3
"""
Test script to verify Gemini endpoint functionality.

This script tests:
1. Direct Gemini client initialization and content generation
2. Gemini service question generation
3. API endpoint that uses Gemini (if available)

Usage:
    python test_gemini_endpoint.py
"""

import os
import sys
import logging
import traceback
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def test_gemini_client():
    """Test direct Gemini client functionality."""
    print("\n" + "="*80)
    print("TEST 1: Direct Gemini Client Test")
    print("="*80)
    
    try:
        from utils.gemini_client import GeminiClient, get_gemini_client
        
        # Test client initialization
        print("Initializing Gemini client...")
        client = get_gemini_client()
        print("✅ Gemini client initialized successfully")
        
        # Test content generation
        print("\nTesting content generation...")
        test_prompt = "Explain the concept of photosynthesis in 2-3 sentences."
        response = client.generate_content(test_prompt)
        
        if response and len(response.strip()) > 0:
            print(f"✅ Content generation successful")
            print(f"Response length: {len(response)} characters")
            print(f"Response preview: {response[:200]}...")
            return True
        else:
            print("❌ Content generation failed: Empty response")
            return False
            
    except Exception as e:
        print(f"❌ Gemini client test failed: {e}")
        logger.exception("Gemini client test error")
        return False

def test_gemini_service():
    """Test Gemini service functionality."""
    print("\n" + "="*80)
    print("TEST 2: Gemini Service Test")
    print("="*80)
    
    try:
        from services.gemini_service import GeminiService, get_gemini_service
        
        # Test service initialization
        print("Initializing Gemini service...")
        service = get_gemini_service()
        print("✅ Gemini service initialized successfully")
        
        # Test content generation
        print("\nTesting content generation...")
        test_prompt = "Create a simple physics question about momentum."
        content = service.generate_content(test_prompt)
        
        if content and len(content.strip()) > 0:
            print(f"✅ Content generation successful")
            print(f"Content length: {len(content)} characters")
            print(f"Content preview: {content[:200]}...")
        else:
            print("⚠️ Content generation returned empty result")
        
        # Test question generation
        print("\nTesting question generation...")
        question_prompt = """
        Generate 2 multiple choice questions about Newton's laws of motion.
        Each question should have:
        - A clear question statement
        - 4 options (A, B, C, D)
        - The correct answer indicated
        
        Format as JSON array:
        [
            {
                "question": "[Question text]",
                "options": {
                    "A": "[Option A]",
                    "B": "[Option B]",
                    "C": "[Option C]",
                    "D": "[Option D]"
                },
                "correct_answer": "[A/B/C/D]",
                "explanation": "[Detailed explanation]",
                "difficulty": "easy",
                "topic": "Newton's Laws of Motion",
                "exam_type": "JEE_MAIN",
                "subject": "Physics"
            }
        ]
        """
        
        # First, let's test what the raw response looks like
        print("Testing raw Gemini response...")
        from utils.gemini_client import get_gemini_client
        client = get_gemini_client()
        raw_response = client.generate_content(question_prompt)
        print(f"Raw response length: {len(raw_response)} characters")
        print(f"Raw response preview:\n{raw_response[:500]}...")
        print("="*50)
        
        questions = service.generate_questions(question_prompt, num_questions=2)
        
        if questions and len(questions) > 0:
            print(f"✅ Question generation successful")
            print(f"Generated {len(questions)} questions")
            for i, q in enumerate(questions[:2]):
                print(f"  Question {i+1}: {q.question[:100]}...")
        else:
            print("❌ Question generation failed: No questions returned")
            return False
        
        # Get usage stats
        stats = service.get_usage_stats()
        print(f"\n📊 Usage Statistics:")
        print(f"  Total API calls: {stats['total_calls']}")
        print(f"  Successful calls: {stats['successful_calls']}")
        print(f"  Failed calls: {stats['failed_calls']}")
        print(f"  Total cost: ${stats['total_cost']:.6f}")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Cache misses: {stats['cache_misses']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini service test failed: {e}")
        logger.exception("Gemini service test error")
        return False

def test_api_endpoint():
    """Test API endpoint that uses Gemini."""
    print("\n" + "="*80)
    print("TEST 3: API Endpoint Test")
    print("="*80)
    
    try:
        import requests
        import json
        
        # Check if server is running
        base_url = "http://localhost:8000"
        
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ Server not responding correctly at {base_url}")
                print("Please ensure the FastAPI server is running: python main.py")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server at {base_url}: {e}")
            print("Please ensure the FastAPI server is running: python main.py")
            return False
        
        print("✅ Server is running")
        
        # Test RAG endpoint (question generation)
        print("\nTesting RAG question generation endpoint...")
        rag_payload = {
            "exam_type": "JEE_MAIN",
            "subject": "Physics",
            "topic": "Newton's Laws of Motion",
            "difficulty": "medium",
            "num_questions": 2
        }
        
        try:
            response = requests.post(
                f"{base_url}/api/rag/generate-questions",
                json=rag_payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("questions"):
                    questions = data["questions"]
                    print(f"✅ RAG endpoint successful")
                    print(f"Generated {len(questions)} questions")
                    for i, q in enumerate(questions[:2]):
                        print(f"  Question {i+1}: {q.get('question', 'N/A')[:100]}...")
                    return True
                else:
                    print(f"❌ RAG endpoint returned no questions")
                    print(f"Response: {json.dumps(data, indent=2)}")
                    return False
            else:
                print(f"❌ RAG endpoint failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ RAG endpoint request failed: {e}")
            return False
        
    except ImportError:
        print("⚠️ Skipping API endpoint test - requests module not available")
        print("Install with: pip install requests")
        return None
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        logger.exception("API endpoint test error")
        return False

def check_environment():
    """Check if required environment variables are set."""
    print("\n" + "="*80)
    print("ENVIRONMENT CHECK")
    print("="*80)
    
    # Check .env file
    env_file = ".env"
    if os.path.exists(env_file):
        print(f"✅ .env file found")
    else:
        print(f"❌ .env file not found")
        return False
    
    # Load and check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        print(f"✅ GOOGLE_API_KEY is set (length: {len(google_api_key)})")
        if google_api_key.startswith("AIza"):
            print("✅ API key format looks correct")
        else:
            print("⚠️ API key format might be incorrect")
    else:
        print("❌ GOOGLE_API_KEY is not set")
        return False
    
    return True

def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("GEMINI ENDPOINT FUNCTIONALITY TEST")
    print("="*80)
    
    # Track test results
    results = {
        "environment": False,
        "gemini_client": False,
        "gemini_service": False,
        "api_endpoint": False
    }
    
    # Check environment
    results["environment"] = check_environment()
    if not results["environment"]:
        print("\n❌ Environment check failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    # Run tests
    results["gemini_client"] = test_gemini_client()
    results["gemini_service"] = test_gemini_service()
    api_result = test_api_endpoint()
    if api_result is not None:
        results["api_endpoint"] = api_result
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL" if result is False else "⚠️ SKIP"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    # Overall result
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    
    if failed == 0:
        print("\n🎉 All tests passed! Gemini endpoint is working correctly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())