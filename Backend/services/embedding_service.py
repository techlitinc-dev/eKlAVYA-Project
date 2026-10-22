"""
Embedding Generation Service Module

This module handles text embedding generation using Google Cloud Vertex AI
for the Mentor AI EdTech Platform. It provides functions to generate embeddings
for single texts and batches, with caching, rate limiting, and error handling.

Functions:
- generate_embedding: Generate embedding for a single text
- generate_batch_embeddings: Generate embeddings for multiple texts
- clear_embedding_cache: Clear the embedding cache
- get_embedding_stats: Get statistics about embedding operations

Features:
- Rate limiting (100 requests per minute)
- In-memory caching to avoid regenerating same embeddings
- Retry logic with exponential backoff
- Input validation (max 3000 characters per text)
- Comprehensive error handling and logging
- Embedding metadata (model, timestamp, dimensions)

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import logging
import hashlib
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import deque
from functools import wraps

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Import Vertex AI client utilities
from utils.vertex_ai_client import (
    generate_embeddings as vertex_generate_embeddings,
    get_embedding_client,
    is_vertex_ai_initialized,
    EMBEDDING_MODEL,
    DEFAULT_EMBEDDING_DIMENSION
)

# Import embedding cache utility
from utils.embedding_cache import get_global_cache

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_LENGTH = 3000  # Maximum characters per text
MAX_BATCH_SIZE = 250  # Maximum texts per batch request
RATE_LIMIT_REQUESTS = 100  # Maximum requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds (1 minute)

# Global rate limiting structures
_request_timestamps: deque = deque()
_total_requests = 0


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class EmbeddingMetadata(BaseModel):
    """Metadata for generated embeddings."""
    
    model: str = Field(
        default=EMBEDDING_MODEL,
        description="Embedding model used for generation"
    )
    dimension: int = Field(
        default=DEFAULT_EMBEDDING_DIMENSION,
        description="Dimension of the embedding vector"
    )
    timestamp: str = Field(
        description="UTC timestamp when embedding was generated"
    )
    cached: bool = Field(
        default=False,
        description="Whether the embedding was retrieved from cache"
    )
    text_length: int = Field(
        description="Length of the input text in characters"
    )


class EmbeddingResult(BaseModel):
    """Result of embedding generation."""
    
    embedding: List[float] = Field(
        description="Embedding vector"
    )
    metadata: EmbeddingMetadata = Field(
        description="Metadata about the embedding"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "embedding": [0.123, -0.456, 0.789, "..."],
                "metadata": {
                    "model": "textembedding-gecko@003",
                    "dimension": 768,
                    "timestamp": "2025-11-26T10:30:00Z",
                    "cached": False,
                    "text_length": 42
                }
            }
        }


class BatchEmbeddingResult(BaseModel):
    """Result of batch embedding generation."""
    
    embeddings: List[List[float]] = Field(
        description="List of embedding vectors"
    )
    metadata: List[EmbeddingMetadata] = Field(
        description="Metadata for each embedding"
    )
    total_count: int = Field(
        description="Total number of embeddings generated"
    )
    cache_hit_count: int = Field(
        description="Number of embeddings retrieved from cache"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "embeddings": [[0.123, -0.456], [0.789, -0.012]],
                "metadata": [
                    {
                        "model": "textembedding-gecko@003",
                        "dimension": 768,
                        "timestamp": "2025-11-26T10:30:00Z",
                        "cached": False,
                        "text_length": 42
                    }
                ],
                "total_count": 2,
                "cache_hit_count": 0
            }
        }


class EmbeddingStats(BaseModel):
    """Statistics about embedding operations."""
    
    total_requests: int
    cache_hits: int
    cache_misses: int
    cache_hit_rate: float
    cache_size: int
    cache_max_size: int


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_text(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate input text for embedding generation.
    
    Args:
        text: Input text to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    
    Example:
        >>> is_valid, error = validate_text("Sample text")
        >>> if not is_valid:
        ...     print(error)
    """
    # Check if text is empty
    if not text or not text.strip():
        return False, "Text cannot be empty or contain only whitespace"
    
    # Check text length
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"Text length ({len(text)}) exceeds maximum allowed ({MAX_TEXT_LENGTH})"
    
    # Text is valid
    return True, None


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing excessive whitespace and special characters.
    
    Args:
        text: Input text to sanitize
    
    Returns:
        Sanitized text
    
    Example:
        >>> cleaned = sanitize_text("  Hello\\n\\nWorld  ")
        >>> print(cleaned)
        'Hello World'
    """
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Replace multiple whitespaces with single space
    text = ' '.join(text.split())
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    return text


# ============================================================================
# RATE LIMITING
# ============================================================================

def check_rate_limit() -> Tuple[bool, Optional[str]]:
    """
    Check if current request is within rate limits.
    
    Returns:
        Tuple of (is_allowed, error_message)
    
    Example:
        >>> allowed, error = check_rate_limit()
        >>> if not allowed:
        ...     print(error)
    """
    global _request_timestamps
    
    current_time = time.time()
    
    # Remove timestamps older than the rate limit window
    while _request_timestamps and _request_timestamps[0] < current_time - RATE_LIMIT_WINDOW:
        _request_timestamps.popleft()
    
    # Check if we've exceeded the rate limit
    if len(_request_timestamps) >= RATE_LIMIT_REQUESTS:
        oldest_timestamp = _request_timestamps[0]
        wait_time = int(RATE_LIMIT_WINDOW - (current_time - oldest_timestamp))
        return False, f"Rate limit exceeded. Please wait {wait_time} seconds before retrying."
    
    # Add current timestamp
    _request_timestamps.append(current_time)
    
    return True, None


# ============================================================================
# CACHING FUNCTIONS
# ============================================================================

def clear_embedding_cache() -> int:
    """
    Clear the entire embedding cache.
    
    Returns:
        Number of cache entries cleared
    
    Example:
        >>> cleared = clear_embedding_cache()
        >>> print(f"Cleared {cleared} cache entries")
    """
    cache = get_global_cache()
    return cache.clear()


# ============================================================================
# CORE EMBEDDING FUNCTIONS
# ============================================================================

def generate_embedding(
    text: str,
    task_type: str = "RETRIEVAL_DOCUMENT",
    use_cache: bool = True
) -> EmbeddingResult:
    """
    Generate embedding for a single text using Vertex AI.
    
    This function generates a 768-dimensional embedding vector for the input
    text using the textembedding-gecko@003 model. It includes input validation,
    rate limiting, caching, and comprehensive error handling.
    
    Args:
        text: Input text to generate embedding for (max 3000 characters)
        task_type: Type of embedding task. Options:
            - RETRIEVAL_DOCUMENT: For documents to be retrieved
            - RETRIEVAL_QUERY: For search queries
            - SEMANTIC_SIMILARITY: For similarity comparison
            - CLASSIFICATION: For text classification
            - CLUSTERING: For text clustering
        use_cache: Whether to use cached embeddings (default: True)
    
    Returns:
        EmbeddingResult with embedding vector and metadata
    
    Raises:
        ValueError: If text is invalid (empty, too long, etc.)
        RuntimeError: If Vertex AI is not initialized
        Exception: If embedding generation fails after retries
    
    Example:
        >>> result = generate_embedding("JEE Main physics concepts")
        >>> print(f"Embedding dimension: {len(result.embedding)}")
        768
        >>> print(f"Model used: {result.metadata.model}")
        textembedding-gecko@003
        
        >>> # For search queries
        >>> query_result = generate_embedding(
        ...     "What are Newton's laws?",
        ...     task_type="RETRIEVAL_QUERY"
        ... )
    """
    global _total_requests
    
    try:
        _total_requests += 1
        
        # Sanitize input text
        text = sanitize_text(text)
        
        # Validate input text
        is_valid, error_message = validate_text(text)
        if not is_valid:
            logger.error(f"Text validation failed: {error_message}")
            raise ValueError(error_message)
        
        # Check Vertex AI initialization
        if not is_vertex_ai_initialized():
            error_msg = "Vertex AI is not initialized. Please check configuration."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        # Get cache instance
        cache = get_global_cache()
        
        # Check cache first
        if use_cache:
            cached_embedding = cache.get(text)
            if cached_embedding is not None:
                logger.info(f"Returning cached embedding for text: {text[:50]}...")
                metadata = EmbeddingMetadata(
                    model=EMBEDDING_MODEL,
                    dimension=len(cached_embedding),
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    cached=True,
                    text_length=len(text)
                )
                return EmbeddingResult(
                    embedding=cached_embedding,
                    metadata=metadata
                )
        
        # Check rate limit
        allowed, error_message = check_rate_limit()
        if not allowed:
            logger.warning(f"Rate limit exceeded: {error_message}")
            raise RuntimeError(error_message)
        
        # Generate embedding using Vertex AI
        logger.info(f"Generating embedding for text: {text[:50]}... (length: {len(text)})")
        
        embeddings = vertex_generate_embeddings(
            texts=[text],
            task_type=task_type,
            auto_truncate=True
        )
        
        embedding = embeddings[0]
        
        # Create metadata
        metadata = EmbeddingMetadata(
            model=EMBEDDING_MODEL,
            dimension=len(embedding),
            timestamp=datetime.utcnow().isoformat() + 'Z',
            cached=False,
            text_length=len(text)
        )
        
        # Add to cache
        if use_cache:
            cache.set(text, embedding, metadata.dict())
        
        logger.info(f"Successfully generated embedding (dimension: {len(embedding)})")
        
        return EmbeddingResult(
            embedding=embedding,
            metadata=metadata
        )
        
    except ValueError as ve:
        logger.error(f"Validation error in generate_embedding: {ve}")
        raise
    
    except RuntimeError as re:
        logger.error(f"Runtime error in generate_embedding: {re}")
        raise
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Unexpected error in generate_embedding: {e}")
        logger.exception("Full traceback:")
        
        # Check if it's a model access error
        if "404" in error_msg and "Publisher Model" in error_msg:
            raise RuntimeError(
                "Vertex AI embedding model is not accessible. "
                "Please enable the Vertex AI API and ensure your project has access to the embedding model. "
                "Visit: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com"
            )
        
        raise Exception(f"Failed to generate embedding: {str(e)}")


def generate_batch_embeddings(
    texts: List[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    use_cache: bool = True
) -> BatchEmbeddingResult:
    """
    Generate embeddings for multiple texts using Vertex AI.
    
    This function generates embeddings for a batch of texts efficiently.
    It uses caching to avoid regenerating embeddings for texts that have
    been processed before, and handles rate limiting automatically.
    
    Args:
        texts: List of input texts (max 250 texts per call)
        task_type: Type of embedding task (same options as generate_embedding)
        use_cache: Whether to use cached embeddings (default: True)
    
    Returns:
        BatchEmbeddingResult with embeddings, metadata, and statistics
    
    Raises:
        ValueError: If texts list is invalid (empty, too many items, etc.)
        RuntimeError: If Vertex AI is not initialized
        Exception: If embedding generation fails
    
    Example:
        >>> texts = [
        ...     "JEE Main physics syllabus",
        ...     "NEET biology chapters",
        ...     "Mathematics important formulas"
        ... ]
        >>> result = generate_batch_embeddings(texts)
        >>> print(f"Generated {result.total_count} embeddings")
        >>> print(f"Cache hits: {result.cache_hit_count}")
        >>> print(f"Dimension: {result.metadata[0].dimension}")
        
        >>> # Process large dataset in batches
        >>> all_texts = [...]  # 1000 texts
        >>> batch_size = 100
        >>> for i in range(0, len(all_texts), batch_size):
        ...     batch = all_texts[i:i + batch_size]
        ...     result = generate_batch_embeddings(batch)
    """
    try:
        # Validate input
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if len(texts) > MAX_BATCH_SIZE:
            raise ValueError(
                f"Batch size ({len(texts)}) exceeds maximum allowed ({MAX_BATCH_SIZE}). "
                f"Please split into smaller batches."
            )
        
        # Check Vertex AI initialization
        if not is_vertex_ai_initialized():
            error_msg = "Vertex AI is not initialized. Please check configuration."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"Processing batch of {len(texts)} texts")
        
        # Get cache instance
        cache = get_global_cache()
        
        # Sanitize all texts
        sanitized_texts = [sanitize_text(text) for text in texts]
        
        # Validate all texts
        for i, text in enumerate(sanitized_texts):
            is_valid, error_message = validate_text(text)
            if not is_valid:
                raise ValueError(f"Text at index {i} is invalid: {error_message}")
        
        # Separate cached and non-cached texts
        embeddings_list: List[List[float]] = []
        metadata_list: List[EmbeddingMetadata] = []
        texts_to_generate: List[str] = []
        text_indices: List[int] = []
        cache_hit_count = 0
        
        # Check cache for each text
        for i, text in enumerate(sanitized_texts):
            if use_cache:
                cached_embedding = cache.get(text)
                if cached_embedding is not None:
                    # Use cached embedding
                    embeddings_list.append(cached_embedding)
                    metadata = EmbeddingMetadata(
                        model=EMBEDDING_MODEL,
                        dimension=len(cached_embedding),
                        timestamp=datetime.utcnow().isoformat() + 'Z',
                        cached=True,
                        text_length=len(text)
                    )
                    metadata_list.append(metadata)
                    cache_hit_count += 1
                    continue
            
            # Need to generate this embedding
            texts_to_generate.append(text)
            text_indices.append(i)
        
        logger.info(f"Cache hits: {cache_hit_count}, Need to generate: {len(texts_to_generate)}")
        
        # Generate embeddings for non-cached texts
        if texts_to_generate:
            # Check rate limit
            allowed, error_message = check_rate_limit()
            if not allowed:
                logger.warning(f"Rate limit exceeded: {error_message}")
                raise RuntimeError(error_message)
            
            # Generate embeddings in batch
            logger.info(f"Generating {len(texts_to_generate)} new embeddings")
            new_embeddings = vertex_generate_embeddings(
                texts=texts_to_generate,
                task_type=task_type,
                auto_truncate=True
            )
            
            # Process generated embeddings
            for i, (text, embedding) in enumerate(zip(texts_to_generate, new_embeddings)):
                # Create metadata
                metadata = EmbeddingMetadata(
                    model=EMBEDDING_MODEL,
                    dimension=len(embedding),
                    timestamp=datetime.utcnow().isoformat() + 'Z',
                    cached=False,
                    text_length=len(text)
                )
                
                # Add to cache
                if use_cache:
                    cache.set(text, embedding, metadata.dict())
                
                # Store results (need to maintain original order)
                original_index = text_indices[i]
                embeddings_list.insert(original_index, embedding)
                metadata_list.insert(original_index, metadata)
        
        logger.info(f"Successfully generated batch of {len(embeddings_list)} embeddings")
        
        return BatchEmbeddingResult(
            embeddings=embeddings_list,
            metadata=metadata_list,
            total_count=len(embeddings_list),
            cache_hit_count=cache_hit_count
        )
        
    except ValueError as ve:
        logger.error(f"Validation error in generate_batch_embeddings: {ve}")
        raise
    
    except RuntimeError as re:
        logger.error(f"Runtime error in generate_batch_embeddings: {re}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in generate_batch_embeddings: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to generate batch embeddings: {str(e)}")


# ============================================================================
# STATISTICS AND MONITORING
# ============================================================================

def get_embedding_stats() -> EmbeddingStats:
    """
    Get statistics about embedding operations.
    
    Returns:
        EmbeddingStats with cache performance and usage metrics
    
    Example:
        >>> stats = get_embedding_stats()
        >>> print(f"Total requests: {stats.total_requests}")
        >>> print(f"Cache hit rate: {stats.cache_hit_rate:.2%}")
        >>> print(f"Cache size: {stats.cache_size}/{stats.cache_max_size}")
    """
    cache = get_global_cache()
    cache_stats = cache.get_stats()
    
    return EmbeddingStats(
        total_requests=_total_requests,
        cache_hits=cache_stats["hits"],
        cache_misses=cache_stats["misses"],
        cache_hit_rate=cache_stats["hit_rate"],
        cache_size=cache_stats["size"],
        cache_max_size=cache_stats["max_size"]
    )


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

logger.info("Embedding service initialized")
logger.info(f"Configuration: Max text length={MAX_TEXT_LENGTH}, "
           f"Max batch size={MAX_BATCH_SIZE}, "
           f"Rate limit={RATE_LIMIT_REQUESTS}/min")
