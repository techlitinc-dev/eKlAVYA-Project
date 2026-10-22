# Child Router Testing Documentation

## Overview

The child router provides endpoints for managing child profiles with a one-child-per-parent restriction. It supports CRUD operations (Create, Read, Update, Delete) for child profiles used in JEE/NEET preparation tracking.

## Endpoints

### POST /api/onboarding/child

Create a child profile for a parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/child" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul123",
    "password": "SecurePass123"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/onboarding/child`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul123",
    "password": "SecurePass123"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul123",
    "password": "SecurePass123"
}
```

**Invalid Request Examples:**
```json
// Age too young
{
    "name": "Young Student",
    "age": 13,
    "grade": 8,
    "current_level": "beginner",
    "username": "young123",
    "password": "SecurePass123"
}

// Age too old
{
    "name": "Adult Student",
    "age": 20,
    "grade": 12,
    "current_level": "advanced",
    "username": "adult123",
    "password": "SecurePass123"
}

// Invalid grade
{
    "name": "Student",
    "age": 16,
    "grade": 13,
    "current_level": "intermediate",
    "username": "student123",
    "password": "SecurePass123"
}

// Invalid current_level
{
    "name": "Student",
    "age": 16,
    "grade": 11,
    "current_level": "expert",
    "username": "student123",
    "password": "SecurePass123"
}

// Missing required fields
{
    "name": "Rahul Sharma",
    "age": 16
}

// Invalid username format
{
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul@#$",
    "password": "SecurePass123"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "child_id": "child_abc123def456",
    "parent_id": "parent_xyz789",
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul123",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Error Scenarios

**400 Bad Request - Parent Already Has Child:**
```json
{
    "detail": "Parent already has a child profile. Only one child profile is allowed per parent."
}
```

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Age must be between 14 and 19 years. Got: 13"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to create child profile. Please try again later."
}
```

#### Troubleshooting

1. **One-Child Restriction:**
   - Each parent can only have ONE child profile
   - To create a new child, delete the existing one first
   - Use DELETE endpoint to remove current child profile

2. **Age Validation:**
   - Must be between 14 and 19 years (inclusive)
   - Age must be appropriate for JEE/NEET preparation
   - Check age corresponds to grade level

3. **Grade Validation:**
   - Must be between 9 and 12 (inclusive)
   - Grade should match the child's current academic level
   - Higher grades typically indicate more advanced study

4. **Current Level Validation:**
   - Must be one of: "beginner", "intermediate", "advanced"
   - Level should reflect child's current knowledge
   - Can be updated later as child progresses

5. **Username Validation:**
   - Must be 3-30 characters long
   - Can contain letters, numbers, underscores, @, and .
   - No special characters other than @, _, and .
   - Must be unique across the system

6. **Password Validation:**
   - Must be 8-50 characters long
   - Must contain at least one letter and one number
   - Used for child login (separate from parent credentials)

7. **Authentication Required:**
   - Parent must be authenticated with valid access token
   - Use `parent_id` query parameter for testing
   - Token must have proper Authorization header format

#### Testing Workflow

1. **First Child Creation:**
   ```bash
   curl -X POST "http://localhost:8000/api/onboarding/child" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
     -d '{
       "name": "Test Child",
       "age": 16,
       "grade": 11,
       "current_level": "intermediate",
       "username": "testchild123",
       "password": "TestPass123"
     }'
   ```

2. **Attempt Duplicate Creation:**
   ```bash
   curl -X POST "http://localhost:8000/api/onboarding/child" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
     -d '{
       "name": "Second Child",
       "age": 15,
       "grade": 10,
       "current_level": "beginner",
       "username": "secondchild123",
       "password": "TestPass123"
     }'
   ```

3. **Validation Testing:**
   ```bash
   curl -X POST "http://localhost:8000/api/onboarding/child" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
     -d '{
       "name": "Invalid Age",
       "age": 13,
       "grade": 8,
       "current_level": "beginner",
       "username": "invalid123",
       "password": "TestPass123"
     }'
   ```

---

### GET /api/onboarding/child

Retrieve child profile for an authenticated parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/child?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/onboarding/child`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `parent_id`: `PARENT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123def456",
    "parent_id": "parent_xyz789",
    "name": "Rahul Sharma",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "rahul123",
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
}
```

#### Error Scenarios

**404 Not Found - No Child Profile:**
```json
{
    "detail": "Child profile not found for this parent"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to retrieve child profile. Please try again later."
}
```

#### Troubleshooting

1. **Parent ID Required:**
   - Must provide `parent_id` query parameter
   - For testing, can use the parent's actual ID
   - In production, this comes from authentication token

2. **Child Must Exist:**
   - Parent must have created a child profile first
   - Use POST endpoint to create child profile before retrieving

---

### PUT /api/onboarding/child/{child_id}

Update child profile information.

#### Testing Steps

1. **Using curl:**
```bash
curl -X PUT "http://localhost:8000/api/onboarding/child/child_abc123def456" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "grade": 12,
    "current_level": "advanced"
  }'
```

2. **Using Postman:**
- Method: PUT
- URL: `{{base_url}}/api/onboarding/child/{{child_id}}`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `child_abc123def456`
- Body (raw JSON):
```json
{
    "grade": 12,
    "current_level": "advanced"
}
```

#### Request Examples

**Valid Partial Update:**
```json
{
    "name": "Rahul Sharma Updated",
    "age": 17,
    "grade": 12,
    "current_level": "advanced"
}
```

**Invalid Request Examples:**
```json
// Invalid age
{
    "age": 20
}

// Invalid grade
{
    "grade": 13
}

// Invalid current_level
{
    "current_level": "expert"
}

// Empty update
{
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123def456",
    "parent_id": "parent_xyz789",
    "name": "Rahul Sharma Updated",
    "age": 17,
    "grade": 12,
    "current_level": "advanced",
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
}
```

#### Error Scenarios

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

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Grade must be between 9 and 12. Got: 13"
}
```

#### Troubleshooting

1. **Child ID Required:**
   - Must provide valid `child_id` in URL path
   - Child must exist in the system
   - Child must belong to the authenticated parent

2. **Partial Updates Supported:**
   - Only include fields that need to be updated
   - Omitted fields remain unchanged
   - All validation rules apply (age, grade, level)

3. **Ownership Verification:**
   - Service verifies child belongs to authenticated parent
   - Cannot update child profiles belonging to other parents
   - Prevents unauthorized access to child data

---

### DELETE /api/onboarding/child/{child_id}

Delete a child profile.

#### Testing Steps

1. **Using curl:**
```bash
curl -X DELETE "http://localhost:8000/api/onboarding/child/child_abc123def456" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: DELETE
- URL: `{{base_url}}/api/onboarding/child/{{child_id}}`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Path Variables:
  - `child_id`: `child_abc123def456`

#### Expected Output

**Success Response (200):**
```json
{
    "message": "Child profile deleted successfully",
    "child_id": "child_abc123def456"
}
```

#### Error Scenarios

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

1. **Permanent Action:**
   - Deletion cannot be undone
   - All associated data will be permanently deleted
   - Child login credentials will be invalidated

2. **After Deletion:**
   - Parent can create a new child profile
   - Previous child_id cannot be reused
   - All child data is permanently removed

3. **Ownership Verification:**
   - Service verifies child belongs to authenticated parent
   - Cannot delete child profiles belonging to other parents
   - Prevents unauthorized deletion of child data

## Complete CRUD Testing Workflow

### 1. Create Child Profile
```bash
# Step 1: Create initial child profile
curl -X POST "http://localhost:8000/api/onboarding/child" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "name": "Test Child",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "username": "testchild123",
    "password": "TestPass123"
  }'
```

### 2. Retrieve Child Profile
```bash
# Step 2: Verify child profile creation
curl -X GET "http://localhost:8000/api/onboarding/child?parent_id=PARENT_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

### 3. Update Child Profile
```bash
# Step 3: Update child profile (partial)
curl -X PUT "http://localhost:8000/api/onboarding/child/CHILD_ID_FROM_STEP1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "current_level": "advanced"
  }'
```

### 4. Verify Update
```bash
# Step 4: Verify child profile update
curl -X GET "http://localhost:8000/api/onboarding/child?parent_id=PARENT_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

### 5. Delete Child Profile
```bash
# Step 5: Delete child profile
curl -X DELETE "http://localhost:8000/api/onboarding/child/CHILD_ID_FROM_STEP1" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

### 6. Verify Deletion
```bash
# Step 6: Verify child profile deletion
curl -X GET "http://localhost:8000/api/onboarding/child?parent_id=PARENT_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

### 7. Create New Child Profile
```bash
# Step 7: Create new child profile (after deletion)
curl -X POST "http://localhost:8000/api/onboarding/child" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "name": "New Test Child",
    "age": 15,
    "grade": 10,
    "current_level": "beginner",
    "username": "newtest123",
    "password": "NewTestPass123"
  }'
```

## Common Issues Across All Endpoints

### Authentication Requirements
- All endpoints require parent authentication (except during testing)
- Use `Authorization: Bearer <token>` header
- For testing, can use `parent_id` query parameter
- Parent must be logged in and have valid session

### One-Child Restriction Enforcement
- Service layer enforces maximum one child per parent
- Attempting to create second child returns 400 error
- Must delete existing child before creating new one
- Prevents multiple child profiles per parent

### Ownership Verification
- All operations verify child belongs to authenticated parent
- Prevents unauthorized access to other children's data
- Uses parent_id from authentication token for verification

### Data Validation
- Age: 14-19 years for JEE/NEET preparation
- Grade: 9-12 for corresponding academic levels
- Current Level: beginner, intermediate, or advanced
- Username: 3-30 characters, alphanumeric with @, _, .
- Password: 8-50 characters with letters and numbers

### Firestore Integration
- Child profiles stored in `children` collection
- Uses child_id as document ID
- Includes parent_id for ownership tracking
- Timestamps for created_at and updated_at fields

## AI Troubleshooting Prompt

```
I'm testing the Mentor AI child router endpoint [INSERT_ENDPOINT] and encountering the following error:

[Insert error message here]

My request payload is:
```json
[Insert request payload here]
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Endpoint: [POST /api/onboarding/child, GET /api/onboarding/child, PUT /api/onboarding/child/{child_id}, or DELETE /api/onboarding/child/{child_id}]
- Authentication token: [Valid/Invalid/Missing]
- Parent ID: [If applicable]
- Child ID: [If applicable]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the child profile flow in services/child_service.py
2. Checking if the request format matches the appropriate model in models/child_models.py
3. Verifying the one-child-per-parent restriction logic
4. Checking the ownership verification process
5. Verifying the Firestore database operations
6. Providing specific steps to fix the issue

Context: This endpoint manages child profiles for the Mentor AI EdTech Platform, enforcing one-child-per-parent restrictions with proper ownership verification and data validation.