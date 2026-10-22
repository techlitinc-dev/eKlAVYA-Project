"""
Test Management Router for Mentor AI Platform.

This module provides FastAPI endpoints for test lifecycle management including
starting tests, submitting answers, calculating scores, and retrieving results.

Example Usage:
    # In main.py
    from routers.test_management_router import router as test_management_router
    app.include_router(test_management_router)
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

# Import models
from models.diagnostic_test_models import (
    TestSubmission,
    TestResults,
    SectionScore,
    TestStatus,
    ErrorResponse,
    SuccessResponse
)

# Note: These would be actual imports in production
# from services.test_scoring_service import TestScoringService
# from utils.firebase_auth import verify_token, get_current_user, is_admin
# from database.firestore_client import get_firestore_client


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create router
router = APIRouter(
    prefix="/api/diagnostic-test",
    tags=["Test Management"],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Test not found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(token: str = Depends(lambda: "mock_token")):
    """
    Verify Firebase Auth token and extract user information.
    
    Args:
        token: Firebase Auth token from Authorization header
        
    Returns:
        User information dict with student_id
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    # Mock implementation for development
    return {
        "student_id": "test_student_123",
        "email": "test@example.com",
        "is_admin": False
    }


async def verify_admin(current_user: dict = Depends(get_current_user)):
    """
    Verify user has admin privileges.
    
    Args:
        current_user: Current user information
        
    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


async def get_test_from_db(test_id: str) -> Dict:
    """
    Retrieve test from database.
    
    Args:
        test_id: Test identifier
        
    Returns:
        Test data dictionary
        
    Raises:
        HTTPException: If test not found
    """
    # In production, retrieve from Firestore
    # db = get_firestore_client()
    # test_ref = db.collection('diagnostic_tests').document(test_id)
    # test = test_ref.get()
    # 
    # if not test.exists:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Test not found: {test_id}"
    #     )
    # 
    # return test.to_dict()
    
    # Mock implementation
    return {
        "test_id": test_id,
        "student_id": "test_student_123",
        "exam_type": "JEE_MAIN",
        "status": "pending",
        "total_questions": 90,
        "total_marks": 360,
        "duration_minutes": 180,
        "generation_date": datetime.utcnow().isoformat(),
        "start_date": None,
        "submission_date": None
    }


async def verify_test_access(test_id: str, student_id: str) -> Dict:
    """
    Verify student has access to test and return test data.
    
    Args:
        test_id: Test identifier
        student_id: Student identifier
        
    Returns:
        Test data dictionary
        
    Raises:
        HTTPException: If test not found or access denied
    """
    test = await get_test_from_db(test_id)
    
    if test.get("student_id") != student_id:
        logger.warning(
            f"Access denied: student {student_id} attempted to access "
            f"test {test_id} owned by {test.get('student_id')}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )
    
    return test


# ============================================================================
# SCORE CALCULATION
# ============================================================================

def calculate_test_scores(
    test_data: Dict,
    submission: TestSubmission
) -> TestResults:
    """
    Calculate test scores from submission.
    
    Args:
        test_data: Test data including questions and marking scheme
        submission: Student's test submission
        
    Returns:
        TestResults with calculated scores
    """
    logger.info(f"Calculating scores for test: {submission.test_id}")
    
    # In production, retrieve full test with questions
    # test = get_full_test(submission.test_id)
    # sections = test.sections
    
    # Mock calculation for development
    # This would iterate through all questions and calculate scores
    
    # Initialize counters
    total_score = 0
    total_marks = test_data.get("total_marks", 360)
    correct_count = 0
    incorrect_count = 0
    unattempted_count = 0
    
    # Mock section scores
    section_scores = {}
    
    # For JEE Main: 3 sections (Physics, Chemistry, Mathematics)
    sections = ["Physics", "Chemistry", "Mathematics"]
    questions_per_section = test_data.get("total_questions", 90) // 3
    
    for section_name in sections:
        section_correct = 0
        section_incorrect = 0
        section_unattempted = 0
        section_score = 0
        section_total = 120  # 30 questions × 4 marks
        
        # Calculate section scores based on answers
        # In production, iterate through actual questions
        for q_num in range(1, questions_per_section + 1):
            answer = submission.answers.get(q_num)
            
            if answer is None or answer == "":
                section_unattempted += 1
                unattempted_count += 1
            else:
                # Mock: assume 80% correct
                import random
                random.seed(q_num)  # Deterministic for testing
                
                if random.random() < 0.8:
                    section_correct += 1
                    correct_count += 1
                    section_score += 4  # +4 marks
                    total_score += 4
                else:
                    section_incorrect += 1
                    incorrect_count += 1
                    section_score -= 1  # -1 mark
                    total_score -= 1
        
        # Create section score
        section_scores[section_name] = SectionScore(
            section_name=f"Section - {section_name}",
            score=max(0, section_score),
            total_marks=section_total,
            correct=section_correct,
            incorrect=section_incorrect,
            unattempted=section_unattempted
        )
    
    # Calculate percentage
    percentage = (total_score / total_marks) * 100 if total_marks > 0 else 0
    
    # Create results
    results = TestResults(
        test_id=submission.test_id,
        student_id=submission.student_id,
        total_score=max(0, total_score),
        total_marks=total_marks,
        percentage=round(percentage, 2),
        section_scores=section_scores,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unattempted_count=unattempted_count
    )
    
    logger.info(
        f"Scores calculated: {results.total_score}/{results.total_marks} "
        f"({results.percentage}%)"
    )
    
    return results


async def store_test_results(results: TestResults, submission: TestSubmission):
    """
    Store test results in database.
    
    Args:
        results: Calculated test results
        submission: Original submission
    """
    # In production, store in Firestore
    # db = get_firestore_client()
    # 
    # # Store results
    # results_ref = db.collection('test_results').document(results.test_id)
    # results_ref.set({
    #     **results.dict(),
    #     'answers': submission.answers,
    #     'time_taken': submission.time_taken,
    #     'submission_time': submission.submission_time.isoformat(),
    #     'created_at': datetime.utcnow().isoformat()
    # })
    # 
    # # Update test status
    # test_ref = db.collection('diagnostic_tests').document(results.test_id)
    # test_ref.update({
    #     'status': 'completed',
    #     'submission_date': submission.submission_time.isoformat()
    # })
    
    logger.info(f"Results stored for test: {results.test_id}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post(
    "/{test_id}/start",
    response_model=SuccessResponse,
    summary="Start Test",
    description="""
    Start a diagnostic test by recording the start time and updating status.
    
    **Requirements**:
    - Test must exist and belong to the student
    - Test status must be 'pending'
    - Student must be authenticated
    
    **Actions**:
    1. Verify test access
    2. Check test status is 'pending'
    3. Record start time
    4. Update status to 'in_progress'
    
    **Note**: Once started, the test timer begins. Students should ensure
    they are ready before starting.
    """,
    responses={
        200: {
            "description": "Test started successfully",
            "model": SuccessResponse
        },
        400: {
            "description": "Test already started or invalid status",
            "model": ErrorResponse
        },
        403: {
            "description": "Access denied",
            "model": ErrorResponse
        }
    }
)
async def start_test(
    test_id: str,
    request_body: Dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a diagnostic test.
    
    Args:
        test_id: Test identifier
        request_body: Request body with student_id
        current_user: Authenticated user information
        
    Returns:
        Success response with start time
        
    Raises:
        HTTPException: If test cannot be started
    """
    student_id = request_body.get("student_id")
    
    logger.info(f"Start test request: test_id={test_id}, student_id={student_id}")
    
    # Verify student_id matches authenticated user
    if student_id != current_user["student_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student ID does not match authenticated user"
        )
    
    # Get and verify test access
    test = await verify_test_access(test_id, student_id)
    
    # Check test status
    current_status = test.get("status", "")
    if current_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot start test with status '{current_status}'. "
                   f"Test must be in 'pending' status."
        )
    
    try:
        # Record start time and update status
        start_time = datetime.utcnow()
        
        # In production, update in Firestore
        # db = get_firestore_client()
        # test_ref = db.collection('diagnostic_tests').document(test_id)
        # test_ref.update({
        #     'status': 'in_progress',
        #     'start_date': start_time.isoformat()
        # })
        
        logger.info(f"Test started: {test_id} at {start_time}")
        
        return SuccessResponse(
            message="Test started successfully",
            data={
                "test_id": test_id,
                "start_time": start_time.isoformat(),
                "duration_minutes": test.get("duration_minutes", 180)
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to start test: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start test: {str(e)}"
        )


@router.post(
    "/{test_id}/submit",
    response_model=TestResults,
    summary="Submit Test",
    description="""
    Submit test answers and calculate results.
    
    **Requirements**:
    - Test must exist and belong to the student
    - Test status must be 'in_progress'
    - All answers must be in valid format
    
    **Process**:
    1. Verify test access and status
    2. Validate submission
    3. Calculate scores (section-wise and total)
    4. Store results in database
    5. Update test status to 'completed'
    6. Return calculated results
    
    **Scoring**:
    - Correct answer: +marks (typically +4)
    - Incorrect answer: -negative_marks (typically -1)
    - Unattempted: 0 marks
    
    **Note**: Test can only be submitted once. After submission, answers
    cannot be changed.
    """,
    responses={
        200: {
            "description": "Test submitted and scored successfully",
            "model": TestResults
        },
        400: {
            "description": "Invalid submission or test status",
            "model": ErrorResponse
        }
    }
)
async def submit_test(
    test_id: str,
    submission: TestSubmission,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit test and calculate results.
    
    Args:
        test_id: Test identifier
        submission: Test submission with answers
        current_user: Authenticated user information
        
    Returns:
        TestResults with calculated scores
        
    Raises:
        HTTPException: If submission fails
    """
    logger.info(
        f"Test submission: test_id={test_id}, student_id={submission.student_id}, "
        f"answers={len(submission.answers)}"
    )
    
    # Verify test_id matches
    if submission.test_id != test_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test ID in URL does not match submission"
        )
    
    # Verify student_id matches authenticated user
    if submission.student_id != current_user["student_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student ID does not match authenticated user"
        )
    
    # Get and verify test access
    test = await verify_test_access(test_id, submission.student_id)
    
    # Check test status
    current_status = test.get("status", "")
    if current_status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit test with status '{current_status}'. "
                   f"Test must be in 'in_progress' status."
        )
    
    # Check if time exceeded
    start_date = test.get("start_date")
    if start_date:
        # In production, parse ISO format datetime
        # start_time = datetime.fromisoformat(start_date)
        # duration = timedelta(minutes=test.get("duration_minutes", 180))
        # if datetime.utcnow() > start_time + duration:
        #     logger.warning(f"Test {test_id} submitted after time limit")
        pass
    
    try:
        # Calculate scores
        results = calculate_test_scores(test, submission)
        
        # Store results
        await store_test_results(results, submission)
        
        logger.info(
            f"Test submitted successfully: {test_id}, "
            f"score={results.total_score}/{results.total_marks}"
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to submit test: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit test: {str(e)}"
        )


@router.get(
    "/{test_id}/results",
    response_model=TestResults,
    summary="Get Test Results",
    description="""
    Retrieve calculated test results.
    
    **Requirements**:
    - Test must exist and belong to the student
    - Test status must be 'completed'
    - Results must have been calculated and stored
    
    **Returns**:
    - Total score and percentage
    - Section-wise scores
    - Correct/incorrect/unattempted counts
    
    **Note**: Results are only available after test submission.
    """,
    responses={
        200: {
            "description": "Results retrieved successfully",
            "model": TestResults
        },
        400: {
            "description": "Test not completed",
            "model": ErrorResponse
        },
        404: {
            "description": "Results not found",
            "model": ErrorResponse
        }
    }
)
async def get_test_results(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get test results.
    
    Args:
        test_id: Test identifier
        current_user: Authenticated user information
        
    Returns:
        TestResults object
        
    Raises:
        HTTPException: If results not available
    """
    logger.info(f"Results request for test: {test_id}")
    
    # Get and verify test access
    test = await verify_test_access(test_id, current_user["student_id"])
    
    # Check test status
    if test.get("status") != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Results not available. Test must be completed first."
        )
    
    try:
        # In production, retrieve from Firestore
        # db = get_firestore_client()
        # results_ref = db.collection('test_results').document(test_id)
        # results_doc = results_ref.get()
        # 
        # if not results_doc.exists:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Results not found"
        #     )
        # 
        # results_data = results_doc.to_dict()
        # return TestResults(**results_data)
        
        # Mock response
        return TestResults(
            test_id=test_id,
            student_id=current_user["student_id"],
            total_score=280,
            total_marks=360,
            percentage=77.78,
            section_scores={
                "Physics": SectionScore(
                    section_name="Section - Physics",
                    score=96,
                    total_marks=120,
                    correct=25,
                    incorrect=3,
                    unattempted=2
                ),
                "Chemistry": SectionScore(
                    section_name="Section - Chemistry",
                    score=92,
                    total_marks=120,
                    correct=24,
                    incorrect=4,
                    unattempted=2
                ),
                "Mathematics": SectionScore(
                    section_name="Section - Mathematics",
                    score=92,
                    total_marks=120,
                    correct=23,
                    incorrect=3,
                    unattempted=4
                )
            },
            correct_count=72,
            incorrect_count=10,
            unattempted_count=8
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve results: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve results: {str(e)}"
        )


@router.get(
    "/{test_id}/status",
    response_model=Dict,
    summary="Get Test Status",
    description="""
    Get current test status and timing information.
    
    **Returns**:
    - Current status (pending, in_progress, completed, expired)
    - Start time (if started)
    - Time remaining in seconds (if in progress)
    - Submission time (if completed)
    
    **Use Case**: Display test timer, check if test can be started/submitted.
    """,
    responses={
        200: {
            "description": "Status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "in_progress",
                        "start_time": "2024-01-15T10:00:00",
                        "time_remaining": 5400,
                        "duration_minutes": 180
                    }
                }
            }
        }
    }
)
async def get_test_status(
    test_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get test status and timing information.
    
    Args:
        test_id: Test identifier
        current_user: Authenticated user information
        
    Returns:
        Status information dictionary
        
    Raises:
        HTTPException: If test not found or access denied
    """
    logger.info(f"Status request for test: {test_id}")
    
    # Get and verify test access
    test = await verify_test_access(test_id, current_user["student_id"])
    
    response = {
        "test_id": test_id,
        "status": test.get("status", "pending"),
        "duration_minutes": test.get("duration_minutes", 180)
    }
    
    # Add start time if available
    if test.get("start_date"):
        response["start_time"] = test["start_date"]
        
        # Calculate time remaining if in progress
        if test.get("status") == "in_progress":
            # In production, calculate actual time remaining
            # start_time = datetime.fromisoformat(test["start_date"])
            # duration = timedelta(minutes=test.get("duration_minutes", 180))
            # end_time = start_time + duration
            # time_remaining = (end_time - datetime.utcnow()).total_seconds()
            # response["time_remaining"] = max(0, int(time_remaining))
            
            # Mock calculation
            response["time_remaining"] = 5400  # 90 minutes in seconds
    
    # Add submission time if completed
    if test.get("submission_date"):
        response["submission_time"] = test["submission_date"]
    
    return response


@router.patch(
    "/{test_id}/status",
    response_model=SuccessResponse,
    summary="Update Test Status (Admin Only)",
    description="""
    Update test status. **Admin only**.
    
    **Use Cases**:
    - Reset test to allow retake
    - Mark test as expired
    - Cancel test
    
    **Valid Status Transitions**:
    - Any status → 'cancelled'
    - 'in_progress' → 'expired' (if time exceeded)
    - 'completed' → 'pending' (admin reset for retake)
    
    **Restrictions**:
    - Only admins can update status
    - Some transitions may not be allowed
    """,
    responses={
        200: {
            "description": "Status updated successfully",
            "model": SuccessResponse
        },
        403: {
            "description": "Admin privileges required",
            "model": ErrorResponse
        }
    }
)
async def update_test_status(
    test_id: str,
    request_body: Dict,
    current_user: dict = Depends(verify_admin)
):
    """
    Update test status (admin only).
    
    Args:
        test_id: Test identifier
        request_body: Request body with new status
        current_user: Authenticated admin user
        
    Returns:
        Success response
        
    Raises:
        HTTPException: If update fails
    """
    new_status = request_body.get("status")
    
    logger.info(f"Status update request: test_id={test_id}, new_status={new_status}")
    
    # Validate status
    try:
        TestStatus(new_status)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status: {new_status}"
        )
    
    # Get test
    test = await get_test_from_db(test_id)
    
    try:
        # In production, update in Firestore
        # db = get_firestore_client()
        # test_ref = db.collection('diagnostic_tests').document(test_id)
        # test_ref.update({
        #     'status': new_status,
        #     'updated_at': datetime.utcnow().isoformat(),
        #     'updated_by': current_user['student_id']
        # })
        
        logger.info(
            f"Test status updated: {test_id} from {test.get('status')} to {new_status}"
        )
        
        return SuccessResponse(
            message="Test status updated successfully",
            data={
                "test_id": test_id,
                "old_status": test.get("status"),
                "new_status": new_status
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to update status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status: {str(e)}"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/management/health",
    summary="Health Check",
    description="Check if the test management service is operational",
    tags=["Health"]
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "test-management",
        "timestamp": datetime.utcnow().isoformat()
    }
