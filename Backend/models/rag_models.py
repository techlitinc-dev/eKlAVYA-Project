"""
RAG API Data Models

This module defines Pydantic models for RAG (Retrieval-Augmented Generation)
API requests and responses in the Mentor AI EdTech Platform.

Models:
- RAGRequest: Request for generating questions for a topic
- RAGResponse: Response with generated questions and metadata
- QuestionGenerationRequest: Batch question generation request
- ValidationResult: Question validation result
- HealthStatus: System health status
- GenerationMetrics: Generation performance metrics

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from models.rag_models import RAGRequest
    >>> 
    >>> request = RAGRequest(
    ...     topic="Limits and Continuity",
    ...     exam_type="JEE_MAIN",
    ...     difficulty="medium",
    ...     num_questions=5
    ... )
    >>> print(request.topic)
    'Limits and Continuity'
"""

from datetime import datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ============================================================================
# REQUEST MODELS
# ============================================================================

class RAGRequest(BaseModel):
    """
    Request model for RAG-based question generation.
    
    This model defines the parameters for generating questions for a specific
    topic using the RAG pipeline.
    
    Attributes:
        topic: Topic name for question generation
        exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
        difficulty: Difficulty level (easy, medium, hard)
        num_questions: Number of questions to generate (1-20)
        include_explanations: Whether to include detailed explanations
        question_type: Type of questions (single_correct, multiple_correct, numerical)
        use_cache: Whether to use cached questions
    
    Example:
        >>> request = RAGRequest(
        ...     topic="Calculus - Limits",
        ...     exam_type="JEE_MAIN",
        ...     difficulty="medium",
        ...     num_questions=5,
        ...     include_explanations=True
        ... )
    """
    
    topic: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Topic name for question generation",
        examples=["Limits and Continuity", "Newton's Laws of Motion", "Cell Biology"]
    )
    
    exam_type: Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"] = Field(
        ...,
        description="Type of entrance exam"
    )
    
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Difficulty level of questions"
    )
    
    num_questions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of questions to generate"
    )
    
    include_explanations: bool = Field(
        default=True,
        description="Whether to include detailed explanations in responses"
    )
    
    question_type: Literal["single_correct", "multiple_correct", "numerical"] = Field(
        default="single_correct",
        description="Type of questions to generate"
    )
    
    use_cache: bool = Field(
        default=True,
        description="Whether to use cached questions if available"
    )
    
    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        """Validate topic is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Topic cannot be empty or whitespace only")
        return v.strip()
    
    @field_validator("exam_type")
    @classmethod
    def validate_exam_type(cls, v: str) -> str:
        """Validate exam type."""
        valid_types = ["JEE_MAIN", "JEE_ADVANCED", "NEET"]
        if v not in valid_types:
            raise ValueError(f"exam_type must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        """Validate difficulty level."""
        valid_difficulties = ["easy", "medium", "hard"]
        if v not in valid_difficulties:
            raise ValueError(f"difficulty must be one of: {', '.join(valid_difficulties)}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "Limits and Continuity",
                "exam_type": "JEE_MAIN",
                "difficulty": "medium",
                "num_questions": 5,
                "include_explanations": True,
                "question_type": "single_correct",
                "use_cache": True
            }
        }
    )


class QuestionGenerationRequest(BaseModel):
    """
    Request model for batch question generation across multiple topics.
    
    This model allows generating questions for multiple topics in a single
    request, useful for creating practice sets or diagnostic tests.
    
    Attributes:
        topics: List of topic names
        exam_type: Type of exam
        difficulty: Difficulty level for all topics
        questions_per_topic: Number of questions per topic
        filters: Optional additional filters
        include_explanations: Whether to include explanations
    
    Example:
        >>> request = QuestionGenerationRequest(
        ...     topics=["Calculus", "Algebra", "Trigonometry"],
        ...     exam_type="JEE_MAIN",
        ...     difficulty="medium",
        ...     questions_per_topic=5
        ... )
    """
    
    topics: List[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of topics for question generation"
    )
    
    exam_type: Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"] = Field(
        ...,
        description="Type of entrance exam"
    )
    
    difficulty: Literal["easy", "medium", "hard"] = Field(
        ...,
        description="Difficulty level for all topics"
    )
    
    questions_per_topic: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Number of questions to generate per topic"
    )
    
    filters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional additional filters for question generation"
    )
    
    include_explanations: bool = Field(
        default=True,
        description="Whether to include detailed explanations"
    )
    
    question_type: Literal["single_correct", "multiple_correct", "numerical"] = Field(
        default="single_correct",
        description="Type of questions to generate"
    )
    
    @field_validator("topics")
    @classmethod
    def validate_topics(cls, v: List[str]) -> List[str]:
        """Validate topics list."""
        if not v:
            raise ValueError("Topics list cannot be empty")
        
        # Remove empty topics
        valid_topics = [topic.strip() for topic in v if topic and topic.strip()]
        
        if not valid_topics:
            raise ValueError("All topics are empty or whitespace")
        
        # Check for duplicates
        if len(valid_topics) != len(set(valid_topics)):
            raise ValueError("Topics list contains duplicates")
        
        return valid_topics
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topics": ["Limits and Continuity", "Differentiation", "Integration"],
                "exam_type": "JEE_MAIN",
                "difficulty": "medium",
                "questions_per_topic": 5,
                "filters": {"subject": "Mathematics"},
                "include_explanations": True,
                "question_type": "single_correct"
            }
        }
    )


class DiagnosticTestRequest(BaseModel):
    """
    Request model for generating a comprehensive diagnostic test.
    
    Attributes:
        exam_type: Type of exam
        topic_distribution: Optional dict mapping topics to question counts
        total_questions: Total questions if no distribution specified
        difficulty_mix: Optional difficulty distribution
    
    Example:
        >>> request = DiagnosticTestRequest(
        ...     exam_type="JEE_MAIN",
        ...     topic_distribution={"Calculus": 10, "Algebra": 10},
        ...     difficulty_mix={"easy": 0.3, "medium": 0.5, "hard": 0.2}
        ... )
    """
    
    exam_type: Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"] = Field(
        ...,
        description="Type of entrance exam"
    )
    
    topic_distribution: Optional[Dict[str, int]] = Field(
        default=None,
        description="Optional mapping of topics to question counts"
    )
    
    total_questions: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Total number of questions if no distribution specified"
    )
    
    difficulty_mix: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional difficulty distribution (percentages must sum to 1.0)"
    )
    
    @field_validator("difficulty_mix")
    @classmethod
    def validate_difficulty_mix(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
        """Validate difficulty mix percentages."""
        if v is None:
            return v
        
        # Check keys
        valid_keys = {"easy", "medium", "hard"}
        if not set(v.keys()).issubset(valid_keys):
            raise ValueError(f"difficulty_mix keys must be from: {valid_keys}")
        
        # Check sum
        total = sum(v.values())
        if abs(total - 1.0) > 0.01:  # Allow small floating point error
            raise ValueError(f"difficulty_mix percentages must sum to 1.0, got {total}")
        
        # Check all positive
        if any(val < 0 for val in v.values()):
            raise ValueError("difficulty_mix percentages must be non-negative")
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exam_type": "JEE_MAIN",
                "topic_distribution": {
                    "Calculus": 10,
                    "Algebra": 10,
                    "Mechanics": 10
                },
                "total_questions": 50,
                "difficulty_mix": {
                    "easy": 0.3,
                    "medium": 0.5,
                    "hard": 0.2
                }
            }
        }
    )


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class QualityStats(BaseModel):
    """
    Statistics about question quality.
    
    Attributes:
        average_score: Average validation score across all questions
        min_score: Minimum validation score
        max_score: Maximum validation score
        high_quality_count: Number of high-quality questions (score > 80)
        total_count: Total number of questions
        valid_count: Number of valid questions
        invalid_count: Number of invalid questions
    """
    
    average_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average validation score"
    )
    
    min_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Minimum validation score"
    )
    
    max_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Maximum validation score"
    )
    
    high_quality_count: int = Field(
        ...,
        ge=0,
        description="Number of high-quality questions (score > 80)"
    )
    
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of questions"
    )
    
    valid_count: int = Field(
        default=0,
        ge=0,
        description="Number of valid questions"
    )
    
    invalid_count: int = Field(
        default=0,
        ge=0,
        description="Number of invalid questions"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "average_score": 85.5,
                "min_score": 78.0,
                "max_score": 95.0,
                "high_quality_count": 5,
                "total_count": 5,
                "valid_count": 5,
                "invalid_count": 0
            }
        }
    )


class RAGMetadata(BaseModel):
    """
    Metadata about the RAG generation process.
    
    Attributes:
        topic: Topic that was requested
        exam_type: Exam type
        difficulty: Difficulty level
        generation_method: Method used (RAG, cached, etc.)
        vector_search_used: Whether vector search was used
        llm_calls: Number of LLM API calls made
        validation_pass_rate: Percentage of questions that passed validation
    """
    
    topic: str = Field(..., description="Topic name")
    exam_type: str = Field(..., description="Exam type")
    difficulty: str = Field(..., description="Difficulty level")
    generation_method: str = Field(
        default="RAG",
        description="Generation method used"
    )
    vector_search_used: bool = Field(
        default=False,
        description="Whether vector search was used for context"
    )
    llm_calls: int = Field(
        default=0,
        ge=0,
        description="Number of LLM API calls made"
    )
    validation_pass_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Validation pass rate (0.0 to 1.0)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "Limits and Continuity",
                "exam_type": "JEE_MAIN",
                "difficulty": "medium",
                "generation_method": "RAG",
                "vector_search_used": True,
                "llm_calls": 1,
                "validation_pass_rate": 0.8
            }
        }
    )


class RAGResponse(BaseModel):
    """
    Response model for RAG question generation.
    
    This model contains the generated questions along with metadata
    and statistics about the generation process.
    
    Attributes:
        questions: List of generated Question objects
        metadata: Metadata about generation process
        generation_time: Time taken to generate (seconds)
        quality_stats: Statistics about question quality
        cache_hit: Whether results were from cache
        total_questions: Total number of questions returned
    
    Example:
        >>> from models.question_models import Question
        >>> response = RAGResponse(
        ...     questions=[question1, question2],
        ...     metadata=metadata,
        ...     generation_time=3.2,
        ...     quality_stats=stats,
        ...     cache_hit=False,
        ...     total_questions=2
        ... )
    """
    
    questions: List[Any] = Field(
        ...,
        description="List of generated questions"
    )
    
    metadata: RAGMetadata = Field(
        ...,
        description="Generation metadata"
    )
    
    generation_time: float = Field(
        ...,
        ge=0.0,
        description="Generation time in seconds"
    )
    
    quality_stats: QualityStats = Field(
        ...,
        description="Quality statistics"
    )
    
    cache_hit: bool = Field(
        default=False,
        description="Whether result was from cache"
    )
    
    total_questions: int = Field(
        ...,
        ge=0,
        description="Total number of questions returned"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "questions": [],
                "metadata": {
                    "topic": "Limits and Continuity",
                    "exam_type": "JEE_MAIN",
                    "difficulty": "medium",
                    "generation_method": "RAG",
                    "vector_search_used": True,
                    "llm_calls": 1,
                    "validation_pass_rate": 0.8
                },
                "generation_time": 3.2,
                "quality_stats": {
                    "average_score": 85.5,
                    "min_score": 78.0,
                    "max_score": 95.0,
                    "high_quality_count": 5,
                    "total_count": 5,
                    "valid_count": 5,
                    "invalid_count": 0
                },
                "cache_hit": False,
                "total_questions": 5
            }
        }
    )


class ValidationResult(BaseModel):
    """
    Result of question validation.
    
    This model represents the outcome of validating a generated question
    including quality score, issues, and warnings.
    
    Attributes:
        is_valid: Whether the question passed validation
        quality_score: Quality score (0-100)
        issues: List of critical issues found
        warnings: List of non-critical warnings
        category_scores: Scores by validation category
    
    Example:
        >>> result = ValidationResult(
        ...     is_valid=True,
        ...     quality_score=85,
        ...     issues=[],
        ...     warnings=["Question could be clearer"]
        ... )
    """
    
    is_valid: bool = Field(
        ...,
        description="Whether question passed validation"
    )
    
    quality_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall quality score (0-100)"
    )
    
    issues: List[str] = Field(
        default_factory=list,
        description="List of critical issues that make question invalid"
    )
    
    warnings: List[str] = Field(
        default_factory=list,
        description="List of non-critical warnings"
    )
    
    category_scores: Dict[str, int] = Field(
        default_factory=dict,
        description="Scores by validation category (structure, quality, context)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "quality_score": 85,
                "issues": [],
                "warnings": ["Question could be more concise"],
                "category_scores": {
                    "structure": 100,
                    "quality": 90,
                    "context": 95
                }
            }
        }
    )


# ============================================================================
# SYSTEM STATUS MODELS
# ============================================================================

class ComponentStatus(BaseModel):
    """
    Status of a system component.
    
    Attributes:
        name: Component name
        status: Status (healthy, degraded, down)
        message: Optional status message
        last_check: When component was last checked
    """
    
    name: str = Field(..., description="Component name")
    status: Literal["healthy", "degraded", "down"] = Field(
        ...,
        description="Component status"
    )
    message: Optional[str] = Field(
        default=None,
        description="Optional status message"
    )
    last_check: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last check timestamp"
    )


class QuotaInfo(BaseModel):
    """
    API quota information.
    
    Attributes:
        remaining_calls: Number of API calls remaining
        total_calls: Total API calls allowed
        reset_time: When quota resets
        usage_percentage: Percentage of quota used
    """
    
    remaining_calls: int = Field(
        ...,
        ge=0,
        description="Remaining API calls"
    )
    
    total_calls: int = Field(
        ...,
        ge=0,
        description="Total API calls allowed"
    )
    
    reset_time: datetime = Field(
        ...,
        description="When quota resets"
    )
    
    usage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of quota used"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "remaining_calls": 750,
                "total_calls": 1000,
                "reset_time": "2024-11-28T00:00:00Z",
                "usage_percentage": 25.0
            }
        }
    )


class HealthStatus(BaseModel):
    """
    Overall system health status.
    
    This model provides comprehensive information about the health
    of all system components and API quotas.
    
    Attributes:
        all_systems_ok: Whether all systems are healthy
        components: Status of each component
        quotas: API quota information
        last_check: When health check was performed
        message: Optional overall status message
    
    Example:
        >>> health = HealthStatus(
        ...     all_systems_ok=True,
        ...     components={
        ...         "gemini": "healthy",
        ...         "vector_search": "healthy",
        ...         "firestore": "healthy"
        ...     },
        ...     quotas=quota_info,
        ...     last_check=datetime.utcnow()
        ... )
    """
    
    all_systems_ok: bool = Field(
        ...,
        description="Whether all systems are operational"
    )
    
    components: Dict[str, str] = Field(
        ...,
        description="Status of each system component"
    )
    
    quotas: Optional[Dict[str, QuotaInfo]] = Field(
        default=None,
        description="API quota information by service"
    )
    
    last_check: datetime = Field(
        default_factory=datetime.utcnow,
        description="When health check was performed"
    )
    
    message: Optional[str] = Field(
        default=None,
        description="Optional overall status message"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "all_systems_ok": True,
                "components": {
                    "gemini": "healthy",
                    "vector_search": "healthy",
                    "firestore": "healthy",
                    "question_generator": "healthy"
                },
                "quotas": {
                    "gemini": {
                        "remaining_calls": 750,
                        "total_calls": 1000,
                        "reset_time": "2024-11-28T00:00:00Z",
                        "usage_percentage": 25.0
                    }
                },
                "last_check": "2024-11-27T10:30:00Z",
                "message": "All systems operational"
            }
        }
    )


# ============================================================================
# METRICS MODELS
# ============================================================================

class GenerationMetrics(BaseModel):
    """
    Metrics about question generation performance.
    
    This model tracks comprehensive statistics about the RAG system's
    performance including success rates, quality scores, and timing.
    
    Attributes:
        total_generated: Total questions generated
        success_rate: Generation success rate (0.0 to 1.0)
        avg_quality_score: Average quality score across all questions
        avg_generation_time: Average time to generate questions (seconds)
        cache_hit_rate: Cache hit rate (0.0 to 1.0)
        total_requests: Total number of generation requests
        failed_requests: Number of failed requests
        high_quality_rate: Rate of high-quality questions (score > 80)
    
    Example:
        >>> metrics = GenerationMetrics(
        ...     total_generated=500,
        ...     success_rate=0.95,
        ...     avg_quality_score=85.5,
        ...     avg_generation_time=3.2,
        ...     cache_hit_rate=0.3
        ... )
    """
    
    total_generated: int = Field(
        ...,
        ge=0,
        description="Total number of questions generated"
    )
    
    success_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Generation success rate"
    )
    
    avg_quality_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average quality score"
    )
    
    avg_generation_time: float = Field(
        ...,
        ge=0.0,
        description="Average generation time in seconds"
    )
    
    cache_hit_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cache hit rate"
    )
    
    total_requests: int = Field(
        default=0,
        ge=0,
        description="Total generation requests"
    )
    
    failed_requests: int = Field(
        default=0,
        ge=0,
        description="Number of failed requests"
    )
    
    high_quality_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Rate of high-quality questions (score > 80)"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_generated": 500,
                "success_rate": 0.95,
                "avg_quality_score": 85.5,
                "avg_generation_time": 3.2,
                "cache_hit_rate": 0.3,
                "total_requests": 100,
                "failed_requests": 5,
                "high_quality_rate": 0.88
            }
        }
    )


# ============================================================================
# UTILITY MODELS
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Standard error response model.
    
    Attributes:
        error: Error type/code
        message: Human-readable error message
        details: Optional detailed error information
        timestamp: When error occurred
    """
    
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional detailed error information"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "GENERATION_FAILED",
                "message": "Failed to generate questions for topic",
                "details": {
                    "topic": "Calculus",
                    "reason": "Insufficient context retrieved"
                },
                "timestamp": "2024-11-27T10:30:00Z"
            }
        }
    )


# Module initialization
import logging
logger = logging.getLogger(__name__)
logger.info("RAG models module loaded")
