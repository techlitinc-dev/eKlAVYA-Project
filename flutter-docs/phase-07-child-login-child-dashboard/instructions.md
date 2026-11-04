# Phase 07 — Instructions

Use Phase 04 child auth and real child-scoped endpoint responses throughout.

## Step 1 — Child login page

Build username/password form and controller on `SessionRepository.loginChild`. Validate the exact
contract. On real success save only the child session and route to child dashboard. Show one generic
message for unknown username/wrong password and never log credentials.

**Verify:** 401 stores nothing and does not navigate; success uses response `child_id/student_id`;
parent session remains intact.

## Step 2 — Child home DTOs and remote data sources

Implement real Dio calls for C5 test list, C6 analytics list, and C7 current schedule. Accept the
documented `scheduled` literal and unknown statuses defensively without inventing records. DTO fields
match `text.md`; no static test/analytics/schedule objects.

**Verify:** paths use the active child response ID and Bearer token; parsing covers empty/null/error.

## Step 3 — Child dashboard repository/controller

Load C5+C6+C7 concurrently with independent section state. Each section returns real data or its own
failure; one failure must not erase other successful responses. Pull-to-refresh repeats the real
calls. Greeting comes from restored login/profile data.

**Verify:** all combinations of success/empty/error are tested without a fallback dataset.

## Step 4 — Dashboard widgets

Render Upcoming/Completed from actual statuses, with `StatusPill` icon + label and documented tap
behavior. AI card appears only from actual analytics state. Schedule card appears only from actual
schedule state; null schedule gets genuine empty UI.

**Verify:** no canned test or schedule appears when C5/C7 fails or returns empty. Accessibility and
text scaling pass.

## Step 5 — Child navigation and logout

Register child dashboard, test, results, and schedule routes from `text.md` §8 using go_router.
Required IDs come from tapped endpoint models. Logout calls the real child logout, clears only child
storage, and returns to role selection.

**Verify:** deep links cannot substitute a fixed ID; child logout preserves parent session.

## Step 6 — Backend-blocked behavior

When C5 returns the current 500 TypeError signature/404/501, show the documented backend-unavailable
state and retry. Do not copy the backend's canned list into Flutter and do not claim tests exist.

**Verify:** current-backend demo shows the honest blocked state; backend-fixed demo displays only the
actual returned tests.

## Step 7 — Final verification

```bash
flutter analyze
flutter test
flutter test integration_test/child_home_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Exercise real child login, restore, dashboard, refresh, and logout. Complete the real-data audit and
gap log in `expected-output.md`.
