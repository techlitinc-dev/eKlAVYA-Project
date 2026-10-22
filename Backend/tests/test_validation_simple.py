#!/usr/bin/env python3
"""
Simple test to isolate validation issue
"""

import json
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_validation():
    """Test validation with a simple question."""
    
    print("=" * 60)
    print("SIMPLE VALIDATION TEST")
    print("=" * 60)
    
    # Create a simple question that should pass validation
    simple_question = {
        "question": "What is $2 + 2$?",
        "options": {
            "A": "3",
            "B": "4", 
            "C": "5",
            "D": "6"
        },
        "correct_answer": "B",
        "explanation": "Basic addition: 2 + 2 = 4",
        "difficulty": "easy",
        "topic": "Arithmetic",
        "exam_type": "JEE_MAIN",
        "subject": "Math",
        "question_type": "single_correct",
        "marks": 4,
        "estimated_time_minutes": 2
    }
    
    print("1. TESTING WITH SIMPLE QUESTION")
    print(f"Question: {json.dumps(simple_question, indent=2)}")
    
    # Test with validator
    from services.question_validator import QuestionValidator
    from models.question_models import Question
    
    validator = QuestionValidator(strict_mode=False, min_quality_score=50)
    result = validator.validate(Question(**simple_question), "Arithmetic")
    
    print(f"2. VALIDATION RESULT")
    print(f"   Is Valid: {result.is_valid}")
    print(f"   Quality Score: {result.quality_score}")
    print(f"   Issues: {result.issues}")
    print(f"   Warnings: {result.warnings}")
    
    # Test with response parser
    print("\n3. TESTING WITH RESPONSE PARSER")
    
    # Convert to JSON string
    question_json = json.dumps([simple_question])
    
    from utils.response_parser import ResponseParser
    parser = ResponseParser(strict_mode=False, log_invalid=True)
    questions, stats = parser.parse_response(question_json)
    
    print(f"   Parser extracted {len(questions)} questions")
    print(f"   Parser stats: {stats}")
    
    # Test the aggressive fix directly
    print("\n4. TESTING AGGRESSIVE FIX")
    
    # Test with aggressive fixing
    parser_aggressive = ResponseParser(strict_mode=False, log_invalid=True)
    
    # Manually call the fix method
    fixed_json = parser_aggressive._fix_latex_json_issues(question_json, aggressive=True)
    print(f"   Fixed JSON: {fixed_json[:200]}...")
    
    # Try parsing with aggressive fix
    questions_aggressive, stats_aggressive = parser_aggressive.parse_response(question_json)
    
    print(f"   Aggressive parser extracted {len(questions_aggressive)} questions")
    print(f"   Aggressive parser stats: {stats_aggressive}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_validation()