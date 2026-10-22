# Quick Test Scenarios - Mentor AI Platform

## Scenario 1: Complete Parent Onboarding Flow

### Step 1: Register Parent
```bash
curl -X POST http://localhost:8000/api/auth/register/simple \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email_address": "john.doe@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
  }'
```

### Step 2: Login
```bash
curl -X POST http://localhost:8000/api/auth/login/email \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "SecurePass123"
  }'
```
**Save the token and parent_id from response!**

### Step 3: Set Preferences
```bash
curl -X POST "http://localhost:8000/api/onboarding/preferences?parent_id=YOUR_PARENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "high"
  }'
```

### Step 4: Create Child Profile
```bash
curl -X POST "http://localhost:8000/api/onboarding/child?parent_id=YOUR_PARENT_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Priya Sharma",
    "age": 17,
    "grade": 12,
    "current_level": "advanced"
  }'
```
**Save the child_id from response!**

### Step 5: Select Exam
```bash
curl -X POST "http://localhost:8000/api/onboarding/exam/select?parent_id=YOUR_PARENT_ID&child_id=YOUR_CHILD_ID" \
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

### Step 6: Verify Onboarding Complete
```bash
curl -X GET "http://localhost:8000/api/onboarding/status?parent_id=YOUR_PARENT_ID"
```

Expected: All fields should be `true`

---

## Scenario 2: Student Learning Journey

### Step 1: Child Login
```bash
curl -X POST http://localhost:8000/api/auth/login/child \
  -H "Content-Type: application/json" \
  -d '{
    "username": "priya_sharma",
    "password": "StudentPass123"
  }'
```
**Save the child token!**

### Step 2: Browse Topics
```bash
curl -X GET "http://localhost:8000/api/study-center/topics?student_id=YOUR_CHILD_ID&subject=Physics" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

### Step 3: Get Learning Materials
```bash
curl -X GET "http://localhost:8000/api/study-center/materials/T01" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

### Step 4: Start Learning Session
```bash
curl -X POST http://localhost:8000/api/study-center/progress/start \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "YOUR_CHILD_ID",
    "topic_id": "T01",
    "topic_name": "Kinematics",
    "subject": "Physics"
  }'
```
**Save the session_id!**

### Step 5: Complete Session
```bash
curl -X POST http://localhost:8000/api/study-center/progress/complete \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "YOUR_CHILD_ID",
    "topic_id": "T01",
    "session_id": "YOUR_SESSION_ID"
  }'
```

### Step 6: Check Progress
```bash
curl -X GET "http://localhost:8000/api/study-center/progress/YOUR_CHILD_ID" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

---

## Scenario 3: Diagnostic Test Flow

### Step 1: Schedule Test (Parent)
```bash
curl -X POST http://localhost:8000/api/diagnostic-test/schedule \
  -H "Authorization: Bearer YOUR_PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": "YOUR_CHILD_ID",
    "exam_type": "JEE_MAIN",
    "scheduled_date": "2025-01-20T09:00:00Z",
    "test_id": "test_'$(date +%s)'"
  }'
```
**Save the test_id!**

### Step 2: Start Test (Child)
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/YOUR_TEST_ID/start" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "YOUR_CHILD_ID"
  }'
```

### Step 3: Check Test Status
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/YOUR_TEST_ID/status" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

### Step 4: Submit Test
```bash
curl -X POST "http://localhost:8000/api/diagnostic-test/YOUR_TEST_ID/submit" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "test_id": "YOUR_TEST_ID",
    "student_id": "YOUR_CHILD_ID",
    "answers": {
      "1": "A",
      "2": "B",
      "3": "C",
      "4": "D",
      "5": "A"
    },
    "time_taken": 10800,
    "submission_time": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"
  }'
```

### Step 5: Get Results
```bash
curl -X GET "http://localhost:8000/api/diagnostic-test/YOUR_TEST_ID/results" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

---

## Scenario 4: AI-Powered Search

### Vector Search for Topics
```bash
curl -X POST http://localhost:8000/api/vector-search/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain electromagnetic induction and Faraday'\''s law",
    "top_k": 5,
    "filters": {
      "exam": "JEE_MAIN",
      "subject": "Physics"
    },
    "include_metadata": true,
    "min_similarity_score": 0.5
  }'
```

### Generate Practice Questions
```bash
curl -X POST http://localhost:8000/api/rag/generate-questions \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Thermodynamics",
    "exam_type": "JEE_MAIN",
    "difficulty": "medium",
    "num_questions": 5,
    "include_explanations": true,
    "question_type": "single_correct",
    "use_cache": true
  }'
```

---

## Scenario 5: Schedule Management

### Generate Study Schedule
```bash
curl -X POST http://localhost:8000/api/schedule/generate \
  -H "Authorization: Bearer YOUR_PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "YOUR_CHILD_ID",
    "analytics_id": "analytics_from_test",
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15",
    "daily_study_hours": 5.0
  }'
```
**Save the schedule_id!**

### Get Today's Tasks
```bash
curl -X GET "http://localhost:8000/api/schedule/progress/today?schedule_id=YOUR_SCHEDULE_ID" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

### Update Progress
```bash
curl -X POST http://localhost:8000/api/schedule/progress/update \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_id": "YOUR_SCHEDULE_ID",
    "day_number": 1,
    "completion_percentage": 100,
    "topics_completed": ["Kinematics", "Newton'\''s Laws"],
    "hours_studied": 5.0,
    "notes": "Completed all topics for today"
  }'
```

### Get Progress Summary
```bash
curl -X GET "http://localhost:8000/api/schedule/progress/YOUR_SCHEDULE_ID" \
  -H "Authorization: Bearer YOUR_CHILD_TOKEN"
```

---

## Scenario 6: Payment Flow

### Step 1: View Plans
```bash
curl -X GET http://localhost:8000/api/payment/plans
```

### Step 2: Create Payment Order
```bash
curl -X POST http://localhost:8000/api/payment/create-order \
  -H "Authorization: Bearer YOUR_PARENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parent_id": "YOUR_PARENT_ID",
    "plan_id": "premium_monthly"
  }'
```
**Save order_id for payment gateway!**

### Step 3: Check Subscription Status
```bash
curl -X GET "http://localhost:8000/api/payment/subscription/YOUR_PARENT_ID" \
  -H "Authorization: Bearer YOUR_PARENT_TOKEN"
```

### Step 4: Get Transaction History
```bash
curl -X GET "http://localhost:8000/api/payment/transactions/YOUR_PARENT_ID" \
  -H "Authorization: Bearer YOUR_PARENT_TOKEN"
```

---

## Testing Tips

### 1. Save Variables
Create a file `test_vars.sh`:
```bash
export BASE_URL="http://localhost:8000"
export PARENT_TOKEN="your_token_here"
export CHILD_TOKEN="your_child_token_here"
export PARENT_ID="your_parent_id"
export CHILD_ID="your_child_id"
export TEST_ID="your_test_id"
export SCHEDULE_ID="your_schedule_id"
```

Then source it:
```bash
source test_vars.sh
```

### 2. Use Variables in Requests
```bash
curl -X GET "$BASE_URL/api/auth/me" \
  -H "Authorization: Bearer $PARENT_TOKEN"
```

### 3. Pretty Print JSON
```bash
curl ... | python3 -m json.tool
```

### 4. Save Response to File
```bash
curl ... > response.json
```

### 5. Check Server Logs
```bash
tail -f server.log
```

---

## Common Issues & Solutions

### Issue: 401 Unauthorized
**Solution:** Token expired, login again to get new token

### Issue: 403 Forbidden
**Solution:** Using wrong user ID or accessing resources you don't own

### Issue: 422 Validation Error
**Solution:** Check request body format matches examples

### Issue: 500 Internal Server Error
**Solution:** Check server logs: `tail -f server.log`

### Issue: Connection Refused
**Solution:** Server not running, start with `./start-dev.sh`

---

## Automated Testing

Run all tests:
```bash
python3 run_endpoint_tests.py
```

Run specific test:
```bash
python3 -m pytest tests/test_auth.py -v
```

---

## Next Steps

1. Complete Scenario 1 to set up a test account
2. Try Scenario 2 to test learning features
3. Test Scenario 3 for diagnostic tests
4. Explore AI features in Scenario 4
5. Test schedule management in Scenario 5
6. Try payment flow in Scenario 6

For detailed API documentation, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
