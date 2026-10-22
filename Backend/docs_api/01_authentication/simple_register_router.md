# Simple Register Router Testing Documentation

## Overview

The simple register router provides a simplified registration endpoint that creates user accounts directly without requiring email verification. This is useful for testing and development scenarios where immediate account creation is needed.

## Endpoint

### POST /register/simple

Register a new user without email verification.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/register/simple" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email_address": "john@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/register/simple`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "name": "John Doe",
    "email_address": "john@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "name": "John Doe",
    "email_address": "john@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
}
```

**Invalid Request Examples:**
```json
// Password mismatch
{
    "name": "John Doe",
    "email_address": "john@example.com",
    "password": "SecurePass123",
    "repeat_password": "DifferentPass123",
    "mobile_number": "+919876543210"
}

// Invalid email format
{
    "name": "John Doe",
    "email_address": "invalid-email",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
}

// Missing required fields
{
    "name": "John Doe",
    "email_address": "john@example.com",
    "mobile_number": "+919876543210"
}

// Short password
{
    "name": "John Doe",
    "email_address": "john@example.com",
    "password": "short",
    "repeat_password": "short",
    "mobile_number": "+919876543210"
}
```

#### Expected Output

**Success Response (201):**
```json
{
    "parent_id": "simple_user_abc123",
    "email": "john@example.com",
    "phone": "+919876543210",
    "verification_required": false,
    "message": "Registration successful. Welcome to Mentor AI!"
}
```

#### Error Scenarios

**400 Bad Request - Password Mismatch:**
```json
{
    "detail": "Passwords do not match"
}
```

**400 Bad Request - Email Already Exists:**
```json
{
    "detail": "Email already exists. Please use a different email or try logging in."
}
```

**400 Bad Request - Invalid Email:**
```json
{
    "detail": "Invalid email format"
}
```

**400 Bad Request - Validation Error:**
```json
{
    "detail": "Name must be at least 2 characters long"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Registration failed. Please try again later."
}
```

#### Troubleshooting

1. **Password Validation:**
   - Password must be at least 8 characters long
   - Both password fields must match exactly
   - No additional password strength requirements (unlike auth_router)

2. **Email Validation:**
   - Must be a valid email format (user@domain.com)
   - Cannot be already registered in the system
   - Case-sensitive check for duplicates

3. **Name Validation:**
   - Must be between 2-100 characters
   - Can include spaces, letters, and special characters
   - Cannot be empty or only whitespace

4. **Mobile Number:**
   - Defaults to "+91XXXXXXXXXX" format if not provided
   - No strict validation in this endpoint (unlike phone registration)
   - Used for display purposes only

5. **Firebase Connection Issues:**
   - Verify Firebase credentials in `.env` file
   - Check if Firebase project is properly configured
   - Ensure Firebase Auth is enabled

#### Testing Workflow

1. **First Registration:**
   ```bash
   curl -X POST "http://localhost:8000/register/simple" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User",
       "email_address": "test1@example.com",
       "password": "TestPass123",
       "repeat_password": "TestPass123",
       "mobile_number": "+919876543210"
     }'
   ```

2. **Duplicate Email Test:**
   ```bash
   curl -X POST "http://localhost:8000/register/simple" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Another User",
       "email_address": "test1@example.com",
       "password": "TestPass123",
       "repeat_password": "TestPass123",
       "mobile_number": "+919876543211"
     }'
   ```

3. **Password Mismatch Test:**
   ```bash
   curl -X POST "http://localhost:8000/register/simple" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User 2",
       "email_address": "test2@example.com",
       "password": "TestPass123",
       "repeat_password": "DifferentPass123",
       "mobile_number": "+919876543212"
     }'
   ```

#### AI Troubleshooting Prompt

```
I'm testing the Mentor AI simple register router endpoint POST /register/simple and encountering the following error:

[Insert error message here]

My request payload is:
```json
{
    "name": "John Doe",
    "email_address": "john@example.com",
    "password": "SecurePass123",
    "repeat_password": "SecurePass123",
    "mobile_number": "+919876543210"
}
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Firebase project: [Your Firebase project ID]
- Email is already registered: [Yes/No]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the simple registration flow in services/simple_register_service.py
2. Checking if the request format matches the SimpleRegisterRequest model
3. Verifying Firebase Auth configuration for user creation
4. Providing specific steps to fix the issue

Context: This endpoint provides simplified user registration without email verification for the Mentor AI EdTech Platform. It creates users directly in Firebase Auth and Firestore.
```

## Key Differences from Auth Router

| Feature | Auth Router | Simple Register Router |
|---------|-------------|---------------------|
| Email Verification | Required | Not required |
| Password Validation | Letters + numbers required | Minimum 8 characters only |
| Phone Validation | Strict +91 format required | Optional, defaults to format |
| Account Creation | Firebase Auth + Firestore | Firebase Auth + Firestore |
| Response | verification_required: true | verification_required: false |
| Use Case | Production registration | Testing/development registration |

## Testing Tips

1. **Use Unique Emails:** Each test should use a different email address
2. **Test Validation:** Try various invalid inputs to test error handling
3. **Check Firestore:** Verify user creation in Firebase Console
4. **Test Login:** After registration, test login with the created credentials
5. **Password Testing:** Test with mismatched passwords to ensure validation works