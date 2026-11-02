# Phase 09 — Test Taking & Submission (text.md)

Verified against commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4` (branch `main`,
2026-11-02). Claims are marked **[live]** (re-verified by booting the backend and
calling the endpoint) or **[code]** (read from source at the cited `path:line`).

---

## 1. Shared conventions this phase relies on

- Package `ai.eklavya.app`; Compose + Hilt + Retrofit + Navigation Compose (phases 02/04).
- Base URL `http://10.0.2.2:8000` default (Android emulator loopback to host).
- Child session is a **separate** token/DataStore from the parent session (phase-04).
  Every request in this phase sends `Authorization: Bearer <child access token>`.
- `student_id` **is** the child session's `child_id` (phase-01 §7.H; the child JWT
  carries duplicate `child_id`/`student_id` claims, `Backend/services/token_service.py:419-420`).
- Error envelopes (phase-01 §4): v1-style `{"error":{"code","message","details","request_id"}}`
  (installed globally by `Backend/core/errors.py:154-181`, so legacy routers emit it too),
  the global catch-all `{"success":false,"error":{"type","message","detail"}}`
  (`Backend/main.py:169-208`), and `{"detail": str}` for unhandled `HTTPException`s.
  The client parser must handle all three plus `RequestValidationError`'s
  `{"error":{"code":"VALIDATION_ERROR","message":...,"details":{"errors":[...]}}}`
  (`Backend/core/errors.py:156-167`).

## 2. Verified backend reality (read this before coding)

### 2.1 Router ownership [code]

`diagnostic_test_router` and `test_management_router` both use prefix
`/api/diagnostic-test`. `diagnostic_test_router` is included first
(`Backend/main.py:296`), so **its** handlers own `/{test_id}/start|submit|results|status`
(phase-01 §11 gap #11). `test_management_router`'s better-formed mocks (including the
random scorer at `Backend/routers/test_management_router.py:170-269`) are shadowed and
never execute.

### 2.2 OpenAPI vs runtime divergence [code][live]

For the four shared paths, the OpenAPI spec shows the **shadowed**
`test_management_router` schemas (e.g. `POST /{test_id}/submit` request body =
`TestSubmission`, responses include `TestResults`), because FastAPI's OpenAPI builder
lets the later-registered operation overwrite the earlier one in the `paths` map.
The **runtime** handler is the diagnostic router's: `submit_test` takes
`request: dict` — any JSON object is accepted, no `TestSubmission` validation occurs
(`Backend/routers/diagnostic_test_router.py:1051-1054`). Do not code against the spec
for these paths; code against §3 and §4 below.

### 2.3 Observed responses today **[live]**

With the stock backend booted (no `.env`, `TESTING_MODE` unset, no Firebase
credentials — see the boot note in `expected-output.md`), every endpoint below returns:

```
HTTP 500
{"success":false,"error":{"type":"TypeError","message":"string indices must be integers","detail":"An internal server error occurred. Please try again later."}}
```

Root cause: `get_current_user_testing` returns the constant string `"test_parent_123"`
(`Backend/middleware/testing_auth.py:20-42`), and each handler subscripts it as a dict
(`current_user["parent_id"]` / `current_user["student_id"]`) before doing anything
else — e.g. `diagnostic_test_router.py:497` (`get_test`), `:567` (`get_test_metadata`),
`:652` (`get_student_tests`), `:950` (`get_test_status`), `:1011` (`start_test`),
`:1073` (`submit_test`), `:1134` (`get_test_results`). The handler raises before
reaching its own logic, so none of the canned mock bodies in §2.4 can be observed
today. The `501` stub in `get_test` (`diagnostic_test_router.py:508-511`) is likewise
unreachable — the TypeError at `:497` fires first.

Verified request/response matrix (commands in `expected-output.md`):

| Call | Observed today |
|---|---|
| `GET /api/diagnostic-test/test_x` | 500 TypeError envelope |
| `GET /api/diagnostic-test/test_x/metadata` | 500 TypeError envelope |
| `GET /api/diagnostic-test/test_x/status` | 500 TypeError envelope |
| `GET /api/diagnostic-test/student/child_1?limit=10&offset=0` | 500 TypeError envelope |
| `POST /api/diagnostic-test/test_x/start {"student_id":"child_1"}` | 500 TypeError envelope |
| `POST /api/diagnostic-test/test_x/submit` (full `TestSubmission` body) | 500 TypeError envelope |
| `GET /api/diagnostic-test/test_x/results` | 500 TypeError envelope |
| `POST /api/diagnostic-test/generate` | 500 TypeError envelope (`:205` subscripts first) |
| `GET /api/diagnostic-test/health` | 500 TypeError envelope — `/health` is **shadowed by `/{test_id}`** (registered at `:452` vs `:784`), so it executes `get_test("health")` |
| `POST /api/diagnostic-test/schedule` (any dict) | 500 v1 envelope `{"error":{"code":"VALIDATION_ERROR","message":"Failed to schedule test: string indices must be integers",...}}` (TypeError raised inside the handler's `try`, converted at `:903-908`) |

**Consequence for the client:** the capability check (§6) must treat
`HTTP 501` **or** the exact 500-TypeError signature **or** `HTTP 404` as
"test fetch unavailable → empty state". A 500 with any other `error.type` is a
generic server failure → error state with retry. The app must never crash on any
of these bodies.

### 2.4 Canned mock shapes in the wired handlers [code] (unreachable today; shown for completeness)

Once the gap-#7 auth-bypass defect is fixed (handlers receive a real dict), these are
the bodies the mocks return — note they do **not** all match the model contracts in §3:

- `GET /{test_id}/metadata` → `TestMetadata` with `exam_type:"JEE_MAIN"`,
  `student_id:"test_student_123"`, `generation_date:now`, `start_date:null`,
  `submission_date:null`, `status:"pending"` (`:575-583`).
- `GET /student/{student_id}` → list of ≤3 dicts; `i==0` has `"status":"scheduled"`,
  others `"completed"` (`:673-684`). `"scheduled"` is **not** a `TestStatus` member
  (`Backend/models/diagnostic_test_models.py:35-41`) — gap #4 drift the client must
  tolerate.
- `GET /{test_id}/status` → `{"test_id","status":"scheduled","created_at":<now iso>,"student_id":"test_student_123","exam_type":"JEE_MAIN"}` (`:954-960`).
- `POST /{test_id}/start` → `{"test_id","student_id":<from body>,"start_time":<now iso>,"status":"in_progress","duration_minutes":180,"total_questions":90}` (`:1015-1022`).
- `POST /{test_id}/submit` → `{"test_id","student_id":<from body>,"total_score":65,"total_questions":90,"percentage":72.2,"submission_time":<now iso>,"status":"completed"}` (`:1077-1085`). **Differs from `TestResults`**: has `total_questions` instead of `total_marks`, no `section_scores`, no `correct/incorrect/unattempted_count`.
- `GET /{test_id}/results` → `{"test_id","student_id","total_score":65,"total_questions":90,"percentage":72.2,"subject_scores":{"Physics":22,"Chemistry":21,"Mathematics":22},"completion_time":"2h 45m","rank_prediction":"5000-6000","recommendations":[...]}` (`:1138-1156`). Also not `TestResults`.

**Client rule:** parse submit/results responses strictly against the `TestResults`
contract (§4). If the response is missing required `TestResults` fields (as the mocks
above are), treat as malformed: show `FailedSubmissionScreen` (submit) or the generic
error state (results), log the divergence, and record it in the gap log. Never
manufacture missing fields.

## 3. Expected contracts (build the parser against these)

These are the Pydantic models the backend declares (and what a gap-#4 fix must serve).

### 3.1 Enums (`Backend/models/diagnostic_test_models.py:28-64`)

```
ExamType:        JEE_MAIN | JEE_ADVANCED | NEET
TestStatus:      pending | in_progress | completed | expired | cancelled   ("scheduled" NOT included — gap #4)
GenerationStatus: queued | in_progress | completed | failed
QuestionType:    single_correct | multiple_correct | numerical | integer
Difficulty:      easy | medium | hard
```

### 3.2 `GET /api/diagnostic-test/{test_id}` → `DiagnosticTest` (`:485-539`)

```json
{
  "test_id": "test_xyz789",
  "metadata": { "test_id": "test_xyz789", "exam_type": "JEE_MAIN", "student_id": "child_abc123",
                "generation_date": "<iso>", "start_date": null, "submission_date": null, "status": "pending" },
  "instructions": "Read all instructions carefully...",
  "sections": [
    {
      "section_name": "Section A - Physics",
      "subject": "Physics",
      "questions": [
        {
          "question_id": "q_001",
          "question_number": 1,
          "question_text": "What is the acceleration due to gravity on Earth?",
          "options": { "A": "9.8 m/s²", "B": "10 m/s²", "C": "8.9 m/s²", "D": "11 m/s²" },
          "correct_answer": "A",
          "question_type": "single_correct",
          "marks": 4,
          "negative_marks": -1,
          "difficulty": "easy",
          "topic": "Mechanics",
          "subject": "Physics"
        }
      ],
      "total_marks": 120,
      "duration_minutes": 60,
      "instructions": "Attempt all questions. Each correct answer: +4 marks."
    }
  ],
  "total_marks": 360,
  "duration_minutes": 180
}
```

Model constraints the client may rely on: `Question.question_number > 0`; MCQ options
have exactly keys `A,B,C,D` (`:389-408`); `Section.total_marks == Σ question.marks`
(`:461-470`); `DiagnosticTest.total_marks == Σ section.total_marks` (`:512-521`).
`correct_answer` is present in the model — the client **must not** use it; the runner
never displays or transmits it. (A production backend would strip it; today nothing is
served at all. Do not build a "review correct answers" feature.)

### 3.3 `GET /api/diagnostic-test/{test_id}/metadata` → `TestMetadata` (`:297-342`)

```json
{ "test_id": "test_xyz789", "exam_type": "JEE_MAIN", "student_id": "child_abc123",
  "generation_date": "<iso>", "start_date": null, "submission_date": null, "status": "pending" }
```

`exam_type` serializes as its value (`use_enum_values`, `:330-331`). `status` may
arrive as `"scheduled"` from Firestore-written docs (see §5.1) — tolerate it.

### 3.4 `POST /api/diagnostic-test/{test_id}/start` (mock)

Wired handler accepts any dict body (`:1051-1054`) and reads `student_id` from it.
**Client sends** `{"student_id":"<child_id>"}`. Contract response (mock): the dict at
§2.4. A gap-#4 backend should persist `start_date` and set `status:"in_progress"`.

### 3.5 `POST /api/diagnostic-test/{test_id}/submit` → `TestResults`

**Send body — `TestSubmission` (`:120-177`):**

```json
{
  "test_id": "test_xyz789",
  "student_id": "child_abc123",
  "answers": { "1": "B", "2": "", "3": "42.5" },
  "time_taken": 5400,
  "submission_time": "2026-11-02T10:00:00Z"
}
```

Field rules: `answers` maps **integer question numbers** to a single string each.
Allowed values per the model validator (`:147-161`): `A`-`D` (case-insensitive,
stored upper-case), empty string `""` (unattempted), or a numeric string (optional
`-` and `.`). `time_taken`: integer seconds `≥ 0`. `submission_time`: ISO-8601;
default server-side is generation time (`:142-145`) — always send it explicitly from
the client clock. Note: JSON object keys are strings; the client sends `"1"` and the
backend coerces to int. `test_id` in the body must equal the path `test_id`
(enforced only in the shadowed handler `:479-484`; send matching values regardless).

**Known contract gap (part of gap #4):** `multiple_correct` questions cannot be
expressed — the format allows exactly one string per question. The runner handles this
per §7.3.

**Expected response — `TestResults` (`:585-656`):**

```json
{
  "test_id": "test_xyz789",
  "student_id": "child_abc123",
  "total_score": 280,
  "total_marks": 360,
  "percentage": 77.78,
  "section_scores": {
    "Physics": { "section_name": "Section - Physics", "score": 96, "total_marks": 120,
                 "correct": 25, "incorrect": 3, "unattempted": 2 }
  },
  "correct_count": 72,
  "incorrect_count": 10,
  "unattempted_count": 8
}
```

`percentage` is validated to equal `total_score/total_marks*100` within 0.1
(`:618-631`); `section_scores` values are `SectionScore` (`:546-582`) keyed by a
string the backend chooses (subject name in all examples — the client must use each
entry's own `section_name` field for display, not the map key).

### 3.6 `GET /api/diagnostic-test/{test_id}/results` → `TestResults`

Same contract as the submit response. Today the wired mock returns the non-conforming
dict in §2.4 — strict parsing per the §2.4 client rule applies.

### 3.7 `GET /api/diagnostic-test/{test_id}/status` → free-form dict

Wired mock: `{"test_id","status","created_at","student_id","exam_type"}` (`:954-960`).
No model guarantees; the client reads `status` defensively (string or absent) and uses
it only as a supplement to `metadata`.

## 4. Duplicate-submission / idempotency reality (gap #4)

**[code]** Nothing prevents duplicate submissions: the wired mock has no dedupe; the
shadowed `test_management_router` guards on `status == "in_progress"`
(`:496-503`) but its status-transition write is commented out (`:293-298`), so even it
could never trigger; no Stack-1 endpoint implements `Idempotency-Key` (phase-01 §4).
A network retry, a double tap, or a process-death auto-submit replay therefore
**would** create multiple records against a naive backend.

**Client strategy (implement exactly):**

1. `SubmissionConfirmDialog`'s confirm button is disabled on first tap; the
   `TestSessionViewModel` exposes `submitting: Boolean` that gates re-entry.
2. When submission succeeds, write a local flag `submitted_{test_id}=true` (DataStore,
   same file as answer persistence) **before** showing `SubmissionResultScreen`.
3. On app restart, if `submitted_{test_id}` is set, the session restores into
   `SUBMITTED` and offers "View results" (calls `GET /results`) instead of re-running.
4. Treat `409`, or a 4xx whose envelope message mentions an invalid state transition,
   as "already submitted": transition to `SUBMITTED` and fetch results.
5. Auto-submit at timer zero and manual submit share one code path so retries are
   impossible.

**BACKEND CHANGE REQUIRED (gap #4):** persist submissions to `test_submissions`, make
`submit` idempotent (e.g. unique `(test_id, student_id)` submission record or an
`Idempotency-Key`), and return `409 INVALID_STATE_TRANSITION` on duplicates.

## 5. Eligibility rule

### 5.1 Where the inputs come from [code]

Phase-08 exam selection creates the Firestore `diagnostic_tests` doc
(`Backend/services/exam_service.py:154-218`):
`{test_id, child_id, exam_type, scheduled_date: now+1day, duration_minutes:180,
total_questions:200, status:"scheduled", created_at}`. Two facts follow:

1. `status` in Firestore is the literal `"scheduled"`, which is not a `TestStatus`
   member (gap #4) — the client must accept `pending` and `scheduled` equivalently.
2. `TestMetadata` (§3.3) has **no `scheduled_date` field**, so the client derives the
   earliest start instant as `generation_date + 1 day` (UTC), matching the backend's
   `now+1day` write. `BACKEND CHANGE REQUIRED (gap #4):` expose `scheduled_date` (or a
   `can_start_at` timestamp) in `TestMetadata` so eligibility does not rely on a
   derived offset.

### 5.2 Eligibility predicate (implement exactly)

A test is **eligible** when ALL hold:

- `metadata.status ∈ {pending, scheduled}` (tolerate both; also accept absent status as
  pending only when `start_date` and `submission_date` are both null);
- `metadata.start_date == null` and `metadata.submission_date == null`;
- current UTC time ≥ `metadata.generation_date + 1 day`;
- the full-test fetch (§6) returned a parseable `DiagnosticTest`.

Otherwise the child sees one of, in priority order:
`Already completed` (submission_date non-null or status completed) ·
`Not yet available — opens <generation_date+1d, localized>` ·
`Test unavailable — backend change pending` (fetch failed with the §2.3 signatures) ·
generic load error with retry.

## 6. Capability check (gate for the whole phase)

`TestRepository.fetchTest(testId)`:

- `200` with valid `DiagnosticTest` → proceed.
- `501`, or `500` whose body is the catch-all with `error.type == "TypeError"` and
  message `"string indices must be integers"`, or `404` → emit
  `TestUnavailableBackendPending` → `TestUnavailableEmptyState` (copy: "Test
  unavailable — backend change pending", subtitle citing gap #4). **Never crash; never
  proceed with fabricated questions.**
- Other `500`/network errors → `TestLoadError` → error state with Retry.

## 7. Screen specifications

All screens use the phase-03 glass system; all interactive targets ≥ 48dp; strings
via `stringResource` (phase-02 convention). Route: `child_test/{test_id}` (nav args:
`test_id`, plus optional `exam_type`, `exam_date` strings passed through from
phase-08 for display).

### 7.1 `TestEligibilityScreen` / `TestInstructionsScreen`

- Fetches `metadata` (and, on eligibility pass, the full test). Loading: skeleton per
  phase-03. Eligibility verdict per §5.2.
- Instructions body: `DiagnosticTest.instructions` + per-section
  `Section.instructions`, plus derived facts: `duration_minutes` (shown as hours/min),
  `total_marks`, section list with `subject` and `total_marks`, marking scheme text
  built from the distinct `(marks, negative_marks)` pairs in the questions, e.g.
  "+4 / −1" (build from data, never hardcode).
- Declarations checklist (all required before Start enables): non-cheating declaration,
  device/ connectivity declaration, timing declaration (auto-submit at zero), guardian
  consent line. Each row a phase-03 checkbox; Start button disabled until all checked.
- Start flow: Start tap → `GlassDialog` (phase-03) confirmation ("Start test? Timer
  begins immediately") → on confirm, `POST /{test_id}/start` fire-and-forget
  (failure is non-blocking: log it; the local timer is authoritative), clear
  `test_in_progress_{test_id}`, navigate to runner in `IN_PROGRESS`.

### 7.2 `TestRunnerScreen`

- Single-question pager (`HorizontalPager`, one question per page, edge-to-edge
  `TestQuestionCard` from phase-03). Question order: sections in order, questions by
  `question_number` within section. A question's global index (1-based) is displayed
  as "Question <n> of <total>"; the submitted `answers` map keys use the global index
  across the whole test (matches the backend's flat `Dict[int,str]`; the
  `question_number` field is unique test-wide in the model, `:363-366`).
- MCQ (`single_correct`): four options rendered as radio rows (`selectableGroup` +
  `Role.RadioButton` semantics; see §8), tapping selects and stores exactly one of
  `A`-`D`. Numerical/integer: numeric keyboard (`KeyboardOptions.Number` /
  `KeyboardType.Decimal` for `numerical`), free text stored as-is (validated against
  the §3.5 numeric-string rule on submit; strip spaces).
- Question palette: bottom-sheet grid (phase-03 `GlassDialog` variant or modal
  bottom sheet), one cell per question, colors: answered (primary), unanswered
  (outline), flagged (accent), current (ring). Cell tap jumps the pager. "Flag" toggle
  on each question (bookmark icon, contentDescription set).
- Timer: countdown from `duration_minutes * 60` seconds starting when the runner
  opens (the `start` call already happened). `LinearProgressIndicator` for elapsed
  fraction + `MM:SS`/`H:MM:SS` text. At zero: auto-submit through the same path as
  manual submit.
- Prev/Next buttons (icons with contentDescriptions; Next disabled on last question
  is not allowed — instead Next on the last question opens the palette/summary).
- Progress indicator: "Answered X of Y" above the pager.
- Offline banner: visible when `ConnectivityManager` reports no validated network —
  "You are offline. Answers are saved on this device; submission needs a connection."
  Runner remains usable; submit attempts while offline queue into
  `FailedSubmissionScreen` with retry (see 7.4).

### 7.3 Answer persistence (implement exactly)

- Source of truth while running: `TestSessionViewModel.answers: Map<Int,String>` and
  `flagged: Set<Int>`, keyed by global question index.
- On **every** mutation, serialize
  `{test_id, answers:{...}, flagged:[...], remaining_seconds, updated_at}` and write to
  the child-session DataStore at key `test_in_progress_{test_id}` (string preference).
- On process death / app restart with `submitted_{test_id}` unset and a non-empty
  `test_in_progress_{test_id}` blob: the eligibility screen offers "Resume incomplete
  test" restoring answers, flags, and the remaining time (never beyond the original
  deadline). After successful submit or explicit discard, delete the blob.
- `multiple_correct` questions (§3.5 gap): render the question text with an inline
  note "Multiple-answer questions are not supported by the current submission format"
  and no input control; the question stays unanswered. Count it as unanswered
  everywhere (palette, progress, summary). Record in the gap log when observed.

### 7.4 Submission

- `SubmissionConfirmDialog` (from runner's submit action or timer zero): summary
  counts (answered / unanswered / flagged) and `time_taken` so far; buttons Confirm /
  Review (dismiss).
- On confirm → `SUBMITTING` → `SubmissionInProgressScreen` (indeterminate progress,
  non-cancellable copy: "Submitting your answers…").
- Success (`200` + valid `TestResults`) → set `submitted_{test_id}`, delete the
  in-progress blob, navigate to `SubmissionResultScreen`; the **child app then
  triggers phase-10** analytics generation (phase-10 owns that flow).
- Failure: network error / timeout / 5xx / malformed body → `FailedSubmissionScreen`:
  copy "Submission failed — your answers are saved on this device", buttons
  Retry (re-POST; safe per §4 client strategy) and Exit to dashboard (blob retained).
- `409` / invalid-state message → treat as already submitted (§4 step 4).

### 7.5 `SubmissionResultScreen`

- Header: exam type, submitted timestamp.
- `ResultCard` (phase-03) for headline: `total_score` / `total_marks`, `percentage`
  (1 decimal), `correct_count` / `incorrect_count` / `unattempted_count`.
- Section breakdown: one row per `section_scores` entry — `section_name`, score as
  `score/total_marks`, and correct/incorrect/unattempted chips.
- Buttons: "Continue" → phase-10 AI status screen (child flow); "Back to dashboard" →
  phase-07 child dashboard (pops the test flow).

### 7.6 State machine (ViewModel-level)

```
ELIGIBLE_CHECK ──(eligible, declarations checked, start confirmed)──▶ INSTRUCTIONS ──▶ IN_PROGRESS
      │                                                                      │ auto/manual
      ▼                                                                      ▼
TestUnavailableEmptyState / error+retry                            SUBMITTING ──200 TestResults──▶ SUBMITTED ──▶ phase-10 AiProcessingStatus
                                                                           │ 409/invalid-state          │
                                                                           └────────▶ SUBMITTED ◀────────┘ (already-submitted path)
                                                                           │ failure
                                                                           ▼
                                                              FailedSubmissionScreen (retry / exit)
```

`IN_PROGRESS` is only entered from a successful capability check (§6); there is no
path into the runner with missing or fabricated questions.

## 8. Accessibility requirements

- Options list: `Modifier.selectableGroup()` with each row
  `Modifier.selectable(selected, role = Role.RadioButton)`, `semantics { contentDescription = "Option A: <text>" }`;
  state change announces via `liveRegion`.
- Palette cells: `contentDescription = "Question 12, answered"` (etc. incl. flagged/current).
- Timer: `semantics { liveRegion = LiveRegionMode.Polite }`, contentDescription
  "Time remaining <n> minutes"; announce only on minute boundaries (never every second).
- All touch targets ≥ 48dp; palette grid cells ≥ 40dp with spacing; confirm dialogs
  follow phase-03 `GlassDialog` focus behavior (title focused first).
- Numerical input: `KeyboardOptions` numeric, label "Your answer", error state read
  aloud when the value fails the numeric-string rule.

## 9. Navigation contract

| From | To | Args |
|---|---|---|
| Child dashboard (phase-07) scheduled-test card | `TestEligibilityScreen` | `test_id` (required), `exam_type`, `exam_date` (optional display strings) |
| Instructions (start confirmed) | `TestRunnerScreen` | — (ViewModel-scoped) |
| Runner (submit success) | `SubmissionResultScreen` | — |
| SubmissionResult | phase-10 `AiProcessingStatusScreen` | `test_id`, `student_id` |
| Any test screen (exit) | Child dashboard | — |

Back behavior: runner intercepts system back with the same confirm dialog as manual
submit ("Submit and exit?" / "Continue test") — the local state is already persisted
(§7.3), so both choices are safe.
