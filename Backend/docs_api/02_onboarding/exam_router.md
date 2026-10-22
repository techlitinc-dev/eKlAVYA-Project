# Exam Router Testing Documentation

## Overview

The exam router provides endpoints for exam selection, diagnostic test scheduling, and onboarding completion tracking. It supports JEE (Main & Advanced) and NEET exams with subject preference management and automatic diagnostic test creation.

## Endpoints

### GET /api/onboarding/exams/available

List all available competitive exams with their dates and subjects.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/exams/available"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/onboarding/exams/available`
- No authentication required (public endpoint)

#### Expected Output

**Success Response (200):**
```json
{
    "exams": [
        {
            "exam_type": "JEE_MAIN",
            "exam_name": "JEE Main",
            "available_dates": ["2025-01-15", "2025-04-15"],
            "subjects": ["Physics", "Chemistry", "Mathematics"]
        },
        {
            "exam_type": "JEE_ADVANCED",
            "exam_name": "JEE Advanced",
            "available_dates": ["2025-05-25"],
            "subjects": ["Physics", "Chemistry", "Mathematics"]
        },
        {
            "exam_type": "NEET",
            "exam_name": "NEET",
            "available_dates": ["2025-05-05"],
            "subjects": ["Physics", "Chemistry", "Biology"]
        }
    ]
}
```

#### Error Scenarios

**500 Internal Server Error:**
```json
{
    "detail": "Failed to retrieve available exams. Please try again later."
}
```

#### Troubleshooting

1. **Public Endpoint:**
   - No authentication required
   - Available for browsing exam options before registration
   - Returns static exam information from configuration

2. **Exam Types:**
   - JEE_MAIN: Joint Entrance Examination (Main)
   - JEE_ADVANCED: Joint Entrance Examination (Advanced)
   - JEE_COMBO: Combined JEE examination
   - NEET: National Eligibility cum Entrance Test

3. **Subject Requirements:**
   - JEE: Physics, Chemistry, Mathematics
   - NEET: Physics, Chemistry, Biology
   - Subjects determine diagnostic test content

4. **Date Format:**
   - Dates in YYYY-MM-DD format
   - Multiple dates available per exam type
   - Based on actual exam schedules

---

### POST /api/onboarding/exam/select

Select target exam with date and subject preferences, and automatically schedule a diagnostic test.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/exam/select" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
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

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/onboarding/exam/select`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `parent_id`: `PARENT_ID` (for testing)
  - `child_id`: `CHILD_ID` (required)
- Body (raw JSON):
```json
{
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    }
}
```

#### Request Examples

**Valid Request - JEE Main:**
```json
{
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    }
}
```

**Valid Request - NEET:**
```json
{
    "exam_type": "NEET",
    "exam_date": "2025-05-05T00:00:00Z",
    "subject_preferences": {
      "Physics": 35,
      "Chemistry": 35,
      "Biology": 30
    }
}
```

**Invalid Request Examples:**
```json
// Past exam date
{
    "exam_type": "JEE_MAIN",
    "exam_date": "2023-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    }
}

// Invalid subject preferences (don't sum to 100)
{
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 50,
      "Chemistry": 30,
      "Mathematics": 30
    }
}

// Wrong subjects for exam type
{
    "exam_type": "NEET",
    "exam_date": "2025-05-05T00:00:00Z",
    "subject_preferences": {
      "Physics": 35,
      "Chemistry": 35,
      "Mathematics": 30
    }
}

// Missing required fields
{
    "exam_type": "JEE_MAIN"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "child_id": "child_abc123",
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    },
    "days_until_exam": 104,
    "diagnostic_test_id": "test_def456",
    "created_at": "2024-01-15T10:30:00Z"
}
```

#### Error Scenarios

**400 Bad Request - Invalid Exam Date:**
```json
{
    "detail": "Exam date must be in the future. Got: 2023-04-15"
}
```

**400 Bad Request - Invalid Subject Preferences:**
```json
{
    "detail": "Subject weightages must sum to 100. Current total: 110"
}
```

**400 Bad Request - Wrong Subjects for Exam Type:**
```json
{
    "detail": "Invalid subjects for NEET. Expected: Physics, Chemistry, Biology. Got: Physics, Chemistry, Mathematics"
}
```

**404 Not Found - Child Not Found:**
```json
{
    "detail": "Child profile not found"
}
```

**403 Forbidden - Ownership Error:**
```json
{
    "detail": "Child does not belong to this parent"
}
```

#### Troubleshooting

1. **Exam Date Validation:**
   - Must be in the future (compared to current UTC time)
   - Format: ISO 8601 datetime string
   - Should be realistic for exam preparation timeline

2. **Subject Preferences:**
   - Must sum to exactly 100
   - Must match exam type requirements
   - JEE: Physics, Chemistry, Mathematics
   - NEET: Physics, Chemistry, Biology
   - All values must be non-negative integers

3. **Child Ownership:**
   - Child must exist and belong to authenticated parent
   - Use `child_id` query parameter to specify which child
   - Service verifies ownership before allowing exam selection

4. **Diagnostic Test Creation:**
   - Automatically created for tomorrow
   - Duration: 180 minutes (3 hours)
   - Total questions: 200
   - Status: "scheduled"
   - Test ID returned for reference

---

### GET /api/onboarding/exam/preferences

Get exam selection and subject preferences for a child.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/exam/preferences?child_id=CHILD_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/onboarding/exam/preferences`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `child_id`: `CHILD_ID` (required)

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123",
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-01-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    },
    "days_until_exam": 52,
    "diagnostic_test_id": "test_xyz789",
    "created_at": "2024-01-10T08:00:00Z"
}
```

#### Error Scenarios

**404 Not Found - Exam Selection Not Found:**
```json
{
    "detail": "Exam selection not found for this child"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to retrieve exam selection. Please try again later."
}
```

#### Troubleshooting

1. **Child ID Required:**
   - Must provide `child_id` query parameter
   - Child must have existing profile
   - Child must belong to authenticated parent

2. **Exam Selection Must Exist:**
   - Child must have selected an exam first
   - Use POST endpoint to create initial selection
   - Cannot retrieve preferences for child without exam selection

---

### PUT /api/onboarding/exam/preferences

Update subject preference weightages for a child's exam selection.

#### Testing Steps

1. **Using curl:**
```bash
curl -X PUT "http://localhost:8000/api/onboarding/exam/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "Physics": 45,
    "Chemistry": 25,
    "Biology": 30
  }'
```

2. **Using Postman:**
- Method: PUT
- URL: `{{base_url}}/api/onboarding/exam/preferences`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `child_id`: `CHILD_ID` (required)
  - `parent_id`: `PARENT_ID` (for testing)
- Body (raw JSON):
```json
{
    "Physics": 45,
    "Chemistry": 25,
    "Biology": 30
}
```

#### Request Examples

**Valid Update - NEET:**
```json
{
    "Physics": 45,
    "Chemistry": 25,
    "Biology": 30
}
```

**Invalid Request Examples:**
```json
// Preferences don't sum to 100
{
    "Physics": 50,
    "Chemistry": 30,
    "Biology": 30
}

// Invalid subjects for exam type
{
    "Physics": 45,
    "Chemistry": 25,
    "Mathematics": 30
}

// Empty update
{
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123",
    "exam_type": "NEET",
    "exam_date": "2025-05-05T00:00:00Z",
    "subject_preferences": {
      "Physics": 45,
      "Chemistry": 25,
      "Biology": 30
    },
    "days_until_exam": 162,
    "diagnostic_test_id": "test_xyz789",
    "created_at": "2024-01-10T08:00:00Z"
}
```

#### Error Scenarios

**400 Bad Request - Invalid Preferences:**
```json
{
    "detail": "Subject weightages must sum to 100. Current total: 110"
}
```

**400 Bad Request - Wrong Subjects:**
```json
{
    "detail": "Invalid subjects for NEET. Expected: Physics, Chemistry, Biology. Got: Physics, Chemistry, Mathematics"
}
```

**404 Not Found - Exam Selection Not Found:**
```json
{
    "detail": "Exam selection not found for this child"
}
```

**403 Forbidden - Ownership Error:**
```json
{
    "detail": "Child does not belong to this parent"
}
```

#### Troubleshooting

1. **Subject Preference Validation:**
   - Must sum to exactly 100
   - Must match exam type requirements
   - All values must be non-negative
   - Service validates against exam type

2. **Partial Updates:**
   - Only provided subjects are updated
   - Can update one or multiple subjects
   - Other subjects remain at current values

---

### GET /api/onboarding/status

Get onboarding completion status for a parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/status?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/onboarding/status`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `parent_id`: `PARENT_ID` (required)

#### Expected Output

**Success Response (200):**
```json
{
    "preferences_completed": true,
    "child_profile_completed": true,
    "exam_selected": false,
    "onboarding_complete": false
}
```

**Complete Success Response (200):**
```json
{
    "preferences_completed": true,
    "child_profile_completed": true,
    "exam_selected": true,
    "onboarding_complete": true
}
```

#### Error Scenarios

**500 Internal Server Error:**
```json
{
    "detail": "Failed to check onboarding status. Please try again later."
}
```

#### Troubleshooting

1. **Status Logic:**
   - All three steps must be true for complete onboarding
   - Each step checked independently
   - Returns boolean status for each step

2. **Step Dependencies:**
   - Preferences must exist for `preferences_completed: true`
   - Child profile must exist for `child_profile_completed: true`
   - Exam selection must exist for `exam_selected: true`
   - Order matters for user experience

3. **Authentication Required:**
   - Parent must be authenticated
   - Use `parent_id` query parameter for testing
   - Status tied to authenticated parent

## Complete Exam Selection Workflow

### 1. Get Available Exams
```bash
# Step 1: List available exams
curl -X GET "http://localhost:8000/api/onboarding/exams/available"
```

### 2. Select Exam (JEE Main)
```bash
# Step 2: Select JEE Main exam
curl -X POST "http://localhost:8000/api/onboarding/exam/select" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "exam_type": "JEE_MAIN",
    "exam_date": "2025-04-15T00:00:00Z",
    "subject_preferences": {
      "Physics": 40,
      "Chemistry": 30,
      "Mathematics": 30
    }
  }' \
  --data-urlencode "parent_id=PARENT_ID&child_id=CHILD_ID"
```

### 3. Verify Exam Selection
```bash
# Step 3: Verify exam selection
curl -X GET "http://localhost:8000/api/onboarding/exam/preferences?child_id=CHILD_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

### 4. Update Subject Preferences
```bash
# Step 4: Update subject preferences
curl -X PUT "http://localhost:8000/api/onboarding/exam/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "Physics": 45,
    "Chemistry": 25,
    "Mathematics": 30
  }' \
  --data-urlencode "child_id=CHILD_ID&parent_id=PARENT_ID"
```

### 5. Check Onboarding Status
```bash
# Step 5: Verify onboarding completion
curl -X GET "http://localhost:8000/api/onboarding/status?parent_id=PARENT_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

## Common Issues Across All Endpoints

### Authentication Requirements
- All endpoints (except available exams) require parent authentication
- Use `Authorization: Bearer <token>` header
- For testing, can use `parent_id` query parameter
- Parent must be logged in with valid session

### Exam Type Validation
- Must be one of: JEE_MAIN, JEE_ADVANCED, JEE_COMBO, or NEET
- Case-sensitive validation
- Determines subject requirements and diagnostic test content

### Subject Preference Rules
- Must sum to exactly 100
- Must match exam type requirements
- All values must be non-negative integers
- Affects study plan and content recommendations

### Diagnostic Test Creation
- Automatically scheduled for next day
- Duration: 180 minutes (3 hours)
- Total questions: 200
- Status starts as "scheduled"
- Test ID returned for reference

### Date Validation
- Must be in future (compared to current UTC time)
- ISO 8601 format required
- Affects preparation timeline calculations

### Child Ownership
- All operations verify child belongs to authenticated parent
- Prevents unauthorized access to exam data
- Uses child_id from query parameters

### Firestore Integration
- Exam selections stored in `exam_selections` collection
- Uses child_id as document identifier
- Includes parent_id for ownership tracking
- Timestamps for created_at and updated_at fields

## AI Troubleshooting Prompt

```
I'm testing the Mentor AI exam router endpoint [INSERT_ENDPOINT] and encountering the following error:

[Insert error message here]

My request payload is:
```json
[Insert request payload here]
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Endpoint: [GET /api/onboarding/exams/available, POST /api/onboarding/exam/select, GET /api/onboarding/exam/preferences, PUT /api/onboarding/exam/preferences, or GET /api/onboarding/status]
- Authentication token: [Valid/Invalid/Missing]
- Parent ID: [If applicable]
- Child ID: [If applicable]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the exam selection and diagnostic test scheduling flow in services/exam_service.py
2. Checking if the request format matches the appropriate model in models/exam_models.py
3. Verifying the exam type validation and subject preference logic
4. Checking the diagnostic test creation process
5. Verifying the onboarding status tracking logic
6. Providing specific steps to fix the issue

Context: This endpoint handles exam selection and diagnostic test scheduling for the Mentor AI EdTech Platform, supporting JEE and NEET exams with subject preference management and automatic test creation.