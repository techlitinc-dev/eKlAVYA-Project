# Phase 07 — Child Login & Child Dashboard

**Purpose:** Deliver Flutter child login and a child home fed by real child auth, test-list,
analytics, and schedule endpoints. Defines the child go_router branch used by Phases 09–11.

## Scope

- Username/password login with generic credentials error and real child-session storage.
- Dashboard greeting from restored child session/profile response.
- Test list from `GET /api/diagnostic-test/student/{student_id}`, grouped by actual status.
- AI-processing and schedule cards from actual analytics/schedule responses.
- Child logout clearing only the child session.
- Child route contract for tests, results, and schedules.

Out of scope: taking tests (P09), results detail (P10), schedule detail (P11), and parent screens.

## Dependencies

Phases 02–04 supply Flutter, design, Dio, and isolated sessions. Phase 05 supplies role selection;
Phase 06 supplies real child credentials. `student_id` always equals response `child_id`.

## Real-data rule

No static child name, canned test, fabricated status, score, analytics card, or schedule preview.
Each dashboard section independently renders loading, real content, genuine empty, or its real error.
The current test-list backend is mock/broken (gaps #4/#7): the app still calls the documented real
endpoint, tolerates the real `scheduled` literal, and shows the backend-blocked/error state on 500.
It must never replace that failure with local test records.

## Backend facts

- Child login uses username/password and returns a distinct child JWT with `child_id`/`student_id`.
- Unknown username and wrong password use one generic error; credentials are never logged.
- Auth bypass in the default backend does not justify omitting the child Bearer token.
- Test-list mock data is a backend limitation, not client sample data to copy into Flutter.

## Endpoints

C1–C4: child login, refresh, logout, and `/me/child` through Phase 04.
C5: `GET /api/diagnostic-test/student/{student_id}`.
C6: `GET /api/analytics/student/{student_id}`.
C7: `GET /api/schedule/student/{student_id}`.

## Deliverable files

`instructions.md` — Flutter implementation sequence; `text.md` — contracts, routes, screens and
security; `expected-output.md` — real-backend checks, blocked-state demo, and gap log.
