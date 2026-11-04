# Phase 04 — Networking, Authentication & Session Management

**Purpose:** Build the Flutter networking, authentication, and session foundation used by Phases
05–11: `AuthRemoteDataSource`, `ApiResult`/`ApiError`, `AuthInterceptor`, single-flight refresh,
`SessionManager`, `SessionRepository`, and role-scoped session events. No feature screen is built.

**Backend source of truth:** commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`, Phase 01 §4,
§6, §8, §9.2, and §11; `Backend/routers/login_router.py`, `services/login_service.py`,
`services/token_service.py`, and `models/login_models.py`.

## Fixed Flutter decisions

- Dart, Flutter Material 3, Riverpod, Dio, go_router, `json_serializable`.
- Base URL from `--dart-define=EKLAVYA_BASE_URL`; Android emulator default `http://10.0.2.2:8000`.
- Parent and child sessions use separate `flutter_secure_storage` namespaces and are never shared.
- Only non-secret active-role metadata uses `shared_preferences`.
- Every authenticated call sends `Authorization: Bearer <active-role token>` even where the current
  development backend ignores it.
- No fake auth repository, static profile, fixed token, fixed user ID, or fabricated login response.

## Scope

In scope:

- Real Dio calls for the ten parent/child auth endpoints below.
- DTOs with byte-exact JSON names and explicit validation of fields required to create a session.
- `ApiResult<T>` and typed errors for legacy, v1, and global catch-all envelopes.
- Active-role Bearer attachment and role-correct refresh endpoint selection.
- Concurrent 401 handling with one refresh per role, atomic token rotation, and exactly one retry.
- Session restore, role-scoped clear/logout, and a broadcast stream of session events.
- Riverpod wiring and debug-only sanitized HTTP logging.

Out of scope: registration UI (P05), child login UI (P07), authenticated feature screens (P05–P11),
and settings logout buttons. The real logout call and local clearing are implemented here.

## Endpoints consumed

| Endpoint | Use |
|---|---|
| `POST /api/auth/login/email` | Parent email login |
| `POST /api/auth/login/phone` | Parent OTP login |
| `POST /api/auth/login/google` | Parent Google login |
| `POST /api/auth/token/refresh` | Parent token rotation |
| `POST /api/auth/logout` | Parent logout |
| `GET /api/auth/me` | Parent profile/session restore |
| `POST /api/auth/login/child` | Child login |
| `POST /api/auth/token/refresh/child` | Child token rotation |
| `POST /api/auth/logout/child` | Child logout |
| `GET /api/auth/me/child` | Child profile/session restore |

No other endpoint is called. Missing/broken behavior is recorded as `BACKEND CHANGE REQUIRED`.

## Backend facts and risks

- JWT HS256; response expiry is authoritative. Refresh rotates both tokens.
- Parent and child token claims and logout endpoints are role-specific.
- Wrong credentials return legacy `{"detail":...}` errors.
- Gap #9 can skip parent password verification in a misconfigured backend; the client still sends
  real credentials and never treats that behavior as a feature.
- Gap #1 stores child passwords plaintext server-side; never log or persist credentials.
- Gap #7 ignores auth in parts of the default backend; still send tokens and session-derived IDs.

## Dependents

Phase 05 is the first consumer. Phases 06–11 reuse the same Dio, repository result, session, and
session-expiration contracts without introducing alternate data sources.

## Files in this phase

| File | Purpose |
|---|---|
| `readme.md` | Scope, decisions, endpoints, risks |
| `instructions.md` | Numbered Flutter implementation and verification steps |
| `text.md` | Exact JSON, storage schema, error mapping, refresh state machine, file map |
| `expected-output.md` | Tests, real-backend smoke checks, real-data audit, gap log |
