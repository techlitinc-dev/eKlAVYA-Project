"""
Simple User Registration Service
"""

import logging
from typing import Dict, Any

from firebase_admin import auth
from firebase_admin.auth import EmailAlreadyExistsError
from google.cloud.firestore_v1 import SERVER_TIMESTAMP

from utils.firebase_config import get_firestore_client, get_auth_client

# Configure logging
logger = logging.getLogger(__name__)


def register_user_simple(
    name: str,
    email_address: str,
    password: str,
    repeat_password: str,
    mobile_number: str = "+91XXXXXXXXXX"  # Default value since it's not required in frontend
) -> Dict[str, Any]:
    """
    Register a new user without email verification.
    
    Args:
        name: User's full name
        mobile_number: User's mobile number
        email_address: User's email address
        password: Account password
        repeat_password: Password confirmation
    
    Returns:
        Dict containing registration status and user info
    
    Raises:
        ValueError: If registration fails
        Exception: If Firebase operation fails
    """
    try:
        logger.info(f"Registering new user: {email_address}")
        
        # Get Firebase Auth client
        auth_client = get_auth_client()
        
        # Create user in Firebase Auth
        user = auth_client.create_user(
            email=email_address,
            password=password,
            email_verified=False,  # Skip email verification as requested
            disabled=False
        )
        
        logger.info(f"User created successfully with UID: {user.uid}")
        
        # Get Firestore client
        db = get_firestore_client()
        
        # Create user document in Firestore
        user_data = {
            "parent_id": user.uid,
            "name": name,
            "mobile_number": mobile_number,
            "email_address": email_address,
            "language": "en",  # Default language
            "role": "parent",
            "created_at": SERVER_TIMESTAMP,
            "email_verified": False,
            "registration_method": "simple"
        }
        
        parents_ref = db.collection("parents")
        parents_ref.document(user.uid).set(user_data)
        
        logger.info(f"User document created in Firestore for UID: {user.uid}")
        
        return {
            "parent_id": user.uid,
            "email": email_address,
            "phone": mobile_number,
            "verification_required": False,
            "message": "Registration successful"
        }
    
    except EmailAlreadyExistsError as e:
        logger.warning(f"Email already exists: {email_address}")
        raise ValueError(f"An account with email {email_address} already exists. Please login instead.")
    
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        raise Exception(f"Registration failed: {str(e)}")