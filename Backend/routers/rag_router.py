"""
RAG Router

This module defines FastAPI endpoints for the RAG (Retrieval-Augmented Generation)
system in the Mentor AI EdTech Platform. It exposes REST API endpoints for
generating questions using the RAG pipeline.

Endpoints:
- POST /generate-questions: Generate questions for a single topic
- POST /generate-batch: Generate questions for multiple topics
- POST /context/build: Build context from vector search (testing)
- POST /context/preview: Preview context without generation
- GET /pipeline/status: Check RAG pipeline health
- GET /metrics: Get generation performance metrics

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> # Start the server
    >>> uvicorn main:app --reload
    >>> 
    >>> # Generate questions
    >>> curl -X POST http://localhost:8000/api/rag/generate-questions \\
    ...      -H "Content-Type: application/json" \\
    ...      -d '{"topic":"Calculus","exam_type":"JEE_MAIN","difficulty":"medium"}'
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse

# Import models
from models.rag_models import (
    RAGRequest,
    RAGResponse,
    QuestionGenerationRequest,
    HealthStatus,
    GenerationMetrics,
    ErrorResponse
)

# Import services - use mock if USE_MOCK_SERVICES is set
import os
if os.getenv("USE_MOCK_SERVICES", "false").lower() == "true":
    from services.mock_rag_service import MockRAGService as RAGService
    from services.mock_rag_service import MockHealthStatus as HealthStatusModel
    from services.mock_rag_service import MockGenerationMetrics as GenerationMetricsModel
else:
    try:
        from services.rag_service import RAGService
    except ImportError as e:
        import logging
        logging.warning(f"Failed to import RAGService: {e}. Using mock service.")
        from services.mock_rag_service import MockRAGService as RAGService


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Create router
router = APIRouter(
    prefix="/api/rag",
    tags=["RAG"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - Invalid input parameters"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error - Generation failed"
        },
        503: {
            "model": ErrorResponse,
            "description": "Service Unavailable - RAG service is down"
        }
    }
)


# Initialize RAG service with fallback to mock
try:
    rag_service = RAGService(enable_caching=True, high_quality_only=True)
    logger.info("RAG service initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize RAGService: {e}. Using mock service.")
    from services.mock_rag_service import MockRAGService
    rag_service = MockRAGService(enable_caching=True, high_quality_only=True)


# ============================================================================
# QUESTION GENERATION ENDPOINTS
# ============================================================================

@router.post(
    "/generate-questions",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate questions for a topic",
    description="""
    Generate high-quality exam questions for a single topic using Gemini API.
    
    This endpoint:
    1. Retrieves relevant context using Gemini-based semantic search
    2. Builds a prompt with syllabus context
    3. Generates questions using Gemini Flash
    4. Validates and filters questions for quality
    5. Returns only high-quality questions (score > 80)
    
    **Features:**
    - Automatic caching (7-day TTL)
    - Quality filtering (validation score > 80)
    - Diversity tracking (no duplicate questions)
    - Comprehensive metadata and statistics
    - Direct Gemini API integration (no vector embeddings needed)
    
    **Use Cases:**
    - Practice question generation
    - Targeted topic revision
    - Weak area reinforcement
    """,
    response_description="Generated questions with metadata and quality statistics"
)
async def generate_questions(
    request: RAGRequest,
    http_request: Request
) -> RAGResponse:
    """
    Generate questions for a single topic using RAG pipeline.
    
    Args:
        request: RAGRequest with topic, exam_type, difficulty, num_questions
        http_request: FastAPI request object for logging
    
    Returns:
        RAGResponse: Generated questions with metadata and statistics
    
    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 500: Generation failed
        HTTPException 503: RAG service unavailable
    
    Example Request:
        ```json
        {
            "topic": "Limits and Continuity",
            "exam_type": "JEE_MAIN",
            "difficulty": "medium",
            "num_questions": 5,
            "include_explanations": true,
            "question_type": "single_correct",
            "use_cache": true
        }
        ```
    
    Example Response:
        ```json
        {
            "questions": [...],
            "metadata": {
                "topic": "Limits and Continuity",
                "exam_type": "JEE_MAIN",
                "difficulty": "medium",
                "generation_method": "RAG",
                "vector_search_used": true,
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
            "cache_hit": false,
            "total_questions": 5
        }
        ```
    """
    try:
        # Log request
        logger.info(
            f"Received question generation request - "
            f"Topic: {request.topic}, Exam: {request.exam_type}, "
            f"Difficulty: {request.difficulty}, Count: {request.num_questions}"
        )
        
        # Validate request
        if not request.topic or not request.topic.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic cannot be empty"
            )
        
        # Generate questions using RAG service
        result = rag_service.generate_for_topic(
            topic=request.topic,
            exam_type=request.exam_type,
            difficulty=request.difficulty,
            count=request.num_questions,
            use_cache=request.use_cache
        )
        
        # Convert RAGResult to RAGResponse
        response = RAGResponse(
            questions=result.questions,
            metadata=result.metadata.dict(),
            generation_time=result.generation_time,
            quality_stats=result.quality_stats.dict(),
            cache_hit=result.cached,
            total_questions=len(result.questions)
        )
        
        # Log success
        logger.info(
            f"Successfully generated {len(result.questions)} questions - "
            f"Topic: {request.topic}, Cache hit: {result.cached}"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Question generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate questions: {str(e)}"
        )


@router.post(
    "/generate-batch",
    response_model=Dict[str, RAGResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate questions for multiple topics",
    description="""
    Generate questions for multiple topics in a single request.
    
    This endpoint processes multiple topics in batch and returns
    separate results for each topic. Each topic is processed
    independently using the full RAG pipeline.
    
    **Features:**
    - Batch processing for efficiency
    - Independent caching per topic
    - Parallel generation where possible
    - Detailed results per topic
    
    **Use Cases:**
    - Creating comprehensive practice sets
    - Multi-topic diagnostic tests
    - Syllabus-wide question generation
    """,
    response_description="Dictionary mapping topics to their generated questions"
)
async def generate_batch(
    request: QuestionGenerationRequest,
    http_request: Request
) -> Dict[str, RAGResponse]:
    """
    Generate questions for multiple topics in batch.
    
    Args:
        request: QuestionGenerationRequest with topics list and parameters
        http_request: FastAPI request object for logging
    
    Returns:
        Dict[str, RAGResponse]: Dictionary mapping each topic to its results
    
    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 500: Batch generation failed
    
    Example Request:
        ```json
        {
            "topics": ["Calculus", "Algebra", "Trigonometry"],
            "exam_type": "JEE_MAIN",
            "difficulty": "medium",
            "questions_per_topic": 5,
            "filters": {"subject": "Mathematics"},
            "include_explanations": true,
            "question_type": "single_correct"
        }
        ```
    
    Example Response:
        ```json
        {
            "Calculus": {
                "questions": [...],
                "metadata": {...},
                "generation_time": 3.2,
                ...
            },
            "Algebra": {
                "questions": [...],
                "metadata": {...},
                "generation_time": 2.8,
                ...
            },
            "Trigonometry": {
                "questions": [...],
                "metadata": {...},
                "generation_time": 3.0,
                ...
            }
        }
        ```
    """
    try:
        # Log request
        logger.info(
            f"Received batch generation request - "
            f"Topics: {request.topics}, Exam: {request.exam_type}, "
            f"Questions per topic: {request.questions_per_topic}"
        )
        
        # Validate request
        if not request.topics or len(request.topics) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topics list cannot be empty"
            )
        
        if len(request.topics) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 topics allowed per batch request"
            )
        
        # Generate questions for each topic
        results = {}
        for topic in request.topics:
            try:
                logger.info(f"Generating questions for topic: {topic}")
                
                result = rag_service.generate_for_topic(
                    topic=topic,
                    exam_type=request.exam_type,
                    difficulty=request.difficulty,
                    count=request.questions_per_topic,
                    use_cache=True
                )
                
                # Convert to RAGResponse
                results[topic] = RAGResponse(
                    questions=result.questions,
                    metadata=result.metadata.dict(),
                    generation_time=result.generation_time,
                    quality_stats=result.quality_stats.dict(),
                    cache_hit=result.cached,
                    total_questions=len(result.questions)
                )
                
                logger.info(
                    f"Successfully generated {len(result.questions)} "
                    f"questions for topic: {topic}"
                )
                
            except Exception as e:
                logger.error(f"Failed to generate questions for topic '{topic}': {str(e)}")
                # Continue with other topics, store error info
                results[topic] = {
                    "error": str(e),
                    "topic": topic
                }
        
        # Log batch completion
        successful_topics = sum(1 for r in results.values() if isinstance(r, RAGResponse))
        logger.info(
            f"Batch generation completed - "
            f"Successful: {successful_topics}/{len(request.topics)}"
        )
        
        return results
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Batch generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch generation failed: {str(e)}"
        )


# ============================================================================
# CONTEXT ENDPOINTS (for testing and debugging)
# ============================================================================

@router.post(
    "/context/build",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Build context using Gemini API",
    description="""
    Build and return context for a topic using Gemini-based semantic search.
    
    This endpoint is primarily for testing and debugging the RAG pipeline.
    It retrieves relevant syllabus content using Gemini API without
    generating questions.
    
    **Use Cases:**
    - Testing Gemini-based search quality
    - Debugging context retrieval
    - Previewing syllabus content
    - Validating topic coverage
    """,
    response_description="Retrieved context and source information"
)
async def build_context(
    request: Dict[str, str],
    http_request: Request
) -> Dict[str, Any]:
    """
    Build context using Gemini API for testing.
    
    Args:
        request: Dictionary with 'topic' and 'exam_type' keys
        http_request: FastAPI request object for logging
    
    Returns:
        Dict containing context text generated by Gemini
    
    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 500: Context building failed
    
    Example Request:
        ```json
        {
            "topic": "Limits and Continuity",
            "exam_type": "JEE_MAIN"
        }
        ```
    
    Example Response:
        ```json
        {
            "context": "Syllabus content here...",
            "sources": "Gemini-based semantic search",
            "token_count": 1500,
            "topic": "Limits and Continuity",
            "exam_type": "JEE_MAIN"
        }
        ```
    """
    try:
        topic = request.get("topic")
        exam_type = request.get("exam_type")
        
        # Validate inputs
        if not topic or not exam_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'topic' and 'exam_type' are required"
            )
        
        logger.info(f"Building context - Topic: {topic}, Exam: {exam_type}")
        
        # Use question generator's Gemini-based context retrieval
        context_result = rag_service.question_generator._retrieve_context(
            topic=topic,
            exam_type=exam_type
        )
        
        # Estimate token count (rough approximation: 1 token ≈ 4 chars)
        token_count = len(context_result) // 4
        
        response = {
            "context": context_result,
            "sources": "Gemini-based semantic search",
            "token_count": token_count,
            "topic": topic,
            "exam_type": exam_type,
            "method": "gemini_api",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Context built successfully - "
            f"Length: {len(context_result)} chars, "
            f"Tokens: ~{token_count}"
        )
        
        return response
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Context building failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to build context: {str(e)}"
        )


@router.post(
    "/context/preview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Preview context without generation",
    description="""
    Preview context and metadata without generating questions.
    
    This endpoint retrieves and displays context information including
    token counts, relevance scores, and content preview without actually
    calling the LLM for question generation.
    
    **Use Cases:**
    - Estimating generation costs
    - Validating context quality
    - Checking token limits
    - Preview before generation
    """,
    response_description="Context preview with metadata"
)
async def preview_context(
    request: Dict[str, str],
    http_request: Request
) -> Dict[str, Any]:
    """
    Preview context without generating questions.
    
    Args:
        request: Dictionary with 'topic' and 'exam_type' keys
        http_request: FastAPI request object for logging
    
    Returns:
        Dict containing context preview and metadata
    
    Example Request:
        ```json
        {
            "topic": "Thermodynamics",
            "exam_type": "JEE_ADVANCED"
        }
        ```
    
    Example Response:
        ```json
        {
            "context_preview": "First 500 characters of context...",
            "token_count": 1500,
            "estimated_cost": 0.001875,
            "topic": "Thermodynamics",
            "exam_type": "JEE_ADVANCED"
        }
        ```
    """
    try:
        topic = request.get("topic")
        exam_type = request.get("exam_type")
        
        if not topic or not exam_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Both 'topic' and 'exam_type' are required"
            )
        
        logger.info(f"Previewing context - Topic: {topic}, Exam: {exam_type}")
        
        # Retrieve context
        context = rag_service.question_generator._retrieve_context(
            topic=topic,
            exam_type=exam_type
        )
        
        # Calculate metrics
        token_count = len(context) // 4  # Rough estimate
        preview_length = 500
        context_preview = context[:preview_length] + "..." if len(context) > preview_length else context
        
        # Estimate cost (Gemini Flash pricing: $0.000125/1K input tokens)
        estimated_cost = (token_count / 1000) * 0.000125
        
        response = {
            "context_preview": context_preview,
            "full_length": len(context),
            "token_count": token_count,
            "estimated_cost": round(estimated_cost, 6),
            "topic": topic,
            "exam_type": exam_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(
            f"Context preview generated - "
            f"Tokens: ~{token_count}, "
            f"Cost: ${estimated_cost:.6f}"
        )
        
        return response
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Context preview failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview context: {str(e)}"
        )


# ============================================================================
# SYSTEM STATUS ENDPOINTS
# ============================================================================

@router.get(
    "/pipeline/status",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Check RAG pipeline health",
    description="""
    Check the health status of the RAG pipeline and all its dependencies.
    
    This endpoint verifies:
    - RAG Service availability
    - Question Generator status
    - Gemini API connectivity
    - Firestore database
    - API quotas and limits
    
    **Use Cases:**
    - Health monitoring
    - Pre-flight checks
    - Debugging service issues
    - Quota tracking
    """,
    response_description="Health status of all RAG components"
)
async def get_pipeline_status(
    http_request: Request
) -> HealthStatus:
    """
    Get RAG pipeline health status.
    
    Args:
        http_request: FastAPI request object for logging
    
    Returns:
        HealthStatus: Health status of all components
    
    Example Response:
        ```json
        {
            "all_systems_ok": true,
            "components": {
                "gemini": "healthy",
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
        ```
    """
    try:
        logger.info("Performing RAG pipeline health check")
        
        # Get health status from RAG service
        health_status = rag_service.health_check()
        
        # Log status
        if health_status.all_systems_ok:
            logger.info("RAG pipeline health check: All systems operational")
        else:
            logger.warning(
                f"RAG pipeline health check: Some systems degraded - "
                f"{health_status.message}"
            )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        
        # Return degraded status
        return HealthStatus(
            all_systems_ok=False,
            components={
                "rag_service": "down",
                "error": str(e)
            },
            quotas=None,
            last_check=datetime.utcnow(),
            message=f"Health check failed: {str(e)}"
        )


@router.get(
    "/metrics",
    response_model=GenerationMetrics,
    status_code=status.HTTP_200_OK,
    summary="Get generation performance metrics",
    description="""
    Retrieve comprehensive performance metrics for the RAG system.
    
    This endpoint provides detailed statistics about:
    - Total questions generated
    - Success and failure rates
    - Average quality scores
    - Generation time statistics
    - Cache hit rates
    - High-quality question rates
    
    **Use Cases:**
    - Performance monitoring
    - Cost analysis
    - Quality tracking
    - Optimization insights
    """,
    response_description="Comprehensive generation performance metrics"
)
async def get_metrics(
    http_request: Request
) -> GenerationMetrics:
    """
    Get RAG system performance metrics.
    
    Args:
        http_request: FastAPI request object for logging
    
    Returns:
        GenerationMetrics: Comprehensive performance statistics
    
    Example Response:
        ```json
        {
            "total_generated": 500,
            "success_rate": 0.95,
            "avg_quality_score": 85.5,
            "avg_generation_time": 3.2,
            "cache_hit_rate": 0.3,
            "total_requests": 100,
            "failed_requests": 5,
            "high_quality_rate": 0.88
        }
        ```
    """
    try:
        logger.info("Retrieving RAG system metrics")
        
        # Get metrics from RAG service
        metrics = rag_service.get_metrics()
        
        logger.info(
            f"Metrics retrieved - "
            f"Total generated: {metrics.total_generated}, "
            f"Success rate: {metrics.success_rate:.2%}"
        )
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


# Module initialization
logger.info("RAG router initialized successfully")
