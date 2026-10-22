# Test Management Router API Documentation

## Overview

The Test Management Router provides endpoints for test lifecycle management including starting tests, submitting answers, calculating scores, and retrieving results. It handles the complete test workflow from initiation to completion with comprehensive scoring and analytics.

## Base URL
```
/api/diagnostic-test
```

## Endpoints

### 1. Start Test

**Endpoint:** `POST /api/diagnostic-test/{test_id}/start`

**Description:** Start a diagnostic test by recording the start time and updating status.

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
  "success": true,
  "message": "Test started successfully",
  "data": {
    "test_id": "test_123",
    "start_time": "2024-01-15T10:30:00Z",
    "duration_minutes": 180
  }
}
```

#### Requirements
- Test must exist and belong to the student
- Test status must be 'pending'
- Student must be authenticated

#### Error Scenarios
- **400 Bad Request:** Test already started or invalid status
- **403 Forbidden:** Student ID does not match authenticated user
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to start test

#### Troubleshooting
- Verify test_id exists and belongs to student
- Check test status is 'pending' before starting
- Ensure student_id matches authenticated user
- Confirm test hasn't been started previously

---

### 2. Submit Test

**Endpoint:** `POST /api/diagnostic-test/{test_id}/submit`

**Description:** Submit test answers and calculate results.

**Authentication:** Required (JWT token)

#### Request Example
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/test_123/submit" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "test_123",
    "student_id": "student_123",
    "answers": {
      "1": "A",
      "2": "B",
      "3": "C",
      "4": "D",
      "5": "A"
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
    },
    "Chemistry": {
      "section_name": "Section - Chemistry",
      "score": 92,
      "total_marks": 120,
      "correct": 24,
      "incorrect": 4,
      "unattempted": 2
    },
    "Mathematics": {
      "section_name": "Section - Mathematics",
      "score": 92,
      "total_marks": 120,
      "correct": 23,
      "incorrect": 3,
      "unattempted": 4
    }
  },
  "correct_count": 72,
  "incorrect_count": 10,
  "unattempted_count": 8
}
```

#### Requirements
- Test must exist and belong to the student
- Test status must be 'in_progress'
- All answers must be in valid format

#### Scoring Rules
- Correct answer: +4 marks (typically)
- Incorrect answer: -1 mark (negative marking)
- Unattempted: 0 marks

#### Error Scenarios
- **400 Bad Request:** Invalid submission or test status
- **403 Forbidden:** Student ID does not match authenticated user
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to submit test

#### Troubleshooting
- Verify test is in 'in_progress' status
- Check answers format (question numbers as strings)
- Ensure test_id in URL matches test_id in body
- Validate student_id matches authenticated user

---

### 3. Get Test Results

**Endpoint:** `GET /api/diagnostic-test/{test_id}/results`

**Description:** Retrieve calculated test results.

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
    },
    "Chemistry": {
      "section_name": "Section - Chemistry",
      "score": 92,
      "total_marks": 120,
      "correct": 24,
      "incorrect": 4,
      "unattempted": 2
    },
    "Mathematics": {
      "section_name": "Section - Mathematics",
      "score": 92,
      "total_marks": 120,
      "correct": 23,
      "incorrect": 3,
      "unattempted": 4
    }
  },
  "correct_count": 72,
  "incorrect_count": 10,
  "unattempted_count": 8
}
```

#### Requirements
- Test must exist and belong to the student
- Test status must be 'completed'
- Results must have been calculated and stored

#### Error Scenarios
- **400 Bad Request:** Test not completed
- **403 Forbidden:** Access denied
- **404 Not Found:** Results not found
- **500 Internal Server Error:** Failed to retrieve results

#### Troubleshooting
- Ensure test has been submitted
- Check test status is 'completed'
- Verify student owns the test
- Wait a few seconds after submission for results to process

---

### 4. Get Test Status

**Endpoint:** `GET /api/diagnostic-test/{test_id}/status`

**Description:** Get current test status and timing information.

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
  "status": "in_progress",
  "start_time": "2024-01-15T10:30:00Z",
  "time_remaining": 5400,
  "duration_minutes": 180
}
```

#### Status Values
- `pending`: Test generated but not started
- `in_progress`: Test is currently being taken
- `completed`: Test has been submitted and scored
- `expired`: Test time limit exceeded
- `cancelled`: Test was cancelled

#### Use Cases
- Display test timer
- Check if test can be started/submitted
- Monitor test progress

#### Error Scenarios
- **403 Forbidden:** Access denied
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to get status

---

### 5. Update Test Status (Admin Only)

**Endpoint:** `PATCH /api/diagnostic-test/{test_id}/status`

**Description:** Update test status. Admin only endpoint.

**Authentication:** Required (Admin JWT token)

#### Request Example
```bash
curl -X PATCH "http://localhost:8000/api/diagnostic-test/test_123/status" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "expired"
  }'
```

#### Expected Response (200 OK)
```json
{
  "success": true,
  "message": "Test status updated successfully",
  "data": {
    "test_id": "test_123",
    "old_status": "in_progress",
    "new_status": "expired"
  }
}
```

#### Valid Status Transitions
- Any status → 'cancelled'
- 'in_progress' → 'expired' (if time exceeded)
- 'completed' → 'pending' (admin reset for retake)

#### Use Cases
- Reset test to allow retake
- Mark test as expired
- Cancel test

#### Error Scenarios
- **400 Bad Request:** Invalid status
- **403 Forbidden:** Admin privileges required
- **404 Not Found:** Test not found
- **500 Internal Server Error:** Failed to update status

---

## Testing Workflows

### Complete Test Lifecycle

1. **Start Test**
   ```bash
   curl -X POST "/api/diagnostic-test/{test_id}/start" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123"}'
   ```

2. **Check Status During Test**
   ```bash
   curl -X GET "/api/diagnostic-test/{test_id}/status" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Submit Test**
   ```bash
   curl -X POST "/api/diagnostic-test/{test_id}/submit" \
     -H "Authorization: Bearer TOKEN" \
     -d '{"student_id": "student_123", "answers": {...}}'
   ```

4. **Get Results**
   ```bash
   curl -X GET "/api/diagnostic-test/{test_id}/results" \
     -H "Authorization: Bearer TOKEN"
   ```

### Admin Test Management

1. **Update Test Status**
   ```bash
   curl -X PATCH "/api/diagnostic-test/{test_id}/status" \
     -H "Authorization: Bearer ADMIN_TOKEN" \
     -d '{"status": "cancelled"}'
   ```

---

## Score Calculation Details

### JEE Main Scoring Pattern
- **Physics**: 30 questions × 4 marks = 120 marks
- **Chemistry**: 30 questions × 4 marks = 120 marks
- **Mathematics**: 30 questions × 4 marks = 120 marks
- **Total**: 90 questions = 360 marks

### Scoring Rules
- Correct answer: +4 marks
- Incorrect answer: -1 mark (25% negative marking)
- Unattempted: 0 marks

### Section Score Calculation
For each section:
```
section_score = (correct_count × 4) - (incorrect_count × 1)
percentage = (section_score / section_total_marks) × 100
```

### Overall Percentage
```
total_percentage = (total_score / total_marks) × 100
```

---

## Common Issues and Solutions

### 1. Test Cannot Be Started
**Problem:** Getting 400 error when starting test
**Solution:** Check if test status is 'pending' and student owns the test

### 2. Submission Failed
**Problem:** Getting 400 error when submitting answers
**Solution:** 
- Verify test is in 'in_progress' status
- Check answers format (question numbers as strings)
- Ensure test_id matches in URL and body

### 3. Results Not Available
**Problem:** Getting 400 error when fetching results
**Solution:** 
- Ensure test has been submitted
- Wait a few seconds for processing
- Check test status is 'completed'

### 4. Access Denied
**Problem:** Getting 403 errors
**Solution:** 
- Verify student_id matches authenticated user
- Check JWT token is valid
- For admin endpoints, ensure admin privileges

---

## AI Troubleshooting Prompt

Copy and paste this prompt into ChatGPT or Claude when encountering issues:

```
I'm testing the Test Management Router in Mentor AI platform and encountering an issue.

**Endpoint:** [ENDPOINT_URL]
**HTTP Method:** [METHOD]
**Request Payload:** [REQUEST_JSON]
**Error Response:** [ERROR_RESPONSE]
**Expected Behavior:** [DESCRIPTION]

**Context:**
- The Test Management Router handles test lifecycle (start, submit, results)
- Tests follow JEE Main pattern: 90 questions, 360 marks, -1 negative marking
- Test states: pending → in_progress → completed
- Authentication uses JWT tokens with student_id
- Admin endpoints require admin privileges

**Question:** Can you help me debug this issue by:
1. Analyzing the error response and request format
2. Checking if the test state transition is valid
3. Identifying common causes for this error
4. Suggesting specific fixes or debugging steps

**Additional Information:**
- Test ID: [TEST_ID]
- Current Test Status: [CURRENT_STATUS]
- Student ID: [STUDENT_ID]
- [Add any relevant logs or observations]
```

---

## Related Models and Services

### Models
- `models.diagnostic_test_models.TestSubmission`
- `models.diagnostic_test_models.TestResults`
- `models.diagnostic_test_models.SectionScore`
- `models.diagnostic_test_models.TestStatus`

### Services
- `services.test_scoring_service.TestScoringService`
- `services.diagnostic_test_service.DiagnosticTestService`

### Authentication
- `middleware.testing_auth.get_current_user_testing`
- Admin verification for status updates

---

## Performance Considerations

1. **Score Calculation:** Results are calculated once during submission
2. **Status Checks:** Lightweight endpoint for frequent polling
3. **Result Retrieval:** Cached for 24 hours after calculation
4. **Concurrent Tests:** Multiple tests can run simultaneously
5. **Database Operations:** Atomic transactions for state updates

---

## Security Notes

1. **Access Control:** Students can only access their own tests
2. **State Validation:** Strict state transition validation
3. **Answer Integrity:** Answers are validated before scoring
4. **Admin Separation:** Admin endpoints have separate authentication
5. **Audit Trail:** All state changes are logged

---

## Testing Best Practices

1. **State Testing:** Test all valid and invalid state transitions
2. **Timing Validation:** Test with expired time limits
3. **Answer Validation:** Test with various answer formats
4. **Permission Testing:** Test access control with different users
5. **Error Recovery:** Test error handling and recovery scenarios