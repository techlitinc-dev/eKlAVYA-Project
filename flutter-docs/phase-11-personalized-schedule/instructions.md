# Phase 11 — Instructions

Implement real schedule endpoints with role-correct JWTs and actual Phase 08/10 inputs.

## Step 1 — Schedule DTOs and remote data source

Create exact DTOs for schedule request, schedule/day/topic/resource, progress update/summary, history,
and regenerate/update bodies. Implement all consumed real Dio calls in `readme.md`.

**Verify:** serialization/request tests cover nullable current schedule, enum values, real IDs,
`current_day`, progress status, and optional today enrichment.

## Step 2 — Repository and role scoping

Implement real parent generate/read/history/regenerate/update methods and child read/progress methods.
Parent calls use parent token; child calls use child token. Student/analytics/schedule IDs come from
active session and prior responses.

**Verify:** tests assert role-correct Bearer and no cross-role token use or fixed IDs.

## Step 3 — Schedule generation

Load actual analytics history and Phase 08 exam selection. Build analysis picker, 2–8 hours input,
real exam date display, and confirmation. Submit real values and keep one in-flight request. On 201
render the returned schedule; on 404/500 show backend-unavailable/error without a local plan.

**Verify:** no fake progress stages/percent, duplicate generation, hardcoded analysis, or fallback
schedule. Long waiting remains indeterminate and accessible.

## Step 4 — Current schedule and shared viewers

Fetch current schedule using real student ID. Render null as empty. Build parent/child shared day
list, today highlight, week strip, filters, progress summary, and day detail from response models.

**Verify:** all topics/resources/goals/milestones/progress are response-derived; child and parent see
the same real schedule with role-appropriate actions.

## Step 5 — Progress and optional today enrichment

Child day completion calls `POST /api/schedule/progress/update` with actual schedule/day/status.
Render returned progress and invalidate real schedule/summary providers. Call today enrichment
non-blockingly; its 500 leaves the main schedule intact and shows no substitute tasks.

**Verify:** failed mutation does not locally claim completion; parent has no progress-update action.

## Step 6 — History and regeneration

Load real history. Regenerate with actual schedule ID and current day; update only documented mutable
fields. Render the returned schedule and refresh history/current providers. Do not use invalid
`paused` or DELETE.

**Verify:** validation and error states are covered; no local history items are invented.

## Step 7 — Final verification

```bash
flutter analyze
flutter test
flutter test integration_test/schedule_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Run current-backend blocked behavior and backend-fixed generation/view/progress/history flows.
Complete the real-data audit and gaps #5-adjacent/#6/#7 in `expected-output.md`.
