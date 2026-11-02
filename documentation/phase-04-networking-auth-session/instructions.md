# Phase 04 — Instructions

Sequential build steps for the implementer. Execute in order; each step names the test(s) that
prove it. Guardrails state what **not** to do. This phase writes no UI except the
session-expired contract consumed by ViewModels (step 11).

Preconditions (verify before step 1):
- Phase-02 decisions are in place: package `ai.eklavya.app`; Hilt, Retrofit, OkHttp,
  kotlinx-serialization, DataStore dependencies; `BuildConfig.EKLAVYA_BASE_URL` defaulting to
  `http://10.0.2.2:8000`.
- Phase-03 design tokens exist (you will not need them except naming `ErrorState` in step 11's
  contract note).
- Backend boots via `./run.sh backend` and answers at `http://localhost:8000/health`.

## Step 1 — DTOs: `data/dto/AuthDtos.kt`

Create one file with `@Serializable` data classes whose property names match the backend JSON
**byte-for-byte** (text.md §3). Required classes:

Requests: `EmailLoginRequest(email, password)`, `PhoneLoginRequest(phone, otp)`,
`GoogleLoginRequest(id_token)`, `ChildLoginRequest(username, password)`,
`TokenRefreshRequest(refresh_token)`.

Responses — every response field must be nullable or have a default, because the legacy routers
return raw dicts and Firestore docs with variable keys:
`LoginResponse(token, refresh_token, parent_id?, email?, phone?, expires_in = 86400,
student_id?, child_id?, username?, name?, is_student = false, message?)` (matches
`login_models.py:274-373`); `TokenResponse(token, refresh_token, expires_in)`; 
`LogoutResponse(message)`; `ParentProfileResponse` as a flexible doc: serialize as
`JsonObject`-backed class or a data class with **all-optional** fields covering every key listed in
text.md §3.6 (`parent_id`, `name`, `email`, `email_address`, `phone`, `mobile_number`, `language`,
`role`, `email_verified`, `phone_verified`, `registration_method`, `created_at`, `last_login`).
Same for `ChildProfileResponse` from `/me/child` (`child_id`, `parent_id`, `firebase_uid`, `name`,
`age`, `grade`, `current_level`, `username`, `email`, `created_at`, `updated_at`, `last_login` —
never map `password`; add `@SerialName`-driven ignore-unknown config).

Guardrails: do not rename fields to Kotlin conventions (`id_token`, `refresh_token`,
`repeat_password` stay snake_case). Do not add fields the backend does not send.

Verify with test `AuthDtoSerializationTest`: JSON samples from text.md §3.1/§3.4/§3.7 decode into
the DTOs; `LoginResponse` with all-null optional fields (parent login) decodes; unknown extra keys
are ignored; re-encoding a decoded DTO preserves the original field names.

## Step 2 — Retrofit interface: `data/api/AuthApi.kt`

```kotlin
interface AuthApi {
    @POST("api/auth/login/email")      suspend fun loginWithEmail(@Body body: EmailLoginRequest): LoginResponse
    @POST("api/auth/login/phone")      suspend fun loginWithPhone(@Body body: PhoneLoginRequest): LoginResponse
    @POST("api/auth/login/google")     suspend fun loginWithGoogle(@Body body: GoogleLoginRequest): LoginResponse
    @POST("api/auth/token/refresh")    suspend fun refreshToken(@Body body: TokenRefreshRequest): TokenResponse
    @POST("api/auth/logout")           suspend fun logout(@Header("Authorization") auth: String): LogoutResponse
    @GET("api/auth/me")                suspend fun getMe(@Header("Authorization") auth: String): JsonObject  // or the flexible ParentProfileResponse
    @POST("api/auth/login/child")      suspend fun loginChild(@Body body: ChildLoginRequest): LoginResponse
    @POST("api/auth/token/refresh/child") suspend fun refreshChildToken(@Body body: TokenRefreshRequest): TokenResponse
    @POST("api/auth/logout/child")     suspend fun logoutChild(@Header("Authorization") auth: String): LogoutResponse
    @GET("api/auth/me/child")          suspend fun getMeChild(@Header("Authorization") auth: String): JsonObject
}
```

Guardrails: relative paths without leading slash (Retrofit resolves against the base URL). The
header parameters are passed `"Bearer $token"` by the repository; the interceptor (step 7) is the
primary header mechanism, but `logout`/`me` take it explicitly in this contract so they also work
when the caller composes headers manually in tests.

## Step 3 — Error model and mapper: `data/network/ApiResult.kt`, `ErrorEnvelopeDtos.kt`, `ApiErrorMapper.kt`

Implement `ApiResult<T>` / `ApiError` / `SessionEvent` / `SessionEvents` exactly as text.md §8.
`ErrorEnvelopeDtos` declares:
- `LegacyErrorEnvelope(val detail: String?)` for `{"detail": ...}`;
- `V1ErrorEnvelope(val error: V1ErrorBody?)` with `V1ErrorBody(code, message, details, request_id)`;
- `CatchAllErrorEnvelope(val success: Boolean?, val error: JsonObject?)` for the `main.py:169` shape.

`ApiErrorMapper.map(throwable, response?, moshi/json instance)` implements text.md §5:
1. If a response exists: read `X-Request-Id` header; try `V1ErrorEnvelope`, then
   `LegacyErrorEnvelope`, then `CatchAllErrorEnvelope`; map status→code per the §5 table; message =
   first non-blank of v1 `error.message`, `detail`, catch-all `error`, else a generic string.
2. `HttpException` with unparseable body → `INTERNAL_ERROR` with the actual status.
3. `IOException` (no response) → `ApiError("NETWORK_UNAVAILABLE", generic, 0, null)`.
4. Anything else → `INTERNAL_ERROR`.

Verify with test `ApiErrorMapperTest`: fixtures for a 401 `{"detail":"Invalid email or password"}`,
a 404 detail, a 422 detail, a v1-style `{"error":{"code":"RATE_LIMITED","message":"...","request_id":"r-1"}}`
plus `X-Request-Id: r-1` header (assert `requestId == "r-1"`), a catch-all 500, a 500 with garbage
body, and a socket-timeout `IOException`. Assert every `code` value matches text.md §5.

## Step 4 — Session manager interface: `data/session/Role.kt`, `SessionManager.kt`

```kotlin
enum class Role { PARENT, CHILD }

interface SessionManager {
    val activeRole: Flow<Role?>                       // from active_role key
    suspend fun saveParentSession(response: LoginResponse)   // encrypts + stores parent slot, sets active_role=PARENT
    suspend fun saveChildSession(response: LoginResponse)    // encrypts + stores child slot, sets active_role=CHILD
    suspend fun getActiveRole(): Role?
    suspend fun setActiveRole(role: Role)
    suspend fun clear(role: Role)                     // wipes that slot's 7 keys; clears active_role if it equaled role
    suspend fun requireToken(role: Role): String      // decrypted access token; throws NoSessionException
    suspend fun refreshToken(role: Role): String?     // decrypted refresh token or null
    suspend fun actorId(role: Role): String?
    suspend fun isExpired(role: Role): Boolean        // obtainedAt + expiresIn <= now
}
class NoSessionException : Exception()
```

`saveParentSession`/`saveChildSession` extract: actor id (`parent_id` / `child_id`), name
(`name`), `is_student` (false/true), `expires_in`, and set `obtained_at = now`. Encryption
happens through `TokenCipher` (step 5) — the DataStore edit is a **single** `edit { }` call so a
crash cannot leave half-written token pairs.

## Step 5 — Token cipher: `data/session/TokenCipher.kt`

`interface TokenCipher { fun encrypt(plain: String): String; fun decrypt(cipherText: String): String }`.
Android implementation: AES key "eklavya_session_key" in Android Keystore (AndroidKeyStore),
AES/GCM/NoPadding with a 12-byte IV prepended to the ciphertext; output Base64. GCM tag failures
throw — treat as corrupt session and clear the slot.

Do **not** use `EncryptedSharedPreferences`; DataStore + manual Keystore AES is the phase-02
decision.

Verify (together with step 6) — no standalone UI.

## Step 6 — SessionManager DataStore implementation

`SessionManagerImpl @Singleton @Inject constructor(@ApplicationContext ctx, cipher: TokenCipher)`
using `ctx.sessionDataStore` (Preferences file named exactly `sessions`) with the key table from
text.md §7. Implement every function from step 4; `clear(role)` removes all 7 keys of the slot and
only touches `active_role` when it matches. `requireToken` decrypts; on `NoSessionException` or
decrypt failure it throws `NoSessionException` (decrypt failure also clears the corrupt slot).

Verify with test `SessionManagerTest` (JVM, `kotlinx-coroutines-test`):
- Provide a fake `TokenCipher` (base64 echo) and a DataStore instance backed by a temp file
  (`PreferenceDataStoreFactory` in a temp dir).
- saveParentSession → assert ciphertext (not raw JWT) stored; getActiveRole == PARENT;
  requireToken(PARENT) returns original; child slot untouched.
- saveChildSession afterwards → both slots coexist; requireToken(CHILD) works; parent token intact.
- setActiveRole(CHILD) → AuthInterceptor would read child; clear(CHILD) wipes child keys and
  clears active_role while parent slot survives.
- Corrupt `child_token_enc` (write garbage) → requireToken(CHILD) throws NoSessionException and
  the slot is cleared.

## Step 7 — AuthInterceptor: `data/network/AuthInterceptor.kt`

`class AuthInterceptor @Inject constructor(private val sessionManager: SessionManager) : Interceptor`.
In `intercept(chain)`: read `sessionManager.getActiveRole()`; if null, proceed without a header;
else attach `Authorization: Bearer ${sessionManager.requireToken(role)}`. Skip attachment only for
the refresh endpoints when the caller already set an explicit `Authorization` header (the
repository sets none — refresh sends the token in the JSON body). Never attach the child token to
a parent call or vice versa: the header always comes from the slot of the active role.

Verify with test `AuthInterceptorTest`: fake `SessionManager` (in-memory map); OkHttp
`MockWebServer` + a throwaway OkHttpClient with only this interceptor. Assert: with activeRole=PARENT
the recorded request carries `Authorization: Bearer parent-jwt`; with CHILD it carries the child
token; with no active role the header is absent. Also assert the **parent token never appears** on
a request made while CHILD is active (explicit string check).

## Step 8 — TokenAuthenticator: `data/network/TokenAuthenticator.kt`

`class TokenAuthenticator @Inject constructor(...) : Authenticator` implementing text.md §9.
Structure:
- `private val mutex = Mutex()` and `private val refreshInFlight = AtomicReference<Deferred<TokenResponse?>?>`-style
  single flight, or simpler: guard the whole refresh with `mutex.tryLock`-or-await semantics so
  concurrent 401s serialize.
- `authenticate(route, response)`: return null if `response.request.header("X-Skip-Refresh") != null`
  (the refresh call itself sets this header via an interceptor-local tag so recursion stops).
  Determine the role from `sessionManager.getActiveRole()` (the failing request's token belongs to
  the active slot by construction of AuthInterceptor).
- Call `sessionRepository.refreshTokens(role)` (step 9). On success: tokens were already saved by
  the repository via `saveParentSession`/`saveChildSession`; build the retry request by replacing
  the `Authorization` header with the new token and return it — **once** (track per-request retry
  via `responseCount(response) < 2` helper that walks `priorResponse` chain, the standard OkHttp
  pattern). On failure: `sessionManager.clear(role)`,
  `sessionEvents.events.tryEmit(SessionEvent.SessionExpired(role))`, return null.

Verify with test `TokenAuthenticatorTest` (MockWebServer + real OkHttpClient wired with the
interceptor and authenticator):
- `refreshSuccessRetriesOriginalOnce`: first call to `/api/auth/me` → 401; refresh endpoint returns
  a new token pair; the retried `/api/auth/me` → 200; assert the retried request used the **new**
  token; assert session store holds rotated values.
- `refreshFailureClearsSessionAndEmitsEvent`: refresh → 401 `{"detail":"Session not found. Please login again."}`;
  assert `requireToken` now throws, and a collected `SessionEvent.SessionExpired(PARENT)` arrives.
- `concurrent401sSingleRefresh`: fire two parallel calls that both 401; assert the refresh endpoint
  received exactly **one** request (race handled), both original calls retried, both succeed.
- `noRetryOnRetry`: original 401, refresh succeeds, retry 401s again → no second refresh, null returned.

## Step 9 — SessionRepository: `data/repository/SessionRepository.kt`

`@Singleton class SessionRepository @Inject constructor(private val authApi: AuthApi, private val sessionManager: SessionManager, private val mapper: ApiErrorMapper, private val sessionEvents: SessionEvents)`.

Public suspend functions returning `ApiResult<T>` (wrap with `runCatching`; map exceptions through
`mapper`):
- `loginWithEmail(email, password)` → on Success: `sessionManager.saveParentSession(resp)`,
  emit nothing; return `ApiResult.Success(resp)`.
- `loginWithPhone(phone, otp)`, `loginWithGoogle(idToken)` — same parent path.
- `loginChild(username, password)` → `saveChildSession`.
- `refreshTokens(role)`: read refresh token via `sessionManager.refreshToken(role)` (null →
  `Failure(AUTHENTICATION_REQUIRED)` without a network call); call the parent or child refresh
  endpoint by role; on Success save via the matching save function and return Success; on Failure
  return Failure untouched (authenticator decides whether to clear).
- `logout(role)`: read access token (`requireToken`, catching NoSessionException → treat as
  already logged out Success); call parent/child logout endpoint with explicit
  `Authorization: Bearer` header; on Success (or 401 "Session not found") call
  `sessionManager.clear(role)` and `sessionEvents.events.tryEmit(SessionEvent.LoggedOut(role))`;
  network failure still clears locally (the server session expires on its own) but emits LoggedOut.
- `getMe(role)`: parent → `/api/auth/me`, child → `/api/auth/me/child`, explicit Bearer header.

Verify with test `SessionRepositoryTest` (MockWebServer):
- `loginEmailSuccessSavesParentSession` — enqueue §3.1 success; assert DataStore slot + activeRole.
- `loginEmail401MapsDetail` — enqueue 401 `{"detail":"Invalid email or password"}`; assert
  `ApiError(code="AUTHENTICATION_REQUIRED", message="Invalid email or password", httpStatus=401)`,
  and no session stored.
- `loginEmail500CatchAll` — enqueue a 500 garbage body; assert `INTERNAL_ERROR` and generic message.
- `loginMalformedJson` — enqueue 200 with `{"token": 123}`; assert `INTERNAL_ERROR` (serialization
  failure path), no session stored.
- `refreshRotatesAndPersists` — seed a parent session; enqueue §3.4 response; assert both tokens
  replaced and `obtained_at` bumped.
- `refreshFailureReturnsFailure` — enqueue refresh 401; assert Failure and that the session is
  **still present** (clearing is the authenticator's job).
- `logoutClearsSlotAndEmits` — seed session; enqueue `{"message":"Logout successful"}`; assert slot
  empty, `LoggedOut(PARENT)` event observed.
- `childLoginSuccessSavesChildSession` — enqueue §3.7 success (`is_student:true`,
  `student_id==child_id`); assert child slot only.

## Step 10 — Hilt wiring: `di/NetworkModule.kt`, `di/SessionModule.kt`

`NetworkModule` provides: base-URL-scoped `Retrofit` (kotlinx-serialization converter,
`BuildConfig.EKLAVYA_BASE_URL`); an `OkHttpClient` with `AuthInterceptor`, `TokenAuthenticator`,
30 s connect/read/write timeouts; and **debug-only** `HttpLoggingInterceptor(Level.HEADERS)` with
`redactHeader("Authorization")` added only `if (BuildConfig.DEBUG)` (text.md §10). Provide
`AuthApi`, `ApiErrorMapper` (holds the Json instance), `SessionEvents`.
`SessionModule` binds `TokenCipher` to the Keystore impl and `SessionManager` to the DataStore
impl, both `@Singleton`.

Guardrails: no logging interceptor in release; no `BODY` level anywhere in this phase.

## Step 11 — Session-expired UI contract

No screens are built here. Publish the convention that every ViewModel in later phases:
1. Injects `SessionEvents`.
2. Launches a collector in `viewModelScope`: on `SessionEvent.SessionExpired(role)` set
   `sessionExpired = role` in its UiState; on `SessionEvent.LoggedOut(role)` clear role-scoped state.
3. Screens render the global expired state with phase-03 `ErrorState` ("Session expired. Please log
   in again.") and a primary `GlassButton` navigating to that role's login route.

Prove the contract with the `TokenAuthenticatorTest` event assertions from step 8 plus a small
`SessionEventsTest`: multiple emissions with no collector do not crash (`tryEmit` with buffer),
and a tardy collector still receives the latest event relevant to it (use
`MutableSharedFlow(extraBufferCapacity = 8)` as declared in text.md §8).

## Step 12 — Final sweep

- Run `./gradlew test` (module `app`) — all tests from steps 1–11 pass.
- Grep the codebase: `grep -rn "Authorization" app/src/main/java | grep -i log` must return
  nothing; confirm no `Level.BODY` anywhere; confirm no test or source file hardcodes a real token.
- Record gap-log entries #1 and #9 in `expected-output.md`.
