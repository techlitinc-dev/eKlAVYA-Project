# Phase 08 — Test Scheduling (text.md)

Reference material. Citations are `path/file.py:line` at commit
`d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`. Phase-01 `text.md` §4 (legacy error envelope
`{"detail": str}`; integer limit/offset) and §6 (auth modes) apply unchanged.

---

## 1. Endpoints consumed in this phase

| # | Endpoint | Method/Purpose | Success | Source |
|---|---|---|---|---|
| S1 | `/api/onboarding/exams/available` | GET — exam catalog | 200 `AvailableExamsResponse` | `routers/exam_router.py:44-131` |
| S2 | `/api/onboarding/exam/select?parent_id=&child_id=` | POST — select exam + **create diagnostic test** | **201** `ExamSelectionResponse` | `routers/exam_router.py:133-267` |
| S3 | `/api/onboarding/exam/preferences?child_id=` | GET — current selection | 200 `ExamSelectionResponse` / 404 | `routers/exam_router.py:270-369` |
| S4 | `/api/onboarding/exam/preferences?child_id=&parent_id=` | PUT — update subject weights | 200 `ExamSelectionResponse` | `routers/exam_router.py:372-489` |
| S5 | `/api/onboarding/status?parent_id=` | GET — onboarding flags | 200 `Dict[str, bool]` | `routers/exam_router.py:492-630` |
| S6 | `/api/diagnostic-test/student/{student_id}?status=&limit=10&offset=0` | GET — tracker list | 200 `List[TestMetadata]` (mock; phase-07 §5) | `routers/diagnostic_test_router.py:595-693` |

AuthN: `?parent_id=` / `?child_id=` query params (temporary). Always send the parent
`Authorization: Bearer` header; ids come from the parent session (gap #7, phase-01 §6.1).

## 2. S1 — Available exams

200 `AvailableExamsResponse {exams: [AvailableExam]}` (`models/exam_models.py:268-381`).
Each `AvailableExam`: `exam_type: str`, `exam_name: str`,
`available_dates: List[str]` (local ISO `YYYY-MM-DD`), `subjects: List[str]`.
Built from `Backend/data/exam_dates.json` (`services/exam_service.py:70-143`); today:

| exam_type | exam_name | available_dates (as shipped) | subjects |
|---|---|---|---|
| `JEE_MAIN` | JEE Main | 2025-01-15, 2025-04-15, 2026-01-15, 2026-04-15 | Physics, Chemistry, Mathematics |
| `JEE_ADVANCED` | JEE Advanced | 2025-05-25, 2026-05-25 | Physics, Chemistry, Mathematics |
| `JEE_COMBO` | JEE Main + Advanced | union of Main + Advanced dates (6 entries) | Physics, Chemistry, Mathematics |
| `NEET` | NEET | 2025-05-05, 2026-05-05 | Physics, Chemistry, Biology |

Notes: dates are static data and will go stale (2025 dates are past) — the date-picker
logic in §7 must filter to future dates and fall back to free future-date selection when
nothing remains (see §7 rules). No auth required by the handler.

## 3. S2 — Select exam (the scheduling transaction)

### 3.1 Request — `ExamSelectionRequest` (`models/exam_models.py:24-183`)

| Field | Type | Rule | Enforcement |
|---|---|---|---|
| `exam_type` | literal | `JEE_MAIN` \| `JEE_ADVANCED` \| `JEE_COMBO` \| `NEET` | `exam_models.py:48-50`, `:65-85` |
| `exam_date` | datetime | future (tz-aware after model coercion; naive → UTC) | `exam_models.py:87-113` |
| `subject_preferences` | `Dict[str,int]` | values ≥ 0; **sum(values) == exactly 100**; keys exactly the subject set for the exam type | `exam_models.py:115-169` |

Service-side additional check: `exam_date` must be **≥ 30 days** in the future
(day granularity) → 400 `"Exam date must be at least 30 days in the future"`
(`services/exam_service.py:279-284`; `utils/date_utils.py:23-93`).

Ownership: `child_id` must exist and belong to `parent_id` → 404 (child missing,
`exam_service.py:267-269` via `ChildService.get_child_by_id`) then 403
(`:271-276`).

### 3.2 Subject-set matrix (contractual)

| exam_type | required keys (exactly) |
|---|---|
| `JEE_MAIN` | `Physics`, `Chemistry`, `Mathematics` |
| `JEE_ADVANCED` | `Physics`, `Chemistry`, `Mathematics` |
| `JEE_COMBO` | `Physics`, `Chemistry`, `Mathematics` |
| `NEET` | `Physics`, `Chemistry`, `Biology` |

Any other key set → 422 `"Invalid subjects for <exam_type>. Expected: ... Got: ..."`
(`exam_models.py:162-167`). Extra keys and missing keys both fail. `JEE_COMBO` uses the
**Mathematics** set (not Biology).

### 3.3 Side effects (what the success means)

`ExamService.select_exam` (`exam_service.py:264-347`):

1. Validates child ownership and date (above) and re-checks sum=100 → 400
   `"Subject weightages must sum to 100. Current total: <n>"` (`:286-293`).
2. `create_diagnostic_test` (`:154-227`): `test_id="test_"+uuid4().hex[:12]`,
   `scheduled_date = datetime.now(timezone.utc) + 1 day`,
   `duration_minutes=180`, `total_questions=200`, `status="scheduled"`, written to
   Firestore `diagnostic_tests`.
3. Selection doc written to `exam_selections` with document id = `child_id`
   (`:305-318`). **One selection per child**: calling S2 again for the same child
   overwrites the selection document but creates a **second** diagnostic test — the app
   must prevent re-selection client-side (show the existing selection from S3 with an
   edit-weights path instead).

### 3.4 Response — 201 `ExamSelectionResponse` (`exam_models.py:186-265`)

```json
POST /api/onboarding/exam/select?parent_id=<id>&child_id=child_abc123
{"exam_type":"JEE_MAIN","exam_date":"2027-04-15T09:00:00+05:30",
 "subject_preferences":{"Physics":35,"Chemistry":30,"Mathematics":35}}
→ 201
{"child_id":"child_abc123","exam_type":"JEE_MAIN","exam_date":"2027-04-15T09:00:00+05:30",
 "subject_preferences":{"Physics":35,"Chemistry":30,"Mathematics":35},
 "days_until_exam":529,"diagnostic_test_id":"test_xyz789ghi012","created_at":"..."}
```

- `days_until_exam` is day-granularity UTC (`utils/date_utils.py:23-64`).
- Error statuses: 400 (date, sum), 403 (ownership), 404 (child), 422 (model), 500.

## 4. S3 — Get selection; S4 — Update weights

- S3 (`exam_router.py:270-369`): 200 `ExamSelectionResponse` from the `exam_selections`
  doc keyed by `child_id`; **404** `"Exam selection not found for child: <child_id>"`
  (`exam_service.py:382-387`) means "not scheduled yet". `days_until_exam` is recomputed
  on read; a past exam date yields 0 (`:394-399`).
- S4 (`exam_router.py:372-489`): body is a **raw** `Dict[str,int]` (not the full
  request model). Enforced server-side: ownership 403, selection exists 404, **sum = 100**
  400 (`exam_service.py:482-489`). **The subject-set is NOT re-validated** on this path —
  the app must send only the keys of the current exam type's matrix (§3.2). Response: 200
  `ExamSelectionResponse` (exam type/date unchanged; `created_at` is the original).

## 5. S5 — Onboarding status

Identical to phase-06 §6: `{preferences_completed, child_profile_completed,
exam_selected, onboarding_complete}` (`exam_router.py:492-621`). `exam_selected` is true
when S3 succeeds for the child (`:592-599`). Re-fetch after S2/S4 so the dashboard
updates.

## 6. S6 — Tracker data

Same contract and same live-behavior caveats as phase-07 §5 (mock; 500 in testing mode;
tolerate `"scheduled"`). The tracker displays `test_id`, `exam_type`,
`scheduled_date`/`generation_date`, `status` pill (including `scheduled`), and
`submission_date` when present. Parent-side calls use the child's `child_id` (the parent
has exactly one child, phase-06); no auth difference from the child-side call.

## 7. Client-side validation (mirror of §3)

1. **Exam type** — from selector cards (S1 data); exactly one selected.
2. **Exam date** — must be (a) in the future, (b) **≥ 30 days** ahead (both checks,
   matching model + service), and (c) when S1 provides future `available_dates` for the
   chosen exam, prefer restricting picker choices to those dates; if none are future,
   allow any date satisfying (a)+(b) and note the catalog is stale. Send an ISO 8601
   datetime; naive local selection should be sent with its offset (the backend accepts
   tz-aware; naive coerces to UTC at `exam_models.py:102-104`).
3. **Subject weights** — integers ≥ 0, exactly the three subjects of the matrix for the
   selected exam, **sum exactly 100**. Live indicator: `remaining = 100 − Σ`; confirm
   enabled only when `remaining == 0`. Per-exam subject lock: switching exam type resets
   the inputs to that exam's subject set (values preserved by subject name where they
   exist — Physics/Chemistry carry over; Mathematics ↔ Biology never does).
4. Submit body key order is irrelevant; key names must match the matrix exactly
   (capitalization matters: `Physics`, `Chemistry`, `Mathematics`, `Biology`).

## 8. Reserved and unused endpoints — DO NOT CALL

| Endpoint | Status | Why |
|---|---|---|
| `POST /api/diagnostic-test/generate` | Reserved internal generation endpoint (mock 201, `diagnostic_test_router.py:144-266`) | Test creation in this workflow happens **only** via S2. |
| `POST /api/diagnostic-test/generate-async` | Reserved (mock 202, `:269-368`) | Same; no client polling needed. |
| `GET /api/diagnostic-test/generation/status/{job_id}` | Reserved (mock 200, `:371-449`) | Same. |
| `POST /api/diagnostic-test/schedule` | **Unused mock — must not be called** (`:803-908`) | Firestore write commented out (`:877-891`); returns canned 201 and even 500s in testing mode (`current_user['parent_id']` on the bypass string, `:894`). Scheduling is S2. |

The app must not contain call sites for any of the four.

## 9. Screen specifications

### 9.1 ScheduleTest

Sections:

1. **Exam type** — cards from S1 (`exam_name`, `subjects` shown on the card,
   `available_dates` count). Selecting a card locks the subject set per §7.3.
2. **Exam date** — date picker per §7.2. Display the chosen date + computed
   `days_until_exam` (local, day granularity — display-only).
3. **Subject preferences** — three sliders/number inputs for the locked subjects; live
   `remaining` indicator ("40 left") that turns into an error style when negative and a
   success style at exactly 0; helper "Total must equal 100."
4. **Review + confirm** — summary card (exam, date, weights) → S2 on confirm.
   Pre-confirm errors: S3 lookup on entry — if a selection exists, skip straight to
   edit-weights mode (S4) instead of allowing S2 again (§3.3).

Success screen: show `diagnostic_test_id`, `scheduled_date` (formatted), and the required
message **"Your child can take this test from <scheduled_date>"**; secondary line:
"180 minutes · 200 questions". Actions: "View tests" → tracker; "Done" → parent
dashboard. Also refresh S5.

Errors: 400 sum → inline on the weights section; 400 date → date field error; 403/404 →
error state (profile mismatch; refresh child data from phase-06); 422 → field mapping;
network → retry; 401 → phase-04 re-auth.

### 9.2 ScheduledTestsTracker

- Loads S6 for the child id; lists tests newest-first with `StatusPill`
  (mapping from phase-07 §10.2, including `scheduled`).
- Tap a test → status detail bottom sheet/screen: full status, `test_id`,
  `exam_type`, dates (`generation_date`, `start_date`, `submission_date`), and
  conditional actions: completed with analysis → "View results" (phase-10 route);
  `scheduled`/`pending` → "How the child starts" explainer (phase-09 owns the actual
  start flow); entry row "Study schedule" → phase-11.
- Empty state: "No tests scheduled yet" → CTA to `ScheduleTest`.
- Error state (S6 500 today) with retry — never crash (phase-07 §5 caveat applies).

## 10. State machines

**ScheduleTest** — `LoadingCatalog(S1 + S3) → Idle(exists? edit-mode : create-mode) →
Submitting(S2 or S4) → Scheduled(response) | Validation | Error(400-sum | 400-date |
403/404 | 422 | 401 | network)`.

**ScheduledTestsTracker** — `Loading → Ready(list) | Empty | Error(retry)`;
detail sheet inherits the tapped item.

## 11. Accessibility

- Exam cards: selected state described ("selected" / "not selected").
- Sliders: value + subject announced; remaining indicator as a live region.
- Success screen: ids read character-by-character hint for copy affordance; the
  "can take this test from <date>" line announced first.
- Tracker pills: icon + label (phase-07 mapping).

## 12. Files (under `Android_App/lib/`)

| Path | Contents |
|---|---|
| `features/parent/data/datasources/exam_remote_data_source.dart` | S1–S6 real Dio calls |
| `features/parent/data/dto/exam_dtos.dart` | Available exams, selection, preference update, status, test metadata |
| `features/parent/data/repositories/exam_repository_impl.dart` | Real calls, errors, existing-selection preflight |
| `features/parent/presentation/pages/schedule_test_page.dart` | §9.1 endpoint-driven form |
| `features/parent/presentation/controllers/schedule_test_controller.dart` | Validation and real submission state |
| `features/parent/presentation/pages/schedule_success_page.dart` | Response-only confirmation |
| `features/parent/presentation/pages/scheduled_tests_tracker_page.dart` | §9.2 real tracker |
| `features/parent/presentation/controllers/scheduled_tests_tracker_controller.dart` | S6 loading/content/empty/error |
| `features/parent/presentation/widgets/test_status_detail_sheet.dart` | Selected real test detail |

go_router routes `schedule_test`, `schedule_success`, and `scheduled_tests_tracker` belong to the
parent branch. Results/schedule routes remain owned by their phases. Available exams/dates and all
success/tracker records come from responses, never Dart constants.
