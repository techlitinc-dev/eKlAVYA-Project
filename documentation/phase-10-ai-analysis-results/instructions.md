# Phase 10 — Instructions

Execute in order; each step has a **Verify** gate. Android code only, package
`ai.eklavya.app`; never modify the backend. Fixed conventions: Compose + Hilt +
Retrofit + Navigation Compose, base URL `http://10.0.2.2:8000`, phase-03 components,
separate child/parent sessions, `child_id` used as `student_id` (phase-01 §7.H).
Send `Authorization: Bearer <token>` on every call even though analytics currently
ignores it (gap #7-adjacent; required in production).

Guardrails: never invent fields/endpoints; where the backend blocks behavior, render
the documented empty/error state and log the gap. Do not build against
`GET /api/analytics/test/{test_id}` (placeholder returning `[]`).

## 0. Boot note

Same as phase-09 `instructions.md` §0: remove/neutralize `Backend/.env`
(`TESTING_MODE=true` at `.env.example:244` breaks boot via
`utils/firebase_config.py:28` → `vector_search_router.py:42`), then
`python3 -m uvicorn main:app --port 8000 &` and wait for `/health`.

## 1. Models

1.1 Create `Android_App/app/src/main/java/ai/eklavya/app/data/analytics/Models.kt`:
`AnalyticsRequest`, `AnalyticsResponse`, `AnalyticsReport`, `AnalyticsOverview`,
`SubjectAnalysis`, `TopicAnalysis`, `AnalyticsInsights`, `PriorityTopic`,
`VisualizationData` (keep as flexible structure or skip strict parse — treat unknown
keys as ignored), matching `text.md` §1–§2 exactly. Enums: `Priority { HIGH, MEDIUM, LOW }`,
`PerformanceLevel { STRONG, MODERATE, WEAK }` (tolerant parse: unknown → null).

**Verify:** `ModelsTest` parses the report JSON embedded in
`Backend/models/analytics_models.py:764-793` (extended with one full
subject/topic/priority sample) asserting required vs nullable fields; unknown fields
ignored. `./gradlew testDebugUnitTest --tests "ai.eklavya.app.data.analytics.ModelsTest"`.

## 2. Service + repository

2.1 `AnalyticsService` (`data/analytics/AnalyticsService.kt`): the five consumed
endpoints (skip `/test/{test_id}`), with `limit`/`offset` query params on the student
list (defaults 10/0, max 50).

2.2 `AnalyticsRepository` (`data/analytics/AnalyticsRepository.kt`):
`generate(request) → AnalyticsResponse`;
`poll(analyticsId) → sealed { Report, NotFound, Error }` distinguishing 200/404/other;
`studentReports(studentId, limit, offset)`; `insights(id)` mapping 404 → `NoInsights`;
`weakTopics(id)`.

**Verify:** MockWebServer tests: 202 parse; poll 200/404/500 mapping; insights 404 →
`NoInsights`; weak-topics 200 `[]` is a valid empty list. `./gradlew testDebugUnitTest --tests "...AnalyticsRepositoryTest"`.

## 3. Poll engine

3.1 Implement `PollScheduler` exactly per `text.md` §3: first poll at 1 s, then
3/6/12/24 s, cap 30 s, overall 5 min → `FAILED_RETRYABLE`; 400/403 → `FAILED`;
cancel stops the coroutine cleanly.

**Verify:** `PollSchedulerTest` with a fake clock/ticker: assert the exact delay
sequence (1,3,6,12,24,30,30,...), timeout at 5 min, 404-continue ×N then success,
cancel emits nothing further. `./gradlew testDebugUnitTest --tests "...PollSchedulerTest"`.

## 4. ViewModel + status screen (child)

4.1 `AiAnalysisViewModel` (`ui/results/AiAnalysisViewModel.kt`) implementing the
`text.md` §4 state machine; auto-trigger entry point
`start(testId, studentId, answers)` (the child path; parent never calls it).

4.2 `AiProcessingStatusScreen` per `text.md` §6.1 with phase-03 `StatusPill`
("pending"), animated progress, Cancel → child dashboard.

**Verify:** `./gradlew :app:compileDebugKotlin`; VM test: 202→poll success →
`COMPLETED`; poll 500×until-timeout → `FAILED_RETRYABLE`; 403 → `FAILED`; cancel
cancels the job (no leak — assert Job cancelled).

## 5. Shared results UI

5.1 Create `ui/results/components/`: `OverviewCard`, `SubjectAnalysisList`,
`TopicAnalysisTable`, `AiInsightsCard`, `PriorityTopicsList` per `text.md` §6.2 —
render strictly from §2 fields, defensive on nulls/empties, charts paired with text.

5.2 Create `ChildResultsScreen` (list + detail) and `ParentResultsViewerScreen`
reusing 5.1; history via `studentReports` with `limit=10`; empty/error states per
§6.3. Insights enrichment: try `report.ai_insights` first, else `insights(id)`,
404 → omit card.

**Verify:** `./gradlew :app:compileDebugKotlin`; screenshot/compose tests (phase-03
test stack) for: full report render; report with `ai_insights=null` and insights-404
(hides card); `priority_topics=[]` and weak-topics-`[]` (fallback/empty copy);
`percentile=null` (hidden).

## 6. Navigation + wiring

6.1 Register routes: `ai_status/{test_id}/{student_id}`, `child_results`,
`parent_results/{child_id}`, `analysis_detail/{analytics_id}` in the respective
NavHosts (phase-05 parent, phase-07 child). Wire phase-09 `SubmissionResultScreen`
"Continue" → `ai_status`. Parent dashboard "Results" → `parent_results/{child_id}`.

**Verify:** `./gradlew :app:assembleDebug`; manual Path A demo (below) shows the
failed-retry state without crash (stock backend: generate returns 500
`DefaultCredentialsError`).

## 7. Final sweep

Re-read written files; confirm no `/test/{test_id}` usage, no invented fields, Bearer
header attached via phase-04 interceptor, and fill `expected-output.md`.
