#!/usr/bin/env python3
"""
Firestore Database Initialization Script

This script initializes all required Firestore collections and indexes
for the Mentor AI backend.

Collections Created:
- parents: Parent user profiles
- students: Student/child profiles
- sessions: User sessions and tokens
- verification_codes: Email/phone verification codes
- exam_selections: Student exam selections
- diagnostic_tests: Generated diagnostic tests
- test_submissions: Student test submissions
- analytics: Test analytics and performance data
- schedules: Study schedules
- schedules/{id}/progress: Daily progress tracking (subcollection)
- subscriptions: Active subscriptions
- subscriptions/{id}/history: Subscription history (subcollection)
- transactions: Payment transactions
- rag_cache: RAG question generation cache
- search_cache: Vector search cache

Usage:
    python3 init_firestore.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.firebase_config import get_firestore_client
from google.cloud import firestore

# Collection names
COLLECTIONS = {
    "parents": "Parent user profiles",
    "students": "Student/child profiles",
    "sessions": "User sessions and authentication tokens",
    "verification_codes": "Email and phone verification codes",
    "exam_selections": "Student exam type selections (JEE/NEET)",
    "diagnostic_tests": "Generated diagnostic tests",
    "test_submissions": "Student test submissions and answers",
    "analytics": "Test analytics and performance data",
    "schedules": "AI-generated study schedules",
    "subscriptions": "Active subscription plans",
    "transactions": "Payment transactions and history",
    "rag_cache": "RAG question generation cache",
    "search_cache": "Vector search results cache",
    "preferences": "Parent preferences and settings",
    "query_cache": "Persistent user query cache (reduces API costs)",
    "rate_limits": "Rate limit tracking and violations",
}

# Sample data for each collection
SAMPLE_DATA = {
    "parents": {
        "_sample": {
            "uid": "sample_parent_id",
            "email": "parent@example.com",
            "phone": "+1234567890",
            "name": "Sample Parent",
            "email_verified": True,
            "phone_verified": True,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
            "is_sample": True,
        }
    },
    "students": {
        "_sample": {
            "student_id": "sample_student_id",
            "parent_id": "sample_parent_id",
            "name": "Sample Student",
            "age": 17,
            "grade": 12,
            "target_exam": "JEE_MAIN",
            "exam_date": "2025-04-15",
            "created_at": firestore.SERVER_TIMESTAMP,
            "is_sample": True,
        }
    },
    "schedules": {
        "_sample": {
            "schedule_id": "sample_schedule_id",
            "student_id": "sample_student_id",
            "parent_id": "sample_parent_id",
            "exam_type": "JEE_MAIN",
            "start_date": "2024-12-01",
            "exam_date": "2025-04-15",
            "total_days": 135,
            "daily_hours": 6,
            "status": "active",
            "created_at": firestore.SERVER_TIMESTAMP,
            "is_sample": True,
        }
    },
    "subscriptions": {
        "_sample": {
            "subscription_id": "sample_subscription_id",
            "parent_id": "sample_parent_id",
            "plan_id": "premium_monthly",
            "status": "active",
            "start_date": firestore.SERVER_TIMESTAMP,
            "end_date": None,
            "auto_renew": True,
            "is_sample": True,
        }
    },
}


def init_firestore():
    """Initialize Firestore collections and indexes."""
    print("=" * 80)
    print("Firestore Database Initialization")
    print("=" * 80)
    print()
    
    try:
        # Get Firestore client
        print("Connecting to Firestore...")
        db = get_firestore_client()
        print("✓ Connected to Firestore")
        print()
        
        # Create collections with sample documents
        print("Creating collections...")
        print("-" * 80)
        
        for collection_name, description in COLLECTIONS.items():
            try:
                # Check if collection exists by trying to get a document
                collection_ref = db.collection(collection_name)
                
                # Create sample document if we have sample data
                if collection_name in SAMPLE_DATA:
                    sample_doc = SAMPLE_DATA[collection_name]["_sample"]
                    doc_ref = collection_ref.document("_sample")
                    
                    # Check if sample already exists
                    if not doc_ref.get().exists:
                        doc_ref.set(sample_doc)
                        print(f"✓ {collection_name:25} - Created with sample data")
                    else:
                        print(f"✓ {collection_name:25} - Already exists")
                else:
                    # Just create a temporary document to initialize collection
                    temp_doc = collection_ref.document("_init")
                    if not temp_doc.get().exists:
                        temp_doc.set({
                            "initialized": True,
                            "created_at": firestore.SERVER_TIMESTAMP,
                            "description": description
                        })
                        print(f"✓ {collection_name:25} - Initialized")
                    else:
                        print(f"✓ {collection_name:25} - Already exists")
                
            except Exception as e:
                print(f"✗ {collection_name:25} - Error: {e}")
        
        print("-" * 80)
        print()
        
        # Create subcollections
        print("Creating subcollections...")
        print("-" * 80)
        
        # Progress subcollection under schedules
        try:
            if "_sample" in SAMPLE_DATA.get("schedules", {}):
                schedule_id = "sample_schedule_id"
                progress_ref = (
                    db.collection("schedules")
                    .document(schedule_id)
                    .collection("progress")
                    .document("day_1")
                )
                
                if not progress_ref.get().exists:
                    progress_ref.set({
                        "day_number": 1,
                        "date": "2024-12-01",
                        "status": "pending",
                        "topics_completed": [],
                        "hours_studied": 0,
                        "is_sample": True,
                    })
                    print(f"✓ schedules/progress        - Created sample progress")
                else:
                    print(f"✓ schedules/progress        - Already exists")
        except Exception as e:
            print(f"✗ schedules/progress        - Error: {e}")
        
        # Subscription history subcollection
        try:
            if "_sample" in SAMPLE_DATA.get("subscriptions", {}):
                parent_id = "sample_parent_id"
                history_ref = (
                    db.collection("subscriptions")
                    .document(parent_id)
                    .collection("history")
                    .document("sample_history_id")
                )
                
                if not history_ref.get().exists:
                    history_ref.set({
                        "subscription_id": "sample_subscription_id",
                        "action": "created",
                        "timestamp": firestore.SERVER_TIMESTAMP,
                        "is_sample": True,
                    })
                    print(f"✓ subscriptions/history     - Created sample history")
                else:
                    print(f"✓ subscriptions/history     - Already exists")
        except Exception as e:
            print(f"✗ subscriptions/history     - Error: {e}")
        
        print("-" * 80)
        print()
        
        # Create indexes (note: these need to be created in Firebase Console)
        print("Required Indexes (create in Firebase Console):")
        print("-" * 80)
        print("1. sessions:")
        print("   - token_hash (Ascending)")
        print("   - refresh_token_hash (Ascending)")
        print()
        print("2. verification_codes:")
        print("   - email (Ascending) + code (Ascending) + type (Ascending)")
        print("   - phone (Ascending) + otp (Ascending) + type (Ascending)")
        print()
        print("3. analytics:")
        print("   - overview.student_id (Ascending) + created_at (Descending)")
        print()
        print("4. schedules:")
        print("   - student_id (Ascending) + created_at (Descending)")
        print()
        print("5. transactions:")
        print("   - parent_id (Ascending) + created_at (Descending)")
        print("   - order_id (Ascending)")
        print()
        print("6. schedules/{scheduleId}/progress:")
        print("   - update_date (Descending)")
        print("-" * 80)
        print()
        
        # Summary
        print("=" * 80)
        print("Initialization Complete!")
        print("=" * 80)
        print()
        print("Collections created:")
        for collection_name in COLLECTIONS.keys():
            print(f"  ✓ {collection_name}")
        print()
        print("Next steps:")
        print("1. Go to Firebase Console: https://console.firebase.google.com/")
        print("2. Select your project")
        print("3. Go to Firestore Database")
        print("4. Verify collections are created")
        print("5. Create required indexes (see list above)")
        print()
        print("Note: Sample documents are marked with 'is_sample: true'")
        print("      You can delete them after testing")
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("Initialization Failed!")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check FIREBASE_CREDENTIALS_PATH in .env")
        print("2. Verify Firebase credentials file exists")
        print("3. Ensure Firebase project is set up correctly")
        print("4. Check internet connection")
        print()
        return False


def cleanup_sample_data():
    """Remove sample data from collections."""
    print("=" * 80)
    print("Cleaning Up Sample Data")
    print("=" * 80)
    print()
    
    try:
        db = get_firestore_client()
        
        # Delete sample documents
        collections_to_clean = ["parents", "students", "schedules", "subscriptions"]
        
        for collection_name in collections_to_clean:
            try:
                doc_ref = db.collection(collection_name).document("_sample")
                if doc_ref.get().exists:
                    doc_ref.delete()
                    print(f"✓ Deleted sample from {collection_name}")
            except Exception as e:
                print(f"✗ Error cleaning {collection_name}: {e}")
        
        # Delete init documents
        for collection_name in COLLECTIONS.keys():
            try:
                doc_ref = db.collection(collection_name).document("_init")
                if doc_ref.get().exists:
                    doc_ref.delete()
                    print(f"✓ Deleted init doc from {collection_name}")
            except Exception as e:
                pass  # Ignore if doesn't exist
        
        print()
        print("✓ Sample data cleanup complete")
        print()
        
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Firestore database")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove sample data instead of initializing"
    )
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_sample_data()
    else:
        success = init_firestore()
        sys.exit(0 if success else 1)
