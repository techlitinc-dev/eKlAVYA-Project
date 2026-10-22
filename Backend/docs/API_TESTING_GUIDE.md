# Mentor AI Platform - API Testing Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [Onboarding Flow](#onboarding-flow)
4. [Study Center](#study-center)
5. [Diagnostic Tests](#diagnostic-tests)
6. [Schedule Management](#schedule-management)
7. [Payment & Subscriptions](#payment--subscriptions)
8. [AI Features](#ai-features)
9. [Testing Tools](#testing-tools)

---

## Getting Started

### Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

### Required Headers
```
Content-Type: application/json
Authorization: Bearer <your_jwt_token>  # For protected endpoints
```

### Environment Setup
1. Start the backend server:
```bash
./start-dev.sh
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

2. Verify server is running:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "mentor-ai-backend"
}
```

---

## Authentication

### 1. Simple Registration (No Email Verification)

**Endpoint:** `POST /api/auth/register/simple`

**Purpose:** Quick registration for testing without email verification

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/register/simple \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Parent",
    "email_address": "testparent@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
  }'
```

**Response:**
```json
{
  "parent_id": "parent_abc123",
  "email": "testparent@example.com",
  "phone": "+919876543210",
  "verification_required": false,
  "message": "Registration successful"
}
```

### 2. Parent Email Login

**Endpoint:** `POST /api/auth/login/email`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login/email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testparent@example.com",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "parent_id": "parent_abc123",
  "email": "testparent@example.com",
  "phone": null,
  "expires_in": 86400
}
```

**Save the token for subsequent requests!**

### 3. Child Login

**Endpoint:** `POST /api/auth/login/child`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login/child \
  -H "Content-Type: application/json" \
  -d '{
    "username": "teststudent123",
    "password": "StudentPass123"
  }'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "student_id": "child_def456",
  "username": "teststudent123",
  "name": "Test Student",
  "is_student": true,
  "expires_in": 86400
}
```

### 4. Get Current User Profile

**Endpoint:** `GET /api/auth/me`

**Request:**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "parent_id": "parent_abc123",
  "email": "testparent@example.com",
  "phone": "+919876543210",
  "language": "en",
  "role": "parent",
  "email_verified": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 5. Logout

**Endpoint:** `POST /api/auth/logout`

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Onboarding Flow

### Step 1: Set Preferences

**Endpoint:** `POST /api/onboarding/preferences?parent_id=YOUR_PARENT_ID`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/preferences?parent_id=parent_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
  }'
```

**Response:**
```json
{
  "parent_id": "parent_abc123",
  "language": "en",
  "email_notifications": true,
  "sms_notifications": true,
  "push_notifications": true,
  "teaching_involvement": "medium",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Step 2: Create Child Profile

**Endpoint:** `POST /api/onboarding/child?parent_id=YOUR_PARENT_ID`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/child?parent_id=parent_abc123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul_sharma",
    "password": "SecurePass123"
  }'
```

**Response:**
```json
{
  "child_id": "child_def456",
  "parent_id": "parent_abc123",
  "name": "Rahul Sharma",
  "age": 16,
  "grade": 11,
  "current_level": "intermediate",
  "username": "rahul_sharma",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Step 3: Select Exam

**Endpoint:** `POST /api/onboarding/exam/select?parent_id=YOUR_PARENT_ID&child_id=YOUR_CHILD_ID`

**Request:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/exam/select?parent_id=parent_abc123&child_id=child_def456" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    }
  }'
```

**Response:**
```json
{
  "child_id": "child_def456",
  "exam_type": "JEE_MAIN",
  "exam_date": "2025-04-15T00:00:00Z",
  "subject_preferences": {
    "Physics": 40,
    "Chemistry": 30,
    "Mathematics": 30
  },
  "days_until_exam": 90,
  "diagnostic_test_id": "test_ghi789",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Step 4: Check Onboarding Status

**Endpoint:** `GET /api/onboarding/status?parent_id=YOUR_PARENT_ID`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/status?parent_id=parent_abc123"
```

**Response:**
```json
{
  "preferences_completed": true,
  "child_profile_completed": true,
  "exam_selected": true,
  "onboarding_complete": true
}
```

---

## Study Center

### 1. Get Available Topics

**Endpoint:** `GET /api/study-center/topics?student_id=YOUR_STUDENT_ID&subject=Physics`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/study-center/topics?student_id=child_def456&subject=Physics" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "success": true,
  "message": "Topics retrieved successfully",
  "data": {
    "topics": [
      {
        "topic_id": "T01",
        "topic_name": "Kinematics",
        "subject": "Physics",
        "chapter": "Motion",
        "difficulty": "medium",
        "estimated_hours": 4.0,
        "progress_percentage": 0.0
      }
    ],
    "total_count": 62
  }
}
```

### 2. Get Learning Materials

**Endpoint:** `GET /api/study-center/materials/T01`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/study-center/materials/T01" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "success": true,
  "message": "Learning materials retrieved successfully",
  "data": {
    "topic_id": "T01",
    "topic_name": "Kinematics",
    "cached": false,
    "generated_at": "2024-01-15T10:30:00Z",
    "has_notes": true,
    "has_mind_map": true,
    "has_teaching_content": true,
    "notes": "# Kinematics\n\n## Introduction\n...",
    "mind_map": {
      "mindmap_id": "mm_T01",
      "structure": {...}
    }
  }
}
```

### 3. Start Learning Session

**Endpoint:** `POST /api/study-center/progress/start`

**Request:**
```bash
curl -X POST http://localhost:8000/api/study-center/progress/start \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "child_def456",
    "topic_id": "T01",
    "topic_name": "Kinematics",
    "subject": "Physics"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Learning session started successfully",
  "data": {
    "session_id": "sess_abc123",
    "topic_id": "T01",
    "start_time": "2024-01-15T10:30:00Z"
  }
}
```

### 4. Complete Learning Session

**Endpoint:** `POST /api/study-center/progress/complete`

**Request:**
```bash
curl -X POST http://localhost:8000/api/study-center/progress/complete \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "child_def456",
    "topic_id": "T01",
    "session_id": "sess_abc123"
  }'
```

### 5. Get Progress Summary

**Endpoint:** `GET /api/study-center/progress/child_def456`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/study-center/progress/child_def456" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "student_id": "child_def456",
    "total_topics": 62,
    "completed_topics": 5,
    "in_progress_topics": 2,
    "completion_percentage": 8.1,
    "total_study_hours": 12.5
  }
}
```

---

## Diagnostic Tests

### 1. Schedule Diagnostic Test

**Endpoint:** `POST /api/diagnostic-test/schedule`

**Request:**
```bash
curl -X POST http://localhost:8000/api/diagnostic-test/schedule \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_def456",
    "exam_type": "JEE_MAIN",
    "scheduled_date": "2025-01-20T09:00:00Z",
    "test_id": "test_123456"
  }'
```

**Response:**
```json
{
  "test_id": "test_123456",
  "scheduled_date": "2025-01-20T09:00:00Z",
  "status": "scheduled",
  "message": "Diagnostic test scheduled successfully"
}
```

### 2. Start Test

**Endpoint:** `POST /api/diagnostic-test/{test_id}/start`

**Request:**
```bash
curl -X POST http://localhost:8000/api/diagnostic-test/test_123456/start \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "child_def456"
  }'
```

**Response:**
```json
{
  "message": "Test started successfully",
  "data": {
    "test_id": "test_123456",
    "start_time": "2024-01-15T10:30:00Z",
    "duration_minutes": 180
  }
}
```

### 3. Submit Test

**Endpoint:** `POST /api/diagnostic-test/{test_id}/submit`

**Request:**
```bash
curl -X POST http://localhost:8000/api/diagnostic-test/test_123456/submit \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test_123456",
    "student_id": "child_def456",
    "answers": {
      "1": "A",
      "2": "B",
      "3": "C"
    },
    "time_taken": 10800,
    "submission_time": "2024-01-15T13:30:00Z"
  }'
```

**Response:**
```json
{
  "test_id": "test_123456",
  "student_id": "child_def456",
  "total_score": 280,
  "total_marks": 360,
  "percentage": 77.78,
  "section_scores": {
    "Physics": {
      "section_name": "Section - Physics",
      "score": 96,
      "total_marks": 120,
      "correct": 25,
      "incorrect": 3,
      "unattempted": 2
    }
  },
  "correct_count": 72,
  "incorrect_count": 10,
  "unattempted_count": 8
}
```

### 4. Get Test Results

**Endpoint:** `GET /api/diagnostic-test/{test_id}/results`

**Request:**
```bash
curl -X GET http://localhost:8000/api/diagnostic-test/test_123456/results \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Schedule Management

### 1. Generate Study Schedule

**Endpoint:** `POST /api/schedule/generate`

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "child_def456",
    "analytics_id": "analytics_123",
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15",
    "daily_study_hours": 5.0
  }'
```

**Response:**
```json
{
  "schedule_id": "schedule_student_123_1234567890",
  "student_id": "child_def456",
  "exam_type": "JEE_MAIN",
  "status": "active",
  "start_date": "2024-01-15",
  "exam_date": "2025-04-15",
  "daily_study_hours": 5.0,
  "completion_percentage": 0.0,
  "days": []
}
```

### 2. Get Schedule

**Endpoint:** `GET /api/schedule/{schedule_id}`

**Request:**
```bash
curl -X GET http://localhost:8000/api/schedule/schedule_student_123_1234567890 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### 3. Update Daily Progress

**Endpoint:** `POST /api/schedule/progress/update`

**Request:**
```bash
curl -X POST http://localhost:8000/api/schedule/progress/update \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "schedule_student_123_1234567890",
    "day_number": 1,
    "completion_percentage": 100,
    "topics_completed": ["Kinematics"],
    "hours_studied": 5.0
  }'
```

### 4. Get Today's Tasks

**Endpoint:** `GET /api/schedule/progress/today?schedule_id=YOUR_SCHEDULE_ID`

**Request:**
```bash
curl -X GET "http://localhost:8000/api/schedule/progress/today?schedule_id=schedule_student_123_1234567890" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Payment & Subscriptions

### 1. Get Subscription Plans

**Endpoint:** `GET /api/payment/plans`

**Request:**
```bash
curl -X GET http://localhost:8000/api/payment/plans
```

**Response:**
```json
[
  {
    "plan_id": "free",
    "name": "Free Plan",
    "price": 0,
    "duration_days": 365,
    "features": ["1 diagnostic test", "Basic analytics"],
    "currency": "INR",
    "is_active": true
  },
  {
    "plan_id": "premium_monthly",
    "name": "Premium Monthly",
    "price": 99900,
    "duration_days": 30,
    "features": ["Unlimited tests", "Advanced analytics"],
    "currency": "INR",
    "is_active": true
  }
]
```

### 2. Create Payment Order

**Endpoint:** `POST /api/payment/create-order`

**Request:**
```bash
curl -X POST http://localhost:8000/api/payment/create-order \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": "parent_abc123",
    "plan_id": "premium_monthly"
  }'
```

**Response:**
```json
{
  "order_id": "order_MNxkZ1aB2cD3eF",
  "amount": 99900,
  "currency": "INR",
  "receipt": "rcpt_20240115_103000_A7K9M",
  "status": "created"
}
```

### 3. Get Subscription Status

**Endpoint:** `GET /api/payment/subscription/{parent_id}`

**Request:**
```bash
curl -X GET http://localhost:8000/api/payment/subscription/parent_abc123 \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Response:**
```json
{
  "is_active": true,
  "plan_name": "Premium Monthly",
  "plan_id": "premium_monthly",
  "status": "active",
  "days_remaining": 25,
  "end_date": "2024-02-14T10:30:00Z",
  "auto_renew": false
}
```

---

## AI Features

### 1. Vector Search (Gemini-based)

**Endpoint:** `POST /api/vector-search/query`

**Request:**
```bash
curl -X POST http://localhost:8000/api/vector-search/query \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are Newton'\''s laws of motion?",
    "top_k": 5,
    "filters": {
      "exam": "JEE_MAIN",
      "subject": "Physics"
    },
    "include_metadata": true
  }'
```

**Response:**
```json
{
  "query": "What are Newton's laws of motion?",
  "results": [
    {
      "topic": "Newton's Laws of Motion",
      "chapter": "Mechanics",
      "content": "Newton's first law states...",
      "similarity_score": 0.92,
      "rank": 1,
      "exam": "JEE_MAIN",
      "subject": "Physics"
    }
  ],
  "total_results": 5,
  "search_time_ms": 125.5
}
```

### 2. RAG Question Generation

**Endpoint:** `POST /api/rag/generate-questions`

**Request:**
```bash
curl -X POST http://localhost:8000/api/rag/generate-questions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "num_questions": 5,
    "include_explanations": true
  }'
```

**Response:**
```json
{
  "questions": [
    {
      "question_id": "q_123",
      "question_text": "Find the limit...",
      "options": ["A", "B", "C", "D"],
      "correct_answer": "B",
      "explanation": "...",
      "difficulty": "medium"
    }
  ],
  "metadata": {
    "topic": "Limits and Continuity",
    "exam_type": "JEE_MAIN",
    "generation_method": "RAG"
  },
  "total_questions": 5
}
```

---

## Testing Tools

### Automated Test Runner

Run all endpoint tests:
```bash
python3 run_endpoint_tests.py
```

### Individual Endpoint Testing

Use the provided curl commands or tools like:
- **Postman**: Import the API collection
- **HTTPie**: `http POST localhost:8000/api/auth/login/email email=test@example.com password=pass123`
- **Python requests**: See test scripts in `tests/` folder

### Common Issues

1. **401 Unauthorized**: Token expired or invalid
   - Solution: Login again to get a new token

2. **403 Forbidden**: Accessing resources you don't own
   - Solution: Use correct parent_id/student_id

3. **422 Validation Error**: Invalid request body
   - Solution: Check request format matches examples

4. **500 Internal Server Error**: Server-side issue
   - Solution: Check server logs for details

### Environment Variables

Required in `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_CREDENTIALS_PATH=config/firebase-credentials.json
JWT_SECRET_KEY=your_secret_key
```

---

## Next Steps

1. Test authentication flow
2. Complete onboarding for a test user
3. Explore study center features
4. Generate and take a diagnostic test
5. Create a study schedule
6. Test payment flow (use test mode)

For more details, see:
- API Documentation: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
