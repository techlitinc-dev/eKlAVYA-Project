# Phase 11 — Personalized Schedule (Flutter)

**Purpose:** Parent generates a real personalized schedule from actual analytics and exam data;
parent and child view it, and child updates actual day progress.

## Verified backend reality

- `POST /api/schedule/generate` is synchronous and returns 201 `Schedule` after a potentially long
  operation. UI uses real waiting/success/error states, not fake job progress.
- JWT and session revocation checks are mandatory here. Parent calls use parent token; child progress
  uses child token.
- Gemini configuration and Firestore are required. Gap #6 collection mismatches can block generation.
- `progress/today` can fail when topics exist; treat it as optional real enrichment and show no
  substitute tasks on failure.
- Invalid documented `paused` example is not mapped into a made-up status.

## Scope

- `ScheduleGeneratePage`: actual analysis picker, hours, real exam date, confirmation.
- Shared `ChildSchedulePage` / `ParentScheduleViewerPage`, day list/week/filter from response.
- `DayDetailPage`: actual topics/resources/goals/milestones; child real progress update.
- `ScheduleHistoryPage` and regenerate dialog using actual schedule ID/current day.
- Real `ScheduleRepository`, DTOs, and Riverpod controllers.

Out of scope: analytics generation (P10), payments, and superadmin (P12).

## Endpoints

`POST /api/schedule/generate`; `GET /api/schedule/{schedule_id}`;
`GET /api/schedule/student/{student_id}`; `GET /api/schedule/student/{student_id}/history`;
`POST /api/schedule/{schedule_id}/regenerate`; `PUT /api/schedule/{schedule_id}`;
`POST /api/schedule/progress/update`; `GET /api/schedule/progress/{schedule_id}`; and optional
`GET /api/schedule/progress/today?schedule_id=`. DELETE is not consumed.

## Dependencies

Phases 02–04 supply Flutter/Dio/sessions/errors; Phase 08 supplies real exam date; Phase 10 supplies
real analytics ID/report and parent results entry.

## Real-data rule

No hardcoded analysis options, schedule, days, topics, resources, progress, streak, history, or
success response. A null current schedule renders empty UI; 404/500 renders the documented blocked
state. Local state may hold only current user input until the server responds. Progress mutation
renders the real response/refetch, not assumed server progress.

## Files

`instructions.md` — Flutter implementation; `text.md` — contracts/states/accessibility;
`expected-output.md` — live checks, backend-blocked demo, real-data audit, and gaps.
