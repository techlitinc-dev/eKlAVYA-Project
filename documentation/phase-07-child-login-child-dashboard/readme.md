# Phase 07 — Child Login & Child Dashboard

**Purpose:** A dedicated child login (username + password created by the parent in phase-06)
and the child's home screen: greeting, "My Tests", an AI-processing card, and a "My
Schedule" card. This phase also defines the **ChildNavGraph route contract** that phases
09/10/11 wire up.

**This phase writes documentation only. No application source code is written here.**

## What the phase delivers

- `text.md` — the child auth endpoint contracts (login, token refresh, logout, me), the
  child test-list / analytics / schedule read contracts, the ChildNavGraph contract, the
  child-mode security rules, and screen state machines.
- `instructions.md` — ordered build steps for `ChildLogin`, `ChildDashboard`, the child
  session integration, and the nav graph.
- `expected-output.md` — acceptance checklist, manual demo script, gap log.

## Scope

In scope:

- `ChildLogin` screen: username + password, generic wrong-credential error, offline /
  server-failure / retry states; on success saves the **child session** and routes into
  the child graph.
- `ChildDashboard`: greeting with the child's name from the child session; "My Tests" list
  (from the diagnostic-test student endpoint) split into Upcoming / Completed; `StatusPill`
  per status with icon + label (never color alone); tap behavior per status; AI-processing
  status card; "My Schedule" card.
- `ChildNavGraph` **contract** (routes and arguments defined here; screens wired in
  phases 09/10/11).
- Child logout: clears **only** the child session, returns to the role-pick screen.

Out of scope:

- Creating child credentials — phase-06. Parent screens — phases 05/06/08.
- Test instructions / runner / submission — phase-09. Results — phase-10. Schedule view —
  phase-11.

## Dependencies

| Dependency | Phase | What this phase assumes |
|---|---|---|
| Project setup | 02 | Package `ai.eklavya.app`; Compose + Hilt + Retrofit + Navigation Compose. |
| Design system | 03 | `StatusPill`, `GlassDialog`, and the glass component set exist. |
| Networking & session | 04 | `SessionManager` exposes **separate** parent and child session storage and the auth-header provider. This phase writes only the child session; the parent session is never read or modified here. |
| Role pick | 05 | An entry screen offers "Parent" vs "Child"; the Child path lands on `child_login`. |
| Child profile + credentials | 06 | A parent has created a child with username/password. |

## Backend facts that shape this phase

1. **Child login is username-only.** `login_service.login_child` queries `children` by
   `username` and plaintext-compares `password` (`Backend/services/login_service.py:776-793`).
   Both unknown username and wrong password return the same 401 `"Invalid username or
   password"` (`:781-793`, mapped at `routers/login_router.py:802-818`) — the app must show
   one generic error. `BACKEND CHANGE REQUIRED` gap #1 (plaintext) applies to phase-06
   handling; do not log credentials here either.
2. **The child token is a distinct JWT** with `child_id`/`student_id` (same value),
   `username`, `is_student:true` claims (phase-01 §6.3; `services/token_service.py:375-557`),
   persisted as a `user_type:"child"` session (`login_service.py:884-894`).
3. **`student_id` ≡ `child_id`.** The login response returns both with the same value
   (`login_service.py:822-823`); every student-scoped endpoint takes the child id.
4. **The test-list endpoint is mock today.** `GET /api/diagnostic-test/student/{student_id}`
   500s in the default testing backend (handler subscripts the bypass string,
   `routers/diagnostic_test_router.py:652`) and its canned first item uses the literal
   `"scheduled"`, which is not a `TestStatus` member (`models/diagnostic_test_models.py:35-41`)
   — `BACKEND CHANGE REQUIRED` gaps #4 and #7. The app implements the documented contract
   and tolerates failure and the extra literal.
5. **Auth header is ignored in the default dev backend** (testing bypass), but every child
   call must still send `Authorization: Bearer <child token>` and scope every request to
   `child_id` from the **child session** (phase-01 §6.1, gap #7).

## Source references

| Backend file | Used for |
|---|---|
| `Backend/routers/login_router.py` | Child login/refresh/logout/me handlers (`:719-827`, `:830-919`, `:922-1010`, `:1013-1144`) |
| `Backend/services/login_service.py` | `login_child` response shape (`:747-830`), session creation |
| `Backend/models/login_models.py` | `ChildLoginRequest` (`:453-558`), `LoginResponse` (`:274-373`), `TokenResponse` (`:376-419`), `LogoutResponse` (`:422-450`) |
| `Backend/routers/diagnostic_test_router.py` | Student test-list handler + mock (`:595-693`) |
| `Backend/models/diagnostic_test_models.py` | `TestStatus` enum (`:35-41`), `TestMetadata` (`:297-342`), `ExamType` (`:28-32`) |
| `Backend/routers/analytics_router.py` | `GET /api/analytics/student/{student_id}` (`:262-286`) |
| `Backend/routers/schedule_router.py` | `GET /api/schedule/student/{student_id}` (`:330-388`) |
| Phase-01 `text.md` §6.3, §7.D, §7.H, §8, §11 | Token claims, mock lifecycle, student≡child, canonical JSON, gaps #1 #4 #7 |
