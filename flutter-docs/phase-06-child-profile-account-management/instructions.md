# Phase 06 — Instructions

Implement against the live parent session and exact contracts in `text.md`.

## Step 1 — Child DTOs and remote data source

Create `ChildProfileRequest`, `ChildProfileResponse`, `ChildProfileUpdate`, and onboarding-status
DTOs with exact wire names. Implement Dio calls E1–E5. `parent_id` and `child_id` are required
method arguments supplied from session/response state.

**Verify:** serialization and request tests cover every field/path/query and no password appears in
any GET/update model or log.

## Step 2 — Real child repository

Return `ApiResult` for create/get/update/delete/status. Create success requires the actual 201
response. Delete success invalidates cached child/onboarding state and triggers real refetch. Do not
manufacture profile timestamps, Firebase IDs, or onboarding flags.

**Verify:** repository tests cover 201/200, 400 one-child, 404, validation errors, and server errors.

## Step 3 — Create-profile form

Build the single-scroll Flutter form with child details, academic level, and login credentials.
Mirror `text.md` §9 validation. Controllers own text input; password fields are obscured and excluded
from logs/analytics.

**Verify:** each invalid rule blocks submission; valid submission sends actual form values once.

## Step 4 — One-time credentials reveal

After real creation success, show the entered username/password once with the returned child profile.
Keep the password only in controller memory, clear it when leaving, and offer clipboard/share only
after explicit user action with a sensitive-content warning.

**Verify:** no storage/log contains the password; back/reopen cannot reveal it again; no success page
appears after a failed POST.

## Step 5 — View and edit profile

Fetch and render the actual child record. Edit only name, age, grade, and current level. Prefill from
the GET response. Username is read-only; password reset is disabled with the gap #2 explanation.
After PUT, render the returned record and invalidate parent dashboard/onboarding providers.

**Verify:** no username/password update is sent; failed PUT does not pretend values were saved.

## Step 6 — Delete profile

Use `GlassDialog` with typed confirmation and explicit consequences. Call DELETE with real IDs. On
success clear child-related cached state, refresh onboarding/dashboard, and route safely. Do not
clear the parent session.

**Verify:** cancel sends nothing; wrong confirmation sends nothing; real success and failure paths
are covered.

## Step 7 — Routes and accessibility

Register create/view/edit routes inside the parent go_router branch. Add semantics, persistent
labels, error announcements, 48-pixel targets, and keyboard/focus behavior.

**Verify:** widget tests cover validation, reveal, edit, delete, loading, empty, and error states.

## Step 8 — Live CRUD and final checks

```bash
flutter analyze
flutter test
flutter test integration_test/child_profile_flow_test.dart \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Against the backend: create through the UI, verify GET, edit supported fields, verify the record,
delete, and verify subsequent GET/onboarding behavior. Use a test account created through real
endpoints. Complete `expected-output.md` and record gaps #1/#2/#7.
