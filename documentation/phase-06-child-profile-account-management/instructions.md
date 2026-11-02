# Phase 06 — Instructions

Sequential implementation steps. Execute in order; each step is verifiable on its own.
Guardrails state what **not** to do. Stack is fixed by phases 02/04: Jetpack Compose, Hilt,
Retrofit, Navigation Compose; package `ai.eklavya.app`; base URL
`BuildConfig.EKLAVYA_BASE_URL` (default `http://10.0.2.2:8000`).

Prereq: phases 02, 03, 04, 05 are complete and the app runs with a parent session
(`SessionManager` provides the parent token and `parent_id`).

## Step 1 — API layer

1. Create `feature/child/api/ChildDtos.kt` mirroring `text.md` §2.1/§2.3/§4.1 exactly:
   `ChildProfileRequest(name, age, grade, current_level, username, password)`,
   `ChildProfileResponse(child_id, parent_id, name, age, grade, current_level, username,
   created_at, updated_at)`, `ChildProfileUpdate` with the four editable fields optional
   (`name`, `age`, `grade`, `current_level`) — **do not** include `username`/`password` in
   the update DTO the UI can populate (they are silently dropped server-side; see
   `Backend/services/child_service.py:416-428`).
2. Create `feature/child/api/ChildApi.kt`:
   - `@POST("api/onboarding/child")` with `@Query("parent_id")` → `ChildProfileResponse`.
   - `@GET("api/onboarding/child")` with `@Query("parent_id")` → `ChildProfileResponse`.
   - `@PUT("api/onboarding/child/{child_id}")` with `@Path("child_id")`,
     `@Query("parent_id")`, body `ChildProfileUpdate` → `ChildProfileResponse`.
   - `@DELETE("api/onboarding/child/{child_id}")` with `@Path("child_id")`,
     `@Query("parent_id")` → `Map<String, String>`.
   - `@GET("api/onboarding/status")` with `@Query("parent_id")` → `Map<String, Boolean>`.
3. Wire the interface into the phase-04 Retrofit/Hilt setup so every call carries the
   parent `Authorization: Bearer` header via `SessionManager`. Never let `parent_id`
   come from UI input — read it from the parent session.

## Step 2 — Client-side validation

Implement `text.md` §9 as a pure validator (unit-testable, no Android deps):
- name: trim, length 2–100, non-blank.
- age: 14–19. grade: 9–12.
- username: trim, length 3–30, `^[a-zA-Z0-9_@.]+$`.
- password: length 8–50, contains `[a-zA-Z]`, contains `[0-9]`.
Return per-field error ids, not server strings. Match the server rules in
`Backend/models/child_models.py:48-252` — do not add extra restrictions.

## Step 3 — ChildProfileCreateScreen + ViewModel

1. Build the multi-section form per `text.md` §10.1: child details (name, age, grade),
   level selector (three cards), credentials (username, password with show/hide toggle,
   helper copy from `text.md` §10.1 item 3).
2. Inline errors under each field from the Step-2 validator (blur + submit). Submit
   disabled until valid. While submitting, disable all inputs.
3. On success (201): replace the form with the **CredentialsRevealStep** (`text.md` §10.2):
   show response `username` + the in-memory form `password`, Copy button per field, Share
   button, warning line, and a single "I've saved these" button that pops to the parent
   dashboard.
4. Error mapping: 400 with the one-child detail (`text.md` §2.2) → replace form with a
   "You already have a child profile" panel linking to view; 400 with username-taken
   detail → inline username error; 422 → map `detail` to the field when recognizable,
   else banner; 401 → phase-04 session-expired flow; IOException → offline banner with
   retry.

## Step 4 — Credential hygiene (mandatory, non-negotiable)

1. The password lives only in the create ViewModel's in-memory state. It is never written
   to disk, never placed in saved-state handles, never sent to analytics/crash reporting.
2. No logging of the E1 request body or the credentials anywhere in the app. Verify your
   OkHttp/Retrofit logging interceptor redacts or skips this call's body.
3. The reveal step cannot be re-entered later (no deep link, no back-stack resurrection
   with the password intact): clearing happens on confirm, on any navigation away, and on
   ViewModel clearance.

## Step 5 — ChildProfileViewScreen + edit

1. Load via `GET /api/onboarding/child` with the session `parent_id`.
   404 → empty state + "Create child profile" CTA (route `child_profile_create`).
   401 → phase-04 re-auth. Network → error + retry. 200 → view state.
2. Edit mode: name/age/grade/level only, same validator as Step 2. PUT with the loaded
   `child_id` and session `parent_id`. On 200, refresh the view and call
   `GET /api/onboarding/status` so dashboard flags update.
3. 400 "No fields provided to update" (`Backend/services/child_service.py:430-436`) →
   silently return to view state (nothing changed). 403/404 → error state + refresh.
4. Credentials section: "Username" row (response value). "Reset password" row rendered
   **disabled** with caption "Coming soon — requires a backend change (gap #2)".
   `BACKEND CHANGE REQUIRED` — do not implement any reset call; the proposed contract in
   `text.md` §8 is non-functional.

## Step 6 — ChildProfileDeleteDialog

1. Use `GlassDialog` (phase-03). Typed confirmation: parent types the child's name; Delete
   enables only on exact match.
2. Show the consequence text verbatim from `text.md` §10.4 ("Your child's login will stop
   working immediately.").
3. On confirm call DELETE; on 200 dismiss + pop to parent dashboard + refresh onboarding
   status. 403/404 → snackbar + re-fetch profile. Network failure → dialog stays open with
   retry. Parse only the `message` key of the 200 body (`text.md` §5).

## Step 7 — Navigation

Register `child_profile_create` and `child_profile_view` as destinations in the **parent**
nav graph (phase-05) per `text.md` §13. The parent dashboard's child card/menu routes:
no profile → create; profile exists → view. Verify the back stack returns to the parent
dashboard in all exit paths.

## Guardrails

- Do not invent endpoints. Only E1–E5 in `text.md` §1 exist for this phase.
- Do not send `username`/`password` in the PUT body expecting a credential change (gap #2).
- Do not log or persist the child password (gap #1 makes it plaintext server-side).
- Do not call the proposed `reset-credentials` endpoint from `text.md` §8 — it does not
  exist.
- Do not expose these screens on the child side; they are parent-session only.
- If the backend disagrees with this document, record the drift in `expected-output.md`
  gap log; never "fix" the backend from the app.

## Verification before sign-off

Run the checklist and demo script in `expected-output.md`, then record results in the gap
log.
