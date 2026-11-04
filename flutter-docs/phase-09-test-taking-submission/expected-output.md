# Phase 09 — Expected Output & Sign-off

## Deliverables

Flutter eligibility, instructions, endpoint-backed test runner, answer persistence, real submission,
and response-driven results with explicit current-backend unavailable handling.

## Automated checks

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] Exact DTO/request tests cover all six consumed calls and no reserved route is called.
- [ ] Current 500 TypeError/501/404 handling produces unavailable UI without questions.
- [ ] Eligibility, duration, sections, questions, and options derive from real responses.
- [ ] Runner restores only actual user answers/timing and handles lifecycle/timer expiry.
- [ ] Submission contains actual answers/measured time and is duplicate-safe.
- [ ] Failed submission shows no score/success; successful result matches response.
- [ ] Semantics, focus, text scaling, and reduced motion pass.

## Required demos

**Current backend:** start the real backend, navigate with an actual test ID, and record the observed
failure. App shows backend-unavailable with retry and no local test.

**Backend-fixed environment:** fetch actual metadata/questions, start, answer, submit, and compare
all result fields with the real response. Verify Phase 10 receives the same real IDs/answers.

## Real-data audit

- [ ] No demo questions/options, fixed duration, local attempt, random/static score, or fabricated
      submission/result exists in production code.
- [ ] Protocol fixtures are not runtime providers.
- [ ] Only user answers/timing originate locally.
- [ ] Failed calls never unlock test runner or Phase 10 completion.

## Gap log

| Gap | Handling |
|---|---|
| #4 mock lifecycle/status/scoring | Explicit unavailable state; no client replacement lifecycle |
| #7 testing-bypass TypeError/auth | Child Bearer and real IDs; honest observed error |
| Stock boot blocker from original phase | Record actual environment blocker; never alter backend in this phase |

Sign off only when current blocked behavior and applicable backend-fixed real flow both pass.
