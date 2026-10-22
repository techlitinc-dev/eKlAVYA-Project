"""
Study Center Service

This module provides orchestration for Study Center Learning Journey
feature in Mentor AI EdTech Platform, coordinating between
learning material generation and progress tracking.

Features:
- Topic management from syllabus data
- Material orchestration with caching
- Learning journey sequencing
- Progress calculation and insights
- Parent dashboard integration

Author: Mentor AI Team
Version: 1.0.0
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.study_center_models import (
    Topic, LearningMaterials, LearningJourney, ProgressSummary
)
from services.learning_material_service import (
    get_learning_material_service, LearningMaterialService
)
from services.progress_tracker_service import (
    get_progress_tracker_service, ProgressTrackerService
)
from utils.firebase_config import get_firestore_client
from utils.study_center_prompts import (
    build_prerequisite_check_prompt,
    build_motivational_message
)

# Configure logging
logger = logging.getLogger(__name__)


class StudyCenterService:
    """
    Service for orchestrating study center operations.
    
    This service coordinates between learning material generation,
    progress tracking, and provides high-level operations
    for the Study Center feature.
    
    Attributes:
        material_service: LearningMaterialService instance
        progress_service: ProgressTrackerService instance
        db: Firestore database client
    
    Example:
        >>> service = StudyCenterService()
        >>> topics = service.get_topics_for_student("student_123", "JEE_MAIN")
        >>> materials = service.get_learning_materials("T02", "student_123")
    """
    
    def __init__(
        self,
        material_service: Optional[LearningMaterialService] = None,
        progress_service: Optional[ProgressTrackerService] = None
    ):
        """
        Initialize StudyCenterService.
        
        Args:
            material_service: Optional LearningMaterialService instance
            progress_service: Optional ProgressTrackerService instance
        """
        logger.info("Initializing StudyCenterService")
        
        # Initialize services
        self.material_service = (
            material_service if material_service 
            else get_learning_material_service()
        )
        
        self.progress_service = (
            progress_service if progress_service 
            else get_progress_tracker_service()
        )
        
        # Initialize Firestore client
        self.db = get_firestore_client()
        logger.info("Firestore client initialized")
        
        logger.info("StudyCenterService initialized")
    
    def get_topics_for_student(
        self,
        student_id: str,
        subject: Optional[str] = None
    ) -> List[Topic]:
        """
        Get available topics for a student's exam type.
        
        Loads topics from syllabus files and enriches
        them with progress data from Firestore.
        
        Args:
            student_id: ID of the student
            subject: Optional subject filter
        
        Returns:
            List of Topic objects with progress information
        
        Example:
            >>> service = StudyCenterService()
            >>> topics = service.get_topics_for_student("student_123", "Physics")
            >>> print(f"Found {len(topics)} Physics topics")
        """
        try:
            # Get student's exam type (would come from student profile)
            exam_type = self._get_student_exam_type(student_id)
            
            # Load syllabus topics
            syllabus_topics = self._load_syllabus_topics(exam_type, subject)
            
            # Get student's progress
            progress_summary = self.progress_service.get_all_progress(student_id)
            
            # Enrich topics with progress data
            enriched_topics = []
            for topic_data in syllabus_topics:
                topic_id = topic_data.get("topic_id", "")
                
                # Create Topic object
                topic = Topic(
                    topic_id=topic_id,
                    topic_name=topic_data.get("topic_name", topic_id),
                    subject=topic_data.get("subject", "Unknown"),
                    chapter=topic_data.get("chapter_name", "Unknown"),
                    difficulty=topic_data.get("difficulty", "medium"),
                    estimated_hours=topic_data.get("estimated_hours", 5.0),
                    prerequisites=topic_data.get("prerequisites", []),
                    is_completed=self.progress_service.get_topic_progress(student_id, topic_id) >= 100,
                    completion_percentage=self.progress_service.get_topic_progress(student_id, topic_id)
                )
                
                enriched_topics.append(topic)
            
            logger.info(
                f"Retrieved {len(enriched_topics)} topics for student {student_id}"
                f"{' (filtered by ' + subject + ')' if subject else ''}"
            )
            
            return enriched_topics
        
        except Exception as e:
            logger.error(f"Error getting topics for student: {e}")
            logger.exception("Full traceback:")
            raise
    
    def get_learning_materials(
        self,
        topic_id: str,
        student_id: str
    ) -> LearningMaterials:
        """
        Get or generate learning materials for a topic.
        
        Checks cache first, generates new materials if needed,
        and starts a learning session for tracking.
        
        Args:
            topic_id: ID of the topic
            student_id: ID of the student
        
        Returns:
            LearningMaterials object with all available materials
        
        Example:
            >>> service = StudyCenterService()
            >>> materials = service.get_learning_materials("T02", "student_123")
            >>> print(f"Materials cached: {materials.cached}")
        """
        try:
            # Get student's exam type
            exam_type = self._get_student_exam_type(student_id)
            
            # Generate or retrieve materials
            materials = self.material_service.generate_materials(
                topic_id=topic_id,
                exam_type=exam_type,
                student_id=student_id,
                material_types=["notes", "mind_map", "teaching_content"]
            )
            
            logger.info(
                f"Retrieved materials for topic {topic_id}, "
                f"cached: {materials.cached}"
            )
            
            return materials
        
        except Exception as e:
            logger.error(f"Error getting learning materials: {e}")
            logger.exception("Full traceback:")
            raise
    
    def check_material_cache(
        self,
        topic_id: str,
        material_type: str,
        exam_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if materials exist in cache.
        
        Queries Firestore to check if specific material
        type for a topic is cached and not expired.
        
        Args:
            topic_id: ID of the topic
            material_type: Type of material to check
            exam_type: Type of exam
        
        Returns:
            Cached material data or None if not found
        
        Example:
            >>> service = StudyCenterService()
            >>> cached = service.check_material_cache("T02", "notes", "JEE_MAIN")
            >>> print(f"Cached: {cached is not None}")
        """
        try:
            # Query learning_materials collection
            materials_ref = self.db.collection("learning_materials")
            query = materials_ref.where(
                "topic_id", "==", topic_id
            ).where(
                "exam_type", "==", exam_type
            ).where(
                "material_type", "==", material_type
            ).where(
                "cache_expires_at", ">", datetime.now()
            )
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                logger.debug(f"Found cached {material_type} for {topic_id}")
                return data
            
            return None
        
        except Exception as e:
            logger.error(f"Error checking material cache: {e}")
            return None
    
    def get_learning_journey(self, student_id: str) -> LearningJourney:
        """
        Get recommended learning sequence for a student.
        
        Analyzes student's progress and creates a recommended
        learning path with prerequisites and next steps.
        
        Args:
            student_id: ID of the student
        
        Returns:
            LearningJourney object with sequence and recommendations
        
        Example:
            >>> service = StudyCenterService()
            >>> journey = service.get_learning_journey("student_123")
            >>> print(f"Next topic: {journey.next_topic.topic_name}")
        """
        try:
            # Get student's exam type and topics
            exam_type = self._get_student_exam_type(student_id)
            all_topics = self.get_topics_for_student(student_id)
            
            # Separate completed and incomplete topics
            completed_topics = [
                topic for topic in all_topics if topic.is_completed
            ]
            incomplete_topics = [
                topic for topic in all_topics if not topic.is_completed
            ]
            
            # Create recommended sequence
            # Simple implementation: order by difficulty and prerequisites
            sorted_topics = sorted(
                incomplete_topics,
                key=lambda t: (t.difficulty, len(t.prerequisites))
            )
            
            # Find next topic (first incomplete with completed prerequisites)
            next_topic = None
            prerequisites_pending = []
            
            for topic in sorted_topics:
                # Check if all prerequisites are completed
                prereq_completed = all(
                    any(pt.topic_id == prereq for pt in completed_topics)
                    for prereq in topic.prerequisites
                )
                
                if prereq_completed and not next_topic:
                    next_topic = topic
                elif not prereq_completed:
                    prerequisites_pending.append(topic)
            
            # If no next topic found, use first incomplete
            if not next_topic and incomplete_topics:
                next_topic = incomplete_topics[0]
            
            # Generate motivational message
            progress_summary = self.progress_service.get_all_progress(student_id)
            motivational_message = build_motivational_message(
                progress_percentage=progress_summary.completion_percentage,
                topics_completed=progress_summary.completed_topics,
                total_topics=progress_summary.total_topics,
                current_streak=progress_summary.current_streak_days,
                recent_activity=self._get_recent_activity(student_id)
            )
            
            # Create LearningJourney
            journey = LearningJourney(
                student_id=student_id,
                recommended_sequence=sorted_topics,
                next_topic=next_topic or incomplete_topics[0] if incomplete_topics else completed_topics[-1],
                prerequisites_pending=prerequisites_pending,
                motivational_message=motivational_message
            )
            
            logger.info(
                f"Generated learning journey for student {student_id}, "
                f"next topic: {next_topic.topic_name if next_topic else 'None'}"
            )
            
            return journey
        
        except Exception as e:
            logger.error(f"Error generating learning journey: {e}")
            logger.exception("Full traceback:")
            raise
    
    def get_progress_summary(self, student_id: str) -> ProgressSummary:
        """
        Get student's overall progress summary.
        
        Delegates to progress tracker service to get
        comprehensive progress analytics.
        
        Args:
            student_id: ID of the student
        
        Returns:
            ProgressSummary object with comprehensive analytics
        
        Example:
            >>> service = StudyCenterService()
            >>> summary = service.get_progress_summary("student_123")
            >>> print(f"Overall progress: {summary.completion_percentage}%")
        """
        try:
            return self.progress_service.get_all_progress(student_id)
        
        except Exception as e:
            logger.error(f"Error getting progress summary: {e}")
            logger.exception("Full traceback:")
            raise
    
    def _get_student_exam_type(self, student_id: str) -> str:
        """
        Get student's exam type from profile.
        
        This is a simplified implementation. In production,
        this would query the student's profile in Firestore.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        """
        # Simplified implementation - would query student profile
        return "JEE_MAIN"  # Default for now
    
    def _load_syllabus_topics(
        self,
        exam_type: str,
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load topics from syllabus JSON files.
        
        Reads syllabus files and extracts topic data,
        optionally filtering by subject.
        
        Args:
            exam_type: Type of exam
            subject: Optional subject filter
        
        Returns:
            List of topic data dictionaries
        """
        try:
            # Determine which syllabus files to read
            subject_files = {
                "JEE_MAIN": {
                    "Physics": "data/syllabus/JEE_MAIN_Physics.json",
                    "Chemistry": "data/syllabus/JEE_MAIN_Chemistry.json",
                    "Mathematics": "data/syllabus/JEE_MAIN_Mathematics.json"
                },
                "JEE_ADVANCED": {
                    "Physics": "data/syllabus/JEE_ADVANCED_Physics.json",
                    "Chemistry": "data/syllabus/JEE_ADVANCED_Chemistry.json",
                    "Mathematics": "data/syllabus/JEE_ADVANCED_Mathematics.json"
                },
                "NEET": {
                    "Physics": "data/syllabus/NEET_Physics.json",
                    "Chemistry": "data/syllabus/NEET_Chemistry.json",
                    "Biology": "data/syllabus/NEET_Biology.json"
                }
            }
            
            all_topics = []
            
            # Load from relevant files
            files_to_load = subject_files.get(exam_type, {})
            
            for subj_name, file_path in files_to_load.items():
                if subject and subj_name != subject:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        syllabus = json.load(f)
                    
                    # Extract topics from all chapters
                    for chapter in syllabus.get("chapters", []):
                        chapter_name = chapter.get("chapter_name", "")
                        
                        for topic in chapter.get("topics", []):
                            # Enrich with subject and chapter info
                            enriched_topic = topic.copy()
                            enriched_topic["subject"] = subj_name
                            enriched_topic["chapter_name"] = chapter_name
                            enriched_topic["estimated_hours"] = self._estimate_study_hours(
                                topic.get("difficulty", "medium")
                            )
                            enriched_topic["prerequisites"] = self._determine_prerequisites(
                                topic.get("topic_id", ""), chapter_name
                            )
                            
                            all_topics.append(enriched_topic)
                
                except FileNotFoundError:
                    logger.warning(f"Syllabus file not found: {file_path}")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing syllabus file {file_path}: {e}")
                    continue
            
            logger.info(
                f"Loaded {len(all_topics)} topics from {exam_type} syllabus"
                f"{' for ' + subject + ')' if subject else ''}"
            )
            
            return all_topics
        
        except Exception as e:
            logger.error(f"Error loading syllabus topics: {e}")
            logger.exception("Full traceback:")
            return []
    
    def _estimate_study_hours(self, difficulty: str) -> float:
        """
        Estimate study hours based on difficulty.
        
        Args:
            difficulty: Difficulty level (easy, medium, hard)
        
        Returns:
            Estimated study hours
        """
        difficulty_hours = {
            "easy": 3.0,
            "medium": 6.0,
            "hard": 10.0
        }
        
        return difficulty_hours.get(difficulty, 6.0)
    
    def _determine_prerequisites(
        self,
        topic_id: str,
        chapter_name: str
    ) -> List[str]:
        """
        Determine prerequisites for a topic.
        
        Simple implementation that sets prerequisites based on
        topic order within chapters.
        
        Args:
            topic_id: ID of the topic
            chapter_name: Name of the chapter
        
        Returns:
            List of prerequisite topic IDs
        """
        # Simple prerequisite logic
        # In production, this would be more sophisticated
        topic_num = int(topic_id[1:]) if topic_id.startswith("T") else 0
        
        # Previous topic is prerequisite
        if topic_num > 1:
            return [f"T{topic_num - 1:02d}"]
        
        return []
    
    def _get_student_achievements(self, student_id: str) -> List[str]:
        """
        Get student's achievements for motivation.
        
        Args:
            student_id: ID of the student
        
        Returns:
            List of achievement identifiers
        """
        try:
            # Query progress document
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id)
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                progress_data = doc.to_dict()
                return progress_data.get("achievements", [])
            
            return []
        
        except Exception as e:
            logger.error(f"Error getting student achievements: {e}")
            return []
    
    def _get_recent_activity(self, student_id: str) -> str:
        """
        Get description of student's recent activity.
        
        Queries recent learning sessions to create
        a human-readable activity description.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Description of recent activity
        """
        try:
            # Query recent sessions
            sessions_ref = self.db.collection("learning_sessions")
            query = sessions_ref.where(
                "student_id", "==", student_id
            ).order_by(
                "start_time", direction="DESCENDING"
            )
            
            docs = query.limit(5).stream()
            
            if not docs:
                return "hasn't started studying yet"
            
            # Get most recent session
            recent_session = docs[0].to_dict()
            topic_name = recent_session.get("topic_name", "a topic")
            start_time = recent_session.get("start_time")
            
            if start_time:
                # Calculate how recent
                hours_ago = (datetime.now() - start_time).total_seconds() / 3600
                
                if hours_ago < 1:
                    return f"started studying {topic_name} just now"
                elif hours_ago < 24:
                    return f"studied {topic_name} today"
                elif hours_ago < 48:
                    return f"studied {topic_name} yesterday"
                else:
                    return f"last studied {topic_name}"
            
            return "has been studying"
        
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return "has been studying"


# Singleton instance
_study_center_service_instance: Optional[StudyCenterService] = None


def get_study_center_service(
    material_service: Optional[LearningMaterialService] = None,
    progress_service: Optional[ProgressTrackerService] = None
) -> StudyCenterService:
    """
    Get or create singleton StudyCenterService instance.
    
    Args:
        material_service: Optional LearningMaterialService instance
        progress_service: Optional ProgressTrackerService instance
    
    Returns:
        StudyCenterService instance
    
    Example:
        >>> service = get_study_center_service()
        >>> topics = service.get_topics_for_student("student_123")
    """
    global _study_center_service_instance
    
    if _study_center_service_instance is None:
        logger.info("Creating new StudyCenterService singleton instance")
        _study_center_service_instance = StudyCenterService(
            material_service=material_service,
            progress_service=progress_service
        )
    
    return _study_center_service_instance


# Module initialization
logger.info("Study center service module loaded")