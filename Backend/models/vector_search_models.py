"""
Vector Search Data Models

This module defines Pydantic models for vector search API requests and
responses in the Mentor AI EdTech Platform. These models provide data
validation, serialization, and documentation for vector search endpoints.

Models:
- SearchFilters: Filters for search results (exam, subject, difficulty)
- SearchRequest: Single query search request
- SearchResult: Individual search result with metadata
- SearchResponse: Single query search response
- BatchSearchRequest: Multiple query search request
- BatchSearchResponse: Batch search response
- SearchMetadata: Metadata about search operation

Author: Mentor AI Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class SearchFilters(BaseModel):
    """
    Filters for refining vector search results.
    
    This model allows filtering search results by exam type, subject,
    difficulty level, chapter, and topic weightage to provide more
    targeted results.
    
    Attributes:
        exam: Filter by exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        subject: Filter by subject (Physics, Chemistry, Mathematics, Biology)
        difficulty: Filter by difficulty level (easy, medium, hard)
        chapter_id: Filter by specific chapter ID
        min_weightage: Filter by minimum topic weightage percentage
        max_weightage: Filter by maximum topic weightage percentage
    
    Example:
        >>> filters = SearchFilters(
        ...     exam="JEE_MAIN",
        ...     subject="Physics",
        ...     difficulty="medium",
        ...     min_weightage=5.0
        ... )
    """
    
    exam: Optional[Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]] = Field(
        default=None,
        description="Filter by exam type: JEE_MAIN, JEE_ADVANCED, or NEET"
    )
    
    subject: Optional[Literal["Physics", "Chemistry", "Mathematics", "Biology"]] = Field(
        default=None,
        description="Filter by subject: Physics, Chemistry, Mathematics, or Biology"
    )
    
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Field(
        default=None,
        description="Filter by difficulty level: easy, medium, or hard"
    )
    
    chapter_id: Optional[str] = Field(
        default=None,
        description="Filter by specific chapter ID (e.g., CH01)"
    )
    
    min_weightage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Filter by minimum topic weightage percentage (0-100)"
    )
    
    max_weightage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Filter by maximum topic weightage percentage (0-100)"
    )
    
    @field_validator("max_weightage")
    @classmethod
    def validate_weightage_range(cls, v: Optional[float], info) -> Optional[float]:
        """
        Validate that max_weightage is greater than min_weightage.
        
        Args:
            v: Max weightage value
            info: Validation info containing other fields
        
        Returns:
            Optional[float]: Validated max weightage
        
        Raises:
            ValueError: If max_weightage is less than min_weightage
        """
        if v is not None and 'min_weightage' in info.data:
            min_val = info.data['min_weightage']
            if min_val is not None and v < min_val:
                raise ValueError(
                    f"max_weightage ({v}) must be greater than or equal to "
                    f"min_weightage ({min_val})"
                )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "exam": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium",
                "min_weightage": 5.0
            }
        }
    )


class SearchRequest(BaseModel):
    """
    Request model for vector similarity search.
    
    This model validates search queries and parameters for finding
    similar topics in the syllabus using vector embeddings.
    
    Attributes:
        query: Search query text (natural language question or topic)
        top_k: Number of results to return (1-50)
        filters: Optional filters to refine search results
        include_metadata: Whether to include full metadata in results
        min_similarity_score: Minimum similarity score threshold (0-1)
    
    Example:
        >>> request = SearchRequest(
        ...     query="What are Newton's laws of motion?",
        ...     top_k=10,
        ...     filters=SearchFilters(exam="JEE_MAIN", subject="Physics"),
        ...     include_metadata=True,
        ...     min_similarity_score=0.5
        ... )
    """
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query text (1-500 characters)"
    )
    
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of results to return (1-50, default: 10)"
    )
    
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional filters to refine search results"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Whether to include full metadata in results"
    )
    
    min_similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0-1, default: 0)"
    )
    
    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """
        Validate that query is not empty or whitespace only.
        
        Args:
            v: Query string to validate
        
        Returns:
            str: Validated and stripped query
        
        Raises:
            ValueError: If query is empty or whitespace only
        """
        stripped = v.strip()
        if not stripped:
            raise ValueError("Query cannot be empty or contain only whitespace")
        return stripped
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are Newton's laws of motion?",
                "top_k": 10,
                "filters": {
                    "exam": "JEE_MAIN",
                    "subject": "Physics",
                    "difficulty": "medium"
                },
                "include_metadata": True,
                "min_similarity_score": 0.5
            }
        }
    )


class SearchMetadata(BaseModel):
    """
    Additional metadata for search results.
    
    Contains supplementary information about the topic including
    key concepts, formulas, chapter weightage, and other relevant data.
    
    Attributes:
        key_concepts: List of key concepts covered in the topic
        formulas: List of important formulas (if applicable)
        chapter_weightage: Weightage of the parent chapter
        topic_id: Unique identifier for the topic
        subtopic_id: Unique identifier for the subtopic
        word_count: Number of words in the content
    
    Example:
        >>> metadata = SearchMetadata(
        ...     key_concepts=["Inertia", "Force", "Motion"],
        ...     formulas=["F = ma"],
        ...     chapter_weightage=15.0,
        ...     topic_id="T01",
        ...     subtopic_id="ST01",
        ...     word_count=125
        ... )
    """
    
    key_concepts: List[str] = Field(
        default_factory=list,
        description="List of key concepts covered in the topic"
    )
    
    formulas: List[str] = Field(
        default_factory=list,
        description="List of important formulas (if applicable)"
    )
    
    chapter_weightage: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Weightage of the parent chapter in percentage"
    )
    
    topic_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the topic"
    )
    
    subtopic_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for the subtopic"
    )
    
    word_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Number of words in the content"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key_concepts": ["Inertia", "Force", "Motion"],
                "formulas": ["F = ma"],
                "chapter_weightage": 15.0,
                "topic_id": "T01",
                "subtopic_id": "ST01",
                "word_count": 125
            }
        }
    )


class SearchResult(BaseModel):
    """
    Individual search result with topic information and similarity score.
    
    Represents a single matched topic from the vector search, including
    the topic content, metadata, and similarity score.
    
    Attributes:
        topic: Topic name or title
        chapter: Chapter name
        content: Topic content text
        metadata: Additional metadata about the topic
        similarity_score: Similarity score (0-1, higher is more similar)
        rank: Result ranking position (1-based)
        exam: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        subject: Subject name
        difficulty: Difficulty level (easy, medium, hard)
        weightage: Topic weightage in exam percentage
    
    Example:
        >>> result = SearchResult(
        ...     topic="Newton's Laws of Motion",
        ...     chapter="Mechanics",
        ...     content="Newton's first law states...",
        ...     metadata={"key_concepts": ["Inertia", "Force"]},
        ...     similarity_score=0.92,
        ...     rank=1,
        ...     exam="JEE_MAIN",
        ...     subject="Physics",
        ...     difficulty="medium",
        ...     weightage=5.0
        ... )
    """
    
    topic: str = Field(
        ...,
        description="Topic name or title"
    )
    
    chapter: str = Field(
        ...,
        description="Chapter name containing this topic"
    )
    
    content: str = Field(
        ...,
        description="Topic content text"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the topic"
    )
    
    similarity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Similarity score (0-1, higher is more similar)"
    )
    
    rank: int = Field(
        ...,
        ge=1,
        description="Result ranking position (1-based)"
    )
    
    exam: str = Field(
        ...,
        description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)"
    )
    
    subject: str = Field(
        ...,
        description="Subject name (Physics, Chemistry, Mathematics, Biology)"
    )
    
    difficulty: str = Field(
        ...,
        description="Difficulty level (easy, medium, hard)"
    )
    
    weightage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Topic weightage in exam percentage"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "topic": "Newton's Laws of Motion",
                "chapter": "Mechanics",
                "content": "Newton's first law states that an object at rest stays at rest and an object in motion stays in motion with the same speed and in the same direction unless acted upon by an unbalanced force.",
                "metadata": {
                    "key_concepts": ["Inertia", "Force", "Motion"],
                    "formulas": [],
                    "chapter_weightage": 15.0,
                    "topic_id": "T01",
                    "subtopic_id": "ST01"
                },
                "similarity_score": 0.92,
                "rank": 1,
                "exam": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium",
                "weightage": 5.0
            }
        }
    )


class SearchResponse(BaseModel):
    """
    Response model for vector similarity search.
    
    Contains the search results, query information, and search statistics.
    
    Attributes:
        query: Original search query
        results: List of search results ordered by similarity
        total_results: Total number of results returned
        search_time_ms: Search execution time in milliseconds
        cached: Whether results were retrieved from cache
        filters_applied: Filters that were applied to the search
        embedding_time_ms: Time taken to generate query embedding
    
    Example:
        >>> response = SearchResponse(
        ...     query="What are Newton's laws?",
        ...     results=[SearchResult(...), SearchResult(...)],
        ...     total_results=2,
        ...     search_time_ms=125.5,
        ...     cached=False,
        ...     filters_applied=SearchFilters(exam="JEE_MAIN"),
        ...     embedding_time_ms=45.2
        ... )
    """
    
    query: str = Field(
        ...,
        description="Original search query"
    )
    
    results: List[SearchResult] = Field(
        ...,
        description="List of search results ordered by similarity score"
    )
    
    total_results: int = Field(
        ...,
        ge=0,
        description="Total number of results returned"
    )
    
    search_time_ms: float = Field(
        ...,
        ge=0,
        description="Total search execution time in milliseconds"
    )
    
    cached: bool = Field(
        default=False,
        description="Whether results were retrieved from cache"
    )
    
    filters_applied: Optional[SearchFilters] = Field(
        default=None,
        description="Filters that were applied to the search"
    )
    
    embedding_time_ms: Optional[float] = Field(
        default=None,
        ge=0,
        description="Time taken to generate query embedding in milliseconds"
    )
    
    @field_validator("total_results")
    @classmethod
    def validate_total_results(cls, v: int, info) -> int:
        """
        Validate that total_results matches results list length.
        
        Args:
            v: Total results value
            info: Validation info containing other fields
        
        Returns:
            int: Validated total results
        """
        if 'results' in info.data:
            results_count = len(info.data['results'])
            if v != results_count:
                raise ValueError(
                    f"total_results ({v}) must match number of results ({results_count})"
                )
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are Newton's laws of motion?",
                "results": [
                    {
                        "topic": "Newton's Laws of Motion",
                        "chapter": "Mechanics",
                        "content": "Newton's first law states that an object at rest stays at rest...",
                        "metadata": {
                            "key_concepts": ["Inertia", "Force", "Motion"],
                            "formulas": [],
                            "chapter_weightage": 15.0
                        },
                        "similarity_score": 0.92,
                        "rank": 1,
                        "exam": "JEE_MAIN",
                        "subject": "Physics",
                        "difficulty": "medium",
                        "weightage": 5.0
                    },
                    {
                        "topic": "Newton's Laws of Motion",
                        "chapter": "Mechanics",
                        "content": "Newton's second law states that the acceleration of an object...",
                        "metadata": {
                            "key_concepts": ["Force", "Mass", "Acceleration"],
                            "formulas": ["F = ma"],
                            "chapter_weightage": 15.0
                        },
                        "similarity_score": 0.88,
                        "rank": 2,
                        "exam": "JEE_MAIN",
                        "subject": "Physics",
                        "difficulty": "medium",
                        "weightage": 5.0
                    }
                ],
                "total_results": 2,
                "search_time_ms": 125.5,
                "cached": False,
                "filters_applied": {
                    "exam": "JEE_MAIN",
                    "subject": "Physics"
                },
                "embedding_time_ms": 45.2
            }
        }
    )


class BatchSearchRequest(BaseModel):
    """
    Request model for batch vector similarity search.
    
    This model validates multiple search queries for batch processing.
    Limited to 20 queries per request for optimal performance.
    
    Attributes:
        queries: List of search queries (1-20 items)
        top_k: Number of results per query
        filters: Optional filters applied to all queries
        include_metadata: Whether to include full metadata
        min_similarity_score: Minimum similarity score threshold
    
    Example:
        >>> request = BatchSearchRequest(
        ...     queries=[
        ...         "What are Newton's laws?",
        ...         "Explain electromagnetic induction",
        ...         "What is organic chemistry?"
        ...     ],
        ...     top_k=5,
        ...     filters=SearchFilters(exam="JEE_MAIN"),
        ...     include_metadata=True
        ... )
    """
    
    queries: List[str] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="List of search queries (1-20 items, each max 500 chars)"
    )
    
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of results per query (1-50, default: 10)"
    )
    
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional filters applied to all queries"
    )
    
    include_metadata: bool = Field(
        default=True,
        description="Whether to include full metadata in results"
    )
    
    min_similarity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold (0-1)"
    )
    
    @field_validator("queries")
    @classmethod
    def validate_queries(cls, v: List[str]) -> List[str]:
        """
        Validate that all queries meet requirements.
        
        Args:
            v: List of queries to validate
        
        Returns:
            List[str]: Validated list of queries
        
        Raises:
            ValueError: If any query is invalid
        """
        if not v:
            raise ValueError("Queries list cannot be empty")
        
        for i, query in enumerate(v):
            # Check if query is empty
            if not query or not query.strip():
                raise ValueError(f"Query at index {i} is empty or whitespace only")
            
            # Check query length
            if len(query) > 500:
                raise ValueError(
                    f"Query at index {i} exceeds maximum length of 500 characters "
                    f"(current: {len(query)} characters)"
                )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queries": [
                    "What are Newton's laws of motion?",
                    "Explain electromagnetic induction principles",
                    "What is organic chemistry and its reactions?"
                ],
                "top_k": 5,
                "filters": {
                    "exam": "JEE_MAIN"
                },
                "include_metadata": True,
                "min_similarity_score": 0.5
            }
        }
    )


class BatchSearchResponse(BaseModel):
    """
    Response model for batch vector similarity search.
    
    Contains search responses for each query along with batch-level
    statistics and timing information.
    
    Attributes:
        queries: Original search queries
        results: List of search responses, one for each query
        total_queries: Total number of queries processed
        total_results: Total number of results across all queries
        total_search_time_ms: Total search execution time
        average_search_time_ms: Average time per query
        cache_hit_count: Number of queries served from cache
    
    Example:
        >>> response = BatchSearchResponse(
        ...     queries=["query1", "query2"],
        ...     results=[SearchResponse(...), SearchResponse(...)],
        ...     total_queries=2,
        ...     total_results=15,
        ...     total_search_time_ms=250.5,
        ...     average_search_time_ms=125.25,
        ...     cache_hit_count=1
        ... )
    """
    
    queries: List[str] = Field(
        ...,
        description="Original search queries"
    )
    
    results: List[SearchResponse] = Field(
        ...,
        description="List of search responses, one for each query"
    )
    
    total_queries: int = Field(
        ...,
        ge=0,
        description="Total number of queries processed"
    )
    
    total_results: int = Field(
        ...,
        ge=0,
        description="Total number of results across all queries"
    )
    
    total_search_time_ms: float = Field(
        ...,
        ge=0,
        description="Total search execution time in milliseconds"
    )
    
    average_search_time_ms: float = Field(
        ...,
        ge=0,
        description="Average search time per query in milliseconds"
    )
    
    cache_hit_count: int = Field(
        default=0,
        ge=0,
        description="Number of queries served from cache"
    )
    
    @field_validator("total_queries")
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """
        Validate that counts match list lengths.
        
        Args:
            v: Total queries value
            info: Validation info containing other fields
        
        Returns:
            int: Validated total queries
        """
        if 'queries' in info.data and 'results' in info.data:
            queries_count = len(info.data['queries'])
            results_count = len(info.data['results'])
            
            if v != queries_count:
                raise ValueError(
                    f"total_queries ({v}) must match number of queries ({queries_count})"
                )
            
            if queries_count != results_count:
                raise ValueError(
                    f"Number of queries ({queries_count}) must match "
                    f"number of results ({results_count})"
                )
        
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "queries": [
                    "What are Newton's laws?",
                    "Explain electromagnetic induction"
                ],
                "results": [
                    {
                        "query": "What are Newton's laws?",
                        "results": [],
                        "total_results": 5,
                        "search_time_ms": 120.5,
                        "cached": False
                    },
                    {
                        "query": "Explain electromagnetic induction",
                        "results": [],
                        "total_results": 5,
                        "search_time_ms": 130.0,
                        "cached": True
                    }
                ],
                "total_queries": 2,
                "total_results": 10,
                "total_search_time_ms": 250.5,
                "average_search_time_ms": 125.25,
                "cache_hit_count": 1
            }
        }
    )
