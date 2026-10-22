"""
Verification Router Module

This module defines FastAPI endpoints for email and phone verification
in the Mentor AI EdTech Platform. It exposes four verification endpoints
for sending and confirming email/phone verification codes.

Endpoints:
- POST /verify/email/send: Send email verification code
- POST /verify/email/confirm: Confirm email with verification code
- POST /verify/phone/send: Send phone OTP
- POST /verify/phone/confirm: Confirm phone with OTP

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status, Depends

from models.verification_models import (
    SendEmailVerificationRequest,
    ConfirmEmailVerificationRequest,
    SendPhoneOTPRequest,
    ConfirmPhoneOTPRequest,
    VerificationResponse
)
from services import verification_service
from middleware.testing_auth import get_current_user_testing as get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(
    prefix="",
    tags=["Verification"]
)


@router.post(
    "/verify/email/send",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Send email verification code",
    description="""
    Send a verification code to the parent's email address.
    
    This endpoint generates a 6-character alphanumeric verification code
    and sends it to the specified email address. The code is valid for
    10 minutes and can be used to verify email ownership.
    
    **Requirements:**
    - Email must be a valid email address
    - Email should be associated with a registered parent account
    
    **Returns:**
    - 200: Verification code sent successfully
    - 400: Invalid email format or validation error
    - 500: Internal server error
    
    **Note:** In production, the verification code is sent via email.
    In development, it's returned in the response for testing purposes.
    """
)
async def send_email_verification(
    request: SendEmailVerificationRequest,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send email verification code to parent.
    
    Args:
        request: SendEmailVerificationRequest containing email address
    
    Returns:
        Dict with message and verification code (dev only)
    
    Raises:
        HTTPException: 400 if email is invalid
        HTTPException: 500 if sending fails
    
    Example:
        Request:
        ```json
        {
            "email": "parent@example.com"
        }
        ```
        
        Response:
        ```json
        {
            "message": "Verification email sent",
            "code": "ABC123"
        }
        ```
    """
    try:
        logger.info(f"Email verification request received for: {request.email}")
        
        # Call service layer to send verification code
        result = verification_service.send_email_verification(
            email=request.email
        )
        
        logger.info(f"Email verification code sent to: {request.email}")
        
        return result
    
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error sending email verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error sending email verification: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email. Please try again later."
        )


@router.post(
    "/verify/email/confirm",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm email with verification code",
    description="""
    Verify email address using the verification code.
    
    This endpoint validates the 6-character verification code sent to
    the parent's email. If valid, it marks the email as verified in
    both Firebase Auth and Firestore.
    
    **Requirements:**
    - Email must match the one used to request verification
    - Code must be exactly 6 alphanumeric characters
    - Code must not be expired (valid for 10 minutes)
    - Code must not have been used before
    
    **Returns:**
    - 200: Email verified successfully
    - 400: Invalid or expired verification code
    - 404: User not found
    - 500: Internal server error
    """
)
async def confirm_email_verification(
    request: ConfirmEmailVerificationRequest
) -> VerificationResponse:
    """
    Confirm email verification with code.
    
    Args:
        request: ConfirmEmailVerificationRequest containing email and code
    
    Returns:
        VerificationResponse with verification status
    
    Raises:
        HTTPException: 400 if code is invalid or expired
        HTTPException: 404 if user not found
        HTTPException: 500 if confirmation fails
    
    Example:
        Request:
        ```json
        {
            "email": "parent@example.com",
            "code": "ABC123"
        }
        ```
        
        Response:
        ```json
        {
            "verified": true,
            "message": "Email verified successfully"
        }
        ```
    """
    try:
        logger.info(f"Email confirmation request received for: {request.email}")
        
        # Call service layer to confirm verification
        result = verification_service.confirm_email_verification(
            email=request.email,
            code=request.code
        )
        
        logger.info(f"Email verified successfully for: {request.email}")
        
        return VerificationResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid code, expired, used)
        error_message = str(e)
        logger.warning(f"Validation error confirming email verification: {error_message}")
        
        # Check if it's a user not found error
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error confirming email verification: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm email verification. Please try again later."
        )


@router.post(
    "/verify/phone/send",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Send phone OTP",
    description="""
    Send a one-time password (OTP) to the parent's phone number.
    
    This endpoint generates a 6-digit numeric OTP and sends it to
    the specified phone number via SMS. The OTP is valid for 10 minutes
    and can be used to verify phone number ownership.
    
    **Requirements:**
    - Phone must be in format +91XXXXXXXXXX (Indian mobile number)
    - Phone should be associated with a registered parent account
    
    **Returns:**
    - 200: OTP sent successfully
    - 400: Invalid phone format or validation error
    - 500: Internal server error
    
    **Note:** In production, the OTP is sent via SMS.
    In development, it's returned in the response for testing purposes.
    """
)
async def send_phone_otp(
    request: SendPhoneOTPRequest,
    current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send OTP to parent's phone number.
    
    Args:
        request: SendPhoneOTPRequest containing phone number
    
    Returns:
        Dict with message and OTP (dev only)
    
    Raises:
        HTTPException: 400 if phone format is invalid
        HTTPException: 500 if sending fails
    
    Example:
        Request:
        ```json
        {
            "phone": "+919876543210"
        }
        ```
        
        Response:
        ```json
        {
            "message": "OTP sent",
            "otp": "123456"
        }
        ```
    """
    try:
        logger.info(f"Phone OTP request received for: {request.phone}")
        
        # Call service layer to send OTP
        result = verification_service.send_phone_otp(
            phone=request.phone
        )
        
        logger.info(f"Phone OTP sent to: {request.phone}")
        
        return result
    
    except ValueError as e:
        # Handle validation errors
        logger.warning(f"Validation error sending phone OTP: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error sending phone OTP: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again later."
        )


@router.post(
    "/verify/phone/confirm",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirm phone with OTP",
    description="""
    Verify phone number using the OTP.
    
    This endpoint validates the 6-digit OTP sent to the parent's phone.
    If valid, it marks the phone number as verified in Firestore.
    
    **Requirements:**
    - Phone must match the one used to request OTP
    - OTP must be exactly 6 numeric digits
    - OTP must not be expired (valid for 10 minutes)
    - OTP must not have been used before
    
    **Returns:**
    - 200: Phone verified successfully
    - 400: Invalid or expired OTP
    - 404: User not found
    - 500: Internal server error
    """
)
async def confirm_phone_otp(
    request: ConfirmPhoneOTPRequest,
    current_user: str = Depends(get_current_user)
) -> VerificationResponse:
    """
    Confirm phone verification with OTP.
    
    Args:
        request: ConfirmPhoneOTPRequest containing phone and OTP
    
    Returns:
        VerificationResponse with verification status
    
    Raises:
        HTTPException: 400 if OTP is invalid or expired
        HTTPException: 404 if user not found
        HTTPException: 500 if confirmation fails
    
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
            "verified": true,
            "message": "Phone verified successfully"
        }
        ```
    """
    try:
        logger.info(f"Phone OTP confirmation request received for: {request.phone}")
        
        # Call service layer to confirm verification
        result = verification_service.confirm_phone_otp(
            phone=request.phone,
            otp=request.otp
        )
        
        logger.info(f"Phone verified successfully for: {request.phone}")
        
        return VerificationResponse(**result)
    
    except ValueError as e:
        # Handle validation errors (invalid OTP, expired, used)
        error_message = str(e)
        logger.warning(f"Validation error confirming phone OTP: {error_message}")
        
        # Check if it's a user not found error
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_message
            )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    except Exception as e:
        # Handle unexpected server errors
        logger.error(f"Error confirming phone OTP: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm phone verification. Please try again later."
        )
