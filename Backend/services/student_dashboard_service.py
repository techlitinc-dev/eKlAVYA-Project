"""
Student Dashboard Service

This service provides dashboard and learning functionality for students
including daily plans, practice modes, doubts, and bookmarks.

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import random

from models.student_models import (
    TodaysPlan,
    TopicResources,
    QuickPracticeRequest,
    QuickPracticeResponse,
    Doubt,
    DoubtRequest,
    DoubtExplanation,
    RevisionItem,
    PerformanceInsights,
    Bookmark,
    BookmarkRequest,
    PeerComparison
)
from utils.firebase_config import get_firestore_client
from services.gemini_service import GeminiService
from services.question_generator import QuestionGenerator

logger = logging.getLogger(__name__)


class StudentDashboardService:
    """Service for student dashboard and learning features."""
    
    def __init__(self):
        """Initialize the service."""
        self.db = get_firestore_client()
        self.gemini_service = GeminiService()
        self.question_generator = QuestionGenerator()
    
    def get_todays_plan(self, student_id: str) -> TodaysPlan:
        """
        Get today's study plan for a student.
        
        Args:
            student_id: Student identifier
        
        Returns:
            TodaysPlan with today's schedule
        """
        logger.info(f"Getting today's plan for student: {student_id}")
        
        try:
            today = date.today()
            
            # Get active schedule
            schedule_query = self.db.collection("schedules")\
                .where("student_id", "==", student_id)\
                .where("status", "==", "active")\
                .limit(1)\
                .stream()
            
            schedule_data = None
            for doc in schedule_query:
                schedule_data = doc.to_dict()
                break
            
            if not schedule_data:
                raise ValueError(f"No active schedule found for student: {student_id}")
            
            # Find today's schedule
            today_topics = []
            total_hours = 0.0
            
            for day in schedule_data.get("days", []):
                day_date = day.get("schedule_date")
                if isinstance(day_date, str):
                    day_date = datetime.fromisoformat(day_date).date()
                
                if day_date == today:
                    for topic in day.get("topics", []):
                        topic_info = {
                            "subject": topic.get("subject"),
                            "topic": topic.get("topic"),
                            "estimated_hours": topic.get("estimated_hours", 0),
                            "priority": topic.get("priority", "medium"),
                            "completed": topic.get("completed", False)
                        }
                        today_topics.append(topic_info)
                        total_hours += topic.get("estimated_hours", 0)
                    break
            
            # Get pending items from yesterday
            yesterday = today - timedelta(days=1)
            pending_items = []
            
            for day in schedule_data.get("days", []):
                day_date = day.get("schedule_date")
                if isinstance(day_date, str):
                    day_date = datetime.fromisoformat(day_date).date()
                
                if day_date == yesterday:
                    for topic in day.get("topics", []):
                        if not topic.get("completed", False):
                            pending_items.append({
                                "topic": f"{topic.get('subject')} - {topic.get('topic')}",
                                "reason": "incomplete"
                            })
            
            # Get current streak
            progress_query = self.db.collection("progress")\
                .where("student_id", "==", student_id)\
                .order_by("date", direction="DESCENDING")\
                .limit(30)\
                .stream()
            
            progress_entries = [doc.to_dict() for doc in progress_query]
            current_streak = self._calculate_streak(progress_entries)
            
            # Calculate today's completion
            completion_percentage = 0.0
            if today_topics:
                completed_count = sum(1 for t in today_topics if t.get("completed", False))
                completion_percentage = (completed_count / len(today_topics)) * 100
            
            # Generate motivational message
            motivational_message = self._generate_motivational_message(
                current_streak,
                completion_percentage
            )
            
            plan = TodaysPlan(
                student_id=student_id,
                date=today,
                topics=today_topics,
                total_estimated_hours=total_hours,
                pending_from_yesterday=pending_items,
                current_streak=current_streak,
                completion_percentage=completion_percentage,
                motivational_message=motivational_message
            )
            
            logger.info(f"Today's plan generated for student: {student_id}")
            return plan
            
        except Exception as e:
            logger.error(f"Error getting today's plan: {e}")
            raise
    
    def get_topic_resources(self, topic_id: str) -> TopicResources:
        """Get curated resources for a topic."""
        logger.info(f"Getting resources for topic: {topic_id}")
        
        try:
            # Get topic details
            topic_doc = self.db.collection("topics").document(topic_id).get()
            if not topic_doc.exists:
                raise ValueError(f"Topic not found: {topic_id}")
            
            topic_data = topic_doc.to_dict()
            topic_name = topic_data.get("topic_name", "Unknown")
            
            # Get curated resources (would be pre-populated in production)
            resources = TopicResources(
                topic_id=topic_id,
                topic_name=topic_name,
                videos=[
                    {
                        "title": f"{topic_name} - Complete Explanation",
                        "url": f"https://youtube.com/search?q={topic_name.replace(' ', '+')}+JEE",
                        "duration": "15:00"
                    }
                ],
                formula_sheets=[
                    {
                        "title": f"{topic_name} Formula Sheet",
                        "url": f"https://example.com/formulas/{topic_id}.pdf"
                    }
                ],
                revision_notes=[
                    {
                        "title": f"Quick Revision - {topic_name}",
                        "content": topic_data.get("description", "Key concepts...")
                    }
                ],
                reference_links=[
                    {
                        "title": "NCERT Reference",
                        "url": "https://ncert.nic.in/"
                    }
                ]
            )
            
            logger.info(f"Resources retrieved for topic: {topic_id}")
            return resources
            
        except Exception as e:
            logger.error(f"Error getting topic resources: {e}")
            raise
    
    def generate_quick_practice(self, request: QuickPracticeRequest) -> QuickPracticeResponse:
        """Generate quick practice session."""
        logger.info(f"Generating quick practice for student: {request.student_id}")
        
        try:
            # Determine number of questions based on duration
            questions_per_minute = 0.33  # ~3 minutes per question
            num_questions = max(3, int(request.duration_minutes * questions_per_minute))
            
            # Get topics based on focus
            topics = self._get_practice_topics(request)
            
            # Generate questions
            questions = []
            for topic in topics[:num_questions]:
                try:
                    topic_questions = self.question_generator.generate_questions(
                        topic=topic["topic"],
                        exam_type=topic.get("exam_type", "JEE_MAIN"),
                        difficulty=request.difficulty or "medium",
                        num_questions=1
                    )
                    if topic_questions:
                        questions.extend(topic_questions)
                except Exception as e:
                    logger.warning(f"Failed to generate question for topic {topic['topic']}: {e}")
            
            practice_id = f"practice_{request.student_id}_{int(datetime.utcnow().timestamp())}"
            
            # Store practice session
            self.db.collection("practice_sessions").document(practice_id).set({
                "practice_id": practice_id,
                "student_id": request.student_id,
                "questions": [q.model_dump() for q in questions],
                "focus": request.focus,
                "created_at": datetime.utcnow()
            })
            
            response = QuickPracticeResponse(
                practice_id=practice_id,
                questions=[q.model_dump() for q in questions],
                total_questions=len(questions),
                estimated_duration=request.duration_minutes,
                focus_area=request.focus
            )
            
            logger.info(f"Quick practice generated: {practice_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error generating quick practice: {e}")
            raise
    
    def create_doubt(self, request: DoubtRequest) -> Doubt:
        """Create a new doubt."""
        logger.info(f"Creating doubt for student: {request.student_id}")
        
        try:
            doubt_id = f"doubt_{request.student_id}_{int(datetime.utcnow().timestamp())}"
            
            doubt = Doubt(
                doubt_id=doubt_id,
                student_id=request.student_id,
                question_id=request.question_id,
                subject=request.subject,
                topic=request.topic,
                doubt_text=request.doubt_text,
                status="open",
                created_at=datetime.utcnow()
            )
            
            self.db.collection("doubts").document(doubt_id).set(doubt.model_dump())
            
            logger.info(f"Doubt created: {doubt_id}")
            return doubt
            
        except Exception as e:
            logger.error(f"Error creating doubt: {e}")
            raise
    
    def get_doubt_explanation(self, doubt_id: str) -> DoubtExplanation:
        """Get AI-generated explanation for a doubt."""
        logger.info(f"Getting explanation for doubt: {doubt_id}")
        
        try:
            # Get doubt details
            doubt_doc = self.db.collection("doubts").document(doubt_id).get()
            if not doubt_doc.exists:
                raise ValueError(f"Doubt not found: {doubt_id}")
            
            doubt_data = doubt_doc.to_dict()
            
            # Generate explanation using Gemini
            prompt = f"""You are an expert tutor for {doubt_data['subject']}.

Topic: {doubt_data['topic']}
Student's Question: {doubt_data['doubt_text']}

Provide a detailed explanation that:
1. Explains the concept clearly
2. Lists key concepts involved
3. Provides 2-3 examples
4. Suggests related topics to study

Format your response as JSON:
{{
    "explanation": "detailed explanation here",
    "key_concepts": ["concept1", "concept2"],
    "examples": ["example1", "example2"],
    "related_topics": ["topic1", "topic2"]
}}"""
            
            response = self.gemini_service.client.generate_content(prompt)
            
            # Parse response (simplified - would need proper JSON parsing)
            explanation = DoubtExplanation(
                doubt_id=doubt_id,
                explanation=response[:500] if len(response) > 500 else response,
                key_concepts=[doubt_data['topic']],
                examples=["Example explanation would be generated here"],
                similar_questions=[],
                resources=[
                    {
                        "title": f"Learn more about {doubt_data['topic']}",
                        "url": f"https://example.com/topic/{doubt_data['topic']}"
                    }
                ]
            )
            
            # Update doubt status
            self.db.collection("doubts").document(doubt_id).update({
                "status": "explained"
            })
            
            logger.info(f"Explanation generated for doubt: {doubt_id}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error getting doubt explanation: {e}")
            raise
    
    def get_revision_due(self, student_id: str) -> List[RevisionItem]:
        """Get topics due for revision."""
        logger.info(f"Getting revision items for student: {student_id}")
        
        try:
            # Get completed topics
            progress_query = self.db.collection("progress")\
                .where("student_id", "==", student_id)\
                .order_by("date", direction="DESCENDING")\
                .limit(100)\
                .stream()
            
            completed_topics = {}
            for doc in progress_query:
                data = doc.to_dict()
                for topic in data.get("topics_completed", []):
                    topic_id = topic.get("topic_id")
                    if topic_id and topic_id not in completed_topics:
                        completed_topics[topic_id] = {
                            "topic_name": topic.get("topic"),
                            "subject": topic.get("subject"),
                            "last_studied": data.get("date"),
                            "estimated_hours": topic.get("hours", 1.0)
                        }
            
            # Calculate revision due dates (spaced repetition)
            revision_items = []
            today = date.today()
            
            for topic_id, topic_data in completed_topics.items():
                last_studied = topic_data["last_studied"]
                if isinstance(last_studied, str):
                    last_studied = datetime.fromisoformat(last_studied).date()
                
                days_since = (today - last_studied).days
                
                # Spaced repetition intervals: 1, 3, 7, 14, 30 days
                if days_since in [1, 3, 7, 14, 30]:
                    priority = "high" if days_since >= 14 else "medium" if days_since >= 7 else "low"
                    
                    revision_items.append(RevisionItem(
                        topic_id=topic_id,
                        topic_name=topic_data["topic_name"],
                        subject=topic_data["subject"],
                        last_studied=last_studied,
                        due_date=today,
                        priority=priority,
                        estimated_time=topic_data["estimated_hours"] * 0.5  # Revision takes less time
                    ))
            
            # Sort by priority
            priority_order = {"high": 0, "medium": 1, "low": 2}
            revision_items.sort(key=lambda x: priority_order[x.priority])
            
            logger.info(f"Found {len(revision_items)} revision items for student: {student_id}")
            return revision_items
            
        except Exception as e:
            logger.error(f"Error getting revision items: {e}")
            raise
    
    def create_bookmark(self, request: BookmarkRequest) -> Bookmark:
        """Create a bookmark."""
        logger.info(f"Creating bookmark for student: {request.student_id}")
        
        try:
            bookmark_id = f"bookmark_{request.student_id}_{int(datetime.utcnow().timestamp())}"
            
            bookmark = Bookmark(
                bookmark_id=bookmark_id,
                student_id=request.student_id,
                item_type=request.item_type,
                item_id=request.item_id,
                title=request.title,
                subject=request.subject,
                tags=request.tags,
                notes=request.notes,
                created_at=datetime.utcnow()
            )
            
            self.db.collection("bookmarks").document(bookmark_id).set(bookmark.model_dump())
            
            logger.info(f"Bookmark created: {bookmark_id}")
            return bookmark
            
        except Exception as e:
            logger.error(f"Error creating bookmark: {e}")
            raise
    
    def get_bookmarks(self, student_id: str) -> List[Bookmark]:
        """Get all bookmarks for a student."""
        logger.info(f"Getting bookmarks for student: {student_id}")
        
        try:
            query = self.db.collection("bookmarks")\
                .where("student_id", "==", student_id)\
                .order_by("created_at", direction="DESCENDING")\
                .stream()
            
            bookmarks = []
            for doc in query:
                data = doc.to_dict()
                bookmarks.append(Bookmark(**data))
            
            logger.info(f"Found {len(bookmarks)} bookmarks for student: {student_id}")
            return bookmarks
            
        except Exception as e:
            logger.error(f"Error getting bookmarks: {e}")
            raise
    
    def _calculate_streak(self, progress_entries: List[Dict]) -> int:
        """Calculate current study streak."""
        if not progress_entries:
            return 0
        
        streak = 0
        expected_date = date.today()
        
        for entry in progress_entries:
            entry_date = entry.get("date")
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date).date()
            
            if entry_date == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
        
        return streak
    
    def _generate_motivational_message(self, streak: int, completion: float) -> str:
        """Generate personalized motivational message."""
        messages = []
        
        if streak >= 7:
            messages.append(f"🔥 Amazing {streak}-day streak! Keep the momentum going!")
        elif streak >= 3:
            messages.append(f"Great job on your {streak}-day streak!")
        else:
            messages.append("Let's build a study streak today!")
        
        if completion >= 80:
            messages.append("You're crushing it today! 💪")
        elif completion >= 50:
            messages.append("Good progress! Keep going!")
        else:
            messages.append("Let's make today count!")
        
        return " ".join(messages)
    
    def _get_practice_topics(self, request: QuickPracticeRequest) -> List[Dict]:
        """Get topics for practice based on focus."""
        topics = []
        
        if request.focus == "weak_topics":
            # Get weak topics from analytics
            analytics_query = self.db.collection("analytics")\
                .where("student_id", "==", request.student_id)\
                .order_by("created_at", direction="DESCENDING")\
                .limit(1)\
                .stream()
            
            for doc in analytics_query:
                analytics_data = doc.to_dict()
                weak_topics = analytics_data.get("weak_topics", [])[:5]
                topics = [
                    {
                        "topic": t.get("topic"),
                        "subject": t.get("subject"),
                        "exam_type": analytics_data.get("exam_type", "JEE_MAIN")
                    }
                    for t in weak_topics
                ]
        
        elif request.focus == "specific_topic" and request.specific_topic:
            topics = [{
                "topic": request.specific_topic,
                "subject": request.subject or "Physics",
                "exam_type": "JEE_MAIN"
            }]
        
        else:
            # Random topics from syllabus
            topics = [
                {"topic": "Thermodynamics", "subject": "Physics", "exam_type": "JEE_MAIN"},
                {"topic": "Calculus", "subject": "Mathematics", "exam_type": "JEE_MAIN"},
                {"topic": "Organic Chemistry", "subject": "Chemistry", "exam_type": "JEE_MAIN"}
            ]
        
        return topics
