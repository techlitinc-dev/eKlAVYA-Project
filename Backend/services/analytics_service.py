"""
Analytics Service - Main Orchestration for Mentor AI Platform.

This service orchestrates the complete analytics pipeline, coordinating:
- Score calculation
- Performance analysis
- AI-powered insights generation
- Report assembly
- Firestore storage and retrieval

Features:
- Complete pipeline orchestration
- Progress tracking for long operations
- Request caching for performance
- Comprehensive error handling
- Retry logic for AI operations
- Execution time logging
- Firestore integration

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.analytics_service import AnalyticsService
    >>> 
    >>> service = AnalyticsService()
    >>> 
    >>> # Generate analytics
    >>> analytics_id = service.generate_analytics(
    ...     test_id="test_123",
    ...     student_id="student_456",
    ...     answers={1: "B", 2: "A", 3: "42"}
    ... )
    >>> 
    >>> # Retrieve analytics
    >>> report = service.get_analytics(analytics_id)
"""

import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from collections import OrderedDict

from google.cloud import firestore
from google.cloud.firestore_v1 import FieldFilter

from models.diagnostic_test_models import Question, DiagnosticTest
from models.score_models import TestScore
from models.performance_models import PerformanceAnalysis
from utils.analytics_parser import AnalyticsInsights
from services.score_calculator import ScoreCalculator
from services.performance_analyzer import PerformanceAnalyzer
from services.gemini_analytics_service import (
    GeminiAnalyticsService,
    GeminiAnalyticsError,
    AnalyticsTimeoutError
)
from services.analytics_report_builder import (
    AnalyticsReportBuilder,
    AnalyticsReport
)
from utils import build_analytics_context

# Configure logging
logger = logging.getLogger(__name__)


class AnalyticsServiceError(Exception):
    """Base exception for analytics service errors."""
    pass


class PipelineStepError(AnalyticsServiceError):
    """Exception raised when a pipeline step fails."""
    pass


class AnalyticsNotFoundError(AnalyticsServiceError):
    """Exception raised when analytics not found."""
    pass


def log_step_time(step_name: str):
    """Decorator to log execution time of pipeline steps."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                logger.info(f"Starting step: {step_name}")
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                logger.info(f"Completed step: {step_name} ({elapsed_time:.2f}s)")
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                logger.error(f"Failed step: {step_name} ({elapsed_time:.2f}s) - {str(e)}")
                raise
        return wrapper
    return decorator


class LRUCache:
    """Simple LRU cache for analytics results."""
    
    def __init__(self, capacity: int = 100):
        """
        Initialize LRU cache.
        
        Args:
            capacity: Maximum number of items to cache
        """
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        if key not in self.cache:
            return None
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: Any):
        """Put item in cache."""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            # Remove least recently used
            self.cache.popitem(last=False)
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()


class ProgressTracker:
    """Track progress of analytics generation."""
    
    def __init__(self, total_steps: int = 7):
        """
        Initialize progress tracker.
        
        Args:
            total_steps: Total number of pipeline steps
        """
        self.total_steps = total_steps
        self.current_step = 0
        self.step_names = []
        self.start_time = None
        self.step_times = {}
    
    def start(self):
        """Start tracking."""
        self.start_time = time.time()
        self.current_step = 0
        self.step_names = []
        self.step_times = {}
    
    def update(self, step_name: str):
        """Update progress."""
        if self.current_step > 0:
            # Record time for previous step
            elapsed = time.time() - self.start_time
            self.step_times[self.step_names[-1]] = elapsed
        
        self.current_step += 1
        self.step_names.append(step_name)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress."""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "percentage": (self.current_step / self.total_steps) * 100,
            "current_step_name": self.step_names[-1] if self.step_names else None,
            "elapsed_time": time.time() - self.start_time if self.start_time else 0
        }
    
    def finish(self):
        """Finish tracking."""
        if self.step_names:
            elapsed = time.time() - self.start_time
            self.step_times[self.step_names[-1]] = elapsed


class AnalyticsService:
    """
    Main analytics orchestration service.
    
    Coordinates the complete analytics pipeline from score calculation
    to AI-powered insights generation and report assembly.
    
    Attributes:
        db: Firestore client
        score_calculator: Score calculation service
        performance_analyzer: Performance analysis service
        gemini_service: AI insights generation service
        report_builder: Report assembly service
        context_builder: Context building utility
        cache: LRU cache for results
    
    Example:
        >>> service = AnalyticsService()
        >>> analytics_id = service.generate_analytics(
        ...     test_id="test_123",
        ...     student_id="student_456",
        ...     answers={1: "B", 2: "A"}
        ... )
    """
    
    def __init__(
        self,
        db: Optional[firestore.Client] = None,
        enable_cache: bool = True,
        cache_capacity: int = 100,
        gemini_max_retries: int = 3
    ):
        """
        Initialize Analytics Service.
        
        Args:
            db: Firestore client (creates new if None)
            enable_cache: Enable result caching
            cache_capacity: Maximum cache size
            gemini_max_retries: Maximum retries for Gemini API
        """
        logger.info("Initializing AnalyticsService")
        
        # Initialize Firestore
        self.db = db if db else firestore.Client()
        
        # Initialize services
        self.score_calculator = ScoreCalculator()
        self.performance_analyzer = PerformanceAnalyzer()
        self.gemini_service = GeminiAnalyticsService()
        self.report_builder = AnalyticsReportBuilder()
        # Note: Using build_analytics_context function directly instead of class
        # self.context_builder = AnalyticsContextBuilder(max_tokens=3000)
        
        # Configuration
        self.enable_cache = enable_cache
        self.gemini_max_retries = gemini_max_retries
        
        # Cache
        self.cache = LRUCache(capacity=cache_capacity) if enable_cache else None
        
        # Collections
        self.tests_collection = "diagnostic_tests"
        self.analytics_collection = "analytics_reports"
        
        logger.info(
            f"AnalyticsService initialized (cache={enable_cache}, "
            f"gemini_retries={gemini_max_retries})"
        )
    
    def generate_analytics(
        self,
        test_id: str,
        student_id: str,
        answers: Dict[int, str],
        test_metadata: Optional[Dict[str, Any]] = None,
        include_ai_insights: bool = True,
        use_cache: bool = True
    ) -> str:
        """
        Generate complete analytics report through pipeline.
        
        Pipeline Steps:
        1. Retrieve test questions from Firestore
        2. Calculate scores using ScoreCalculator
        3. Analyze performance using PerformanceAnalyzer
        4. Build context using AnalyticsContextBuilder
        5. Generate AI insights using GeminiAnalyticsService
        6. Build report using AnalyticsReportBuilder
        7. Store report in Firestore
        
        Args:
            test_id: Test identifier
            student_id: Student identifier
            answers: Student answers dict {question_number: answer}
            test_metadata: Additional test metadata
            include_ai_insights: Whether to generate AI insights
            use_cache: Whether to use cached results
        
        Returns:
            analytics_id: Unique analytics report identifier
        
        Raises:
            AnalyticsServiceError: If pipeline fails
            PipelineStepError: If specific step fails
        
        Example:
            >>> analytics_id = service.generate_analytics(
            ...     test_id="test_123",
            ...     student_id="student_456",
            ...     answers={1: "B", 2: "A", 3: "42"},
            ...     include_ai_insights=True
            ... )
        """
        logger.info(
            f"Starting analytics generation for test={test_id}, "
            f"student={student_id}"
        )
        
        # Check cache
        if use_cache and self.cache:
            cache_key = self._generate_cache_key(test_id, student_id, answers)
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.info("Returning cached analytics")
                return cached_result
        
        # Initialize progress tracker
        tracker = ProgressTracker(total_steps=7 if include_ai_insights else 6)
        tracker.start()
        
        pipeline_start = time.time()
        
        try:
            # Step 1: Retrieve test questions
            tracker.update("Retrieving test questions")
            test_data, questions = self._retrieve_test_questions(test_id)
            
            # Step 2: Calculate scores
            tracker.update("Calculating scores")
            test_score = self._calculate_scores(
                test_id,
                student_id,
                test_data,
                questions,
                answers
            )
            
            # Step 3: Analyze performance
            tracker.update("Analyzing performance")
            performance_analysis = self._analyze_performance(test_score)
            
            # Step 4 & 5: Generate AI insights (if enabled)
            ai_insights = None
            if include_ai_insights:
                tracker.update("Building context for AI")
                context = self._build_ai_context(test_score, performance_analysis)
                
                tracker.update("Generating AI insights")
                ai_insights = self._generate_ai_insights(
                    context,
                    test_data.get("exam_type", "JEE_MAIN"),
                    student_id
                )
            
            # Step 6: Build complete report
            tracker.update("Building analytics report")
            report = self._build_report(
                test_score,
                performance_analysis,
                ai_insights,
                test_metadata
            )
            
            # Step 7: Store in Firestore
            tracker.update("Storing report")
            analytics_id = self._store_report(report)
            
            # Finish tracking
            tracker.finish()
            
            # Log total time
            total_time = time.time() - pipeline_start
            logger.info(
                f"Analytics generation complete: {analytics_id} "
                f"({total_time:.2f}s total)"
            )
            
            # Log step times
            for step_name, step_time in tracker.step_times.items():
                logger.debug(f"  {step_name}: {step_time:.2f}s")
            
            # Cache result
            if use_cache and self.cache:
                self.cache.put(cache_key, analytics_id)
            
            return analytics_id
            
        except Exception as e:
            logger.error(f"Analytics generation failed: {str(e)}")
            raise AnalyticsServiceError(f"Pipeline failed: {str(e)}")
    
    @log_step_time("retrieve_test_questions")
    def _retrieve_test_questions(
        self,
        test_id: str
    ) -> tuple[Dict[str, Any], List[Question]]:
        """Retrieve test questions from Firestore."""
        try:
            # Get test document
            test_ref = self.db.collection(self.tests_collection).document(test_id)
            test_doc = test_ref.get()
            
            if not test_doc.exists:
                raise PipelineStepError(f"Test not found: {test_id}")
            
            test_data = test_doc.to_dict()
            
            # Parse questions
            questions = []
            if "questions" in test_data:
                for q_data in test_data["questions"]:
                    try:
                        question = Question(**q_data)
                        questions.append(question)
                    except Exception as e:
                        logger.warning(f"Failed to parse question: {str(e)}")
                        continue
            
            if not questions:
                raise PipelineStepError(f"No valid questions found in test: {test_id}")
            
            logger.info(f"Retrieved {len(questions)} questions for test {test_id}")
            return test_data, questions
            
        except Exception as e:
            logger.error(f"Failed to retrieve test questions: {str(e)}")
            raise PipelineStepError(f"Test retrieval failed: {str(e)}")
    
    @log_step_time("calculate_scores")
    def _calculate_scores(
        self,
        test_id: str,
        student_id: str,
        test_data: Dict[str, Any],
        questions: List[Question],
        answers: Dict[int, str]
    ) -> TestScore:
        """Calculate test scores."""
        try:
            exam_type = test_data.get("exam_type", "JEE_MAIN")
            
            test_score = self.score_calculator.calculate_test_score(
                test_id=test_id,
                student_id=student_id,
                exam_type=exam_type,
                questions=questions,
                student_answers=answers,
                time_taken=test_data.get("time_taken"),
                submission_time=datetime.utcnow()
            )
            
            logger.info(
                f"Score calculated: {test_score.total_marks_obtained}/"
                f"{test_score.total_max_marks} ({test_score.percentage:.1f}%)"
            )
            
            return test_score
            
        except Exception as e:
            logger.error(f"Score calculation failed: {str(e)}")
            raise PipelineStepError(f"Score calculation failed: {str(e)}")
    
    @log_step_time("analyze_performance")
    def _analyze_performance(self, test_score: TestScore) -> PerformanceAnalysis:
        """Analyze performance."""
        try:
            performance_analysis = self.performance_analyzer.analyze_performance(
                test_score=test_score,
                include_time_analysis=True
            )
            
            logger.info(
                f"Performance analyzed: {len(performance_analysis.strong_topics)} strong, "
                f"{len(performance_analysis.weak_topics)} weak topics"
            )
            
            return performance_analysis
            
        except Exception as e:
            logger.error(f"Performance analysis failed: {str(e)}")
            raise PipelineStepError(f"Performance analysis failed: {str(e)}")
    
    @log_step_time("build_ai_context")
    def _build_ai_context(
        self,
        test_score: TestScore,
        performance_analysis: PerformanceAnalysis
    ) -> str:
        """Build context for AI insights generation."""
        try:
            # Use the build_analytics_context function from utils
            context = build_analytics_context(
                performance_analysis=performance_analysis,
                test_score=test_score
            )
            
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            estimated_tokens = len(context) // 4
            
            logger.info(
                f"Context built: {len(context)} chars, "
                f"~{estimated_tokens} tokens"
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Context building failed: {str(e)}")
            raise PipelineStepError(f"Context building failed: {str(e)}")
    
    @log_step_time("generate_ai_insights")
    def _generate_ai_insights(
        self,
        context: str,
        exam_type: str,
        student_id: str
    ) -> Optional[AnalyticsInsights]:
        """Generate AI insights with retry logic."""
        retry_count = 0
        last_error = None
        
        while retry_count < self.gemini_max_retries:
            try:
                # Generate insights
                analytics_dict = self.gemini_service.generate_analytics(
                    context=context,
                    exam_type=exam_type,
                    student_name=None,  # Can be added if available
                    include_examples=True,
                    max_retries=2,
                    return_partial=True
                )
                
                # Extract AnalyticsInsights from response
                # (gemini_service already returns parsed insights via analytics_parser)
                from utils.analytics_parser import AnalyticsParser
                parser = AnalyticsParser()
                
                # Convert dict to AnalyticsInsights if needed
                if isinstance(analytics_dict, dict) and "metadata" in analytics_dict:
                    # Already has metadata, likely from service
                    # Extract the core analytics data
                    ai_insights = AnalyticsInsights(
                        strengths=analytics_dict.get("strengths", []),
                        weaknesses=analytics_dict.get("weaknesses", []),
                        learning_patterns=analytics_dict.get("learning_patterns", []),
                        overall_assessment=analytics_dict.get("overall_assessment", ""),
                        study_strategy=analytics_dict.get("study_strategy", "")
                    )
                else:
                    # Parse from dict
                    ai_insights = AnalyticsInsights(**analytics_dict)
                
                logger.info(
                    f"AI insights generated: {len(ai_insights.strengths)} strengths, "
                    f"{len(ai_insights.weaknesses)} weaknesses"
                )
                
                return ai_insights
                
            except AnalyticsTimeoutError as e:
                retry_count += 1
                last_error = e
                logger.warning(
                    f"AI insights timeout (attempt {retry_count}/{self.gemini_max_retries})"
                )
                if retry_count < self.gemini_max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
                
            except GeminiAnalyticsError as e:
                retry_count += 1
                last_error = e
                logger.warning(
                    f"AI insights error (attempt {retry_count}/{self.gemini_max_retries}): {str(e)}"
                )
                if retry_count < self.gemini_max_retries:
                    time.sleep(2 ** retry_count)
                
            except Exception as e:
                logger.error(f"Unexpected error in AI insights: {str(e)}")
                last_error = e
                break
        
        # If all retries failed, return None (report will be generated without AI insights)
        logger.warning(
            f"AI insights generation failed after {retry_count} attempts: {str(last_error)}"
        )
        return None
    
    @log_step_time("build_report")
    def _build_report(
        self,
        test_score: TestScore,
        performance_analysis: PerformanceAnalysis,
        ai_insights: Optional[AnalyticsInsights],
        test_metadata: Optional[Dict[str, Any]]
    ) -> AnalyticsReport:
        """Build complete analytics report."""
        try:
            report = self.report_builder.build_report(
                score_result=test_score,
                performance_analysis=performance_analysis,
                ai_insights=ai_insights,
                test_metadata=test_metadata
            )
            
            logger.info(
                f"Report built: {len(report.subject_analysis)} subjects, "
                f"{len(report.priority_topics)} priority topics"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Report building failed: {str(e)}")
            raise PipelineStepError(f"Report building failed: {str(e)}")
    
    @log_step_time("store_report")
    def _store_report(self, report: AnalyticsReport) -> str:
        """Store analytics report in Firestore."""
        try:
            # Generate analytics ID
            analytics_id = f"analytics_{report.overview.test_id}_{report.overview.student_id}_{int(time.time())}"
            
            # Convert report to dict
            report_dict = report.model_dump(mode='json')
            
            # Add analytics ID to report
            report_dict["analytics_id"] = analytics_id
            report_dict["created_at"] = firestore.SERVER_TIMESTAMP
            
            # Store in Firestore
            analytics_ref = self.db.collection(self.analytics_collection).document(analytics_id)
            analytics_ref.set(report_dict)
            
            logger.info(f"Report stored: {analytics_id}")
            
            return analytics_id
            
        except Exception as e:
            logger.error(f"Report storage failed: {str(e)}")
            raise PipelineStepError(f"Report storage failed: {str(e)}")
    
    def get_analytics(self, analytics_id: str) -> AnalyticsReport:
        """
        Retrieve analytics report by ID.
        
        Args:
            analytics_id: Analytics report identifier
        
        Returns:
            AnalyticsReport: Complete analytics report
        
        Raises:
            AnalyticsNotFoundError: If analytics not found
        
        Example:
            >>> report = service.get_analytics("analytics_test123_student456_...")
        """
        try:
            analytics_ref = self.db.collection(self.analytics_collection).document(analytics_id)
            analytics_doc = analytics_ref.get()
            
            if not analytics_doc.exists:
                raise AnalyticsNotFoundError(f"Analytics not found: {analytics_id}")
            
            report_dict = analytics_doc.to_dict()
            
            # Convert to AnalyticsReport
            report = AnalyticsReport(**report_dict)
            
            logger.info(f"Retrieved analytics: {analytics_id}")
            
            return report
            
        except AnalyticsNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to retrieve analytics: {str(e)}")
            raise AnalyticsServiceError(f"Analytics retrieval failed: {str(e)}")
    
    def get_student_analytics(
        self,
        student_id: str,
        limit: int = 10,
        order_by: str = "generated_at"
    ) -> List[AnalyticsReport]:
        """
        Retrieve all analytics reports for a student.
        
        Args:
            student_id: Student identifier
            limit: Maximum number of reports to return
            order_by: Field to order by (default: generated_at)
        
        Returns:
            List[AnalyticsReport]: List of analytics reports
        
        Example:
            >>> reports = service.get_student_analytics("student_456", limit=5)
        """
        try:
            # Query analytics for student
            analytics_query = (
                self.db.collection(self.analytics_collection)
                .where(filter=FieldFilter("overview.student_id", "==", student_id))
                .order_by(order_by, direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            analytics_docs = analytics_query.stream()
            
            reports = []
            for doc in analytics_docs:
                try:
                    report_dict = doc.to_dict()
                    report = AnalyticsReport(**report_dict)
                    reports.append(report)
                except Exception as e:
                    logger.warning(f"Failed to parse analytics doc: {str(e)}")
                    continue
            
            logger.info(f"Retrieved {len(reports)} analytics for student {student_id}")
            
            return reports
            
        except Exception as e:
            logger.error(f"Failed to retrieve student analytics: {str(e)}")
            raise AnalyticsServiceError(f"Student analytics retrieval failed: {str(e)}")
    
    def _generate_cache_key(
        self,
        test_id: str,
        student_id: str,
        answers: Dict[int, str]
    ) -> str:
        """Generate cache key for analytics request."""
        # Create deterministic key from inputs
        answers_str = str(sorted(answers.items()))
        key_str = f"{test_id}:{student_id}:{answers_str}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def clear_cache(self):
        """Clear analytics cache."""
        if self.cache:
            self.cache.clear()
            logger.info("Analytics cache cleared")
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Dict with service statistics
        """
        stats = {
            "cache_enabled": self.enable_cache,
            "cache_size": len(self.cache.cache) if self.cache else 0,
            "gemini_max_retries": self.gemini_max_retries
        }
        
        # Add Gemini service stats
        if hasattr(self.gemini_service, 'get_usage_stats'):
            stats["gemini_stats"] = self.gemini_service.get_usage_stats()
        
        return stats
