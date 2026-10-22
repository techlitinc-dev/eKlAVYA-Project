"""
Advanced Rate Limiter Middleware

This module provides comprehensive rate limiting for the Mentor AI backend
with multiple strategies and persistent storage.

Features:
- Per-user rate limiting
- Per-endpoint rate limiting
- Global rate limiting
- Sliding window algorithm
- Persistent storage in Firestore
- Automatic cleanup of old records
- Configurable limits per endpoint
- Rate limit headers in responses

Author: Mentor AI Team
Version: 1.0.0
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.firebase_config import get_firestore_client
from google.cloud import firestore

logger = logging.getLogger(__name__)

# Rate limit configurations (requests per minute)
RATE_LIMITS = {
    # Search endpoints
    "/api/vector-search/query": 30,
    "/api/vector-search/query/batch": 10,
    
    # RAG endpoints
    "/api/rag/generate-questions": 20,
    "/api/rag/generate-batch": 5,
    
    # Embedding endpoints
    "/api/vector-search/embeddings/generate": 50,
    "/api/vector-search/embeddings/batch": 20,
    
    # Test endpoints
    "/api/diagnostic-test/generate": 10,
    "/api/diagnostic-test/{test_id}/submit": 30,
    
    # Schedule endpoints
    "/api/schedule/generate": 5,
    "/api/schedule/progress/update": 100,
    
    # Default for other endpoints
    "default": 60,
}

# Global rate limit (all endpoints combined)
GLOBAL_RATE_LIMIT = 200  # requests per minute

# Time window in seconds
RATE_LIMIT_WINDOW = 60

# Firestore collection for rate limiting
RATE_LIMIT_COLLECTION = "rate_limits"


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies.
    
    Features:
    - Per-user limits
    - Per-endpoint limits
    - Global limits
    - Sliding window algorithm
    - Persistent storage
    """
    
    def __init__(self, use_firestore: bool = True):
        """
        Initialize rate limiter.
        
        Args:
            use_firestore: Whether to use Firestore for persistence
        """
        self.use_firestore = use_firestore
        
        # In-memory storage (fast access)
        self.user_requests: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque())
        )
        self.global_requests: deque = deque()
        
        # Firestore client
        self.db = None
        if use_firestore:
            try:
                self.db = get_firestore_client()
                logger.info("Rate limiter initialized with Firestore persistence")
            except Exception as e:
                logger.warning(f"Firestore not available for rate limiter: {e}")
                self.use_firestore = False
        
        logger.info(f"Rate limiter initialized (Firestore: {self.use_firestore})")
    
    def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        request_id: Optional[str] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits.
        
        Args:
            user_id: User identifier
            endpoint: API endpoint path
            request_id: Optional request identifier for logging
        
        Returns:
            Tuple of (allowed, info_dict)
            - allowed: Whether request is allowed
            - info_dict: Rate limit information
        """
        current_time = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(current_time)
        
        # Get endpoint-specific limit
        endpoint_limit = self._get_endpoint_limit(endpoint)
        
        # Check global rate limit
        global_allowed, global_info = self._check_global_limit(current_time)
        if not global_allowed:
            return False, global_info
        
        # Check per-user per-endpoint limit
        user_endpoint_key = f"{user_id}:{endpoint}"
        user_requests = self.user_requests[user_id][endpoint]
        
        # Remove requests outside the window
        cutoff_time = current_time - RATE_LIMIT_WINDOW
        while user_requests and user_requests[0] < cutoff_time:
            user_requests.popleft()
        
        # Check if limit exceeded
        current_count = len(user_requests)
        
        if current_count >= endpoint_limit:
            # Calculate retry after
            oldest_request = user_requests[0]
            retry_after = int(RATE_LIMIT_WINDOW - (current_time - oldest_request))
            
            info = {
                "allowed": False,
                "limit": endpoint_limit,
                "remaining": 0,
                "reset": int(current_time + retry_after),
                "retry_after": retry_after,
                "endpoint": endpoint,
            }
            
            logger.warning(
                f"Rate limit exceeded: user={user_id}, endpoint={endpoint}, "
                f"count={current_count}/{endpoint_limit}"
            )
            
            # Log to Firestore
            if self.use_firestore and self.db:
                self._log_rate_limit_violation(user_id, endpoint, request_id)
            
            return False, info
        
        # Allow request
        user_requests.append(current_time)
        self.global_requests.append(current_time)
        
        info = {
            "allowed": True,
            "limit": endpoint_limit,
            "remaining": endpoint_limit - current_count - 1,
            "reset": int(current_time + RATE_LIMIT_WINDOW),
            "endpoint": endpoint,
        }
        
        return True, info
    
    def _check_global_limit(self, current_time: float) -> Tuple[bool, Dict]:
        """Check global rate limit across all users."""
        cutoff_time = current_time - RATE_LIMIT_WINDOW
        
        # Remove old requests
        while self.global_requests and self.global_requests[0] < cutoff_time:
            self.global_requests.popleft()
        
        current_count = len(self.global_requests)
        
        if current_count >= GLOBAL_RATE_LIMIT:
            oldest_request = self.global_requests[0]
            retry_after = int(RATE_LIMIT_WINDOW - (current_time - oldest_request))
            
            info = {
                "allowed": False,
                "limit": GLOBAL_RATE_LIMIT,
                "remaining": 0,
                "reset": int(current_time + retry_after),
                "retry_after": retry_after,
                "endpoint": "global",
                "message": "Global rate limit exceeded. Please try again later.",
            }
            
            logger.warning(f"Global rate limit exceeded: {current_count}/{GLOBAL_RATE_LIMIT}")
            
            return False, info
        
        return True, {}
    
    def _get_endpoint_limit(self, endpoint: str) -> int:
        """Get rate limit for specific endpoint."""
        # Try exact match
        if endpoint in RATE_LIMITS:
            return RATE_LIMITS[endpoint]
        
        # Try pattern match (for parameterized routes)
        for pattern, limit in RATE_LIMITS.items():
            if "{" in pattern:
                # Simple pattern matching
                pattern_parts = pattern.split("/")
                endpoint_parts = endpoint.split("/")
                
                if len(pattern_parts) == len(endpoint_parts):
                    match = all(
                        p == e or "{" in p
                        for p, e in zip(pattern_parts, endpoint_parts)
                    )
                    if match:
                        return limit
        
        # Return default
        return RATE_LIMITS["default"]
    
    def _cleanup_old_requests(self, current_time: float):
        """Clean up old request records from memory."""
        cutoff_time = current_time - RATE_LIMIT_WINDOW
        
        # Clean global requests
        while self.global_requests and self.global_requests[0] < cutoff_time:
            self.global_requests.popleft()
        
        # Clean user requests (periodically)
        if int(current_time) % 60 == 0:  # Every minute
            for user_id in list(self.user_requests.keys()):
                for endpoint in list(self.user_requests[user_id].keys()):
                    requests = self.user_requests[user_id][endpoint]
                    while requests and requests[0] < cutoff_time:
                        requests.popleft()
                    
                    # Remove empty deques
                    if not requests:
                        del self.user_requests[user_id][endpoint]
                
                # Remove empty user entries
                if not self.user_requests[user_id]:
                    del self.user_requests[user_id]
    
    def _log_rate_limit_violation(
        self,
        user_id: str,
        endpoint: str,
        request_id: Optional[str]
    ):
        """Log rate limit violation to Firestore."""
        try:
            violation_data = {
                "user_id": user_id,
                "endpoint": endpoint,
                "request_id": request_id,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "type": "rate_limit_exceeded",
            }
            
            self.db.collection(RATE_LIMIT_COLLECTION).add(violation_data)
        except Exception as e:
            logger.error(f"Failed to log rate limit violation: {e}")
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get rate limit statistics for a user."""
        current_time = time.time()
        cutoff_time = current_time - RATE_LIMIT_WINDOW
        
        stats = {
            "user_id": user_id,
            "window_seconds": RATE_LIMIT_WINDOW,
            "endpoints": {},
            "total_requests": 0,
        }
        
        if user_id in self.user_requests:
            for endpoint, requests in self.user_requests[user_id].items():
                # Count requests in current window
                count = sum(1 for req_time in requests if req_time > cutoff_time)
                limit = self._get_endpoint_limit(endpoint)
                
                stats["endpoints"][endpoint] = {
                    "requests": count,
                    "limit": limit,
                    "remaining": max(0, limit - count),
                }
                stats["total_requests"] += count
        
        return stats


# Global rate limiter instance
_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(use_firestore=True)
    return _rate_limiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    
    Automatically checks rate limits for all requests and adds
    rate limit headers to responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/", "/api/docs", "/api/redoc", "/api/openapi.json"]:
            return await call_next(request)
        
        # Get user ID from request
        user_id = self._get_user_id(request)
        
        if not user_id:
            # No authentication, use IP address
            user_id = request.client.host if request.client else "anonymous"
        
        # Check rate limit
        rate_limiter = get_rate_limiter()
        allowed, info = rate_limiter.check_rate_limit(
            user_id=user_id,
            endpoint=request.url.path,
            request_id=request.headers.get("X-Request-ID")
        )
        
        if not allowed:
            # Rate limit exceeded
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "limit": info["limit"],
                    "retry_after": info["retry_after"],
                    "reset": info["reset"],
                },
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"]),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        return response
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request."""
        # Try to get from auth header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In production, decode JWT to get user ID
            # For now, use a hash of the token
            import hashlib
            token = auth_header[7:]
            return hashlib.md5(token.encode()).hexdigest()[:16]
        
        # Try to get from custom header
        user_id = request.headers.get("X-User-ID")
        if user_id:
            return user_id
        
        return None


# Module initialization
logger.info("Rate limiter middleware module loaded")
logger.info(f"Rate limits configured for {len(RATE_LIMITS)} endpoints")
logger.info(f"Global rate limit: {GLOBAL_RATE_LIMIT} requests per minute")
