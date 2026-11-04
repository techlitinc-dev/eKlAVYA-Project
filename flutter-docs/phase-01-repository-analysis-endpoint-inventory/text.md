# Phase 01 — Repository Analysis (text.md)

Verified against commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4` (branch `main`, 2026-11-02).
Every claim cites its source as `path/file.py:line`.

---

## 1. Repository layout

```
eKlAVYA-Project/
├── Backend/                  FastAPI backend (the API both clients consume)
│   ├── main.py               App factory, middleware, router mounting
│   ├── core/                 config, security, errors, ids, time
│   ├── middleware/           auth_middleware, testing_auth, rate_limiter, subscription
│   ├── dependencies.py       Request-id, pagination, idempotency helpers
│   ├── models/               Pydantic request/response + entity models (29 files)
│   ├── routers/              35 router modules (HTTP layer)
│   ├── services/             Business logic (65 modules)
│   ├── repositories/         Storage abstraction (in-memory backend only)
│   ├── providers/            Mock AI providers (ocr/speech/answer/decision)
│   ├── seed.py               Startup seed data for the /api/v1 in-memory domain
│   ├── data/                 Static JSON datasets (PYQ, colleges, plans, exam dates)
│   ├── utils/firebase_config.py  Firestore client singleton
│   ├── tests/                Pytest suite
│   └── docs_api/, docs/      Legacy Markdown API testing guides
├── Frontend_Website/         Existing React 19 + Vite + TS + Tailwind v4 SPA (running app)
│   └── src/pages             LandingAndAuth, Student*, ParentPortal, SuperAdminPortal
├── Android_App/              EMPTY before Phase 02 — Flutter project root.
├── Super_Admin/              NO code — README.md only; superadmin UI lives in Frontend_Website
├── Ref_Docs/                 Reverse-engineered MARKS-app reference material (upstream product)
└── task.md plan.md endpoints.md design.md screenflow.md userflow.md   Planning docs
```

Note: `endpoints.md` (root) is an accurate legacy API reference. `Ref_Docs/*` describe the
**upstream MARKS/SATHEE product** (getmarks.app), not this backend — treat as background only.

## 2. Architecture — two coexisting API generations on one FastAPI app

`Backend/main.py` mounts **two disjoint stacks** into a single app (`FastAPI(title="Mentor AI Backend")`):

**Stack 1 — Legacy "Mentor AI" domain, prefix `/api/*` (Firestore-backed).**
Firebase Admin SDK for parent identity; Firestore for persistence; Google Gemini for AI.
This stack owns the entire required workflow: parent auth, child profiles, exam selection,
diagnostic tests, analytics, schedules, parent dashboards, payments, superadmin.

**Stack 2 — eKLAVYA v1 domain, prefix `/api/v1/*` (in-memory repository).**
Planner/notes/mindmaps/scans/speech/simulated-calls/teacher/parent modules built per
`endpoint_instructions.md`. Auth is header-based (`X-User-Id`, `X-User-Role`) while
`TESTING_MODE=true` (the default, `core/config.py:66,116-120`). Storage is
`InMemoryRepository` (`repositories/memory.py:21`) seeded at startup (`seed.py:63`) —
**process-lifetime only, not production persistence**. This stack is a testing playground;
no endpoint in it is consumed by the Flutter app or superadmin panel in this documentation set.

Both stacks run simultaneously. The Flutter app and superadmin panel target **Stack 1 only**.

Docs: interactive OpenAPI at `http://localhost:8000/api/docs`; spec at `/api/openapi.json`
(`main.py:132`).

### Middleware order (`main.py:137-169`)

`CORSMiddleware` (origins: `localhost:3000/3001/5173` + regex `https?://(localhost|127.0.0.1)(:\d+)?`,
`allow_credentials=True`, all methods/headers, `max_age=3600`) → `RateLimitMiddleware`
(`middleware/rate_limiter.py`) → exception handlers (`core/errors.py:182`) →
`RequestIDMiddleware` (`dependencies.py:51`, stamps `X-Request-Id`).

## 3. Technology inventory

| Layer | Technology | Evidence |
|---|---|---|
| Backend framework | FastAPI + Uvicorn, Pydantic v2 | `Backend/requirements.txt`, `main.py` |
| Parent identity | Firebase Admin SDK (server) + Firebase REST `signInWithPassword` | `services/auth_service.py`, `services/login_service.py:215-252` |
| Primary DB (Stack 1) | Google Cloud Firestore | `utils/firebase_config.py`; collections listed §5 |
| Secondary storage | Static JSON under `Backend/data/` | `data/pyq_and_colleges.json`, `data/subscription_plans.json`, `data/exam_dates.json` |
| Stack 2 storage | In-memory dict repository | `repositories/memory.py:21` |
| AI | `google.generativeai`, default model `gemini-2.5-flash-lite`, key env `GOOGLE_API_KEY` | `services/gemini_analytics_service.py:129,152` |
| JWT | PyJWT, HS256, secrets env `JWT_SECRET` (legacy fallback `JWT_SECRET_KEY`) | `services/token_service.py:34-53` |
| Rate limiting | In-process limiter middleware | `middleware/rate_limiter.py` |
| Web app | React 19, react-router-dom v7, axios, Tailwind v4, Vite 6, TS 5.6 | `Frontend_Website/package.json` |

`Backend/core/config.py:59-77` `Settings`: `environment="development"`, `api_v1_prefix="/api/v1"`,
`testing_mode=True` (default), `repository_backend="memory"`, `mock_providers=True`,
`seed_on_startup=True`. JWT/Gemini/Firebase values are read ad hoc via `os.getenv` in consuming
modules, **not** through this Settings object.

`.env.example` keys: `GOOGLE_API_KEY`, `GEMINI_MODEL`, `FIREBASE_CREDENTIALS_PATH`,
`FIREBASE_PROJECT_ID`, `FIREBASE_API_KEY`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`,
`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`, `CORS_ORIGINS`,
`RAZORPAY_*`, `SMTP_*`, `HERMES_*`. **Dead config** (declared but not read): the two
`JWT_*_EXPIRE_*` vars and `CORS_ORIGINS` — token expiries are hardcoded (§6) and CORS origins
are hardcoded in `main.py:137-153`.

## 4. Global conventions

**IDs** (`core/ids.py:13`): `new_id(prefix)` → `"{prefix}_{uuid4().hex}"`, e.g. `note_9f2c1ab3…`.
Child ids are `child_{uuid4().hex[:12]}` (`services/child_service.py`), test ids
`test_{uuid4().hex[:12]}` (`services/exam_service.py:154-218`), analytics ids
`analytics_{test_id}_{student_id}_{int(time.time())}` (`services/analytics_service.py:624-635`),
schedule ids `schedule_{student_id}_{analytics_id}_{timestamp}` (`services/gemini_scheduler_service.py:450`).

**Timestamps** (`core/time.py`): all datetimes timezone-aware UTC (`utcnow()`), serialized as ISO
8601; dates are local ISO `YYYY-MM-DD`.

**Pagination — two systems:**
- Legacy `/api/*`: integer `limit`/`offset` query params (e.g. `GET /api/diagnostic-test/student/{student_id}?status=&limit=10&offset=0`).
- v1 `/api/v1/*`: cursor pagination — `limit` (default 20, 1–100) + `cursor` (base64 of `{"o": offset}`); responses are `Page[T] {items, next_cursor}` (`models/common.py`, `dependencies.py:66-124`).

**Error envelopes:**
- v1 `/api/v1/*` handlers return `{"error": {"code", "message", "details", "request_id"}}` (`core/errors.py:139`).
- Legacy `/api/*` routers raise `HTTPException` → body `{"detail": str}` (`core/errors.py:167` maps 404→`NOT_FOUND`, everything else→`VALIDATION_ERROR`). A global catch-all returns 500 with `{"success": false, "error": {...}}` (`main.py:169`).

| HTTP | `code` (v1) | Meaning |
|---|---|---|
| 401 | `AUTHENTICATION_REQUIRED` | Missing/invalid/expired token |
| 403 | `PERMISSION_DENIED` | Authenticated but wrong role/owner |
| 404 | `NOT_FOUND` | Unknown id (also used to hide other users' private records) |
| 409 | `RESOURCE_CONFLICT` / `IDEMPOTENCY_CONFLICT` / `INVALID_STATE_TRANSITION` | Duplicate/conflicting write |
| 413 | `UPLOAD_TOO_LARGE` | Upload limit |
| 415 | `UPLOAD_TYPE_NOT_ALLOWED` | Upload MIME check |
| 422 | `VALIDATION_ERROR` / `SYLLABUS_CONTEXT_INVALID` / `GROUNDING_FAILED` | Pydantic/business validation |
| 429 | `RATE_LIMITED` | Rate limiter |
| 503 | `PROVIDER_UNAVAILABLE` | Gemini/Firebase unreachable |

Flutter clients must handle both envelopes: parse `error.code` (v1) when present, else map
HTTP status and read `detail`.

**Idempotency:** v1 create/generate/execute endpoints accept an `Idempotency-Key` header
(per-user+scope, 24 h retention, 409 on body mismatch, `dependencies.py:148`). No Stack-1
endpoint implements idempotency (a gap for test submission, see §11).

## 5. Storage — Firestore collections (Stack 1)

Written/read by services (evidence in `services/`):

| Collection | Contents | Key writers |
|---|---|---|
| `parents` | Parent account docs: `parent_id` (=Firebase uid), `email`, `phone`, `language`, `role:"parent"`, `registration_method`, `email_verified`, `phone_verified`, `created_at` | `auth_service.py:90-98`, `simple_register_service.py:62-75` |
| `children` | Child profiles: `child_id`, `parent_id`, `firebase_uid`, `name`, `age`, `grade`, `current_level`, `username`, `email`, **`password` (plaintext — gap #1, §11)**, `created_at`/`updated_at` | `child_service.py:133-179` |
| `sessions` | Login sessions: `token_hash`, `refresh_token_hash` (SHA-256), `revoked`, `access_expires_at`, `refresh_expires_at`, `user_type` (`"parent"`/`"child"`) | `login_service.py:100-109,884-894` |
| `verification_codes` | Email/phone OTPs: `email`/`phone`, `code`/`otp`, `type`, `used`, 10-min expiry | `verification_service.py` |
| `exam_selections` | Exam choice + subject weights + `diagnostic_test_id` | `exam_service.py` |
| `diagnostic_tests` | Scheduled tests: `test_id`, `child_id`, `exam_type`, `scheduled_date`, `duration_minutes:180`, `total_questions:200`, `status:"scheduled"` | `exam_service.py:154-218` |
| `analytics_reports` | AI analysis output (full `AnalyticsReport`) | `analytics_service.py:624-635` |
| `schedules` | Generated `Schedule` documents | `schedule_service.py`, `gemini_scheduler_service.py:450` |
| `progress`, `goals`, `notification_settings`, `subscriptions`, `test_submissions`, `micro_states`, `hermes_gamification` | Dashboard/goal/notification/premium/progress state | respective services |

**Known collection-name mismatches (gap #6, §11):** `schedule_service.py:84-85` reads analytics
from collection `analytics` and student profiles from `students`; the analytics pipeline writes
`analytics_reports` and child profiles live in `children`. `parent_dashboard_service.py` also
reads `analytics`. End-to-end schedule generation therefore 404s today.

## 6. Authentication & sessions (Stack 1, the workflow stack)

There is **no `UserRole` enum** anywhere. Roles are plain strings: `"parent"` (Firestore docs),
`"child"`/`student` (same entity, §7.H), `"superadmin"` (admin sessions), plus v1-only
`("student","teacher","parent","admin")` in `core/security.py:31`.

### 6.1 Two disjoint auth modes (environment-dependent)

- `TESTING_MODE=true` (**default**, `core/config.py`): legacy routers depend on
  `get_current_user_testing` (`middleware/testing_auth.py:20-42`) which **ignores the
  Authorization header and always returns the constant string `"test_parent_123"`**. Several
  routers then do `current_user["parent_id"]` on that string and raise 500 — auth is effectively
  absent in dev. v1 routers read `X-User-Id`/`X-User-Role` headers instead.
- `TESTING_MODE=false` + `ENVIRONMENT=production`: schedule/embedding/hermes routers verify the
  JWT via `middleware/auth_middleware.py:136` and check session revocation in Firestore.

**Consequence for clients (documented in every phase):** the Flutter app must always send
`Authorization: Bearer <token>`; in the current default backend that header is ignored, so
ownership enforcement **cannot be observed client-side** — the app must still scope every call
to ids returned from its own login (see §7.B–D). Authorization is a backend gap (#7, §11).

### 6.2 Parent token (JWT HS256) — `services/token_service.py`

- Secret: env `JWT_SECRET`, legacy fallback `JWT_SECRET_KEY` (`token_service.py:53`); algorithm `HS256`.
- **Expiries are hardcoded constants** (`token_service.py:34-35`): access `ACCESS_TOKEN_EXPIRY=86400` (24 h), refresh `REFRESH_TOKEN_EXPIRY=2592000` (30 d). `.env.example`'s JWT expiry vars are dead config.
- Access-token claims (`generate_access_token`, `token_service.py:66-143`): `parent_id`, `email?`, `phone?`, `iat`, `exp`, `type:"access"`.
- Refresh-token claims (`token_service.py:145-205`): `parent_id`, `iat`, `exp`, `type:"refresh"`.
- Sessions persisted in `sessions` with SHA-256 `token_hash`/`refresh_token_hash`; logout sets `revoked:true` (`login_service.py:501+`); refresh rotates **both** tokens and updates the hashes (`login_service.py:409+`).

### 6.3 Child token — `token_service.py:375-557`

- Access claims: `child_id`, `student_id` (**same value as `child_id`**), `username`, `is_student:true`, `name?`, `iat`, `exp`, `type:"access"`.
- Refresh claims mirror the parent refresh shape with the child id.
- Child sessions share the `sessions` collection with `user_type:"child"` (`login_service.py:884-894`).
- Child endpoints: `POST /api/auth/login/child`, `POST /api/auth/token/refresh/child`, `POST /api/auth/logout/child`, `GET /api/auth/me/child`.

### 6.4 Credential verification specifics

- **Parent email login** (`login_service.py:171-252`): password checked via Firebase REST
  `signInWithPassword` using env `FIREBASE_API_KEY`; **if the key is absent, password
  verification is silently skipped** (gap #9, §11).
- **Parent phone login** (`login_service.py:336-367`): OTP looked up in `verification_codes`
  (`phone==, otp==, type=="phone"`, `used` flag, 10-min expiry).
- **Child login** (`login_service.py:747-839`): queries `children` by `username`, then
  **plaintext-compares** the stored `password` field (gap #1, §11). Success message:
  `"Child login successful"`. Only `username` is a supported login identifier (no child email
  or child_id login).

### 6.5 Verification / OTP (`routers/verification_router.py`)

`POST /verify/email/send` (6-char alphanumeric code), `POST /verify/email/confirm`,
`POST /verify/phone/send` (6-digit OTP), `POST /verify/phone/confirm`. Codes single-use,
10-minute validity. **There is no forgot-password / password-reset flow anywhere** — `verification_service.py`
contains only the four functions above (gap #3, §11).

## 7. Workflow traces (route → service → model)

### A. Parent registration & login

1. `POST /api/auth/register/simple` (`simple_register_router.py:31`, service `simple_register_service.py`) —
   body `SimpleRegisterRequest {name 2-100, email_address, password ≥8 (letter+digit), repeat_password, mobile_number}`.
   Creates Firebase user + Firestore `parents` doc (`role:"parent"`, `registration_method:"simple"`).
   Response `AuthResponse {parent_id, email?, phone?, verification_required, message}` — **no token is issued at registration**.
2. Alternatives: `POST /api/auth/register/parent/email` (`auth_models.py:23`: `email, password ≥8 w/ letter+digit, language en|hi|mr`),
   `POST /api/auth/register/parent/phone` (phone regex `^\+91[6-9]\d{9}$`, **no password** — OTP is the credential),
   `POST /api/auth/register/parent/google` (verifies Google `id_token` via Firebase, `auth_service.py:276`).
3. `POST /api/auth/login/email` (`login_router.py:97`) → `LoginResponse {token, refresh_token, parent_id, email, phone, expires_in:86400}`.
4. Session maintenance: `POST /api/auth/token/refresh` (rotate), `POST /api/auth/logout` (revoke), `GET /api/auth/me` (Firestore parent doc).

### B. Child profile creation & child credentials

1. `POST /api/onboarding/child?parent_id=<id>` (`child_router.py:41-161`) — body `ChildProfileRequest`
   (`models/child_models.py:22-265`): `name 2-100`, `age 14-19`, `grade 9-12`,
   `current_level: beginner|intermediate|advanced`, `username 3-30 regex ^[a-zA-Z0-9_@.]+$`,
   `password 8-50 with ≥1 letter and ≥1 digit`.
2. `ChildService.create_child_profile` (`child_service.py:122-179`):
   - Enforces **one child per parent** (400 otherwise, `:122-128`).
   - Creates a **Firebase Auth user** with email `f"{username}@mentor-ai.local"` (or the raw
     username if it already contains `@`) and the same password.
   - Writes Firestore `children` doc: `child_id = child_{uuid4.hex[:12]}`, `parent_id`,
     `firebase_uid`, profile fields, `email`, and **`"password": <plaintext>`** (`:172`, with the
     source comment "In production, this should be hashed").
   - **Therefore, in this backend, creating a child profile DOES create child login credentials**
     (username + the password supplied at creation). The doc sets required by the task are
     satisfied — but note the credentials are stored in plaintext (gap #1).
3. Response `ChildProfileResponse {child_id, parent_id, name, age, grade, current_level, username, created_at, updated_at}`.
4. Management: `GET /api/onboarding/child?parent_id`, `PUT /api/onboarding/child/{child_id}?parent_id`,
   `DELETE /api/onboarding/child/{child_id}?parent_id`.
   **`ChildProfileUpdate` declares optional `username`/`password`, but `update_child_profile`
   silently drops them** (`child_service.py:416-442` only applies name/age/grade/current_level).
   → **No parent-facing child credential reset exists (gap #2).** Firestore-delete removes the
   profile (child login stops working since login queries `children`).
5. `GET /api/onboarding/status?parent_id` → `{preferences_completed, child_profile_completed, exam_selected, onboarding_complete}`.

### C. Test scheduling (parent)

The real scheduling path is exam selection:
1. `POST /api/onboarding/exam/select?parent_id=<id>&child_id=<id>` (`exam_router.py:133-267`) —
   returns **HTTP 201** (`exam_router.py:136`). Body `ExamSelectionRequest` (`exam_models.py:24-183`):
   `exam_type: JEE_MAIN|JEE_ADVANCED|JEE_COMBO|NEET`, `exam_date` (future datetime),
   `subject_preferences: Dict[str,int]` — **must sum to exactly 100** and subjects must be exactly
   `{Physics, Chemistry, Mathematics}` for JEE* or `{Physics, Chemistry, Biology}` for NEET.
   Service-level rules beyond the model (`exam_service.py:279-284`, `utils/date_utils.py:67-93`):
   `exam_date` must be **≥ 30 days in the future** (400 otherwise), and the child must belong to
   the parent (403 otherwise).
2. `ExamService` → `create_diagnostic_test` (`exam_service.py:154-218`): writes `diagnostic_tests`
   doc `{test_id, child_id, exam_type, scheduled_date: now+1day, duration_minutes:180, total_questions:200, status:"scheduled", created_at}`.
3. Response `ExamSelectionResponse {child_id, exam_type, exam_date, subject_preferences, days_until_exam, diagnostic_test_id, created_at}`.
4. Status enum mismatch (gap #4): `TestStatus` (`diagnostic_test_models.py:28-64`) is
   `pending|in_progress|completed|expired|cancelled` — **there is no `"scheduled"` member**, yet
   `exam_service.py:197` and the mocks write the literal `"scheduled"`.
5. Related: `GET /api/onboarding/exams/available`, `GET/PUT /api/onboarding/exam/preferences?child_id`,
   and a mock `POST /api/diagnostic-test/schedule` (Firestore write commented out — do not use).

### D. Child test-taking & submission

`diagnostic_test_router.py` and `test_management_router.py` both mount at `/api/diagnostic-test`;
the former is registered first (`main.py:296`) so its handlers own
`/{test_id}/start|submit|results|status`. All are **mock handlers** (gap #4):

- `GET /api/diagnostic-test/student/{student_id}?status=&limit=10&offset=0` — canned list (`diagnostic_test_router.py:595-693`).
- `GET /api/diagnostic-test/{test_id}` — **501 Not Implemented** (`:508`). A child cannot fetch test questions end-to-end today.
- `POST /api/diagnostic-test/{test_id}/start` — mock dict.
- `POST /api/diagnostic-test/{test_id}/submit` — accepts `TestSubmission` (`diagnostic_test_models.py:120-177`):
  `test_id`, `student_id`, `answers: Dict[int,str]` (values must be `A`–`D`, empty, or numeric),
  `time_taken: int ≥ 0` (seconds), `submission_time: datetime`. Scoring in the wired path is
  **random** (`test_management_router.py:170-269`, `random.seed(q_num)`, 80% correct, +4/−1).
  A real scorer exists unconnected: `services/score_calculator.py:153` with per-exam marking
  schemes (+4/−1 JEE Main single-correct; +3/−1 Advanced; +4/−2 partial multiple-correct;
  NEET +4/−1 — `models/score_models.py:23-69`).
- Result shape `TestResults` (`diagnostic_test_models.py:585-656`): `test_id`, `student_id`,
  `total_score`, `total_marks`, `percentage 0-100`, `section_scores: Dict[str, SectionScore{section_name, score, total_marks, correct, incorrect, unattempted}]`,
  `correct_count`, `incorrect_count`, `unattempted_count`.
- **Nothing persists**: Firestore writes are commented out (`test_management_router.py:272-300`),
  the status transition to `completed` is commented (`:293-298`), so duplicate-submission
  prevention (a `status == "in_progress"` check at `:496-503`) can never trigger.

### E. AI analysis

1. `POST /api/analytics/generate` (`analytics_router.py:77-190`) — body `AnalyticsRequest`
   (`analytics_models.py:89-146`): `test_id`, `student_id`,
   `answers: List[QuestionAnswer{question_number, answer}] | Dict[int,str]`,
   `include_ai_insights: bool = true`, `use_cache: bool = true`.
2. Returns HTTP **202** `AnalyticsResponse {analytics_id, status: pending|completed|failed|cached, message, report?, error?, progress?}`.
3. Client polls `GET /api/analytics/{analytics_id}` → returns the **bare `AnalyticsReport`**
   (`response_model=AnalyticsReport`, `analytics_router.py:193-211`) — NOT the
   `AnalyticsResponse` status wrapper. Only the 202 from `generate` carries
   `{analytics_id, status, message, ...}`. Clients must therefore treat the 202 body as the
   job handle and the GET result as the completed report; a GET 404 means "not found/expired".
   **The mechanism is poll-based.** Reality (`analytics_service.py:261-391`): the pipeline is
   synchronous and blocking inside the request (Firestore read → ScoreCalculator →
   PerformanceAnalyzer → context → Gemini → report builder → Firestore write); by the time the
   first poll lands, the report is already complete. No webhooks, no background jobs. Clients
   must implement polling anyway (contract-safe), with a short first delay.
   Note: `GET /api/analytics/test/{test_id}` is a placeholder that always returns `[]`
   (`analytics_router.py:333`); use `/student/{student_id}` for listing.
4. Report stored in `analytics_reports` (`analytics_service.py:624-635`); in-memory LRU cache
   keyed by test+student+answers.
5. `AnalyticsReport` (`analytics_models.py:706-762`): `analytics_id?`, `overview` (`AnalyticsOverview`:
   `test_id, student_id, exam_type, total_score, max_score, percentage, percentile, accuracy, time_taken?, total_questions, attempted, correct, incorrect, unattempted`),
   `subject_analysis: List[SubjectAnalysis]` (`subject, score, max_score, percentage, accuracy, total_questions, attempted, correct, incorrect, strengths[], weaknesses[], ai_insights?, top_topics[max 3], weak_topics[max 3]`),
   `topic_analysis: List[TopicAnalysis]` (`topic, subject, accuracy, total_questions, correct, incorrect, priority: HIGH|MEDIUM|LOW, estimated_hours, recommendation, performance_level: strong|moderate|weak, gap_from_benchmark`),
   `ai_insights?: AnalyticsInsights` (`strengths[], weaknesses[], learning_patterns[], overall_assessment, study_strategy`),
   `priority_topics: List[PriorityTopic]` max 10 (`topic, subject, priority, reason, estimated_hours, current_accuracy?, target_accuracy?, action_items[]`),
   `visualization_data?`, `metadata: Dict`, `generated_at`.
6. Retrieval: `GET /api/analytics/student/{student_id}?limit=10&offset=0`, `/api/analytics/test/{test_id}?limit=50`,
   `/api/analytics/{id}/insights` → `AnalyticsInsights`, `/api/analytics/{id}/weak-topics` → `List[PriorityTopic]`.
7. Preparation status free-string values from `performance_analyzer.py:738-744`:
   `"Excellent" | "Good" | "Needs Improvement" | "Requires Significant Work"` (not an enum).
8. `routers/ai_features_router.py` (`/api/ai/*`) is **100% hardcoded mock** — do not consume.

### F. Personalized schedule

1. `POST /api/schedule/generate` (`schedule_router.py:143-266`) — JWT auth dependency; body
   `ScheduleRequest` (`schedule_models.py:72-161`): `student_id`, `analytics_id`,
   `exam_type: JEE_MAIN|JEE_ADVANCED|NEET` (no JEE_COMBO), `exam_date` (future date),
   `daily_study_hours: float 2-8 (default 4.0)`, `preferences?: Dict`.
2. **Synchronous** — returns the complete `Schedule` with HTTP 201 after the full pipeline
   (`schedule_service.py:422-630`: validate → fetch analytics → fetch student profile → syllabus
   weightages → `PriorityCalculator` → time-feasibility → Gemini (`gemini_scheduler_service.py:140`,
   `gemini-2.5-flash-lite`) → save to `schedules`).
3. **Gap #6:** step 2 reads collection `analytics` and `students` (`schedule_service.py:84-85`) —
   but analytics live in `analytics_reports` and child profiles in `children`. Generation from a
   real analysis raises 404 today.
4. `Schedule` (`schedule_models.py:441-567`): `schedule_id`, `student_id`, `analytics_id`,
   `exam_type`, `exam_date`, `generated_date`, `total_days`, `daily_study_hours 2-8`,
   `status: active|completed|abandoned`, `days: List[ScheduleDay]`, `revision_days: List[int]`,
   `practice_test_days: List[int]`, `buffer_days: List[int]`, `priority_topics: List[TopicPriority]`.
   `ScheduleDay`: `day_number>0`, `schedule_date`, `subjects[]`, `topics: List[DailyTopic{topic, subject, priority: critical|high|medium|low, estimated_hours, subtopics[], resources[], goals[]}]`,
   `total_hours`, `milestones[]`, `completed`, `completion_percentage`.
5. Endpoints: `GET /api/schedule/{schedule_id}`; `GET /api/schedule/student/{student_id}?status_filter=active`;
   `GET /api/schedule/student/{student_id}/history?limit=10`; `POST /api/schedule/{id}/regenerate`
   (`{current_day>0}`); `PUT /api/schedule/{id}` (`{updates: Dict}`); `DELETE /api/schedule/{id}`;
   `POST /api/schedule/progress/update` (`ProgressUpdate`); `GET /api/schedule/progress/{schedule_id}`;
   `GET /api/schedule/progress/today?schedule_id=`. **No parent/child authorization distinction**
   and no ownership checks (gap #7).

### G. Parent dashboard

`routers/parent_dashboard_router.py` (prefix `/api/parent`, testing-bypass auth):
- `GET /api/parent/dashboard/{child_id}` → `ChildDashboard` (`parent_models.py:16-55`): `child_id`,
  `child_name`, `overall_progress 0-100`, `current_streak`, `hours_studied_today`,
  `hours_studied_week`, `schedule_status: on_track|behind|ahead`, `days_until_exam`,
  `weak_areas: List[Dict]`, `upcoming_tasks: List[Dict]`, `recent_test_score?`, `last_active`.
  Service reads `children`, `schedules` (`status=="active"`), `analytics` (mismatch, gap #6), `progress`.
- `GET /api/parent/reports/weekly/{child_id}?week_start=` → `WeeklyReport` (`week_start`, `week_end`,
  `total_hours_studied`, `previous_week_hours`, `topics_completed`, `tests_taken`,
  `average_test_score?`, `attendance_rate`, `subject_breakdown`, `achievements[]`, `areas_of_concern[]`).
- `GET/PUT /api/parent/notifications/settings?parent_id=` → `NotificationSettings` (9 boolean flags, `parent_models.py:133-162`).
- Goals: `POST/GET /api/parent/goals/{child_id}`, `PUT /api/parent/goals/{child_id}/{goal_id}` —
  `Goal {goal_id, child_id, goal_type: target_score|daily_hours|topic_completion|test_count, target_value, current_value, deadline?, status: active|completed|failed|cancelled, created_at, completed_at?}`.
- `POST /api/parent/reports/email-schedule` — mock.

### H. "Student" ≡ "Child"

Same entity, two names; **no separate student table**. A child is the Firestore `children` doc
created by a parent; APIs that say `student_id` take the child's id as the value. Proof:
`login_service.login_child` returns `"student_id": child_id` and `"child_id": child_id` for the
same doc (`login_service.py:822-823`); the student JWT carries duplicate `child_id`/`student_id`
claims (`token_service.py:419-420`). A genuinely separate concept exists only in the v1 domain
(teachers/classes — not part of this workflow).

### I. Superadmin

`routers/superadmin_router.py` (prefix `/api/superadmin`). **No auth dependency on any endpoint**
(gap #8). 17 endpoints:

| Endpoint | Behavior |
|---|---|
| `POST /login` | Accepts any email containing "admin" (defaults `admin@eklavya.ai`); **password never verified** (`:413-421`). Returns parent-format JWT with `parent_id="superadmin_root"` + demo account ids. |
| `POST /demo-session` | Idempotently seeds demo parent `parent_demo_eklavya` + child `child_demo_aarav` (username `aarav_jee2026`) + premium subscription; returns ready JWTs for `role ∈ student\|parent\|superadmin`. |
| `GET /overview` | KPIs: `total_parents, total_students, active_premium_subscriptions, total_revenue_inr, total_pyq_questions, total_flashcards, total_ncert_modules, total_colleges_tracked, syllabus_micro_topics, custom_tests_generated, homework_assignments, active_concept_walls`; `distributions.pyq_by_subject/pyq_by_exam`; `system_health`; recent audit logs. |
| `GET /users` | Read-only lists: parents (subscription plan/status) and students (grade, exam_scope, completion_pct, micro-topic counts `UNTOUCHED/LEARNING/MASTERED`, locked concept walls, xp, streak_days, badges, weekly_league_points). |
| `POST /users/action` | Mutating: `action ∈ grant_premium\|revoke_premium\|unlock_concept_wall\|trigger_concept_wall\|award_xp\|reset_chat_cap`, `target_id`, `value?`. Writes `subscriptions`, `micro_states`, `hermes_gamification`. |
| `GET/POST /questions`, `PUT/DELETE /questions/{id}` | PYQ CMS; persisted to a local JSON file (`:74-82`). |
| `GET/POST /flashcards`, `DELETE /flashcards/{id}` | Flashcard CMS. |
| `GET /colleges`, `PUT /colleges/{college_id}` | College cutoff read/update. |
| `GET /assessments` | Assessment listing. |
| `GET/PUT /system-config` | Chat caps, mastery threshold, rate limit, maintenance mode (+ SOUL prompt + audit log on GET). |

**Superadmin has NO visibility into `diagnostic_tests`, test submissions, `analytics_reports`,
or `schedules`** — no endpoint references them (gap #8).

### J. Environment variables that matter

| Env var | Used by | Notes |
|---|---|---|
| `GOOGLE_API_KEY` | Gemini services | Missing → ProviderUnavailable paths |
| `GEMINI_MODEL` | Gemini services | Default `gemini-2.5-flash-lite` |
| `FIREBASE_CREDENTIALS_PATH`, `FIREBASE_PROJECT_ID` | `utils/firebase_config.py` | Firestore client |
| `FIREBASE_API_KEY` | `login_service.py:215-252` | If absent, parent email password check silently skipped |
| `JWT_SECRET` / `JWT_SECRET_KEY` | `token_service.py:53` | Required to mint/verify tokens |
| `TESTING_MODE` / `ENVIRONMENT` | `core/config.py` | `testing_mode=True` default; refused when `ENVIRONMENT=production` |
| `SEED_ON_STARTUP` | `main.py:77` | Seeds v1 in-memory domain |

## 8. Verified request/response contracts (canonical JSON)

Parent registration (simple):
```json
POST /api/auth/register/simple
{"name":"Rajesh Sharma","email_address":"rajesh@example.com","password":"Passw0rd1","repeat_password":"Passw0rd1","mobile_number":"+919876543210"}
→ 201 {"parent_id":"<firebase-uid>","email":"rajesh@example.com","phone":"+919876543210","verification_required":false,"message":"Registration successful"}
```

Parent login:
```json
POST /api/auth/login/email
{"email":"rajesh@example.com","password":"Passw0rd1"}
→ 200 {"token":"<jwt>","refresh_token":"<jwt>","parent_id":"<id>","email":"rajesh@example.com","phone":null,"expires_in":86400,"student_id":null,"child_id":null,"username":null,"name":null,"is_student":false,"message":null}
```

Child login:
```json
POST /api/auth/login/child
{"username":"aarav_jee2026","password":"Passw0rd1"}
→ 200 {"token":"<jwt>","refresh_token":"<jwt>","parent_id":"<parent-id>","email":"aarav_jee2026@student.local","expires_in":86400,"student_id":"child_abc123","child_id":"child_abc123","username":"aarav_jee2026","name":"Aarav","is_student":true,"message":"Child login successful"}
```

Child profile creation:
```json
POST /api/onboarding/child?parent_id=<id>
{"name":"Aarav Sharma","age":16,"grade":11,"current_level":"intermediate","username":"aarav_jee2026","password":"Passw0rd1"}
→ 201 {"child_id":"child_abc123","parent_id":"<id>","name":"Aarav Sharma","age":16,"grade":11,"current_level":"intermediate","username":"aarav_jee2026","created_at":"...","updated_at":"..."}
```

Exam selection (schedules the diagnostic test):
```json
POST /api/onboarding/exam/select?parent_id=<id>&child_id=child_abc123
{"exam_type":"JEE_MAIN","exam_date":"2027-04-15T09:00:00+05:30","subject_preferences":{"Physics":35,"Chemistry":30,"Mathematics":35}}
→ 201 {"child_id":"child_abc123","exam_type":"JEE_MAIN","exam_date":"...","subject_preferences":{"Physics":35,"Chemistry":30,"Mathematics":35},"days_until_exam":529,"diagnostic_test_id":"test_xyz789","created_at":"..."}
```
(Service additionally enforces `exam_date` ≥ 30 days in the future — 400 otherwise,
`exam_service.py:279-284`.)
```

Test submission:
```json
POST /api/diagnostic-test/test_xyz789/submit
{"test_id":"test_xyz789","student_id":"child_abc123","answers":{"1":"B","2":"","3":"D"},"time_taken":5400,"submission_time":"2026-11-02T10:00:00Z"}
→ 200 {"test_id":"test_xyz789","student_id":"child_abc123","total_score":4,"total_marks":12,"percentage":33.33,"section_scores":{"Physics":{"section_name":"Physics","score":4,"total_marks":12,"correct":1,"incorrect":0,"unattempted":2}},"correct_count":1,"incorrect_count":0,"unattempted_count":2}
```

Analytics generation + polling:
```json
POST /api/analytics/generate
{"test_id":"test_xyz789","student_id":"child_abc123","answers":{"1":"B","2":"D"},"include_ai_insights":true,"use_cache":true}
→ 202 {"analytics_id":"analytics_test_xyz789_child_abc123_1699999999","status":"pending","message":"Analytics generation started","report":null,"error":null,"progress":null}
GET /api/analytics/analytics_test_xyz789_child_abc123_1699999999
→ 200 {"analytics_id":"...","overview":{ "test_id":"...", "student_id":"...", "exam_type":"JEE_MAIN", "total_score":62, "max_score":120, ...}, "subject_analysis":[...], "topic_analysis":[...], "ai_insights":{...}, "priority_topics":[...], "generated_at":"..."}
```
(The poll returns the **bare `AnalyticsReport`** — no `status`/`message` wrapper; §7.E.)
```

Schedule generation:
```json
POST /api/schedule/generate
{"student_id":"child_abc123","analytics_id":"analytics_...","exam_type":"JEE_MAIN","exam_date":"2027-04-15","daily_study_hours":4.0,"preferences":{}}
→ 201 {"schedule_id":"schedule_child_abc123_...","student_id":"child_abc123","analytics_id":"...","exam_type":"JEE_MAIN","exam_date":"2027-04-15","generated_date":"2026-11-02","total_days":120,"daily_study_hours":4.0,"status":"active","days":[{"day_number":1,"schedule_date":"2026-11-03","subjects":["Physics"],"topics":[{"topic":"Kinematics","subject":"Physics","priority":"high","estimated_hours":2.0,"subtopics":[...],"resources":[...],"goals":[...]}],"total_hours":4.0,"milestones":[...],"completed":false,"completion_percentage":0.0}],"revision_days":[...],"practice_test_days":[...],"buffer_days":[...],"priority_topics":[...]}
```

---

## 9. Complete endpoint inventory

**Column semantics**
- **AuthN** — `none` (public) · `JWT` (Bearer token verified + session revocation check) · `bypass` (testing bypass: header ignored, constant user) · `header` (v1 `X-User-Id`/`X-User-Role` headers, only meaningful when `TESTING_MODE=true`) · `self` (endpoint authenticates itself, e.g. parses its own token).
- **AuthZ** — roles allowed and ownership scope. `"—"` = none enforced.
- **Errors** — realistic status codes for that endpoint. Exact bodies: v1 → `{"error":{"code","message","details","request_id"}}` (§4); legacy → `{"detail": str}`. `V` = 422 validation, `A` = 401, `F` = 403, `N` = 404, `C` = 409, `R` = 429, `P` = 503. `500` is always possible via the global catch-all.
- **Consumer** — `flutter` (new Flutter app) · `superadmin` (superadmin panel) · `web` (existing `Frontend_Website` SPA) · `internal` (backend/testing only, never a client) · `unused` (no legitimate consumer in scope; reason given).
- **Phase** — documentation phase integrating the endpoint (`P04`…`P13`), or `—` when not consumed.

### 9.1 eKLAVYA v1 routers — prefix `/api/v1` (`main.py:165-166`; registry `routers/eklavya_registry.py:22`)

AuthN: `header` on every endpoint. AuthZ: role-scoped via `core/access.py` (students own records; teachers via class; parents read-only via `ParentLink`; admin all). Storage: in-memory, seeded. **Consumer: `internal` — testing playground only.** None of these endpoints are consumed by the Flutter app or superadmin panel. They are listed here for completeness; the traceability check (§10) accounts for them collectively.

**syllabus_router.py** — no router prefix.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| GET `/api/v1/syllabi` | List syllabi | Principal | `limit,cursor` | limit 1–100 | 200 `Page[Syllabus]` | A,F,R | internal · — · — | `syllabus_router.py:51` |
| GET `/api/v1/syllabi/{syllabus_id}` | Get syllabus | Principal | path id | exists | 200 `Syllabus` | A,F,N | internal · — · — | `:66` |
| GET `/api/v1/syllabi/{syllabus_id}/subjects` | List subjects | Principal | limit/cursor | — | 200 `Page[Subject]` | A,F,R | internal · — · — | `:79` |
| GET `/api/v1/subjects/{subject_id}/chapters` | List chapters | Principal | limit/cursor | — | 200 `Page[Chapter]` | A,F,N,R | internal · — · — | `:95` |
| GET `/api/v1/chapters/{chapter_id}/topics` | List topics | Principal | limit/cursor | — | 200 `Page[Topic]` | A,F,N,R | internal · — · — | `:111` |
| GET `/api/v1/me/syllabus-profile` | Get profile | own student | `?student_id` | — | 200 `SyllabusProfile` | A,F,N | internal · — · — | `:127` |
| PUT `/api/v1/me/syllabus-profile` | Update profile | own student | body `SyllabusProfileUpdate` + `?student_id` | version, enums | 200 `SyllabusProfile` | A,F,N,C,V | internal · — · — | `:140` |
| GET `/api/v1/me/syllabus-progress` | Get progress | own student | `?student_id` | — | 200 `SyllabusProgress` | A,F,N | internal · — · — | `:156` |
| POST `/api/v1/teacher/syllabus-templates` | Create template | teacher | body `SyllabusTemplateCreate` (+Idempotency-Key) | name/payload | 201 `SyllabusTemplate` | A,F,V,C | internal · — · — | `:169` |
| POST `/api/v1/teacher/syllabus-templates/{template_id}/publish` | Publish template | teacher | path id (+Idem-Key) | exists | 200 `SyllabusTemplate` | A,F,N,C,V | internal · — · — | `:205` |

**planner_router.py** — all `Principal`.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| GET `/api/v1/planner/today` | Today's plan | own student | `?student_id` | — | 200 `TodayOut` | A,F,N | internal · — · — | `planner_router.py:56` |
| GET `/api/v1/planner/tasks` | List tasks | own student | `?student_id,from,to,status,subjectId` + limit/cursor | date format | 200 `Page[TaskOut]` | A,F,R,V | internal · — · — | `:69` |
| POST `/api/v1/planner/tasks` | Create task | own student | body `TaskCreate` + `?student_id` (+Idem-Key) | scheduled_date required | 201 `TaskOut` | A,F,V,C | internal · — · — | `:91` |
| GET `/api/v1/planner/tasks/{task_id}` | Get task | owner | path id | exists | 200 `TaskOut` | A,F,N | internal · — · — | `:126` |
| PATCH `/api/v1/planner/tasks/{task_id}` | Update task | owner | body `TaskUpdate` (version) | optimistic lock | 200 `TaskOut` | A,F,N,C,V | internal · — · — | `:139` |
| POST `/api/v1/planner/tasks/{task_id}/complete` | Complete task | owner | opt body `{actual_minutes}` (+Idem-Key) | — | 200 `TaskOut` | A,F,N,C | internal · — · — | `:153` |
| POST `/api/v1/planner/tasks/{task_id}/reschedule` | Reschedule | owner | body `RescheduleIn` | scheduled_date required | 200 `TaskOut` | A,F,N,V,C | internal · — · — | `:187` |
| POST `/api/v1/planner/generate` | Generate plan | own student | body `{days}` (+Idem-Key) | — | 202/200 `GenerationJobOut` | A,F,V,C | internal · — · — | `:205` |
| POST `/api/v1/planner/replan` | Replan | own student | body `{from_date?}` (+Idem-Key) | — | `GenerationJobOut` | A,F,V,C | internal · — · — | `:237` |
| GET `/api/v1/planner/generation-jobs/{job_id}` | Job status | owner | path id | exists | 200 `GenerationJobOut` | A,F,N | internal · — · — | `:269` |
| POST `/api/v1/study-sessions` | Start session | own student | body `{task_id?}` (+Idem-Key) | — | 201 `SessionOut` | A,F,V,C | internal · — · — | `:286` |
| PATCH `/api/v1/study-sessions/{session_id}` | Session action | owner | body `SessionPatch` (action) | enum | 200 `SessionOut` | A,F,N,C,V | internal · — · — | `:320` |
| GET `/api/v1/revision/due` | Due revisions | own student | `?student_id` + limit/cursor | — | 200 `Page[RevisionItemOut]` | A,F,R | internal · — · — | `:338` |
| POST `/api/v1/revision/{revision_id}/complete` | Complete revision | owner | path id | exists | 200 `RevisionItemOut` | A,F,N | internal · — · — | `:354` |

**notes_router.py** — `Principal`; owner-only (`assert_owner_access`, admin sees all).

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| GET `/api/v1/notes` | List notes | `?query,topicId,tag` + limit/cursor | — | 200 `Page[NoteOut]` | A,F,R | internal · — · — | `notes_router.py:62` |
| POST `/api/v1/notes` | Create note | body `NoteCreate` (+Idem-Key) | title required | 201 `NoteOut` | A,F,V,C | internal · — · — | `:80` |
| GET `/api/v1/notes/{note_id}` | Get note | path id | exists+owner | 200 `NoteOut` | A,F,N | internal · — · — | `:113` |
| PATCH `/api/v1/notes/{note_id}` | Update note | body `NoteUpdate` (version) | optimistic lock | 200 `NoteOut` | A,F,N,C,V | internal · — · — | `:127` |
| DELETE `/api/v1/notes/{note_id}` | Archive note | path id | exists+owner | 204 | A,F,N | internal · — · — | `:147` |
| GET `/api/v1/notes/{note_id}/versions` | Versions | limit/cursor | — | 200 `Page[NoteVersion]` | A,F,N,R | internal · — · — | `:161` |
| POST `/api/v1/notes/{note_id}/restore` | Restore | body `{version}` | — | 200 `NoteOut` | A,F,N,V | internal · — · — | `:177` |
| POST `/api/v1/notes/{note_id}/attachments` | Upload file | multipart `file` | PNG/JPEG/PDF magic bytes | 201 `Attachment` | A,F,N,413,415 | internal · — · — | `:192` |
| POST `/api/v1/notes/{note_id}/links` | Link note | body `{linked_note_id}` | — | 200 `NoteOut` | A,F,N,V | internal · — · — | `:209` |
| DELETE `/api/v1/notes/{note_id}/links/{linked_note_id}` | Unlink | path ids | — | 204 | A,F,N | internal · — · — | `:224` |
| POST `/api/v1/notes/{note_id}/export` | Export | body `{format: txt\|pdf}` | enum | 201 `ExportOut` | A,F,N,V | internal · — · — | `:239` |
| POST `/api/v1/notes/{note_id}/share` | Share | body `ShareIn` | level required | 200 `NoteOut` | A,F,N,V | internal · — · — | `:256` |
| POST `/api/v1/notes/{note_id}/ai-actions` | AI action | body `AiActionIn` | action required | 200 `AiActionOut` | A,F,N,V,P | internal · — · — | `:271` |

**mindmap_router.py** — `Principal`.

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| GET `/api/v1/mindmaps` | List maps | limit/cursor | — | 200 `Page[MapOut]` | A,F,R | internal · — · — | `mindmap_router.py:52` |
| POST `/api/v1/mindmaps` | Create map | body `MapCreate` (+Idem-Key) | title required | 201 `MapOut` | A,F,V,C | internal · — · — | `:67` |
| GET `/api/v1/mindmaps/{map_id}` | Get map | path id | exists | 200 `MapOut` | A,F,N | internal · — · — | `:99` |
| PATCH `/api/v1/mindmaps/{map_id}` | Update map | body `MapUpdate` (version) | — | 200 `MapOut` | A,F,N,C,V | internal · — · — | `:112` |
| DELETE `/api/v1/mindmaps/{map_id}` | Delete map | path id | exists | 204 | A,F,N | internal · — · — | `:126` |
| POST `/api/v1/mindmaps/{map_id}/nodes` | Add node | body `NodeCreate` (+Idem-Key) | label required | 201 `NodeOut` | A,F,N,V,C | internal · — · — | `:140` |
| PATCH `/api/v1/mindmaps/{map_id}/nodes/{node_id}` | Update node | body `NodeUpdate` | — | 200 `NodeOut` | A,F,N,V | internal · — · — | `:173` |
| DELETE `/api/v1/mindmaps/{map_id}/nodes/{node_id}` | Delete node | path ids (root protected) | — | 204 | A,F,N,C | internal · — · — | `:188` |
| POST `/api/v1/mindmaps/{map_id}/edges` | Add edge | body `EdgeCreate` | source+target required | 201 `EdgeOut` | A,F,N,V | internal · — · — | `:203` |
| DELETE `/api/v1/mindmaps/{map_id}/edges/{edge_id}` | Delete edge | path ids | — | 204 | A,F,N | internal · — · — | `:218` |
| POST `/api/v1/mindmaps/{map_id}/generate` | AI generate | path id (+Idem-Key) | — | `GenerateOut` | A,F,N,C,P | internal · — · — | `:233` |
| POST `/api/v1/mindmaps/{map_id}/regenerate-branch` | Regenerate branch | body `{node_id}` | — | `GenerateOut` | A,F,N,V,P | internal · — · — | `:264` |
| GET `/api/v1/mindmaps/{map_id}/revisions` | Revisions | limit/cursor | — | 200 `Page[RevisionOut]` | A,F,N,R | internal · — · — | `:278` |
| POST `/api/v1/mindmaps/{map_id}/export` | Export | opt body `{format}` | — | `ExportOut` | A,F,N | internal · — · — | `:294` |

**scan_router.py** — `Principal`; owner/admin only.

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| POST `/api/v1/scans` | Create scan | body `ScanCreate` (+Idem-Key) | intent required | 201 `ScanOut` | A,F,V,C | internal · — · — | `scan_router.py:44` |
| POST `/api/v1/scans/{scan_id}/pages` | Upload page | multipart `file`, `page_number?` | image/pdf | 201 `PageOut` | A,F,N,413,415 | internal · — · — | `:77` |
| POST `/api/v1/scans/{scan_id}/process` | Run OCR+ | path id | exists | 200 `ScanOut` | A,F,N,P | internal · — · — | `:98` |
| GET `/api/v1/scans/{scan_id}` | Get scan | path id | — | 200 `ScanOut` | A,F,N | internal · — · — | `:113` |
| GET `/api/v1/scans/{scan_id}/ocr` | Get OCR text | path id | — | 200 `OcrOut` | A,F,N | internal · — · — | `:126` |
| PUT `/api/v1/scans/{scan_id}/ocr-confirmation` | Confirm OCR | body `{text}` | — | 200 `ScanOut` | A,F,N,V | internal · — · — | `:139` |
| POST `/api/v1/scans/{scan_id}/execute` | Execute intent | body `{steps?}` (+Idem-Key) | — | `ExecutionOut` | A,F,N,C,P | internal · — · — | `:154` |
| GET `/api/v1/scans/{scan_id}/result` | Result | path id | — | `ResultOut` | A,F,N | internal · — · — | `:198` |
| POST `/api/v1/scans/{scan_id}/save-note` | Save as note | path id | idempotent | 201/200 `Note` | A,F,N,C | internal · — · — | `:211` |
| POST `/api/v1/scans/{scan_id}/create-mindmap` | Make mindmap | path id | idempotent | 201/200 `MindMap` | A,F,N,C | internal · — · — | `:243` |
| POST `/api/v1/scans/{scan_id}/schedule-revision` | Schedule revision | path id | idempotent | 201/200 `RevisionItem` | A,F,N,C | internal · — · — | `:279` |

**speech_router.py** — `Principal`; owner/admin.

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| POST `/api/v1/speech` | Create asset | body `SpeechCreate` (+Idem-Key) | source_type, transcript | 201/200 `SpeechAssetOut` | A,F,V,C | internal · — · — | `speech_router.py:35` |
| GET `/api/v1/speech/{speech_asset_id}` | Get asset | path id | exists+owner | 200 `SpeechAssetOut` | A,F,N | internal · — · — | `:78` |
| GET `/api/v1/speech/{speech_asset_id}/playback-url` | Playback URL | path id | — | 200 `PlaybackUrlOut` | A,F,N | internal · — · — | `:92` |

**communication_router.py** — `Principal`; call creation teacher/admin only.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/v1/simulated-calls` | Create call | teacher/admin | body `CallCreate` (+Idem-Key) | transcript required | 201 `CallOut` | A,F,V,C | internal · — · — | `communication_router.py:45` |
| GET `/api/v1/simulated-calls` | List calls | sender (admin all) | limit/cursor | — | 200 `Page[CallOut]` | A,F,R | internal · — · — | `:100` |
| GET `/api/v1/simulated-calls/{call_id}` | Get call | sender/admin/recipient | path id | — | 200 `CallOut` | A,F,N | internal · — · — | `:116` |
| POST `/api/v1/simulated-calls/{call_id}/cancel` | Cancel | sender/admin | path id | — | 200 `CallOut` | A,F,N | internal · — · — | `:130` |
| GET `/api/v1/me/simulated-calls` | My deliveries | recipient | limit/cursor | — | 200 `Page[MyDeliveryOut]` | A,F,R | internal · — · — | `:144` |
| POST `/api/v1/me/simulated-calls/{delivery_id}/accept` | Accept | recipient | path id | — | 200 `DeliveryOut` | A,F,N | internal · — · — | `:159` |
| POST `/api/v1/me/simulated-calls/{delivery_id}/dismiss` | Dismiss | recipient | path id | — | 200 `DeliveryOut` | A,F,N | internal · — · — | `:173` |
| POST `/api/v1/me/simulated-calls/{delivery_id}/playback-started` | Playback started | recipient | path id | — | 200 `DeliveryOut` | A,F,N | internal · — · — | `:187` |
| POST `/api/v1/me/simulated-calls/{delivery_id}/complete` | Complete | recipient | path id (idempotent) | — | 200 `DeliveryOut` | A,F,N | internal · — · — | `:203` |
| GET `/api/v1/messages` | Messages | owner | `?unread` + limit/cursor | — | 200 `Page[MessageOut]` | A,F,R | internal · — · — | `:217` |
| POST `/api/v1/messages/{message_id}/read` | Mark read | owner | path id | — | 200 `MessageOut` | A,F,N | internal · — · — | `:236` |

**teacher_router.py** — `Principal` + teacher/admin; class-scoped (404 if teacher not in class).

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| GET `/api/v1/teacher/classes/{class_id}/progress` | Class progress | limit/cursor | class membership | 200 `Page[ProgressSummaryOut]` | A,F,N,R | internal · — · — | `teacher_router.py:55` |
| POST `/api/v1/teacher/classes/{class_id}/tasks` | Create tasks | body `TeacherTaskCreate` (+Idem-Key) | title required | 201 `TeacherTaskCreateOut` | A,F,N,V,C | internal · — · — | `:72` |
| POST `/api/v1/teacher/classes/{class_id}/resources` | Share resource | body `ResourceShareIn` | title required | 201 `ResourceShareOut` | A,F,N,V | internal · — · — | `:122` |
| GET `/api/v1/teacher/reviews` | Scan reviews | limit/cursor | — | 200 `Page[ReviewOut]` | A,F,R | internal · — · — | `:145` |
| POST `/api/v1/teacher/reviews/{review_id}/resolve` | Resolve review | body `ReviewResolveIn` | resolution required | `ReviewResolveOut` | A,F,N,V | internal · — · — | `:161` |

**parent_router.py** — `Principal` parent role; read-only, scoped to linked children.

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| GET `/api/v1/parent/children` | Linked children | limit/cursor | link exists | 200 `Page[ChildOut]` | A,F,R | internal · — · — | `parent_router.py:41` |
| GET `/api/v1/parent/children/{student_id}/progress` | Child progress | path id | linked | 200 `SyllabusProgress` | A,F,N | internal · — · — | `:56` |
| GET `/api/v1/parent/children/{student_id}/reports` | Child report | path id | linked | 200 `ReportOut` | A,F,N | internal · — · — | `:70` |
| GET `/api/v1/parent/communication-preferences` | Get prefs | — | — | 200 `PrefsOut` | A,F | internal · — · — | `:83` |
| PUT `/api/v1/parent/communication-preferences` | Update prefs | body `PrefsUpdate` | — | 200 `PrefsOut` | A,F,V | internal · — · — | `:96` |

### 9.2 Auth & onboarding routers (Stack 1)

**auth_router.py** — prefix `/api/auth`, tag "Authentication". AuthN: `none` (public).

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/auth/register/parent/email` | Register parent w/ email | — | body `ParentEmailRegisterRequest` | email format; password ≥8 with letter+digit; `language ∈ en\|hi\|mr` | 201 `AuthResponse` (no token) | V,C (email exists) | flutter · Parent registration · P05 | `auth_router.py:41`, `auth_models.py:23` |
| POST `/api/auth/register/parent/phone` | Register parent w/ phone | — | body `ParentPhoneRegisterRequest` | phone `^\+91[6-9]\d{9}$`; no password collected | 201 `AuthResponse` | V,C | flutter · Parent registration (phone) · P05 | `auth_router.py:133`, `auth_models.py:97` |
| POST `/api/auth/register/parent/google` | Register parent w/ Google | — | body `ParentGoogleRegisterRequest` | `id_token` ≥50 chars, verified via Firebase | 201 `AuthResponse` | V,A(unverified token) | flutter · Parent registration (Google) · P05 | `auth_router.py:223` |

**simple_register_router.py** — prefix `/api/auth`.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/auth/register/simple` | Register parent (simple form) | — | body `SimpleRegisterRequest` | name 2–100; email; password ≥8 letter+digit; repeat_password match; mobile_number | 201 `AuthResponse` | V,C | flutter · Parent registration · P05 | `simple_register_router.py:31` |

**login_router.py** — prefix `/api/auth`, tag "Login". AuthN: `self` / `none`.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/auth/login/email` | Parent email login | — | body `EmailLoginRequest{email,password}` | email format | 200 `LoginResponse` (token+refresh, expires_in 86400) | A(wrong creds),V,P(Firebase down) | flutter · Parent login · P04/P05 | `login_router.py:97` |
| POST `/api/auth/login/phone` | Parent phone+OTP login | — | body `PhoneLoginRequest{phone,otp?}` | phone format; OTP 6-digit, 10-min expiry, single-use | 200 `LoginResponse` | A(invalid OTP),V | flutter · Parent login · P04/P05 | `login_router.py:203` |
| POST `/api/auth/login/google` | Parent Google login | — | body `GoogleLoginRequest{id_token}` | Firebase-verified | 200 `LoginResponse` | A,V | flutter · Parent login · P04/P05 | `login_router.py:311` |
| POST `/api/auth/token/refresh` | Rotate parent tokens | valid refresh token | body `TokenRefreshRequest{refresh_token}` | JWT verify + session not revoked | 200 `TokenResponse{token,refresh_token,expires_in}` | A,V | flutter · Session restore · P04 | `login_router.py:409` |
| POST `/api/auth/logout` | Parent logout | Bearer | `Authorization` header | session revoked | 200 `LogoutResponse` | A | flutter · Logout · P04 | `login_router.py:501` |
| GET `/api/auth/me` | Parent profile | Bearer | `Authorization` header | — | 200 Firestore parent doc | A | flutter · Profile/settings · P05 | `login_router.py:592` |
| POST `/api/auth/login/child` | **Child login** | — | body `ChildLoginRequest{username,password}` | username 3–30 `^[a-zA-Z0-9_@.]+$`; password 8–50 letter+digit | 200 `LoginResponse` (`is_student:true`, `student_id`=`child_id`) | A(wrong creds),V | flutter · Child login · P07 | `login_router.py:719`, `login_models.py:453` |
| POST `/api/auth/token/refresh/child` | Rotate child tokens | valid child refresh | body `TokenRefreshRequest` | JWT verify + session | 200 `TokenResponse` | A,V | flutter · Child session restore · P07 | `login_router.py:830` |
| POST `/api/auth/logout/child` | Child logout | child Bearer | `Authorization` header | — | 200 `LogoutResponse` | A | flutter · Child logout · P07 | `login_router.py:922` |
| GET `/api/auth/me/child` | Child profile | child Bearer | `Authorization` header | — | 200 child doc | A | flutter · Child dashboard · P07 | `login_router.py:1013` |

**verification_router.py** — no prefix (paths `/verify/*`), tag "Verification". AuthN: `bypass` on send + phone-confirm.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/verify/email/send` | Send email code | — | body `{email}` + auth dep | email format | 200 `{message, code?}` (code returned in dev) | V,R | flutter · Parent email verification · P05 | `verification_router.py:43` |
| POST `/verify/email/confirm` | Confirm email code | — | body `{email,code}` | 6-char code, single-use, 10-min | 200 `VerificationResponse` | A,V | flutter · Parent email verification · P05 | `verification_router.py:131` |
| POST `/verify/phone/send` | Send phone OTP | — | body `{phone}` + auth dep | phone format | 200 `{message, otp?}` | V,R | flutter · Parent phone verification · P05 | `verification_router.py:230` |
| POST `/verify/phone/confirm` | Confirm OTP | — | body `{phone,otp}` | 6-digit OTP | 200 `VerificationResponse` | A,V | flutter · Parent phone verification/OTP login · P05 | `verification_router.py:318` |

**preferences_router.py** — prefix `/api/onboarding`. AuthN: `?parent_id=` query only (temporary).

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/onboarding/preferences` | Save parent preferences | — | body `PreferencesRequest` + `?parent_id` | language; notification booleans; teaching_involvement | 201 `PreferencesResponse` | V | web · Onboarding (optional for Flutter) · — | `preferences_router.py:40` |
| GET `/api/onboarding/preferences` | Get preferences | — | `?parent_id` | — | 200 `PreferencesResponse` | N | web · Onboarding · — | `preferences_router.py:150` |
| PUT `/api/onboarding/preferences` | Update preferences | — | body `PreferencesUpdate` + `?parent_id` | — | 200 `PreferencesResponse` | V,N | web · Onboarding · — | `preferences_router.py:245` |

**child_router.py** — prefix `/api/onboarding`, tag "Onboarding - Child Profile". AuthN: `?parent_id=` query.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/onboarding/child` | Create child profile + credentials | — | body `ChildProfileRequest` + `?parent_id` | name 2–100; age 14–19; grade 9–12; level enum; username 3–30 regex; password 8–50 letter+digit. One child per parent (400) | 201 `ChildProfileResponse` (also creates Firebase user) | V,C(one-child),A(Firebase) | flutter · Child profile creation · P06 | `child_router.py:41`, `child_models.py:22`, `child_service.py:122-179` |
| GET `/api/onboarding/child` | Get child profile | — | `?parent_id` | has child | 200 `ChildProfileResponse` | N | flutter · Child management · P06 | `child_router.py:164` |
| PUT `/api/onboarding/child/{child_id}` | Update profile | — | path id + body `ChildProfileUpdate` + `?parent_id` | name/age/grade/level; **username/password silently dropped** (gap #2) | 200 `ChildProfileResponse` | V,N | flutter · Child management · P06 | `child_router.py:262`, `child_service.py:416-442` |
| DELETE `/api/onboarding/child/{child_id}` | Delete child | — | path id + `?parent_id` | — | 200 dict | N | flutter · Child management · P06 | `child_router.py:381` |

**exam_router.py** — prefix `/api/onboarding`, tag "Onboarding - Exam Selection". AuthN: `?parent_id=`/`?child_id=` query.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| GET `/api/onboarding/exams/available` | List exams | — | — | — | 200 `AvailableExamsResponse` | — | flutter · Test scheduling · P08 | `exam_router.py:44` |
| POST `/api/onboarding/exam/select` | Select exam → schedules diagnostic test | — | body `ExamSelectionRequest` + `?parent_id` + `?child_id` | exam_type enum; exam_date future; subject_preferences sum=100, exact subject set per exam | 200 `ExamSelectionResponse` (with `diagnostic_test_id`) | V,N,C | flutter · Test scheduling · P08 | `exam_router.py:133`, `exam_models.py:24`, `exam_service.py:154-218` |
| GET `/api/onboarding/exam/preferences` | Get selection | — | `?child_id` | has selection | 200 `ExamSelectionResponse` | N | flutter · Test scheduling · P08 | `exam_router.py:270` |
| PUT `/api/onboarding/exam/preferences` | Update weights | — | `Dict[str,int]` body + `?child_id` | sum=100, subject set | 200 `ExamSelectionResponse` | V,N | flutter · Test scheduling · P08 | `exam_router.py:372` |
| GET `/api/onboarding/status` | Onboarding checklist | — | `?parent_id` | — | 200 `{preferences_completed, child_profile_completed, exam_selected, onboarding_complete}` | — | flutter · Dashboard/onboarding resume · P05/P06/P08 | `exam_router.py:492` |

### 9.3 Vector search / RAG / questions

**embedding_router.py** — prefix `/api/vector-search/embeddings`. AuthN: `JWT`.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `…/embeddings/generate` | Embed text | — | body `EmbeddingRequest` | text, task_type required | 200 `EmbeddingResponse` | A,V,P | internal · RAG pipeline · — | `embedding_router.py:104` |
| POST `…/embeddings/batch` | Batch embed | — | body `BatchEmbeddingRequest` | texts required | 200 `BatchEmbeddingResponse` | A,V,P | internal · RAG pipeline · — | `:310` |
| GET `…/embeddings/status` | Service status | — | — | — | 200 dict | A | internal · — · — | `:493` |

**vector_search_router.py** — prefix `/api/vector-search`. AuthN: `bypass` (TESTING_MODE) or `JWT`.

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| POST `/api/vector-search/query` | Semantic search | body `SearchRequest` | query required | 200 `SearchResponse` | A,V,P | internal · RAG · — | `vector_search_router.py:113` |
| POST `/api/vector-search/query/batch` | Batch search | body `BatchSearchRequest` (1–20 queries) | queries required | 200 `BatchSearchResponse` | A,V,P | internal · RAG · — | `:277` |
| GET `/api/vector-search/index/status` | Index status | — | — | 200 dict | A | internal · — · — | `:421` |
| GET `/api/vector-search/syllabus/{exam}/{subject}` | Syllabus content | path exam,subject | — | 200 dict | A,N | internal · — · — | `:541` |
| GET `/api/vector-search/syllabus/stats` | Syllabus stats | — | — | 200 dict | A | internal · — · — | `:667` |

**rag_router.py** — prefix `/api/rag`. AuthN: `none`.

| Endpoint | Purpose | Input | Validation | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|---|
| POST `/api/rag/generate-questions` | Generate questions | body `RAGRequest` | topic required | 200 `RAGResponse` | V,P | internal · question generation · — | `rag_router.py:104` |
| POST `/api/rag/generate-batch` | Batch generate | body `QuestionGenerationRequest` | topics required | 200 dict | V,P | internal · question generation · — | `:250` |
| POST `/api/rag/context/build` | Build context | `Dict[str,str]` body | — | 200 dict | V,P | internal · — · — | `:412` |
| POST `/api/rag/context/preview` | Preview context | `Dict[str,str]` body | — | 200 dict | V,P | internal · — · — | `:520` |
| GET `/api/rag/pipeline/status` | Pipeline health | — | — | 200 `HealthStatus` | P | internal · — · — | `:632` |
| GET `/api/rag/metrics` | Metrics | — | — | 200 `GenerationMetrics` | — | internal · — · — | `:722` |

**question_router.py** — prefix `/api/questions`. ⚠ **NOT mounted in `main.py` — unreachable in the running app.**

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| POST `/api/questions/generate` | Generate | body `RAGRequest` | `RAGResponse` | unused — router unmounted (gap #10) · — · — | `question_router.py:125` |
| GET `/api/questions/{question_id}` | Get question | path Firestore id | `Question` | unused — router unmounted · — · — | `:228` |
| GET `/api/questions/by-topic/{topic}` | By topic | path topic | `QuestionBatch` | unused — router unmounted · — · — | `:303` |
| POST `/api/questions/validate` | Validate | body `Question` | `ValidationResult` | unused — router unmounted · — · — | `:477` |
| POST `/api/questions/search` | Search | body `QuestionFilter` + `?limit` | `QuestionBatch` | unused — router unmounted · — · — | `:576` |
| GET `/api/questions/stats` | Stats | `?exam_type` | dict | unused — router unmounted · — · — | `:728` |

### 9.4 Diagnostic tests, schedule, payment

**diagnostic_test_router.py** — prefix `/api/diagnostic-test`, tag "Diagnostic Test". AuthN: `bypass` (returns `str`; some handlers subscript it as dict → 500, gap #7-adjacent). All handlers are **mocks** (gap #4).

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/diagnostic-test/generate` | Generate test | — | body `TestGenerationRequest` | exam_type required | 201 `TestGenerationResult` | V,P | flutter · (reserved; not scheduling path) · P08 ref | `:144` |
| POST `/api/diagnostic-test/generate-async` | Async generate | — | same body | — | 202 dict | V,P | flutter · (reserved) · P08 ref | `:269` |
| GET `/api/diagnostic-test/generation/status/{job_id}` | Gen job status | — | path job_id | — | 200 `GenerationStatusResponse` | N | flutter · (reserved) · P08 ref | `:371` |
| GET `/api/diagnostic-test/{test_id}` | Get full test w/ questions | — | path id | — | **501 Not Implemented** | N,501 | flutter · Test-taking · P09 (blocked, gap #4) | `:452` |
| GET `/api/diagnostic-test/{test_id}/metadata` | Test metadata | — | path id | — | 200 `TestMetadata` | N | flutter · Test-taking · P09 | `:523` |
| GET `/api/diagnostic-test/student/{student_id}` | Child's tests | — | `?status,limit=10,offset=0` | — | 200 `List[TestMetadata]` (mock) | N | flutter · Child dashboard · P07/P09 | `:595` |
| DELETE `/api/diagnostic-test/{test_id}` | Delete test | — | path id | — | 200 `SuccessResponse` | N | internal · — · — | `:696` |
| GET `/api/diagnostic-test/health` | Health | — | — | — | 200 | — | internal · — · — | `:784` |
| POST `/api/diagnostic-test/schedule` | Mock schedule | — | raw dict body | — | 201 canned `{"status":"scheduled"}` (no Firestore write) | — | unused — mock; use `/api/onboarding/exam/select` instead · — · — | `:803` |
| GET `/api/diagnostic-test/{test_id}/status` | Test status | — | path id | — | 200 dict | N | flutter · Test-taking · P09 | `:911` |
| POST `/api/diagnostic-test/{test_id}/start` | Start attempt | — | dict body | — | 200 dict (mock) | N | flutter · Test-taking · P09 | `:970` |
| POST `/api/diagnostic-test/{test_id}/submit` | Submit answers | — | `TestSubmission` | answers `Dict[int,str]` (A–D/empty/numeric); time_taken ≥0 | 200 `TestResults` (mock scoring) | V,N | flutter · Test submission · P09 | `:1032` |
| GET `/api/diagnostic-test/{test_id}/results` | Results | — | path id | — | 200 `TestResults` | N | flutter · Results · P09/P10 | `:1095` |

**test_management_router.py** — prefix `/api/diagnostic-test`, tag "Test Management". AuthN: local mock (`:57` always `test_student_123`); `verify_admin` (`:78`) always False → PATCH 403. ⚠ Its `start/submit/results/status` are **shadowed** by the diagnostic router (registered later? No — diagnostic first at `main.py:296`; test_management included after, its duplicates lose).

| Endpoint | Purpose | Input | Success | Errors | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|---|
| POST `/api/diagnostic-test/{test_id}/start` | (shadowed) | dict body | `SuccessResponse` | — | unused — shadowed by diagnostic router · — · — | `test_management_router.py:307` |
| POST `/api/diagnostic-test/{test_id}/submit` | (shadowed) | `TestSubmission` | `TestResults` | — | unused — shadowed · — · — | `:416` |
| GET `/api/diagnostic-test/{test_id}/results` | (shadowed) | — | `TestResults` | — | unused — shadowed · — · — | `:537` |
| GET `/api/diagnostic-test/{test_id}/status` | (shadowed) | — | dict | — | unused — shadowed · — · — | `:663` |
| PATCH `/api/diagnostic-test/{test_id}/status` | Admin status update | dict body + admin | `SuccessResponse` | F (admin check never passes) | unused — uncallable as implemented · — · — | `:745` |
| GET `/api/diagnostic-test/management/health` | Health | — | 200 | — | internal · — · — | `:847` |

**schedule_router.py** — prefix `/api/schedule`. AuthN: `JWT` (`middleware/auth_middleware.py:136`).

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/schedule/generate` | Generate personalized schedule | JWT, no ownership check (gap #7) | body `ScheduleRequest` | analytics_id, exam_date future, daily_study_hours 2–8 | 201 `Schedule` (synchronous) | A,V,N,P | flutter · Schedule generation · P11 | `schedule_router.py:143`, `schedule_models.py:72` |
| GET `/api/schedule/{schedule_id}` | Get schedule | JWT | path id | — | 200 `Schedule` | A,N | flutter · Schedule view · P11 | `:268` |
| GET `/api/schedule/student/{student_id}` | Current schedule | JWT | `?status_filter=active` | — | 200 `Schedule` (nullable) | A,N | flutter · Child/parent schedule view · P11 | `:330` |
| GET `/api/schedule/student/{student_id}/history` | History | JWT | `?limit=10` | — | 200 `List[Schedule]` | A | flutter · Schedule history · P11 | `:391` |
| POST `/api/schedule/{schedule_id}/regenerate` | Adaptive regenerate | JWT | body `{current_day>0}` | current_day > 0 | 200 `Schedule` | A,V,N,P | flutter · Schedule adjust · P11 | `:446` |
| PUT `/api/schedule/{schedule_id}` | Update | JWT | body `{updates: Dict}` | — | 200 `Schedule` | A,N,V | flutter · Schedule adjust · P11 | `:533` |
| DELETE `/api/schedule/{schedule_id}` | Delete | JWT | path id | — | 200 `SuccessResponse` | A,N | internal · — · — | `:610` |
| POST `/api/schedule/progress/update` | Day progress | JWT | body `ProgressUpdate` | day_number, status enum | 200 `ProgressUpdate` | A,V,N | flutter · Schedule progress · P11 | `:679` |
| GET `/api/schedule/progress/{schedule_id}` | Progress summary | JWT | path id | — | 200 dict | A,N | flutter · Schedule progress · P11 | `:767` |
| GET `/api/schedule/progress/today` | Today's tasks | JWT | `?schedule_id` required | — | 200 `List[Dict]` | A,V,N | flutter · Today view · P11 | `:836` |

**payment_router.py** — prefix `/api/payment`. AuthN: `bypass`. Existing web billing; **not part of the required workflow** (Flutter phases do not consume it).

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| GET `/api/payment/plans` | List plans | — | 200 `List[SubscriptionPlan]` | web · ParentPortal billing · — | `payment_router.py:80` |
| POST `/api/payment/create-order` | Create Razorpay order | body `CreateOrderRequest` | 201 `OrderResponse` | web · billing · — | `:164` |
| POST `/api/payment/verify` | Verify signature | body `VerifyPaymentRequest` | 200 `SubscriptionDetails` | web · billing · — | `:303` |
| GET `/api/payment/subscription/{parent_id}` | Subscription status | path id | 200 `SubscriptionStatusResponse` | web · billing · — | `:450` |
| GET `/api/payment/transactions/{parent_id}` | Transactions | path id | 200 `List[TransactionRecord]` | web · billing · — | `:558` |
| POST `/api/payment/cancel/{parent_id}` | Cancel | path id | 200 `SubscriptionDetails` | web · billing · — | `:672` |

### 9.5 Dashboards, gamification, analytics, AI features

**parent_dashboard_router.py** — prefix `/api/parent`, tag "Parent Dashboard". AuthN: `bypass`.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| GET `/api/parent/dashboard/{child_id}` | Child dashboard | — (ownership not enforced, gap #7) | path child_id | — | 200 `ChildDashboard` | N | flutter · Parent dashboard · P05 | `parent_dashboard_router.py:42`, `parent_models.py:16` |
| GET `/api/parent/reports/weekly/{child_id}` | Weekly report | — | `?week_start` | — | 200 `WeeklyReport` | N | flutter · Parent reports · P05 | `:67` |
| POST `/api/parent/reports/email-schedule` | Schedule email reports (mock) | — | body `EmailScheduleRequest` | frequency enum | 201 | V | web · settings · — | `:93` |
| GET `/api/parent/notifications/settings` | Get settings | — | `?parent_id` required | — | 200 `NotificationSettings` | V,N | flutter · Parent settings · P05 | `:112` |
| PUT `/api/parent/notifications/settings` | Update settings | — | body `NotificationSettings` | — | 200 `NotificationSettings` | V | flutter · Parent settings · P05 | `:135` |
| POST `/api/parent/goals/{child_id}` | Create goal | — | body `GoalRequest` | goal_type enum; target_value > 0 | 201 `Goal` | V,N | flutter · Parent goals · P05 | `:161` |
| GET `/api/parent/goals/{child_id}` | List goals | — | path child_id | — | 200 `List[Goal]` | N | flutter · Parent goals · P05 | `:188` |
| PUT `/api/parent/goals/{child_id}/{goal_id}` | Update goal | — | body `GoalUpdateRequest` | status enum | 200 `Goal` | V,N | flutter · Parent goals · P05 | `:211` |

**student_dashboard_router.py** — prefix `/api/student`. AuthN: `bypass`. The child dashboard in this documentation set is built from diagnostic-test/analytics/schedule endpoints instead; these are classified `unused` for the Flutter app.

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| GET `/api/student/today/{student_id}` | Today's plan | path id | 200 `TodaysPlan` | unused (child Today view uses `/api/schedule/progress/today`) · — · — | `student_dashboard_router.py:46` |
| GET `/api/student/topic/{topic_id}/resources` | Resources | path id | 200 `TopicResources` | unused · — · — | `:71` |
| POST `/api/student/practice/quick` | Quick practice | body `QuickPracticeRequest` | 201 `QuickPracticeResponse` | unused · — · — | `:96` |
| POST `/api/student/doubts` | Create doubt | body `DoubtRequest` | 201 `Doubt` | unused · — · — | `:120` |
| GET `/api/student/doubts/{doubt_id}/explanation` | Doubt answer | path id | 200 `DoubtExplanation` | unused · — · — | `:144` |
| GET `/api/student/revision/due` | Due revisions | `?student_id` | 200 `List[RevisionItem]` | unused · — · — | `:169` |
| POST `/api/student/revision/mark-complete/{topic_id}` | Mark revision | `?student_id` | 200 | unused · — · — | `:192` |
| POST `/api/student/bookmarks` | Add bookmark | body `BookmarkRequest` | 201 `Bookmark` | unused · — · — | `:210` |
| GET `/api/student/bookmarks` | List bookmarks | `?student_id` | 200 `List[Bookmark]` | unused · — · — | `:234` |
| DELETE `/api/student/bookmarks/{bookmark_id}` | Delete bookmark | path id | 200 | unused · — · — | `:257` |
| GET `/api/student/insights/{student_id}` | Insights | path id | 200 `PerformanceInsights` | unused · — · — | `:274` |
| GET `/api/student/compare/percentile` | Peer comparison | `?student_id` | 200 `PeerComparison` | unused · — · — | `:308` |

**gamification_router.py** — prefix `/api/gamification`. AuthN: `bypass`. Consumer: `web` (leaderboard page); not required by the workflow.

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| GET `/api/gamification/achievements` | Achievements | `?student_id` | 200 `StudentAchievements` | web · leaderboard · — | `gamification_router.py:37` |
| POST `/api/gamification/achievements/claim/{achievement_id}` | Claim | `?student_id` | 200 | web · leaderboard · — | `:85` |
| GET `/api/gamification/challenge/daily` | Daily challenge | — | 200 `DailyChallenge` | web · leaderboard · — | `:103` |
| POST `/api/gamification/challenge/daily/submit` | Submit challenge | body `DailyChallengeSubmission` | 200 `DailyChallengeResult` | web · leaderboard · — | `:137` |
| GET `/api/gamification/challenge/leaderboard` | Leaderboard | `?challenge_date` | 200 `Leaderboard` | web · leaderboard · — | `:164` |
| GET `/api/gamification/streak` | Streak | `?student_id` | 200 `StreakInfo` | web · leaderboard · — | `:191` |
| GET `/api/gamification/points/history` | Points history | `?student_id` | 200 `PointsHistory` | web · leaderboard · — | `:213` |

**analytics_router.py** — prefix `/api/analytics`, tag "Analytics". AuthN: `none` declared (gap #7-adjacent).

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/analytics/generate` | Start AI analysis | — | body `AnalyticsRequest` | test_id, student_id; answers list-or-dict | 202 `AnalyticsResponse` (status pending) | V,N,P | flutter · AI analysis trigger · P10 | `analytics_router.py:77`, `analytics_models.py:89` |
| GET `/api/analytics/{analytics_id}` | Poll report | — | path id | — | 200 `AnalyticsReport` | N | flutter · AI status/results · P10 | `:193` |
| GET `/api/analytics/student/{student_id}` | Child's analyses | — | `?limit=10,offset=0` | — | 200 `List[AnalyticsReport]` | N | flutter · Child/parent results lists · P10 | `:262` |
| GET `/api/analytics/test/{test_id}` | Test analyses | — | `?limit=50` | — | 200 `List[AnalyticsReport]` | N | flutter · Results · P10 | `:333` |
| GET `/api/analytics/{analytics_id}/insights` | AI insights | — | path id | — | 200 `AnalyticsInsights` | N | flutter · Results detail · P10 | `:410` |
| GET `/api/analytics/{analytics_id}/weak-topics` | Weak topics | — | path id | — | 200 `List[PriorityTopic]` | N | flutter · Results detail · P10 | `:485` |

**syllabus_coverage_router.py** — prefix `/api/syllabus/coverage`. AuthN: `bypass`. Consumer: `unused` for this scope (analytics covers weakness data).

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| GET `/api/syllabus/coverage/{student_id}` | Coverage | `?exam_type` | 200 dict | unused · — · — | `syllabus_coverage_router.py:41` |
| GET `/api/syllabus/coverage/{student_id}/untested` | Untested topics | `?exam_type,subject,limit=20` | 200 dict | unused · — · — | `:113` |
| GET `/api/syllabus/coverage/{student_id}/weak` | Weak topics | `?exam_type,subject,threshold=60.0,limit=20` | 200 dict | unused · — · — | `:150` |
| GET `/api/syllabus/coverage/{student_id}/recommendations` | Recommendations | `?exam_type,num_topics=10` | 200 dict | unused · — · — | `:196` |
| GET `/api/syllabus/coverage/{student_id}/progress` | Progress | `?exam_type` | 200 dict | unused · — · — | `:238` |
| GET `/api/syllabus/coverage/{student_id}/topic/{topic_id}` | Topic detail | `?exam_type` | 200 dict | unused · — · — | `:284` |
| GET `/api/syllabus/coverage/health` | Health | — | 200 | internal · — · — | `:343` |

**ai_features_router.py** — prefix `/api/ai`. AuthN: `bypass`. ⚠ **100% hardcoded mock data** — no service/Gemini calls. Consumer: `unused` (do not ship to clients).

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| POST `/api/ai/tutor/ask` | Ask tutor (mock) | body `AITutorRequest` (student_id, question) | 200 `AITutorResponse` | unused — mock · — · — | `ai_features_router.py:35` |
| GET `/api/ai/tutor/history/{student_id}` | Chat history (mock) | `?limit=50` | 200 `ChatHistory` | unused — mock · — · — | `:72` |
| GET `/api/ai/recommend/topics/{student_id}` | Topic recs (mock) | `?limit=5` | 200 `List[TopicRecommendation]` | unused — mock · — · — | `:92` |
| GET `/api/ai/recommend/resources/{topic_id}` | Resource recs (mock) | `?limit=5` | 200 `List[ResourceRecommendation]` | unused — mock · — · — | `:131` |
| GET `/api/ai/readiness/{student_id}` | Readiness (mock) | — | 200 `ExamReadiness` | unused — mock · — · — | `:170` |
| GET `/api/ai/analysis/mistakes/{student_id}` | Mistakes (mock) | — | 200 `MistakeAnalysis` | unused — mock · — · — | `:220` |

**hermes_router.py** — prefix `/api/hermes`. AuthN: `JWT`. Consumer: `web` (existing StudentMentor/ParentPortal pages).

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| POST `/api/hermes/chat` | Tutor chat | body `HermesChatRequest` (message) | 200 `HermesChatResponse` | web · StudentMentor · — | `hermes_router.py:144` |
| GET `/api/hermes/sessions` | Sessions | `?child_id` | 200 `List[HermesSessionInfo]` | web · StudentMentor · — | `:171` |
| GET `/api/hermes/sessions/{session_id}/messages` | Messages | `?child_id` | 200 `List[HermesMessage]` | web · StudentMentor · — | `:185` |
| POST `/api/hermes/sessions/{session_id}/end` | End session | `?child_id` | 200 | web · StudentMentor · — | `:200` |
| POST `/api/hermes/quiz/attempt` | Record quiz | body `QuizAttemptRequest` | 200 `QuizAttemptResult` | web · StudentMentor · — | `:217` |
| GET `/api/hermes/topics` | Micro-topics | `?child_id` | 200 `List[MicroTopicItem]` | web · StudentMentor · — | `:238` |
| GET `/api/hermes/progress` | Progress | `?child_id` | 200 `HermesProgress` | web · StudentMentor · — | `:252` |
| POST `/api/hermes/admin/seed-topics` | Seed topics | `?force=false` | 200 `SeedResult` | internal · — · — | `:266` |
| POST `/api/hermes/summary/generate/{child_id}` | Gen summary | opt body, `?date` | 200 `SummaryResponse` | web · ParentPortal · — | `:281` |
| GET `/api/hermes/summary/{child_id}` | Get summary | `?date,audience=student\|parent` | 200 `SummaryResponse` | web · ParentPortal · — | `:300` |
| GET `/api/hermes/today` | Today | `?child_id` | 200 `TodayResponse` | web · StudentDashboard · — | `:334` |
| GET `/api/hermes/gamification` | Gamification | `?child_id` | 200 `GamificationState` | web · StudentDashboard · — | `:349` |
| GET `/api/hermes/score-prediction` | Score prediction | `?child_id` | 200 `ScorePrediction` | web · StudentDashboard · — | `:364` |
| GET `/api/hermes/parent/overview` | Parent overview | `?child_id` required | 200 `ParentOverview` | web · ParentPortal · — | `:391` |
| GET `/api/hermes/parent/weekly` | Parent weekly | `?child_id,date` | 200 `ParentWeeklyReport` | web · ParentPortal · — | `:406` |

### 9.6 MARKS ecosystem, SATHEE AI Hub, SuperAdmin

**marks_router.py** — prefix `/api`. AuthN: `resolve_acting_user` (`:79`: `?student_id=` → JWT → fallback `student_default_01`). Storage: `data/pyq_and_colleges.json` + Firestore. Consumer: `web` (PYQ/custom-test/notebook pages).

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| GET `/api/cpyqb/exam/{exam_id}/subject/{subject_id}/chapter/{chapter_id}/topic/{topic_id}/questions` | Topic PYQs | `?offset=0,limit=20,pyqFilter,years,qType,difficulty,revisionZone` | 200 `PYQQuestionListResponse` | web · StudentPyq · — | `marks_router.py:105` |
| GET `/api/cpyqb/questions` | Filtered PYQs | `?examId,subjectId,chapterId,topicId,…` + limit/offset | 200 `PYQQuestionListResponse` | web · StudentPyq · — | `:146` |
| POST `/api/solving-modes/practice/start` | Practice attempt | body `PracticeAttemptRequest` | 200 `PracticeAttemptResponse` | web · StudentPyq · — | `:182` |
| GET `/api/custom-test/build/step1` | CTG step 1 | — | 200 `CTGStep1Response` | web · StudentTests · — | `:198` |
| POST `/api/custom-test/build/step2` | CTG step 2 | body `CTGStep2Request` | 200 `CTGStep2Response` | web · StudentTests · — | `:209` |
| POST `/api/custom-test/generate` | Generate custom test | body `CTGGenerateRequest` | 201 `CTGGeneratedTestResponse` | web · StudentTests · — | `:221` |
| POST `/api/custom-test/submit` | Submit custom test | body `CTGSubmitRequest` (testId, responses) | 200 `CTGSubmitResponse` | web · CBT exam page · — | `:235` |
| GET `/api/custom-test/analysis/{test_id}` | Custom analysis | path id | 200 | web · StudentTests · — | `:248` |
| GET `/api/rfc/subject/{subject_id}/chapter/{chapter_id}/cards` | Flashcards | — | 200 `FlashCardDeckResponse` | web · StudentRevision · — | `:261` |
| GET `/api/rfc/subject/{subject_id}/chapter/{chapter_id}/card/{card_id}` | Single card | — | 200 | web · StudentRevision · — | `:277` |
| POST `/api/rfc/mastery` | Mastery update | body `{cardId}` | 200 | web · StudentRevision · — | `:296` |
| POST `/api/notebook` | Create notebook | body `CreateNotebookRequest` | 201 `NotebookItem` | web · notebooks · — | `:310` |
| GET `/api/notebook/smart` | List notebooks | `?includeArchived=false` | 200 `List[NotebookItem]` | web · notebooks · — | `:324` |
| PATCH `/api/notebook/{notebook_id}` | Update notebook | body `UpdateNotebookRequest` | 200 `NotebookItem` | web · notebooks · — | `:337` |
| POST `/api/notebook/question` | Bookmark question | body `{questionId}` | 200 | web · notebooks · — | `:353` |
| GET `/api/notebook/{notebook_id}/questions` | Notebook questions | — | 200 | web · notebooks · — | `:365` |
| GET `/api/notebook/errors` | Error notebook | `?subject,status,mistakeType` | 200 `ErrorNotebookListResponse` | web · notebooks · — | `:379` |
| POST `/api/notebook/errors/{error_id}/resolve` | Resolve error | — | 200 | web · notebooks · — | `:408` |
| POST `/api/assignment/teacher/create` | Create assignment | body `CreateAssignmentRequest` | 201 `CreateAssignmentResponse` | web · ParentPortal assignments · — | `:422` |
| GET `/api/assignment/student/id/{identifier}` | Get assignment | path code | 200 | web · assignments · — | `:436` |
| POST `/api/assignment/student/id/{identifier}/submit` | Submit assignment | body `{responses}` | 200 | web · assignments · — | `:447` |
| GET `/api/assignment/student/id/{identifier}/analysis` | Assignment analytics | path code | 200 | web · assignments · — | `:462` |
| POST `/api/targets/update` | Update daily target | body `UpdateDailyGoalRequest` | 200 | web · StudentDashboard · — | `:476` |
| GET `/api/targets/heatmap` | Heatmap | `?month=YYYY-MM` | 200 `MonthlyHeatmapResponse` | web · StudentDashboard · — | `:490` |
| GET `/api/targets/daily-dose` | Daily dose | `?examId=jee_main` | 200 | web · StudentDashboard · — | `:503` |
| POST `/api/targets/daily-dose/submit` | Submit daily dose | body `{responses}` | 200 | web · StudentDashboard · — | `:515` |
| GET `/api/leaderboard/achievements` | Leagues | — | 200 `LeaderboardLeaguesResponse` | web · StudentDashboard · — | `:527` |
| GET `/api/neet/ncert/subject/{subject_id}/modules` | NCERT modules | — | 200 `NcertModuleListResponse` | web · StudentPyq · — | `:541` |

**sathee_ai_router.py** — prefix `/api/ai-hub`. AuthN: `none`. Consumer: `web`.

| Endpoint | Purpose | Input | Success | Consumer / UI / Phase | Source |
|---|---|---|---|---|---|
| POST `/api/ai-hub/vision/ocr` | OCR image | multipart `image?` + form flags | 200 `OCRResponse` | web · StudentMentor OCR · — | `sathee_ai_router.py:49` |
| POST `/api/ai-hub/chat/stream` | SSE doubt stream | body `StreamingDoubtRequest` | SSE stream | web · StudentMentor · — | `:73` |
| POST `/api/ai-hub/qa/generate-similar-questions` | Similar questions | body `GenerateSimilarQuestionsRequest` | 200 | web · StudentPyq · — | `:93` |
| POST `/api/ai-hub/rank/predict` | Rank prediction | body `RankPredictRequest` | 200 `RankPredictResponse` | web · StudentRevision tools · — | `:106` |
| GET `/api/ai-hub/colleges/cutoffs` | College cutoffs | `?collegeId,exam,category=General` | 200 | web · tools · — | `:118` |
| POST `/api/ai-hub/omr/evaluate` | OMR evaluation | multipart `omrImage?` + form | 200 `OMREvaluateResponse` | web · tools · — | `:137` |

**superadmin_router.py** — prefix `/api/superadmin`, tag "SuperAdmin Portal". AuthN: `none` on all (gap #8). Audit-logged.

| Endpoint | Purpose | AuthZ | Input | Validation | Success | Errors | Consumer / UI feature / Phase | Source |
|---|---|---|---|---|---|---|---|---|
| POST `/api/superadmin/login` | Superadmin login (password not verified) | — | body `{email, password}` | email contains "admin" | 200 dict + superadmin JWT | A,V | superadmin · Superadmin login · P12 | `superadmin_router.py:413` |
| POST `/api/superadmin/demo-session` | Seed demo accounts + issue role JWT | — | body `{role: student\|parent\|superadmin}` | enum | 200 dict with JWTs | V | internal · (web demo switcher) · — | `:435` |
| GET `/api/superadmin/overview` | Platform KPIs | — | — | — | 200 KPI dict | — | superadmin · Dashboard · P12 | `:454` |
| GET `/api/superadmin/users` | List parents+students | — | — | — | 200 dict | — | superadmin · Users · P12 | `:535` |
| POST `/api/superadmin/users/action` | User admin action | — | body `{action, target_id, value?}` | action enum | 200 dict | V,N | superadmin · Users · P12 | `:609` |
| GET `/api/superadmin/questions` | List PYQs | — | `?examId,subjectId,search` | — | 200 dict | — | superadmin · Questions CMS · P12 | `:710` |
| POST `/api/superadmin/questions` | Create PYQ | — | body `PYQQuestionUpsertRequest` | statementHtml, solutionHtml required | 201 dict | V | superadmin · Questions CMS · P12 | `:737` |
| PUT `/api/superadmin/questions/{question_id}` | Update PYQ | — | same body | — | 200 dict | V,N | superadmin · Questions CMS · P12 | `:758` |
| DELETE `/api/superadmin/questions/{question_id}` | Delete PYQ | — | path id | — | 200 dict | N | superadmin · Questions CMS (destructive) · P12 | `:777` |
| GET `/api/superadmin/flashcards` | List flashcards | — | — | — | 200 dict | — | superadmin · Content CMS · P12 | `:794` |
| POST `/api/superadmin/flashcards` | Create flashcard | — | body `{title, frontText, backFormulaHtml}` | 3 fields required | 201 dict | V | superadmin · Content CMS · P12 | `:800` |
| DELETE `/api/superadmin/flashcards/{card_id}` | Delete flashcard | — | path id | — | 200 dict | N | superadmin · Content CMS (destructive) · P12 | `:820` |
| GET `/api/superadmin/colleges` | List colleges | — | — | — | 200 dict | — | superadmin · Colleges · P12 | `:831` |
| PUT `/api/superadmin/colleges/{college_id}` | Update cutoffs | — | body `{branchCode, year?, cutoffs?, seats?}` | branchCode required | 200 dict | V,N | superadmin · Colleges · P12 | `:838` |
| GET `/api/superadmin/assessments` | List assessments | — | — | — | 200 dict | — | superadmin · Assessments · P12 | `:867` |
| GET `/api/superadmin/system-config` | Governance config | — | — | — | 200 dict | — | superadmin · AI settings · P12 | `:882` |
| PUT `/api/superadmin/system-config` | Update config | — | body `{chat caps, mastery threshold, rate limit, maintenance_mode}` | — | 200 dict | V | superadmin · AI settings · P12 | `:892` |

**App-level routes** (`main.py`): `GET /health` (`main.py:212`) — internal/liveness; `GET /` (`main.py:398`) — internal.

---

## 10. Endpoint traceability check

Totals: **285 endpoints listed** = 283 router rows (86 under `/api/v1`, 197 under legacy `/api/*`)
+ 2 app-level. Of these, **279 are mounted**; the 6 `question_router` rows are defined but
unreachable (gap #10). Row counts below were mechanically counted from the §9 tables.

| Router group | Rows | Consumer split (flutter / superadmin / web / internal / unused) | Phase | Disposition |
|---|---|---|---|---|
| syllabus, planner, notes, mindmaps, scan, speech, communication, teacher, parent (v1) | 86 | 0 / 0 / 0 / 86 / 0 | — | Playground (in-memory, TESTING_MODE). Not consumed by Flutter/superadmin; accounted for. |
| auth, simple_register, login, verification | 18 | 18 / 0 / 0 / 0 / 0 | P04–P07 | **Consumed.** |
| preferences (onboarding) | 3 | 0 / 0 / 3 / 0 / 0 | — | Existing web onboarding; Flutter may skip. Accounted. |
| child (onboarding) | 4 | 4 / 0 / 0 / 0 / 0 | P06 | **Consumed.** |
| exam (onboarding) | 5 | 5 / 0 / 0 / 0 / 0 | P08 | **Consumed.** |
| embedding, vector_search, rag | 14 | 0 / 0 / 0 / 14 / 0 | — | RAG pipeline. Accounted. |
| question_router | 6 | 0 / 0 / 0 / 0 / 6 | — | Unmounted in `main.py` (gap #10). Accounted. |
| diagnostic_test | 13 | 10 / 0 / 0 / 2 / 1 | P07–P10 | **Consumed** (mock today — gaps #4, #15). |
| test_management | 6 | 0 / 0 / 0 / 0 / 6 | — | 4 routes shadowed; PATCH uncallable. Accounted. |
| schedule | 10 | 9 / 0 / 0 / 1 / 0 | P11 | **Consumed** (collection mismatch — gap #6; today-tasks defect — gap #14). |
| payment | 6 | 0 / 0 / 6 / 0 / 0 | — | Existing web billing. Accounted. |
| parent_dashboard | 8 | 7 / 0 / 1 / 0 / 0 | P05 | **Consumed** (email-schedule is web). |
| student_dashboard | 12 | 0 / 0 / 0 / 0 / 12 | — | Overlapped by schedule/diagnostic endpoints in our scope. Accounted. |
| gamification | 7 | 0 / 0 / 7 / 0 / 0 | — | Existing web leaderboard. Accounted. |
| analytics | 6 | 6 / 0 / 0 / 0 / 0 | P10 | **Consumed.** |
| syllabus_coverage | 7 | 0 / 0 / 0 / 1 / 6 | — | Redundant with analytics in our scope (health = internal). Accounted. |
| ai_features | 6 | 0 / 0 / 0 / 0 / 6 | — | Hardcoded mocks; must not ship to clients. Accounted. |
| hermes | 15 | 0 / 0 / 14 / 1 / 0 | — | Existing web mentor pages (seed-topics = internal). Accounted. |
| marks | 28 | 0 / 0 / 28 / 0 / 0 | — | Existing web PYQ/tests pages. Accounted. |
| sathee_ai | 6 | 0 / 0 / 6 / 0 / 0 | — | Existing web AI-hub pages. Accounted. |
| superadmin | 17 | 0 / 16 / 0 / 1 / 0 | P12 | **Consumed** (demo-session = internal). |
| app-level | 2 | 0 / 0 / 0 / 2 / 0 | — | Health/root. Accounted. |
| **Total** | **285** | **59 / 16 / 65 / 108 / 37** | | |

No endpoint is omitted without an explanation. The Flutter app consumes **59** endpoints,
the superadmin panel consumes **16** (`demo-session` excluded).

## 11. Consolidated BACKEND CHANGE REQUIRED list

The following are missing or broken **in the backend at the inspected commit**. Clients must not
work around them silently; each phase cites these where relevant. Suggested endpoint shapes are
proposals only — the backend team owns final contracts.

1. **Child password stored and compared in plaintext.** `child_service.py:172` writes
   `"password": <plaintext>` into Firestore; `login_service.py:790-793` compares plaintext.
   → Hash at creation (e.g. bcrypt via passlib), compare hashes at login; keep the Firebase Auth
   user password in sync. Until then, Flutter must treat child credentials as dev-only and must
   never log them.
2. **No parent-facing child credential reset.** `ChildProfileUpdate.username/password` exist but
   `update_child_profile` drops them (`child_service.py:416-442`); Firebase user untouched.
   → Add e.g. `POST /api/onboarding/child/{child_id}/reset-credentials {new_password}` updating
   Firestore (hashed) + Firebase Auth.
3. **No forgot-password / password-reset for parents.** `verification_service.py` has only
   email/phone verification OTPs.
   → Add `POST /api/auth/password/reset-request {email}` + `POST /api/auth/password/reset-confirm`
   (Firebase REST `sendOobCode`/`resetPassword` can back this).
4. **Diagnostic test lifecycle is mock.** `GET /api/diagnostic-test/{test_id}` returns 501
   (`diagnostic_test_router.py:508`); submissions/results do not persist (Firestore writes
   commented out, `test_management_router.py:272-300`); scoring is random
   (`test_management_router.py:170-269`); status transition to `completed` commented out
   (`:293-298`); duplicate submission therefore unpreventable; `"scheduled"` is not a `TestStatus`
   member (`diagnostic_test_models.py:28-64`).
   → Persist diagnostic tests + questions (generators exist: `services/test_assembler.py`,
   `services/question_generator.py`); implement `GET /{test_id}`; wire the real scorer
   (`services/score_calculator.py:153` with `score_models.py` marking schemes); persist
   submissions (`test_submissions`); transition status; make submit idempotent
   (e.g. `Idempotency-Key` or submission-record dedupe).
5. **Analytics is synchronous under a 202/polling contract.** `analytics_service.py:261-391`
   runs inline. Contract-safe but slow; clients must poll.
   → (Recommended) Move to FastAPI `BackgroundTasks` and keep the same response shape.
6. **Collection-name mismatches break schedule + parent dashboard.** `schedule_service.py:84-85`
   reads `analytics` + `students`; writers store `analytics_reports` + `children`.
   `parent_dashboard_service.py` also reads `analytics`.
   → Read `analytics_reports`/`children` (or write aliases).
7. **No ownership/authorization enforcement on workflow endpoints.** Testing bypass returns a
   constant user (`testing_auth.py:20-42`); analytics has no auth; child/parent/scoping is
   unenforced; several routers crash (500) subscripting the bypass string as a dict.
   → Real JWT auth dependencies + parent-owns-child checks on onboarding, diagnostic,
   analytics, schedule, parent-dashboard endpoints; graceful principal handling.
8. **Superadmin cannot monitor the workflow domain.** No superadmin endpoint touches
   `diagnostic_tests`, submissions, `analytics_reports`, or `schedules`; superadmin login verifies
   no password (`superadmin_router.py:413-421`); no auth on the other 16 endpoints.
   → Add read-only `GET /api/superadmin/tests`, `/submissions`, `/analytics`, `/schedules` +
   stats; verify superadmin password; protect endpoints with the superadmin JWT.
9. **Parent email-login password check is silently skipped without `FIREBASE_API_KEY`.**
   `login_service.py:215-252`.
   → Fail closed when the key is absent.
10. **`question_router` defined but never mounted** (`main.py` imports 34 routers; question is absent).
    → Mount it or delete it.
11. **Two routers share `/api/diagnostic-test` with overlapping routes** — diagnostic wins by
    registration order; the real (test_management) implementations are unreachable.
    → Merge or split prefixes.
12. **Dead config:** `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`/`JWT_REFRESH_TOKEN_EXPIRE_DAYS`/
    `CORS_ORIGINS` in `.env.example` are ignored (hardcoded in `token_service.py:34-35`,
    `main.py:137-153`). Minor frontend bug for context: web calls
    `POST /api/targets/daily-dose/complete` which does not exist (backend has `/submit`) —
    out of scope for Flutter/superadmin.
13. **Stock boot fails under the shipped `.env` (verified live).** `install.sh` copies
    `.env.example` verbatim, whose line 244 sets `TESTING_MODE=true` (while line 88 documents
    `false`). With `TESTING_MODE=true`, `vector_search_router.py:42-44` executes
    `from middleware.testing_auth import get_current_user`, but `testing_auth.py` only defines
    `get_current_user_testing` → `ImportError` at startup; `./run.sh backend` cannot serve.
    Verified: import fails with `TESTING_MODE=true`, succeeds with `TESTING_MODE=false`.
    → Fix the import (alias or add the symbol) and reconcile the duplicated env blocks in
    `.env.example`. **Dev workaround until fixed: set `TESTING_MODE=false` in `.env`.**
14. **`GET /api/schedule/progress/today` always 500s when today has topics (verified in code).**
    `progress_tracker.py:631-642` builds task dicts with `topic.subject.value` (DailyTopic.subject
    is a plain `str`), `topic.daily_goals` (the field is `goals`), and `topic.difficulty.value`
    (`DailyTopic` has no `difficulty` field) → `AttributeError` → 500.
    → Align the mapping with `schedule_models.py` `DailyTopic`.
15. **All `/api/diagnostic-test` endpoints 500 before their own logic (verified live).** The
    testing bypass returns the string `"test_parent_123"`; handlers subscript it as a dict
    (e.g. `current_user["parent_id"]`, `diagnostic_test_router.py:652`) → `TypeError` 500 on
    every diagnostic-test endpoint, including the child's test list and the `get_test` 501 —
    the 501 is unreachable. Extends gaps #4/#7: no diagnostic-test call succeeds today.
    → Fix principal handling (return a dict-shaped principal or drop the subscripts) and land
    the real lifecycle from gap #4.
16. **Two `Schedule` read-path defects.** (a) `PUT /api/schedule/{id}` docs/examples reference
    `status: "paused"` (`schedule_router.py:101,353,541`), but `ScheduleStatus` is
    `active|completed|abandoned` — such updates can never succeed. (b) `Schedule.validate_exam_date`
    is a field validator (`schedule_models.py:529-539`) that re-runs on **every** `Schedule` parse,
    so a schedule whose exam_date has passed 500s on GET/PUT — old schedules become unreadable.
    → Fix docs/enum; validate `exam_date` only on write.

## 12. Seed & demo identities (for manual testing)

| Identity | Id / credential | Source |
|---|---|---|
| Superadmin | email `admin@eklavya.ai` (any "admin" email accepted; password field ignored) → JWT `parent_id="superadmin_root"` | `superadmin_router.py:366-378,413-421` |
| Demo parent | `parent_demo_eklavya` (`rajesh.sharma@eklavya.ai`), created by `POST /api/superadmin/demo-session` | `superadmin_router.py:180` |
| Demo child | `child_demo_aarav`, username `aarav_jee2026` | `superadmin_router.py:180` |
| v1 seed student | `student_aarav` (Aarav Sharma) — header `X-User-Id: student_aarav` | `seed.py:63` |
| v1 seed teacher | `teacher_rao` · v1 seed parent `parent_rajesh` · v1 admin `admin_local` | `seed.py:63` |

`POST /api/superadmin/demo-session {"role":"parent"|"student"|"superadmin"}` returns ready-to-use
JWTs — the fastest way to obtain a valid token for any role during development.
