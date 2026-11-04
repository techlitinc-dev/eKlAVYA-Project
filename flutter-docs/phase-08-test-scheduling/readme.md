# Phase 08 — Test Scheduling

**Purpose:** Let a parent select a real available exam/date and subject weights summing to 100.
`POST /api/onboarding/exam/select` stores the selection and creates the diagnostic test consumed by
Phase 09. Includes a real scheduled-test tracker.

## Scope

- `ScheduleTestPage`: exams/dates fetched from the backend, constrained date selection, subject
  weights, review, real POST, and response-driven confirmation.
- `ScheduledTestsTrackerPage`: real student test list and status/detail actions.
- Real selection/preferences GET and weights PUT; real onboarding status.
- JEE/NEET subject validation and ≥30-day rule mirrored client-side.

Out of scope: test taking (P09), analytics (P10), and personalized schedules (P11).

## Dependencies

Phases 02–04 provide Flutter, widgets, Dio, and parent session. Phase 05 provides navigation; Phase
06 provides the real child ID.

## Real-data rule

Available exams and dates come from `GET /api/onboarding/exams/available`, not a Dart constant.
The displayed diagnostic test ID, scheduled date, selection, tracker rows, and statuses come from
endpoint responses. No hardcoded exam cards, dates, test ID, scheduled row, success response, or
fallback tracker. Validation constants (allowed subjects and sum=100) are contract rules, not data
substitutes. Failures render honest errors/blocked states.

## Backend facts

1. Scheduling is exam selection; only `POST /api/onboarding/exam/select` creates the workflow test.
2. Real responses can contain `scheduled` outside the enum (gap #4); accept and label it.
3. Model requires future date, non-negative weights, exact subject set, sum 100; service requires
   at least 30 days.
4. PUT preferences rechecks only sum server-side, so Flutter enforces the full subject matrix.
5. Reserved generation/mock scheduling endpoints in `text.md` §8 are never called.
6. IDs come from the active parent session and endpoint-resolved child.

## Endpoints

`GET /api/onboarding/exams/available`; `POST /api/onboarding/exam/select`;
`GET/PUT /api/onboarding/exam/preferences`; `GET /api/onboarding/status`; and
`GET /api/diagnostic-test/student/{child_id}`.

## Deliverable files

`instructions.md` — Flutter implementation and live verification; `text.md` — exact contracts,
validation, states, and paths; `expected-output.md` — acceptance checks, demo, and gap log.
