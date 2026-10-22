"""
Simple Test for Study Center API

This script tests basic functionality without AI generation
to avoid API version issues.
"""

import logging
from datetime import datetime
from services.study_center_service import get_study_center_service
from services.progress_tracker_service import get_progress_tracker_service
from utils.firebase_config import get_firestore_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic functionality without AI generation"""
    logger.info("Testing basic Study Center functionality...")
    
    try:
        # Initialize services
        study_service = get_study_center_service()
        progress_service = get_progress_tracker_service()
        db = get_firestore_client()
        
        logger.info("✓ Services initialized successfully")
        
        # Test topic loading
        topics = study_service.get_topics_for_student("test_student")
        logger.info(f"✓ Loaded {len(topics)} topics from syllabus")
        
        if topics:
            first_topic = topics[0]
            logger.info(f"✓ First topic: {first_topic.topic_id} - {first_topic.topic_name}")
            
            # Test progress tracking
            progress = progress_service.get_all_progress("test_student")
            logger.info(f"✓ Progress summary created with {progress.total_topics} total topics")
            
            # Test session management
            session_id = progress_service.start_learning_session(
                "test_student", 
                first_topic.topic_id
            )
            logger.info(f"✓ Started session: {session_id}")
            
            # Test session end
            import time
            time.sleep(1)  # Simulate study time
            
            ended_session = progress_service.end_learning_session(session_id)
            logger.info(f"✓ Ended session: {ended_session.get('duration_minutes')} minutes")
            
            logger.info("✓ All basic functionality tests passed!")
            return True
            
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    if success:
        logger.info("🎉 Study Center basic functionality is working!")
    else:
        logger.info("❌ Study Center functionality needs fixes!")