# Phase 09 — Expected Output & Sign-off

## Deliverables of this phase

1. `data/testtaking/` — models, strict parsers, `TestService`, `TestRepository` with
   the §6 capability check of `text.md`.
2. `ui/testtaking/` — `TestEligibilityScreen`, `TestInstructionsScreen`,
   `TestRunnerScreen`, `SubmissionConfirmDialog`, `SubmissionInProgressScreen`,
   `SubmissionResultScreen`, `FailedSubmissionScreen`, `TestSessionViewModel`.
3. DataStore persistence: `test_in_progress_{test_id}` blob, `submitted_{test_id}` flag.
4. Route `child_test/{test_id}` registered in the child NavHost (phase-07 contract).

## Verification checklist

- [ ] `./gradlew testDebugUnitTest` green (ModelsTest, TestRepositoryTest,
      EligibilityTest, TestSessionViewModelTest, SubmissionTest).
- [ ] `./gradlew :app:assembleDebug` succeeds.
- [ ] Manual run against the **stock** backend: child taps the scheduled test →
      "Test unavailable — backend change pending" empty state; no crash; back returns
      to the dashboard.
- [ ] Parser rejects the wired mock submit/results dicts (missing `TestResults`
      fields) — covered by ModelsTest.
- [ ] Submit gating: only one HTTP submit per attempt; 409 maps to SUBMITTED.
- [ ] No usage of `Question.correct_answer` anywhere in UI code.
- [ ] No fabricated questions/results anywhere; no invented endpoints.
- [ ] Gap log below is filled with anything observed beyond the listed items.

## Live backend verification (what the docs claim, re-checkable)

Boot per `instructions.md` §0, then:

```bash
# Every one of these returns HTTP 500 {"success":false,"error":{"type":"TypeError",...}}
for p in "test_x" "test_x/metadata" "test_x/status" "test_x/results" "health"; do
  echo "GET /$p"; curl -s -w " -> %{http_code}\n" "http://localhost:8000/api/diagnostic-test/$p"
done
curl -s -w " -> %{http_code}\n" -X POST http://localhost:8000/api/diagnostic-test/test_x/start \
  -H "Content-Type: application/json" -d '{"student_id":"child_1"}'
curl -s -w " -> %{http_code}\n" -X POST http://localhost:8000/api/diagnostic-test/test_x/submit \
  -H "Content-Type: application/json" \
  -d '{"test_id":"test_x","student_id":"child_1","answers":{"1":"B","2":""},"time_taken":5400,"submission_time":"2026-11-02T10:00:00Z"}'
curl -s -w " -> %{http_code}\n" "http://localhost:8000/api/diagnostic-test/student/child_1?limit=10&offset=0"
# OpenAPI divergence check: spec shows TestSubmission for submit, runtime accepts any dict
curl -s http://localhost:8000/api/openapi.json | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['paths']['/api/diagnostic-test/{test_id}/submit']['post']['requestBody'])"
```

Expected: 500 TypeError envelope for all diagnostic calls (verified 2026-11-02 at
`d8ab491`); the OpenAPI request body is `$ref: TestSubmission` even though the wired
handler takes `request: dict` (`diagnostic_test_router.py:1051-1054`).

## Demo script

### Path A — current backend (must not crash)

1. Boot backend per `instructions.md` §0. Install app: `./gradlew :app:installDebug`.
2. Log in as a child (phase-07 flow, username + password created in phase-06).
3. Dashboard shows the scheduled test card (phase-08 data: `diagnostic_test_id`).
4. Tap the card → eligibility screen loads → shows "Test unavailable — backend change
   pending" with a Retry button. (Because `GET /{test_id}/metadata` returns the 500
   TypeError envelope — the capability check's gate.)
5. Tap Retry → same state (idempotent, no crash, no empty runner, no fake questions).
6. Back → dashboard.

### Path B — backend-fixed walkthrough (for demo after gap #4 is resolved)

Preconditions: backend persists generated tests with questions; `GET /{test_id}`
serves the §3.2 `DiagnosticTest`; submit persists and returns §3.5 `TestResults`;
`TestMetadata` exposes `status`/`generation_date` (and ideally `scheduled_date`).

1. From the dashboard, tap the scheduled test whose `generation_date + 1 day` has
   passed → Instructions screen shows duration (from `duration_minutes`), total marks,
   sections, marking scheme, declarations.
2. Check all declarations → Start → confirm dialog → runner opens; timer at
   `duration_minutes`.
3. Answer several questions (MCQ tap; numerical entry), flag one, open palette, jump
   around; force-kill the app mid-test; reopen → "Resume incomplete test" restores
   answers, flags, and remaining time.
4. Submit via palette summary → confirm → `SubmissionInProgressScreen` →
   `SubmissionResultScreen` shows score, percentage, counts, per-section breakdown.
5. Continue → phase-10 `AiProcessingStatusScreen`.

## Gap log (BACKEND CHANGE REQUIRED items encountered in this phase)

| # | Gap (phase-01 §11 ref) | Evidence | Client handling | Backend must add |
|---|---|---|---|---|
| 1 | #4 — `GET /{test_id}` not implemented | `diagnostic_test_router.py:508-511` (501 unreachable: TypeError at `:497` fires first — verified live) | Capability check → "Test unavailable — backend change pending" empty state; full UI built against §3.2 | Persist generated tests + questions (generators exist: `services/test_assembler.py`); serve `DiagnosticTest` |
| 2 | #4 — submissions/results not persisted; scoring random in shadowed router | `test_management_router.py:272-300` (writes commented), `:170-269` | Strict `TestResults` parsing; malformed mock dicts → FailedSubmission/error state, never crash | Persist submissions (`test_submissions`); wire real scorer `services/score_calculator.py:153` |
| 3 | #4 — no submit idempotency | No dedupe anywhere on the wired path; `Idempotency-Key` unsupported in Stack 1 (phase-01 §4) | Disable-on-tap, local `submitted_{test_id}` flag, 409/invalid-state → SUBMITTED (text.md §4) | Idempotent submit (unique submission record or `Idempotency-Key`); `409 INVALID_STATE_TRANSITION` on duplicates |
| 4 | #4 — `"scheduled"` not a `TestStatus` member | `diagnostic_test_models.py:35-41` vs `exam_service.py:197` | Client accepts `pending` and `scheduled` equivalently | Add `SCHEDULED` to `TestStatus` (or write `pending`) |
| 5 | #4 — `TestMetadata` lacks `scheduled_date` | Model `:297-342`; doc written with `scheduled_date` at `exam_service.py:154-218` | Eligibility derives `generation_date + 1 day` (text.md §5.1) | Expose `scheduled_date`/`can_start_at` in `TestMetadata` |
| 6 | #7-adjacent — testing-bypass TypeError masks every diagnostic endpoint | `testing_auth.py:20-42` returns `"test_parent_123"`; handlers subscript it (`:497` etc.) — all endpoints 500, verified live | 500-TypeError signature → unavailable empty state | Return a dict principal (or real JWT auth per gap #7) |
| 7 | #4 — `multiple_correct` not expressible in `TestSubmission.answers` | `Dict[int,str]` at `diagnostic_test_models.py:133`; validator `:147-161` | Runner shows unsupported note; question counts as unanswered | Define multi-answer encoding (e.g. `"A,C"`) and document it |
| 8 | #13 — stock boot blocker: `.env` with `TESTING_MODE=true` breaks import | `utils/firebase_config.py:28` + `.env.example:244` → `vector_search_router.py:42` ImportError (verified live) | Documented boot workaround in instructions.md §0 | Fix conditional import; tracked as phase-01 §11 gap #13 |

## Sign-off rule

Every checkbox above must be checked, both demo paths recorded (Path A with
screenshots), and any new drift appended to this gap log with `path:line` evidence —
documentation is fixed, never the backend.
