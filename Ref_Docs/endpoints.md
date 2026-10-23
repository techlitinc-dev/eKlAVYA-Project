# API Endpoint Catalog & Data Contracts: Mentor AI (SATHEE Platform)

## 1. Global API Architecture & Standard Envelopes

### 1.1. Base URL Registry

The backend architecture distributes workloads across specialized regional domains and microservice hosts:

| Service Domain | Base URL / Host | Purpose / Responsibilities |
| :--- | :--- | :--- |
| **Authentication & Core JEE** | `https://sathee-jee.prutor.ai` | JEE question banks, mock tests, student profiles, syllabus. |
| **Core SSC & Recruitment** | `https://sathee-ssc.prutor.ai` | SSC, RRB, Banking mock tests, DPPs, and user performance. |
| **JEE Test Dedicated Host** | `https://jeetest.prutor.ai` | High-concurrency JEE Main CBT test delivery engine. |
| **NEET Test Dedicated Host** | `https://neettest.prutor.ai` | High-concurrency NEET-UG test delivery engine. |
| **Azure AI Cognitive Engine** | `https://azureapi.prutor.ai` | Computer vision OCR, ML rank prediction, question synthesis. |
| **RobustResults LLM Streaming** | `https://chatbot.robustresults.com` | High-throughput streaming Socratic AI doubt solver and chatbot. |
| **Video Token Signer** | `https://servervideo.prutor.ai` | Time-limited HMAC signed URL generation for video lectures. |
| **Encrypted Video Stream Edge** | `https://videob.prutor.digital` | CDN edge delivery for adaptive HLS/DASH video segments. |
| **Physical OMR Evaluation** | `https://omr.sathee.prutor.ai` | Computer vision physical OMR sheet scanning and grading. |
| **IITK KPI Analytics Engine** | `https://kpi.sathee.iitk.ac.in` | Elasticsearch-backed DPP performance and watch-time metrics. |
| **Firebase Cloud Functions** | `https://asia-south1-satheeqrcode.cloudfunctions.net` | SMS OTP, Custom token minting, WhatsApp, dynamic short links. |

---

### 1.2. Standard Request Headers

Except for public OTP endpoints, all backend API calls require standard authentication and client identification headers:

```http
Authorization: Bearer <firebase_id_token>
Content-Type: application/json
Accept: application/json
X-App-Version: 2.0.23
X-Platform: android
X-Device-Id: d8a9f3b1-7c2e-4b6a-912a-8ef0c192a34b
X-Exam-Type: jee
Accept-Language: en
```

---

### 1.3. Standard Response Envelope

All REST endpoints adhere to a standardized JSON response envelope:

```json
{
  "success": true,
  "status": 200,
  "message": "Operation executed successfully.",
  "data": {},
  "timestamp": "2026-10-22T08:00:00.000Z"
}
```

Standard Error Envelope:
```json
{
  "success": false,
  "status": 400,
  "message": "Detailed human-readable error description.",
  "errorCode": "INVALID_OTP_TOKEN",
  "data": null,
  "timestamp": "2026-10-22T08:00:00.000Z"
}
```

---

## 2. Authentication & Identity Microservices

### 2.1. Request Phone OTP (`sendSmartPingOtpHttp`)
Dispatches a 6-digit numeric verification code to the student's mobile number via SmartPing gateway.

- **URL:** `POST https://asia-south1-satheeqrcode.cloudfunctions.net/sendSmartPingOtpHttp`
- **Auth:** None (Public)
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "phone": "9876543210",
  "countryCode": "+91",
  "appSignature": "k8X2a91N"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "OTP dispatched successfully.",
  "data": {
    "requestId": "req_otp_9941a87b",
    "expiresInSeconds": 300,
    "resendCooldownSeconds": 45
  }
}
```

---

### 2.2. Verify OTP & Mint Custom Token (`firebaseCustomToken`)
Validates the entered SMS code and mints a Firebase custom authentication token.

- **URL:** `POST https://asia-south1-satheeqrcode.cloudfunctions.net/firebaseCustomToken`
- **Auth:** None (Public)
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "phone": "9876543210",
  "countryCode": "+91",
  "otp": "482910",
  "deviceInfo": {
    "model": "Pixel 7 Pro",
    "osVersion": "Android 14",
    "appVersion": "2.0.23"
  }
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Verification successful.",
  "data": {
    "customToken": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOiJ1c2VyXzk4NzY1NDMyMTAiLCJjbGFpbXMiOnsicm9sZSI6InN0dWRlbnQifX0...",
    "isNewUser": false,
    "userId": "user_9876543210"
  }
}
```

---

### 2.3. User Session Verification (`/google-auth/verify`)
Verifies the current Firebase ID token with the Prutor backend and initializes session permissions.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/verify`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "fcmToken": "eX81a_b9c2:APA91bF...d8a",
  "platform": "android"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Session valid.",
  "data": {
    "userId": "64d271f7b88914101df01020",
    "email": "student@sathee.ac.in",
    "phone": "9876543210",
    "name": "Rohan Sharma",
    "enrolledCourses": ["jee"],
    "role": "student",
    "preferredLanguage": "hi",
    "targetYear": 2026,
    "currentStreak": 12,
    "coinsBalance": 450
  }
}
```

---

### 2.4. Update Student Profile (`/google-auth/edit-student-profile`)
Updates student academic preferences, category reservation, school details, and target exam year.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/edit-student-profile`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "name": "Rohan Sharma",
  "category": "OBC-NCL",
  "gender": "male",
  "state": "Uttar Pradesh",
  "district": "Kanpur Nagar",
  "schoolUdise": "09340100101",
  "schoolName": "Kendriya Vidyalaya IIT Kanpur",
  "targetExam": "jee",
  "targetYear": 2026,
  "preferredLanguage": "hi"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Profile updated successfully.",
  "data": {
    "updatedAt": "2026-10-22T08:15:00.000Z"
  }
}
```

---

## 3. AI Hub & Cognitive Microservices

### 3.1. Handwritten & Equation OCR (`/vision/ocr`)
Extracts mathematical formulas, LaTeX markup, printed question statements, and diagram text from an uploaded image.

- **URL:** `POST https://azureapi.prutor.ai/vision/ocr`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: multipart/form-data`

#### Request (Multipart Form)
- `image`: Binary image file (JPEG / PNG / WebP, max 10MB)
- `detectMath`: `"true"` (Boolean string)
- `language`: `"en"` / `"hi"`

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "OCR text extraction completed.",
  "data": {
    "ocrText": "A particle of mass $m$ is moving in a circle of radius $r$ under the influence of a centripetal force $F = -\\frac{k}{r^2}$. Calculate the total mechanical energy of the particle.",
    "confidence": 0.982,
    "hasEquations": true,
    "detectedSubject": "Physics",
    "boundingBoxes": [
      { "text": "A particle of mass $m$", "box": [12, 14, 280, 45] }
    ]
  }
}
```

---

### 3.2. Streaming Socratic AI Doubt Solver (`/chat_stream`)
Streams deductive, step-by-step Socratic explanations using Server-Sent Events (SSE).

- **URL:** `POST https://chatbot.robustresults.com/chat_stream`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`, `Accept: text/event-stream`

#### Request Body
```json
{
  "query": "A particle of mass $m$ is moving in a circle of radius $r$ under centripetal force $F = -\\frac{k}{r^2}$. Calculate total mechanical energy.",
  "subject": "Physics",
  "exam": "jee",
  "language": "en",
  "conversationId": null,
  "stream": true,
  "mode": "step_by_step"
}
```

#### Response (Event Stream Chunks)
```text
data: {"id": "msg_001", "stage": "analyzing", "delta": "### Concept Analysis\n"}

data: {"id": "msg_001", "stage": "reasoning", "delta": "The given centripetal force is $$F = \\frac{m v^2}{r} = \\frac{k}{r^2}$$\n"}

data: {"id": "msg_001", "stage": "reasoning", "delta": "Multiplying both sides by $\\frac{r}{2}$, we get the Kinetic Energy:\n$$K = \\frac{1}{2} m v^2 = \\frac{k}{2r}$$\n"}

data: {"id": "msg_001", "stage": "reasoning", "delta": "Potential energy $U$ is given by $$\\int F \\cdot dr = -\\frac{k}{r}$$\n"}

data: {"id": "msg_001", "stage": "solution", "delta": "Therefore, Total Mechanical Energy $$E = K + U = \\frac{k}{2r} - \\frac{k}{r} = -\\frac{k}{2r}$$\n"}

data: [DONE]
```

---

### 3.3. AI Rank & Percentile Predictor (`/rank/predict`)
Predicts All India Rank (AIR), category rank, and percentile from raw marks using historical multi-year normalization models.

- **URL:** `POST https://azureapi.prutor.ai/rank/predict`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
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

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Rank prediction successful.",
  "data": {
    "predictedPercentile": 98.72,
    "predictedAIR": 14200,
    "airRange": { "min": 13100, "max": 15400 },
    "categoryRank": 3280,
    "confidenceScore": 0.94,
    "historicalTrend": [
      { "year": 2025, "marks": 215, "percentile": 98.65 },
      { "year": 2024, "marks": 215, "percentile": 98.81 }
    ]
  }
}
```

---

### 3.4. Generate Similar Practice Questions (`/qa/generate-similar-questions/`)
Synthesizes isomorphic practice problems sharing identical mathematical concepts but altered numerical values.

- **URL:** `POST https://azureapi.prutor.ai/qa/generate-similar-questions/`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "questionText": "Find the equivalent resistance across terminals A and B of an infinite ladder network of 1 ohm resistors.",
  "subject": "Physics",
  "topic": "Current Electricity",
  "difficulty": "medium",
  "count": 3
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Similar questions generated successfully.",
  "data": {
    "questions": [
      {
        "id": "gen_q_01",
        "questionText": "In an infinite ladder network of capacitors, each capacitor in the series arm has capacitance $2\\mu F$ and in the shunt arm has $4\\mu F$. Find equivalent capacitance.",
        "options": [
          { "key": "A", "text": "$2\\mu F$" },
          { "key": "B", "text": "$4\\mu F$" },
          { "key": "C", "text": "$\\sqrt{12}\\mu F$" },
          { "key": "D", "text": "$1.23\\mu F$" }
        ],
        "correctOption": "A",
        "explanation": "Let equivalent capacitance be $C_{eq}$. The circuit repeats..."
      }
    ]
  }
}
```

---

## 4. Assessment & Test Series Microservices

### 4.1. Fetch Full Mock Test Questions (`/google-auth/mock-test-name-api-multi-lang`)
Fetches complete question sets, sections, instructions, and marking schemes for an NTA CBT examination.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/mock-test-name-api-multi-lang`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "testId": "65b128f7c9e011241df088a2",
  "examType": "jee",
  "language": "en"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Mock test retrieved successfully.",
  "data": {
    "testId": "65b128f7c9e011241df088a2",
    "title": "JEE Main 2026 Full Syllabus Mock 01",
    "durationMinutes": 180,
    "totalQuestions": 90,
    "totalMarks": 300,
    "sections": [
      {
        "sectionId": "sec_phy",
        "name": "Physics",
        "totalQuestions": 30,
        "mandatoryQuestions": 25,
        "questions": [
          {
            "questionId": "q_phy_001",
            "questionNumber": 1,
            "type": "MCQ",
            "questionText": "A car accelerates from rest at a constant rate $\\alpha$ for some time...",
            "questionImage": null,
            "options": [
              { "optionId": "opt_A", "text": "$\\frac{\\alpha \\beta t}{\\alpha + \\beta}$" },
              { "optionId": "opt_B", "text": "$\\frac{(\\alpha + \\beta)t}{\\alpha \\beta}$" },
              { "optionId": "opt_C", "text": "$\\frac{\\alpha^2 t}{\\beta}$" },
              { "optionId": "opt_D", "text": "$\\frac{\\beta^2 t}{\\alpha}$" }
            ],
            "markingScheme": {
              "correctMarks": 4,
              "negativeMarks": -1
            }
          }
        ]
      }
    ]
  }
}
```

---

### 4.2. Submit Complete Examination (`/google-auth/all-submissions-save-multi-lang`)
Submits a student's final question responses for automated grading, rank calculation, and mistake tagging.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/all-submissions-save-multi-lang`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "testId": "65b128f7c9e011241df088a2",
  "userId": "64d271f7b88914101df01020",
  "examType": "jee",
  "timeSpentSeconds": 10420,
  "submissionType": "user_submit",
  "responses": [
    {
      "questionId": "q_phy_001",
      "sectionId": "sec_phy",
      "selectedOption": "opt_A",
      "status": "answered",
      "timeSpentSeconds": 142
    },
    {
      "questionId": "q_phy_002",
      "sectionId": "sec_phy",
      "selectedOption": null,
      "status": "marked_for_review",
      "timeSpentSeconds": 55
    }
  ]
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Examination submitted and graded.",
  "data": {
    "attemptId": "att_65c499e120f",
    "totalMarksObtained": 224,
    "maxMarks": 300,
    "totalAttempted": 65,
    "correctCount": 58,
    "incorrectCount": 7,
    "unattemptedCount": 25,
    "accuracyPercentage": 89.23,
    "percentile": 98.42,
    "allIndiaRank": 2840,
    "subjectBreakdown": {
      "Physics": { "marks": 82, "correct": 21, "incorrect": 2 },
      "Chemistry": { "marks": 78, "correct": 20, "incorrect": 2 },
      "Mathematics": { "marks": 64, "correct": 17, "incorrect": 3 }
    }
  }
}
```

---

### 4.3. Fetch Test Performance Report (`/google-auth/get-student-report-multi-lang`)
Provides deep analytical diagnostic reports including time spent per question, topic weaknesses, and topper comparison.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/get-student-report-multi-lang`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "attemptId": "att_65c499e120f",
  "language": "en"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Student report retrieved successfully.",
  "data": {
    "attemptId": "att_65c499e120f",
    "testTitle": "JEE Main Full Mock 01",
    "topperScore": 288,
    "averageScore": 112,
    "studentScore": 224,
    "speedMetrics": {
      "averageTimePerQuestionSeconds": 160,
      "topperAverageTimeSeconds": 115
    },
    "weakTopics": [
      { "subject": "Mathematics", "topic": "Probability", "incorrectCount": 2 },
      { "subject": "Chemistry", "topic": "Ionic Equilibrium", "incorrectCount": 1 }
    ],
    "strongTopics": [
      { "subject": "Physics", "topic": "Kinematics", "accuracy": 1.0 },
      { "subject": "Physics", "topic": "Modern Physics", "accuracy": 1.0 }
    ]
  }
}
```

---

### 4.4. Fetch Error Notebook (`/google-auth/error-notebook`)
Retrieves all historical mistakes aggregated across tests for targeted re-attempt and conceptual review.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/error-notebook`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "userId": "64d271f7b88914101df01020",
  "subject": "Physics",
  "status": "unresolved",
  "page": 1,
  "limit": 20
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Error notebook retrieved successfully.",
  "data": {
    "totalCount": 34,
    "page": 1,
    "items": [
      {
        "errorId": "err_001",
        "questionId": "q_phy_014",
        "testName": "JEE Main Mock 02",
        "subject": "Physics",
        "topic": "Rotational Motion",
        "questionText": "A solid cylinder of mass M...",
        "studentSelectedOption": "B",
        "correctOption": "C",
        "solutionText": "The mistake occurred because moment of inertia of cylinder was taken as MR^2 instead of 1/2 MR^2...",
        "mistakeType": "formula_mixup",
        "attemptCount": 1,
        "isMastered": false
      }
    ]
  }
}
```

---

## 5. Course, Syllabus & Knowledge Tree Microservices

### 5.1. Fetch Exam Knowledge Tree (`/google-auth/get-knowledge-tree`)
Retrieves the complete hierarchical subject, chapter, and topic taxonomy mapped to NCERT and competitive syllabi.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/get-knowledge-tree`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "exam": "jee",
  "bookletType": "NCERT"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Knowledge tree retrieved successfully.",
  "data": {
    "subtopics": [
      {
        "_id": "62d271f7b88914101df01020",
        "name": "Physics",
        "type": "subject",
        "order_no": 1,
        "subtopics": [
          {
            "_id": "62d271f7b88914101df01021",
            "name": "Units and Measurements",
            "type": "chapter",
            "order_no": 1,
            "performanceData": {
              "completionPercentage": 100.0,
              "dppAccuracy": 85.0
            },
            "subtopics": [
              {
                "_id": "62d271f7b88914101df01022",
                "name": "Dimensional Analysis",
                "type": "topic",
                "order_no": 1
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

### 5.2. Fetch Crash Course Catalog (`/google-auth/get-crashcourse-list`)
Returns all active crash course batches (e.g., 40-Day Rapid Revision, 100-Day Comprehensive).

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/get-crashcourse-list`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "exam": "jee",
  "language": "hi"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Crash courses retrieved.",
  "data": {
    "courses": [
      {
        "courseId": "cc_jee_40day",
        "title": "JEE Main 2026 - 40 Days Rapid Sprint",
        "description": "Daily live lessons, DPPs, and weekend mock tests designed by IIT Kanpur professors.",
        "totalDays": 40,
        "completedDays": 14,
        "enrolledCount": 42100,
        "bannerUrl": "https://cdn.prutor.ai/banners/crash_course_jee_40.webp"
      }
    ]
  }
}
```

---

## 6. Secure Media & Video Streaming Microservices

### 6.1. Generate Time-Limited Signed Video URL (`/generate-signed-url`)
Mints a secure, HMAC-signed video stream URL valid for a single session to prevent DRM circumvention and piracy.

- **URL:** `POST https://servervideo.prutor.ai/generate-signed-url`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "lessonId": "chem_ald_02",
  "course": "jee",
  "resolution": "auto"
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Signed URL generated.",
  "data": {
    "streamUrl": "https://videob.prutor.digital/api/secure/url?token=hmac_9948a72b109e&exp=1792650300&uid=64d271f7b88914101df01020",
    "expiresAt": 1792650300,
    "inVideoQuizzes": [
      {
        "timestampSeconds": 510,
        "quizId": "ivq_001",
        "questionText": "What catalyst is used in Rosenmund Reduction?",
        "options": ["Pd/BaSO4", "LiAlH4", "NaBH4", "Pt/C"],
        "correctIndex": 0
      }
    ]
  }
}
```

---

### 6.2. Log Video Watch Progress (`/google-auth/video-tracking`)
Heartbeat logging for student watch time, utilized for parent monitoring, attendance, and KPI tracking.

- **URL:** `POST https://sathee-jee.prutor.ai/google-auth/video-tracking`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "lessonId": "chem_ald_02",
  "currentPositionSeconds": 520,
  "totalDurationSeconds": 1800,
  "isCompleted": false
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Playback progress logged."
}
```

---

## 7. Admissions & College Cutoff Microservices

### 7.1. Query College Details & Cutoff Trends (`/api/nexdoc/college-details`)
Retrieves comprehensive admissions data, NIRF ranking, 3-year cutoff trends, and placement records.

- **URL:** `GET https://sathee.iitk.ac.in/api/nexdoc/college-details?collegeId=iit_bombay`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Accept: application/json`

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "College details retrieved.",
  "data": {
    "id": "iit_bombay",
    "name": "Indian Institute of Technology Bombay",
    "nirfRank": 3,
    "state": "Maharashtra",
    "city": "Mumbai",
    "branches": [
      {
        "branchCode": "CSE",
        "branchName": "Computer Science and Engineering",
        "seats": 120,
        "cutoffs": {
          "2025": { "General": 68, "OBC": 145, "SC": 890, "ST": 420, "EWS": 210 },
          "2024": { "General": 72, "OBC": 152, "SC": 920, "ST": 445, "EWS": 225 }
        }
      }
    ]
  }
}
```

---

## 8. Physical OMR Scanning Microservice

### 8.1. Evaluate Physical OMR Sheet (`/api/upload/`)
Accepts an image of a physical 100/180/200-question bubbling OMR answer sheet, executes computer vision bubble circle detection, grades against answer key, and returns instantaneous score.

- **URL:** `POST https://omr.sathee.prutor.ai/api/upload/`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: multipart/form-data`

#### Request (Multipart Form)
- `omrImage`: Image file (JPEG/PNG)
- `templateId`: `"jee_advanced_paper1_2026"`
- `rollNumber`: `"1029481"`

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "OMR processed successfully.",
  "data": {
    "detectedRollNumber": "1029481",
    "confidenceScore": 0.991,
    "totalBubblesDetected": 180,
    "totalAttempted": 48,
    "correctCount": 42,
    "incorrectCount": 6,
    "marksCalculated": 162,
    "scannedAnswers": {
      "1": "A",
      "2": "C",
      "3": "B"
    }
  }
}
```

---

## 9. Communications & Utility Microservices

### 9.1. Create Short Link (`/createShortLink`)
Generates deep-linkable short referral or quiz sharing URLs (`https://sathee.prutor.info/...`).

- **URL:** `POST https://asia-south1-satheeqrcode.cloudfunctions.net/createShortLink`
- **Auth:** `Bearer <idToken>`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "originalUrl": "https://sathee.prutor.info/quizshare?quizId=q_9918&userId=user_9876543210",
  "campaign": "referral_whatsapp",
  "expiresInDays": 30
}
```

#### Response Body (`200 OK`)
```json
{
  "success": true,
  "status": 200,
  "message": "Shortlink generated.",
  "data": {
    "shortUrl": "https://sathee.prutor.info/s/w8X1k"
  }
}
```
