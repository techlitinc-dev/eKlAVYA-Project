# Phase 04 — Networking, Authentication & Session Management

**Purpose:** Build the networking, authentication, and session-management foundation of the
Android app. Every later phase (05–11) calls HTTP through the components defined here:
`AuthApi`, `ApiResult`/`ApiError`, `AuthInterceptor`, `TokenAuthenticator`, `SessionManager`,
`SessionRepository`, and the `SessionEvent` bus. This phase produces **no user-facing screens**
except the shared session-expired contract consumed by ViewModels.

**Inspected source of truth (verified against commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`,
branch `main`, 2026-11-02)**

| Item | Value |
|---|---|
| Backend auth routers | `Backend/routers/login_router.py`, `Backend/routers/simple_register_router.py`, `Backend/routers/auth_router.py` (mounted at prefix `/api/auth`, `Backend/main.py:238-256,330-334`) |
| Backend services | `Backend/services/login_service.py`, `Backend/services/token_service.py` |
| Backend models | `Backend/models/login_models.py` (`LoginResponse` :274, `TokenResponse` :376, `LogoutResponse` :422, request models) |
| Contract authority | `documentation/phase-01-repository-analysis-endpoint-inventory/text.md` §4 (errors), §6 (auth & sessions), §8 (canonical JSON), §9.2 (endpoint inventory), §11 (gaps #1, #7, #9) |

## Shared project decisions (fixed by phase-02; reused verbatim — do not re-litigate)

- Android package: `ai.eklavya.app`. Kotlin + Jetpack Compose + Hilt + Retrofit/OkHttp +
  kotlinx-serialization + Navigation Compose + DataStore (Preferences).
- Base URL: `BuildConfig.EKLAVYA_BASE_URL`, default `http://10.0.2.2:8000` (Android emulator
  loopback for `localhost:8000`).
- Design tokens and components come from phase-03 by name (e.g. `GlassCard`, `GlassTextField`,
  `GlassButton`, `StatusPill`, `ErrorState`). This phase is non-visual except the session-expired
  contract; where it touches UI it names phase-03 components.
- **Parent and child sessions are stored SEPARATELY and never shared.** Tokens are encrypted
  with Android Keystore (AES) before they land in DataStore; only non-sensitive metadata stays
  plaintext (see `text.md` §7).

## Scope

In scope:

- Retrofit API interface `AuthApi` with all parent and child auth calls (12 endpoints).
- DTOs in `data/dto/` with field names byte-identical to the backend JSON.
- `ApiResult<T>` sealed wrapper and typed `ApiError` that understands **both** backend error
  envelopes (phase-01 §4).
- `AuthInterceptor` — attaches `Authorization: Bearer <token>` for the **active role** from
  `SessionManager`.
- `TokenAuthenticator` — on HTTP 401: single-flight refresh, rotate both tokens, retry the
  original request exactly once; on refresh failure clear that role's session and emit a global
  `SessionEvent.SessionExpired`.
- `SessionManager` — DataStore preferences file `sessions`; keystore-encrypted token strings;
  role-scoped read/write/clear; `saveParentSession`, `saveChildSession`, `getActiveRole`,
  `setActiveRole`, `clear(role)`, `requireToken(role)`.
- `SessionRepository` — login/refresh/logout/me wrappers returning `ApiResult`.
- Hilt modules wiring the above into the OkHttp client.
- Session-expired UI contract: each ViewModel consumes `SharedFlow<SessionEvent>`.

Out of scope (covered by later phases): registration UI (P05), child login UI (P07), screens that
consume authenticated APIs (P05–P11), logout UI flows (P05/P07). This phase implements the
`logout` API call and session clearing, not the settings-screen button.

## Endpoints consumed (all from phase-01 §9.2; auth/onboarding inventory)

| # | Endpoint | Phase-01 source | Used here for |
|---|---|---|---|
| 1 | `POST /api/auth/login/email` | `login_router.py:97` | Parent login (P05 wires UI) |
| 2 | `POST /api/auth/login/phone` | `login_router.py:203` | Parent OTP login (optional in P05) |
| 3 | `POST /api/auth/login/google` | `login_router.py:311` | Parent Google login (optional in P05) |
| 4 | `POST /api/auth/token/refresh` | `login_router.py:409` | Parent token rotation |
| 5 | `POST /api/auth/logout` | `login_router.py:501` | Parent logout |
| 6 | `GET /api/auth/me` | `login_router.py:592` | Parent profile / session restore check |
| 7 | `POST /api/auth/login/child` | `login_router.py:719` | Child login (P07 wires UI) |
| 8 | `POST /api/auth/token/refresh/child` | `login_router.py:830` | Child token rotation |
| 9 | `POST /api/auth/logout/child` | `login_router.py:922` | Child logout |
| 10 | `GET /api/auth/me/child` | `login_router.py:1013` | Child profile / session restore check |

No other endpoints are touched in this phase. Never invent an endpoint; if it is not in
`text.md` §3 or phase-01 §9.2, it does not exist.

## Backend facts this phase encodes (see text.md §4–§6 for the full contracts)

- JWT HS256; secret from env `JWT_SECRET` (legacy fallback `JWT_SECRET_KEY`)
  (`token_service.py:41-63`). Expiries **hardcoded**: access 86400 s, refresh 2592000 s
  (`token_service.py:34-35`).
- Parent access claims: `parent_id`, `email?`, `phone?`, `type:"access"` (`token_service.py:66-143`).
- Child access claims: `child_id`, `student_id` (same value), `username`, `is_student:true`,
  `name?`, `type:"access"` (`token_service.py:375-451`).
- Refresh **rotates both tokens** and updates the Firestore `sessions` doc hashes
  (`login_service.py:543-656` parent, `:911-1031` child).
- Logout sets `revoked:true` on the `sessions` doc (`login_service.py:726-729`, `:1108-1111`).
- Wrong credentials → 401 `{"detail": ...}` (legacy envelope, phase-01 §4).

## Backend risks documented (not worked around)

- **Gap #9** (phase-01 §11): without env `FIREBASE_API_KEY` the parent email-login password
  check is **silently skipped** server-side (`login_service.py:215-252`). Client behavior is
  unaffected — it still sends credentials and handles 401 — but the app cannot rely on the
  backend to reject wrong passwords in such deployments. Recorded in `expected-output.md` gap log.
- **Gap #1** (phase-01 §11): child password is stored/compared in plaintext
  (`login_service.py:789-793`, `child_service.py:172`). The app must **never log credentials**
  and must mark child-credential surfaces dev-only.
- **Gap #7** (phase-01 §11): in the default backend (`TESTING_MODE=true`) the Authorization
  header is ignored by several routers (`middleware/testing_auth.py:20-42`). The app must still
  always send it, and must scope every call to ids returned from its own login.

## Dependents

Phase 05 (parent registration/login/dashboard) is the first consumer. Phases 06–11 reuse
`SessionManager`, `ApiResult`, and the session-expired contract unchanged.

## Files in this phase

| File | Read this for |
|---|---|
| `readme.md` | Scope, decisions, endpoint list, risks (this file). |
| `instructions.md` | Sequential numbered build steps; each step names its verification test. |
| `text.md` | Exact JSON contracts, JWT claims, DataStore schema, error mapping, state machines, file map. |
| `expected-output.md` | Acceptance checklist, verification commands, gap log (#1, #9). |
