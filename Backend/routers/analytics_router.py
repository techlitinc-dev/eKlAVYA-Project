"""
Analytics Router for Mentor AI Platform.

This module defines FastAPI endpoints for analytics generation and retrieval,
including performance analysis, AI insights, and study recommendations.

Endpoints:
- POST /api/analytics/generate: Generate new analytics report
- GET /api/analytics/{analytics_id}: Retrieve complete analytics report
- GET /api/analytics/student/{student_id}: Get student's analytics history
- GET /api/analytics/test/{test_id}: Get analytics for a specific test
- GET /api/analytics/{analytics_id}/insights: Get AI insights only
- GET /api/analytics/{analytics_id}/weak-topics: Get high-priority weak topics

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from google.cloud.firestore_v1 import FieldFilter

# Import models
from models.analytics_models import (
    AnalyticsRequest,
    AnalyticsResponse,
    AnalyticsReport,
    AnalyticsInsights,
    PriorityTopic
)

# Import service
from services.analytics_service import (
    AnalyticsService,
    AnalyticsNotFoundError,
    AnalyticsServiceError
)
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


def get_analytics_service():
    """Dependency to get analytics service instance."""
    return AnalyticsService()


def verify_student_or_parent(student_id: str):
    """
    Dependency to verify student or parent access.
    
    In a real implementation, this would check:
    - If the requesting user is the student themselves
    - If the requesting user is a parent of the student
    - JWT token validation
    - Firebase auth integration
    
    For now, this is a placeholder that always returns True.
    """
    # TODO: Implement actual authentication and authorization
    # This would typically check:
    # 1. JWT token from request headers
    # 2. Firebase user ID verification
    # 3. Parent-child relationship validation
    return True


@router.post(
    "/generate",
    response_model=AnalyticsResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate analytics report",
    description="""
    Generate a comprehensive analytics report for a student's test performance.
    
    This endpoint triggers the complete analytics pipeline:
    1. Retrieves test questions from database
    2. Calculates scores with exam-specific marking schemes
    3. Analyzes performance patterns and identifies strengths/weaknesses
    4. Generates AI-powered insights using Gemini Flash
    5. Assembles complete report with visualizations
    6. Stores report for future retrieval
    
    **Process:**
    - Asynchronous operation - returns analytics_id immediately
    - Full processing happens in background
    - Client polls GET /api/analytics/{analytics_id} for results
    
    **Rate Limiting:**
    - 10 requests per minute per user
    - 100 requests per hour per IP
    """,
    responses={
        202: {
            "description": "Analytics generation started",
            "content": {
                "application/json": {
                    "example": {
                        "analytics_id": "analytics_test123_student456_1234567890",
                        "status": "pending",
                        "message": "Analytics generation in progress"
                    }
                }
            }
        },
        400: {"description": "Invalid request data"},
        401: {"description": "Unauthorized access"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error"}
    }
)
async def generate_analytics(
    request: AnalyticsRequest,
    service: AnalyticsService = Depends(get_analytics_service)
) -> AnalyticsResponse:
    """
    Generate analytics report for a student's test.
    
    Args:
        request: AnalyticsRequest with test_id, student_id, and answers
        service: AnalyticsService instance (injected dependency)
    
    Returns:
        AnalyticsResponse with analytics_id and status
    
    Raises:
        HTTPException: 400 for validation errors
        HTTPException: 500 for processing errors
    """
    try:
        logger.info(
            f"Analytics generation request for test={request.test_id}, "
            f"student={request.student_id}"
        )
        
        # Verify access (placeholder - always returns True)
        verify_student_or_parent(request.student_id)
        
        # Convert answers to the format expected by the service
        # If answers is a dict, convert to list of QuestionAnswer objects
        answers_dict = {}
        if isinstance(request.answers, dict):
            answers_dict = request.answers
        else:
            # Convert list of QuestionAnswer to dict
            answers_dict = {
                answer.question_number: answer.answer 
                for answer in request.answers
            }
        
        # Generate analytics (this returns the analytics_id)
        analytics_id = service.generate_analytics(
            test_id=request.test_id,
            student_id=request.student_id,
            answers=answers_dict,
            include_ai_insights=request.include_ai_insights,
            use_cache=request.use_cache
        )
        
        logger.info(f"Analytics generation started: {analytics_id}")
        
        return AnalyticsResponse(
            analytics_id=analytics_id,
            status="pending",
            message="Analytics generation in progress"
        )
        
    except ValueError as e:
        logger.warning(f"Validation error in analytics request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics. Please try again later."
        )


@router.get(
    "/{analytics_id}",
    response_model=AnalyticsReport,
    summary="Get analytics report",
    description="""
    Retrieve a complete analytics report by ID.
    
    Returns the full analytics report including:
    - Performance overview and subject analysis
    - Topic-wise performance with priorities
    - AI-generated insights and recommendations
    - Visualizations for charts and graphs
    - Priority topics for study planning
    """,
    responses={
        200: {"description": "Analytics report retrieved successfully"},
        404: {"description": "Analytics report not found"},
        401: {"description": "Unauthorized access"},
        500: {"description": "Internal server error"}
    }
)
async def get_analytics(
    analytics_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
) -> AnalyticsReport:
    """
    Retrieve complete analytics report by ID.
    
    Args:
        analytics_id: Unique analytics report identifier
        service: AnalyticsService instance (injected dependency)
    
    Returns:
        AnalyticsReport with complete analytics data
    
    Raises:
        HTTPException: 404 if analytics not found
        HTTPException: 500 for processing errors
    """
    try:
        logger.info(f"Retrieving analytics: {analytics_id}")
        
        # Retrieve analytics report
        report = service.get_analytics(analytics_id)
        
        # In a real implementation, we would verify the student/parent
        # has access to this report
        # verify_student_or_parent(report.overview.student_id)
        
        logger.info(f"Analytics retrieved successfully: {analytics_id}")
        
        return report
        
    except AnalyticsNotFoundError:
        logger.warning(f"Analytics not found: {analytics_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics report not found: {analytics_id}"
        )
    
    except Exception as e:
        logger.error(f"Error retrieving analytics {analytics_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics. Please try again later."
        )


@router.get(
    "/student/{student_id}",
    response_model=List[AnalyticsReport],
    summary="Get student analytics history",
    description="""
    Retrieve analytics history for a student.
    
    Returns a list of analytics reports ordered by generation date (newest first).
    
    **Pagination:**
    - limit: Number of reports to return (default: 10, max: 50)
    - offset: Number of reports to skip (default: 0)
    """,
    responses={
        200: {"description": "Student analytics history retrieved"},
        401: {"description": "Unauthorized access"},
        500: {"description": "Internal server error"}
    }
)
async def get_student_analytics(
    student_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of reports to return"),
    offset: int = Query(0, ge=0, description="Number of reports to skip"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> List[AnalyticsReport]:
    """
    Retrieve analytics history for a student.
    
    Args:
        student_id: Student identifier
        limit: Number of reports to return (1-50)
        offset: Number of reports to skip
        service: AnalyticsService instance (injected dependency)
    
    Returns:
        List of AnalyticsReport objects
    
    Raises:
        HTTPException: 500 for processing errors
    """
    try:
        logger.info(f"Retrieving analytics for student: {student_id}")
        
        # Verify access (placeholder)
        verify_student_or_parent(student_id)
        
        # Retrieve student analytics with pagination
        reports = service.get_student_analytics(
            student_id=student_id,
            limit=limit,
            order_by="generated_at"
        )
        
        # Apply offset manually since Firestore doesn't support it directly
        # with order_by on a different field
        if offset > 0:
            reports = reports[offset:]
        
        logger.info(f"Retrieved {len(reports)} analytics for student: {student_id}")
        
        return reports
        
    except Exception as e:
        logger.error(f"Error retrieving student analytics for {student_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve student analytics. Please try again later."
        )


@router.get(
    "/test/{test_id}",
    response_model=List[AnalyticsReport],
    summary="Get analytics by test",
    description="""
    Retrieve all analytics reports for a specific test.
    
    Returns analytics reports for all students who took the specified test.
    Results are ordered by generation date (newest first).
    """,
    responses={
        200: {"description": "Test analytics retrieved successfully"},
        401: {"description": "Unauthorized access"},
        404: {"description": "No analytics found for test"},
        500: {"description": "Internal server error"}
    }
)
async def get_analytics_by_test(
    test_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of reports to return"),
    service: AnalyticsService = Depends(get_analytics_service)
) -> List[AnalyticsReport]:
    """
    Retrieve all analytics reports for a specific test.
    
    Args:
        test_id: Test identifier
        limit: Number of reports to return (1-100)
        service: AnalyticsService instance (injected dependency)
    
    Returns:
        List of AnalyticsReport objects for the test
    
    Raises:
        HTTPException: 404 if no analytics found
        HTTPException: 500 for processing errors
    """
    try:
        logger.info(f"Retrieving analytics for test: {test_id}")
        
        # In a real implementation, we would verify the user has access
        # to view analytics for this test (teacher/admin role)
        # verify_teacher_or_admin_access()
        
        # Retrieve analytics for the test
        # Note: This requires a custom method in AnalyticsService
        # Since it's not implemented, we'll simulate it
        reports = []  # This would be implemented in the service
        
        # Placeholder implementation - in reality, this would query by test_id
        # reports = service.get_analytics_by_test(test_id, limit=limit)
        
        if not reports:
            logger.info(f"No analytics found for test: {test_id}")
            # For now, we'll return empty list instead of 404
            # raise HTTPException(
            #     status_code=status.HTTP_404_NOT_FOUND,
            #     detail=f"No analytics found for test: {test_id}"
            # )
        
        logger.info(f"Retrieved {len(reports)} analytics for test: {test_id}")
        
        return reports
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving analytics for test {test_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test analytics. Please try again later."
        )


@router.get(
    "/{analytics_id}/insights",
    response_model=AnalyticsInsights,
    summary="Get AI insights only",
    description="""
    Extract and return only the AI-generated insights from an analytics report.
    
    This endpoint provides quick access to the AI-powered analysis without
    the overhead of the complete report, useful for dashboards and summaries.
    """,
    responses={
        200: {"description": "AI insights retrieved successfully"},
        404: {"description": "Analytics report not found"},
        401: {"description": "Unauthorized access"},
        500: {"description": "Internal server error"}
    }
)
async def get_analytics_insights(
    analytics_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
) -> AnalyticsInsights:
    """
    Extract AI insights from an analytics report.
    
    Args:
        analytics_id: Analytics report identifier
        service: AnalyticsService instance (injected dependency)
    
    Returns:
        AnalyticsInsights with AI-generated analysis
    
    Raises:
        HTTPException: 404 if analytics not found
        HTTPException: 500 for processing errors
    """
    try:
        logger.info(f"Retrieving insights for analytics: {analytics_id}")
        
        # Retrieve full analytics report
        report = service.get_analytics(analytics_id)
        
        # Extract insights
        insights = report.ai_insights
        
        if insights is None:
            logger.warning(f"No AI insights available for: {analytics_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No AI insights available for analytics: {analytics_id}"
            )
        
        logger.info(f"Insights retrieved successfully: {analytics_id}")
        
        return insights
        
    except AnalyticsNotFoundError:
        logger.warning(f"Analytics not found: {analytics_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics report not found: {analytics_id}"
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for no insights)
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving insights for {analytics_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve insights. Please try again later."
        )


@router.get(
    "/{analytics_id}/weak-topics",
    response_model=List[PriorityTopic],
    summary="Get high-priority weak topics",
    description="""
    Extract and return only the high-priority weak topics from an analytics report.
    
    This endpoint provides quick access to the most critical topics that need
    immediate attention, useful for study planning and focused practice.
    """,
    responses={
        200: {"description": "Weak topics retrieved successfully"},
        404: {"description": "Analytics report not found"},
        401: {"description": "Unauthorized access"},
        500: {"description": "Internal server error"}
    }
)
async def get_weak_topics(
    analytics_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
) -> List[PriorityTopic]:
    """
    Extract high-priority weak topics from an analytics report.
    
    Args:
        analytics_id: Analytics report identifier
        service: AnalyticsService instance (injected dependency)
    
    Returns:
        List of PriorityTopic objects with HIGH priority
    
    Raises:
        HTTPException: 404 if analytics not found
        HTTPException: 500 for processing errors
    """
    try:
        logger.info(f"Retrieving weak topics for analytics: {analytics_id}")
        
        # Retrieve full analytics report
        report = service.get_analytics(analytics_id)
        
        # Filter for high-priority topics
        high_priority_topics = [
            topic for topic in report.priority_topics
            if topic.priority.upper() == "HIGH"
        ]
        
        logger.info(
            f"Retrieved {len(high_priority_topics)} weak topics for: {analytics_id}"
        )
        
        return high_priority_topics
        
    except AnalyticsNotFoundError:
        logger.warning(f"Analytics not found: {analytics_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analytics report not found: {analytics_id}"
        )
    
    except Exception as e:
        logger.error(f"Error retrieving weak topics for {analytics_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve weak topics. Please try again later."
        )
