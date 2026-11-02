# Phase 08 — Test Scheduling

**Purpose:** The parent picks the target exam (JEE Main / JEE Advanced / JEE Combo /
NEET), a future exam date, and per-subject focus weights that must sum to exactly 100.
`POST /api/onboarding/exam/select` stores the selection and **creates the diagnostic test**
the child will later take (phase-09). This phase delivers the scheduling screen, the
success confirmation, and a tracker of the child's scheduled tests.

**This phase writes documentation only. No application source code is written here.**

## What the phase delivers

- `text.md` — the exam-selection contracts (`GET /api/onboarding/exams/available`,
  `POST/GET/PUT /api/onboarding/exam/*`, `GET /api/onboarding/status`), the exact
  validation algebra (sum = 100, subject-set matrix, ≥30-day rule), the diagnostic-test
  creation side effects, the reserved/unused diagnostic endpoints, screen state machines.
- `instructions.md` — ordered build steps including a worked 100-sum example and the
  NEET-vs-JEE subject matrix.
- `expected-output.md` — acceptance checklist, manual demo script, gap log.

## Scope

In scope:

- `ScheduleTest` screen: exam-type selector cards, constrained exam-date picker,
  subject-preference inputs with a live remaining indicator, review + confirm, and a
  success screen showing `diagnostic_test_id` and `scheduled_date` with the message
  "Your child can take this test from <date>".
- `ScheduledTestsTracker` screen: the child's tests from
  `GET /api/diagnostic-test/student/{child_id}` with status pills; tap → status detail;
  entry points to results (phase-10) and schedule (phase-11).
- Re-validation of `GET /api/onboarding/exam/preferences` (edit weights) and
  `GET /api/onboarding/status`.

Out of scope:

- Taking / submitting the test — phase-09. Results / AI analysis — phase-10.
- Personalized schedule generation — phase-11. Child profile — phase-06.

## Dependencies

| Dependency | Phase | What this phase assumes |
|---|---|---|
| Project setup | 02 | Package `ai.eklavya.app`; Compose + Hilt + Retrofit + Navigation Compose. |
| Design system | 03 | Glass component set + `StatusPill`. |
| Networking & session | 04 | Retrofit + `SessionManager` parent auth header; parent session supplies `parent_id` and the child's `child_id`. |
| Parent dashboard | 05 | Hosts the entry into `ScheduleTest` and `ScheduledTestsTracker`. |
| Child profile | 06 | A child exists (scheduling requires `child_id`). |

## Backend facts that shape this phase

1. **Scheduling = exam selection.** The only path that creates a diagnostic test in this
   workflow is `POST /api/onboarding/exam/select` → `ExamService.create_diagnostic_test`
   (`Backend/services/exam_service.py:154-227`): `test_id = "test_" + uuid4().hex[:12]`,
   `scheduled_date = now + 1 day`, `duration_minutes = 180`, `total_questions = 200`,
   `status = "scheduled"`, persisted to Firestore `diagnostic_tests`
   (`:189-206`). The selection itself is stored in `exam_selections` keyed by `child_id`
   (`:305-318`).
2. **`"scheduled"` is not a `TestStatus` enum member** (`models/diagnostic_test_models.py:35-41`)
   — `BACKEND CHANGE REQUIRED` gap #4. Clients must accept and render the literal.
3. **Validation is layered.** The Pydantic model requires a future `exam_date`, non-negative
   weights, sum exactly 100, and the exact subject set per exam
   (`models/exam_models.py:87-169`); the service adds a **≥30-day** minimum
   (`services/exam_service.py:279-284`, `utils/date_utils.py:67-93`). Both layers must be
   mirrored client-side.
4. **PUT preferences re-checks only the sum** — the raw `Dict[str,int]` body bypasses the
   model's subject-set validation (`routers/exam_router.py:411-416`,
   `services/exam_service.py:482-489`), so the app must enforce the subject matrix itself
   on edit.
5. **Reserved and unused endpoints.** `POST /api/diagnostic-test/generate`,
  `/generate-async`, `/generation/status/{job_id}` are internal generation mocks the app
   does not call; `POST /api/diagnostic-test/schedule` is an unused mock that must not be
   called (phase-01 §9.4; `routers/diagnostic_test_router.py:144,269,371,803`).
6. AuthN is `?parent_id=`/`?child_id=` query (temporary; phase-01 §6.1, gap #7); the app
   always sends the parent Bearer header and session-derived ids.

## Source references

| Backend file | Used for |
|---|---|
| `Backend/routers/exam_router.py` | All five onboarding endpoints (`:44-131`, `:133-267`, `:270-369`, `:372-489`, `:492-630`); POST select returns **201** (`:136`) |
| `Backend/models/exam_models.py` | `ExamSelectionRequest` validation (`:24-183`), `ExamSelectionResponse` (`:186-265`), `AvailableExam(s)` (`:268-381`), `DiagnosticTestSchedule` (`:384-481`) |
| `Backend/services/exam_service.py` | Available-exams data source (`:70-143`), `create_diagnostic_test` (`:154-227`), `select_exam` checks (`:264-347`), preferences update (`:424-530`), `get_exam_selection` (`:350-422`) |
| `Backend/utils/date_utils.py` | `calculate_days_until` day granularity (`:23-64`), `validate_exam_date(min_days=30)` (`:67-93`) |
| `Backend/routers/diagnostic_test_router.py` | Student test list (`:595-693`) for the tracker; reserved/unused endpoints (`:144`,`:269`,`:371`,`:803`) |
| `Backend/data/exam_dates.json` | The actual `available_dates` payload (JEE Main 2025-01-15/2025-04-15/2026-01-15/2026-04-15; JEE Advanced 2025-05-25/2026-05-25; NEET 2025-05-05/2026-05-05) |
| Phase-01 `text.md` §7.C, §8, §11 | Workflow trace, canonical JSON, gaps #4 #7 |
