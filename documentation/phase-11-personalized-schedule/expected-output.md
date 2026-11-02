# Phase 11 — Expected Output & Sign-off

## Deliverables

1. `data/schedule/` — models, `ScheduleService`, `ScheduleRepository` with the gap-#6
   and 401 mappings of `text.md`.
2. `ui/schedule/` — `ScheduleGenerateScreen`, `ChildScheduleScreen`,
   `ParentScheduleViewerScreen`, `DayDetailScreen`, `ScheduleHistoryScreen`,
   `RegenerateDialog`, shared components, `ScheduleGenerateViewModel`.
3. Routes: `schedule_generate/{child_id}`, `child_schedule`,
   `parent_schedule/{child_id}`, `day_detail/{day_number}`,
   `schedule_history/{child_id}`.
4. DataStore: `last_schedule_{student_id}`.

## Verification checklist

- [ ] `./gradlew testDebugUnitTest` green (ScheduleModelsTest,
      ScheduleRepositoryTest, ScheduleGenerateViewModelTest, viewer VM tests).
- [ ] `./gradlew :app:assembleDebug` succeeds.
- [ ] Repository maps: gap-#6 404 → unavailable state; 401 → session-expired;
      200-null → empty state; timeout(60s) → retry.
- [ ] No `DELETE` usage; no `paused` status; no JEE_COMBO in requests; no fabricated
      schedules (grep the codebase).
- [ ] Parent flow uses parent token; child progress uses child token (interceptor
      test).
- [ ] Gap log filled with anything observed beyond listed items.

## Live backend verification (re-checkable claims)

Boot per `instructions.md` §0. Environment 1 (no keys at all):

```bash
# Service endpoints: 500 ValueError Google API key (dependency init precedes auth)
curl -s -w "\n-> %{http_code}\n" http://localhost:8000/api/schedule/sched_1
curl -s -w "\n-> %{http_code}\n" -X POST http://localhost:8000/api/schedule/generate \
  -H "Content-Type: application/json" \
  -d '{"student_id":"c","analytics_id":"a","exam_type":"JEE_MAIN","exam_date":"2027-04-15","daily_study_hours":4.0}'
# Progress endpoints: 401 (no Gemini in ProgressTracker; auth runs first)
curl -s -w "\n-> %{http_code}\n" -X POST http://localhost:8000/api/schedule/progress/update \
  -H "Content-Type: application/json" \
  -d '{"schedule_id":"s","day_number":1,"update_date":"2026-11-02","status":"completed","topics_completed":[],"total_time_spent":2.0,"completion_percentage":100.0}'
```

Environment 2 (`JWT_SECRET=devsecret GOOGLE_API_KEY=dummy` boot; mint a parent JWT
with claims `{parent_id, email, iat, exp, type:"access"}` — see phase-01 §6.2):

```bash
TOKEN=$(python3 -c "import jwt,time;print(jwt.encode({'parent_id':'parent_demo_eklavya','iat':int(time.time()),'exp':int(time.time())+86400,'type':'access'},'devsecret',algorithm='HS256'))")
# Without Firestore, even a valid token is "revoked" (fail-closed session check):
curl -s -w "\n-> %{http_code}\n" http://localhost:8000/api/schedule/sched_1 -H "Authorization: Bearer $TOKEN"
curl -s -w "\n-> %{http_code}\n" "http://localhost:8000/api/schedule/student/child_demo_aarav?status_filter=active" -H "Authorization: Bearer $TOKEN"
# Both verified live: 401 {"error":{"code":"VALIDATION_ERROR","message":"Token has been revoked. Please login again.","request_id":"..."}}
```

Expected (all verified 2026-11-02 at `d8ab491`): 500 `ValueError` bodies in
Environment 1; 401 `VALIDATION_ERROR` bodies in Environment 2 — including for a
cryptographically valid token, because `is_token_revoked` fails closed without
Firestore (`Backend/middleware/auth_middleware.py:100-133`).

## Demo script

### Path A — current backend (graceful, no fakes)

1. Environment 2 boot. Parent login → child results screen (phase-10) → "Create
   study schedule".
2. Pick analysis, date, hours → Confirm → `GENERATING` → 401 (Firestore absent) →
   "Session expired — log in again" state, or with no header the same state via the
   401 mapping. No crash, no schedule fabricated.
3. Child app → Schedule tab → "No active schedule" after 401 handling (or generic
   retry on 500 in Environment 1).

### Path B — backend-fixed walkthrough (gap #6 fixed; Firestore + Gemini available)

Preconditions: backend reads `analytics_reports`/`children`; `sessions` queryable;
`GOOGLE_API_KEY` valid (or a stubbed Gemini); a completed phase-10 analysis exists;
parent and child logged in with valid tokens.

1. Parent: results screen → Create study schedule → analysis picker shows the
   phase-10 report; set hours 4.5; exam date prefilled from phase-08 → Confirm →
   pre-check returns `null` → `GENERATING` (job UI) → **201** with full `Schedule`.
2. Viewer: header ring (0%), today highlighted (or "Up next" when today has no day),
   filter chips show e.g. 2 practice-test days; open Day 1 → topics with
   subtopics/resources/goals; regenerate menu → set `current_day` → 200 with replaced
   tail days.
3. Child: same schedule visible read-only; Day 1 → completion sheet → check both
   topics, time 3.5 h, status `completed` → 200 → day shows 100% + checkmark;
   summary header updates (`days_completed 1/120`).
4. Parent: history shows 1–2 entries with status pills; pull-to-refresh updates.
5. Gap-#6 regression check (optional): revert the collection fix server-side →
   generate returns 404 `"Analytics not found: ..."` → app shows "Schedule
   unavailable — backend change pending".

## Gap log

| # | Gap (phase-01 §11 ref) | Evidence | Client handling | Backend must add |
|---|---|---|---|---|
| 1 | **#6 — collection mismatch breaks generation** | `schedule_service.py:84-85` reads `analytics`/`students`; writers use `analytics_reports` (`analytics_service.py:254`) and `children` (`child_service.py:133-179`); routers map `AnalyticsNotFoundError`/`StudentNotFoundError` → 404 `{"error":{"code":"NOT_FOUND","message":"Analytics not found: <id>"\|"Student not found: <id>"}}` (`schedule_router.py:238-250`) | "Schedule unavailable — backend change pending" state with Retry; never fabricate | Read `analytics_reports`/`children` (or write aliases); same fix needed in `parent_dashboard_service.py` |
| 2 | #7 — no parent/child authorization distinction, no ownership checks | `schedule_router.py` handlers accept any authenticated principal (gap #7) | Client scopes all calls to its own ids; tokens per role | Ownership checks (parent owns child; child owns own schedule) |
| 3 | New — `GET /api/schedule/progress/today` crashes whenever today has topics | `progress_tracker.py` today-tasks builder: `topic.subject.value` (DailyTopic.subject is `str`, `schedule_models.py:286`) and `topic.difficulty` (field does not exist on DailyTopic) → AttributeError → 500 | Non-blocking: today derived locally from fetched `Schedule`; endpoint result used only on 200 | Fix builder to `topic.subject` and drop/define `difficulty` |
| 4 | New — PUT example `status:"paused"` can never succeed | Example `schedule_router.py:90-105`; `ScheduleStatus` lacks `paused` (`schedule_models.py:50-55`); re-validation → 500 | Client only sends active/completed/abandoned | Add `paused` to the enum or fix the example |
| 5 | New — read-path re-validates `exam_date` as future | `Schedule.validate_exam_date` (`schedule_models.py:531-539`) runs in `get_schedule`/`update_schedule` parsing → past-exam schedules unreadable (500) | Documented limitation; no client action | Validate only on write, or grandfather old schedules |
| 6 | New — generate has no idempotency | Each POST creates a new `schedule_id` (`gemini_scheduler_service.py:450`) | Pre-check via `GET /student?status_filter=active`; confirm-before-generate-anyway | Optional `Idempotency-Key` support |
| 7 | #13 — stock boot blocker (shared with phases 09/10) | `utils/firebase_config.py:28` + `.env.example:244` → `vector_search_router.py:42` ImportError (verified live) | Boot workaround documented in instructions §0 | Fix conditional import; tracked as phase-01 §11 gap #13 |
| 8 | New — fail-closed session check makes dev testing impossible without Firestore | `auth_middleware.py:100-133` returns "revoked" on any error (verified live: valid JWT → 401 revoked) | Documented; Path B requires a working Firestore `sessions` collection | Optional dev bypass or clearer 503 when the sessions store is unreachable |

## Sign-off rule

All checkboxes pass; both demo paths recorded (Path B with the backend-fixed
environment); any new drift appended here with `path:line` evidence — fix
documentation, never the backend.
