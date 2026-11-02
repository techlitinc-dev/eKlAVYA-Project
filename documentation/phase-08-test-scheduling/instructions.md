# Phase 08 — Instructions

Sequential implementation steps. Stack fixed by phases 02/04: Compose + Hilt + Retrofit +
Navigation Compose; package `ai.eklavya.app`; base URL `BuildConfig.EKLAVYA_BASE_URL`.

Prereqs: phases 02–07 complete. A parent session exists and a child profile has been
created (phase-06).

## Step 1 — API layer

1. `feature/schedule/api/ScheduleDtos.kt` mirroring `text.md` §2/§3/§4:
   `AvailableExam(exam_type, exam_name, available_dates, subjects)`,
   `AvailableExamsResponse(exams)`, `ExamSelectionRequest(exam_type, exam_date,
   subject_preferences)`, `ExamSelectionResponse(child_id, exam_type, exam_date,
   subject_preferences, days_until_exam, diagnostic_test_id, created_at)`. Lenient enum
   parsing for `TestMetadata.status` (`scheduled` tolerated — gap #4).
2. `feature/schedule/api/ScheduleApi.kt`:
   - `@GET("api/onboarding/exams/available")` → `AvailableExamsResponse`.
   - `@POST("api/onboarding/exam/select")` with `@Query("parent_id")`, `@Query("child_id")`,
     body `ExamSelectionRequest` → `ExamSelectionResponse` (expect **HTTP 201**,
     `Backend/routers/exam_router.py:136`).
   - `@GET("api/onboarding/exam/preferences")` with `@Query("child_id")` →
     `ExamSelectionResponse`.
   - `@PUT("api/onboarding/exam/preferences")` with `@Query("child_id")`,
     `@Query("parent_id")`, body `Map<String, Int>` → `ExamSelectionResponse`.
   - `@GET("api/onboarding/status")` with `@Query("parent_id")` → `Map<String, Boolean>`.
   - `@GET("api/diagnostic-test/student/{student_id}")` with `@Path`, `@Query status?`,
     `limit(10)`, `offset(0)` → `List<TestMetadata>` (tracker).
3. All calls attach the parent Bearer header; `parent_id` and `child_id` come from the
   parent session / the phase-06-loaded child. Never from UI input.

## Step 2 — Validation engine (pure, unit-testable)

Implement `text.md` §7 exactly:

- **Date rule:** reject past dates; reject dates < 30 days ahead (mirror
  `exam_service.py:279-284` and `utils/date_utils.py:67-93`). Day granularity is fine.
- **Subject matrix (memorize this table):**

  | exam_type | required subject keys (exactly these, spelled exactly) |
  |---|---|
  | JEE_MAIN | Physics, Chemistry, Mathematics |
  | JEE_ADVANCED | Physics, Chemistry, Mathematics |
  | JEE_COMBO | Physics, Chemistry, Mathematics |
  | NEET | Physics, Chemistry, Biology |

- **Sum rule:** weights are integers ≥ 0 and must total **exactly 100**.
- **Worked example (100-sum):** NEET, weights `{Physics: 40, Chemistry: 35, Biology: 25}`.
  Step-by-step: Σ = 40 + 35 + 25 = 100 → remaining = 100 − 100 = 0 → confirm enabled.
  Counter-examples that must be rejected client-side before submit:
  `{Physics: 40, Chemistry: 35, Biology: 20}` → Σ = 95 → remaining = 5 → confirm disabled.
  `{Physics: 40, Chemistry: 35, Biology: 25, Aptitude: 5}` → 105 and an illegal key →
  reject with "exactly three subjects" error.
  `{Physics: 50, Chemistry: 50}` → missing Biology → reject.
  `{physics: 40, Chemistry: 35, Biology: 25}` → wrong capitalization → reject (keys are
  case-sensitive; `exam_models.py:160-167` compares exact strings).
  `{Physics: -10, Chemistry: 60, Biology: 50}` → negative value → reject
  (`exam_models.py:136-140`).

## Step 3 — ScheduleTest screen (create mode)

1. On entry, run S1 and S3 (preflight) in parallel. S3 200 → switch to edit mode
   (Step 4). S3 404 → create mode with the catalog.
2. Render exam cards (S1): title, subjects, date count; selection described for
   accessibility. Selecting a card applies the subject lock: initialize the three inputs
   to the exam's subjects; switching exams remaps by subject name (Physics/Chemistry
   values carry over; Mathematics value never transfers to Biology or vice versa — reset
   to 0/empty on set change).
3. Date picker enforcing the Step-2 date rule; prefer S1 future `available_dates` as
   choices; if none are future, allow any valid future date (catalog staleness,
   `text.md` §2). Send ISO 8601 with offset.
4. Subject inputs with the live `remaining` indicator (§2 example). Confirm enabled only
   at `remaining == 0` and a valid date.
5. Review card → S2. Map errors per `text.md` §9.1. On 201 → success screen.

## Step 4 — Edit-weights mode (S4 path)

Shown when S3 found an existing selection. Display current exam type + date read-only;
edit only the three weights (same sum engine). Submit via S4 with the matrix keys for the
**existing** exam type — the server re-validates only the sum on this path
(`exam_service.py:482-489`), so the client-side matrix check is the only guard; a body
with wrong keys would be stored unvalidated. On success refresh S5.

## Step 5 — ScheduleSuccessScreen

Show `diagnostic_test_id`, `scheduled_date` formatted for the locale, the required line
**"Your child can take this test from <scheduled_date>"**, and "180 minutes · 200
questions" (`exam_service.py:189-199`). Actions: "View tests" → tracker; "Done" → parent
dashboard. Refresh S5 in both paths.

## Step 6 — ScheduledTestsTracker

1. Load S6 with the child's id; newest-first list; `StatusPill` per item (mapping from
   phase-07 `text.md` §10.2, including `scheduled`).
2. Tap → detail sheet: status, `test_id`, `exam_type`, `generation_date`,
   `start_date`, `submission_date`; actions per `text.md` §9.2 (results → phase-10 route
   stub; schedule → phase-11 stub; keep stubs labeled).
3. Empty state CTA → `schedule_test`. Error state (S6 500 today) with retry.

## Step 7 — Navigation

Register `schedule_test`, `schedule_success`, `scheduled_tests_tracker` in the **parent**
nav graph (phase-05). Parent dashboard entries: "Schedule a test" and "My child's tests".
No child-session screens are part of this phase.

## Guardrails

- Do not invent endpoints. Only S1–S6 (`text.md` §1`)` exist for this phase.
- Do not call any of the four endpoints in `text.md` §8 — especially
  `POST /api/diagnostic-test/schedule`.
- Do not send `username`/`password` anywhere in this phase.
- Do not allow S2 to run twice for the same child (§3.3 of `text.md`): the preflight S3
  must gate create vs edit.
- Do not let the stale catalog block scheduling (2025 dates are past; `text.md` §2).
- Never work around a backend error silently — record it in `expected-output.md` gap log.

## Verification before sign-off

Run the checklist and demo script in `expected-output.md`; record drift in its gap log.
