# Phase 08 — Instructions

Implement only S1–S6 from `text.md`; reserved/mock generation endpoints remain uncalled.

## Step 1 — DTOs and real scheduling data source

Create exact DTOs for available exams, selection request/response, preference update, onboarding
status, and test metadata. Implement real Dio calls S1–S6 with session/response-derived IDs.

**Verify:** available exams/dates are decoded from S1; no exam/date list constant exists in feature
code. Request tests assert POST returns/handles 201 and exact weight map.

## Step 2 — Repository and validation

Implement repository methods returning `ApiResult`. Mirror subject sets, non-negative weights,
sum=100, future date, and ≥30-day rule. Apply full validation to both POST and PUT. Do not clamp or
invent weights to make an invalid submission pass.

**Verify:** validator tests cover JEE Main/Advanced/Combo and NEET subject sets, 99/100/101 totals,
negative values, missing subjects, and date boundaries.

## Step 3 — Schedule-test page

On entry fetch S1 and any existing S3 selection. Render only returned exams/dates and actual prior
weights. Build exam selector, date picker constrained to returned dates plus contract rules, weight
inputs, live remaining total, and review step.

**Verify:** loading/error/empty S1 states contain no substitute exams. Changing exam resets only
incompatible user input, not to hardcoded weights.

## Step 4 — Selection and success

Submit actual form values with real parent/child IDs. On 201 render `diagnostic_test_id`,
`scheduled_date`, exam, and date from `ExamSelectionResponse`. Invalidate status/selection/tracker
providers so they refetch. Do not construct a local success object after failure.

**Verify:** double-submit prevention, 400/404/409/422/500 handling, and response-driven success.

## Step 5 — Preferences editing

Load current S3 values and submit changed real weights through S4. Render returned selection and
refresh status. Never call the unused `/api/diagnostic-test/schedule` endpoint.

**Verify:** full subject validation applies despite the backend's weaker PUT check.

## Step 6 — Scheduled-test tracker

Fetch S6 using the real child ID. Group/display only returned tests with labelled statuses. Detail,
results, and schedule actions pass the selected response IDs. Empty/error/backend-mock responses get
honest states, not tracker fixtures.

**Verify:** `scheduled` renders correctly; 500 produces blocked/error UI and no rows.

## Step 7 — Final verification

```bash
flutter analyze
flutter test
flutter test integration_test/scheduling_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Run available-exams → selection → real confirmation → preferences → tracker against the backend.
Record actual backend availability/gaps and complete `expected-output.md`.
