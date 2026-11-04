# Phase 07 — Child Login & Child Dashboard (text.md)

Reference material. Citations are `path/file.py:line` at commit
`d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`. Phase-01 `text.md` §4 (error envelopes:
legacy `{"detail": str}`; pagination: integer `limit`/`offset` on `/api/*`) and §6 (auth)
apply unchanged.

---

## 1. Endpoints consumed in this phase

| # | Endpoint | Method/Purpose | Success | Source |
|---|---|---|---|---|
| C1 | `/api/auth/login/child` | POST — child login | 200 `LoginResponse` | `routers/login_router.py:719-827` |
| C2 | `/api/auth/token/refresh/child` | POST — rotate child tokens | 200 `TokenResponse` | `routers/login_router.py:830-919` |
| C3 | `/api/auth/logout/child` | POST — revoke child session | 200 `LogoutResponse` | `routers/login_router.py:922-1010` |
| C4 | `/api/auth/me/child` | GET — child profile from token | 200 child doc | `routers/login_router.py:1013-1144` |
| C5 | `/api/diagnostic-test/student/{student_id}` | GET — child's tests | 200 `List[TestMetadata]` (mock; see §5) | `routers/diagnostic_test_router.py:595-693` |
| C6 | `/api/analytics/student/{student_id}` | GET — child's analyses (presence) | 200 `List[AnalyticsReport]` | `routers/analytics_router.py:262-286` |
| C7 | `/api/schedule/student/{student_id}` | GET — child's active schedule (presence) | 200 `Schedule` or null | `routers/schedule_router.py:330-388` |

All C5–C7 calls: `student_id` = `child_id` from the **child session** (student ≡ child,
phase-01 §7.H). Auth header: `Authorization: Bearer <child access token>` (ignored by the
testing bypass, but always sent — phase-01 §6.1).

## 2. C1 — Child login

### 2.1 Request — `ChildLoginRequest` (`models/login_models.py:453-509`)

| Field | Rule |
|---|---|
| `username` | 3–30 chars after strip; regex `^[a-zA-Z0-9_@.]+$` (`login_models.py:485-518`) |
| `password` | 8–50 chars; ≥1 letter; ≥1 digit (same validator family as `child_models.py:223-252`) |

Malformed body → 422.

### 2.2 Response — 200 `LoginResponse` (`login_models.py:274-373`, built at
`login_service.py:818-830`)

```json
POST /api/auth/login/child
{"username":"aarav_jee2026","password":"Passw0rd1"}
→ 200
{"token":"<jwt>","refresh_token":"<jwt>","parent_id":"<parent-id>",
 "email":"aarav_jee2026@student.local","expires_in":86400,
 "student_id":"child_abc123","child_id":"child_abc123",
 "username":"aarav_jee2026","name":"Aarav Sharma","is_student":true,
 "message":"Child login successful"}
```

Facts the client relies on:

- `student_id == child_id` (same Firestore doc id; `login_service.py:822-823`). Store one
  value; expose it as `childId`.
- `email` is synthesized as `f"{username}@student.local"` (`login_service.py:826`) — it is
  not a mailbox; never try to email it, never display it as contact info.
- `expires_in` = 86400 (24 h; `token_service.ACCESS_TOKEN_EXPIRY` per phase-01 §6.2).
- `name` may be null if the profile lacks it; the greeting falls back to username.
- `is_student` is always `true` here; the app routes by it (parent logins return
  `is_student:false`/null — phase-01 §8).

### 2.3 Errors

- **401** `"Invalid username or password"` — returned for *both* unknown username and
  wrong password (`login_service.py:781-793`; mapping `login_router.py:802-818` shows a
  404 branch only when the message contains "not found", which this service never
  produces — so 404 is not expected from C1). UI shows exactly one generic message;
  never distinguish which field failed.
- **422** body validation.
- **500** backend failure → "server failure" state with retry (not a credential error).
- Success also updates `last_login` server-side (`login_service.py:810-813`) — no client
  action.

## 3. C2 — Child token refresh

`POST /api/auth/token/refresh/child`, body `TokenRefreshRequest{refresh_token}`
(`login_models.py:220-271`; non-empty string).

- 200 `TokenResponse{token, refresh_token, expires_in}` (`login_models.py:376-419`) —
  both tokens rotate (phase-01 §6.2). Persist the new pair, replacing the old.
- 401 → refresh dead: clear the child session and return to `child_login`. **Never** fall
  back to the parent session — sessions are separate (fixed decision, phase-04).

## 4. C3 / C4 — Child logout and profile

- C3: header `Authorization: Bearer <child token>` → 200 `LogoutResponse{message}`; 401
  (`login_router.py:993-1001`). On 401 the session is already invalid — still clear local
  child state. C3 revokes only the child session doc (`user_type:"child"`,
  phase-01 §6.3); the parent session is untouched.
- C4: same header → 200 child doc, e.g. `{child_id, parent_id, name, username, age,
  grade, current_level, created_at, last_login}` (`login_router.py:1063-1075` doc
  example). The handler requires `is_student:true` in the token and 401s expired/invalid
  tokens (`login_router.py:1084-1111`). Caveat: a **parent** token fails the
  `is_student` check via a `ValueError` that this handler does not map to HTTP
  (`login_router.py:1089-1090`) → 500. That is a backend defect (gap #7-adjacent); the
  app must never send a parent token to C4, and treats 500 on C4 as an auth-state error,
  not as child data.
- C4 is optional for the dashboard (identity already comes from the C1 response); use it
  as a session-validity probe on cold start.

## 5. C5 — Child test list (MOCK — read carefully)

`GET /api/diagnostic-test/student/{student_id}?status=&limit=10&offset=0`

- Query params: `status` optional `TestStatus`; `limit` default 10, **1–100**;
  `offset` default 0 (`diagnostic_test_router.py:623-628`).
- Contract success: 200 `List[TestMetadata]` (`diagnostic_test_models.py:297-342`):

```json
[{"test_id":"test_1","exam_type":"JEE_MAIN","student_id":"child_abc123",
  "generation_date":"2026-11-02T09:00:00","start_date":null,
  "submission_date":null,"status":"pending"}]
```

  Fields: `test_id: str`, `exam_type: ExamType`, `student_id: str`,
  `generation_date: datetime`, `start_date: datetime?`, `submission_date: datetime?`,
  `status: TestStatus`.

- Enums (`diagnostic_test_models.py:28-41`):
  - `ExamType`: `JEE_MAIN | JEE_ADVANCED | NEET` — **no `JEE_COMBO`** member even though
    exam selection accepts it (phase-08); if `JEE_COMBO` ever appears, parse leniently.
  - `TestStatus`: `pending | in_progress | completed | expired | cancelled`.
  - **Plus the literal `"scheduled"`** written by the mocks and by `exam_service`
    (`diagnostic_test_router.py:681`, `services/exam_service.py:197`) which is **not** a
    `TestStatus` member — `BACKEND CHANGE REQUIRED` gap #4. The client model must accept
    `"scheduled"` and map it to an "Upcoming/scheduled" UI state.

- **Live behavior today (gap #4/#7):** the handler subscripts the bypass string
  `current_user["parent_id"]` (`diagnostic_test_router.py:652`) → TypeError → 500 for any
  real `student_id` in the default testing backend. Even with auth fixed, the first canned
  item (`:672-684`) returns `"scheduled"` and would fail response validation. Therefore:
  the app must implement the contract, and must **tolerate 500/empty** by rendering the
  "My Tests" empty state with a refresh affordance — never crash. Recorded in the gap log.

## 6. C6 — Child analytics presence

`GET /api/analytics/student/{student_id}?limit=10&offset=0` → 200
`List[AnalyticsReport]` (`analytics_router.py:262-286`; limit 1–50). This phase uses the
list **only as a presence check**: non-empty ⇒ at least one completed analysis exists.
Report internals are phase-10. Auth: declared `none` (gap #7) — the app still sends the
child header and the session-derived `student_id`.

## 7. C7 — Child schedule presence

`GET /api/schedule/student/{student_id}?status_filter=active` → 200 **`Schedule` or
`null`** (`schedule_router.py:330-388`; `response_model=Optional[Schedule]`). Null (or a
200 with `null` body) means "no active schedule" — a normal empty state, not an error.
Presence only; `Schedule` internals are phase-11. Do not call any other `/api/schedule/*`
endpoint in this phase.

## 8. Child go_router branch contract

Defined here; wired by phases 09/10/11. Separate graph from the parent graph (fixed
decision: parent and child sessions/graphs are fully separate).

| Route | Screen (owner phase) | Arguments | Entry rules |
|---|---|---|---|
| `child_login` | ChildLogin (this phase) | — | Start destination when no child session; role-pick "Child" lands here |
| `child_dashboard` | ChildDashboard (this phase) | — | Default start when a valid child session exists |
| `child_test_instructions` | Test instructions (phase-09) | `test_id` | Tap an eligible test (§10.2) |
| `child_test_runner` | Test runner (phase-09) | `test_id` | From instructions → start |
| `child_submission_status` | Submission status (phase-09) | `test_id` | After submission |
| `child_results` | Results (phase-10) | `test_id` | Tap a completed test with results; AI-processing card CTA |
| `child_schedule` | Schedule view (phase-11) | — (uses session child_id) | "My Schedule" card CTA |

Rules: no parent-only or superadmin route is registered in this graph; no route accepts a
`child_id` argument — the child id always comes from the child session; destinations
phases 09–11 own may be stubs (TODO screen) until their phase lands.

## 9. Child-mode security rules (prominent, non-negotiable)

1. **Only the authenticated child's data.** Every C5–C7 call uses `student_id = child_id`
   from the child session. There is no child selector anywhere in child mode; there is no
   way to view a sibling. A child mode screen never takes an id from navigation arguments
   that could name another child (§8: only `test_id` args; `test_id`s belong to the
   session child by construction of the lists).
2. **No cross-role reachability.** The child graph contains no parent or superadmin
   destinations; the parent graph contains no child destinations (child login is the child
   graph's start). Back from `child_login` returns to role-pick, never to parent screens.
3. **Session isolation.** Child login writes only the child session slot (token,
   refresh_token, child_id/student_id, username, name, parent_id reference, is_student,
   expiry). The parent session store is never read or written in this phase. Token
   refresh (C2) uses only the child refresh token. Logout (C3) clears only the child
   session and returns to role-pick; a parent session present on the device is untouched
   (verify in testing: parent stays logged in after child logout).
4. **Header discipline.** All C2–C7 calls send `Authorization: Bearer <child token>`. A
   parent token must never be attached to child calls (C4's 500-on-parent-token is the
   visible symptom, §4).
5. **No credential logging.** C1's body and the child token are never logged (gap #1
   hygiene carries over).

## 10. Screen specifications

### 10.1 ChildLogin

- Two fields (username, password with show/hide), both required; submit disabled while
  either is blank or locally invalid (§2.1 rules; local errors are convenience only — the
  401 stays generic).
- States: `Idle → Submitting → Success(nav by is_student) | Error(401-generic |
  validation | network | server-500)`. Offline → inline "No connection" + retry.
- Success: persist child session (§9.3), then route: `is_student == true` →
  `child_dashboard`; anything else → error state (unexpected for this endpoint).
- "Back" returns to the role-pick screen.

### 10.2 ChildDashboard

Layout order (phase-03 glass components):

1. **Greeting** — "Hello, {name}" (name from child session; fallback username).
2. **AI-processing card** — shown while an analysis is pending for this child (derived
   from C6: a submission exists whose report is not yet retrievable — until phase-10 the
   precise signal is the C6 list state; the card links to `child_results` for the newest
   `test_id`). Copy: "Your report is being prepared." Card hidden when nothing pending.
3. **My Tests** — C5 list, split locally:
   - **Upcoming**: `status ∈ {pending, scheduled}` (plus `in_progress` resumed attempt).
   - **Completed**: `status == completed`.
   - Remaining statuses (`expired`, `cancelled`) render in the list with their pills but
     are not tappable.
   - `StatusPill` per item: icon + text label, colored — never color alone
     (accessibility). Mapping: `pending` "Pending" (clock icon), `scheduled` "Scheduled"
     (calendar icon), `in_progress` "In progress" (play icon), `completed` "Completed"
     (check icon), `expired` "Expired" (alert icon), `cancelled` "Cancelled" (cross icon).
   - Tap behavior: eligible test (`status ∈ {pending, scheduled}` with
     `scheduled_date`/`generation_date` ≤ now — until phase-09 hardens eligibility, treat
     any `pending`/`scheduled` item as eligible) → `child_test_instructions(test_id)`.
     `completed` with results present (C6 non-empty for that test's analysis — presence at
     child level is sufficient today) → `child_results(test_id)`.
4. **My Schedule** — C7 card: schedule present → title + `total_days`/`exam_date` summary +
   CTA `child_schedule`; null → "No active study plan yet" (generation is phase-11/flow;
   the card never errors the page).
5. **Logout** — menu action → C3 (best-effort) → clear child session → role-pick.

Data policy: single `Riverpod controller` loading C5+C6+C7 in parallel on entry and on pull-to-
refresh; each section fails independently (section-level retry), the dashboard itself
only fails if C5 fails — in which case show the full error/empty state with retry (C5 is
the mock-prone call; §5).

### 10.3 Empty / error states

- C5 empty list → "No tests yet" + explanation that a parent schedules tests (phase-08).
- C5 500/network → error state with retry (per §5, expected on today's backend).
- C6 empty → hide AI card.
- C7 null → §10.2 item 4 empty copy.

## 11. State machines

**ChildLogin** — `Idle → Submitting → Authenticated(session saved, navigate) |
InvalidCredentials(generic) | Offline(retry) | ServerFailure(retry)`.

**ChildDashboard** — `Loading → Ready(tests, analysisPending, schedule) |
TestsError(retry) | SessionExpired(→ child_login via phase-04 auth handler)`.
Pull-to-refresh returns to `Loading` without clearing the screen.

## 12. Accessibility

- Login uses labelled fields, password-toggle state semantics, live-region error announcements, and
  announced submit progress.
- Dashboard pills carry icon + text + Flutter `Semantics` labels (for example, actual completed
  status); section headings identify Upcoming/Completed/My Schedule; lists announce real counts;
  actual AI status updates use a live region.

## 13. Files (under `Android_App/lib/`)

| Path | Contents |
|---|---|
| `features/auth/data/datasources/auth_remote_data_source.dart` | C1–C4 real Dio calls from Phase 04 |
| `features/auth/data/dto/auth_dtos.dart` | Child login/session DTOs from Phase 04 |
| `features/auth/presentation/pages/child_login_page.dart` | §10.1 page |
| `features/auth/presentation/controllers/child_login_controller.dart` | §10.1 immutable state/intent |
| `features/child/data/datasources/child_home_remote_data_source.dart` | C5–C7 real Dio calls |
| `features/child/data/dto/child_home_dtos.dart` | Test/analytics/schedule mirrors with lenient status parsing |
| `features/child/data/repositories/child_home_repository_impl.dart` | Real C5–C7 repository |
| `features/child/presentation/pages/child_dashboard_page.dart` | §10.2 endpoint-driven dashboard |
| `features/child/presentation/controllers/child_dashboard_controller.dart` | Independent C5/C6/C7 section states |
| `router/child_routes.dart` | §8 go_router contract |

Reuse Phase 03 `StatusPill`; do not add a feature-local variant. No file contains fallback test,
analytics, schedule, greeting, or ID values.
