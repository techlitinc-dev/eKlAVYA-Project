"""
Setup Study Center Database Indexes

This script creates the necessary Firestore indexes for
optimal performance of the Study Center Learning Journey feature.

Required Indexes:
1. learning_materials: topic_id + exam_type + material_type
2. mind_maps: topic_id + exam_type
3. learning_progress: student_id
4. learning_sessions: student_id + session_date

Author: Mentor AI Team
Version: 1.0.0
"""

import logging
from firebase_admin import firestore
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import from utils
from utils.firebase_config import get_firestore_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_index_definitions():
    """
    Generate index definitions for Study Center feature.
    
    Returns index definitions that can be used to create indexes
    through Firebase Console or gcloud CLI.
    """
    logger.info("Generating Study Center database index definitions...")
    
    # Index definitions for Firebase Console
    index_definitions = {
        "learning_materials": {
            "collection": "learning_materials",
            "fields": [
                {"field": "topic_id", "order": "ASCENDING"},
                {"field": "exam_type", "order": "ASCENDING"},
                {"field": "material_type", "order": "ASCENDING"}
            ],
            "description": "Composite index for querying learning materials by topic, exam type, and material type"
        },
        "mind_maps": {
            "collection": "mind_maps",
            "fields": [
                {"field": "topic_id", "order": "ASCENDING"},
                {"field": "exam_type", "order": "ASCENDING"}
            ],
            "description": "Composite index for querying mind maps by topic and exam type"
        },
        "learning_progress": {
            "collection": "learning_progress",
            "fields": [
                {"field": "student_id", "order": "ASCENDING"}
            ],
            "description": "Single field index for querying student progress"
        },
        "learning_sessions": {
            "collection": "learning_sessions",
            "fields": [
                {"field": "student_id", "order": "ASCENDING"},
                {"field": "session_date", "order": "DESCENDING"}
            ],
            "description": "Composite index for querying sessions by student and date"
        }
    }
    
    return index_definitions


def print_firestore_index_instructions():
    """
    Print instructions for creating Firestore indexes manually.
    """
    logger.info("=" * 60)
    logger.info("FIRESTORE INDEX CREATION INSTRUCTIONS")
    logger.info("=" * 60)
    
    index_definitions = generate_index_definitions()
    
    logger.info("\nTo create the required indexes for Study Center feature:")
    logger.info("\n1. Go to Firebase Console: https://console.firebase.google.com")
    logger.info("2. Select your project")
    logger.info("3. Navigate to Firestore Database")
    logger.info("4. Click on 'Indexes' tab")
    logger.info("5. Click 'Create Index' for each of the following:")
    
    for collection_name, index_def in index_definitions.items():
        logger.info(f"\n📋 Index for collection: {collection_name}")
        logger.info(f"   Description: {index_def['description']}")
        logger.info("   Fields:")
        for field in index_def["fields"]:
            logger.info(f"   - {field['field']} ({field['order']})")
    
    logger.info("\n" + "=" * 60)
    logger.info("ALTERNATIVE: Using gcloud CLI")
    logger.info("=" * 60)
    
    logger.info("\nYou can also create indexes using gcloud CLI:")
    logger.info("1. Install gcloud CLI and Firebase Tools")
    logger.info("2. Run: firebase login")
    logger.info("3. Create a firestore.indexes.json file with the following content:")
    
    # Generate JSON content
    indexes_json = {
        "indexes": [
            {
                "collectionGroup": collection,
                "queryScope": "COLLECTION",
                "fields": index_def["fields"]
            }
            for collection, index_def in index_definitions.items()
        ]
    }
    
    import json
    logger.info("\n" + json.dumps(indexes_json, indent=2))
    logger.info("\n4. Run: firebase deploy --only firestore:indexes")
    
    logger.info("\n" + "=" * 60)
    logger.info("NOTE: Index creation may take several minutes to complete.")
    logger.info("=" * 60)


def create_indexes():
    """
    Print index creation instructions since Firestore indexes
    cannot be created programmatically through the Admin SDK.
    """
    logger.info("Study Center database indexes cannot be created programmatically.")
    logger.info("Please follow the manual instructions below.")
    
    print_firestore_index_instructions()


def check_indexes():
    """
    Check if required indexes exist for Study Center.
    
    Note: Firestore indexes cannot be checked programmatically through Admin SDK.
    This function provides guidance on manual verification.
    
    Returns:
        Dict with index status information
    """
    logger.info("Checking Study Center database indexes...")
    logger.info("Note: Index verification must be done manually through Firebase Console.")
    
    # List of required indexes
    required_indexes = {
        "learning_materials": [
            {"name": "topic_exam_material_type", "fields": ["topic_id", "exam_type", "material_type"]}
        ],
        "mind_maps": [
            {"name": "topic_exam_type", "fields": ["topic_id", "exam_type"]}
        ],
        "learning_progress": [
            {"name": "student_id_index", "fields": ["student_id"]}
        ],
        "learning_sessions": [
            {"name": "student_session_date", "fields": ["student_id", "session_date"]}
        ]
    }
    
    # Check each collection
    index_status = {}
    
    for collection_name, indexes in required_indexes.items():
        # Since we can't check programmatically, we'll mark as needs verification
        collection_status = {
            "collection": collection_name,
            "exists": "needs_verification",
            "indexes": "check_manually",
            "required": [req["name"] for req in indexes],
            "missing": "check_manually",
            "status": "needs_manual_verification"
        }
        
        index_status[collection_name] = collection_status
        logger.info(f"Collection '{collection_name}': Requires manual verification")
    
    return index_status


if __name__ == "__main__":
    """
    Main execution function.
    
    Usage:
        python scripts/setup_study_center_indexes.py
    """
    logger.info("Setting up Study Center database indexes...")
    
    try:
        # Print index creation instructions
        create_indexes()
        
        # Check index status
        status = check_indexes()
        
        # Print summary
        logger.info("=" * 50)
        logger.info("INDEX CREATION SUMMARY")
        logger.info("=" * 50)
        
        logger.info("✓ Index creation instructions provided above")
        logger.info("✓ Please create indexes manually through Firebase Console")
        logger.info("✓ Use the provided JSON configuration for gcloud CLI")
        
        logger.info("=" * 50)
        logger.info("NEXT STEPS:")
        logger.info("1. Create indexes using Firebase Console or gcloud CLI")
        logger.info("2. Wait for indexes to be created (may take several minutes)")
        logger.info("3. Test the Study Center API endpoints")
        logger.info("4. Monitor performance with the new indexes")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Failed to generate index instructions: {e}")
        logger.exception("Full traceback:")