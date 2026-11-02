# Phase 06 — Child Profile & Account Management

**Purpose:** The parent creates, views, edits, and deletes their child's profile — and, in this
backend, **creating the profile also creates the child's login account**. This phase delivers the
parent-facing child-management feature set of the Android app: profile creation with a one-time
credentials reveal, profile view/edit, and profile deletion.

**This phase writes documentation only. No application source code is written here.**

## What the phase delivers

- `text.md` — exact API contracts for the child-profile endpoints (`POST/GET/PUT/DELETE
  /api/onboarding/child`, `GET /api/onboarding/status`), the canonical JSON, the validation
  rules reproduced client-side, the credentials security model, screen state machines, and
  citations into the backend.
- `instructions.md` — ordered implementation steps for the three screens and their ViewModels.
- `expected-output.md` — acceptance checklist, manual demo script, and the phase gap log.

## Scope

In scope:

- `ChildProfileCreate` screen: multi-section form (child details, academic level, login
  credentials) with inline validation, followed by a **credentials reveal step** shown once
  after successful creation.
- `ChildProfileView` / `ChildProfileEdit` screen: view and edit name, age, grade, current
  level. Credential section shows username only; password reset row is present but disabled.
- `ChildProfileDelete`: confirmation dialog (typed confirmation) with explicit consequence
  text. On confirm, the child profile is deleted and the child login stops working.
- Onboarding status integration (`GET /api/onboarding/status`) so the parent dashboard can
  reflect `child_profile_completed`.

Out of scope (handled by other phases):

- Parent registration/login/dashboard — phase-05.
- Child login and child home — phase-07.
- Exam selection / test scheduling — phase-08.

## Dependencies

| Dependency | Phase | What this phase assumes |
|---|---|---|
| Project setup | 02 | App module exists; package `ai.eklavya.app`; Jetpack Compose, Hilt, Retrofit, Navigation Compose in place. |
| Design system | 03 | Glassmorphism components (including `GlassDialog`) are available; this phase references them by name. |
| Networking & session | 04 | Retrofit base URL is `BuildConfig.EKLAVYA_BASE_URL` (default `http://10.0.2.2:8000`); a `SessionManager` provides the parent auth header (`Authorization: Bearer <parent token>`) and parent/child session storage APIs. This phase only ever touches the **parent** session. |
| Parent dashboard | 05 | The parent dashboard exists and hosts the entry navigation into this phase's screens. |

## Backend facts that shape this phase (read before implementing)

1. **Creating a child profile creates the login account.** `ChildService.create_child_profile`
   creates a Firebase Auth user with the supplied username/password
   (`Backend/services/child_service.py:130-153`) and writes the Firestore `children` document
   (`:155-179`). There is no separate "create child account" step anywhere.
2. **One child per parent.** A second `POST` returns 400
   (`Backend/services/child_service.py:122-128`). The app must explain this instead of offering
   a second profile.
3. **The stored child password is plaintext server-side** — `BACKEND CHANGE REQUIRED`,
   phase-01 §11 gap #1 (`child_service.py:172`, compared in plaintext at
   `login_service.py:789-793`). Consequence for the app: the credentials must be shown to the
   parent **once, at creation**, and must never be logged, persisted, or re-displayed — no GET
   endpoint returns the password.
4. **There is no parent-facing credential reset.** `ChildProfileUpdate` declares
   `username`/`password`, but `update_child_profile` silently drops them
   (`child_service.py:416-428`) — `BACKEND CHANGE REQUIRED`, gap #2. The reset row in the edit
   screen is disabled. A target contract is proposed in `text.md` §8, clearly labeled
   **proposed / non-functional**; do not implement a client call to it.
5. **AuthN is the `?parent_id=` query param** (temporary). The testing bypass ignores the
   Authorization header (`Backend/middleware/testing_auth.py:20-42`, phase-01 §6.1). The app
   still sends the header and must always pass `parent_id` from its **own parent session** —
   never a value typed by the user (gap #7: ownership is not observable client-side).

## Source references

| Backend file | Used for |
|---|---|
| `Backend/routers/child_router.py` | Endpoint declarations, status codes, error mapping (`:41-161`, `:164-259`, `:262-378`, `:381-478`) |
| `Backend/services/child_service.py` | One-child rule (`:122-128`), Firebase user creation (`:130-153`), plaintext password write (`:172`), update field filtering (`:416-442`), delete (`:504-537`) |
| `Backend/models/child_models.py` | `ChildProfileRequest` validation (`:22-265`), `ChildProfileResponse` (`:268-359`), `ChildProfileUpdate` (`:362-608`) |
| `Backend/routers/exam_router.py` | `GET /api/onboarding/status` handler (`:492-630`) |
| Phase-01 `text.md` §7.B, §8, §11 | Workflow trace, canonical JSON, gaps #1 #2 #7 |
