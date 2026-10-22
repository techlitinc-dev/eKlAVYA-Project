"""
Vertex AI Client Initialization and Management Module

This module handles the initialization and configuration of Google Cloud Vertex AI
for the Mentor AI EdTech Platform. It provides singleton access to Vertex AI
services including text embeddings and vector search.

Features:
- Singleton pattern for Vertex AI client initialization
- Text embedding generation (textembedding-gecko@003)
- Vector search client access
- Multi-region support (us-central1, asia-south1)
- Retry logic for transient API failures
- Environment-based configuration
- Comprehensive error handling and logging
- Client instance caching

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import logging
import time
from typing import Optional, Any, List
from functools import wraps

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global flags and cached instances
_vertex_ai_initialized: bool = False
_embedding_client_cache: Optional[Any] = None
_vector_search_client_cache: Optional[Any] = None
_current_project_id: Optional[str] = None
_current_location: Optional[str] = None

# Supported regions for Vertex AI
SUPPORTED_REGIONS = ["us-central1", "asia-south1", "europe-west1", "us-east1"]
DEFAULT_REGION = "us-central1"

# Embedding model configuration
EMBEDDING_MODEL = "textembedding-gecko@003"
DEFAULT_EMBEDDING_DIMENSION = 768

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
RETRY_BACKOFF_FACTOR = 2


def retry_on_failure(max_retries: int = MAX_RETRIES, delay: float = RETRY_DELAY):
    """
    Decorator to retry functions on transient failures.
    
    This decorator implements exponential backoff retry logic for functions
    that may experience transient API failures.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1)
    
    Returns:
        Decorated function with retry logic
    
    Example:
        >>> @retry_on_failure(max_retries=3, delay=1)
        >>> def api_call():
        >>>     # Make API call
        >>>     pass
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
                    
                    # Check if it's a retryable error
                    error_message = str(e).lower()
                    is_retryable = any(
                        keyword in error_message
                        for keyword in ["timeout", "temporarily", "unavailable", "503", "429"]
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


def initialize_vertex_ai(
    project_id: Optional[str] = None,
    location: Optional[str] = None
) -> None:
    """
    Initialize Vertex AI with project and location configuration.
    
    This function implements a singleton pattern to ensure Vertex AI is
    initialized only once. It loads configuration from environment variables
    or uses provided parameters.
    
    Args:
        project_id: Google Cloud project ID (default: from GOOGLE_CLOUD_PROJECT env var)
        location: Google Cloud region (default: from GOOGLE_CLOUD_LOCATION env var)
    
    Raises:
        ValueError: If project_id or location is not provided and not in environment
        ImportError: If google-cloud-aiplatform package is not installed
        Exception: If Vertex AI initialization fails
    
    Environment Variables:
        GOOGLE_CLOUD_PROJECT: Google Cloud project ID
        GOOGLE_CLOUD_LOCATION: Google Cloud region (e.g., us-central1)
        GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON (optional)
    
    Example:
        >>> initialize_vertex_ai()
        # Vertex AI initialized successfully with project: my-project
        
        >>> initialize_vertex_ai(project_id="my-project", location="us-central1")
        # Vertex AI initialized with custom configuration
    """
    global _vertex_ai_initialized, _current_project_id, _current_location
    
    # Check if Vertex AI is already initialized with same config
    if _vertex_ai_initialized:
        if project_id and project_id != _current_project_id:
            logger.warning(
                f"Vertex AI already initialized with project {_current_project_id}. "
                f"Ignoring new project_id: {project_id}"
            )
        if location and location != _current_location:
            logger.warning(
                f"Vertex AI already initialized with location {_current_location}. "
                f"Ignoring new location: {location}"
            )
        logger.info("Vertex AI is already initialized")
        return
    
    try:
        # Import Vertex AI SDK
        try:
            import vertexai
            from google.cloud import aiplatform
        except ImportError as e:
            error_msg = (
                "google-cloud-aiplatform package is not installed. "
                "Please install it using: pip install google-cloud-aiplatform"
            )
            logger.error(error_msg)
            raise ImportError(error_msg) from e
        
        # Get project_id from parameter or environment
        if not project_id:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        if not project_id:
            error_msg = (
                "Google Cloud project ID is not provided. "
                "Please set GOOGLE_CLOUD_PROJECT environment variable or pass project_id parameter."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Get location from parameter or environment
        if not location:
            location = os.getenv("GOOGLE_CLOUD_LOCATION", DEFAULT_REGION)
        
        # Validate location
        if location not in SUPPORTED_REGIONS:
            logger.warning(
                f"Location '{location}' is not in the list of commonly supported regions: {SUPPORTED_REGIONS}. "
                "Proceeding anyway, but initialization may fail if the region is invalid."
            )
        
        # Check for credentials
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            if not os.path.exists(credentials_path):
                logger.warning(
                    f"GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {credentials_path}. "
                    "Will attempt to use Application Default Credentials (ADC)."
                )
            else:
                logger.info(f"Using credentials from: {credentials_path}")
        else:
            logger.info("Using Application Default Credentials (ADC)")
        
        # Initialize Vertex AI
        logger.info(f"Initializing Vertex AI with project: {project_id}, location: {location}")
        vertexai.init(project=project_id, location=location)
        
        # Store current configuration
        _current_project_id = project_id
        _current_location = location
        _vertex_ai_initialized = True
        
        logger.info("=" * 80)
        logger.info("Vertex AI initialized successfully")
        logger.info(f"Project ID: {project_id}")
        logger.info(f"Location: {location}")
        logger.info(f"Embedding Model: {EMBEDDING_MODEL}")
        logger.info(f"Supported Regions: {', '.join(SUPPORTED_REGIONS)}")
        logger.info("=" * 80)
        
    except ValueError as ve:
        logger.error(f"Configuration error during Vertex AI initialization: {ve}")
        raise
    
    except ImportError as ie:
        logger.error(f"Import error during Vertex AI initialization: {ie}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during Vertex AI initialization: {e}")
        logger.exception("Full traceback:")
        raise


@retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
def get_embedding_client() -> Any:
    """
    Get text embedding client instance for generating embeddings.
    
    This function returns a client configured with the textembedding-gecko@003
    model for generating text embeddings. The client instance is cached to
    avoid re-initialization.
    
    Returns:
        TextEmbeddingModel: Configured embedding model client
    
    Raises:
        ImportError: If google-cloud-aiplatform is not installed
        Exception: If Vertex AI initialization fails
    
    Example:
        >>> embedding_client = get_embedding_client()
        >>> embeddings = embedding_client.get_embeddings(["sample text"])
        >>> vector = embeddings[0].values
    """
    global _embedding_client_cache
    
    # Return cached client if available
    if _embedding_client_cache is not None:
        logger.debug("Returning cached embedding client")
        return _embedding_client_cache
    
    # Ensure Vertex AI is initialized
    if not _vertex_ai_initialized:
        logger.warning("Vertex AI not initialized, initializing now...")
        initialize_vertex_ai()
    
    try:
        from vertexai.language_models import TextEmbeddingModel
        
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        embedding_client = TextEmbeddingModel.from_pretrained(EMBEDDING_MODEL)
        
        # Cache the client instance
        _embedding_client_cache = embedding_client
        
        logger.info("Embedding client initialized successfully")
        logger.debug(f"Model: {EMBEDDING_MODEL}, Dimension: {DEFAULT_EMBEDDING_DIMENSION}")
        
        return embedding_client
        
    except ImportError as e:
        error_msg = (
            "Failed to import TextEmbeddingModel from vertexai.language_models. "
            "Please ensure google-cloud-aiplatform is installed correctly."
        )
        logger.error(error_msg)
        raise ImportError(error_msg) from e
    
    except Exception as e:
        logger.error(f"Error initializing embedding client: {e}")
        logger.exception("Full traceback:")
        raise


@retry_on_failure(max_retries=MAX_RETRIES, delay=RETRY_DELAY)
def get_vector_search_client() -> Any:
    """
    Get vector search client instance for similarity search operations.
    
    This function returns a client for performing vector similarity search
    operations using Vertex AI Matching Engine. The client instance is
    cached to avoid re-initialization.
    
    Returns:
        MatchingEngineIndexEndpoint: Vector search client instance
    
    Raises:
        ImportError: If google-cloud-aiplatform is not installed
        Exception: If Vertex AI initialization fails
    
    Example:
        >>> vector_client = get_vector_search_client()
        >>> # Configure and use for vector search operations
    """
    global _vector_search_client_cache
    
    # Return cached client if available
    if _vector_search_client_cache is not None:
        logger.debug("Returning cached vector search client")
        return _vector_search_client_cache
    
    # Ensure Vertex AI is initialized
    if not _vertex_ai_initialized:
        logger.warning("Vertex AI not initialized, initializing now...")
        initialize_vertex_ai()
    
    try:
        from google.cloud import aiplatform
        
        logger.info("Initializing vector search client")
        
        # Initialize AI Platform client
        # Note: Actual index endpoint configuration will be done when needed
        vector_search_client = aiplatform.MatchingEngineIndexEndpoint
        
        # Cache the client class
        _vector_search_client_cache = vector_search_client
        
        logger.info("Vector search client initialized successfully")
        
        return vector_search_client
        
    except ImportError as e:
        error_msg = (
            "Failed to import from google.cloud.aiplatform. "
            "Please ensure google-cloud-aiplatform is installed correctly."
        )
        logger.error(error_msg)
        raise ImportError(error_msg) from e
    
    except Exception as e:
        logger.error(f"Error initializing vector search client: {e}")
        logger.exception("Full traceback:")
        raise


def generate_embeddings(
    texts: List[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    auto_truncate: bool = True
) -> List[List[float]]:
    """
    Generate embeddings for a list of text inputs.
    
    This is a convenience function that wraps the embedding client to generate
    embeddings with proper error handling and retry logic.
    
    Args:
        texts: List of text strings to generate embeddings for
        task_type: Type of embedding task (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY,
                  SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING)
        auto_truncate: Automatically truncate texts that exceed model limits
    
    Returns:
        List of embedding vectors (each vector is a list of floats)
    
    Raises:
        ValueError: If texts list is empty
        Exception: If embedding generation fails
    
    Example:
        >>> texts = ["Machine learning is fascinating", "AI is the future"]
        >>> embeddings = generate_embeddings(texts)
        >>> print(len(embeddings))  # 2
        >>> print(len(embeddings[0]))  # 768
    """
    if not texts:
        raise ValueError("texts list cannot be empty")
    
    logger.info(f"Generating embeddings for {len(texts)} text(s)")
    
    try:
        embedding_client = get_embedding_client()
        
        # Generate embeddings
        # Note: task_type parameter not supported in current SDK version
        embeddings = embedding_client.get_embeddings(
            texts,
            auto_truncate=auto_truncate
        )
        
        # Extract embedding values
        embedding_vectors = [embedding.values for embedding in embeddings]
        
        logger.info(f"Successfully generated {len(embedding_vectors)} embeddings")
        logger.debug(f"Embedding dimension: {len(embedding_vectors[0])}")
        
        return embedding_vectors
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        logger.exception("Full traceback:")
        raise


def get_vertex_ai_status() -> dict:
    """
    Get the current status of Vertex AI initialization.
    
    Returns:
        Dict containing initialization status and configuration details
    
    Example:
        >>> status = get_vertex_ai_status()
        >>> print(status)
        {
            'initialized': True,
            'project_id': 'my-project',
            'location': 'us-central1',
            'embedding_model': 'textembedding-gecko@003',
            'embedding_client_cached': True,
            'vector_search_client_cached': True
        }
    """
    return {
        "initialized": _vertex_ai_initialized,
        "project_id": _current_project_id,
        "location": _current_location,
        "embedding_model": EMBEDDING_MODEL if _vertex_ai_initialized else None,
        "embedding_dimension": DEFAULT_EMBEDDING_DIMENSION if _vertex_ai_initialized else None,
        "embedding_client_cached": _embedding_client_cache is not None,
        "vector_search_client_cached": _vector_search_client_cache is not None,
        "supported_regions": SUPPORTED_REGIONS
    }


def reset_vertex_ai() -> None:
    """
    Reset Vertex AI initialization and clear all cached clients.
    
    This function is primarily useful for testing or when you need to
    reinitialize with different configuration.
    
    Warning:
        This will clear all cached client instances. Use with caution.
    
    Example:
        >>> reset_vertex_ai()
        # All Vertex AI clients cleared and reset
    """
    global _vertex_ai_initialized, _embedding_client_cache, _vector_search_client_cache
    global _current_project_id, _current_location
    
    _vertex_ai_initialized = False
    _embedding_client_cache = None
    _vector_search_client_cache = None
    _current_project_id = None
    _current_location = None
    
    logger.info("Vertex AI reset successfully - all cached clients cleared")


def is_vertex_ai_initialized() -> bool:
    """
    Check if Vertex AI has been initialized.
    
    Returns:
        bool: True if Vertex AI is initialized, False otherwise
    
    Example:
        >>> if is_vertex_ai_initialized():
        >>>     client = get_embedding_client()
    """
    return _vertex_ai_initialized


# Module-level initialization
# This ensures Vertex AI is initialized when the module is imported
# However, it gracefully handles missing configuration
try:
    logger.info("Attempting to initialize Vertex AI on module import...")
    initialize_vertex_ai()
except ValueError as e:
    # Environment variables not set - this is expected in some cases
    logger.warning(f"Vertex AI initialization skipped: {e}")
    logger.warning("Vertex AI will be initialized on first use")
except ImportError as e:
    # Package not installed - this is expected if not using Vertex AI
    logger.warning(f"Vertex AI initialization skipped: {e}")
    logger.warning("Vertex AI will not be available until package is installed")
except Exception as e:
    # Unexpected error - log it but don't crash the application
    logger.error(f"Failed to initialize Vertex AI on module import: {e}")
    logger.warning("Vertex AI will attempt to initialize on first use")
