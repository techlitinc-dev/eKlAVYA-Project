"""
Authentication Service Module

This module contains business logic for parent authentication and registration
in the Mentor AI EdTech Platform. It handles three registration methods:
email/password, phone number, and Google OAuth.

Functions:
- register_parent_with_email: Email-based registration
- register_parent_with_phone: Phone-based registration
- register_parent_with_google: Google OAuth registration

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

import firebase_admin
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError, EmailAlreadyExistsError
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from utils.firebase_config import get_firestore_client, get_auth_client

# Configure logging
logger = logging.getLogger(__name__)


def register_parent_with_email(
    email: str,
    password: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Register a new parent using email and password.
    
    This function creates a new Firebase user with email/password credentials
    and stores the parent's information in Firestore. The parent will need to
    verify their email address before accessing certain features.
    
    Args:
        email: Parent's email address
        password: Account password (must meet Firebase requirements)
        language: Preferred language (en/hi/mr), defaults to 'en'
    
    Returns:
        Dict containing:
            - parent_id: Unique identifier for the parent
            - email: Parent's email address
            - verification_required: Always True for email registration
            - message: Success message
    
    Raises:
        EmailAlreadyExistsError: If email is already registered
        ValueError: If email or password is invalid
        Exception: If Firebase operation fails
    
    Example:
        >>> result = register_parent_with_email(
        ...     email="parent@example.com",
        ...     password="SecurePass123",
        ...     language="en"
        ... )
        >>> print(result['parent_id'])
        'parent_abc123xyz'
    """
    try:
        logger.info(f"Attempting to register parent with email: {email}")
        
        # Get Firebase Auth client
        auth_client = get_auth_client()
        
        # Create Firebase user with email and password
        user = auth_client.create_user(
            email=email,
            password=password,
            email_verified=False,  # Email verification required
            disabled=False
        )
        
        logger.info(f"Firebase user created successfully. UID: {user.uid}")
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Prepare parent document data
        parent_data = {
            "parent_id": user.uid,
            "email": email,
            "language": language,
            "role": "parent",
            "created_at": SERVER_TIMESTAMP,
            "email_verified": False,
            "registration_method": "email"
        }
        
        # Store parent information in Firestore
        parents_ref = db.collection("parents")
        parents_ref.document(user.uid).set(parent_data)
        
        logger.info(f"Parent document created in Firestore for UID: {user.uid}")
        
        # Send email verification link (optional, Firebase handles this)
        try:
            verification_link = auth_client.generate_email_verification_link(email)
            logger.info(f"Email verification link generated for: {email}")
        except Exception as e:
            logger.warning(f"Failed to generate verification link: {e}")
        
        # Return success response
        return {
            "parent_id": user.uid,
            "email": email,
            "phone": None,
            "verification_required": True,
            "message": "Registration successful. Please verify your email to continue."
        }
    
    except EmailAlreadyExistsError as e:
        logger.warning(f"Email already exists: {email}")
        raise ValueError(f"An account with email {email} already exists. Please login instead.")
    
    except ValueError as e:
        logger.error(f"Invalid input for email registration: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error during email registration: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Registration failed: {str(e)}")


def register_parent_with_phone(
    phone: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Register a new parent using phone number.
    
    This function creates a new Firebase user with a phone number and stores
    the parent's information in Firestore. The parent will receive an OTP
    for verification during the login process.
    
    Args:
        phone: Parent's phone number in format +91XXXXXXXXXX
        language: Preferred language (en/hi/mr), defaults to 'en'
    
    Returns:
        Dict containing:
            - parent_id: Unique identifier for the parent
            - phone: Parent's phone number
            - verification_required: Always True for phone registration
            - message: Success message
    
    Raises:
        ValueError: If phone number is already registered or invalid
        Exception: If Firebase operation fails
    
    Example:
        >>> result = register_parent_with_phone(
        ...     phone="+919876543210",
        ...     language="hi"
        ... )
        >>> print(result['parent_id'])
        'parent_def456uvw'
    """
    try:
        logger.info(f"Attempting to register parent with phone: {phone}")
        
        # Get Firebase Auth client
        auth_client = get_auth_client()
        
        # Check if phone number already exists
        try:
            existing_user = auth_client.get_user_by_phone_number(phone)
            if existing_user:
                logger.warning(f"Phone number already exists: {phone}")
                raise ValueError(
                    f"An account with phone number {phone} already exists. Please login instead."
                )
        except UserNotFoundError:
            # Phone number doesn't exist, proceed with registration
            pass
        
        # Create Firebase user with phone number
        user = auth_client.create_user(
            phone_number=phone,
            disabled=False
        )
        
        logger.info(f"Firebase user created successfully with phone. UID: {user.uid}")
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Prepare parent document data
        parent_data = {
            "parent_id": user.uid,
            "phone": phone,
            "language": language,
            "role": "parent",
            "created_at": SERVER_TIMESTAMP,
            "phone_verified": False,
            "registration_method": "phone"
        }
        
        # Store parent information in Firestore
        parents_ref = db.collection("parents")
        parents_ref.document(user.uid).set(parent_data)
        
        logger.info(f"Parent document created in Firestore for UID: {user.uid}")
        
        # Return success response
        return {
            "parent_id": user.uid,
            "email": None,
            "phone": phone,
            "verification_required": True,
            "message": "Registration successful. You will receive an OTP for verification during login."
        }
    
    except ValueError as e:
        logger.error(f"Invalid input for phone registration: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error during phone registration: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Registration failed: {str(e)}")


def register_parent_with_google(
    id_token: str,
    language: str = "en"
) -> Dict[str, Any]:
    """
    Register or login a parent using Google OAuth.
    
    This function verifies the Google ID token, extracts user information,
    and creates or updates the parent's record in Firestore. Google OAuth
    users are pre-verified and don't need additional email verification.
    
    Args:
        id_token: Google OAuth ID token from Google Sign-In
        language: Preferred language (en/hi/mr), defaults to 'en'
    
    Returns:
        Dict containing:
            - parent_id: Unique identifier for the parent
            - email: Parent's email address from Google
            - verification_required: Always False for Google OAuth
            - message: Success message
    
    Raises:
        ValueError: If ID token is invalid or verification fails
        Exception: If Firebase operation fails
    
    Example:
        >>> result = register_parent_with_google(
        ...     id_token="eyJhbGciOiJSUzI1NiIs...",
        ...     language="en"
        ... )
        >>> print(result['parent_id'])
        'google_user_ghi789rst'
    """
    try:
        logger.info("Attempting to register/login parent with Google OAuth")
        
        # Get Firebase Auth client
        auth_client = get_auth_client()
        
        # Verify the Google ID token
        try:
            decoded_token = auth_client.verify_id_token(id_token)
            logger.info("Google ID token verified successfully")
        except Exception as e:
            logger.error(f"Invalid Google ID token: {e}")
            raise ValueError("Invalid Google ID token. Please try signing in again.")
        
        # Extract user information from decoded token
        uid = decoded_token.get("uid")
        email = decoded_token.get("email")
        email_verified = decoded_token.get("email_verified", False)
        
        if not uid or not email:
            logger.error("Missing uid or email in decoded token")
            raise ValueError("Invalid token: missing user information")
        
        logger.info(f"Google user authenticated - UID: {uid}, Email: {email}")
        
        # Get Firestore client
        db = get_firestore_client()
        parents_ref = db.collection("parents")
        parent_doc_ref = parents_ref.document(uid)
        
        # Check if parent already exists
        parent_doc = parent_doc_ref.get()
        
        if parent_doc.exists:
            # Existing user - update last login and language preference
            logger.info(f"Existing parent found. Updating record for UID: {uid}")
            
            parent_doc_ref.update({
                "language": language,
                "last_login": SERVER_TIMESTAMP,
                "email_verified": email_verified
            })
            
            message = "Login successful. Welcome back!"
        
        else:
            # New user - create parent document
            logger.info(f"New parent. Creating record for UID: {uid}")
            
            parent_data = {
                "parent_id": uid,
                "email": email,
                "language": language,
                "role": "parent",
                "created_at": SERVER_TIMESTAMP,
                "last_login": SERVER_TIMESTAMP,
                "email_verified": email_verified,
                "registration_method": "google"
            }
            
            parent_doc_ref.set(parent_data)
            
            message = "Registration successful. Welcome to Mentor AI!"
        
        logger.info(f"Parent document processed successfully for UID: {uid}")
        
        # Return success response
        return {
            "parent_id": uid,
            "email": email,
            "phone": None,
            "verification_required": False,  # Google users are pre-verified
            "message": message
        }
    
    except ValueError as e:
        logger.error(f"Invalid input for Google registration: {e}")
        raise
    
    except Exception as e:
        logger.error(f"Error during Google registration: {e}")
        logger.exception("Full traceback:")
        raise Exception(f"Registration failed: {str(e)}")
