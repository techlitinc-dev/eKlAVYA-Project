# Login Router Testing Documentation

## Overview

The login router provides endpoints for authentication, session management, and user profile retrieval. It supports multiple authentication methods including email/password, phone/OTP, Google OAuth, and child login with username/password.

## Endpoints

### POST /login/email

Authenticate parent using email and password.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/login/email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "SecurePass123"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/login/email`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "email": "parent@example.com",
    "password": "SecurePass123"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "email": "parent@example.com",
    "password": "SecurePass123"
}
```

**Invalid Request Examples:**
```json
// Invalid email format
{
    "email": "invalid-email",
    "password": "SecurePass123"
}

// Missing password
{
    "email": "parent@example.com"
}

// Unregistered email
{
    "email": "nonexistent@example.com",
    "password": "SecurePass123"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "parent_id": "parent_123abc",
    "email": "parent@example.com",
    "phone": null,
    "expires_in": 86400
}
```

#### Error Scenarios

**401 Unauthorized - Invalid Credentials:**
```json
{
    "detail": "Invalid email or password"
}
```

**404 Not Found - User Not Found:**
```json
{
    "detail": "Parent with email nonexistent@example.com not found"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Login failed. Please try again later."
}
```

#### Token Usage

After successful login, use the access token in subsequent requests:

```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Troubleshooting

1. **Invalid Credentials:**
   - Verify the email is registered in the system
   - Check if the password is correct
   - Ensure the account is not disabled

2. **User Not Found:**
   - Register the user first using `/register/parent/email`
   - Check if the email was entered correctly

3. **Firebase Connection Issues:**
   - Verify Firebase credentials in `.env` file
   - Check if Firebase Auth is properly configured

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint POST /login/email and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "email": "parent@example.com",
    "password": "SecurePass123"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- User is already registered: [Yes/No]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the authentication flow in services/login_service.py
2. Checking if the request format matches the EmailLoginRequest model in models/login_models.py
3. Verifying Firebase Auth configuration
4. Providing specific steps to fix the issue

Context: This endpoint handles email/password authentication for parents in the Mentor AI EdTech Platform using Firebase Auth and JWT tokens.
```

---

### POST /login/phone

Authenticate parent using phone number and OTP.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/login/phone" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "otp": "123456"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/login/phone`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "phone": "+919876543210",
    "otp": "123456"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "phone": "+919876543210",
    "otp": "123456"
}
```

**Invalid Request Examples:**
```json
// Invalid phone format
{
    "phone": "9876543210",
    "otp": "123456"
}

// Invalid OTP format
{
    "phone": "+919876543210",
    "otp": "12345"
}

// Unregistered phone
{
    "phone": "+919999999999",
    "otp": "123456"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "parent_id": "parent_def456",
    "email": null,
    "phone": "+919876543210",
    "expires_in": 86400
}
```

#### Error Scenarios

**401 Unauthorized - Invalid OTP:**
```json
{
    "detail": "Invalid or expired OTP"
}
```

**404 Not Found - User Not Found:**
```json
{
    "detail": "Parent with phone +919999999999 not found"
}
```

#### Troubleshooting

1. **OTP Issues:**
   - For testing, OTP might be optional or set to a default value
   - Check if OTP has expired (typically 10 minutes)
   - Verify OTP format is exactly 6 digits

2. **Phone Number Issues:**
   - Ensure phone is registered in the system
   - Verify phone format: +91 followed by 10 digits
   - Check if first digit after +91 is 6-9

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint POST /login/phone and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "phone": "+919876543210",
    "otp": "123456"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- Phone is already registered: [Yes/No]
- OTP source: [SMS/Testing mode]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the phone authentication flow in services/login_service.py
2. Checking if the request matches the PhoneLoginRequest model in models/login_models.py
3. Verifying OTP generation and validation process
4. Providing specific steps to fix the issue

Context: This endpoint handles phone/OTP authentication for parents in the Mentor AI EdTech Platform using Firebase Auth and SMS verification.
```

---

### POST /login/google

Authenticate parent using Google OAuth.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/login/google" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY..."
}'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/login/google`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY..."
}
```

#### Request Examples

**Valid Request:**
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhYzRlMWY2MmI4YWQxN2FkZGU0MzVmNDZhNGUyOTIzODJlNzMwN2YiLCJ0eXAiOiJKV1QifQ..."
}
```

**Invalid Request Examples:**
```json
// Empty token
{
    "id_token": ""
}

// Invalid token format
{
    "id_token": "invalid_token"
}

// Expired token
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...[expired]"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "parent_id": "google_user_ghi789",
    "email": "parent@gmail.com",
    "phone": null,
    "expires_in": 86400
}
```

#### Error Scenarios

**401 Unauthorized - Invalid Token:**
```json
{
    "detail": "Invalid Google ID token"
}
```

#### Troubleshooting

1. **Getting Google ID Token:**
   - Use Google Sign-In JavaScript library in frontend
   - For testing, use Google OAuth 2.0 Playground
   - Token must be a valid Firebase-compatible Google ID token

2. **Token Validation:**
   - Ensure token is not expired (usually 1 hour expiry)
   - Token must be properly formatted JWT
   - Firebase project must have Google provider enabled

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint POST /login/google and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY..."
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- Google OAuth client ID: [Your client ID]
- Token source: [Google Sign-In/OAuth Playground]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the Google OAuth authentication flow in services/login_service.py
2. Checking if the request matches the GoogleLoginRequest model in models/login_models.py
3. Verifying Firebase Google authentication configuration
4. Providing steps to obtain a valid Google ID token for testing
5. Identifying any OAuth configuration issues

Context: This endpoint handles Google OAuth authentication for the Mentor AI EdTech Platform using Firebase Auth.
```

---

### POST /token/refresh

Refresh an expired access token using a valid refresh token.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/token/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/token/refresh`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Request Examples

**Valid Request:**
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwYXJlbnRfMTIzYWJjIiwiZXhwIjoxNjM..."
}
```

**Invalid Request Examples:**
```json
// Empty refresh token
{
    "refresh_token": ""
}

// Invalid refresh token
{
    "refresh_token": "invalid_token"
}

// Expired refresh token
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.[expired]"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400
}
```

#### Error Scenarios

**401 Unauthorized - Invalid Token:**
```json
{
    "detail": "Invalid or expired refresh token"
}
```

#### Troubleshooting

1. **Refresh Token Issues:**
   - Ensure refresh token is valid and not expired (30 days)
   - Check if the session was revoked (logout invalidates refresh tokens)
   - Verify the refresh token format

2. **Token Rotation:**
   - Both access and refresh tokens are rotated for security
   - Old tokens are invalidated after refresh
   - Always use the latest refresh token for subsequent refreshes

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint POST /token/refresh and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Original login method: [email/phone/google]
- Time since original login: [hours/days]
- User has logged out: [Yes/No]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the token refresh flow in services/login_service.py
2. Checking if the request matches the TokenRefreshRequest model in models/login_models.py
3. Verifying the refresh token validation process
4. Providing specific steps to fix the issue

Context: This endpoint handles JWT token refresh for the Mentor AI EdTech Platform, allowing users to maintain sessions without re-authentication.
```

---

### POST /logout

Logout and revoke the current session.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/logout`
- Headers: `Authorization: Bearer {{access_token}}`

#### Request Examples

**Valid Request:**
```bash
# With valid access token
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Invalid Request Examples:**
```bash
# Missing authorization header
curl -X POST "http://localhost:8000/logout"

# Invalid token format
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: InvalidToken"

# Expired token
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer expired_token_here"
```

#### Expected Output

**Success Response (200):**
```json
{
    "message": "Logout successful"
}
```

#### Error Scenarios

**401 Unauthorized - Missing Token:**
```json
{
    "detail": "Authorization header required"
}
```

**401 Unauthorized - Invalid Token:**
```json
{
    "detail": "Invalid authorization header format. Expected: Bearer <token>"
}
```

#### Troubleshooting

1. **Authorization Header Issues:**
   - Ensure the header is properly formatted: `Bearer <token>`
   - Check if the token is valid and not expired
   - Verify the token was obtained from a successful login

2. **Session Revocation:**
   - After logout, the access token is immediately invalidated
   - The refresh token is also revoked
   - Any subsequent API calls with the old tokens will fail

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint POST /logout and encountering the following error:

[Insert error message here]

My request is:
```bash
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Token source: [from email/phone/google login]
- Time since login: [minutes/hours]
- User has already logged out: [Yes/No]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the logout flow in services/login_service.py
2. Checking the token extraction and validation process
3. Verifying the session revocation mechanism
4. Providing specific steps to fix the issue

Context: This endpoint handles user logout and session revocation for the Mentor AI EdTech Platform.
```

---

### GET /me

Get the authenticated parent's profile information.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/me`
- Headers: `Authorization: Bearer {{access_token}}`

#### Request Examples

**Valid Request:**
```bash
# With valid access token
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Expected Output

**Success Response (200):**
```json
{
    "parent_id": "parent_123abc",
    "email": "parent@example.com",
    "phone": null,
    "language": "en",
    "role": "parent",
    "email_verified": true,
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
}
```

#### Error Scenarios

**401 Unauthorized - Missing Token:**
```json
{
    "detail": "Authorization header required"
}
```

**401 Unauthorized - Expired Token:**
```json
{
    "detail": "Token has expired. Please login again."
}
```

**404 Not Found - Profile Not Found:**
```json
{
    "detail": "Parent profile not found"
}
```

#### Troubleshooting

1. **Token Issues:**
   - Ensure the access token is valid and not expired (24 hours)
   - Check if the token is properly formatted in the Authorization header
   - Verify the token was obtained from a successful login

2. **Profile Issues:**
   - Check if the parent profile exists in Firestore
   - Verify the parent_id in the token matches a document in the parents collection

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint GET /me and encountering the following error:

[Insert error message here]

My request is:
```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Token source: [from email/phone/google login]
- Time since login: [minutes/hours]
- User exists in Firestore: [Yes/No]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the token verification process in services/token_service.py
2. Checking the parent profile retrieval from Firestore
3. Verifying the JWT payload structure
4. Providing specific steps to fix the issue

Context: This endpoint retrieves the authenticated parent's profile information for the Mentor AI EdTech Platform.
```

---

### POST /login/child

Authenticate child/student using username and password.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/login/child" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "rahul123",
    "password": "SecurePass123"
}'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/login/child`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "username": "rahul123",
    "password": "SecurePass123"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "username": "rahul123",
    "password": "SecurePass123"
}
```

**Invalid Request Examples:**
```json
// Invalid username format
{
    "username": "rahul@#$",
    "password": "SecurePass123"
}

// Weak password
{
    "username": "rahul123",
    "password": "weak"
}

// Non-existent user
{
    "username": "nonexistent123",
    "password": "SecurePass123"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "parent_id": "parent_abc123",
    "student_id": "child_def456",
    "child_id": "child_def456",
    "username": "rahul123",
    "name": "Rahul Sharma",
    "email": "rahul123@student.local",
    "is_student": true,
    "expires_in": 86400,
    "message": "Child login successful"
}
```

#### Error Scenarios

**401 Unauthorized - Invalid Credentials:**
```json
{
    "detail": "Invalid username or password"
}
```

**404 Not Found - Child Not Found:**
```json
{
    "detail": "Child with username nonexistent123 not found"
}
```

#### Troubleshooting

1. **Child Profile Issues:**
   - Ensure the child profile is created by parent first
   - Check if the username and password are set correctly
   - Verify the child account is active

2. **Username/Password Validation:**
   - Username must be 3-30 characters, alphanumeric with @, _, .
   - Password must be at least 8 characters with letters and numbers
   - Check for typos in credentials

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI login router endpoint POST /login/child and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "username": "rahul123",
    "password": "SecurePass123"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Child profile created by parent: [Yes/No]
- Parent ID: [If known]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the child authentication flow in services/login_service.py
2. Checking if the request matches the ChildLoginRequest model in models/login_models.py
3. Verifying the child profile exists in Firestore
4. Providing specific steps to fix the issue

Context: This endpoint handles child/student authentication for the Mentor AI EdTech Platform using username/password credentials set by parents.
```

---

### POST /token/refresh/child

Refresh an expired child access token using a valid child refresh token.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/token/refresh/child" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/token/refresh/child`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400
}
```

#### Error Scenarios

**401 Unauthorized - Invalid Token:**
```json
{
    "detail": "Invalid or expired refresh token"
}
```

---

### POST /logout/child

Logout child and revoke the current session.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/logout/child" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/logout/child`
- Headers: `Authorization: Bearer {{child_access_token}}`

#### Expected Output

**Success Response (200):**
```json
{
    "message": "Child logout successful"
}
```

---

### GET /me/child

Get the authenticated child's profile information.

#### Testing Steps

1. **Using curl:**
```bash
curl -X GET "http://localhost:8000/me/child" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

2. **Using Postman:**
- Method: GET
- URL: `{{base_url}}/me/child`
- Headers: `Authorization: Bearer {{child_access_token}}`

#### Expected Output

**Success Response (200):**
```json
{
    "child_id": "child_abc123",
    "parent_id": "parent_xyz789",
    "name": "Rahul Sharma",
    "username": "rahul123",
    "age": 16,
    "grade": 11,
    "current_level": "intermediate",
    "created_at": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-15T10:30:00Z"
}
```

#### Error Scenarios

**401 Unauthorized - Not a Student Token:**
```json
{
    "detail": "Invalid token: not a student token"
}
```

## Common Issues Across All Endpoints

### Token Management
- Access tokens expire after 24 hours
- Refresh tokens expire after 30 days
- Always use the latest refresh token for subsequent refreshes
- Logout invalidates both access and refresh tokens

### Authorization Header Format
- Must be exactly: `Authorization: Bearer <token>`
- No extra spaces or characters
- Token must be valid JWT format

### Firebase Connection
- Verify all Firebase credentials in `.env`
- Check Firebase project configuration
- Ensure proper service account permissions

### Testing Workflow
1. Register a user (if needed)
2. Login to get tokens
3. Use access token for API calls
4. Refresh token when expired
5. Logout when done