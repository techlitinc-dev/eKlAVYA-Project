# Phase 07 — Instructions

Sequential implementation steps. Stack fixed by phases 02/04: Compose + Hilt + Retrofit +
Navigation Compose; package `ai.eklavya.app`; base URL `BuildConfig.EKLAVYA_BASE_URL`.

Prereqs: phases 02–06 complete. A parent has created a child (phase-06) so real
credentials exist for testing.

## Step 1 — Child auth API layer

1. `feature/childauth/api/ChildAuthDtos.kt` mirroring `text.md` §2.1/§2.2/§3/§4:
   `ChildLoginRequest(username, password)`; `LoginResponse` with all fields the child
   login returns — note `phone: String?` exists in the shared model
   (`Backend/models/login_models.py:321-324`) and is null for children; `TokenResponse`;
   `LogoutResponse`.
2. `feature/childauth/api/ChildAuthApi.kt`:
   - `@POST("api/auth/login/child")` body `ChildLoginRequest` → `LoginResponse`.
   - `@POST("api/auth/token/refresh/child")` body `{refresh_token}` → `TokenResponse`.
   - `@POST("api/auth/logout/child")` with child Bearer header → `LogoutResponse`.
   - `@GET("api/auth/me/child")` with child Bearer header → `Map<String, Any>` (or a DTO
     of the fields in `text.md` §4).
3. Wire child auth calls to a **child** Retrofit/okhttp path whose interceptor reads the
   child token from `SessionManager` (phase-04). If phase-04 exposes one interceptor
   driven by a session type, add the child branch; do not reuse the parent interceptor
   statefully.

## Step 2 — Child session write path

Using the phase-04 `SessionManager` child-session API, persist on C1 success:
access token, refresh token, `child_id` (= `student_id`), `username`, `name`,
`parent_id` (reference only), `is_student`, `expires_in`. Rules:
- Only the child session slot is written. Never read or write the parent session here.
- No credential or token logging (gap #1 hygiene).

## Step 3 — ChildLogin screen

1. Build `ChildLoginScreen` + ViewModel per `text.md` §10.1. Local validation mirrors
   `text.md` §2.1 (username 3–30 `^[a-zA-Z0-9_@.]+$`, password 8–50 letter+digit) as
   convenience hints only.
2. Map errors exactly: 401 → one generic message "Incorrect username or password"
   (never per-field, never "user not found" — `text.md` §2.3); 422 → local validation
   banner; IOException → offline state with retry; 500 → server-failure state with retry.
3. On success: save session (Step 2), then check `is_student == true` → navigate to
   `child_dashboard`; else error state (unexpected).
4. Loading state disables inputs; back returns to role-pick.

## Step 4 — ChildHome API layer

1. `feature/childhome/api/ChildHomeDtos.kt`: `TestMetadata` mirror with **lenient enum
   parsing** — `status` accepts `pending|in_progress|completed|expired|cancelled|scheduled`
   (`scheduled` tolerated, gap #4; `text.md` §5); `exam_type` accepts
   `JEE_MAIN|JEE_ADVANCED|NEET` and parses unknown values without crashing (gap #4).
2. `feature/childhome/api/ChildHomeApi.kt`:
   - `@GET("api/diagnostic-test/student/{student_id}")` with `@Path student_id`,
     `@Query status?/limit(10)/offset(0)` → `List<TestMetadata>`.
   - `@GET("api/analytics/student/{student_id}")` with `@Query limit(10)/offset(0)` →
     JsonArray (presence only).
   - `@GET("api/schedule/student/{student_id}")` with `@Query("status_filter") "active"` →
     nullable `Schedule` summary DTO (parse defensively; only fields used this phase are
     `schedule_id`, `exam_type`, `exam_date`, `total_days`, `status` — presence only).
3. Every call uses `student_id` = child session `child_id` and the child Bearer header.

## Step 5 — ChildDashboard screen

1. Greeting from session name (fallback username).
2. Load C5, C6, C7 in parallel on entry and pull-to-refresh. Section-level error
   handling; full-page error only when C5 fails (`text.md` §10.2 data policy).
3. "My Tests": split per `text.md` §10.2 into Upcoming (`pending`, `scheduled`,
   `in_progress`) and Completed (`completed`); render `expired`/`cancelled` as
   non-tappable rows. Implement `StatusPill` (icon + label, never color alone) with the
   mapping in `text.md` §10.2.
4. Taps: eligible upcoming test → `child_test_instructions(test_id)`; completed test →
   `child_results(test_id)`. Destinations are stubs until phases 09/10 — register the
   routes now per §6 below.
5. AI-processing card: visible when C6 is non-empty and the newest analysis is not yet
   viewable (until phase-10, showing it whenever C6 returned data for a test whose
   results screen lacks a report is acceptable); CTA → `child_results`.
6. "My Schedule" card per `text.md` §10.2 item 4; CTA → `child_schedule` (phase-11 stub).
7. Logout menu: call C3 best-effort (ignore network failure), clear **only** the child
   session, navigate to role-pick. Verify parent session untouched.

## Step 6 — ChildNavGraph

Create `navigation/ChildNavGraph.kt` implementing the §8 contract: routes
`child_login`, `child_dashboard`, `child_test_instructions(test_id)`,
`child_test_runner(test_id)`, `child_submission_status(test_id)`, `child_results(test_id)`,
`child_schedule`. Start-destination rule: valid child session → `child_dashboard`;
otherwise `child_login`. Register the phase-09/10/11 destinations as stub composables now
and mark them with their owner phase. Do not add any parent/superadmin route to this
graph, and do not add a `child_id` navigation argument anywhere.

## Step 7 — Token refresh handling

On a 401 from C5–C7 with the child token: attempt C2 once with the child refresh token;
on success retry the original call; on failure clear the child session and navigate to
`child_login` (never to parent login). Parent tokens are not involved at any point.

## Guardrails

- Do not invent endpoints. Only C1–C7 in `text.md` §1.
- Do not call `GET /api/diagnostic-test/{test_id}` or any start/submit/results endpoint —
  those are phase-09 and are 501/mocks today.
- Do not distinguish unknown-username from wrong-password in any UI or log output.
- Do not put a child selector, sibling list, or any cross-child navigation in child mode.
- Do not call `POST /api/diagnostic-test/schedule` (unused mock) for any reason.
- Tolerate C5 failure (500 today) with an empty/error state — never crash (gaps #4, #7).

## Verification before sign-off

Run the checklist and demo script in `expected-output.md`; record drift in its gap log.
