#!/usr/bin/env python3
"""
Detailed Debug Script for Question Generation

This script traces the complete question generation process step by step
to identify exactly where the validation is failing.
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

def test_question_generation():
    """Test the complete question generation pipeline with detailed logging."""
    
    print("=" * 80)
    print("DETAILED QUESTION GENERATION DEBUG")
    print("=" * 80)
    
    try:
        # Step 1: Test prompt building
        print("\n1. TESTING PROMPT BUILDING")
        print("-" * 40)
        
        from utils.prompt_templates import build_prompt
        
        prompt = build_prompt(
            exam_type="JEE_MAIN",
            topic="Newton's Laws of Motion",
            syllabus_context="Newton's Laws of Motion: First Law (Inertia), Second Law (F=ma), Third Law (Action-Reaction). Applications include equilibrium, friction, connected bodies.",
            difficulty="medium",
            num_questions=1,
            question_type="single_correct",
            subject="Physics"
        )
        
        print(f"✓ Prompt built successfully")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"First 500 chars:\n{prompt[:500]}...")
        
        # Step 2: Test Gemini service directly
        print("\n2. TESTING GEMINI SERVICE DIRECTLY")
        print("-" * 40)
        
        from services.gemini_service import GeminiService
        
        gemini_service = GeminiService()
        
        print("Calling Gemini service...")
        generated_questions = gemini_service.generate_questions(
            prompt=prompt,
            num_questions=1,
            use_cache=False,
            retry_on_insufficient=False
        )
        
        print(f"✓ Gemini returned {len(generated_questions)} questions")
        
        for i, q in enumerate(generated_questions, 1):
            print(f"\nQuestion {i}:")
            print(f"  Type: {type(q)}")
            if hasattr(q, 'dict'):
                q_dict = q.dict()
            else:
                q_dict = q
            print(f"  Keys: {list(q_dict.keys()) if isinstance(q_dict, dict) else 'Not a dict'}")
            
            # Check for required fields
            required_fields = ['question', 'correct_answer', 'explanation', 'difficulty', 'topic', 'exam_type', 'subject']
            missing_fields = []
            
            for field in required_fields:
                if field not in q_dict:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"  ❌ Missing fields: {missing_fields}")
            else:
                print(f"  ✓ All required fields present")
        
        # Step 3: Test question validation directly
        print("\n3. TESTING QUESTION VALIDATION")
        print("-" * 40)
        
        from services.question_validator import QuestionValidator
        
        validator = QuestionValidator(min_quality_score=50)  # Lower threshold for testing
        
        for i, q in enumerate(generated_questions, 1):
            print(f"\nValidating Question {i}:")
            
            try:
                result = validator.validate(q, "Newton's Laws of Motion")
                print(f"  Validation result: {result}")
                print(f"  Is valid: {result.is_valid}")
                print(f"  Quality score: {result.quality_score}")
                print(f"  Issues: {result.issues}")
                print(f"  Warnings: {result.warnings}")
                
            except Exception as e:
                print(f"  ❌ Validation failed with error: {e}")
                import traceback
                traceback.print_exc()
        
        # Step 4: Test complete question generator
        print("\n4. TESTING COMPLETE QUESTION GENERATOR")
        print("-" * 40)
        
        from services.question_generator import QuestionGenerator
        
        generator = QuestionGenerator(min_validation_score=50)  # Lower threshold
        
        try:
            questions = generator.generate_questions(
                topic="Newton's Laws of Motion",
                exam_type="JEE_MAIN",
                difficulty="medium",
                num_questions=1,
                use_cache=False
            )
            
            print(f"✓ Question generator returned {len(questions)} questions")
            
            for i, q in enumerate(questions, 1):
                print(f"\nFinal Question {i}:")
                print(f"  Question: {q.question[:100]}...")
                print(f"  Exam Type: {q.exam_type}")
                print(f"  Subject: {q.subject}")
                print(f"  Topic: {q.topic}")
                print(f"  Difficulty: {q.difficulty}")
                
        except Exception as e:
            print(f"  ❌ Question generator failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Step 5: Test with different topics
        print("\n5. TESTING WITH DIFFERENT TOPICS")
        print("-" * 40)
        
        test_topics = [
            ("Calculus", "JEE_MAIN", "Math"),
            ("Chemical Bonding", "JEE_MAIN", "Chemistry"),
            ("Cell Structure", "NEET", "Biology")
        ]
        
        for topic, exam_type, subject in test_topics:
            print(f"\nTesting topic: {topic} ({exam_type}, {subject})")
            
            try:
                questions = generator.generate_questions(
                    topic=subject,
                    exam_type=exam_type,
                    difficulty="medium",
                    num_questions=1,
                    use_cache=False
                )
                
                print(f"  ✓ Success: {len(questions)} questions generated")
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
    
    except Exception as e:
        print(f"\n❌ DEBUG SCRIPT FAILED: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_question_generation()