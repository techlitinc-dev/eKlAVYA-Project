# Phase 11 — Personalized Schedule (text.md)

Verified against commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`; **[live]** =
observed by booting the backend and calling the endpoint (2026-11-02), **[code]** =
read from source. Envelopes per phase-01 §4.

## 1. Auth model for this router (unlike the others)

Every endpoint depends on `middleware/auth_middleware.py:136 get_current_user`:

1. Missing/invalid `Authorization` → 401 `"Authorization header required"` /
   `"Invalid token. Please login again."` (v1 envelope, code `VALIDATION_ERROR`).
2. Cryptographically valid token → `is_token_revoked` queries Firestore `sessions`;
   **any error (including no Firestore) is treated as revoked** → 401 `"Token has been
   revoked. Please login again."` [live]. A real, unrevoked session is required even
   in development.
3. Dependency order matters: `service`/`scheduler`/`tracker` dependencies are
   resolved **before** `current_user` in the handler signatures, so without
   `GOOGLE_API_KEY` the service endpoints fail with a 500 `ValueError` before auth is
   even checked [live]; `ProgressTracker` needs no Gemini, so progress endpoints fail
   straight at 401 [live].

**Client rules:** attach the correct role's token (parent token for generate/
regenerate/update/history; child token for progress update — the child "completes
days" flow). Surface 401 as "Session expired — log in again" (auth refresh is
phase-04; on refresh failure → logout). Never retry 401s silently.

## 2. Endpoint contracts

### 2.1 `POST /api/schedule/generate` → 201 `Schedule` (synchronous)

Request — `ScheduleRequest` (`Backend/models/schedule_models.py:72-161`):

```json
{
  "student_id": "child_abc123",
  "analytics_id": "analytics_test_xyz789_child_abc123_1699999999",
  "exam_type": "JEE_MAIN",
  "exam_date": "2027-04-15",
  "daily_study_hours": 4.0,
  "preferences": null
}
```

Validation (model validators `:127-145` and service `validate_schedule_request`
`schedule_service.py:376-420`): `exam_type ∈ JEE_MAIN|JEE_ADVANCED|NEET` (**no
JEE_COMBO** — exam selection in phase-08 allows JEE_COMBO; the client maps JEE_COMBO
to `JEE_MAIN` for schedule purposes and notes the derivation); `exam_date` must be a
**future** date (`> date.today()`, local); `daily_study_hours` float **2–8**,
default 4.0, rounded to 1dp; `analytics_id` and `student_id` non-empty;
`preferences` optional free-form dict (send `null`). Violations → 422
`VALIDATION_ERROR` envelope with per-field errors.

Pipeline (synchronous, `schedule_service.py:422-630`): validate → fetch analytics →
fetch student profile → syllabus weightages → `PriorityCalculator` → time
feasibility → Gemini (`gemini_scheduler_service.py:140`, `gemini-2.5-flash-lite`) →
validate/parse → save to `schedules` (`schedule_id` =
`schedule_{student_id}_{analytics_id}_{timestamp}`, `gemini_scheduler_service.py:450`).
Response: complete `Schedule`, HTTP **201**.

**Client call policy:** wrap in a job-style UI state (`GENERATING`); client timeout
**60 s**; on timeout show a retry prompt — re-calling `generate` is the prescribed
recovery (the backend has no idempotency key; each call creates a new schedule
**but** see 2.3 for the duplicate-avoidance pre-check). On `404` with detail
`"Analytics not found: ..."` or `"Student not found: ..."` → **gap #6** →
"Schedule unavailable" state (never a fake schedule). On 422 → field errors back to
the form. On 500/timeout → retry.

### 2.2 `GET /api/schedule/{schedule_id}` → 200 `Schedule`; 404 envelope

### 2.3 `GET /api/schedule/student/{student_id}?status_filter=active` → `Schedule | null`

Returns the first matching schedule (newest `generated_date` first) **or JSON
`null`** with 200 (`schedule_router.py:349-388`). `status_filter` default `active`;
allowed values per service query: `active|completed|abandoned` (`ScheduleStatus`,
`schedule_models.py:50-55`). **Duplicate-avoidance pre-check:** before generating, the
parent screen calls this; if a `Schedule` is returned, offer "View existing schedule"
instead of generating a second one (legitimate use of the contract; not a workaround).

### 2.4 `GET /api/schedule/student/{student_id}/history?limit=10` → `List<Schedule>`

`limit` 1–100, default 10 (`schedule_router.py:412`); newest first. May legitimately
return `[]`.

### 2.5 `POST /api/schedule/{schedule_id}/regenerate` → 200 `Schedule`

Body `RegenerateRequest` (`schedule_router.py:74-87`): `{"current_day": 15}` —
`current_day > 0` (422 otherwise). Adaptive regenerate fetches schedule + progress,
keeps completed days, regenerates the remainder (`Backend/services/adaptive_scheduler.py`).
404 when schedule missing. **Client:** `RegenerateDialog` collects `current_day`
(default = first incomplete day), explains consequences (days ≥ current_day are
replaced; completed progress is kept), fires the call, replaces the in-memory
schedule on success.

### 2.6 `PUT /api/schedule/{schedule_id}` → 200 `Schedule`

Body `UpdateScheduleRequest` (`schedule_router.py:90-105`): `{"updates": {...}}`.
Service semantics (`schedule_service.py:789-847`): merge keys into the stored doc,
re-validate as `Schedule`, save. Therefore only updates that keep the model valid
work. **Supported client updates:** `status ∈ active|completed|abandoned` and
`daily_study_hours` 2–8. Do **not** send `status:"paused"` (the router's own example
is invalid — no such enum member; the re-validation throws → 500 envelope) or
`exam_date` changes (route to regenerate instead). Unknown keys are ignored by the
model (Pydantic default) — don't rely on this.

### 2.7 `DELETE /api/schedule/{schedule_id}` (not consumed)

Soft delete: sets `status:"abandoned"` (`schedule_service.py:848-880`). No app UI
consumes it; documented for completeness.

### 2.8 `POST /api/schedule/progress/update` → 200 `ProgressUpdate`

Body — `ProgressUpdate` (`schedule_models.py:570-682`):

```json
{
  "schedule_id": "schedule_child_abc123_...",
  "day_number": 3,
  "update_date": "2026-11-02",
  "status": "partial",
  "topics_completed": [
    { "topic": "Thermodynamics", "time_spent": 2.5, "completion_percentage": 60.0, "notes": "Need more practice on entropy" }
  ],
  "total_time_spent": 4.0,
  "completion_percentage": 75.0,
  "next_day_adjustments": ["Add 1 hour for Thermodynamics Second Law"]
}
```

`status ∈ completed|partial|skipped` (`DayStatus`, `schedule_models.py:57-61`);
`day_number > 0`; `update_date` local `YYYY-MM-DD`; `topics_completed` free-form
dicts (render keys `topic`, `time_spent`, `completion_percentage`, `notes`);
`total_time_spent` hours ≥ 0; `completion_percentage` 0–100. Service writes
`schedules/{schedule_id}/progress/{day_number}` (`progress_tracker.py:134-138`),
updates the day's completion, and evaluates reschedule triggers (2 missed days,
topic overrun, 3+ days behind, practice accuracy < 50% — `schedule_router.py:694-699`).
404 on missing schedule/day (`DayNotFoundError`, `schedule_router.py:751-756`).
Response echoes the `ProgressUpdate`.

### 2.9 `GET /api/schedule/progress/{schedule_id}` → summary `Dict`

Free-form dict (verified keys, `progress_tracker.py`): `schedule_id`, `total_days`,
`days_completed`, `days_remaining`, `total_topics`, `topics_completed`,
`topics_remaining`, `total_hours_studied`, `completion_percentage`, `days_behind`,
`days_ahead`, `average_daily_study_time`, `current_study_streak`, `status`,
`exam_date` (ISO), `days_until_exam`. Render known keys defensively; ignore unknowns.
404 when schedule missing.

### 2.10 `GET /api/schedule/progress/today?schedule_id=` → `List<Dict>`

`schedule_id` required (422 without). Promised fields (router docstring
`schedule_router.py:836-862`): `topic`, `subject`, `estimated_hours`, `subtopics`,
`resources`, `goals`, `priority`, `difficulty`. **Implementation defect [code]:**
the builder accesses `topic.subject.value` (DailyTopic.subject is a plain `str`,
`schedule_models.py:286`) and `topic.difficulty` (DailyTopic has **no** `difficulty`
field) — so whenever today's date matches a scheduled day with topics, the endpoint
raises `AttributeError` → 500. When no day matches today it returns `[]`.
**Client handling:** non-blocking. The primary "today" rendering derives from the
already-fetched `Schedule` (day whose `schedule_date` equals today; else the next
incomplete day) — local derivation from contract data, not fabricated data. The
endpoint result is used only as enrichment when it returns 200; 500/404 → silently
fall back to the local derivation and log the gap.

## 3. `Schedule` model contract (`schedule_models.py:441-567`)

```json
{
  "schedule_id": "schedule_child_abc123_analytics_..._1699999999",
  "student_id": "child_abc123",
  "analytics_id": "analytics_...",
  "exam_type": "JEE_MAIN",
  "exam_date": "2027-04-15",
  "generated_date": "<iso>",
  "total_days": 120,
  "daily_study_hours": 4.0,
  "status": "active",
  "days": [
    {
      "day_number": 1,
      "schedule_date": "2026-11-03",
      "subjects": ["Physics"],
      "topics": [
        {
          "topic": "Thermodynamics",
          "subject": "Physics",
          "priority": "high",
          "estimated_hours": 2.0,
          "subtopics": ["First Law", "Second Law"],
          "resources": ["NCERT Chapter 12"],
          "goals": ["Understand first law applications"]
        }
      ],
      "total_hours": 4.0,
      "milestones": ["Complete Thermodynamics fundamentals"],
      "completed": false,
      "completion_percentage": 0.0
    }
  ],
  "revision_days": [110, 111, 112],
  "practice_test_days": [113, 114],
  "buffer_days": [30, 60],
  "priority_topics": [
    {
      "topic": "Thermodynamics", "subject": "Physics",
      "priority_score": 300.0, "current_accuracy": 25.0, "target_accuracy": 70.0,
      "weightage": 4.0, "estimated_hours": 12.0, "difficulty": "medium",
      "priority_level": "critical"
    }
  ]
}
```

Field rules the client relies on: `Schedule.status ∈ active|completed|abandoned`
(`:50-55`); `daily_study_hours` 2–8 (`:500-504`); `exam_date` re-validated as future
even on reads (`:531-539`) — a schedule whose exam date passes becomes unreadable
(500 on re-validation; `get_schedule` catches parse failures → `ScheduleServiceError`
→ 500 envelope) — acceptable, noted; `ScheduleDay.day_number>0`, `completion_percentage`
0–100, `completed: bool` (`:333-438`); `DailyTopic.priority ∈ critical|high|medium|low`
(`:42-47`, `:285-304`); `TopicPriority.priority_level` same enum plus score/accuracy
fields (`:164-255`). Date fields serialize as `YYYY-MM-DD`; `generated_date` as ISO.

Enums (`schedule_models.py:28-70`): `ExamType {JEE_MAIN, JEE_ADVANCED, NEET}`,
`DifficultyLevel {easy, medium, hard}`, `PriorityLevel {critical, high, medium, low}`,
`ScheduleStatus {active, completed, abandoned}`, `DayStatus {completed, partial, skipped}`,
`RescheduleReason {missed_sessions, topic_overrun, low_performance, student_request}`.

## 4. State machines

### 4.1 Generation (parent)

```
FORM ──submit──▶ CHECKING_EXISTING ──active schedule──▶ VIEW_EXISTING (dialog: view / generate anyway)
     │                                    └─null──▶ GENERATING ──201──▶ ACTIVE(schedule loaded)
     │                                                   │404 gap#6         │
     │                                                   ▼                  ▼
     │                                             UNAVAILABLE          load error → retry
     │                                            ("Schedule unavailable)
     └── 422 ──▶ field errors on form; 500/timeout(60s) ──▶ RETRY prompt (re-call generate)
```

`generate anyway` bypasses the pre-check only on explicit parent confirmation.

### 4.2 Day completion (child)

```
DayDetail ──"Mark day complete"──▶ CompletionSheet (per-topic checklist, time spent, status chips completed/partial/skipped)
   ──confirm──▶ SUBMITTING_PROGRESS ──200──▶ refresh day (completion_percentage, completed) + summary header
                              │404 (day/schedule missing) → snackbar "Day not found" + refresh schedule
                              │5xx/network → retry sheet (body preserved)
```

## 5. Screen specifications

Routes: `schedule_generate/{child_id}` (parent), `child_schedule` (child),
`parent_schedule/{child_id}` (parent), `day_detail/{day_number}`,
`schedule_history/{child_id}`.

### 5.1 `ScheduleGenerateScreen` (parent)

- Prefetch: `GET /api/analytics/student/{child_id}?limit=10` → analysis picker
  (rows: `exam_type` + `generated_at` from `overview`, `percentage`); the chosen
  report's `analytics_id` seeds the form. `exam_date` prefilled from phase-08
  selection (editable date picker, must be future). `daily_study_hours` stepper 2–8
  (default 4.0, 0.5 steps) with live "≈ N hours/week" hint. `exam_type` derived from
  the selected analysis' `overview.exam_type` when it is one of JEE_MAIN/JEE_ADVANCED/
  NEET; if the source was JEE_COMBO, use JEE_MAIN and show the derivation note.
- Confirm → pre-check (2.3) → `GENERATING` (job-style: indeterminate progress, copy
  "Building your child's study plan — this can take up to a minute", non-cancellable
  but back-safe) → success → `ParentScheduleViewerScreen`; gap-#6 404 →
  "Schedule unavailable — backend change pending" state with details collapsible
  (shows the endpoint's `message`) and Retry.
- Accessibility: stepper buttons are ≥48 logical pixels with Flutter semantics labels such as
  "Increase daily study hours"; progress region is announced once.

### 5.2 `ChildScheduleScreen` / `ParentScheduleViewerScreen` (shared widgets)

- Load order: `GET /student/{student_id}?status_filter=active` → null → empty state
  ("No active schedule — your parent can generate one from your latest analysis").
  Non-null → `Schedule` cached in memory + `shared_preferences` `last_schedule_{student_id}`.
- Header (from progress summary 2.9, defensive): completion ring, `days_completed/
  total_days`, `days_until_exam`, streak; fallback to schedule-local computation
  (count `completed` days) if the summary call fails.
- Day list: one phase-03 `ScheduleCard` per day: date, `subjects`, topic titles,
  `total_hours`, `StatusPill` for day type (`revision`/`practice`/`buffer` when
  `day_number ∈ revision_days|practice_test_days|buffer_days`, else default), and
  completion state (check + `completion_percentage`). Today highlighted (ring +
  "Today" label; today = local date == `schedule_date`; else next incomplete day
  labeled "Up next").
- Week strip: horizontal 7-day pager of `schedule_date`s; tap scrolls the list.
- Filter chips: All / Revision / Practice tests / Buffer (uses the three day-number
  lists).
- Pull-to-refresh re-fetches schedule + summary. 401 → session-expired state
  (phase-04 refresh, else logout).

### 5.3 `DayDetailScreen`

- Shows one `ScheduleDay`: header (date, type pill, `total_hours`), topics list —
  per `DailyTopic`: topic, subject, priority `StatusPill` (critical=error,
  high=warning, medium=neutral, low=outline), `estimated_hours`, expandable
  `subtopics`, `resources`, `goals`; then `milestones` section.
- Child only: "Mark day complete" → 4.2 completion sheet. Parent sees a read-only
  note ("Progress is marked by your child").
- After a 200 progress update, locally update the day (do not re-fetch the whole
  schedule unless the response indicates a reschedule).

### 5.4 `ScheduleHistoryScreen`

`history?limit=10` rows: `generated_date`, `status` pill, `exam_date`, progress ring
from local day counts; row tap opens read-only viewer (same widgets, no edit
actions). 401/500 per standard mappings.

### 5.5 `RegenerateDialog` (parent, from viewer overflow menu)

Fields: `current_day` number input (default: first incomplete `day_number`),
consequences text: "Days from day N onward will be re-planned by the AI. Completed
days and recorded progress are kept. Your exam date and daily hours stay unchanged."
Confirm → 2.5; success replaces schedule; 404 → schedule-missing error state.

## 6. Accessibility

- Day list rows are ≥56 logical pixels; `StatusPill`s always carry text and a Flutter semantics
  label such as "Revision day".
- Completion ring exposes the actual response-derived percentage through `Semantics(label: ...)`.
- Week strip cells expose actual date/topic counts through semantics labels.
- Completion-sheet checkboxes use Flutter `Checkbox` semantics; time field uses a numeric keyboard;
  status chips expose a single-selection radio-group semantics pattern.
- All error/empty states provide a focusable retry action with visible label.
