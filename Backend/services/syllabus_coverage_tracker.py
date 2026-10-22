"""
Syllabus Coverage Tracker Service

This service tracks which syllabus topics have been tested for each student,
enabling comprehensive syllabus coverage analysis and personalized test generation.

Features:
- Track topic coverage per student
- Calculate coverage percentages
- Identify untested topics
- Identify weak topics (low performance)
- Progressive coverage recommendations
- Coverage analytics and reporting

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from collections import defaultdict

from pydantic import BaseModel, Field
from utils.firebase_config import get_firestore_client
from services.syllabus_service import load_syllabus, get_topics

# Configure logging
logger = logging.getLogger(__name__)


class TopicCoverage(BaseModel):
    """Coverage data for a single topic."""
    topic_id: str
    topic_name: str
    subject: str
    chapter: str
    times_tested: int = 0
    total_questions: int = 0
    correct_answers: int = 0
    incorrect_answers: int = 0
    first_tested: Optional[datetime] = None
    last_tested: Optional[datetime] = None
    average_score: float = 0.0
    
    def update_from_test(self, correct: int, total: int):
        """Update coverage from test results."""
        self.times_tested += 1
        self.total_questions += total
        self.correct_answers += correct
        self.incorrect_answers += (total - correct)
        self.last_tested = datetime.utcnow()
        
        if self.first_tested is None:
            self.first_tested = datetime.utcnow()
        
        # Calculate average score
        if self.total_questions > 0:
            self.average_score = (self.correct_answers / self.total_questions) * 100


class StudentCoverage(BaseModel):
    """Complete coverage data for a student."""
    student_id: str
    exam_type: str
    overall_coverage_percentage: float = 0.0
    total_topics: int = 0
    covered_topics: int = 0
    untested_topics: int = 0
    weak_topics: int = 0
    
    subject_coverage: Dict[str, float] = Field(default_factory=dict)
    chapter_coverage: Dict[str, float] = Field(default_factory=dict)
    topic_coverage: Dict[str, TopicCoverage] = Field(default_factory=dict)
    
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class SyllabusCoverageTracker:
    """
    Service for tracking and analyzing syllabus coverage.
    
    This service maintains coverage data in Firestore and provides
    methods for coverage analysis, recommendations, and reporting.
    
    Attributes:
        firestore_client: Firestore database client
        weak_topic_threshold: Score threshold for weak topics (default: 60%)
    """
    
    def __init__(
        self,
        firestore_client=None,
        weak_topic_threshold: float = 60.0
    ):
        """
        Initialize SyllabusCoverageTracker.
        
        Args:
            firestore_client: Optional Firestore client
            weak_topic_threshold: Percentage below which topic is considered weak
        """
        logger.info("Initializing SyllabusCoverageTracker")
        
        self.firestore_client = firestore_client or get_firestore_client()
        self.weak_topic_threshold = weak_topic_threshold
        
        logger.info(f"Coverage tracker initialized (weak threshold: {weak_topic_threshold}%)")
    
    def track_test_coverage(
        self,
        student_id: str,
        exam_type: str,
        test_id: str,
        questions: List[Dict],
        answers: Dict[int, str],
        correct_answers: Dict[int, bool]
    ):
        """
        Track syllabus coverage from a completed test.
        
        Args:
            student_id: Student identifier
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            test_id: Test identifier
            questions: List of question dictionaries with topic info
            answers: Student's answers {question_number: answer}
            correct_answers: Correctness map {question_number: is_correct}
        """
        logger.info(
            f"Tracking coverage: student={student_id}, exam={exam_type}, "
            f"test={test_id}, questions={len(questions)}"
        )
        
        try:
            # Get current coverage
            coverage = self.get_student_coverage(student_id, exam_type)
            
            # Group questions by topic
            topic_results = defaultdict(lambda: {"correct": 0, "total": 0})
            
            for i, question in enumerate(questions, 1):
                topic_id = question.get("topic_id", "unknown")
                is_correct = correct_answers.get(i, False)
                
                topic_results[topic_id]["total"] += 1
                if is_correct:
                    topic_results[topic_id]["correct"] += 1
            
            # Update coverage for each topic
            for topic_id, results in topic_results.items():
                if topic_id not in coverage.topic_coverage:
                    # Find topic details
                    topic_info = self._get_topic_info(exam_type, topic_id)
                    
                    coverage.topic_coverage[topic_id] = TopicCoverage(
                        topic_id=topic_id,
                        topic_name=topic_info.get("topic_name", "Unknown"),
                        subject=topic_info.get("subject", "Unknown"),
                        chapter=topic_info.get("chapter", "Unknown")
                    )
                
                # Update topic coverage
                coverage.topic_coverage[topic_id].update_from_test(
                    correct=results["correct"],
                    total=results["total"]
                )
            
            # Recalculate overall coverage
            coverage = self._recalculate_coverage(coverage, exam_type)
            
            # Save to Firestore
            self._save_coverage(coverage)
            
            logger.info(
                f"Coverage updated: {coverage.covered_topics}/{coverage.total_topics} "
                f"topics ({coverage.overall_coverage_percentage:.1f}%)"
            )
            
        except Exception as e:
            logger.error(f"Failed to track coverage: {e}")
            logger.exception("Full traceback:")
            raise
    
    def get_student_coverage(
        self,
        student_id: str,
        exam_type: str
    ) -> StudentCoverage:
        """
        Get complete coverage data for a student.
        
        Args:
            student_id: Student identifier
            exam_type: Exam type
        
        Returns:
            StudentCoverage object with all coverage data
        """
        try:
            # Try to load from Firestore
            doc_ref = self.firestore_client.collection("syllabus_coverage").document(
                f"{student_id}_{exam_type}"
            )
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Convert topic_coverage dict back to TopicCoverage objects
                if "topic_coverage" in data:
                    data["topic_coverage"] = {
                        k: TopicCoverage(**v) for k, v in data["topic_coverage"].items()
                    }
                return StudentCoverage(**data)
            
            # Create new coverage
            logger.info(f"Creating new coverage for {student_id} - {exam_type}")
            return self._create_new_coverage(student_id, exam_type)
            
        except Exception as e:
            logger.error(f"Failed to get coverage: {e}")
            # Return empty coverage as fallback
            return self._create_new_coverage(student_id, exam_type)
    
    def get_untested_topics(
        self,
        student_id: str,
        exam_type: str,
        subject: Optional[str] = None
    ) -> List[Dict]:
        """
        Get topics that haven't been tested yet.
        
        Args:
            student_id: Student identifier
            exam_type: Exam type
            subject: Optional subject filter
        
        Returns:
            List of untested topic dictionaries
        """
        coverage = self.get_student_coverage(student_id, exam_type)
        
        # Get all topics for exam
        all_topics = self._get_all_topics(exam_type, subject)
        
        # Filter untested
        untested = [
            topic for topic in all_topics
            if topic["topic_id"] not in coverage.topic_coverage
        ]
        
        logger.info(
            f"Found {len(untested)} untested topics for {student_id} - {exam_type}"
        )
        
        return untested
    
    def get_weak_topics(
        self,
        student_id: str,
        exam_type: str,
        subject: Optional[str] = None,
        min_questions: int = 3
    ) -> List[Dict]:
        """
        Get topics where student performed poorly.
        
        Args:
            student_id: Student identifier
            exam_type: Exam type
            subject: Optional subject filter
            min_questions: Minimum questions to consider (default: 3)
        
        Returns:
            List of weak topic dictionaries with performance data
        """
        coverage = self.get_student_coverage(student_id, exam_type)
        
        weak_topics = []
        
        for topic_id, topic_cov in coverage.topic_coverage.items():
            # Skip if not enough questions
            if topic_cov.total_questions < min_questions:
                continue
            
            # Skip if subject filter doesn't match
            if subject and topic_cov.subject != subject:
                continue
            
            # Check if weak
            if topic_cov.average_score < self.weak_topic_threshold:
                weak_topics.append({
                    "topic_id": topic_id,
                    "topic_name": topic_cov.topic_name,
                    "subject": topic_cov.subject,
                    "chapter": topic_cov.chapter,
                    "average_score": topic_cov.average_score,
                    "total_questions": topic_cov.total_questions,
                    "times_tested": topic_cov.times_tested
                })
        
        # Sort by score (weakest first)
        weak_topics.sort(key=lambda x: x["average_score"])
        
        logger.info(
            f"Found {len(weak_topics)} weak topics for {student_id} - {exam_type}"
        )
        
        return weak_topics
    
    def get_coverage_recommendations(
        self,
        student_id: str,
        exam_type: str,
        num_topics: int = 10
    ) -> Dict[str, List[Dict]]:
        """
        Get recommended topics for next test.
        
        Prioritizes:
        1. Untested topics (40%)
        2. Weak topics (40%)
        3. Revision topics (20%)
        
        Args:
            student_id: Student identifier
            exam_type: Exam type
            num_topics: Number of topics to recommend
        
        Returns:
            Dictionary with categorized recommendations
        """
        untested = self.get_untested_topics(student_id, exam_type)
        weak = self.get_weak_topics(student_id, exam_type)
        coverage = self.get_student_coverage(student_id, exam_type)
        
        # Calculate distribution
        num_untested = min(len(untested), int(num_topics * 0.4))
        num_weak = min(len(weak), int(num_topics * 0.4))
        num_revision = num_topics - num_untested - num_weak
        
        # Get revision topics (tested but not recently)
        revision = self._get_revision_topics(coverage, num_revision)
        
        recommendations = {
            "untested": untested[:num_untested],
            "weak": weak[:num_weak],
            "revision": revision,
            "total": num_untested + num_weak + len(revision)
        }
        
        logger.info(
            f"Recommendations for {student_id}: "
            f"{num_untested} untested, {num_weak} weak, {len(revision)} revision"
        )
        
        return recommendations
    
    def _create_new_coverage(
        self,
        student_id: str,
        exam_type: str
    ) -> StudentCoverage:
        """Create new coverage object for student."""
        # Get total topics
        all_topics = self._get_all_topics(exam_type)
        
        coverage = StudentCoverage(
            student_id=student_id,
            exam_type=exam_type,
            total_topics=len(all_topics),
            untested_topics=len(all_topics)
        )
        
        return coverage
    
    def _recalculate_coverage(
        self,
        coverage: StudentCoverage,
        exam_type: str
    ) -> StudentCoverage:
        """Recalculate all coverage percentages."""
        # Get all topics
        all_topics = self._get_all_topics(exam_type)
        coverage.total_topics = len(all_topics)
        
        # Count covered topics
        coverage.covered_topics = len(coverage.topic_coverage)
        coverage.untested_topics = coverage.total_topics - coverage.covered_topics
        
        # Count weak topics
        coverage.weak_topics = sum(
            1 for tc in coverage.topic_coverage.values()
            if tc.average_score < self.weak_topic_threshold
        )
        
        # Calculate overall percentage
        if coverage.total_topics > 0:
            coverage.overall_coverage_percentage = (
                coverage.covered_topics / coverage.total_topics
            ) * 100
        
        # Calculate subject-wise coverage
        subjects = set(t["subject"] for t in all_topics)
        for subject in subjects:
            subject_topics = [t for t in all_topics if t["subject"] == subject]
            covered_in_subject = sum(
                1 for tc in coverage.topic_coverage.values()
                if tc.subject == subject
            )
            
            if len(subject_topics) > 0:
                coverage.subject_coverage[subject] = (
                    covered_in_subject / len(subject_topics)
                ) * 100
        
        # Calculate chapter-wise coverage
        chapters = set((t["subject"], t["chapter"]) for t in all_topics)
        for subject, chapter in chapters:
            chapter_topics = [
                t for t in all_topics
                if t["subject"] == subject and t["chapter"] == chapter
            ]
            covered_in_chapter = sum(
                1 for tc in coverage.topic_coverage.values()
                if tc.subject == subject and tc.chapter == chapter
            )
            
            chapter_key = f"{subject}_{chapter}"
            if len(chapter_topics) > 0:
                coverage.chapter_coverage[chapter_key] = (
                    covered_in_chapter / len(chapter_topics)
                ) * 100
        
        coverage.last_updated = datetime.utcnow()
        
        return coverage
    
    def _save_coverage(self, coverage: StudentCoverage):
        """Save coverage to Firestore."""
        try:
            doc_ref = self.firestore_client.collection("syllabus_coverage").document(
                f"{coverage.student_id}_{coverage.exam_type}"
            )
            
            # Convert to dict
            data = coverage.dict()
            
            # Convert TopicCoverage objects to dicts
            if "topic_coverage" in data:
                data["topic_coverage"] = {
                    k: v.dict() if isinstance(v, TopicCoverage) else v
                    for k, v in data["topic_coverage"].items()
                }
            
            doc_ref.set(data)
            logger.info(f"Coverage saved for {coverage.student_id}")
            
        except Exception as e:
            logger.error(f"Failed to save coverage: {e}")
            raise
    
    def _get_all_topics(
        self,
        exam_type: str,
        subject: Optional[str] = None
    ) -> List[Dict]:
        """Get all topics for exam type."""
        # Determine subjects
        if "JEE" in exam_type:
            subjects = ["Physics", "Chemistry", "Mathematics"]
        elif exam_type == "NEET":
            subjects = ["Physics", "Chemistry", "Biology"]
        else:
            subjects = []
        
        # Filter by subject if provided
        if subject:
            subjects = [s for s in subjects if s == subject]
        
        # Get topics from syllabus service
        all_topics = []
        for subj in subjects:
            try:
                topics = get_topics(exam_type, subj, use_cache=True)
                all_topics.extend(topics)
            except Exception as e:
                logger.warning(f"Could not load topics for {exam_type} - {subj}: {e}")
        
        return all_topics
    
    def _get_topic_info(self, exam_type: str, topic_id: str) -> Dict:
        """Get topic information from syllabus."""
        all_topics = self._get_all_topics(exam_type)
        
        for topic in all_topics:
            if topic.get("topic_id") == topic_id:
                return topic
        
        return {
            "topic_id": topic_id,
            "topic_name": "Unknown",
            "subject": "Unknown",
            "chapter": "Unknown"
        }
    
    def _get_revision_topics(
        self,
        coverage: StudentCoverage,
        num_topics: int
    ) -> List[Dict]:
        """Get topics that need revision (tested but not recently)."""
        from datetime import timedelta
        
        revision_topics = []
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        
        for topic_id, topic_cov in coverage.topic_coverage.items():
            # Skip weak topics (handled separately)
            if topic_cov.average_score < self.weak_topic_threshold:
                continue
            
            # Check if needs revision (not tested recently)
            if topic_cov.last_tested and topic_cov.last_tested < cutoff_date:
                revision_topics.append({
                    "topic_id": topic_id,
                    "topic_name": topic_cov.topic_name,
                    "subject": topic_cov.subject,
                    "chapter": topic_cov.chapter,
                    "last_tested": topic_cov.last_tested.isoformat(),
                    "average_score": topic_cov.average_score
                })
        
        # Sort by last tested (oldest first)
        revision_topics.sort(key=lambda x: x["last_tested"])
        
        return revision_topics[:num_topics]


# Module initialization
logger.info("Syllabus coverage tracker module loaded")
