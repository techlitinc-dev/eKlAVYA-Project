"""
Progress Tracker Service

This module provides progress tracking and analytics for the Study Center
Learning Journey feature in Mentor AI EdTech Platform.

Features:
- Track learning sessions with timestamps and duration
- Calculate completion percentages for topics
- Monitor study streaks and patterns
- Generate insights for parents
- Manage achievement tracking
- Award badges and milestones

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple

from models.study_center_models import (
    LearningSession, ProgressSummary, ParentInsights
)
from utils.firebase_config import get_firestore_client
from utils.study_center_prompts import (
    build_motivational_message,
    build_parent_recommendations
)

# Configure logging
logger = logging.getLogger(__name__)


class ProgressTrackerService:
    """
    Service for tracking and analyzing student learning progress.
    
    This service manages learning sessions, calculates progress metrics,
    generates insights, and tracks achievements for students.
    
    Attributes:
        db: Firestore database client
    
    Example:
        >>> service = ProgressTrackerService()
        >>> session_id = service.start_learning_session("student_123", "T02")
        >>> progress = service.get_all_progress("student_123")
    """
    
    def __init__(self):
        """
        Initialize ProgressTrackerService.
        """
        logger.info("Initializing ProgressTrackerService")
        
        # Initialize Firestore client
        self.db = get_firestore_client()
        logger.info("Firestore client initialized")
        
        logger.info("ProgressTrackerService initialized")
    
    def start_learning_session(
        self,
        student_id: str,
        topic_id: str,
        topic_name: Optional[str] = None,
        subject: Optional[str] = None
    ) -> str:
        """
        Start a new learning session.
        
        Creates a new session record with start timestamp
        and returns the session ID for tracking.
        
        Args:
            student_id: ID of the student
            topic_id: ID of the topic being studied
            topic_name: Name of the topic (optional)
            subject: Subject area (optional)
        
        Returns:
            Session ID for the new learning session
        
        Example:
            >>> service = ProgressTrackerService()
            >>> session_id = service.start_learning_session(
            ...     "student_123", "T02", "Kinematics", "Physics"
            ... )
            >>> print(f"Started session: {session_id}")
        """
        try:
            # Generate session ID
            session_id = f"sess_{student_id}_{topic_id}_{int(datetime.now().timestamp())}"
            
            # Create session document
            session_doc = {
                "session_id": session_id,
                "student_id": student_id,
                "topic_id": topic_id,
                "topic_name": topic_name or topic_id,
                "subject": subject or "Unknown",
                "start_time": datetime.now(timezone.utc),
                "end_time": None,
                "duration_minutes": None,
                "materials_viewed": [],
                "completed": False,
                "session_date": datetime.now(timezone.utc).date().isoformat(),
            }
            
            # Store in Firestore
            self.db.collection("learning_sessions").add(session_doc)
            
            logger.info(f"Started learning session {session_id} for student {student_id}")
            return session_id
        
        except Exception as e:
            logger.error(f"Error starting learning session: {e}")
            logger.exception("Full traceback:")
            raise
    
    def end_learning_session(self, session_id: str) -> Dict[str, Any]:
        """
        End a learning session and calculate duration.
        
        Updates the session with end timestamp and calculates
        the total duration in minutes.
        
        Args:
            session_id: ID of the session to end
        
        Returns:
            Dictionary with session details and duration
        
        Example:
            >>> service = ProgressTrackerService()
            >>> result = service.end_learning_session("sess_123")
            >>> print(f"Session duration: {result['duration_minutes']} minutes")
        """
        try:
            # Query for the session
            sessions_ref = self.db.collection("learning_sessions")
            query = sessions_ref.where("session_id", "==", session_id)
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                session_data = doc.to_dict()
                start_time = session_data.get("start_time")
                
                if not start_time:
                    logger.warning(f"Session {session_id} has no start time")
                    continue
                
                # Calculate duration
                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds() / 60
                
                # Update session
                update_data = {
                    "end_time": end_time,
                    "duration_minutes": int(duration),
                    "completed": True
                }
                
                doc.reference.update(update_data)
                
                # Update topic progress
                self._update_topic_progress(
                    session_data.get("student_id"),
                    session_data.get("topic_id"),
                    duration,
                    session_data.get("materials_viewed", [])
                )
                
                logger.info(f"Ended session {session_id}, duration: {duration:.1f} minutes")
                
                return {
                    "session_id": session_id,
                    "duration_minutes": int(duration),
                    "start_time": start_time,
                    "end_time": end_time
                }
            
            raise ValueError(f"Session {session_id} not found")
        
        except Exception as e:
            logger.error(f"Error ending learning session: {e}")
            logger.exception("Full traceback:")
            raise
    
    def mark_topic_complete(self, student_id: str, topic_id: str) -> Dict[str, Any]:
        """
        Mark a topic as 100% complete.
        
        Updates the progress record for a topic to indicate
        full completion and records completion timestamp.
        
        Args:
            student_id: ID of the student
            topic_id: ID of the topic to mark complete
        
        Returns:
            Dictionary with updated progress information
        
        Example:
            >>> service = ProgressTrackerService()
            >>> result = service.mark_topic_complete("student_123", "T02")
            >>> print(f"Topic marked complete: {result['completed']}")
        """
        try:
            # Get or create progress document
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id)
            
            docs = query.limit(1).stream()
            
            progress_doc = None
            for doc in docs:
                progress_doc = doc
                break
            
            if progress_doc:
                # Update existing progress
                progress_data = progress_doc.to_dict()
                topics = progress_data.get("topics", {})
                
                if topic_id in topics:
                    topics[topic_id]["completion_percentage"] = 100.0
                    topics[topic_id]["completed_at"] = datetime.now()
                    topics[topic_id]["materials_accessed"] = topics[topic_id].get("materials_accessed", [])
                else:
                    # Create new topic entry
                    topics[topic_id] = {
                        "topic_name": topic_id,
                        "subject": "Unknown",
                        "completion_percentage": 100.0,
                        "time_spent_minutes": 0,
                        "sessions_count": 0,
                        "first_accessed": datetime.now(),
                        "last_accessed": datetime.now(),
                        "completed_at": datetime.now(),
                        "materials_accessed": []
                    }
                
                # Update overall stats
                completed_topics = sum(
                    1 for topic in topics.values()
                    if topic.get("completion_percentage", 0) >= 100
                )
                total_topics = len(topics)
                
                progress_data["overall_stats"] = {
                    "total_topics": total_topics,
                    "completed_topics": completed_topics,
                    "in_progress_topics": total_topics - completed_topics,
                    "not_started_topics": 0,
                    "total_study_time_minutes": progress_data.get("overall_stats", {}).get("total_study_time_minutes", 0),
                    "current_streak_days": progress_data.get("overall_stats", {}).get("current_streak_days", 0),
                    "longest_streak_days": progress_data.get("overall_stats", {}).get("longest_streak_days", 0)
                }
                progress_data["last_updated"] = datetime.now()
                
                progress_doc.reference.update(progress_data)
                
            else:
                # Create new progress document
                progress_data = {
                    "progress_id": f"prog_{student_id}",
                    "student_id": student_id,
                    "exam_type": "JEE_MAIN",  # Would get from student profile
                    "topics": {
                        topic_id: {
                            "topic_name": topic_id,
                            "subject": "Unknown",
                            "completion_percentage": 100.0,
                            "time_spent_minutes": 0,
                            "sessions_count": 0,
                            "first_accessed": datetime.now(timezone.utc),
                            "last_accessed": datetime.now(timezone.utc),
                            "completed_at": datetime.now(timezone.utc),
                            "materials_accessed": []
                        }
                    },
                    "overall_stats": {
                        "total_topics": 1,
                        "completed_topics": 1,
                        "in_progress_topics": 0,
                        "not_started_topics": 0,
                        "total_study_time_minutes": 0,
                        "current_streak_days": 1,
                        "longest_streak_days": 1
                    },
                    "last_updated": datetime.now()
                }
                
                self.db.collection("learning_progress").add(progress_data)
            
            logger.info(f"Marked topic {topic_id} complete for student {student_id}")
            
            return {
                "student_id": student_id,
                "topic_id": topic_id,
                "completed": True,
                "completion_percentage": 100.0,
                "completed_at": datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error marking topic complete: {e}")
            logger.exception("Full traceback:")
            raise
    
    def get_topic_progress(self, student_id: str, topic_id: str) -> float:
        """
        Get completion percentage for a specific topic.
        
        Retrieves the progress data for a single topic
        and returns the completion percentage.
        
        Args:
            student_id: ID of the student
            topic_id: ID of the topic
        
        Returns:
            Completion percentage (0.0 to 100.0)
        
        Example:
            >>> service = ProgressTrackerService()
            >>> progress = service.get_topic_progress("student_123", "T02")
            >>> print(f"Progress: {progress}%")
        """
        try:
            # Query progress document
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id)
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                progress_data = doc.to_dict()
                topics = progress_data.get("topics", {})
                
                if topic_id in topics:
                    return topics[topic_id].get("completion_percentage", 0.0)
            
            return 0.0
        
        except Exception as e:
            logger.error(f"Error getting topic progress: {e}")
            return 0.0
    
    def get_all_progress(self, student_id: str) -> ProgressSummary:
        """
        Get complete progress summary for a student.
        
        Aggregates progress across all topics and calculates
        overall statistics including streaks and study time.
        
        Args:
            student_id: ID of the student
        
        Returns:
            ProgressSummary object with comprehensive progress data
        
        Example:
            >>> service = ProgressTrackerService()
            >>> summary = service.get_all_progress("student_123")
            >>> print(f"Completion: {summary.completion_percentage}%")
        """
        try:
            # Query progress document
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id)
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                progress_data = doc.to_dict()
                
                # Extract overall stats
                overall_stats = progress_data.get("overall_stats", {})
                topics = progress_data.get("topics", {})
                
                # Calculate subject-wise progress
                topics_by_subject = {}
                for topic_data in topics.values():
                    subject = topic_data.get("subject", "Unknown")
                    if subject not in topics_by_subject:
                        topics_by_subject[subject] = {"completed": 0, "total": 0}
                    
                    topics_by_subject[subject]["total"] += 1
                    if topic_data.get("completion_percentage", 0) >= 100:
                        topics_by_subject[subject]["completed"] += 1
                
                # Create ProgressSummary
                total_topics = overall_stats.get("total_topics", 0)
                completed_topics = overall_stats.get("completed_topics", 0)
                completion_percentage = (
                    (completed_topics / total_topics * 100) if total_topics > 0 else 0.0
                )
                
                return ProgressSummary(
                    student_id=student_id,
                    total_topics=total_topics,
                    completed_topics=completed_topics,
                    completion_percentage=completion_percentage,
                    total_study_time_hours=overall_stats.get("total_study_time_minutes", 0) / 60.0,
                    current_streak_days=overall_stats.get("current_streak_days", 0),
                    topics_by_subject=topics_by_subject
                )
            
            # Return empty progress if no document found
            return ProgressSummary(
                student_id=student_id,
                total_topics=0,
                completed_topics=0,
                completion_percentage=0.0,
                total_study_time_hours=0.0,
                current_streak_days=0,
                topics_by_subject={}
            )
        
        except Exception as e:
            logger.error(f"Error getting all progress: {e}")
            logger.exception("Full traceback:")
            raise
    
    def calculate_study_streaks(self, student_id: str) -> int:
        """
        Calculate consecutive study days for a student.
        
        Analyzes learning sessions to determine the current
        streak of consecutive study days.
        
        Args:
            student_id: ID of the student
        
        Returns:
            Current streak in days
        
        Example:
            >>> service = ProgressTrackerService()
            >>> streak = service.calculate_study_streaks("student_123")
            >>> print(f"Current streak: {streak} days")
        """
        try:
            # Query recent sessions
            sessions_ref = self.db.collection("learning_sessions")
            query = sessions_ref.where("student_id", "==", student_id).order_by(
                "session_date", direction="DESCENDING"
            )
            
            docs = query.limit(30).stream()  # Last 30 days
            
            # Extract unique study dates
            study_dates = set()
            for doc in docs:
                session_data = doc.to_dict()
                session_date = session_data.get("session_date")
                if session_date:
                    study_dates.add(session_date)
            
            # Calculate streak
            if not study_dates:
                return 0
            
            # Sort dates and check consecutive days
            sorted_dates = sorted(study_dates, reverse=True)
            streak = 0
            current_date = datetime.now().date()
            
            for date_str in sorted_dates:
                study_date = datetime.fromisoformat(date_str).date()
                
                if study_date == current_date:
                    streak += 1
                    current_date = current_date - timedelta(days=1)
                else:
                    break
            
            return streak
        
        except Exception as e:
            logger.error(f"Error calculating study streaks: {e}")
            return 0
    
    def get_parent_insights(self, child_id: str, child_name: str) -> ParentInsights:
        """
        Generate comprehensive progress insights for parents.
        
        Creates detailed analytics including study patterns,
        topic performance, and actionable recommendations.
        
        Args:
            child_id: ID of the child student
            child_name: Name of the child
        
        Returns:
            ParentInsights object with comprehensive analytics
        
        Example:
            >>> service = ProgressTrackerService()
            >>> insights = service.get_parent_insights("student_123", "John")
            >>> print(f"Overall progress: {insights.overall_progress}%")
        """
        try:
            # Get child's progress
            progress_summary = self.get_all_progress(child_id)
            
            # Get recent sessions for analytics
            sessions_ref = self.db.collection("learning_sessions")
            query = sessions_ref.where("student_id", "==", child_id).order_by(
                "start_time", direction="DESCENDING"
            )
            
            docs = query.limit(100).stream()  # Last 100 sessions
            
            # Analyze study patterns
            total_time_7_days = 0
            total_time_30_days = 0
            topic_study_times = {}
            last_session_time = None
            
            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)
            
            for doc in docs:
                session_data = doc.to_dict()
                start_time = session_data.get("start_time")
                duration = session_data.get("duration_minutes", 0)
                topic_id = session_data.get("topic_id", "")
                
                # Track last session
                if not last_session_time or start_time > last_session_time:
                    last_session_time = start_time
                
                # Calculate time periods
                if start_time > seven_days_ago:
                    total_time_7_days += duration
                
                if start_time > thirty_days_ago:
                    total_time_30_days += duration
                
                # Track topic study times
                if topic_id not in topic_study_times:
                    topic_study_times[topic_id] = {
                        "topic_name": session_data.get("topic_name", topic_id),
                        "time_spent_minutes": 0,
                        "sessions_count": 0
                    }
                
                topic_study_times[topic_id]["time_spent_minutes"] += duration
                topic_study_times[topic_id]["sessions_count"] += 1
            
            # Calculate averages
            daily_average = total_time_7_days / 7.0 if total_time_7_days > 0 else 0.0
            weekly_average = total_time_30_days / 4.0 if total_time_30_days > 0 else 0.0  # 4 weeks
            
            # Find most and least studied topics
            sorted_topics = sorted(
                topic_study_times.items(),
                key=lambda x: x[1]["time_spent_minutes"],
                reverse=True
            )
            
            most_studied = [
                {"topic_name": data["topic_name"], "time_spent_minutes": data["time_spent_minutes"], "sessions_count": data["sessions_count"]}
                for _, data in sorted_topics[:3]
            ]
            
            least_studied = [
                {"topic_name": data["topic_name"], "time_spent_minutes": data["time_spent_minutes"], "sessions_count": data["sessions_count"]}
                for _, data in sorted_topics[-3:] if len(sorted_topics) > 3
            ]
            
            # Calculate study consistency
            recent_sessions = [
                doc for doc in docs
                if doc.to_dict().get("start_time", datetime.min) > thirty_days_ago
            ]
            
            study_days = len(set(
                doc.to_dict().get("session_date")
                for doc in recent_sessions
            ))
            
            consistency_score = study_days / 30.0 if study_days > 0 else 0.0
            
            # Generate recommendations
            weak_areas = [
                data["topic_name"] for _, data in sorted_topics[-3:]
                if data["time_spent_minutes"] < 60  # Less than 1 hour
            ]
            
            strong_areas = [
                data["topic_name"] for _, data in sorted_topics[:3]
                if data["time_spent_minutes"] > 180  # More than 3 hours
            ]
            
            recommendations = build_parent_recommendations(
                progress_summary.completion_percentage,
                consistency_score,
                weak_areas,
                strong_areas
            )
            
            # Create ParentInsights
            return ParentInsights(
                child_id=child_id,
                child_name=child_name,
                overall_progress=progress_summary.completion_percentage,
                topics_completed=progress_summary.completed_topics,
                total_topics=progress_summary.total_topics,
                daily_average_minutes=daily_average,
                weekly_average_minutes=weekly_average,
                most_studied_topics=most_studied,
                least_studied_topics=least_studied,
                current_streak=progress_summary.current_streak_days,
                last_study_session=last_session_time or datetime.now(),
                recommendations=recommendations
            )
        
        except Exception as e:
            logger.error(f"Error generating parent insights: {e}")
            logger.exception("Full traceback:")
            raise
    
    def _update_topic_progress(
        self,
        student_id: str,
        topic_id: str,
        duration_minutes: float,
        materials_viewed: List[str]
    ):
        """
        Update progress for a topic after session ends.
        
        Internal method to update the time spent and
        materials accessed for a specific topic.
        
        Args:
            student_id: ID of the student
            topic_id: ID of the topic
            duration_minutes: Duration of the session
            materials_viewed: List of materials accessed
        """
        try:
            # Get or create progress document
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id)
            
            docs = query.limit(1).stream()
            
            progress_doc = None
            for doc in docs:
                progress_doc = doc
                break
            
            if progress_doc:
                # Update existing progress
                progress_data = progress_doc.to_dict()
                topics = progress_data.get("topics", {})
                
                if topic_id in topics:
                    # Update existing topic
                    topic_data = topics[topic_id]
                    topic_data["time_spent_minutes"] += duration_minutes
                    topic_data["sessions_count"] += 1
                    topic_data["last_accessed"] = datetime.now()
                    
                    # Update materials accessed
                    existing_materials = set(topic_data.get("materials_accessed", []))
                    existing_materials.update(materials_viewed)
                    topic_data["materials_accessed"] = list(existing_materials)
                    
                    # Check for achievements
                    self._check_and_award_achievements(
                        student_id, progress_data, topic_id, topic_data
                    )
                else:
                    # Create new topic entry
                    topics[topic_id] = {
                        "topic_name": topic_id,
                        "subject": "Unknown",
                        "completion_percentage": 0.0,
                        "time_spent_minutes": duration_minutes,
                        "sessions_count": 1,
                        "first_accessed": datetime.now(),
                        "last_accessed": datetime.now(),
                        "materials_accessed": materials_viewed
                    }
                
                # Update overall stats
                total_time = progress_data.get("overall_stats", {}).get("total_study_time_minutes", 0)
                progress_data["overall_stats"]["total_study_time_minutes"] = total_time + duration_minutes
                
                # Update streak
                current_streak = self.calculate_study_streaks(student_id)
                progress_data["overall_stats"]["current_streak_days"] = current_streak
                
                progress_data["last_updated"] = datetime.now()
                progress_doc.reference.update(progress_data)
            
            else:
                # Create new progress document
                progress_data = {
                    "progress_id": f"prog_{student_id}",
                    "student_id": student_id,
                    "exam_type": "JEE_MAIN",  # Would get from student profile
                    "topics": {
                        topic_id: {
                            "topic_name": topic_id,
                            "subject": "Unknown",
                            "completion_percentage": 0.0,
                            "time_spent_minutes": duration_minutes,
                            "sessions_count": 1,
                            "first_accessed": datetime.now(),
                            "last_accessed": datetime.now(),
                            "materials_accessed": materials_viewed
                        }
                    },
                    "overall_stats": {
                        "total_topics": 1,
                        "completed_topics": 0,
                        "in_progress_topics": 1,
                        "not_started_topics": 0,
                        "total_study_time_minutes": duration_minutes,
                        "current_streak_days": 1,
                        "longest_streak_days": 1
                    },
                    "last_updated": datetime.now()
                }
                
                self.db.collection("learning_progress").add(progress_data)
        
        except Exception as e:
            logger.error(f"Error updating topic progress: {e}")
    
    def _check_and_award_achievements(
        self,
        student_id: str,
        progress_data: Dict[str, Any],
        topic_id: str,
        topic_data: Dict[str, Any]
    ):
        """
        Check and award achievements based on progress.
        
        Args:
            student_id: ID of the student
            progress_data: Progress data dictionary
            topic_id: ID of the topic
            topic_data: Topic data dictionary
        """
        try:
            # Get current achievements
            achievements = progress_data.get("achievements", [])
            
            # Check for topic completion achievement
            if topic_data.get("completion_percentage", 0) >= 100:
                completed_topics = progress_data.get("overall_stats", {}).get("completed_topics", 0)
                
                # Check for milestone achievements
                if completed_topics == 5 and "first_5_topics" not in achievements:
                    achievements.append("first_5_topics")
                    logger.info(f"Awarded first_5_topics achievement to {student_id}")
                
                elif completed_topics == 10 and "first_10_topics" not in achievements:
                    achievements.append("first_10_topics")
                    logger.info(f"Awarded first_10_topics achievement to {student_id}")
                
                # Check for subject completion
                subject = topic_data.get("subject", "Unknown")
                subject_topics = [
                    t for t in progress_data.get("topics", {}).values()
                    if t.get("subject") == subject and t.get("completion_percentage", 0) >= 100
                ]
                
                if len(subject_topics) >= 5 and f"all_{subject.lower()}_topics" not in achievements:
                    achievements.append(f"all_{subject.lower()}_topics")
                    logger.info(f"Awarded all_{subject.lower()}_topics achievement to {student_id}")
            
            # Check for streak achievement
            current_streak = progress_data.get("overall_stats", {}).get("current_streak_days", 0)
            if current_streak >= 7 and "week_streak" not in achievements:
                achievements.append("week_streak")
                logger.info(f"Awarded week_streak achievement to {student_id}")
            
            # Update achievements in progress data
            progress_data["achievements"] = achievements
            
            # Update the progress document
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id)
            
            docs = query.limit(1).stream()
            for doc in docs:
                doc.reference.update({"achievements": achievements})
                break
        
        except Exception as e:
            logger.error(f"Error checking achievements: {e}")


# Singleton instance
_progress_tracker_service_instance: Optional[ProgressTrackerService] = None


def get_progress_tracker_service() -> ProgressTrackerService:
    """
    Get or create singleton ProgressTrackerService instance.
    
    Returns:
        ProgressTrackerService instance
    
    Example:
        >>> service = get_progress_tracker_service()
        >>> session_id = service.start_learning_session("student_123", "T02")
    """
    global _progress_tracker_service_instance
    
    if _progress_tracker_service_instance is None:
        logger.info("Creating new ProgressTrackerService singleton instance")
        _progress_tracker_service_instance = ProgressTrackerService()
    
    return _progress_tracker_service_instance


# Module initialization
logger.info("Progress tracker service module loaded")