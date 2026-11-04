# Phase 08 — Expected Output & Sign-off

## Deliverables

Flutter exam/date selection, validated weights, response-driven scheduling confirmation, preference
editing, onboarding refresh, and real scheduled-test tracker.

## Verification checklist

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] S1–S6 DTO/request tests match exact contracts and status codes.
- [ ] Exams/dates come from S1; no exam/date constants exist in feature code.
- [ ] JEE/NEET subject sets, non-negative weights, sum=100, future date, and ≥30 days are tested.
- [ ] Invalid input never triggers POST/PUT; values are never clamped or invented.
- [ ] Confirmation displays only actual 201 response fields including diagnostic test ID/date.
- [ ] Preferences use real S3 values and returned S4 response.
- [ ] Tracker uses real S6 rows/statuses and handles `scheduled` and backend failures honestly.
- [ ] Reserved/mock generation and scheduling endpoints are never called.
- [ ] Accessibility, loading, empty, error, and duplicate-submit prevention pass.

## Real-backend demo

Fetch available exams, select an actually returned exam/date, enter valid weights, submit, and compare
the confirmation with the 201 response. Verify selection/status with GET, edit weights and verify PUT,
then inspect tracker behavior. Record backend blockers rather than manufacturing a successful test.

## Real-data audit

- [ ] No hardcoded exam cards/dates, default preference record, diagnostic ID, scheduled row, or
      success response.
- [ ] All IDs derive from parent session and real child/test responses.
- [ ] Failed/empty calls produce no substitute content.

## Gap log

| Gap | Handling |
|---|---|
| #4 `scheduled` outside enum/mock lifecycle | Accept real literal; blocked/error state on failure |
| #7 auth/ownership bypass | Parent Bearer and session/response-derived IDs |

Sign off only when all applicable live responses match the UI and the real-data audit is clean.
