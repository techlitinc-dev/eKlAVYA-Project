# Phase 05 — Instructions

Sequential build steps. Execute in order; each step names its verification test(s). This phase
assumes phase-04 is signed off: `AuthApi`, `SessionRepository`, `SessionManager`, `ApiResult`,
`SessionEvents`, and the OkHttp pipeline exist and are green.

Guardrails (apply throughout): never invent an endpoint or field (contracts are exactly
`text.md` §3); every network call goes through `ApiResult`; every screen consumes
`SessionEvents`; user-visible strings come from the `text.md` §4 mapping; validation rules are
`text.md` §5 and the backend stays the authority (client rules are pre-checks only).

## Step 1 — DTOs and ParentApi

Create `data/dto/ParentDtos.kt`, `data/dto/OnboardingDtos.kt` and `data/api/ParentApi.kt`
exactly per `text.md` §10 (byte-exact JSON names; unknown keys ignored; optional response fields
nullable). Register `ParentApi` in the phase-04 `NetworkModule` (same Retrofit instance — add a
provider method there; do not create a second Retrofit).

Verify with test `ParentDtoSerializationTest`: decode the JSON samples in `text.md` §3.1, §3.3,
§3.8, §3.9, §3.10, §3.11; assert `Goal` decodes with `completed_at=null`; assert
`NotificationSettings` decodes with the documented defaults when the service omits keys
(`parent_dashboard_service.py:362-364` returns a full object, but tolerate omissions).

## Step 2 — ParentRepository

Create `data/repository/ParentRepository.kt` (`@Singleton`), wrapping `ParentApi` calls in
`runCatching` → `ApiResult` via the phase-04 `ApiErrorMapper`. Functions:
`registerSimple`, `registerWithEmail`, `registerWithPhone`, `registerWithGoogle`,
`sendEmailCode`, `confirmEmailCode`, `sendPhoneOtp`, `confirmPhoneOtp`, `onboardingStatus`,
`getChild`, `dashboard`, `weeklyReport`, `goals`, `createGoal`, `updateGoal`,
`notificationSettings`, `updateNotificationSettings`. The send/confirm functions return the raw
`JsonObject` for sends (the dev `code`/`otp` fields) mapped into a small
`SendCodeResult(message, devCode: String?)` type — never expose `JsonObject` to ViewModels.

Verify with test `ParentRepositoryTest` (MockWebServer): duplicate-email 400 maps
`ApiError(code="VALIDATION_ERROR", message="An account with email ... already exists. Please
login instead.", httpStatus=400)`; `/verify/email/send` 200 exposes `devCode`; dashboard 404
`Child not found: child_x` maps to `NOT_FOUND` with that message; goals GET returns `[]` decoded
as empty list; a garbage-body 500 maps to `INTERNAL_ERROR`.

## Step 3 — Form validation helpers

Create `ui/parent/validation/ParentValidators.kt`: pure functions `validateName`,
`validateEmail`, `validatePassword` (≥8, letter+digit), `validatePhone` (`^\+91[6-9]\d{9}$`),
`validateRepeatPassword`, `validateOtp` (`^\d{6}$`), `validateEmailCode` (6 alnum), plus
`validateGoal(target: String, type: String)` returning field-error strings or null. No Android
dependencies (JVM-testable).

Verify with test `ParentValidatorsTest`: table-driven — empty/short/long names, malformed
emails, password "abcdefgh" (no digit) fails, "abcd1234" passes, phone "+911234567890" fails
(starts 1), "+919876543210" passes, OTP "12345" fails / "123456" passes. Rules mirror
`text.md` §5 and the cited backend validators.

## Step 4 — Navigation graph

Create `ui/navigation/ParentNavGraph.kt` with the routes in `text.md` §6 (exact strings,
including query args `email`, `phone`, `child_id`). Add a `RootViewModel` +
`MainActivity` restore flow per `text.md` §8 before setting the start destination (show a branded
splash while `Restoring`). Settings "switch to child mode" navigates to the global route string
`child_login` (phase-07 registers it; if absent in the current build the action shows
"Coming in a later update" — do not crash on `IllegalArgumentException`; wrap the navigate call).

Verify with test `ParentNavGraphTest` (Compose navigation test): every route in `text.md` §6
resolves to its screen; argument values round-trip (`parent_verify_email?email=a%40b.com` parses
`email=a@b.com`); unknown route falls back to `parent_welcome`.

## Step 5 — WelcomeScreen and ParentRegisterScreen

Build `ui/parent/welcome/WelcomeScreen.kt` (+ `WelcomeViewModel`, stateless per `text.md` §7.1)
and `ui/parent/register/ParentRegisterScreen.kt` + `ParentRegisterViewModel` + UiState exactly as
`text.md` §7.2. Wire validators from step 3 (validate on blur and on submit; `submitting` blocks
the button). Success path: `registerSimple` 201 → one-shot navigate to
`parent_verify_email?email=...` (simple path — `verification_required:false` per
`text.md` §3.1 Note 3); Google/phone alternates may be stubbed behind the same buttons but must
call their repository functions when enabled. Map errors per `text.md` §4.

Verify with tests:
- `ParentRegisterViewModelTest` (fake ParentRepository): invalid email + short password →
  submit blocked, field errors set, no repository call; duplicate email 400 → `registerError`
  shows backend `detail`; success → `registeredEmail` set and navigation event emitted.
- `ParentRegisterScreenTest` (Compose): typing an invalid phone shows the phone error text;
  submit button disabled while `submitting`; error `ErrorState`/banner appears on failure.

## Step 6 — VerifyEmailScreen and VerifyPhoneScreen

Build `ui/parent/verify/VerifyEmailScreen.kt`, `VerifyPhoneScreen.kt`, shared
`VerifyViewModel` + `VerifyUiState` per `text.md` §7.3. On entry: auto-send (email or phone by
route arg). Dev builds only (`BuildConfig.DEBUG`): show the returned `devCode`/`otp` in a "DEV
ONLY — code: X" banner. Resend enforces a 60 s cooldown with `resendCooldownSec` ticking.
Confirm success → navigate `parent_login` (with the verified target prefilled on login where
trivially available). Skip button visible only for the simple-register path.

Verify with tests:
- `VerifyViewModelTest`: send success populates `devCode` (fake repo returns
  `SendCodeResult(message="OTP sent", devCode="123456")`); confirm 400 → `error` shows backend
  detail; resend twice → second send immediate-call rejected by cooldown state; success →
  `verified=true` one-shot.
- `VerifyScreenTest`: 6-digit OTP entry enables Verify; cooldown text updates; DEV banner absent
  when `BuildConfig.DEBUG == false` (gate the composable param).

## Step 7 — ParentLoginScreen (+ forgot-password placeholder)

Build `ui/parent/login/ParentLoginScreen.kt` + `ParentLoginViewModel` per `text.md` §7.4. Submit
→ `sessionRepository.loginWithEmail` → Success → run the `text.md` §8 restore tree inline
(same RootViewModel logic; extract it into a `ParentSessionRestorer` helper class so MainActivity
and the login VM share it). Build `ui/parent/login/ForgotPasswordScreen.kt` per `text.md` §7.5:
form fully laid out, submit is local-only, notice "Password reset isn't available yet." — no
network call. Mark the code with `// BACKEND CHANGE REQUIRED (gap #3, phase-01 §11)` at the
stub.

Verify with tests:
- `ParentLoginViewModelTest`: 401 → `loginError = "Incorrect email or password."` (§4 mapping);
  success → restorer invoked (mock `ParentSessionRestorer`); `SessionExpired` event → UiState
  `loginError` cleared and global expired handling triggered.
- `ParentLoginScreenTest`: password visibility toggle works; validation errors render;
  forgot-password navigates to `parent_forgot_password`.
- `ForgotPasswordScreenTest`: submit does not invoke any repository (fake that throws on call).

## Step 8 — ParentSessionRestorer + onboarding status

Implement `domain/ParentSessionRestorer.kt` executing `text.md` §8 steps 1–4 in order:
`getMe(PARENT)` → `getChild(parentId)` → `onboardingStatus(parentId)` → `dashboard(childId)`.
Expose a result sealed type `RestoreResult(Restored(childId?, onboardingComplete, dashboard?),
LoggedOut, Offline)` and never throw. RootViewModel and ParentLoginViewModel both consume it.

Verify with test `ParentSessionRestorerTest` (fakes): happy path returns `Restored` with all
data; child 404 → `Restored(childId=null)`; me 401 → `LoggedOut`; me network error → `Offline`;
dashboard 404 → still `Restored` with `dashboard=null`; exactly one call per endpoint (no
duplicate fetches).

## Step 9 — ParentDashboardScreen

Build `ui/parent/dashboard/ParentDashboardScreen.kt` + `ParentDashboardViewModel` + UiState per
`text.md` §7.6 using phase-03 components. Render rules: `schedule_status` → `StatusPill`
(on_track=info, behind=error, ahead=success); weak areas and upcoming tasks iterate the
`Map<String,String>` with the documented keys but tolerate missing keys (render only present
values); `recent_test_score=null` → "No tests taken yet."; `onboardingComplete==false` → banner
with "Set up" CTA (`OnSetupChildClick` routes to the phase-06 route placeholder
`parent_child_setup` — register the route name now, screen lands in P06); pull-to-refresh →
`OnRefresh` re-runs dashboard fetch; offline banner per `text.md` §13 with cached payload.

Verify with tests:
- `ParentDashboardViewModelTest`: full §3.8 payload → all UiState fields; empty
  `weak_areas`/`upcoming_tasks` + null score → empty-state copy flags; 404 → `error` with §4
  mapping + setup CTA state; `SessionExpired` → global expired state.
- `ParentDashboardScreenTest`: renders child name, stats, weak-area rows, upcoming-task rows,
  both CTAs ("Schedule a test", "View results"); empty states render the exact copy; error state
  shows `ErrorState` with retry.

## Step 10 — WeeklyReportScreen

Build `ui/parent/reports/WeeklyReportScreen.kt` + ViewModel + UiState per `text.md` §7.7. Default
`week_start` = current Monday computed client-side; prev/next re-fetch with
`week_start=YYYY-MM-DD` (service recomputes `week_end`, `text.md` §3.9). Delta copy vs
`previous_week_hours` in words ("2.5 h more than last week").

Verify with tests: `WeeklyReportViewModelTest` (fake repo returns canned `WeeklyReport`) —
navigation changes `weekStart` and refetches; null `average_test_score` hides the score row.
`WeeklyReportScreenTest` — renders summary cards, subject rows, achievements, concerns.

## Step 11 — GoalsScreen

Build `ui/parent/goals/GoalsScreen.kt` + ViewModel + UiState per `text.md` §7.8. Create sheet
validates `target_value > 0` (`validateGoal`); `goal_type` chips map to the four enum values;
edit menu offers status changes (`active/completed/failed/cancelled`) and target/deadline edits
via `updateGoal`. On 404 from PUT → toast per §4 + `OnRefresh`.

Verify with tests: `GoalsViewModelTest` — create success appends to list with `status="active"`;
invalid target blocks save; PUT 404 → error + refresh requested; `GoalsScreenTest` — list rows
render progress "78.5 / 85", sheet opens/closes, chips selectable.

## Step 12 — SettingsScreen

Build `ui/parent/settings/ParentSettingsScreen.kt` + ViewModel + UiState per `text.md` §7.9.
Load: profile via `sessionRepository.getMe(PARENT)` (read `name`, then `email`/`email_address`,
then `phone`/`mobile_number` fallbacks — `text.md` §3.5), settings via
`notificationSettings(parentId)` (defaults render when doc absent). Toggles: optimistic update,
300 ms debounce per key to `updateNotificationSettings` (full `NotificationSettings` body
including `parent_id`, `text.md` §3.11); Failure → revert the toggle + `settingsError` snackbar.
Logout: confirm dialog → `sessionRepository.logout(PARENT)` → clear + navigate `parent_login`
regardless of result; `SessionEvent.LoggedOut(PARENT)` observed.

Verify with tests: `ParentSettingsViewModelTest` — doc with only `email_address` renders email
from it; toggle flips immediately then persists (advance debounce clock); PUT failure reverts;
logout emits navigation + clears state; `ParentSettingsScreenTest` — 9 switches render with
labels, dialog confirm flow works.

## Step 13 — ParentResultsScreen placeholder

Build `ui/parent/results/ParentResultsScreen.kt` per `text.md` §7.10 (no API calls). Wire the
dashboard "View results" CTA to `parent_results?child_id={childId}`.

Verify with `ParentResultsScreenTest`: copy renders, back navigates to `parent_dashboard`.

## Step 14 — Offline detection and retry banner

Implement `data/network/ConnectivityObserver.kt` (Hilt singleton wrapping
`ConnectivityManager.registerDefaultNetworkCallback`) exposing `Flow<Boolean>` (online). Each
screen VM from steps 9–12 combines it with repository failures: any
`ApiError.code == "NETWORK_UNAVAILABLE"` (or offline==false observed) → `offline=true` and the
banner per `text.md` §13; "Retry" re-issues the last fetch. Mutations fail with the offline
copy and preserve form state.

Verify with test `OfflineBehaviorTest` (fake ConnectivityObserver + fake repos): dashboard load
failing with `NETWORK_UNAVAILABLE` keeps prior data, sets `offline=true`, banner composable
shows; retry after going online refetches; register submit while offline sets the mutation error
copy and keeps fields.

## Step 15 — Compose UI test suite and final sweep

Complete the Compose tests listed in steps 5–13 if not already done; add `ParentFlowUiTest`:
welcome → register (validation errors) → register success → verify (dev code path) → login 401
message → login success → dashboard renders → create goal → toggle a setting → logout returns to
login. Run `./gradlew :app:test` and `./gradlew :app:connectedDebugAndroidTest` (or the project's
standard test tasks from phase-02) — all green. Grep for forbidden calls: no ViewModel may import
`AuthApi`/`ParentApi` directly (repository only), no screen may construct a session, no code
calls a path outside `text.md` §3. Record the gap log entries (#3, #6, #7) in
`expected-output.md`.
