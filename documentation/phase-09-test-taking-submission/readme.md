# Phase 09 — Test Taking & Submission (Android)

**Purpose:** The child takes the scheduled diagnostic test end to end: eligibility
check, instructions, a single-question test runner with timer and answer
persistence, submission, and the results screen. This is a **child-session** phase:
every call is scoped to the child session's `child_id`, which is used as
`student_id` (phase-01 §7.H: "student" and "child" are the same entity).

**Hard truth first (verified live against commit `d8ab491`):** the backend's
diagnostic-test endpoints are mock handlers, and in the current default backend
**every one of them returns HTTP 500** with body
`{"success":false,"error":{"type":"TypeError","message":"string indices must be integers",...}}`
because the testing-auth bypass returns the constant string `"test_parent_123"` and
the handlers subscript it as a dict (`Backend/routers/diagnostic_test_router.py:497,500,567,652,749,950,1011,1073,1134`;
`Backend/middleware/testing_auth.py:20-42`). The 501 that exists in code at
`diagnostic_test_router.py:508-511` is **unreachable** — the TypeError fires first.
This phase therefore builds the complete client against the documented contracts,
gated behind a runtime capability check: when the fetch fails (501, the observed
500-TypeError signature, or 404), the app shows a "Test unavailable — backend change
pending" empty state and never crashes. See `text.md` §2 for the full verified
behavior table and `expected-output.md` for the demo script that demonstrates both
states.

## Scope

In scope:

- `TestEligibilityScreen` / `TestInstructionsScreen` (eligibility gate + instructions + declarations + start confirmation)
- `TestRunnerScreen` (single-question pager, palette, countdown timer, answer persistence, offline banner)
- `SubmissionConfirmDialog`, `SubmissionInProgressScreen`, `SubmissionResultScreen`, `FailedSubmissionScreen`
- `TestSessionViewModel` + `TestRepository` (diagnostic-test endpoints, Retrofit)
- Polling-free state machine: `ELIGIBLE_CHECK → INSTRUCTIONS → IN_PROGRESS → SUBMITTING → SUBMITTED`
- Navigation hooks to phase-10 (`AiProcessingStatus`) and back to the phase-07 child dashboard

Out of scope:

- AI analysis and results (phase-10), schedules (phase-11)
- Test scheduling itself (phase-08; this phase consumes its output `diagnostic_test_id`)
- Parent UI (parents never take tests)

## Endpoints consumed

All on the diagnostic router, prefix `/api/diagnostic-test`
(`Backend/routers/diagnostic_test_router.py:45-52`). The router is registered
**before** `test_management_router` (`Backend/main.py:296` then `:303`), so its
handlers own `/{test_id}/start|submit|results|status` (phase-01 §11 gap #11).

| Endpoint | Wired status today | Use in this phase |
|---|---|---|
| `GET /api/diagnostic-test/{test_id}` | 500 TypeError (501 stub unreachable) — **gap #4** | Fetch full test (questions) — gated behind capability check |
| `GET /api/diagnostic-test/{test_id}/metadata` | 500 TypeError | Eligibility status check |
| `GET /api/diagnostic-test/{test_id}/status` | 500 TypeError | Supplementary status dict |
| `POST /api/diagnostic-test/{test_id}/start` | 500 TypeError | Start attempt (mock contract) |
| `POST /api/diagnostic-test/{test_id}/submit` | 500 TypeError; wired body is **any dict** (`:1051-1054`), NOT `TestSubmission`; OpenAPI shows the *shadowed* `TestSubmission` schema | Submit answers → `TestResults` contract |
| `GET /api/diagnostic-test/{test_id}/results` | 500 TypeError | Fetch persisted results (mock dict shape — see `text.md` §2.4) |

Not consumed: `POST /generate`, `POST /generate-async`, `GET /generation/status/{job_id}`,
`POST /schedule` (mock — phase-08 owns scheduling), `DELETE /{test_id}`, `GET /health`
(shadowed by `/{test_id}` — verified live: `/health` returns the same 500 TypeError).

## Dependencies

| Phase | What this phase needs from it |
|---|---|
| 02 | Gradle project, package `ai.eklavya.app`, minSdk/targetSdk, `AndroidManifest` INTERNET permission |
| 03 | `TestQuestionCard`, `ResultCard`, `StatusPill`, `GlassDialog`, glass theme, spacing/typography tokens |
| 04 | Retrofit/OkHttp client, base URL `http://10.0.2.2:8000` (emulator default), both error-envelope parsers (`{"error":{...}}` and `{"success":false,...}`), child session DataStore (separate from parent session) |
| 07 | Child dashboard navigation contract: route `child_test/{test_id}` carrying `diagnostic_test_id` from the scheduled-test card; child session provides `child_id` as `student_id` |
| 08 | `diagnostic_test_id`, `exam_type`, `exam_date` produced by exam selection (`Backend/routers/exam_router.py:133-267`) |

## Backend changes this phase depends on (phase-01 §11)

- **Gap #4** — diagnostic test lifecycle is mock: implement `GET /{test_id}` (persist
  generated tests + questions; generators exist at `Backend/services/test_assembler.py`),
  persist submissions, wire the real scorer (`Backend/services/score_calculator.py:153`),
  transition status, make submit idempotent, add `"scheduled"` to `TestStatus`
  (`Backend/models/diagnostic_test_models.py:35-41`).
- **Gap #7 (adjacent)** — the testing-bypass TypeError: the bypass returns a string
  (`testing_auth.py:42`) while handlers subscript it as a dict; this is what produces
  today's uniform 500 on every endpoint in this phase.
- New observation recorded in this phase's gap log: stock boot blocker
  (`Backend/utils/firebase_config.py:28` `load_dotenv()` + `.env.example:244`
  `TESTING_MODE=true` breaks `Backend/routers/vector_search_router.py:42` import).

## Sources verified for this phase

`Backend/routers/diagnostic_test_router.py` (full file),
`Backend/routers/test_management_router.py` (full file; shadowed — contract reference only),
`Backend/models/diagnostic_test_models.py` (full file: enums `:28-64`, `TestSubmission` `:120-177`,
`TestMetadata` `:297-342`, `Question` `:345-431`, `Section` `:434-482`, `DiagnosticTest` `:485-539`,
`SectionScore` `:546-582`, `TestResults` `:585-656`),
`Backend/middleware/testing_auth.py`, `Backend/main.py:288-310` (router order),
`Backend/services/exam_service.py:154-218` (scheduled test shape), `Backend/main.py:169-208`
(global 500 handler). All "observed today" claims were re-verified live by booting the
backend and curling each endpoint (commands reproduced in `expected-output.md`).

## File map (deliverable)

| File | Contents |
|---|---|
| `readme.md` | This file: scope, endpoints, dependencies, gap references |
| `instructions.md` | Ordered, numbered build steps with a verify command after each |
| `text.md` | Verified backend reality, exact JSON contracts, eligibility rule derivation, state machine, screen specs, accessibility spec |
| `expected-output.md` | Acceptance checklist, test list, demo script (current-backend and backend-fixed paths), gap log |
