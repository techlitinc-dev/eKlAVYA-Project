# Phase 04 — Networking, Auth & Session (text.md)

Reference material for this phase. Every contract below was verified against
commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4` (branch `main`, 2026-11-02).
Citations are `path/file.py:line` relative to the repository root. Phase-01 citations
(`phase-01 .../text.md §n`) refer to `flutter-docs/phase-01-repository-analysis-endpoint-inventory/text.md`.

---

## 1. Stack and fixed project decisions

| Decision | Value |
|---|---|
| Native ID / Dart package | `ai.eklavya.app` / `eklavya_app` |
| Language / UI | Dart, Flutter Material 3 |
| State / DI | Riverpod |
| HTTP | Dio + `json_serializable` (`application/json`) |
| Navigation | go_router |
| Secret storage | `flutter_secure_storage`, separate parent/child namespaces |
| Non-secret preferences | `shared_preferences` for active role only |
| Base URL | `--dart-define=EKLAVYA_BASE_URL`, Android emulator default `http://10.0.2.2:8000` |
| Roles | `enum Role { parent, child }` — sessions stored separately, never shared |

Nothing in this phase may add dependencies beyond those fixed in Phase 02. Production providers use
only the real remote auth data source.

## 2. Wire format conventions

- All requests and responses are JSON, UTF-8. DTOs use `json_serializable` and `@JsonKey` where
  needed; field names must match the backend byte-for-byte (§3).
- Dates/times: ISO 8601, timezone-aware UTC strings; dates are local `YYYY-MM-DD`
  (phase-01 §4 "Timestamps").
- Success status codes per endpoint are listed in §3. Anything else non-2xx is an error.
- Pagination does **not** apply to any endpoint in this phase (integer `limit`/`offset` only
  matters from P10 onward; phase-01 §4).

## 3. Endpoint contracts (canonical JSON)

All paths are as mounted in `Backend/main.py`: login and register routers at prefix `/api/auth`
(`main.py:252-256`, `main.py:330-334`), verification router at prefix `""` so paths are `/verify/*`
(`main.py:245-249`).

### 3.1 POST /api/auth/login/email — parent email login
Handler `login_router.py:97-200`; service `login_service.login_with_email` (`login_service.py:171-303`).
Request model `EmailLoginRequest` (`login_models.py:26-62`): `email` is `EmailStr`; `password` has
`min_length=8` enforced by Pydantic before the service runs.

Request:
```json
{"email": "rajesh@example.com", "password": "Passw0rd1"}
```
Success 200 `LoginResponse` (`login_models.py:274-373` — all fields below exist on the model):
```json
{"token": "<jwt>", "refresh_token": "<jwt>", "parent_id": "<firebase-uid>",
 "email": "rajesh@example.com", "phone": null, "expires_in": 86400,
 "student_id": null, "child_id": null, "username": null, "name": null,
 "is_student": false, "message": null}
```
`expires_in` is always `token_service.ACCESS_TOKEN_EXPIRY` = 86400 (`login_service.py:293`,
`token_service.py:34`). For a parent login the child/student fields are `null`/`false`.

Errors: 401 `{"detail":"Invalid email or password"}` (wrong credentials, `login_router.py:188-191`,
message from `login_service.py:206,240`); 404 `{"detail":"Parent profile not found..."}` when the
Firebase user exists but has no Firestore `parents` doc (`login_router.py:181-185`,
`login_service.py:263`); 422 when Pydantic validation fails (e.g. password shorter than 8);
500 `{"detail":"Login failed. Please try again later."}`.

### 3.2 POST /api/auth/login/phone — parent phone + OTP login
Handler `login_router.py:203-308`; service `login_service.login_with_phone` (`login_service.py:306-426`).
Request model `PhoneLoginRequest` (`login_models.py:65-160`): `phone` must match
`^\+91[6-9]\d{9}$` (:115); `otp` is **required** by the model, exactly 6 digits (`^\d{6}$`, :89-94,
:146). The router comment says "make OTP optional" (`login_router.py:272-273`), but Pydantic rejects
a missing `otp` with 422 before the handler sees it — the client must always send a 6-digit OTP.
OTP semantics (phase-01 §6.4–6.5): single-use, 10-minute validity, checked against
`verification_codes` with `type=="phone"` (`login_service.py:336-367`).

Request:
```json
{"phone": "+919876543210", "otp": "123456"}
```
Success 200 `LoginResponse`: same shape as §3.1 with `phone` set, `email` from the parent doc if any.
Errors: 401 invalid/expired/used OTP (`{"detail":"Invalid OTP"}` etc., `login_router.py:296-299`);
404 `No user found with phone: ...` (`login_router.py:289-293`); 422 format errors; 500.

### 3.3 POST /api/auth/login/google — parent Google login
Handler `login_router.py:311-406`; service `login_service.login_with_google` (`login_service.py:429-540`).
Request model `GoogleLoginRequest` (`login_models.py:163-217`): `id_token`, min length 50 (:206).
Success 200 `LoginResponse`; the service creates the parent profile if absent
(`login_service.py:484-507`). Errors: 401 invalid token (`login_router.py:389-397`); 422; 500.

### 3.4 POST /api/auth/token/refresh — rotate parent tokens
Handler `login_router.py:409-498`; service `login_service.refresh_access_token` (`login_service.py:543-665`).
Request model `TokenRefreshRequest` (`login_models.py:220-271`): `{"refresh_token": "<jwt>"}`.
Success 200 `TokenResponse` (`login_models.py:376-419`):
```json
{"token": "<new jwt>", "refresh_token": "<new jwt>", "expires_in": 86400}
```
**Rotation is real**: both tokens are replaced and the `sessions` doc hashes/expiry are updated
(`login_service.py:625-647`). The old refresh token is rejected afterwards (its hash no longer
matches → 401 "Session not found", `login_service.py:595-597`).
Errors: 401 invalid/expired/revoked refresh, session not found (`login_router.py:481-489`,
`login_service.py:578-613`); 422 empty token; 500.

### 3.5 POST /api/auth/logout — parent logout
Handler `login_router.py:501-589`; service `login_service.logout` (`login_service.py:668-744`).
Auth: `Authorization: Bearer <access token>` header (`extract_token_from_header`,
`login_router.py:49-94`; missing/malformed header → 401). Success 200 `LogoutResponse`
(`login_models.py:422-450`): `{"message": "Logout successful"}`. Effect: the `sessions` doc with the
matching SHA-256 `token_hash` gets `revoked:true` (`login_service.py:713-729`). Note: logout with an
**expired** access token is allowed server-side (`login_service.py:702-706` decodes without
verification), but a totally invalid signature still 401s. Errors: 401 invalid token / session not
found; 500.

### 3.6 GET /api/auth/me — parent profile
Handler `login_router.py:592-716`. Auth: Bearer access token; expired/invalid → 401
(`login_router.py:672-684`); missing parent doc → 404 (`login_router.py:691-696`).
Success 200: the raw Firestore `parents` document as JSON (`login_router.py:687-703`).
**The doc shape varies by registration method** (writers: `simple_register_service.py:62-75`,
`auth_service.py:90-98,200-208,318-327`):

| registration_method | Keys actually present on the doc |
|---|---|
| `simple` | `parent_id`, `name`, `mobile_number`, `email_address`, `language` ("en"), `role` ("parent"), `created_at`, `email_verified`, `registration_method` |
| `email` | `parent_id`, `email`, `language`, `role`, `created_at`, `email_verified`, `registration_method` |
| `phone` | `parent_id`, `phone`, `language`, `role`, `created_at`, `phone_verified`, `registration_method` |
| `google` | `parent_id`, `email`, `language`, `role`, `created_at`, `last_login`, `email_verified`, `registration_method` |

There is no single guaranteed `email`/`phone`/`name` key — the client DTO must treat every field as
optional and read both `email`/`email_address` and `phone`/`mobile_number` (phase-05 relies on this).

### 3.7 Child endpoints (implemented now, UI in phase-07)

| Endpoint | Handler | Request | Success | Notes |
|---|---|---|---|---|
| `POST /api/auth/login/child` | `login_router.py:719-827` | `ChildLoginRequest` (`login_models.py:453-557`): `username` 3–30 `^[a-zA-Z0-9_@.]+$`; `password` 8–50 with ≥1 letter and ≥1 digit | 200 `LoginResponse` with `is_student:true`, `student_id`=`child_id`, `email:"<username>@student.local"`, `message:"Child login successful"` | Plaintext compare server-side (gap #1); wrong creds 401 `{"detail":"Invalid username or password"}` (`login_service.py:781-793`) |
| `POST /api/auth/token/refresh/child` | `login_router.py:830-919` | `TokenRefreshRequest` | 200 `TokenResponse`; rotates both, updates `sessions` doc (`login_service.py:1016-1022`) | 401 on invalid/revoked/missing session |
| `POST /api/auth/logout/child` | `login_router.py:922-1010` | Bearer child access token | 200 `{"message":"Child logout successful"}` | Sets `revoked:true` (`login_service.py:1108-1111`) |
| `GET /api/auth/me/child` | `login_router.py:1013-1144` | Bearer child access token | 200 child doc (Firestore `children` doc + `child_id`) | 401 if token lacks `is_student`; 404 if doc missing |

Child sessions share the `sessions` collection with `user_type:"child"` (`login_service.py:884-894`).

## 4. JWT facts (do not re-derive; cite these)

- Algorithm `HS256` (`token_service.py:38`). Secret: env `JWT_SECRET`, legacy fallback
  `JWT_SECRET_KEY`; generation fails if neither is set (`token_service.py:41-63`).
- Hardcoded expiries in seconds: `ACCESS_TOKEN_EXPIRY = 86400` (24 h), `REFRESH_TOKEN_EXPIRY =
  2592000` (30 d) (`token_service.py:34-35`). The `.env.example` JWT expiry vars are dead config
  (phase-01 §3, §11 gap #12). The client treats the response's `expires_in` as advisory but may rely
  on the 86400 value observed in every login/refresh response.
- Parent access-token claims (`token_service.py:66-143`): `parent_id`, optional `email`, optional
  `phone`, `iat`, `exp`, `type:"access"`. Parent refresh claims (`:145-205`): `parent_id`, `iat`,
  `exp`, `type:"refresh"`.
- Child access-token claims (`token_service.py:375-451`): `child_id`, `student_id` (duplicate of
  `child_id`, :419-420), `username`, `is_student:true`, optional `name`, `iat`, `exp`,
  `type:"access"`. Child refresh (`:454-520`) mirrors with `type:"refresh"`.
- The client never parses JWTs for authorization decisions; it stores tokens opaquely. Expiry
  checks use `expires_in` + `obtainedAt`, not claim decoding.
- Session doc on the server (`login_service.py:100-109`, `:884-894`): `token_hash`,
  `refresh_token_hash` (SHA-256, `login_service.py:37-55`), `access_expires_at`,
  `refresh_expires_at`, `revoked`, `last_activity`; parent docs carry `parent_id`, child docs
  carry `child_id` and `user_type:"child"`.

## 5. Error envelopes and the client-side mapping (phase-01 §4)

Two envelope families coexist:

1. **Legacy `/api/*`** — FastAPI `HTTPException` body: `{"detail": "<string>"}`
   (`core/errors.py:167`). This is what every endpoint in §3 returns on error.
2. **v1 `/api/v1/*`** — `{"error": {"code", "message", "details", "request_id"}}`
   (`core/errors.py:139`). None of this phase's endpoints use it, but the client parser must
   support it because later phases share the same `ApiError` type.
3. Global catch-all: any unhandled exception → HTTP 500 body
   `{"success": false, "error": {...}}` (`main.py:169`).

Client mapping (implemented in `ApiErrorMapper`, step 3 of instructions.md):

| HTTP | v1 `error.code` when present | Client `ApiError.code` when absent (legacy) | `message` source |
|---|---|---|---|
| 400 | `VALIDATION_ERROR` | `VALIDATION_ERROR` | `detail` |
| 401 | `AUTHENTICATION_REQUIRED` | `AUTHENTICATION_REQUIRED` | `detail` |
| 403 | `PERMISSION_DENIED` | `PERMISSION_DENIED` | `detail` |
| 404 | `NOT_FOUND` | `NOT_FOUND` | `detail` |
| 409 | `RESOURCE_CONFLICT` | `RESOURCE_CONFLICT` | `detail` |
| 422 | `VALIDATION_ERROR` | `VALIDATION_ERROR` | `detail` |
| 429 | `RATE_LIMITED` | `RATE_LIMITED` | `detail` |
| 500 | `INTERNAL_ERROR` | `INTERNAL_ERROR` | `detail` |
| 503 | `PROVIDER_UNAVAILABLE` | `PROVIDER_UNAVAILABLE` | `detail` |
| network failure | — | `NETWORK_UNAVAILABLE` | Dio timeout/connection exception category, not raw secret text |

`ApiError` fields: `code: String`, `message: String` (user-presentable, non-null; fall back to a
generic string when `detail` is missing), `httpStatus: Int`, `requestId: String?` read from the
`X-Request-Id` response header (`dependencies.py:51` — stamped on every response by
`RequestIDMiddleware`). If the body is not parseable JSON at all: `code=INTERNAL_ERROR`,
`httpStatus` = actual status, `message` = generic.

## 6. Backend risks encoded as client rules

- **Gap #9 (phase-01 §11):** `login_service.py:215-252` — if env `FIREBASE_API_KEY` is absent, the
  password check is skipped with a warning and **any** password logs in as long as the email exists.
  Client impact: none functionally (send credentials, map the 401). Documented so testers are not
  surprised when wrong passwords succeed in misconfigured dev backends.
- **Gap #1 (phase-01 §11):** child credentials are plaintext at rest (`child_service.py:172`,
  compare at `login_service.py:789-793`). Client rule: never log usernames/passwords; the HTTP
  logging interceptor must redact `Authorization` and never print bodies of login requests beyond
  non-secret fields (see §10).
- **Gap #7 (phase-01 §11) / §6.1:** with the default `TESTING_MODE=true`, routers using
  `get_current_user_testing` ignore the Authorization header and return `"test_parent_123"`
  (`middleware/testing_auth.py:20-42`). Some routers then 500 subscripting that string. Client rule:
  always send the Bearer header anyway (production backends enforce it), and always scope requests
  to ids obtained from the app's own login responses.

## 7. Session storage schema

`flutter_secure_storage` keys are namespaced by role. Tokens are protected by Android Keystore or
iOS Keychain through the plugin. Only `active_role` is stored in `shared_preferences`.

| Key suffix | Dart value | Content |
|---|---|---|
| `parent_session.token` | `String` | parent access JWT from real login/refresh |
| `parent_session.refresh_token` | `String` | parent refresh JWT |
| `parent_session.actor_id` | `String` | response `parent_id` |
| `parent_session.display_name` | `String?` | response login/profile name/email |
| `parent_session.is_student` | `bool` | validated false for parent |
| `parent_session.obtained_at` | `int` | client storage timestamp |
| `parent_session.expires_in` | `int` | response `expires_in` |
| `child_session.*` | same fields | child equivalents; actor ID from `child_id` |
| `active_role` | `String?` | non-secret `PARENT`/`CHILD` pointer in preferences |

Rules:

- Saving or clearing one role never modifies the other role's values.
- `active_role` controls Bearer selection; role switching never copies tokens.
- `requireToken(role)` returns the stored token or throws `NoSessionException`.
- Required response fields are validated; no fixed actor ID, display name, role, token, or expiry is
  substituted when the response is incomplete.
- Token rotation persists the new pair before any original request is retried.

## 8. ApiResult, ApiError, SessionEvent

```dart
sealed class ApiResult<T> {
  const ApiResult();
}
final class ApiSuccess<T> extends ApiResult<T> {
  final T data;
  const ApiSuccess(this.data);
}
final class ApiFailure<T> extends ApiResult<T> {
  final ApiError error;
  const ApiFailure(this.error);
}

final class ApiError {
  final String code;
  final String message;
  final int httpStatus; // 0 for transport failures
  final String? requestId;
  const ApiError(this.code, this.message, this.httpStatus, this.requestId);
}

sealed class SessionEvent { const SessionEvent(this.role); final Role role; }
final class SessionExpired extends SessionEvent { const SessionExpired(super.role); }
final class LoggedOut extends SessionEvent { const LoggedOut(super.role); }
```

A singleton broadcast `StreamController<SessionEvent>` publishes events. Later Riverpod controllers
listen only for their role, clear role-scoped state, and route to that role's login.

## 9. Refresh state machine

States: `Idle → Refreshing → Retrying → Idle`, or `Refreshing → Cleared`.

1. Dio receives 401 on an authenticated request; refresh calls and already-retried requests are
   excluded.
2. Concurrent failures for a role await one shared refresh `Future`.
3. `SessionRepository.refresh(role)` calls the role-correct endpoint with that role's stored refresh
   token through bare Dio.
4. Success persists both real returned tokens atomically, then retries each original request exactly
   once with the new access token.
5. Failure clears only that role, emits `SessionExpired(role)`, and returns the original auth error.
6. A retry that returns 401 never triggers another refresh.

## 10. Logging and security rules

- Debug logging is limited to sanitized method/path/status/timing. Authorization, cookies, auth
  request bodies, and response bodies are never logged. Release registers no HTTP logger.
- Tokens, passwords, OTPs, and refresh tokens never enter debugPrint, crash reports, analytics,
  dart-defines, or source.
- Development cleartext is scoped to the configured local backend; release requires HTTPS. Phase 13
  owns release hardening and pinning decisions.
- A transport/server/parse failure returns `ApiFailure`; it never fabricates a session or profile.

## 11. File map

| Path under `Android_App/lib/` | Contents |
|---|---|
| `features/auth/data/dto/auth_dtos.dart` | Request/response DTOs and generated JSON mapping |
| `features/auth/data/datasources/auth_remote_data_source.dart` | Ten real Dio calls |
| `features/auth/data/repositories/session_repository_impl.dart` | Real login/refresh/logout/me implementation |
| `features/auth/domain/repositories/session_repository.dart` | Repository contract returning `ApiResult` |
| `core/network/api_result.dart` | Result and error types |
| `core/network/api_error_mapper.dart` | All envelope/transport/parse mapping |
| `core/network/auth_interceptor.dart` | Bearer, single-flight refresh, retry-once |
| `core/network/dio_provider.dart` | Configured feature and bare refresh Dio providers |
| `core/session/session.dart` | Session and role models |
| `core/session/secure_session_storage.dart` | Role-isolated secure storage |
| `core/session/session_manager.dart` | Save/restore/switch/clear/token API |
| `core/session/session_events.dart` | Broadcast role-scoped events |

Tests mirror these paths under `test/`. Protocol responses are confined to tests; live sign-off uses
the running backend and real accounts created through documented endpoints.
