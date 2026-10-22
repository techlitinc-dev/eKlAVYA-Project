"""
Simple Registration Router
"""

import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from models.auth_models import AuthResponse
from services.simple_register_service import register_user_simple

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="",
    tags=["Registration"]
)


class SimpleRegisterRequest(BaseModel):
    """Request model for simple registration."""
    name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    email_address: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="Account password")
    repeat_password: str = Field(..., min_length=8, description="Password confirmation")
    mobile_number: str = Field(default="+91XXXXXXXXXX", description="Mobile number")


@router.post(
    "/register/simple",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Simple user registration",
    description="""
    Register a new user without email verification.
    
    This is a simplified registration endpoint that creates a user
    directly in Firebase Auth and Firestore without requiring email verification.
    
    **Requirements:**
    - User's full name
    - Mobile number (in +91XXXXXXXXXX format)
    - Email address
    - Password (minimum 8 characters)
    - Repeat password for confirmation
    
    **Returns:**
    - 201: Registration successful
    - 400: Validation error or email already exists
    - 500: Internal server error
    
    **Features:**
    - No email verification required
    - Immediate account creation
    """
)
async def register_simple(
    request: SimpleRegisterRequest
) -> AuthResponse:
    """
    Register a new user without email verification.
    
    Args:
        request: SimpleRegisterRequest with user registration data
    
    Returns:
        AuthResponse with registration status and user info
    
    Raises:
        HTTPException: 400 if validation fails or email exists
        HTTPException: 500 if registration fails
    """
    try:
        logger.info(f"Simple registration request for: {request.email_address}")
        
        # Call service layer to register user
        result = register_user_simple(
            name=request.name,
            mobile_number=request.mobile_number,
            email_address=request.email_address,
            password=request.password,
            repeat_password=request.repeat_password
        )
        
        logger.info(f"User registered successfully: {request.email_address}")
        
        return AuthResponse(**result)
    
    except ValueError as e:
        # Handle validation errors
        error_message = str(e)
        logger.warning(f"Registration validation error: {error_message}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error during registration: {e}")
        logger.exception("Full traceback:")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )