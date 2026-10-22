"""
Embedding Generation Data Models

This module defines Pydantic models for embedding generation API requests
and responses in the Mentor AI EdTech Platform. These models provide data
validation, serialization, and documentation for embedding endpoints.

Models:
- EmbeddingRequest: Single text embedding request
- EmbeddingResponse: Single embedding result with metadata
- BatchEmbeddingRequest: Multiple text embedding request
- BatchEmbeddingResponse: Batch embedding results
- EmbeddingMetadata: Metadata about embedding generation

Author: Mentor AI Team
Version: 1.0.0
"""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class EmbeddingRequest(BaseModel):
    """
    Request model for generating a single text embedding.
    
    This model validates the input text for embedding generation.
    Text length is limited to 3000 characters to ensure optimal
    performance and API compliance.
    
    Attributes:
        text: Input text to generate embedding for
        task_type: Type of embedding task (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
        include_metadata: Whether to include detailed metadata in response
    
    Example:
        >>> request = EmbeddingRequest(
        ...     text="Newton's laws of motion explain the relationship between force and motion",
        ...     task_type="RETRIEVAL_DOCUMENT",
        ...     include_metadata=True
        ... )
    """
    
    text: str = Field(
        ...,
        min_length=1,
        max_length=3000,
        description="Text to generate embedding for (1-3000 characters)"
    )
    
    task_type: Literal[
        "RETRIEVAL_DOCUMENT",
        "RETRIEVAL_QUERY",
        "SEMANTIC_SIMILARITY",
        "CLASSIFICATION",
        "CLUSTERING"
    ] = Field(
        default="RETRIEVAL_DOCUMENT",
        description=(
            "Embedding task type: "
            "RETRIEVAL_DOCUMENT for documents to be retrieved, "
            "RETRIEVAL_QUERY for search queries, "
            "SEMANTIC_SIMILARITY for similarity comparison, "
            "CLASSIFICATION for text classification, "
            "CLUSTERING for text clustering"
        )
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Whether to include detailed metadata in the response"
    )
    
    @field_validator("text")
    @classmethod
    def validate_text_not_empty(cls, v: str) -> str:
        """
        Validate that text is not empty or whitespace only.
        
        Args:
            v: Text string to validate
        
        Returns:
            str: Validated and stripped text
        
        Raises:
            ValueError: If text is empty or whitespace only
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Text cannot be empty or contain only whitespace")
        return stripped
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Newton's laws of motion explain the relationship between force and motion",
                "task_type": "RETRIEVAL_DOCUMENT",
                "include_metadata": True
            }
        }
    )


class EmbeddingMetadata(BaseModel):
    """
    Metadata about embedding generation.
    
    Contains information about the embedding model used, dimensions,
    processing time, and caching status.
    
    Attributes:
        model: Name of the embedding model used
        dimension: Dimension of the embedding vector
        timestamp: UTC timestamp when embedding was generated
        cached: Whether the embedding was retrieved from cache
        text_length: Length of the input text in characters
        processing_time_ms: Time taken to generate embedding in milliseconds
    
    Example:
        >>> metadata = EmbeddingMetadata(
        ...     model="textembedding-gecko@003",
        ...     dimension=768,
        ...     timestamp=datetime.utcnow(),
        ...     cached=False,
        ...     text_length=75,
        ...     processing_time_ms=120.5
        ... )
    """
    
    model: str = Field(
        ...,
        description="Embedding model name (e.g., textembedding-gecko@003)"
    )
    
    dimension: int = Field(
        ...,
        ge=1,
        description="Dimension of the embedding vector (typically 768)"
    )
    
    timestamp: datetime = Field(
        ...,
        description="UTC timestamp when embedding was generated"
    )
    
    cached: bool = Field(
        default=False,
        description="Whether the embedding was retrieved from cache"
    )
    
    text_length: int = Field(
        ...,
        ge=0,
        description="Length of the input text in characters"
    )
    
    processing_time_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Processing time in milliseconds"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "model": "textembedding-gecko@003",
                "dimension": 768,
                "timestamp": "2025-11-26T10:30:00.000Z",
                "cached": False,
                "text_length": 75,
                "processing_time_ms": 120.5
            }
        }
    )


class EmbeddingResponse(BaseModel):
    """
    Response model for single text embedding generation.
    
    Contains the generated embedding vector and optional metadata
    about the embedding generation process.
    
    Attributes:
        embedding: List of floating-point values representing the embedding
        dimension: Dimension of the embedding vector
        model: Name of the model used for generation
        timestamp: When the embedding was generated
        metadata: Optional detailed metadata about the generation
    
    Example:
        >>> response = EmbeddingResponse(
        ...     embedding=[0.123, -0.456, 0.789, ...],  # 768 dimensions
        ...     dimension=768,
        ...     model="textembedding-gecko@003",
        ...     timestamp=datetime.utcnow(),
        ...     metadata=EmbeddingMetadata(...)
        ... )
    """
    
    embedding: List[float] = Field(
        ...,
        description="Embedding vector (list of floating-point values)"
    )
    
    dimension: int = Field(
        ...,
        ge=1,
        description="Dimension of the embedding vector"
    )
    
    model: str = Field(
        ...,
        description="Embedding model used for generation"
    )
    
    timestamp: datetime = Field(
        ...,
        description="UTC timestamp when embedding was generated"
    )
    
    metadata: Optional[EmbeddingMetadata] = Field(
        default=None,
        description="Detailed metadata about embedding generation (if requested)"
    )
    
    @field_validator("embedding")
    @classmethod
    def validate_embedding_not_empty(cls, v: List[float]) -> List[float]:
        """
        Validate that embedding vector is not empty.
        
        Args:
            v: Embedding vector to validate
        
        Returns:
            List[float]: Validated embedding vector
        
        Raises:
            ValueError: If embedding is empty
        """
        if not v:
            raise ValueError("Embedding vector cannot be empty")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "embedding": [0.123, -0.456, 0.789, 0.012, -0.345],  # Truncated for example
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
    )


class BatchEmbeddingRequest(BaseModel):
    """
    Request model for generating embeddings for multiple texts.
    
    This model validates a batch of input texts for embedding generation.
    Limited to 100 texts per request for optimal performance.
    
    Attributes:
        texts: List of texts to generate embeddings for
        task_type: Type of embedding task for all texts
        include_metadata: Whether to include metadata for each embedding
    
    Example:
        >>> request = BatchEmbeddingRequest(
        ...     texts=[
        ...         "Newton's laws of motion",
        ...         "Electromagnetic induction principles",
        ...         "Organic chemistry reaction mechanisms"
        ...     ],
        ...     task_type="RETRIEVAL_DOCUMENT",
        ...     include_metadata=True
        ... )
    """
    
    texts: List[str] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of texts to generate embeddings for (1-100 items, each max 3000 chars)"
    )
    
    task_type: Literal[
        "RETRIEVAL_DOCUMENT",
        "RETRIEVAL_QUERY",
        "SEMANTIC_SIMILARITY",
        "CLASSIFICATION",
        "CLUSTERING"
    ] = Field(
        default="RETRIEVAL_DOCUMENT",
        description="Embedding task type applied to all texts"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Whether to include metadata for each embedding"
    )
    
    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v: List[str]) -> List[str]:
        """
        Validate that all texts meet requirements.
        
        Args:
            v: List of texts to validate
        
        Returns:
            List[str]: Validated list of texts
        
        Raises:
            ValueError: If any text is invalid
        """
        if not v:
            raise ValueError("Texts list cannot be empty")
        
        for i, text in enumerate(v):
            # Check if text is empty
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} is empty or whitespace only")
            
            # Check text length
            if len(text) > 3000:
                raise ValueError(
                    f"Text at index {i} exceeds maximum length of 3000 characters "
                    f"(current: {len(text)} characters)"
                )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "texts": [
                    "Newton's laws of motion explain force and motion relationships",
                    "Electromagnetic induction describes how changing magnetic fields create electric currents",
                    "Organic chemistry studies carbon-based compounds and their reactions"
                ],
                "task_type": "RETRIEVAL_DOCUMENT",
                "include_metadata": True
            }
        }
    )


class BatchEmbeddingResponse(BaseModel):
    """
    Response model for batch embedding generation.
    
    Contains a list of embedding responses for each input text,
    along with batch-level statistics.
    
    Attributes:
        embeddings: List of embedding responses, one for each input text
        total_count: Total number of embeddings generated
        successful_count: Number of successfully generated embeddings
        failed_count: Number of failed embeddings
        total_processing_time_ms: Total time taken for batch processing
        cache_hit_count: Number of embeddings retrieved from cache
    
    Example:
        >>> response = BatchEmbeddingResponse(
        ...     embeddings=[
        ...         EmbeddingResponse(...),
        ...         EmbeddingResponse(...),
        ...         EmbeddingResponse(...)
        ...     ],
        ...     total_count=3,
        ...     successful_count=3,
        ...     failed_count=0,
        ...     total_processing_time_ms=350.2,
        ...     cache_hit_count=1
        ... )
    """
    
    embeddings: List[EmbeddingResponse] = Field(
        ...,
        description="List of embedding responses for each input text"
    )
    
    total_count: int = Field(
        ...,
        ge=0,
        description="Total number of texts processed"
    )
    
    successful_count: int = Field(
        ...,
        ge=0,
        description="Number of successfully generated embeddings"
    )
    
    failed_count: int = Field(
        default=0,
        ge=0,
        description="Number of failed embeddings"
    )
    
    total_processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Total processing time for the batch in milliseconds"
    )
    
    cache_hit_count: int = Field(
        default=0,
        ge=0,
        description="Number of embeddings retrieved from cache"
    )
    
    @field_validator("total_count")
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """
        Validate that total count matches embeddings list length.
        
        Args:
            v: Total count value
            info: Validation info containing other fields
        
        Returns:
            int: Validated total count
        """
        if 'embeddings' in info.data:
            embeddings_count = len(info.data['embeddings'])
            if v != embeddings_count:
                raise ValueError(
                    f"Total count ({v}) must match number of embeddings ({embeddings_count})"
                )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "embeddings": [
                    {
                        "embedding": [0.123, -0.456, 0.789],
                        "dimension": 768,
                        "model": "textembedding-gecko@003",
                        "timestamp": "2025-11-26T10:30:00.000Z",
                        "metadata": {
                            "model": "textembedding-gecko@003",
                            "dimension": 768,
                            "timestamp": "2025-11-26T10:30:00.000Z",
                            "cached": False,
                            "text_length": 63,
                            "processing_time_ms": 115.3
                        }
                    },
                    {
                        "embedding": [0.234, -0.567, 0.890],
                        "dimension": 768,
                        "model": "textembedding-gecko@003",
                        "timestamp": "2025-11-26T10:30:00.100Z",
                        "metadata": {
                            "model": "textembedding-gecko@003",
                            "dimension": 768,
                            "timestamp": "2025-11-26T10:30:00.100Z",
                            "cached": True,
                            "text_length": 89,
                            "processing_time_ms": 5.2
                        }
                    }
                ],
                "total_count": 2,
                "successful_count": 2,
                "failed_count": 0,
                "total_processing_time_ms": 120.5,
                "cache_hit_count": 1
            }
        }
    )
