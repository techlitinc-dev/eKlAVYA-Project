# Phase 11 — Instructions

Execute in order; each step has a **Verify** gate. Android code only (package
`ai.eklavya.app`); never modify the backend. Conventions: Compose + Hilt + Retrofit +
Navigation Compose, base URL `http://10.0.2.2:8000`, phase-03 components
(`ScheduleCard`, `StatusPill`, `GlassDialog`), separate parent/child sessions,
`child_id` as `student_id`.

Guardrails:

- **Gap #6 is expected:** generation from a real analysis 404s on the stock backend
  even after auth/Firebase work. The client must show "Schedule unavailable" and
  never fabricate a schedule. Do not propose client workarounds that fake data.
- Do not call `DELETE /api/schedule/{id}` from app UI. Do not send
  `status:"paused"` in PUT. Do not call `GET /api/schedule/progress/today` as the
  sole source of "today" (see `text.md` §2.10).
- Parent calls carry the parent token; child progress calls carry the child token.

## 0. Boot note

Same as phase-09/10: neutralize `Backend/.env` (`TESTING_MODE=true` at
`.env.example:244` breaks boot via `utils/firebase_config.py:28` →
`vector_search_router.py:42`). For live auth probes, boot with
`JWT_SECRET=<secret> GOOGLE_API_KEY=<key> python3 -m uvicorn main:app --port 8000 &`.

## 1. Models

1.1 `Android_App/app/src/main/java/ai/eklavya/app/data/schedule/Models.kt`:
`ScheduleRequest`, `Schedule`, `ScheduleDay`, `DailyTopic`, `TopicPriority`,
`RegenerateRequest`, `UpdateScheduleRequest`, `ProgressUpdate`, `ScheduleSummary`
(defensive, all fields nullable — it is a free-form dict), `TodayTask` (nullable
fields). Enums: `ExamType {JEE_MAIN, JEE_ADVANCED, NEET}` (no JEE_COMBO),
`ScheduleStatus {ACTIVE, COMPLETED, ABANDONED}`, `DayStatus {COMPLETED, PARTIAL,
SKIPPED}`, `PriorityLevel {CRITICAL, HIGH, MEDIUM, LOW}`, `DifficultyLevel`.
Kotlin property names camelCase; JSON names snake_case via the phase-04 JSON stack.

**Verify:** `ScheduleModelsTest` parses the §3 example JSON and asserts enums, day
lists, and `priority_topics`; parses the summary dict with an extra unknown key
(ignored). `./gradlew testDebugUnitTest --tests "ai.eklavya.app.data.schedule.ScheduleModelsTest"`.

## 2. Service + repository

2.1 `ScheduleService` (`data/schedule/ScheduleService.kt`): the nine consumed
endpoints with exact signatures per `text.md` §2 (query params `status_filter`,
`limit`, `schedule_id`). `getStudentSchedule` response type allows `null` body →
map to Kotlin `null`.

2.2 `ScheduleRepository` (`data/schedule/ScheduleRepository.kt`): sealed results;
explicit mapping: 404 detail containing `"Analytics not found"` / `"Student not
found"` → `ScheduleUnavailableBackendPending` (gap #6); other 404 → `NotFound`; 401
→ `SessionExpired`; 422 → `Validation(fieldErrors)`; 500/network/timeout(60s) →
`Failed`.

**Verify:** MockWebServer tests: null-body 200 → `null`; 404 gap-#6 body →
`ScheduleUnavailableBackendPending`; 401 → `SessionExpired`; PUT example with
`paused` would 500 (do not send — assert the repo never emits it by contract test on
the request builder: only `ACTIVE/COMPLETED/ABANDONED` and 2–8 hours allowed).
`./gradlew testDebugUnitTest --tests "...ScheduleRepositoryTest"`.

## 3. Parent: generation flow

3.1 `ScheduleGenerateViewModel` + `ScheduleGenerateScreen` per `text.md` §5.1:
analysis picker (phase-10 list call), exam date picker (future), hours stepper 2–8,
JEE_COMBO→JEE_MAIN derivation note, existing-schedule pre-check (2.3), `GENERATING`
job state with 60 s timeout, gap-#6 unavailable state, retry.

**Verify:** VM tests: pre-check active-schedule → `VIEW_EXISTING`; null → generate;
201 → `ACTIVE`; 404 gap-#6 → `UNAVAILABLE`; timeout → retry prompt; 422 → field
errors. `./gradlew testDebugUnitTest --tests "...ScheduleGenerateViewModelTest"`.

## 4. Shared viewers + child completion

4.1 `ui/schedule/components/`: `ScheduleHeader` (summary-driven, fallback to local
counts), `DayList` (`ScheduleCard` rows + today highlight + week strip + filter
chips), `DayTopics` (topic cards with expanders), `RegenerateDialog`.

4.2 `ChildScheduleScreen`, `ParentScheduleViewerScreen`, `DayDetailScreen`
(child-only completion via `ProgressUpdate` per `text.md` §4.2),
`ScheduleHistoryScreen`.

4.3 Today derivation per `text.md` §2.10 (local from `Schedule`; endpoint enrichment
non-blocking on 200, ignored on 5xx/404 with gap log).

**Verify:** `./gradlew :app:compileDebugKotlin`; VM tests: day completion 200 updates
day + summary; 404 → snackbar + refresh; filter chips narrow days by the three
day-number lists; today highlight picks `schedule_date == today` else next incomplete.

## 5. Navigation

5.1 Register routes per `text.md` §5 in the parent and child NavHosts; wire the
phase-10 parent results screen "Create study schedule" action →
`schedule_generate/{child_id}`.

**Verify:** `./gradlew :app:assembleDebug`; manual Path A demo shows 401/500 handled
gracefully (below).

## 6. Final sweep

Re-read files: no `paused` status, no `DELETE` call, no JEE_COMBO sent to the
backend, no fabricated schedules; fill `expected-output.md` gap log.
