"""
Persistent Query Cache Service

This service provides intelligent caching of user queries and responses
in Firestore to reduce API costs and improve response times.

Features:
- Persistent storage in Firestore
- Automatic cache key generation
- TTL-based expiration
- Query normalization
- Cache hit/miss tracking
- Statistics and analytics
- Automatic cleanup of expired entries

Author: Mentor AI Team
Version: 1.0.0
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

from utils.firebase_config import get_firestore_client
from google.cloud import firestore

logger = logging.getLogger(__name__)

# Cache configuration
QUERY_CACHE_COLLECTION = "query_cache"
CACHE_TTL_DAYS = 30  # Cache queries for 30 days
MAX_CACHE_SIZE_MB = 100  # Maximum cache size per user

# Cache statistics
_cache_stats = {
    "hits": 0,
    "misses": 0,
    "saves": 0,
    "errors": 0,
}


class QueryCacheService:
    """
    Service for caching user queries and responses.
    
    This service stores query-response pairs in Firestore to avoid
    redundant API calls when users search for the same thing twice.
    """
    
    def __init__(self, enable_cache: bool = True):
        """
        Initialize query cache service.
        
        Args:
            enable_cache: Whether to enable caching
        """
        self.enable_cache = enable_cache
        self.db = None
        
        if enable_cache:
            try:
                self.db = get_firestore_client()
                logger.info("Query cache service initialized with Firestore")
            except Exception as e:
                logger.warning(f"Firestore not available for query cache: {e}")
                self.enable_cache = False
        
        logger.info(f"Query cache service initialized (enabled: {self.enable_cache})")
    
    def get_cached_query(
        self,
        user_id: str,
        query: str,
        query_type: str,
        filters: Optional[Dict] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a query.
        
        Args:
            user_id: User identifier
            query: Search query text
            query_type: Type of query ("search", "rag", "embedding")
            filters: Optional query filters
        
        Returns:
            Cached response dict or None if not found
        """
        if not self.enable_cache or not self.db:
            return None
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query, query_type, filters)
            
            # Query Firestore
            doc_ref = (
                self.db.collection(QUERY_CACHE_COLLECTION)
                .document(user_id)
                .collection("queries")
                .document(cache_key)
            )
            
            doc = doc_ref.get()
            
            if not doc.exists:
                _cache_stats["misses"] += 1
                logger.debug(f"Cache miss: user={user_id}, query={query[:50]}...")
                return None
            
            # Check if expired
            data = doc.to_dict()
            cached_at = data.get("cached_at")
            
            if isinstance(cached_at, str):
                cached_at = datetime.fromisoformat(cached_at)
            
            expiry_time = cached_at + timedelta(days=CACHE_TTL_DAYS)
            
            if datetime.utcnow() > expiry_time:
                # Expired, delete it
                doc_ref.delete()
                _cache_stats["misses"] += 1
                logger.debug(f"Cache expired: user={user_id}, query={query[:50]}...")
                return None
            
            # Cache hit!
            _cache_stats["hits"] += 1
            
            # Update access time
            doc_ref.update({
                "last_accessed": firestore.SERVER_TIMESTAMP,
                "access_count": firestore.Increment(1)
            })
            
            logger.info(
                f"Cache HIT: user={user_id}, query={query[:50]}..., "
                f"saved_tokens=~{data.get('estimated_tokens', 0)}"
            )
            
            return {
                "response": data.get("response"),
                "cached_at": cached_at,
                "access_count": data.get("access_count", 1),
                "estimated_tokens_saved": data.get("estimated_tokens", 0),
            }
        
        except Exception as e:
            logger.error(f"Error retrieving cached query: {e}")
            _cache_stats["errors"] += 1
            return None
    
    def save_query_response(
        self,
        user_id: str,
        query: str,
        query_type: str,
        response: Any,
        filters: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Save query and response to cache.
        
        Args:
            user_id: User identifier
            query: Search query text
            query_type: Type of query
            response: Response to cache
            filters: Optional query filters
            metadata: Optional metadata (tokens used, etc.)
        
        Returns:
            True if saved successfully
        """
        if not self.enable_cache or not self.db:
            return False
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query, query_type, filters)
            
            # Estimate tokens (rough: 1 token ≈ 4 chars)
            response_str = json.dumps(response) if not isinstance(response, str) else response
            estimated_tokens = len(response_str) // 4
            
            # Prepare cache data
            cache_data = {
                "query": query,
                "query_type": query_type,
                "filters": filters or {},
                "response": response,
                "cached_at": firestore.SERVER_TIMESTAMP,
                "last_accessed": firestore.SERVER_TIMESTAMP,
                "access_count": 0,
                "estimated_tokens": estimated_tokens,
                "metadata": metadata or {},
            }
            
            # Save to Firestore
            doc_ref = (
                self.db.collection(QUERY_CACHE_COLLECTION)
                .document(user_id)
                .collection("queries")
                .document(cache_key)
            )
            
            doc_ref.set(cache_data)
            
            _cache_stats["saves"] += 1
            
            logger.info(
                f"Cache SAVE: user={user_id}, query={query[:50]}..., "
                f"tokens=~{estimated_tokens}"
            )
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving query to cache: {e}")
            _cache_stats["errors"] += 1
            return False
    
    def _generate_cache_key(
        self,
        query: str,
        query_type: str,
        filters: Optional[Dict]
    ) -> str:
        """
        Generate unique cache key for query.
        
        Args:
            query: Search query
            query_type: Type of query
            filters: Query filters
        
        Returns:
            SHA-256 hash as cache key
        """
        # Normalize query
        normalized_query = query.lower().strip()
        
        # Create key string
        key_parts = [
            query_type,
            normalized_query,
        ]
        
        # Add filters if present
        if filters:
            # Sort filters for consistent hashing
            sorted_filters = json.dumps(filters, sort_keys=True)
            key_parts.append(sorted_filters)
        
        key_string = "|".join(key_parts)
        
        # Generate hash
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def get_user_cache_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get cache statistics for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enable_cache or not self.db:
            return {
                "enabled": False,
                "total_queries": 0,
                "total_tokens_saved": 0,
            }
        
        try:
            # Query user's cached queries
            queries_ref = (
                self.db.collection(QUERY_CACHE_COLLECTION)
                .document(user_id)
                .collection("queries")
            )
            
            docs = list(queries_ref.stream())
            
            total_queries = len(docs)
            total_tokens_saved = 0
            total_accesses = 0
            query_types = {}
            
            for doc in docs:
                data = doc.to_dict()
                access_count = data.get("access_count", 0)
                estimated_tokens = data.get("estimated_tokens", 0)
                query_type = data.get("query_type", "unknown")
                
                total_accesses += access_count
                total_tokens_saved += (access_count * estimated_tokens)
                
                if query_type not in query_types:
                    query_types[query_type] = 0
                query_types[query_type] += 1
            
            return {
                "enabled": True,
                "total_queries": total_queries,
                "total_accesses": total_accesses,
                "total_tokens_saved": total_tokens_saved,
                "estimated_cost_saved": total_tokens_saved * 0.000125 / 1000,  # Gemini pricing
                "query_types": query_types,
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "enabled": True,
                "error": str(e),
            }
    
    def clear_user_cache(self, user_id: str) -> int:
        """
        Clear all cached queries for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Number of queries deleted
        """
        if not self.enable_cache or not self.db:
            return 0
        
        try:
            queries_ref = (
                self.db.collection(QUERY_CACHE_COLLECTION)
                .document(user_id)
                .collection("queries")
            )
            
            docs = list(queries_ref.stream())
            count = 0
            
            for doc in docs:
                doc.reference.delete()
                count += 1
            
            logger.info(f"Cleared {count} cached queries for user {user_id}")
            
            return count
        
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0
    
    def cleanup_expired_cache(self, user_id: Optional[str] = None) -> int:
        """
        Clean up expired cache entries.
        
        Args:
            user_id: Optional user ID to clean (if None, cleans all users)
        
        Returns:
            Number of entries deleted
        """
        if not self.enable_cache or not self.db:
            return 0
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=CACHE_TTL_DAYS)
            count = 0
            
            if user_id:
                # Clean specific user
                queries_ref = (
                    self.db.collection(QUERY_CACHE_COLLECTION)
                    .document(user_id)
                    .collection("queries")
                    .where("cached_at", "<", cutoff_time)
                )
                
                docs = list(queries_ref.stream())
                for doc in docs:
                    doc.reference.delete()
                    count += 1
            else:
                # Clean all users (admin operation)
                users_ref = self.db.collection(QUERY_CACHE_COLLECTION).stream()
                
                for user_doc in users_ref:
                    queries_ref = (
                        user_doc.reference
                        .collection("queries")
                        .where("cached_at", "<", cutoff_time)
                    )
                    
                    docs = list(queries_ref.stream())
                    for doc in docs:
                        doc.reference.delete()
                        count += 1
            
            logger.info(f"Cleaned up {count} expired cache entries")
            
            return count
        
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global cache statistics."""
        hit_rate = 0.0
        total_requests = _cache_stats["hits"] + _cache_stats["misses"]
        
        if total_requests > 0:
            hit_rate = _cache_stats["hits"] / total_requests
        
        return {
            "hits": _cache_stats["hits"],
            "misses": _cache_stats["misses"],
            "saves": _cache_stats["saves"],
            "errors": _cache_stats["errors"],
            "hit_rate": round(hit_rate, 4),
            "total_requests": total_requests,
        }


# Global instance
_query_cache_service = None


def get_query_cache_service() -> QueryCacheService:
    """Get or create global query cache service instance."""
    global _query_cache_service
    if _query_cache_service is None:
        _query_cache_service = QueryCacheService(enable_cache=True)
    return _query_cache_service


# Module initialization
logger.info("Query cache service module loaded")
logger.info(f"Cache TTL: {CACHE_TTL_DAYS} days")
