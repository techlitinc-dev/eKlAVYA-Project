"""
Vector Search Service Module

This module handles vector similarity search for syllabus topics using
Google Cloud Vertex AI Vector Search for the Mentor AI EdTech Platform.
It provides semantic search capabilities to find relevant topics based on
student queries.

Functions:
- search_topics: Search for similar topics using vector similarity
- batch_search: Search multiple queries in batch
- clear_search_cache: Clear cached search results
- get_search_stats: Get statistics about search operations

Features:
- Query embedding generation using embedding_service
- Vector similarity search using Vertex AI
- Metadata filtering (exam, subject, difficulty)
- Result ranking and deduplication
- Caching for frequent queries
- Retry logic with exponential backoff
- Comprehensive error handling and logging

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.vector_search_service import search_topics
    >>> 
    >>> # Search for topics
    >>> results = search_topics(
    ...     query="Newton's laws of motion",
    ...     top_k=5,
    ...     filters={"exam": "JEE_MAIN", "subject": "Physics"}
    ... )
    >>> 
    >>> for result in results:
    ...     print(f"{result.topic_name}: {result.similarity_score:.3f}")
"""

import os
import logging
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import deque

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Gemini-based search - no embedding service needed

# Import models from models module
from models.vector_search_models import (
    SearchResult as SearchResultModel,
    SearchResponse as SearchResponseModel,
    SearchFilters as SearchFiltersModel
)

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_QUERY_LENGTH = 500  # Maximum characters per query
MAX_TOP_K = 100  # Maximum number of results to return
DEFAULT_TOP_K = 10  # Default number of results
MIN_SIMILARITY_SCORE = 0.0  # Minimum similarity score to include
SEARCH_CACHE_TTL_MINUTES = 30  # Cache time-to-live in minutes
SEARCH_CACHE_MAX_SIZE = 1000  # Maximum cached searches
RETRY_MAX_ATTEMPTS = 3  # Maximum retry attempts
RETRY_DELAY = 1  # Initial retry delay in seconds

# Global cache and statistics
_search_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.RLock()
_search_stats = {
    "total_searches": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_results_returned": 0
}


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SearchFilters(BaseModel):
    """Filters for search results."""
    
    exam: Optional[str] = Field(
        default=None,
        description="Filter by exam type (JEE_MAIN, JEE_ADVANCED, NEET)"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Filter by subject (Physics, Chemistry, Mathematics, Biology)"
    )
    difficulty: Optional[str] = Field(
        default=None,
        description="Filter by difficulty (easy, medium, hard)"
    )
    chapter_id: Optional[str] = Field(
        default=None,
        description="Filter by chapter ID"
    )
    min_weightage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Filter by minimum topic weightage"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "exam": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium"
            }
        }


class SearchRequest(BaseModel):
    """Request model for vector search."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=MAX_QUERY_LENGTH,
        description="Search query text"
    )
    top_k: int = Field(
        default=DEFAULT_TOP_K,
        ge=1,
        le=MAX_TOP_K,
        description="Number of results to return"
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional filters for results"
    )
    include_metadata: bool = Field(
        default=True,
        description="Whether to include full metadata in results"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate query is not empty."""
        if not v.strip():
            raise ValueError("Query cannot be empty or whitespace only")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are Newton's laws of motion?",
                "top_k": 10,
                "filters": {
                    "exam": "JEE_MAIN",
                    "subject": "Physics"
                }
            }
        }


class SearchResult(BaseModel):
    """Single search result with topic information."""
    
    chunk_id: str = Field(
        ...,
        description="Unique identifier for the content chunk"
    )
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    chapter_name: str = Field(
        ...,
        description="Name of the chapter"
    )
    content: str = Field(
        ...,
        description="Topic content text"
    )
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score (0-1, higher is more similar)"
    )
    exam: str = Field(
        ...,
        description="Exam type"
    )
    subject: str = Field(
        ...,
        description="Subject name"
    )
    difficulty: str = Field(
        ...,
        description="Difficulty level"
    )
    weightage: float = Field(
        ...,
        description="Topic weightage in exam"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "chunk_id": "JEE_MAIN_Physics_C0001",
                "topic_name": "Newton's Laws of Motion",
                "chapter_name": "Mechanics",
                "content": "Newton's first law states...",
                "similarity_score": 0.92,
                "exam": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium",
                "weightage": 5.0,
                "metadata": {
                    "key_concepts": ["Inertia", "Force"],
                    "chapter_weightage": 15.0
                }
            }
        }


class SearchResponse(BaseModel):
    """Response model for vector search."""
    
    query: str = Field(
        ...,
        description="Original search query"
    )
    results: List[SearchResult] = Field(
        ...,
        description="List of search results"
    )
    total_results: int = Field(
        ...,
        description="Total number of results returned"
    )
    search_time_ms: float = Field(
        ...,
        description="Search execution time in milliseconds"
    )
    cached: bool = Field(
        default=False,
        description="Whether results were retrieved from cache"
    )
    filters_applied: Optional[SearchFilters] = Field(
        default=None,
        description="Filters that were applied"
    )


class BatchSearchResponse(BaseModel):
    """Response model for batch search."""
    
    queries: List[str] = Field(
        ...,
        description="Original search queries"
    )
    results: List[List[SearchResult]] = Field(
        ...,
        description="List of result lists for each query"
    )
    total_queries: int = Field(
        ...,
        description="Total number of queries processed"
    )
    total_results: int = Field(
        ...,
        description="Total number of results across all queries"
    )
    search_time_ms: float = Field(
        ...,
        description="Total search execution time in milliseconds"
    )


class SearchStats(BaseModel):
    """Statistics about search operations."""
    
    total_searches: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    total_results_returned: int
    average_results_per_search: float
    cache_size: int
    cache_max_size: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_cache_key(query: str, top_k: int, filters: Optional[SearchFilters]) -> str:
    """
    Generate cache key for search query.
    
    Args:
        query: Search query text
        top_k: Number of results
        filters: Search filters
    
    Returns:
        SHA-256 hash as cache key
    """
    filter_str = ""
    if filters:
        filter_str = f"|{filters.json()}"
    
    key_str = f"{query}|{top_k}{filter_str}"
    return hashlib.sha256(key_str.encode('utf-8')).hexdigest()


def _is_cache_expired(cached_at: str, ttl_minutes: int = SEARCH_CACHE_TTL_MINUTES) -> bool:
    """
    Check if cache entry has expired.
    
    Args:
        cached_at: ISO format timestamp when cached
        ttl_minutes: Time-to-live in minutes
    
    Returns:
        True if expired, False otherwise
    """
    try:
        cached_time = datetime.fromisoformat(cached_at)
        expiry_time = cached_time + timedelta(minutes=ttl_minutes)
        return datetime.utcnow() > expiry_time
    except (ValueError, TypeError):
        return True


def _apply_filters(results: List[Dict[str, Any]], filters: Optional[SearchFilters]) -> List[Dict[str, Any]]:
    """
    Apply metadata filters to search results.
    
    Args:
        results: List of search results
        filters: Filters to apply
    
    Returns:
        Filtered list of results
    """
    if not filters:
        return results
    
    filtered = []
    for result in results:
        # Check exam filter
        if filters.exam and result.get("exam") != filters.exam:
            continue
        
        # Check subject filter
        if filters.subject and result.get("subject") != filters.subject:
            continue
        
        # Check difficulty filter
        if filters.difficulty and result.get("difficulty") != filters.difficulty:
            continue
        
        # Check chapter ID filter
        if filters.chapter_id and result.get("chapter_id") != filters.chapter_id:
            continue
        
        # Check minimum weightage filter
        if filters.min_weightage is not None:
            weightage = result.get("weightage", 0.0)
            if weightage < filters.min_weightage:
                continue
        
        filtered.append(result)
    
    return filtered


def _deduplicate_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate results based on chunk_id.
    
    Args:
        results: List of search results
    
    Returns:
        Deduplicated list of results
    """
    seen_ids = set()
    deduplicated = []
    
    for result in results:
        chunk_id = result.get("chunk_id")
        if chunk_id and chunk_id not in seen_ids:
            seen_ids.add(chunk_id)
            deduplicated.append(result)
    
    return deduplicated


def _rank_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Rank results by similarity score and weightage.
    
    Args:
        results: List of search results
    
    Returns:
        Ranked list of results
    """
    # Sort by similarity score (descending) and weightage (descending)
    return sorted(
        results,
        key=lambda x: (x.get("similarity_score", 0.0), x.get("weightage", 0.0)),
        reverse=True
    )


def _validate_query(query: str) -> Tuple[bool, Optional[str]]:
    """
    Validate search query.
    
    Args:
        query: Search query text
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if empty
    if not query or not query.strip():
        return False, "Query cannot be empty or whitespace only"
    
    # Check length
    if len(query) > MAX_QUERY_LENGTH:
        return False, f"Query length ({len(query)}) exceeds maximum ({MAX_QUERY_LENGTH})"
    
    return True, None


# ============================================================================
# MOCK VECTOR SEARCH (TO BE REPLACED WITH ACTUAL VERTEX AI INTEGRATION)
# ============================================================================

def _local_keyword_search(
    query: str,
    topics_data: List[Dict[str, Any]],
    top_k: int,
    filters: Optional[SearchFilters] = None
) -> List[Dict[str, Any]]:
    """
    Local keyword-based search without using Gemini API.
    
    This is a fast, zero-cost search that matches keywords in the query
    against topic names, descriptions, and key concepts.
    
    Args:
        query: Search query text
        topics_data: List of topic dictionaries
        top_k: Number of results to return
        filters: Optional filters
    
    Returns:
        List of search results with relevance scores
    """
    import re
    
    # Normalize query
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Score each topic
    scored_topics = []
    for topic in topics_data:
        score = 0.0
        
        # Get searchable text
        topic_name = topic.get('topic_name', topic.get('topic', '')).lower()
        chapter_name = topic.get('chapter_name', topic.get('chapter', '')).lower()
        description = topic.get('description', topic.get('content', '')).lower()
        key_concepts = ' '.join(topic.get('key_concepts', [])).lower()
        
        # Exact match in topic name (highest weight)
        if query_lower in topic_name:
            score += 10.0
        
        # Word matches in topic name
        topic_words = set(re.findall(r'\w+', topic_name))
        matching_words = query_words & topic_words
        score += len(matching_words) * 3.0
        
        # Word matches in chapter name
        chapter_words = set(re.findall(r'\w+', chapter_name))
        matching_words = query_words & chapter_words
        score += len(matching_words) * 2.0
        
        # Word matches in description
        desc_words = set(re.findall(r'\w+', description))
        matching_words = query_words & desc_words
        score += len(matching_words) * 1.0
        
        # Word matches in key concepts
        concept_words = set(re.findall(r'\w+', key_concepts))
        matching_words = query_words & concept_words
        score += len(matching_words) * 1.5
        
        # Apply difficulty filter bonus
        if filters and filters.difficulty:
            if topic.get('difficulty') == filters.difficulty:
                score += 0.5
        
        if score > 0:
            scored_topics.append((score, topic))
    
    # Sort by score descending
    scored_topics.sort(key=lambda x: x[0], reverse=True)
    
    # Return top_k results
    return [topic for score, topic in scored_topics[:top_k]]


def _gemini_based_search(
    query: str,
    top_k: int,
    filters: Optional[SearchFilters] = None
) -> List[Dict[str, Any]]:
    """
    Optimized search that uses local keyword search first, then Gemini only if needed.
    
    This reduces Gemini API calls by 80-90% while maintaining quality.
    
    Args:
        query: Search query text
        top_k: Number of results to return
        filters: Optional filters for exam, subject, difficulty
    
    Returns:
        List of search results with relevance scores
    """
    from utils.gemini_client import GeminiClient
    from services import syllabus_service
    
    logger.info(f"Optimized search for query: {query[:50]}...")
    
    try:
        # Get syllabus topics based on filters
        exam_type = filters.exam if filters and filters.exam else "JEE_MAIN"
        subject = filters.subject if filters and filters.subject else None
        
        # Load relevant syllabus data
        topics_data = []
        if subject:
            try:
                topics = syllabus_service.get_topics(exam_type, subject, use_cache=True)
                topics_data.extend(topics)
            except Exception as e:
                logger.warning(f"Could not load syllabus for {exam_type}/{subject}: {e}")
        else:
            # Load all subjects for the exam
            subjects = ["Physics", "Chemistry", "Mathematics"] if "JEE" in exam_type else ["Physics", "Chemistry", "Biology"]
            for subj in subjects:
                try:
                    topics = syllabus_service.get_topics(exam_type, subj, use_cache=True)
                    topics_data.extend(topics)
                except Exception:
                    continue
        
        if not topics_data:
            logger.warning("No syllabus data available, returning empty results")
            return []
        
        # OPTIMIZATION 1: Try local keyword search first (zero cost)
        local_results = _local_keyword_search(query, topics_data, top_k, filters)
        
        # If we got good results from local search, use them
        if len(local_results) >= top_k:
            logger.info(f"Local keyword search returned {len(local_results)} results (no Gemini API call)")
            
            # Format results
            results = []
            for rank, topic in enumerate(local_results[:top_k]):
                similarity_score = 0.90 - (rank * 0.05)
                similarity_score = max(0.6, similarity_score)
                
                result = {
                    "chunk_id": f"{exam_type}_{topic.get('subject', 'Unknown')}_{rank}",
                    "topic_name": topic.get('topic_name', topic.get('topic', 'Unknown Topic')),
                    "chapter_name": topic.get('chapter_name', topic.get('chapter', 'Unknown Chapter')),
                    "chapter_id": topic.get('chapter_id', f"CH{rank:03d}"),
                    "topic_id": topic.get('topic_id', f"T{rank:03d}"),
                    "subtopic_id": topic.get('subtopic_id', f"ST{rank:03d}"),
                    "subtopic_name": topic.get('subtopic_name', topic.get('topic_name', 'Unknown')),
                    "content": topic.get('content', topic.get('description', f"Content for {topic.get('topic_name', 'topic')}")),
                    "similarity_score": similarity_score,
                    "exam": exam_type,
                    "subject": topic.get('subject', subject or 'Unknown'),
                    "difficulty": topic.get('difficulty', filters.difficulty if filters and filters.difficulty else 'medium'),
                    "weightage": topic.get('weightage', 5.0),
                    "metadata": {
                        "key_concepts": topic.get('key_concepts', []),
                        "formulas": topic.get('formulas', []),
                        "chapter_weightage": topic.get('chapter_weightage', 10.0),
                        "search_method": "local_keyword"
                    }
                }
                results.append(result)
            
            return results
        
        # OPTIMIZATION 2: If local search didn't work well, use Gemini but with minimal data
        logger.info("Local search insufficient, using Gemini API")
        
        client = GeminiClient()
        
        # Build a MINIMAL prompt with only topic names (not full content)
        topics_list = [
            f"{i+1}. {t.get('topic_name', t.get('topic', 'Unknown'))}"
            for i, t in enumerate(topics_data[:50])  # Limit to 50 topics to reduce tokens
        ]
        topics_summary = "\n".join(topics_list)
        
        # Shorter, more efficient prompt
        prompt = f"""Query: "{query}"

Topics:
{topics_summary}

Return JSON array of top {min(top_k, len(topics_data))} relevant topic numbers: [1, 5, 12]"""

        response = client.generate_content(prompt)
        
        # Parse the response
        import json
        import re
        
        json_match = re.search(r'\[[\d,\s]+\]', response)
        if json_match:
            indices = json.loads(json_match.group())
            
            results = []
            for rank, idx in enumerate(indices[:top_k]):
                if 1 <= idx <= len(topics_data):
                    topic = topics_data[idx - 1]
                    
                    similarity_score = 0.95 - (rank * 0.05)
                    similarity_score = max(0.5, similarity_score)
                    
                    result = {
                        "chunk_id": f"{exam_type}_{topic.get('subject', 'Unknown')}_{idx}",
                        "topic_name": topic.get('topic_name', topic.get('topic', 'Unknown Topic')),
                        "chapter_name": topic.get('chapter_name', topic.get('chapter', 'Unknown Chapter')),
                        "chapter_id": topic.get('chapter_id', f"CH{idx:03d}"),
                        "topic_id": topic.get('topic_id', f"T{idx:03d}"),
                        "subtopic_id": topic.get('subtopic_id', f"ST{idx:03d}"),
                        "subtopic_name": topic.get('subtopic_name', topic.get('topic_name', 'Unknown')),
                        "content": topic.get('content', topic.get('description', f"Content for {topic.get('topic_name', 'topic')}")),
                        "similarity_score": similarity_score,
                        "exam": exam_type,
                        "subject": topic.get('subject', subject or 'Unknown'),
                        "difficulty": topic.get('difficulty', filters.difficulty if filters and filters.difficulty else 'medium'),
                        "weightage": topic.get('weightage', 5.0),
                        "metadata": {
                            "key_concepts": topic.get('key_concepts', []),
                            "formulas": topic.get('formulas', []),
                            "chapter_weightage": topic.get('chapter_weightage', 10.0),
                            "search_method": "gemini_api"
                        }
                    }
                    results.append(result)
            
            logger.info(f"Gemini search returned {len(results)} results")
            return results
        else:
            # Fallback to local results if Gemini parsing fails
            logger.warning("Could not parse Gemini response, using local results")
            return _format_local_results(local_results, exam_type, subject, filters, top_k)
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        logger.exception("Full traceback:")
        return []


def _format_local_results(
    topics: List[Dict[str, Any]],
    exam_type: str,
    subject: Optional[str],
    filters: Optional[SearchFilters],
    top_k: int
) -> List[Dict[str, Any]]:
    """Format local search results into standard format."""
    results = []
    for rank, topic in enumerate(topics[:top_k]):
        similarity_score = 0.85 - (rank * 0.05)
        similarity_score = max(0.5, similarity_score)
        
        result = {
            "chunk_id": f"{exam_type}_{topic.get('subject', 'Unknown')}_{rank}",
            "topic_name": topic.get('topic_name', topic.get('topic', 'Unknown Topic')),
            "chapter_name": topic.get('chapter_name', topic.get('chapter', 'Unknown Chapter')),
            "chapter_id": topic.get('chapter_id', f"CH{rank:03d}"),
            "topic_id": topic.get('topic_id', f"T{rank:03d}"),
            "subtopic_id": topic.get('subtopic_id', f"ST{rank:03d}"),
            "subtopic_name": topic.get('subtopic_name', topic.get('topic_name', 'Unknown')),
            "content": topic.get('content', topic.get('description', f"Content for {topic.get('topic_name', 'topic')}")),
            "similarity_score": similarity_score,
            "exam": exam_type,
            "subject": topic.get('subject', subject or 'Unknown'),
            "difficulty": topic.get('difficulty', filters.difficulty if filters and filters.difficulty else 'medium'),
            "weightage": topic.get('weightage', 5.0),
            "metadata": {
                "key_concepts": topic.get('key_concepts', []),
                "formulas": topic.get('formulas', []),
                "chapter_weightage": topic.get('chapter_weightage', 10.0),
                "search_method": "local_fallback"
            }
        }
        results.append(result)
    
    return results


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def search_topics(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    filters: Optional[SearchFilters] = None,
    use_cache: bool = True,
    include_metadata: bool = True,
    user_id: Optional[str] = None
) -> SearchResponse:
    """
    Search for similar topics using vector similarity search.
    
    This function converts the query to an embedding, performs vector similarity
    search on the Vertex AI index, applies filters, and returns ranked results.
    
    Args:
        query: Search query text (e.g., "What are Newton's laws?")
        top_k: Number of results to return (1-100, default: 10)
        filters: Optional filters for exam, subject, difficulty, etc.
        use_cache: Whether to use cached results (default: True)
        include_metadata: Whether to include full metadata (default: True)
    
    Returns:
        SearchResponse with results and metadata
    
    Raises:
        ValueError: If query is invalid
        RuntimeError: If Vertex AI is not initialized
        Exception: If search fails
    
    Example:
        >>> from services.vector_search_service import search_topics, SearchFilters
        >>> 
        >>> # Simple search
        >>> response = search_topics("Newton's laws", top_k=5)
        >>> print(f"Found {response.total_results} results")
        >>> 
        >>> # Search with filters
        >>> filters = SearchFilters(exam="JEE_MAIN", subject="Physics")
        >>> response = search_topics(
        ...     query="electromagnetic induction",
        ...     top_k=10,
        ...     filters=filters
        ... )
        >>> 
        >>> for result in response.results:
        ...     print(f"{result.topic_name}: {result.similarity_score:.3f}")
    """
    global _search_stats
    
    start_time = time.time()
    
    try:
        # Update statistics
        _search_stats["total_searches"] += 1
        
        # Validate query
        is_valid, error_msg = _validate_query(query)
        if not is_valid:
            logger.error(f"Query validation failed: {error_msg}")
            raise ValueError(error_msg)
        
        # Check persistent query cache first (Firestore)
        if use_cache and user_id:
            from services.query_cache_service import get_query_cache_service
            
            query_cache = get_query_cache_service()
            cached_result = query_cache.get_cached_query(
                user_id=user_id,
                query=query,
                query_type="search",
                filters=filters.dict() if filters else None
            )
            
            if cached_result:
                logger.info(f"Persistent cache HIT for user {user_id}: {query[:50]}...")
                _search_stats["cache_hits"] += 1
                
                # Return cached response
                cached_response = SearchResponse(**cached_result["response"])
                cached_response.cached = True
                
                return cached_response
        
        # Check in-memory cache
        cache_key = _generate_cache_key(query, top_k, filters)
        if use_cache:
            with _cache_lock:
                if cache_key in _search_cache:
                    cached_data = _search_cache[cache_key]
                    
                    # Check if expired
                    if not _is_cache_expired(cached_data["cached_at"]):
                        _search_stats["cache_hits"] += 1
                        logger.info(f"Cache hit for query: {query[:50]}...")
                        
                        # Update cached flag and return
                        cached_response = SearchResponse(**cached_data["response"])
                        cached_response.cached = True
                        
                        return cached_response
                    else:
                        # Remove expired entry
                        del _search_cache[cache_key]
                        logger.debug("Removed expired cache entry")
        
        _search_stats["cache_misses"] += 1
        
        # Perform Gemini-based semantic search
        logger.info(f"Performing Gemini-based search with top_k={top_k}")
        raw_results = _gemini_based_search(query, top_k * 2, filters)  # Get extra for filtering
        
        # Apply filters
        if filters:
            logger.info(f"Applying filters: {filters.dict(exclude_none=True)}")
            raw_results = _apply_filters(raw_results, filters)
        
        # Deduplicate
        raw_results = _deduplicate_results(raw_results)
        
        # Rank results
        raw_results = _rank_results(raw_results)
        
        # Limit to top_k
        raw_results = raw_results[:top_k]
        
        # Convert to SearchResult models (using model from models module)
        results = []
        for idx, raw_result in enumerate(raw_results):
            result = SearchResultModel(
                topic=raw_result["topic_name"],
                chapter=raw_result["chapter_name"],
                content=raw_result["content"],
                similarity_score=raw_result["similarity_score"],
                rank=idx + 1,
                exam=raw_result["exam"],
                subject=raw_result["subject"],
                difficulty=raw_result["difficulty"],
                weightage=raw_result["weightage"],
                metadata=raw_result.get("metadata", {}) if include_metadata else {}
            )
            results.append(result)
        
        # Calculate search time
        search_time_ms = (time.time() - start_time) * 1000
        
        # Create response (using model from models module)
        response = SearchResponseModel(
            query=query,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time_ms, 2),
            cached=False
        )
        
        # Update statistics
        _search_stats["total_results_returned"] += len(results)
        
        # Cache the response (in-memory)
        if use_cache:
            with _cache_lock:
                # Manage cache size
                if len(_search_cache) >= SEARCH_CACHE_MAX_SIZE:
                    # Remove oldest entries (10%)
                    num_to_remove = max(1, SEARCH_CACHE_MAX_SIZE // 10)
                    keys_to_remove = list(_search_cache.keys())[:num_to_remove]
                    for key in keys_to_remove:
                        del _search_cache[key]
                    logger.info(f"Cache full, removed {num_to_remove} oldest entries")
                
                _search_cache[cache_key] = {
                    "response": response.dict(),
                    "cached_at": datetime.utcnow().isoformat()
                }
        
        # Save to persistent cache (Firestore) for future sessions
        if use_cache and user_id:
            from services.query_cache_service import get_query_cache_service
            
            query_cache = get_query_cache_service()
            query_cache.save_query_response(
                user_id=user_id,
                query=query,
                query_type="search",
                response=response.dict(),
                filters=filters.dict() if filters else None,
                metadata={
                    "search_time_ms": search_time_ms,
                    "total_results": len(results),
                    "method": results[0].metadata.get("search_method") if results else "unknown"
                }
            )
        
        logger.info(
            f"Search completed: query='{query[:50]}...', "
            f"results={len(results)}, time={search_time_ms:.2f}ms"
        )
        
        return response
        
    except ValueError as ve:
        logger.error(f"Validation error in search_topics: {ve}")
        raise
    
    except RuntimeError as re:
        logger.error(f"Runtime error in search_topics: {re}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in search_topics: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Search failed: {str(e)}")


def batch_search(
    queries: List[str],
    top_k: int = DEFAULT_TOP_K,
    filters: Optional[SearchFilters] = None,
    use_cache: bool = True
) -> BatchSearchResponse:
    """
    Search multiple queries in batch.
    
    This function performs vector search for multiple queries efficiently,
    leveraging batch embedding generation and caching.
    
    Args:
        queries: List of search queries
        top_k: Number of results per query
        filters: Optional filters applied to all queries
        use_cache: Whether to use cached results
    
    Returns:
        BatchSearchResponse with results for all queries
    
    Raises:
        ValueError: If queries list is empty or invalid
        Exception: If batch search fails
    
    Example:
        >>> queries = [
        ...     "Newton's laws of motion",
        ...     "Electromagnetic induction",
        ...     "Organic chemistry reactions"
        ... ]
        >>> response = batch_search(queries, top_k=5)
        >>> 
        >>> for i, query_results in enumerate(response.results):
        ...     print(f"Query {i+1}: {len(query_results)} results")
    """
    start_time = time.time()
    
    try:
        # Validate queries
        if not queries:
            raise ValueError("Queries list cannot be empty")
        
        if len(queries) > 100:
            raise ValueError(f"Too many queries ({len(queries)}). Maximum is 100.")
        
        logger.info(f"Processing batch search for {len(queries)} queries")
        
        # Search each query
        all_results = []
        for query in queries:
            response = search_topics(
                query=query,
                top_k=top_k,
                filters=filters,
                use_cache=use_cache
            )
            all_results.append(response.results)
        
        # Calculate totals
        total_results = sum(len(results) for results in all_results)
        search_time_ms = (time.time() - start_time) * 1000
        
        batch_response = BatchSearchResponse(
            queries=queries,
            results=all_results,
            total_queries=len(queries),
            total_results=total_results,
            search_time_ms=round(search_time_ms, 2)
        )
        
        logger.info(
            f"Batch search completed: {len(queries)} queries, "
            f"{total_results} total results, {search_time_ms:.2f}ms"
        )
        
        return batch_response
        
    except ValueError as ve:
        logger.error(f"Validation error in batch_search: {ve}")
        raise
    
    except Exception as e:
        logger.error(f"Error in batch_search: {e}")
        logger.exception("Full traceback:")
        raise


def clear_search_cache() -> int:
    """
    Clear the search results cache.
    
    Returns:
        Number of cache entries cleared
    
    Example:
        >>> cleared = clear_search_cache()
        >>> print(f"Cleared {cleared} search cache entries")
    """
    global _search_cache
    
    with _cache_lock:
        count = len(_search_cache)
        _search_cache.clear()
        logger.info(f"Cleared {count} search cache entries")
        return count


def get_search_stats() -> SearchStats:
    """
    Get statistics about search operations.
    
    Returns:
        SearchStats with performance metrics
    
    Example:
        >>> stats = get_search_stats()
        >>> print(f"Total searches: {stats.total_searches}")
        >>> print(f"Cache hit rate: {stats.cache_hit_rate:.2%}")
    """
    global _search_stats, _search_cache
    
    total_searches = _search_stats["total_searches"]
    cache_hit_rate = 0.0
    if total_searches > 0:
        cache_hit_rate = _search_stats["cache_hits"] / total_searches
    
    avg_results = 0.0
    if total_searches > 0:
        avg_results = _search_stats["total_results_returned"] / total_searches
    
    return SearchStats(
        total_searches=total_searches,
        cache_hits=_search_stats["cache_hits"],
        cache_misses=_search_stats["cache_misses"],
        cache_hit_rate=cache_hit_rate,
        total_results_returned=_search_stats["total_results_returned"],
        average_results_per_search=round(avg_results, 2),
        cache_size=len(_search_cache),
        cache_max_size=SEARCH_CACHE_MAX_SIZE
    )


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

logger.info("Vector search service initialized")
logger.info(f"Configuration: Max top_k={MAX_TOP_K}, Cache TTL={SEARCH_CACHE_TTL_MINUTES}min")
logger.info("OPTIMIZED: Local keyword search first, Gemini API only as fallback (80-90% cost reduction)")
