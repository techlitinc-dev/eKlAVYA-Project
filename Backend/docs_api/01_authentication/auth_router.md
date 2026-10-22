# Auth Router Testing Documentation

## Overview

The auth router provides endpoints for parent registration using three different methods: email/password, phone number, and Google OAuth. All endpoints create parent accounts in Firebase Auth and Firestore.

## Endpoints

### POST /register/parent/email

Register a new parent account using email and password.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/register/parent/email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "SecurePass123",
    "language": "en"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/register/parent/email`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "email": "parent@example.com",
    "password": "SecurePass123",
    "language": "en"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "email": "parent@example.com",
    "password": "SecurePass123",
    "language": "en"
}
```

**Invalid Request Examples:**
```json
// Missing password
{
    "email": "parent@example.com",
    "language": "en"
}

// Invalid email format
{
    "email": "invalid-email",
    "password": "SecurePass123",
    "language": "en"
}

// Weak password (no numbers)
{
    "email": "parent@example.com",
    "password": "weakpassword",
    "language": "en"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "parent_id": "abc123xyz456",
    "email": "parent@example.com",
    "phone": null,
    "verification_required": true,
    "message": "Registration successful. Please verify your email to continue."
}
```

#### Error Scenarios

**400 Bad Request - Duplicate Email:**
```json
{
    "detail": "Email already exists. Please use a different email or try logging in."
}
```

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Password must contain at least one letter and one number"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Registration failed. Please try again later."
}
```

#### Troubleshooting

1. **Duplicate Email Error:**
   - Check if the email is already registered in Firebase Auth
   - Use a different email address or try the login endpoint

2. **Password Validation Error:**
   - Ensure password is at least 8 characters
   - Include both letters and numbers in the password
   - Example valid passwords: "SecurePass123", "Password1", "MyPass123"

3. **Firebase Connection Error:**
   - Verify Firebase credentials in `.env` file
   - Check if Firebase project is properly configured
   - Ensure Firebase Admin SDK is initialized

4. **Email Format Error:**
   - Use valid email format (e.g., user@domain.com)
   - Avoid special characters that break email validation

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI auth router endpoint POST /register/parent/email and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "email": "parent@example.com",
    "password": "SecurePass123",
    "language": "en"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the error and identifying the root cause
2. Checking if the request format is correct according to the models in models/auth_models.py
3. Verifying the Firebase Auth configuration
4. Providing specific steps to fix the issue

Context: This endpoint is part of the Mentor AI EdTech Platform's parent registration system using Firebase Auth and FastAPI.
```

---

### POST /register/parent/phone

Register a new parent account using phone number.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/register/parent/phone" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "language": "hi"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/register/parent/phone`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "phone": "+919876543210",
    "language": "hi"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "phone": "+919876543210",
    "language": "hi"
}
```

**Invalid Request Examples:**
```json
// Invalid format (missing +91)
{
    "phone": "9876543210",
    "language": "hi"
}

// Invalid format (wrong country code)
{
    "phone": "+447911123456",
    "language": "hi"
}

// Invalid Indian number (starts with 5)
{
    "phone": "+915876543210",
    "language": "hi"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "parent_id": "def456uvw789",
    "email": null,
    "phone": "+919876543210",
    "verification_required": true,
    "message": "Registration successful. You will receive an OTP for verification during login."
}
```

#### Error Scenarios

**400 Bad Request - Duplicate Phone:**
```json
{
    "detail": "Phone number already exists. Please use a different number or try logging in."
}
```

**400 Bad Request - Invalid Format:**
```json
{
    "detail": "Phone number must be in format +91XXXXXXXXXX where X is a digit. Indian mobile numbers start with 6, 7, 8, or 9 and have 10 digits total."
}
```

#### Troubleshooting

1. **Phone Format Validation:**
   - Must start with +91 country code
   - Must have exactly 10 digits after +91
   - First digit after +91 must be 6, 7, 8, or 9

2. **Duplicate Phone Error:**
   - Check if the phone number is already registered
   - Use a different phone number or try the login endpoint

3. **Firebase Phone Auth:**
   - Ensure Firebase phone authentication is enabled
   - Verify Firebase project settings for phone auth

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI auth router endpoint POST /register/parent/phone and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "phone": "+919876543210",
    "language": "hi"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the phone number format validation
2. Checking if the request matches the ParentPhoneRegisterRequest model in models/auth_models.py
3. Verifying Firebase phone authentication configuration
4. Providing specific steps to fix the issue

Context: This endpoint registers parents using Indian mobile numbers with OTP verification in the Mentor AI EdTech Platform.
```

---

### POST /register/parent/google

Register or login a parent account using Google OAuth.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/register/parent/google" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...",
    "language": "en"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/register/parent/google`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...",
    "language": "en"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhYzRlMWY2MmI4YWQxN2FkZGU0MzVmNDZhNGUyOTIzODJlNzMwN2YiLCJ0eXAiOiJKV1QifQ...",
    "language": "en"
}
```

**Invalid Request Examples:**
```json
// Empty token
{
    "id_token": "",
    "language": "en"
}

// Too short token
{
    "id_token": "short_token",
    "language": "en"
}

// Missing token
{
    "language": "en"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "parent_id": "google_ghi789rst012",
    "email": "parent@gmail.com",
    "phone": null,
    "verification_required": false,
    "message": "Registration successful. Welcome to Mentor AI!"
}
```

#### Error Scenarios

**400 Bad Request - Invalid Token:**
```json
{
    "detail": "Invalid Google ID token. Please try signing in again."
}
```

**400 Bad Request - Token Expired:**
```json
{
    "detail": "Google ID token has expired. Please sign in again."
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

3. **Firebase Google Auth:**
   - Enable Google authentication in Firebase Console
   - Configure OAuth consent screen
   - Add authorized domains for your application

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI auth router endpoint POST /register/parent/google and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...",
    "language": "en"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- Google OAuth client ID: [Your client ID]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the Google ID token validation process
2. Checking if the request matches the ParentGoogleRegisterRequest model in models/auth_models.py
3. Verifying Firebase Google authentication configuration
4. Providing steps to obtain a valid Google ID token for testing
5. Identifying any OAuth configuration issues

Context: This endpoint handles Google OAuth registration/login for the Mentor AI EdTech Platform using Firebase Auth.
```

## Common Issues Across All Endpoints

### Firebase Connection Issues
- Verify `FIREBASE_PROJECT_ID`, `FIREBASE_PRIVATE_KEY`, and `FIREBASE_CLIENT_EMAIL` in `.env`
- Check if service account has proper permissions
- Ensure Firebase project is not deleted or disabled

### Language Validation
- Supported languages: "en" (English), "hi" (Hindi), "mr" (Marathi)
- Default language is "en" if not specified
- Invalid language will cause validation error

### General Testing Tips
1. Use unique email/phone for each test to avoid duplicate errors
2. Check Firebase Console to verify created users
3. Test both success and error scenarios
4. Verify email verification is sent for email registration
5. Test with different language preferences