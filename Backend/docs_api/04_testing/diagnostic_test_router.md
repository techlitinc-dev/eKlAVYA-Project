# Diagnostic Test Router API Documentation

## Overview

The Diagnostic Test Router provides endpoints for generating, managing, and retrieving diagnostic tests in the Mentor AI platform. It supports both synchronous and asynchronous test generation, test lifecycle management, and comprehensive result analytics.

## Base URL
```
/api/diagnostic-test
```

## Endpoints

### 1. Generate Diagnostic Test (Synchronous)

**Endpoint:** `POST /api/diagnostic-test/generate`

**Description:** Generate a diagnostic test synchronously. This endpoint may take 2-3 minutes to complete as it generates all questions and assembles the test.

**Rate Limit:** 1 test per student per hour

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/generate" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "JEE_MAIN",
    "student_id": "student_123",
    "num_questions": 90,
    "difficulty": "medium",
    "topics": ["Physics", "Chemistry", "Mathematics"]
  }'
```

#### Expected Response (201 Created)
```json
{
  "test_id": "test_mock_123",
  "status": "success",
  "questions_generated": 90,
  "total_questions": 90,
  "generation_time": 2.5,
  "errors": [],
  "warnings": []
}
```

#### Error Scenarios
- **400 Bad Request:** Invalid exam type or missing required fields
- **403 Forbidden:** Student ID does not match authenticated user
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Test generation failed

#### Troubleshooting
- Ensure exam_type is one of: JEE_MAIN, JEE_ADVANCED, NEET
- Verify student_id matches the authenticated user's ID
- Check if you've exceeded the rate limit (1 test per hour)
- For long generation times, consider using the async endpoint

---

### 2. Generate Diagnostic Test (Asynchronous)

**Endpoint:** `POST /api/diagnostic-test/generate-async`

**Description:** Start asynchronous test generation. Returns immediately with a job ID that can be used to check generation progress.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/generate-async" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "JEE_MAIN",
    "student_id": "student_123",
    "num_questions": 90,
    "difficulty": "medium"
  }'
```

#### Expected Response (202 Accepted)
```json
{
  "job_id": "job_uuid_456",
  "status": "queued",
  "message": "Test generation started"
}
```

#### Testing Workflow
1. Submit async generation request
2. Poll the status endpoint every 5-10 seconds
3. Retrieve test when status is "completed"

#### Error Scenarios
- **400 Bad Request:** Invalid request parameters
- **403 Forbidden:** Student ID mismatch
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Failed to start generation

---

### 3. Check Generation Status

**Endpoint:** `GET /api/diagnostic-test/generation/status/{job_id}`

**Description:** Check the status of an asynchronous test generation job.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/generation/status/job_uuid_456" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "job_id": "job_uuid_456",
  "status": "completed",
  "progress": 100,
  "current_step": "Test generated successfully",
  "test_id": "test_mock_123",
  "error": null
}
```

#### Status Values
- `queued`: Job is waiting to start
- `in_progress`: Generation is running
- `completed`: Test generated successfully
- `failed`: Generation failed

#### Error Scenarios
- **404 Not Found:** Job not found or access denied

---

### 4. Get Complete Test

**Endpoint:** `GET /api/diagnostic-test/{test_id}`

**Description:** Retrieve complete diagnostic test with all questions.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/test_mock_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "test_id": "test_mock_123",
  "exam_type": "JEE_MAIN",
  "student_id": "student_123",
  "questions": [
    {
      "question_id": "q_1",
      "question": "What is the derivative of sin(x)?",
      "options": {
        "A": "cos(x)",
        "B": "-cos(x)",
        "C": "sin(x)",
        "D": "-sin(x)"
      },
      "correct_answer": "A",
      "explanation": "The derivative of sin(x) is cos(x)",
      "difficulty": "easy",
      "topic": "Calculus",
      "subject": "Mathematics"
    }
  ],
  "metadata": {
    "total_questions": 90,
    "duration_minutes": 180,
    "total_marks": 360
  }
}
```

#### Error Scenarios
- **403 Forbidden:** Access denied to this test
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to retrieve test

---

### 5. Get Test Metadata

**Endpoint:** `GET /api/diagnostic-test/{test_id}/metadata`

**Description:** Retrieve test metadata without questions (faster than full test retrieval).

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/test_mock_123/metadata" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "test_id": "test_mock_123",
  "exam_type": "JEE_MAIN",
  "student_id": "student_123",
  "generation_date": "2024-01-15T10:00:00Z",
  "start_date": null,
  "submission_date": null,
  "status": "pending",
  "metadata": {
    "total_questions": 90,
    "duration_minutes": 180,
    "total_marks": 360
  }
}
```

#### Error Scenarios
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to retrieve metadata

---

### 6. Get Student Tests

**Endpoint:** `GET /api/diagnostic-test/student/{student_id}`

**Description:** Retrieve all tests for a student with optional filtering.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/student/student_123?status=completed&limit=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Query Parameters
- `status`: Filter by test status (pending, in_progress, completed, expired)
- `limit`: Maximum number of tests to return (default: 10, max: 100)
- `offset`: Number of tests to skip for pagination (default: 0)

#### Expected Response (200 OK)
```json
[
  {
    "test_id": "test_1",
    "exam_type": "JEE_MAIN",
    "student_id": "student_123",
    "generation_date": "2024-01-15T10:00:00Z",
    "start_date": "2024-01-15T10:30:00Z",
    "submission_date": "2024-01-15T13:45:00Z",
    "status": "completed"
  },
  {
    "test_id": "test_2",
    "exam_type": "JEE_MAIN",
    "student_id": "student_123",
    "generation_date": "2024-01-10T09:00:00Z",
    "start_date": null,
    "submission_date": null,
    "status": "scheduled"
  }
]
```

#### Error Scenarios
- **403 Forbidden:** Can only access your own tests
- **500 Internal Server Error:** Failed to retrieve tests

---

### 7. Delete Test

**Endpoint:** `DELETE /api/diagnostic-test/{test_id}`

**Description:** Delete a diagnostic test. Can only delete tests that have not been submitted.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X DELETE "http://localhost:8000/api/diagnostic-test/test_mock_123" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Test deleted successfully",
  "data": {
    "test_id": "test_mock_123"
  }
}
```

#### Error Scenarios
- **400 Bad Request:** Cannot delete completed test
- **403 Forbidden:** Access denied
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to delete test

---

### 8. Schedule Diagnostic Test

**Endpoint:** `POST /api/diagnostic-test/schedule`

**Description:** Schedule a diagnostic test for a specific date and time.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/schedule" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "child_123",
    "exam_type": "JEE_MAIN",
    "scheduled_date": "2024-02-01T09:00:00Z",
    "test_id": "test_456"
  }'
```

#### Expected Response (201 Created)
```json
{
  "test_id": "test_456",
  "scheduled_date": "2024-02-01T09:00:00Z",
  "status": "scheduled",
  "message": "Diagnostic test scheduled successfully"
}
```

#### Error Scenarios
- **400 Bad Request:** Missing required fields
- **500 Internal Server Error:** Failed to schedule test

---

### 9. Get Test Status

**Endpoint:** `GET /api/diagnostic-test/{test_id}/status`

**Description:** Get the current status of a diagnostic test.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/test_123/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "test_id": "test_123",
  "status": "scheduled",
  "created_at": "2024-01-15T10:00:00Z",
  "student_id": "student_123",
  "exam_type": "JEE_MAIN"
}
```

#### Error Scenarios
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to get test status

---

### 10. Start Test

**Endpoint:** `POST /api/diagnostic-test/{test_id}/start`

**Description:** Start a diagnostic test for the student.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/test_123/start" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123"
  }'
```

#### Expected Response (200 OK)
```json
{
  "test_id": "test_123",
  "student_id": "student_123",
  "start_time": "2024-01-15T10:30:00Z",
  "status": "in_progress",
  "duration_minutes": 180,
  "total_questions": 90
}
```

#### Error Scenarios
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to start test

---

### 11. Submit Test

**Endpoint:** `POST /api/diagnostic-test/{test_id}/submit`

**Description:** Submit a completed diagnostic test with answers.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/test_123/submit" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "student_123",
    "answers": {
      "1": "A",
      "2": "B",
      "3": "C",
      "4": "D"
    },
    "time_taken": 7200,
    "submission_time": "2024-01-15T13:30:00Z"
  }'
```

#### Expected Response (200 OK)
```json
{
  "test_id": "test_123",
  "student_id": "student_123",
  "total_score": 65,
  "total_questions": 90,
  "percentage": 72.2,
  "submission_time": "2024-01-15T13:30:00Z",
  "status": "completed"
}
```

#### Error Scenarios
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to submit test

---

### 12. Get Test Results

**Endpoint:** `GET /api/diagnostic-test/{test_id}/results`

**Description:** Get detailed results for a completed diagnostic test.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/test_123/results" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Expected Response (200 OK)
```json
{
  "test_id": "test_123",
  "student_id": "student_123",
  "total_score": 65,
  "total_questions": 90,
  "percentage": 72.2,
  "subject_scores": {
    "Physics": 22,
    "Chemistry": 21,
    "Mathematics": 22
  },
  "completion_time": "2h 45m",
  "rank_prediction": "5000-6000",
  "recommendations": [
    "Focus on Thermodynamics in Physics",
    "Practice Organic Chemistry problems",
    "Revise Calculus concepts"
  ]
}
```

#### Error Scenarios
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to get test results

---

## Testing Workflows

### Complete Diagnostic Test Workflow

1. **Generate Test (Async)**
   ```bash
   # Start async generation
   curl -X POST "/api/diagnostic-test/generate-async" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"exam_type": "JEE_MAIN", "student_id": "student_123"}'
   
   # Poll for completion
   curl -X GET "/api/diagnostic-test/generation/status/{job_id}" \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Schedule Test**
   ```bash
   curl -X POST "/api/diagnostic-test/schedule" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"child_id": "child_123", "exam_type": "JEE_MAIN", "scheduled_date": "2024-02-01T09:00:00Z", "test_id": "test_456"}'
   ```

3. **Start Test**
   ```bash
   curl -X POST "/api/diagnostic-test/{test_id}/start" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123"}'
   ```

4. **Submit Test**
   ```bash
   curl -X POST "/api/diagnostic-test/{test_id}/submit" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123", "answers": {...}}'
   ```

5. **Get Results**
   ```bash
   curl -X GET "/api/diagnostic-test/{test_id}/results" \
     -H "Authorization: Bearer TOKEN"
   ```

---

## Common Issues and Solutions

### 1. Test Generation Timeout
**Problem:** Synchronous generation times out after 2-3 minutes
**Solution:** Use the async endpoint and poll for status

### 2. Rate Limit Exceeded
**Problem:** Getting 429 errors
**Solution:** Wait 1 hour between test generations per student

### 3. Access Denied
**Problem:** 403 errors when accessing tests
**Solution:** Ensure student_id matches authenticated user's ID

### 4. Invalid Exam Type
**Problem:** 400 errors for exam_type
**Solution:** Use valid values: JEE_MAIN, JEE_ADVANCED, NEET

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing the Diagnostic Test Router in the Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Mentor AI platform uses FastAPI with Firebase/Firestore backend
- Diagnostic tests are generated using AI (Gemini) and stored in Firestore
- Tests support JEE_MAIN, JEE_ADVANCED, and NEET exam types
- Rate limiting: 1 test per student per hour
- Authentication uses JWT tokens with student_id

**Question:** Can you help me debug this issue by:
1. Analyzing the error response
2. Checking if the request format is correct
3. Identifying common causes for this error
4. Suggesting specific fixes or debugging steps

**Additional Information:**
[Add any relevant logs, screenshots, or observations]
```

---

## Related Models and Services

### Models
- `models.diagnostic_test_models.TestGenerationRequest`
- `models.diagnostic_test_models.TestGenerationResult`
- `models.diagnostic_test_models.DiagnosticTest`
- `models.diagnostic_test_models.TestMetadata`

### Services
- `services.diagnostic_test_service.DiagnosticTestService`
- `services.test_scoring_service.TestScoringService`

### Authentication
- `middleware.testing_auth.get_current_user_testing`

---

## Performance Considerations

1. **Test Generation:** Use async endpoint for better UX
2. **Large Responses:** Use `/metadata` endpoint when possible
3. **Pagination:** Use limit/offset for student tests
4. **Caching:** Results are cached for 24 hours
5. **Rate Limits:** Respect 1 test/hour per student

---

## Security Notes

1. **Access Control:** Students can only access their own tests
2. **Token Validation:** All endpoints require valid JWT
3. **Input Validation:** All inputs are validated before processing
4. **Rate Limiting:** Enforced to prevent abuse
5. **Data Encryption:** All data is encrypted in transit and at rest