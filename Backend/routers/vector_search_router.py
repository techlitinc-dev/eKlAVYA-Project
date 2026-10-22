"""
Vector Search Router Module

This module defines FastAPI endpoints for vector similarity search and syllabus
management in the Mentor AI EdTech Platform. It provides semantic search capabilities
for finding relevant topics based on student queries.

Endpoints:
- POST /api/vector-search/query: Search for similar topics
- POST /api/vector-search/query/batch: Batch search multiple queries
- GET /api/vector-search/index/status: Get vector index status
- GET /api/vector-search/syllabus/{exam}/{subject}: Get syllabus content
- GET /api/vector-search/syllabus/stats: Get syllabus statistics

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, status, Depends, Path, Query

from models.vector_search_models import (
    SearchRequest,
    SearchResponse,
    BatchSearchRequest,
    BatchSearchResponse,
    SearchFilters
)
from services import vector_search_service, syllabus_service

# Use testing auth if TESTING_MODE is enabled
import os
TESTING_MODE = os.getenv("TESTING_MODE", "false").lower() == "true"
USE_MOCK_SERVICES = os.getenv("USE_MOCK_SERVICES", "false").lower() == "true"

if TESTING_MODE:
    from middleware.testing_auth import get_current_user
else:
    from middleware.auth_middleware import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/vector-search",
    tags=["Vector Search"]
)

# Rate limiting storage (user_id -> deque of timestamps)
_rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque())
_rate_limit_window = 60  # 1 minute in seconds
_rate_limit_max_requests = 50  # Maximum search requests per window


# ============================================================================
# RATE LIMITING
# ============================================================================

def check_rate_limit(user_id: str) -> None:
    """
    Check if user has exceeded rate limit for search operations.
    
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
            f"Search rate limit exceeded for user {user_id}: "
            f"{len(user_requests)} requests in last {_rate_limit_window}s"
        )
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Maximum {_rate_limit_max_requests} search requests per minute allowed",
                "retry_after_seconds": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )
    
    # Add current request timestamp
    user_requests.append(current_time)
    logger.debug(f"Rate limit check passed for user {user_id}: {len(user_requests)}/{_rate_limit_max_requests}")


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.post(
    "/query",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search for similar topics",
    description="""
    Search for similar syllabus topics using Gemini-based semantic search.
    
    This endpoint uses Gemini API to perform intelligent semantic search
    to find the most relevant topics from the JEE/NEET syllabus. Results can be
    filtered by exam, subject, difficulty level, and other criteria.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Rate Limit:** 50 search requests per minute per user
    
    **Requirements:**
    - Query must be 1-500 characters
    - Top-k must be between 1-50 (default: 10)
    - Filters are optional but must match valid values
    
    **Returns:**
    - 200: Search results with relevance scores
    - 400: Invalid request (query validation failed)
    - 401: Authentication failed or token expired
    - 429: Rate limit exceeded
    - 500: Internal server error
    - 503: Search service unavailable
    """,
    responses={
        200: {
            "description": "Search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "query": "What are Newton's laws?",
                        "results": [
                            {
                                "topic": "Newton's Laws of Motion",
                                "chapter": "Mechanics",
                                "content": "Newton's first law states...",
                                "metadata": {
                                    "key_concepts": ["Inertia", "Force"],
                                    "formulas": []
                                },
                                "similarity_score": 0.92,
                                "rank": 1,
                                "exam": "JEE_MAIN",
                                "subject": "Physics",
                                "difficulty": "medium",
                                "weightage": 5.0
                            }
                        ],
                        "total_results": 5,
                        "search_time_ms": 125.5,
                        "cached": False
                    }
                }
            }
        }
    }
)
async def search_topics(
    request: SearchRequest,
    user_id: str = Depends(get_current_user)
) -> SearchResponse:
    """
    Search for similar topics using Gemini-based semantic search.
    
    Args:
        request: SearchRequest containing query and filters
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        SearchResponse with ranked search results
    
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 429 for rate limit exceeded
        HTTPException: 503 if search service is unavailable
        HTTPException: 500 for server errors
    
    Example:
        Request:
        ```json
        {
            "query": "What are Newton's laws of motion?",
            "top_k": 10,
            "filters": {
                "exam": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium"
            },
            "include_metadata": true,
            "min_similarity_score": 0.5
        }
        ```
    """
    try:
        logger.info(f"Search request from user {user_id}: query='{request.query[:50]}...'")
        
        # Check rate limit
        check_rate_limit(user_id)
        
        # Perform vector search
        response = vector_search_service.search_topics(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            use_cache=True,
            include_metadata=request.include_metadata
        )
        
        logger.info(
            f"Search completed for user {user_id}: "
            f"results={response.total_results}, time={response.search_time_ms:.2f}ms, "
            f"cached={response.cached}"
        )
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as ve:
        # Handle validation errors
        logger.warning(f"Validation error during search: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except RuntimeError as re:
        # Handle service unavailable errors
        logger.error(f"Runtime error during search: {re}")
        
        # Check if it's a Gemini API error
        error_msg = str(re)
        if "Gemini" in error_msg or "API" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "Gemini API Service Unavailable",
                    "message": "Search service requires Gemini API to be accessible.",
                    "note": "This feature uses Gemini API for semantic search"
                }
            )
        
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during search: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again later."
        )


@router.post(
    "/query/batch",
    response_model=BatchSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch search multiple queries",
    description="""
    Search for similar topics using multiple queries with Gemini API.
    
    This endpoint processes multiple search queries efficiently using Gemini,
    allowing you to get results for up to 20 queries at once. Each query is
    processed independently with the same filters applied.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Rate Limit:** 50 search requests per minute per user (counts as 1 request regardless of batch size)
    
    **Requirements:**
    - 1-20 queries per request
    - Each query must be 1-500 characters
    - Top-k applies to all queries (1-50, default: 10)
    
    **Returns:**
    - 200: Batch search results
    - 400: Invalid request (validation failed)
    - 401: Authentication failed or token expired
    - 429: Rate limit exceeded
    - 500: Internal server error
    - 503: Search service unavailable
    """,
    responses={
        200: {
            "description": "Batch search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "queries": [
                            "What are Newton's laws?",
                            "Explain electromagnetic induction"
                        ],
                        "results": [],
                        "total_queries": 2,
                        "total_results": 15,
                        "total_search_time_ms": 250.5,
                        "average_search_time_ms": 125.25,
                        "cache_hit_count": 1
                    }
                }
            }
        }
    }
)
async def batch_search_topics(
    request: BatchSearchRequest,
    user_id: str = Depends(get_current_user)
) -> BatchSearchResponse:
    """
    Search for similar topics using multiple queries.
    
    Args:
        request: BatchSearchRequest containing multiple queries
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        BatchSearchResponse with results for each query
    
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 429 for rate limit exceeded
        HTTPException: 503 if search service is unavailable
        HTTPException: 500 for server errors
    
    Example:
        Request:
        ```json
        {
            "queries": [
                "What are Newton's laws?",
                "Explain electromagnetic induction",
                "What is organic chemistry?"
            ],
            "top_k": 5,
            "filters": {
                "exam": "JEE_MAIN"
            },
            "include_metadata": true
        }
        ```
    """
    try:
        logger.info(f"Batch search request from user {user_id}: {len(request.queries)} queries")
        
        # Check rate limit (counts as one request)
        check_rate_limit(user_id)
        
        # Perform batch vector search
        response = vector_search_service.batch_search(
            queries=request.queries,
            top_k=request.top_k,
            filters=request.filters,
            use_cache=True
        )
        
        logger.info(
            f"Batch search completed for user {user_id}: "
            f"queries={response.total_queries}, total_results={response.total_results}, "
            f"time={response.total_search_time_ms:.2f}ms, cache_hits={response.cache_hit_count}"
        )
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as ve:
        # Handle validation errors
        logger.warning(f"Validation error during batch search: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except RuntimeError as re:
        # Handle service unavailable errors
        logger.error(f"Runtime error during batch search: {re}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(re)
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error during batch search: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch search failed. Please try again later."
        )


# ============================================================================
# INDEX STATUS ENDPOINTS
# ============================================================================

@router.get(
    "/index/status",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get vector search index status",
    description="""
    Get the current status and statistics of the Gemini-based search service.
    
    This endpoint provides information about the search service status,
    including health status and search statistics.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Returns:**
    - Service status
    - Search statistics
    - Cache performance
    - Last update timestamp
    """,
    responses={
        200: {
            "description": "Index status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "index": "vector-search-index",
                        "status": "deployed",
                        "health": "healthy",
                        "total_vectors": 15000,
                        "last_updated": "2025-11-26T10:00:00.000Z",
                        "search_stats": {
                            "total_searches": 1250,
                            "cache_hits": 450,
                            "cache_hit_rate": 0.36,
                            "average_search_time_ms": 85.5
                        }
                    }
                }
            }
        }
    }
)
async def get_index_status(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get Gemini-based search service status and statistics.
    
    Args:
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        Dictionary containing service status and statistics
    
    Example:
        Response:
        ```json
        {
            "service": "gemini-search",
            "status": "healthy",
            "health": "healthy",
            "method": "gemini_api",
            "search_stats": {
                "total_searches": 1250,
                "cache_hit_rate": 0.36
            }
        }
        ```
    """
    try:
        logger.info(f"Index status request from user {user_id}")
        
        # Get search statistics
        search_stats = vector_search_service.get_search_stats()
        
        # Build status response
        status_response = {
            "service": "gemini-search",
            "status": "healthy",
            "health": "healthy",
            "method": "gemini_api",
            "note": "Using Gemini API for semantic search (no vector embeddings required)",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "search_stats": {
                "total_searches": search_stats.total_searches,
                "cache_hits": search_stats.cache_hits,
                "cache_misses": search_stats.cache_misses,
                "cache_hit_rate": round(search_stats.cache_hit_rate, 4),
                "total_results_returned": search_stats.total_results_returned,
                "average_results_per_search": search_stats.average_results_per_search,
                "cache_size": search_stats.cache_size,
                "cache_max_size": search_stats.cache_max_size
            }
        }
        
        logger.info(f"Index status retrieved for user {user_id}")
        
        return status_response
    
    except Exception as e:
        # Handle errors gracefully
        logger.error(f"Error retrieving index status: {e}")
        logger.exception("Full traceback:")
        
        # Return degraded status
        return {
            "service": "gemini-search",
            "status": "error",
            "health": "degraded",
            "method": "gemini_api",
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "error": "Failed to retrieve complete status",
            "message": str(e)
        }


# ============================================================================
# SYLLABUS ENDPOINTS
# ============================================================================

@router.get(
    "/syllabus/{exam}/{subject}",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get syllabus content for exam and subject",
    description="""
    Get syllabus topics and content for a specific exam and subject.
    
    This endpoint retrieves the complete syllabus data including chapters,
    topics, subtopics, difficulty levels, and weightage information.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Path Parameters:**
    - exam: JEE_MAIN, JEE_ADVANCED, or NEET
    - subject: Physics, Chemistry, Mathematics (JEE only), or Biology (NEET only)
    
    **Returns:**
    - Complete syllabus structure
    - Topics with metadata
    - Chapter information
    - Weightage and difficulty data
    """,
    responses={
        200: {
            "description": "Syllabus retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "exam": "JEE_MAIN",
                        "subject": "Physics",
                        "topics": [
                            {
                                "topic_name": "Newton's Laws of Motion",
                                "chapter_name": "Mechanics",
                                "difficulty": "medium",
                                "weightage": 5.0
                            }
                        ],
                        "total_topics": 150
                    }
                }
            }
        },
        404: {
            "description": "Syllabus not found for exam/subject combination"
        }
    }
)
async def get_syllabus_content(
    exam: str = Path(
        ...,
        description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)",
        example="JEE_MAIN"
    ),
    subject: str = Path(
        ...,
        description="Subject name (Physics, Chemistry, Mathematics, Biology)",
        example="Physics"
    ),
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get syllabus content for specific exam and subject.
    
    Args:
        exam: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        subject: Subject name (Physics, Chemistry, Mathematics, Biology)
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        Dictionary containing syllabus topics and metadata
    
    Raises:
        HTTPException: 400 for invalid exam/subject combination
        HTTPException: 404 if syllabus file not found
        HTTPException: 500 for server errors
    
    Example:
        GET /api/vector-search/syllabus/JEE_MAIN/Physics
    """
    try:
        logger.info(f"Syllabus request from user {user_id}: {exam} - {subject}")
        
        # Get topics from syllabus service
        topics = syllabus_service.get_topics(exam, subject, use_cache=True)
        
        # Build response
        response = {
            "exam": exam,
            "subject": subject,
            "topics": topics,
            "total_topics": len(topics),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        
        logger.info(f"Syllabus retrieved for user {user_id}: {len(topics)} topics")
        
        return response
    
    except ValueError as ve:
        # Handle validation errors (invalid exam/subject combination)
        logger.warning(f"Validation error retrieving syllabus: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    
    except FileNotFoundError as fnf:
        # Handle missing syllabus files
        logger.warning(f"Syllabus file not found: {fnf}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Syllabus not found for {exam} - {subject}"
        )
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error retrieving syllabus: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve syllabus. Please try again later."
        )


@router.get(
    "/syllabus/stats",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get syllabus statistics",
    description="""
    Get comprehensive statistics about available syllabus content.
    
    This endpoint provides an overview of all available syllabus data,
    including total topics, chapters, subjects, and exams covered in
    the platform.
    
    **Authentication Required:** Bearer token in Authorization header
    
    **Returns:**
    - Total topics across all exams
    - Subjects available per exam
    - Chapter counts
    - Difficulty distribution
    - Weightage summaries
    """,
    responses={
        200: {
            "description": "Statistics retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "total_exams": 3,
                        "total_subjects": 7,
                        "total_topics": 450,
                        "exams": {
                            "JEE_MAIN": {
                                "subjects": ["Physics", "Chemistry", "Mathematics"],
                                "total_topics": 150
                            },
                            "NEET": {
                                "subjects": ["Physics", "Chemistry", "Biology"],
                                "total_topics": 150
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_syllabus_statistics(
    user_id: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get comprehensive syllabus statistics.
    
    Args:
        user_id: Authenticated user ID from dependency injection
    
    Returns:
        Dictionary containing syllabus statistics across all exams and subjects
    
    Example:
        Response:
        ```json
        {
            "total_exams": 3,
            "total_subjects": 7,
            "total_topics": 450,
            "exams": {
                "JEE_MAIN": {
                    "subjects": ["Physics", "Chemistry", "Mathematics"]
                }
            }
        }
        ```
    """
    try:
        logger.info(f"Syllabus statistics request from user {user_id}")
        
        # Define exam-subject mappings
        exam_subjects = {
            "JEE_MAIN": ["Physics", "Chemistry", "Mathematics"],
            "JEE_ADVANCED": ["Physics", "Chemistry", "Mathematics"],
            "NEET": ["Physics", "Chemistry", "Biology"]
        }
        
        # Collect statistics
        total_topics = 0
        total_chapters = 0
        total_subtopics = 0
        exam_stats = {}
        
        for exam, subjects in exam_subjects.items():
            exam_data = {
                "subjects": subjects,
                "total_topics": 0,
                "total_chapters": 0,
                "total_subtopics": 0,
                "subjects_data": {}
            }
            
            for subject in subjects:
                try:
                    # Get syllabus statistics
                    stats = syllabus_service.get_syllabus_stats(exam, subject, use_cache=True)
                    
                    exam_data["total_topics"] += stats.total_topics
                    exam_data["total_chapters"] += stats.total_chapters
                    exam_data["total_subtopics"] += stats.total_subtopics
                    
                    exam_data["subjects_data"][subject] = {
                        "chapters": stats.total_chapters,
                        "topics": stats.total_topics,
                        "subtopics": stats.total_subtopics,
                        "average_weightage": stats.average_topic_weightage,
                        "difficulty_distribution": stats.difficulty_distribution
                    }
                    
                    total_topics += stats.total_topics
                    total_chapters += stats.total_chapters
                    total_subtopics += stats.total_subtopics
                
                except (FileNotFoundError, ValueError):
                    # Skip if syllabus file doesn't exist
                    logger.debug(f"Syllabus not found for {exam} - {subject}, skipping")
                    continue
            
            exam_stats[exam] = exam_data
        
        # Build response
        response = {
            "total_exams": len(exam_subjects),
            "total_subjects": len(set(subject for subjects in exam_subjects.values() for subject in subjects)),
            "total_chapters": total_chapters,
            "total_topics": total_topics,
            "total_subtopics": total_subtopics,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "exams": exam_stats
        }
        
        logger.info(f"Syllabus statistics retrieved for user {user_id}")
        
        return response
    
    except Exception as e:
        # Handle errors gracefully
        logger.error(f"Error retrieving syllabus statistics: {e}")
        logger.exception("Full traceback:")
        
        # Return error response
        return {
            "error": "Failed to retrieve syllabus statistics",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }


# ============================================================================
# ROUTER EVENT HANDLERS
# ============================================================================

@router.on_event("startup")
async def startup_event():
    """Log router initialization."""
    logger.info("Vector search router initialized")
    logger.info(f"Rate limit: {_rate_limit_max_requests} requests per {_rate_limit_window} seconds")


@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Vector search router shutting down")
    _rate_limit_storage.clear()
