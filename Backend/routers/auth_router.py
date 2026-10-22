"""
Authentication Router Module

This module defines FastAPI endpoints for parent authentication and registration
in the Mentor AI EdTech Platform. It exposes three registration methods:
email/password, phone number, and Google OAuth.

Endpoints:
- POST /register/parent/email: Register parent with email
- POST /register/parent/phone: Register parent with phone
- POST /register/parent/google: Register parent with Google OAuth

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from firebase_admin.auth import EmailAlreadyExistsError

from models.auth_models import (
    ParentEmailRegisterRequest,
    ParentPhoneRegisterRequest,
    ParentGoogleRegisterRequest,
    AuthResponse
)
from services import auth_service

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="",
    tags=["Authentication"]
)


@router.post(
    "/register/parent/email",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register parent with email",
    description="""
    Register a new parent account using email and password.
    
    This endpoint creates a new parent account with email/password credentials.
    After successful registration, the parent will receive an email verification
    link to verify their email address.
    
    **Requirements:**
    - Email must be valid and not already registered
    - Password must be at least 8 characters with letters and numbers
    - Language must be one of: en (English), hi (Hindi), mr (Marathi)
    
    **Returns:**
    - 201: Registration successful, email verification required
    - 400: Email already exists or validation error
    - 500: Internal server error
    """
)
async def register_parent_with_email(
    request: ParentEmailRegisterRequest
) -> AuthResponse:
    """
    Register a new parent using email and password.
    
    Args:
        request: ParentEmailRegisterRequest containing email, password, and language
    
    Returns:
        AuthResponse with parent_id, email, and verification status
    
    Raises:
        HTTPException: 400 if email exists or validation fails
        HTTPException: 500 if registration fails
    
    Example:
        Request:
        ```json
        {
            "email": "parent@example.com",
            "password": "SecurePass123",
            "language": "en"
        }
        ```
        
        Response:
        ```json
        {
            "parent_id": "abc123xyz456",
            "email": "parent@example.com",
            "phone": null,
            "verification_required": true,
            "message": "Registration successful. Please verify your email to continue."
        }
        ```
    """
    try:
        logger.info(f"Registration request received for email: {request.email}")
        
        # Call service layer to register parent
        result = auth_service.register_parent_with_email(
            email=request.email,
            password=request.password,
            language=request.language
        )
        
        logger.info(f"Parent registered successfully with email: {request.email}")
        
        return AuthResponse(**result)
    
    except ValueError as e:
        # Handle validation errors and duplicate email
        logger.warning(f"Validation error during email registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during email registration: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@router.post(
    "/register/parent/phone",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register parent with phone number",
    description="""
    Register a new parent account using phone number.
    
    This endpoint creates a new parent account with a phone number.
    After successful registration, the parent will receive an OTP
    for verification during the login process.
    
    **Requirements:**
    - Phone must be in format +91XXXXXXXXXX (Indian mobile number)
    - Phone number must not already be registered
    - Language must be one of: en (English), hi (Hindi), mr (Marathi)
    
    **Returns:**
    - 201: Registration successful, OTP verification required
    - 400: Phone already exists or validation error
    - 500: Internal server error
    """
)
async def register_parent_with_phone(
    request: ParentPhoneRegisterRequest
) -> AuthResponse:
    """
    Register a new parent using phone number.
    
    Args:
        request: ParentPhoneRegisterRequest containing phone and language
    
    Returns:
        AuthResponse with parent_id, phone, and verification status
    
    Raises:
        HTTPException: 400 if phone exists or validation fails
        HTTPException: 500 if registration fails
    
    Example:
        Request:
        ```json
        {
            "phone": "+919876543210",
            "language": "hi"
        }
        ```
        
        Response:
        ```json
        {
            "parent_id": "def456uvw789",
            "email": null,
            "phone": "+919876543210",
            "verification_required": true,
            "message": "Registration successful. You will receive an OTP for verification during login."
        }
        ```
    """
    try:
        logger.info(f"Registration request received for phone: {request.phone}")
        
        # Call service layer to register parent
        result = auth_service.register_parent_with_phone(
            phone=request.phone,
            language=request.language
        )
        
        logger.info(f"Parent registered successfully with phone: {request.phone}")
        
        return AuthResponse(**result)
    
    except ValueError as e:
        # Handle validation errors and duplicate phone
        logger.warning(f"Validation error during phone registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during phone registration: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@router.post(
    "/register/parent/google",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register/Login parent with Google OAuth",
    description="""
    Register or login a parent account using Google Sign-In.
    
    This endpoint handles both new registrations and existing user logins
    using Google OAuth. The Google ID token is verified on the backend,
    and user information is extracted to create or update the parent account.
    
    **Requirements:**
    - Valid Google ID token from Google Sign-In
    - Language preference (optional, defaults to English)
    
    **Features:**
    - No email verification required (Google users are pre-verified)
    - Automatically creates account for new users
    - Updates language preference for existing users
    
    **Returns:**
    - 201: Registration/Login successful
    - 400: Invalid Google ID token
    - 500: Internal server error
    """
)
async def register_parent_with_google(
    request: ParentGoogleRegisterRequest
) -> AuthResponse:
    """
    Register or login a parent using Google OAuth.
    
    Args:
        request: ParentGoogleRegisterRequest containing Google ID token and language
    
    Returns:
        AuthResponse with parent_id, email, and verification status
    
    Raises:
        HTTPException: 400 if Google token is invalid
        HTTPException: 500 if registration/login fails
    
    Example:
        Request:
        ```json
        {
            "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...",
            "language": "en"
        }
        ```
        
        Response:
        ```json
        {
            "parent_id": "google_ghi789rst012",
            "email": "parent@gmail.com",
            "phone": null,
            "verification_required": false,
            "message": "Registration successful. Welcome to Mentor AI!"
        }
        ```
    """
    try:
        logger.info("Registration/Login request received for Google OAuth")
        
        # Call service layer to register/login parent
        result = auth_service.register_parent_with_google(
            id_token=request.id_token,
            language=request.language
        )
        
        logger.info(f"Parent registered/logged in successfully via Google OAuth")
        
        return AuthResponse(**result)
    
    except ValueError as e:
        # Handle invalid Google token and validation errors
        logger.warning(f"Validation error during Google registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during Google registration: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration/Login failed. Please try again later."
        )
