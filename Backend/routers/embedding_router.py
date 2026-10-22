"""
Embedding Generation Router Module

This module defines FastAPI endpoints for text embedding generation using
Google Cloud Vertex AI in the Mentor AI EdTech Platform. It provides endpoints
for single and batch embedding generation with authentication and rate limiting.

Endpoints:
- POST /api/vector-search/embeddings/generate: Generate single embedding
- POST /api/vector-search/embeddings/batch: Generate batch embeddings
- GET /api/vector-search/embeddings/status: Get embedding service status

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse

from models.embedding_models import (
    EmbeddingRequest,
    EmbeddingResponse,
    BatchEmbeddingRequest,
    BatchEmbeddingResponse,
    EmbeddingMetadata
)
from services import embedding_service
from middleware.auth_middleware import get_current_user
from utils.vertex_ai_client import is_vertex_ai_initialized, get_vertex_ai_status

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/vector-search/embeddings",
    tags=["Vector Search - Embeddings"]
)

# Rate limiting storage (user_id -> deque of timestamps)
_rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())
_rate_limit_window = 60  # 1 minute in seconds
_rate_limit_max_requests = 100  # Maximum requests per window


# ============================================================================
# RATE LIMITING
# ============================================================================

def check_rate_limit(user_id: str) -> None:
    """
    Check if user has exceeded rate limit.
    
    Args:
        user_id: User identifier for rate limiting
    
    Raises:
        HTTPException: 429 if rate limit exceeded
    """
    global _rate_limit_storage
    
    current_time = time.time()
    user_requests = _rate_limit_storage[user_id]
    
    # Remove timestamps older than the window
    while user_requests and user_requests[0] < current_time - _rate_limit_window:
        user_requests.popleft()
    
    # Check if limit exceeded
    if len(user_requests) >= _rate_limit_max_requests:
        oldest_request = user_requests[0]
        retry_after = int(_rate_limit_window - (current_time - oldest_request))
        
        logger.warning(
            f"Rate limit exceeded for user {user_id}: "
            f"{len(user_requests)} requests in last {_rate_limit_window}s"
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {_rate_limit_max_requests} requests per minute allowed",
                "retry_after_seconds": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Add current request timestamp
    user_requests.append(current_time)
    logger.debug(f"Rate limit check passed for user {user_id}: {len(user_requests)}/{_rate_limit_max_requests}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/generate",
    response_model=EmbeddingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate single text embedding",
    description="""
    Generate embedding vector for a single text input using Vertex AI.
    
    This endpoint converts text into a high-dimensional vector representation
    (768 dimensions) that can be used for semantic search, similarity comparison,
    and other NLP tasks.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Rate Limit:** 100 requests per minute per user
    
    **Requirements:**
    - Text must be 1-3000 characters
    - Text cannot be empty or whitespace only
    - Valid task type must be specified
    
    **Returns:**
    - 200: Embedding generated successfully
    - 400: Invalid request (text validation failed)
    - 401: Authentication failed or token expired
    - 429: Rate limit exceeded
    - 500: Internal server error
    - 503: Vertex AI service unavailable
    """,
    responses={
        200: {
            "description": "Embedding generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "embedding": [0.123, -0.456, 0.789, "..."],
                        "dimension": 768,
                        "model": "textembedding-gecko@003",
                        "timestamp": "2025-11-26T10:30:00.000Z",
                        "metadata": {
                            "model": "textembedding-gecko@003",
                            "dimension": 768,
                            "timestamp": "2025-11-26T10:30:00.000Z",
                            "cached": False,
                            "text_length": 75,
                            "processing_time_ms": 120.5
                        }
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": "Rate limit exceeded",
                            "message": "Maximum 100 requests per minute allowed",
                            "retry_after_seconds": 45
                        }
                    }
                }
            }
        }
    }
)
async def generate_embedding(
    request: EmbeddingRequest,
    user_id: str = Depends(get_current_user)
) -> EmbeddingResponse:
    """
    Generate embedding for a single text input.
    
    Args:
        request: EmbeddingRequest containing text and options
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        EmbeddingResponse with embedding vector and metadata
    
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 429 for rate limit exceeded
        HTTPException: 503 if Vertex AI is unavailable
        HTTPException: 500 for server errors
    
    Example:
        Request:
        ```json
        {
            "text": "Newton's laws of motion explain force and motion",
            "task_type": "RETRIEVAL_DOCUMENT",
            "include_metadata": true
        }
        ```
        
        Response:
        ```json
        {
            "embedding": [0.123, -0.456, ...],  # 768 dimensions
            "dimension": 768,
            "model": "textembedding-gecko@003",
            "timestamp": "2025-11-26T10:30:00.000Z"
        }
        ```
    """
    start_time = time.time()
    
    try:
        logger.info(f"Embedding generation request from user {user_id}")
        logger.debug(f"Text length: {len(request.text)}, Task type: {request.task_type}")
        
        # Check rate limit
        check_rate_limit(user_id)
        
        # Check if Vertex AI is initialized
        if not is_vertex_ai_initialized():
            logger.error("Vertex AI is not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding service is currently unavailable. Please try again later."
            )
        
        # Generate embedding using service layer
        result = embedding_service.generate_embedding(
            text=request.text,
            task_type=request.task_type,
            use_cache=True
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000
        
        # Build response
        metadata = None
        if request.include_metadata:
            metadata = EmbeddingMetadata(
                model=result.metadata.model,
                dimension=result.metadata.dimension,
                timestamp=datetime.fromisoformat(result.metadata.timestamp.replace('Z', '+00:00')),
                cached=result.metadata.cached,
                text_length=result.metadata.text_length,
                processing_time_ms=round(processing_time, 2)
            )
        
        response = EmbeddingResponse(
            embedding=result.embedding,
            dimension=len(result.embedding),
            model=result.metadata.model,
            timestamp=datetime.fromisoformat(result.metadata.timestamp.replace('Z', '+00:00')),
            metadata=metadata
        )
        
        logger.info(
            f"Embedding generated successfully for user {user_id}: "
            f"dimension={response.dimension}, cached={result.metadata.cached}, "
            f"time={processing_time:.2f}ms"
        )
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as ve:
        # Handle validation errors
        logger.warning(f"Validation error during embedding generation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except RuntimeError as re:
        # Handle service unavailable errors
        logger.error(f"Runtime error during embedding generation: {re}")
        
        # Check if it's a model access error
        error_msg = str(re)
        if "Vertex AI embedding model is not accessible" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Vertex AI API Not Enabled",
                    "message": "The Vertex AI embedding model is not accessible. Please enable the Vertex AI API for your project.",
                    "action": "Visit https://console.cloud.google.com/apis/library/aiplatform.googleapis.com to enable the API",
                    "note": "After enabling the API, wait a few minutes for changes to propagate"
                }
            )
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during embedding generation: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embedding. Please try again later."
        )


@router.post(
    "/batch",
    response_model=BatchEmbeddingResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate batch embeddings",
    description="""
    Generate embeddings for multiple text inputs in a single request.
    
    This endpoint processes multiple texts efficiently using batch embedding
    generation. It's optimized for processing up to 100 texts at once.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Rate Limit:** 100 requests per minute per user (counts as 1 request regardless of batch size)
    
    **Requirements:**
    - 1-100 texts per request
    - Each text must be 1-3000 characters
    - All texts cannot be empty or whitespace only
    
    **Returns:**
    - 200: Embeddings generated successfully
    - 400: Invalid request (validation failed)
    - 401: Authentication failed or token expired
    - 429: Rate limit exceeded
    - 500: Internal server error
    - 503: Vertex AI service unavailable
    """,
    responses={
        200: {
            "description": "Batch embeddings generated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "embeddings": [
                            {
                                "embedding": [0.123, -0.456],
                                "dimension": 768,
                                "model": "textembedding-gecko@003",
                                "timestamp": "2025-11-26T10:30:00.000Z"
                            }
                        ],
                        "total_count": 3,
                        "successful_count": 3,
                        "failed_count": 0,
                        "total_processing_time_ms": 350.2,
                        "cache_hit_count": 1
                    }
                }
            }
        }
    }
)
async def generate_batch_embeddings(
    request: BatchEmbeddingRequest,
    user_id: str = Depends(get_current_user)
) -> BatchEmbeddingResponse:
    """
    Generate embeddings for multiple texts in batch.
    
    Args:
        request: BatchEmbeddingRequest containing list of texts
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        BatchEmbeddingResponse with embeddings for all texts
    
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 429 for rate limit exceeded
        HTTPException: 503 if Vertex AI is unavailable
        HTTPException: 500 for server errors
    
    Example:
        Request:
        ```json
        {
            "texts": [
                "Newton's laws of motion",
                "Electromagnetic induction",
                "Organic chemistry reactions"
            ],
            "task_type": "RETRIEVAL_DOCUMENT",
            "include_metadata": true
        }
        ```
    """
    start_time = time.time()
    
    try:
        logger.info(f"Batch embedding request from user {user_id}: {len(request.texts)} texts")
        
        # Check rate limit
        check_rate_limit(user_id)
        
        # Check if Vertex AI is initialized
        if not is_vertex_ai_initialized():
            logger.error("Vertex AI is not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Embedding service is currently unavailable. Please try again later."
            )
        
        # Generate embeddings using service layer
        result = embedding_service.generate_batch_embeddings(
            texts=request.texts,
            task_type=request.task_type,
            use_cache=True
        )
        
        # Calculate total processing time
        total_processing_time = (time.time() - start_time) * 1000
        
        # Build response embeddings
        embeddings_list = []
        for emb_result in result.embeddings:
            metadata = None
            if request.include_metadata:
                metadata = EmbeddingMetadata(
                    model=emb_result.metadata.model,
                    dimension=emb_result.metadata.dimension,
                    timestamp=datetime.fromisoformat(emb_result.metadata.timestamp.replace('Z', '+00:00')),
                    cached=emb_result.metadata.cached,
                    text_length=emb_result.metadata.text_length,
                    processing_time_ms=None  # Individual times not tracked in batch
                )
            
            embedding_response = EmbeddingResponse(
                embedding=emb_result.embedding,
                dimension=len(emb_result.embedding),
                model=emb_result.metadata.model,
                timestamp=datetime.fromisoformat(emb_result.metadata.timestamp.replace('Z', '+00:00')),
                metadata=metadata
            )
            embeddings_list.append(embedding_response)
        
        response = BatchEmbeddingResponse(
            embeddings=embeddings_list,
            total_count=len(embeddings_list),
            successful_count=len(embeddings_list),
            failed_count=0,
            total_processing_time_ms=round(total_processing_time, 2),
            cache_hit_count=result.cache_hit_count
        )
        
        logger.info(
            f"Batch embeddings generated for user {user_id}: "
            f"total={response.total_count}, cached={response.cache_hit_count}, "
            f"time={total_processing_time:.2f}ms"
        )
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as ve:
        # Handle validation errors
        logger.warning(f"Validation error during batch embedding generation: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except RuntimeError as re:
        # Handle service unavailable errors
        logger.error(f"Runtime error during batch embedding generation: {re}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during batch embedding generation: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch embeddings. Please try again later."
        )


@router.get(
    "/status",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get embedding service status",
    description="""
    Get the current status and statistics of the embedding service.
    
    This endpoint provides information about Vertex AI initialization,
    cache performance, and API quota usage.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Returns:**
    - Service health status
    - Vertex AI initialization status
    - Cache statistics (hits, misses, size)
    - Rate limit information
    - Model information
    """,
    responses={
        200: {
            "description": "Service status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "service": "embedding-service",
                        "status": "healthy",
                        "vertex_ai": {
                            "initialized": True,
                            "project_id": "mentor-ai-project",
                            "location": "us-central1",
                            "model": "textembedding-gecko@003"
                        },
                        "cache": {
                            "hits": 150,
                            "misses": 75,
                            "hit_rate": 0.67,
                            "size": 1250
                        },
                        "rate_limit": {
                            "max_requests_per_minute": 100,
                            "window_seconds": 60
                        }
                    }
                }
            }
        }
    }
)
async def get_embedding_service_status(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get embedding service status and statistics.
    
    Args:
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        Dictionary containing service status, Vertex AI info, and statistics
    
    Example:
        Response:
        ```json
        {
            "service": "embedding-service",
            "status": "healthy",
            "vertex_ai": {
                "initialized": true,
                "project_id": "mentor-ai-project",
                "model": "textembedding-gecko@003"
            },
            "cache": {
                "hits": 150,
                "misses": 75,
                "hit_rate": 0.67
            }
        }
        ```
    """
    try:
        logger.info(f"Status request from user {user_id}")
        
        # Get Vertex AI status
        vertex_status = get_vertex_ai_status()
        
        # Get embedding service statistics
        embedding_stats = embedding_service.get_embedding_stats()
        
        # Build status response
        status_response = {
            "service": "embedding-service",
            "status": "healthy" if vertex_status["initialized"] else "degraded",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "vertex_ai": {
                "initialized": vertex_status["initialized"],
                "project_id": vertex_status["project_id"],
                "location": vertex_status["location"],
                "model": vertex_status["embedding_model"],
                "dimension": vertex_status["embedding_dimension"],
                "regions_supported": vertex_status["supported_regions"]
            },
            "cache": {
                "total_requests": embedding_stats.total_requests,
                "hits": embedding_stats.cache_hits,
                "misses": embedding_stats.cache_misses,
                "hit_rate": round(embedding_stats.cache_hit_rate, 4),
                "size": embedding_stats.cache_size,
                "max_size": embedding_stats.cache_max_size,
                "fill_percentage": round(
                    (embedding_stats.cache_size / embedding_stats.cache_max_size) * 100, 2
                ) if embedding_stats.cache_max_size > 0 else 0
            },
            "rate_limit": {
                "max_requests_per_minute": _rate_limit_max_requests,
                "window_seconds": _rate_limit_window,
                "user_current_count": len(_rate_limit_storage.get(user_id, []))
            }
        }
        
        logger.info(f"Status retrieved for user {user_id}")
        
        return status_response
    
    except Exception as e:
        # Handle errors gracefully
        logger.error(f"Error retrieving embedding service status: {e}")
        logger.exception("Full traceback:")
        
        # Return degraded status
        return {
            "service": "embedding-service",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "error": "Failed to retrieve complete status",
            "message": str(e)
        }


# ============================================================================
# ROUTER EVENT HANDLERS
# ============================================================================

@router.on_event("startup")
async def startup_event():
    """Log router initialization."""
    logger.info("Embedding router initialized")
    logger.info(f"Rate limit: {_rate_limit_max_requests} requests per {_rate_limit_window} seconds")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Embedding router shutting down")
    _rate_limit_storage.clear()
