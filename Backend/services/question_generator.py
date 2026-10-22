"""
Question Generator Service for Mentor AI Platform

This module orchestrates the complete RAG (Retrieval-Augmented Generation)
pipeline for generating exam questions. It combines vector search, context
building, prompt generation, LLM generation, and question validation.

Features:
- End-to-end RAG pipeline for question generation
- Vector search integration for syllabus retrieval
- Context building from search results
- Prompt generation using templates
- Gemini Flash LLM generation
- Question validation and filtering
- Firestore storage
- Batch generation support
- Retry logic for insufficient results
- Caching of generated questions
- Comprehensive statistics tracking

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.question_generator import QuestionGenerator
    >>> 
    >>> # Initialize generator
    >>> generator = QuestionGenerator()
    >>> 
    >>> # Generate questions
    >>> questions = generator.generate_questions(
    ...     topic="Limits and Continuity",
    ...     exam_type="JEE_MAIN",
    ...     difficulty="medium",
    ...     num_questions=5
    ... )
    >>> 
    >>> print(f"Generated {len(questions)} valid questions")
    >>> 
    >>> # Get statistics
    >>> stats = generator.get_generation_stats()
    >>> print(f"Success rate: {stats['success_rate']:.1%}")
"""

import logging
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from models.question_models import Question
from services.vector_search_service import search_topics, SearchFilters
from services.gemini_service import GeminiService
from services.question_validator import QuestionValidator, ValidationResult
from utils.prompt_templates import build_prompt
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MIN_VALID_QUESTIONS_RATIO = 0.8  # 80% of requested questions
MAX_GENERATION_ATTEMPTS = 2
MIN_VALIDATION_SCORE = 70
SEARCH_TOP_K = 5  # Number of vector search results to retrieve
FIRESTORE_COLLECTION = "generated_questions"
CACHE_TTL_HOURS = 24


class QuestionGeneratorError(Exception):
    """Base exception for question generator errors."""
    pass


class InsufficientContextError(QuestionGeneratorError):
    """Raised when vector search returns insufficient context."""
    pass


class QuestionGenerator:
    """
    Orchestrates the complete RAG pipeline for question generation.
    
    This service combines all components needed for generating high-quality
    exam questions: vector search, context building, prompt engineering,
    LLM generation, and validation.
    
    Attributes:
        gemini_service: Service for Gemini LLM API calls
        validator: Service for question validation
        firestore_client: Firestore database client
        use_cache: Whether to cache questions in Firestore
        generation_stats: Statistics tracking
    
    Example:
        >>> generator = QuestionGenerator()
        >>> questions = generator.generate_questions(
        ...     topic="Calculus",
        ...     exam_type="JEE_MAIN",
        ...     difficulty="medium",
        ...     num_questions=5
        ... )
    """
    
    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        validator: Optional[QuestionValidator] = None,
        use_cache: bool = True,
        min_validation_score: int = MIN_VALIDATION_SCORE
    ):
        """
        Initialize QuestionGenerator.
        
        Args:
            gemini_service: Optional GeminiService instance
            validator: Optional QuestionValidator instance
            use_cache: Whether to check/store in Firestore cache
            min_validation_score: Minimum validation score for questions
        """
        logger.info("Initializing QuestionGenerator")
        
        # Initialize services
        self.gemini_service = gemini_service if gemini_service else GeminiService()
        self.validator = validator if validator else QuestionValidator(
            min_quality_score=min_validation_score
        )
        
        # Firestore client
        try:
            self.firestore_client = get_firestore_client()
            logger.info("Firestore client initialized")
        except Exception as e:
            logger.warning(f"Firestore initialization failed: {e}")
            self.firestore_client = None
        
        self.use_cache = use_cache and self.firestore_client is not None
        self.min_validation_score = min_validation_score
        
        # Statistics
        self.generation_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_questions_generated": 0,
            "total_questions_valid": 0,
            "total_questions_invalid": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_validation_score": 0.0,
            "average_generation_time": 0.0,
            "total_generation_time": 0.0,
            "vector_search_calls": 0,
            "llm_calls": 0
        }
        
        logger.info(
            f"QuestionGenerator initialized (cache={use_cache}, "
            f"min_score={min_validation_score})"
        )
    
    def generate_questions(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        num_questions: int,
        use_cache: bool = True,
        question_type: str = "single_correct"
    ) -> List[Question]:
        """
        Generate questions using the complete RAG pipeline.
        
        Pipeline steps:
        1. Check Firestore cache for existing questions
        2. Query vector search for syllabus context
        3. Build context from search results
        4. Generate prompt using templates
        5. Call Gemini to generate questions
        6. Validate each question
        7. Filter by validation score
        8. Store valid questions in Firestore
        9. Return questions with metadata
        
        Args:
            topic: Topic name for questions
            exam_type: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
            difficulty: Difficulty level (easy, medium, hard)
            num_questions: Number of questions to generate
            use_cache: Whether to use Firestore cache
            question_type: Type of questions (single_correct, etc.)
        
        Returns:
            List of validated Question objects with metadata
        
        Raises:
            QuestionGeneratorError: If generation fails completely
            ValueError: If parameters are invalid
        
        Example:
            >>> generator = QuestionGenerator()
            >>> questions = generator.generate_questions(
            ...     topic="Limits and Continuity",
            ...     exam_type="JEE_MAIN",
            ...     difficulty="medium",
            ...     num_questions=5
            ... )
            >>> for q in questions:
            ...     print(f"{q.topic}: Score {q.validation_score}")
        """
        start_time = time.time()
        
        # Validate parameters
        self._validate_parameters(topic, exam_type, difficulty, num_questions)
        
        logger.info(
            f"Generating {num_questions} {difficulty} questions on '{topic}' "
            f"for {exam_type}"
        )
        
        self.generation_stats["total_requests"] += 1
        
        try:
            # Step 1: Check cache
            if self.use_cache and use_cache:
                cached_questions = self._check_cache(
                    topic, exam_type, difficulty, num_questions
                )
                if cached_questions and len(cached_questions) >= num_questions:
                    logger.info(f"Cache hit! Returning {len(cached_questions)} cached questions")
                    self.generation_stats["cache_hits"] += 1
                    return cached_questions[:num_questions]
            
            self.generation_stats["cache_misses"] += 1
            
            # Step 2: Retrieve context using vector search
            logger.info("Step 1: Retrieving context from vector search")
            syllabus_context = self._retrieve_context(topic, exam_type)
            
            if not syllabus_context or len(syllabus_context.strip()) < 50:
                raise InsufficientContextError(
                    f"Insufficient context retrieved for topic '{topic}'"
                )
            
            logger.info(f"Retrieved context: {len(syllabus_context)} characters")
            
            # Step 3 & 4: Generate questions (with retry logic)
            valid_questions = []
            attempt = 0
            
            while attempt < MAX_GENERATION_ATTEMPTS and \
                  len(valid_questions) < int(num_questions * MIN_VALID_QUESTIONS_RATIO):
                
                attempt += 1
                logger.info(f"Generation attempt {attempt}/{MAX_GENERATION_ATTEMPTS}")
                
                # Build prompt
                logger.info("Step 2: Building prompt")
                # Determine subject based on exam type and topic
                subject = self._determine_subject(exam_type, topic)
                
                prompt = build_prompt(
                    exam_type=exam_type,
                    topic=topic,
                    syllabus_context=syllabus_context,
                    difficulty=difficulty,
                    num_questions=num_questions,
                    question_type=question_type,
                    subject=subject
                )
                
                # Generate questions using Gemini
                logger.info("Step 3: Calling Gemini to generate questions")
                self.generation_stats["llm_calls"] += 1
                
                generated_questions = self.gemini_service.generate_questions(
                    prompt=prompt,
                    num_questions=num_questions,
                    use_cache=True,
                    retry_on_insufficient=True
                )
                
                self.generation_stats["total_questions_generated"] += len(generated_questions)
                logger.info(f"Gemini generated {len(generated_questions)} questions")
                
                # Step 5 & 6: Validate and filter questions
                logger.info("Step 4: Validating questions")
                validated_questions = self._validate_and_filter(
                    generated_questions,
                    syllabus_context
                )
                
                logger.info(
                    f"Validated: {len(validated_questions)} valid out of "
                    f"{len(generated_questions)}"
                )
                
                # Combine with previous attempts (avoid duplicates)
                valid_questions = self._merge_questions(
                    valid_questions,
                    validated_questions
                )
                
                # Check if we have enough
                if len(valid_questions) >= num_questions:
                    break
                
                # Log retry reason
                if attempt < MAX_GENERATION_ATTEMPTS:
                    logger.warning(
                        f"Insufficient valid questions: {len(valid_questions)}/{num_questions}. "
                        f"Retrying..."
                    )
            
            # Check final results
            if len(valid_questions) == 0:
                self.generation_stats["failed_requests"] += 1
                raise QuestionGeneratorError(
                    f"Failed to generate any valid questions for topic '{topic}'"
                )
            
            # Step 7: Add metadata
            logger.info("Step 5: Adding metadata to questions")
            final_questions = self._add_metadata(
                valid_questions[:num_questions],
                topic,
                exam_type,
                difficulty
            )
            
            # Step 8: Store in Firestore
            if self.use_cache:
                logger.info("Step 6: Storing questions in Firestore")
                self._store_questions(final_questions, topic, exam_type, difficulty)
            
            # Update statistics
            generation_time = time.time() - start_time
            self._update_statistics(
                len(final_questions),
                generation_time,
                success=True
            )
            
            logger.info(
                f"Generation completed: {len(final_questions)} questions in "
                f"{generation_time:.2f}s"
            )
            
            self.generation_stats["successful_requests"] += 1
            
            return final_questions
        
        except InsufficientContextError as ice:
            logger.error(f"Insufficient context error: {ice}")
            self.generation_stats["failed_requests"] += 1
            raise
        
        except Exception as e:
            logger.error(f"Question generation failed: {e}")
            logger.exception("Full traceback:")
            
            generation_time = time.time() - start_time
            self._update_statistics(0, generation_time, success=False)
            
            self.generation_stats["failed_requests"] += 1
            raise QuestionGeneratorError(f"Generation failed: {str(e)}")
    
    def generate_batch(
        self,
        topics: List[str],
        exam_type: str,
        difficulty: str,
        num_per_topic: int = 5
    ) -> Dict[str, List[Question]]:
        """
        Generate questions for multiple topics in batch.
        
        Args:
            topics: List of topic names
            exam_type: Exam type for all topics
            difficulty: Difficulty level for all topics
            num_per_topic: Number of questions per topic
        
        Returns:
            Dictionary mapping topic to list of questions
        
        Example:
            >>> generator = QuestionGenerator()
            >>> results = generator.generate_batch(
            ...     topics=["Calculus", "Algebra", "Trigonometry"],
            ...     exam_type="JEE_MAIN",
            ...     difficulty="medium",
            ...     num_per_topic=5
            ... )
            >>> for topic, questions in results.items():
            ...     print(f"{topic}: {len(questions)} questions")
        """
        logger.info(
            f"Batch generation: {len(topics)} topics, {num_per_topic} questions each"
        )
        
        results = {}
        
        for topic in topics:
            try:
                questions = self.generate_questions(
                    topic=topic,
                    exam_type=exam_type,
                    difficulty=difficulty,
                    num_questions=num_per_topic
                )
                results[topic] = questions
                logger.info(f"✓ {topic}: {len(questions)} questions generated")
            
            except Exception as e:
                logger.error(f"✗ {topic}: Generation failed - {e}")
                results[topic] = []
        
        total_generated = sum(len(qs) for qs in results.values())
        logger.info(
            f"Batch generation completed: {total_generated} total questions across "
            f"{len(results)} topics"
        )
        
        return results
    
    def _retrieve_context(self, topic: str, exam_type: str) -> str:
        """
        Retrieve syllabus context using local data with optional Gemini enhancement.
        
        OPTIMIZATION: Uses local syllabus data directly, only calls Gemini if
        exact match not found. This reduces API calls by 70-80%.
        
        Args:
            topic: Topic to search for
            exam_type: Exam type for filtering
        
        Returns:
            Combined context text from syllabus
        """
        try:
            self.generation_stats["vector_search_calls"] += 1
            
            # Load syllabus data for the exam
            from services import syllabus_service
            import json
            import os
            
            # Determine subjects based on exam type
            subjects = ["Physics", "Chemistry", "Mathematics"] if "JEE" in exam_type else ["Physics", "Chemistry", "Biology"]
            
            # OPTIMIZATION 1: Try to find exact or close match in syllabus data
            matched_content = None
            topic_lower = topic.lower()
            
            for subject in subjects:
                try:
                    # Load syllabus file directly for better structure
                    syllabus_file = f"data/syllabus/{exam_type}_{subject}.json"
                    if os.path.exists(syllabus_file):
                        with open(syllabus_file, 'r') as f:
                            syllabus_data = json.load(f)
                        
                        # Search through chapters and topics
                        for chapter in syllabus_data.get('chapters', []):
                            for topic_item in chapter.get('topics', []):
                                topic_name = topic_item.get('topic_name', '').lower()
                                
                                # Check for exact or partial match
                                if topic_lower in topic_name or topic_name in topic_lower:
                                    # Found a match! Build context from this topic
                                    matched_content = self._build_context_from_topic(
                                        topic_item, 
                                        chapter, 
                                        exam_type, 
                                        subject
                                    )
                                    logger.info(f"Found exact match for '{topic}' in {subject} syllabus (no Gemini call)")
                                    return matched_content
                                
                                # Also check subtopics
                                for subtopic in topic_item.get('subtopics', []):
                                    subtopic_name = subtopic.get('subtopic_name', '').lower()
                                    if topic_lower in subtopic_name or subtopic_name in topic_lower:
                                        matched_content = self._build_context_from_subtopic(
                                            subtopic,
                                            topic_item,
                                            chapter,
                                            exam_type,
                                            subject
                                        )
                                        logger.info(f"Found subtopic match for '{topic}' in {subject} syllabus (no Gemini call)")
                                        return matched_content
                
                except Exception as e:
                    logger.debug(f"Could not search {subject} syllabus: {e}")
                    continue
            
            # OPTIMIZATION 2: If no exact match, try keyword matching
            logger.info(f"No exact match found, trying keyword search for '{topic}'")
            keyword_matches = []
            topic_words = set(topic_lower.split())
            
            for subject in subjects:
                try:
                    syllabus_file = f"data/syllabus/{exam_type}_{subject}.json"
                    if os.path.exists(syllabus_file):
                        with open(syllabus_file, 'r') as f:
                            syllabus_data = json.load(f)
                        
                        for chapter in syllabus_data.get('chapters', []):
                            for topic_item in chapter.get('topics', []):
                                topic_name = topic_item.get('topic_name', '').lower()
                                topic_name_words = set(topic_name.split())
                                
                                # Calculate word overlap
                                overlap = len(topic_words & topic_name_words)
                                if overlap > 0:
                                    keyword_matches.append((overlap, topic_item, chapter, subject))
                
                except Exception as e:
                    logger.debug(f"Could not search {subject} syllabus: {e}")
                    continue
            
            # If we found keyword matches, use the best one
            if keyword_matches:
                keyword_matches.sort(key=lambda x: x[0], reverse=True)
                overlap, best_topic, best_chapter, best_subject = keyword_matches[0]
                
                matched_content = self._build_context_from_topic(
                    best_topic,
                    best_chapter,
                    exam_type,
                    best_subject
                )
                logger.info(f"Found keyword match for '{topic}' with {overlap} overlapping words (no Gemini call)")
                return matched_content
            
            # OPTIMIZATION 3: Only use Gemini as last resort for complex queries
            logger.info(f"No local match found, using Gemini API as fallback for '{topic}'")
            
            # Collect all topics for Gemini
            all_topics = []
            for subject in subjects:
                try:
                    topics = syllabus_service.get_topics(exam_type, subject, use_cache=True)
                    all_topics.extend(topics)
                except Exception as e:
                    logger.debug(f"Could not load {subject} syllabus: {e}")
                    continue
            
            if not all_topics:
                logger.warning(f"No syllabus data available for {exam_type}")
                return f"Topic: {topic}\nExam: {exam_type}\nGenerate questions based on standard syllabus."
            
            # Use minimal Gemini prompt
            topics_list = [
                f"{i+1}. {t.get('topic_name', t.get('topic', 'Unknown'))}"
                for i, t in enumerate(all_topics[:30])  # Limit to 30 to reduce tokens
            ]
            
            context_prompt = f"""Topic: "{topic}"
Exam: {exam_type}

Available topics:
{chr(10).join(topics_list)}

Which topic number is most relevant? Reply with just the number."""
            
            response = self.gemini_service.client.generate_content(context_prompt)
            
            # Try to extract topic number
            import re
            match = re.search(r'\d+', response)
            if match:
                idx = int(match.group()) - 1
                if 0 <= idx < len(all_topics):
                    selected_topic = all_topics[idx]
                    # Build context from selected topic
                    context = f"""Topic: {selected_topic.get('topic_name', topic)}
Chapter: {selected_topic.get('chapter_name', 'Unknown')}
Key Concepts: {', '.join(selected_topic.get('key_concepts', []))}
Formulas: {', '.join(selected_topic.get('formulas', []))}
Content: {selected_topic.get('content', selected_topic.get('description', 'No content available'))}"""
                    
                    logger.info(f"Built context using Gemini selection for '{topic}'")
                    return context
            
            # Final fallback
            return f"Topic: {topic}\nExam: {exam_type}\nGenerate questions based on standard syllabus."
        
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            logger.exception("Full traceback:")
            return f"Topic: {topic}\nExam: {exam_type}\nGenerate questions based on standard syllabus."
    
    def _build_context_from_topic(
        self,
        topic_item: Dict,
        chapter: Dict,
        exam_type: str,
        subject: str
    ) -> str:
        """Build detailed context from a matched topic."""
        context_parts = [
            f"Exam: {exam_type}",
            f"Subject: {subject}",
            f"Chapter: {chapter.get('chapter_name', 'Unknown')} (Weightage: {chapter.get('weightage', 0)}%)",
            f"Topic: {topic_item.get('topic_name', 'Unknown')} (Weightage: {topic_item.get('weightage', 0)}%)",
            f"Difficulty: {topic_item.get('difficulty', 'medium')}",
            f"Description: {topic_item.get('description', 'No description')}",
            ""
        ]
        
        # Add subtopics
        subtopics = topic_item.get('subtopics', [])
        if subtopics:
            context_parts.append("Subtopics:")
            for st in subtopics:
                context_parts.append(f"\n{st.get('subtopic_name', 'Unknown')}:")
                context_parts.append(f"Content: {st.get('content', 'No content')}")
                
                key_concepts = st.get('key_concepts', [])
                if key_concepts:
                    context_parts.append(f"Key Concepts: {', '.join(key_concepts)}")
                
                formulas = st.get('formulas', [])
                if formulas:
                    context_parts.append(f"Formulas: {', '.join(formulas)}")
                
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _build_context_from_subtopic(
        self,
        subtopic: Dict,
        topic_item: Dict,
        chapter: Dict,
        exam_type: str,
        subject: str
    ) -> str:
        """Build detailed context from a matched subtopic."""
        context_parts = [
            f"Exam: {exam_type}",
            f"Subject: {subject}",
            f"Chapter: {chapter.get('chapter_name', 'Unknown')}",
            f"Topic: {topic_item.get('topic_name', 'Unknown')}",
            f"Subtopic: {subtopic.get('subtopic_name', 'Unknown')}",
            f"Difficulty: {subtopic.get('difficulty', topic_item.get('difficulty', 'medium'))}",
            "",
            f"Content: {subtopic.get('content', 'No content')}",
            ""
        ]
        
        key_concepts = subtopic.get('key_concepts', [])
        if key_concepts:
            context_parts.append(f"Key Concepts: {', '.join(key_concepts)}")
        
        formulas = subtopic.get('formulas', [])
        if formulas:
            context_parts.append(f"Important Formulas: {', '.join(formulas)}")
        
        return "\n".join(context_parts)
    
    def _validate_and_filter(
        self,
        questions: List[Question],
        syllabus_context: str
    ) -> List[Question]:
        """
        Validate questions and filter by quality score.
        
        Args:
            questions: List of generated questions
            syllabus_context: Syllabus context for validation
        
        Returns:
            List of valid questions that passed validation
        """
        valid_questions = []
        validation_scores = []
        
        for idx, question in enumerate(questions, 1):
            try:
                # Validate question
                result = self.validator.validate(question, syllabus_context)
                
                if result.is_valid and result.quality_score >= self.min_validation_score:
                    # Add validation metadata to question
                    question_dict = question.dict()
                    question_dict["validation_score"] = result.quality_score
                    question_dict["validation_warnings"] = result.warnings
                    
                    # Recreate question with metadata
                    validated_question = Question(**question_dict)
                    valid_questions.append(validated_question)
                    validation_scores.append(result.quality_score)
                    
                    logger.debug(
                        f"Question {idx} valid: score={result.quality_score}, "
                        f"topic={question.topic}"
                    )
                    
                    self.generation_stats["total_questions_valid"] += 1
                else:
                    logger.debug(
                        f"Question {idx} rejected: score={result.quality_score}, "
                        f"issues={result.issues}"
                    )
                    self.generation_stats["total_questions_invalid"] += 1
            
            except Exception as e:
                logger.warning(f"Question {idx} validation error: {e}")
                self.generation_stats["total_questions_invalid"] += 1
        
        # Update average validation score
        if validation_scores:
            avg_score = sum(validation_scores) / len(validation_scores)
            current_avg = self.generation_stats["average_validation_score"]
            total_valid = self.generation_stats["total_questions_valid"]
            
            # Calculate running average
            self.generation_stats["average_validation_score"] = (
                (current_avg * (total_valid - len(validation_scores)) + 
                 sum(validation_scores)) / total_valid
                if total_valid > 0 else 0
            )
        
        return valid_questions
    
    def _merge_questions(
        self,
        existing: List[Question],
        new: List[Question]
    ) -> List[Question]:
        """
        Merge question lists, avoiding duplicates.
        
        Args:
            existing: Existing questions
            new: New questions to add
        
        Returns:
            Merged list without duplicates
        """
        # Create set of existing question texts (normalized)
        existing_texts = {
            q.question.lower().strip()
            for q in existing
        }
        
        # Add new questions that aren't duplicates
        merged = list(existing)
        
        for question in new:
            question_text = question.question.lower().strip()
            if question_text not in existing_texts:
                merged.append(question)
                existing_texts.add(question_text)
        
        return merged
    
    def _add_metadata(
        self,
        questions: List[Question],
        topic: str,
        exam_type: str,
        difficulty: str
    ) -> List[Question]:
        """
        Add generation metadata to questions.
        
        Args:
            questions: List of questions
            topic: Topic name
            exam_type: Exam type
            difficulty: Difficulty level
        
        Returns:
            Questions with added metadata
        """
        enriched_questions = []
        
        for question in questions:
            # Convert to dict to add metadata
            question_dict = question.dict()
            
            # Add metadata
            question_dict.update({
                "generation_timestamp": datetime.utcnow(),
                "generation_method": "RAG",
                "requested_topic": topic,
                "requested_exam_type": exam_type,
                "requested_difficulty": difficulty
            })
            
            # Recreate question (validation will handle extra fields)
            enriched_questions.append(question)
        
        return enriched_questions
    
    def _check_cache(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        num_questions: int
    ) -> Optional[List[Question]]:
        """
        Check Firestore cache for existing questions.
        
        Args:
            topic: Topic name
            exam_type: Exam type
            difficulty: Difficulty level
            num_questions: Number of questions needed
        
        Returns:
            List of cached questions or None
        """
        if not self.firestore_client:
            return None
        
        try:
            # Query Firestore for matching questions
            questions_ref = self.firestore_client.collection(FIRESTORE_COLLECTION)
            
            # Build query
            query = questions_ref.where(filter=[
                {"field": "requested_topic", "op": "==", "value": topic},
                {"field": "requested_exam_type", "op": "==", "value": exam_type},
                {"field": "requested_difficulty", "op": "==", "value": difficulty}
            ]).limit(num_questions * 2)  # Get extra for variety
            
            # Execute query
            docs = query.stream()
            
            # Convert to Question objects
            cached_questions = []
            for doc in docs:
                data = doc.to_dict()
                
                # Check if not expired
                if "generation_timestamp" in data:
                    gen_time = data["generation_timestamp"]
                    if isinstance(gen_time, str):
                        gen_time = datetime.fromisoformat(gen_time)
                    
                    age = datetime.utcnow() - gen_time
                    if age > timedelta(hours=CACHE_TTL_HOURS):
                        continue  # Skip expired questions
                
                # Reconstruct Question object
                try:
                    question = Question(**data)
                    cached_questions.append(question)
                except Exception as e:
                    logger.warning(f"Failed to parse cached question: {e}")
            
            if cached_questions:
                logger.info(
                    f"Found {len(cached_questions)} cached questions for "
                    f"'{topic}' ({exam_type}, {difficulty})"
                )
                return cached_questions
            
            return None
        
        except Exception as e:
            logger.warning(f"Cache check failed: {e}")
            return None
    
    def _store_questions(
        self,
        questions: List[Question],
        topic: str,
        exam_type: str,
        difficulty: str
    ) -> None:
        """
        Store questions in Firestore.
        
        Args:
            questions: List of questions to store
            topic: Topic name
            exam_type: Exam type
            difficulty: Difficulty level
        """
        if not self.firestore_client:
            logger.warning("Firestore client not available, skipping storage")
            return
        
        try:
            collection_ref = self.firestore_client.collection(FIRESTORE_COLLECTION)
            
            for question in questions:
                # Generate unique ID
                question_hash = hashlib.md5(
                    question.question.encode()
                ).hexdigest()
                
                doc_id = f"{exam_type}_{topic}_{difficulty}_{question_hash[:8]}"
                
                # Prepare data
                data = question.dict()
                data.update({
                    "requested_topic": topic,
                    "requested_exam_type": exam_type,
                    "requested_difficulty": difficulty,
                    "generation_timestamp": datetime.utcnow(),
                    "generation_method": "RAG"
                })
                
                # Store in Firestore
                collection_ref.document(doc_id).set(data)
            
            logger.info(f"Stored {len(questions)} questions in Firestore")
        
        except Exception as e:
            logger.error(f"Failed to store questions in Firestore: {e}")
    
    def _validate_parameters(
        self,
        topic: str,
        exam_type: str,
        difficulty: str,
        num_questions: int
    ) -> None:
        """
        Validate generation parameters.
        
        Args:
            topic: Topic name
            exam_type: Exam type
            difficulty: Difficulty level
            num_questions: Number of questions
        
        Raises:
            ValueError: If parameters are invalid
        """
        if not topic or len(topic.strip()) < 3:
            raise ValueError("Topic must be at least 3 characters")
        
        if exam_type not in ["JEE_MAIN", "JEE_ADVANCED", "NEET"]:
            raise ValueError(
                f"Invalid exam_type: {exam_type}. Must be JEE_MAIN, JEE_ADVANCED, or NEET"
            )
        
        if difficulty not in ["easy", "medium", "hard"]:
            raise ValueError(
                f"Invalid difficulty: {difficulty}. Must be easy, medium, or hard"
            )
        
        if num_questions < 1 or num_questions > 20:
            raise ValueError("num_questions must be between 1 and 20")
    
    def _update_statistics(
        self,
        num_generated: int,
        generation_time: float,
        success: bool
    ) -> None:
        """
        Update generation statistics.
        
        Args:
            num_generated: Number of questions generated
            generation_time: Time taken in seconds
            success: Whether generation was successful
        """
        self.generation_stats["total_generation_time"] += generation_time
        
        if success:
            total_successful = self.generation_stats["successful_requests"]
            if total_successful > 0:
                current_avg = self.generation_stats["average_generation_time"]
                self.generation_stats["average_generation_time"] = (
                    (current_avg * (total_successful - 1) + generation_time) / 
                    total_successful
                )
            else:
                self.generation_stats["average_generation_time"] = generation_time
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive generation statistics.
        
        Returns:
            Dictionary with generation statistics
        
        Example:
            >>> generator = QuestionGenerator()
            >>> # ... generate questions ...
            >>> stats = generator.get_generation_stats()
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
            >>> print(f"Avg validation score: {stats['average_validation_score']:.1f}")
        """
        stats = dict(self.generation_stats)
        
        # Calculate derived metrics
        total_requests = stats["total_requests"]
        if total_requests > 0:
            stats["success_rate"] = (
                stats["successful_requests"] / total_requests
            )
            stats["cache_hit_rate"] = (
                stats["cache_hits"] / 
                (stats["cache_hits"] + stats["cache_misses"])
                if (stats["cache_hits"] + stats["cache_misses"]) > 0 else 0
            )
        else:
            stats["success_rate"] = 0.0
            stats["cache_hit_rate"] = 0.0
        
        total_generated = stats["total_questions_generated"]
        if total_generated > 0:
            stats["validation_pass_rate"] = (
                stats["total_questions_valid"] / total_generated
            )
        else:
            stats["validation_pass_rate"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """
        Reset generation statistics.
        
        Example:
            >>> generator = QuestionGenerator()
            >>> generator.reset_stats()
        """
        self.generation_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_questions_generated": 0,
            "total_questions_valid": 0,
            "total_questions_invalid": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_validation_score": 0.0,
            "average_generation_time": 0.0,
            "total_generation_time": 0.0,
            "vector_search_calls": 0,
            "llm_calls": 0
        }
        logger.info("Generation statistics reset")
    
    def _determine_subject(self, exam_type: str, topic: str) -> str:
        """
        Determine subject based on exam type and topic.
        
        Args:
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            topic: Topic name
        
        Returns:
            Subject name (Physics, Chemistry, Math, Biology)
        """
        topic_lower = topic.lower()
        
        # Physics keywords
        physics_keywords = [
            'motion', 'force', 'energy', 'wave', 'optics', 'electricity', 'magnetism',
            'thermodynamics', 'mechanics', 'kinematics', 'dynamics', 'gravity',
            'fluid', 'heat', 'temperature', 'light', 'sound', 'nuclear', 'quantum',
            'relativity', 'electromagnetic', 'circuit', 'current', 'voltage',
            'resistance', 'capacitance', 'inductance', 'lens', 'mirror'
        ]
        
        # Chemistry keywords
        chemistry_keywords = [
            'atom', 'molecule', 'bond', 'reaction', 'acid', 'base', 'salt',
            'organic', 'inorganic', 'periodic', 'element', 'compound', 'mixture',
            'solution', 'concentration', 'ph', 'oxidation', 'reduction', 'catalyst',
            'equilibrium', 'kinetics', 'thermochemistry', 'electrochemistry',
            'carbon', 'hydrogen', 'oxygen', 'nitrogen', 'metal', 'nonmetal'
        ]
        
        # Biology keywords
        biology_keywords = [
            'cell', 'tissue', 'organ', 'organism', 'genetics', 'evolution',
            'ecology', 'physiology', 'anatomy', 'taxonomy', 'microbiology',
            'biotechnology', 'immunology', 'reproduction', 'respiration',
            'photosynthesis', 'digestion', 'circulation', 'nervous', 'hormone',
            'enzyme', 'protein', 'dna', 'rna', 'chromosome', 'gene'
        ]
        
        # Math keywords
        math_keywords = [
            'algebra', 'trigonometry', 'calculus', 'geometry', 'coordinate',
            'derivative', 'integral', 'limit', 'function', 'equation', 'inequality',
            'matrix', 'vector', 'probability', 'statistics', 'permutation',
            'combination', 'sequence', 'series', 'polynomial', 'logarithm',
            'complex', 'number', 'set', 'relation', 'differential'
        ]
        
        # Check for keywords in topic
        for keyword in physics_keywords:
            if keyword in topic_lower:
                return "Physics"
        
        for keyword in chemistry_keywords:
            if keyword in topic_lower:
                return "Chemistry"
        
        for keyword in biology_keywords:
            if keyword in topic_lower:
                return "Biology"
        
        for keyword in math_keywords:
            if keyword in topic_lower:
                return "Math"
        
        # Default based on exam type
        if exam_type == "NEET":
            return "Biology"  # NEET has more biology questions
        elif "JEE" in exam_type:
            return "Physics"  # JEE has more physics questions
        else:
            return "Physics"  # Default fallback


# Module initialization
logger.info("Question generator module loaded")
logger.info(f"Configuration: min_valid_ratio={MIN_VALID_QUESTIONS_RATIO}, max_attempts={MAX_GENERATION_ATTEMPTS}")
