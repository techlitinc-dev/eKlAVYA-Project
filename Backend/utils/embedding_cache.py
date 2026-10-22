"""
Embedding Cache Utility Module

This module provides a persistent, thread-safe caching system for text embeddings
in the Mentor AI EdTech Platform. It reduces API calls by storing previously
generated embeddings with TTL (time-to-live) management.

Features:
- In-memory cache with dictionary storage
- Persistent storage to JSON file
- TTL (time-to-live) management - default 7 days
- Size limit management - max 10,000 entries
- Thread-safe operations using locks
- SHA-256 hashing for cache keys
- Cache statistics (hits, misses, size)
- Automatic cleanup of expired entries

Functions:
- get: Retrieve embedding from cache
- set: Store embedding in cache
- exists: Check if text has cached embedding
- clear: Clear entire cache
- remove: Remove specific cache entry
- get_stats: Get cache statistics
- cleanup_expired: Remove expired entries
- save: Manually save cache to disk
- load: Manually load cache from disk

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import json
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Cache configuration constants
DEFAULT_TTL_DAYS = 7  # Default time-to-live in days
MAX_CACHE_SIZE = 10000  # Maximum number of cache entries
CACHE_FILE_PATH = "data/embeddings/cache.json"  # Default cache file path
AUTO_SAVE_INTERVAL = 100  # Save to disk every N operations
CLEANUP_INTERVAL = 1000  # Cleanup expired entries every N operations


class EmbeddingCache:
    """
    Thread-safe cache for storing and retrieving text embeddings.
    
    This class provides an in-memory cache with persistent storage to disk.
    It includes TTL management, size limits, and automatic cleanup of expired
    entries. All operations are thread-safe using locks.
    
    Attributes:
        cache: Dictionary storing cache entries
        stats: Dictionary tracking cache statistics
        lock: Threading lock for thread-safe operations
        ttl_days: Time-to-live in days for cache entries
        max_size: Maximum number of cache entries allowed
        cache_file: Path to cache persistence file
        operation_count: Counter for triggering auto-save and cleanup
    
    Example:
        >>> cache = EmbeddingCache()
        >>> cache.set("sample text", [0.1, 0.2, 0.3])
        >>> embedding = cache.get("sample text")
        >>> print(embedding)
        [0.1, 0.2, 0.3]
    """
    
    def __init__(
        self,
        cache_file: str = CACHE_FILE_PATH,
        ttl_days: int = DEFAULT_TTL_DAYS,
        max_size: int = MAX_CACHE_SIZE,
        auto_load: bool = True
    ):
        """
        Initialize the embedding cache.
        
        Args:
            cache_file: Path to cache persistence file (default: data/embeddings/cache.json)
            ttl_days: Time-to-live in days for cache entries (default: 7)
            max_size: Maximum number of cache entries (default: 10000)
            auto_load: Whether to automatically load cache from disk (default: True)
        
        Example:
            >>> cache = EmbeddingCache(ttl_days=14, max_size=20000)
            >>> # Custom cache with 14-day TTL and 20k max size
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.stats: Dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "evictions": 0
        }
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.ttl_days = ttl_days
        self.max_size = max_size
        self.cache_file = cache_file
        self.operation_count = 0
        
        logger.info("Initializing EmbeddingCache")
        logger.info(f"TTL: {ttl_days} days, Max size: {max_size}, Cache file: {cache_file}")
        
        # Load existing cache from disk
        if auto_load:
            self.load()
    
    def _generate_key(self, text: str) -> str:
        """
        Generate cache key from text using SHA-256 hash.
        
        This handles long texts by creating a fixed-length hash key.
        
        Args:
            text: Input text to generate key for
        
        Returns:
            SHA-256 hash of the text as hexadecimal string
        
        Example:
            >>> cache = EmbeddingCache()
            >>> key = cache._generate_key("sample text")
            >>> print(len(key))  # Always 64 characters
            64
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry has expired based on TTL.
        
        Args:
            entry: Cache entry dictionary containing timestamp
        
        Returns:
            True if entry has expired, False otherwise
        """
        if "timestamp" not in entry:
            return True
        
        try:
            entry_time = datetime.fromisoformat(entry["timestamp"])
            expiry_time = entry_time + timedelta(days=self.ttl_days)
            return datetime.utcnow() > expiry_time
        except (ValueError, TypeError):
            # Invalid timestamp format
            return True
    
    def _increment_operation_count(self) -> None:
        """
        Increment operation counter and trigger auto-save/cleanup if needed.
        
        This method is called after each cache operation to periodically
        save the cache to disk and cleanup expired entries.
        """
        self.operation_count += 1
        
        # Auto-save to disk
        if self.operation_count % AUTO_SAVE_INTERVAL == 0:
            logger.debug(f"Auto-saving cache after {self.operation_count} operations")
            self.save()
        
        # Auto-cleanup expired entries
        if self.operation_count % CLEANUP_INTERVAL == 0:
            logger.debug(f"Auto-cleanup after {self.operation_count} operations")
            self.cleanup_expired()
    
    def get(self, text: str) -> Optional[List[float]]:
        """
        Retrieve embedding from cache if it exists and hasn't expired.
        
        This method is thread-safe and automatically updates cache statistics.
        
        Args:
            text: Input text to retrieve embedding for
        
        Returns:
            Embedding vector as list of floats, or None if not found/expired
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("hello", [0.1, 0.2, 0.3])
            >>> embedding = cache.get("hello")
            >>> print(embedding)
            [0.1, 0.2, 0.3]
            >>> 
            >>> missing = cache.get("not exists")
            >>> print(missing)
            None
        """
        with self.lock:
            key = self._generate_key(text)
            
            if key in self.cache:
                entry = self.cache[key]
                
                # Check if entry has expired
                if self._is_expired(entry):
                    # Remove expired entry
                    del self.cache[key]
                    self.stats["misses"] += 1
                    logger.debug(f"Cache entry expired for text: {text[:50]}...")
                    return None
                
                # Valid cache hit
                self.stats["hits"] += 1
                logger.debug(f"Cache hit for text: {text[:50]}...")
                self._increment_operation_count()
                return entry["embedding"]
            
            # Cache miss
            self.stats["misses"] += 1
            logger.debug(f"Cache miss for text: {text[:50]}...")
            self._increment_operation_count()
            return None
    
    def set(
        self,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store embedding in cache with current timestamp.
        
        This method is thread-safe and implements cache size management.
        If cache is full, oldest entries are removed (FIFO).
        
        Args:
            text: Input text that was embedded
            embedding: Embedding vector as list of floats
            metadata: Optional metadata to store with embedding
        
        Returns:
            True if successfully stored, False otherwise
        
        Example:
            >>> cache = EmbeddingCache()
            >>> success = cache.set("hello", [0.1, 0.2, 0.3])
            >>> print(success)
            True
            >>> 
            >>> # With metadata
            >>> cache.set(
            ...     "hello",
            ...     [0.1, 0.2, 0.3],
            ...     metadata={"model": "gecko-003", "dimension": 768}
            ... )
            True
        """
        with self.lock:
            try:
                # Check if cache is full
                if len(self.cache) >= self.max_size:
                    # Remove oldest entries (FIFO) - 10% of max size
                    num_to_remove = max(1, self.max_size // 10)
                    keys_to_remove = list(self.cache.keys())[:num_to_remove]
                    
                    for old_key in keys_to_remove:
                        del self.cache[old_key]
                        self.stats["evictions"] += 1
                    
                    logger.info(f"Cache full, evicted {num_to_remove} oldest entries")
                
                key = self._generate_key(text)
                
                # Store cache entry
                self.cache[key] = {
                    "embedding": embedding,
                    "timestamp": datetime.utcnow().isoformat(),
                    "text_preview": text[:100],  # Store preview for debugging
                    "dimension": len(embedding),
                    "metadata": metadata or {}
                }
                
                self.stats["sets"] += 1
                logger.debug(f"Cached embedding for text: {text[:50]}... (dimension: {len(embedding)})")
                self._increment_operation_count()
                
                return True
                
            except Exception as e:
                logger.error(f"Error setting cache entry: {e}")
                return False
    
    def exists(self, text: str) -> bool:
        """
        Check if text has a valid (non-expired) cached embedding.
        
        This method is thread-safe and doesn't update statistics.
        
        Args:
            text: Input text to check
        
        Returns:
            True if valid cache entry exists, False otherwise
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("hello", [0.1, 0.2, 0.3])
            >>> print(cache.exists("hello"))
            True
            >>> print(cache.exists("not exists"))
            False
        """
        with self.lock:
            key = self._generate_key(text)
            
            if key not in self.cache:
                return False
            
            # Check if expired
            if self._is_expired(self.cache[key]):
                return False
            
            return True
    
    def remove(self, text: str) -> bool:
        """
        Remove specific cache entry.
        
        Args:
            text: Input text to remove from cache
        
        Returns:
            True if entry was removed, False if not found
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("hello", [0.1, 0.2, 0.3])
            >>> cache.remove("hello")
            True
            >>> cache.exists("hello")
            False
        """
        with self.lock:
            key = self._generate_key(text)
            
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Removed cache entry for text: {text[:50]}...")
                self._increment_operation_count()
                return True
            
            return False
    
    def clear(self) -> int:
        """
        Clear entire cache and reset statistics.
        
        Returns:
            Number of entries cleared
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("text1", [0.1, 0.2])
            >>> cache.set("text2", [0.3, 0.4])
            >>> cleared = cache.clear()
            >>> print(cleared)
            2
        """
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            self.stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "evictions": 0
            }
            self.operation_count = 0
            
            logger.info(f"Cleared {count} entries from cache")
            return count
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of expired entries removed
        
        Example:
            >>> cache = EmbeddingCache(ttl_days=0)  # Immediate expiry for testing
            >>> cache.set("text", [0.1, 0.2])
            >>> # Wait or modify timestamp
            >>> removed = cache.cleanup_expired()
        """
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics including hits, misses, and size.
        
        Returns:
            Dictionary containing cache statistics
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("text1", [0.1, 0.2])
            >>> cache.get("text1")  # Hit
            >>> cache.get("text2")  # Miss
            >>> stats = cache.get_stats()
            >>> print(stats)
            {
                'hits': 1,
                'misses': 1,
                'sets': 1,
                'evictions': 0,
                'size': 1,
                'max_size': 10000,
                'hit_rate': 0.5,
                'fill_rate': 0.0001
            }
        """
        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0
            fill_rate = len(self.cache) / self.max_size
            
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "sets": self.stats["sets"],
                "evictions": self.stats["evictions"],
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
                "fill_rate": fill_rate,
                "ttl_days": self.ttl_days
            }
    
    def save(self, file_path: Optional[str] = None) -> bool:
        """
        Save cache to JSON file for persistence.
        
        Args:
            file_path: Optional custom file path (default: use initialized path)
        
        Returns:
            True if successfully saved, False otherwise
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("text", [0.1, 0.2, 0.3])
            >>> cache.save()
            True
            >>> # Cache saved to data/embeddings/cache.json
        """
        with self.lock:
            try:
                save_path = file_path or self.cache_file
                
                # Create directory if it doesn't exist
                cache_dir = os.path.dirname(save_path)
                if cache_dir:
                    os.makedirs(cache_dir, exist_ok=True)
                
                # Prepare data for serialization
                cache_data = {
                    "version": "1.0.0",
                    "saved_at": datetime.utcnow().isoformat(),
                    "ttl_days": self.ttl_days,
                    "max_size": self.max_size,
                    "stats": self.stats,
                    "entries": self.cache
                }
                
                # Write to file
                with open(save_path, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, indent=2)
                
                logger.info(f"Cache saved to {save_path} ({len(self.cache)} entries)")
                return True
                
            except Exception as e:
                logger.error(f"Error saving cache to file: {e}")
                logger.exception("Full traceback:")
                return False
    
    def load(self, file_path: Optional[str] = None) -> bool:
        """
        Load cache from JSON file.
        
        Args:
            file_path: Optional custom file path (default: use initialized path)
        
        Returns:
            True if successfully loaded, False otherwise
        
        Example:
            >>> cache = EmbeddingCache(auto_load=False)
            >>> cache.load()
            True
            >>> # Cache loaded from data/embeddings/cache.json
        """
        with self.lock:
            try:
                load_path = file_path or self.cache_file
                
                # Check if file exists
                if not os.path.exists(load_path):
                    logger.info(f"Cache file not found at {load_path}, starting with empty cache")
                    return False
                
                # Load from file
                with open(load_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Validate data structure
                if "entries" not in cache_data:
                    logger.warning(f"Invalid cache file format at {load_path}")
                    return False
                
                # Load cache entries
                self.cache = cache_data["entries"]
                
                # Load statistics if available
                if "stats" in cache_data:
                    self.stats = cache_data["stats"]
                
                # Cleanup expired entries after loading
                expired_count = self.cleanup_expired()
                
                logger.info(
                    f"Cache loaded from {load_path} "
                    f"({len(self.cache)} entries, {expired_count} expired removed)"
                )
                return True
                
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding cache file: {e}")
                return False
            
            except Exception as e:
                logger.error(f"Error loading cache from file: {e}")
                logger.exception("Full traceback:")
                return False
    
    def __len__(self) -> int:
        """
        Get number of entries in cache.
        
        Returns:
            Number of cache entries
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("text", [0.1, 0.2])
            >>> print(len(cache))
            1
        """
        with self.lock:
            return len(self.cache)
    
    def __contains__(self, text: str) -> bool:
        """
        Check if text exists in cache (using 'in' operator).
        
        Args:
            text: Input text to check
        
        Returns:
            True if exists, False otherwise
        
        Example:
            >>> cache = EmbeddingCache()
            >>> cache.set("text", [0.1, 0.2])
            >>> print("text" in cache)
            True
        """
        return self.exists(text)
    
    def __del__(self):
        """
        Destructor - save cache before object destruction.
        """
        try:
            self.save()
            logger.debug("Cache saved on destruction")
        except:
            pass


# ============================================================================
# GLOBAL CACHE INSTANCE
# ============================================================================

# Create a global singleton cache instance
_global_cache: Optional[EmbeddingCache] = None
_global_cache_lock = threading.Lock()


def get_global_cache() -> EmbeddingCache:
    """
    Get or create the global singleton cache instance.
    
    This function ensures only one cache instance is created across
    the entire application, providing efficient memory usage.
    
    Returns:
        Global EmbeddingCache instance
    
    Example:
        >>> from utils.embedding_cache import get_global_cache
        >>> cache = get_global_cache()
        >>> cache.set("text", [0.1, 0.2, 0.3])
    """
    global _global_cache
    
    if _global_cache is None:
        with _global_cache_lock:
            # Double-check locking pattern
            if _global_cache is None:
                _global_cache = EmbeddingCache()
                logger.info("Global embedding cache instance created")
    
    return _global_cache


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get(text: str) -> Optional[List[float]]:
    """
    Get embedding from global cache.
    
    Convenience function for accessing global cache instance.
    
    Args:
        text: Input text to retrieve embedding for
    
    Returns:
        Embedding vector or None if not found
    
    Example:
        >>> from utils.embedding_cache import get, set
        >>> set("hello", [0.1, 0.2, 0.3])
        >>> embedding = get("hello")
    """
    return get_global_cache().get(text)


def set(text: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Set embedding in global cache.
    
    Convenience function for accessing global cache instance.
    
    Args:
        text: Input text that was embedded
        embedding: Embedding vector
        metadata: Optional metadata
    
    Returns:
        True if successfully stored
    
    Example:
        >>> from utils.embedding_cache import set
        >>> set("hello", [0.1, 0.2, 0.3])
        True
    """
    return get_global_cache().set(text, embedding, metadata)


def exists(text: str) -> bool:
    """
    Check if text exists in global cache.
    
    Args:
        text: Input text to check
    
    Returns:
        True if exists, False otherwise
    """
    return get_global_cache().exists(text)


def clear() -> int:
    """
    Clear global cache.
    
    Returns:
        Number of entries cleared
    """
    return get_global_cache().clear()


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

logger.info("Embedding cache utility initialized")
logger.info(f"Default configuration: TTL={DEFAULT_TTL_DAYS} days, Max size={MAX_CACHE_SIZE}")
