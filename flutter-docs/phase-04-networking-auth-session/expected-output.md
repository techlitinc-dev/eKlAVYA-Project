# Phase 04 — Expected Output & Sign-off

## Deliverables

1. Byte-exact auth DTOs and one real Dio remote data source for all ten auth endpoints.
2. `ApiResult`, `ApiError`, and mapping for legacy, v1, catch-all, network, and parse failures.
3. Active-role Bearer attachment, per-role single-flight refresh, atomic rotation, and retry-once.
4. Secure, independent parent/child session storage and real login/refresh/logout/me repository calls.
5. Riverpod wiring, sanitized debug logging, and role-scoped session events.

## Automated verification

- [ ] `dart run build_runner build --delete-conflicting-outputs` completes without drift.
- [ ] `flutter analyze`, `flutter test`, and the debug APK build pass.
- [ ] DTO tests cover exact field names, optional profile keys, unknown keys, and malformed responses.
- [ ] Error tests cover all envelopes, status codes, request IDs, timeout/socket failure, and parsing.
- [ ] Session tests prove both roles coexist and clearing one preserves the other.
- [ ] Interceptor tests prove only the active role token is attached and public login has no stale
      Bearer token.
- [ ] Concurrent 401s cause exactly one role-correct refresh; each original request retries once.
- [ ] A second 401 causes no refresh loop. Refresh failure clears that role and emits expiration.
- [ ] Successful refresh persists both real response tokens before retry.
- [ ] No session is saved for 401, 500, malformed JSON, or missing required login fields.
- [ ] Release has no HTTP logger; debug logs contain no token, password, OTP, or auth body.

## Real-backend smoke check

Start `./run.sh backend`. Create/use accounts only through the documented registration and child-
profile endpoints, then exercise:

1. Parent email login with tester-entered credentials → real response saved, correct actor ID/expiry.
2. Parent `/me` restore → profile displayed/stored only from the response.
3. Child login → separate child session with response `child_id == student_id`.
4. Role switching → requests carry only the active role token.
5. Child logout → child session gone, parent session intact.
6. Stop backend and retry → `NETWORK_UNAVAILABLE`, no crash and no fabricated success/profile.

Record actual status codes and scrub tokens from evidence.

## Real-data audit

- [ ] No fake/demo/static auth repository or production provider override exists.
- [ ] No hardcoded JWT, parent/child ID, profile, expiry fallback, login response, or success result.
- [ ] Missing/invalid response fields produce a parse/session error, not invented values.
- [ ] Errors never return placeholder profiles or tokens.
- [ ] Contract JSON is used only for serialization/protocol tests, never as a runtime data source.
- [ ] End-to-end auth sign-off uses the running backend and real endpoint-created accounts.

## Gap log

| Gap | Evidence | Client stance |
|---|---|---|
| #1 child plaintext password | `child_service.py:172`, `login_service.py:789-793` | Never log/persist passwords; secure token storage only |
| #7 testing auth bypass | `middleware/testing_auth.py:20-42` | Always send Bearer and session-derived IDs |
| #9 skipped parent password check without Firebase key | `login_service.py:215-252` | Send real credentials; do not present misconfiguration as valid security |

## Sign-off rule

Phases 05–11 start only after automated checks and applicable real-backend flows pass. Backend drift
is documented; it is never hidden with client-side fabricated data.
