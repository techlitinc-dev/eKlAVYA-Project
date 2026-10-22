"""
Gemini Analytics Service for AI-Powered Test Performance Analysis - Mentor AI Platform.

This module provides a service for generating educational analytics using Google's
Gemini Flash model. It analyzes test performance and generates actionable insights
with study recommendations.

Features:
- Analytics generation with structured JSON output
- Retry logic with exponential backoff
- Response validation and parsing
- Comprehensive error handling
- Timeout management
- Request/response logging
- Cost tracking and usage statistics
- Fallback strategies for partial failures

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from services.gemini_analytics_service import GeminiAnalyticsService
    >>> 
    >>> # Initialize service
    >>> service = GeminiAnalyticsService()
    >>> 
    >>> # Generate analytics
    >>> analytics = service.generate_analytics(
    ...     context=formatted_context,
    ...     exam_type="JEE_MAIN",
    ...     student_name="Priya"
    ... )
    >>> 
    >>> # Check usage stats
    >>> stats = service.get_usage_stats()
    >>> print(f"Total cost: ${stats['total_cost']:.4f}")
"""

import os
import json
import time
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, Literal
from functools import wraps

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from google.api_core import exceptions as google_exceptions

from utils.analytics_prompt_templates import (
    build_analytics_prompt,
    build_quick_analytics_prompt,
    validate_analytics_output,
    AnalyticsPromptError
)

# Configure logging
logger = logging.getLogger(__name__)

# Gemini Flash pricing (as of 2024)
# Input: $0.000125 per 1K tokens (up to 128K context)
# Output: $0.000375 per 1K tokens
GEMINI_INPUT_COST_PER_1K = 0.000125
GEMINI_OUTPUT_COST_PER_1K = 0.000375

# API configuration
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_FACTOR = 2  # exponential backoff

# Generation parameters (aligned with project memory)
GENERATION_CONFIG = {
    "temperature": 0.7,  # Balanced creativity
    "top_p": 0.9,
    "top_k": 40,
    "max_output_tokens": 2048,
    "response_mime_type": "application/json"
}

# Type definitions
ExamType = Literal["JEE_MAIN", "JEE_ADVANCED", "NEET"]


class GeminiAnalyticsError(Exception):
    """Base exception for Gemini Analytics Service errors."""
    pass


class AnalyticsAPIError(GeminiAnalyticsError):
    """Exception raised for API-related errors."""
    pass


class AnalyticsParsingError(GeminiAnalyticsError):
    """Exception raised for response parsing errors."""
    pass


class AnalyticsValidationError(GeminiAnalyticsError):
    """Exception raised for response validation errors."""
    pass


class AnalyticsTimeoutError(GeminiAnalyticsError):
    """Exception raised when API call times out."""
    pass


def log_execution_time(func):
    """Decorator to log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {elapsed_time:.2f}s")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed_time:.2f}s: {str(e)}")
            raise
    return wrapper


class GeminiAnalyticsService:
    """
    Service for generating AI-powered educational analytics using Gemini Flash.
    
    This service manages analytics generation with robust error handling,
    retry logic, validation, and cost tracking.
    
    Attributes:
        model: Gemini Flash model instance
        generation_config: Model generation configuration
        timeout: Request timeout in seconds
        usage_stats: Dictionary tracking API usage and costs
    
    Example:
        >>> service = GeminiAnalyticsService()
        >>> analytics = service.generate_analytics(context, "JEE_MAIN")
        >>> print(f"Strengths: {len(analytics['strengths'])}")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        model_name: str = "gemini-2.5-flash-lite"
    ):
        """
        Initialize Gemini Analytics Service.
        
        Args:
            api_key: Google API key (reads from GOOGLE_API_KEY env if None)
            timeout: Request timeout in seconds (default: 30)
            model_name: Gemini model name (default: gemini-2.5-flash-lite)
        
        Raises:
            ValueError: If API key is not provided or found in environment
        """
        logger.info("Initializing GeminiAnalyticsService")
        
        # Get API key
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Google API key not provided. Set GOOGLE_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        # Configure Gemini
        try:
            genai.configure(api_key=self.api_key)
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {str(e)}")
            raise
        
        # Initialize model
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        logger.info(f"Gemini model initialized: {model_name}")
        
        # Generation configuration
        self.generation_config = GenerationConfig(**GENERATION_CONFIG)
        
        # Request configuration
        self.timeout = timeout
        
        # Usage statistics
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "validation_errors": 0,
            "parsing_errors": 0,
            "api_errors": 0,
            "timeout_errors": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        
        logger.info(
            f"GeminiAnalyticsService initialized (timeout={timeout}s, "
            f"model={model_name})"
        )
    
    @log_execution_time
    def generate_analytics(
        self,
        context: str,
        exam_type: ExamType = "JEE_MAIN",
        student_name: Optional[str] = None,
        include_examples: bool = True,
        max_retries: int = MAX_RETRIES,
        return_partial: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive analytics from test performance context.
        
        This is the main method for analytics generation. It handles:
        - Prompt building
        - API calls with retry logic
        - Response parsing and validation
        - Error handling with fallback strategies
        - Usage tracking
        
        Args:
            context: Formatted test performance context
            exam_type: Type of exam (JEE_MAIN, JEE_ADVANCED, NEET)
            student_name: Optional student name for personalization
            include_examples: Include example analytics in prompt
            max_retries: Maximum retry attempts (default: 3)
            return_partial: Return partial results on validation errors
        
        Returns:
            Dictionary containing analytics with structure:
            {
                "strengths": [...],
                "weaknesses": [...],
                "learning_patterns": [...],
                "overall_assessment": "...",
                "study_strategy": "...",
                "metadata": {
                    "generated_at": "...",
                    "exam_type": "...",
                    "tokens_used": {...},
                    "generation_time": ...
                }
            }
        
        Raises:
            GeminiAnalyticsError: If generation fails after all retries
            ValueError: If context is empty or invalid
        
        Example:
            >>> analytics = service.generate_analytics(
            ...     context=test_context,
            ...     exam_type="JEE_MAIN",
            ...     student_name="Rahul"
            ... )
        """
        if not context or not context.strip():
            raise ValueError("Context cannot be empty")
        
        logger.info(
            f"Starting analytics generation for {exam_type}"
            f"{f' (student: {student_name})' if student_name else ''}"
        )
        
        start_time = time.time()
        self.usage_stats["total_calls"] += 1
        
        try:
            # Build prompt
            prompt = self._build_prompt(
                context=context,
                exam_type=exam_type,
                student_name=student_name,
                include_examples=include_examples
            )
            
            logger.info(f"Prompt built: {len(prompt)} characters (~{len(prompt)//4} tokens)")
            
            # Call API with retry logic
            response_text, tokens_used = self._call_api_with_retry(
                prompt=prompt,
                max_retries=max_retries
            )
            
            # Parse and validate response
            analytics = self._parse_and_validate_response(
                response_text=response_text,
                return_partial=return_partial
            )
            
            # Add metadata
            generation_time = time.time() - start_time
            analytics["metadata"] = {
                "generated_at": datetime.utcnow().isoformat(),
                "exam_type": exam_type,
                "student_name": student_name,
                "tokens_used": tokens_used,
                "generation_time": generation_time,
                "model": self.model_name
            }
            
            # Update statistics
            self._update_usage_stats(
                tokens_used=tokens_used,
                response_time=generation_time,
                success=True
            )
            
            logger.info(
                f"Analytics generated successfully in {generation_time:.2f}s "
                f"({tokens_used['total_tokens']} tokens)"
            )
            
            return analytics
            
        except Exception as e:
            generation_time = time.time() - start_time
            self._update_usage_stats(
                tokens_used=None,
                response_time=generation_time,
                success=False
            )
            logger.error(f"Analytics generation failed: {str(e)}")
            raise
    
    def _build_prompt(
        self,
        context: str,
        exam_type: ExamType,
        student_name: Optional[str],
        include_examples: bool
    ) -> str:
        """Build analytics prompt using template."""
        try:
            if include_examples:
                prompt = build_analytics_prompt(
                    context=context,
                    exam_type=exam_type,
                    student_name=student_name,
                    include_examples=True
                )
            else:
                prompt = build_quick_analytics_prompt(
                    context=context,
                    exam_type=exam_type
                )
            
            logger.debug("Prompt built successfully")
            return prompt
            
        except AnalyticsPromptError as e:
            logger.error(f"Failed to build prompt: {str(e)}")
            raise ValueError(f"Invalid context or exam type: {str(e)}")
    
    def _call_api_with_retry(
        self,
        prompt: str,
        max_retries: int
    ) -> tuple[str, Dict[str, int]]:
        """
        Call Gemini API with exponential backoff retry logic.
        
        Args:
            prompt: Complete prompt for Gemini
            max_retries: Maximum retry attempts
        
        Returns:
            Tuple of (response_text, tokens_used)
        
        Raises:
            AnalyticsAPIError: If API call fails after all retries
            AnalyticsTimeoutError: If API call times out
        """
        retry_delay = INITIAL_RETRY_DELAY
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"API call attempt {attempt + 1}/{max_retries}")
                
                # Make API call with timeout
                response = self.model.generate_content(
                    prompt,
                    generation_config=self.generation_config,
                    request_options={"timeout": self.timeout}
                )
                
                # Extract response text
                if not response.text:
                    raise AnalyticsAPIError("Empty response from Gemini API")
                
                response_text = response.text.strip()
                
                # Calculate token usage (estimate if not available)
                tokens_used = self._calculate_tokens(prompt, response_text, response)
                
                logger.info(
                    f"API call successful: {tokens_used['total_tokens']} tokens used"
                )
                
                return response_text, tokens_used
                
            except google_exceptions.DeadlineExceeded as e:
                last_error = e
                self.usage_stats["timeout_errors"] += 1
                logger.warning(f"API call timeout on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                else:
                    raise AnalyticsTimeoutError(
                        f"API call timed out after {max_retries} attempts"
                    )
            
            except google_exceptions.ResourceExhausted as e:
                last_error = e
                self.usage_stats["api_errors"] += 1
                logger.warning(f"Rate limit exceeded on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries - 1:
                    # Longer delay for rate limits
                    rate_limit_delay = retry_delay * 2
                    logger.info(f"Waiting {rate_limit_delay}s for rate limit...")
                    time.sleep(rate_limit_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                else:
                    raise AnalyticsAPIError(
                        f"Rate limit exceeded after {max_retries} attempts"
                    )
            
            except google_exceptions.GoogleAPIError as e:
                last_error = e
                self.usage_stats["api_errors"] += 1
                logger.warning(f"API error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                else:
                    raise AnalyticsAPIError(
                        f"API call failed after {max_retries} attempts: {str(e)}"
                    )
            
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Retrying after {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= RETRY_BACKOFF_FACTOR
                else:
                    raise AnalyticsAPIError(
                        f"Unexpected error after {max_retries} attempts: {str(e)}"
                    )
        
        # Should not reach here, but just in case
        raise AnalyticsAPIError(f"API call failed: {str(last_error)}")
    
    def _parse_and_validate_response(
        self,
        response_text: str,
        return_partial: bool
    ) -> Dict[str, Any]:
        """
        Parse and validate Gemini response.
        
        Args:
            response_text: Raw response text from Gemini
            return_partial: Return partial results on validation errors
        
        Returns:
            Validated analytics dictionary
        
        Raises:
            AnalyticsParsingError: If JSON parsing fails
            AnalyticsValidationError: If validation fails and return_partial=False
        """
        try:
            # Try to parse JSON directly
            analytics = json.loads(response_text)
            logger.debug("Response parsed successfully")
            
        except json.JSONDecodeError as e:
            # Try to extract JSON from text (sometimes wrapped in markdown)
            logger.warning(f"Direct JSON parse failed: {str(e)}, attempting extraction")
            analytics = self._extract_json_from_text(response_text)
            
            if analytics is None:
                self.usage_stats["parsing_errors"] += 1
                raise AnalyticsParsingError(
                    f"Failed to parse JSON response: {str(e)}\n"
                    f"Response: {response_text[:500]}..."
                )
        
        # Validate response structure
        is_valid, error_message = validate_analytics_output(analytics)
        
        if not is_valid:
            self.usage_stats["validation_errors"] += 1
            logger.warning(f"Validation failed: {error_message}")
            
            if return_partial:
                # Return partial results with validation error
                logger.info("Returning partial results despite validation error")
                analytics["validation_error"] = error_message
                analytics["is_partial"] = True
            else:
                raise AnalyticsValidationError(
                    f"Response validation failed: {error_message}"
                )
        else:
            logger.debug("Response validated successfully")
            analytics["is_partial"] = False
        
        return analytics
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON from text that may contain markdown or extra content.
        
        Args:
            text: Text potentially containing JSON
        
        Returns:
            Parsed JSON dictionary or None if extraction fails
        """
        # Remove markdown code blocks
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _calculate_tokens(
        self,
        prompt: str,
        response_text: str,
        response: Any
    ) -> Dict[str, int]:
        """
        Calculate token usage from API response.
        
        Args:
            prompt: Input prompt
            response_text: Response text
            response: Gemini API response object
        
        Returns:
            Dictionary with token counts and cost
        """
        # Try to get actual token counts from response
        input_tokens = 0
        output_tokens = 0
        
        try:
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
        except:
            # Estimate if not available (rough approximation: 4 chars = 1 token)
            input_tokens = len(prompt) // 4
            output_tokens = len(response_text) // 4
            logger.debug("Using estimated token counts")
        
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * GEMINI_INPUT_COST_PER_1K
        output_cost = (output_tokens / 1000) * GEMINI_OUTPUT_COST_PER_1K
        total_cost = input_cost + output_cost
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }
    
    def _update_usage_stats(
        self,
        tokens_used: Optional[Dict[str, int]],
        response_time: float,
        success: bool
    ):
        """Update usage statistics."""
        if success:
            self.usage_stats["successful_calls"] += 1
        else:
            self.usage_stats["failed_calls"] += 1
        
        if tokens_used:
            self.usage_stats["total_input_tokens"] += tokens_used["input_tokens"]
            self.usage_stats["total_output_tokens"] += tokens_used["output_tokens"]
            self.usage_stats["total_cost"] += tokens_used["total_cost"]
        
        # Update average response time
        self.usage_stats["total_response_time"] += response_time
        total_calls = self.usage_stats["total_calls"]
        self.usage_stats["average_response_time"] = (
            self.usage_stats["total_response_time"] / total_calls
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get current usage statistics.
        
        Returns:
            Dictionary containing usage statistics
        
        Example:
            >>> stats = service.get_usage_stats()
            >>> print(f"Total cost: ${stats['total_cost']:.4f}")
            >>> print(f"Success rate: {stats['success_rate']:.1%}")
        """
        total_calls = self.usage_stats["total_calls"]
        successful_calls = self.usage_stats["successful_calls"]
        
        stats = self.usage_stats.copy()
        
        # Add calculated metrics
        stats["success_rate"] = (
            successful_calls / total_calls if total_calls > 0 else 0.0
        )
        stats["failure_rate"] = (
            self.usage_stats["failed_calls"] / total_calls if total_calls > 0 else 0.0
        )
        stats["average_tokens_per_call"] = (
            (self.usage_stats["total_input_tokens"] + self.usage_stats["total_output_tokens"]) 
            / total_calls if total_calls > 0 else 0
        )
        stats["average_cost_per_call"] = (
            self.usage_stats["total_cost"] / total_calls if total_calls > 0 else 0.0
        )
        
        return stats
    
    def reset_usage_stats(self):
        """Reset all usage statistics to zero."""
        logger.info("Resetting usage statistics")
        
        self.usage_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "validation_errors": 0,
            "parsing_errors": 0,
            "api_errors": 0,
            "timeout_errors": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0.0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
    
    def test_connection(self) -> bool:
        """
        Test connection to Gemini API.
        
        Returns:
            True if connection successful, False otherwise
        
        Example:
            >>> if service.test_connection():
            ...     print("Connection OK")
        """
        try:
            logger.info("Testing Gemini API connection...")
            
            test_prompt = "Respond with: OK"
            response = self.model.generate_content(
                test_prompt,
                generation_config=GenerationConfig(
                    temperature=0,
                    max_output_tokens=10
                ),
                request_options={"timeout": 10}
            )
            
            if response.text:
                logger.info("Connection test successful")
                return True
            else:
                logger.warning("Connection test returned empty response")
                return False
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
