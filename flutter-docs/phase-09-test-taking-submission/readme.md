# Phase 09 — Test Taking & Submission (Flutter)

**Purpose:** Let the child take a scheduled diagnostic test end to end: real eligibility/metadata,
instructions, question runner, timer, answer persistence, submission, and response-driven result.
Every request is scoped to the active child session's `child_id == student_id`.

## Backend reality

At inspected commit `d8ab491`, diagnostic handlers are mocks and the default testing-auth bypass
causes HTTP 500 TypeError responses. The 501 stub is unreachable on the observed path. The Flutter
client calls only the documented endpoints and shows "Test unavailable — backend change pending"
on the verified failure signatures. It never inserts local questions, a demo attempt, random scores,
or a fabricated submission success. See `text.md` and Phase 01 gaps #4/#7.

## Scope

- `TestEligibilityPage` / `TestInstructionsPage` using real metadata/status.
- `TestRunnerPage` with endpoint-provided questions, single-question navigation, palette, countdown,
  user-answer persistence, offline state, and lifecycle handling.
- Submission confirmation/progress/result/failure pages driven by actual submit responses.
- Riverpod `TestSessionController` and real `TestRepository`.
- `ELIGIBILITY_CHECK → INSTRUCTIONS → IN_PROGRESS → SUBMITTING → SUBMITTED` with honest blocked and
  failure branches.
- Handoff to Phase 10 only with real `test_id`, `student_id`, and user-entered answers.

Out of scope: analytics (P10), schedules (P11), scheduling (P08), and parent test taking.

## Endpoints

Prefix `/api/diagnostic-test`:

- `GET /{test_id}` — full test/questions.
- `GET /{test_id}/metadata` and `GET /{test_id}/status` — eligibility/status.
- `POST /{test_id}/start` — start attempt.
- `POST /{test_id}/submit` — submit actual answers.
- `GET /{test_id}/results` — persisted results only.

Do not call generate/generate-async/generation-status/schedule/delete/health shadow routes.

## Dependencies

Phases 02–04 provide Flutter, design, Dio, errors, and child session. Phase 07 supplies child routes;
Phase 08 supplies real diagnostic test/exam IDs and dates.

## Real-data rule

Questions, options, duration, status, attempt, result, and score come from endpoint responses. Only
answers and timing entered/performed by the user originate locally. Current backend failure never
unlocks a local test. Contract fixtures may test parsing only; sign-off uses current-backend blocked
behavior and a backend-fixed real API for the happy path.

## Files

`instructions.md` — Flutter implementation; `text.md` — verified contracts/state/accessibility;
`expected-output.md` — automated checks, current/fixed backend demos, real-data audit, gap log.
