# Phase 11 — Personalized Schedule (Android)

**Purpose:** The parent generates a personalized study schedule from the child's AI
analysis (phase-10), and both parent and child view it — the child also marks day
progress. Phase-01 §7.F: `POST /api/schedule/generate` is **synchronous** (full
`Schedule` in a 201 response) after a long pipeline; the client still wraps the call
in a job-style UI state because generation can take tens of seconds.

**Verified backend reality (commit `d8ab491`, re-verified live 2026-11-02):**

- **Auth is real and mandatory here.** The schedule router uses
  `middleware/auth_middleware.py:136 get_current_user` — JWT verification **plus** a
  Firestore `sessions` revocation check that **fails closed** (on any Firestore error,
  the token is treated as revoked). Verified live:
  - No `Authorization` header → `401 {"error":{"code":"VALIDATION_ERROR","message":"Authorization header required",...}}`.
  - Valid Bearer token without Firestore → `401 {"error":{"code":"VALIDATION_ERROR","message":"Token has been revoked. Please login again.",...}}`.
  - The app must send the **parent** token for parent-triggered calls and the
    **child** token for child progress updates.
- **Gemini is required to even construct the service.** `ScheduleService()` and
  `AdaptiveScheduler()` build `GeminiSchedulerService` in `__init__`
  (`Backend/services/schedule_service.py:350-363`); without `GOOGLE_API_KEY` every
  schedule call except the progress ones fails first with `500
  {"success":false,"error":{"type":"ValueError","message":"Google API key not provided..."}}`
  (verified live) because the dependency is instantiated before auth runs.
- **Gap #6 blocks end-to-end generation.** `schedule_service.py:84-85` reads
  Firestore collections `analytics` and `students`, but writers store
  `analytics_reports` (`analytics_service.py:254`) and `children`
  (`child_service.py:133-179`). Generating from a real analysis therefore raises
  `AnalyticsNotFoundError`/`StudentNotFoundError` → 404 with detail `"Analytics not
  found: <id>"` / `"Student not found: <id>"` (`schedule_router.py:238-250`). This is
  **BACKEND CHANGE REQUIRED (gap #6)**; the client surfaces a graceful "Schedule
  unavailable" state and this phase's demo script uses backend-fixed steps.
- Two new implementation bugs verified by code reading (in the gap log):
  `GET /api/schedule/progress/today` always crashes with `AttributeError` when
  today's day has topics (`topic.subject.value` on a `str` field and a nonexistent
  `topic.difficulty`, `progress_tracker.py` today-tasks builder), and `PUT` with the
  router's own example `status:"paused"` can never work (`ScheduleStatus` has no
  `paused` member, `schedule_models.py:50-55`).

## Scope

In scope:

- `ScheduleGenerateScreen` (parent: analysis picker + hours stepper + exam date + confirm)
- `ChildScheduleScreen` / `ParentScheduleViewerScreen` (shared day list, today highlighted, week strip, day-type filters)
- `DayDetailScreen` (topics, subtopics, resources, goals, milestones; child-only "mark day complete" → `POST /progress/update`)
- `ScheduleHistoryScreen`, `RegenerateDialog`
- `ScheduleRepository` + models; job-style generation state machine
- Trigger UX: **parent triggers generation** from the results screen (needs
  `analytics_id` from phase-10, `exam_date` from phase-08 exam selection,
  `daily_study_hours` picker 2–8); **child views read-only** plus day completion.

Out of scope:

- Analytics itself (phase-10); payments; the superadmin panel (phase-12).

## Endpoints consumed (prefix `/api/schedule`, `Backend/routers/schedule_router.py:65-68`)

| Endpoint | Behavior (verified) | Use |
|---|---|---|
| `POST /api/schedule/generate` | 201 `Schedule`, synchronous; 404 on gap #6; JWT | Parent generation |
| `GET /api/schedule/{schedule_id}` | 200 `Schedule`; 404 envelope | Detail fetch |
| `GET /api/schedule/student/{student_id}?status_filter=active` | 200 `Schedule` **or JSON `null`** | Current-schedule lookup (both apps) |
| `GET /api/schedule/student/{student_id}/history?limit=10` | 200 `List<Schedule>` newest first | History |
| `POST /api/schedule/{schedule_id}/regenerate` | 200 `Schedule`; body `{current_day>0}` | RegenerateDialog |
| `PUT /api/schedule/{schedule_id}` | 200 `Schedule`; body `{updates:{}}` | Status/hours adjustments (defensive scope) |
| `POST /api/schedule/progress/update` | 200 `ProgressUpdate`; 404 on missing schedule/day | Child day completion |
| `GET /api/schedule/progress/{schedule_id}` | 200 summary `Dict` | Progress header |
| `GET /api/schedule/progress/today?schedule_id=` | 200 `List<Dict>` — **crashes 500 when today's day has topics (new gap)** | Non-blocking "today" enrichment |

Not consumed: `DELETE /api/schedule/{schedule_id}` (soft-delete; no app UI — internal).

## Dependencies

| Phase | What this phase needs |
|---|---|
| 02/04 | Project setup, Retrofit stack, base URL, envelope parsers, parent + child sessions |
| 03 | `ScheduleCard`, `StatusPill`, `GlassDialog`, glass theme |
| 08 | `exam_date` (parent selected it; `ExamSelectionResponse.exam_date`) |
| 10 | `analytics_id` (generate response or `GET /api/analytics/student/{child_id}` list) and the parent results screen as the generation entry point |

## Backend changes this phase depends on (phase-01 §11)

- **Gap #6 (prominent)** — `schedule_service.py:84-85` must read `analytics_reports`/`children` (or aliases); `parent_dashboard_service.py` has the same mismatch.
- **Gap #7** — no ownership distinction between parent/child on schedule endpoints; client must scope to its own ids.
- **Gap #5-adjacent / new** — `progress/today` AttributeError crash; `PUT` example status `paused` invalid; `DELETE`-as-soft-delete semantics.

## Sources verified

`Backend/routers/schedule_router.py` (full), `Backend/models/schedule_models.py`
(full: enums `:28-70`, `ScheduleRequest` `:72-161`, `TopicPriority` `:164-255`,
`DailyTopic` `:258-330`, `ScheduleDay` `:333-438`, `Schedule` `:441-567`,
`ProgressUpdate` `:570-682`), `Backend/services/schedule_service.py:84-85` (collection
names), `:348-420` (init + validation), `:422-630` (pipeline), `:640+` (get/update),
`:789-847` (update), `:848+` (soft delete), `Backend/services/progress_tracker.py`
(subcollection writes `:134-138`, summary keys, today-tasks builder),
`Backend/middleware/auth_middleware.py:136-236` (fail-closed revocation). Live
verification commands in `expected-output.md`.

## File map

| File | Contents |
|---|---|
| `readme.md` | Scope, endpoints, dependencies, gap references (this file) |
| `instructions.md` | Ordered build steps with verify commands |
| `text.md` | Verified contracts, eligibility of inputs, state machines, screen specs, accessibility |
| `expected-output.md` | Checklist, live verification, demo script (backend-fixed), gap log |
