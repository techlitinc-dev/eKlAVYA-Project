# Phase 13 — Reference (text.md)

Backend facts cited here come from phase-01 (`documentation/phase-01-repository-analysis-endpoint-inventory/text.md`,
§ references given) and from the files it cites. Client facts come from the phases named.

---

## 1. Security hardening checklist

### 1.1 Token handling (Android)

| # | Requirement | Basis |
|---|---|---|
| T1 | Access + refresh tokens are encrypted at rest with a key stored in **Android Keystore** (never plain SharedPreferences/files) | phase-04 fixed decision; secrets at rest |
| T2 | Parent and child tokens live in **separate stores** keyed by role; only the active role's token is attached by `AuthInterceptor` | §1.2 below |
| T3 | Token lifetimes are treated as server truth: access 24 h, refresh 30 d (hardcoded backend-side, `token_service.py:34-35`); the app never hardcodes expiry assumptions for validation, only for scheduling refresh | phase-01 §6.2 |
| T4 | 401 handling: one refresh attempt via `POST /api/auth/token/refresh` (parent) or `POST /api/auth/token/refresh/child` (child, phase-01 §6.3); a second 401 logs the role out locally | phase-04 |
| T5 | Tokens never appear in logs, crash reports, analytics, or UI (see LogSanitizer §1.3) | gap #1 hygiene |
| T6 | Web: token in `localStorage["eklavya_token"]` is the phase-04 convention (documented XSS trade-off of localStorage vs httpOnly cookies; backend sets no cookies, so localStorage is the only vehicle — accepted for this build, flagged for a future hardening pass) | phase-04 |

### 1.2 Session separation guarantees

Facts (phase-01 §6, §7.H): parent JWT claims carry `parent_id`; child JWT carries `child_id` and
a duplicate `student_id` of the **same value**; the two roles use disjoint endpoints. The app
must guarantee:

- S1. Parent session and child session are **separate DataStore entries** (distinct file names /
  preferences keys per role). One entry per role, never a combined store.
- S2. Child logout (`POST /api/auth/logout/child` + local clear) removes **only** the child
    entry; the parent session remains fully usable without re-login, and vice versa.
- S3. Switching role (parent → child or back) never overwrites the other role's token before the
  new login succeeds.
- S4. Every request is scoped to ids from that role's own session (child calls use the child's
  `student_id`; parent calls use the child id obtained from the parent's own profile/data) —
  the client-side scoping that compensates for backend gap #7 today.
- S5. Automated isolation test exists and passes (§3.4, critical test #5): login parent → login
  child → assert both entries present → child logout → assert parent entry intact and child
  entry gone → parent dashboard loads offline-of-credentials.

### 1.3 LogSanitizer rule (binding)

One logging rule for both clients:

> **All** log output passes through `LogSanitizer.sanitize(message)` (Android:
> `core/logging/LogSanitizer.kt`; web: `src/lib/logSanitizer.ts`). Raw `Log.d/i/w/e` and
> `console.*` call sites are forbidden in application code; lint/CI greps for them.

The sanitizer must redact, at minimum:

- JWTs: pattern `eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+` → `[REDACTED_JWT]`
- Key/value pairs whose key matches `(?i)(password|pass|otp|token|authorization|secret|api[_-]?key|credential)` → value replaced with `[REDACTED]`
- Email and phone in non-auth flows → keep (needed for support), but never alongside a token in
  the same line.

Reason: gap #1 (child passwords are plaintext server-side, `child_service.py:172`) makes any
credential-bearing log line a full credential leak; gap #9 (password check silently skipped
without `FIREBASE_API_KEY`, `login_service.py:215-252`) means login request logging could
capture parent passwords.

### 1.4 Authorization assumptions — exact backend checks required before production

Today these are **assumptions the clients rely on but cannot observe**: with `TESTING_MODE=true`
(default) the testing bypass returns the constant `"test_parent_123"` and ignores the
Authorization header (`middleware/testing_auth.py:20-42`, phase-01 §6.1); analytics declares no
auth; the superadmin router declares no auth dependency (phase-01 §11 gaps #7, #8). Before
production the backend **must** enforce, and the clients must then receive 401/403 exactly as
listed:

| Family | Required server-side check (gap #7 unless noted) |
|---|---|
| `/api/onboarding/*` (child, exam) | JWT verified; `parent_id` taken from the token, not the query string; for child-scoped reads/writes the target child's `parent_id` must equal the caller's `parent_id` (parent-owns-child). `?parent_id=` query auth replaced. |
| `/api/parent/*` | JWT verified; caller is a parent token; `child_id` path/query targets must belong to the caller (`parent_dashboard_router.py` today: bypass, no ownership check). |
| `/api/diagnostic-test/*` | JWT verified; student token may reach only tests whose `child_id` matches the token's `child_id`/`student_id`; parent token may read their own child's tests; submit may only transition that student's own in-progress attempt (also fixes duplicate-submit enforcement, gap #4). |
| `/api/analytics/*` | JWT verified; `generate`/`student/*` scoped to parent-owns-child or the student themself; reports of other students' ids return 404 (phase-01 §4: "404 also used to hide other users' private records"). |
| `/api/schedule/*` | JWT verified; `student_id` in `ScheduleRequest` must be the caller's child (parent) or the caller (student); regenerate/update/delete restricted to the owner. |
| `/api/superadmin/*` (all 16) | JWT verified **and** the token must be a superadmin token (gap #8). The hermes router's existing role split (`resolve_child_access`, phase-01 §9.5 hermes rows: parent tokens 403 on `/api/hermes/chat`, student tokens 403 on `/api/hermes/parent/*`) is the in-repo precedent for the required check. |
| Superadmin login | Password hash verified before token issuance (gap #8, `superadmin_router.py:413-421`); fail closed. |
| Parent email login | Fail closed when `FIREBASE_API_KEY` is absent (gap #9, `login_service.py:215-252`). |

Client obligations once enforcement lands: map 401 → re-auth/logout; map 403 →
`PermissionDeniedState`/screen-level denial; never retry a 403 with token refresh.

### 1.5 Secrets handling

- Server secrets (`JWT_SECRET`/`JWT_SECRET_KEY`, `GOOGLE_API_KEY`, `FIREBASE_CREDENTIALS_PATH`,
  `RAZORPAY_*`, `SMTP_*`) live only in `Backend/.env` (created by `install.sh` from
  `.env.example`), never in VCS, never in client code, never in logs (§1.3).
- Android: no server secret in the APK. The Firebase client `apiKey` in `google-services.json`
  is a client identifier, not a secret — still keep the file out of public repos per policy.
- Web: no secrets in `Frontend_Website/`; only `VITE_API_BASE_URL` (public by design).
- Child credentials: created once at profile creation (phase-01 §7.B); the app shows them once
  (phase-06), never stores them beyond the child's own login session, never logs them (gap #1
  makes client-side hygiene load-bearing).
- `.env.example` dead keys (`JWT_*_EXPIRE_*`, `CORS_ORIGINS`, phase-01 §11 gap #12) are a backend
  cleanup item; noted for completeness.

### 1.6 Cert pinning recommendation (release builds)

Recommend (not gate): OkHttp `CertificatePinner` pinning the API host's leaf/SPKI pins in the
`release` flavor; debug builds skip pinning so MockWebserver integration tests run. Rotation
plan: ship ≥2 pins (current + next). This mitigates MITM credential/token capture given tokens
travel as Bearer headers on every call.

### 1.7 Superadmin panel security (phase-12 verification points)

- P-S1. `LatexRenderer` sanitizes via DOMPurify (HTML profile) before `dangerouslySetInnerHTML`
  (previously unsanitized at `Frontend_Website/src/components/LatexRenderer.tsx:61-62`) — CMS
  content is attacker-controlled input.
- P-S2. No-secret-display rule: passwords, tokens, JWT payloads, Firebase values never rendered;
  the `/users` response has no password fields today, and the panel filters defensively anyway.
- P-S3. `SuperadminSecurityNotice` on every superadmin screen (phase-12 text.md §8 copy).
- P-S4. Local audit trail (`eklavya_superadmin_audit`) contains actor/action/target only — no
  secrets; capped at 500 entries.
- P-S5. Typed confirmation for destructive-ish actions (revoke premium, trigger wall, deletes).
- P-S6. Honest blocked states for gap #8 monitoring pages — no fabricated data.

### 1.8 Known backend security gaps (phase-01 §11) — client exposure summary

| Gap | Severity for clients | Client posture |
|---|---|---|
| #1 child plaintext passwords | High | Never log/display credentials; LogSanitizer §1.3; show-once UX (phase-06) |
| #2 no child credential reset | Medium | Disabled control + tooltip (phase-12) |
| #3 no parent password reset | Medium | Documented; no forgot-password UI ships claiming otherwise |
| #4 mock test lifecycle | High (integrity) | Submission duplicate-guard coded per contract; blocked steps marked in E2E |
| #7 no authorization enforcement | Critical pre-prod | Client-side scoping S4; §1.4 lists required checks |
| #8 superadmin unauthenticated + no password check | Critical pre-prod | Banner P-S3; token still sent; §1.4 lists required checks |
| #9 silent password-check skip | High | Backend fail-closed required; client shows generic login failure |

### 1.9 Input-validation recap (per phase, client-side enforcement)

| Phase | Surface | Rules enforced client-side (server truth in phase-01) |
|---|---|---|
| P04/P05 | Parent registration | name 2–100; email format; password ≥8 with ≥1 letter + ≥1 digit; repeat match; phone `^\+91[6-9]\d{9}$` (phase-01 §7.A) |
| P05 | OTP entry | 6-digit; 10-min window messaging; single-use messaging |
| P06 | Child profile | name 2–100; age 14–19; grade 9–12; `current_level` enum; username 3–30 `^[a-zA-Z0-9_@.]+$`; password 8–50 with ≥1 letter + ≥1 digit (phase-01 §7.B) |
| P08 | Exam selection | `subject_preferences` exactly {Physics, Chemistry, Mathematics} (JEE*) or {…Biology} (NEET), sum exactly 100; future `exam_date` (phase-01 §7.C) |
| P09 | Test runner | answers constrained to A–D / empty / numeric; `time_taken ≥ 0`; timer-driven autosubmit; resubmit guard (contract §3.3) |
| P11 | Schedule request | `daily_study_hours` 2–8; future `exam_date`; `analytics_id` present (phase-01 §7.F) |
| P12 | PYQ editor | `statementHtml`/`solutionHtml` required; MCQ 4 options + correctOption A–D; NAT numeric answer + positive tolerance (phase-12 text.md §2.5) |

---

## 2. Test strategy

### 2.1 Unit tests (Android)

- ViewModels: every ViewModel from phases 04–11 — initial state, loading, success, error,
  retry; state exposed via immutable UI state / StateFlow.
- Validators: each rule row of §1.9 as a parameterized test (valid + each invalid branch).
- Repositories with fakes: each repository interface gets a `Fake*` implementation for
  ViewModel tests (e.g. `FakeAuthRepository`, `FakeChildRepository`, `FakeTestRepository`,
  `FakeAnalyticsRepository`, `FakeScheduleRepository`, `FakeParentDashboardRepository`) with
  scripted success/failure; the fakes also record call arguments for scoping assertions (which
  ids were requested — feeds S4).
- LogSanitizer: redaction tests (JWT pattern, password/otp/token keys, passthrough of benign
  lines).

### 2.2 Integration tests (MockWebserver)

One MockWebserver test class per endpoint contract consumed (59 android + 16 superadmin-class
web calls are HTTP-level identical in shape): enqueue the canonical success JSON (phase-01 §8),
assert the request path/headers (Bearer injected; query params), assert the parsed model.

### 2.3 Error-envelope matrix (must be tested for every client call family)

| Envelope | Example source | Required client behavior |
|---|---|---|
| 401 `{"detail": ...}` | wrong child credentials (`login_router.py:719` region) | clear form error; no token stored |
| 404 `{"detail": ...}` | unknown ids; also hides other users' data (phase-01 §4) | "not found" empty state, no retry storm |
| 400/422 `{"detail": ...}` | validation (`ChildProfileRequest`, exam sum≠100) | field-level errors where mappable |
| 500 catch-all `{"success": false, ...}` | global handler (`main.py:169`) | generic error + retry |
| v1 envelope `{"error": {"code", ...}}` | not consumed by these clients | parser exists but unused (documented) |
| Network failure / timeout | — | offline error state; queued resubmit only where the phase spec allows |

### 2.4 Compose UI tests (per screen; the five critical ones starred)

Registration & onboarding (P05/P06): form validation errors; OTP entry; child-profile create
success showing credentials once. Child login (P07): *child login wrong-credentials → error
shown, no navigation*. Child dashboard (P07): assigned test visible (mocked list). Test
scheduling (P08): subject weights sum enforcement; schedule success shows `diagnostic_test_id`.
Test runner (P09): *timer expiry triggers autosubmit*; palette navigation; answer persistence
across recompositions. Submission (P09): *duplicate-guard — second submit tap is a no-op while
in-flight / after success*. Results (P10): report rendering with mocked `AnalyticsReport`.
Schedule (P11): day list, progress update, regenerate. Parent screens (P05): dashboard, weekly
report, goals. *Session isolation (P04/P07): the S5 procedure as an instrumented test*.
Web (phase-12, vitest + Testing Library, §2.6).

### 2.5 Coverage targets and commands

- Gate: **line coverage ≥ 70%** on `data/` (repositories, DTO mappers, validators) **and** on
  ViewModels. Report: JaCoCo (`./gradlew jacocoTestReport`); the gate fails CI below target.
- Commands: unit + integration `./gradlew test`; device tests
  `./gradlew connectedDebugAndroidTest`; all together as documented in phase-02:
  `./gradlew test connectedDebugAndroidTest`.

### 2.6 Web tests for the superadmin panel

`Frontend_Website/package.json` ships no test runner — add dev dependencies first:
`npm i -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`
and script `"test": "vitest run"` with a jsdom environment. Suites:

1. `LatexRenderer.test.tsx` — renders LaTeX; strips `<img onerror>` (assert no `onerror` attr).
2. `RequireSuperadmin.test.tsx` — non-superadmin session renders `PermissionDeniedState`.
3. `UsersActionDialog.test.tsx` — typed confirmation gates Confirm; award_xp validates positive int.
4. `MonitoringPages.test.tsx` — all four pages render `BACKEND CHANGE REQUIRED` notice and make
   **zero** `api` calls (mock the axios instance and assert not called).
5. `Login.test.tsx` — 401 path shows server `detail`; success stores session and navigates.
6. `DataTable.a11y.test.tsx` — arrow-key movement moves `aria-activedescendant`; sort buttons
   toggle `aria-sort`.
7. `localAudit.test.tsx` — mutation appends entry with actor/action/target.

---

## 3. End-to-end verification (14-step required workflow)

Preconditions: backend running (`./run.sh backend`); Android app installed on an emulator or the
web SPA used where the Android step is equivalent (state which); superadmin panel reachable.
Identities: fresh parent for steps 1–2; demo identities (phase-01 §12) allowed for the rest.

### 3.1 The demo script (numbered)

1. **Parent registers (simple) → verify email → login.** Register via
   `POST /api/auth/register/simple`; verify email via `/verify/email/send` + `/confirm`; log in
   via `POST /api/auth/login/email`. Note for the demo: in dev the send endpoint returns the
   code in the response body (`verification_router.py:43` region) — email delivery is
   dev-stubbed; state this when demoing.
2. **Create child profile (credentials shown once).** `POST /api/onboarding/child?parent_id=…`;
   UI shows username/password once (phase-06), then never again.
3. **Child account exists via the backend account-creation flow.** State plainly: profile
   creation created the Firebase Auth user (`{username}@mentor-ai.local`) and the Firestore
   `children` doc — i.e. the child can log in immediately (phase-01 §7.B). Prove it:
   `POST /api/auth/login/child` with the new credentials → 200 `is_student: true`.
4. **Parent schedules a test.** `POST /api/onboarding/exam/select?parent_id=…&child_id=…` with
   weights summing to 100 → `diagnostic_test_id` in the response; the Firestore
   `diagnostic_tests` doc is written with status `"scheduled"` (phase-01 §7.C).
5. **Child logs in on the child login screen** with their own username/password → child session
   stored in the child DataStore entry (S1–S3).
6. **Child sees the assigned test.** `GET /api/diagnostic-test/student/{student_id}` lists it
   (today a canned list — gap #4; if the scheduled test is absent from the mock list, verify via
   `GET /api/diagnostic-test/{test_id}/metadata` and record the deviation).
7. **Child opens the eligible test, reads instructions, completes, submits.** Flow:
   `GET /{test_id}` (questions) → `POST /{test_id}/start` → `POST /{test_id}/submit` with
   `TestSubmission` (`answers` map, `time_taken`, `submission_time`) → `TestResults`.
   **Known blocker: `GET /api/diagnostic-test/{test_id}` returns 501 Not Implemented
   (`diagnostic_test_router.py:508`, gap #4). This step is blocked on the default backend. Run
   it only in a backend-fixed environment; otherwise mark BLOCKED (gap #4) and continue.**
8. **Backend processes the submission.** Expected: submission persisted (`test_submissions`),
   status transitions to `completed`. **Blocked on default backend: Firestore writes are
   commented out (`test_management_router.py:272-300`) and scoring is random — gap #4; verify
   only in a backend-fixed run.**
9. **AI analysis trigger + poll.** `POST /api/analytics/generate` → 202 `{status: "pending"}`;
   poll `GET /api/analytics/{analytics_id}` until `status: "completed"` with a full
   `AnalyticsReport` (phase-01 §7.E; today the pipeline completes synchronously, so the first
   poll already shows `completed` — gap #5 note; contract-safe).
10. **Personalized schedule generation.** `POST /api/schedule/generate`
    `{student_id, analytics_id, exam_type, exam_date, daily_study_hours}` → 201 `Schedule`.
    **Known blocker: `schedule_service.py:84-85` reads collections `analytics`/`students` while
    writers store `analytics_reports`/`children` — real generation 404s (gap #6). Verify only in
    a backend-fixed run; otherwise mark BLOCKED (gap #6).**
11. **Child views results + schedule.** `GET /api/analytics/student/{student_id}`,
    `GET /api/analytics/{analytics_id}`, `GET /api/schedule/student/{student_id}`,
    `GET /api/schedule/{schedule_id}` (and `/progress/today`) render in the child app.
12. **Parent views child status/analysis/schedule.** `GET /api/parent/dashboard/{child_id}`,
    `GET /api/parent/reports/weekly/{child_id}`, plus the analytics/schedule reads of step 11.
    Note: the dashboard service also reads the mismatched `analytics` collection (gap #6) — the
    app must render missing `recent_test_score` defensively.
13. **Session separation checks.** Today (gap #7): verify client-side scoping — separate
    DataStore entries; child logout preserves the parent session (S2/S5); parent and child UIs
    are unreachable across roles. Once gap #7 lands: child token against
    `GET /api/parent/dashboard/{child_id}` must return **403**; parent token against child-only
    endpoints likewise; record which mode the run used.
14. **Superadmin monitors.** Log in at the panel (banner visible — password not verified, gap
    #8); `GET /api/superadmin/users` + `/overview` show live parent/child data; the four
    Workflow Monitoring pages show `BlockingNotice` (gap #8 — tests/submissions/analytics/
    schedules endpoints PROPOSED, not implemented). Execute a read-only action (e.g. Award XP) to
    demonstrate the audit trail.

### 3.2 Verification matrix

| # | Step | Endpoint(s) | Expected result | Pass criteria | Known blockers |
|---|---|---|---|---|---|
| 1 | Parent register → verify → login | POST /api/auth/register/simple; /verify/email/send; /verify/email/confirm; POST /api/auth/login/email | 201 `AuthResponse` (no token); code confirmed; 200 `LoginResponse` with `token`, `expires_in: 86400` | parent_id present; token stored in parent entry; login succeeds with the new account | Email delivery dev-stubbed (code in response) |
| 2 | Create child profile | POST /api/onboarding/child?parent_id= | 201 `ChildProfileResponse` | child_id returned; credentials rendered once; one-child-per-parent rule surfaces as form error on repeat | gap #1 (plaintext server-side; client never logs) |
| 3 | Child account exists & can log in | POST /api/auth/login/child | 200 `LoginResponse` `is_student: true`, `student_id == child_id` | immediate login with creation credentials | none for the flow itself |
| 4 | Parent schedules test | POST /api/onboarding/exam/select | 200 `ExamSelectionResponse` with `diagnostic_test_id` | non-empty diagnostic_test_id; sum≠100 rejected with field error | status string `"scheduled"` is not a `TestStatus` member (gap #4) — client must tolerate unknown statuses |
| 5 | Child login (child screen) | POST /api/auth/login/child | 200 child session | child token in child DataStore entry only (S1) | none |
| 6 | Child sees assigned test | GET /api/diagnostic-test/student/{id} (fallback /metadata) | 200 list/metadata | scheduled test identifiable | Mock list (gap #4) may omit it — record deviation |
| 7 | Open/complete/submit test | GET /{test_id}; POST /start; POST /submit | 200 `TestResults` shape | submission accepted once; duplicate tap no-op | **BLOCKED on default backend: GET /{test_id} → 501 (gap #4). Backend-fixed run only.** |
| 8 | Backend processes submission | POST /submit persistence | submission doc + status `completed` | second submit rejected/idem-potent | **BLOCKED by default: persistence commented out, random scoring (gap #4). Backend-fixed run only.** |
| 9 | AI analysis trigger + poll | POST /api/analytics/generate; GET /api/analytics/{id} | 202 pending → poll completed `AnalyticsReport` | report has overview, subject_analysis, priority_topics | Synchronous backend (gap #5) — first poll already completed; contract-safe |
| 10 | Schedule generation | POST /api/schedule/generate | 201 `Schedule` | schedule_id, days length == total_days | **BLOCKED by default: collection mismatch 404s real runs (gap #6). Backend-fixed run only.** |
| 11 | Child views results + schedule | GET /api/analytics/student/{id}; /{id}; GET /api/schedule/student/{id}; /{id} | 200 report + schedule | both render in child UI | depends on 9/10 success mode |
| 12 | Parent views status/analysis/schedule | GET /api/parent/dashboard/{child_id}; /reports/weekly/{child_id}; analytics/schedule reads | 200 dashboard + report | KPIs render; missing fields degrade gracefully | gap #6 (`analytics` read) may hide recent_test_score |
| 13 | Session separation | client storage; cross-role call probes | separate entries; child logout keeps parent | S5 instrumented test green; today: client-side scoping verified. Post-gap-#7: 403 on cross-role calls | gap #7 — no server-side 403 observable today |
| 14 | Superadmin monitoring | POST /api/superadmin/login; GET /users; /overview; monitoring pages | users + KPIs live; 4 pages show BlockingNotice | banner visible; users table live; zero monitoring fetches | gap #8 (login unverified; no monitoring endpoints) |

---

## 4. Traceability re-check

### 4.1 Endpoint → phase mapping (reproduced from phase-01 §10)

| Router group | Endpoints | Consumer | Integrated in | Check |
|---|---|---|---|---|
| auth, simple_register, login, verification | 18 | android | P04–P07 (auth/session P04; registration+login+verify P05; child login P07) | exactly one home per endpoint |
| child (onboarding) | 4 | android | P06 | — |
| exam (onboarding) | 5 | android | P08 | — |
| diagnostic_test (10 used) | 10 of 13 | android | P07 (student list), P08 (reserved generation), P09 (taking/submission/results) | unused rows (delete/health/schedule-mock) accounted in phase-01 §10 |
| analytics | 6 | android | P10 | — |
| schedule (9 used) | 9 of 10 | android | P11 | DELETE classified internal in phase-01 §10 |
| parent_dashboard (7 used) | 7 of 8 | android | P05 | email-schedule classified web in phase-01 §10 |
| superadmin | 16 | superadmin | P12 | demo-session classified internal, consumed only by existing switcher |

Confirmation statements: (a) every android-classified endpoint group appears in exactly one
phase row set above, matching phase-01 §10's "Consumed" dispositions; (b) the superadmin group
(16) is consumed by phase 12 only; (c) no endpoint is consumed by two phases; (d) everything
classified web/internal/unused in phase-01 §10 stays out of the Android app and panel.

### 4.2 Phase screen → test coverage matrix

| Phase | Screens | Covering tests |
|---|---|---|
| P04 | Session restore, logout | unit: AuthViewModel; integration: refresh/logout contracts; instrumented: session isolation (critical #5) |
| P05 | Registration, email verify, parent login, dashboard, weekly report, goals, settings | unit: RegistrationValidators, ParentDashboardViewModel; Compose: form validation, OTP; integration: auth + parent endpoints |
| P06 | Child profile create/manage | unit: ChildProfileValidators; Compose: create-success shows credentials once; integration: child CRUD |
| P07 | Child login, child dashboard, child logout | Compose: *wrong-credentials* (critical #2); dashboard assigned-test; instrumented isolation |
| P08 | Test scheduling (exam select) | unit: ExamSelectionValidators (sum=100); Compose: scheduling success; integration: exam/select |
| P09 | Test runner, submission, results | Compose: *timer autosubmit* (critical #3), *duplicate-guard* (critical #4); integration: start/submit/results incl. 404/422 |
| P10 | AI analysis trigger, polling, results detail | unit: AnalyticsViewModel poll states; Compose: report render; integration: generate/poll/get contracts |
| P11 | Schedule view/adjust/progress/today | unit: ScheduleValidators; Compose: day list + progress; integration: generate/get/regenerate (error envelope for gap #6) |
| P12 (web) | Login, dashboard, users, questions, content, assessments, ai-settings, 4 monitoring pages | vitest suites §2.6 (1–7) |
