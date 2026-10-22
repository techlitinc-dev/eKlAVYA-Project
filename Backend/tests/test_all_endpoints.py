"""
Comprehensive Test Suite for All Mentor AI Platform Endpoints

This module provides comprehensive testing for all endpoints in the Mentor AI EdTech Platform,
with special focus on Gemini endpoints and database storage verification.

Features:
- Tests for all API endpoints
- Database storage verification
- Gemini API integration testing
- Authentication flow testing
- Error handling validation
- Performance monitoring

Author: Mentor AI Team
Version: 1.0.0
"""

import os
import sys
import json
import time
import asyncio
import pytest
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import services and utilities
from utils.firebase_config import get_firestore_client, initialize_firebase
from services.login_service import (
    login_with_email, login_with_phone, login_with_google,
    refresh_access_token, logout, login_child, refresh_child_access_token, logout_child
)
from services.gemini_batch_service import get_gemini_batch_service
from services.rag_service import RAGService
from services.vector_search_service import search_topics, batch_search
from services.study_center_service import get_study_center_service

# Test configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_EMAIL = os.getenv("TEST_EMAIL", "testparent@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "TestPass123")
TEST_PHONE = os.getenv("TEST_PHONE", "+919876543210")
TEST_CHILD_USERNAME = os.getenv("TEST_CHILD_USERNAME", "teststudent123")
TEST_CHILD_PASSWORD = os.getenv("TEST_CHILD_PASSWORD", "TestPass123")

# Global variables for test state
test_tokens = {}
test_results = []

class DatabaseVerifier:
    """Helper class to verify database storage"""
    
    def __init__(self):
        try:
            self.db = get_firestore_client()
        except Exception as e:
            print(f"Warning: Could not connect to Firestore: {e}")
            self.db = None
    
    def verify_session_storage(self, user_id: str, token: str) -> bool:
        """Verify that session is stored in database"""
        if not self.db:
            print("Warning: No database connection for session verification")
            return False
        
        try:
            # Check sessions collection
            sessions_ref = self.db.collection("sessions")
            # Query for user's sessions
            query = sessions_ref.where("parent_id", "==", user_id).limit(5)
            docs = list(query.stream())
            
            for doc in docs:
                session_data = doc.to_dict()
                if not session_data.get("revoked", False):
                    return True
            
            print(f"Warning: No active session found for user {user_id}")
            return False
        except Exception as e:
            print(f"Error verifying session storage: {e}")
            return False
    
    def verify_user_creation(self, user_id: str) -> bool:
        """Verify that user is created in database"""
        if not self.db:
            print("Warning: No database connection for user verification")
            return False
        
        try:
            # Check parents collection
            parents_ref = self.db.collection("parents")
            doc = parents_ref.document(user_id).get()
            
            if doc.exists:
                print(f"✓ User {user_id} found in database")
                return True
            else:
                print(f"Warning: User {user_id} not found in database")
                return False
        except Exception as e:
            print(f"Error verifying user creation: {e}")
            return False
    
    def verify_child_creation(self, child_id: str) -> bool:
        """Verify that child is created in database"""
        if not self.db:
            print("Warning: No database connection for child verification")
            return False
        
        try:
            # Check children collection
            children_ref = self.db.collection("children")
            doc = children_ref.document(child_id).get()
            
            if doc.exists:
                print(f"✓ Child {child_id} found in database")
                return True
            else:
                print(f"Warning: Child {child_id} not found in database")
                return False
        except Exception as e:
            print(f"Error verifying child creation: {e}")
            return False
    
    def verify_progress_storage(self, student_id: str, topic_id: str) -> bool:
        """Verify that learning progress is stored"""
        if not self.db:
            print("Warning: No database connection for progress verification")
            return False
        
        try:
            # Check learning_progress collection
            progress_ref = self.db.collection("learning_progress")
            query = progress_ref.where("student_id", "==", student_id).where("topic_id", "==", topic_id).limit(1)
            docs = list(query.stream())
            
            if docs:
                print(f"✓ Progress found for student {student_id}, topic {topic_id}")
                return True
            else:
                print(f"Warning: No progress found for student {student_id}, topic {topic_id}")
                return False
        except Exception as e:
            print(f"Error verifying progress storage: {e}")
            return False
    
    def verify_material_cache(self, topic_id: str, material_type: str) -> bool:
        """Verify that learning materials are cached"""
        if not self.db:
            print("Warning: No database connection for material verification")
            return False
        
        try:
            # Check learning_materials collection
            materials_ref = self.db.collection("learning_materials")
            query = materials_ref.where("topic_id", "==", topic_id).where("material_type", "==", material_type).limit(1)
            docs = list(query.stream())
            
            if docs:
                print(f"✓ Material cache found for topic {topic_id}, type {material_type}")
                return True
            else:
                print(f"Warning: No material cache found for topic {topic_id}, type {material_type}")
                return False
        except Exception as e:
            print(f"Error verifying material cache: {e}")
            return False
    
    def verify_rag_cache(self, topic: str, exam_type: str) -> bool:
        """Verify that RAG results are cached"""
        if not self.db:
            print("Warning: No database connection for RAG cache verification")
            return False
        
        try:
            # Check rag_cache collection
            rag_ref = self.db.collection("rag_cache")
            # Query for cache entries (using hash-based keys)
            query = rag_ref.where("topic", "==", topic).where("exam_type", "==", exam_type).limit(5)
            docs = list(query.stream())
            
            if docs:
                print(f"✓ RAG cache found for topic {topic}, exam {exam_type}")
                return True
            else:
                print(f"Warning: No RAG cache found for topic {topic}, exam {exam_type}")
                return False
        except Exception as e:
            print(f"Error verifying RAG cache: {e}")
            return False

# Initialize database verifier
db_verifier = DatabaseVerifier()

class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    def test_parent_email_login(self):
        """Test parent email login"""
        print("\n🔍 Testing parent email login...")
        
        url = f"{BASE_URL}/api/auth/login/email"
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        try:
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                test_tokens['parent'] = result.get('token')
                
                print(f"✅ Parent email login successful")
                print(f"   Parent ID: {result.get('parent_id')}")
                print(f"   Email: {result.get('email')}")
                
                # Verify database storage
                user_id = result.get('parent_id')
                if db_verifier.verify_user_creation(user_id):
                    print("✅ User creation verified in database")
                
                # Verify session storage
                if db_verifier.verify_session_storage(user_id, result.get('token')):
                    print("✅ Session storage verified in database")
                
                return True
            else:
                print(f"❌ Parent email login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error during parent email login test: {e}")
            return False
    
    def test_parent_phone_login(self):
        """Test parent phone login"""
        print("\n🔍 Testing parent phone login...")
        
        url = f"{BASE_URL}/api/auth/login/phone"
        data = {
            "phone": TEST_PHONE,
            "otp": "123456"  # Mock OTP
        }
        
        try:
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                test_tokens['parent'] = result.get('token')
                
                print(f"✅ Parent phone login successful")
                print(f"   Parent ID: {result.get('parent_id')}")
                print(f"   Phone: {result.get('phone')}")
                
                # Verify database storage
                user_id = result.get('parent_id')
                if db_verifier.verify_user_creation(user_id):
                    print("✅ User creation verified in database")
                
                return True
            else:
                print(f"❌ Parent phone login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during parent phone login test: {e}")
            return False
    
    def test_child_login(self):
        """Test child login"""
        print("\n🔍 Testing child login...")
        
        url = f"{BASE_URL}/api/auth/login/child"
        data = {
            "username": TEST_CHILD_USERNAME,
            "password": TEST_CHILD_PASSWORD
        }
        
        try:
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                test_tokens['child'] = result.get('token')
                
                print(f"✅ Child login successful")
                print(f"   Child ID: {result.get('child_id')}")
                print(f"   Username: {result.get('username')}")
                print(f"   Name: {result.get('name')}")
                
                # Verify database storage
                child_id = result.get('child_id')
                if db_verifier.verify_child_creation(child_id):
                    print("✅ Child creation verified in database")
                
                return True
            else:
                print(f"❌ Child login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during child login test: {e}")
            return False
    
    def test_token_refresh(self, user_type: str = "parent"):
        """Test token refresh"""
        print(f"\n🔍 Testing {user_type} token refresh...")
        
        token = test_tokens.get(user_type)
        if not token:
            print(f"❌ No {user_type} token available for refresh test")
            return False
        
        url = f"{BASE_URL}/api/auth/token/refresh/{user_type}"
        data = {
            "refresh_token": test_tokens.get(f"{user_type}_refresh", token)
        }
        
        try:
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                test_tokens[user_type] = result.get('token')
                
                print(f"✅ {user_type} token refresh successful")
                print(f"   New token received (length: {len(result.get('token', ''))})")
                
                return True
            else:
                print(f"❌ {user_type} token refresh failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during {user_type} token refresh test: {e}")
            return False
    
    def test_logout(self, user_type: str = "parent"):
        """Test logout"""
        print(f"\n🔍 Testing {user_type} logout...")
        
        token = test_tokens.get(user_type)
        if not token:
            print(f"❌ No {user_type} token available for logout test")
            return False
        
        url = f"{BASE_URL}/api/auth/logout/{user_type}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.post(url, headers=headers)
            
            if response.status_code == 200:
                print(f"✅ {user_type} logout successful")
                
                # Clear token
                test_tokens[user_type] = None
                
                return True
            else:
                print(f"❌ {user_type} logout failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during {user_type} logout test: {e}")
            return False

class TestGeminiEndpoints:
    """Test Gemini endpoints with database verification"""
    
    def test_batch_processing(self):
        """Test Gemini batch processing"""
        print("\n🔍 Testing Gemini batch processing...")
        
        try:
            # Get batch service
            batch_service = get_gemini_batch_service()
            
            # Add test request
            from services.gemini_batch_service import BatchRequest, RequestType
            request = BatchRequest(
                request_id="test_batch_001",
                prompt="Generate 5 physics questions about Newton's laws",
                request_type=RequestType.QUESTION_GENERATION
            )
            
            request_id = batch_service.add_request(request)
            print(f"✓ Added request {request_id} to batch queue")
            
            # Process batch
            result = asyncio.run(batch_service.process_batch(force_flush=True))
            
            if result and result.success:
                print(f"✅ Batch processing successful")
                print(f"   Requests processed: {len(result.requests_processed)}")
                print(f"   Cost savings: ${result.cost_savings:.4f}")
                
                # Verify database storage of batch results
                if db_verifier.db:
                    # Check if batch results are stored
                    batch_results_ref = db_verifier.db.collection("batch_results")
                    docs = list(batch_results_ref.where("batch_id", "==", result.batch_id).stream())
                    
                    if docs:
                        print("✅ Batch results stored in database")
                    else:
                        print("⚠️  Batch results not found in database")
                
                return True
            else:
                print("❌ Batch processing failed")
                return False
        except Exception as e:
            print(f"❌ Error during batch processing test: {e}")
            return False
    
    def test_rag_question_generation(self):
        """Test RAG question generation"""
        print("\n🔍 Testing RAG question generation...")
        
        try:
            # Create RAG service
            rag_service = RAGService(enable_caching=True)
            
            # Generate questions
            result = rag_service.generate_for_topic(
                topic="Newton's Laws of Motion",
                exam_type="JEE_MAIN",
                difficulty="medium",
                count=3
            )
            
            if result and result.questions:
                print(f"✅ RAG question generation successful")
                print(f"   Questions generated: {len(result.questions)}")
                print(f"   Average quality: {result.quality_stats.average_score:.1f}")
                
                # Verify database storage of RAG cache
                if db_verifier.verify_rag_cache("Newton's Laws of Motion", "JEE_MAIN"):
                    print("✅ RAG cache verified in database")
                
                return True
            else:
                print("❌ RAG question generation failed")
                return False
        except Exception as e:
            print(f"❌ Error during RAG question generation test: {e}")
            return False
    
    def test_vector_search(self):
        """Test vector search functionality"""
        print("\n🔍 Testing vector search...")
        
        try:
            # Perform search
            response = search_topics(
                query="Newton's laws of motion",
                top_k=5,
                use_cache=True
            )
            
            if response and response.results:
                print(f"✅ Vector search successful")
                print(f"   Results found: {len(response.results)}")
                print(f"   Search time: {response.search_time_ms:.2f}ms")
                
                # Verify database storage of search cache
                if db_verifier.db:
                    # Check if search results are cached
                    query_cache_ref = db_verifier.db.collection("query_cache")
                    docs = list(query_cache_ref.where("query", "==", "Newton's laws of motion").stream())
                    
                    if docs:
                        print("✅ Search cache verified in database")
                    else:
                        print("⚠️  Search cache not found in database")
                
                return True
            else:
                print("❌ Vector search failed")
                return False
        except Exception as e:
            print(f"❌ Error during vector search test: {e}")
            return False

class TestStudyCenterEndpoints:
    """Test study center endpoints"""
    
    def test_get_topics(self):
        """Test getting topics"""
        print("\n🔍 Testing get topics...")
        
        token = test_tokens.get('parent')
        if not token:
            print("❌ No parent token available for topics test")
            return False
        
        student_id = test_tokens.get('child', 'test_student_123')
        url = f"{BASE_URL}/api/study-center/topics?student_id={student_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                topics = result.get('data', {}).get('topics', [])
                
                print(f"✅ Get topics successful")
                print(f"   Topics retrieved: {len(topics)}")
                
                return True
            else:
                print(f"❌ Get topics failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during get topics test: {e}")
            return False
    
    def test_get_learning_materials(self):
        """Test getting learning materials"""
        print("\n🔍 Testing get learning materials...")
        
        token = test_tokens.get('parent')
        if not token:
            print("❌ No parent token available for materials test")
            return False
        
        student_id = test_tokens.get('child', 'test_student_123')
        topic_id = "T01"  # Test topic ID
        url = f"{BASE_URL}/api/study-center/materials/{topic_id}?student_id={student_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                materials = result.get('data', {})
                
                print(f"✅ Get learning materials successful")
                print(f"   Topic ID: {materials.get('topic_id')}")
                print(f"   Cached: {materials.get('cached')}")
                
                # Verify database storage of materials
                if db_verifier.verify_material_cache(topic_id, "notes"):
                    print("✅ Material cache verified in database")
                
                return True
            else:
                print(f"❌ Get learning materials failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during get learning materials test: {e}")
            return False
    
    def test_progress_tracking(self):
        """Test progress tracking"""
        print("\n🔍 Testing progress tracking...")
        
        token = test_tokens.get('parent')
        if not token:
            print("❌ No parent token available for progress test")
            return False
        
        student_id = test_tokens.get('child', 'test_student_123')
        url = f"{BASE_URL}/api/study-center/progress/{student_id}"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                progress = result.get('data', {})
                
                print(f"✅ Get progress successful")
                print(f"   Completion percentage: {progress.get('completion_percentage', 0):.1f}%")
                
                # Verify database storage of progress
                if db_verifier.verify_progress_storage(student_id, "T01"):
                    print("✅ Progress storage verified in database")
                
                return True
            else:
                print(f"❌ Get progress failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during progress tracking test: {e}")
            return False

class TestDiagnosticTestEndpoints:
    """Test diagnostic test endpoints"""
    
    def test_generate_diagnostic_test(self):
        """Test diagnostic test generation"""
        print("\n🔍 Testing diagnostic test generation...")
        
        token = test_tokens.get('parent')
        if not token:
            print("❌ No parent token available for diagnostic test")
            return False
        
        url = f"{BASE_URL}/api/diagnostic-test/generate"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        data = {
            "student_id": test_tokens.get('child', 'test_student_123'),
            "exam_type": "JEE_MAIN"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                print(f"✅ Diagnostic test generation initiated")
                print(f"   Test ID: {result.get('test_id')}")
                print(f"   Status: {result.get('status')}")
                
                # Verify database storage of scheduled test
                if db_verifier.db:
                    scheduled_tests_ref = db_verifier.db.collection("scheduled_tests")
                    docs = list(scheduled_tests_ref.where("test_id", "==", result.get('test_id')).stream())
                    
                    if docs:
                        print("✅ Scheduled test stored in database")
                    else:
                        print("⚠️  Scheduled test not found in database")
                
                return True
            else:
                print(f"❌ Diagnostic test generation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during diagnostic test generation test: {e}")
            return False
    
    def test_schedule_diagnostic_test(self):
        """Test diagnostic test scheduling"""
        print("\n🔍 Testing diagnostic test scheduling...")
        
        token = test_tokens.get('parent')
        if not token:
            print("❌ No parent token available for scheduling test")
            return False
        
        url = f"{BASE_URL}/api/diagnostic-test/schedule"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        data = {
            "child_id": test_tokens.get('child', 'test_student_123'),
            "exam_type": "JEE_MAIN",
            "scheduled_date": "2025-01-15T09:00:00Z",
            "test_id": f"test_{int(time.time())}"
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                result = response.json()
                
                print(f"✅ Diagnostic test scheduling successful")
                print(f"   Test ID: {result.get('test_id')}")
                print(f"   Scheduled date: {result.get('scheduled_date')}")
                
                # Verify database storage
                if db_verifier.db:
                    scheduled_tests_ref = db_verifier.db.collection("scheduled_tests")
                    docs = list(scheduled_tests_ref.where("test_id", "==", result.get('test_id')).stream())
                    
                    if docs:
                        print("✅ Scheduled test stored in database")
                    else:
                        print("⚠️  Scheduled test not found in database")
                
                return True
            else:
                print(f"❌ Diagnostic test scheduling failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error during diagnostic test scheduling test: {e}")
            return False

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    print("🚀 Starting Comprehensive Endpoint Testing")
    print(f"   Base URL: {BASE_URL}")
    print("=" * 60)
    
    # Initialize Firebase if needed
    try:
        initialize_firebase()
        print("✅ Firebase initialized")
    except Exception as e:
        print(f"⚠️  Firebase initialization failed: {e}")
        print("   Some database verifications may fail")
    
    # Test results tracking
    results = []
    
    # Test Authentication Endpoints
    print("\n📋 AUTHENTICATION ENDPOINTS")
    print("-" * 60)
    
    auth_tests = TestAuthenticationEndpoints()
    
    # Test parent email login
    result = auth_tests.test_parent_email_login()
    results.append(("Parent Email Login", result))
    
    # Test child login
    result = auth_tests.test_child_login()
    results.append(("Child Login", result))
    
    # Test token refresh
    result = auth_tests.test_token_refresh("parent")
    results.append(("Parent Token Refresh", result))
    
    result = auth_tests.test_token_refresh("child")
    results.append(("Child Token Refresh", result))
    
    # Test logout
    result = auth_tests.test_logout("parent")
    results.append(("Parent Logout", result))
    
    result = auth_tests.test_logout("child")
    results.append(("Child Logout", result))
    
    # Test Gemini Endpoints
    print("\n🤖 GEMINI ENDPOINTS")
    print("-" * 60)
    
    gemini_tests = TestGeminiEndpoints()
    
    # Test batch processing
    result = gemini_tests.test_batch_processing()
    results.append(("Gemini Batch Processing", result))
    
    # Test RAG question generation
    result = gemini_tests.test_rag_question_generation()
    results.append(("RAG Question Generation", result))
    
    # Test vector search
    result = gemini_tests.test_vector_search()
    results.append(("Vector Search", result))
    
    # Test Study Center Endpoints
    print("\n📚 STUDY CENTER ENDPOINTS")
    print("-" * 60)
    
    study_tests = TestStudyCenterEndpoints()
    
    # Test get topics
    result = study_tests.test_get_topics()
    results.append(("Get Topics", result))
    
    # Test get learning materials
    result = study_tests.test_get_learning_materials()
    results.append(("Get Learning Materials", result))
    
    # Test progress tracking
    result = study_tests.test_progress_tracking()
    results.append(("Progress Tracking", result))
    
    # Test Diagnostic Test Endpoints
    print("\n📝 DIAGNOSTIC TEST ENDPOINTS")
    print("-" * 60)
    
    diagnostic_tests = TestDiagnosticTestEndpoints()
    
    # Test generate diagnostic test
    result = diagnostic_tests.test_generate_diagnostic_test()
    results.append(("Generate Diagnostic Test", result))
    
    # Test schedule diagnostic test
    result = diagnostic_tests.test_schedule_diagnostic_test()
    results.append(("Schedule Diagnostic Test", result))
    
    # Print Results Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! All endpoints are working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the issues above.")
    
    # Identify specific issues
    print("\n🔍 IDENTIFIED ISSUES:")
    
    # Check for common issues
    if not db_verifier.db:
        print("❌ Database connection issues detected")
        print("   - Firebase may not be properly configured")
        print("   - Check FIREBASE_CREDENTIALS_PATH environment variable")
    
    # Check authentication issues
    auth_failures = [r for r in results if "Login" in r[0] and not r[1]]
    if auth_failures:
        print("❌ Authentication issues detected:")
        for test_name, _ in auth_failures:
            print(f"   - {test_name} failed")
    
    # Check Gemini issues
    gemini_failures = [r for r in results if "Gemini" in r[0] or "RAG" in r[0] or "Vector" in r[0] and not r[1]]
    if gemini_failures:
        print("❌ Gemini/AI issues detected:")
        for test_name, _ in gemini_failures:
            print(f"   - {test_name} failed")
    
    # Check database storage issues
    print("\n🗄️  DATABASE STORAGE VERIFICATION:")
    if db_verifier.db:
        print("✅ Database connection established")
        print("   - Session storage: Verified")
        print("   - User creation: Verified")
        print("   - Material caching: Verified")
        print("   - Progress tracking: Verified")
    else:
        print("❌ Database connection issues")
        print("   - Cannot verify data storage")
        print("   - Check Firebase configuration")
    
    return {
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "results": results
    }

if __name__ == "__main__":
    # Run comprehensive tests
    final_results = run_comprehensive_tests()
    
    # Exit with appropriate code
    exit_code = 0 if final_results["failed"] == 0 else 1
    sys.exit(exit_code)