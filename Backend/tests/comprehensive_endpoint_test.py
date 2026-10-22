#!/usr/bin/env python3
"""
Comprehensive Endpoint Test Script for Mentor AI Platform

This script tests all API endpoints in the Mentor AI EdTech Platform
to verify their functionality and identify any issues.

Author: Mentor AI Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import httpx
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds

# Test data
TEST_PARENT_EMAIL = "testparent@example.com"
TEST_PARENT_PHONE = "+919876543210"
TEST_PARENT_PASSWORD = "TestPassword123"
TEST_PARENT_NAME = "Test Parent"

TEST_CHILD_NAME = "Test Child"
TEST_CHILD_AGE = 16
TEST_CHILD_GRADE = "11"
TEST_CHILD_LEVEL = "intermediate"

TEST_EXAM_TYPE = "JEE_MAIN"
TEST_EXAM_DATE = (datetime.now() + timedelta(days=180)).isoformat() + "Z"

@dataclass
class TestResult:
    """Test result data structure."""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: str = ""
    response_data: Dict[str, Any] = None

class EndpointTester:
    """Comprehensive endpoint tester for Mentor AI Platform."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.test_results: List[TestResult] = []
        self.auth_tokens = {}
        self.test_ids = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
        
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None
    ) -> TestResult:
        """Make HTTP request and record result."""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                response = await self.client.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, params=params, headers=headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, params=params, headers=headers)
            elif method.upper() == "PATCH":
                response = await self.client.patch(url, json=data, params=params, headers=headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response_time = (time.time() - start_time) * 1000
            success = 200 <= response.status_code < 300
            
            try:
                response_data = response.json() if response.content else {}
            except:
                response_data = {"raw_response": response.text}
                
            result = TestResult(
                endpoint=endpoint,
                method=method,
                status_code=response.status_code,
                response_time_ms=response_time,
                success=success,
                response_data=response_data
            )
            
            if not success:
                result.error_message = response_data.get("detail", str(response_data))
                
            return result
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                endpoint=endpoint,
                method=method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
    async def test_health_endpoints(self):
        """Test health check endpoints."""
        logger.info("Testing health endpoints...")
        
        # Root endpoint
        result = await self.make_request("GET", "/")
        self.test_results.append(result)
        
        # Health check
        result = await self.make_request("GET", "/health")
        self.test_results.append(result)
        
    async def test_authentication_endpoints(self):
        """Test authentication and registration endpoints."""
        logger.info("Testing authentication endpoints...")
        
        # Parent registration endpoints
        result = await self.make_request(
            "POST", 
            "/api/auth/register/parent/email",
            data={
                "name": TEST_PARENT_NAME,
                "email": TEST_PARENT_EMAIL,
                "password": TEST_PARENT_PASSWORD
            }
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/auth/register/parent/phone",
            data={
                "name": TEST_PARENT_NAME,
                "phone": TEST_PARENT_PHONE,
                "password": TEST_PARENT_PASSWORD
            }
        )
        self.test_results.append(result)
        
        # Simple registration (for testing)
        result = await self.make_request(
            "POST", 
            "/api/auth/register/simple",
            data={
                "name": TEST_PARENT_NAME,
                "email_address": TEST_PARENT_EMAIL,
                "password": TEST_PARENT_PASSWORD,
                "repeat_password": TEST_PARENT_PASSWORD,
                "mobile_number": TEST_PARENT_PHONE
            }
        )
        self.test_results.append(result)
        
        # Login endpoints
        result = await self.make_request(
            "POST", 
            "/api/auth/login/email",
            data={
                "email": TEST_PARENT_EMAIL,
                "password": TEST_PARENT_PASSWORD
            }
        )
        self.test_results.append(result)
        
        if result.success and result.response_data:
            self.auth_tokens["parent"] = result.response_data.get("access_token")
            
        result = await self.make_request(
            "POST", 
            "/api/auth/login/phone",
            data={
                "phone": TEST_PARENT_PHONE,
                "password": TEST_PARENT_PASSWORD
            }
        )
        self.test_results.append(result)
        
        # Token refresh
        if self.auth_tokens.get("parent"):
            result = await self.make_request(
                "POST", 
                "/api/auth/token/refresh",
                data={"refresh_token": self.auth_tokens["parent"]},
                headers={"Authorization": f"Bearer {self.auth_tokens['parent']}"}
            )
            self.test_results.append(result)
            
        # Logout
        if self.auth_tokens.get("parent"):
            result = await self.make_request(
                "POST", 
                "/api/auth/logout",
                headers={"Authorization": f"Bearer {self.auth_tokens['parent']}"}
            )
            self.test_results.append(result)
            
    async def test_verification_endpoints(self):
        """Test email and phone verification endpoints."""
        logger.info("Testing verification endpoints...")
        
        # Email verification
        result = await self.make_request(
            "POST", 
            "/verify/email/send",
            data={"email": TEST_PARENT_EMAIL}
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/verify/email/confirm",
            data={"email": TEST_PARENT_EMAIL, "code": "ABC123"}
        )
        self.test_results.append(result)
        
        # Phone verification
        result = await self.make_request(
            "POST", 
            "/verify/phone/send",
            data={"phone": TEST_PARENT_PHONE}
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/verify/phone/confirm",
            data={"phone": TEST_PARENT_PHONE, "otp": "123456"}
        )
        self.test_results.append(result)
        
    async def test_onboarding_endpoints(self):
        """Test onboarding endpoints (preferences, child, exam)."""
        logger.info("Testing onboarding endpoints...")
        
        parent_id = "test_parent_123"
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        
        # Preferences endpoints
        result = await self.make_request(
            "POST", 
            "/api/onboarding/preferences",
            data={
                "language": "en",
                "email_notifications": True,
                "sms_notifications": True,
                "push_notifications": True,
                "teaching_involvement": "medium"
            },
            params={"parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/onboarding/preferences",
            params={"parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "PUT", 
            "/api/onboarding/preferences",
            data={"language": "hi", "teaching_involvement": "high"},
            params={"parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Child profile endpoints
        result = await self.make_request(
            "POST", 
            "/child",
            data={
                "name": TEST_CHILD_NAME,
                "age": TEST_CHILD_AGE,
                "grade": TEST_CHILD_GRADE,
                "level": TEST_CHILD_LEVEL
            },
            params={"parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
        child_id = "test_child_123"
        result = await self.make_request(
            "GET", 
            f"/child/{child_id}",
            params={"parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Exam selection endpoints
        result = await self.make_request(
            "GET", 
            "/api/onboarding/exams/available"
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/onboarding/exam/select",
            data={
                "exam_type": TEST_EXAM_TYPE,
                "exam_date": TEST_EXAM_DATE,
                "subject_preferences": {
                    "Physics": 40,
                    "Chemistry": 30,
                    "Mathematics": 30
                }
            },
            params={"parent_id": parent_id, "child_id": child_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/onboarding/exam/preferences",
            params={"child_id": child_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "PUT", 
            "/api/onboarding/exam/preferences",
            data={"Physics": 50, "Chemistry": 25, "Mathematics": 25},
            params={"child_id": child_id, "parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Onboarding status
        result = await self.make_request(
            "GET", 
            "/api/onboarding/status",
            params={"parent_id": parent_id},
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_vector_search_endpoints(self):
        """Test vector search and embedding endpoints."""
        logger.info("Testing vector search endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        
        # Embedding generation
        result = await self.make_request(
            "POST", 
            "/api/vector-search/embeddings/generate",
            data={
                "text": "Newton's laws of motion explain force and motion",
                "task_type": "RETRIEVAL_DOCUMENT",
                "include_metadata": True
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/vector-search/embeddings/batch",
            data={
                "texts": [
                    "Newton's laws of motion",
                    "Electromagnetic induction",
                    "Organic chemistry reactions"
                ],
                "task_type": "RETRIEVAL_DOCUMENT",
                "include_metadata": True
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/vector-search/embeddings/status",
            headers=headers
        )
        self.test_results.append(result)
        
        # Vector search
        result = await self.make_request(
            "POST", 
            "/api/vector-search/query",
            data={
                "query": "laws of motion",
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "limit": 10
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/vector-search/query/batch",
            data={
                "queries": ["motion", "chemistry", "mathematics"],
                "exam_type": "JEE_MAIN",
                "limit": 5
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/vector-search/index/status",
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/vector-search/syllabus/JEE_MAIN/Physics",
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_rag_endpoints(self):
        """Test RAG (Retrieval-Augmented Generation) endpoints."""
        logger.info("Testing RAG endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        
        # Question generation
        result = await self.make_request(
            "POST", 
            "/api/rag/generate-questions",
            data={
                "topic": "Newton's Laws of Motion",
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium",
                "question_count": 5,
                "question_types": ["mcq", "numerical"]
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/rag/generate-batch",
            data={
                "topics": [
                    {"topic": "Kinematics", "question_count": 3},
                    {"topic": "Thermodynamics", "question_count": 2}
                ],
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "difficulty": "medium"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/rag/context/build",
            data={
                "topic": "Newton's Laws",
                "exam_type": "JEE_MAIN",
                "subject": "Physics"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/rag/context/preview",
            data={
                "topic": "Newton's Laws",
                "exam_type": "JEE_MAIN",
                "subject": "Physics"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/rag/pipeline/status",
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/rag/metrics",
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_diagnostic_test_endpoints(self):
        """Test diagnostic test endpoints."""
        logger.info("Testing diagnostic test endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        
        # Test generation
        result = await self.make_request(
            "POST", 
            "/api/diagnostic-test/generate",
            data={
                "student_id": student_id,
                "exam_type": "JEE_MAIN",
                "subject_preferences": {
                    "Physics": 40,
                    "Chemistry": 30,
                    "Mathematics": 30
                },
                "difficulty": "medium",
                "question_count": 90
            },
            headers=headers
        )
        self.test_results.append(result)
        
        if result.success and result.response_data:
            test_id = result.response_data.get("test_id", "test_123")
            self.test_ids["diagnostic"] = test_id
            
            # Get test
            result = await self.make_request(
                "GET", 
                f"/api/diagnostic-test/{test_id}",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get test metadata
            result = await self.make_request(
                "GET", 
                f"/api/diagnostic-test/{test_id}/metadata",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get student tests
            result = await self.make_request(
                "GET", 
                f"/api/diagnostic-test/student/{student_id}",
                headers=headers
            )
            self.test_results.append(result)
            
            # Schedule test
            result = await self.make_request(
                "POST", 
                "/api/diagnostic-test/schedule",
                data={
                    "student_id": student_id,
                    "exam_type": "JEE_MAIN",
                    "scheduled_date": (datetime.now() + timedelta(days=1)).isoformat() + "Z"
                },
                headers=headers
            )
            self.test_results.append(result)
            
            # Get test status
            result = await self.make_request(
                "GET", 
                f"/api/diagnostic-test/{test_id}/status",
                headers=headers
            )
            self.test_results.append(result)
            
            # Start test
            result = await self.make_request(
                "POST", 
                f"/api/diagnostic-test/{test_id}/start",
                data={"student_id": student_id},
                headers=headers
            )
            self.test_results.append(result)
            
    async def test_test_management_endpoints(self):
        """Test test lifecycle management endpoints."""
        logger.info("Testing test management endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        test_id = self.test_ids.get("diagnostic", "test_123")
        student_id = "test_student_123"
        
        # Start test (test management router)
        result = await self.make_request(
            "POST", 
            f"/api/diagnostic-test/{test_id}/start",
            data={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Submit test
        result = await self.make_request(
            "POST", 
            f"/api/diagnostic-test/{test_id}/submit",
            data={
                "test_id": test_id,
                "student_id": student_id,
                "answers": {str(i): "A" for i in range(1, 91)},  # Mock answers
                "time_taken": 5400,  # 90 minutes in seconds
                "submission_time": datetime.now().isoformat() + "Z"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Get results
        result = await self.make_request(
            "GET", 
            f"/api/diagnostic-test/{test_id}/results",
            headers=headers
        )
        self.test_results.append(result)
        
        # Get test status
        result = await self.make_request(
            "GET", 
            f"/api/diagnostic-test/{test_id}/status",
            headers=headers
        )
        self.test_results.append(result)
        
        # Update test status (admin only)
        result = await self.make_request(
            "PATCH", 
            f"/api/diagnostic-test/{test_id}/status",
            data={"status": "completed"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Health check
        result = await self.make_request(
            "GET", 
            "/api/diagnostic-test/management/health",
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_schedule_endpoints(self):
        """Test schedule management endpoints."""
        logger.info("Testing schedule endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        
        # Generate schedule
        result = await self.make_request(
            "POST", 
            "/api/schedule/generate",
            data={
                "student_id": student_id,
                "exam_type": "JEE_MAIN",
                "exam_date": TEST_EXAM_DATE,
                "study_hours_per_day": 4,
                "weak_topics": ["Thermodynamics", "Electromagnetism"],
                "strong_topics": ["Kinematics", "Optics"]
            },
            headers=headers
        )
        self.test_results.append(result)
        
        if result.success and result.response_data:
            schedule_id = result.response_data.get("schedule_id", "schedule_123")
            self.test_ids["schedule"] = schedule_id
            
            # Get schedule
            result = await self.make_request(
                "GET", 
                f"/api/schedule/{schedule_id}",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get student schedules
            result = await self.make_request(
                "GET", 
                f"/api/schedule/student/{student_id}",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get schedule history
            result = await self.make_request(
                "GET", 
                f"/api/schedule/student/{student_id}/history",
                headers=headers
            )
            self.test_results.append(result)
            
            # Regenerate schedule
            result = await self.make_request(
                "POST", 
                f"/api/schedule/{schedule_id}/regenerate",
                data={
                    "reason": "Performance update",
                    "weak_topics": ["Quantum Mechanics"]
                },
                headers=headers
            )
            self.test_results.append(result)
            
            # Update schedule
            result = await self.make_request(
                "PUT", 
                f"/api/schedule/{schedule_id}",
                data={"study_hours_per_day": 5},
                headers=headers
            )
            self.test_results.append(result)
            
            # Update progress
            result = await self.make_request(
                "POST", 
                "/api/schedule/progress/update",
                data={
                    "schedule_id": schedule_id,
                    "student_id": student_id,
                    "topic_id": "topic_123",
                    "completed": True,
                    "time_spent": 120
                },
                headers=headers
            )
            self.test_results.append(result)
            
            # Get progress
            result = await self.make_request(
                "GET", 
                f"/api/schedule/progress/{schedule_id}",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get today's progress
            result = await self.make_request(
                "GET", 
                "/api/schedule/progress/today",
                params={"student_id": student_id},
                headers=headers
            )
            self.test_results.append(result)
            
    async def test_payment_endpoints(self):
        """Test payment and subscription endpoints."""
        logger.info("Testing payment endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        parent_id = "test_parent_123"
        
        # Get subscription plans
        result = await self.make_request(
            "GET", 
            "/api/payment/plans"
        )
        self.test_results.append(result)
        
        # Create payment order
        result = await self.make_request(
            "POST", 
            "/api/payment/create-order",
            data={
                "plan_id": "premium_monthly",
                "amount": 99900,  # ₹999.00 in paise
                "currency": "INR"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        if result.success and result.response_data:
            order_id = result.response_data.get("order_id", "order_123")
            
            # Verify payment
            result = await self.make_request(
                "POST", 
                "/api/payment/verify",
                data={
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": "pay_123",
                    "razorpay_signature": "test_signature"
                },
                headers=headers
            )
            self.test_results.append(result)
            
        # Get subscription
        result = await self.make_request(
            "GET", 
            f"/api/payment/subscription/{parent_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Get transactions
        result = await self.make_request(
            "GET", 
            f"/api/payment/transactions/{parent_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Cancel subscription
        result = await self.make_request(
            "POST", 
            f"/api/payment/cancel/{parent_id}",
            data={"reason": "Not satisfied"},
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_study_center_endpoints(self):
        """Test study center endpoints."""
        logger.info("Testing study center endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        
        # Get topics
        result = await self.make_request(
            "GET", 
            "/api/study-center/topics",
            params={"exam_type": "JEE_MAIN", "subject": "Physics"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get topic details
        result = await self.make_request(
            "GET", 
            "/api/study-center/topics/topic_123",
            headers=headers
        )
        self.test_results.append(result)
        
        # Get learning materials
        result = await self.make_request(
            "GET", 
            "/api/study-center/materials/topic_123",
            headers=headers
        )
        self.test_results.append(result)
        
        # Generate materials
        result = await self.make_request(
            "POST", 
            "/api/study-center/materials/generate",
            data={
                "topic": "Newton's Laws",
                "exam_type": "JEE_MAIN",
                "subject": "Physics",
                "material_types": ["notes", "questions", "videos"]
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Get mindmap
        result = await self.make_request(
            "GET", 
            "/api/study-center/mindmap/topic_123",
            headers=headers
        )
        self.test_results.append(result)
        
        # Teach topic
        result = await self.make_request(
            "GET", 
            "/api/study-center/teach/topic_123",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get progress
        result = await self.make_request(
            "GET", 
            f"/api/study-center/progress/{student_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Start progress
        result = await self.make_request(
            "POST", 
            "/api/study-center/progress/start",
            data={
                "student_id": student_id,
                "topic_id": "topic_123"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Complete progress
        result = await self.make_request(
            "POST", 
            "/api/study-center/progress/complete",
            data={
                "student_id": student_id,
                "topic_id": "topic_123",
                "time_spent": 1200
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Get learning journey
        result = await self.make_request(
            "GET", 
            f"/api/study-center/journey/{student_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Get parent progress view
        result = await self.make_request(
            "GET", 
            "/api/study-center/parent-progress/child_123",
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_ai_features_endpoints(self):
        """Test AI-powered features endpoints."""
        logger.info("Testing AI features endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        
        # AI tutor
        result = await self.make_request(
            "POST", 
            "/api/ai/tutor/ask",
            data={
                "question": "What is Newton's second law?",
                "context": "Physics basics",
                "student_id": student_id
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Get tutor history
        result = await self.make_request(
            "GET", 
            f"/api/ai/tutor/history/{student_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Topic recommendations
        result = await self.make_request(
            "GET", 
            f"/api/ai/recommend/topics/{student_id}",
            params={"exam_type": "JEE_MAIN", "limit": 10},
            headers=headers
        )
        self.test_results.append(result)
        
        # Resource recommendations
        result = await self.make_request(
            "GET", 
            "/api/ai/recommend/resources/topic_123",
            params={"learning_style": "visual", "difficulty": "medium"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Exam readiness
        result = await self.make_request(
            "GET", 
            f"/api/ai/readiness/{student_id}",
            params={"exam_type": "JEE_MAIN"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Mistake analysis
        result = await self.make_request(
            "GET", 
            f"/api/ai/analysis/mistakes/{student_id}",
            params={"exam_type": "JEE_MAIN", "limit": 20},
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_analytics_endpoints(self):
        """Test analytics endpoints."""
        logger.info("Testing analytics endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        test_id = self.test_ids.get("diagnostic", "test_123")
        
        # Generate analytics
        result = await self.make_request(
            "POST", 
            "/api/analytics/generate",
            data={
                "test_id": test_id,
                "student_id": student_id,
                "answers": {str(i): "A" for i in range(1, 91)},
                "include_ai_insights": True,
                "use_cache": True
            },
            headers=headers
        )
        self.test_results.append(result)
        
        if result.success and result.response_data:
            analytics_id = result.response_data.get("analytics_id", "analytics_123")
            
            # Get analytics report
            result = await self.make_request(
                "GET", 
                f"/api/analytics/{analytics_id}",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get AI insights
            result = await self.make_request(
                "GET", 
                f"/api/analytics/{analytics_id}/insights",
                headers=headers
            )
            self.test_results.append(result)
            
            # Get weak topics
            result = await self.make_request(
                "GET", 
                f"/api/analytics/{analytics_id}/weak-topics",
                headers=headers
            )
            self.test_results.append(result)
            
        # Get student analytics
        result = await self.make_request(
            "GET", 
            f"/api/analytics/student/{student_id}",
            params={"limit": 10, "offset": 0},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get test analytics
        result = await self.make_request(
            "GET", 
            f"/api/analytics/test/{test_id}",
            params={"limit": 50},
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_syllabus_coverage_endpoints(self):
        """Test syllabus coverage endpoints."""
        logger.info("Testing syllabus coverage endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        
        # Get student coverage
        result = await self.make_request(
            "GET", 
            f"/api/syllabus/coverage/{student_id}",
            params={"exam_type": "JEE_MAIN"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get untested topics
        result = await self.make_request(
            "GET", 
            f"/api/syllabus/coverage/{student_id}/untested",
            params={"exam_type": "JEE_MAIN", "limit": 20},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get weak topics
        result = await self.make_request(
            "GET", 
            f"/api/syllabus/coverage/{student_id}/weak",
            params={"exam_type": "JEE_MAIN", "threshold": 60.0, "limit": 20},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get recommendations
        result = await self.make_request(
            "GET", 
            f"/api/syllabus/coverage/{student_id}/recommendations",
            params={"exam_type": "JEE_MAIN", "num_topics": 10},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get progress
        result = await self.make_request(
            "GET", 
            f"/api/syllabus/coverage/{student_id}/progress",
            params={"exam_type": "JEE_MAIN"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Get topic details
        result = await self.make_request(
            "GET", 
            f"/api/syllabus/coverage/{student_id}/topic/topic_123",
            params={"exam_type": "JEE_MAIN"},
            headers=headers
        )
        self.test_results.append(result)
        
        # Health check
        result = await self.make_request(
            "GET", 
            "/api/syllabus/coverage/health",
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_dashboard_endpoints(self):
        """Test parent and student dashboard endpoints."""
        logger.info("Testing dashboard endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        child_id = "child_123"
        student_id = "test_student_123"
        
        # Parent dashboard
        result = await self.make_request(
            "GET", 
            f"/api/parent/dashboard/{child_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Weekly report
        result = await self.make_request(
            "GET", 
            f"/api/parent/reports/weekly/{child_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Schedule email reports
        result = await self.make_request(
            "POST", 
            "/api/parent/reports/email-schedule",
            data={
                "email": TEST_PARENT_EMAIL,
                "frequency": "weekly",
                "child_id": child_id
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Notification settings
        result = await self.make_request(
            "GET", 
            "/api/parent/notifications/settings",
            params={"parent_id": "parent_123"},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "PUT", 
            "/api/parent/notifications/settings",
            data={
                "parent_id": "parent_123",
                "email_notifications": True,
                "sms_notifications": False,
                "push_notifications": True
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Goals
        result = await self.make_request(
            "POST", 
            f"/api/parent/goals/{child_id}",
            data={
                "title": "Complete Physics syllabus",
                "description": "Finish all Physics topics in 2 months",
                "target_date": (datetime.now() + timedelta(days=60)).isoformat() + "Z",
                "target_score": 85
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            f"/api/parent/goals/{child_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Student dashboard
        result = await self.make_request(
            "GET", 
            f"/api/student/today/{student_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/student/topic/topic_123/resources",
            headers=headers
        )
        self.test_results.append(result)
        
        # Quick practice
        result = await self.make_request(
            "POST", 
            "/api/student/practice/quick",
            data={
                "student_id": student_id,
                "duration": 30,
                "focus_area": "weak_topics",
                "subject": "Physics"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Doubts
        result = await self.make_request(
            "POST", 
            "/api/student/doubts",
            data={
                "student_id": student_id,
                "question": "What is the difference between kinetic and potential energy?",
                "subject": "Physics",
                "topic": "Work, Energy and Power"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/student/doubts/doubt_123/explanation",
            headers=headers
        )
        self.test_results.append(result)
        
        # Revision
        result = await self.make_request(
            "GET", 
            "/api/student/revision/due",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/student/revision/mark-complete/topic_123",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Bookmarks
        result = await self.make_request(
            "POST", 
            "/api/student/bookmarks",
            data={
                "student_id": student_id,
                "type": "question",
                "item_id": "q_123",
                "title": "Newton's Second Law Question",
                "subject": "Physics"
            },
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "GET", 
            "/api/student/bookmarks",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "DELETE", 
            "/api/student/bookmarks/bookmark_123",
            headers=headers
        )
        self.test_results.append(result)
        
        # Performance insights
        result = await self.make_request(
            "GET", 
            f"/api/student/insights/{student_id}",
            headers=headers
        )
        self.test_results.append(result)
        
        # Peer comparison
        result = await self.make_request(
            "GET", 
            "/api/student/compare/percentile",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
    async def test_gamification_endpoints(self):
        """Test gamification endpoints."""
        logger.info("Testing gamification endpoints...")
        
        headers = {"Authorization": f"Bearer {self.auth_tokens.get('parent', 'test_token')}"}
        student_id = "test_student_123"
        
        # Achievements
        result = await self.make_request(
            "GET", 
            "/api/gamification/achievements",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/gamification/achievements/claim/ach_123",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Daily challenge
        result = await self.make_request(
            "GET", 
            "/api/gamification/challenge/daily",
            headers=headers
        )
        self.test_results.append(result)
        
        result = await self.make_request(
            "POST", 
            "/api/gamification/challenge/daily/submit",
            data={
                "challenge_id": "challenge_2024-01-15",
                "answer": "B",
                "time_taken": 95
            },
            headers=headers
        )
        self.test_results.append(result)
        
        # Leaderboard
        result = await self.make_request(
            "GET", 
            "/api/gamification/challenge/leaderboard",
            headers=headers
        )
        self.test_results.append(result)
        
        # Streak
        result = await self.make_request(
            "GET", 
            "/api/gamification/streak",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
        # Points history
        result = await self.make_request(
            "GET", 
            "/api/gamification/points/history",
            params={"student_id": student_id},
            headers=headers
        )
        self.test_results.append(result)
        
    async def run_all_tests(self):
        """Run all endpoint tests."""
        logger.info("Starting comprehensive endpoint testing...")
        
        try:
            await self.test_health_endpoints()
            await self.test_authentication_endpoints()
            await self.test_verification_endpoints()
            await self.test_onboarding_endpoints()
            await self.test_vector_search_endpoints()
            await self.test_rag_endpoints()
            await self.test_diagnostic_test_endpoints()
            await self.test_test_management_endpoints()
            await self.test_schedule_endpoints()
            await self.test_payment_endpoints()
            await self.test_study_center_endpoints()
            await self.test_ai_features_endpoints()
            await self.test_analytics_endpoints()
            await self.test_syllabus_coverage_endpoints()
            await self.test_dashboard_endpoints()
            await self.test_gamification_endpoints()
            
        except Exception as e:
            logger.error(f"Error during testing: {e}")
            logger.exception("Full traceback:")
            
    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        
        # Group results by endpoint category
        categories = {}
        for result in self.test_results:
            category = result.endpoint.split('/')[2] if len(result.endpoint.split('/')) > 2 else 'root'
            if category not in categories:
                categories[category] = []
            categories[category].append(result)
            
        # Generate report
        report = []
        report.append("# Comprehensive Endpoint Test Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Base URL: {self.base_url}")
        report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total Tests: {total_tests}")
        report.append(f"- Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        report.append(f"- Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        report.append("")
        
        # Category breakdown
        report.append("## Results by Category")
        for category, results in sorted(categories.items()):
            successful = sum(1 for r in results if r.success)
            total = len(results)
            report.append(f"- {category}: {successful}/{total} ({successful/total*100:.1f}%)")
        report.append("")
        
        # Failed tests
        if failed_tests > 0:
            report.append("## Failed Tests")
            for result in self.test_results:
                if not result.success:
                    report.append(f"### {result.method} {result.endpoint}")
                    report.append(f"- Status Code: {result.status_code}")
                    report.append(f"- Error: {result.error_message}")
                    report.append(f"- Response Time: {result.response_time_ms:.2f}ms")
                    report.append("")
                    
        # Slow tests (>2000ms)
        slow_tests = [r for r in self.test_results if r.response_time_ms > 2000]
        if slow_tests:
            report.append("## Slow Tests (>2000ms)")
            for result in sorted(slow_tests, key=lambda x: x.response_time_ms, reverse=True):
                report.append(f"### {result.method} {result.endpoint}")
                report.append(f"- Response Time: {result.response_time_ms:.2f}ms")
                report.append(f"- Status Code: {result.status_code}")
                report.append("")
                
        # Detailed results
        report.append("## Detailed Results")
        for category, results in sorted(categories.items()):
            report.append(f"### {category}")
            for result in results:
                status = "✅" if result.success else "❌"
                report.append(f"{status} {result.method} {result.endpoint} - {result.status_code} ({result.response_time_ms:.2f}ms)")
                
        return "\n".join(report)

async def main():
    """Main function to run tests."""
    async with EndpointTester() as tester:
        await tester.run_all_tests()
        report = tester.generate_report()
        
        # Save report to file
        with open("comprehensive_test_report.md", "w") as f:
            f.write(report)
            
        # Print summary
        print("=" * 80)
        print("COMPREHENSIVE ENDPOINT TEST COMPLETE")
        print("=" * 80)
        print(f"Total Tests: {len(tester.test_results)}")
        print(f"Successful: {sum(1 for r in tester.test_results if r.success)}")
        print(f"Failed: {sum(1 for r in tester.test_results if not r.success)}")
        print(f"Report saved to: comprehensive_test_report.md")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())