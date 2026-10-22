# Verification Router Testing Documentation

## Overview

The verification router provides endpoints for email and phone verification using OTP (One-Time Password) and verification codes. It supports both sending verification codes and confirming them to complete the verification process.

## Endpoints

### POST /verify/email/send

Send a verification code to parent's email address.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/verify/email/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "parent@example.com"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/verify/email/send`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "email": "parent@example.com"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "email": "parent@example.com"
}
```

**Invalid Request Examples:**
```json
// Invalid email format
{
    "email": "invalid-email"
}

// Missing email
{
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "message": "Verification email sent",
    "code": "ABC123"
}
```

**Note:** In production, the verification code is sent via email. In development mode, the code is returned in the response for testing purposes.

#### Error Scenarios

**400 Bad Request - Invalid Email:**
```json
{
    "detail": "Invalid email format"
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to send verification email. Please try again later."
}
```

#### Troubleshooting

1. **Authentication Required:**
   - This endpoint requires a valid access token
   - Use the Authorization header with Bearer token
   - Token must be from a logged-in parent

2. **Email Validation:**
   - Must be a valid email format
   - Email should be associated with a registered parent
   - Case-insensitive validation

3. **Development Mode:**
   - Verification code is returned in response for testing
   - In production, code is sent via email service
   - Code is valid for 10 minutes

---

### POST /verify/email/confirm

Confirm email address using verification code.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/verify/email/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "code": "ABC123"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/verify/email/confirm`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
```json
{
    "email": "parent@example.com",
    "code": "ABC123"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "email": "parent@example.com",
    "code": "ABC123"
}
```

**Invalid Request Examples:**
```json
// Invalid code format
{
    "email": "parent@example.com",
    "code": "123"
}

// Invalid email format
{
    "email": "invalid-email",
    "code": "ABC123"
}

// Missing fields
{
    "email": "parent@example.com"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "verified": true,
    "message": "Email verified successfully"
}
```

#### Error Scenarios

**400 Bad Request - Invalid Code:**
```json
{
    "detail": "Invalid verification code"
}
```

**400 Bad Request - Expired Code:**
```json
{
    "detail": "Verification code has expired"
}
```

**400 Bad Request - Code Already Used:**
```json
{
    "detail": "Verification code has already been used"
}
```

**404 Not Found - User Not Found:**
```json
{
    "detail": "User with email parent@example.com not found"
}
```

#### Troubleshooting

1. **Code Validation:**
   - Code must be exactly 6 alphanumeric characters
   - Case-insensitive comparison (converted to uppercase)
   - Valid for 10 minutes from generation

2. **Testing Workflow:**
   - First call `/verify/email/send` to get code
   - Use the returned code in confirmation
   - In development, code is returned in send response

3. **Common Issues:**
   - Using wrong email (must match the one used to request code)
   - Using expired code (check timestamp)
   - Using already used code

---

### POST /verify/phone/send

Send a one-time password (OTP) to parent's phone number.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/verify/phone/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+919876543210"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/verify/phone/send`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
- Body (raw JSON):
```json
{
    "phone": "+919876543210"
}
```

#### Request Examples

**Valid Request:**
```json
{
    "phone": "+919876543210"
}
```

**Invalid Request Examples:**
```json
// Invalid phone format
{
    "phone": "9876543210"
}

// Wrong country code
{
    "phone": "+447911123456"
}

// Invalid Indian number (starts with 5)
{
    "phone": "+915876543210"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "message": "OTP sent",
    "otp": "123456"
}
```

**Note:** In production, the OTP is sent via SMS. In development mode, the OTP is returned in the response for testing purposes.

#### Error Scenarios

**400 Bad Request - Invalid Phone:**
```json
{
    "detail": "Phone number must be in format +91XXXXXXXXXX where X is a digit. Indian mobile numbers start with 6, 7, 8, or 9 and have 10 digits total."
}
```

**500 Internal Server Error:**
```json
{
    "detail": "Failed to send OTP. Please try again later."
}
```

#### Troubleshooting

1. **Phone Format Validation:**
   - Must start with +91 country code
   - Must have exactly 10 digits after +91
   - First digit after +91 must be 6, 7, 8, or 9

2. **Authentication Required:**
   - This endpoint requires a valid access token
   - Use the Authorization header with Bearer token
   - Token must be from a logged-in parent

3. **Development Mode:**
   - OTP is returned in response for testing
   - In production, OTP is sent via SMS service
   - OTP is valid for 10 minutes

---

### POST /verify/phone/confirm

Confirm phone number using OTP.

#### Testing Steps

1. **Using curl:**
```bash
curl -X POST "http://localhost:8000/verify/phone/confirm" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+919876543210",
    "otp": "123456"
  }'
```

2. **Using Postman:**
- Method: POST
- URL: `{{base_url}}/verify/phone/confirm`
- Headers: 
  - `Content-Type: application/json`
  - `Authorization: Bearer {{access_token}}`
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
// Invalid OTP format
{
    "phone": "+919876543210",
    "otp": "12345"
}

// Invalid phone format
{
    "phone": "9876543210",
    "otp": "123456"
}

// Missing fields
{
    "phone": "+919876543210"
}
```

#### Expected Output

**Success Response (200):**
```json
{
    "verified": true,
    "message": "Phone verified successfully"
}
```

#### Error Scenarios

**400 Bad Request - Invalid OTP:**
```json
{
    "detail": "Invalid OTP"
}
```

**400 Bad Request - Expired OTP:**
```json
{
    "detail": "OTP has expired"
}
```

**400 Bad Request - OTP Already Used:**
```json
{
    "detail": "OTP has already been used"
}
```

**404 Not Found - User Not Found:**
```json
{
    "detail": "User with phone +919876543210 not found"
}
```

#### Troubleshooting

1. **OTP Validation:**
   - OTP must be exactly 6 numeric digits
   - Valid for 10 minutes from generation
   - Cannot be reused after successful verification

2. **Testing Workflow:**
   - First call `/verify/phone/send` to get OTP
   - Use the returned OTP in confirmation
   - In development, OTP is returned in send response

## Complete Verification Testing Workflow

### Email Verification Testing

1. **Login First:**
   ```bash
   curl -X POST "http://localhost:8000/login/email" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "parent@example.com",
       "password": "SecurePass123"
     }'
   ```

2. **Send Verification Code:**
   ```bash
   curl -X POST "http://localhost:8000/verify/email/send" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ACCESS_TOKEN_FROM_LOGIN" \
     -d '{
       "email": "parent@example.com"
     }'
   ```

3. **Confirm Verification:**
   ```bash
   curl -X POST "http://localhost:8000/verify/email/confirm" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "parent@example.com",
       "code": "CODE_FROM_RESPONSE"
     }'
   ```

### Phone Verification Testing

1. **Login First:**
   ```bash
   curl -X POST "http://localhost:8000/login/phone" \
     -H "Content-Type: application/json" \
     -d '{
       "phone": "+919876543210",
       "otp": "123456"
     }'
   ```

2. **Send OTP:**
   ```bash
   curl -X POST "http://localhost:8000/verify/phone/send" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ACCESS_TOKEN_FROM_LOGIN" \
     -d '{
       "phone": "+919876543210"
     }'
   ```

3. **Confirm OTP:**
   ```bash
   curl -X POST "http://localhost:8000/verify/phone/confirm" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer ACCESS_TOKEN_FROM_LOGIN" \
     -d '{
       "phone": "+919876543210",
       "otp": "OTP_FROM_RESPONSE"
     }'
   ```

## Common Issues Across All Endpoints

### Authentication Requirements
- `/verify/email/send` and `/verify/phone/send` require valid access tokens
- `/verify/email/confirm` and `/verify/phone/confirm` do not require tokens
- Use tokens from successful login endpoints

### Code/OTP Format
- Email codes: 6 alphanumeric characters (A-Z, 0-9)
- Phone OTPs: 6 numeric digits (0-9)
- Both are case-insensitive for email codes

### Expiration Time
- All verification codes/OTPs expire after 10 minutes
- Timestamp is set at generation time
- Expired codes cannot be used

### Single Use
- Each verification code/OTP can only be used once
- After successful verification, code is marked as used
- Used codes cannot be reused

### Development vs Production
- Development: Codes/OTPs returned in response
- Production: Codes sent via email/SMS services
- Behavior controlled by environment variables

## AI Troubleshooting Prompt

```
I'm testing the Mentor AI verification router endpoint [INSERT_ENDPOINT] and encountering the following error:

[Insert error message here]

My request payload is:
```json
[Insert request payload here]
```

The response I'm getting is:
[Insert full response here]

Environment details:
- API URL: http://localhost:8000
- Endpoint: [verify/email/send, verify/email/confirm, verify/phone/send, or verify/phone/confirm]
- Authentication token: [Valid/Invalid/Missing]
- Previous step completed: [Login/Send code]
- Using curl/Postman: [Specify which tool]

Please help me debug this issue by:
1. Analyzing the verification flow in services/verification_service.py
2. Checking if request format matches the appropriate model in models/verification_models.py
3. Verifying the authentication requirements for the endpoint
4. Checking the code/OTP generation and validation logic
5. Providing specific steps to fix the issue

Context: This endpoint handles email or phone verification for the Mentor AI EdTech Platform using OTP-based authentication with Firebase Auth and Firestore.