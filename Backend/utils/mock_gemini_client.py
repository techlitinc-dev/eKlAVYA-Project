"""
Mock Gemini Client for Development

Provides mock responses without requiring Google Cloud credentials.
Use by setting USE_MOCK_SERVICES=true in environment.
"""

import logging
import random
import json
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class MockGeminiClient:
    """Mock Gemini client that returns sample questions."""
    
    def __init__(self, **kwargs):
        logger.info("🔧 Using MockGeminiClient for development")
        self.model_name = "mock-gemini-2.5-flash-lite"
        self.project_id = kwargs.get("project_id", "mock-project")
        self.location = kwargs.get("location", "mock-location")
    
    def generate_content(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate mock question content."""
        logger.info(f"MockGemini: Generating content for prompt length {len(prompt)}")
        
        # Parse the prompt to understand what's being requested
        prompt_lower = prompt.lower()
        
        if "physics" in prompt_lower or "mechanics" in prompt_lower:
            subject = "Physics"
            topic = "Mechanics"
        elif "chemistry" in prompt_lower or "organic" in prompt_lower:
            subject = "Chemistry"
            topic = "Organic Chemistry"
        elif "math" in prompt_lower or "calculus" in prompt_lower:
            subject = "Mathematics"
            topic = "Calculus"
        elif "biology" in prompt_lower:
            subject = "Biology"
            topic = "Cell Biology"
        else:
            subject = "Physics"
            topic = "General Physics"
        
        # Determine number of questions from prompt
        num_questions = 5
        for word in prompt.split():
            if word.isdigit():
                num_questions = min(int(word), 10)
                break
        
        # Generate mock questions
        questions = self._generate_mock_questions(subject, topic, num_questions)
        
        return json.dumps({"questions": questions}, indent=2)
    
    def _generate_mock_questions(self, subject: str, topic: str, count: int) -> List[Dict]:
        """Generate mock questions."""
        questions = []
        
        templates = {
            "Physics": [
                ("A ball is thrown vertically upward with velocity {v} m/s. Find the maximum height reached.", 
                 ["5 m", "10 m", "15 m", "20 m"], "B"),
                ("Calculate the force required to accelerate a {m} kg object at {a} m/s².",
                 ["{f1} N", "{f2} N", "{f3} N", "{f4} N"], "A"),
                ("A car travels {d} km in {t} hours. What is its average speed?",
                 ["{s1} km/h", "{s2} km/h", "{s3} km/h", "{s4} km/h"], "C"),
                ("What is the SI unit of force?",
                 ["Joule", "Newton", "Watt", "Pascal"], "B"),
                ("The acceleration due to gravity on Earth is approximately:",
                 ["8.9 m/s²", "9.8 m/s²", "10.8 m/s²", "11.8 m/s²"], "B"),
            ],
            "Chemistry": [
                ("What is the molecular formula of water?",
                 ["H2O", "H2O2", "HO", "H3O"], "A"),
                ("Which element has atomic number 6?",
                 ["Nitrogen", "Carbon", "Oxygen", "Boron"], "B"),
                ("What type of bond is formed between Na and Cl in NaCl?",
                 ["Covalent", "Ionic", "Metallic", "Hydrogen"], "B"),
                ("The pH of a neutral solution at 25°C is:",
                 ["0", "7", "14", "1"], "B"),
                ("Which gas is released during photosynthesis?",
                 ["Carbon dioxide", "Nitrogen", "Oxygen", "Hydrogen"], "C"),
            ],
            "Mathematics": [
                ("Find the derivative of f(x) = x²",
                 ["x", "2x", "x²", "2"], "B"),
                ("What is the integral of 2x dx?",
                 ["x", "x²", "2x²", "x² + C"], "D"),
                ("Solve: 2x + 5 = 15",
                 ["x = 5", "x = 10", "x = 7", "x = 3"], "A"),
                ("What is the value of sin(90°)?",
                 ["0", "1", "-1", "0.5"], "B"),
                ("The sum of angles in a triangle is:",
                 ["90°", "180°", "270°", "360°"], "B"),
            ],
            "Biology": [
                ("What is the powerhouse of the cell?",
                 ["Nucleus", "Mitochondria", "Ribosome", "Golgi body"], "B"),
                ("DNA stands for:",
                 ["Deoxyribonucleic acid", "Diribonucleic acid", "Deoxyribose acid", "None"], "A"),
                ("Which organ produces insulin?",
                 ["Liver", "Kidney", "Pancreas", "Heart"], "C"),
                ("The basic unit of life is:",
                 ["Atom", "Molecule", "Cell", "Tissue"], "C"),
                ("Photosynthesis occurs in:",
                 ["Mitochondria", "Chloroplast", "Nucleus", "Ribosome"], "B"),
            ]
        }
        
        subject_templates = templates.get(subject, templates["Physics"])
        
        for i in range(count):
            template = subject_templates[i % len(subject_templates)]
            question_text, options, correct = template
            
            # Format with random values
            v = random.randint(10, 50)
            m = random.randint(1, 10)
            a = random.randint(1, 10)
            d = random.randint(50, 200)
            t = random.randint(1, 5)
            
            question_text = question_text.format(v=v, m=m, a=a, d=d, t=t)
            
            formatted_options = []
            for opt in options:
                formatted_opt = opt.format(
                    f1=m*a, f2=m*a+5, f3=m*a-3, f4=m*a+10,
                    s1=d//t-10, s2=d//t+10, s3=d//t, s4=d//t+20
                )
                formatted_options.append(formatted_opt)
            
            question = {
                "question_id": f"mock_q_{subject[:3].lower()}_{i+1}",
                "question": question_text,
                "options": {
                    "A": formatted_options[0],
                    "B": formatted_options[1],
                    "C": formatted_options[2],
                    "D": formatted_options[3]
                },
                "correct_answer": correct,
                "explanation": f"This is a {subject} question about {topic}. The correct answer is {correct}.",
                "difficulty": ["easy", "medium", "hard"][i % 3],
                "topic": topic,
                "subject": subject,
                "question_type": "single_correct_mcq",
                "validation_score": random.randint(80, 95)
            }
            questions.append(question)
        
        return questions
    
    async def generate_content_async(self, prompt: str, **kwargs) -> str:
        """Async version of generate_content."""
        return self.generate_content(prompt, **kwargs)
    
    def generate_content_stream(self, prompt: str, **kwargs):
        """Stream mock content."""
        content = self.generate_content(prompt, **kwargs)
        for chunk in content.split('\n'):
            yield chunk + '\n'
    
    def update_config(self, **kwargs):
        """Update mock configuration."""
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """Get mock configuration."""
        return {
            "project_id": self.project_id,
            "location": self.location,
            "model_name": self.model_name,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 2048
        }


# Global mock client
_mock_client = None


def get_gemini_client(**kwargs) -> MockGeminiClient:
    """Get or create mock Gemini client."""
    global _mock_client
    if _mock_client is None:
        _mock_client = MockGeminiClient(**kwargs)
    return _mock_client


def is_gemini_initialized() -> bool:
    """Always return True for mock."""
    return True


# For compatibility
GeminiClient = MockGeminiClient
