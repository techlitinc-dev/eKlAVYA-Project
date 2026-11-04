# Phase 10 — Instructions

Use actual Phase 09 handoff values and analytics responses. Never generate client-side AI content.

## Step 1 — Analytics DTOs and remote data source

Create exact DTOs for generate request/response, bare `AnalyticsReport`, overview, subjects, topics,
insights, chart data, and priority topics. Implement the five consumed real Dio calls in `readme.md`.
Do not consume the placeholder test-list endpoint.

**Verify:** tests decode bare report and list shapes, nullable insights, and HIGH weak-topic results;
generate request contains the actual answers map.

## Step 2 — Real repository

Implement trigger, poll/fetch, student history, insights, and weak-topics methods returning
`ApiResult`. Child trigger uses child session ID and Phase 09 answers. Parent repository exposes only
read methods.

**Verify:** no parent trigger method/call exists; all IDs come from route/session/response state.

## Step 3 — Processing controller

Implement `TRIGGERING → POLLING → COMPLETED / FAILED / FAILED_RETRYABLE`. A real 202 supplies the
analytics ID. Poll the bare report endpoint with the documented interval/backoff/timeout. 200 with a
valid report completes; 404 remains pending within policy; other errors map honestly. Use an
indeterminate indicator because no real progress number exists.

**Verify:** synchronous-first-poll success, delayed 404-then-200, timeout, 500, malformed report, and
retry are covered without a fabricated status wrapper/progress field.

## Step 4 — Processing page

Build `AiProcessingStatusPage` with actual state labels, cancellation/navigation policy, error/retry,
and accessibility announcements. Do not claim named server stages that the API does not report.

**Verify:** no percentage or stage is invented; completion uses the decoded real report.

## Step 5 — Shared results widgets and viewers

Build overview, subject, topic, insight, weak-topic, and visualization widgets requiring report model
inputs. Child and parent pages load real report/history and optional enrichment independently. Missing
insights/weak topics render empty states; errors do not erase successful base report content.

**Verify:** every value is traceable to report/endpoint fields; charts have text equivalents; parent
never triggers analysis.

## Step 6 — Navigation, cache, and cleanup

Wire Phase 09 handoff and Phase 05/07 entries with real IDs. Clear temporary submitted answers after
the trigger succeeds according to the handoff policy. Any cache contains only actual reports and is
labelled when offline.

**Verify:** deep links cannot insert fixed analytics IDs; no temporary answer payload leaks to logs.

## Step 7 — Final verification

```bash
flutter analyze
flutter test
flutter test integration_test/analytics_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Run current-backend failure handling and backend-fixed real generation/poll/results demos. Complete
`expected-output.md` and record gaps #4/#5/#7 plus contract drift.
