"""
Question Router

This module defines FastAPI endpoints for question management and retrieval
in the Mentor AI EdTech Platform. It provides CRUD operations and search
functionality for exam questions stored in Firestore.

Endpoints:
- POST /generate: Generate new questions using RAG
- GET /{question_id}: Get specific question by ID
- GET /by-topic/{topic}: Get questions for a topic with pagination
- POST /validate: Validate question quality
- POST /search: Search questions with filters
- GET /stats: Get question statistics

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> # Start the server
    >>> uvicorn main:app --reload
    >>> 
    >>> # Get questions by topic
    >>> curl http://localhost:8000/api/questions/by-topic/Calculus?exam_type=JEE_MAIN&limit=5
"""

import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from collections import defaultdict

from fastapi import APIRouter, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse

# Firebase/Firestore imports
from google.cloud import firestore

# Import models
from models.rag_models import RAGRequest, RAGResponse, ErrorResponse
from models.question_models import (
    Question,
    QuestionFilter,
    QuestionBatch,
    QuestionMetadata
)
from services.question_validator import QuestionValidator, ValidationResult

# Import services
from services.rag_service import RAGService


# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# Create router
router = APIRouter(
    prefix="/api/questions",
    tags=["Questions"],
    responses={
        400: {
            "model": ErrorResponse,
            "description": "Bad Request - Invalid parameters"
        },
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Question or resource not found"
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal Server Error"
        }
    }
)


# Initialize services
rag_service = RAGService(enable_caching=True, high_quality_only=True)
question_validator = QuestionValidator()

# Initialize Firestore client
try:
    db = firestore.Client()
    logger.info("Firestore client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {str(e)}")
    db = None


# Constants
QUESTIONS_COLLECTION = "questions"
DEFAULT_LIMIT = 20
MAX_LIMIT = 100


# ============================================================================
# QUESTION GENERATION ENDPOINT
# ============================================================================

@router.post(
    "/generate",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate new questions",
    description="""
    Generate new questions using the RAG (Retrieval-Augmented Generation) pipeline.
    
    This endpoint internally uses the RAG service to:
    1. Retrieve relevant context from syllabus
    2. Generate questions using Gemini Flash
    3. Validate and filter for quality
    4. Store in Firestore automatically
    
    **Features:**
    - Automatic storage in Firestore
    - Quality filtering (score > 80)
    - Caching support
    - Metadata tracking
    
    **Use Cases:**
    - Creating new practice questions
    - Building question banks
    - Topic-specific question generation
    """,
    response_description="Generated questions with metadata"
)
async def generate_questions(request: RAGRequest) -> RAGResponse:
    """
    Generate questions using RAG pipeline.
    
    Args:
        request: RAGRequest with topic, exam_type, difficulty, count
    
    Returns:
        RAGResponse: Generated questions with metadata and statistics
    
    Raises:
        HTTPException 400: Invalid request parameters
        HTTPException 500: Generation failed
    
    Example Request:
        ```json
        {
            "topic": "Limits and Continuity",
            "exam_type": "JEE_MAIN",
            "difficulty": "medium",
            "num_questions": 5,
            "use_cache": true
        }
        ```
    """
    try:
        logger.info(
            f"Generating questions - Topic: {request.topic}, "
            f"Exam: {request.exam_type}, Count: {request.num_questions}"
        )
        
        # Use RAG service to generate questions
        result = rag_service.generate_for_topic(
            topic=request.topic,
            exam_type=request.exam_type,
            difficulty=request.difficulty,
            count=request.num_questions,
            use_cache=request.use_cache
        )
        
        # Convert to RAGResponse
        response = RAGResponse(
            questions=result.questions,
            metadata=result.metadata,
            generation_time=result.generation_time,
            quality_stats=result.quality_stats,
            cache_hit=result.cached,
            total_questions=len(result.questions)
        )
        
        logger.info(
            f"Successfully generated {len(result.questions)} questions "
            f"for topic: {request.topic}"
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


# ============================================================================
# QUESTION RETRIEVAL ENDPOINTS
# ============================================================================

@router.get(
    "/{question_id}",
    response_model=Question,
    status_code=status.HTTP_200_OK,
    summary="Get question by ID",
    description="""
    Retrieve a specific question by its Firestore document ID.
    
    **Use Cases:**
    - Displaying question details
    - Editing existing questions
    - Reviewing question quality
    """,
    response_description="Question details"
)
async def get_question(
    question_id: str = Path(..., description="Firestore document ID of the question")
) -> Question:
    """
    Get a specific question by ID.
    
    Args:
        question_id: Firestore document ID
    
    Returns:
        Question: Question details
    
    Raises:
        HTTPException 404: Question not found
        HTTPException 500: Database error
    
    Example:
        ```
        GET /api/questions/q_abc123
        ```
    """
    try:
        logger.info(f"Retrieving question: {question_id}")
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Get question from Firestore
        doc_ref = db.collection(QUESTIONS_COLLECTION).document(question_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"Question not found: {question_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question with ID '{question_id}' not found"
            )
        
        # Convert to Question model
        question_data = doc.to_dict()
        question_data['id'] = doc.id
        question = Question.from_dict(question_data)
        
        logger.info(f"Successfully retrieved question: {question_id}")
        return question
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to retrieve question: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve question: {str(e)}"
        )


@router.get(
    "/by-topic/{topic}",
    response_model=QuestionBatch,
    status_code=status.HTTP_200_OK,
    summary="Get questions by topic",
    description="""
    Retrieve all questions for a specific topic with optional filtering and pagination.
    
    **Query Parameters:**
    - exam_type: Filter by exam type (JEE_MAIN, JEE_ADVANCED, NEET)
    - difficulty: Filter by difficulty (easy, medium, hard)
    - limit: Number of questions to return (default: 20, max: 100)
    - offset: Number of questions to skip (for pagination)
    - sort_by: Sort field (created_at, quality_score, difficulty)
    - sort_order: Sort order (asc, desc)
    
    **Features:**
    - Pagination support
    - Multiple filter options
    - Sorting capabilities
    - Aggregate statistics
    
    **Use Cases:**
    - Topic-based practice sets
    - Question bank browsing
    - Building custom tests
    """,
    response_description="Batch of questions with statistics"
)
async def get_questions_by_topic(
    topic: str = Path(..., description="Topic name"),
    exam_type: Optional[Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]] = Query(
        None,
        description="Filter by exam type"
    ),
    difficulty: Optional[Literal["easy", "medium", "hard"]] = Query(
        None,
        description="Filter by difficulty level"
    ),
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Number of questions to return (max: {MAX_LIMIT})"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of questions to skip"
    ),
    sort_by: Literal["created_at", "quality_score", "difficulty"] = Query(
        "created_at",
        description="Field to sort by"
    ),
    sort_order: Literal["asc", "desc"] = Query(
        "desc",
        description="Sort order"
    )
) -> QuestionBatch:
    """
    Get questions for a specific topic.
    
    Args:
        topic: Topic name
        exam_type: Optional exam type filter
        difficulty: Optional difficulty filter
        limit: Number of results to return
        offset: Number of results to skip
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
    
    Returns:
        QuestionBatch: Batch of questions with statistics
    
    Example:
        ```
        GET /api/questions/by-topic/Calculus?exam_type=JEE_MAIN&limit=5
        ```
    """
    try:
        logger.info(
            f"Retrieving questions - Topic: {topic}, Exam: {exam_type}, "
            f"Difficulty: {difficulty}, Limit: {limit}, Offset: {offset}"
        )
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Build Firestore query
        query = db.collection(QUESTIONS_COLLECTION).where("topic", "==", topic)
        
        # Apply filters
        if exam_type:
            query = query.where("exam_type", "==", exam_type)
        
        if difficulty:
            query = query.where("difficulty", "==", difficulty)
        
        # Apply sorting
        if sort_by == "created_at":
            query = query.order_by(
                "created_at",
                direction=firestore.Query.DESCENDING if sort_order == "desc" else firestore.Query.ASCENDING
            )
        elif sort_by == "quality_score":
            query = query.order_by(
                "metadata.validation_score",
                direction=firestore.Query.DESCENDING if sort_order == "desc" else firestore.Query.ASCENDING
            )
        
        # Get total count (for pagination metadata)
        all_docs = query.stream()
        total_count = sum(1 for _ in all_docs)
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        docs = query.stream()
        
        # Convert to Question objects
        questions = []
        quality_scores = []
        topics_covered = set()
        
        for doc in docs:
            question_data = doc.to_dict()
            question_data['id'] = doc.id
            question = Question.from_dict(question_data)
            questions.append(question)
            
            # Collect stats
            quality_scores.append(question.metadata.validation_score)
            topics_covered.add(question.topic)
            if question.subtopic:
                topics_covered.add(question.subtopic)
        
        # Calculate statistics
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Create QuestionBatch response
        batch = QuestionBatch(
            questions=questions,
            total_count=len(questions),
            avg_quality_score=avg_quality,
            topics_covered=list(topics_covered),
            generation_time=0.0  # Not applicable for retrieval
        )
        
        logger.info(
            f"Retrieved {len(questions)} questions for topic '{topic}' "
            f"(Total available: {total_count})"
        )
        
        return batch
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to retrieve questions by topic: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve questions: {str(e)}"
        )


# ============================================================================
# QUESTION VALIDATION ENDPOINT
# ============================================================================

@router.post(
    "/validate",
    response_model=ValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate question quality",
    description="""
    Validate a question for structural correctness and quality.
    
    This endpoint performs comprehensive validation including:
    - Structural validation (question length, options, answer format)
    - Quality validation (distinct options, no placeholders, grammar)
    - Contextual validation (syllabus alignment, topic relevance)
    
    **Features:**
    - Multi-category scoring (structure, quality, context)
    - Detailed issue reporting
    - Quality score (0-100)
    - Non-critical warnings
    
    **Use Cases:**
    - Validating manually created questions
    - Quality assurance
    - Pre-submission checks
    """,
    response_description="Validation result with score and issues"
)
async def validate_question(question: Question) -> ValidationResult:
    """
    Validate question quality.
    
    Args:
        question: Question to validate
    
    Returns:
        ValidationResult: Validation result with score and issues
    
    Example Request:
        ```json
        {
            "question": "What is the derivative of sin(x)?",
            "options": {
                "A": "cos(x)",
                "B": "-cos(x)",
                "C": "sin(x)",
                "D": "-sin(x)"
            },
            "correct_answer": "A",
            "explanation": "The derivative of sin(x) is cos(x) by standard rules.",
            "difficulty": "easy",
            "topic": "Calculus",
            "exam_type": "JEE_MAIN",
            "subject": "Math"
        }
        ```
    
    Example Response:
        ```json
        {
            "is_valid": true,
            "quality_score": 85,
            "issues": [],
            "warnings": ["Question could be more concise"],
            "category_scores": {
                "structure": 100,
                "quality": 90,
                "context": 95
            }
        }
        ```
    """
    try:
        logger.info(f"Validating question - Topic: {question.topic}")
        
        # Validate using QuestionValidator
        validation_result = question_validator.validate(
            question=question,
            syllabus_context=None  # Could optionally retrieve context
        )
        
        logger.info(
            f"Question validated - "
            f"Valid: {validation_result.is_valid}, "
            f"Score: {validation_result.quality_score}"
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Question validation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate question: {str(e)}"
        )


# ============================================================================
# QUESTION SEARCH ENDPOINT
# ============================================================================

@router.post(
    "/search",
    response_model=QuestionBatch,
    status_code=status.HTTP_200_OK,
    summary="Search questions with filters",
    description="""
    Search questions using multiple filter criteria.
    
    **Supported Filters:**
    - exam_type: JEE_MAIN, JEE_ADVANCED, NEET
    - subject: Physics, Chemistry, Math, Biology
    - topic: Any topic name
    - difficulty: easy, medium, hard
    - min_quality_score: Minimum validation score (0-100)
    - question_type: single_correct, multiple_correct, numerical
    
    **Features:**
    - Multi-criteria filtering
    - Quality-based filtering
    - Pagination support
    - Aggregate statistics
    
    **Use Cases:**
    - Advanced question search
    - Building filtered question sets
    - Quality-based curation
    """,
    response_description="Filtered questions batch"
)
async def search_questions(
    filters: QuestionFilter,
    limit: int = Query(
        DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Number of questions to return (max: {MAX_LIMIT})"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of questions to skip"
    )
) -> QuestionBatch:
    """
    Search questions with filters.
    
    Args:
        filters: QuestionFilter with search criteria
        limit: Number of results to return
        offset: Number of results to skip
    
    Returns:
        QuestionBatch: Filtered questions with statistics
    
    Example Request:
        ```json
        {
            "exam_type": "JEE_MAIN",
            "subject": "Math",
            "difficulty": "medium",
            "min_quality_score": 80,
            "question_type": "single_correct"
        }
        ```
    """
    try:
        logger.info(f"Searching questions with filters: {filters}")
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Build Firestore query
        query = db.collection(QUESTIONS_COLLECTION)
        
        # Apply filters
        if filters.exam_type:
            query = query.where("exam_type", "==", filters.exam_type)
        
        if filters.subject:
            query = query.where("subject", "==", filters.subject)
        
        if filters.topic:
            query = query.where("topic", "==", filters.topic)
        
        if filters.difficulty:
            query = query.where("difficulty", "==", filters.difficulty)
        
        if filters.question_type:
            query = query.where("question_type", "==", filters.question_type)
        
        # Quality score filtering (need to fetch all and filter in-memory for now)
        # Firestore doesn't support filtering on nested fields easily
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        docs = query.stream()
        
        # Convert to Question objects and filter by quality
        questions = []
        quality_scores = []
        topics_covered = set()
        
        for doc in docs:
            question_data = doc.to_dict()
            question_data['id'] = doc.id
            question = Question.from_dict(question_data)
            
            # Apply quality score filter
            if filters.min_quality_score:
                if question.metadata.validation_score < filters.min_quality_score:
                    continue
            
            questions.append(question)
            quality_scores.append(question.metadata.validation_score)
            topics_covered.add(question.topic)
        
        # Calculate statistics
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Create QuestionBatch response
        batch = QuestionBatch(
            questions=questions,
            total_count=len(questions),
            avg_quality_score=avg_quality,
            topics_covered=list(topics_covered),
            generation_time=0.0
        )
        
        logger.info(f"Search returned {len(questions)} questions")
        
        return batch
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Question search failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search questions: {str(e)}"
        )


# ============================================================================
# STATISTICS ENDPOINT
# ============================================================================

@router.get(
    "/stats",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get question statistics",
    description="""
    Get comprehensive statistics about questions in the database.
    
    **Statistics Included:**
    - Total questions count
    - Questions by topic
    - Questions by difficulty
    - Average quality score
    - Questions by exam type
    - Questions by subject (if filtered)
    
    **Query Parameters:**
    - exam_type: Filter stats by exam type
    - subject: Filter stats by subject
    
    **Use Cases:**
    - Dashboard metrics
    - Content gap analysis
    - Quality monitoring
    - Capacity planning
    """,
    response_description="Question statistics and distributions"
)
async def get_question_stats(
    exam_type: Optional[Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]] = Query(
        None,
        description="Filter by exam type"
    ),
    subject: Optional[Literal["Physics", "Chemistry", "Math", "Biology"]] = Query(
        None,
        description="Filter by subject"
    )
) -> Dict[str, Any]:
    """
    Get question statistics.
    
    Args:
        exam_type: Optional exam type filter
        subject: Optional subject filter
    
    Returns:
        Dict containing various statistics
    
    Example Response:
        ```json
        {
            "total_questions": 500,
            "by_topic": {
                "Calculus": 50,
                "Algebra": 45,
                "Mechanics": 60
            },
            "by_difficulty": {
                "easy": 150,
                "medium": 250,
                "hard": 100
            },
            "by_exam_type": {
                "JEE_MAIN": 300,
                "JEE_ADVANCED": 200
            },
            "avg_quality_score": 85.5,
            "timestamp": "2024-11-27T10:30:00Z"
        }
        ```
    """
    try:
        logger.info(f"Retrieving statistics - Exam: {exam_type}, Subject: {subject}")
        
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service unavailable"
            )
        
        # Build base query
        query = db.collection(QUESTIONS_COLLECTION)
        
        # Apply filters
        if exam_type:
            query = query.where("exam_type", "==", exam_type)
        
        if subject:
            query = query.where("subject", "==", subject)
        
        # Execute query
        docs = query.stream()
        
        # Collect statistics
        total_questions = 0
        by_topic = defaultdict(int)
        by_difficulty = defaultdict(int)
        by_exam_type = defaultdict(int)
        by_subject = defaultdict(int)
        quality_scores = []
        
        for doc in docs:
            data = doc.to_dict()
            total_questions += 1
            
            # Count by topic
            topic = data.get("topic", "Unknown")
            by_topic[topic] += 1
            
            # Count by difficulty
            difficulty = data.get("difficulty", "Unknown")
            by_difficulty[difficulty] += 1
            
            # Count by exam type
            exam = data.get("exam_type", "Unknown")
            by_exam_type[exam] += 1
            
            # Count by subject
            subj = data.get("subject", "Unknown")
            by_subject[subj] += 1
            
            # Collect quality scores
            if "metadata" in data and "validation_score" in data["metadata"]:
                quality_scores.append(data["metadata"]["validation_score"])
        
        # Calculate average quality
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Build response
        stats = {
            "total_questions": total_questions,
            "by_topic": dict(sorted(by_topic.items(), key=lambda x: x[1], reverse=True)),
            "by_difficulty": dict(by_difficulty),
            "by_exam_type": dict(by_exam_type),
            "by_subject": dict(by_subject),
            "avg_quality_score": round(avg_quality, 2),
            "filters_applied": {
                "exam_type": exam_type,
                "subject": subject
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Statistics retrieved - Total questions: {total_questions}")
        
        return stats
        
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


# ============================================================================
# ERROR HANDLERS
# ============================================================================
# Note: Exception handlers are defined in main.py, not in routers
# Routers should raise HTTPException which will be caught by FastAPI

# Module initialization
logger.info("Question router initialized successfully")
