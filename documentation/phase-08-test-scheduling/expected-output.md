# Phase 08 — Expected Output & Sign-off

## Deliverables of this phase

1. `text.md` — verified contracts for S1–S6, the validation algebra (sum=100, subject
   matrix, ≥30-day rule), the S2 side effects, the reserved/unused endpoint list, screen
   specs.
2. `instructions.md` — ordered build steps with the 100-sum worked example and the
   NEET/JEE subject matrix.
3. Running app code: `ScheduleTest` (+ edit-weights mode), `ScheduleSuccessScreen`,
   `ScheduledTestsTracker` — parent session only.

## Verification checklist

### Contracts

- [ ] S1 parsed as `AvailableExamsResponse`; the four exam entries render (JEE_MAIN,
      JEE_ADVANCED, JEE_COMBO, NEET) with their subject lists.
- [ ] S2 sends `{exam_type, exam_date, subject_preferences}` with query `parent_id`,
      `child_id`; **201** accepted as success (not only 200).
- [ ] Response parsed as `ExamSelectionResponse` with `diagnostic_test_id`,
      `days_until_exam`, `created_at`.
- [ ] Client rejects, before submit: sum ≠ 100; negative weights; missing/extra/wrong-case
      subject keys; date in the past; date < 30 days out (worked example from
      `instructions.md` Step 2 all covered by unit tests).
- [ ] S3 preflight gates create vs edit; S3 404 → create mode.
- [ ] S4 sends exactly the exam's three matrix keys with sum 100; server-only-sum
      weakness compensated client-side (`text.md` §4).
- [ ] S5 refreshed after S2/S4 success; dashboard flags update.
- [ ] S6 called with the child's id; `scheduled` literal parsed (gap #4); 500 tolerated
      with retry UI.

### Screens

- [ ] Success screen shows `diagnostic_test_id`, `scheduled_date`, the exact message
      "Your child can take this test from <date>", and "180 minutes · 200 questions".
- [ ] Re-selection for the same child is impossible (edit-weights path instead).
- [ ] Tracker: pills for every status incl. `scheduled`; detail sheet shows all
      `TestMetadata` dates; results/schedule entries route to phase-10/11 stubs.
- [ ] Empty state (no tests) and error state (S6 failure) both present.

### Hygiene

- [ ] No call sites for `POST /api/diagnostic-test/generate`, `/generate-async`,
      `/generation/status/{job_id}`, or `POST /api/diagnostic-test/schedule` (code search
      confirms).
- [ ] All ids (`parent_id`, `child_id`, `student_id`) session-derived; parent Bearer
      header on every call.
- [ ] Accessibility: exam-card selection state, slider announcements, live-region
      remaining indicator.

## Manual demo script

Prereqs: backend running; parent logged in; child exists (phase-06).

1. Parent dashboard → "Schedule a test". Catalog loads; pick **NEET**.
2. Date picker: try yesterday → rejected; try +10 days → rejected (< 30 days); pick
   2026-05-05 (+30 days or more) → accepted.
3. Weights: enter Physics 40, Chemistry 35, Biology 20 → "5 left", confirm disabled;
   adjust Biology to 25 → "0 left", confirm enabled. Try adding a fourth subject →
   rejected. Switch exam to JEE Main → subjects lock to Physics/Chemistry/Mathematics and
   Biology's value is dropped.
4. Confirm. Success screen shows `diagnostic_test_id`, `scheduled_date` = tomorrow, and
   "Your child can take this test from <tomorrow>".
5. Backend cross-checks:
   ```bash
   curl -s "http://localhost:8000/api/onboarding/exam/preferences?child_id=<child_id>"
   curl -s "http://localhost:8000/api/onboarding/status?parent_id=<parent_id>"
   ```
   Expect 200 with the selection (incl. `diagnostic_test_id`) and `exam_selected:true`.
6. Re-enter "Schedule a test" → edit-weights mode (no second S2). Change weights to
   45/30/25, save; S4 200; preferences reflect the change; **no new diagnostic test** is
   created (only one `diagnostic_test_id` exists).
7. Tracker: list shows the test with the Scheduled pill (or the S6 error/retry state on
   today's mock backend — both acceptable; crash is not). Tap → detail shows status and
   dates.
8. Negative tests against the live backend:
   ```bash
   curl -s -X POST "http://localhost:8000/api/onboarding/exam/select?parent_id=<id>&child_id=<id>" \
     -H 'Content-Type: application/json' \
     -d '{"exam_type":"NEET","exam_date":"2027-05-05T00:00:00Z","subject_preferences":{"Physics":40,"Chemistry":30,"Biology":29}}'
   ```
   Expect 400 (sum). Replace Biology with "Mathematics" for NEET → expect 422 (subject
   set). Same payload with exam_date +5 days → expect 400 (30-day rule).
9. Restart the app: parent session intact; tracker state reloads from S6.

## Gap log

| Gap (phase-01 §11) | Where encountered | How this phase handles it |
|---|---|---|
| #4 — `"scheduled"` not a `TestStatus` member; diagnostic lifecycle mock (`diagnostic_test_models.py:35-41`, `exam_service.py:197`) | S6 tracker + success copy | Lenient status parsing; pill includes Scheduled; contract documented. |
| #4 + #7 — S6 500s in testing mode (bypass-string subscript, `diagnostic_test_router.py:652`) | Tracker | Error/retry state; never crash. |
| #7 — query-param auth; header ignored (`testing_auth.py:20-42`) | S1–S6 | Session-derived ids + Bearer header always; 403 as error state. |
| Backend observation — S2 re-run overwrites the selection but creates a second test (`exam_service.py:305-318` + `:154-227`) | ScheduleTest flow | Client-side gating: S3 preflight routes to edit mode; documented here for the backend team (idempotency belongs to gap #4's fix list). |
| Backend observation — S4 does not re-validate the subject set (`routers/exam_router.py:411-416`, `exam_service.py:482-489`) | Edit-weights mode | Client enforces the matrix; documented here. |
| Backend observation — static catalog dates go stale (`Backend/data/exam_dates.json`) | Date picker | Future-date filtering + free-date fallback (`text.md` §7.2). |

## Sign-off rule

Every checklist box checked; demo script passes including the negative curl checks; gap
log entries cite `path:line`. Backend drift is recorded, never silently worked around.
Then phase-09 may start.
