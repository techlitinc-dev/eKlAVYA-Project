"""
Gemini Flash Client Module

This module provides a client for interacting with Google's Gemini 1.5 Flash model
through Vertex AI for the Mentor AI EdTech Platform. It handles initialization,
configuration, content generation, and error handling.

Features:
- Singleton pattern for client initialization
- Gemini 2.5 Flash Lite model (gemini-2.5-flash-lite)
- Configurable generation parameters
- Retry logic with exponential backoff
- Comprehensive error handling
- Support for both sync and async operations
- Environment-based configuration

Author: Mentor AI Team
Version: 1.0.0

Example Usage:
    >>> from utils.gemini_client import GeminiClient
    >>> 
    >>> # Initialize client
    >>> client = GeminiClient()
    >>> 
    >>> # Generate content
    >>> response = client.generate_content(
    ...     prompt="Explain Newton's laws of motion in simple terms"
    ... )
    >>> print(response)
    >>> 
    >>> # Async generation
    >>> import asyncio
    >>> async def generate():
    ...     response = await client.generate_content_async(
    ...         prompt="Create 5 physics questions about momentum"
    ...     )
    ...     return response
    >>> asyncio.run(generate())
"""

import os
import logging
import time
import asyncio
from typing import Optional, Dict, Any, List
from functools import wraps

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Constants
# Default model: cheapest Gemini tier. gemini-2.5-flash-lite ($0.10/M in,
# $0.40/M out) is gated for newer API keys ("no longer available to new
# users"); override with GEMINI_MODEL, e.g. gemini-3.5-flash-lite.
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_TOP_K = 40
DEFAULT_MAX_OUTPUT_TOKENS = 2048
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_FACTOR = 2

# Global client cache
_gemini_client_cache: Optional[Any] = None
_gemini_initialized: bool = False


class GeminiClientError(Exception):
    """Base exception for Gemini client errors."""
    pass


class GeminiQuotaExceededError(GeminiClientError):
    """Raised when API quota is exceeded."""
    pass


class GeminiInvalidArgumentError(GeminiClientError):
    """Raised when invalid arguments are provided."""
    pass


class GeminiServiceUnavailableError(GeminiClientError):
    """Raised when Gemini service is unavailable."""
    pass


def retry_with_backoff(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """
    Decorator to retry functions with exponential backoff.
    
    This decorator implements exponential backoff retry logic for functions
    that may experience transient API failures.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        >>> @retry_with_backoff(max_retries=3, delay=1)
        >>> def api_call():
        ...     # Make API call
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_message = str(e).lower()
                    
                    # Check if it's a retryable error
                    is_retryable = any(
                        keyword in error_message
                        for keyword in [
                            "timeout", "temporarily", "unavailable",
                            "503", "429", "deadline", "resource exhausted"
                        ]
                    )
                    
                    if not is_retryable or attempt == max_retries - 1:
                        # Don't retry non-transient errors or on last attempt
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay} seconds..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= RETRY_BACKOFF_FACTOR
            
            # If all retries failed, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


class GeminiClient:
    """
    Client for interacting with Google's Gemini 1.5 Flash model via Vertex AI.
    
    This class provides a unified interface for generating content using the
    Gemini Flash model, with built-in error handling, retry logic, and
    configuration management.
    
    Attributes:
        project_id: Google Cloud project ID
        location: Google Cloud region
        model_name: Gemini model name (default: gemini-2.5-flash-lite)
        temperature: Sampling temperature (0.0 to 1.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        max_output_tokens: Maximum tokens to generate
    
    Example:
        >>> client = GeminiClient()
        >>> response = client.generate_content("Explain photosynthesis")
        >>> print(response)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        top_k: int = DEFAULT_TOP_K,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    ):
        """
        Initialize Gemini client with configuration.
        
        Args:
            project_id: Google Cloud project ID (default: from GOOGLE_CLOUD_PROJECT env)
            location: Google Cloud region (default: from GOOGLE_CLOUD_LOCATION env)
            model_name: Gemini model name (default: gemini-2.5-flash-lite)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            top_p: Nucleus sampling parameter (default: 0.9)
            top_k: Top-k sampling parameter (default: 40)
            max_output_tokens: Maximum tokens to generate (default: 2048)
        
        Raises:
            ValueError: If project_id or location is not provided
            ImportError: If required libraries are not installed
            Exception: If client initialization fails
        """
        global _gemini_client_cache, _gemini_initialized
        
        logger.info("Initializing Gemini Flash client")
        
        # Import Google Generative AI SDK (simpler than Vertex AI)
        try:
            import google.generativeai as genai
            self._genai = genai
            self._google_exceptions = None  # Not needed for direct API
        except ImportError as e:
            error_msg = (
                "google-generativeai package is not installed. "
                "Please install it using: pip install google-generativeai"
            )
            logger.error(error_msg)
            raise ImportError(error_msg) from e
        
        # Get API key from environment
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            error_msg = (
                "GOOGLE_API_KEY environment variable is not set. "
                "Please get your API key from https://makersuite.google.com/app/apikey "
                "and add it to your .env file."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Store configuration
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.max_output_tokens = max_output_tokens
        
        logger.info(f"Gemini configuration: model={model_name}, API key={'*' * 10}...")
        
        # Configure Gemini API
        try:
            self._genai.configure(api_key=api_key)
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise
        
        # Create generation config
        self.generation_config = {
            'temperature': temperature,
            'top_p': top_p,
            'top_k': top_k,
            'max_output_tokens': max_output_tokens
        }
        
        # Initialize model
        try:
            self.model = self._genai.GenerativeModel(
                model_name=model_name,
                generation_config=self.generation_config
            )
            logger.info(f"Gemini model '{model_name}' initialized successfully")
            _gemini_initialized = True
            _gemini_client_cache = self
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            raise
    
    @retry_with_backoff(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
    def generate_content(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Generate content from a text prompt using Gemini Flash.
        
        This method sends a prompt to the Gemini model and returns the generated
        text response. It includes automatic retry logic for transient failures.
        
        Args:
            prompt: Input text prompt for generation
            temperature: Override default temperature (optional)
            max_output_tokens: Override default max tokens (optional)
            stop_sequences: List of sequences where generation should stop (optional)
        
        Returns:
            Generated text response from Gemini
        
        Raises:
            GeminiQuotaExceededError: If API quota is exceeded
            GeminiInvalidArgumentError: If invalid arguments provided
            GeminiServiceUnavailableError: If service is unavailable
            GeminiClientError: For other Gemini-related errors
        
        Example:
            >>> client = GeminiClient()
            >>> response = client.generate_content(
            ...     prompt="Create 3 chemistry questions about acids and bases",
            ...     temperature=0.8
            ... )
            >>> print(response)
        """
        try:
            logger.info(f"Generating content with prompt length: {len(prompt)}")
            
            # Validate prompt
            if not prompt or not prompt.strip():
                raise GeminiInvalidArgumentError("Prompt cannot be empty")
            
            # Create custom generation config if parameters are overridden
            generation_config = self.generation_config
            if temperature is not None or max_output_tokens is not None:
                generation_config = {
                    'temperature': temperature if temperature is not None else self.temperature,
                    'top_p': self.top_p,
                    'top_k': self.top_k,
                    'max_output_tokens': max_output_tokens if max_output_tokens is not None else self.max_output_tokens
                }
            
            # Generate content
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=False
            )
            
            # Extract text from response
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                raise GeminiClientError("Received empty response from Gemini")
            
            generated_text = response.text.strip()
            logger.info(f"Successfully generated {len(generated_text)} characters")
            
            return generated_text
        
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check for quota/rate limit errors
            if 'quota' in error_msg or 'rate limit' in error_msg or '429' in error_msg:
                logger.error(f"Gemini quota exceeded: {e}")
                raise GeminiQuotaExceededError(
                    "API quota exceeded. Please check your quota limits and try again later."
                ) from e
            
            # Check for invalid argument errors
            elif 'invalid' in error_msg or '400' in error_msg:
                logger.error(f"Invalid argument to Gemini: {e}")
                raise GeminiInvalidArgumentError(
                    f"Invalid argument provided: {str(e)}"
                ) from e
            
            # Check for service unavailable errors
            elif 'unavailable' in error_msg or '503' in error_msg:
                logger.error(f"Gemini service unavailable: {e}")
                raise GeminiServiceUnavailableError(
                    "Gemini service is temporarily unavailable. Please try again later."
                ) from e
            
            # Generic error
            else:
                logger.error(f"Unexpected error during content generation: {e}")
                logger.exception("Full traceback:")
                raise GeminiClientError(f"Failed to generate content: {str(e)}") from e
    
    async def generate_content_async(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> str:
        """
        Asynchronously generate content from a text prompt.
        
        This is the async version of generate_content(), allowing for non-blocking
        content generation in async contexts.
        
        Args:
            prompt: Input text prompt for generation
            temperature: Override default temperature (optional)
            max_output_tokens: Override default max tokens (optional)
            stop_sequences: List of sequences where generation should stop (optional)
        
        Returns:
            Generated text response from Gemini
        
        Raises:
            GeminiQuotaExceededError: If API quota is exceeded
            GeminiInvalidArgumentError: If invalid arguments provided
            GeminiServiceUnavailableError: If service is unavailable
            GeminiClientError: For other Gemini-related errors
        
        Example:
            >>> import asyncio
            >>> client = GeminiClient()
            >>> 
            >>> async def generate():
            ...     response = await client.generate_content_async(
            ...         prompt="Explain quantum mechanics"
            ...     )
            ...     return response
            >>> 
            >>> result = asyncio.run(generate())
        """
        try:
            logger.info(f"Async generating content with prompt length: {len(prompt)}")
            
            # Run synchronous generate_content in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self.generate_content,
                prompt,
                temperature,
                max_output_tokens,
                stop_sequences
            )
            
            logger.info("Async content generation completed")
            return response
        
        except Exception as e:
            logger.error(f"Error in async content generation: {e}")
            raise
    
    def generate_content_stream(self, prompt: str):
        """
        Generate content with streaming response.
        
        This method streams the generated content token by token, allowing for
        real-time display of generation progress.
        
        Args:
            prompt: Input text prompt for generation
        
        Yields:
            Text chunks as they are generated
        
        Example:
            >>> client = GeminiClient()
            >>> for chunk in client.generate_content_stream("Explain AI"):
            ...     print(chunk, end='', flush=True)
        """
        try:
            logger.info(f"Streaming content generation with prompt length: {len(prompt)}")
            
            # Validate prompt
            if not prompt or not prompt.strip():
                raise GeminiInvalidArgumentError("Prompt cannot be empty")
            
            # Generate content with streaming
            response_stream = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                stream=True
            )
            
            # Yield chunks as they arrive
            for chunk in response_stream:
                if chunk.text:
                    yield chunk.text
            
            logger.info("Streaming generation completed")
        
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            raise GeminiClientError(f"Failed to stream content: {str(e)}") from e
    
    def update_config(
        self,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        max_output_tokens: Optional[int] = None
    ):
        """
        Update generation configuration parameters.
        
        Args:
            temperature: New temperature value (optional)
            top_p: New top_p value (optional)
            top_k: New top_k value (optional)
            max_output_tokens: New max output tokens (optional)
        
        Example:
            >>> client = GeminiClient()
            >>> client.update_config(temperature=0.9, max_output_tokens=3000)
        """
        if temperature is not None:
            self.temperature = temperature
        if top_p is not None:
            self.top_p = top_p
        if top_k is not None:
            self.top_k = top_k
        if max_output_tokens is not None:
            self.max_output_tokens = max_output_tokens
        
        # Recreate generation config
        self.generation_config = self._GenerationConfig(
            temperature=self.temperature,
            top_p=self.top_p,
            top_k=self.top_k,
            max_output_tokens=self.max_output_tokens
        )
        
        logger.info(
            f"Updated generation config: temp={self.temperature}, "
            f"top_p={self.top_p}, top_k={self.top_k}, "
            f"max_tokens={self.max_output_tokens}"
        )
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.
        
        Returns:
            Dictionary containing current configuration parameters
        
        Example:
            >>> client = GeminiClient()
            >>> config = client.get_config()
            >>> print(config)
        """
        return {
            "project_id": self.project_id,
            "location": self.location,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens
        }


def get_gemini_client(
    project_id: Optional[str] = None,
    location: Optional[str] = None
) -> GeminiClient:
    """
    Get or create a singleton Gemini client instance.
    
    This function implements a singleton pattern to reuse the same client
    instance across the application.
    
    Args:
        project_id: Google Cloud project ID (optional)
        location: Google Cloud region (optional)
    
    Returns:
        GeminiClient instance
    
    Example:
        >>> client = get_gemini_client()
        >>> response = client.generate_content("Hello, Gemini!")
    """
    global _gemini_client_cache, _gemini_initialized
    
    if _gemini_initialized and _gemini_client_cache is not None:
        logger.info("Returning cached Gemini client")
        return _gemini_client_cache
    
    logger.info("Creating new Gemini client instance")
    return GeminiClient(project_id=project_id, location=location)


def is_gemini_initialized() -> bool:
    """
    Check if Gemini client is initialized.
    
    Returns:
        True if client is initialized, False otherwise
    
    Example:
        >>> if is_gemini_initialized():
        ...     print("Client ready")
    """
    return _gemini_initialized


# Module initialization
logger.info("Gemini client module loaded")
logger.info(f"Default model: {DEFAULT_MODEL}")
logger.info(f"Default config: temp={DEFAULT_TEMPERATURE}, top_p={DEFAULT_TOP_P}, "
           f"top_k={DEFAULT_TOP_K}, max_tokens={DEFAULT_MAX_OUTPUT_TOKENS}")
