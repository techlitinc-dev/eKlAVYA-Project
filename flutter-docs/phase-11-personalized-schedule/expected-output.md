# Phase 11 — Expected Output & Sign-off

## Deliverables

Flutter real schedule generation, shared parent/child viewers, day details/progress, history, and
regeneration with role-correct sessions.

## Automated checks

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] Exact request/response coverage includes nullable current schedule and all consumed endpoints.
- [ ] Generate uses actual analytics ID, exam date, and 2–8 hours; only one request is in flight.
- [ ] 201 renders returned schedule; 404/500 produces no local schedule.
- [ ] Parent/child calls carry their own role tokens and real scoped IDs.
- [ ] Null schedule/history and empty enrichment render genuine empty states.
- [ ] Child progress success uses response/refetch; failure does not claim completion.
- [ ] Today 500 is non-blocking and produces no substitute tasks.
- [ ] History/regeneration use actual schedule IDs/current day; invalid paused/DELETE is unused.
- [ ] Accessibility and long-wait announcements pass.

## Required demos

Current backend: record real auth/Gemini/collection failures and confirm unavailable UI contains no
plan. Backend-fixed environment: generate from actual analytics, view parent/child schedules, update
child day progress, verify summary/refetch, and inspect real history/regeneration responses.

## Real-data audit

- [ ] No hardcoded analysis option, schedule/day/topic/resource, progress, history, or success result.
- [ ] No fake job progress or local schedule-generation algorithm.
- [ ] Only current user form input originates locally before mutation.

## Gap log

| Gap | Handling |
|---|---|
| #5-adjacent today crash/invalid status | Optional failure isolation; do not use paused |
| #6 collection mismatch | Backend-unavailable state; no local plan |
| #7 ownership gaps | Role JWT and session/response-derived IDs |

Sign off only when blocked behavior and applicable real schedule flows pass.
