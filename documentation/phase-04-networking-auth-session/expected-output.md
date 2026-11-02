# Phase 04 — Expected Output & Sign-off

## Deliverables of this phase

1. `data/dto/AuthDtos.kt`, `data/api/AuthApi.kt` covering all 12 endpoints in `text.md` §3 with
   byte-exact JSON field names.
2. `ApiResult`/`ApiError`/`ApiErrorMapper` handling **both** error envelopes from phase-01 §4.
3. `AuthInterceptor` attaching the active role's Bearer token; `TokenAuthenticator` doing
   single-flight refresh, rotation persistence, retry-once, and session-clear + `SessionExpired`
   emission on refresh failure.
4. `SessionManager` (DataStore file `sessions`, Keystore-AES-encrypted tokens) with
   saveParentSession/saveChildSession/getActiveRole/setActiveRole/clear(role)/requireToken(role).
5. `SessionRepository` with login/refresh/logout/me returning `ApiResult`.
6. Hilt modules wiring Retrofit/OkHttp/cipher/manager/repository/bus; debug-only redacted logging.
7. `SessionEvents` contract consumed by later-phase ViewModels.

## Verification checklist

- [ ] `./gradlew :app:test` passes. Named tests all green:
      `AuthDtoSerializationTest`, `ApiErrorMapperTest`, `SessionManagerTest`,
      `AuthInterceptorTest`, `TokenAuthenticatorTest`, `SessionRepositoryTest`,
      `SessionEventsTest`.
- [ ] MockWebServer coverage proven: parent login success (200 → session stored, activeRole=PARENT),
      401 (typed `AUTHENTICATION_REQUIRED` with the backend `detail` as message, nothing stored),
      500 catch-all, malformed-JSON 200 (`INTERNAL_ERROR`, nothing stored); refresh rotation
      (both tokens replaced, single atomic DataStore edit); refresh-failure path (Failure returned,
      session intact at repository level, authenticator clears + emits `SessionExpired`);
      concurrent-401 race (exactly one refresh request served, both originals retried).
- [ ] Interceptor demonstrably attaches `Authorization: Bearer <token>` for the ACTIVE role only
      (`AuthInterceptorTest` records requests via MockWebServer; explicit assertion that the parent
      token is absent while CHILD is active).
- [ ] Refresh race handled: `TokenAuthenticatorTest.concurrent401sSingleRefresh` shows one refresh
      call for N simultaneous 401s, and the retried requests carry the rotated token.
- [ ] Tokens never appear in logs: release build has no `HttpLoggingInterceptor`; debug build uses
      `Level.HEADERS` with `redactHeader("Authorization")`; grep for `Level.BODY` in
      `app/src/` returns zero hits.
- [ ] DataStore file `sessions` contains only Base64 ciphertext under `*_token_enc` / `*_refresh_enc`
      keys (inspectable via Device Explorer on a debug run: raw JWT text must not appear).
- [ ] Parent and child sessions coexist independently: `SessionManagerTest` saves both, clears
      child, and shows the parent slot + tokens intact.
- [ ] `SessionEvents` emits `SessionExpired(role)` and `LoggedOut(role)` as specified in
      `text.md` §8.

## Manual smoke check against the dev backend

```bash
./run.sh backend            # http://localhost:8000
```

- Register a parent with `POST /api/auth/register/simple` (see P05 `text.md` §3; works today),
  then in the app (or a scratch `SessionRepository` call from a debug screen) run
  `loginWithEmail` with the same credentials and confirm `ApiResult.Success` with `expires_in=86400`.
- Stop the backend and repeat the call: expect `ApiResult.Failure` with
  `code=NETWORK_UNAVAILABLE` (never a crash, never a raw exception surfacing to callers).

## Gap log (backend facts this phase encodes but does not fix)

| Gap | Phase-01 ref | Evidence | Client stance recorded |
|---|---|---|---|
| #1 Child password plaintext at rest | phase-01 §11 #1 | `child_service.py:172`, `login_service.py:789-793` | Credentials never logged; child-credential surfaces treated as dev-only until backend hashes |
| #9 Parent password check skipped without `FIREBASE_API_KEY` | phase-01 §11 #9 | `login_service.py:215-252` | Client unaffected (still sends credentials, maps 401); testers warned that wrong passwords may "succeed" in misconfigured dev backends |
| #7 Testing bypass ignores Authorization header | phase-01 §11 #7 | `middleware/testing_auth.py:20-42` | Client always sends Bearer and scopes calls to ids from its own login; no silent dependency on backend enforcement |

## Sign-off rule

Phases 05–11 may start only when every box above is checked. Any mismatch between this
documentation and the running backend at commit `d8ab491` is a documentation bug: fix the doc and
record the drift here; if the drift is a genuine backend defect, append it to phase-01 §11 instead
of working around it.
