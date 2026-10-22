"""
Syllabus Data Management Service Module

This module handles loading and processing JEE/NEET syllabus data for the
Mentor AI EdTech Platform. It provides functions to load syllabus from JSON
files, extract topics, chunk content for embeddings, and manage syllabus metadata.

Functions:
- load_syllabus: Load syllabus data from JSON files
- get_topics: Get all topics for an exam and subject
- chunk_topics: Split topics into chunks for embedding generation
- get_syllabus_stats: Get statistics about syllabus data
- clear_syllabus_cache: Clear cached syllabus data

Features:
- Pydantic models for data validation
- In-memory caching of loaded syllabus
- Automatic chunking for embedding (max 500 words)
- Metadata extraction (subject, chapter, topic, weightage, difficulty)
- Support for JEE_MAIN, JEE_ADVANCED, NEET exams
- Graceful error handling for missing files
- Comprehensive logging

Supported Exams:
- JEE_MAIN: Physics, Chemistry, Mathematics
- JEE_ADVANCED: Physics, Chemistry, Mathematics
- NEET: Physics, Chemistry, Biology

Author: Mentor AI Team
Version: 1.0.0

Example Syllabus JSON Structure:
{
  "exam": "JEE_MAIN",
  "subject": "Physics",
  "version": "2024",
  "chapters": [
    {
      "chapter_id": "CH01",
      "chapter_name": "Mechanics",
      "weightage": 15,
      "topics": [
        {
          "topic_id": "T01",
          "topic_name": "Newton's Laws of Motion",
          "difficulty": "medium",
          "weightage": 5,
          "subtopics": [
            {
              "subtopic_id": "ST01",
              "subtopic_name": "First Law of Motion",
              "content": "An object at rest stays at rest...",
              "key_concepts": ["Inertia", "Force"],
              "difficulty": "easy"
            }
          ]
        }
      ]
    }
  ]
}
"""

import os
import json
import logging
import threading
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
SYLLABUS_DATA_DIR = "data/syllabus"
MAX_CHUNK_WORDS = 500  # Maximum words per chunk for embedding
MIN_CHUNK_WORDS = 50   # Minimum words per chunk
CACHE_ENABLED = True

# Global cache and lock
_syllabus_cache: Dict[str, Dict[str, Any]] = {}
_cache_lock = threading.RLock()


# ============================================================================
# ENUMS
# ============================================================================

class ExamType(str, Enum):
    """Supported exam types."""
    JEE_MAIN = "JEE_MAIN"
    JEE_ADVANCED = "JEE_ADVANCED"
    NEET = "NEET"


class SubjectType(str, Enum):
    """Supported subjects."""
    PHYSICS = "Physics"
    CHEMISTRY = "Chemistry"
    MATHEMATICS = "Mathematics"
    BIOLOGY = "Biology"


class DifficultyLevel(str, Enum):
    """Difficulty levels for topics."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Subtopic(BaseModel):
    """Model for subtopic data."""
    
    subtopic_id: str = Field(
        ...,
        description="Unique identifier for subtopic"
    )
    subtopic_name: str = Field(
        ...,
        description="Name of the subtopic"
    )
    content: str = Field(
        ...,
        description="Detailed content of the subtopic"
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="List of key concepts covered"
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM,
        description="Difficulty level of the subtopic"
    )
    formulas: List[str] = Field(
        default_factory=list,
        description="Important formulas (if any)"
    )
    
    class Config:
        use_enum_values = True


class Topic(BaseModel):
    """Model for topic data."""
    
    topic_id: str = Field(
        ...,
        description="Unique identifier for topic"
    )
    topic_name: str = Field(
        ...,
        description="Name of the topic"
    )
    difficulty: DifficultyLevel = Field(
        default=DifficultyLevel.MEDIUM,
        description="Overall difficulty level"
    )
    weightage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weightage in exam (percentage)"
    )
    subtopics: List[Subtopic] = Field(
        default_factory=list,
        description="List of subtopics under this topic"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of the topic"
    )
    
    class Config:
        use_enum_values = True


class Chapter(BaseModel):
    """Model for chapter data."""
    
    chapter_id: str = Field(
        ...,
        description="Unique identifier for chapter"
    )
    chapter_name: str = Field(
        ...,
        description="Name of the chapter"
    )
    weightage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weightage in exam (percentage)"
    )
    topics: List[Topic] = Field(
        default_factory=list,
        description="List of topics in this chapter"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of the chapter"
    )
    
    @validator('weightage')
    def validate_weightage(cls, v):
        """Validate weightage is within reasonable range."""
        if v < 0 or v > 100:
            raise ValueError("Weightage must be between 0 and 100")
        return v


class Syllabus(BaseModel):
    """Model for complete syllabus data."""
    
    exam: ExamType = Field(
        ...,
        description="Exam type (JEE_MAIN, JEE_ADVANCED, NEET)"
    )
    subject: SubjectType = Field(
        ...,
        description="Subject name"
    )
    version: str = Field(
        default="2024",
        description="Syllabus version/year"
    )
    chapters: List[Chapter] = Field(
        default_factory=list,
        description="List of chapters in the syllabus"
    )
    total_weightage: Optional[float] = Field(
        default=None,
        description="Total weightage (should sum to 100)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    class Config:
        use_enum_values = True
    
    @validator('subject')
    def validate_subject_exam_combination(cls, v, values):
        """Validate subject is valid for the exam type."""
        if 'exam' not in values:
            return v
        
        exam = values['exam']
        
        # Biology is only for NEET
        if v == SubjectType.BIOLOGY and exam != ExamType.NEET:
            raise ValueError("Biology is only available for NEET exam")
        
        # Mathematics is not for NEET
        if v == SubjectType.MATHEMATICS and exam == ExamType.NEET:
            raise ValueError("Mathematics is not available for NEET exam")
        
        return v


class TopicChunk(BaseModel):
    """Model for chunked topic data suitable for embedding."""
    
    chunk_id: str = Field(
        ...,
        description="Unique identifier for this chunk"
    )
    exam: str = Field(
        ...,
        description="Exam type"
    )
    subject: str = Field(
        ...,
        description="Subject name"
    )
    chapter_id: str = Field(
        ...,
        description="Chapter identifier"
    )
    chapter_name: str = Field(
        ...,
        description="Chapter name"
    )
    topic_id: str = Field(
        ...,
        description="Topic identifier"
    )
    topic_name: str = Field(
        ...,
        description="Topic name"
    )
    subtopic_id: Optional[str] = Field(
        default=None,
        description="Subtopic identifier (if applicable)"
    )
    subtopic_name: Optional[str] = Field(
        default=None,
        description="Subtopic name (if applicable)"
    )
    content: str = Field(
        ...,
        description="Text content for this chunk"
    )
    word_count: int = Field(
        ...,
        description="Number of words in the content"
    )
    difficulty: str = Field(
        ...,
        description="Difficulty level"
    )
    weightage: float = Field(
        ...,
        description="Weightage in exam"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class SyllabusStats(BaseModel):
    """Statistics about syllabus data."""
    
    exam: str
    subject: str
    total_chapters: int
    total_topics: int
    total_subtopics: int
    total_chunks: int
    average_topic_weightage: float
    difficulty_distribution: Dict[str, int]
    cached: bool


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_syllabus_file_path(exam: str, subject: str) -> str:
    """
    Get the file path for syllabus JSON file.
    
    Args:
        exam: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        subject: Subject name (Physics, Chemistry, Mathematics, Biology)
    
    Returns:
        Path to the syllabus JSON file
    
    Example:
        >>> path = _get_syllabus_file_path("JEE_MAIN", "Physics")
        >>> print(path)
        data/syllabus/JEE_MAIN_Physics.json
    """
    filename = f"{exam}_{subject}.json"
    return os.path.join(SYLLABUS_DATA_DIR, filename)


def _get_cache_key(exam: str, subject: str) -> str:
    """
    Generate cache key for syllabus data.
    
    Args:
        exam: Exam type
        subject: Subject name
    
    Returns:
        Cache key string
    """
    return f"{exam}_{subject}"


def _count_words(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Input text
    
    Returns:
        Number of words
    """
    return len(text.split())


def _validate_exam_subject(exam: str, subject: str) -> Tuple[bool, Optional[str]]:
    """
    Validate exam and subject combination.
    
    Args:
        exam: Exam type
        subject: Subject name
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate exam type
    try:
        exam_type = ExamType(exam)
    except ValueError:
        valid_exams = [e.value for e in ExamType]
        return False, f"Invalid exam type: {exam}. Must be one of {valid_exams}"
    
    # Validate subject type
    try:
        subject_type = SubjectType(subject)
    except ValueError:
        valid_subjects = [s.value for s in SubjectType]
        return False, f"Invalid subject: {subject}. Must be one of {valid_subjects}"
    
    # Validate combination
    if subject == SubjectType.BIOLOGY.value and exam != ExamType.NEET.value:
        return False, "Biology is only available for NEET exam"
    
    if subject == SubjectType.MATHEMATICS.value and exam == ExamType.NEET.value:
        return False, "Mathematics is not available for NEET exam"
    
    return True, None


# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def load_syllabus(exam: str, subject: str, use_cache: bool = True) -> Syllabus:
    """
    Load syllabus data from JSON file with caching.
    
    This function loads syllabus data from JSON files stored in the
    data/syllabus directory. It validates the data using Pydantic models
    and caches the loaded syllabus for faster subsequent access.
    
    Args:
        exam: Exam type (JEE_MAIN, JEE_ADVANCED, NEET)
        subject: Subject name (Physics, Chemistry, Mathematics, Biology)
        use_cache: Whether to use cached data (default: True)
    
    Returns:
        Syllabus model with complete syllabus data
    
    Raises:
        ValueError: If exam/subject combination is invalid
        FileNotFoundError: If syllabus file is not found
        json.JSONDecodeError: If JSON file is invalid
        Exception: If data validation fails
    
    Example:
        >>> syllabus = load_syllabus("JEE_MAIN", "Physics")
        >>> print(f"Loaded {len(syllabus.chapters)} chapters")
        Loaded 15 chapters
        
        >>> # Load NEET Biology
        >>> neet_bio = load_syllabus("NEET", "Biology")
    """
    global _syllabus_cache
    
    try:
        # Validate exam and subject combination
        is_valid, error_msg = _validate_exam_subject(exam, subject)
        if not is_valid:
            logger.error(f"Validation error: {error_msg}")
            raise ValueError(error_msg)
        
        # Check cache first
        cache_key = _get_cache_key(exam, subject)
        if use_cache and CACHE_ENABLED:
            with _cache_lock:
                if cache_key in _syllabus_cache:
                    logger.info(f"Returning cached syllabus for {exam} - {subject}")
                    return Syllabus(**_syllabus_cache[cache_key])
        
        # Get file path
        file_path = _get_syllabus_file_path(exam, subject)
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = (
                f"Syllabus file not found: {file_path}. "
                f"Please ensure syllabus data for {exam} - {subject} exists."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Load JSON file
        logger.info(f"Loading syllabus from: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate and parse with Pydantic
        syllabus = Syllabus(**data)
        
        # Cache the data
        if CACHE_ENABLED:
            with _cache_lock:
                _syllabus_cache[cache_key] = data
                logger.info(f"Cached syllabus for {exam} - {subject}")
        
        logger.info(
            f"Successfully loaded syllabus for {exam} - {subject}: "
            f"{len(syllabus.chapters)} chapters, "
            f"{sum(len(ch.topics) for ch in syllabus.chapters)} topics"
        )
        
        return syllabus
        
    except ValueError as ve:
        logger.error(f"Validation error loading syllabus: {ve}")
        raise
    
    except FileNotFoundError as fnf:
        logger.error(f"File not found: {fnf}")
        raise
    
    except json.JSONDecodeError as jde:
        logger.error(f"Invalid JSON in syllabus file: {jde}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error loading syllabus: {e}")
        logger.exception("Full traceback:")
        raise


def get_topics(exam: str, subject: str, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Get all topics for an exam and subject.
    
    Returns a flattened list of all topics with their metadata including
    chapter information, weightage, and difficulty.
    
    Args:
        exam: Exam type
        subject: Subject name
        use_cache: Whether to use cached syllabus data
    
    Returns:
        List of dictionaries containing topic information
    
    Example:
        >>> topics = get_topics("JEE_MAIN", "Physics")
        >>> for topic in topics[:3]:
        ...     print(f"{topic['topic_name']} - {topic['difficulty']}")
        Newton's Laws of Motion - medium
        Work and Energy - medium
        Rotational Motion - hard
    """
    try:
        # Load syllabus
        syllabus = load_syllabus(exam, subject, use_cache=use_cache)
        
        # Extract all topics with metadata
        topics_list = []
        
        for chapter in syllabus.chapters:
            for topic in chapter.topics:
                topic_dict = {
                    "exam": syllabus.exam,
                    "subject": syllabus.subject,
                    "chapter_id": chapter.chapter_id,
                    "chapter_name": chapter.chapter_name,
                    "chapter_weightage": chapter.weightage,
                    "topic_id": topic.topic_id,
                    "topic_name": topic.topic_name,
                    "topic_weightage": topic.weightage,
                    "difficulty": topic.difficulty,
                    "description": topic.description,
                    "subtopics_count": len(topic.subtopics)
                }
                topics_list.append(topic_dict)
        
        logger.info(f"Retrieved {len(topics_list)} topics for {exam} - {subject}")
        return topics_list
        
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        raise


def chunk_topics(
    exam: str,
    subject: str,
    max_words: int = MAX_CHUNK_WORDS,
    min_words: int = MIN_CHUNK_WORDS,
    use_cache: bool = True
) -> List[TopicChunk]:
    """
    Chunk topics into smaller pieces suitable for embedding generation.
    
    This function breaks down syllabus content into chunks of maximum
    specified word count, preserving context and metadata. Each chunk
    represents a semantically meaningful unit for embedding.
    
    Args:
        exam: Exam type
        subject: Subject name
        max_words: Maximum words per chunk (default: 500)
        min_words: Minimum words per chunk (default: 50)
        use_cache: Whether to use cached syllabus data
    
    Returns:
        List of TopicChunk objects ready for embedding
    
    Example:
        >>> chunks = chunk_topics("JEE_MAIN", "Physics", max_words=300)
        >>> print(f"Created {len(chunks)} chunks")
        Created 450 chunks
        >>> 
        >>> # Check first chunk
        >>> first = chunks[0]
        >>> print(f"Chapter: {first.chapter_name}")
        >>> print(f"Topic: {first.topic_name}")
        >>> print(f"Words: {first.word_count}")
    """
    try:
        # Load syllabus
        syllabus = load_syllabus(exam, subject, use_cache=use_cache)
        
        chunks = []
        chunk_counter = 0
        
        # Iterate through all chapters and topics
        for chapter in syllabus.chapters:
            for topic in chapter.topics:
                # Process each subtopic
                for subtopic in topic.subtopics:
                    content = subtopic.content.strip()
                    
                    # Skip if content is too short
                    word_count = _count_words(content)
                    if word_count < min_words:
                        logger.debug(
                            f"Skipping subtopic {subtopic.subtopic_id}: "
                            f"only {word_count} words (min: {min_words})"
                        )
                        continue
                    
                    # If content is within max words, create single chunk
                    if word_count <= max_words:
                        chunk_counter += 1
                        chunk = TopicChunk(
                            chunk_id=f"{exam}_{subject}_C{chunk_counter:04d}",
                            exam=syllabus.exam,
                            subject=syllabus.subject,
                            chapter_id=chapter.chapter_id,
                            chapter_name=chapter.chapter_name,
                            topic_id=topic.topic_id,
                            topic_name=topic.topic_name,
                            subtopic_id=subtopic.subtopic_id,
                            subtopic_name=subtopic.subtopic_name,
                            content=content,
                            word_count=word_count,
                            difficulty=subtopic.difficulty,
                            weightage=topic.weightage,
                            metadata={
                                "key_concepts": subtopic.key_concepts,
                                "formulas": subtopic.formulas,
                                "chapter_weightage": chapter.weightage
                            }
                        )
                        chunks.append(chunk)
                    
                    else:
                        # Split content into multiple chunks
                        words = content.split()
                        start_idx = 0
                        
                        while start_idx < len(words):
                            # Get chunk of max_words
                            end_idx = min(start_idx + max_words, len(words))
                            chunk_words = words[start_idx:end_idx]
                            chunk_content = ' '.join(chunk_words)
                            
                            chunk_counter += 1
                            chunk = TopicChunk(
                                chunk_id=f"{exam}_{subject}_C{chunk_counter:04d}",
                                exam=syllabus.exam,
                                subject=syllabus.subject,
                                chapter_id=chapter.chapter_id,
                                chapter_name=chapter.chapter_name,
                                topic_id=topic.topic_id,
                                topic_name=topic.topic_name,
                                subtopic_id=subtopic.subtopic_id,
                                subtopic_name=subtopic.subtopic_name,
                                content=chunk_content,
                                word_count=len(chunk_words),
                                difficulty=subtopic.difficulty,
                                weightage=topic.weightage,
                                metadata={
                                    "key_concepts": subtopic.key_concepts,
                                    "formulas": subtopic.formulas,
                                    "chapter_weightage": chapter.weightage,
                                    "part": f"{(start_idx // max_words) + 1}"
                                }
                            )
                            chunks.append(chunk)
                            
                            start_idx = end_idx
        
        logger.info(
            f"Created {len(chunks)} chunks for {exam} - {subject} "
            f"(max_words: {max_words}, min_words: {min_words})"
        )
        
        return chunks
        
    except Exception as e:
        logger.error(f"Error chunking topics: {e}")
        logger.exception("Full traceback:")
        raise


def get_syllabus_stats(exam: str, subject: str, use_cache: bool = True) -> SyllabusStats:
    """
    Get statistics about syllabus data.
    
    Returns comprehensive statistics including chapter count, topic count,
    difficulty distribution, and average weightage.
    
    Args:
        exam: Exam type
        subject: Subject name
        use_cache: Whether to use cached data
    
    Returns:
        SyllabusStats model with statistics
    
    Example:
        >>> stats = get_syllabus_stats("JEE_MAIN", "Physics")
        >>> print(f"Total chapters: {stats.total_chapters}")
        >>> print(f"Total topics: {stats.total_topics}")
        >>> print(f"Difficulty distribution: {stats.difficulty_distribution}")
    """
    try:
        # Load syllabus
        syllabus = load_syllabus(exam, subject, use_cache=use_cache)
        
        # Calculate statistics
        total_chapters = len(syllabus.chapters)
        total_topics = sum(len(ch.topics) for ch in syllabus.chapters)
        total_subtopics = sum(
            len(topic.subtopics)
            for ch in syllabus.chapters
            for topic in ch.topics
        )
        
        # Get chunks count
        chunks = chunk_topics(exam, subject, use_cache=use_cache)
        total_chunks = len(chunks)
        
        # Calculate average weightage
        topic_weightages = [
            topic.weightage
            for ch in syllabus.chapters
            for topic in ch.topics
        ]
        avg_weightage = sum(topic_weightages) / len(topic_weightages) if topic_weightages else 0.0
        
        # Calculate difficulty distribution
        difficulty_dist = {"easy": 0, "medium": 0, "hard": 0}
        for ch in syllabus.chapters:
            for topic in ch.topics:
                for subtopic in topic.subtopics:
                    difficulty_dist[subtopic.difficulty] += 1
        
        # Check if data is from cache
        cache_key = _get_cache_key(exam, subject)
        is_cached = cache_key in _syllabus_cache
        
        stats = SyllabusStats(
            exam=exam,
            subject=subject,
            total_chapters=total_chapters,
            total_topics=total_topics,
            total_subtopics=total_subtopics,
            total_chunks=total_chunks,
            average_topic_weightage=round(avg_weightage, 2),
            difficulty_distribution=difficulty_dist,
            cached=is_cached
        )
        
        logger.info(f"Generated statistics for {exam} - {subject}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting syllabus statistics: {e}")
        raise


def clear_syllabus_cache() -> int:
    """
    Clear the syllabus cache.
    
    Returns:
        Number of cache entries cleared
    
    Example:
        >>> cleared = clear_syllabus_cache()
        >>> print(f"Cleared {cleared} syllabus entries")
    """
    global _syllabus_cache
    
    with _cache_lock:
        count = len(_syllabus_cache)
        _syllabus_cache.clear()
        logger.info(f"Cleared {count} syllabus cache entries")
        return count


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Create data directory if it doesn't exist
os.makedirs(SYLLABUS_DATA_DIR, exist_ok=True)

logger.info("Syllabus service initialized")
logger.info(f"Data directory: {SYLLABUS_DATA_DIR}")
logger.info(f"Max chunk words: {MAX_CHUNK_WORDS}, Min chunk words: {MIN_CHUNK_WORDS}")
logger.info(f"Caching: {'Enabled' if CACHE_ENABLED else 'Disabled'}")
