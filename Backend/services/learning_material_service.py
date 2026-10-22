"""
Learning Material Service

This module provides AI-powered learning material generation and caching
for the Study Center Learning Journey feature in Mentor AI EdTech Platform.

Features:
- Generate comprehensive study notes using Gemini AI
- Create structured mind maps in JSON format
- Produce teaching content with examples
- Implement material caching in Firestore
- Track generation metadata and analytics
- Rate limiting for cost control

Author: Mentor AI Team
Version: 1.0.0
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from models.study_center_models import (
    LearningMaterials, MindMap, TeachingContent
)
from services.gemini_service import GeminiService, get_gemini_service
from utils.firebase_config import get_firestore_client
from firebase_admin import firestore
from utils.study_center_prompts import (
    build_notes_prompt,
    build_mindmap_prompt,
    build_teaching_prompt,
    build_syllabus_context
)

# Configure logging
logger = logging.getLogger(__name__)

# Cache expiration time (30 days)
CACHE_EXPIRY_DAYS = 30

# Rate limiting for AI generation
MAX_GENERATION_REQUESTS_PER_HOUR = 10


class LearningMaterialService:
    """
    Service for generating and managing learning materials.
    
    This service handles AI-powered content generation using Gemini Flash,
    implements caching to optimize token usage, and tracks generation
    metadata for analytics.
    
    Attributes:
        gemini_service: GeminiService instance for AI generation
        db: Firestore database client
        cache_enabled: Whether to use material caching
        rate_limit_enabled: Whether to enforce rate limiting
    
    Example:
        >>> service = LearningMaterialService()
        >>> materials = service.generate_materials("T02", "JEE_MAIN", student_id)
        >>> print(f"Generated materials for {materials.topic_name}")
    """
    
    def __init__(
        self,
        cache_enabled: bool = True,
        rate_limit_enabled: bool = True,
        gemini_service: Optional[GeminiService] = None
    ):
        """
        Initialize LearningMaterialService.
        
        Args:
            cache_enabled: Enable material caching (default: True)
            rate_limit_enabled: Enable rate limiting (default: True)
            gemini_service: Optional GeminiService instance
        """
        logger.info("Initializing LearningMaterialService")
        
        # Initialize Gemini service
        self.gemini_service = gemini_service if gemini_service else get_gemini_service()
        logger.info("Gemini service initialized")
        
        # Initialize Firestore client
        self.db = get_firestore_client()
        logger.info("Firestore client initialized")
        
        # Configuration
        self.cache_enabled = cache_enabled
        self.rate_limit_enabled = rate_limit_enabled
        
        # Rate limiting tracking
        self._generation_requests: Dict[str, List[datetime]] = {}
        
        logger.info(
            f"LearningMaterialService initialized "
            f"(cache={cache_enabled}, rate_limit={rate_limit_enabled})"
        )
    
    def generate_materials(
        self,
        topic_id: str,
        exam_type: str,
        student_id: str,
        material_types: Optional[List[str]] = None
    ) -> LearningMaterials:
        """
        Generate or retrieve learning materials for a topic.
        
        This is the main method for material generation. It handles:
        - Cache checking for all material types
        - AI generation for missing materials
        - Cache storage for newly generated content
        - Rate limiting enforcement
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            student_id: ID of the student requesting materials
            material_types: List of material types to generate
                         (notes, mind_map, teaching_content, all)
        
        Returns:
            LearningMaterials object with all requested materials
        
        Raises:
            ValueError: If topic_id or exam_type is invalid
            Exception: If generation fails after retries
        
        Example:
            >>> service = LearningMaterialService()
            >>> materials = service.generate_materials(
            ...     "T02", "JEE_MAIN", "student_123", ["notes", "mind_map"]
            ... )
            >>> print(f"Generated: {materials.notes is not None}")
        """
        if not topic_id or not exam_type:
            raise ValueError("topic_id and exam_type are required")
        
        if not material_types:
            material_types = ["notes", "mind_map", "teaching_content"]
        
        # Load topic data from syllabus
        topic_data = self._load_topic_data(topic_id, exam_type)
        if not topic_data:
            raise ValueError(f"Topic {topic_id} not found in {exam_type} syllabus")
        
        topic_name = topic_data.get("topic_name", topic_id)
        syllabus_context = build_syllabus_context(topic_data)
        
        logger.info(
            f"Generating materials for topic {topic_id} ({topic_name}) "
            f"for {exam_type}, types: {material_types}"
        )
        
        # Initialize materials object
        materials = LearningMaterials(
            topic_id=topic_id,
            topic_name=topic_name,
            generated_at=datetime.now()
        )
        
        # Check rate limiting
        if self.rate_limit_enabled:
            if not self._check_rate_limit(student_id):
                raise ValueError(
                    f"Rate limit exceeded for student {student_id}. "
                    f"Maximum {MAX_GENERATION_REQUESTS_PER_HOUR} requests per hour."
                )
        
        # Generate each requested material type
        for material_type in material_types:
            try:
                if material_type == "notes":
                    materials.notes = self._generate_or_get_cached(
                        topic_id, exam_type, "notes", syllabus_context
                    )
                
                elif material_type == "mind_map":
                    materials.mind_map = self._generate_or_get_cached_mindmap(
                        topic_id, exam_type, syllabus_context
                    )
                
                elif material_type == "teaching_content":
                    materials.teaching_content = self._generate_or_get_cached_teaching(
                        topic_id, exam_type, topic_data.get("difficulty", "medium")
                    )
                
                logger.info(f"Generated {material_type} for topic {topic_id}")
                
            except Exception as e:
                logger.error(f"Failed to generate {material_type} for {topic_id}: {e}")
                logger.exception("Full traceback:")
                # Continue with other materials even if one fails
        
        # Record generation request for rate limiting
        if self.rate_limit_enabled:
            self._record_generation_request(student_id)
        
        logger.info(f"Material generation completed for topic {topic_id}")
        return materials
    
    def _generate_or_get_cached(
        self,
        topic_id: str,
        exam_type: str,
        material_type: str,
        syllabus_context: str
    ) -> Optional[str]:
        """
        Generate notes or retrieve from cache.
        
        Checks cache first, generates new content if cache miss,
        and stores in cache for future requests.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            material_type: Type of material (notes)
            syllabus_context: Syllabus context for generation
        
        Returns:
            Generated content string or None if generation fails
        """
        # Check cache first
        if self.cache_enabled:
            cached_content = self._get_cached_material(
                topic_id, exam_type, material_type
            )
            if cached_content:
                logger.info(f"Cache hit for {material_type} of topic {topic_id}")
                self._update_cache_access(topic_id, exam_type, material_type)
                return cached_content
        
        # Generate new content
        if material_type == "notes":
            prompt = build_notes_prompt(
                self._get_topic_name(topic_id),
                exam_type,
                syllabus_context
            )
            
            # Generate using Gemini with retry logic
            max_retries = 2
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries + 1):
                try:
                    logger.info(f"Generation attempt {attempt + 1}/{max_retries + 1}")
                    
                    # Generate using Gemini
                    if material_type == "notes":
                        content = self.gemini_service.generate_content(
                            prompt, use_cache=False
                        )
                    else:
                        # For mind maps and teaching content, use questions method
                        response = self.gemini_service.generate_questions(
                            prompt, num_questions=1, use_cache=False
                        )
                        
                        if response and len(response) > 0:
                            content = response[0].question  # Use question field for content
                            break  # Success, exit retry loop
                    
                except Exception as e:
                    logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        logger.error("All generation Attempts failed")
                        content = None
                        break
        
        else:
            content = None
        
        # Cache the generated content
        if content and self.cache_enabled:
            self._cache_material(
                topic_id, exam_type, material_type, content
            )
        
        return content
    
    def _generate_or_get_cached_mindmap(
        self,
        topic_id: str,
        exam_type: str,
        syllabus_context: str
    ) -> Optional[MindMap]:
        """
        Generate mind map or retrieve from cache.
        
        Specialized method for mind map generation with JSON parsing
        and structured object creation.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            syllabus_context: Syllabus context for generation
        
        Returns:
            MindMap object or None if generation fails
        """
        # Check cache first
        if self.cache_enabled:
            cached_mindmap = self._get_cached_mindmap(topic_id, exam_type)
            if cached_mindmap:
                logger.info(f"Cache hit for mindmap of topic {topic_id}")
                self._update_cache_access(topic_id, exam_type, "mind_map")
                return cached_mindmap
        
        # Generate new mind map
        prompt = build_mindmap_prompt(
            self._get_topic_name(topic_id),
            exam_type,
            syllabus_context
        )
        
        try:
            # Generate using Gemini
            response = self.gemini_service.generate_questions(
                prompt, num_questions=1, use_cache=False
            )
            
            if response and len(response) > 0:
                # Parse JSON response
                json_content = response[0].question
                mindmap_structure = json.loads(json_content)
                
                # Create MindMap object
                mindmap = MindMap(
                    mindmap_id=f"mm_{topic_id}_{int(time.time())}",
                    topic_id=topic_id,
                    structure=mindmap_structure,
                    text_representation=self._convert_mindmap_to_text(mindmap_structure),
                    generated_at=datetime.now()
                )
                
                # Cache the mind map
                if self.cache_enabled:
                    self._cache_mindmap(topic_id, exam_type, mindmap)
                
                return mindmap
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse mindmap JSON: {e}")
        except Exception as e:
            logger.error(f"Failed to generate mindmap: {e}")
            logger.exception("Full traceback:")
        
        return None
    
    def _generate_or_get_cached_teaching(
        self,
        topic_id: str,
        exam_type: str,
        difficulty: str
    ) -> Optional[TeachingContent]:
        """
        Generate teaching content or retrieve from cache.
        
        Specialized method for teaching content generation with
        structured sections and examples.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            difficulty: Difficulty level of content
        
        Returns:
            TeachingContent object or None if generation fails
        """
        # Check cache first
        if self.cache_enabled:
            cached_teaching = self._get_cached_teaching(topic_id, exam_type)
            if cached_teaching:
                logger.info(f"Cache hit for teaching content of topic {topic_id}")
                self._update_cache_access(topic_id, exam_type, "teaching_content")
                return cached_teaching
        
        # Generate new teaching content
        prompt = build_teaching_prompt(
            self._get_topic_name(topic_id),
            exam_type,
            difficulty
        )
        
        try:
            # Generate using Gemini
            content = self.gemini_service.generate_content(
                prompt, use_cache=False
            )
            
            if content and len(content.strip()) > 0:
                # Parse teaching content from response
                
                # Create TeachingContent object
                teaching_content = TeachingContent(
                    topic_id=topic_id,
                    introduction=self._extract_section(content, "INTRODUCTION"),
                    key_concepts=self._extract_key_concepts(content),
                    examples=self._extract_examples(content),
                    summary=self._extract_section(content, "SUMMARY"),
                    difficulty_level=difficulty
                )
                
                # Cache the teaching content
                if self.cache_enabled:
                    self._cache_teaching(topic_id, exam_type, teaching_content)
                
                return teaching_content
        
        except Exception as e:
            logger.error(f"Failed to generate teaching content: {e}")
            logger.exception("Full traceback:")
        
        return None
    
    def _load_topic_data(self, topic_id: str, exam_type: str) -> Optional[Dict[str, Any]]:
        """
        Load topic data from syllabus JSON files.
        
        Reads syllabus files from data/syllabus/ directory and
        extracts topic information.
        
        Args:
            topic_id: ID of the topic to load
            exam_type: Type of exam (determines which file to read)
        
        Returns:
            Topic data dictionary or None if not found
        """
        try:
            # Determine which syllabus file to read
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
            
            # Try each subject file to find the topic
            for subject, file_path in subject_files.get(exam_type, {}).items():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        syllabus = json.load(f)
                    
                    # Search through chapters and topics
                    for chapter in syllabus.get("chapters", []):
                        for topic in chapter.get("topics", []):
                            if topic.get("topic_id") == topic_id:
                                return topic
                
                except FileNotFoundError:
                    logger.warning(f"Syllabus file not found: {file_path}")
                    continue
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing syllabus file {file_path}: {e}")
                    continue
            
            logger.warning(f"Topic {topic_id} not found in {exam_type} syllabus")
            return None
        
        except Exception as e:
            logger.error(f"Error loading topic data: {e}")
            logger.exception("Full traceback:")
            return None
    
    def _get_topic_name(self, topic_id: str) -> str:
        """Get topic name from cached data or return topic_id."""
        # This is a simplified version - in production, we'd cache topic data
        return topic_id
    
    def _get_cached_material(
        self,
        topic_id: str,
        exam_type: str,
        material_type: str
    ) -> Optional[str]:
        """
        Retrieve cached material from Firestore.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            material_type: Type of material (notes, teaching_content)
        
        Returns:
            Cached content string or None if not found/expired
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
                return data.get("content")
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached material: {e}")
            return None
    
    def _get_cached_mindmap(
        self,
        topic_id: str,
        exam_type: str
    ) -> Optional[MindMap]:
        """
        Retrieve cached mind map from Firestore.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
        
        Returns:
            Cached MindMap object or None if not found/expired
        """
        try:
            # Query mind_maps collection
            mindmaps_ref = self.db.collection("mind_maps")
            query = mindmaps_ref.where(
                "topic_id", "==", topic_id
            ).where(
                "exam_type", "==", exam_type
            ).where(
                "cache_expires_at", ">", datetime.now()
            )
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                logger.debug(f"Found cached mindmap for {topic_id}")
                return MindMap(**data)
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached mindmap: {e}")
            return None
    
    def _get_cached_teaching(
        self,
        topic_id: str,
        exam_type: str
    ) -> Optional[TeachingContent]:
        """
        Retrieve cached teaching content from Firestore.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
        
        Returns:
            Cached TeachingContent object or None if not found/expired
        """
        try:
            # Query learning_materials collection
            materials_ref = self.db.collection("learning_materials")
            query = materials_ref.where(
                "topic_id", "==", topic_id
            ).where(
                "exam_type", "==", exam_type
            ).where(
                "material_type", "==", "teaching_content"
            ).where(
                "cache_expires_at", ">", datetime.now()
            )
            
            docs = query.limit(1).stream()
            
            for doc in docs:
                data = doc.to_dict()
                content = data.get("content")
                
                # Parse teaching content from cached JSON
                if content:
                    teaching_data = json.loads(content)
                    return TeachingContent(**teaching_data)
            
            return None
        
        except Exception as e:
            logger.error(f"Error retrieving cached teaching: {e}")
            return None
    
    def _cache_material(
        self,
        topic_id: str,
        exam_type: str,
        material_type: str,
        content: str
    ):
        """
        Cache material in Firestore.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            material_type: Type of material
            content: Content to cache
        """
        try:
            # Calculate cache expiry
            cache_expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
            
            # Create document
            material_doc = {
                "material_id": f"mat_{topic_id}_{material_type}_{int(time.time())}",
                "topic_id": topic_id,
                "topic_name": self._get_topic_name(topic_id),
                "exam_type": exam_type,
                "material_type": material_type,
                "content": content,
                "cache_expires_at": cache_expires_at,
                "access_count": 1,
                "last_accessed": datetime.now(),
                "metadata": {
                    "generated_at": datetime.now(),
                    "model_version": "gemini-2.5-flash-lite",
                    "generation_time_ms": 0  # Would track actual generation time
                }
            }
            
            # Store in Firestore
            self.db.collection("learning_materials").add(material_doc)
            logger.debug(f"Cached {material_type} for {topic_id}")
        
        except Exception as e:
            logger.error(f"Error caching material: {e}")
    
    def _cache_mindmap(
        self,
        topic_id: str,
        exam_type: str,
        mindmap: MindMap
    ):
        """
        Cache mind map in Firestore.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            mindmap: MindMap object to cache
        """
        try:
            # Calculate cache expiry
            cache_expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
            
            # Create document
            mindmap_doc = {
                "mindmap_id": mindmap.mindmap_id,
                "topic_id": topic_id,
                "topic_name": self._get_topic_name(topic_id),
                "exam_type": exam_type,
                "structure": mindmap.structure,
                "text_representation": mindmap.text_representation,
                "generated_at": mindmap.generated_at,
                "cache_expires_at": cache_expires_at
            }
            
            # Store in Firestore
            self.db.collection("mind_maps").add(mindmap_doc)
            logger.debug(f"Cached mindmap for {topic_id}")
        
        except Exception as e:
            logger.error(f"Error caching mindmap: {e}")
    
    def _cache_teaching(
        self,
        topic_id: str,
        exam_type: str,
        teaching_content: TeachingContent
    ):
        """
        Cache teaching content in Firestore.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            teaching_content: TeachingContent object to cache
        """
        try:
            # Calculate cache expiry
            cache_expires_at = datetime.now() + timedelta(days=CACHE_EXPIRY_DAYS)
            
            # Create document
            teaching_doc = {
                "material_id": f"mat_{topic_id}_teaching_{int(time.time())}",
                "topic_id": topic_id,
                "topic_name": self._get_topic_name(topic_id),
                "exam_type": exam_type,
                "material_type": "teaching_content",
                "content": teaching_content.model_dump_json(),
                "cache_expires_at": cache_expires_at,
                "access_count": 1,
                "last_accessed": datetime.now()
            }
            
            # Store in Firestore
            self.db.collection("learning_materials").add(teaching_doc)
            logger.debug(f"Cached teaching content for {topic_id}")
        
        except Exception as e:
            logger.error(f"Error caching teaching content: {e}")
    
    def _update_cache_access(
        self,
        topic_id: str,
        exam_type: str,
        material_type: str
    ):
        """
        Update cache access statistics.
        
        Args:
            topic_id: ID of the topic
            exam_type: Type of exam
            material_type: Type of material
        """
        try:
            # Query and update the cached document
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
                # Update access count and timestamp
                doc.reference.update({
                    "access_count": firestore.Increment(1),
                    "last_accessed": datetime.now()
                })
                break
        
        except Exception as e:
            logger.error(f"Error updating cache access: {e}")
    
    def _check_rate_limit(self, student_id: str) -> bool:
        """
        Check if student has exceeded rate limit.
        
        Args:
            student_id: ID of the student
        
        Returns:
            True if within rate limit, False if exceeded
        """
        if not self.rate_limit_enabled:
            return True
        
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        # Get requests in the last hour
        requests = self._generation_requests.get(student_id, [])
        recent_requests = [
            req_time for req_time in requests 
            if req_time > one_hour_ago
        ]
        
        # Update requests list
        self._generation_requests[student_id] = recent_requests
        
        # Check if under limit
        return len(recent_requests) < MAX_GENERATION_REQUESTS_PER_HOUR
    
    def _record_generation_request(self, student_id: str):
        """
        Record a generation request for rate limiting.
        
        Args:
            student_id: ID of the student
        """
        if not self.rate_limit_enabled:
            return
        
        current_time = datetime.now()
        
        # Add to requests list
        if student_id not in self._generation_requests:
            self._generation_requests[student_id] = []
        
        self._generation_requests[student_id].append(current_time)
    
    def _convert_mindmap_to_text(self, structure: Dict[str, Any]) -> str:
        """
        Convert mind map structure to text representation.
        
        Args:
            structure: Mind map structure dictionary
        
        Returns:
            Markdown text representation
        """
        lines = []
        
        # Central concept
        central = structure.get("central_concept", "")
        if central:
            lines.append(f"# {central}")
            lines.append("")
        
        # Main branches
        branches = structure.get("main_branches", [])
        for branch in branches:
            branch_name = branch.get("name", "")
            if branch_name:
                lines.append(f"## {branch_name}")
                
                # Sub-branches
                sub_branches = branch.get("sub_branches", [])
                for sub in sub_branches:
                    lines.append(f"- {sub}")
                
                lines.append("")
        
        # Connections
        connections = structure.get("connections", [])
        if connections:
            lines.append("### Connections")
            for conn in connections:
                from_concept = conn.get("from", "")
                to_concept = conn.get("to", "")
                conn_type = conn.get("type", "")
                lines.append(f"- {from_concept} → {to_concept} ({conn_type})")
        
        return "\n".join(lines)
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """
        Extract a section from generated content.
        
        Args:
            content: Full generated content
            section_name: Name of section to extract
        
        Returns:
            Extracted section content
        """
        lines = content.split('\n')
        section_lines = []
        in_section = False
        
        for line in lines:
            if line.strip().startswith(section_name.upper()):
                in_section = True
                continue
            
            if in_section and line.strip().startswith('#') and not line.strip().startswith(section_name.upper()):
                break
            
            if in_section:
                section_lines.append(line)
        
        return '\n'.join(section_lines).strip()
    
    def _extract_key_concepts(self, content: str) -> List[Dict[str, str]]:
        """
        Extract key concepts from generated content.
        
        Args:
            content: Full generated content
        
        Returns:
            List of key concept dictionaries
        """
        lines = content.split('\n')
        concepts = []
        current_concept = {}
        
        in_concepts = False
        
        for line in lines:
            if line.strip().startswith('KEY CONCEPTS'):
                in_concepts = True
                continue
            
            if in_concepts and line.strip().startswith('#') and not line.strip().startswith('KEY CONCEPTS'):
                break
            
            if in_concepts and line.strip().startswith('-'):
                # Simple extraction - in production, use more sophisticated parsing
                concept_text = line.strip()[1:].strip()
                if ':' in concept_text:
                    name, explanation = concept_text.split(':', 1)
                    current_concept = {
                        "name": name.strip(),
                        "explanation": explanation.strip()
                    }
                    concepts.append(current_concept)
        
        return concepts
    
    def _extract_examples(self, content: str) -> List[Dict[str, str]]:
        """
        Extract worked examples from generated content.
        
        Args:
            content: Full generated content
        
        Returns:
            List of example dictionaries
        """
        lines = content.split('\n')
        examples = []
        current_example = {}
        
        in_examples = False
        
        for line in lines:
            if line.strip().startswith('WORKED EXAMPLES'):
                in_examples = True
                continue
            
            if in_examples and line.strip().startswith('#') and not line.strip().startswith('WORKED EXAMPLES'):
                if current_example:
                    examples.append(current_example)
                break
            
            if in_examples:
                # Simple extraction - in production, use more sophisticated parsing
                if 'Problem:' in line:
                    current_example['problem'] = line.split('Problem:', 1)[1].strip()
                elif 'Solution:' in line:
                    current_example['solution'] = line.split('Solution:', 1)[1].strip()
                elif current_example and 'Key insights:' in line:
                    current_example['key_insights'] = line.split('Key insights:', 1)[1].strip()
                    examples.append(current_example)
                    current_example = {}
        
        return examples


# Singleton instance
_learning_material_service_instance: Optional[LearningMaterialService] = None


def get_learning_material_service(
    cache_enabled: bool = True,
    rate_limit_enabled: bool = True
) -> LearningMaterialService:
    """
    Get or create singleton LearningMaterialService instance.
    
    Args:
        cache_enabled: Enable material caching
        rate_limit_enabled: Enable rate limiting
    
    Returns:
        LearningMaterialService instance
    
    Example:
        >>> service = get_learning_material_service()
        >>> materials = service.generate_materials("T02", "JEE_MAIN", "student_123")
    """
    global _learning_material_service_instance
    
    if _learning_material_service_instance is None:
        logger.info("Creating new LearningMaterialService singleton instance")
        _learning_material_service_instance = LearningMaterialService(
            cache_enabled=cache_enabled,
            rate_limit_enabled=rate_limit_enabled
        )
    
    return _learning_material_service_instance


# Module initialization
logger.info("Learning material service module loaded")