# Phase 10 — Expected Output & Sign-off

## Deliverables

1. `data/analytics/` — models, `AnalyticsService`, `AnalyticsRepository`, `PollScheduler`.
2. `ui/results/` — `AiProcessingStatusScreen`, `ChildResultsScreen`,
   `ParentResultsViewerScreen`, shared `ui/results/components/`, `AiAnalysisViewModel`.
3. Routes: `ai_status/{test_id}/{student_id}`, `child_results`,
   `parent_results/{child_id}`, `analysis_detail/{analytics_id}`.
4. Child-session DataStore: `submitted_answers_{test_id}`, `last_analytics_{test_id}`.

## Verification checklist

- [ ] `./gradlew testDebugUnitTest` green (ModelsTest, AnalyticsRepositoryTest,
      PollSchedulerTest, VM tests).
- [ ] `./gradlew :app:assembleDebug` succeeds.
- [ ] Poll delay sequence exactly 1,3,6,12,24,30,30,… with 5-minute overall timeout.
- [ ] Child auto-trigger fires only after a successful phase-09 submission; parent
      app contains no `generate` call (grep the codebase for proof).
- [ ] Insights card silently omitted on 404/`null`; weak-topics `[]` handled.
- [ ] No consumption of `GET /api/analytics/test/{test_id}`; no invented fields.
- [ ] Gap log filled with anything observed beyond listed items.

## Live backend verification (re-checkable claims)

Boot per `instructions.md` §0 (no Firebase credentials), then:

```bash
# All analytics endpoints 500 with DefaultCredentialsError (service dependency
# constructs a Firestore client before the handler runs) — verified 2026-11-02:
curl -s -w "\n-> %{http_code}\n" -X POST http://localhost:8000/api/analytics/generate \
  -H "Content-Type: application/json" \
  -d '{"test_id":"test_x","student_id":"child_1","answers":{"1":"B"},"include_ai_insights":true,"use_cache":true}'
curl -s -w "\n-> %{http_code}\n" http://localhost:8000/api/analytics/abc
curl -s -w "\n-> %{http_code}\n" "http://localhost:8000/api/analytics/student/child_1?limit=10&offset=0"
curl -s -w "\n-> %{http_code}\n" "http://localhost:8000/api/analytics/test/test_x?limit=50"
curl -s -w "\n-> %{http_code}\n" http://localhost:8000/api/analytics/abc/insights
curl -s -w "\n-> %{http_code}\n" http://localhost:8000/api/analytics/abc/weak-topics
```

Expected (verified): `500 {"success":false,"error":{"type":"DefaultCredentialsError","message":"Your default credentials were not found...","detail":"..."}}`
for every call — including a body missing required fields (validation never runs
first). In a working-Firestore environment the failure/success mapping per
`text.md` §1 applies instead.

## Demo scripts

### Path A — current backend (graceful failure)

1. Boot stock backend; install app; child login; complete/tap through to
   `SubmissionResultScreen` (or reach it in the phase-09 gated flow) → Continue.
2. `TRIGGERING` → POST returns 500 `DefaultCredentialsError` → `FAILED_RETRYABLE`
   screen: "Analysis could not be started — retry?" with Retry and Back.
3. Retry → same (idempotent, no crash). Parent app: dashboard → Results →
   "No analyses yet" (list endpoint also 500s → show the generic load-error state with
   retry, per repository mapping).

### Path B — backend-fixed walkthrough (gap #4/#5 environment)

Preconditions: `diagnostic_tests/{test_id}` exists with questions (gap #4 fixed);
Firestore reachable; `GOOGLE_API_KEY` set (or provider mocked).

1. Child submits test (phase-09 Path B) → Continue → `AiProcessingStatusScreen`
   (pending pill, animation).
2. POST returns 202 with `analytics_id`; first poll (~1 s) returns `200` with the
   full report (pipeline is synchronous — gap #5) → `ChildResultsScreen` renders:
   score ring, per-subject `AnalysisCard`s, topic table with priority chips,
   AI insights card, weak-topics cards (HIGH only) with action items.
3. Kill app; reopen results → instant render from `last_analytics_{test_id}`.
4. Parent app: dashboard → child Results → same report via `ParentResultsViewerScreen`;
   verify the parent build contains no analytics `generate` call.
5. Re-POST generate with identical answers → cache hit returns the same
   `analytics_id` (observable in backend logs; `analytics_service.py:310-316`).

## Gap log

| # | Gap (phase-01 §11 ref) | Evidence | Client handling | Backend must add |
|---|---|---|---|---|
| 1 | #5 — synchronous pipeline under 202 contract | `analytics_service.py:261-391` runs inline; router hardcodes `status:"pending"` (`analytics_router.py:171-175`) | Full poll implementation stays (contract-safe); first poll usually returns the report | Move pipeline to `BackgroundTasks`, same response shape |
| 2 | #4 (coupling) — generate requires persisted test + questions; failure is an indistinguishable 500 | `analytics_service.py:401-421`; router `:184-190` | Generic failed-retry state | Persist tests+questions (gap #4); return 404 `TEST_NOT_FOUND` / 422 with detail |
| 3 | #7-adjacent — no auth on analytics endpoints | `analytics_router.py:57-74` placeholder; dependency unused (`:40`) | Send Bearer anyway; note scoping cannot be enforced client-side | Real JWT + ownership checks (gap #7) |
| 4 | New — poll response carries no `status` field (bare `AnalyticsReport`; `AnalyticsReport` lacks status) | `analytics_router.py:193-217`; `analytics_models.py:706-762` | Poll maps HTTP codes: 200 = completed, 404 = pending, 5xx = retry | (Optional) include `status` in the report or a poll wrapper. **Phase-01 §7.E/§8 corrected 2026-11-02 to document the bare-report shape.** |
| 5 | New — `GET /api/analytics/test/{test_id}` is a placeholder returning `[]` | `analytics_router.py:380-395` | Endpoint not consumed | Implement service query or remove the endpoint |
| 6 | New — insights endpoint 404 conflates "report missing" and "insights not generated" | `analytics_router.py:454-460` | 404 → hide insights card | Distinct code (e.g. 204 or `INSIGHTS_UNAVAILABLE`) |
| 7 | New — `weak-topics` silently drops MEDIUM/LOW | `analytics_router.py:527-530` | Render report `priority_topics` (max 10) as labeled fallback list | Return all priorities or document HIGH-only contract |
| 8 | #13 — stock `.env` breaks boot (shared with phase-09/11) | `utils/firebase_config.py:28` + `.env.example:244` → `vector_search_router.py:42` | Boot workaround documented | Fix conditional import; tracked as phase-01 §11 gap #13 |

## Sign-off rule

All checkboxes pass; both demo paths recorded; any new drift appended here with
`path:line` evidence — fix documentation, never the backend.
