"""
Firebase Configuration and Initialization Module

This module handles the initialization and configuration of Firebase Admin SDK
for the Mentor AI EdTech Platform. It provides singleton access to Firebase
services including Authentication and Firestore.

Features:
- Singleton pattern for Firebase app initialization
- Firestore database client access
- Firebase Authentication client access
- Environment-based configuration
- Comprehensive error handling and logging

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, auth, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Global flag to track Firebase initialization status
_firebase_initialized: bool = False


def initialize_firebase() -> None:
    """
    Initialize Firebase Admin SDK with service account credentials.
    
    This function implements a singleton pattern to ensure Firebase is
    initialized only once. It loads credentials from the path specified
    in the FIREBASE_SERVICE_ACCOUNT_PATH environment variable.
    
    Raises:
        ValueError: If FIREBASE_SERVICE_ACCOUNT_PATH is not set
        FileNotFoundError: If service account file is not found
        Exception: If Firebase initialization fails
    
    Environment Variables:
        FIREBASE_SERVICE_ACCOUNT_PATH: Path to Firebase service account JSON file
    
    Example:
        >>> initialize_firebase()
        # Firebase initialized successfully with service account
    """
    global _firebase_initialized
    
    # Check if Firebase is already initialized
    if _firebase_initialized:
        logger.info("Firebase Admin SDK is already initialized")
        return
    
    try:
        # Get service account path from environment variable
        service_account_path = os.getenv("FIREBASE_CREDENTIALS_PATH") or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if not service_account_path:
            error_msg = (
                "FIREBASE_SERVICE_ACCOUNT_PATH environment variable is not set. "
                "Please set it to the path of your Firebase service account JSON file."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check if service account file exists
        if not os.path.exists(service_account_path):
            error_msg = (
                f"Firebase service account file not found at: {service_account_path}. "
                "Please ensure the file exists and the path is correct."
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Initialize Firebase credentials
        logger.info(f"Loading Firebase credentials from: {service_account_path}")
        cred = credentials.Certificate(service_account_path)
        
        # Initialize Firebase app
        firebase_admin.initialize_app(cred)
        
        _firebase_initialized = True
        logger.info("=" * 80)
        logger.info("Firebase Admin SDK initialized successfully")
        logger.info(f"Service Account: {service_account_path}")
        logger.info("Available Services: Authentication, Firestore")
        logger.info("=" * 80)
        
    except ValueError as ve:
        logger.error(f"Configuration error during Firebase initialization: {ve}")
        raise
    
    except FileNotFoundError as fnf:
        logger.error(f"File not found error during Firebase initialization: {fnf}")
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error during Firebase initialization: {e}")
        logger.exception("Full traceback:")
        raise


def get_firestore_client() -> firestore.firestore.Client:
    """
    Get Firestore database client instance.
    
    This function returns a Firestore client that can be used to interact
    with the Firebase Firestore database. It ensures Firebase is initialized
    before returning the client.
    
    Returns:
        firestore.firestore.Client: Firestore database client instance
    
    Raises:
        Exception: If Firebase initialization fails
    
    Example:
        >>> db = get_firestore_client()
        >>> users_ref = db.collection('users')
        >>> docs = users_ref.stream()
    """
    # Ensure Firebase is initialized
    if not _firebase_initialized:
        logger.warning("Firebase not initialized, initializing now...")
        initialize_firebase()
    
    # Return Firestore client
    client = firestore.client()
    logger.debug("Firestore client instance retrieved")
    return client


def get_auth_client() -> auth:
    """
    Get Firebase Authentication client instance.
    
    This function returns the Firebase Auth module that can be used for
    authentication operations such as verifying ID tokens, creating users,
    and managing user accounts.
    
    Returns:
        auth: Firebase Authentication module instance
    
    Raises:
        Exception: If Firebase initialization fails
    
    Example:
        >>> auth_client = get_auth_client()
        >>> decoded_token = auth_client.verify_id_token(id_token)
        >>> user = auth_client.get_user(uid)
    """
    # Ensure Firebase is initialized
    if not _firebase_initialized:
        logger.warning("Firebase not initialized, initializing now...")
        initialize_firebase()
    
    logger.debug("Firebase Auth client instance retrieved")
    return auth


def is_firebase_initialized() -> bool:
    """
    Check if Firebase Admin SDK has been initialized.
    
    Returns:
        bool: True if Firebase is initialized, False otherwise
    """
    return _firebase_initialized


# Module-level initialization
# This ensures Firebase is initialized when the module is imported
try:
    logger.info("Attempting to initialize Firebase Admin SDK on module import...")
    initialize_firebase()
except ValueError as e:
    # Environment variable not set - this is expected in some cases
    logger.warning(f"Firebase initialization skipped: {e}")
    logger.warning("Firebase will be initialized on first use")
except FileNotFoundError as e:
    # Service account file not found - this is expected in some cases
    logger.warning(f"Firebase initialization skipped: {e}")
    logger.warning("Firebase will be initialized on first use")
except Exception as e:
    # Unexpected error - log it but don't crash the application
    logger.error(f"Failed to initialize Firebase on module import: {e}")
    logger.warning("Firebase will attempt to initialize on first use")
