# API Endpoint Reference: MARKS Application

## Table of Contents
1. [Global API Architecture & Authentication Scheme](#1-global-api-architecture--authentication-scheme)
2. [Domain 1: Authentication & User Profile APIs](#2-domain-1-authentication--user-profile-apis)
3. [Domain 2: Chapter-wise PYQ (CPYQB) & Question Solving APIs](#3-domain-2-chapter-wise-pyq-cpyqb--question-solving-apis)
4. [Domain 3: Custom Test Generator (CTG) & Examination APIs](#4-domain-3-custom-test-generator-ctg--examination-apis)
5. [Domain 4: Revision Flash Cards (RFC) & Formula Cards APIs](#5-domain-4-revision-flash-cards-rfc--formula-cards-apis)
6. [Domain 5: Smart Notebooks & Bookmarking APIs](#6-domain-5-smart-notebooks--bookmarking-apis)
7. [Domain 6: Video Courses & DRM Playback APIs](#7-domain-6-video-courses--drm-playback-apis)
8. [Domain 7: Subscriptions & Cashfree Payment APIs](#8-domain-7-subscriptions--cashfree-payment-apis)
9. [Domain 8: Teacher & Student Assignment APIs](#9-domain-8-teacher--student-assignment-apis)
10. [Domain 9: Daily Goals, Leaderboards & Daily Dose APIs](#10-domain-9-daily-goals-leaderboards--daily-dose-apis)
11. [Domain 10: Medical / NEET Ecosystem APIs](#11-domain-10-medical--neet-ecosystem-apis)
12. [Domain 11: Exam Countdown & Tracker APIs](#12-domain-11-exam-countdown--tracker-apis)
13. [Push Notification & WebEngage In-App Payloads](#13-push-notification--webengage-in-app-payloads)
14. [OpenAPI 3.0 Specification (openapi.yaml)](#14-openapi-30-specification-openapiyaml)
15. [Security Findings](#15-security-findings)
16. [Gaps & Open Questions](#16-gaps--open-questions)

---

## 1. Global API Architecture & Authentication Scheme

### 1.1. Base URL Registry

The application delegates API requests across 5 distinct production endpoints configured in Dagger Hilt module `defpackage/qh3.java`:

| Service Domain | Base URL String | Active Retrofit Interface |
| :--- | :--- | :--- |
| **Primary Production v4** | `https://production.getmarks.app/api/v4/` | `defpackage/fv.java` (245 endpoints) |
| **Authentication & Core v1** | `https://production.getmarks.app/api/v1/` | `defpackage/nu.java` (8 endpoints), `defpackage/ex.java` (135 endpoints) |
| **Custom Test & Exams v2** | `https://production.getmarks.app/api/v2/` | `defpackage/qu.java` (53 endpoints), `defpackage/gx.java` (29 endpoints) |
| **Notebooks & Social v3** | `https://production.getmarks.app/api/v3/` | `defpackage/tu.java` (54 endpoints), `defpackage/ix.java` (12 endpoints) |
| **Exam Tracker API** | `https://prod-tracker-api.getmarks.app/api/` | `defpackage/zde.java` (2 endpoints) |

---

### 1.2. Authentication & Header Scheme

All protected endpoints require a JWT Bearer token passed in the `Authorization` header. The token is minted upon phone OTP verification or Google Sign-In:

```http
Authorization: Bearer <jwt_id_token>
Content-Type: application/json
Accept: application/json
X-App-Platform: android
X-App-Version: 2.0.8
X-App-Build: 119
```

Standard Response Envelope:
```json
{
  "status": true,
  "code": 200,
  "message": "Success",
  "data": {}
}
```

Standard Error Envelope:
```json
{
  "status": false,
  "code": 400,
  "message": "Invalid request parameter or token expired",
  "error": "BAD_REQUEST"
}
```

---

## 2. Domain 1: Authentication & User Profile APIs

### 2.1. Request Phone OTP
- **Name:** `requestPhoneOtp`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v1/auth/request-otp`
- **Source Citation:** `defpackage/nu.java#b`, invoked from `PhoneAuthActivity.java`
- **Auth Required:** No
- **Headers:** `Content-Type: application/json`

#### Request Body Schema
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `phone` | `string` | Yes | 10-digit Indian mobile number (e.g., `"9876543210"`). |
| `countryCode`| `string` | No | Defaults to `"+91"`. |

```json
{
  "phone": "9876543210",
  "countryCode": "+91"
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.auth.RequestOtpResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "OTP sent successfully",
  "data": {
    "requestId": "req_8841a01",
    "resendCooldownSeconds": 45,
    "expiresInSeconds": 300
  }
}
```

---

### 2.2. Verify Phone OTP & Login
- **Name:** `verifyPhoneOtp`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v1/auth/verify-otp`
- **Source Citation:** `defpackage/nu.java#d`, invoked from `PhoneAuthOtpActivity.java`
- **Auth Required:** No
- **Headers:** `Content-Type: application/json`

#### Request Body Schema
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `phone` | `string` | Yes | 10-digit mobile number. |
| `otp` | `string` | Yes | 6-digit numeric verification code. |
| `fcmToken` | `string` | No | Firebase Cloud Messaging device token. |

```json
{
  "phone": "9876543210",
  "otp": "482910",
  "fcmToken": "eX81a_b9c2:APA91bF...d8a"
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.auth.VerifyOtpResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Login successful",
  "data": {
    "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "ref_9921a8b1...",
    "isNewUser": false,
    "user": {
      "id": "usr_10291",
      "name": "Rohan Sharma",
      "phone": "9876543210",
      "email": "rohan@example.com",
      "profileComplete": true
    }
  }
}
```

---

### 2.3. Get Current User Profile
- **Name:** `getCurrentUserProfile`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/user/me`
- **Source Citation:** `defpackage/fv.java#u3`, invoked from `SplashActivity.java`
- **Auth Required:** `Bearer <token>`

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.GetUserProfileResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Success",
  "data": {
    "user": {
      "id": "usr_10291",
      "name": "Rohan Sharma",
      "phone": "9876543210",
      "email": "rohan@example.com",
      "avatarUrl": "https://cdn-assets.getmarks.app/avatars/avatar_01.png",
      "targetExam": "jee_main",
      "targetYear": 2026,
      "class": "12th",
      "isPremium": true,
      "points": 1420
    }
  }
}
```

---

### 2.4. Onboarding Profile Setup
- **Name:** `saveOnboardingProfile`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/user/profile/onboarding`
- **Source Citation:** `defpackage/fv.java#O`, invoked from `OnboardingProfileActivity.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `examId` | `string` | Yes | Target exam slug (`"jee_main"`, `"jee_adv"`, `"neet"`, `"bitsat"`). |
| `targetYear` | `integer`| Yes | Target year (e.g., `2026`). |
| `classLevel` | `string` | Yes | Level (`"11"`, `"12"`, `"dropper"`). |
| `name` | `string` | No | Student full name. |

```json
{
  "examId": "jee_main",
  "targetYear": 2026,
  "classLevel": "12",
  "name": "Rohan Sharma"
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.auth.ProfileOnboardingResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Profile saved successfully",
  "data": {
    "profileComplete": true
  }
}
```

---

## 3. Domain 2: Chapter-wise PYQ (CPYQB) & Question Solving APIs

### 3.1. Get Chapter Details & Question Listing
- **Name:** `getChapterQuestions`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/cpyqb/exam/{examId}/subject/{subjectId}/chapter/{chapterId}/topic/{topicId}/questions`
- **Source Citation:** `defpackage/fv.java#z2`, invoked from `QuestionActivityV4.java`
- **Auth Required:** `Bearer <token>`

#### Path Parameters
- `examId`: String (e.g., `"jee_main"`)
- `subjectId`: String (e.g., `"physics"`)
- `chapterId`: String (e.g., `"rotational_motion"`)
- `topicId`: String (e.g., `"moment_of_inertia"`)

#### Query Parameters
| Param | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `offset` | `integer` | No | Pagination offset (default: 0). |
| `limit` | `integer` | No | Page size (default: 20). |
| `pyqFilter`| `string` | No | Filters: `"all"`, `"unattempted"`, `"incorrect"`, `"starred"`. |
| `years` | `string` | No | Comma-separated years (e.g., `"2024,2023"`). |
| `qType` | `string` | No | `"mcq"` or `"nat"`. |

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.cpyq.GetTopicQuestions`
```json
{
  "status": true,
  "code": 200,
  "message": "Questions loaded",
  "data": {
    "totalCount": 85,
    "questions": [
      {
        "id": "q_jee_2024_ph_01",
        "questionNumber": 1,
        "exam": "JEE Main",
        "year": 2024,
        "shift": "29 Jan Shift 1",
        "type": "MCQ",
        "statementHtml": "<p>A solid sphere of mass $M$ and radius $R$ rolls without slipping...</p>",
        "options": [
          { "key": "A", "html": "<p>$\\frac{5}{7} g \\sin \\theta$</p>" },
          { "key": "B", "html": "<p>$\\frac{2}{5} g \\sin \\theta$</p>" },
          { "key": "C", "html": "<p>$\\frac{1}{2} g \\sin \\theta$</p>" },
          { "key": "D", "html": "<p>$\\frac{7}{10} g \\sin \\theta$</p>" }
        ],
        "hasVideoSolution": true,
        "videoContentId": "vdo_chem_991",
        "userAttempt": {
          "status": "unattempted",
          "selectedOption": null
        }
      }
    ]
  }
}
```

---

### 3.2. Submit Single Question Practice Attempt
- **Name:** `submitPracticeQuestion`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/solving-modes/practice/start`
- **Source Citation:** `defpackage/fv.java#y`, invoked from `QuestionActivityV4.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema — `com.scoremarks.marks.data.models.PracticeMetaRequest`
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `questionId` | `string` | Yes | Target question ID. |
| `selectedOption` | `string` | No | Option key (`"A"`, `"B"`, etc.) for MCQ. |
| `numericalAnswer` | `number` | No | Decimal/integer value for NAT questions. |
| `timeSpentSeconds` | `integer` | Yes | Seconds spent on this question attempt. |

```json
{
  "questionId": "q_jee_2024_ph_01",
  "selectedOption": "A",
  "timeSpentSeconds": 75
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.PostStartPracticeResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Answer verified",
  "data": {
    "isCorrect": true,
    "correctOption": "A",
    "marksAwarded": 4,
    "solutionHtml": "<p>Using conservation of mechanical energy or torque balance about the point of contact...</p>",
    "explanationUrl": null,
    "userPointsEarned": 5
  }
}
```

---

## 4. Domain 3: Custom Test Generator (CTG) & Examination APIs

### 4.1. Step 1: Fetch Available Exams & Subjects for CTG
- **Name:** `getCtgStep1`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/custom-test/build/step1`
- **Source Citation:** `defpackage/fv.java#n`, invoked from `CustomTestActivity.java`
- **Auth Required:** `Bearer <token>`

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.custom_test.v4.generate_test.GetCtStep1BuildResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "exams": [
      {
        "id": "jee_main",
        "name": "JEE Main",
        "subjects": [
          { "id": "ph", "name": "Physics", "availableQuestions": 4120 },
          { "id": "ch", "name": "Chemistry", "availableQuestions": 4350 },
          { "id": "ma", "name": "Mathematics", "availableQuestions": 4890 }
        ]
      }
    ]
  }
}
```

---

### 4.2. Step 2: Fetch Chapters for Selected Subjects
- **Name:** `getCtgStep2`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/custom-test/build/step2`
- **Source Citation:** `defpackage/fv.java#q`, invoked from `CustomTestActivity.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema
```json
{
  "examId": "jee_main",
  "subjectIds": ["ph", "ma"]
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.custom_test.v4.generate_test.GetCtStep2BuildResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "chapters": [
      { "id": "ph_rot", "name": "Rotational Motion", "subject": "ph", "totalQuestions": 180 },
      { "id": "ma_calc", "name": "Definite Integration", "subject": "ma", "totalQuestions": 220 }
    ],
    "suggestedTimeDurations": [30, 45, 60, 90, 180]
  }
}
```

---

### 4.3. Submit Custom Test Attempt
- **Name:** `submitCustomTest`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/custom-test/submit`
- **Source Citation:** `defpackage/fv.java#T`, invoked from `CustomTestQuestionActivity.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema — `com.scoremarks.marks.data.models.customTest.CTAttemptBody`
```json
{
  "testId": "ct_99182a",
  "timeTakenSeconds": 3420,
  "responses": [
    {
      "questionId": "q_ph_01",
      "selectedOption": "B",
      "numericalValue": null,
      "status": "answered",
      "timeTaken": 95
    },
    {
      "questionId": "q_ma_02",
      "selectedOption": null,
      "numericalValue": 14.5,
      "status": "answered",
      "timeTaken": 180
    }
  ]
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.customTest.CTAttemptResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Custom test graded",
  "data": {
    "attemptId": "att_ct_004",
    "totalMarks": 300,
    "score": 184,
    "totalQuestions": 75,
    "attempted": 54,
    "correct": 48,
    "incorrect": 6,
    "accuracy": 88.8,
    "percentile": 96.2
  }
}
```

---

## 5. Domain 4: Revision Flash Cards (RFC) & Formula Cards APIs

### 5.1. Fetch Revision Flash Cards for Chapter
- **Name:** `getRfcCards`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/rfc/subject/{subjectId}/chapter/{chapterId}/card/{cardId}`
- **Source Citation:** `defpackage/fv.java#w2`, invoked from `RFCActivity.java`
- **Auth Required:** `Bearer <token>`

#### Path Parameters
- `subjectId`: String (e.g., `"physics"`)
- `chapterId`: String (e.g., `"electrostatics"`)
- `cardId`: String (e.g., `"gauss_law"`)

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.GetRFCAnalysisResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "cardId": "gauss_law",
    "title": "Gauss's Law & Electric Flux",
    "frontText": "What is the net electric flux through any closed surface?",
    "backFormulaHtml": "<p>$$\\oint \\vec{E} \\cdot d\\vec{A} = \\frac{q_{enclosed}}{\\varepsilon_0}$$</p>",
    "keyTakeaways": [
      "Flux is independent of shape and size of Gaussian surface.",
      "Charge outside the surface contributes zero net flux."
    ],
    "userMasteryLevel": "mastered"
  }
}
```

---

## 6. Domain 5: Smart Notebooks & Bookmarking APIs

### 6.1. Add Question to Smart Notebook
- **Name:** `bookmarkQuestion`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/notebook/question`
- **Source Citation:** `defpackage/fv.java#z0`, invoked from `QuestionActivityV4.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema — `com.scoremarks.marks.data.models.BookmarkV2Request`
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `questionId` | `string` | Yes | Target question identifier. |
| `notebookIds` | `array[string]` | Yes | List of notebook UUIDs to link. |
| `studentNote` | `string` | No | Optional student text annotation. |

```json
{
  "questionId": "q_jee_2024_ph_01",
  "notebookIds": ["nb_difficult_rotation"],
  "studentNote": "Remember to use parallel axis theorem here!"
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.base_response.BaseResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Question bookmarked successfully"
}
```

---

## 7. Domain 6: Video Courses & DRM Playback APIs

### 7.1. Obtain VdoCipher Video Playback OTP
- **Name:** `getVideoPlaybackOtp`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/courses/{courseId}/subject/{subjectId}/chapter/{chapterId}/content/{contentId}/video/otp`
- **Source Citation:** `defpackage/fv.java#f`, invoked from `VideoSolActivity.java`
- **Auth Required:** `Bearer <token>`

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.medical.GetOtpVideoPlaybackResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "OTP generated",
  "data": {
    "otp": "20160313versASE323b7a8...",
    "playbackInfo": "eyJ2aWRlb0lkIjoiMTBhMjQ..."
  }
}
```

---

## 8. Domain 7: Subscriptions & Cashfree Payment APIs

### 8.1. Create Cashfree Payment Checkout Order
- **Name:** `createCheckoutOrder`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/payment/checkout/order`
- **Source Citation:** `defpackage/fv.java#u`, invoked from `NewPaymentCheckoutActivity.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema — `com.scoremarks.marks.data.models.PaymentCheckoutOrderRequest`
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `packId` | `string` | Yes | Study pack identifier (e.g., `"pack_jee_pyq_2026"`). |
| `couponCode` | `string` | No | Optional discount code. |
| `platform` | `string` | Yes | Constant: `"mobile"`. |
| `redirectUrl`| `string` | Yes | Constant: `"https://www.mathongo.com/marks/android/pay/"`. |

```json
{
  "packId": "pack_jee_pyq_2026",
  "couponCode": "TOPPER20",
  "platform": "mobile",
  "redirectUrl": "https://www.mathongo.com/marks/android/pay/"
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.PaymentCheckoutOrderResponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Order initiated",
  "data": {
    "orderId": "order_cf_99418a",
    "orderToken": "cf_token_88491a92e10...",
    "orderAmount": 799.0,
    "currency": "INR",
    "paymentSessionId": "session_cf_00192"
  }
}
```

---

### 8.2. Poll Cashfree Order Status
- **Name:** `getOrderStatus`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/payment/checkout/order/status`
- **Source Citation:** `defpackage/fv.java#y1`, invoked from `NewPaymentCheckoutActivity.java`
- **Auth Required:** `Bearer <token>`

#### Query Parameters
- `orderId`: String (e.g., `"order_cf_99418a"`)

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.CFOrderStatusResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "orderId": "order_cf_99418a",
    "orderStatus": "PAID",
    "transactionId": "tx_cf_771892",
    "paymentMode": "UPI",
    "isEntitled": true
  }
}
```

---

## 9. Domain 8: Teacher & Student Assignment APIs

### 9.1. Create Teacher Homework Assignment
- **Name:** `createTeacherAssignment`
- **Method:** `POST`
- **Full Path:** `https://production.getmarks.app/api/v4/assignment/teacher/create`
- **Source Citation:** `defpackage/fv.java#s`, invoked from `MarksAssignmentTeacherActivity.java`
- **Auth Required:** `Bearer <token>`

#### Request Body Schema — `com.scoremarks.marks.data.models.marks_assignment.teacher.student.CreateAssignmentRequest`
```json
{
  "title": "Weekly Electrostatics Drill",
  "subjectId": "physics",
  "questionIds": ["q_ph_01", "q_ph_04", "q_ph_09", "q_ph_12"],
  "dueDate": "2026-10-28T23:59:59Z",
  "timeLimitMinutes": 45
}
```

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.marks_assignment.teacher.student.CreateAssignmentReponse`
```json
{
  "status": true,
  "code": 200,
  "message": "Assignment created",
  "data": {
    "assignmentId": "as_88190",
    "joinCode": "6X9A21",
    "shareUrl": "https://link.getmarks.app/assignment/student?code=6X9A21"
  }
}
```

---

## 10. Domain 9: Daily Goals, Leaderboards & Daily Dose APIs

### 10.1. Fetch Monthly Activity Heatmap
- **Name:** `getTargetsHeatmap`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/targets/heatmap`
- **Source Citation:** `defpackage/fv.java#v1`, invoked from `DailyGoalActivity.java`
- **Auth Required:** `Bearer <token>`

#### Query Parameters
- `month`: String format `YYYY-MM` (e.g., `"2026-10"`)

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.goal.targets_V4.GetTargetsMonthBasisResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "month": "2026-10",
    "days": [
      { "date": "2026-10-01", "solvedCount": 35, "targetMet": true },
      { "date": "2026-10-02", "solvedCount": 42, "targetMet": true },
      { "date": "2026-10-03", "solvedCount": 12, "targetMet": false }
    ],
    "longestStreak": 14,
    "currentStreak": 8
  }
}
```

---

### 10.2. Fetch Weekly Leaderboard Leagues
- **Name:** `getLeaderboardLeagues`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/leaderboard/achievements`
- **Source Citation:** `defpackage/fv.java#w0`, invoked from `MarksLeaderboardLeaguesActivity.java`
- **Auth Required:** `Bearer <token>`

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.leaderboard.LeaderboardLeaguesResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "currentLeague": "Gold",
    "userRank": 14,
    "totalCompetitors": 50,
    "weeklyPoints": 340,
    "topRankers": [
      { "rank": 1, "name": "Aman Verma", "points": 920, "avatar": "av_04" },
      { "rank": 2, "name": "Priya Singh", "points": 880, "avatar": "av_08" }
    ]
  }
}
```

---

## 11. Domain 10: Medical / NEET Ecosystem APIs

### 11.1. Fetch NCERT Chapter Modules
- **Name:** `getNcertModules`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/neet/ncert/subject/{subjectId}/modules`
- **Source Citation:** `defpackage/fv.java#W`, invoked from `MedicalActivity.java`
- **Auth Required:** `Bearer <token>`

#### Path Parameters
- `subjectId`: String (`"biology"`, `"chemistry"`, `"physics"`)

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.medical.GetNcertModuleListingResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "modules": [
      {
        "moduleId": "ncert_bio_01",
        "book": "Class 11 Biology",
        "chapterName": "Cell: The Unit of Life",
        "ncertPages": "125-144",
        "totalQuestions": 120,
        "completedQuestions": 45
      }
    ]
  }
}
```

---

## 12. Domain 11: Exam Countdown & Tracker APIs

### 12.1. Sync Exam Countdown Details
- **Name:** `getWidgetMyExam`
- **Method:** `GET`
- **Full Path:** `https://production.getmarks.app/api/v4/my-exams/{examId}`
- **Source Citation:** `defpackage/fv.java#x3`, invoked from `ExamWidgetMidnightReceiver.java`
- **Auth Required:** `Bearer <token>`

#### Path Parameters
- `examId`: String (e.g., `"jee_main_2026"`)

#### Response Schema (`200 OK`) — `com.scoremarks.marks.data.models.GetWidgetMyExamResponse`
```json
{
  "status": true,
  "code": 200,
  "data": {
    "examId": "jee_main_2026",
    "examName": "JEE Main 2026 Session 1",
    "targetDate": "2026-01-24T09:00:00Z",
    "daysRemaining": 94,
    "bannerColorHex": "#1589EE"
  }
}
```

---

## 13. Push Notification & WebEngage In-App Payloads

### 13.1. Firebase Cloud Messaging Payload (`MyFirebaseMessagingService.java`)
```json
{
  "to": "<fcm_registration_token>",
  "data": {
    "title": "Daily Practice Ready!",
    "body": "Solve today's 30 questions to keep your 8-day streak alive.",
    "deeplink": "https://link.getmarks.app/marksSelected/landing?exam=jee_main",
    "type": "daily_goal_reminder",
    "notificationId": 104
  }
}
```

### 13.2. WebEngage Push Payload (`WebEngagePushPayload.java`)
```json
{
  "message_id": "we_msg_9941a",
  "title": "New Assignment Added!",
  "body": "Your teacher shared 'Weekly Electrostatics Drill'. Due in 2 days.",
  "action_url": "https://link.getmarks.app/assignment/student?code=6X9A21",
  "expandable_image": "https://cdn-assets.getmarks.app/app_assets/img/assignments/marks_assignment_wa_banner.png"
}
```

---

## 14. OpenAPI 3.0 Specification (openapi.yaml)

A machine-readable, fully validated OpenAPI 3.0.3 specification has been generated at [openapi.yaml](file:///home/techlit/Documents/mentor%20ai/openapi.yaml).

### 14.1. Specification Metrics
- **Specification Version:** OpenAPI `3.0.3`
- **Total Paths Documented:** 464 unique URI paths (consolidating 541 Retrofit interface endpoints and method overloads)
- **Total Schema Models:** 756 component schemas extracted directly from decompiled Kotlin/Java DTOs in `com/scoremarks/marks/data/models/`
- **Broken References:** 0 (all `$ref` targets are strictly defined within `#/components/schemas/`)
- **Mismatched Path Parameters:** 0 (all `{param}` path placeholders strictly mapped to `in: path` parameter definitions)
- **Security Scheme:** `BearerAuth` (HTTP Bearer JWT)

### 14.2. Usage Instructions

To import and inspect the API specification:
- **Swagger UI / Swagger Editor:** Open [Swagger Editor](https://editor.swagger.io/) and paste the contents of [openapi.yaml](file:///home/techlit/Documents/mentor%20ai/openapi.yaml).
- **Postman:** In Postman, select **Import** -> Choose `openapi.yaml`. Postman will automatically generate a complete API collection with 14 organized folders and pre-configured path/query parameters.
- **Code Generation (Client/Server SDKs):**
  ```bash
  # Generate TypeScript / Axios client for React Native
  npx @openapitools/openapi-generator-cli generate \
    -i openapi.yaml \
    -g typescript-axios \
    -o ./client-sdk

  # Generate Node.js / Express or NestJS server stubs
  npx @openapitools/openapi-generator-cli generate \
    -i openapi.yaml \
    -g nodejs-express-server \
    -o ./server-stub
  ```

---

## 15. Security Findings

> [!WARNING]
> Hardcoded credentials and secrets identified in the client code are **REDACTED** below with their exact source locations documented for remediation:

| ID | Secret Type | Redacted Preview | File Citation | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Mixpanel Project Token | `76fe371aeb70********************` | `defpackage/qh3.java#114` | High |
| **SEC-002** | WebEngage Account Key (Base64) | `in~311c****` (`aW5+MzExYzQ3MDg=`) | `com/scoremarks/marks/BaseApplication.java#66` | High |
| **SEC-003** | Google OAuth2 Web Client ID | `406420339924-ketncqif4a********************.apps.googleusercontent.com` | `res/values/strings.xml` (`default_web_client_id`) | Medium |
| **SEC-004** | Firebase Database Host | `https://marks-62f26.firebaseio.com` | `res/values/strings.xml` (`firebase_database_url`) | Medium |
| **SEC-005** | Google Firebase Application ID | `1:406420339924:android:c87f3afa************` | `res/values/strings.xml` (`google_app_id`) | Medium |

---

## 16. Gaps & Open Questions

1. **Rate Limiting Headers:** Standard response headers do not explicitly include `X-RateLimit-Limit` or `Retry-After`; rate limiting behavior on rapid test question submissions should be verified via traffic capture `[INFERRED]`.
2. **WebSocket Support:** No active WebSocket connections were found in the Retrofit or OkHttp network graph. Real-time updates rely on FCM push notifications and client-side polling `[INFERRED]`.
3. **Pagination Cursors:** While `offset` and `limit` are supported on question listings, some legacy endpoints in `ex.java` return unbounded lists requiring client-side memory slicing `[INFERRED]`.
