# Phase 07 — Expected Output & Sign-off

## Deliverables

Flutter child login, session restore, endpoint-driven dashboard, child routes, and isolated logout.

## Verification checklist

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] Wrong credentials show one generic error, save nothing, and do not navigate.
- [ ] Real child login saves response child ID/student ID and preserves parent session.
- [ ] Dashboard C5/C6/C7 calls use the real child ID and child Bearer token.
- [ ] Sections independently handle loading/content/empty/error; one failure erases no other data.
- [ ] Test grouping and taps use actual statuses/IDs; `scheduled` is accepted.
- [ ] AI/schedule cards reflect actual responses; null/empty yields no fabricated card content.
- [ ] Child logout clears only child state and returns to role selection.
- [ ] Child go_router routes match `text.md` and use endpoint-derived IDs.
- [ ] Accessibility, refresh, and session-expiry behavior pass.

## Real-backend demo

Log in with credentials created in Phase 06, restore the child session, and inspect dashboard network
calls. In the current backend, document the real C5 failure and confirm the backend-unavailable UI
contains no tests. In a backend-fixed environment, compare every displayed test/analytics/schedule
value with its response. Log out child and verify parent session remains.

## Real-data audit

- [ ] No canned test list, static greeting, fake analytics, hardcoded schedule, or fallback rows.
- [ ] Backend canned responses are not copied into application/test fixtures presented as live data.
- [ ] Current 500/404/501 responses produce honest blocked/error states.
- [ ] No request uses a fixed student ID.

## Gap log

| Gap | Handling |
|---|---|
| #1 plaintext child credentials | Never log credentials |
| #4 mock test lifecycle/status mismatch | Accept real `scheduled`; show blocked state on failure |
| #7 auth bypass | Child Bearer + response-derived child/student ID |

Sign off only when both current-backend blocked behavior and available real-data flows are verified.
