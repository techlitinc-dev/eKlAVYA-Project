"""
Parent Dashboard Service

This service provides dashboard and reporting functionality for parents
to monitor their child's progress and performance.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any

from models.parent_models import (
    ChildDashboard,
    WeeklyReport,
    NotificationSettings,
    Goal,
    GoalRequest,
    GoalUpdateRequest
)
from utils.firebase_config import get_firestore_client

logger = logging.getLogger(__name__)


class ParentDashboardService:
    """Service for parent dashboard and reporting."""
    
    def __init__(self):
        """Initialize the service."""
        self.db = get_firestore_client()
    
    def get_child_dashboard(self, child_id: str) -> ChildDashboard:
        """
        Get dashboard overview for a child.
        
        Args:
            child_id: Child identifier
        
        Returns:
            ChildDashboard with current status
        """
        logger.info(f"Getting dashboard for child: {child_id}")
        
        try:
            # Get child profile
            child_doc = self.db.collection("children").document(child_id).get()
            if not child_doc.exists:
                raise ValueError(f"Child not found: {child_id}")
            
            child_data = child_doc.to_dict()
            
            # Get active schedule
            schedule_query = self.db.collection("schedules")\
                .where("student_id", "==", child_id)\
                .where("status", "==", "active")\
                .limit(1)\
                .stream()
            
            schedule_data = None
            for doc in schedule_query:
                schedule_data = doc.to_dict()
                break
            
            # Get recent analytics
            analytics_query = self.db.collection("analytics")\
                .where("student_id", "==", child_id)\
                .order_by("created_at", direction="DESCENDING")\
                .limit(1)\
                .stream()
            
            analytics_data = None
            for doc in analytics_query:
                analytics_data = doc.to_dict()
                break
            
            # Get progress data
            progress_query = self.db.collection("progress")\
                .where("student_id", "==", child_id)\
                .order_by("date", direction="DESCENDING")\
                .limit(7)\
                .stream()
            
            progress_entries = [doc.to_dict() for doc in progress_query]
            
            # Calculate metrics
            current_streak = self._calculate_streak(progress_entries)
            hours_today = self._calculate_hours_today(progress_entries)
            hours_week = self._calculate_hours_week(progress_entries)
            
            # Determine schedule status
            schedule_status = "on_track"
            days_until_exam = 0
            overall_progress = 0.0
            
            if schedule_data:
                overall_progress = schedule_data.get("completion_percentage", 0.0)
                exam_date = schedule_data.get("exam_date")
                if isinstance(exam_date, str):
                    exam_date = datetime.fromisoformat(exam_date).date()
                days_until_exam = (exam_date - date.today()).days
                
                # Determine if on track
                expected_progress = (1 - (days_until_exam / schedule_data.get("total_days", 1))) * 100
                if overall_progress < expected_progress - 10:
                    schedule_status = "behind"
                elif overall_progress > expected_progress + 10:
                    schedule_status = "ahead"
            
            # Get weak areas from analytics
            weak_areas = []
            if analytics_data:
                weak_topics = analytics_data.get("weak_topics", [])[:3]
                for topic in weak_topics:
                    weak_areas.append({
                        "subject": topic.get("subject", "Unknown"),
                        "topic": topic.get("topic", "Unknown"),
                        "accuracy": f"{topic.get('accuracy', 0):.0f}%"
                    })
            
            # Get upcoming tasks from schedule
            upcoming_tasks = []
            if schedule_data and "days" in schedule_data:
                today = date.today()
                for day in schedule_data["days"][:5]:  # Next 5 days
                    day_date = day.get("schedule_date")
                    if isinstance(day_date, str):
                        day_date = datetime.fromisoformat(day_date).date()
                    
                    if day_date >= today:
                        for topic in day.get("topics", [])[:2]:  # First 2 topics
                            upcoming_tasks.append({
                                "date": day_date.isoformat(),
                                "topic": f"{topic.get('subject')} - {topic.get('topic')}",
                                "duration": f"{topic.get('estimated_hours', 0)} hours"
                            })
            
            # Get recent test score
            recent_test_score = None
            if analytics_data:
                recent_test_score = analytics_data.get("percentage", None)
            
            # Get last active time
            last_active = datetime.utcnow()
            if progress_entries:
                last_active = progress_entries[0].get("timestamp", datetime.utcnow())
                if isinstance(last_active, str):
                    last_active = datetime.fromisoformat(last_active)
            
            dashboard = ChildDashboard(
                child_id=child_id,
                child_name=child_data.get("name", "Unknown"),
                overall_progress=overall_progress,
                current_streak=current_streak,
                hours_studied_today=hours_today,
                hours_studied_week=hours_week,
                schedule_status=schedule_status,
                days_until_exam=days_until_exam,
                weak_areas=weak_areas,
                upcoming_tasks=upcoming_tasks,
                recent_test_score=recent_test_score,
                last_active=last_active
            )
            
            logger.info(f"Dashboard generated for child: {child_id}")
            return dashboard
            
        except Exception as e:
            logger.error(f"Error getting dashboard: {e}")
            raise
    
    def get_weekly_report(self, child_id: str, week_start: Optional[date] = None) -> WeeklyReport:
        """
        Get weekly progress report for a child.
        
        Args:
            child_id: Child identifier
            week_start: Week start date (defaults to current week)
        
        Returns:
            WeeklyReport with weekly metrics
        """
        logger.info(f"Getting weekly report for child: {child_id}")
        
        if week_start is None:
            # Get current week start (Monday)
            today = date.today()
            week_start = today - timedelta(days=today.weekday())
        
        week_end = week_start + timedelta(days=6)
        
        try:
            # Get progress entries for this week
            progress_query = self.db.collection("progress")\
                .where("student_id", "==", child_id)\
                .where("date", ">=", week_start.isoformat())\
                .where("date", "<=", week_end.isoformat())\
                .stream()
            
            progress_entries = [doc.to_dict() for doc in progress_query]
            
            # Get previous week for comparison
            prev_week_start = week_start - timedelta(days=7)
            prev_week_end = week_start - timedelta(days=1)
            
            prev_progress_query = self.db.collection("progress")\
                .where("student_id", "==", child_id)\
                .where("date", ">=", prev_week_start.isoformat())\
                .where("date", "<=", prev_week_end.isoformat())\
                .stream()
            
            prev_progress_entries = [doc.to_dict() for doc in prev_progress_query]
            
            # Calculate metrics
            total_hours = sum(entry.get("hours_studied", 0) for entry in progress_entries)
            previous_week_hours = sum(entry.get("hours_studied", 0) for entry in prev_progress_entries)
            
            topics_completed = sum(
                len(entry.get("topics_completed", [])) for entry in progress_entries
            )
            
            # Get tests taken this week
            tests_query = self.db.collection("test_submissions")\
                .where("student_id", "==", child_id)\
                .where("submission_date", ">=", week_start.isoformat())\
                .where("submission_date", "<=", week_end.isoformat())\
                .stream()
            
            test_submissions = [doc.to_dict() for doc in tests_query]
            tests_taken = len(test_submissions)
            
            average_test_score = None
            if test_submissions:
                scores = [test.get("percentage", 0) for test in test_submissions]
                average_test_score = sum(scores) / len(scores)
            
            # Calculate attendance rate
            days_with_activity = len(set(entry.get("date") for entry in progress_entries))
            attendance_rate = (days_with_activity / 7) * 100
            
            # Subject breakdown
            subject_breakdown = {}
            for entry in progress_entries:
                for topic in entry.get("topics_completed", []):
                    subject = topic.get("subject", "Unknown")
                    if subject not in subject_breakdown:
                        subject_breakdown[subject] = {"hours": 0.0, "score": 0.0}
                    subject_breakdown[subject]["hours"] += topic.get("hours", 0)
            
            # Add scores from tests
            for test in test_submissions:
                subject_scores = test.get("subject_scores", {})
                for subject, score in subject_scores.items():
                    if subject in subject_breakdown:
                        subject_breakdown[subject]["score"] = score
            
            # Achievements this week
            achievements = []
            if days_with_activity >= 7:
                achievements.append("Perfect attendance - 7 days!")
            if total_hours >= 35:
                achievements.append("Study champion - 35+ hours!")
            if topics_completed >= 10:
                achievements.append(f"Completed {topics_completed} topics")
            
            # Areas of concern
            areas_of_concern = []
            if attendance_rate < 70:
                areas_of_concern.append("Low study attendance")
            if average_test_score and average_test_score < 60:
                areas_of_concern.append("Test scores need improvement")
            if total_hours < previous_week_hours * 0.8:
                areas_of_concern.append("Study hours decreased significantly")
            
            report = WeeklyReport(
                child_id=child_id,
                week_start=week_start,
                week_end=week_end,
                total_hours_studied=total_hours,
                previous_week_hours=previous_week_hours,
                topics_completed=topics_completed,
                tests_taken=tests_taken,
                average_test_score=average_test_score,
                attendance_rate=attendance_rate,
                subject_breakdown=subject_breakdown,
                achievements=achievements,
                areas_of_concern=areas_of_concern
            )
            
            logger.info(f"Weekly report generated for child: {child_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error getting weekly report: {e}")
            raise
    
    def _calculate_streak(self, progress_entries: List[Dict]) -> int:
        """Calculate current study streak."""
        if not progress_entries:
            return 0
        
        # Sort by date descending
        sorted_entries = sorted(
            progress_entries,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        streak = 0
        expected_date = date.today()
        
        for entry in sorted_entries:
            entry_date = entry.get("date")
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date).date()
            
            if entry_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _calculate_hours_today(self, progress_entries: List[Dict]) -> float:
        """Calculate hours studied today."""
        today = date.today().isoformat()
        
        for entry in progress_entries:
            if entry.get("date") == today:
                return entry.get("hours_studied", 0.0)
        
        return 0.0
    
    def _calculate_hours_week(self, progress_entries: List[Dict]) -> float:
        """Calculate hours studied this week."""
        week_start = date.today() - timedelta(days=date.today().weekday())
        
        total_hours = 0.0
        for entry in progress_entries:
            entry_date = entry.get("date")
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date).date()
            
            if entry_date >= week_start:
                total_hours += entry.get("hours_studied", 0.0)
        
        return total_hours
    
    def get_notification_settings(self, parent_id: str) -> NotificationSettings:
        """Get notification settings for a parent."""
        logger.info(f"Getting notification settings for parent: {parent_id}")
        
        try:
            doc = self.db.collection("notification_settings").document(parent_id).get()
            
            if doc.exists:
                data = doc.to_dict()
                return NotificationSettings(**data)
            else:
                # Return default settings
                return NotificationSettings(parent_id=parent_id)
                
        except Exception as e:
            logger.error(f"Error getting notification settings: {e}")
            raise
    
    def update_notification_settings(
        self,
        parent_id: str,
        settings: NotificationSettings
    ) -> NotificationSettings:
        """Update notification settings for a parent."""
        logger.info(f"Updating notification settings for parent: {parent_id}")
        
        try:
            self.db.collection("notification_settings").document(parent_id).set(
                settings.model_dump()
            )
            
            logger.info(f"Notification settings updated for parent: {parent_id}")
            return settings
            
        except Exception as e:
            logger.error(f"Error updating notification settings: {e}")
            raise
    
    def create_goal(self, parent_id: str, request: GoalRequest) -> Goal:
        """Create a new goal for a child."""
        logger.info(f"Creating goal for child: {request.child_id}")
        
        try:
            goal_id = f"goal_{request.child_id}_{int(datetime.utcnow().timestamp())}"
            
            goal = Goal(
                goal_id=goal_id,
                child_id=request.child_id,
                goal_type=request.goal_type,
                target_value=request.target_value,
                current_value=0.0,
                deadline=request.deadline,
                status="active",
                created_at=datetime.utcnow()
            )
            
            self.db.collection("goals").document(goal_id).set(goal.model_dump())
            
            logger.info(f"Goal created: {goal_id}")
            return goal
            
        except Exception as e:
            logger.error(f"Error creating goal: {e}")
            raise
    
    def get_goals(self, child_id: str) -> List[Goal]:
        """Get all goals for a child."""
        logger.info(f"Getting goals for child: {child_id}")
        
        try:
            query = self.db.collection("goals")\
                .where("child_id", "==", child_id)\
                .order_by("created_at", direction="DESCENDING")\
                .stream()
            
            goals = []
            for doc in query:
                data = doc.to_dict()
                goals.append(Goal(**data))
            
            logger.info(f"Found {len(goals)} goals for child: {child_id}")
            return goals
            
        except Exception as e:
            logger.error(f"Error getting goals: {e}")
            raise
    
    def update_goal(
        self,
        goal_id: str,
        updates: GoalUpdateRequest
    ) -> Goal:
        """Update a goal."""
        logger.info(f"Updating goal: {goal_id}")
        
        try:
            doc_ref = self.db.collection("goals").document(goal_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                raise ValueError(f"Goal not found: {goal_id}")
            
            goal_data = doc.to_dict()
            
            # Apply updates
            update_dict = updates.model_dump(exclude_none=True)
            goal_data.update(update_dict)
            
            # If status changed to completed, set completion timestamp
            if updates.status == "completed" and goal_data.get("status") != "completed":
                goal_data["completed_at"] = datetime.utcnow()
            
            doc_ref.update(goal_data)
            
            logger.info(f"Goal updated: {goal_id}")
            return Goal(**goal_data)
            
        except Exception as e:
            logger.error(f"Error updating goal: {e}")
            raise
