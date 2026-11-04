# Phase 05 — Parent Registration/Login/Dashboard (text.md)

Reference material for this phase, verified against commit
`d8ab4917480c90a7c5c663f7fe6e8a726ce490f4` (branch `main`, 2026-11-02). Citations are
`path/file.py:line` from the repository root; phase-01 citations refer to
`flutter-docs/phase-01-repository-analysis-endpoint-inventory/text.md`.

---

## 1. Fixed decisions reused from earlier phases

Native ID `ai.eklavya.app`; Dart/Flutter + Riverpod + Dio + `json_serializable` + go_router +
`flutter_secure_storage`; base URL from `--dart-define=EKLAVYA_BASE_URL` with Android emulator
default `http://10.0.2.2:8000`. Phase 04 owns all auth HTTP: `AuthRemoteDataSource`,
`ApiResult`/`ApiError`, `AuthInterceptor`, refresh coordinator, `SessionManager`, and session events.
Phase 03 owns design tokens; screens cite `GlassCard`, `GlassTextField`, `GlassButton`, `StatusPill`,
and `ErrorState`. Every feature value comes from a real endpoint response or current user input.

## 2. Single-child contract (fixed backend reality)

`ChildService.create_child_profile` enforces one child per parent — a second profile is rejected
with HTTP 400 "Parent can only have one child profile..." (`child_service.py:122-128`). Therefore:

- The app resolves **the** child with `GET /api/onboarding/child?parent_id=<parent_id>`
  (`child_router.py:164`, response `ChildProfileResponse`, 404 when none). There is no child list.
- UI seams stay list-shaped (e.g. `children: List<ChildSummary>` in dashboard state holding 0..1
  items, `childId: String?`) so a future multi-child backend does not break navigation or state
  shapes — but every behavior is correct for exactly one child, including the "no child yet"
  case (CTA routes to phase-06 child creation).
- `student_id` and `child_id` are the same value everywhere (phase-01 §8.H; child login response
  duplicates them, `login_service.py:822-823`).

## 3. Endpoint contracts (canonical JSON)

Base URL from phase-04. Errors are the legacy envelope `{"detail": "<string>"}` (phase-01 §4);
`requestId` comes from the `X-Request-Id` response header.

### 3.1 POST /api/auth/register/simple — primary registration
Router `simple_register_router.py:31-109`; service `simple_register_service.register_user_simple`
(`simple_register_service.py:18-93`). Request model `SimpleRegisterRequest`
(`simple_register_router.py:22-28`): `name` 2–100, `email_address` EmailStr, `password` min 8,
`repeat_password` min 8, `mobile_number` default `"+91XXXXXXXXXX"`.

Request:
```json
{"name": "Rajesh Sharma", "email_address": "rajesh@example.com", "password": "Passw0rd1",
 "repeat_password": "Passw0rd1", "mobile_number": "+919876543210"}
```
Success 201 `AuthResponse` (`auth_models.py:230-278`). Actual service output
(`simple_register_service.py:79-85`):
```json
{"parent_id": "<firebase-uid>", "email": "rajesh@example.com", "phone": "+919876543210",
 "verification_required": false, "message": "Registration successful"}
```
Note 1: `phone` **echoes `mobile_number`** in this response (it is not `null` when a mobile number
was supplied); phase-01 §8's example showed `phone:null` — this document records the service
behavior, which is the authority. Note 2: the Firestore `parents` doc written by this path carries
keys `parent_id, name, mobile_number, email_address, language, role, created_at, email_verified,
registration_method:"simple"` (`simple_register_service.py:62-75`) — no plain `email`/`phone`
keys. Note 3: `verification_required` is `false`; **no token is returned** — the app must route to
ParentLogin after success (phase-01 §7.A).
Errors: 400 `{"detail":"An account with email rajesh@example.com already exists. Please login instead."}`
(duplicate, `simple_register_service.py:87-89`); 400 for other ValueErrors (e.g. password mismatch
raised by the service layer; Pydantic 422 for schema violations); 500.

### 3.2 Optional registration alternates (behind the same ParentRegister screen)

| Endpoint | Request → Success 201 | Notes |
|---|---|---|
| `POST /api/auth/register/parent/email` (`auth_router.py:41-130`, `auth_models.py:23-94`) | `{email, password, language:"en"\|"hi"\|"mr"}` → `{parent_id, email, phone:null, verification_required:true, message:"Registration successful. Please verify your email to continue."}` | password ≥8 with ≥1 letter + ≥1 digit (:60-84); doc keys `parent_id,email,language,role,created_at,email_verified,registration_method:"email"` (`auth_service.py:90-98`); **no `name` collected or stored**; 400 duplicate |
| `POST /api/auth/register/parent/phone` (`auth_router.py:133-220`, `auth_models.py:97-162`) | `{phone, language}` → `{parent_id, email:null, phone, verification_required:true, message:"...You will receive an OTP for verification during login."}` | phone regex `^\+91[6-9]\d{9}$` (:145); **no password — OTP is the credential**; doc has `phone_verified:false` (`auth_service.py:200-208`) |
| `POST /api/auth/register/parent/google` (`auth_router.py:223-313`) | `{id_token, language}` → `{parent_id, email, phone:null, verification_required:false, message:...}` | id_token ≥50 chars; backend verifies via Firebase (`auth_service.py:269-281`); existing users get message "Login successful. Welcome back!" (`auth_service.py:312`) but still **no token** — login still required |

### 3.3 Verification endpoints (6-char email code, 6-digit phone OTP; single-use, 10-minute)

`verification_service.py:33-34` sets `VERIFICATION_CODE_EXPIRY_MINUTES = 10`. Codes are stored in
`verification_codes` with `used:false` and marked `used:true` on confirm (:139-149, :257-261,
:317-328, :429-433). **In this build the code/OTP is returned in the response body for dev**
(`verification_service.py:152,157-160` and `:331,336-339` — comments say "Remove this field in
production").

- `POST /verify/email/send` (`verification_router.py:43-128`): `{email}` → 200
  `{"message":"Verification email sent","code":"A3B7C9"}`. 6-char uppercase alphanumeric
  (`verification_service.py:37-55`). 400 invalid email; 500.
- `POST /verify/email/confirm` (`verification_router.py:131-227`): `{email, code}` (code 6
  alphanumeric, uppercased client-side-friendly, `verification_models.py:85-111`) → 200
  `VerificationResponse` (`verification_models.py:279-315`):
  `{"verified": true, "message": "Email verified successfully"}`. Also sets Firebase
  `email_verified=True` (`verification_service.py:234-239`) and Firestore `email_verified:true,
  verified_at` (:251-254). Errors: 400 invalid/already-used/expired code; 404
  `No user found with email: ...`; 500.
- `POST /verify/phone/send` (`verification_router.py:230-315`): `{phone}` (regex §5) → 200
  `{"message":"OTP sent","otp":"123456"}`. 6-digit numeric (`verification_service.py:58-75`).
- `POST /verify/phone/confirm` (`verification_router.py:318-414`): `{phone, otp}` → 200
  `{"verified": true, "message": "Phone verified successfully"}`; sets Firestore
  `phone_verified:true` (`verification_service.py:423-426`). Errors: 400 invalid/used/expired OTP;
  404 user not found; 500.

### 3.4 Parent login (primary path; details in phase-04 text.md §3)

`POST /api/auth/login/email` `{email,password}` → 200 `LoginResponse` (`login_router.py:97`,
`login_models.py:274-373`), 401 `Invalid email or password`. Optional alternates behind the same
ParentLogin screen: `POST /api/auth/login/phone` (`login_router.py:203`; **otp is required by the
Pydantic model** `login_models.py:89-94` despite the router comment at `:272-273` — always send a
6-digit OTP) and `POST /api/auth/login/google` (`login_router.py:311`). Success →
`sessionManager.saveParentSession(...)` (phase-04) → navigate per §8.

### 3.5 POST /api/auth/logout and GET /api/auth/me
Phase-04 `text.md` §3.5/§3.6. Logout success `{"message":"Logout successful"}` then
`sessionManager.clear(PARENT)` + `SessionEvent.LoggedOut(PARENT)`. `/me` returns the raw parents
doc with method-dependent keys (phase-04 §3.6 table) — the profile UI reads `name`,
`email`/`email_address`, `phone`/`mobile_number`, `language`, `email_verified`/`phone_verified`.

### 3.6 GET /api/onboarding/status?parent_id=<id>
`exam_router.py:492-630`. Response (all booleans; `exam_router.py:612-617`):
```json
{"preferences_completed": true, "child_profile_completed": true,
 "exam_selected": false, "onboarding_complete": false}
```
`onboarding_complete = preferences_completed && child_profile_completed && exam_selected`
(`exam_router.py:605-610`). Auth: testing bypass; `parent_id` from query. Used post-login to decide
dashboard banners/CTAs (§8 step 4); also used to detect "no child yet" → route to phase-06 prompt.

### 3.7 GET /api/onboarding/child?parent_id=<id>
`child_router.py:164`; service `ChildService.get_child_profile`. Success 200
`ChildProfileResponse`: `{child_id, parent_id, name, age, grade, current_level, username,
created_at, updated_at}` (phase-01 §7.B item 3; `child_models.py:22-265` request side applies to
POST only). 404 when the parent has no child. This is the app's source of `child_id` (§2).

### 3.8 GET /api/parent/dashboard/{child_id}
`parent_dashboard_router.py:42-64`; service `parent_dashboard_service.py:35-172`. Success 200
`ChildDashboard` (`parent_models.py:16-55`):
```json
{"child_id": "child_abc123", "child_name": "Aarav Sharma", "overall_progress": 67.5,
 "current_streak": 5, "hours_studied_today": 3.5, "hours_studied_week": 22.0,
 "schedule_status": "on_track", "days_until_exam": 45,
 "weak_areas": [{"subject": "Physics", "topic": "Thermodynamics", "accuracy": "45%"}],
 "upcoming_tasks": [{"date": "2024-01-16", "topic": "Physics - Optics", "duration": "2 hours"}],
 "recent_test_score": 78.5, "last_active": "2024-01-15T18:30:00Z"}
```
Field rules: `weak_areas` and `upcoming_tasks` items are `Dict[str,str]` — the service builds keys
`subject/topic/accuracy` and `date/topic/duration` (`parent_dashboard_service.py:113-138`) but the
model accepts any string map, so the client must render from whatever keys arrive and tolerate
missing keys. `recent_test_score` may be `null`. `last_active` is always an ISO datetime.
404 `{"detail":"Child not found: <id>"}` when the child doc is missing (`parent_dashboard_service.py:50-51`,
router `:57-58`); 500 otherwise.

### 3.9 GET /api/parent/reports/weekly/{child_id}?week_start=YYYY-MM-DD
`parent_dashboard_router.py:67-90`; service `parent_dashboard_service.py:174-297`. `week_start` is
optional (defaults to Monday of the current week server-side, `:187-192`); `week_end =
week_start + 6 days` (:192). Success 200 `WeeklyReport` (`parent_models.py:58-98`):
```json
{"child_id": "child_abc123", "week_start": "2026-10-26", "week_end": "2026-11-01",
 "total_hours_studied": 28.5, "previous_week_hours": 25.0, "topics_completed": 12,
 "tests_taken": 3, "average_test_score": 76.5, "attendance_rate": 85.7,
 "subject_breakdown": {"Physics": {"hours": 10.0, "score": 72.0}},
 "achievements": ["7-day streak"], "areas_of_concern": ["Low study attendance"]}
```
`average_test_score` nullable. Achievements are canned strings from service thresholds
(`parent_dashboard_service.py:260-266`); areas of concern likewise (:269-275). No 404 path — the
service returns zeros for a child with no data; the router only 500s.

### 3.10 Goals
- `POST /api/parent/goals/{child_id}` (`parent_dashboard_router.py:161-185`; service
  `parent_dashboard_service.py:390-415`). Body `GoalRequest` (`parent_models.py:207-227`):
  `{child_id, goal_type, target_value, deadline?}` — the router overwrites body `child_id` with
  the path value (`parent_dashboard_router.py:176-177`), so the client may
  send either but path wins. `goal_type ∈ target_score|daily_hours|topic_completion|test_count`,
  `target_value > 0` (Pydantic `gt=0`, `:215`), `deadline` optional `YYYY-MM-DD`. Success 201
  `Goal` (`parent_models.py:165-204`) with `goal_id = "goal_{child_id}_{epochSeconds}"`,
  `current_value: 0.0`, `status: "active"`, `created_at` ISO. Errors: 422 invalid type/value;
  500.
- `GET /api/parent/goals/{child_id}` (`parent_dashboard_router.py:188-208`; service
  `:417-437`): 200 JSON array, newest `created_at` first. Empty array (not 404) when none.
- `PUT /api/parent/goals/{child_id}/{goal_id}` (`parent_dashboard_router.py:211-234`; service
  `:439-471`). Body `GoalUpdateRequest` (`parent_models.py:230-246`): all-optional
  `{target_value?, deadline?, status?}`, `status ∈ active|completed|failed|cancelled`. Service
  merges non-null fields and stamps `completed_at` when `status` becomes `completed`
  (`parent_dashboard_service.py:460-463`). 404 `{"detail":"Goal not found: <id>"}`; 422; 500.

### 3.11 Notification settings
- `GET /api/parent/notifications/settings?parent_id=<id>` (`parent_dashboard_router.py:112-132`;
  service `:352-368`): 200 `NotificationSettings` (`parent_models.py:133-162`) — 9 booleans:
  `missed_days_alert` (default true), `daily_summary` (false), `test_completion` (true),
  `schedule_milestones` (true), `weekly_report` (true), `low_performance_alert` (true),
  `achievement_notifications` (true), `email_notifications` (true), `push_notifications`
  (false), plus required `parent_id`. **When no doc exists the service returns defaults**
  (`parent_dashboard_service.py:362-364`) — the client still shows all toggles and PUTs the full
  object back.
- `PUT /api/parent/notifications/settings` (`parent_dashboard_router.py:135-158`; service
  `:370-388`): body is the full `NotificationSettings` **including `parent_id`** (Pydantic
  `Field(...)` at `parent_models.py:136`), returns 200 with the same shape. 422 if `parent_id`
  missing; 500.

## 4. Error mapping to user-visible strings

`ApiError` (phase-04) → copy rules (never show `code` raw to users):

| Context | `code` / status | User-visible string |
|---|---|---|
| ParentLogin | `AUTHENTICATION_REQUIRED` (401) | "Incorrect email or password." |
| ParentRegister | 400/422 with `detail` | Show `detail` verbatim (backend strings are already user-presentable, e.g. duplicate email, password mismatch) |
| Verify screens | 400 with `detail` | Show `detail` verbatim ("Invalid verification code", "Verification code has expired. Please request a new one.", "Verification code has already been used") |
| Verify screens | 404 | "No account found for this email/phone." |
| Dashboard/Reports/Goals/Settings | 404 `Child not found...` | "Child profile not found." (+ CTA to phase-06 creation when on dashboard) |
| Goals PUT | 404 `Goal not found...` | "This goal no longer exists." (refresh list) |
| Any | `NETWORK_UNAVAILABLE` | "No internet connection." (trigger offline UI per §12) |
| Any | `RATE_LIMITED` | "Too many attempts. Please wait a moment and try again." |
| Any | `INTERNAL_ERROR` / other | "Something went wrong. Please try again." + retry affordance |

## 5. Form validation rules (client mirrors backend; backend remains authority)

| Field | Rule | Backend mirror |
|---|---|---|
| name | length 2–100 | `simple_register_router.py:24` |
| email | `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$` | `EmailStr` (`auth_models.py:44`) |
| password | length ≥ 8, ≥1 letter `[A-Za-z]`, ≥1 digit `\d` | `auth_models.py:49-84` |
| repeat_password | equal to password | service-level check (ValueError → 400) |
| phone | `^\+91[6-9]\d{9}$` | `auth_models.py:145` |
| email code | 6 chars `[A-Z0-9]` (accept lowercase, uppercase before send) | `verification_models.py:85-111` |
| phone OTP | 6 digits `^\d{6}$` | `verification_models.py:241-267` |
| goal_type | enum `target_score\|daily_hours\|topic_completion\|test_count` | `parent_models.py:211` |
| target_value | > 0 | `parent_models.py:215` |
| deadline | optional, `YYYY-MM-DD`, not in the past | client-side only |

Validate on field blur + on submit; disable submit while any rule fails or a call is in flight.
Debounce: none needed (validation is synchronous); network-triggering actions (resend code) use a
60-second cooldown button state.

## 6. Navigation contract

The parent go_router branch uses these logical route names (exact strings): `parent_welcome`, `parent_register`,
`parent_verify_email?email={email}`, `parent_verify_phone?phone={phone}`, `parent_login`,
`parent_forgot_password`, `parent_dashboard`, `parent_reports?child_id={child_id}`,
`parent_goals?child_id={child_id}`, `parent_settings`, `parent_results?child_id={child_id}`.
Phase-07 registers `child_login` in a separate graph; Settings' "switch to child mode" navigates
there. Dashboard is the parent-graph start destination after restore decides (§8).

## 7. Screen specifications (layout, states, events)

Common: every screen is a Flutter go_router destination with a Riverpod `Notifier` exposing one
immutable `UiState` and consuming Phase 04 session events. One-shot UI events use a scoped Dart
stream. Loading uses Phase 03 skeleton/progress; errors use `ErrorState` with retry. Every remote
field comes from the endpoint model; failures never substitute fabricated content.

### 7.1 WelcomeScreen (route parent_welcome)
Layout: hero + app name, `GlassButton` "I'm a Parent" → `parent_register`, `GlassButton`
"Child sign-in" → `child_login` (registered by phase-07; navigate by global route string).
UiState: `WelcomeUiState` (stateless).
Events: `OnParentClick`, `OnChildClick`.

### 7.2 ParentRegisterScreen (route parent_register)
Layout: `GlassCard` form — `GlassTextField` name, email, mobile (prefix +91), password,
repeat_password; `GlassButton` "Create account" (primary); text button → `parent_login`;
"Or continue with" row: Google button (optional alternate), "Use phone instead" link toggling the
email/OTP register variant (§3.2).
Api: `ParentRepository.registerSimple(...)` → 201 → navigate `parent_verify_email?email=...` when
an email verification step is offered; because simple registration sets
`verification_required:false` (`simple_register_service.py:83`) and the dev code is available,
this phase routes simple-register success → **VerifyEmail (optional skip)** → ParentLogin; the
screen shows "Registration successful — log in to continue." after verify/skip. Phone-variant
success → `parent_verify_phone` → login.
Validation per §5. UiState:
```text
ParentRegisterUiState(
    name: String = "", email: String = "", phone: String = "",
    password: String = "", repeatPassword: String = "",
    nameError: String? = null, emailError: String? = null, phoneError: String? = null,
    passwordError: String? = null, repeatPasswordError: String? = null,
    submitting: Boolean = false, registerError: String? = null,
    registeredEmail: String? = null,   // non-null → navigate to verify/login
)
```
Events: `OnNameChange`, `OnEmailChange`, `OnPhoneChange`, `OnPasswordChange`,
`OnRepeatPasswordChange`, `OnSubmit`, `OnLoginClick`, `OnGoogleClick` (optional),
`OnUsePhoneInsteadToggle`, `OnErrorShown`.

### 7.3 VerifyEmailScreen (route parent_verify_email?email=) / VerifyPhoneScreen (route parent_verify_phone?phone=)
Layout: title (email/phone masked), 6-cell code input, `GlassButton` "Verify", "Resend code"
(60 s cooldown), "Skip for now" (simple-register path only) → ParentLogin.
Api: send on entry (`/verify/email/send` or `/verify/phone/send`); confirm on submit. Dev builds
(BUILD_TYPE debug): surface the returned `code`/`otp` in a clearly-labeled "DEV ONLY" banner
(§3.3) — never show in release.
UiState:
```text
VerifyUiState(
    target: String, code: String = "", codeError: String? = null,
    sending: Boolean = false, verifying: Boolean = false,
    devCode: String? = null, resendCooldownSec: Int = 0,
    verified: Boolean = false,               // → navigate to ParentLogin
    error: String? = null,
)
```
Events: `OnCodeChange`, `OnVerify`, `OnResend`, `OnSkip`, `OnErrorShown`.

### 7.4 ParentLoginScreen (route parent_login)
Layout: `GlassCard` with email + password `GlassTextField`s (password toggle), "Forgot password?"
text button → `parent_forgot_password` (see §12 — disabled placeholder), `GlassButton` "Log in",
link → `parent_register`. Optional alternates: "Log in with OTP" (phone + OTP inline, §3.4) and
Google button.
Api: `SessionRepository.loginWithEmail` (phase-04) → Success → §8 restore tree (dashboard).
UiState:
```text
ParentLoginUiState(
    email: String = "", password: String = "",
    emailError: String? = null, passwordError: String? = null,
    submitting: Boolean = false, loginError: String? = null,  // mapped per §4
    loggedIn: Boolean = false,          // → navigation handled by root
)
```
Events: `OnEmailChange`, `OnPasswordChange`, `OnSubmit`, `OnRegisterClick`,
`OnForgotPasswordClick`, `OnOtpLoginClick` (optional), `OnGoogleClick` (optional), `OnErrorShown`.

### 7.5 ParentForgotPasswordScreen (route parent_forgot_password) — BACKEND CHANGE REQUIRED (gap #3)
Spec'd UI per §12 (email input + "Send reset link" + confirmation copy). The Riverpod controller **must not
call any endpoint** — none exists (phase-01 §11 #3). The screen shows an explanatory notice:
"Password reset isn't available yet." and a back button. UiState: `ForgotPasswordUiState
(email: String = "", submitted: Boolean = false)`. Events: `OnEmailChange`, `OnSubmit`
(local-only), `OnBack`.

### 7.6 ParentDashboardScreen (route parent_dashboard)
Layout (scroll column of `GlassCard`s):
1. Header card: `child_name`, `StatusPill` for `schedule_status` (`on_track`→info,
   `behind`→error, `ahead`→success), "days until exam" line.
2. Progress row: `overall_progress` (%), `current_streak` (days), `hours_studied_today`,
   `hours_studied_week`.
3. Weak areas card: list from `weak_areas` (`{subject, topic, accuracy}` strings); empty →
   "No weak areas reported yet." (expected while gap #6 unfixed).
4. Upcoming tasks card: `upcoming_tasks` (`date`, `topic`, `duration`); empty →
   "No upcoming tasks.".
5. Recent test score card: `recent_test_score` % or "No tests taken yet." when null.
6. CTAs: `GlassButton` "Schedule a test" (→ phase-08 route placeholder `parent_schedule`),
   `GlassButton` "View results" (→ `parent_results?child_id=`).
Top bar: settings icon → `parent_settings`; refresh action.
Data: §3.8; `child_id` resolved per §8 step 2. Pull-to-refresh re-fetches; cache behavior per §12.
UiState:
```text
ParentDashboardUiState(
    loading: Boolean = true, childId: String? = null, childName: String? = null,
    overallProgress: Float? = null, currentStreak: Int? = null,
    hoursToday: Float? = null, hoursWeek: Float? = null,
    scheduleStatus: String? = null, daysUntilExam: Int? = null,
    weakAreas: List<Map<String, String>> = emptyList(),
    upcomingTasks: List<Map<String, String>> = emptyList(),
    recentTestScore: Float? = null, lastActive: String? = null,
    onboardingComplete: Boolean? = null,   // §3.6; false → banner + "Set up" CTA
    offline: Boolean = false, error: String? = null,
)
```
Events: `OnRefresh`, `OnSettingsClick`, `OnScheduleTestClick`, `OnViewResultsClick`,
`OnSetupChildClick`, `OnRetry`, `OnSessionExpiredAck`.

### 7.7 WeeklyReportScreen (route parent_reports?child_id=)
Layout: week selector (prev/next week arrows around `week_start`–`week_end`), summary
`GlassCard`s (hours vs previous week, topics completed, tests taken, attendance %,
average score when non-null), `subject_breakdown` list, achievements list, areas-of-concern list
with `StatusPill` warning styling.
Api: §3.9. UiState:
```text
WeeklyReportUiState(
    loading: Boolean = false, childId: String = "", weekStart: String = "",
    weekEnd: String = "", totalHours: Float? = null, previousWeekHours: Float? = null,
    topicsCompleted: Int? = null, testsTaken: Int? = null,
    averageTestScore: Float? = null, attendanceRate: Float? = null,
    subjectBreakdown: Map<String, Map<String, Float>> = emptyMap(),
    achievements: List<String> = emptyList(), areasOfConcern: List<String> = emptyList(),
    offline: Boolean = false, error: String? = null,
)
```
Events: `OnPreviousWeek`, `OnNextWeek`, `OnRetry`, `OnBack`.

### 7.8 GoalsScreen (route parent_goals?child_id=)
Layout: goal list (`GlassCard` per goal: type label, progress `current_value/target_value`,
deadline, `StatusPill` for status); FAB/`GlassButton` "New goal" opens bottom sheet form:
goal_type chips, target value `GlassTextField`, optional deadline date picker; edit via goal card
menu (change status / edit target).
Api: §3.10 (GET on entry, POST create, PUT update). UiState:
```text
GoalsUiState(
    loading: Boolean = false, childId: String = "", goals: List<GoalUi> = emptyList(),
    sheetOpen: Boolean = false, editingGoalId: String? = null,
    goalType: String = "target_score", targetValue: String = "",
    targetError: String? = null, deadline: String? = null,
    saving: Boolean = false, error: String? = null,
)
GoalUi(goalId: String, goalType: String, targetValue: Float,
                  currentValue: Float, deadline: String?, status: String)
```
Events: `OnRefresh`, `OnCreateClick`, `OnEditClick(goalId)`, `OnGoalTypeChange`,
`OnTargetValueChange`, `OnDeadlineChange`, `OnSave`, `OnCancelSheet`, `OnStatusChange(goalId,status)`,
`OnDelete` (not supported by backend — absent), `OnRetry`.

### 7.9 SettingsScreen (route parent_settings)
Layout: profile card from `/me` (name or email/phone fallback — remember key variance §3.5);
notification toggles (9 switches from §3.11); "Weekly report" link → `parent_reports`; action
list: "Switch to child mode" (→ `child_login`), "Log out" (confirm dialog).
Api: GET settings on entry; PUT on every toggle change (debounced 300 ms per toggle; optimistic
UI, revert + toast on Failure). Logout: `SessionRepository.logout(PARENT)` → clear + navigate to
`parent_login` regardless of call result (phase-04 semantics).
UiState:
```text
ParentSettingsUiState(
    loading: Boolean = true, displayName: String? = null, email: String? = null,
    phone: String? = null,
    missedDaysAlert: Boolean = true, dailySummary: Boolean = false,
    testCompletion: Boolean = true, scheduleMilestones: Boolean = true,
    weeklyReport: Boolean = true, lowPerformanceAlert: Boolean = true,
    achievementNotifications: Boolean = true, emailNotifications: Boolean = true,
    pushNotifications: Boolean = false,
    savingSettings: Boolean = false, settingsError: String? = null,
    confirmLogout: Boolean = false, loggingOut: Boolean = false, error: String? = null,
)
```
Events: `OnToggle(key)`, `OnWeeklyReportClick`, `OnSwitchToChildClick`, `OnLogoutClick`,
`OnLogoutConfirm`, `OnLogoutDismiss`, `OnRetry`, `OnErrorShown`.

### 7.10 ParentResultsScreen (route parent_results?child_id=)
Load `GET /api/analytics/student/{student_id}` using the real resolved child ID. Render loading,
the returned analysis list, a genuine empty state, or the mapped error. Phase 10 adds the detailed
viewer; this phase must not show a fabricated report or static placeholder score. `ParentResultsUiState`
contains the child ID, loading/error state, and response-derived analysis summaries only.

## 8. Session-restore routing (app start; root Riverpod controller + go_router redirect)

Run once per cold start, before choosing the start destination:
1. `SessionManager.getActiveRole()`. If `PARENT` and `!isExpired(PARENT)` → call
   `SessionRepository.getMe(PARENT)`. Success → continue. `Failure` with
   `code=AUTHENTICATION_REQUIRED` → the refresh coordinator already attempted refresh and cleared;
   go to step 5. `Failure` with `code=NETWORK_UNAVAILABLE` → show offline gate screen with Retry
   (do not enter the dashboard without data; cached-last dashboards render per §12 once reachable
   again).
2. Resolve the child: `GET /api/onboarding/child?parent_id=<parent_id from login response slot>`.
   Success → stash `child_id` in dashboard state. 404 → keep `childId=null` (dashboard shows
   setup CTA).
3. Fetch `GET /api/onboarding/status?parent_id=` → stash `onboardingComplete` (§3.6).
4. Fetch dashboard (§3.8) when `childId != null`; on 404 `Child not found` fall back to step 2's
   null state.
5. No/expired/failed session → `parent_welcome`. (Expired triggers `refreshTokens` first per
   phase-04 §9; only on refresh Failure land here.)
Restore never creates sessions and never touches the child slot. Expired-session restore failure
must emit `SessionEvent.SessionExpired(PARENT)` exactly once (refresh coordinator contract).

## 9. Dashboard data-source notes (which collections feed it)

Per phase-01 §5 and `parent_dashboard_service.py:35-172`, `GET /api/parent/dashboard/{child_id}`
derives every field from Firestore reads:

| Response field | Source collection | Writer (phase-01 §5) |
|---|---|---|
| `child_name` | `children` doc | `child_service.py:133-179` |
| `overall_progress`, `days_until_exam`, `schedule_status`, `upcoming_tasks` | `schedules` where `student_id==child_id`, `status=="active"` (`parent_dashboard_service.py:56-65,98-138`) | `schedule_service.py`, `gemini_scheduler_service.py:450` |
| `current_streak`, `hours_studied_today`, `hours_studied_week`, `last_active` | `progress` last 7 entries (:80-86, :89-91, :145-150) | `progress_tracker*.py` services |
| `weak_areas`, `recent_test_score` | `analytics` latest doc by `created_at` (:68-77, :113-143) | `analytics_service.py:624-635` — **writes `analytics_reports`, not `analytics`** |

**Gap #6 caveat (phase-01 §11 #6):** the read collection `analytics` does not match the writer
collection `analytics_reports`. Consequence today: `weak_areas` is `[]` and
`recent_test_score` is `null` even after a successful analysis, until the backend fixes the name.
The UI must treat those as first-class empty states (never as errors) and the weekly report's
`average_test_score` may stay null for the same persistence gap (submissions are not persisted —
phase-01 §11 #4). Additionally, even with the collection fixed, the service reads flat doc fields
`weak_topics` and `percentage` (`parent_dashboard_service.py:115,143`), while the stored report
nests data under `overview`/`topic_analysis` (`analytics_models.py:706-762`) — the client renders
whatever arrives and does not synthesize missing fields.

## 10. DTO and real Dio data-source catalog

Create `features/parent/data/dto/parent_dtos.dart` and `onboarding_dtos.dart` with
`json_serializable` mirrors of:

- simple/email/phone/Google registration requests and `AuthResponse`;
- email/phone verification requests and `VerificationResponse`;
- onboarding status and child profile;
- `ChildDashboard`, `WeeklyReport`, `Goal`, goal create/update requests, and `NotificationSettings`.

Response DTOs ignore unknown keys and mark only genuinely optional backend fields nullable. Required
IDs, role state, and mutation outcomes are validated rather than replaced with local defaults.

Implement real Dio methods in `parent_remote_data_source.dart` and
`onboarding_remote_data_source.dart`:

| Method | Real request |
|---|---|
| `registerSimple` / `registerWithEmail` / `registerWithPhone` / `registerWithGoogle` | Corresponding documented POST under `/api/auth/register` |
| `sendEmailCode` / `confirmEmailCode` | `POST /verify/email/send` / `POST /verify/email/confirm` |
| `sendPhoneOtp` / `confirmPhoneOtp` | `POST /verify/phone/send` / `POST /verify/phone/confirm` |
| `onboardingStatus` / `getChild` | GET endpoints with real `parent_id` query |
| `dashboard` / `weeklyReport` | GET with real child ID and optional real `week_start` |
| `goals` / `createGoal` / `updateGoal` | GET/POST/PUT with response-derived child/goal IDs |
| `notificationSettings` / `updateNotificationSettings` | GET/PUT with real parent ID/settings body |

Auth comes from Phase 04's active-parent Bearer interceptor. Every method returns decoded endpoint
data or throws for `ApiErrorMapper`; none reads a fixture or constructs a fallback response.

## 11. Accessibility matrix

| Screen | Requirements |
|---|---|
| All | Touch targets ≥48 logical pixels; Phase 03 contrast; icon buttons have Flutter `Semantics` labels; form fields have persistent labels |
| Register/Login | Errors use assertive live-region semantics; password toggle exposes state; disabled submit reasons are readable |
| Verify screens | One labelled code field using an appropriate Flutter keyboard; resend cooldown uses a polite live region with actual remaining time |
| Dashboard | Status values and response-derived metrics have text labels; zero-item lists announce genuine empty copy |
| Weekly report | Previous/next buttons are labelled; real deltas are stated in words, not color alone |
| Goals | Type chips and actual current/target values are read as sentences; status pills are textual |
| Settings | Each switch is labelled; logout confirmation has named Log out/Cancel actions and managed focus |

## 12. BACKEND CHANGE REQUIRED items in this phase

- **Gap #3 — forgot password (phase-01 §11 #3).** No reset endpoint exists; `verification_service.py`
  implements only the four verification functions. Proposed flow (proposal only — backend team
  owns the contract; do not implement against it): `POST /api/auth/password/reset-request {email}`
  → Firebase REST `sendOobCode` (verifyViaEmail) or an OTP variant reusing `verification_codes`;
  `POST /api/auth/password/reset-confirm {email, code, new_password}` → `accounts:resetPassword`.
  Client stance: ParentForgotPasswordScreen (§7.5) exists with the spec'd layout but is gated —
  primary action shows "Password reset isn't available yet." No network call is made. Logged in
  the gap log; revisited when the backend lands the endpoints.
- **Gap #6 — dashboard analytics mismatch (phase-01 §11 #6).** §9 caveat; client renders empty
  states, never fabricates weak areas or scores.
- **Gap #7 — no ownership enforcement (phase-01 §11 #7).** Client always sends Bearer and only
  ever uses `parent_id`/`child_id` from its own login (phase-01 §6.1 consequence).
- **Gap #9 — silent password-check skip (phase-01 §11 #9).** Testers must not treat a successful
  wrong-password login in a misconfigured dev backend as an app bug (phase-04 records it).

## 13. Offline behavior (fixed contract)

Offline state comes from real Dio transport failures and platform reachability information, never a
simulated connectivity flag. On `NETWORK_UNAVAILABLE`:
- Dashboard, WeeklyReport, Goals, and Settings may retain only their last successful in-memory
  endpoint payload and render it under "You're offline — showing last loaded data." with Retry.
- Mutations do not queue or claim success; they show "No internet connection." and preserve form input.
- Restore stops at the offline gate; Retry repeats the real session/onboarding calls.
- No cached payload is treated as a fresh response and no missing cached payload is replaced with
  fabricated content.
