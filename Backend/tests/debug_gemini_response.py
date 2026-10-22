#!/usr/bin/env python3
"""
Debug script to see the raw Gemini response
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def debug_gemini_response():
    """Debug the raw Gemini response."""
    
    print("=" * 80)
    print("DEBUGGING GEMINI RESPONSE")
    print("=" * 80)
    
    try:
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        # Simple prompt to generate one question
        prompt = """You are an expert JEE Main question generator. Generate exactly 1 question about Newton's Laws of Motion.

Return ONLY a valid JSON array with this exact structure:
[
  {
    "question": "Question text here",
    "options": {
      "A": "Option A",
      "B": "Option B", 
      "C": "Option C",
      "D": "Option D"
    },
    "correct_answer": "A",
    "explanation": "Detailed explanation here",
    "difficulty": "medium",
    "topic": "Newton's Laws of Motion",
    "exam_type": "JEE_MAIN",
    "subject": "Physics",
    "question_type": "single_correct",
    "marks": 4,
    "estimated_time_minutes": 3
  }
]

Generate the question now:"""
        
        print("1. CALLING GEMINI DIRECTLY")
        print("-" * 40)
        print(f"Prompt length: {len(prompt)} characters")
        
        # Call Gemini client directly to get raw response
        response = gemini_service.client.generate_content(prompt)
        
        print("2. RAW GEMINI RESPONSE")
        print("-" * 40)
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(response)} characters")
        print("Raw response:")
        print(response)
        print("-" * 40)
        
        # Try to parse as JSON
        try:
            parsed = json.loads(response)
            print(f"JSON parsing successful: {type(parsed)}")
            
            if isinstance(parsed, dict):
                print("Response is a JSON object")
                print(f"Keys: {list(parsed.keys())}")
                
                # Check if it looks like a question wrapped in an object
                if 'question' in parsed:
                    print("✓ Looks like a single question object")
                    # Wrap in array
                    array_response = [parsed]
                    print(f"Wrapped in array: {json.dumps(array_response, indent=2)}")
                
            elif isinstance(parsed, list):
                print("Response is a JSON array")
                print(f"Array length: {len(parsed)}")
                
            else:
                print(f"Unexpected JSON type: {type(parsed)}")
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing failed: {e}")
            
            # Try to extract JSON from markdown
            if '```json' in response:
                print("Found JSON markdown block, attempting to extract...")
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    json_text = response[start:end].strip()
                    print(f"Extracted JSON: {json_text}")
                    
                    try:
                        parsed = json.loads(json_text)
                        print(f"Extracted JSON parsing successful: {type(parsed)}")
                    except json.JSONDecodeError as e2:
                        print(f"Extracted JSON parsing failed: {e2}")
        
        # Test response parser
        print("\n3. TESTING RESPONSE PARSER")
        print("-" * 40)
        
        from utils.response_parser import ResponseParser
        
        parser = ResponseParser(strict_mode=False, log_invalid=True)
        questions, stats = parser.parse_response(response)
        
        print(f"Parser extracted {len(questions)} questions")
        print(f"Parser stats: {stats}")
        
        # Test gemini_service.generate_questions method
        print("\n4. TESTING GEMINI SERVICE METHOD")
        print("-" * 40)
        
        questions = gemini_service.generate_questions(
            prompt=prompt,
            num_questions=1,
            use_cache=False,
            retry_on_insufficient=False
        )
        
        print(f"Gemini service returned {len(questions)} questions")
        
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    debug_gemini_response()