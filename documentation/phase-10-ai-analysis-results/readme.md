# Phase 10 — AI Analysis & Results (Android)

**Purpose:** After a diagnostic test is submitted (phase-09), the child's app
triggers the AI analysis and shows processing status; both child and parent apps then
render the analysis report (overview, subjects, topics, insights, weak topics) from
shared components. Phase-01 §7.E defines the mechanism: **poll-based** — `POST
/api/analytics/generate` returns `202` with an `analytics_id`, the client polls
`GET /api/analytics/{analytics_id}` until the report exists.

**Verified backend reality (commit `d8ab491`, re-verified live 2026-11-02):**

- The analytics router declares **no auth dependency** — the imported
  `get_current_user_testing` is never used (`Backend/routers/analytics_router.py:40`;
  handlers at `:121-190`, `:214-259`, etc. take no `current_user`). The client still
  sends `Authorization: Bearer <token>` (production requirement, phase-01 §6.1).
- The pipeline is **synchronous** inside the POST (gap #5,
  `Backend/services/analytics_service.py:261-391`): by the time the POST returns, the
  report is already stored (or failed). The 202 body is hardcoded
  `"status":"pending"` (`analytics_router.py:171-175`). The first poll therefore
  almost always finds the report — the client implements polling anyway (contract-safe).
- `GET /api/analytics/{analytics_id}` returns the **bare `AnalyticsReport` object**
  (`response_model=AnalyticsReport`, `analytics_router.py:193-259`) — there is **no
  `status`, `message`, `report`, `error`, or `progress` wrapper** on the poll
  response, and `AnalyticsReport` itself has no status field
  (`Backend/models/analytics_models.py:706-762`). This corrects the illustrative
  wrapper shape in phase-01 `text.md` §8 (recorded in the gap log).
- Without Firestore credentials, **every** analytics endpoint returns `HTTP 500`
  `{"success":false,"error":{"type":"DefaultCredentialsError",...}}` because the
  `AnalyticsService` dependency constructs a Firestore client in `__init__`
  (verified live; `Backend/services/analytics_service.py:219-257`). The happy path
  requires a backend-fixed environment (see `expected-output.md`).

## Scope

In scope:

- Poll-based status flow: `TRIGGERING → POLLING → COMPLETED / FAILED / FAILED_RETRYABLE`
- `AiProcessingStatusScreen` (child, auto-triggered after submit)
- Shared results UI used by two viewers: `ChildResultsScreen` and `ParentResultsViewerScreen`
- `AnalyticsRepository` + models for all six analytics endpoints
- Trigger UX: **child app triggers** analysis after successful test submission (same
  answers map as phase-09); **parent app never triggers** — it reads via the GET endpoints.

Out of scope:

- Test taking/submission (phase-09); schedules (phase-11); the parent's *decision* UI
  for generating a schedule is phase-11 (this phase only displays results).

## Endpoints consumed (all prefix `/api/analytics`, `analytics_router.py:46-49`)

| Endpoint | Verified behavior | Use |
|---|---|---|
| `POST /api/analytics/generate` | 202 `AnalyticsResponse` (status hardcoded `pending`); synchronous pipeline; 500 if test doc/questions missing (message: "Failed to generate analytics. Please try again later.") | Child auto-trigger |
| `GET /api/analytics/{analytics_id}` | 200 bare `AnalyticsReport`; 404 `NOT_FOUND` envelope when absent | Poll for completion; fetch report |
| `GET /api/analytics/student/{student_id}?limit=&offset=` | `List[AnalyticsReport]`; `limit` 1–50 (default 10), `offset` ≥ 0 (`:283-284`); filters Firestore on `overview.student_id` | Results lists (child + parent) |
| `GET /api/analytics/test/{test_id}?limit=` | **Always returns `[]`** — placeholder (`:380-395`) | Not consumed by UI; do not build against it |
| `GET /api/analytics/{analytics_id}/insights` | 200 `AnalyticsInsights`; 404 if report missing **or `ai_insights` is null** (`:454-460`) | Insights card data (optional enrichment) |
| `GET /api/analytics/{analytics_id}/weak-topics` | 200 `List[PriorityTopic]` filtered to `priority == "HIGH"` only (`:527-530`); 404 if report missing | Weak-topics list |

Not consumed: `GET /api/analytics/test/{test_id}` (placeholder returning `[]`).

## Dependencies

| Phase | What this phase needs |
|---|---|
| 02/04 | Project setup, Retrofit stack, base URL `http://10.0.2.2:8000`, error-envelope parsers, child and parent sessions (separate) |
| 03 | `AnalysisCard`, `ResultCard`, `StatusPill`, glass theme |
| 09 | `SubmissionResultScreen` → `AiProcessingStatusScreen` handoff with `test_id`, `student_id`, and the submitted answers map (persisted in DataStore until generation is triggered) |
| 05/07 | Dashboard navigation sources (parent results entry; child results entry) |

## Backend changes this phase depends on (phase-01 §11)

- **Gap #5** — analytics is synchronous under a 202/polling contract; recommended
  FastAPI `BackgroundTasks` keeping the same response shape.
- **Gap #4 (coupling)** — `generate` reads `diagnostic_tests/{test_id}` and requires a
  `questions` array (`analytics_service.py:401-421`); with tests not persisted,
  generate fails with a generic 500. Return a distinguishable error (e.g. 404
  `TEST_NOT_FOUND`) instead.
- **Gap #7 (adjacent)** — no auth/ownership checks on analytics endpoints
  (`verify_student_or_parent` is a placeholder returning `True`,
  `analytics_router.py:57-74`).
- New observations in this phase's gap log: poll-response has no status field;
  `GET /test/{test_id}` placeholder; phase-01 §8 wrapper-shape drift.

## Sources verified

`Backend/routers/analytics_router.py` (full), `Backend/models/analytics_models.py`
(full: `AnalyticsStatus`/`ChartType` `:31-46`, `QuestionAnswer` `:48-86`,
`AnalyticsRequest` `:89-146`, `AnalyticsOverview` `:149-241`, `SubjectAnalysis`
`:244-335`, `TopicAnalysis` `:338-422`, `AnalyticsInsights` `:425-498`,
`ChartData`/`VisualizationData` `:501-626`, `PriorityTopic` `:629-703`,
`AnalyticsReport` `:706-762`, `AnalyticsResponse` `:796-839`),
`Backend/services/analytics_service.py:219-257` (init + collections), `:261-391`
(pipeline), `:620-643` (id format + Firestore write), `:645-681` (get), `:683-730`
(student query), `Backend/core/errors.py:139-181` (envelopes). Live re-verification
commands in `expected-output.md`.

## File map

| File | Contents |
|---|---|
| `readme.md` | Scope, endpoints, dependencies, gap references (this file) |
| `instructions.md` | Ordered build steps with verify commands |
| `text.md` | Verified endpoint contracts, poll schedule, state machine, report field reference, screen specs, accessibility |
| `expected-output.md` | Checklist, live verification commands, demo scripts (current + backend-fixed), gap log |
