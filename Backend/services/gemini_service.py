"""
Gemini Service for Question Generation

This module provides a high-level service for interacting with Google's Gemini
Flash model to generate exam questions in the Mentor AI EdTech Platform.

Features:
- Question generation with automatic parsing and validation
- Response caching with LRU cache (100 items max)
- Rate limiting (60 requests/minute)
- Automatic retry logic for insufficient questions
- Cost tracking and usage statistics
- Async support for non-blocking operations
- Comprehensive error handling and logging

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.gemini_service import GeminiService
    >>> from utils.prompt_templates import build_prompt
    >>> 
    >>> # Initialize service
    >>> service = GeminiService()
    >>> 
    >>> # Build prompt
    >>> prompt = build_prompt(
    ...     exam_type="JEE_MAIN",
    ...     topic="Calculus",
    ...     syllabus_context="Limits and derivatives...",
    ...     difficulty="medium",
    ...     num_questions=5
    ... )
    >>> 
    >>> # Generate questions
    >>> questions = service.generate_questions(prompt, num_questions=5)
    >>> print(f"Generated {len(questions)} questions")
    >>> 
    >>> # Get usage stats
    >>> stats = service.get_usage_stats()
    >>> print(f"Total cost: ${stats['total_cost']:.4f}")
"""

import time
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from functools import lru_cache
from collections import deque

from models.question_models import Question
from utils.gemini_client import GeminiClient, GeminiClientError
from utils.response_parser import ResponseParser, ResponseParserError

# Configure logging
logger = logging.getLogger(__name__)

# Gemini Flash pricing (as of 2024)
# Input: $0.000125 per 1K tokens (up to 128K context)
# Output: $0.000375 per 1K tokens
GEMINI_INPUT_COST_PER_1K = 0.000125
GEMINI_OUTPUT_COST_PER_1K = 0.000375

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 60
RATE_LIMIT_WINDOW = 60  # seconds

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAY = 2  # seconds


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    pass


class InsufficientQuestionsError(Exception):
    """Raised when generated questions are insufficient."""
    pass


class GeminiService:
    """
    High-level service for Gemini API interactions.
    
    This service manages question generation using Gemini Flash, including
    caching, rate limiting, cost tracking, and error handling.
    
    Attributes:
        client: GeminiClient instance for API calls
        parser: ResponseParser for validating responses
        cache_enabled: Whether to use response caching
        rate_limit_enabled: Whether to enforce rate limiting
        usage_stats: Dictionary tracking API usage and costs
    
    Example:
        >>> service = GeminiService()
        >>> questions = service.generate_questions(prompt, num_questions=5)
        >>> stats = service.get_usage_stats()
        >>> print(f"Total API calls: {stats['total_calls']}")
    """
    
    def __init__(
        self,
        cache_enabled: bool = True,
        rate_limit_enabled: bool = True,
        gemini_client: Optional[GeminiClient] = None,
        parser: Optional[ResponseParser] = None
    ):
        """
        Initialize GeminiService.
        
        Args:
            cache_enabled: Enable response caching (default: True)
            rate_limit_enabled: Enable rate limiting (default: True)
            gemini_client: Optional GeminiClient instance (creates new if None)
            parser: Optional ResponseParser instance (creates new if None)
        """
        logger.info("Initializing GeminiService")
        
        # Initialize Gemini client
        self.client = gemini_client if gemini_client else GeminiClient()
        logger.info("Gemini client initialized")
        
        # Initialize response parser
        self.parser = parser if parser else ResponseParser(
            strict_mode=False,
            log_invalid=True
        )
        logger.info("Response parser initialized")
        
        # Configuration
        self.cache_enabled = cache_enabled
        self.rate_limit_enabled = rate_limit_enabled
        
        # Cache for responses (LRU cache with max 100 items)
        self._response_cache: Dict[str, Tuple[List[Question], datetime]] = {}
        self._cache_max_size = 100
        self._cache_ttl = timedelta(hours=24)  # Cache expires after 24 hours
        
        # Rate limiting
        self._request_timestamps: deque = deque(maxlen=MAX_REQUESTS_PER_MINUTE)
        
        # Usage statistics
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "total_questions_generated": 0,
            "total_questions_valid": 0,
            "total_questions_invalid": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        
        logger.info(
            f"GeminiService initialized (cache={cache_enabled}, "
            f"rate_limit={rate_limit_enabled})"
        )
    
    def generate_questions(
        self,
        prompt: str,
        num_questions: int,
        use_cache: bool = True,
        retry_on_insufficient: bool = True
    ) -> List[Question]:
        """
        Generate questions using Gemini Flash.
        
        This is the main method for question generation. It handles:
        - Prompt validation
        - Cache checking
        - Rate limiting
        - API calls
        - Response parsing
        - Retry logic
        - Cost tracking
        
        Args:
            prompt: Complete prompt for Gemini
            num_questions: Expected number of questions
            use_cache: Use cached response if available (default: True)
            retry_on_insufficient: Retry if insufficient questions (default: True)
        
        Returns:
            List of validated Question objects
        
        Raises:
            RateLimitExceededError: If rate limit is exceeded
            GeminiClientError: If API call fails after retries
            ValueError: If prompt is invalid
        
        Example:
            >>> service = GeminiService()
            >>> prompt = build_prompt("JEE_MAIN", "Calculus", "...", "medium", 5)
            >>> questions = service.generate_questions(prompt, num_questions=5)
            >>> print(f"Generated {len(questions)} questions")
        """
        start_time = time.time()
        
        # Validate prompt
        if not self._validate_prompt(prompt):
            raise ValueError("Invalid prompt: must be non-empty string")
        
        if num_questions < 1 or num_questions > 20:
            raise ValueError("num_questions must be between 1 and 20")
        
        logger.info(f"Generating {num_questions} questions (prompt length: {len(prompt)})")
        
        # Check cache
        if self.cache_enabled and use_cache:
            cache_key = self._get_cache_key(prompt)
            cached_questions = self._get_from_cache(cache_key)
            
            if cached_questions is not None:
                logger.info(f"Cache hit! Returning {len(cached_questions)} cached questions")
                self.usage_stats["cache_hits"] += 1
                
                # Return requested number of questions
                return cached_questions[:num_questions]
        
        self.usage_stats["cache_misses"] += 1
        
        # Check rate limit
        if self.rate_limit_enabled:
            if not self._check_rate_limit():
                wait_time = self._get_rate_limit_wait_time()
                logger.warning(f"Rate limit exceeded. Waiting {wait_time:.1f}s")
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Please wait {wait_time:.1f} seconds"
                )
        
        # Attempt generation with retries
        questions = []
        attempt = 0
        max_attempts = MAX_RETRIES + 1 if retry_on_insufficient else 1
        
        while attempt < max_attempts:
            try:
                attempt += 1
                logger.info(f"Generation attempt {attempt}/{max_attempts}")
                
                # Call Gemini API
                response_text = self._call_gemini_api(prompt)
                
                # Parse response
                questions, parse_stats = self.parser.parse_response(
                    response_text,
                    expected_count=num_questions
                )
                
                # Update statistics
                self.usage_stats["total_questions_generated"] += parse_stats["total"]
                self.usage_stats["total_questions_valid"] += parse_stats["valid"]
                self.usage_stats["total_questions_invalid"] += parse_stats["invalid"]
                
                logger.info(
                    f"Parsed {parse_stats['valid']} valid questions "
                    f"out of {parse_stats['total']}"
                )
                
                # Check if we have enough questions
                if len(questions) >= num_questions:
                    logger.info(f"Successfully generated {len(questions)} questions")
                    break
                
                # Insufficient questions
                if retry_on_insufficient and attempt < max_attempts:
                    logger.warning(
                        f"Insufficient questions: got {len(questions)}, "
                        f"expected {num_questions}. Retrying..."
                    )
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.warning(
                        f"Returning partial results: {len(questions)}/{num_questions}"
                    )
                    break
            
            except GeminiClientError as e:
                logger.error(f"Gemini API error on attempt {attempt}: {e}")
                
                if attempt < max_attempts:
                    logger.info(f"Retrying after {RETRY_DELAY}s...")
                    time.sleep(RETRY_DELAY)
                else:
                    self.usage_stats["failed_calls"] += 1
                    raise
            
            except Exception as e:
                logger.error(f"Unexpected error during generation: {e}")
                logger.exception("Full traceback:")
                self.usage_stats["failed_calls"] += 1
                raise
        
        # Update response time
        response_time = time.time() - start_time
        self._update_response_time(response_time)
        
        logger.info(
            f"Question generation completed in {response_time:.2f}s "
            f"({len(questions)} questions)"
        )
        
        # Cache result
        if self.cache_enabled and len(questions) > 0:
            cache_key = self._get_cache_key(prompt)
            self._add_to_cache(cache_key, questions)
        
        self.usage_stats["successful_calls"] += 1
        
        return questions
    
    def generate_content(
        self,
        prompt: str,
        use_cache: bool = True,
        retry_on_failure: bool = True
    ) -> Optional[str]:
        """
        Generate content using Gemini Flash.
        
        This method is for generating general content (not questions)
        like learning materials, mind maps, teaching content.
        
        Args:
            prompt: Complete prompt for Gemini
            use_cache: Use cached response if available (default: True)
            retry_on_failure: Retry if generation fails (default: True)
        
        Returns:
            Generated content string or None if generation fails
        
        Raises:
            RateLimitExceededError: If rate limit is exceeded
            GeminiClientError: If API call fails after retries
            ValueError: If prompt is invalid
        
        Example:
            >>> service = GeminiService()
            >>> content = service.generate_content(prompt)
            >>> print(f"Generated content length: {len(content)}")
        """
        start_time = time.time()
        
        # Validate prompt
        if not self._validate_prompt(prompt):
            raise ValueError("Invalid prompt: must be non-empty string")
        
        logger.info(f"Generating content (prompt length: {len(prompt)})")
        
        # Check cache
        if self.cache_enabled and use_cache:
            cache_key = self._get_cache_key(prompt)
            # Check content cache first
            content_cache = getattr(self, '_content_cache', {})
            if cache_key in content_cache:
                logger.info("Cache hit! Returning cached content")
                self.usage_stats["cache_hits"] += 1
                return content_cache[cache_key]
        
        self.usage_stats["cache_misses"] += 1
        
        # Check rate limit
        if self.rate_limit_enabled:
            if not self._check_rate_limit():
                wait_time = self._get_rate_limit_wait_time()
                logger.warning(f"Rate limit exceeded. Waiting {wait_time:.1f}s")
                raise RateLimitExceededError(
                    f"Rate limit exceeded. Please wait {wait_time:.1f} seconds"
                )
        
        # Attempt generation with retries
        content = None
        attempt = 0
        max_attempts = MAX_RETRIES + 1 if retry_on_failure else 1
        
        while attempt < max_attempts:
            try:
                attempt += 1
                logger.info(f"Generation attempt {attempt}/{max_attempts}")
                
                # Call Gemini API
                response_text = self._call_gemini_api(prompt)
                
                if response_text and len(response_text.strip()) > 0:
                    content = response_text.strip()
                    logger.info(f"Successfully generated content (length: {len(content)})")
                    break
                    
            except Exception as e:
                logger.warning(f"Generation attempt {attempt} failed: {e}")
                
                if attempt < max_attempts:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error("All generation attempts failed")
                    content = None
                    break
        
        # Update response time
        response_time = time.time() - start_time
        self._update_response_time(response_time)
        
        # Cache result
        if content and self.cache_enabled:
            cache_key = self._get_cache_key(prompt)
            # Store content directly in cache as a string, not as a Question object
            self._content_cache = getattr(self, '_content_cache', {})
            self._content_cache[cache_key] = content
        
        self.usage_stats["successful_calls"] += 1
        
        return content
    
    async def generate_questions_async(
        self,
        prompt: str,
        num_questions: int,
        use_cache: bool = True,
        retry_on_insufficient: bool = True
    ) -> List[Question]:
        """
        Asynchronously generate questions using Gemini Flash.
        
        This is the async version of generate_questions(), allowing for
        non-blocking question generation in async contexts.
        
        Args:
            prompt: Complete prompt for Gemini
            num_questions: Expected number of questions
            use_cache: Use cached response if available (default: True)
            retry_on_insufficient: Retry if insufficient questions (default: True)
        
        Returns:
            List of validated Question objects
        
        Example:
            >>> service = GeminiService()
            >>> questions = await service.generate_questions_async(prompt, 5)
        """
        logger.info(f"Async generating {num_questions} questions")
        
        # Run synchronous method in executor to avoid blocking
        loop = asyncio.get_event_loop()
        questions = await loop.run_in_executor(
            None,
            self.generate_questions,
            prompt,
            num_questions,
            use_cache,
            retry_on_insufficient
        )
        
        return questions
    
    def _call_gemini_api(self, prompt: str) -> str:
        """
        Call Gemini API and track usage.
        
        Args:
            prompt: Prompt to send to Gemini
        
        Returns:
            Response text from Gemini
        
        Raises:
            GeminiClientError: If API call fails
        """
        logger.debug(f"Calling Gemini API (prompt length: {len(prompt)})")
        
        # Update rate limiting
        self._record_request()
        
        # Estimate input tokens (rough: 1 token ≈ 4 characters)
        input_tokens = len(prompt) // 4
        
        # Call API
        try:
            response_text = self.client.generate_content(prompt)
            
            # Estimate output tokens
            output_tokens = len(response_text) // 4
            
            # Update statistics
            self.usage_stats["total_calls"] += 1
            self.usage_stats["total_input_tokens"] += input_tokens
            self.usage_stats["total_output_tokens"] += output_tokens
            
            # Calculate and track cost
            cost = self._calculate_cost(input_tokens, output_tokens)
            self.usage_stats["total_cost"] += cost
            
            logger.info(
                f"API call successful. Tokens: {input_tokens} in, {output_tokens} out. "
                f"Cost: ${cost:.6f}"
            )
            
            return response_text
        
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _validate_prompt(self, prompt: str) -> bool:
        """
        Validate prompt before sending to API.
        
        Args:
            prompt: Prompt to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not prompt or not isinstance(prompt, str):
            return False
        
        if not prompt.strip():
            return False
        
        # Check minimum length
        if len(prompt) < 100:
            logger.warning("Prompt is very short (< 100 chars)")
        
        # Check maximum length (Gemini Flash supports up to 1M tokens ≈ 4M chars)
        max_chars = 500000  # 500K chars as a safe limit
        if len(prompt) > max_chars:
            logger.error(f"Prompt too long: {len(prompt)} > {max_chars}")
            return False
        
        return True
    
    def _check_rate_limit(self) -> bool:
        """
        Check if rate limit is exceeded.
        
        Returns:
            True if within rate limit, False if exceeded
        """
        if not self.rate_limit_enabled:
            return True
        
        current_time = time.time()
        
        # Remove timestamps older than rate limit window
        while self._request_timestamps and \
              current_time - self._request_timestamps[0] > RATE_LIMIT_WINDOW:
            self._request_timestamps.popleft()
        
        # Check if we're at the limit
        if len(self._request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            return False
        
        return True
    
    def _get_rate_limit_wait_time(self) -> float:
        """
        Calculate wait time until rate limit resets.
        
        Returns:
            Wait time in seconds
        """
        if not self._request_timestamps:
            return 0.0
        
        current_time = time.time()
        oldest_request = self._request_timestamps[0]
        elapsed = current_time - oldest_request
        
        return max(0.0, RATE_LIMIT_WINDOW - elapsed)
    
    def _record_request(self):
        """Record a new API request for rate limiting."""
        if self.rate_limit_enabled:
            self._request_timestamps.append(time.time())
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for a Gemini API call.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Cost in USD
        
        Example:
            >>> service = GeminiService()
            >>> cost = service._calculate_cost(1000, 500)
            >>> print(f"${cost:.6f}")
        """
        input_cost = (input_tokens / 1000.0) * GEMINI_INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000.0) * GEMINI_OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost
        
        return total_cost
    
    def _get_cache_key(self, prompt: str) -> str:
        """
        Generate cache key from prompt.
        
        Args:
            prompt: Prompt text
        
        Returns:
            SHA-256 hash of prompt
        """
        return hashlib.sha256(prompt.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Question]]:
        """
        Retrieve questions from cache.
        
        Args:
            cache_key: Cache key
        
        Returns:
            List of questions if cached and not expired, None otherwise
        """
        if cache_key not in self._response_cache:
            return None
        
        questions, timestamp = self._response_cache[cache_key]
        
        # Check if cache is expired
        if datetime.now() - timestamp > self._cache_ttl:
            logger.debug(f"Cache entry expired: {cache_key}")
            del self._response_cache[cache_key]
            return None
        
        logger.debug(f"Cache hit: {cache_key}")
        return questions
    
    def _add_to_cache(self, cache_key: str, questions: List[Question]):
        """
        Add questions to cache.
        
        Implements LRU eviction when cache is full.
        
        Args:
            cache_key: Cache key
            questions: Questions to cache
        """
        # Evict oldest entry if cache is full
        if len(self._response_cache) >= self._cache_max_size:
            # Find oldest entry
            oldest_key = min(
                self._response_cache.keys(),
                key=lambda k: self._response_cache[k][1]
            )
            logger.debug(f"Cache full, evicting: {oldest_key}")
            del self._response_cache[oldest_key]
        
        self._response_cache[cache_key] = (questions, datetime.now())
        logger.debug(f"Added to cache: {cache_key}")
    
    def _update_response_time(self, response_time: float):
        """
        Update average response time statistics.
        
        Args:
            response_time: Response time in seconds
        """
        total_calls = self.usage_stats["successful_calls"] + 1
        self.usage_stats["total_response_time"] += response_time
        self.usage_stats["average_response_time"] = (
            self.usage_stats["total_response_time"] / total_calls
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics.
        
        Returns:
            Dictionary with usage statistics including:
            - API calls (total, successful, failed)
            - Cache performance (hits, misses, hit rate)
            - Token usage (input, output, total)
            - Cost tracking (total, per question)
            - Question statistics (generated, valid, invalid)
            - Performance metrics (response time)
        
        Example:
            >>> service = GeminiService()
            >>> # ... generate questions ...
            >>> stats = service.get_usage_stats()
            >>> print(f"Total cost: ${stats['total_cost']:.4f}")
            >>> print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
        """
        stats = dict(self.usage_stats)
        
        # Calculate derived metrics
        total_cache_attempts = stats["cache_hits"] + stats["cache_misses"]
        stats["cache_hit_rate"] = (
            stats["cache_hits"] / total_cache_attempts
            if total_cache_attempts > 0 else 0.0
        )
        
        stats["total_tokens"] = stats["total_input_tokens"] + stats["total_output_tokens"]
        
        stats["cost_per_question"] = (
            stats["total_cost"] / stats["total_questions_valid"]
            if stats["total_questions_valid"] > 0 else 0.0
        )
        
        stats["validation_rate"] = (
            stats["total_questions_valid"] / stats["total_questions_generated"]
            if stats["total_questions_generated"] > 0 else 0.0
        )
        
        return stats
    
    def reset_usage_stats(self):
        """
        Reset all usage statistics.
        
        Useful for testing or periodic stat collection.
        
        Example:
            >>> service = GeminiService()
            >>> # ... generate questions ...
            >>> stats = service.get_usage_stats()
            >>> # Save stats somewhere
            >>> service.reset_usage_stats()
        """
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "total_questions_generated": 0,
            "total_questions_valid": 0,
            "total_questions_invalid": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        logger.info("Usage statistics reset")
    
    def clear_cache(self):
        """
        Clear the response cache.
        
        Example:
            >>> service = GeminiService()
            >>> service.clear_cache()
        """
        self._response_cache.clear()
        logger.info("Response cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache.
        
        Returns:
            Dictionary with cache statistics
        
        Example:
            >>> service = GeminiService()
            >>> cache_info = service.get_cache_info()
            >>> print(f"Cache size: {cache_info['size']}/{cache_info['max_size']}")
        """
        return {
            "size": len(self._response_cache),
            "max_size": self._cache_max_size,
            "ttl_hours": self._cache_ttl.total_seconds() / 3600,
            "enabled": self.cache_enabled
        }


# Singleton instance (optional)
_gemini_service_instance: Optional[GeminiService] = None


def get_gemini_service(
    cache_enabled: bool = True,
    rate_limit_enabled: bool = True
) -> GeminiService:
    """
    Get or create singleton GeminiService instance.
    
    Args:
        cache_enabled: Enable response caching
        rate_limit_enabled: Enable rate limiting
    
    Returns:
        GeminiService instance
    
    Example:
        >>> service = get_gemini_service()
        >>> questions = service.generate_questions(prompt, 5)
    """
    global _gemini_service_instance
    
    if _gemini_service_instance is None:
        logger.info("Creating new GeminiService singleton instance")
        _gemini_service_instance = GeminiService(
            cache_enabled=cache_enabled,
            rate_limit_enabled=rate_limit_enabled
        )
    
    return _gemini_service_instance


# Module initialization
logger.info("Gemini service module loaded")
logger.info(f"Rate limit: {MAX_REQUESTS_PER_MINUTE} requests per {RATE_LIMIT_WINDOW}s")
logger.info(f"Pricing: ${GEMINI_INPUT_COST_PER_1K}/1K input, ${GEMINI_OUTPUT_COST_PER_1K}/1K output")
