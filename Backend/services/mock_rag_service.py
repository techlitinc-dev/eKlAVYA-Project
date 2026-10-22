"""
Mock RAG Service for Development

Provides mock RAG functionality without requiring Google Cloud credentials.
Use by setting USE_MOCK_SERVICES=true in environment.
"""

import logging
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MockQualityStats(BaseModel):
    """Statistics about question quality."""
    average_score: float = 85.0
    min_score: float = 75.0
    max_score: float = 95.0
    high_quality_count: int = 5
    total_count: int = 5


class MockRAGMetadata(BaseModel):
    """Metadata about the RAG generation process."""
    topic: str
    exam_type: str
    difficulty: str
    requested_count: int
    actual_count: int
    generation_time_seconds: float
    cache_hit: bool = False
    vector_search_used: bool = True
    llm_calls: int = 1
    validation_pass_rate: float = 0.9


@dataclass
class MockRAGResult:
    """Result of RAG question generation."""
    questions: List[Dict]
    metadata: MockRAGMetadata
    quality_stats: MockQualityStats
    generation_time: float
    cached: bool = False


class MockHealthStatus(BaseModel):
    """System health status."""
    all_systems_ok: bool = True
    components: Dict[str, str] = {
        "question_generator": "healthy",
        "gemini_service": "mock",
        "vector_search": "mock",
        "firestore": "unavailable"
    }
    quotas: Optional[Dict] = None
    last_check: datetime = datetime.utcnow()
    message: str = "Mock RAG service operational"


class MockGenerationMetrics(BaseModel):
    """Generation performance metrics."""
    total_generated: int = 0
    success_rate: float = 0.95
    avg_quality_score: float = 85.0
    avg_generation_time: float = 2.5
    cache_hit_rate: float = 0.3
    total_requests: int = 0
    failed_requests: int = 0
    high_quality_rate: float = 0.88


class MockRAGService:
    """Mock RAG service for development without Google Cloud."""
    
    def __init__(self, enable_caching: bool = True, high_quality_only: bool = True):
        logger.info("🔧 Initializing MockRAGService for development")
        self.enable_caching = enable_caching
        self.high_quality_only = high_quality_only
        self._metrics = MockGenerationMetrics()
        self._request_count = 0
    
    def generate_for_topic(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        count: int = 5,
        use_cache: bool = True,
        question_type: str = "single_correct"
    ):
        """Generate mock questions for a topic."""
        start_time = time.time()
        
        logger.info(f"MockRAG: Generating {count} questions for {topic} ({exam_type}, {difficulty})")
        
        self._request_count += 1
        self._metrics.total_requests = self._request_count
        self._metrics.total_generated += count
        
        # Generate mock questions
        questions = self._generate_mock_questions(topic, exam_type, difficulty, count)
        
        generation_time = time.time() - start_time
        
        # Return a simple object with dict-compatible attributes
        class Result:
            pass
        
        result = Result()
        result.questions = questions
        result.metadata = {
            "topic": topic,
            "exam_type": exam_type,
            "difficulty": difficulty,
            "generation_method": "RAG",
            "vector_search_used": True,
            "llm_calls": 1,
            "validation_pass_rate": 0.9
        }
        result.quality_stats = {
            "average_score": round(random.uniform(82, 92), 1),
            "min_score": round(random.uniform(75, 80), 1),
            "max_score": round(random.uniform(90, 98), 1),
            "high_quality_count": count,
            "total_count": count,
            "valid_count": count,
            "invalid_count": 0
        }
        result.generation_time = generation_time
        result.cached = False
        
        return result
    
    def _generate_mock_questions(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        count: int
    ) -> List[Dict]:
        """Generate mock questions."""
        questions = []
        
        # Subject detection
        topic_lower = topic.lower()
        if any(w in topic_lower for w in ["physics", "mechanics", "motion", "force", "energy"]):
            subject = "Physics"
        elif any(w in topic_lower for w in ["chemistry", "organic", "inorganic", "reaction"]):
            subject = "Chemistry"
        elif any(w in topic_lower for w in ["math", "calculus", "algebra", "geometry"]):
            subject = "Mathematics"
        elif any(w in topic_lower for w in ["biology", "cell", "genetics", "botany"]):
            subject = "Biology"
        else:
            subject = "Physics"
        
        templates = {
            "Physics": [
                ("A particle moves with velocity v = {v} m/s. Calculate its kinetic energy if mass is {m} kg.",
                 ["{ke1} J", "{ke2} J", "{ke3} J", "{ke4} J"], "A"),
                ("What is the SI unit of {quantity}?",
                 ["Newton", "Joule", "Watt", "Pascal"], "B"),
                ("A body falls freely from height h. Its velocity at ground is:",
                 ["√(gh)", "√(2gh)", "2gh", "gh"], "B"),
            ],
            "Chemistry": [
                ("The IUPAC name of CH3-CH2-OH is:",
                 ["Methanol", "Ethanol", "Propanol", "Butanol"], "B"),
                ("Which of the following is an alkali metal?",
                 ["Calcium", "Sodium", "Magnesium", "Aluminum"], "B"),
                ("The oxidation state of Mn in KMnO4 is:",
                 ["+5", "+6", "+7", "+4"], "C"),
            ],
            "Mathematics": [
                ("The derivative of sin(x) is:",
                 ["cos(x)", "-cos(x)", "sin(x)", "-sin(x)"], "A"),
                ("∫ x dx equals:",
                 ["x", "x²/2 + C", "2x", "1"], "B"),
                ("The value of lim(x→0) sin(x)/x is:",
                 ["0", "1", "∞", "undefined"], "B"),
            ],
            "Biology": [
                ("The powerhouse of the cell is:",
                 ["Nucleus", "Mitochondria", "Ribosome", "Golgi body"], "B"),
                ("DNA replication is:",
                 ["Conservative", "Semi-conservative", "Dispersive", "Random"], "B"),
                ("Photosynthesis occurs in:",
                 ["Mitochondria", "Chloroplast", "Nucleus", "Cytoplasm"], "B"),
            ]
        }
        
        subject_templates = templates.get(subject, templates["Physics"])
        
        for i in range(count):
            template = subject_templates[i % len(subject_templates)]
            q_text, options, correct = template
            
            # Format with random values
            v = random.randint(5, 20)
            m = random.randint(1, 10)
            ke = 0.5 * m * v * v
            
            q_text = q_text.format(
                v=v, m=m, quantity=random.choice(["force", "energy", "power"])
            )
            
            formatted_options = []
            for opt in options:
                formatted_options.append(opt.format(
                    ke1=int(ke), ke2=int(ke*1.5), ke3=int(ke*0.5), ke4=int(ke*2)
                ))
            
            question = {
                "question_id": f"mock_{exam_type.lower()}_{subject.lower()}_{i+1}",
                "question": q_text,
                "options": {
                    "A": formatted_options[0],
                    "B": formatted_options[1],
                    "C": formatted_options[2],
                    "D": formatted_options[3]
                },
                "correct_answer": correct,
                "explanation": f"This is a {difficulty} level {subject} question about {topic}.",
                "difficulty": difficulty,
                "topic": topic,
                "subject": subject,
                "question_type": "single_correct_mcq",
                "validation_score": random.randint(80, 95),
                "marks": 4 if exam_type == "JEE_MAIN" else 4,
                "negative_marks": 1 if exam_type == "JEE_MAIN" else 1
            }
            questions.append(question)
        
        return questions
    
    def health_check(self) -> MockHealthStatus:
        """Return mock health status."""
        return MockHealthStatus()
    
    def get_metrics(self) -> MockGenerationMetrics:
        """Return mock metrics."""
        return self._metrics
    
    def reset_metrics(self):
        """Reset metrics."""
        self._metrics = MockGenerationMetrics()
        self._request_count = 0


# Factory function
def get_rag_service(enable_caching: bool = True, high_quality_only: bool = True):
    """Get RAG service (mock or real based on environment)."""
    import os
    
    if os.getenv("USE_MOCK_SERVICES", "false").lower() == "true":
        logger.info("Using MockRAGService")
        return MockRAGService(enable_caching, high_quality_only)
    
    # Try to import real service
    try:
        from services.rag_service import RAGService
        return RAGService(enable_caching=enable_caching, high_quality_only=high_quality_only)
    except Exception as e:
        logger.warning(f"Failed to initialize real RAGService: {e}")
        logger.info("Falling back to MockRAGService")
        return MockRAGService(enable_caching, high_quality_only)
