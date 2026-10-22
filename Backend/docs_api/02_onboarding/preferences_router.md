# Preferences Router Testing Documentation

## Overview

The preferences router provides endpoints for managing parent preference settings including language, notifications, and teaching involvement levels. It supports creating, retrieving, and updating preferences with partial updates.

## Endpoints

### POST /api/onboarding/preferences

Create preference settings for a parent account.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/api/onboarding/preferences`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
}
```

**Invalid Request Examples:**
```json
// Invalid language
{
    "language": "invalid",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
}

// Invalid teaching involvement
{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "expert"
}

// Missing all required fields (but language is required)
{
    "email_notifications": false,
    "sms_notifications": false,
    "push_notifications": false,
    "teaching_involvement": "low"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "parent_id": "parent_123abc456def",
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Error Scenarios

**400 Bad Request - Preferences Already Exist:**
```json
{
    "detail": "Preferences already exist for this parent. Use PUT endpoint to update existing preferences."
}
```

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Invalid language: 'invalid'. Must be one of: en, hi, mr"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to create preferences. Please try again later."
}
```

#### Troubleshooting

1. **Language Validation:**
   - Must be one of: "en" (English), "hi" (Hindi), "mr" (Marathi)
   - Default is "en" if not specified
   - Case-sensitive validation

2. **Teaching Involvement Levels:**
   - "high": High involvement in child's education
   - "medium": Moderate involvement
   - "low": Minimal involvement
   - Affects content recommendations and notifications

3. **Notification Settings:**
   - All notification fields default to `true`
   - Can be individually enabled/disabled
   - Affects which communication channels are used

4. **Authentication Required:**
   - Parent must be authenticated with valid access token
   - Use `parent_id` query parameter for testing
   - Preferences are tied to parent account

---

### GET /api/onboarding/preferences

Retrieve current preference settings for an authenticated parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/preferences?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/api/onboarding/preferences`
- Headers: 
  - `Authorization: Bearer {{access_token}}`
- Query Params:
  - `parent_id`: `PARENT_ID`

#### Expected Output

**Success Response (200):**
```json
{
    "parent_id": "parent_123abc456def",
    "language": "hi",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": false,
    "teaching_involvement": "high",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T14:45:00Z"
}
```

#### Error Scenarios

**404 Not Found - Preferences Not Found:**
```json
{
    "detail": "Preferences not found for this parent"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to retrieve preferences. Please try again later."
}
```

#### Troubleshooting

1. **Parent ID Required:**
   - Must provide `parent_id` query parameter
   - For testing, can use parent's actual ID
   - In production, this comes from authentication token

2. **Preferences Must Exist:**
   - Parent must have created preferences first
   - Use POST endpoint to create initial preferences
   - Cannot retrieve preferences that don't exist

---

### PUT /api/onboarding/preferences

Update one or more preference fields for an authenticated parent.

#### Testing Steps

1. **Using curl:**
```bash
curl -X PUT "http://localhost:8000/api/onboarding/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "language": "hi",
    "teaching_involvement": "high"
  }'
```

2. **Using Postman:**
- Method: PUT
- URL: `{{base_url}}/api/onboarding/preferences`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "language": "hi",
    "teaching_involvement": "high"
}
```

#### Request Examples

**Valid Partial Update:**
```json
{
    "language": "hi",
    "teaching_involvement": "high"
}
```

**Invalid Request Examples:**
```json
// Invalid language
{
    "language": "invalid",
    "teaching_involvement": "high"
}

// Invalid teaching involvement
{
    "language": "en",
    "teaching_involvement": "expert"
}

// Empty update
{
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "parent_id": "parent_123abc456def",
    "language": "hi",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": false,
    "teaching_involvement": "high",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
}
```

#### Error Scenarios

**400 Bad Request - No Fields to Update:**
```json
{
    "detail": "At least one field must be provided for update"
}
```

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Invalid teaching involvement level: 'expert'. Must be one of: high, medium, low"
}
```

**404 Not Found - Preferences Not Found:**
```json
{
    "detail": "Preferences not found for this parent"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to update preferences. Please try again later."
}
```

#### Troubleshooting

1. **Partial Updates Supported:**
   - Only include fields that need to be updated
   - Omitted fields remain unchanged
   - At least one field must be provided

2. **Field Validation:**
   - All field validation rules apply (same as POST endpoint)
   - Invalid fields will cause 400 errors
   - Valid fields will be updated while preserving others

3. **Preferences Must Exist:**
   - Can only update preferences that have been created
   - Use POST endpoint to create initial preferences
   - Cannot update non-existent preferences

## Complete Testing Workflow

### 1. Create Initial Preferences
```bash
# Step 1: Create initial preferences
curl -X POST "http://localhost:8000/api/onboarding/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "language": "en",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "teaching_involvement": "medium"
  }'
```

### 2. Retrieve Preferences
```bash
# Step 2: Verify preferences creation
curl -X GET "http://localhost:8000/api/onboarding/preferences?parent_id=PARENT_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

### 3. Update Preferences (Partial)
```bash
# Step 3: Update language only
curl -X PUT "http://localhost:8000/api/onboarding/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "language": "hi"
  }'
```

### 4. Update Preferences (Multiple Fields)
```bash
# Step 4: Update multiple fields
curl -X PUT "http://localhost:8000/api/onboarding/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN" \
  -d '{
    "language": "mr",
    "email_notifications": false,
    "teaching_involvement": "high"
  }'
```

### 5. Verify Final State
```bash
# Step 5: Verify final preferences state
curl -X GET "http://localhost:8000/api/onboarding/preferences?parent_id=PARENT_ID" \
  -H "Authorization: Bearer PARENT_ACCESS_TOKEN"
```

## Common Issues Across All Endpoints

### Authentication Requirements
- All endpoints require parent authentication
- Use `Authorization: Bearer <token>` header
- For testing, can use `parent_id` query parameter
- Parent must be logged in with valid session

### Language Support
- English: "en"
- Hindi: "hi"
- Marathi: "mr"
- Affects UI language and content localization

### Teaching Involvement Impact
- High: More detailed progress reports, frequent recommendations
- Medium: Balanced approach to notifications and content
- Low: Minimal intervention, basic progress tracking

### Notification Settings
- Email: Important updates, weekly reports, achievement alerts
- SMS: Urgent notifications, test reminders, security alerts
- Push: Daily reminders, study tips, motivational messages

### Firestore Integration
- Preferences stored in `preferences` collection
- Uses parent_id as document identifier
- Includes timestamps for created_at and updated_at
- One preference document per parent

### Validation Rules
- Language: Must be one of supported options
- Teaching Involvement: Must be high, medium, or low
- All boolean fields default to true if not specified
- String fields must not be empty or whitespace only

## AI Troubleshooting Prompt

```
I'm testing the Mentor AI preferences router endpoint [INSERT_ENDPOINT] and encountering the following error:

[Insert error message here]

My request payload is:
```json
[Insert request payload here]
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Endpoint: [POST /api/onboarding/preferences, GET /api/onboarding/preferences, or PUT /api/onboarding/preferences]
- Authentication token: [Valid/Invalid/Missing]
- Parent ID: [If applicable]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the preferences management flow in services/preferences_service.py
2. Checking if the request format matches the appropriate model in models/preferences_models.py
3. Verifying the authentication and authorization requirements
4. Checking the partial update logic for PUT endpoint
5. Verifying the Firestore database operations for preferences
6. Providing specific steps to fix the issue

Context: This endpoint manages parent preferences for the Mentor AI EdTech Platform, including language, notification settings, and teaching involvement levels with proper validation and partial update support.