# Phase 05 — Expected Output & Sign-off

## Deliverables

Complete Flutter parent registration, verification, login/restore, dashboard, weekly report, goals,
settings, and navigation using the real endpoints and Phase 04 sessions.

## Verification checklist

- [ ] `flutter analyze` and `flutter test` pass; parent integration flow runs against the backend.
- [ ] DTO/request tests cover every endpoint and all parent-profile response variants.
- [ ] Registration success routes to login and never fabricates a token/session.
- [ ] Verification uses real sent/confirmed codes; production never depends on dev-returned codes.
- [ ] Wrong login credentials store nothing; valid login restores the response-derived parent.
- [ ] Child/onboarding resolution uses real parent ID and returned child ID.
- [ ] Dashboard/report/goals/settings render only actual response fields.
- [ ] Goal and notification mutations refresh/render server responses, not assumed server state.
- [ ] Parent logout leaves child session untouched; switch-to-child never shares the parent token.
- [ ] Forgot-password is an honest gap #3 unavailable state.
- [ ] Accessibility, loading, empty, error, retry, and session-expired states pass widget tests.

## Real-backend demo

1. Register a parent through the UI and log in with the same tester-entered credentials.
2. Verify `/me` and onboarding/child calls use the real parent ID.
3. Open dashboard and weekly report; compare every value with the endpoint responses.
4. Create and edit a goal; verify with subsequent GET.
5. Change notification settings; verify with subsequent GET.
6. Stop backend and retry; verify network error and no replacement dashboard.
7. Log out and verify parent session cleared only.

## Real-data audit

- [ ] No demo parent/child, fixed IDs, hardcoded metrics, report, goals, settings, or results.
- [ ] Empty `weak_areas`/null score and backend gap #6 remain honest empty states.
- [ ] Failed calls never return local success or fabricated content.
- [ ] Offline content, if enabled, is a labelled prior successful response only.

## Gap log

| Gap | Handling |
|---|---|
| #3 no parent password reset | Disabled/unavailable explanation; no simulated flow |
| #6 dashboard collection mismatch | Render real null/empty fields; no inferred analytics |
| #7 auth/ownership bypass | Bearer + session-derived IDs on every call |

Sign off only when automated and applicable live checks pass and every value can be traced to an
endpoint response or current user input.
