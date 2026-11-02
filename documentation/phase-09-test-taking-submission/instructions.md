# Phase 09 — Instructions

Execute the steps in order. Each step ends with a **Verify** command or test that must
pass before continuing. This phase writes Android code only (package
`ai.eklavya.app`); it never modifies the backend. Conventions inherited from
phases 02/03/04: Compose + Hilt + Retrofit + Navigation Compose, base URL
`http://10.0.2.2:8000`, phase-03 components (`TestQuestionCard`, `ResultCard`,
`StatusPill`, `GlassDialog`), child session separate from the parent session.

Guardrails (apply to every step):

- Never invent an endpoint, field, or response shape. If it is not in `text.md`, it
  does not exist.
- Where the backend blocks required behavior, keep the client honest: show the gated
  empty state, never fabricate questions or results, and record the item in
  `expected-output.md`'s gap log.
- Child screens use the **child session's `child_id` as `student_id`** on every call.
- Always send `Authorization: Bearer <child access token>` (ignored by the current
  backend; required in production).

## 0. Boot note for all verification below

The stock backend cannot boot with the shipped `.env` (`Backend/utils/firebase_config.py:28`
loads `.env`, and `.env.example:244` sets `TESTING_MODE=true`, which breaks the import at
`Backend/routers/vector_search_router.py:42`). For every Verify step, boot with:

```bash
cd Backend && rm -f .env        # or: ensure .env has no TESTING_MODE=true line
python3 -m uvicorn main:app --port 8000 &
sleep 15 && curl -s http://localhost:8000/health   # expect {"status":"healthy",...}
```

## 1. Data layer: models and JSON parsers

1.1 Create `Android_App/app/src/main/java/ai/eklavya/app/data/testtaking/Models.kt`
with Kotlin data classes mirroring the §3 contracts exactly:
`DiagnosticTest`, `TestMetadata`, `TestSection` (name it `TestSection`, not `Section`),
`Question`, `TestSubmissionRequest`, `SectionScore`, `TestResults`; enums
`ExamType`, `TestStatus` (include a tolerant `SCHEDULED("scheduled")` entry for the
gap-#4 drift), `QuestionType`, `Difficulty`. Use `@JsonClass` (Moshi) or
`@Serializable` (kotlinx) — match the phase-04 JSON stack. Keep `correct_answer` in
`Question` (it exists in the contract) but never render it.

1.2 Write strict parsers for `TestResults` and `DiagnosticTest` that **fail on missing
required fields** (the wired mocks in `text.md` §2.4 must fail parsing — this is the
malformed-response path).

**Verify:** unit test `ModelsTest` in
`Android_App/app/src/test/java/ai/eklavya/app/data/testtaking/ModelsTest.kt`:
parse the §3.2 example JSON → assert sections/questions counts and `total_marks`;
parse the §3.5 example → assert all `TestResults` fields; parse the §2.4 mock submit
dict → assert parse **fails** (missing `total_marks`).

```bash
cd Android_App && ./gradlew testDebugUnitTest --tests "ai.eklavya.app.data.testtaking.ModelsTest"
```

## 2. Repository + Retrofit service

2.1 Create `TestService` interface (`data/testtaking/TestService.kt`):

```kotlin
@GET("api/diagnostic-test/{test_id}")
suspend fun getTest(@Path("test_id") testId: String): Response<DiagnosticTest>

@GET("api/diagnostic-test/{test_id}/metadata")
suspend fun getMetadata(@Path("test_id") testId: String): Response<TestMetadata>

@GET("api/diagnostic-test/{test_id}/status")
suspend fun getStatus(@Path("test_id") testId: String): Response<JsonObject>

@POST("api/diagnostic-test/{test_id}/start")
suspend fun start(@Path("test_id") testId: String, @Body body: Map<String, String>): Response<JsonObject>

@POST("api/diagnostic-test/{test_id}/submit")
suspend fun submit(@Path("test_id") testId: String, @Body body: TestSubmissionRequest): Response<TestResults>

@GET("api/diagnostic-test/{test_id}/results")
suspend fun getResults(@Path("test_id") testId: String): Response<TestResults>
```

Bind it with the phase-04 Retrofit instance (base URL `http://10.0.2.2:8000`).

2.2 Create `TestRepository` (`data/testtaking/TestRepository.kt`) returning sealed
results. Implement the capability check (`text.md` §6) exactly:
`501`, catch-all-500 with `error.type=="TypeError"`, and `404` →
`TestUnavailableBackendPending`; other errors → `TestLoadError`.

**Verify:** unit tests with a `MockWebServer` (phase-04 test stack):
enqueue the §2.3 500 TypeError body → repository emits `TestUnavailableBackendPending`;
enqueue 501 → same; enqueue the §3.2 body → emits test; enqueue §2.4 mock results →
malformed error. Run `./gradlew testDebugUnitTest --tests "ai.eklavya.app.data.testtaking.TestRepositoryTest"`.

## 3. Eligibility + ViewModel

3.1 Create `TestSessionViewModel` (`ui/testtaking/TestSessionViewModel.kt`) with the
§7.6 state machine (`ELIGIBLE_CHECK`, `INSTRUCTIONS`, `IN_PROGRESS`, `SUBMITTING`,
`SUBMITTED`, plus `Failed(retryable)` and `UnavailableBackendPending`).

3.2 Implement the eligibility predicate from `text.md` §5.2: status ∈
{pending, scheduled}, both dates null, now ≥ generation_date + 1 day. Implement the
derived "opens at" timestamp; do not add a `scheduled_date` field to the client model
(mark the backend need in the gap log — §5.1 `BACKEND CHANGE REQUIRED`).

**Verify:** unit test `EligibilityTest` covering: scheduled + dates null + 2 days
after generation → eligible; status completed → not eligible (completed state);
generation yesterday (< 1 day) → not eligible with correct "opens at" string;
status `"scheduled"` string parses. `./gradlew testDebugUnitTest --tests "...EligibilityTest"`.

## 4. Eligibility + instructions screen

4.1 Create `TestEligibilityScreen` and `TestInstructionsScreen`
(`ui/testtaking/TestEligibilityScreen.kt`, `TestInstructionsScreen.kt`) per `text.md`
§7.1: skeleton loading, verdict states, instructions + section summary + marking
scheme derived from data, declarations checklist, start-confirmation `GlassDialog`.

**Verify:** `./gradlew :app:compileDebugKotlin` passes; manual run (emulator, child
logged in per phase-07, tap the scheduled test): against the stock backend you must
see the "Test unavailable — backend change pending" empty state (because
`/metadata` 500s) — screenshot this for `expected-output.md`.

## 5. Test runner

5.1 Create `TestRunnerScreen` (`ui/testtaking/TestRunnerScreen.kt`) per §7.2:
`HorizontalPager` single-question pages, palette bottom sheet, countdown timer
(`duration_minutes * 60`, auto-submit at zero), progress line, prev/next, flag toggle,
offline banner.

5.2 Wire answer persistence §7.3: every mutation writes the serialized blob to the
child-session DataStore key `test_in_progress_{test_id}`; resume path restores it.

5.3 Implement the `multiple_correct` unsupported note per §3.5/§7.3 (no input control;
counted unanswered).

**Verify:** `./gradlew :app:compileDebugKotlin`; unit test `TestSessionViewModelTest`:
answer mutations update the map and persist (fake DataStore); timer zero triggers
submit once; multiple mock questions render types correctly (single_correct → 4
options; numerical → text field; multiple_correct → note, no control).

## 6. Submission flow

6.1 Implement `SubmissionConfirmDialog` (counts summary), `SubmissionInProgressScreen`,
`SubmissionResultScreen` (ResultCard + per-`section_scores` rows per §7.5), and
`FailedSubmissionScreen` with Retry/Exit per §7.4.

6.2 Implement the idempotency strategy §4 exactly: disable-on-tap, `submitted_{test_id}`
DataStore flag set on success before navigation, 409/invalid-state → treat as
submitted, shared auto/manual submit path.

**Verify:** unit tests `SubmissionTest` (MockWebServer): 200 valid TestResults →
SUBMITTED + flag written; 500 → FailedSubmission with blob retained; 409 → SUBMITTED
path; double-invoke of submit() only issues one HTTP call (button/flag gating).

## 7. Navigation + phase-10 handoff

7.1 Register the route `child_test/{test_id}` (args per `text.md` §9) in the child
NavHost (phase-07 file); wire "Continue" on results to phase-10's
`AiProcessingStatusScreen` route with `test_id`, `student_id` args. Until phase-10
lands, navigate there behind the same route name — do not stub a fake screen.

**Verify:** `./gradlew :app:assembleDebug` succeeds; manual: run the app, log in as a
child, tap scheduled test → unavailable empty state (stock backend); exit → dashboard.

## 8. Final sweep

8.1 Re-read every file you wrote; delete dead code and unused imports; ensure no
`correct_answer` usage outside the model; ensure no hardcoded base URL (phase-04
BuildConfig field).

8.2 Fill in `expected-output.md`'s checklist and gap log; run the demo script (both
paths) and attach/record results.
