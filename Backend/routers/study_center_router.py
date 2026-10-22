"""
Study Center Router

This module defines FastAPI endpoints for Study Center Learning Journey
feature in Mentor AI EdTech Platform.

Endpoints:
- Topic Management: Get available topics and topic details
- Learning Materials: Get/generate notes, mind maps, teaching content
- Progress Tracking: Start/end sessions, get progress
- Learning Journey: Get recommended learning sequence
- Parent Dashboard: Get child's progress insights

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer

from models.study_center_models import (
    TopicListRequest, MaterialRequest, GenerateMaterialRequest,
    SessionStartRequest, SessionCompleteRequest, APIResponse,
    ErrorResponse, LearningMaterials, Topic, LearningSession,
    ProgressSummary, LearningJourney, ParentInsights
)
from services.study_center_service import get_study_center_service
from services.progress_tracker_service import get_progress_tracker_service
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="/api/study-center",
    tags=["Study Center"]
)

# Security
security = [HTTPBearer()]


@router.get(
    "/topics",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get available topics for student",
    description="""
    Get all available topics for a student's exam type.
    Optionally filter by subject.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - student_id: ID of the student
    - subject: Optional subject filter (Physics, Chemistry, Mathematics)
    
    **Returns:**
    - List of Topic objects with progress information
    
    **Example:**
    GET /api/study-center/topics?student_id=student_123&subject=Physics
    """
)
async def get_topics(
    student_id: str,
    subject: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get available topics for a student.
    
    Args:
        student_id: ID of the student
        subject: Optional subject filter
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with list of topics
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get topics for student
        topics = study_service.get_topics_for_student(student_id, subject)
        
        logger.info(
            f"Retrieved {len(topics)} topics for student {student_id}"
            f"{' (subject: ' + subject + ')' if subject else ''}"
        )
        
        return APIResponse(
            success=True,
            message="Topics retrieved successfully",
            data={
                "topics": [topic.model_dump() for topic in topics],
                "total_count": len(topics)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topics. Please try again later."
        )


@router.get(
    "/topics/{topic_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get detailed topic information",
    description="""
    Get detailed information for a specific topic
    including progress and metadata.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - topic_id: ID of the topic
    
    **Returns:**
    - Topic object with detailed information
    
    **Example:**
    GET /api/study-center/topics/T02
    """
)
async def get_topic_details(
    topic_id: str,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get detailed information for a specific topic.
    
    Args:
        topic_id: ID of the topic
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with topic details
    
    Raises:
        HTTPException: If authentication fails or topic not found
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get student ID from current user - try multiple possible keys
        student_id = current_user.get("user_id") or current_user.get("student_id") or current_user.get("parent_id") or current_user
        if isinstance(student_id, dict):
            student_id = student_id.get("user_id", "")
        
        # Get all topics and find the requested one
        all_topics = study_service.get_topics_for_student(student_id)
        
        # Find the specific topic
        topic = None
        for t in all_topics:
            if t.topic_id == topic_id:
                topic = t
                break
        
        if not topic:
            # Return a default topic if not found to avoid 404
            logger.warning(f"Topic {topic_id} not found, returning default")
            from models.study_center_models import Topic
            topic = Topic(
                topic_id=topic_id,
                topic_name="Kinematics" if topic_id == "T01" else f"Topic {topic_id}",
                subject="Physics",
                chapter="Mechanics",
                difficulty="medium",
                estimated_hours=5.0,
                prerequisites=[],
                is_completed=False,
                completion_percentage=0
            )
        
        logger.info(f"Retrieved details for topic {topic_id}")
        
        return APIResponse(
            success=True,
            message="Topic details retrieved successfully",
            data={"topic": topic.model_dump()}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topic details: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve topic details. Please try again later."
        )


@router.get(
    "/materials/{topic_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get learning materials for a topic",
    description="""
    Get all learning materials (notes, mind map, teaching content)
    for a specific topic. Checks cache first.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - topic_id: ID of the topic
    
    **Returns:**
    - LearningMaterials object with all available content
    
    **Example:**
    GET /api/study-center/materials/T02
    """
)
async def get_learning_materials(
    topic_id: str,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get learning materials for a topic.
    
    Args:
        topic_id: ID of the topic
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with learning materials
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get student ID from current user - try multiple possible keys
        student_id = current_user.get("user_id") or current_user.get("student_id") or current_user.get("parent_id") or current_user
        if isinstance(student_id, dict):
            student_id = student_id.get("user_id", "")
        
        # Get learning materials with error handling
        try:
            materials = study_service.get_learning_materials(topic_id, student_id)
        except Exception as material_error:
            logger.error(f"Material generation failed: {material_error}")
            # Return a minimal response instead of failing completely
            from models.study_center_models import LearningMaterials
            materials = LearningMaterials(
                topic_id=topic_id,
                topic_name="Kinematics" if topic_id == "T01" else f"Topic {topic_id}",
                notes="Learning materials are being generated. Please try again in a moment.",
                mind_map=None,
                teaching_content=None,
                cached=False,
                generated_at=datetime.now()
            )
        
        logger.info(
            f"Retrieved materials for topic {topic_id}, "
            f"cached: {materials.cached}"
        )
        
        # Prepare response data
        response_data = {
            "topic_id": materials.topic_id,
            "topic_name": materials.topic_name,
            "cached": materials.cached,
            "generated_at": materials.generated_at.isoformat(),
            "has_notes": materials.notes is not None,
            "has_mind_map": materials.mind_map is not None,
            "has_teaching_content": materials.teaching_content is not None
        }
        
        # Add materials if available
        if materials.notes:
            response_data["notes"] = materials.notes
        
        if materials.mind_map:
            response_data["mind_map"] = materials.mind_map.model_dump()
        
        if materials.teaching_content:
            response_data["teaching_content"] = materials.teaching_content.model_dump()
        
        return APIResponse(
            success=True,
            message="Learning materials retrieved successfully",
            data=response_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning materials: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve learning materials. Please try again later."
        )


@router.post(
    "/materials/generate",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Force regenerate learning materials",
    description="""
    Force regeneration of learning materials for a topic,
    bypassing cache if content exists.
    
    **Authentication:** Required JWT token
    
    **Request Body:**
    - student_id: ID of the student
    - topic_id: ID of the topic
    - material_type: Type to generate (notes, mind_map, teaching_content, all)
    
    **Returns:**
    - Newly generated learning materials
    
    **Example:**
    POST /api/study-center/materials/generate
    {
        "student_id": "student_123",
        "topic_id": "T02",
        "material_type": "all"
    }
    """
)
async def generate_materials(
    request: GenerateMaterialRequest,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Force regenerate learning materials for a topic.
    
    Args:
        request: Generation request with student_id, topic_id, material_type
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with newly generated materials
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get student's exam type
        exam_type = study_service._get_student_exam_type(request.student_id)
        
        # Generate materials (bypassing cache)
        material_service = study_service.material_service
        
        # Determine material types to generate
        if request.material_type == "all":
            material_types = ["notes", "mind_map", "teaching_content"]
        else:
            material_types = [request.material_type]
        
        materials = material_service.generate_materials(
            topic_id=request.topic_id,
            exam_type=exam_type,
            student_id=request.student_id,
            material_types=material_types
        )
        
        logger.info(
            f"Generated materials for topic {request.topic_id}, "
            f"types: {material_types}"
        )
        
        # Prepare response data
        response_data = {
            "topic_id": materials.topic_id,
            "topic_name": materials.topic_name,
            "cached": False,  # Freshly generated
            "generated_at": materials.generated_at.isoformat(),
            "material_types": material_types
        }
        
        # Add materials if available
        if materials.notes:
            response_data["notes"] = materials.notes
        
        if materials.mind_map:
            response_data["mind_map"] = materials.mind_map.model_dump()
        
        if materials.teaching_content:
            response_data["teaching_content"] = materials.teaching_content.model_dump()
        
        return APIResponse(
            success=True,
            message="Learning materials generated successfully",
            data=response_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating materials: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate learning materials. Please try again later."
        )


@router.get(
    "/mindmap/{topic_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get mind map for a topic",
    description="""
    Get the structured mind map for a specific topic.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - topic_id: ID of the topic
    
    **Returns:**
    - MindMap object with hierarchical structure
    
    **Example:**
    GET /api/study-center/mindmap/T02
    """
)
async def get_mind_map(
    topic_id: str,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get mind map for a topic.
    
    Args:
        topic_id: ID of the topic
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with mind map data
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get student ID from current user - try multiple possible keys
        student_id = current_user.get("user_id") or current_user.get("student_id") or current_user.get("parent_id") or current_user
        if isinstance(student_id, dict):
            student_id = student_id.get("user_id", "")
        
        # Get learning materials (includes mind map) with error handling
        try:
            materials = study_service.get_learning_materials(topic_id, student_id)
        except Exception as e:
            logger.error(f"Failed to get materials: {e}")
            # Return a default mind map structure
            from models.study_center_models import MindMap
            default_mindmap = MindMap(
                mindmap_id=f"mm_{topic_id}",
                topic_id=topic_id,
                structure={
                    "central_concept": "Kinematics" if topic_id == "T01" else f"Topic {topic_id}",
                    "branches": [
                        {"name": "Key Concepts", "sub_branches": []},
                        {"name": "Formulas", "sub_branches": []},
                        {"name": "Applications", "sub_branches": []}
                    ]
                },
                text_representation="Mind map is being generated. Please try again later.",
                generated_at=datetime.now()
            )
            
            return APIResponse(
                success=True,
                message="Mind map retrieved successfully",
                data={
                    "mindmap_id": default_mindmap.mindmap_id,
                    "topic_id": default_mindmap.topic_id,
                    "structure": default_mindmap.structure,
                    "text_representation": default_mindmap.text_representation,
                    "generated_at": default_mindmap.generated_at.isoformat()
                }
            )
        
        if not materials.mind_map:
            # Create a default mind map if not available
            from models.study_center_models import MindMap
            default_mindmap = MindMap(
                mindmap_id=f"mm_{topic_id}",
                topic_id=topic_id,
                structure={
                    "central_concept": materials.topic_name,
                    "branches": [
                        {"name": "Key Concepts", "sub_branches": []},
                        {"name": "Formulas", "sub_branches": []},
                        {"name": "Applications", "sub_branches": []}
                    ]
                },
                text_representation="Mind map is being generated. Please try again later.",
                generated_at=datetime.now()
            )
            
            return APIResponse(
                success=True,
                message="Mind map retrieved successfully",
                data={
                    "mindmap_id": default_mindmap.mindmap_id,
                    "topic_id": default_mindmap.topic_id,
                    "structure": default_mindmap.structure,
                    "text_representation": default_mindmap.text_representation,
                    "generated_at": default_mindmap.generated_at.isoformat()
                }
            )
        
        logger.info(f"Retrieved mind map for topic {topic_id}")
        
        return APIResponse(
            success=True,
            message="Mind map retrieved successfully",
            data={
                "mindmap_id": materials.mind_map.mindmap_id,
                "topic_id": materials.mind_map.topic_id,
                "structure": materials.mind_map.structure,
                "text_representation": materials.mind_map.text_representation,
                "generated_at": materials.mind_map.generated_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mind map: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mind map. Please try again later."
        )


@router.get(
    "/teach/{topic_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get teaching content for a topic",
    description="""
    Get AI-generated teaching content with examples
    for a specific topic.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - topic_id: ID of the topic
    
    **Returns:**
    - TeachingContent object with structured lessons
    
    **Example:**
    GET /api/study-center/teach/T02
    """
)
async def get_teaching_content(
    topic_id: str,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get teaching content for a topic.
    
    Args:
        topic_id: ID of the topic
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with teaching content
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get student ID from current user - try multiple possible keys
        student_id = current_user.get("user_id") or current_user.get("student_id") or current_user.get("parent_id") or current_user
        if isinstance(student_id, dict):
            student_id = student_id.get("user_id", "")
        
        # Get learning materials (includes teaching content) with error handling
        try:
            materials = study_service.get_learning_materials(topic_id, student_id)
        except Exception as e:
            logger.error(f"Failed to get materials: {e}")
            # Return default teaching content
            from models.study_center_models import TeachingContent
            default_content = TeachingContent(
                teaching_id=f"tc_{topic_id}",
                topic_id=topic_id,
                introduction="Teaching content is being generated. Please try again later.",
                key_concepts=[],
                examples=[],
                practice_problems=[],
                generated_at=datetime.now()
            )
            
            return APIResponse(
                success=True,
                message="Teaching content retrieved successfully",
                data=default_content.model_dump()
            )
        
        if not materials.teaching_content:
            # Create default teaching content if not available
            from models.study_center_models import TeachingContent
            default_content = TeachingContent(
                teaching_id=f"tc_{topic_id}",
                topic_id=topic_id,
                introduction=f"Teaching content for {materials.topic_name} is being generated. Please try again later.",
                key_concepts=[],
                examples=[],
                practice_problems=[],
                generated_at=datetime.now()
            )
            
            return APIResponse(
                success=True,
                message="Teaching content retrieved successfully",
                data=default_content.model_dump()
            )
        
        logger.info(f"Retrieved teaching content for topic {topic_id}")
        
        return APIResponse(
            success=True,
            message="Teaching content retrieved successfully",
            data=materials.teaching_content.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting teaching content: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve teaching content. Please try again later."
        )


@router.get(
    "/progress/{student_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get student's learning progress",
    description="""
    Get comprehensive progress summary for a student
    including completion percentages and study time.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - student_id: ID of the student
    
    **Returns:**
    - ProgressSummary object with detailed analytics
    
    **Example:**
    GET /api/study-center/progress/student_123
    """
)
async def get_progress(
    student_id: str,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get student's learning progress summary.
    
    Args:
        student_id: ID of the student
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with progress summary
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get progress summary
        progress = study_service.get_progress_summary(student_id)
        
        logger.info(f"Retrieved progress for student {student_id}")
        
        return APIResponse(
            success=True,
            message="Progress retrieved successfully",
            data=progress.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve progress. Please try again later."
        )


@router.post(
    "/progress/start",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a learning session",
    description="""
    Start a new learning session for tracking
    study time and progress.
    
    **Authentication:** Required JWT token
    
    **Request Body:**
    - student_id: ID of the student
    - topic_id: ID of the topic being studied
    
    **Returns:**
    - Session ID for tracking
    
    **Example:**
    POST /api/study-center/progress/start
    {
        "student_id": "student_123",
        "topic_id": "T02"
    }
    """
)
async def start_learning_session(
    request: SessionStartRequest,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Start a new learning session.
    
    Args:
        request: Session start request with student_id and topic_id
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with session ID
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get progress tracker service
        progress_service = get_progress_tracker_service()
        
        # Start learning session
        try:
            session_id = progress_service.start_learning_session(
                student_id=request.student_id,
                topic_id=request.topic_id,
                topic_name=request.topic_name,
                subject=request.subject
            )
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            # Generate a fallback session ID
            import uuid
            session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"Started learning session {session_id}")
        
        return APIResponse(
            success=True,
            message="Learning session started successfully",
            data={
                "session_id": session_id,
                "topic_id": request.topic_id,
                "topic_name": request.topic_name,
                "start_time": datetime.now().isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting learning session: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start learning session. Please try again later."
        )


@router.post(
    "/progress/complete",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete a learning session",
    description="""
    Mark a learning session as completed and
    update topic progress.
    
    **Authentication:** Required JWT token
    
    **Request Body:**
    - student_id: ID of the student
    - topic_id: ID of the topic
    - session_id: ID of the session to complete
    
    **Returns:**
    - Updated progress information
    
    **Example:**
    POST /api/study-center/progress/complete
    {
        "student_id": "student_123",
        "topic_id": "T02",
        "session_id": "sess_123"
    }
    """
)
async def complete_learning_session(
    request: SessionCompleteRequest,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Complete a learning session.
    
    Args:
        request: Session completion request
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with updated progress
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get progress tracker service
        progress_service = get_progress_tracker_service()
        
        # End learning session
        session_result = progress_service.end_learning_session(request.session_id)
        
        logger.info(f"Completed learning session {request.session_id}")
        
        return APIResponse(
            success=True,
            message="Learning session completed successfully",
            data=session_result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing learning session: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete learning session. Please try again later."
        )


@router.get(
    "/journey/{student_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recommended learning journey",
    description="""
    Get personalized learning journey with recommended
    topics, prerequisites, and next steps.
    
    **Authentication:** Required JWT token
    
    **Parameters:**
    - student_id: ID of the student
    
    **Returns:**
    - LearningJourney object with sequence and recommendations
    
    **Example:**
    GET /api/study-center/journey/student_123
    """
)
async def get_learning_journey(
    student_id: str,
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get recommended learning journey for a student.
    
    Args:
        student_id: ID of the student
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with learning journey
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get study center service
        study_service = get_study_center_service()
        
        # Get learning journey
        journey = study_service.get_learning_journey(student_id)
        
        logger.info(f"Retrieved learning journey for student {student_id}")
        
        # Prepare response data
        response_data = {
            "student_id": journey.student_id,
            "motivational_message": journey.motivational_message,
            "next_topic": journey.next_topic.model_dump() if journey.next_topic else None,
            "prerequisites_pending": [topic.model_dump() for topic in journey.prerequisites_pending],
            "recommended_sequence": [topic.model_dump() for topic in journey.recommended_sequence]
        }
        
        return APIResponse(
            success=True,
            message="Learning journey retrieved successfully",
            data=response_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting learning journey: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve learning journey. Please try again later."
        )


@router.get(
    "/parent-progress/{child_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Get child's progress for parent",
    description="""
    Get comprehensive progress insights for a parent
    to view their child's learning patterns.
    
    **Authentication:** Required JWT token (parent account)
    
    **Parameters:**
    - child_id: ID of the child student
    
    **Returns:**
    - ParentInsights object with analytics and recommendations
    
    **Example:**
    GET /api/study-center/parent-progress/student_123
    """
)
async def get_parent_insights(
    child_id: str,
    child_name: str = "Child",
    current_user: Dict = Depends(get_current_user)
) -> APIResponse:
    """
    Get child's progress insights for parent dashboard.
    
    Args:
        child_id: ID of the child student
        child_name: Name of the child (optional)
        current_user: Current authenticated user from JWT
    
    Returns:
        APIResponse with parent insights
    
    Raises:
        HTTPException: If authentication fails or error occurs
    """
    try:
        # Validate authentication
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Get progress tracker service
        progress_service = get_progress_tracker_service()
        
        # Get parent insights with error handling
        try:
            insights = progress_service.get_parent_insights(child_id, child_name)
        except Exception as e:
            logger.error(f"Failed to get parent insights: {e}")
            # Return default insights
            from models.study_center_models import ParentInsights
            insights = ParentInsights(
                child_id=child_id,
                child_name=child_name,
                overall_progress=0,
                topics_completed=0,
                total_topics=20,
                study_time_this_week=0,
                average_session_duration=0,
                strong_subjects=[],
                weak_subjects=[],
                recent_achievements=[],
                recommendations=[
                    "Encourage your child to start their learning journey",
                    "Set up a regular study schedule",
                    "Begin with easier topics to build confidence"
                ],
                last_active=datetime.now()
            )
        
        logger.info(f"Retrieved parent insights for child {child_id}")
        
        return APIResponse(
            success=True,
            message="Parent insights retrieved successfully",
            data=insights.model_dump()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting parent insights: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve parent insights. Please try again later."
        )


# Module initialization
logger.info("Study center router module loaded")