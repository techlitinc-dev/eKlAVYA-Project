# Phase 05 — Expected Output & Sign-off

## Deliverables of this phase

1. `ParentApi` + DTOs covering every endpoint in `text.md` §3 (register simple + 3 alternates,
   verification ×4, onboarding status, onboarding child, dashboard, weekly report, goals ×3,
   notification settings ×2) with byte-exact JSON field names.
2. `ParentRepository` returning `ApiResult`; send-code results expose the dev `code`/`otp` as an
   explicit `devCode` field, never a raw `JsonObject`.
3. Screens with ViewModel + UiState + exhaustive events per `text.md` §7: Welcome, ParentRegister,
   VerifyEmail, VerifyPhone, ParentLogin, ForgotPassword (placeholder, no network),
   ParentDashboard, WeeklyReport, Goals, Settings, ParentResults (placeholder).
4. `ParentNavGraph` with the exact routes in `text.md` §6; `ParentSessionRestorer` implementing
   the `text.md` §8 restore tree; session-restore auto-attempt on app start (valid parent session
   → skip straight to dashboard; restore failure → login/welcome; offline → gate with retry).
5. Validation per `text.md` §5 (email regex, password ≥8 with letter+digit, phone
   `^\+91[6-9]\d{9}$`, repeat-password match, OTP/code formats, goal target > 0).
6. Offline contract per `text.md` §13 (cached-last + retry banner on data screens; mutation
   failures keep form state; no queuing).
7. Error strings follow the `text.md` §4 mapping exactly.

## Verification checklist

- [ ] `./gradlew :app:test` and the Compose UI test tasks pass: `ParentDtoSerializationTest`,
      `ParentRepositoryTest`, `ParentValidatorsTest`, `ParentNavGraphTest`,
      `ParentRegisterViewModelTest`, `ParentRegisterScreenTest`, `VerifyViewModelTest`,
      `VerifyScreenTest`, `ParentLoginViewModelTest`, `ParentLoginScreenTest`,
      `ForgotPasswordScreenTest`, `ParentSessionRestorerTest`, `ParentDashboardViewModelTest`,
      `ParentDashboardScreenTest`, `WeeklyReportViewModelTest`, `WeeklyReportScreenTest`,
      `GoalsViewModelTest`, `GoalsScreenTest`, `ParentSettingsViewModelTest`,
      `ParentSettingsScreenTest`, `ParentResultsScreenTest`, `OfflineBehaviorTest`,
      `ParentFlowUiTest`.
- [ ] Register success shows "Registration successful" and routes to VerifyEmail (simple path,
      `verification_required:false` per `text.md` §3.1); duplicate email shows the backend
      `detail` verbatim; **no token is stored at registration** (assert `SessionManager` slots
      empty after register).
- [ ] Verify screens auto-send on entry, honor the 60 s resend cooldown, show the DEV code banner
      only in debug builds, and map 400/404 per §4.
- [ ] Login: wrong password → "Incorrect email or password."; success → dashboard; session
      restore on cold start skips login when a valid parent session exists (restore = GET
      `/api/auth/me` per `text.md` §8).
- [ ] Dashboard renders child name, status pill, stats, weak areas, upcoming tasks, recent test
      score; empty/null fields render the documented empty states (gap #6 — never an error).
- [ ] Goals: create (201, `status:"active"`), list (newest first), edit/status change
      (`completed_at` stamped server-side); PUT 404 handled per §4.
- [ ] Settings: 9 toggles load (defaults when no doc) and PUT optimistically with debounce;
      profile survives doc-key variance (`email_address`/`mobile_number` fallbacks); logout
      clears the session and returns to `parent_login` even on network failure.
- [ ] Interceptor unchanged from phase-04: all `ParentApi` calls carry the parent Bearer token;
      child slot untouched.
- [ ] Forgot-password screen performs **zero** network calls (asserted by a throwing fake).
- [ ] Gap log below is complete and cross-references phase-01 §11.

## Manual demo script (against the dev backend)

Preconditions: backend running (`./run.sh backend`); app pointing at
`http://10.0.2.2:8000`; use a fresh email.

1. **Welcome** → tap "I'm a Parent" → ParentRegister opens.
2. **Register** — submit empty form → field errors (name/email/password rules). Fill
   `Test Parent`, `t<timestamp>@example.com`, `+919876543210`, `Passw0rd1`/`Passw0rd1` → submit →
   "Registration successful" → routed to VerifyEmail; DEV banner shows the 6-char code.
3. **Verify** — enter the code → "Email verified successfully" → routed to ParentLogin.
   Resend cooldown ticks 60→0.
4. **Login** — wrong password first: "Incorrect email or password." Then correct → dashboard.
   Cold-start the app: session restored, lands on dashboard without logging in again.
5. **Dashboard** — shows the registered email's child state (no child yet → setup banner +
   "Set up" CTA; with a child seeded, shows cards). "Schedule a test" and "View results" navigate
   (results = placeholder).
6. **Goal** — Goals → New goal → type `target_score`, target `85` → save → appears as
   "0.0 / 85", status `active`. Edit → mark `completed`.
7. **Settings** — toggles flip and persist (re-enter screen: values held); profile shows
   name/email; "Switch to child mode" routes to child login (phase-07).
8. **Logout** — confirm → session cleared → back at ParentLogin; cold start now lands on
   Welcome/Login.

## Gap log (backend facts encoded; nothing silently worked around)

| Gap | Phase-01 ref | Evidence | Client stance |
|---|---|---|---|
| #3 No forgot-password flow | §11 #3 | `verification_service.py` has only 4 functions; no reset endpoints | Screen spec'd + gated ("not available yet"); zero network calls; proposed Firebase-backed contract documented in `text.md` §12 as proposal-only |
| #6 `analytics` vs `analytics_reports` read mismatch | §11 #6 | `parent_dashboard_service.py:68-77` reads `analytics`; `analytics_service.py:624-635` writes `analytics_reports` | Dashboard/weekly empty states are first-class; client never fabricates weak areas or scores |
| #7 No ownership enforcement | §11 #7 | `middleware/testing_auth.py:20-42`; `parent_dashboard_router.py:48-52` takes any `child_id` | App only calls with ids from its own login; Bearer always sent |
| #9 Silent password-check skip (dev-backend risk) | §11 #9 | `login_service.py:215-252` | Recorded for testers; not an app defect |

Resolved — documentation drift found while verifying phase-01 §8: the canonical example for
`POST /api/auth/register/simple` originally showed `"phone":null`, but the service returns
`"phone": "<mobile_number>"` when supplied (`simple_register_service.py:79-85`). **Phase-01 §8
was corrected on 2026-11-02**; this phase's `text.md` §3.1 already stated the service behavior
as authority.

## Sign-off rule

Phase 06 may start only when every box above is checked. Any mismatch between this documentation
and the running backend at commit `d8ab491` is a documentation bug: fix the doc and record the
drift in this gap log; if the drift is a genuine backend defect, append it to phase-01 §11
instead of working around it.
