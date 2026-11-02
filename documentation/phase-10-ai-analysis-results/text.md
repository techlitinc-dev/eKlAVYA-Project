# Phase 10 — AI Analysis & Results (text.md)

Verified against commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`; **[live]** = observed
by booting the backend and calling the endpoint (2026-11-02), **[code]** = read from
source. Envelope conventions per phase-01 §4 and phase-09 `text.md` §1.

## 1. Endpoint contracts

### 1.1 `POST /api/analytics/generate` → 202 `AnalyticsResponse`

Request — `AnalyticsRequest` (`Backend/models/analytics_models.py:89-146`):

```json
{
  "test_id": "test_xyz789",
  "student_id": "child_abc123",
  "answers": { "1": "B", "2": "D", "3": "42.5" },
  "include_ai_insights": true,
  "use_cache": true
}
```

`answers` accepts `List[QuestionAnswer{question_number>0, answer, time_taken?}]` **or**
`Dict[int,str]` (`:121`); the router normalizes lists to a dict (`analytics_router.py:150-158`).
The child app always sends the dict form — the same map it submitted in phase-09.

Response — `AnalyticsResponse` (`analytics_models.py:796-829`):

```json
{
  "analytics_id": "analytics_test_xyz789_child_abc123_1699999999",
  "status": "pending",
  "message": "Analytics generation in progress",
  "report": null,
  "error": null,
  "progress": null
}
```

Facts you must encode:

- `status` is **always** `"pending"` in the router (`analytics_router.py:171-175`),
  even though the pipeline already ran synchronously (gap #5). Enum values
  (`analytics_models.py:31-37`): `pending|completed|failed|cached`; treat all except
  `pending` as terminal when reading `status` (only relevant if the backend starts
  returning the enum faithfully).
- `analytics_id` format: `analytics_{test_id}_{student_id}_{unix_seconds}`
  (`analytics_service.py:624-635`). The client must treat it as an opaque string.
- LRU cache: an identical `(test_id, student_id, answers)` re-generate returns the
  **same** `analytics_id` from an in-memory, per-process cache
  (`analytics_service.py:310-316,384-386`). Re-triggering after a lost poll is cheap
  and safe; it does not create a second report while the process lives. Cache is lost
  on backend restart.
- Errors: Pydantic validation → 422 `VALIDATION_ERROR` envelope
  (`core/errors.py:156-167`); any pipeline failure (including "test doc not found" —
  `analytics_service.py:401-421` raises `PipelineStepError`) → 500 v1 envelope with
  message `"Failed to generate analytics. Please try again later."`
  (`analytics_router.py:184-190`). **[live]** In a no-Firestore environment, even a
  valid body returns 500 `DefaultCredentialsError` because the service dependency
  constructs the Firestore client before body validation matters. The client cannot
  distinguish these today → generic failed-retry state, gap-logged.

### 1.2 `GET /api/analytics/{analytics_id}` → `AnalyticsReport` (bare)

**Poll response is the bare report** (`response_model=AnalyticsReport`,
`analytics_router.py:193-217`) — no wrapper:

```json
{
  "analytics_id": "analytics_...",
  "overview": { "...": "see §2" },
  "subject_analysis": [ "...": "see §2" ],
  "topic_analysis": [ "...": "see §2" ],
  "ai_insights": { "...": "see §2" },
  "priority_topics": [ "...": "see §2" ],
  "visualization_data": null,
  "metadata": { },
  "generated_at": "<iso>"
}
```

- `200` → report exists → terminal `COMPLETED` for the poller.
- `404` → `{"error":{"code":"NOT_FOUND","message":"Analytics report not found: <id>","request_id":"..."}}`
  (`analytics_router.py:246-251` on `AnalyticsNotFoundError`,
  `analytics_service.py:661-664`). The poller reads 404 as "still pending / not yet
  available" and continues until the overall timeout.
- `500` → transient failure; count it and continue (per-attempt retry semantics §3).

### 1.3 `GET /api/analytics/student/{student_id}?limit=10&offset=0` → `List[AnalyticsReport]`

Query params (`analytics_router.py:283-284`): `limit` 1–50 (default 10), `offset` ≥ 0
(applied in-memory after the Firestore query, `:315-318`). Service filters on
`overview.student_id` ordered by `generated_at` desc (`analytics_service.py:683-730`).
Errors → 500 envelope (invalid queries surface as 422 from FastAPI param validation).

### 1.4 `GET /api/analytics/test/{test_id}?limit=50` → `List[AnalyticsReport]`

**[code] Placeholder: always returns `[]`** (`analytics_router.py:380-395` — the
service call is commented out). Do not build any UI against this endpoint.

### 1.5 `GET /api/analytics/{analytics_id}/insights` → `AnalyticsInsights`

200 = `report.ai_insights` (`analytics_router.py:445-463`). 404 when the report is
missing (`:465-470`) **or when `ai_insights` is null** (`:454-460`, message "No AI
insights available for analytics: <id>") — the client treats endpoint-404 as
"insights not generated for this report" and hides the insights card rather than
showing an error.

### 1.6 `GET /api/analytics/{analytics_id}/weak-topics` → `List[PriorityTopic>`

Returns only entries with `priority == "HIGH"` (case-normalized,
`analytics_router.py:527-530`). 200 with `[]` is a valid outcome (no high-priority
weak topics). 404 when the report is missing (`:538-543`).

## 2. `AnalyticsReport` field reference (`analytics_models.py:706-762`)

The client renders **only** these fields, defensively (all lists may be empty;
every non-required field nullable):

- `analytics_id: String?`
- `overview: AnalyticsOverview` **(required)** — `test_id`, `student_id`, `exam_type`
  (string; model example uses `JEE_MAIN`; the enum is not enforced here), `total_score: Int`,
  `max_score: Int>0`, `percentage: Float 0–100` (rounded 2dp, `:215-221`), `percentile: Float? 0–100`,
  `accuracy: Float 0–100`, `time_taken: Int?` seconds, `total_questions: Int>0`,
  `attempted`, `correct`, `incorrect`, `unattempted` (`:149-241`)
- `subject_analysis: List<SubjectAnalysis>` **(required)** — `subject`, `score`, `max_score>0`,
  `percentage 0–100`, `accuracy 0–100`, `total_questions>0`, `attempted/correct/incorrect`,
  `strengths: List<String>`, `weaknesses: List<String>`, `ai_insights: String?`,
  `top_topics: List<String>` (max 3), `weak_topics: List<String>` (max 3) (`:244-335`)
- `topic_analysis: List<TopicAnalysis>` **(required)** — `topic`, `subject`, `accuracy 0–100`,
  `total_questions`, `correct`, `incorrect`, `priority ∈ HIGH|MEDIUM|LOW` (normalized
  uppercase by validator `:398-405`), `estimated_hours ≥ 0`, `recommendation`,
  `performance_level: strong|moderate|weak?`, `gap_from_benchmark: Float?` (`:338-422`)
- `ai_insights: AnalyticsInsights?` — `strengths: List<Dict>`, `weaknesses: List<Dict>`,
  `learning_patterns: List<String>`, `overall_assessment: String`, `study_strategy: String` (`:425-498`).
  Dict items are free-form (`topic/subject/accuracy/reason/recommendation/priority/estimated_study_hours`
  appear in the model example) — render `topic` + `reason` when present, else a JSON-naive fallback.
- `priority_topics: List<PriorityTopic>` (max 10) — `topic`, `subject`,
  `priority ∈ HIGH|MEDIUM|LOW`, `reason`, `estimated_hours ≥ 0`, `current_accuracy 0–100` **(required)**,
  `target_accuracy 0–100` **(required)**, `action_items: List<String>` (`:629-703`)
- `visualization_data: VisualizationData?` — optional chart bundles (`:559-626`); the
  app renders charts **only** paired with text values (see §6 accessibility) and
  tolerates `null`.
- `metadata: Map<String,Any>` (free-form; ignore unknown keys), `generated_at: DateTime`

## 3. Polling schedule (implement exactly)

- `POST /generate` returns → wait **1 s** → poll `GET /{analytics_id}`.
- Subsequent intervals double: **3 s, 6 s, 12 s, 24 s**, then cap at **30 s**.
- Overall timeout **5 minutes** from POST return → `FAILED_RETRYABLE`
  ("Analysis is taking too long — check your connection and retry").
- Per attempt: `200` → `COMPLETED`; `404` → continue; `5xx`/transport → count and
  continue (no special limit besides the overall timeout); `400/403` → `FAILED`
  (unrecoverable — show error + back).
- Cancel (user leaves the status screen): stop the loop client-side. Generation
  already completed server-side (gap #5), so re-entering later polls the same id and
  gets the report; or re-POST generate (cache hit, same `analytics_id`). Never block
  navigation on the loop.

## 4. State machine

```
IDLE ──(child submits test, phase-09 success)──▶ TRIGGERING ──202──▶ POLLING ──200──▶ COMPLETED ──▶ results screen
                                          │400/403            │5xx-forever/5min
                                          ▼                   ▼
                                        FAILED             FAILED_RETRYABLE ──retry──▶ POLLING (same id)
```

- `TRIGGERING`: `SubmissionResultScreen` "Continue" fires `generate` with the stored
  answers map. A `500` here → `FAILED_RETRYABLE` with "Retry analysis" (re-POST).
- `POLLING`: `AiProcessingStatusScreen` — animated indeterminate progress, `StatusPill`
  "pending" (phase-03), elapsed-time line, Cancel → dashboard.
- `COMPLETED`: report cached in memory + DataStore (`last_analytics_{test_id}`) so
  re-entry renders instantly.
- Parent flow has no `TRIGGERING`/`POLLING`: it lists `GET /student/{child_id}` and
  opens reports directly (`IDLE → COMPLETED` on selection). A missing report id → 404
  error state with back.

## 5. Trigger rules (implement exactly)

- **Child app**: on `SubmissionResultScreen` Continue, call `generate` once with
  `{test_id, student_id=child_id, answers=<the submitted map>, include_ai_insights:true,
  use_cache:true}`. Keep the submitted answers in DataStore until a terminal
  analytics state is reached (then they may be cleared; the submitted flag of
  phase-09 remains).
- **Parent app**: never calls `POST /generate`. If the child's analysis does not
  exist yet, the parent's list (`GET /student/{child_id}`) is simply empty →
  "No analyses yet" empty state with copy explaining the child completes a test first.
- No automatic retries of the POST beyond user-initiated Retry (the synchronous
  backend makes automatic re-POST pointless and could duplicate reports post-cache-expiry).

## 6. Screen specifications

Shared composables live in `ui/results/components/` so both viewers reuse them.

### 6.1 `AiProcessingStatusScreen` (child)

- Animated progress (phase-03 indeterminate spinner + subtle progress line),
  headline "Analyzing your performance", subtitle "This usually takes under a minute."
- `StatusPill("pending")`; on `FAILED_RETRYABLE` swap to error copy + Retry button;
  Cancel (text button) → child dashboard.
- Accessibility: progress region
  `semantics { contentDescription = "Analysis in progress" }`, no auto-announcing
  timer; state changes announced via `liveRegion`.

### 6.2 Results viewers: `ChildResultsScreen` / `ParentResultsViewerScreen`

Same composables, different nav sources and app bars (child: bottom nav to dashboard;
parent: opened from the phase-05 dashboard "Results" entry, back to it). Content:

1. **Overview card** — score ring (percentage), `total_score/max_score`, `accuracy`,
   `percentile` (hidden when null), attempted/correct/incorrect/unattempted row,
   `exam_type`, `generated_at` (localized date). Uses phase-03 `ResultCard`.
2. **Subject analysis** — one `AnalysisCard` per `subject_analysis` entry: subject,
   `score/max_score`, `percentage`, `accuracy` bar, `strengths` chips (positive
   color), `weaknesses` chips (warning color), `top_topics`/`weak_topics` (max 3 each,
   labeled), `ai_insights` paragraph when non-null.
3. **Topic analysis** — table rows: topic, subject, accuracy (with `performance_level`
   chip `strong|moderate|weak`), `priority` chip `HIGH|MEDIUM|LOW` (phase-03
   `StatusPill` colors: HIGH = error, MEDIUM = warning, LOW = neutral),
   `estimated_hours` ("≈12 h"), `recommendation` (expandable row).
4. **AI insights card** — `overall_assessment`, `study_strategy`, `strengths` and
   `weaknesses` as labeled bullet lists (`topic` — `reason` lines), `learning_patterns`
   bullets. Data source: `report.ai_insights` when present; else call
   `GET /{id}/insights` (404 → omit card silently).
5. **Priority / weak topics** — list from `GET /{id}/weak-topics` (HIGH only) rendered
   as `PriorityTopic` cards: topic, subject, `reason`, `estimated_hours`,
   current→target accuracy ("25% → 70%"), `action_items` checklist-style bullets;
   if empty, fallback to `report.priority_topics` sorted HIGH→MEDIUM→LOW with the
   same card (labeled "Priority topics").

### 6.3 Lists & empty/error states

- `ChildResultsScreen` entry also offers a history list (`GET /student/{child_id}`,
  limit 10): rows = `exam_type` + `generated_at` + `percentage`; opens detail view
  (the shared report composable). Empty → "No analyses yet — complete a test."
- Parent: `ParentResultsViewerScreen` opens on the same list for its `child_id`.
- Report-level errors: 404 → "Analysis not found" + back; 500/network → retry state.

### 6.4 Accessibility

- Every chart/graph derived from `visualization_data` must be paired with its text
  value (contentDescription stating the numbers) — a chart alone is never the sole
  carrier of a value. If `visualization_data` is null, the text layout stands alone.
- Accuracy bars: `contentDescription = "Physics accuracy 50 percent"`.
- Priority chips carry text labels (never color-only): contentDescription
  "Priority high".

## 7. Navigation contract

| From | To | Args |
|---|---|---|
| `SubmissionResultScreen` (phase-09) | `AiProcessingStatusScreen` | `test_id`, `student_id` |
| `AiProcessingStatusScreen` (COMPLETED) | `ChildResultsScreen` | `analytics_id` |
| Child dashboard → "My results" | `ChildResultsScreen` (list) | — (child session id) |
| Parent dashboard → child "Results" | `ParentResultsViewerScreen` | `child_id` |
| Results list row tap | report detail (shared composable) | `analytics_id` |

## 8. DataStore keys (child session)

- `submitted_answers_{test_id}` — the exact answers map, retained until terminal
  analytics state (phase-09 writes it; this phase consumes it).
- `last_analytics_{test_id}` — `analytics_id` for instant re-entry.
