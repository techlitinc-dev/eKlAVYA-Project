# Phase 04 — Instructions

Execute in order. Preconditions: Phases 02–03 pass, the real backend answers `/health`, and the
Flutter project has the fixed Dio/Riverpod/secure-storage stack. This phase builds no feature UI.

## Step 1 — Auth DTOs

Create `features/auth/data/dto/auth_dtos.dart` with `json_serializable` DTOs for:

- `EmailLoginRequest`, `PhoneLoginRequest`, `GoogleLoginRequest`, `ChildLoginRequest`, and
  `TokenRefreshRequest`;
- `LoginResponse`, `TokenResponse`, and `LogoutResponse`;
- flexible parent/child profile DTOs covering every key in `text.md` §3.6–§3.7.

Use `@JsonKey(name: ...)` for snake_case wire fields and ignore unknown response keys. Never map a
child password. Do not invent defaults for tokens, actor IDs, role flags, names, or expiry: required
session fields are validated from the actual response and missing/invalid fields produce a parse
error rather than a fabricated session.

**Verify:** serialization tests decode the contract shapes, variable profile keys, null optionals,
and unknown keys; generated JSON retains exact wire names.

## Step 2 — Real auth remote data source

Create `AuthRemoteDataSource` using Dio with exactly the ten paths in `readme.md`. Each method makes
the documented GET/POST and returns decoded response data. No method reads a local fixture or returns
a constructed login/profile response.

Refresh uses the separate bare Dio. Logout/me rely on the active-role interceptor; explicit header
attachment is allowed only when testing a call in isolation.

**Verify:** adapter/request tests assert method, path, JSON body, and content type. A live backend
smoke test reaches the real login endpoint with credentials entered by the tester.

## Step 3 — Results, errors, and session events

Finish `ApiResult<T>`, `ApiError`, `ApiErrorMapper`, and `SessionEvent` per `text.md` §5 and §8.
Map `DioException` response bodies in legacy → v1 → catch-all order while retaining status and
`X-Request-Id`. Map connection/timeout and decoding failures without exposing raw secrets.

Use a broadcast `StreamController<SessionEvent>` for `SessionExpired(role)` and `LoggedOut(role)`.

**Verify:** tests cover each envelope, malformed JSON, timeout, socket failure, and event delivery.
No error mapper returns domain data.

## Step 4 — Session model and secure storage

Implement `Role`, seven-field `Session`, `SecureSessionStorage`, and `SessionManager` per `text.md`
§7. Save parent and child values in independent secure-storage namespaces. Write token pairs and
metadata atomically from the caller's perspective; a refresh cannot leave one old token paired with
one new token.

`requireToken` throws `NoSessionException` when absent/corrupt. Corrupt storage clears only the
affected role. `active_role` in preferences never contains a token.

**Verify:** storage tests prove coexistence, role switching, independent clear, corrupt-value
handling, and no token in `shared_preferences` or logs.

## Step 5 — Bearer interceptor

Implement `AuthInterceptor` as a Dio interceptor. On each authenticated feature request, resolve the
current active role and attach only that role's real access token. Public login/register requests do
not receive a stale Bearer token. Refresh calls use their JSON refresh token and bare Dio.

**Verify:** request tests prove parent/child isolation and absence of Authorization on public calls.
The test must not use fixed production identities in application code.

## Step 6 — Single-flight refresh and retry-once

Implement the `text.md` §9 state machine inside the auth interceptor/refresh coordinator:

1. Reject recursive refresh and second retries.
2. Share one in-flight refresh `Future` per role across concurrent 401s.
3. Call the role-correct refresh endpoint through `SessionRepository`.
4. Persist both returned tokens before retrying.
5. Retry each original request once with its new token.
6. On refresh failure, clear only that role and emit `SessionExpired(role)`.

**Verify:** concurrent-request tests observe one refresh and successful retries; second 401 does not
refresh again; refresh failure emits and clears. No synthetic successful response is used by app code.

## Step 7 — Session repository

Implement `SessionRepository` returning `ApiResult` for:

- three parent login methods and child login;
- role-correct token refresh;
- role-correct `/me` restore;
- role-correct logout and local clear.

Save a session only after a real successful login response passes required-field validation. On
logout, clear local role state even if the server is unreachable; report the server failure honestly
and never claim server revocation succeeded. Refresh failure remains a failure until the refresh
coordinator applies its clear/event policy.

**Verify:** protocol tests cover success, 401, 500, malformed success JSON, token rotation, and
logout. Then run parent and child login/restore/logout smoke flows against the running backend using
real accounts created through documented endpoints.

## Step 8 — Riverpod wiring and sanitized logging

Provide `AppConfig`, secure storage, `SessionManager`, bare refresh Dio, configured feature Dio,
remote data source, repository, and session-event stream through Riverpod. Production providers must
always select the real remote implementations.

Debug logging uses sanitized method/path/status/timing only. Disable Authorization, cookie, request
body, and response body logging for auth. Release adds no HTTP logger.

**Verify:** provider graph resolves the real data source; source scan finds no fake/demo repository,
hardcoded token/user ID, credential log, or release HTTP logger.

## Step 9 — Session-expiration UI contract

Later screen controllers listen for session events affecting their role. Expiration clears
role-specific screen state and routes to that role's login using Phase 03 `ErrorState` and
`GlassButton`. Do not show a cached profile as though the session were still authenticated.

**Verify:** a controller test observes the event and reaches the role-correct logged-out state.

## Step 10 — Final verification

```bash
cd Android_App
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter build apk --debug --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Complete the live-backend smoke checks and every item in `expected-output.md`. Record gaps #1, #7,
and #9 without modifying the backend.
