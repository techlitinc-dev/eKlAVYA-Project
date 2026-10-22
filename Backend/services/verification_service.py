"""
Verification Service Module

This module contains business logic for email and phone verification
in the Mentor AI EdTech Platform. It handles verification code generation,
storage, and validation for parent accounts.

Functions:
- send_email_verification: Send email verification code
- confirm_email_verification: Confirm email with verification code
- send_phone_otp: Send phone OTP
- confirm_phone_otp: Confirm phone with OTP
- Helper functions for code generation and validation

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any

from firebase_admin.auth import UserNotFoundError
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from utils.firebase_config import get_firestore_client, get_auth_client

# Configure logging
logger = logging.getLogger(__name__)

# Verification code expiry time (in minutes)
VERIFICATION_CODE_EXPIRY_MINUTES = 10


def generate_verification_code() -> str:
    """
    Generate a random 6-character alphanumeric verification code.
    
    Creates a verification code using uppercase letters and digits
    for email verification purposes.
    
    Returns:
        str: 6-character uppercase alphanumeric code
    
    Example:
        >>> code = generate_verification_code()
        >>> print(code)
        'A3B7C9'
    """
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(characters, k=6))
    logger.debug(f"Generated verification code: {code}")
    return code


def generate_otp() -> str:
    """
    Generate a random 6-digit numeric OTP.
    
    Creates a one-time password using numeric digits only
    for phone verification purposes.
    
    Returns:
        str: 6-digit numeric OTP
    
    Example:
        >>> otp = generate_otp()
        >>> print(otp)
        '123456'
    """
    otp = ''.join(random.choices(string.digits, k=6))
    logger.debug(f"Generated OTP: {otp}")
    return otp


def is_code_expired(created_at: datetime) -> bool:
    """
    Check if a verification code has expired.
    
    Verification codes are valid for 10 minutes from creation.
    
    Args:
        created_at: Timestamp when the code was created
    
    Returns:
        bool: True if code has expired, False otherwise
    
    Example:
        >>> created = datetime.utcnow() - timedelta(minutes=15)
        >>> is_code_expired(created)
        True
    """
    expiry_time = created_at + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)
    expired = datetime.utcnow() > expiry_time
    
    if expired:
        logger.debug(f"Code expired. Created: {created_at}, Expiry: {expiry_time}")
    
    return expired


def send_email_verification(email: str) -> Dict[str, Any]:
    """
    Send email verification code to parent.
    
    Generates a 6-character alphanumeric code and stores it in Firestore.
    In production, this would also send an actual email to the parent.
    
    Args:
        email: Parent's email address
    
    Returns:
        Dict containing message and code (code field for dev only)
    
    Raises:
        Exception: If code generation or storage fails
    
    Example:
        >>> result = send_email_verification("parent@example.com")
        >>> print(result['message'])
        'Verification email sent'
    """
    try:
        logger.info(f"Sending email verification code to: {email}")
        
        # Generate verification code
        code = generate_verification_code()
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Calculate expiry timestamp
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)
        
        # Store verification code in Firestore
        verification_data = {
            "email": email,
            "code": code,
            "created_at": SERVER_TIMESTAMP,
            "expires_at": expires_at,
            "used": False,
            "type": "email"
        }
        
        verification_ref = db.collection("verification_codes")
        doc_ref = verification_ref.add(verification_data)
        
        logger.info(f"Verification code stored successfully. Doc ID: {doc_ref[1].id}")
        logger.info(f"[DEV] Verification code for {email}: {code}")
        
        # In production, send actual email here
        # email_service.send_verification_email(email, code)
        
        return {
            "message": "Verification email sent",
            "code": code  # Remove this field in production
        }
    
    except Exception as e:
        logger.error(f"Error sending email verification: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to send verification email: {str(e)}")


def confirm_email_verification(email: str, code: str) -> Dict[str, Any]:
    """
    Confirm email verification with code.
    
    Validates the verification code and updates the parent's email
    verification status in both Firebase Auth and Firestore.
    
    Args:
        email: Parent's email address
        code: 6-character verification code
    
    Returns:
        Dict containing verification status and message
    
    Raises:
        ValueError: If code is invalid, expired, or already used
        Exception: If verification fails
    
    Example:
        >>> result = confirm_email_verification("parent@example.com", "ABC123")
        >>> print(result['verified'])
        True
    """
    try:
        logger.info(f"Confirming email verification for: {email}")
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Query verification codes
        verification_ref = db.collection("verification_codes")
        query = verification_ref.where("email", "==", email).where("code", "==", code).where("type", "==", "email").limit(1)
        docs = list(query.stream())
        
        if not docs:
            logger.warning(f"Invalid verification code for email: {email}")
            raise ValueError("Invalid verification code")
        
        # Get the verification document
        doc = docs[0]
        verification_data = doc.to_dict()
        
        # Check if code is already used
        if verification_data.get("used", False):
            logger.warning(f"Verification code already used for email: {email}")
            raise ValueError("Verification code has already been used")
        
        # Check if code is expired
        created_at = verification_data.get("created_at")
        if created_at and hasattr(created_at, 'timestamp'):
            created_datetime = datetime.fromtimestamp(created_at.timestamp())
            if is_code_expired(created_datetime):
                logger.warning(f"Verification code expired for email: {email}")
                raise ValueError("Verification code has expired. Please request a new one.")
        
        # Get Firebase Auth client
        auth_client = get_auth_client()
        
        # Get user by email
        try:
            user = auth_client.get_user_by_email(email)
            logger.info(f"User found with UID: {user.uid}")
        except UserNotFoundError:
            logger.error(f"User not found for email: {email}")
            raise ValueError(f"No user found with email: {email}")
        
        # Update Firebase Auth email verification status
        auth_client.update_user(
            user.uid,
            email_verified=True
        )
        logger.info(f"Firebase Auth updated: email_verified=True for UID: {user.uid}")
        
        # Update Firestore parents collection
        parents_ref = db.collection("parents")
        parent_doc_ref = parents_ref.document(user.uid)
        
        # Check if parent document exists
        parent_doc = parent_doc_ref.get()
        if not parent_doc.exists:
            logger.error(f"Parent document not found in Firestore for UID: {user.uid}")
            raise ValueError(f"Parent profile not found. Please complete registration first.")
        
        parent_doc_ref.update({
            "email_verified": True,
            "verified_at": SERVER_TIMESTAMP
        })
        logger.info(f"Firestore parents collection updated for UID: {user.uid}")
        
        # Mark verification code as used
        doc.reference.update({
            "used": True,
            "used_at": SERVER_TIMESTAMP
        })
        logger.info(f"Verification code marked as used")
        
        return {
            "verified": True,
            "message": "Email verified successfully"
        }
    
    except ValueError as e:
        logger.warning(f"Validation error during email verification: {e}")
        raise
    
    except UserNotFoundError as e:
        logger.error(f"User not found during email verification: {e}")
        raise ValueError(f"No user account found with email: {email}. Please register first.")
    
    except Exception as e:
        logger.error(f"Error confirming email verification: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to confirm email verification: {str(e)}")


def send_phone_otp(phone: str) -> Dict[str, Any]:
    """
    Send OTP to parent's phone number.
    
    Generates a 6-digit numeric OTP and stores it in Firestore.
    In production, this would also send an actual SMS to the phone.
    
    Args:
        phone: Parent's phone number in +91XXXXXXXXXX format
    
    Returns:
        Dict containing message and OTP (OTP field for dev only)
    
    Raises:
        Exception: If OTP generation or storage fails
    
    Example:
        >>> result = send_phone_otp("+919876543210")
        >>> print(result['message'])
        'OTP sent'
    """
    try:
        logger.info(f"Sending phone OTP to: {phone}")
        
        # Generate OTP
        otp = generate_otp()
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Calculate expiry timestamp
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)
        
        # Store OTP in Firestore
        otp_data = {
            "phone": phone,
            "otp": otp,
            "created_at": SERVER_TIMESTAMP,
            "expires_at": expires_at,
            "used": False,
            "type": "phone"
        }
        
        verification_ref = db.collection("verification_codes")
        doc_ref = verification_ref.add(otp_data)
        
        logger.info(f"OTP stored successfully. Doc ID: {doc_ref[1].id}")
        logger.info(f"[DEV] OTP for {phone}: {otp}")
        
        # In production, send actual SMS here
        # sms_service.send_otp_sms(phone, otp)
        
        return {
            "message": "OTP sent",
            "otp": otp  # Remove this field in production
        }
    
    except Exception as e:
        logger.error(f"Error sending phone OTP: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to send OTP: {str(e)}")


def confirm_phone_otp(phone: str, otp: str) -> Dict[str, Any]:
    """
    Confirm phone verification with OTP.
    
    Validates the OTP and updates the parent's phone verification
    status in the Firestore parents collection.
    
    Args:
        phone: Parent's phone number
        otp: 6-digit OTP
    
    Returns:
        Dict containing verification status and message
    
    Raises:
        ValueError: If OTP is invalid, expired, or already used
        Exception: If verification fails
    
    Example:
        >>> result = confirm_phone_otp("+919876543210", "123456")
        >>> print(result['verified'])
        True
    """
    try:
        logger.info(f"Confirming phone OTP for: {phone}")
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Query verification codes
        verification_ref = db.collection("verification_codes")
        query = verification_ref.where("phone", "==", phone).where("otp", "==", otp).where("type", "==", "phone").limit(1)
        docs = list(query.stream())
        
        if not docs:
            logger.warning(f"Invalid OTP for phone: {phone}")
            raise ValueError("Invalid OTP")
        
        # Get the verification document
        doc = docs[0]
        otp_data = doc.to_dict()
        
        # Check if OTP is already used
        if otp_data.get("used", False):
            logger.warning(f"OTP already used for phone: {phone}")
            raise ValueError("OTP has already been used")
        
        # Check if OTP is expired
        created_at = otp_data.get("created_at")
        if created_at and hasattr(created_at, 'timestamp'):
            created_datetime = datetime.fromtimestamp(created_at.timestamp())
            if is_code_expired(created_datetime):
                logger.warning(f"OTP expired for phone: {phone}")
                raise ValueError("OTP has expired. Please request a new one.")
        
        # Get Firebase Auth client
        auth_client = get_auth_client()
        
        # Get user by phone
        try:
            user = auth_client.get_user_by_phone_number(phone)
            logger.info(f"User found with UID: {user.uid}")
        except UserNotFoundError:
            logger.error(f"User not found for phone: {phone}")
            raise ValueError(f"No user account found with phone: {phone}. Please register first.")
        
        # Update Firestore parents collection
        parents_ref = db.collection("parents")
        parent_doc_ref = parents_ref.document(user.uid)
        
        # Check if parent document exists
        parent_doc = parent_doc_ref.get()
        if not parent_doc.exists:
            logger.error(f"Parent document not found in Firestore for UID: {user.uid}")
            raise ValueError(f"Parent profile not found. Please complete registration first.")
        
        parent_doc_ref.update({
            "phone_verified": True,
            "verified_at": SERVER_TIMESTAMP
        })
        logger.info(f"Firestore parents collection updated for UID: {user.uid}")
        
        # Mark OTP as used
        doc.reference.update({
            "used": True,
            "used_at": SERVER_TIMESTAMP
        })
        logger.info(f"OTP marked as used")
        
        return {
            "verified": True,
            "message": "Phone verified successfully"
        }
    
    except ValueError as e:
        logger.warning(f"Validation error during phone verification: {e}")
        raise
    
    except UserNotFoundError as e:
        logger.error(f"User not found during phone verification: {e}")
        raise ValueError(f"No user account found with phone: {phone}. Please register first.")
    
    except Exception as e:
        logger.error(f"Error confirming phone OTP: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Failed to confirm phone verification: {str(e)}")
