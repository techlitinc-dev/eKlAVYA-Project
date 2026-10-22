# Mentor AI API Endpoints Testing Guide

## Overview

This comprehensive guide covers all API endpoints for the Mentor AI EdTech Platform, organized by functional areas for easy testing and reference. Each section includes detailed testing instructions, request/response examples, error scenarios, and troubleshooting guidance.

## Table of Contents

1. [Authentication](#authentication)
2. [Registration](#registration)
3. [Simple Registration](#simple-registration)
4. [Verification](#verification)
5. [Login](#login)
6. [Onboarding - Preferences](#onboarding---preferences)
7. [Onboarding - Child Profile](#onboarding---child-profile)
8. [Onboarding - Exam Selection](#onboarding---exam-selection)
9. [Parent Dashboard](#parent-dashboard)
10. [Student Dashboard](#student-dashboard)
11. [Diagnostic Tests](#diagnostic-tests)
12. [Test Management](#test-management)
13. [Schedule](#schedule)
14. [Study Center](#study-center)
15. [Gamification](#gamification)
16. [Analytics](#analytics)
17. [Syllabus Coverage](#syllabus-coverage)
18. [Vector Search - Embeddings](#vector-search---embeddings)
19. [Vector Search](#vector-search)
20. [RAG](#rag)
21. [AI Features](#ai-features)
22. [Payment](#payment)
23. [Health](#health)

## Authentication

### Overview

Authentication endpoints handle parent registration using multiple methods: email/password, phone number, and Google OAuth. These endpoints create user accounts in Firebase Auth and Firestore.

### POST /register/parent/email

Register a new parent account using email and password.

**Request:**
```bash
curl -X POST "http://localhost:8000/register/parent/email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "SecurePass123",
    "language": "en"
  }'
```

**Response (201):**
```json
{
    "parent_id": "abc123xyz456",
    "email": "parent@example.com",
    "phone": null,
    "verification_required": true,
    "message": "Registration successful. Please verify your email to continue."
}
```

**Common Errors:**
- 400: Email already exists
- 400: Password validation failed
- 500: Firebase connection error

### POST /register/parent/phone

Register a new parent account using phone number.

**Request:**
```bash
curl -X POST "http://localhost:8000/register/parent/phone" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "language": "hi"
  }'
```

**Response (201):**
```json
{
    "parent_id": "def456uvw789",
    "email": null,
    "phone": "+919876543210",
    "verification_required": true,
    "message": "Registration successful. You will receive an OTP for verification during login."
}
```

**Common Errors:**
- 400: Phone number already exists
- 400: Invalid phone format
- 500: Firebase connection error

### POST /register/parent/google

Register or login a parent account using Google OAuth.

**Request:**
```bash
curl -X POST "http://localhost:8000/register/parent/google" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY...",
    "language": "en"
  }'
```

**Response (201):**
```json
{
    "parent_id": "google_ghi789rst012",
    "email": "parent@gmail.com",
    "phone": null,
    "verification_required": false,
    "message": "Registration successful. Welcome to Mentor AI!"
}
```

**Common Errors:**
- 400: Invalid Google ID token
- 400: Token expired
- 500: Firebase connection error

## Registration

### Overview

Registration endpoints provide simplified user account creation without requiring email verification, useful for testing and development scenarios.

### POST /register/simple

Register a new user without email verification.

**Request:**
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

**Response (201):**
```json
{
    "parent_id": "simple_user_abc123",
    "email": "john@example.com",
    "phone": "+919876543210",
    "verification_required": false,
    "message": "Registration successful. Welcome to Mentor AI!"
}
```

**Common Errors:**
- 400: Passwords do not match
- 400: Email already exists
- 400: Invalid email format
- 400: Validation error (name too short)
- 500: Registration failed

## Verification

### Overview

Verification endpoints handle email and phone verification using OTP (One-Time Password) and verification codes.

### POST /verify/email/send

Send a verification code to parent's email address.

**Request:**
```bash
curl -X POST "http://localhost:8000/verify/email/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "email": "parent@example.com"
  }'
```

**Response (200):**
```json
{
    "message": "Verification email sent",
    "code": "ABC123"
}
```

**Common Errors:**
- 400: Invalid email format
- 401: Authorization required
- 500: Failed to send email

### POST /verify/email/confirm

Confirm email address using verification code.

**Request:**
```bash
curl -X POST "http://localhost:8000/verify/email/confirm" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "code": "ABC123"
  }'
```

**Response (200):**
```json
{
    "verified": true,
    "message": "Email verified successfully"
}
```

**Common Errors:**
- 400: Invalid verification code
- 400: Code expired
- 400: Code already used
- 404: User not found

### POST /verify/phone/send

Send a one-time password (OTP) to parent's phone number.

**Request:**
```bash
curl -X POST "http://localhost:8000/verify/phone/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+919876543210"
  }'
```

**Response (200):**
```json
{
    "message": "OTP sent",
    "otp": "123456"
}
```

**Common Errors:**
- 400: Invalid phone format
- 401: Authorization required
- 500: Failed to send OTP

### POST /verify/phone/confirm

Confirm phone number using OTP.

**Request:**
```bash
curl -X POST "http://localhost:8000/verify/phone/confirm" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "phone": "+919876543210",
    "otp": "123456"
  }'
```

**Response (200):**
```json
{
    "verified": true,
    "message": "Phone verified successfully"
}
```

**Common Errors:**
- 400: Invalid OTP
- 400: OTP expired
- 400: OTP already used
- 404: User not found

## Login

### Overview

Login endpoints provide authentication, session management, and user profile retrieval. They support multiple authentication methods including email/password, phone/OTP, Google OAuth, and child login.

### POST /login/email

Authenticate parent using email and password.

**Request:**
```bash
curl -X POST "http://localhost:8000/login/email" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "parent@example.com",
    "password": "SecurePass123"
  }'
```

**Response (200):**
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

**Common Errors:**
- 401: Invalid email or password
- 404: User not found
- 500: Login failed

### POST /login/phone

Authenticate parent using phone number and OTP.

**Request:**
```bash
curl -X POST "http://localhost:8000/login/phone" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "otp": "123456"
  }'
```

**Response (200):**
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

**Common Errors:**
- 401: Invalid or expired OTP
- 404: User not found

### POST /login/google

Authenticate parent using Google OAuth.

**Request:**
```bash
curl -X POST "http://localhost:8000/login/google" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhY..."
  }'
```

**Response (200):**
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

**Common Errors:**
- 401: Invalid Google ID token

### POST /token/refresh

Refresh an expired access token using a valid refresh token.

**Request:**
```bash
curl -X POST "http://localhost:8000/token/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400
}
```

**Common Errors:**
- 401: Invalid or expired refresh token

### POST /logout

Logout and revoke current session.

**Request:**
```bash
curl -X POST "http://localhost:8000/logout" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200):**
```json
{
    "message": "Logout successful"
}
```

**Common Errors:**
- 401: Authorization header required
- 401: Invalid authorization header format

### GET /me

Get authenticated parent's profile information.

**Request:**
```bash
curl -X GET "http://localhost:8000/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200):**
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

**Common Errors:**
- 401: Authorization header required
- 401: Token has expired
- 404: Profile not found

### POST /login/child

Authenticate child/student using username and password.

**Request:**
```bash
curl -X POST "http://localhost:8000/login/child" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "rahul123",
    "password": "SecurePass123"
  }'
```

**Response (200):**
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

**Common Errors:**
- 401: Invalid username or password
- 404: Child not found

### POST /token/refresh/child

Refresh an expired child access token using a valid child refresh token.

**Request:**
```bash
curl -X POST "http://localhost:8000/token/refresh/child" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Response (200):**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 86400
}
```

**Common Errors:**
- 401: Invalid or expired refresh token

### POST /logout/child

Logout child and revoke current session.

**Request:**
```bash
curl -X POST "http://localhost:8000/logout/child" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200):**
```json
{
    "message": "Child logout successful"
}
```

### GET /me/child

Get authenticated child's profile information.

**Request:**
```bash
curl -X GET "http://localhost:8000/me/child" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Response (200):**
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

**Common Errors:**
- 401: Invalid token: not a student token

## Onboarding - Preferences

### Overview

Preferences endpoints manage parent preference settings including language, notifications, and teaching involvement levels.

### POST /api/onboarding/preferences

Create preference settings for a parent account.

**Request:**
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

**Response (201):**
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

**Common Errors:**
- 400: Preferences already exist
- 400: Invalid language
- 500: Failed to create preferences

### GET /api/onboarding/preferences

Retrieve current preference settings for an authenticated parent.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/preferences?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
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

**Common Errors:**
- 404: Preferences not found
- 500: Failed to retrieve preferences

### PUT /api/onboarding/preferences

Update one or more preference fields for an authenticated parent.

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/onboarding/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "language": "hi",
    "teaching_involvement": "high"
  }'
```

**Response (200):**
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

**Common Errors:**
- 400: No fields to update
- 400: Invalid teaching involvement level
- 404: Preferences not found
- 500: Failed to update preferences

## Onboarding - Child Profile

### Overview

Child profile endpoints manage student profiles with CRUD operations, enforcing one-child-per-parent restriction.

### POST /api/onboarding/child

Create child profile for a parent.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/child" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "parent_id": "parent_123abc",
    "name": "Student Name",
    "age": 16,
    "grade": "11",
    "current_level": "intermediate"
  }'
```

**Response (201):**
```json
{
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "name": "Student Name",
    "age": 16,
    "grade": "11",
    "current_level": "intermediate",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Parent already has a child
- 400: Invalid age or grade
- 403: Ownership verification failed
- 500: Failed to create child profile

### GET /api/onboarding/child

Get child profile information.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/child?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "name": "Student Name",
    "age": 16,
    "grade": "11",
    "current_level": "intermediate",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 500: Failed to retrieve child profile

### PUT /api/onboarding/child/{child_id}

Update child profile information.

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/onboarding/child/child_def456" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "name": "Updated Student Name",
    "age": 17,
    "grade": "12"
  }'
```

**Response (200):**
```json
{
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "name": "Updated Student Name",
    "age": 17,
    "grade": "12",
    "current_level": "intermediate",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 400: Invalid age or grade
- 500: Failed to update child profile

### DELETE /api/onboarding/child/{child_id}

Delete child profile.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/onboarding/child/child_def456" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "message": "Child profile deleted successfully"
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 500: Failed to delete child profile

## Onboarding - Exam Selection

### Overview

Exam selection endpoints manage exam preferences, diagnostic test scheduling, and onboarding status tracking.

### GET /api/onboarding/exams/available

List available exams for selection.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/exams/available" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "exams": [
        {
            "exam_type": "JEE_MAIN",
            "name": "JEE Main",
            "description": "Joint Entrance Examination (Main)",
            "subjects": ["Physics", "Chemistry", "Mathematics"],
            "exam_date": "2024-04-06"
        },
        {
            "exam_type": "JEE_ADVANCED",
            "name": "JEE Advanced",
            "description": "Joint Entrance Examination (Advanced)",
            "subjects": ["Physics", "Chemistry", "Mathematics"],
            "exam_date": "2024-05-26"
        },
        {
            "exam_type": "NEET",
            "name": "NEET UG",
            "description": "National Eligibility cum Entrance Test",
            "subjects": ["Physics", "Chemistry", "Biology"],
            "exam_date": "2024-05-05"
        }
    ]
}
```

**Common Errors:**
- 401: Authorization required
- 500: Failed to retrieve exams

### POST /api/onboarding/exam/select

Select exam and schedule diagnostic test.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/onboarding/exam/select" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "parent_id": "parent_123abc",
    "exam_type": "JEE_MAIN",
    "exam_date": "2024-04-06",
    "subject_preferences": {
        "Physics": 40,
        "Chemistry": 35,
        "Mathematics": 25
    }
  }'
```

**Response (201):**
```json
{
    "exam_selection_id": "exam_sel_789",
    "parent_id": "parent_123abc",
    "exam_type": "JEE_MAIN",
    "exam_date": "2024-04-06",
    "subject_preferences": {
        "Physics": 40,
        "Chemistry": 35,
        "Mathematics": 25
    },
    "diagnostic_test_id": "diag_test_456",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Subject preferences must sum to 100
- 400: Invalid exam type
- 400: Past exam date
- 403: Ownership verification failed
- 500: Failed to select exam

### GET /api/onboarding/exam/preferences

Get exam selection preferences.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/exam/preferences?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "exam_selection_id": "exam_sel_789",
    "parent_id": "parent_123abc",
    "exam_type": "JEE_MAIN",
    "exam_date": "2024-04-06",
    "subject_preferences": {
        "Physics": 40,
        "Chemistry": 35,
        "Mathematics": 25
    },
    "diagnostic_test_id": "diag_test_456",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Exam preferences not found
- 403: Ownership verification failed
- 500: Failed to retrieve preferences

### PUT /api/onboarding/exam/preferences

Update subject preferences.

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/onboarding/exam/preferences" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "parent_id": "parent_123abc",
    "subject_preferences": {
        "Physics": 45,
        "Chemistry": 30,
        "Mathematics": 25
    }
  }'
```

**Response (200):**
```json
{
    "exam_selection_id": "exam_sel_789",
    "parent_id": "parent_123abc",
    "exam_type": "JEE_MAIN",
    "exam_date": "2024-04-06",
    "subject_preferences": {
        "Physics": 45,
        "Chemistry": 30,
        "Mathematics": 25
    },
    "diagnostic_test_id": "diag_test_456",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
}
```

**Common Errors:**
- 400: Subject preferences must sum to 100
- 404: Exam preferences not found
- 403: Ownership verification failed
- 500: Failed to update preferences

### GET /api/onboarding/status

Get onboarding completion status.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/onboarding/status?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "parent_id": "parent_123abc",
    "preferences_completed": true,
    "child_profile_created": true,
    "exam_selected": true,
    "diagnostic_scheduled": true,
    "onboarding_complete": true,
    "completion_percentage": 100
}
```

**Common Errors:**
- 403: Ownership verification failed
- 500: Failed to retrieve status

## Parent Dashboard

### Overview

Parent dashboard endpoints provide comprehensive child progress monitoring, goal management, and reporting features.

### GET /api/parent/dashboard/{child_id}

Get child dashboard information.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/parent/dashboard/child_def456" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "name": "Student Name",
    "age": 16,
    "grade": "11",
    "current_level": "intermediate",
    "overall_progress": 65,
    "study_streak": 7,
    "last_active": "2024-01-15T10:30:00Z",
    "subject_wise_progress": {
        "Physics": 70,
        "Chemistry": 60,
        "Mathematics": 65
    },
    "recent_activities": [
        {
            "type": "practice_completed",
            "subject": "Physics",
            "topic": "Mechanics",
            "score": 85,
            "timestamp": "2024-01-15T09:30:00Z"
        }
    ]
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 500: Failed to retrieve dashboard

### GET /api/parent/reports/weekly/{child_id}

Get weekly progress report.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/parent/reports/weekly/child_def456?start_date=2024-01-08&end_date=2024-01-15" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "week_start": "2024-01-08",
    "week_end": "2024-01-15",
    "total_study_time": 720,
    "practice_sessions": 12,
    "topics_completed": 8,
    "average_score": 78,
    "subject_breakdown": {
        "Physics": {
            "time_spent": 240,
            "sessions": 4,
            "topics_completed": 3,
            "average_score": 82
        },
        "Chemistry": {
            "time_spent": 180,
            "sessions": 3,
            "topics_completed": 2,
            "average_score": 75
        },
        "Mathematics": {
            "time_spent": 300,
            "sessions": 5,
            "topics_completed": 3,
            "average_score": 77
        }
    }
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 400: Invalid date range
- 500: Failed to generate report

### POST /api/parent/reports/email-schedule

Schedule email reports.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/parent/reports/email-schedule" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "parent_id": "parent_123abc",
    "frequency": "weekly",
    "day_of_week": "monday",
    "time": "09:00",
    "enabled": true
  }'
```

**Response (201):**
```json
{
    "schedule_id": "email_sched_123",
    "parent_id": "parent_123abc",
    "frequency": "weekly",
    "day_of_week": "monday",
    "time": "09:00",
    "enabled": true,
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid frequency
- 400: Invalid day of week
- 400: Invalid time format
- 500: Failed to create schedule

### GET /api/parent/notifications/settings

Get notification settings.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/parent/notifications/settings?parent_id=PARENT_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "parent_id": "parent_123abc",
    "email_notifications": true,
    "sms_notifications": true,
    "push_notifications": true,
    "weekly_reports": true,
    "achievement_alerts": true,
    "study_reminders": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
}
```

**Common Errors:**
- 404: Settings not found
- 403: Ownership verification failed
- 500: Failed to retrieve settings

### PUT /api/parent/notifications/settings

Update notification settings.

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/parent/notifications/settings" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "parent_id": "parent_123abc",
    "email_notifications": true,
    "sms_notifications": false,
    "push_notifications": true,
    "weekly_reports": false
  }'
```

**Response (200):**
```json
{
    "parent_id": "parent_123abc",
    "email_notifications": true,
    "sms_notifications": false,
    "push_notifications": true,
    "weekly_reports": false,
    "achievement_alerts": true,
    "study_reminders": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T16:00:00Z"
}
```

**Common Errors:**
- 404: Settings not found
- 403: Ownership verification failed
- 400: Invalid notification settings
- 500: Failed to update settings

### POST /api/parent/goals/{child_id}

Create learning goal for child.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/parent/goals/child_def456" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Complete Physics Mechanics",
    "description": "Finish all mechanics topics by end of month",
    "target_date": "2024-02-01",
    "subject": "Physics",
    "topics": ["Mechanics", "Kinematics", "Dynamics"]
  }'
```

**Response (201):**
```json
{
    "goal_id": "goal_123",
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "title": "Complete Physics Mechanics",
    "description": "Finish all mechanics topics by end of month",
    "target_date": "2024-02-01",
    "subject": "Physics",
    "topics": ["Mechanics", "Kinematics", "Dynamics"],
    "status": "active",
    "progress": 0,
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 400: Invalid target date
- 500: Failed to create goal

### GET /api/parent/goals/{child_id}

Get goals for child.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/parent/goals/child_def456" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "goals": [
        {
            "goal_id": "goal_123",
            "child_id": "child_def456",
            "parent_id": "parent_123abc",
            "title": "Complete Physics Mechanics",
            "description": "Finish all mechanics topics by end of month",
            "target_date": "2024-02-01",
            "subject": "Physics",
            "topics": ["Mechanics", "Kinematics", "Dynamics"],
            "status": "active",
            "progress": 25,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 500: Failed to retrieve goals

### PUT /api/parent/goals/{child_id}/{goal_id}

Update goal progress or status.

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/parent/goals/child_def456/goal_123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "progress": 50,
    "status": "in_progress"
  }'
```

**Response (200):**
```json
{
    "goal_id": "goal_123",
    "child_id": "child_def456",
    "parent_id": "parent_123abc",
    "title": "Complete Physics Mechanics",
    "description": "Finish all mechanics topics by end of month",
    "target_date": "2024-02-01",
    "subject": "Physics",
    "topics": ["Mechanics", "Kinematics", "Dynamics"],
    "status": "in_progress",
    "progress": 50,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-20T15:45:00Z"
}
```

**Common Errors:**
- 404: Goal not found
- 403: Ownership verification failed
- 400: Invalid progress value
- 500: Failed to update goal

## Student Dashboard

### Overview

Student dashboard endpoints provide personalized learning features, practice generation, doubt resolution, and performance insights.

### GET /api/student/today/{student_id}

Get today's learning plan.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/today/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "date": "2024-01-15",
    "daily_plan": {
        "topics_to_cover": ["Mechanics", "Chemical Bonding"],
        "practice_sessions": 3,
        "estimated_time": 120,
        "difficulty_level": "medium"
    },
    "recommendations": [
        {
            "type": "practice",
            "subject": "Physics",
            "topic": "Mechanics",
            "reason": "Based on your progress"
        }
    ],
    "motivational_message": "Great progress! Keep up the good work!"
}
```

**Common Errors:**
- 401: Invalid student token
- 404: Student not found
- 500: Failed to retrieve daily plan

### GET /api/student/topic/{topic_id}/resources

Get learning resources for a topic.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/topic/physics_mechanics/resources" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "topic_id": "physics_mechanics",
    "topic_name": "Mechanics",
    "subject": "Physics",
    "resources": [
        {
            "type": "video",
            "title": "Introduction to Mechanics",
            "url": "https://example.com/mechanics-intro",
            "duration": 300,
            "difficulty": "beginner"
        },
        {
            "type": "notes",
            "title": "Mechanics Fundamentals",
            "content": "Basic principles of mechanics...",
            "format": "pdf",
            "pages": 15
        }
    ]
}
```

**Common Errors:**
- 404: Topic not found
- 401: Invalid student token
- 500: Failed to retrieve resources

### POST /api/student/practice/quick

Generate quick practice session.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/student/practice/quick" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "student_id": "student_def456",
    "subject": "Physics",
    "difficulty": "medium",
    "num_questions": 5,
    "time_limit": 600
  }'
```

**Response (201):**
```json
{
    "practice_id": "practice_123",
    "student_id": "student_def456",
    "subject": "Physics",
    "difficulty": "medium",
    "questions": [
        {
            "question_id": "q_1",
            "text": "What is Newton's first law?",
            "options": ["A", "B", "C", "D"],
            "type": "multiple_choice"
        }
    ],
    "time_limit": 600,
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid parameters
- 401: Invalid student token
- 500: Failed to generate practice

### POST /api/student/doubts

Create a doubt/question.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/student/doubts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "student_id": "student_def456",
    "subject": "Physics",
    "topic": "Mechanics",
    "question": "How do you calculate friction force?",
    "context": "I'm confused about the formula"
  }'
```

**Response (201):**
```json
{
    "doubt_id": "doubt_123",
    "student_id": "student_def456",
    "subject": "Physics",
    "topic": "Mechanics",
    "question": "How do you calculate friction force?",
    "context": "I'm confused about the formula",
    "status": "pending",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid question format
- 401: Invalid student token
- 500: Failed to create doubt

### GET /api/student/doubts/{doubt_id}/explanation

Get explanation for a doubt.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/doubts/doubt_123/explanation" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "doubt_id": "doubt_123",
    "explanation": "Friction force is calculated using the formula F = μN, where μ is the coefficient of friction and N is the normal force...",
    "teacher_notes": "Remember that friction always opposes motion",
    "related_examples": [
        {
            "description": "Block on inclined plane",
            "solution": "F = μmg cos(θ)"
        }
    ],
    "generated_at": "2024-01-15T11:00:00Z"
}
```

**Common Errors:**
- 404: Doubt not found
- 401: Invalid student token
- 500: Failed to generate explanation

### GET /api/student/revision/due

Get due revision items.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/revision/due" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "due_revisions": [
        {
            "topic_id": "physics_kinematics",
            "topic_name": "Kinematics",
            "subject": "Physics",
            "last_studied": "2024-01-10",
            "revision_due": "2024-01-17",
            "priority": "high",
            "estimated_time": 30
        }
    ],
    "total_revisions": 1,
    "total_time": 30
}
```

**Common Errors:**
- 401: Invalid student token
- 500: Failed to retrieve revisions

### POST /api/student/revision/mark-complete/{topic_id}

Mark revision as complete.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/student/revision/mark-complete/physics_kinematics" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "message": "Revision marked as complete",
    "topic_id": "physics_kinematics",
    "completed_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Topic not found
- 401: Invalid student token
- 500: Failed to mark complete

### POST /api/student/bookmarks

Create bookmark.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/student/bookmarks" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "student_id": "student_def456",
    "topic_id": "physics_mechanics",
    "resource_type": "video",
    "resource_url": "https://example.com/mechanics-video",
    "title": "Mechanics Introduction",
    "notes": "Good explanation of basics"
  }'
```

**Response (201):**
```json
{
    "bookmark_id": "bookmark_123",
    "student_id": "student_def456",
    "topic_id": "physics_mechanics",
    "resource_type": "video",
    "resource_url": "https://example.com/mechanics-video",
    "title": "Mechanics Introduction",
    "notes": "Good explanation of basics",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid bookmark data
- 401: Invalid student token
- 500: Failed to create bookmark

### GET /api/student/bookmarks

Get bookmarks.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/bookmarks" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "bookmarks": [
        {
            "bookmark_id": "bookmark_123",
            "student_id": "student_def456",
            "topic_id": "physics_mechanics",
            "resource_type": "video",
            "resource_url": "https://example.com/mechanics-video",
            "title": "Mechanics Introduction",
            "notes": "Good explanation of basics",
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}
```

**Common Errors:**
- 401: Invalid student token
- 500: Failed to retrieve bookmarks

### DELETE /api/student/bookmarks/{bookmark_id}

Delete bookmark.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/student/bookmarks/bookmark_123" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "message": "Bookmark deleted successfully"
}
```

**Common Errors:**
- 404: Bookmark not found
- 401: Invalid student token
- 500: Failed to delete bookmark

### GET /api/student/insights/{student_id}

Get performance insights.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/insights/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "insights": [
        {
            "type": "strength",
            "subject": "Physics",
            "topic": "Mechanics",
            "description": "Strong understanding of basic concepts",
            "confidence": 85
        },
        {
            "type": "improvement",
            "subject": "Chemistry",
            "topic": "Organic Chemistry",
            "description": "Needs more practice with reaction mechanisms",
            "confidence": 60
        }
    ],
    "overall_performance": 75,
    "generated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to generate insights

### GET /api/student/compare/percentile

Get peer comparison percentile.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/student/compare/percentile?subject=Physics&exam_type=JEE_MAIN" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "subject": "Physics",
    "exam_type": "JEE_MAIN",
    "percentile": 78,
    "total_students": 10000,
    "students_below": 7800,
    "students_above": 2200,
    "benchmark_scores": {
        "25th_percentile": 45,
        "50th_percentile": 65,
        "75th_percentile": 80,
        "90th_percentile": 90
    },
    "generated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid parameters
- 401: Invalid student token
- 500: Failed to generate comparison

## Diagnostic Tests

### Overview

Diagnostic test endpoints manage test creation, execution, and analysis for initial student assessment.

### POST /api/diagnostic/create

Create diagnostic test.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/diagnostic/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "child_id": "child_def456",
    "exam_type": "JEE_MAIN",
    "subject_preferences": {
        "Physics": 40,
        "Chemistry": 35,
        "Mathematics": 25
    }
  }'
```

**Response (201):**
```json
{
    "test_id": "diag_test_123",
    "child_id": "child_def456",
    "exam_type": "JEE_MAIN",
    "subject_preferences": {
        "Physics": 40,
        "Chemistry": 35,
        "Mathematics": 25
    },
    "status": "scheduled",
    "scheduled_date": "2024-01-20T10:00:00Z",
    "duration": 180,
    "total_questions": 90,
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 400: Invalid exam type
- 500: Failed to create test

### GET /api/diagnostic/{test_id}

Get diagnostic test details.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/diagnostic/diag_test_123" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "test_id": "diag_test_123",
    "child_id": "child_def456",
    "exam_type": "JEE_MAIN",
    "subject_preferences": {
        "Physics": 40,
        "Chemistry": 35,
        "Mathematics": 25
    },
    "status": "in_progress",
    "scheduled_date": "2024-01-20T10:00:00Z",
    "started_at": "2024-01-20T10:05:00Z",
    "duration": 180,
    "total_questions": 90,
    "questions_attempted": 30,
    "time_remaining": 150
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 500: Failed to retrieve test

### POST /api/diagnostic/{test_id}/start

Start diagnostic test.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/diagnostic/diag_test_123/start" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "test_id": "diag_test_123",
    "status": "in_progress",
    "started_at": "2024-01-20T10:05:00Z",
    "time_remaining": 180,
    "questions": [
        {
            "question_id": "q_1",
            "text": "What is Newton's first law?",
            "options": ["A", "B", "C", "D"],
            "type": "multiple_choice"
        }
    ]
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 400: Test already started
- 500: Failed to start test

### POST /api/diagnostic/{test_id}/submit

Submit diagnostic test answers.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/diagnostic/diag_test_123/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "answers": [
        {
            "question_id": "q_1",
            "selected_option": "A",
            "time_spent": 45
        }
    ],
    "total_time": 165
  }'
```

**Response (200):**
```json
{
    "test_id": "diag_test_123",
    "status": "completed",
    "completed_at": "2024-01-20T13:15:00Z",
    "total_time": 165,
    "score": {
        "total": 90,
        "correct": 65,
        "incorrect": 25,
        "percentage": 72.2
    },
    "subject_wise_scores": {
        "Physics": {
            "total": 36,
            "correct": 28,
            "percentage": 77.8
        },
        "Chemistry": {
            "total": 32,
            "correct": 22,
            "percentage": 68.8
        },
        "Mathematics": {
            "total": 22,
            "correct": 15,
            "percentage": 68.2
        }
    },
    "recommendations": [
        "Focus on Chemistry organic reactions",
        "Practice Mathematics integration problems"
    ]
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 400: Test not in progress
- 500: Failed to submit test

### GET /api/diagnostic/{test_id}/results

Get diagnostic test results.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/diagnostic/diag_test_123/results" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "test_id": "diag_test_123",
    "child_id": "child_def456",
    "status": "completed",
    "completed_at": "2024-01-20T13:15:00Z",
    "total_time": 165,
    "score": {
        "total": 90,
        "correct": 65,
        "incorrect": 25,
        "percentage": 72.2
    },
    "subject_wise_scores": {
        "Physics": {
            "total": 36,
            "correct": 28,
            "percentage": 77.8
        },
        "Chemistry": {
            "total": 32,
            "correct": 22,
            "percentage": 68.8
        },
        "Mathematics": {
            "total": 22,
            "correct": 15,
            "percentage": 68.2
        }
    },
    "recommendations": [
        "Focus on Chemistry organic reactions",
        "Practice Mathematics integration problems"
    ],
    "analysis": {
        "strengths": ["Physics Mechanics"],
        "weaknesses": ["Chemistry Organic", "Mathematics Calculus"],
        "suggested_level": "intermediate"
    }
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 400: Results not available
- 500: Failed to retrieve results

## Test Management

### Overview

Test management endpoints handle test creation, pattern management, and scheduling for practice tests.

### POST /api/testing/test/create

Create practice test.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/testing/test/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "child_id": "child_def456",
    "title": "Physics Mechanics Practice",
    "subject": "Physics",
    "topics": ["Mechanics", "Kinematics"],
    "difficulty": "medium",
    "num_questions": 20,
    "time_limit": 1200,
    "pattern": "JEE_MAIN"
  }'
```

**Response (201):**
```json
{
    "test_id": "practice_test_123",
    "child_id": "child_def456",
    "title": "Physics Mechanics Practice",
    "subject": "Physics",
    "topics": ["Mechanics", "Kinematics"],
    "difficulty": "medium",
    "num_questions": 20,
    "time_limit": 1200,
    "pattern": "JEE_MAIN",
    "status": "created",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 400: Invalid test parameters
- 500: Failed to create test

### GET /api/testing/test/{test_id}

Get test details.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/testing/test/practice_test_123" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "test_id": "practice_test_123",
    "child_id": "child_def456",
    "title": "Physics Mechanics Practice",
    "subject": "Physics",
    "topics": ["Mechanics", "Kinematics"],
    "difficulty": "medium",
    "num_questions": 20,
    "time_limit": 1200,
    "pattern": "JEE_MAIN",
    "status": "ready",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 500: Failed to retrieve test

### POST /api/testing/test/{test_id}/start

Start practice test.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/testing/test/practice_test_123/start" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "test_id": "practice_test_123",
    "status": "in_progress",
    "started_at": "2024-01-15T11:00:00Z",
    "time_remaining": 1200,
    "questions": [
        {
            "question_id": "q_1",
            "text": "What is Newton's first law?",
            "options": ["A", "B", "C", "D"],
            "type": "multiple_choice"
        }
    ]
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 400: Test already started
- 500: Failed to start test

### POST /api/testing/test/{test_id}/submit

Submit practice test answers.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/testing/test/practice_test_123/submit" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "answers": [
        {
            "question_id": "q_1",
            "selected_option": "A",
            "time_spent": 60
        }
    ],
    "total_time": 1150
  }'
```

**Response (200):**
```json
{
    "test_id": "practice_test_123",
    "status": "completed",
    "completed_at": "2024-01-15T11:19:00Z",
    "total_time": 1150,
    "score": {
        "total": 20,
        "correct": 16,
        "incorrect": 4,
        "percentage": 80
    },
    "detailed_results": [
        {
            "question_id": "q_1",
            "correct": true,
            "time_spent": 60,
            "explanation": "Newton's first law states that an object..."
        }
    ]
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 400: Test not in progress
- 500: Failed to submit test

### GET /api/testing/test/{test_id}/results

Get practice test results.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/testing/test/practice_test_123/results" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "test_id": "practice_test_123",
    "child_id": "child_def456",
    "status": "completed",
    "completed_at": "2024-01-15T11:19:00Z",
    "total_time": 1150,
    "score": {
        "total": 20,
        "correct": 16,
        "incorrect": 4,
        "percentage": 80
    },
    "detailed_results": [
        {
            "question_id": "q_1",
            "correct": true,
            "time_spent": 60,
            "explanation": "Newton's first law states that an object..."
        }
    ],
    "topic_wise_performance": {
        "Mechanics": {
            "total": 12,
            "correct": 10,
            "percentage": 83.3
        },
        "Kinematics": {
            "total": 8,
            "correct": 6,
            "percentage": 75
        }
    }
}
```

**Common Errors:**
- 404: Test not found
- 403: Ownership verification failed
- 400: Results not available
- 500: Failed to retrieve results

## Schedule

### Overview

Schedule endpoints manage study schedule generation with AI-powered adaptive planning and rescheduling capabilities.

### POST /api/schedule/generate

Generate study schedule.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/schedule/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "child_id": "child_def456",
    "exam_date": "2024-04-06",
    "study_hours_per_day": 4,
    "preferred_study_times": ["morning", "evening"],
    "weak_subjects": ["Chemistry"],
    "strong_subjects": ["Physics"]
  }'
```

**Response (201):**
```json
{
    "schedule_id": "schedule_123",
    "child_id": "child_def456",
    "exam_date": "2024-04-06",
    "study_hours_per_day": 4,
    "generated_at": "2024-01-15T10:30:00Z",
    "daily_plans": [
        {
            "date": "2024-01-16",
            "day": "Tuesday",
            "topics": [
                {
                    "subject": "Physics",
                    "topic": "Mechanics",
                    "duration": 120,
                    "priority": "high"
                }
            ],
            "total_study_time": 240
        }
    ],
    "weekly_goals": [
        {
            "week": "2024-01-15 to 2024-01-21",
            "goal": "Complete Physics Mechanics",
            "topics": ["Mechanics", "Kinematics"]
        }
    ]
}
```

**Common Errors:**
- 404: Child not found
- 403: Ownership verification failed
- 400: Invalid exam date
- 500: Failed to generate schedule

### GET /api/schedule/{child_id}

Get study schedule.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/schedule/child_def456" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "schedule_id": "schedule_123",
    "child_id": "child_def456",
    "exam_date": "2024-04-06",
    "study_hours_per_day": 4,
    "generated_at": "2024-01-15T10:30:00Z",
    "daily_plans": [
        {
            "date": "2024-01-16",
            "day": "Tuesday",
            "topics": [
                {
                    "subject": "Physics",
                    "topic": "Mechanics",
                    "duration": 120,
                    "priority": "high"
                }
            ],
            "total_study_time": 240
        }
    ],
    "weekly_goals": [
        {
            "week": "2024-01-15 to 2024-01-21",
            "goal": "Complete Physics Mechanics",
            "topics": ["Mechanics", "Kinematics"]
        }
    ]
}
```

**Common Errors:**
- 404: Schedule not found
- 403: Ownership verification failed
- 500: Failed to retrieve schedule

### PUT /api/schedule/{child_id}

Update study schedule.

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/schedule/child_def456" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "study_hours_per_day": 5,
    "preferred_study_times": ["morning", "afternoon"],
    "weak_subjects": ["Mathematics"]
  }'
```

**Response (200):**
```json
{
    "schedule_id": "schedule_123",
    "child_id": "child_def456",
    "exam_date": "2024-04-06",
    "study_hours_per_day": 5,
    "updated_at": "2024-01-20T15:45:00Z",
    "daily_plans": [
        {
            "date": "2024-01-16",
            "day": "Tuesday",
            "topics": [
                {
                    "subject": "Physics",
                    "topic": "Mechanics",
                    "duration": 150,
                    "priority": "high"
                }
            ],
            "total_study_time": 300
        }
    ]
}
```

**Common Errors:**
- 404: Schedule not found
- 403: Ownership verification failed
- 400: Invalid update parameters
- 500: Failed to update schedule

## Study Center

### Overview

Study Center endpoints provide comprehensive learning materials, progress tracking, and personalized content recommendations.

### GET /api/study/progress/{student_id}

Get study progress.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/study/progress/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "overall_progress": 65,
    "subject_progress": {
        "Physics": {
            "completed_topics": 15,
            "total_topics": 25,
            "percentage": 60,
            "current_topic": "Thermodynamics"
        },
        "Chemistry": {
            "completed_topics": 12,
            "total_topics": 20,
            "percentage": 60,
            "current_topic": "Organic Chemistry"
        },
        "Mathematics": {
            "completed_topics": 18,
            "total_topics": 24,
            "percentage": 75,
            "current_topic": "Integration"
        }
    },
    "study_stats": {
        "total_study_time": 3600,
        "sessions_completed": 45,
        "average_session_duration": 80,
        "last_study_date": "2024-01-15"
    }
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to retrieve progress

### GET /api/study/materials/{subject}/{topic}

Get learning materials for a topic.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/study/materials/Physics/Mechanics" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "subject": "Physics",
    "topic": "Mechanics",
    "materials": [
        {
            "type": "video",
            "title": "Introduction to Mechanics",
            "url": "https://example.com/mechanics-intro",
            "duration": 600,
            "difficulty": "beginner",
            "description": "Basic concepts of mechanics"
        },
        {
            "type": "notes",
            "title": "Mechanics Fundamentals",
            "content": "Comprehensive notes on mechanics...",
            "format": "pdf",
            "pages": 20,
            "download_url": "https://example.com/mechanics-notes.pdf"
        },
        {
            "type": "practice",
            "title": "Mechanics Practice Questions",
            "questions": 15,
            "difficulty": "medium",
            "url": "https://example.com/mechanics-practice"
        }
    ]
}
```

**Common Errors:**
- 404: Topic not found
- 401: Invalid student token
- 500: Failed to retrieve materials

### POST /api/study/session/start

Start study session.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/study/session/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "student_id": "student_def456",
    "subject": "Physics",
    "topic": "Mechanics",
    "material_type": "video"
  }'
```

**Response (201):**
```json
{
    "session_id": "session_123",
    "student_id": "student_def456",
    "subject": "Physics",
    "topic": "Mechanics",
    "material_type": "video",
    "started_at": "2024-01-15T10:30:00Z",
    "status": "active"
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 400: Invalid session parameters
- 500: Failed to start session

### POST /api/study/session/{session_id}/complete

Complete study session.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/study/session/session_123/complete" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "time_spent": 600,
    "progress_percentage": 100,
    "notes": "Completed video and notes"
  }'
```

**Response (200):**
```json
{
    "session_id": "session_123",
    "student_id": "student_def456",
    "completed_at": "2024-01-15T20:30:00Z",
    "time_spent": 600,
    "progress_percentage": 100,
    "notes": "Completed video and notes",
    "status": "completed"
}
```

**Common Errors:**
- 404: Session not found
- 401: Invalid student token
- 400: Invalid completion data
- 500: Failed to complete session

## Gamification

### Overview

Gamification endpoints manage achievements, badges, leaderboards, and motivational features to enhance student engagement.

### GET /api/gamification/achievements/{student_id}

Get student achievements.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/gamification/achievements/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "achievements": [
        {
            "achievement_id": "ach_123",
            "title": "Physics Champion",
            "description": "Score 80%+ in 5 Physics tests",
            "badge_url": "https://example.com/badges/physics-champion.png",
            "earned_at": "2024-01-15T10:30:00Z",
            "points": 100
        },
        {
            "achievement_id": "ach_124",
            "title": "Week Warrior",
            "description": "Maintain 7-day study streak",
            "badge_url": "https://example.com/badges/week-warrior.png",
            "earned_at": "2024-01-14T09:00:00Z",
            "points": 50
        }
    ],
    "total_points": 150,
    "total_achievements": 2
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to retrieve achievements

### POST /api/gamification/achievements/{student_id}

Award achievement to student.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/gamification/achievements/student_def456" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "achievement_type": "test_completion",
    "subject": "Physics",
    "score": 85,
    "difficulty": "medium"
  }'
```

**Response (201):**
```json
{
    "achievement_id": "ach_125",
    "student_id": "student_def456",
    "title": "Physics Master",
    "description": "Score 85% in Physics test",
    "badge_url": "https://example.com/badges/physics-master.png",
    "earned_at": "2024-01-15T10:30:00Z",
    "points": 75
}
```

**Common Errors:**
- 404: Student not found
- 403: Ownership verification failed
- 400: Invalid achievement data
- 500: Failed to award achievement

### GET /api/gamification/leaderboard/{exam_type}

Get leaderboard for exam type.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/gamification/leaderboard/JEE_MAIN" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "exam_type": "JEE_MAIN",
    "leaderboard": [
        {
            "rank": 1,
            "student_id": "student_abc123",
            "name": "Top Student",
            "total_points": 2500,
            "avatar_url": "https://example.com/avatars/top-student.png"
        },
        {
            "rank": 2,
            "student_id": "student_def456",
            "name": "Current Student",
            "total_points": 1500,
            "avatar_url": "https://example.com/avatars/current-student.png"
        }
    ],
    "student_rank": 2,
    "total_participants": 5000
}
```

**Common Errors:**
- 400: Invalid exam type
- 401: Invalid student token
- 500: Failed to retrieve leaderboard

### GET /api/gamification/streak/{student_id}

Get study streak information.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/gamification/streak/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "current_streak": 7,
    "longest_streak": 15,
    "last_study_date": "2024-01-15",
    "streak_bonus_points": 35,
    "next_milestone": 10,
    "milestone_bonus": 50
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to retrieve streak

### POST /api/gamification/streak/{student_id}/update

Update study streak.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/gamification/streak/student_def456/update" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "current_streak": 8,
    "updated_at": "2024-01-15T10:30:00Z",
    "points_earned": 5
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to update streak

## Analytics

### Overview

Analytics endpoints provide performance analytics, insights, and predictive analysis for student progress tracking.

### GET /api/analytics/performance/{student_id}

Get performance analytics.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/analytics/performance/student_def456?period=30d" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "period": "30d",
    "overall_performance": {
        "average_score": 75,
        "improvement_rate": 12,
        "study_time": 2400,
        "sessions_completed": 30
    },
    "subject_wise_performance": {
        "Physics": {
            "average_score": 78,
            "improvement_rate": 15,
            "time_spent": 900,
            "sessions": 12
        },
        "Chemistry": {
            "average_score": 72,
            "improvement_rate": 8,
            "time_spent": 750,
            "sessions": 10
        },
        "Mathematics": {
            "average_score": 75,
            "improvement_rate": 13,
            "time_spent": 750,
            "sessions": 8
        }
    },
    "trends": [
        {
            "metric": "score",
            "trend": "improving",
            "change": "+5%"
        }
    ]
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 400: Invalid period
- 500: Failed to retrieve analytics

### GET /api/analytics/progress/{student_id}

Get progress analytics.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/analytics/progress/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "syllabus_coverage": {
        "total_topics": 69,
        "completed_topics": 45,
        "coverage_percentage": 65.2,
        "remaining_topics": 24
    },
    "subject_coverage": {
        "Physics": {
            "total_topics": 25,
            "completed_topics": 18,
            "coverage_percentage": 72
        },
        "Chemistry": {
            "total_topics": 22,
            "completed_topics": 14,
            "coverage_percentage": 63.6
        },
        "Mathematics": {
            "total_topics": 22,
            "completed_topics": 13,
            "coverage_percentage": 59.1
        }
    },
    "completion_predictions": {
        "estimated_completion_date": "2024-03-15",
        "confidence": 85
    }
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to retrieve progress analytics

### GET /api/analytics/insights/{student_id}

Get AI-generated insights.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/analytics/insights/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "insights": [
        {
            "type": "strength",
            "subject": "Physics",
            "topic": "Mechanics",
            "description": "Strong understanding of Newton's laws",
            "confidence": 85,
            "recommendation": "Consider advanced topics"
        },
        {
            "type": "weakness",
            "subject": "Chemistry",
            "topic": "Organic Chemistry",
            "description": "Struggles with reaction mechanisms",
            "confidence": 70,
            "recommendation": "Focus on practice problems"
        }
    ],
    "generated_at": "2024-01-15T10:30:00Z",
    "ai_confidence": 80
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to generate insights

### GET /api/analytics/predictions/{student_id}

Get performance predictions.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/analytics/predictions/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "predictions": [
        {
            "type": "exam_score",
            "exam_type": "JEE_MAIN",
            "predicted_score": 145,
            "confidence": 75,
            "factors": [
                "Current performance trend",
                "Study time consistency",
                "Practice test scores"
            ]
        },
        {
            "type": "readiness",
            "exam_type": "JEE_MAIN",
            "readiness_percentage": 68,
            "confidence": 70,
            "recommendations": [
                "Focus on weak areas",
                "Increase practice frequency"
            ]
        }
    ],
    "generated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to generate predictions

## Syllabus Coverage

### Overview

Syllabus coverage endpoints track topic completion, identify gaps, and provide coverage analysis.

### GET /api/syllabus/coverage/{student_id}

Get syllabus coverage.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/syllabus/coverage/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "exam_type": "JEE_MAIN",
    "overall_coverage": 65.2,
    "subject_coverage": {
        "Physics": {
            "total_topics": 25,
            "completed_topics": 18,
            "coverage_percentage": 72,
            "topics": [
                {
                    "topic_id": "physics_mechanics",
                    "name": "Mechanics",
                    "completed": true,
                    "completion_date": "2024-01-10",
                    "time_spent": 300
                }
            ]
        },
        "Chemistry": {
            "total_topics": 22,
            "completed_topics": 14,
            "coverage_percentage": 63.6,
            "topics": [
                {
                    "topic_id": "chemistry_organic",
                    "name": "Organic Chemistry",
                    "completed": false,
                    "completion_date": null,
                    "time_spent": 0
                }
            ]
        },
        "Mathematics": {
            "total_topics": 22,
            "completed_topics": 13,
            "coverage_percentage": 59.1,
            "topics": [
                {
                    "topic_id": "math_calculus",
                    "name": "Calculus",
                    "completed": true,
                    "completion_date": "2024-01-12",
                    "time_spent": 450
                }
            ]
        }
    },
    "last_updated": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to retrieve coverage

### POST /api/syllabus/coverage/{student_id}/update

Update topic completion status.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/syllabus/coverage/student_def456/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "topic_id": "chemistry_organic",
    "completed": true,
    "time_spent": 240,
    "notes": "Completed organic reactions chapter"
  }'
```

**Response (200):**
```json
{
    "topic_id": "chemistry_organic",
    "student_id": "student_def456",
    "completed": true,
    "completion_date": "2024-01-15T10:30:00Z",
    "time_spent": 240,
    "notes": "Completed organic reactions chapter",
    "updated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 400: Invalid topic ID
- 500: Failed to update coverage

### GET /api/syllabus/gaps/{student_id}

Get knowledge gaps analysis.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/syllabus/gaps/student_def456" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "knowledge_gaps": [
        {
            "subject": "Chemistry",
            "topic": "Organic Chemistry",
            "gap_type": "weak_area",
            "severity": "high",
            "recommendation": "Focus on reaction mechanisms and nomenclature",
            "estimated_time_to_master": 8
        },
        {
            "subject": "Mathematics",
            "topic": "Integration",
            "gap_type": "not_covered",
            "severity": "medium",
            "recommendation": "Start with basic integration techniques",
            "estimated_time_to_master": 6
        }
    ],
    "total_gaps": 2,
    "priority_order": [
        "Chemistry - Organic Chemistry",
        "Mathematics - Integration"
    ]
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 500: Failed to analyze gaps

## Vector Search - Embeddings

### Overview

Embedding endpoints generate text embeddings for semantic search and content analysis using 768-dimensional vectors.

### POST /api/embeddings/generate

Generate text embeddings.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/embeddings/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "text": "Newton\\'s laws of motion describe the relationship between forces and motion",
    "model": "text-embedding-ada-002"
  }'
```

**Response (200):**
```json
{
    "embedding": [0.0189, -0.0074, 0.0234, ..., 0.0167],
    "model": "text-embedding-ada-002",
    "dimensions": 768,
    "usage": {
        "prompt_tokens": 12,
        "total_tokens": 12
    }
}
```

**Common Errors:**
- 400: Text too long (>8192 tokens)
- 401: Invalid token
- 500: Embedding service unavailable

### POST /api/embeddings/batch

Generate batch embeddings.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/embeddings/batch" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "texts": [
        "Newton\\'s first law",
        "Newton\\'s second law",
        "Newton\\'s third law"
    ],
    "model": "text-embedding-ada-002"
  }'
```

**Response (200):**
```json
{
    "embeddings": [
        [0.0189, -0.0074, 0.0234, ..., 0.0167],
        [0.0212, -0.0098, 0.0187, ..., 0.0198],
        [0.0156, -0.0043, 0.0298, ..., 0.0123]
    ],
    "model": "text-embedding-ada-002",
    "dimensions": 768,
    "usage": {
        "prompt_tokens": 18,
        "total_tokens": 18
    }
}
```

**Common Errors:**
- 400: Batch size too large (>100 texts)
- 401: Invalid token
- 500: Embedding service unavailable

## Vector Search

### Overview

Vector search endpoints provide semantic search capabilities using embeddings for finding similar content and topics.

### POST /api/vector/search

Perform semantic search.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/vector/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "query": "Newton\\'s laws of motion",
    "similarity_threshold": 0.7,
    "max_results": 10,
    "search_type": "topics"
  }'
```

**Response (200):**
```json
{
    "query": "Newton's laws of motion",
    "results": [
        {
            "id": "physics_mechanics",
            "title": "Mechanics",
            "subject": "Physics",
            "similarity_score": 0.89,
            "content_preview": "Newton's laws describe the relationship between forces..."
        },
        {
            "id": "physics_kinematics",
            "title": "Kinematics",
            "subject": "Physics",
            "similarity_score": 0.82,
            "content_preview": "Kinematics deals with motion without considering forces..."
        }
    ],
    "total_results": 2,
    "search_time": 0.045
}
```

**Common Errors:**
- 400: Invalid similarity threshold
- 400: Query too short
- 401: Invalid token
- 500: Search service unavailable

### GET /api/vector/similar/{content_id}

Find similar content.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/vector/similar/physics_mechanics?threshold=0.8&limit=5" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "content_id": "physics_mechanics",
    "similar_content": [
        {
            "id": "physics_dynamics",
            "title": "Dynamics",
            "subject": "Physics",
            "similarity_score": 0.85,
            "content_preview": "Dynamics extends mechanics to include forces..."
        },
        {
            "id": "physics_statics",
            "title": "Statics",
            "subject": "Physics",
            "similarity_score": 0.81,
            "content_preview": "Statics deals with forces in equilibrium..."
        }
    ],
    "total_similar": 2
}
```

**Common Errors:**
- 404: Content not found
- 401: Invalid token
- 400: Invalid threshold
- 500: Search service unavailable

## RAG

### Overview

RAG (Retrieval-Augmented Generation) endpoints generate contextual responses using vector search and AI generation.

### POST /api/rag/generate

Generate RAG response.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/rag/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "query": "Explain Newton\\'s first law with examples",
    "context": "Physics",
    "max_tokens": 500,
    "temperature": 0.7
  }'
```

**Response (200):**
```json
{
    "query": "Explain Newton's first law with examples",
    "response": "Newton's first law of motion, also known as the law of inertia, states that an object at rest stays at rest and an object in motion stays in motion unless acted upon by an external force. For example, a book on a table remains stationary until you push it, and a moving car continues moving until brakes are applied.",
    "sources": [
        {
            "id": "physics_mechanics",
            "title": "Mechanics",
            "relevance_score": 0.92
        }
    ],
    "usage": {
        "prompt_tokens": 15,
        "completion_tokens": 85,
        "total_tokens": 100
    }
}
```

**Common Errors:**
- 400: Query too long
- 401: Invalid token
- 500: RAG service unavailable

### GET /api/rag/pipeline/status

Get RAG pipeline status.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/rag/pipeline/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "status": "healthy",
    "vector_db": "connected",
    "embedding_service": "available",
    "generation_service": "available",
    "last_check": "2024-01-15T10:30:00Z",
    "performance_metrics": {
        "avg_response_time": 1.2,
        "success_rate": 99.5
    }
}
```

**Common Errors:**
- 401: Invalid token
- 500: Status check failed

## AI Features

### Overview

AI features endpoints provide various AI-powered capabilities including tutoring, recommendations, and content generation.

### POST /api/ai/tutor/chat

AI tutor chat.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ai/tutor/chat" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN" \
  -d '{
    "student_id": "student_def456",
    "message": "How do I solve quadratic equations?",
    "subject": "Mathematics",
    "conversation_history": [
        {
            "role": "user",
            "message": "What are quadratic equations?"
        },
        {
            "role": "assistant",
            "message": "Quadratic equations are polynomial equations..."
        }
    ]
  }'
```

**Response (200):**
```json
{
    "response": "To solve quadratic equations ax² + bx + c = 0, you can use the quadratic formula: x = (-b ± √(b²-4ac))/2a. For example, to solve 2x² + 5x - 3 = 0, first identify a=2, b=5, c=-3, then apply the formula...",
    "confidence": 0.85,
    "related_topics": ["Quadratic Formula", "Factoring", "Graphing"],
    "conversation_id": "conv_123"
}
```

**Common Errors:**
- 400: Message too long
- 401: Invalid student token
- 500: AI service unavailable

### GET /api/ai/recommendations/{student_id}

Get personalized recommendations.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/ai/recommendations/student_def456?type=study_topics" \
  -H "Authorization: Bearer STUDENT_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "student_id": "student_def456",
    "recommendations": [
        {
            "type": "study_topic",
            "subject": "Chemistry",
            "topic": "Organic Chemistry - Reaction Mechanisms",
            "priority": "high",
            "reason": "Based on your recent test performance",
            "estimated_time": 120
        },
        {
            "type": "practice",
            "subject": "Mathematics",
            "topic": "Integration Problems",
            "priority": "medium",
            "reason": "Gap identified in syllabus coverage",
            "estimated_time": 60
        }
    ],
    "generated_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 404: Student not found
- 401: Invalid student token
- 400: Invalid recommendation type
- 500: Failed to generate recommendations

### POST /api/ai/content/generate

Generate AI content.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/ai/content/generate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "content_type": "notes",
    "subject": "Physics",
    "topic": "Mechanics",
    "difficulty": "medium",
    "length": "medium"
  }'
```

**Response (200):**
```json
{
    "content": "# Mechanics Notes\\n\\n## Introduction\\n\\nMechanics is the branch of physics dealing with forces and motion...",
    "content_type": "notes",
    "subject": "Physics",
    "topic": "Mechanics",
    "difficulty": "medium",
    "generated_at": "2024-01-15T10:30:00Z",
    "word_count": 500
}
```

**Common Errors:**
- 400: Invalid content type
- 401: Invalid token
- 500: Content generation failed

## Payment

### Overview

Payment endpoints handle subscription management, order creation, and payment verification using Razorpay integration.

### GET /api/payment/plans

Get available subscription plans.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/payment/plans"
```

**Response (200):**
```json
{
    "plans": [
        {
            "plan_id": "free",
            "name": "Free Plan",
            "price": 0,
            "currency": "INR",
            "duration": "lifetime",
            "features": [
                "Basic access to study materials",
                "Limited practice tests",
                "Community support"
            ]
        },
        {
            "plan_id": "premium_monthly",
            "name": "Premium Monthly",
            "price": 99900,
            "currency": "INR",
            "duration": "monthly",
            "features": [
                "Unlimited access to study materials",
                "Unlimited practice tests",
                "AI tutor access",
                "Priority support",
                "Performance analytics"
            ]
        },
        {
            "plan_id": "premium_yearly",
            "name": "Premium Yearly",
            "price": 99900,
            "currency": "INR",
            "duration": "yearly",
            "features": [
                "All Premium Monthly features",
                "2 months free"
            ]
        }
    ]
}
```

**Common Errors:**
- 500: Failed to retrieve plans

### POST /api/payment/order/create

Create payment order.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/payment/order/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "plan_id": "premium_monthly",
    "amount": 99900,
    "currency": "INR",
    "receipt_email": "parent@example.com"
  }'
```

**Response (201):**
```json
{
    "order_id": "order_123",
    "razorpay_order_id": "order_abc123def456",
    "amount": 99900,
    "currency": "INR",
    "status": "created",
    "created_at": "2024-01-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid plan ID
- 400: Invalid amount
- 401: Invalid token
- 500: Failed to create order

### POST /api/payment/verify

Verify payment.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/payment/verify" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "razorpay_order_id": "order_abc123def456",
    "razorpay_payment_id": "pay_abc123def456",
    "razorpay_signature": "generated_signature"
  }'
```

**Response (200):**
```json
{
    "payment_id": "payment_123",
    "order_id": "order_123",
    "status": "verified",
    "subscription_activated": true,
    "plan_id": "premium_monthly",
    "activated_at": "2024-01-15T10:30:00Z",
    "expires_at": "2024-02-15T10:30:00Z"
}
```

**Common Errors:**
- 400: Invalid signature
- 400: Payment not found
- 401: Invalid token
- 500: Verification failed

### GET /api/payment/subscription/{parent_id}

Get subscription status.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/payment/subscription/parent_123abc" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response (200):**
```json
{
    "parent_id": "parent_123abc",
    "subscription": {
        "plan_id": "premium_monthly",
        "status": "active",
        "activated_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-02-15T10:30:00Z",
        "auto_renew": true
    },
    "payment_history": [
        {
            "payment_id": "payment_123",
            "amount": 99900,
            "currency": "INR",
            "status": "success",
            "date": "2024-01-15T10:30:00Z"
        }
    ]
}
```

**Common Errors:**
- 404: Parent not found
- 401: Invalid token
- 500: Failed to retrieve subscription

## Health

### Overview

Health endpoints provide system status monitoring and health checks for all services.

### GET /api/health

Get overall system health.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/health"
```

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "services": {
        "database": "healthy",
        "ai_services": "healthy",
        "payment_gateway": "healthy",
        "email_service": "healthy"
    },
    "uptime": "99.9%"
}
```

**Common Errors:**
- 500: Health check failed

### GET /api/health/detailed

Get detailed health information.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/health/detailed"
```

**Response (200):**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.0.0",
    "services": {
        "database": {
            "status": "healthy",
            "response_time": 45,
            "connections": 25
        },
        "ai_services": {
            "status": "healthy",
            "gemini_api": "available",
            "rag_pipeline": "operational",
            "response_time": 1.2
        },
        "payment_gateway": {
            "status": "healthy",
            "razorpay": "connected",
            "last_transaction": "2024-01-15T09:45:00Z"
        },
        "email_service": {
            "status": "healthy",
            "provider": "sendgrid",
            "last_email": "2024-01-15T10:00:00Z"
        }
    },
    "metrics": {
        "cpu_usage": "45%",
        "memory_usage": "60%",
        "disk_usage": "30%",
        "network_latency": 25
    }
}
```

**Common Errors:**
- 500: Detailed health check failed

## Common Testing Patterns

### Authentication Flow
1. Register parent using email/phone/Google
2. Login to get access and refresh tokens
3. Use access token for authenticated requests
4. Refresh token when expired
5. Logout when done

### Error Handling
- 400: Bad Request - Invalid input data
- 401: Unauthorized - Invalid/missing token
- 403: Forbidden - Permission denied
- 404: Not Found - Resource doesn't exist
- 429: Too Many Requests - Rate limit exceeded
- 500: Internal Server Error - Service failure
- 503: Service Unavailable - External service down

### Testing Best Practices
1. Use unique identifiers for each test
2. Test both success and error scenarios
3. Verify response structure matches documentation
4. Check authentication requirements for each endpoint
5. Test with different user roles (parent/child)
6. Validate input constraints and edge cases
7. Monitor rate limits and implement backoff
8. Use environment variables for configuration

### Environment Setup
```bash
# Development
API_BASE_URL=http://localhost:8000

# Staging
API_BASE_URL=https://staging-api.mentor-ai.com

# Production
API_BASE_URL=https://api.mentor-ai.com
```

This comprehensive endpoints guide provides all the information needed to test the Mentor AI API effectively. Each endpoint includes detailed request/response examples, error scenarios, and troubleshooting guidance.
