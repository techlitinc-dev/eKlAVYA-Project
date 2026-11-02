# Phase 05 — Parent Registration, Login & Dashboard

**Purpose:** Deliver the complete parent-experience part 1 on Android: welcome/role-pick,
parent registration (with email/phone verification), parent login with automatic session restore,
the parent dashboard, weekly report, goals, settings (notification toggles, profile, logout,
switch-to-child-mode), and a results-viewer placeholder that links forward to phase-10.

**Inspected source of truth (verified against commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`,
branch `main`, 2026-11-02)**

| Item | Value |
|---|---|
| Registration routers | `Backend/routers/simple_register_router.py`, `Backend/routers/auth_router.py` (prefix `/api/auth`, `main.py:238-242,330-334`) |
| Verification router | `Backend/routers/verification_router.py` (prefix `""`, paths `/verify/*`, `main.py:245-249`) |
| Login router | `Backend/routers/login_router.py` (phase-04) |
| Parent dashboard router | `Backend/routers/parent_dashboard_router.py` (prefix `/api/parent` in-router) |
| Services | `simple_register_service.py`, `auth_service.py`, `verification_service.py`, `parent_dashboard_service.py` |
| Models | `auth_models.py`, `login_models.py`, `verification_models.py`, `parent_models.py` |
| Contract authority | phase-01 `text.md` §4 (errors), §7.A (registration & login trace), §8 (canonical JSON), §9.2 (inventory), §11 (gaps #1 #3 #6 #7 #9) |

## Shared project decisions (fixed by phase-02; reused verbatim — do not re-litigate)

- Package `ai.eklavya.app`; Kotlin + Compose + Hilt + Retrofit/OkHttp + kotlinx-serialization +
  Navigation Compose + DataStore; base URL `BuildConfig.EKLAVYA_BASE_URL` default
  `http://10.0.2.2:8000`.
- Phase-04 components are the only HTTP path: `AuthApi`, `ApiResult`/`ApiError`, `AuthInterceptor`,
  `TokenAuthenticator`, `SessionManager`, `SessionEvents`. This phase adds **one** new API
  interface (`ParentApi`), one repository (`ParentRepository`), and the `ui/parent/...` screen
  packages.
- Parent and child sessions are stored separately (phase-04). Settings "switch to child mode"
  launches the child login flow (phase-07) — it never reuses the parent token.
- All screens use phase-03 design tokens by name (GlassCard, GlassTextField, GlassButton,
  StatusPill, ErrorState, plus typography/color/spacing tokens).

## Scope

Screens (fully specified in `text.md` §6–§9): Welcome/role-pick, ParentRegister,
VerifyEmail, VerifyPhone, ParentLogin, ParentDashboard, WeeklyReport, Goals (list/create/edit),
Settings, ParentResults placeholder. Plus: `ParentNavGraph` wiring, session-restore routing on app
start, offline detection with cached-last + retry banner, and per-screen ViewModel/UiState/events.

## Endpoints consumed (phase-01 §9.2; verified in text.md §3)

| Endpoint | Source | Screen(s) |
|---|---|---|
| `POST /api/auth/register/simple` | `simple_register_router.py:31` | ParentRegister (primary) |
| `POST /api/auth/register/parent/email` | `auth_router.py:41` | ParentRegister (optional alternate) |
| `POST /api/auth/register/parent/phone` | `auth_router.py:133` | ParentRegister (optional alternate) |
| `POST /api/auth/register/parent/google` | `auth_router.py:223` | ParentRegister (optional alternate) |
| `POST /verify/email/send` / `POST /verify/email/confirm` | `verification_router.py:43,131` | VerifyEmail |
| `POST /verify/phone/send` / `POST /verify/phone/confirm` | `verification_router.py:230,318` | VerifyPhone |
| `POST /api/auth/login/email` (+ `/phone`, `/google` optional) | `login_router.py:97,203,311` | ParentLogin |
| `GET /api/auth/me` | `login_router.py:592` | Session restore, Settings profile |
| `POST /api/auth/logout` | `login_router.py:501` | Settings logout |
| `GET /api/onboarding/status?parent_id=` | `exam_router.py:492-630` | Post-login routing / dashboard banner |
| `GET /api/onboarding/child?parent_id=` | `child_router.py:164` | Resolve the single child_id |
| `GET /api/parent/dashboard/{child_id}` | `parent_dashboard_router.py:42` | ParentDashboard |
| `GET /api/parent/reports/weekly/{child_id}?week_start=` | `parent_dashboard_router.py:67` | WeeklyReport |
| `GET`/`POST /api/parent/goals/{child_id}`, `PUT /api/parent/goals/{child_id}/{goal_id}` | `parent_dashboard_router.py:161,188,211` | Goals |
| `GET`/`PUT /api/parent/notifications/settings` | `parent_dashboard_router.py:112,135` | Settings |

## Backend realities this phase is designed around

1. **Registration issues no token.** All register endpoints return `AuthResponse` without tokens
   (`auth_models.py:230-278`; services return dicts with no `token` key). The app therefore forces
   a login immediately after successful registration (phase-01 §7.A).
2. **One child per parent.** `ChildService.create_child_profile` rejects a second child with 400
   (`child_service.py:122-128`). The "switch/select child" concept collapses to a single child
   context: the app resolves the child via `GET /api/onboarding/child?parent_id=`. Multi-child UI
   is documented as future-proof (list-shaped seams) but functional only against the single-child
   reality. See `text.md` §10.
3. **Firestore doc keys vary by registration method** (`email`/`email_address`,
   `phone`/`mobile_number`, `name` only for simple). See phase-04 `text.md` §3.6; the profile DTO
   is defensive.
4. **Verification codes are returned in the response in dev** (`verification_service.py:157-160,
   336-339`) — the Verify screens display them in a dev-only notice and must not depend on that
   field in production builds.
5. **BACKEND CHANGE REQUIRED — gap #3:** no forgot-password endpoint exists
   (phase-01 §11 #3; `verification_service.py` has only the four verification functions). The
   forgot-password entry in ParentLogin is rendered, navigates to a spec'd screen, and is marked
   non-functional until the backend lands the proposed Firebase-backed flow (`text.md` §12).
6. **Gap #6:** the dashboard reads collection `analytics` while writers store `analytics_reports`
   (`parent_dashboard_service.py:68-77` vs `analytics_service.py:624-635`). Expect
   `weak_areas=[]` and `recent_test_score=null` even after a real analysis, until the backend
   fixes the collection name (`text.md` §11).
7. **Gap #7:** ownership is not enforced in the default backend (phase-01 §6.1). The app scopes
   every call to the parent_id/child_id from its own login.

## Dependents

Phase 06 (child profile) reuses ParentNavGraph and the dashboard's child-resolution logic.
Phase 08 consumes the dashboard CTA. Phase 10 replaces the ParentResults placeholder.

## Files in this phase

| File | Read this for |
|---|---|
| `readme.md` | Scope, decisions, endpoints, backend realities (this file). |
| `instructions.md` | Ordered build steps for each screen package, navigation, validation, offline, tests. |
| `text.md` | Exact request/response JSON, state machines, data-source notes, accessibility matrix. |
| `expected-output.md` | Checklist, manual demo script, gap log (#3, #6, #7). |
