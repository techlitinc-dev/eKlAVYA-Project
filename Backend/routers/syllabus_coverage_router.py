"""
Syllabus Coverage Router

API endpoints for syllabus coverage tracking and reporting.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from services.syllabus_coverage_tracker import SyllabusCoverageTracker
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/syllabus/coverage",
    tags=["Syllabus Coverage"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Coverage data not found"},
        500: {"description": "Internal Server Error"}
    }
)

# Initialize service
coverage_tracker = SyllabusCoverageTracker()


# Mock authentication dependency (already imported from testing_auth)


@router.get(
    "/{student_id}",
    summary="Get Student Coverage",
    description="""
    Get complete syllabus coverage data for a student.
    
    Returns:
    - Overall coverage percentage
    - Subject-wise coverage
    - Chapter-wise coverage
    - Topic-level details
    - Weak topics
    - Untested topics
    """
)
async def get_student_coverage(
    student_id: str,
    exam_type: str = Query(..., description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)"),
    current_user: dict = Depends(get_current_user)
):
    """
    Get syllabus coverage for a student.
    
    Args:
        student_id: Student identifier
        exam_type: Exam type
        current_user: Authenticated user
    
    Returns:
        Complete coverage data
    """
    logger.info(f"Coverage request: student={student_id}, exam={exam_type}")
    
    # Verify access
    if student_id != current_user["student_id"]:
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )
    
    try:
        coverage = coverage_tracker.get_student_coverage(student_id, exam_type)
        
        return {
            "student_id": coverage.student_id,
            "exam_type": coverage.exam_type,
            "overall_coverage": {
                "percentage": round(coverage.overall_coverage_percentage, 2),
                "covered_topics": coverage.covered_topics,
                "total_topics": coverage.total_topics,
                "untested_topics": coverage.untested_topics,
                "weak_topics": coverage.weak_topics
            },
            "subject_coverage": {
                subject: round(percentage, 2)
                for subject, percentage in coverage.subject_coverage.items()
            },
            "chapter_coverage": {
                chapter: round(percentage, 2)
                for chapter, percentage in coverage.chapter_coverage.items()
            },
            "last_updated": coverage.last_updated.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get coverage: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve coverage: {str(e)}"
        )


@router.get(
    "/{student_id}/untested",
    summary="Get Untested Topics",
    description="Get list of topics that haven't been tested yet"
)
async def get_untested_topics(
    student_id: str,
    exam_type: str = Query(..., description="Exam type"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    limit: int = Query(20, ge=1, le=100, description="Maximum topics to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get untested topics for a student."""
    logger.info(f"Untested topics request: student={student_id}, exam={exam_type}")
    
    # Verify access
    if student_id != current_user["student_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        untested = coverage_tracker.get_untested_topics(
            student_id, exam_type, subject
        )
        
        return {
            "student_id": student_id,
            "exam_type": exam_type,
            "subject": subject,
            "total_untested": len(untested),
            "topics": untested[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to get untested topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{student_id}/weak",
    summary="Get Weak Topics",
    description="Get topics where student performed poorly"
)
async def get_weak_topics(
    student_id: str,
    exam_type: str = Query(..., description="Exam type"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    threshold: float = Query(60.0, ge=0, le=100, description="Score threshold"),
    limit: int = Query(20, ge=1, le=100, description="Maximum topics to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get weak topics for a student."""
    logger.info(f"Weak topics request: student={student_id}, exam={exam_type}")
    
    # Verify access
    if student_id != current_user["student_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Temporarily update threshold
        original_threshold = coverage_tracker.weak_topic_threshold
        coverage_tracker.weak_topic_threshold = threshold
        
        weak = coverage_tracker.get_weak_topics(
            student_id, exam_type, subject
        )
        
        # Restore original threshold
        coverage_tracker.weak_topic_threshold = original_threshold
        
        return {
            "student_id": student_id,
            "exam_type": exam_type,
            "subject": subject,
            "threshold": threshold,
            "total_weak": len(weak),
            "topics": weak[:limit]
        }
        
    except Exception as e:
        logger.error(f"Failed to get weak topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{student_id}/recommendations",
    summary="Get Coverage Recommendations",
    description="""
    Get recommended topics for next test based on coverage analysis.
    
    Prioritizes:
    - Untested topics (40%)
    - Weak topics (40%)
    - Revision topics (20%)
    """
)
async def get_recommendations(
    student_id: str,
    exam_type: str = Query(..., description="Exam type"),
    num_topics: int = Query(10, ge=1, le=50, description="Number of topics"),
    current_user: dict = Depends(get_current_user)
):
    """Get recommended topics for next test."""
    logger.info(f"Recommendations request: student={student_id}, exam={exam_type}")
    
    # Verify access
    if student_id != current_user["student_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        recommendations = coverage_tracker.get_coverage_recommendations(
            student_id, exam_type, num_topics
        )
        
        return {
            "student_id": student_id,
            "exam_type": exam_type,
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{student_id}/progress",
    summary="Get Coverage Progress",
    description="Get coverage progress over time"
)
async def get_coverage_progress(
    student_id: str,
    exam_type: str = Query(..., description="Exam type"),
    current_user: dict = Depends(get_current_user)
):
    """Get coverage progress timeline."""
    logger.info(f"Progress request: student={student_id}, exam={exam_type}")
    
    # Verify access
    if student_id != current_user["student_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        coverage = coverage_tracker.get_student_coverage(student_id, exam_type)
        
        # Build progress data
        progress = {
            "student_id": student_id,
            "exam_type": exam_type,
            "current_coverage": round(coverage.overall_coverage_percentage, 2),
            "covered_topics": coverage.covered_topics,
            "total_topics": coverage.total_topics,
            "subjects": {}
        }
        
        # Add subject-wise progress
        for subject, percentage in coverage.subject_coverage.items():
            progress["subjects"][subject] = {
                "coverage_percentage": round(percentage, 2),
                "status": "excellent" if percentage >= 80 else
                         "good" if percentage >= 60 else
                         "needs_improvement"
            }
        
        return progress
        
    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{student_id}/topic/{topic_id}",
    summary="Get Topic Details",
    description="Get detailed coverage information for a specific topic"
)
async def get_topic_details(
    student_id: str,
    topic_id: str,
    exam_type: str = Query(..., description="Exam type"),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed coverage for a specific topic."""
    logger.info(f"Topic details request: student={student_id}, topic={topic_id}")
    
    # Verify access
    if student_id != current_user["student_id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        coverage = coverage_tracker.get_student_coverage(student_id, exam_type)
        
        if topic_id not in coverage.topic_coverage:
            return {
                "student_id": student_id,
                "topic_id": topic_id,
                "status": "untested",
                "message": "This topic has not been tested yet"
            }
        
        topic_cov = coverage.topic_coverage[topic_id]
        
        return {
            "student_id": student_id,
            "topic_id": topic_id,
            "topic_name": topic_cov.topic_name,
            "subject": topic_cov.subject,
            "chapter": topic_cov.chapter,
            "status": "tested",
            "statistics": {
                "times_tested": topic_cov.times_tested,
                "total_questions": topic_cov.total_questions,
                "correct_answers": topic_cov.correct_answers,
                "incorrect_answers": topic_cov.incorrect_answers,
                "average_score": round(topic_cov.average_score, 2),
                "performance": "strong" if topic_cov.average_score >= 80 else
                              "good" if topic_cov.average_score >= 60 else
                              "needs_improvement"
            },
            "timeline": {
                "first_tested": topic_cov.first_tested.isoformat() if topic_cov.first_tested else None,
                "last_tested": topic_cov.last_tested.isoformat() if topic_cov.last_tested else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get topic details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Health Check",
    description="Check if coverage service is operational",
    tags=["Health"]
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "syllabus-coverage",
        "timestamp": datetime.utcnow().isoformat()
    }


# Module initialization
logger.info("Syllabus coverage router loaded")
