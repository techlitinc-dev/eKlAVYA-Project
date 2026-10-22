"""
Authentication Middleware Module

This module provides authentication middleware and dependency functions for
protecting endpoints in the Mentor AI EdTech Platform. It handles JWT token
verification, session validation, and user authentication.

Functions:
- verify_auth_token: Middleware for automatic token verification
- get_current_user: Dependency for protected endpoints
- extract_token: Helper to parse Authorization header
- is_token_revoked: Helper to check session revocation status

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import hashlib
from typing import Optional, Callable

from fastapi import Request, Header, Depends, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import jwt

from services import token_service
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)


def extract_token(authorization: Optional[str]) -> str:
    """
    Extract JWT token from Authorization header.
    
    Parses the "Bearer <token>" format and extracts the token.
    
    Args:
        authorization: Authorization header value
    
    Returns:
        str: Extracted JWT token
    
    Raises:
        HTTPException: 401 if header is missing or invalid format
    
    Example:
        >>> token = extract_token("Bearer eyJhbGci...")
        >>> print(token[:20])
        'eyJhbGciOiJIUzI1NiIs'
    """
    if not authorization:
        logger.warning("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Check if header starts with "Bearer "
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token
    token = authorization[7:].strip()  # Remove "Bearer " prefix
    
    if not token:
        logger.warning("Token missing in authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing in authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return token


def is_token_revoked(token: str) -> bool:
    """
    Check if a token has been revoked.
    
    Queries the sessions collection in Firestore to check if the
    session associated with the token has been revoked.
    
    Args:
        token: JWT token string
    
    Returns:
        bool: True if token is revoked or session not found, False if active
    
    Example:
        >>> revoked = is_token_revoked("eyJhbGci...")
        >>> print(revoked)
        False
    """
    try:
        # Hash token for lookup
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Query sessions collection
        sessions_ref = db.collection("sessions")
        query = sessions_ref.where("token_hash", "==", token_hash).limit(1)
        docs = list(query.stream())
        
        # If no session found, consider token revoked
        if not docs:
            logger.warning("Session not found for token")
            return True
        
        # Get session data
        session_data = docs[0].to_dict()
        
        # Check if session is revoked
        is_revoked = session_data.get("revoked", False)
        
        if is_revoked:
            logger.info("Token has been revoked")
        
        return is_revoked
    
    except Exception as e:
        logger.error(f"Error checking token revocation status: {e}")
        # On error, consider token revoked for security
        return True


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Dependency function to get current authenticated user.
    
    This dependency can be used in FastAPI route handlers to protect
    endpoints and automatically extract the authenticated user's ID.
    
    Args:
        authorization: Authorization header containing Bearer token
    
    Returns:
        str: Parent ID of the authenticated user
    
    Raises:
        HTTPException: 401 if authentication fails
    
    Example:
        >>> @router.get("/profile")
        >>> async def get_profile(user_id: str = Depends(get_current_user)):
        ...     return {"user_id": user_id}
    """
    try:
        logger.debug("Authenticating user from token")
        
        # Extract token from header
        token = extract_token(authorization)
        
        # Verify token
        try:
            payload = token_service.verify_token(token)
            
            # Check for either parent_id or student_id (for child tokens)
            parent_id = payload.get("parent_id")
            student_id = payload.get("student_id")
            user_id = parent_id or student_id
            
            if not user_id:
                logger.error("Token payload missing parent_id or student_id")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user information",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            user_type = "parent" if parent_id else "student"
            logger.debug(f"Token verified for {user_type}: {user_id}")
        
        except jwt.ExpiredSignatureError:
            logger.warning("Access token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if token is revoked
        if is_token_revoked(token):
            logger.warning(f"Revoked token used by {user_type}: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        logger.info(f"User authenticated successfully: {user_type} {user_id}")
        
        return user_id
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error during authentication: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware for automatic token verification.
    
    This middleware automatically verifies JWT tokens for incoming requests.
    If a valid token is present, it adds the user_id to request.state.
    Public endpoints (without Authorization header) are allowed through.
    
    Usage:
        app.add_middleware(AuthMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process incoming request and verify authentication.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware or endpoint handler
        
        Returns:
            Response from the next handler
        
        Raises:
            HTTPException: 401 if token is invalid or revoked
        """
        # Get Authorization header
        authorization = request.headers.get("Authorization")
        
        # If no authorization header, allow request (public endpoint)
        if not authorization:
            logger.debug(f"Public endpoint accessed: {request.url.path}")
            return await call_next(request)
        
        try:
            # Extract token
            token = extract_token(authorization)
            
            # Verify token
            try:
                payload = token_service.verify_token(token)
                parent_id = payload.get("parent_id")
                
                if not parent_id:
                    logger.error("Token payload missing parent_id")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token: missing user information",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                logger.debug(f"Token verified for parent: {parent_id}")
            
            except jwt.ExpiredSignatureError:
                logger.warning("Access token has expired")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid access token: {e}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check if token is revoked
            if is_token_revoked(token):
                logger.warning(f"Revoked token used by parent: {parent_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked. Please login again.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Add user_id to request state for downstream handlers
            request.state.user_id = parent_id
            logger.debug(f"User authenticated via middleware: {parent_id}")
        
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        
        except Exception as e:
            # Log unexpected errors but don't block public endpoints
            logger.error(f"Error in auth middleware: {e}")
            logger.exception("Full traceback:")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Call next middleware or endpoint
        return await call_next(request)


async def verify_auth_token(request: Request, call_next: Callable):
    """
    Middleware function for token verification.
    
    This is a standalone middleware function that can be added to FastAPI
    using app.middleware("http").
    
    Args:
        request: Incoming HTTP request
        call_next: Next middleware or endpoint handler
    
    Returns:
        Response from the next handler
    
    Usage:
        @app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            return await verify_auth_token(request, call_next)
    """
    # Get Authorization header
    authorization = request.headers.get("Authorization")
    
    # If no authorization header, allow request (public endpoint)
    if not authorization:
        logger.debug(f"Public endpoint accessed: {request.url.path}")
        return await call_next(request)
    
    try:
        # Extract token
        token = extract_token(authorization)
        
        # Verify token
        try:
            payload = token_service.verify_token(token)
            parent_id = payload.get("parent_id")
            
            if not parent_id:
                logger.error("Token payload missing parent_id")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user information",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            logger.debug(f"Token verified for parent: {parent_id}")
        
        except jwt.ExpiredSignatureError:
            logger.warning("Access token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if token is revoked
        if is_token_revoked(token):
            logger.warning(f"Revoked token used by parent: {parent_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked. Please login again.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Add user_id to request state for downstream handlers
        request.state.user_id = parent_id
        logger.debug(f"User authenticated via middleware: {parent_id}")
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Error in auth middleware: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Call next middleware or endpoint
    return await call_next(request)
