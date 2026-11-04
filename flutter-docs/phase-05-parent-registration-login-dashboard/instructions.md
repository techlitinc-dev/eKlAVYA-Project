# Phase 05 — Instructions

Execute after Phases 02–04 pass. All remote values come from the real endpoints in `text.md`.

## Step 1 — DTOs and real remote data sources

Create parent/auth verification/onboarding DTOs with exact JSON names from `text.md` §3. Accept all
documented parent-profile key variants. Do not default names, IDs, scores, goals, or report values.

Implement Dio data sources for registration, verification, onboarding, dashboard, weekly report,
goals, and notification settings. Phase 04 owns login/logout/me; reuse it rather than duplicating
calls. IDs are method arguments derived from session/API state.

**Verify:** request/serialization tests assert every path, query, body, and response shape.

## Step 2 — Repositories and providers

Implement real repositories returning `ApiResult` and domain models. Registration returns the actual
success record and never creates a local session. Dashboard/report/goals/settings return only parsed
responses or failures. Register only these real implementations with Riverpod.

**Verify:** provider and repository tests show no static/demo implementation and no success result
without a successful endpoint response.

## Step 3 — Welcome and parent registration

Build `WelcomePage` and `ParentRegisterPage` with Phase 03 widgets and validation from `text.md` §5.
Submit the primary simple-registration request, or a documented alternate only when its UI is fully
implemented. On real success route to login; never auto-login without tokens.

**Verify:** invalid inputs make no request; valid input calls the endpoint; 409/422/500 render mapped
errors; no profile is fabricated before login.

## Step 4 — Email and phone verification

Build verification pages using actual email/phone passed from registration. Send and confirm through
the four verification endpoints. OTP/code inputs use real user entry. Development-returned codes may
be surfaced only in clearly development-only UI; production neither displays nor depends on them.

**Verify:** resend/confirm responses drive state; expired/wrong/rate-limited codes show real errors.

## Step 5 — Parent login and session restore

Build `ParentLoginPage` on `SessionRepository`. On success, restore from the stored real session and
call `/api/auth/me` when required. Root router redirects from restored role state, not a fixed route.

Implement forgot-password as a backend-unavailable notice only (gap #3); no reset request, success
message, or fabricated email flow.

**Verify:** wrong credentials produce generic real error and no session; successful login routes by
actual role; cold start restores only a valid stored session.

## Step 6 — Resolve child and onboarding state

After parent authentication, fetch onboarding status and child profile in the documented order. Use
the returned child ID for all parent-feature calls. Handle no-child, one-child, request failure, and
session expiry honestly. Do not invent a multi-child list.

**Verify:** tests cover each response branch and assert no request uses a hardcoded child ID.

## Step 7 — Parent dashboard

Build `ParentDashboardPage` and its Riverpod controller. Load the real dashboard response and render
its fields with Phase 03 cards. Empty `weak_areas` and null scores remain empty/null UI. CTAs route
only when their required real child/onboarding data exists.

**Verify:** loading, populated, empty, error, retry, and stale-cache states have widget tests; no
metric is hardcoded.

## Step 8 — Weekly report

Build week selection and `WeeklyReportPage`. Request the selected real week and child ID. Render only
returned report fields; do not calculate replacement analytics when data is absent.

**Verify:** query formatting, real response rendering, empty weeks, and failures are covered.

## Step 9 — Goals

Implement real list/create/edit calls. Validate goal type, positive target, and optional deadline per
contract. Use returned goal IDs for edits. Refresh from the server after mutations rather than
inventing server timestamps/status/current values.

**Verify:** create/edit success uses response data; errors preserve honest form state; empty goals
render an empty state.

## Step 10 — Settings and logout

Load profile and notification settings from their endpoints. Update toggles through PUT and render
the returned settings. Logout calls Phase 04 parent logout and clears only parent state. Switch-to-
child opens child login without copying tokens.

**Verify:** notification state is never locally assumed after failure; parent/child sessions remain
isolated.

## Step 11 — Results entry and parent navigation

Wire all routes in go_router. Parent results initially loads the real analytics list only as far as
Phase 10 contracts permit; do not show a static results placeholder/report. Complete detailed shared
results in Phase 10.

**Verify:** required IDs are route/session/API derived and unknown routes fail safely.

## Step 12 — Offline behavior and final checks

Optionally cache only the last successful dashboard/report responses with child ID and fetch time.
Always attempt refresh when online; label cached content stale and never present it as a new response.

```bash
flutter analyze
flutter test
flutter test integration_test/parent_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Run the real registration→login→child resolution→dashboard→report→goals→settings→logout flow.
Complete `expected-output.md` and record gaps #3/#6/#7.
