"""
Login Router Module

This module defines FastAPI endpoints for authentication and session management
in the Mentor AI EdTech Platform. It exposes login endpoints for email, phone,
and Google OAuth, along with token refresh, logout, and protected endpoints.

Endpoints:
- POST /login/email: Login with email and password
- POST /login/phone: Login with phone and OTP
- POST /login/google: Login with Google OAuth
- POST /token/refresh: Refresh access token
- POST /logout: Logout and revoke session
- GET /me: Get current parent profile (protected)

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Header
import jwt

from models.login_models import (
    EmailLoginRequest,
    PhoneLoginRequest,
    GoogleLoginRequest,
    TokenRefreshRequest,
    LoginResponse,
    TokenResponse,
    LogoutResponse,
    ChildLoginRequest
)
from services import login_service, token_service
from utils.firebase_config import get_firestore_client

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="",
    tags=["Login"]
)


def extract_token_from_header(authorization: Optional[str]) -> str:
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
        >>> token = extract_token_from_header("Bearer eyJhbGci...")
        >>> print(token[:20])
        'eyJhbGciOiJIUzI1NiIs'
    """
    if not authorization:
        logger.warning("Authorization header missing")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )
    
    # Check if header starts with "Bearer "
    if not authorization.startswith("Bearer "):
        logger.warning(f"Invalid authorization header format: {authorization[:20]}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )
    
    # Extract token
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if not token:
        logger.warning("Token missing in authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing in authorization header"
        )
    
    return token


@router.post(
    "/login/email",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    description="""
    Authenticate parent using email and password.
    
    This endpoint verifies the parent's credentials and returns JWT tokens
    for session management. The access token is used for API authentication,
    while the refresh token is used to obtain new access tokens.
    
    **Requirements:**
    - Email must be registered in the system
    - Password must match the registered password
    
    **Returns:**
    - 200: Login successful with tokens and parent information
    - 401: Invalid email or password
    - 404: Parent profile not found
    - 500: Internal server error
    
    **Tokens:**
    - Access Token: Valid for 24 hours
    - Refresh Token: Valid for 30 days
    """
)
async def login_with_email(
    request: EmailLoginRequest
) -> LoginResponse:
    """
    Login parent with email and password.
    
    Args:
        request: EmailLoginRequest containing email and password
    
    Returns:
        LoginResponse with tokens and parent information
    
    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 404 if user not found
        HTTPException: 500 if login fails
    
    Example:
        Request:
        ```json
        {
            "email": "parent@example.com",
            "password": "SecurePass123"
        }
        ```
        
        Response:
        ```json
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "parent_id": "parent_123abc",
            "email": "parent@example.com",
            "phone": null,
            "expires_in": 86400
        }
        ```
    """
    try:
        logger.info(f"Email login request for: {request.email}")
        
        # Call service layer to authenticate
        result = login_service.login_with_email(
            email=request.email,
            password=request.password
        )
        
        logger.info(f"Email login successful for: {request.email}")
        
        return LoginResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid credentials, user not found)
        error_message = str(e)
        logger.warning(f"Login validation error: {error_message}")
        
        # Check if it's a user not found error
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        
        # Invalid credentials
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during email login: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.post(
    "/login/phone",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with phone and OTP",
    description="""
    Authenticate parent using phone number and OTP.
    
    This endpoint verifies the OTP sent to the parent's phone number
    and returns JWT tokens for session management.
    
    **Requirements:**
    - Phone number must be registered in the system
    - OTP must be valid and not expired (valid for 10 minutes)
    - OTP must not have been used before
    
    **Returns:**
    - 200: Login successful with tokens and parent information
    - 401: Invalid or expired OTP
    - 404: Parent profile not found
    - 500: Internal server error
    
    **Tokens:**
    - Access Token: Valid for 24 hours
    - Refresh Token: Valid for 30 days
    """
)
async def login_with_phone(
    request: PhoneLoginRequest
) -> LoginResponse:
    """
    Login parent with phone number and OTP.
    
    Args:
        request: PhoneLoginRequest containing phone and OTP
    
    Returns:
        LoginResponse with tokens and parent information
    
    Raises:
        HTTPException: 401 if OTP is invalid or expired
        HTTPException: 404 if user not found
        HTTPException: 500 if login fails
    
    Example:
        Request:
        ```json
        {
            "phone": "+919876543210",
            "otp": "123456"
        }
        ```
        
        Response:
        ```json
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "parent_id": "parent_def456",
            "email": null,
            "phone": "+919876543210",
            "expires_in": 86400
        }
        ```
    """
    try:
        logger.info(f"Phone login request for: {request.phone}")
        
        # Call service layer to authenticate
        # For testing, make OTP optional
        otp = getattr(request, 'otp', None)
        result = login_service.login_with_phone(
            phone=request.phone,
            otp=otp
        )
        
        logger.info(f"Phone login successful for: {request.phone}")
        
        return LoginResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid OTP, user not found)
        error_message = str(e)
        logger.warning(f"Login validation error: {error_message}")
        
        # Check if it's a user not found error
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        
        # Invalid or expired OTP
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during phone login: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.post(
    "/login/google",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with Google OAuth",
    description="""
    Authenticate parent using Google Sign-In.
    
    This endpoint verifies the Google ID token and returns JWT tokens
    for session management. If the user doesn't exist, a new account
    is automatically created.
    
    **Requirements:**
    - Valid Google ID token from Google Sign-In
    
    **Returns:**
    - 200: Login successful with tokens and parent information
    - 401: Invalid Google ID token
    - 500: Internal server error
    
    **Features:**
    - Automatically creates new user if not registered
    - Email is pre-verified (from Google)
    - No password required
    
    **Tokens:**
    - Access Token: Valid for 24 hours
    - Refresh Token: Valid for 30 days
    """
)
async def login_with_google(
    request: GoogleLoginRequest
) -> LoginResponse:
    """
    Login parent with Google OAuth.
    
    Args:
        request: GoogleLoginRequest containing Google ID token
    
    Returns:
        LoginResponse with tokens and parent information
    
    Raises:
        HTTPException: 401 if Google token is invalid
        HTTPException: 500 if login fails
    
    Example:
        Request:
        ```json
        {
            "id_token": "eyJhbGciOiJSUzI1NiIs..."
        }
        ```
        
        Response:
        ```json
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "parent_id": "google_user_ghi789",
            "email": "parent@gmail.com",
            "phone": null,
            "expires_in": 86400
        }
        ```
    """
    try:
        logger.info("Google OAuth login request received")
        
        # Call service layer to authenticate
        result = login_service.login_with_google(
            id_token=request.id_token
        )
        
        logger.info(f"Google login successful for: {result.get('email')}")
        
        return LoginResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid Google token)
        error_message = str(e)
        logger.warning(f"Google login validation error: {error_message}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during Google login: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="""
    Obtain a new access token using a refresh token.
    
    This endpoint allows clients to refresh expired access tokens
    without requiring the user to login again. The refresh token
    must be valid and not revoked.
    
    **Requirements:**
    - Valid refresh token
    - Refresh token must not be expired (valid for 30 days)
    - Session must not be revoked
    
    **Returns:**
    - 200: New tokens generated successfully
    - 401: Invalid, expired, or revoked refresh token
    - 500: Internal server error
    
    **Token Rotation:**
    - Both access and refresh tokens are rotated for security
    - Old tokens are invalidated after refresh
    """
)
async def refresh_token(
    request: TokenRefreshRequest
) -> TokenResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: TokenRefreshRequest containing refresh token
    
    Returns:
        TokenResponse with new access and refresh tokens
    
    Raises:
        HTTPException: 401 if refresh token is invalid or expired
        HTTPException: 500 if token refresh fails
    
    Example:
        Request:
        ```json
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        }
        ```
        
        Response:
        ```json
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "expires_in": 86400
        }
        ```
    """
    try:
        logger.info("Token refresh request received")
        
        # Call service layer to refresh token
        result = login_service.refresh_access_token(
            refresh_token=request.refresh_token
        )
        
        logger.info("Token refreshed successfully")
        
        return TokenResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid, expired, or revoked token)
        error_message = str(e)
        logger.warning(f"Token refresh validation error: {error_message}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error refreshing token: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again later."
        )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout and revoke session",
    description="""
    Logout parent and revoke the current session.
    
    This endpoint invalidates the current session and marks it as revoked
    in the database. The access token will no longer be valid after logout.
    
    **Requirements:**
    - Valid Authorization header with Bearer token
    
    **Returns:**
    - 200: Logout successful
    - 401: Invalid or missing token
    - 500: Internal server error
    
    **Note:**
    - Session is revoked immediately
    - Token cannot be used after logout
    - Refresh token is also invalidated
    """
)
async def logout(
    authorization: Optional[str] = Header(None)
) -> LogoutResponse:
    """
    Logout parent by revoking session.
    
    Args:
        authorization: Authorization header containing Bearer token
    
    Returns:
        LogoutResponse with confirmation message
    
    Raises:
        HTTPException: 401 if token is invalid or missing
        HTTPException: 500 if logout fails
    
    Example:
        Headers:
        ```
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
        ```
        
        Response:
        ```json
        {
            "message": "Logout successful"
        }
        ```
    """
    try:
        # Extract token from header
        token = extract_token_from_header(authorization)
        
        logger.info("Logout request received")
        
        # Call service layer to logout
        result = login_service.logout(token=token)
        
        logger.info("Logout successful")
        
        return LogoutResponse(**result)
    
    except HTTPException:
        # Re-raise HTTPExceptions from extract_token_from_header
        raise
    
    except ValueError as e:
        # Handle validation errors (invalid token, session not found)
        error_message = str(e)
        logger.warning(f"Logout validation error: {error_message}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during logout: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again later."
        )


@router.get(
    "/me",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get current parent profile",
    description="""
    Get the authenticated parent's profile information.
    
    This is a protected endpoint that requires a valid access token.
    It returns the parent's profile data from Firestore.
    
    **Requirements:**
    - Valid Authorization header with Bearer token
    - Token must not be expired
    
    **Returns:**
    - 200: Parent profile data
    - 401: Invalid, missing, or expired token
    - 404: Parent profile not found
    - 500: Internal server error
    
    **Use Cases:**
    - Get current user information
    - Display user profile
    - Verify authentication status
    """
)
async def get_current_parent(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get current authenticated parent's profile.
    
    Args:
        authorization: Authorization header containing Bearer token
    
    Returns:
        Dict containing parent profile data
    
    Raises:
        HTTPException: 401 if token is invalid, missing, or expired
        HTTPException: 404 if parent profile not found
        HTTPException: 500 if request fails
    
    Example:
        Headers:
        ```
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
        ```
        
        Response:
        ```json
        {
            "parent_id": "parent_123abc",
            "email": "parent@example.com",
            "phone": null,
            "language": "en",
            "role": "parent",
            "email_verified": true,
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        # Extract token from header
        token = extract_token_from_header(authorization)
        
        logger.info("Get current parent profile request")
        
        # Verify token and extract payload
        try:
            payload = token_service.verify_token(token)
            parent_id = payload.get("parent_id")
            
            if not parent_id:
                raise ValueError("Invalid token: missing parent_id")
            
            logger.info(f"Token verified for parent: {parent_id}")
        
        except jwt.ExpiredSignatureError:
            logger.warning("Access token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please login again."
            )
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please login again."
            )
        
        # Get parent profile from Firestore
        db = get_firestore_client()
        parents_ref = db.collection("parents")
        parent_doc = parents_ref.document(parent_id).get()
        
        if not parent_doc.exists:
            logger.error(f"Parent profile not found for ID: {parent_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent profile not found"
            )
        
        # Get parent data
        parent_data = parent_doc.to_dict()
        
        logger.info(f"Parent profile retrieved successfully for: {parent_id}")
        
        return parent_data
    
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error getting parent profile: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get parent profile. Please try again later."
        )


@router.post(
    "/login/child",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with child username and password",
    description="""
    Authenticate child/student using username and password provided by parent.
    
    This endpoint verifies the child's credentials and returns JWT tokens
    for session management. Children use their username (not email) to login.
    
    **Requirements:**
    - Username must be created by parent during child profile setup
    - Password must match the password set by parent
    - Child profile must exist and be active
    
    **Returns:**
    - 200: Login successful with tokens and child information
    - 401: Invalid username or password
    - 404: Child profile not found
    - 500: Internal server error
    
    **Tokens:**
    - Access Token: Valid for 24 hours
    - Refresh Token: Valid for 30 days
    """
)
async def login_child(
    request: ChildLoginRequest
) -> LoginResponse:
    """
    Login child with username and password.
    
    Args:
        request: ChildLoginRequest containing username and password
    
    Returns:
        LoginResponse with tokens and child information
    
    Raises:
        HTTPException: 401 if credentials are invalid
        HTTPException: 404 if child not found
        HTTPException: 500 if login fails
    
    Example:
        Request:
        ```json
        {
            "username": "rahul123",
            "password": "SecurePass123"
        }
        ```
        
        Response:
        ```json
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "parent_id": "parent_abc123",
            "student_id": "child_def456",
            "child_id": "child_def456",
            "username": "rahul123",
            "name": "Rahul Sharma",
            "email": "rahul123@student.local",
            "is_student": true,
            "expires_in": 86400,
            "message": "Child login successful"
        }
        ```
    """
    try:
        logger.info(f"Child login request for username: {request.username}")
        
        # Call service layer to authenticate child
        result = login_service.login_child(
            username=request.username,
            password=request.password
        )
        
        logger.info(f"Child login successful for username: {request.username}")
        
        return LoginResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid credentials, child not found)
        error_message = str(e)
        logger.warning(f"Child login validation error: {error_message}")
        
        # Check if it's a not found error
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        
        # Invalid credentials
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during child login: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Child login failed. Please try again later."
        )


@router.post(
    "/token/refresh/child",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh child access token",
    description="""
    Obtain a new child access token using a child refresh token.
    
    This endpoint allows child clients to refresh expired access tokens
    without requiring the user to login again. The refresh token
    must be valid and not revoked.
    
    **Requirements:**
    - Valid child refresh token
    - Refresh token must not be expired (valid for 30 days)
    - Child session must not be revoked
    
    **Returns:**
    - 200: New tokens generated successfully
    - 401: Invalid, expired, or revoked refresh token
    - 500: Internal server error
    
    **Token Rotation:**
    - Both access and refresh tokens are rotated for security
    - Old tokens are invalidated after refresh
    """
)
async def refresh_child_token(
    request: TokenRefreshRequest
) -> TokenResponse:
    """
    Refresh child access token using refresh token.
    
    Args:
        request: TokenRefreshRequest containing child refresh token
    
    Returns:
        TokenResponse with new access and refresh tokens
    
    Raises:
        HTTPException: 401 if refresh token is invalid or expired
        HTTPException: 500 if token refresh fails
    
    Example:
        Request:
        ```json
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
        }
        ```
        
        Response:
        ```json
        {
            "token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "expires_in": 86400
        }
        ```
    """
    try:
        logger.info("Child token refresh request received")
        
        # Call service layer to refresh child token
        result = login_service.refresh_child_access_token(
            refresh_token=request.refresh_token
        )
        
        logger.info("Child token refreshed successfully")
        
        return TokenResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid, expired, or revoked token)
        error_message = str(e)
        logger.warning(f"Child token refresh validation error: {error_message}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error refreshing child token: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Child token refresh failed. Please try again later."
        )


@router.post(
    "/logout/child",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout child and revoke session",
    description="""
    Logout child and revoke the current session.
    
    This endpoint invalidates the current child session and marks it as revoked
    in the database. The access token will no longer be valid after logout.
    
    **Requirements:**
    - Valid Authorization header with Bearer token (child token)
    
    **Returns:**
    - 200: Logout successful
    - 401: Invalid or missing token
    - 500: Internal server error
    
    **Note:**
    - Session is revoked immediately
    - Token cannot be used after logout
    - Refresh token is also invalidated
    """
)
async def logout_child(
    authorization: Optional[str] = Header(None)
) -> LogoutResponse:
    """
    Logout child by revoking session.
    
    Args:
        authorization: Authorization header containing Bearer token
    
    Returns:
        LogoutResponse with confirmation message
    
    Raises:
        HTTPException: 401 if token is invalid or missing
        HTTPException: 500 if logout fails
    
    Example:
        Headers:
        ```
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
        ```
        
        Response:
        ```json
        {
            "message": "Child logout successful"
        }
        ```
    """
    try:
        # Extract token from header
        token = extract_token_from_header(authorization)
        
        logger.info("Child logout request received")
        
        # Call service layer to logout child
        result = login_service.logout_child(token=token)
        
        logger.info("Child logout successful")
        
        return LogoutResponse(**result)
    
    except HTTPException:
        # Re-raise HTTPExceptions from extract_token_from_header
        raise
    
    except ValueError as e:
        # Handle validation errors (invalid token, session not found)
        error_message = str(e)
        logger.warning(f"Child logout validation error: {error_message}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during child logout: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Child logout failed. Please try again later."
        )


@router.get(
    "/me/child",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get current child profile",
    description="""
    Get the authenticated child's profile information.
    
    This is a protected endpoint that requires a valid child access token.
    It returns the child's profile data from Firestore.
    
    **Requirements:**
    - Valid Authorization header with Bearer token (child token)
    - Token must not be expired
    
    **Returns:**
    - 200: Child profile data
    - 401: Invalid, missing, or expired token
    - 404: Child profile not found
    - 500: Internal server error
    
    **Use Cases:**
    - Get current child user information
    - Display child profile
    - Verify child authentication status
    """
)
async def get_current_child(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    Get current authenticated child's profile.
    
    Args:
        authorization: Authorization header containing Bearer token
    
    Returns:
        Dict containing child profile data
    
    Raises:
        HTTPException: 401 if token is invalid, missing, or expired
        HTTPException: 404 if child profile not found
        HTTPException: 500 if request fails
    
    Example:
        Headers:
        ```
        Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
        ```
        
        Response:
        ```json
        {
            "child_id": "child_abc123",
            "parent_id": "parent_xyz789",
            "name": "Rahul Sharma",
            "username": "rahul123",
            "age": 16,
            "grade": 11,
            "current_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-15T10:30:00Z"
        }
        ```
    """
    try:
        # Extract token from header
        token = extract_token_from_header(authorization)
        
        logger.info("Get current child profile request")
        
        # Verify token and extract payload
        try:
            payload = token_service.verify_token(token)
            is_student = payload.get("is_student", False)
            
            if not is_student:
                raise ValueError("Invalid token: not a student token")
            
            child_id = payload.get("child_id") or payload.get("student_id")
            
            if not child_id:
                raise ValueError("Invalid token: missing child_id")
            
            logger.info(f"Child token verified for ID: {child_id}")
        
        except jwt.ExpiredSignatureError:
            logger.warning("Child access token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired. Please login again."
            )
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid child access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token. Please login again."
            )
        
        # Get child profile from Firestore
        db = get_firestore_client()
        children_ref = db.collection("children")
        child_doc = children_ref.document(child_id).get()
        
        if not child_doc.exists:
            logger.error(f"Child profile not found for ID: {child_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child profile not found"
            )
        
        # Get child data
        child_data = child_doc.to_dict()
        child_data["child_id"] = child_id  # Include document ID
        
        logger.info(f"Child profile retrieved successfully for: {child_id}")
        
        return child_data
    
    except HTTPException:
        # Re-raise HTTPExceptions
        raise
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error getting child profile: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get child profile. Please try again later."
        )
