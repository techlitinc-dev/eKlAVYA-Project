# Complete Endpoint Reference - Mentor AI Platform

## Base URL
```
Development: http://localhost:8000
Production: https://api.mentorai.com
```

---

## Table of Contents
1. [Health & System](#health--system)
2. [Authentication](#authentication)
3. [Onboarding](#onboarding)
4. [Study Center](#study-center)
5. [Diagnostic Tests](#diagnostic-tests)
6. [Schedule Management](#schedule-management)
7. [Payment & Subscriptions](#payment--subscriptions)
8. [AI Features](#ai-features)

---

## Health & System

### GET /health
**Description:** Check API health status  
**Authentication:** None  
**Response:** `200 OK`
```json
{
  "status": "healthy",
  "service": "mentor-ai-backend"
}
```

### GET /
**Description:** Root endpoint with API information  
**Authentication:** None  
**Response:** `200 OK` - API metadata and available endpoints

---

## Authentication

### POST /api/auth/register/simple
**Description:** Simple registration without email verification  
**Authentication:** None  
**Request Body:**
```json
{
  "name": "string",
  "email_address": "string",
  "password": "string (min 8 chars)",
  "repeat_password": "string",
  "mobile_number": "string (+91XXXXXXXXXX)"
}
```
**Response:** `201 Created`
```json
{
  "parent_id": "string",
  "email": "string",
  "phone": "string",
  "verification_required": false,
  "message": "string"
}
```

### POST /api/auth/login/email
**Description:** Parent login with email and password  
**Authentication:** None  
**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```
**Response:** `200 OK`
```json
{
  "token": "string (JWT)",
  "refresh_token": "string",
  "parent_id": "string",
  "email": "string",
  "phone": "string | null",
  "expires_in": 86400
}
```

### POST /api/auth/login/child
**Description:** Child/student login with username and password  
**Authentication:** None  
**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```
**Response:** `200 OK`
```json
{
  "token": "string (JWT)",
  "refresh_token": "string",
  "student_id": "string",
  "username": "string",
  "name": "string",
  "is_student": true,
  "expires_in": 86400
}
```

### GET /api/auth/me
**Description:** Get current authenticated user profile  
**Authentication:** Bearer Token (Required)  
**Response:** `200 OK` - User profile data

### POST /api/auth/logout
**Description:** Logout and revoke session  
**Authentication:** Bearer Token (Required)  
**Response:** `200 OK`
```json
{
  "message": "Logout successful"
}
```

---

## Onboarding

### POST /api/onboarding/preferences
**Description:** Set parent preferences  
**Authentication:** Query param `parent_id`  
**Query Params:** `parent_id` (required)  
**Request Body:**
```json
{
  "language": "en | hi | mr",
  "email_notifications": boolean,
  "sms_notifications": boolean,
  "push_notifications": boolean,
  "teaching_involvement": "high | medium | low"
}
```
**Response:** `201 Created` - Preferences object with timestamps

### GET /api/onboarding/preferences
**Description:** Get parent preferences  
**Authentication:** Query param `parent_id`  
**Query Params:** `parent_id` (required)  
**Response:** `200 OK` - Preferences object

### POST /api/onboarding/child
**Description:** Create child profile (one per parent)  
**Authentication:** Query param `parent_id`  
**Query Params:** `parent_id` (required)  
**Request Body:**
```json
{
  "name": "string (2-100 chars)",
  "age": number (14-19),
  "grade": number (9-12),
  "current_level": "beginner | intermediate | advanced"
}
```
**Response:** `201 Created`
```json
{
  "child_id": "string",
  "parent_id": "string",
  "name": "string",
  "age": number,
  "grade": number,
  "current_level": "string",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

### GET /api/onboarding/child
**Description:** Get child profile  
**Authentication:** Query param `parent_id`  
**Query Params:** `parent_id` (required)  
**Response:** `200 OK` - Child profile object

### GET /api/onboarding/exams/available
**Description:** List available exams with dates  
**Authentication:** None  
**Response:** `200 OK`
```json
{
  "exams": [
    {
      "exam_type": "JEE_MAIN | JEE_ADVANCED | NEET",
      "exam_name": "string",
      "available_dates": ["ISO 8601"],
      "subjects": ["string"]
    }
  ]
}
```

### POST /api/onboarding/exam/select
**Description:** Select exam and schedule diagnostic test  
**Authentication:** Query params `parent_id`, `child_id`  
**Query Params:** `parent_id`, `child_id` (both required)  
**Request Body:**
```json
{
  "exam_type": "JEE_MAIN | JEE_ADVANCED | NEET",
  "exam_date": "ISO 8601",
  "subject_preferences": {
    "Physics": number,
    "Chemistry": number,
    "Mathematics": number  // or Biology for NEET
  }
}
```
**Note:** Subject preferences must sum to 100  
**Response:** `201 Created`
```json
{
  "child_id": "string",
  "exam_type": "string",
  "exam_date": "ISO 8601",
  "subject_preferences": object,
  "days_until_exam": number,
  "diagnostic_test_id": "string",
  "created_at": "ISO 8601"
}
```

### GET /api/onboarding/status
**Description:** Check onboarding completion status  
**Authentication:** Query param `parent_id`  
**Query Params:** `parent_id` (required)  
**Response:** `200 OK`
```json
{
  "preferences_completed": boolean,
  "child_profile_completed": boolean,
  "exam_selected": boolean,
  "onboarding_complete": boolean
}
```

---

## Study Center

### GET /api/study-center/topics
**Description:** Get available topics for student  
**Authentication:** Bearer Token (Required)  
**Query Params:** `student_id` (required), `subject` (optional)  
**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Topics retrieved successfully",
  "data": {
    "topics": [
      {
        "topic_id": "string",
        "topic_name": "string",
        "subject": "string",
        "chapter": "string",
        "difficulty": "easy | medium | hard",
        "estimated_hours": number,
        "progress_percentage": number
      }
    ],
    "total_count": number
  }
}
```

### GET /api/study-center/topics/{topic_id}
**Description:** Get detailed topic information  
**Authentication:** Bearer Token (Required)  
**Path Params:** `topic_id`  
**Response:** `200 OK` - Detailed topic object

### GET /api/study-center/materials/{topic_id}
**Description:** Get learning materials for topic  
**Authentication:** Bearer Token (Required)  
**Path Params:** `topic_id`  
**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "topic_id": "string",
    "topic_name": "string",
    "cached": boolean,
    "generated_at": "ISO 8601",
    "has_notes": boolean,
    "has_mind_map": boolean,
    "has_teaching_content": boolean,
    "notes": "string (markdown)",
    "mind_map": object,
    "teaching_content": object
  }
}
```

### POST /api/study-center/materials/generate
**Description:** Force regenerate learning materials  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "student_id": "string",
  "topic_id": "string",
  "material_type": "notes | mind_map | teaching_content | all"
}
```
**Response:** `200 OK` - Newly generated materials

### GET /api/study-center/mindmap/{topic_id}
**Description:** Get mind map for topic  
**Authentication:** Bearer Token (Required)  
**Path Params:** `topic_id`  
**Response:** `200 OK` - Mind map structure

### GET /api/study-center/teach/{topic_id}
**Description:** Get teaching content for topic  
**Authentication:** Bearer Token (Required)  
**Path Params:** `topic_id`  
**Response:** `200 OK` - Teaching content with examples

### POST /api/study-center/progress/start
**Description:** Start learning session  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "student_id": "string",
  "topic_id": "string",
  "topic_name": "string",
  "subject": "string"
}
```
**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "session_id": "string",
    "topic_id": "string",
    "start_time": "ISO 8601"
  }
}
```

### POST /api/study-center/progress/complete
**Description:** Complete learning session  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "student_id": "string",
  "topic_id": "string",
  "session_id": "string"
}
```
**Response:** `200 OK` - Updated progress

### GET /api/study-center/progress/{student_id}
**Description:** Get student's learning progress  
**Authentication:** Bearer Token (Required)  
**Path Params:** `student_id`  
**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "student_id": "string",
    "total_topics": number,
    "completed_topics": number,
    "in_progress_topics": number,
    "completion_percentage": number,
    "total_study_hours": number
  }
}
```

### GET /api/study-center/journey/{student_id}
**Description:** Get recommended learning journey  
**Authentication:** Bearer Token (Required)  
**Path Params:** `student_id`  
**Response:** `200 OK` - Learning journey with recommendations

### GET /api/study-center/parent-progress/{child_id}
**Description:** Get child's progress for parent dashboard  
**Authentication:** Bearer Token (Required)  
**Path Params:** `child_id`  
**Query Params:** `child_name` (optional)  
**Response:** `200 OK` - Parent insights with analytics

---

## Diagnostic Tests

### POST /api/diagnostic-test/schedule
**Description:** Schedule diagnostic test  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "child_id": "string",
  "exam_type": "JEE_MAIN | JEE_ADVANCED | NEET",
  "scheduled_date": "ISO 8601",
  "test_id": "string"
}
```
**Response:** `201 Created`
```json
{
  "test_id": "string",
  "scheduled_date": "ISO 8601",
  "status": "scheduled",
  "message": "Diagnostic test scheduled successfully"
}
```

### POST /api/diagnostic-test/{test_id}/start
**Description:** Start diagnostic test  
**Authentication:** Bearer Token (Required)  
**Path Params:** `test_id`  
**Request Body:**
```json
{
  "student_id": "string"
}
```
**Response:** `200 OK`
```json
{
  "message": "Test started successfully",
  "data": {
    "test_id": "string",
    "start_time": "ISO 8601",
    "duration_minutes": number
  }
}
```

### POST /api/diagnostic-test/{test_id}/submit
**Description:** Submit test answers  
**Authentication:** Bearer Token (Required)  
**Path Params:** `test_id`  
**Request Body:**
```json
{
  "test_id": "string",
  "student_id": "string",
  "answers": {
    "1": "A",
    "2": "B"
  },
  "time_taken": number,
  "submission_time": "ISO 8601"
}
```
**Response:** `200 OK`
```json
{
  "test_id": "string",
  "student_id": "string",
  "total_score": number,
  "total_marks": number,
  "percentage": number,
  "section_scores": object,
  "correct_count": number,
  "incorrect_count": number,
  "unattempted_count": number
}
```

### GET /api/diagnostic-test/{test_id}/results
**Description:** Get test results  
**Authentication:** Bearer Token (Required)  
**Path Params:** `test_id`  
**Response:** `200 OK` - Complete test results

### GET /api/diagnostic-test/{test_id}/status
**Description:** Get test status and timing  
**Authentication:** Bearer Token (Required)  
**Path Params:** `test_id`  
**Response:** `200 OK`
```json
{
  "test_id": "string",
  "status": "pending | in_progress | completed | expired",
  "duration_minutes": number,
  "start_time": "ISO 8601 | null",
  "time_remaining": number | null,
  "submission_time": "ISO 8601 | null"
}
```

### GET /api/diagnostic-test/{test_id}/metadata
**Description:** Get test metadata without questions  
**Authentication:** Bearer Token (Required)  
**Path Params:** `test_id`  
**Response:** `200 OK` - Test metadata

### GET /api/diagnostic-test/student/{student_id}
**Description:** Get all tests for student  
**Authentication:** Bearer Token (Required)  
**Path Params:** `student_id`  
**Query Params:** `status` (optional), `limit` (default: 10), `offset` (default: 0)  
**Response:** `200 OK` - List of test metadata

---

## Schedule Management

### POST /api/schedule/generate
**Description:** Generate AI-powered study schedule  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "student_id": "string",
  "analytics_id": "string",
  "exam_type": "JEE_MAIN | JEE_ADVANCED | NEET",
  "exam_date": "YYYY-MM-DD",
  "daily_study_hours": number (2-8)
}
```
**Response:** `201 Created`
```json
{
  "schedule_id": "string",
  "student_id": "string",
  "exam_type": "string",
  "status": "active",
  "start_date": "YYYY-MM-DD",
  "exam_date": "YYYY-MM-DD",
  "daily_study_hours": number,
  "completion_percentage": number,
  "days": []
}
```

### GET /api/schedule/{schedule_id}
**Description:** Get complete schedule  
**Authentication:** Bearer Token (Required)  
**Path Params:** `schedule_id`  
**Response:** `200 OK` - Complete schedule with all days

### GET /api/schedule/student/{student_id}
**Description:** Get active student schedule  
**Authentication:** Bearer Token (Required)  
**Path Params:** `student_id`  
**Query Params:** `status_filter` (default: "active")  
**Response:** `200 OK` - Active schedule or null

### GET /api/schedule/student/{student_id}/history
**Description:** Get schedule history  
**Authentication:** Bearer Token (Required)  
**Path Params:** `student_id`  
**Query Params:** `limit` (default: 10, max: 100)  
**Response:** `200 OK` - List of schedules

### POST /api/schedule/{schedule_id}/regenerate
**Description:** Regenerate remaining schedule  
**Authentication:** Bearer Token (Required)  
**Path Params:** `schedule_id`  
**Request Body:**
```json
{
  "current_day": number
}
```
**Response:** `200 OK` - Updated schedule

### POST /api/schedule/progress/update
**Description:** Update daily progress  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "schedule_id": "string",
  "day_number": number,
  "completion_percentage": number,
  "topics_completed": ["string"],
  "hours_studied": number,
  "notes": "string"
}
```
**Response:** `200 OK` - Updated progress

### GET /api/schedule/progress/{schedule_id}
**Description:** Get progress summary  
**Authentication:** Bearer Token (Required)  
**Path Params:** `schedule_id`  
**Response:** `200 OK`
```json
{
  "total_days_completed": number,
  "total_topics_completed": number,
  "total_hours_studied": number,
  "completion_percentage": number,
  "days_ahead_behind": number,
  "average_daily_study_time": number,
  "current_study_streak": number,
  "days_until_exam": number
}
```

### GET /api/schedule/progress/today
**Description:** Get today's tasks  
**Authentication:** Bearer Token (Required)  
**Query Params:** `schedule_id` (required)  
**Response:** `200 OK` - List of today's topics with details

---

## Payment & Subscriptions

### GET /api/payment/plans
**Description:** Get all subscription plans  
**Authentication:** None  
**Response:** `200 OK`
```json
[
  {
    "plan_id": "string",
    "name": "string",
    "price": number,
    "duration_days": number,
    "features": ["string"],
    "currency": "INR",
    "is_active": boolean
  }
]
```

### POST /api/payment/create-order
**Description:** Create Razorpay payment order  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "parent_id": "string",
  "plan_id": "string"
}
```
**Response:** `201 Created`
```json
{
  "order_id": "string",
  "amount": number,
  "currency": "INR",
  "receipt": "string",
  "status": "created"
}
```

### POST /api/payment/verify
**Description:** Verify payment and activate subscription  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "order_id": "string",
  "payment_id": "string",
  "razorpay_signature": "string"
}
```
**Response:** `200 OK` - Subscription details

### GET /api/payment/subscription/{parent_id}
**Description:** Get subscription status  
**Authentication:** Bearer Token (Required)  
**Path Params:** `parent_id`  
**Response:** `200 OK`
```json
{
  "is_active": boolean,
  "plan_name": "string",
  "plan_id": "string",
  "status": "active | expired | cancelled",
  "days_remaining": number,
  "end_date": "ISO 8601",
  "auto_renew": boolean
}
```

### GET /api/payment/transactions/{parent_id}
**Description:** Get transaction history  
**Authentication:** Bearer Token (Required)  
**Path Params:** `parent_id`  
**Response:** `200 OK` - List of transactions

### POST /api/payment/cancel/{parent_id}
**Description:** Cancel subscription  
**Authentication:** Bearer Token (Required)  
**Path Params:** `parent_id`  
**Response:** `200 OK` - Cancelled subscription details

---

## AI Features

### POST /api/vector-search/query
**Description:** Semantic search using Gemini API  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "query": "string",
  "top_k": number (1-50, default: 10),
  "filters": {
    "exam": "JEE_MAIN | JEE_ADVANCED | NEET",
    "subject": "Physics | Chemistry | Mathematics | Biology",
    "difficulty": "easy | medium | hard"
  },
  "include_metadata": boolean,
  "min_similarity_score": number (0-1)
}
```
**Response:** `200 OK`
```json
{
  "query": "string",
  "results": [
    {
      "topic": "string",
      "chapter": "string",
      "content": "string",
      "similarity_score": number,
      "rank": number,
      "exam": "string",
      "subject": "string"
    }
  ],
  "total_results": number,
  "search_time_ms": number,
  "cached": boolean
}
```

### POST /api/vector-search/query/batch
**Description:** Batch search multiple queries  
**Authentication:** Bearer Token (Required)  
**Request Body:**
```json
{
  "queries": ["string"],
  "top_k": number,
  "filters": object,
  "include_metadata": boolean
}
```
**Response:** `200 OK` - Batch search results

### GET /api/vector-search/index/status
**Description:** Get search service status  
**Authentication:** Bearer Token (Required)  
**Response:** `200 OK` - Service status and statistics

### GET /api/vector-search/syllabus/{exam}/{subject}
**Description:** Get syllabus content  
**Authentication:** Bearer Token (Required)  
**Path Params:** `exam`, `subject`  
**Response:** `200 OK` - Syllabus topics and metadata

### GET /api/vector-search/syllabus/stats
**Description:** Get syllabus statistics  
**Authentication:** Bearer Token (Required)  
**Response:** `200 OK` - Comprehensive syllabus stats

### POST /api/rag/generate-questions
**Description:** Generate questions using RAG  
**Authentication:** None  
**Request Body:**
```json
{
  "topic": "string",
  "exam_type": "JEE_MAIN | JEE_ADVANCED | NEET",
  "difficulty": "easy | medium | hard",
  "num_questions": number (1-20),
  "include_explanations": boolean,
  "question_type": "single_correct | multiple_correct | numerical",
  "use_cache": boolean
}
```
**Response:** `200 OK`
```json
{
  "questions": [
    {
      "question_id": "string",
      "question_text": "string",
      "options": ["string"],
      "correct_answer": "string",
      "explanation": "string",
      "difficulty": "string"
    }
  ],
  "metadata": object,
  "generation_time": number,
  "quality_stats": object,
  "cache_hit": boolean,
  "total_questions": number
}
```

### POST /api/rag/generate-batch
**Description:** Generate questions for multiple topics  
**Authentication:** None  
**Request Body:**
```json
{
  "topics": ["string"],
  "exam_type": "string",
  "difficulty": "string",
  "questions_per_topic": number,
  "include_explanations": boolean
}
```
**Response:** `200 OK` - Dictionary mapping topics to results

### GET /api/rag/pipeline/status
**Description:** Check RAG pipeline health  
**Authentication:** None  
**Response:** `200 OK` - Health status of all components

### GET /api/rag/metrics
**Description:** Get generation performance metrics  
**Authentication:** None  
**Response:** `200 OK` - Performance statistics

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Error message describing validation issue"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required" | "Token expired"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied to this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

### 429 Too Many Requests
```json
{
  "detail": {
    "error": "Rate limit exceeded",
    "message": "Maximum X requests per minute allowed",
    "retry_after_seconds": number
  }
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service temporarily unavailable"
}
```

---

## Rate Limits

- **Vector Search:** 50 requests/minute per user
- **Embeddings:** 100 requests/minute per user
- **Diagnostic Tests:** 1 generation per hour per student
- **Other endpoints:** No specific limits (general API rate limiting applies)

---

## Authentication

Most endpoints require authentication using JWT tokens:

```
Authorization: Bearer <your_jwt_token>
```

Tokens expire after 24 hours. Use the refresh token endpoint to get a new token without re-authenticating.

---

## Pagination

Endpoints that return lists support pagination:

**Query Parameters:**
- `limit`: Number of items per page (default varies by endpoint)
- `offset`: Number of items to skip

**Example:**
```
GET /api/diagnostic-test/student/child_123?limit=10&offset=20
```

---

## Filtering

Many endpoints support filtering via query parameters or request body filters:

**Common Filters:**
- `exam`: JEE_MAIN, JEE_ADVANCED, NEET
- `subject`: Physics, Chemistry, Mathematics, Biology
- `difficulty`: easy, medium, hard
- `status`: pending, in_progress, completed, etc.

---

## Date Formats

All dates use ISO 8601 format:
- **Date only:** `YYYY-MM-DD`
- **Date and time:** `YYYY-MM-DDTHH:MM:SSZ`

---

## For More Information

- **Interactive API Docs:** http://localhost:8000/api/docs
- **ReDoc:** http://localhost:8000/api/redoc
- **Testing Guide:** See `API_TESTING_GUIDE.md`
- **Quick Scenarios:** See `QUICK_TEST_SCENARIOS.md`
