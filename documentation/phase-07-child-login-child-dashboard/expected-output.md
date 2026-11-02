# Phase 07 — Expected Output & Sign-off

## Deliverables of this phase

1. `text.md` — verified child-auth contracts, the C5 mock caveat, the ChildNavGraph
   contract, child-mode security rules, screen/state specs.
2. `instructions.md` — ordered build steps for auth API, child session, both screens, nav
   graph, refresh handling.
3. Running app code: `ChildLogin`, `ChildDashboard`, `ChildNavGraph` with phase-09/10/11
   stubs, child logout returning to role-pick.

## Verification checklist

### Contracts

- [ ] `POST /api/auth/login/child` sends `{username, password}`; 200 parsed per
      `text.md` §2.2 with `student_id == child_id`, `is_student:true`,
      `email == "<username>@student.local"`, `expires_in:86400`.
- [ ] 401 from login renders the single generic error; no code path distinguishes
      unknown-user vs wrong-password.
- [ ] `POST /api/auth/token/refresh/child` rotates and persists the child token pair;
      401 clears the child session and routes to `child_login`.
- [ ] `POST /api/auth/logout/child` sends the child Bearer header; success clears **only**
      the child session (parent session verified intact).
- [ ] `GET /api/auth/me/child` used at most as a session-validity probe; a 500 on it is
      treated as auth-state error, never as child profile data.
- [ ] C5 called as `GET /api/diagnostic-test/student/{child_id}?status=&limit=10&offset=0`
      with the session child id and child header.
- [ ] C6/C7 called for presence only, with `status_filter=active` on C7; C7 `null` body
      handled as a normal empty state.

### Security (child mode)

- [ ] No child selector / sibling access anywhere in child mode.
- [ ] Child graph contains no parent/superadmin destinations; back from `child_login`
      goes to role-pick only.
- [ ] All C5–C7 calls derive `student_id` from the child session and attach the child
      Bearer header.
- [ ] No child credential or token appears in logs.
- [ ] Child logout leaves a logged-in parent session untouched on the device.

### Resilience & accessibility

- [ ] C5 returning 500 (today's mock behavior) renders the tests error/empty state with
      retry — no crash.
- [ ] `status:"scheduled"` in any test payload parses and renders the Scheduled pill.
- [ ] Dashboard sections fail independently; pull-to-refresh works.
- [ ] Pills have icon + label + contentDescription; login errors announced.

## Manual demo script

Prereqs: backend running; parent logged in on the app; child `aarav_jee2026` /
`Passw0rd1` created via phase-06 (or via demo seed `POST /api/superadmin/demo-session`
{"role":"parent"} → `child_demo_aarav` / `aarav_jee2026`, phase-01 §12).

1. Role-pick → "Child" → `ChildLogin`. Enter wrong password → generic error, no field
   blame. Enter wrong username → identical generic error.
2. Disable network → submit → offline state with retry. Re-enable, submit → dashboard.
3. Backend cross-check of the saved session: the app's child token decodes (JWT payload
   inspection, debug build only) to `is_student:true`, `child_id` set.
4. Dashboard: greeting shows the child's name. With today's mock backend, "My Tests"
   shows the error/empty state with retry (expected — `text.md` §5).
5. Create a real scheduled test via the parent flow (phase-08 preview) or accept the
   empty state; verify no crash either way and pull-to-refresh executes.
6. "My Schedule" card shows the empty copy when no active schedule; logout from the menu
   → C3 → role-pick. Log in as parent again and confirm the parent session was never
   disturbed by the child session's creation or teardown.
7. Token refresh: force-expire the child access token (or wipe it locally) and trigger a
   C5 call → C2 runs → call retried; then corrupt the refresh token → child session
   cleared → `child_login`.
8. Repeat login with `is_student` false response injected (mock) → error state, no
   navigation into child graph.

## Gap log

| Gap (phase-01 §11) | Where encountered | How this phase handles it |
|---|---|---|
| #1 — plaintext child password (`child_service.py:172`, `login_service.py:789-793`) | Login request handling | No credential logging; generic 401; dev-only awareness. |
| #4 — diagnostic lifecycle mock; `"scheduled"` not a `TestStatus` member (`diagnostic_test_models.py:35-41`, `diagnostic_test_router.py:681`) | C5 | Lenient client enum parsing; Scheduled pill; contract implemented against documentation. |
| #4 + #7 — student test-list handler 500s in testing mode (subscripts bypass string) | C5 | Tolerated: error/empty state with retry; logged here as live-behavior evidence (`diagnostic_test_router.py:652`). |
| #7 — no auth enforcement / header ignored (`testing_auth.py:20-42`) | C1–C7 | Header always sent; ids always session-derived; 403/401 handled as auth states. |
| Backend defect (new observation) — `GET /api/auth/me/child` raises unmapped `ValueError` for parent tokens → 500 (`login_router.py:1089-1090`) | C4 | App never sends parent tokens to C4; 500 treated as auth-state error. Logged here. |
| Backend defect (new observation) — child-login router has a 404 branch (`login_router.py:807-812`) the service can never trigger (`login_service.py:781-793`) | C1 error mapping | Documented: only 401/422/500 expected. Logged here. |

## Sign-off rule

Every checklist box checked; demo script passes; gap log entries cite `path:line`. Then —
and only then — phase-08 may start. Backend drift goes to the gap log, never to silent
workarounds.
