#!/usr/bin/env python3
"""
Simple test for RAG endpoint to debug timeout issue.
"""

import requests
import json
import time

def test_rag_endpoint():
    """Test RAG endpoint with simple request."""
    url = "http://localhost:8000/api/rag/generate-questions"
    
    payload = {
        "topic": "Newton's Laws of Motion",
        "exam_type": "JEE_MAIN", 
        "difficulty": "medium",
        "num_questions": 1,
        "include_explanations": True,
        "question_type": "single_correct",
        "use_cache": False
    }
    
    print(f"Sending request to {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 second timeout
        )
        
        elapsed = time.time() - start_time
        print(f"Request completed in {elapsed:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Generated {len(data.get('questions', []))} questions")
            print(f"Cache hit: {data.get('cache_hit', False)}")
        else:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("Request timed out!")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_rag_endpoint()