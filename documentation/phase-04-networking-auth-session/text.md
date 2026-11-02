# Phase 04 — Networking, Auth & Session (text.md)

Reference material for this phase. Every contract below was verified against
commit `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4` (branch `main`, 2026-11-02).
Citations are `path/file.py:line` relative to the repository root. Phase-01 citations
(`phase-01 .../text.md §n`) refer to `documentation/phase-01-repository-analysis-endpoint-inventory/text.md`.

---

## 1. Stack and fixed project decisions

| Decision | Value |
|---|---|
| Package | `ai.eklavya.app` |
| Language / UI | Kotlin, Jetpack Compose |
| DI | Hilt |
| HTTP | Retrofit + OkHttp + kotlinx-serialization (JSON content type `application/json`) |
| Navigation | Navigation Compose |
| Local storage | DataStore Preferences (file name `sessions` for auth state) |
| Base URL | `BuildConfig.EKLAVYA_BASE_URL`, default `http://10.0.2.2:8000` |
| Token crypto | Android Keystore AES before tokens enter DataStore |
| Roles | `enum class Role { PARENT, CHILD }` — sessions stored separately, never shared |

Nothing in this phase may add dependencies beyond those fixed in phase-02.

## 2. Wire format conventions

- All requests and responses are JSON, UTF-8. Request bodies use kotlinx-serialization
  `@Serializable` data classes; field names must match the backend byte-for-byte (§3).
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
| network failure | — | `NETWORK_UNAVAILABLE` | OkHttp `IOException` message class, not raw text |

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

## 7. Session storage schema (DataStore file `sessions`, private to SessionManager)

Preferences keys (exact strings; `enc` values are Base64 of Keystore-AES ciphertext, never raw JWTs):

| Key | Type | Plaintext? | Content |
|---|---|---|---|
| `active_role` | String | yes | `"PARENT"` \| `"CHILD"` \| `""` (none) |
| `parent_token_enc` | String | no (encrypted) | parent access JWT |
| `parent_refresh_enc` | String | no (encrypted) | parent refresh JWT |
| `parent_actor_id` | String | yes | parent_id |
| `parent_name` | String (nullable) | yes | display name when known (`name` from login/me) |
| `parent_is_student` | Boolean | yes | always `false` for this slot |
| `parent_obtained_at` | Long | yes | epoch seconds when tokens were stored |
| `parent_expires_in` | Long | yes | `expires_in` from the last login/refresh (86400) |
| `child_token_enc` | String | no (encrypted) | child access JWT |
| `child_refresh_enc` | String | no (encrypted) | child refresh JWT |
| `child_actor_id` | String | yes | child_id |
| `child_name` | String (nullable) | yes | child display name |
| `child_is_student` | Boolean | yes | always `true` for this slot |
| `child_obtained_at` | Long | yes | epoch seconds |
| `child_expires_in` | Long | yes | 86400 |

Rules:
- Parent and child slots are independent. Saving one never touches the other.
- `active_role` controls which slot `AuthInterceptor` reads; it is set at login and cleared when
  that role's session is cleared. Switching roles does not delete the other slot's tokens.
- `requireToken(role)`: returns the decrypted access token or throws `NoSessionException` —
  never returns null silently.

## 8. ApiResult, ApiError, SessionEvent (client types, fixed contract)

```kotlin
sealed interface ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>
    data class Failure(val error: ApiError) : ApiResult<Nothing>
}

data class ApiError(
    val code: String,          // AUTHENTICATION_REQUIRED | NOT_FOUND | ... | NETWORK_UNAVAILABLE | INTERNAL_ERROR
    val message: String,       // user-presentable
    val httpStatus: Int,       // 0 for network failures
    val requestId: String?,    // X-Request-Id response header, may be null
)

sealed interface SessionEvent {
    data class SessionExpired(val role: Role) : SessionEvent   // refresh failed server-side; role session cleared
    data class LoggedOut(val role: Role) : SessionEvent        // local clear after successful logout call
}
```

`SessionEvents` bus: `@Singleton class SessionEvents { val events: MutableSharedFlow<SessionEvent> =
MutableSharedFlow(extraBufferCapacity = 8) }`. Every ViewModel in later phases collects this flow
and surfaces `SessionExpired` as a global "session expired, please log in again" state that routes
to the login screen of the given role.

## 9. TokenAuthenticator state machine (single role at a time; enforced per role)

States: `Idle` → `Refreshing` (single flight) → `Retrying` → back to `Idle`; or `Refreshing` →
`Cleared`.

1. OkHttp calls `authenticate(route, response)` only after a 401 (and not for the refresh call
   itself — the refresh request carries a flag header to break recursion; see instructions step 8).
2. If a refresh is already in flight for this role, **await** the in-flight result (single-flight
   mutex); do not start a second refresh.
3. On 401: call `SessionRepository.refresh(role)` with that role's stored refresh token.
4. Success → save rotated tokens via `SessionManager.saveParentSession`/`saveChildSession`
   (keeps `active_role` unchanged), then **retry the original request exactly once** with the new
   access token.
5. Failure (401 from refresh endpoint, network error, malformed body) → `SessionManager.clear(role)`,
   emit `SessionEvents.events.tryEmit(SessionEvent.SessionExpired(role))`, return `null` so the
   original request fails with the 401.
6. Refresh responses always carry new `refresh_token` values (§3.4) — the client must persist both
   new tokens atomically (single DataStore edit) before retrying.

## 10. Logging and security rules (mandatory)

- `HttpLoggingInterceptor` is added **only in debug builds** (`if (BuildConfig.DEBUG)`), level
  `Level.HEADERS`, with `redactHeader("Authorization")`. Bodies are not logged for
  `/api/auth/login/*`, `/api/auth/register/*`, `/api/auth/token/refresh*` (they contain
  credentials/tokens).
- Never write tokens, passwords, OTPs, or refresh tokens to Logcat, Timber, crash reports, or
  analytics. Tokens exist in memory only as `String` inside the session layer and as ciphertext in
  DataStore.
- Certificate pinning / cleartext: the dev base URL is `http://10.0.2.2:8000` (emulator loopback),
  so `usesCleartextTraffic` stays enabled only for that host per phase-02 manifest decisions;
  document the production risk in the gap log (P13 owns hardening).

## 11. File map created by this phase (under `Android_App/` per phase-02 layout)

| Path | Contents |
|---|---|
| `app/src/main/java/ai/eklavya/app/data/dto/AuthDtos.kt` | All request/response DTOs for §3 (exact JSON names, all optional response fields nullable) |
| `app/src/main/java/ai/eklavya/app/data/api/AuthApi.kt` | Retrofit interface, 12 calls |
| `app/src/main/java/ai/eklavya/app/data/network/ApiResult.kt` | `ApiResult`, `ApiError`, `SessionEvent`, `SessionEvents` |
| `app/src/main/java/ai/eklavya/app/data/network/ErrorEnvelopeDtos.kt` | v1 + legacy error DTOs |
| `app/src/main/java/ai/eklavya/app/data/network/ApiErrorMapper.kt` | Both-envelope mapping per §5 |
| `app/src/main/java/ai/eklavya/app/data/session/Role.kt` | `enum class Role { PARENT, CHILD }` |
| `app/src/main/java/ai/eklavya/app/data/session/TokenCipher.kt` | Keystore AES encrypt/decrypt interface + Android impl |
| `app/src/main/java/ai/eklavya/app/data/session/SessionManager.kt` | Interface + DataStore impl per §7 |
| `app/src/main/java/ai/eklavya/app/data/network/AuthInterceptor.kt` | Bearer attach for active role |
| `app/src/main/java/ai/eklavya/app/data/network/TokenAuthenticator.kt` | 401 → refresh → retry once per §9 |
| `app/src/main/java/ai/eklavya/app/data/repository/SessionRepository.kt` | login/refresh/logout/me wrappers returning `ApiResult` |
| `app/src/main/java/ai/eklavya/app/di/NetworkModule.kt`, `SessionModule.kt` | Hilt wiring (OkHttp, Retrofit, cipher, manager, repository, bus) |

Test files (mirror under `app/src/test/java/ai/eklavya/app/`): `AuthDtoSerializationTest`,
`ApiErrorMapperTest`, `SessionManagerTest` (DataStore + fake cipher), `AuthInterceptorTest`,
`TokenAuthenticatorTest`, `SessionRepositoryTest` (MockWebServer). See instructions.md for the
exact list and what each must prove.
