# Phase 10 — AI Analysis & Results (Flutter)

**Purpose:** After real test submission, trigger analysis and show processing status; child and
parent viewers render the actual analytics report through shared Flutter widgets.

## Verified backend reality

- `POST /api/analytics/generate` returns 202 but currently runs synchronously.
- `GET /api/analytics/{analytics_id}` returns a bare `AnalyticsReport`, not a status/progress wrapper.
- Poll anyway: 200 decodes the real report; 404 means not yet available within the documented policy.
- Missing Firestore credentials can produce real 500 responses. Show failure/retry, never a report
  substitute.
- Send Bearer tokens even though current analytics routes lack enforcement (gap #7).

## Scope

- `TRIGGERING → POLLING → COMPLETED / FAILED / FAILED_RETRYABLE` using only endpoint outcomes.
- Child `AiProcessingStatusPage`, auto-triggered after real submission.
- Shared report widgets and `ChildResultsPage` / `ParentResultsViewerPage`.
- Real `AnalyticsRepository` and DTOs for consumed analytics endpoints.
- Child triggers with actual submitted answers; parent reads only and never triggers.

Out of scope: test taking (P09) and schedule generation (P11).

## Endpoints

| Endpoint | Use |
|---|---|
| `POST /api/analytics/generate` | Child trigger with real test/student/answers |
| `GET /api/analytics/{analytics_id}` | Poll/fetch bare report |
| `GET /api/analytics/student/{student_id}?limit=&offset=` | Child/parent real history |
| `GET /api/analytics/{analytics_id}/insights` | Optional real insights |
| `GET /api/analytics/{analytics_id}/weak-topics` | Actual HIGH-priority topics |

Do not consume placeholder `GET /api/analytics/test/{test_id}`.

## Dependencies

Phases 02–04 provide Flutter/Dio/sessions/errors; Phase 03 supplies cards; Phase 09 supplies real
submission handoff; Phases 05/07 supply parent/child entries.

## Real-data rule

No fabricated progress percent, processing message claiming a server stage, analysis ID, score,
subject/topic analysis, insight, weak topic, chart, or report. Indeterminate progress is used because
the backend provides no numeric progress. Empty/failed endpoint responses never become local AI
analysis.

## Files

`instructions.md` — Flutter repositories/controllers/pages/polling; `text.md` — exact contracts and
states; `expected-output.md` — live checks, demos, real-data audit, and gaps.
