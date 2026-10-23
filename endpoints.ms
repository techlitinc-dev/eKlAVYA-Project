# eKlAVYA / Mentor AI Platform — Complete Backend API Reference (`endpoints.md`)

> **Target Audience:** AI Coding Agents & Frontend Engineers building the Web Application.
> This specification documents every backend endpoint, authentication scheme, query/path parameter, and exact JSON request/response payload exposed by the FastAPI backend (`Backend/main.py`).

---

## Table of Contents

1. [Global API Conventions & Authentication](#1-global-api-conventions--authentication)
2. [Domain 1: Health & System Metadata](#2-domain-1-health--system-metadata)
3. [Domain 2: Authentication, Verification & Session Management](#3-domain-2-authentication-verification--session-management)
4. [Domain 3: Parent Onboarding, Child Profile & Exam Selection](#4-domain-3-parent-onboarding-child-profile--exam-selection)
5. [Domain 4: Hermes 1-to-1 Socratic AI Mentor & Micro-Topic State Machine](#5-domain-4-hermes-1-to-1-socratic-ai-mentor--micro-topic-state-machine)
6. [Domain 5: MARKS Chapter-wise PYQ Bank (CPYQB) & Practice Mode](#6-domain-5-marks-chapter-wise-pyq-bank-cpyqb--practice-mode)
7. [Domain 6: MARKS Multi-Step Custom Test Generator (CTG) & CBT Engine](#7-domain-6-marks-multi-step-custom-test-generator-ctg--cbt-engine)
8. [Domain 7: MARKS Revision Flash Cards (RFC) & Formula Cards](#8-domain-7-marks-revision-flash-cards-rfc--formula-cards)
9. [Domain 8: MARKS Smart Notebooks, Bookmarking & Automated Error Notebook](#9-domain-8-marks-smart-notebooks-bookmarking--automated-error-notebook)
10. [Domain 9: MARKS Teacher / Parent Homework Assignments & Classroom Analytics](#10-domain-9-marks-teacher--parent-homework-assignments--classroom-analytics)
11. [Domain 10: MARKS Daily Goals, Activity Heatmap, Daily Dose & Weekly Leagues](#11-domain-10-marks-daily-goals-activity-heatmap-daily-dose--weekly-leagues)
12. [Domain 11: Medical / NEET NCERT Line-by-Line Modules & Revision Zones](#12-domain-11-medical--neet-ncert-line-by-line-modules--revision-zones)
13. [Domain 12: SATHEE AI Hub — Vision OCR, SSE Streaming Doubt Solver, Similar Questions, OMR Grader, Rank Predictor & College Cutoffs](#13-domain-12-sathee-ai-hub--vision-ocr-sse-streaming-doubt-solver-similar-questions-omr-grader-rank-predictor--college-cutoffs)
14. [Domain 13: Study Center & AI Learning Journey](#14-domain-13-study-center--ai-learning-journey)
15. [Domain 14: Diagnostic Tests & Test Lifecycle Management](#15-domain-14-diagnostic-tests--test-lifecycle-management)
16. [Domain 15: Adaptive Study Schedule & Progress Tracking](#16-domain-15-adaptive-study-schedule--progress-tracking)
17. [Domain 16: Vector Search, Embeddings, RAG Question Generation & Syllabus Coverage](#17-domain-16-vector-search-embeddings-rag-question-generation--syllabus-coverage)
18. [Domain 17: Parent Dashboard, Student Dashboard, Legacy Gamification & Analytics](#18-domain-17-parent-dashboard-student-dashboard-legacy-gamification--analytics)
19. [Domain 18: Subscriptions & Razorpay Payments](#19-domain-18-subscriptions--razorpay-payments)
20. [Recommended Web Application Architecture & User Flows for AI Agents](#20-recommended-web-application-architecture--user-flows-for-ai-agents)

---

## 1. Global API Conventions & Authentication

### 1.1. Base URLs
- **Local Development:** `http://localhost:8000`
- **Interactive Swagger UI:** `http://localhost:8000/api/docs`
- **OpenAPI JSON Schema:** `http://localhost:8000/api/openapi.json`

### 1.2. Request Headers
Protected endpoints accept a JWT Bearer token in the `Authorization` header:
```http
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
Accept: application/json
```

### 1.3. Two-Role Identity Model (Parent vs. Student)
- **Parent Token:** Minted via `POST /api/auth/login/email`, `POST /api/auth/login/phone`, or `POST /api/auth/login/google`. Used for onboarding, child creation, payment subscriptions, and parent analytics (`/api/hermes/parent/*`, `/api/parent/*`). When calling shared Hermes endpoints as a parent, pass `?child_id=<child_id>`.
- **Student (Child) Token:** Minted via `POST /api/auth/login/child`. Used for the student portal (`/api/hermes/chat`, `/api/cpyqb/*`, `/api/custom-test/*`, `/api/rfc/*`, `/api/notebook/*`, `/api/targets/*`, `/api/ai-hub/*`).
- **Development / Query Param Override:** All MARKS & SATHEE endpoints (`/api/cpyqb/*`, `/api/custom-test/*`, `/api/rfc/*`, `/api/notebook/*`, `/api/assignment/*`, `/api/targets/*`, `/api/leaderboard/*`, `/api/neet/*`) also accept an optional `?student_id=<id>` query parameter for convenient frontend development and testing.

---

## 2. Domain 1: Health & System Metadata

### 2.1. `GET /health`
- **Description:** Liveness check for load balancers and frontend connectivity banners.
- **Auth:** Public
- **Response (`200 OK`):**
```json
{
  "status": "healthy",
  "service": "mentor-ai-backend"
}
```

### 2.2. `GET /`
- **Description:** Returns API version, documentation links, and top-level route prefixes.
- **Auth:** Public
- **Response (`200 OK`):**
```json
{
  "name": "Mentor AI Backend API",
  "version": "1.0.0",
  "status": "running",
  "documentation": {
    "swagger": "/api/docs",
    "redoc": "/api/redoc"
  }
}
```

---

## 3. Domain 2: Authentication, Verification & Session Management

### 3.1. `POST /api/auth/register/simple`
- **Description:** Fast parent registration without email/SMS OTP blocker (recommended for web onboarding).
- **Auth:** Public
- **Request Body:**
```json
{
  "name": "Rajesh Sharma",
  "email_address": "rajesh@example.com",
  "password": "Password123!",
  "repeat_password": "Password123!",
  "mobile_number": "+919876543210"
}
```
- **Response (`201 Created`):**
```json
{
  "parent_id": "parent_8841a",
  "email": "rajesh@example.com",
  "phone": "+919876543210",
  "verification_required": false,
  "message": "Registration successful"
}
```

### 3.2. `POST /api/auth/register/parent/email`
- **Description:** Register parent account using email, password, and phone number.
- **Auth:** Public
- **Request Body:**
```json
{
  "name": "Rajesh Sharma",
  "email": "rajesh@example.com",
  "password": "Password123!",
  "phone": "+919876543210"
}
```
- **Response (`201 Created`):** Returns `parent_id`, `email`, and verification status.

### 3.3. `POST /api/auth/register/parent/phone` & `POST /api/auth/register/parent/google`
- **Description:** Register parent via phone number or Google OAuth `id_token`.
- **Request Body (`/google`):**
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

### 3.4. Email & Phone Verification Endpoints
- `POST /verify/email/send` — Body: `{"email": "rajesh@example.com"}`
- `POST /verify/email/confirm` — Body: `{"email": "rajesh@example.com", "code": "123456"}`
- `POST /verify/phone/send` — Body: `{"phone": "+919876543210"}`
- `POST /verify/phone/confirm` — Body: `{"phone": "+919876543210", "otp": "123456"}`

### 3.5. `POST /api/auth/login/email`
- **Description:** Authenticate parent with email & password.
- **Auth:** Public
- **Request Body:**
```json
{
  "email": "rajesh@example.com",
  "password": "Password123!"
}
```
- **Response (`200 OK`):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "parent_id": "parent_8841a",
  "email": "rajesh@example.com",
  "phone": "+919876543210",
  "expires_in": 86400
}
```

### 3.6. `POST /api/auth/login/phone` & `POST /api/auth/login/google`
- **Description:** Parent login using phone + OTP (`{"phone": "+919876543210", "otp": "123456"}`) or Google OAuth (`{"id_token": "..."}`).

### 3.7. `POST /api/auth/login/child`
- **Description:** Authenticate student/child with their username and password.
- **Auth:** Public
- **Request Body:**
```json
{
  "username": "aarav_jee2026",
  "password": "StudentPass123!"
}
```
- **Response (`200 OK`):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "student_id": "child_9920b",
  "username": "aarav_jee2026",
  "name": "Aarav Sharma",
  "is_student": true,
  "expires_in": 86400
}
```

### 3.8. Session & Profile Endpoints
- `GET /api/auth/me` — Get current parent profile (`Bearer <parent_token>`).
- `GET /api/auth/me/child` — Get current student profile (`Bearer <child_token>`).
- `POST /api/auth/token/refresh` — Body: `{"refresh_token": "..."}` -> Returns new `token`.
- `POST /api/auth/token/refresh/child` — Body: `{"refresh_token": "..."}` -> Returns new student `token`.
- `POST /api/auth/logout` & `POST /api/auth/logout/child` — Revokes active session.

---

## 4. Domain 3: Parent Onboarding, Child Profile & Exam Selection

### 4.1. `POST /api/onboarding/preferences` (`GET`, `PUT` also supported)
- **Query Params:** `parent_id` (required)
- **Request Body:**
```json
{
  "language": "en",
  "email_notifications": true,
  "sms_notifications": true,
  "push_notifications": true,
  "teaching_involvement": "high"
}
```
- **Allowed `language` values:** `"en"`, `"hi"`, `"mr"` (Hermes also supports `"hinglish"`, `"ta"`, `"te"`, `"bn"`, `"gu"`, `"kn"`, `"ml"`, `"pa"`, `"or"`).

### 4.2. `POST /api/onboarding/child`
- **Description:** Create the student profile under a parent account (1 child per parent).
- **Query Params:** `parent_id` (required)
- **Request Body:**
```json
{
  "name": "Aarav Sharma",
  "age": 17,
  "grade": 12,
  "current_level": "intermediate",
  "username": "aarav_jee2026",
  "password": "StudentPass123!"
}
```
- **Response (`201 Created`):**
```json
{
  "child_id": "child_9920b",
  "parent_id": "parent_8841a",
  "name": "Aarav Sharma",
  "age": 17,
  "grade": 12,
  "current_level": "intermediate",
  "username": "aarav_jee2026",
  "created_at": "2026-10-23T08:30:00Z",
  "updated_at": "2026-10-23T08:30:00Z"
}
```
- **Related Child Endpoints:**
  - `GET /api/onboarding/child?parent_id={parent_id}`
  - `PUT /api/onboarding/child/{child_id}?parent_id={parent_id}`
  - `DELETE /api/onboarding/child/{child_id}?parent_id={parent_id}`

### 4.3. `GET /api/onboarding/exams/available`
- **Description:** List supported competitive exams (`JEE_MAIN`, `JEE_ADVANCED`, `NEET`), dates, and subjects.
- **Response (`200 OK`):**
```json
{
  "exams": [
    {
      "exam_type": "JEE_MAIN",
      "exam_name": "JEE Main",
      "available_dates": ["2026-01-24T00:00:00Z", "2026-04-05T00:00:00Z"],
      "subjects": ["Physics", "Chemistry", "Mathematics"]
    }
  ]
}
```

### 4.4. `POST /api/onboarding/exam/select`
- **Description:** Select target exam and subject weightage preferences (must sum to 100).
- **Query Params:** `parent_id` (required), `child_id` (required)
- **Request Body:**
```json
{
  "exam_type": "JEE_MAIN",
  "exam_date": "2026-01-24T00:00:00Z",
  "subject_preferences": {
    "Physics": 35,
    "Chemistry": 30,
    "Mathematics": 35
  }
}
```
- **Response (`201 Created`):** Returns `child_id`, `exam_type`, `days_until_exam`, and `diagnostic_test_id`.
- **Related Endpoints:**
  - `GET /api/onboarding/exam/preferences?parent_id=...&child_id=...`
  - `PUT /api/onboarding/exam/preferences?parent_id=...&child_id=...`
  - `GET /api/onboarding/status?parent_id=...`

---

## 5. Domain 4: Hermes 1-to-1 Socratic AI Mentor & Micro-Topic State Machine

### 5.1. `POST /api/hermes/admin/seed-topics`
- **Description:** Idempotently seeds deterministic micro-topics from `data/syllabus/*.json`.
- **Auth:** `Bearer <token>`
- **Query Params:** `force` (optional bool, default `false`)
- **Response (`200 OK`):**
```json
{
  "already_seeded": false,
  "micro_topics_count": 42,
  "exams": ["JEE_ADVANCED", "JEE_MAIN"]
}
```

### 5.2. `POST /api/hermes/chat`
- **Description:** Chat with Hermes (1-to-1 Socratic mentor). Gives hints, formulas, and guiding questions—never raw final answers to numericals. Student token only (parents receive `403 Forbidden`).
- **Auth:** `Bearer <student_token>`
- **Request Body:**
```json
{
  "message": "A projectile is launched at 20 m/s at 45 degrees. How do I find its horizontal range?",
  "session_id": null,
  "micro_topic_id": "mt_48a19c02",
  "language": "en"
}
```
- **Response (`200 OK`):**
```json
{
  "session_id": "sess_99182a",
  "answer": "Let's break this down! Which kinematic equation relates horizontal velocity $u \\cos\\theta$ and time of flight $T$? Try writing $R = (u \\cos 45^\\circ) \\times T$ first!",
  "language": "en",
  "locked_topic": null,
  "tokens_used": 145,
  "daily_turns_used": 1,
  "daily_turns_cap": 50,
  "mock": false
}
```

### 5.3. Session History Endpoints
- `GET /api/hermes/sessions` — Lists student's mentor chat sessions.
- `GET /api/hermes/sessions/{session_id}/messages` — Returns ordered message history `[{"role": "student"|"hermes", "content": "...", "created_at": "..."}]`.
- `POST /api/hermes/sessions/{session_id}/end` — Ends session and compresses rolling tutor memory.

### 5.4. `POST /api/hermes/quiz/attempt`
- **Description:** Records a micro-topic quiz attempt and drives the deterministic state machine (`UNTOUCHED` $\to$ `LEARNING` $\to$ `MASTERED` on 2 consecutive passes $\ge 70\%$; locks **Concept Wall** on 3 consecutive failures).
- **Auth:** `Bearer <token>`
- **Request Body:**
```json
{
  "micro_topic_id": "mt_48a19c02",
  "score_pct": 80.0,
  "total_questions": 10
}
```
- **Response (`200 OK`):**
```json
{
  "micro_topic_id": "mt_48a19c02",
  "topic_name": "Motion in Plane",
  "previous_state": "UNTOUCHED",
  "new_state": "LEARNING",
  "passed": true,
  "consecutive_passes": 1,
  "consecutive_failures": 0,
  "concept_wall_locked": false,
  "events": []
}
```

### 5.5. `GET /api/hermes/topics` & `GET /api/hermes/progress`
- **`GET /api/hermes/topics`:** Returns all in-scope micro-topics with student's current state (`UNTOUCHED`, `LEARNING`, `MASTERED`) and `concept_wall_locked`.
- **`GET /api/hermes/progress`:** Returns overall syllabus completion percentage, counts by state, subject breakdown, and active `concept_walls`.

### 5.6. Daily Summaries, Student Home, Gamification & Parent Insights
- `POST /api/hermes/summary/generate/{child_id}?date=YYYY-MM-DD` — Generates idempotent daily summary in parent's preferred language.
- `GET /api/hermes/summary/{child_id}?date=YYYY-MM-DD&audience=student|parent` — Retrieves generated summary.
- `GET /api/hermes/today` — Student home widget: exam countdown, today's suggested micro-topics, active Concept Wall, streak, XP, and daily chat cap usage.
- `GET /api/hermes/gamification` — Returns `xp`, `streak_days`, `badges` (`first_steps`, `quiz_10_passed`, `first_mastered`, `wall_breaker`, `streak_7`, `streak_30`), and lifetime `counters`.
- `GET /api/hermes/score-prediction` — Predicts JEE/NEET marks out of 300 from weighted syllabus mastery (`predicted_total`, `total_low`, `total_high`, per-subject breakdown).
- `GET /api/hermes/parent/overview?child_id={child_id}` — Parent token required. Returns 7-day activity counters, syllabus progress, and `attention_flags` (`inactive_48h`, `streak_at_risk`, `concept_wall_active`).
- `GET /api/hermes/parent/weekly?child_id={child_id}&date=YYYY-MM-DD` — Parent token required. Returns 7-day per-day breakdown and narrative summary.

---

## 6. Domain 5: MARKS Chapter-wise PYQ Bank (CPYQB) & Practice Mode

### 6.1. `GET /api/cpyqb/exam/{exam_id}/subject/{subject_id}/chapter/{chapter_id}/topic/{topic_id}/questions`
- **Description:** Hierarchical PYQ listing with student attempt status (`unattempted`, `correct`, `incorrect`, `isStarred`), shift metadata, and NCERT page mappings.Pass `"all"` for any path segment to wildcard it, or use `GET /api/cpyqb/questions`.
- **Query Params:**
  - `offset` (int, default `0`)
  - `limit` (int, default `20`, max `100`)
  - `pyqFilter` (`"all"` | `"unattempted"` | `"incorrect"` | `"correct"` | `"starred"`)
  - `years` (comma-separated string, e.g. `"2024,2023"`)
  - `qType` (`"MCQ"` | `"NAT"`)
  - `difficulty` (`"easy"` | `"medium"` | `"hard"`)
  - `revisionZone` (`"high_yield"` | `"must_revise"` | `"trap_zone"`)
  - `student_id` (optional string)
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Questions loaded",
  "totalCount": 2,
  "questions": [
    {
      "id": "q_jee_2024_ph_01",
      "questionNumber": 1,
      "examId": "jee_main",
      "exam": "JEE Main",
      "subjectId": "physics",
      "subject": "Physics",
      "chapterId": "rotational_motion",
      "chapter": "Rotational Motion",
      "topicId": "moment_of_inertia",
      "topic": "Moment of Inertia & Rolling Motion",
      "year": 2024,
      "shift": "29 Jan Shift 1",
      "type": "MCQ",
      "difficulty": "medium",
      "revisionZone": "high_yield",
      "ncertPages": "Class 11, pp. 164-172",
      "statementHtml": "<p>A solid sphere of mass $M$ and radius $R$ rolls without slipping down an inclined plane of inclination $\\theta$. The acceleration of the center of mass of the sphere is:</p>",
      "options": [
        { "key": "A", "html": "<p>$\\frac{5}{7} g \\sin \\theta$</p>" },
        { "key": "B", "html": "<p>$\\frac{2}{5} g \\sin \\theta$</p>" },
        { "key": "C", "html": "<p>$\\frac{1}{2} g \\sin \\theta$</p>" },
        { "key": "D", "html": "<p>$\\frac{7}{10} g \\sin \\theta$</p>" }
      ],
      "hasVideoSolution": true,
      "videoContentId": "vdo_ph_rot_01",
      "userAttempt": {
        "status": "unattempted",
        "selectedOption": null,
        "numericalAnswer": null,
        "isStarred": false
      }
    }
  ]
}
```

### 6.2. `GET /api/cpyqb/questions`
- **Description:** Flexible query-parameter filter across the entire PYQ bank.
- **Query Params:** `examId`, `subjectId`, `chapterId`, `topicId`, `pyqFilter`, `years`, `qType`, `difficulty`, `revisionZone`, `offset`, `limit`, `student_id`.
- **Response (`200 OK`):** Same `PYQQuestionListResponse` envelope as 6.1.

### 6.3. `POST /api/solving-modes/practice/start`
- **Description:** Submits a single question attempt in Practice Mode. Immediately grades MCQ (`selectedOption`) or NAT (`numericalAnswer` within decimal tolerance), awards gamification points, increments today's activity heatmap, and **automatically logs wrong attempts into the student's Error Notebook**.
- **Query Params:** `student_id` (optional)
- **Request Body:**
```json
{
  "questionId": "q_jee_2024_ph_01",
  "selectedOption": "A",
  "numericalAnswer": null,
  "timeSpentSeconds": 65,
  "mistakeTag": "formula_mixup"
}
```
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Answer verified",
  "questionId": "q_jee_2024_ph_01",
  "isCorrect": true,
  "correctOption": "A",
  "correctNumericalAnswer": null,
  "marksAwarded": 4,
  "solutionHtml": "<p>For a body rolling without slipping down an incline...</p>",
  "userPointsEarned": 5,
  "loggedToErrorNotebook": false,
  "errorId": null
}
```

---

## 7. Domain 6: MARKS Multi-Step Custom Test Generator (CTG) & CBT Engine

### 7.1. `GET /api/custom-test/build/step1`
- **Description:** Step 1 of the Custom Test builder wizard—returns exams and available question counts per subject.
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "exams": [
    {
      "id": "jee_main",
      "name": "JEE Main",
      "subjects": [
        { "id": "physics", "name": "Physics", "availableQuestions": 3 },
        { "id": "chemistry", "name": "Chemistry", "availableQuestions": 1 },
        { "id": "mathematics", "name": "Mathematics", "availableQuestions": 1 }
      ]
    }
  ]
}
```

### 7.2. `POST /api/custom-test/build/step2`
- **Description:** Step 2 of the Custom Test builder—returns chapters for the selected subjects and suggested durations in minutes.
- **Request Body:**
```json
{
  "examId": "jee_main",
  "subjectIds": ["physics", "mathematics"]
}
```
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "chapters": [
    { "id": "rotational_motion", "name": "Rotational Motion", "subject": "physics", "totalQuestions": 2 },
    { "id": "electrostatics", "name": "Electrostatics", "subject": "physics", "totalQuestions": 1 },
    { "id": "definite_integration", "name": "Definite Integration", "subject": "mathematics", "totalQuestions": 1 }
  ],
  "suggestedTimeDurations": [30, 45, 60, 90, 180]
}
```

### 7.3. `POST /api/custom-test/generate`
- **Description:** Synthesizes a timed NTA CBT custom test according to chapter question allocations.
- **Request Body:**
```json
{
  "examId": "jee_main",
  "title": "Rotational Motion & Calculus Drill",
  "subjectIds": ["physics", "mathematics"],
  "chapterAllocations": [
    { "chapterId": "rotational_motion", "questionCount": 2 },
    { "chapterId": "definite_integration", "questionCount": 1 }
  ],
  "durationMinutes": 45,
  "difficulty": "mixed"
}
```
- **Response (`201 Created`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Custom test synthesized",
  "testId": "ct_91a8b20c",
  "title": "Rotational Motion & Calculus Drill",
  "examId": "jee_main",
  "durationMinutes": 45,
  "totalQuestions": 3,
  "totalMarks": 12,
  "questions": [ /* Array of PYQQuestionItem */ ]
}
```

### 7.4. `POST /api/custom-test/submit`
- **Description:** Grades a completed CBT Custom Test, calculates negative marks, accuracy, percentile, subject breakdown, and weak/strong topics, and populates the Error Notebook.
- **Request Body:**
```json
{
  "testId": "ct_91a8b20c",
  "timeTakenSeconds": 1820,
  "responses": [
    {
      "questionId": "q_jee_2024_ph_01",
      "selectedOption": "A",
      "numericalValue": null,
      "status": "answered",
      "timeTaken": 75
    },
    {
      "questionId": "q_jee_2024_ph_02",
      "selectedOption": null,
      "numericalValue": 36.0,
      "status": "answered",
      "timeTaken": 110
    }
  ]
}
```
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Custom test graded",
  "attemptId": "att_7c81920e",
  "testId": "ct_91a8b20c",
  "totalMarks": 12,
  "score": 8,
  "totalQuestions": 3,
  "attempted": 2,
  "correct": 2,
  "incorrect": 0,
  "unattempted": 1,
  "accuracy": 100.0,
  "percentile": 81.33,
  "subjectBreakdown": {
    "Physics": { "marks": 8, "correct": 2, "incorrect": 0, "unattempted": 0 },
    "Mathematics": { "marks": 0, "correct": 0, "incorrect": 0, "unattempted": 1 }
  },
  "weakTopics": [],
  "strongTopics": [
    { "subject": "Physics", "topic": "Moment of Inertia & Rolling Motion", "accuracy": 1.0 }
  ]
}
```

### 7.5. `GET /api/custom-test/analysis/{test_id}`
- **Description:** Returns the full post-test diagnostic report card including topper comparison, speed metrics, and question-by-question solutions.
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "data": {
    "attemptId": "att_7c81920e",
    "testId": "ct_91a8b20c",
    "testTitle": "Rotational Motion & Calculus Drill",
    "studentScore": 8,
    "totalMarks": 12,
    "topperScore": 11,
    "averageScore": 5,
    "accuracy": 100.0,
    "percentile": 81.33,
    "speedMetrics": {
      "averageTimePerQuestionSeconds": 910.0,
      "topperAverageTimeSeconds": 65.0
    },
    "subjectBreakdown": {},
    "weakTopics": [],
    "strongTopics": [],
    "questionDetails": []
  }
}
```

---

## 8. Domain 7: MARKS Revision Flash Cards (RFC) & Formula Cards

### 8.1. `GET /api/rfc/subject/{subject_id}/chapter/{chapter_id}/cards`
- **Description:** Fetches interactive concept & LaTeX formula flashcards for a subject/chapter (`subject_id`: `physics`, `chemistry`, `mathematics`, or `all`; `chapter_id`: e.g. `electrostatics`, `rotational_motion`, or `all`).
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "subjectId": "physics",
  "chapterId": "electrostatics",
  "totalCards": 1,
  "masteredCount": 0,
  "needsRevisionCount": 0,
  "cards": [
    {
      "cardId": "gauss_law",
      "subjectId": "physics",
      "chapterId": "electrostatics",
      "chapterName": "Electrostatics",
      "topicName": "Electric Flux & Gauss's Law",
      "title": "Gauss's Law & Electric Flux",
      "frontText": "What is the net electric flux through any closed Gaussian surface?",
      "backFormulaHtml": "<p>$$\\oint \\vec{E} \\cdot d\\vec{A} = \\frac{q_{\\text{enclosed}}}{\\varepsilon_0}$$</p>",
      "keyTakeaways": [
        "Net flux is independent of the shape or size of the closed Gaussian surface.",
        "Charges outside the Gaussian surface contribute zero net flux."
      ],
      "userMasteryLevel": "unseen"
    }
  ]
}
```

### 8.2. `GET /api/rfc/subject/{subject_id}/chapter/{chapter_id}/card/{card_id}`
- **Description:** Fetches a single flashcard by `card_id`.

### 8.3. `POST /api/rfc/mastery`
- **Description:** Updates student's mastery state on a flashcard (`"mastered"` or `"needs_revision"`).
- **Request Body:**
```json
{
  "cardId": "gauss_law",
  "masteryLevel": "mastered"
}
```
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Card mastery updated",
  "data": {
    "cardId": "gauss_law",
    "userMasteryLevel": "mastered"
  }
}
```

---

## 9. Domain 8: MARKS Smart Notebooks, Bookmarking & Automated Error Notebook

### 9.1. `POST /api/notebook`
- **Description:** Creates a custom named Smart Notebook with a color tag.
- **Request Body:**
```json
{
  "title": "Rotational Motion Traps",
  "colorHex": "#FF5722",
  "subjectId": "physics"
}
```
- **Response (`201 Created`):**
```json
{
  "notebookId": "nb_41a9c812",
  "title": "Rotational Motion Traps",
  "colorHex": "#FF5722",
  "subjectId": "physics",
  "questionCount": 0,
  "isPinned": false,
  "isArchived": false,
  "createdAt": "2026-10-23T08:40:00Z"
}
```

### 9.2. `GET /api/notebook/smart`
- **Description:** Lists all custom Smart Notebooks for the student (pinned notebooks first).
- **Query Params:** `includeArchived` (bool, default `false`), `student_id` (optional).

### 9.3. `PATCH /api/notebook/{notebook_id}`
- **Description:** Pin, archive, recolor, or rename a Smart Notebook.
- **Request Body:**
```json
{
  "title": "High-Yield Rotation Problems",
  "isPinned": true,
  "isArchived": false
}
```

### 9.4. `POST /api/notebook/question`
- **Description:** Bookmarks a question into one or more Smart Notebooks with an optional personal note, and automatically marks `isStarred = true` in the PYQ Bank.
- **Request Body:**
```json
{
  "questionId": "q_jee_2024_ph_01",
  "notebookIds": ["nb_41a9c812"],
  "studentNote": "Remember to use parallel axis theorem before torque balance!"
}
```

### 9.5. `GET /api/notebook/{notebook_id}/questions`
- **Description:** Lists all bookmarked questions and personal student notes inside a specific notebook.

### 9.6. `GET /api/notebook/errors`
- **Description:** Retrieves the student's **Automated Error Notebook** populated whenever a student answers a question incorrectly in Practice Mode, Custom Tests, or Homework Assignments.
- **Query Params:**
  - `subject` (optional: `"Physics"`, `"Chemistry"`, `"Mathematics"`, `"Biology"`)
  - `status` (`"unresolved"` | `"mastered"` | `"all"`, default `"unresolved"`)
  - `mistakeType` (optional: `"formula_mixup"` | `"calculation"` | `"conceptual"` | `"silly"`)
  - `page` (int, default `1`), `limit` (int, default `20`)
- **Response (`200 OK`):**
```json
{
  "success": true,
  "status": 200,
  "totalCount": 1,
  "page": 1,
  "items": [
    {
      "errorId": "err_9018ab12",
      "questionId": "q_jee_2023_ph_03",
      "testName": "CPYQB Practice Mode",
      "subject": "Physics",
      "chapter": "Electrostatics",
      "topic": "Electric Flux & Gauss's Law",
      "questionText": "<p>A charge $q$ is placed at the center of the line joining two equal charges $Q$...</p>",
      "studentSelectedOption": "D",
      "correctOption": "B",
      "solutionText": "<p>For equilibrium of extreme charge $Q$, net force must be zero...</p>",
      "mistakeType": "conceptual",
      "attemptCount": 1,
      "isMastered": false,
      "createdAt": "2026-10-23T08:42:00Z"
    }
  ]
}
```

### 9.7. `POST /api/notebook/errors/{error_id}/resolve`
- **Description:** Marks an Error Notebook item as mastered (`isMastered = true`) and awards `+10` weekly league points.

---

## 10. Domain 9: MARKS Teacher / Parent Homework Assignments & Classroom Analytics

### 10.1. `POST /api/assignment/teacher/create`
- **Description:** Creates a timed homework assignment from selected PYQ question IDs and generates a 6-character alphanumeric `joinCode` and shareable deep link.
- **Request Body:**
```json
{
  "title": "Weekly Electrostatics & Rotation Drill",
  "subjectId": "physics",
  "questionIds": ["q_jee_2024_ph_01", "q_jee_2023_ph_03"],
  "dueDate": "2026-10-30T23:59:59Z",
  "timeLimitMinutes": 30
}
```
- **Response (`201 Created`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Assignment created",
  "assignmentId": "as_5519a01b",
  "joinCode": "6X9A21",
  "shareUrl": "https://link.getmarks.app/assignment/student?code=6X9A21",
  "title": "Weekly Electrostatics & Rotation Drill",
  "questionCount": 2,
  "timeLimitMinutes": 30,
  "dueDate": "2026-10-30T23:59:59Z"
}
```

### 10.2. `GET /api/assignment/student/id/{identifier}`
- **Description:** Fetches assignment metadata and question list. `{identifier}` can be either the `assignmentId` (`as_5519a01b`) OR the 6-character `joinCode` (`6X9A21`).

### 10.3. `POST /api/assignment/student/id/{identifier}/submit`
- **Description:** Submits a student's homework attempt, grades responses, and returns their live classroom rank.
- **Request Body:**
```json
{
  "timeTakenSeconds": 420,
  "responses": [
    { "questionId": "q_jee_2024_ph_01", "selectedOption": "A", "timeTaken": 200 },
    { "questionId": "q_jee_2023_ph_03", "selectedOption": "B", "timeTaken": 220 }
  ]
}
```
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "message": "Assignment submitted and graded",
  "data": {
    "submissionId": "sub_118a902f",
    "studentId": "stu_01",
    "score": 8,
    "totalMarks": 8,
    "correct": 2,
    "incorrect": 0,
    "timeTakenSeconds": 420,
    "rank": 1,
    "totalStudents": 1
  }
}
```

### 10.4. `GET /api/assignment/student/id/{identifier}/analysis`
- **Description:** Returns teacher/parent classroom analytics including average score, highest score, question-level error rates (sorted by hardest questions first), and student leaderboard.
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "assignmentId": "as_5519a01b",
  "title": "Weekly Electrostatics & Rotation Drill",
  "joinCode": "6X9A21",
  "totalSubmissions": 2,
  "averageScore": 5.5,
  "highestScore": 8,
  "averageTimeSeconds": 130.0,
  "questionErrorRates": [
    {
      "questionId": "q_jee_2023_ph_03",
      "topic": "Electric Flux & Gauss's Law",
      "errorRatePercentage": 50.0,
      "incorrectOrSkippedCount": 1
    }
  ],
  "leaderboard": [
    { "rank": 1, "studentId": "stu_hw_01", "score": 8, "totalMarks": 8, "timeTakenSeconds": 110 }
  ]
}
```

---

## 11. Domain 10: MARKS Daily Goals, Activity Heatmap, Daily Dose & Weekly Leagues

### 11.1. `POST /api/targets/update`
- **Description:** Sets the student's daily question-solving goal (5 to 200 questions/day).
- **Request Body:**
```json
{
  "dailyTargetQuestions": 30
}
```

### 11.2. `GET /api/targets/heatmap`
- **Description:** Returns a GitHub-style monthly consistency heatmap showing questions solved per day, whether the daily goal was met, current streak, and longest streak.
- **Query Params:** `month` (`YYYY-MM`, e.g. `"2026-10"`), `student_id` (optional).
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "month": "2026-10",
  "dailyTargetQuestions": 30,
  "days": [
    { "date": "2026-10-01", "solvedCount": 35, "targetMet": true },
    { "date": "2026-10-02", "solvedCount": 12, "targetMet": false }
  ],
  "longestStreak": 8,
  "currentStreak": 4,
  "totalSolvedInMonth": 240
}
```

### 11.3. `GET /api/targets/daily-dose` & `POST /api/targets/daily-dose/submit`
- **`GET /api/targets/daily-dose?examId=jee_main`:** Returns today's 5-question rapid sprint quiz.
- **`POST /api/targets/daily-dose/submit`:**
  - **Request Body:**
```json
{
  "date": "2026-10-23",
  "responses": [
    { "questionId": "q_jee_2024_ph_01", "selectedOption": "A" }
  ]
}
```
  - **Response (`200 OK`):** Returns `correct`, `incorrect`, `pointsEarned` (`15 * correct + 25` bonus), and `weeklyPointsTotal`.

### 11.4. `GET /api/leaderboard/achievements`
- **Description:** Returns the student's weekly League tier (`Bronze` < 200, `Silver` 200–499, `Gold` 500–899, `Diamond` 900–1499, `Master` $\ge 1500$), rank, and top rankers.
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "currentLeague": "Gold",
  "userRank": 3,
  "totalCompetitors": 50,
  "weeklyPoints": 540,
  "nextLeagueThreshold": 900,
  "topRankers": [
    { "rank": 1, "name": "Aman Verma", "points": 920, "avatar": "av_04" },
    { "rank": 2, "name": "Priya Singh", "points": 880, "avatar": "av_08" },
    { "rank": 3, "name": "You", "studentId": "student_default_01", "points": 540, "avatar": "av_01" }
  ]
}
```

---

## 12. Domain 11: Medical / NEET NCERT Line-by-Line Modules & Revision Zones

### 12.1. `GET /api/neet/ncert/subject/{subject_id}/modules`
- **Description:** Returns NCERT page-mapped chapter modules for `biology`, `chemistry`, `physics`, or `all`, along with question counts in High Yield, Must Revise, and Trap Zones.
- **Response (`200 OK`):**
```json
{
  "status": true,
  "code": 200,
  "subjectId": "biology",
  "modules": [
    {
      "moduleId": "ncert_bio_01",
      "subjectId": "biology",
      "book": "Class 11 Biology",
      "chapterId": "cell_unit_of_life",
      "chapterName": "Cell: The Unit of Life",
      "ncertPages": "125-144",
      "totalQuestions": 120,
      "completedQuestions": 1,
      "highYieldCount": 45,
      "mustReviseCount": 50,
      "trapZoneCount": 25
    }
  ]
}
```

---

## 13. Domain 12: SATHEE AI Hub — Vision OCR, SSE Streaming Doubt Solver, Similar Questions, OMR Grader, Rank Predictor & College Cutoffs

### 13.1. `POST /api/ai-hub/vision/ocr`
- **Description:** Extracts mathematical formulas, LaTeX markup, and printed/handwritten question text from an uploaded image, and auto-detects the subject (`Physics`, `Chemistry`, `Mathematics`, `Biology`).
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `image`: File upload (JPEG/PNG/WebP, optional if `textHint` is provided)
  - `detectMath`: `"true"` | `"false"` (default `"true"`)
  - `language`: `"en"` | `"hi"` (default `"en"`)
  - `textHint`: Optional string override for testing
- **Response (`200 OK`):**
```json
{
  "success": true,
  "status": 200,
  "message": "OCR text extraction completed.",
  "ocrText": "A particle of mass $m$ is moving in a circle of radius $r$ under the influence of a centripetal force $F = -\\frac{k}{r^2}$. Calculate the total mechanical energy of the particle.",
  "confidence": 0.982,
  "hasEquations": true,
  "detectedSubject": "Physics",
  "boundingBoxes": [
    { "text": "A particle of mass $m$ is moving in a circle of radius $r$", "box": [12, 14, 280, 45] }
  ]
}
```

### 13.2. `POST /api/ai-hub/chat/stream`
- **Description:** Streams step-by-step Socratic doubt explanations using **Server-Sent Events (`text/event-stream`)** across 3 reasoning stages (`analyzing` $\to$ `reasoning` $\to$ `solution` $\to$ `[DONE]`).
- **Request Body:**
```json
{
  "query": "A particle of mass $m$ moves in a circle of radius $r$ under centripetal force $F = -k/r^2$. Find total mechanical energy.",
  "subject": "Physics",
  "exam": "jee",
  "language": "en",
  "conversationId": null,
  "mode": "step_by_step"
}
```
- **Response Stream (`200 OK`, `Content-Type: text/event-stream`):**
```text
data: {"id": "msg_a1b2c3", "stage": "analyzing", "delta": "### Concept Analysis (Physics)\nLet's break down the key physical and mathematical principles...\n"}

data: {"id": "msg_a1b2c3", "stage": "reasoning", "delta": "First, identify the governing relation and conserved quantities:\n$$F_{\\text{net}} = \\frac{m v^2}{r} \\implies K = \\frac{1}{2} m v^2$$\n"}

data: {"id": "msg_a1b2c3", "stage": "reasoning", "delta": "Next, relate potential energy $U(r)$ to the conservative force field:\n$$U(r) = -\\int F(r)\\,dr$$\n"}

data: {"id": "msg_a1b2c3", "stage": "solution", "delta": "Therefore, combining kinetic and potential energy gives the total mechanical energy:\n$$E = K + U = \\frac{k}{2r} - \\frac{k}{r} = -\\frac{k}{2r}$$\n"}

data: [DONE]
```

### 13.3. `POST /api/ai-hub/qa/generate-similar-questions`
- **Description:** Synthesizes isomorphic practice problems testing the exact same concept as a question the student struggled with, using altered numerical values.
- **Request Body:**
```json
{
  "questionText": "Find the equivalent resistance across terminals A and B of an infinite ladder network of 1 ohm resistors.",
  "subject": "Physics",
  "topic": "Current Electricity",
  "difficulty": "medium",
  "count": 3
}
```
- **Response (`200 OK`):**
```json
{
  "success": true,
  "status": 200,
  "message": "Similar questions generated successfully.",
  "questions": [
    {
      "id": "gen_q_01",
      "questionText": "[Physics - Current Electricity Variant 1] In an infinite ladder network of capacitors, each capacitor in the series arm has capacitance $2\\,\\mu\\text{F}$ and in the shunt arm has $4\\,\\mu\\text{F}$. Find the equivalent capacitance across the input terminals.",
      "options": [
        { "key": "A", "text": "$2\\,\\mu\\text{F}$" },
        { "key": "B", "text": "$4\\,\\mu\\text{F}$" },
        { "key": "C", "text": "$\\sqrt{12}\\,\\mu\\text{F}$" },
        { "key": "D", "text": "$1.5\\,\\mu\\text{F}$" }
      ],
      "correctOption": "A",
      "explanation": "Let the equivalent capacitance of the infinite ladder be $C_{\\text{eq}}$..."
    }
  ]
}
```

### 13.4. `POST /api/ai-hub/rank/predict`
- **Description:** Predicts All India Rank (AIR), percentile, category rank (`General`, `OBC-NCL`, `SC`, `ST`, `EWS`), and 2-year historical trend from raw marks and shift difficulty.
- **Request Body:**
```json
{
  "exam": "jee_main",
  "rawMarks": 215,
  "maxMarks": 300,
  "category": "OBC-NCL",
  "state": "Uttar Pradesh",
  "shiftDifficulty": "moderate",
  "session": "session_1"
}
```
- **Response (`200 OK`):**
```json
{
  "success": true,
  "status": 200,
  "message": "Rank prediction successful.",
  "exam": "jee_main",
  "predictedPercentile": 96.46,
  "predictedAIR": 44250,
  "airRange": { "min": 40710, "max": 47790 },
  "category": "OBC-NCL",
  "categoryRank": 10178,
  "confidenceScore": 0.94,
  "historicalTrend": [
    { "year": 2025, "marks": 215.0, "percentile": 96.39 },
    { "year": 2024, "marks": 215.0, "percentile": 96.55 }
  ]
}
```

### 13.5. `GET /api/ai-hub/colleges/cutoffs`
- **Description:** Queries IIT, NIT, and AIIMS college details, NIRF rankings, and multi-year category-wise branch cutoffs. Pass `studentAir` to automatically compute `isEligible: true|false` for every branch!
- **Query Params:**
  - `collegeId` (optional: `"iit_bombay"`, `"iit_kanpur"`, `"nit_trichy"`, `"aiims_delhi"`)
  - `exam` (optional: `"jee_advanced"`, `"jee_main"`, `"neet"`)
  - `category` (`"General"` | `"OBC-NCL"` | `"SC"` | `"ST"` | `"EWS"`, default `"General"`)
  - `studentAir` (optional int, e.g. `120`)
- **Response (`200 OK`):**
```json
{
  "success": true,
  "status": 200,
  "message": "College details retrieved.",
  "data": {
    "id": "iit_bombay",
    "name": "Indian Institute of Technology Bombay",
    "exam": "jee_advanced",
    "nirfRank": 3,
    "state": "Maharashtra",
    "city": "Mumbai",
    "branches": [
      {
        "branchCode": "CSE",
        "branchName": "Computer Science and Engineering",
        "seats": 120,
        "cutoffs": {
          "2025": { "General": 68, "OBC-NCL": 145, "SC": 890, "ST": 420, "EWS": 210 }
        },
        "isEligible": false,
        "cutoffForCategory": 68
      },
      {
        "branchCode": "EE",
        "branchName": "Electrical Engineering",
        "seats": 110,
        "cutoffs": {
          "2025": { "General": 480, "OBC-NCL": 820, "SC": 2400, "ST": 1150, "EWS": 690 }
        },
        "isEligible": true,
        "cutoffForCategory": 480
      }
    ]
  }
}
```

### 13.6. `POST /api/ai-hub/omr/evaluate`
- **Description:** Evaluates an uploaded physical OMR bubble sheet image (or scanned answer JSON) against a template answer key (`jee_main_paper1_2026`, `jee_advanced_paper1_2026`, `neet_ug_2026`).
- **Content-Type:** `multipart/form-data`
- **Form Fields:**
  - `omrImage`: Optional image file
  - `templateId`: `"jee_advanced_paper1_2026"` (default)
  - `rollNumber`: `"1029481"`
  - `scannedAnswersJson`: Optional JSON string e.g. `'{"1": "A", "2": "C", "3": "B"}'`
- **Response (`200 OK`):**
```json
{
  "success": true,
  "status": 200,
  "message": "OMR processed successfully.",
  "templateId": "jee_advanced_paper1_2026",
  "detectedRollNumber": "1029481",
  "confidenceScore": 0.991,
  "totalBubblesDetected": 180,
  "totalAttempted": 8,
  "correctCount": 7,
  "incorrectCount": 1,
  "marksCalculated": 27,
  "maxMarks": 40,
  "scannedAnswers": { "1": "A", "2": "C", "3": "B" }
}
```

---

## 14. Domain 13: Study Center & AI Learning Journey

- `GET /api/study-center/topics?student_id={id}&subject={opt}` — Lists syllabus topics with student progress percentage.
- `GET /api/study-center/topics/{topic_id}` — Detailed topic metadata.
- `GET /api/study-center/materials/{topic_id}` — Returns AI-generated revision notes (Markdown), mind map structure, and teaching examples.
- `POST /api/study-center/materials/generate` — Body: `{"student_id": "...", "topic_id": "...", "material_type": "all"}`.
- `GET /api/study-center/mindmap/{topic_id}` — Mind map nodes & edges for visual rendering.
- `GET /api/study-center/teach/{topic_id}` — Step-by-step concept teaching content.
- `POST /api/study-center/progress/start` — Body: `{"student_id": "...", "topic_id": "...", "topic_name": "...", "subject": "..."}`.
- `POST /api/study-center/progress/complete` — Body: `{"student_id": "...", "topic_id": "...", "session_id": "..."}`.
- `GET /api/study-center/progress/{student_id}` — Overall study hours and topic completion counts.
- `GET /api/study-center/journey/{student_id}` — Next recommended topics in learning sequence.
- `GET /api/study-center/parent-progress/{child_id}` — Parent summary of child's Study Center progress.

---

## 15. Domain 14: Diagnostic Tests & Test Lifecycle Management

- `POST /api/diagnostic-test/generate` — Generate a full-length 200-question diagnostic test synchronously.
- `POST /api/diagnostic-test/generate-async` — Enqueue background test generation; poll via `GET /api/diagnostic-test/generation/status/{job_id}`.
- `POST /api/diagnostic-test/schedule` — Body: `{"child_id": "...", "exam_type": "JEE_MAIN", "scheduled_date": "2026-10-25T10:00:00Z", "test_id": "..."}`.
- `GET /api/diagnostic-test/{test_id}` — Fetch full test with sections and questions.
- `GET /api/diagnostic-test/{test_id}/metadata` — Fetch test metadata without questions.
- `GET /api/diagnostic-test/student/{student_id}` — List all diagnostic tests for a student.
- `POST /api/diagnostic-test/{test_id}/start` — Body: `{"student_id": "..."}`.
- `POST /api/diagnostic-test/{test_id}/submit` — Body: `{"test_id": "...", "student_id": "...", "answers": {"1": "A"}, "time_taken": 3600, "submission_time": "..."}`.
- `GET /api/diagnostic-test/{test_id}/results` — Detailed score report and section breakdown.
- `GET /api/diagnostic-test/{test_id}/status` — Current test status (`pending`, `in_progress`, `completed`, `expired`).

---

## 16. Domain 15: Adaptive Study Schedule & Progress Tracking

- `POST /api/schedule/generate` — Body: `{"student_id": "...", "analytics_id": "...", "exam_type": "JEE_MAIN", "exam_date": "2026-01-24", "daily_study_hours": 5}`.
- `GET /api/schedule/{schedule_id}` — Complete day-by-day study schedule.
- `GET /api/schedule/student/{student_id}` — Active schedule for a student.
- `GET /api/schedule/student/{student_id}/history` — Past schedules.
- `POST /api/schedule/{schedule_id}/regenerate` — Body: `{"current_day": 12}` — Re-plans remaining days adaptively.
- `POST /api/schedule/progress/update` — Body: `{"schedule_id": "...", "day_number": 1, "completion_percentage": 100, "topics_completed": ["T01"], "hours_studied": 4.5, "notes": "..."}`.
- `GET /api/schedule/progress/{schedule_id}` — Overall schedule completion, streak, and days ahead/behind.
- `GET /api/schedule/progress/today?schedule_id={id}` — Today's scheduled topics and tasks.

---

## 17. Domain 16: Vector Search, Embeddings, RAG Question Generation & Syllabus Coverage

- `POST /api/vector-search/query` — Body: `{"query": "rotational kinetic energy", "top_k": 5, "filters": {"exam": "JEE_MAIN", "subject": "Physics"}}`.
- `GET /api/vector-search/syllabus/{exam}/{subject}` — Full structured JSON syllabus (`JEE_MAIN`, `JEE_ADVANCED`, `NEET`).
- `POST /api/rag/generate-questions` — Body: `{"topic": "Thermodynamics", "exam_type": "JEE_MAIN", "difficulty": "medium", "num_questions": 5, "include_explanations": true, "question_type": "single_correct"}`.
- `GET /api/syllabus/coverage/{student_id}` — Overall and subject-wise syllabus coverage percentages.
- `GET /api/syllabus/coverage/{student_id}/untested` — Topics not yet attempted.
- `GET /api/syllabus/coverage/{student_id}/weak` — Topics with accuracy below 60%.
- `GET /api/syllabus/coverage/{student_id}/recommendations` — Prioritized next topics to test.

---

## 18. Domain 17: Parent Dashboard, Student Dashboard, Legacy Gamification & Analytics

### Parent Portal (`/api/parent/*`)
- `GET /api/parent/dashboard/{child_id}` — Overview of child's study hours, test scores, and schedule status.
- `GET /api/parent/reports/weekly/{child_id}` — Weekly parent report.
- `POST /api/parent/goals/{child_id}` & `GET /api/parent/goals/{child_id}` — Parent-defined target goals for the child.

### Student Portal (`/api/student/*`)
- `GET /api/student/today/{student_id}` — Today's study plan and motivational quote.
- `POST /api/student/practice/quick` — Quick practice generator.
- `POST /api/student/doubts` & `GET /api/student/doubts/{doubt_id}/explanation` — Doubt logging.
- `GET /api/student/revision/due?student_id={id}` — Spaced-repetition topics due for revision.
- `GET /api/student/insights/{student_id}` & `GET /api/student/compare/percentile?student_id={id}` — Performance insights and peer percentile comparison.

### Analytics & AI Insights (`/api/analytics/*`, `/api/ai/*`)
- `POST /api/analytics/generate` & `GET /api/analytics/{analytics_id}` — Deep test analytics generation.
- `GET /api/ai/readiness/{student_id}` — Exam readiness score, rank range, and topic gaps.
- `GET /api/ai/analysis/mistakes/{student_id}` — Mistake pattern breakdown (`calculation`, `conceptual`, `silly`).

---

## 19. Domain 18: Subscriptions & Razorpay Payments

- `GET /api/payment/plans` — Lists subscription tiers (`free`, `premium_monthly`, `premium_yearly`) with pricing in INR and feature entitlements.
- `POST /api/payment/create-order` — Body: `{"parent_id": "...", "plan_id": "premium_monthly"}` -> Returns Razorpay `order_id`, `amount`, `currency`.
- `POST /api/payment/verify` — Body: `{"order_id": "...", "payment_id": "...", "razorpay_signature": "..."}` -> Verifies signature and unlocks premium entitlements.
- `GET /api/payment/subscription/{parent_id}` — Active subscription status and `days_remaining`.
- `GET /api/payment/transactions/{parent_id}` — Payment transaction history.
- `POST /api/payment/cancel/{parent_id}` — Cancels active subscription.

---

## 20. Recommended Web Application Architecture & User Flows for AI Agents

When building the frontend web application against this backend, implement two role-based portals sharing a unified design system (with KaTeX / MathJax enabled globally for rendering `$...$` and `$$...$$` LaTeX formulas):

1. **Parent Portal (`/parent/*`):**
   - **Auth & Onboarding Wizard:** `POST /api/auth/register/simple` $\to$ `POST /api/auth/login/email` $\to$ `POST /api/onboarding/preferences` $\to$ `POST /api/onboarding/child` $\to$ `POST /api/onboarding/exam/select`.
   - **Parent Command Center:** Consumes `GET /api/hermes/parent/overview`, `GET /api/hermes/parent/weekly`, and `GET /api/hermes/summary/{child_id}?audience=parent` to show 7-day consistency, Concept Wall alerts, and localized daily summaries.
   - **Homework Assignment Creator:** Uses `POST /api/assignment/teacher/create` and `GET /api/assignment/student/id/{code}/analysis` so parents or mentors can assign custom PYQ drills and inspect question error rates.
   - **Subscription & Billing:** Uses `GET /api/payment/plans` and `POST /api/payment/create-order`.

2. **Student Portal (`/student/*`):**
   - **Student Login & Home Dashboard:** `POST /api/auth/login/child` $\to$ `GET /api/hermes/today`, `GET /api/targets/heatmap`, `GET /api/leaderboard/achievements`, and `GET /api/targets/daily-dose`.
   - **1-to-1 Socratic AI Mentor (Hermes):** Chat UI powered by `POST /api/hermes/chat` (and `POST /api/ai-hub/chat/stream` for real-time SSE streaming + `POST /api/ai-hub/vision/ocr` for uploading photos of handwritten/printed doubts).
   - **Chapter-wise PYQ Bank (CPYQB):** Hierarchical browser (`GET /api/cpyqb/questions`) with filters for Year, Shift, MCQ/NAT, Revision Zone (`high_yield`, `must_revise`, `trap_zone`), and instant Practice Mode checking (`POST /api/solving-modes/practice/start`).
   - **NTA CBT Custom Test Arena:** 2-step wizard (`GET /api/custom-test/build/step1` $\to$ `POST /api/custom-test/build/step2` $\to$ `POST /api/custom-test/generate`) leading into a fullscreen NTA CBT exam interface (`POST /api/custom-test/submit` $\to$ `GET /api/custom-test/analysis/{test_id}`).
   - **Smart Notebooks & Automated Error Notebook:** Tabbed view of custom bookmarked notebooks (`GET /api/notebook/smart`) and auto-captured test/practice mistakes (`GET /api/notebook/errors`), with a **"Practice Similar Questions"** button on every mistake wired to `POST /api/ai-hub/qa/generate-similar-questions`.
   - **Revision Flash Cards (RFC) & Formula Deck:** Interactive 3D flip cards (`GET /api/rfc/subject/{subject_id}/chapter/{chapter_id}/cards` & `POST /api/rfc/mastery`).
   - **Rank Predictor, College Cutoffs & Physical OMR Grader:** Interactive tools powered by `POST /api/ai-hub/rank/predict`, `GET /api/ai-hub/colleges/cutoffs`, and `POST /api/ai-hub/omr/evaluate`.
