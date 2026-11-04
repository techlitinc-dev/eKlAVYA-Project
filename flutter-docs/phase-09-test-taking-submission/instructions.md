# Phase 09 — Instructions

Implement only the documented diagnostic endpoints. The current backend-blocked path is a required
result, not something to hide with local test data.

## Step 1 — Test DTOs and real remote data source

Create exact DTOs for metadata, sections/questions, start/status, submission, and results from
`text.md`. Implement real Dio calls for fetch, metadata, status, start, submit, and results. Test and
student IDs are required arguments from child route/session state.

**Verify:** serialization/request tests cover integer answer keys on the wire, allowed answer values,
duration/status fields, and every path. No fixture is registered as an app data source.

## Step 2 — Repository and capability handling

Implement `TestRepository` returning `ApiResult`. Classify the observed 500 TypeError signature, 501,
and 404 as backend-unavailable where specified. Do not convert any failure into an empty test with
questions or a successful attempt.

**Verify:** current-backend responses produce the unavailable state; malformed responses produce a
parse error; successful responses decode unchanged.

## Step 3 — Eligibility and instructions

Build controller/page that fetch real metadata/status/full test as required. Derive eligibility only
from actual status/time/attempt contract. Render returned duration, question counts, sections, and
instructions. Declarations are user input; start calls the real start endpoint.

**Verify:** unavailable/ineligible states cannot start; no duration or question count is hardcoded.

## Step 4 — Test session and runner

On real start/fetch success, create session state from returned questions and metadata. Implement
single-question navigation, palette, selectable options, and countdown from the actual duration/start
time. Persist only user answers and session timing locally for recovery; never persist credentials.

**Verify:** all questions/options come from the response; navigation and answer restoration work;
app lifecycle/timer expiry trigger the documented submission behavior without inventing answers.

## Step 5 — Submission

Show actual answered/unanswered counts. Submit the real answers map with real test/student IDs and
measured time. Prevent duplicate submission. On success render the actual result response and pass
the same real answers to Phase 10 handoff storage/state.

**Verify:** request body matches contract; timeout/network/server errors keep honest unsubmitted
state for retry where allowed; second submit is impossible; failed submit shows no score/result.

## Step 6 — Result and navigation

Fetch persisted results only when required by the contract. Route to child dashboard or Phase 10
with real IDs. Do not calculate a replacement score when results are missing.

**Verify:** result fields match response; current backend ends at the explicit unavailable/error
state rather than a fabricated result.

## Step 7 — Accessibility and final checks

Add semantics for question/options/palette/timer, 48-pixel targets, text scaling, focus order, and
reduced motion.

```bash
flutter analyze
flutter test
flutter test integration_test/test_taking_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Run both demos in `expected-output.md`: current backend blocked behavior and backend-fixed real test
flow. Complete the real-data audit and gaps #4/#7.
