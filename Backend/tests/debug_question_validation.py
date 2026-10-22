#!/usr/bin/env python3
"""
Debug script to understand why questions are failing validation.
"""

import json
from services.question_generator import QuestionGenerator
from models.question_models import Question

def debug_validation():
    """Debug the question generation and validation process."""
    
    # Initialize generator
    generator = QuestionGenerator()
    
    # Test simple generation
    print("=== Testing Question Generation ===")
    
    try:
        # Test direct Gemini client first
        print("\n--- Testing Direct Gemini Client ---")
        client_response = generator.gemini_service.client.generate_content(
            """Generate 1 multiple choice question about Newton's laws of motion.
            
            Format as JSON:
            {
                "question": "According to Newton's first law of motion, what happens to an object at rest?",
                "options": {
                    "A": "It remains at rest",
                    "B": "It starts moving",
                    "C": "It accelerates",
                    "D": "It decelerates"
                },
                "correct_answer": "A",
                "explanation": "Newton's first law states that an object at rest remains at rest unless acted upon by an external force.",
                "difficulty": "easy",
                "topic": "Newton's Laws of Motion",
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "question_type": "single_correct"
            }"""
        )
        print(f"Direct client response:\n{client_response}\n")
        
        # Now test through service
        print("\n--- Testing Through Gemini Service ---")
        
        # First, let's see what the raw response looks like
        raw_response = generator.gemini_service.client.generate_content(
            """Generate 1 multiple choice question about Newton's laws of motion.
            
            Format as JSON:
            {
                "question": "According to Newton's first law of motion, what happens to an object at rest?",
                "options": {
                    "A": "It remains at rest",
                    "B": "It starts moving",
                    "C": "It accelerates",
                    "D": "It decelerates"
                },
                "correct_answer": "A",
                "explanation": "Newton's first law states that an object at rest remains at rest unless acted upon by an external force.",
                "difficulty": "easy",
                "topic": "Newton's Laws of Motion",
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "question_type": "single_correct"
            }"""
        )
        print(f"Raw response from Gemini:\n{raw_response}\n")
        
        questions = generator.gemini_service.generate_questions(
            prompt="""Generate 1 multiple choice question about Newton's laws of motion.
            
            Format as JSON:
            {
                "question": "According to Newton's first law of motion, what happens to an object at rest?",
                "options": {
                    "A": "It remains at rest",
                    "B": "It starts moving",
                    "C": "It accelerates",
                    "D": "It decelerates"
                },
                "correct_answer": "A",
                "explanation": "Newton's first law states that an object at rest remains at rest unless acted upon by an external force.",
                "difficulty": "easy",
                "topic": "Newton's Laws of Motion",
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "question_type": "single_correct"
            }""",
            num_questions=1,
            use_cache=False,
            retry_on_insufficient=False
        )
        
        print(f"Generated {len(questions)} questions")
        
        for i, q in enumerate(questions):
            print(f"\n--- Question {i+1} ---")
            print(f"Question: {q.question}")
            print(f"Options: {q.options}")
            print(f"Correct Answer: {q.correct_answer}")
            print(f"Explanation: {q.explanation}")
            print(f"Difficulty: {q.difficulty}")
            print(f"Topic: {q.topic}")
            
            # Validate
            from services.question_validator import QuestionValidator
            validator = QuestionValidator(min_quality_score=0)  # Very low threshold for debugging
            
            result = validator.validate(q)
            print(f"\nValidation Result:")
            print(f"  Valid: {result.is_valid}")
            print(f"  Score: {result.quality_score}")
            print(f"  Issues: {result.issues}")
            print(f"  Warnings: {result.warnings}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_validation()