# Phase 13 — Reference (text.md)

Backend facts come from `flutter-docs/phase-01-repository-analysis-endpoint-inventory/text.md` and
its source citations. Client behavior comes from Phases 02–12.

## 1. Security hardening checklist

### 1.1 Token handling

| # | Requirement | Basis |
|---|---|---|
| T1 | Access/refresh tokens use `flutter_secure_storage`, backed by Android Keystore/iOS Keychain; never plain preferences/files | Phase 04 |
| T2 | Parent and child tokens use separate role namespaces; Dio attaches only the active role token | Phase 04 |
| T3 | Response `expires_in` and server validation are authoritative; no fabricated expiry fallback | Phase 01 §6 |
| T4 | Concurrent 401s share one role-correct refresh; both tokens rotate; original request retries once | Phase 04 |
| T5 | Tokens/passwords/OTPs never enter logs, crash reports, analytics, UI, or dart-defines | §1.3 |
| T6 | Web retains `localStorage["eklavya_token"]` with its documented XSS trade-off | Phase 02/12 |

### 1.2 Session separation guarantees

- S1. `parent_session.*` and `child_session.*` are independent secure-storage namespaces.
- S2. Child logout clears only child values; parent logout clears only parent values.
- S3. Role switching never copies or overwrites the other role's tokens.
- S4. Every request uses IDs from its own login and real endpoint-resolved child/test/analytics/
  schedule records. No fixed identity is accepted from route constants or user-entered IDs.
- S5. Automated integration proves parent login → child login → both present → child logout → parent
  still usable, and the inverse where supported.

### 1.3 LogSanitizer rule

All application log output passes through `LogSanitizer.sanitize`:

- Flutter: `lib/core/logging/log_sanitizer.dart`; raw secret-bearing `debugPrint` and HTTP body logs
  are forbidden.
- Web: `src/lib/logSanitizer.ts`; raw secret-bearing `console.*` is forbidden.
- Redact JWT patterns and values keyed by password/pass/OTP/token/authorization/secret/API key/
  credential. Auth request/response bodies are not logged.
- Tests prove redaction and benign-message passthrough without logging real credentials.

### 1.4 Backend authorization required before production

| Family | Required server behavior |
|---|---|
| `/api/onboarding/*` | Verify JWT; derive parent from token; enforce parent-owns-child; remove query-param identity trust |
| `/api/parent/*` | Verify parent JWT and child ownership |
| `/api/diagnostic-test/*` | Student/parent ownership; only student owner starts/submits own attempt; idempotent transitions |
| `/api/analytics/*` | Parent-owns-child or student self; foreign records return 404 |
| `/api/schedule/*` | Parent owns student or student self; restrict generate/update/regenerate/progress appropriately |
| `/api/superadmin/*` | Verify superadmin JWT and password on login; fail closed |
| Parent email login | Fail closed when Firebase password verification is unavailable |

Clients map 401 to role-correct re-auth and 403 to denial, never refresh-loop 403. Current bypasses
are Phase 01 gaps #7/#8/#9 and are not proof that security works.

### 1.5 Secrets handling

- Server secrets remain only in backend environment configuration and never in Flutter/web/VCS/logs.
- Flutter binaries contain no server secret. Public Firebase client identifiers are distinguished
  from service-account credentials.
- Child passwords are shown once from current user input after real creation and never persisted.
- Real endpoint responses used in evidence are scrubbed of tokens and credentials.

### 1.6 Release transport

Release requires an explicit HTTPS base URL. Optional certificate/SPKI pinning uses a custom Dio
`HttpClient`/`SecurityContext` or native host configuration with current+next pins and a rotation
plan. It must never become an accept-all `badCertificateCallback`. Debug transport tests may use a
separate controlled adapter; production providers never select it.

### 1.7 Superadmin verification

- Sanitize attacker-controlled LaTeX/HTML using DOMPurify before rendering.
- Display `SuperadminSecurityNotice` on every panel page.
- Never display passwords, tokens, JWT payloads, Firebase secrets, or service credentials.
- Audit entries contain actor/action/target only and are capped at 500.
- Destructive actions require typed confirmation/acknowledgement.
- Missing monitoring capabilities use `BlockingNotice`, never fabricated tables or preview rows.

### 1.8 Known client exposure

| Gap | Client posture |
|---|---|
| #1 plaintext child password | Memory-only reveal and strict log hygiene |
| #2/#3 missing credential reset | Disabled/honest unavailable UI; no proposed call |
| #4 mock diagnostic lifecycle | Explicit blocked state; no local questions/scores/results |
| #5 synchronous analytics under 202 | Contract-safe polling; no fake progress |
| #6 collection mismatch | Real empty/error/blocked state; no replacement metrics/plans |
| #7/#8/#9 auth gaps | Send real credentials/tokens, scope IDs, require backend fix pre-production |

### 1.9 Input-validation recap

| Phase | Rules |
|---|---|
| P04/P05 | Name 2–100; valid email; password ≥8 with letter+digit/match; Indian phone contract; six-digit OTP |
| P06 | Age 14–19; grade 9–12; level enum; username 3–30 regex; password 8–50 letter+digit |
| P08 | Exact JEE/NEET subject set; weights non-negative and sum 100; future exam date and ≥30 days |
| P09 | Actual question answer format A–D/empty/numeric; measured nonnegative time; duplicate guard |
| P10 | Real test/student/answers; poll only real analytics ID |
| P11 | Hours 2–8; future exam date; real analytics/schedule/day IDs |
| P12 | PYQ required fields, MCQ A–D, NAT numeric answer/positive tolerance |

Validation tests use fixed inputs to exercise rules; those inputs are not runtime remote data.

## 2. Test strategy

### 2.1 Dart unit and controller tests

- Validators: every valid/invalid branch in §1.9.
- DTOs/mappers: exact contract JSON shapes, unknown keys, nullability, malformed data.
- Riverpod controllers: initial/loading/content/empty/error/retry/session-expiry transitions driven by
  a controlled Dio transport at the remote-data-source boundary.
- Session storage/events: role isolation, rotation, corruption, logout, expiration.
- `LogSanitizer`: redaction rules.
- Do not create `FakeAuthRepository`, `FakeChildRepository`, `FakeTestRepository`, or other fake
  domain repositories that supply static records. Production and controller providers use the real
  repository; tests control only HTTP transport/protocol responses.

### 2.2 Endpoint integration tests

Cover all 59 `flutter` endpoint contracts and 16 superadmin calls at the HTTP layer. Assert method,
path, query, body, Bearer role, status, and parsed shape. Run feature integration against the running
backend with accounts/records created through the documented workflow.

When the current backend blocks a flow, assert the actual error and unavailable UI. A backend-fixed
run verifies the real happy path. No fallback endpoint or local object is used to force a pass.

### 2.3 Error-envelope matrix

| Condition | Required behavior |
|---|---|
| 401 `{"detail":...}` | Role-correct refresh/re-auth; no session/data fabrication |
| 403 | Permission-denied state; no refresh loop |
| 404 | Genuine not-found/empty state; no substitute record |
| 400/422 | Field/global validation from actual detail |
| 409 | Actual conflict/already-submitted handling where documented |
| 500 catch-all | Generic error/retry and sanitized diagnostics |
| v1 error envelope | Parse code/message/details/request ID |
| Timeout/socket | Offline error; retry only as phase permits |
| Malformed success | Parse error; never save/display a partial invented model |

### 2.4 Flutter widget, golden, and integration tests

- Every screen: loading, real-content model, genuine empty, error, retry, and accessibility semantics.
- Design system: token/golden/state/reduced-motion tests with visual-only catalog fixtures.
- Critical: registration validation; child wrong-password no navigation; timer/autosubmit when real
  test is available; duplicate-submit guard; session isolation.
- Feature golden tests may use contract-shaped visual inputs but never become production providers.
- `integration_test` performs real endpoint calls and compares displayed values to responses.

### 2.5 Coverage and commands

```bash
flutter analyze
flutter test
flutter test --coverage
flutter test integration_test --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Gate ≥70% line coverage for data repositories/DTO mappers/validators and Riverpod controllers.
Record the lcov/report path and actual percentages. Web runs `npm test` and `npm run build`.

### 2.6 Web suites

1. Axios auth/base URL/error handling. 2. Auth context/session persistence. 3. DataTable/filter/
pagination with real rows. 4. Question/content forms and sanitization. 5. Mutation confirmation and
error states. 6. Security notice/audit/no-secret rules. 7. Monitoring `BlockingNotice` with zero
fabricated records.

## 3. End-to-end verification (14 steps)

Preconditions: real backend running, Flutter app installed, superadmin reachable, and accounts/
records created through documented endpoints. Fresh parent is preferred; Phase 01 seeded identities
are real backend data when used. Record default/backend-fixed/mixed run mode.

### 3.1 Script

1. **Register parent** using actual form input → 201, no token assumed.
2. **Login parent** → real parent session; `/me` and onboarding/child calls use returned parent ID.
3. **Create child** → 201 record; one-time credentials reveal; verify GET.
4. **Select exam** using returned exam/date and valid weights → 201 selection + diagnostic test ID.
5. **Login child** with created credentials → distinct child session; parent remains.
6. **Read assigned tests** from student endpoint → compare actual list or record gap #4 blocker.
7. **Start and answer** using real fetched test/questions → record responses or gap #4 blocker.
8. **Submit actual answers** → real result or blocker; test duplicate guard where supported.
9. **Generate analytics** with same real test/student/answers → 202 ID or configuration blocker.
10. **View results** through bare report/history for child and parent → compare values or blocker.
11. **Generate schedule** from actual analytics/exam/hours → 201 schedule or gap #6 blocker.
12. **View/update schedule** as child → actual schedule/progress response or blocker.
13. **Verify sessions** through role switches and independent logouts; inspect secure role isolation.
14. **Verify superadmin** real reads/mutations for 16 endpoints; monitoring remains blocked gap #8.

### 3.2 Matrix rules

Each row records actual request, status, sanitized response evidence, UI observation, and pass/blocked.
No mock list, fallback metadata, static report, local schedule, or preview row can convert a blocked
row into a pass. Backend-fixed happy paths are labelled separately from default-backend behavior.

## 4. Traceability re-check

### 4.1 Endpoint mapping

- 59 `flutter` endpoints map to P04–P11 as Phase 01 §10 specifies.
- 16 `superadmin` endpoints map to P12; existing demo-session switcher remains separately classified.
- Web/internal/unused/mock/unsafe endpoints stay out of Flutter.
- No endpoint is silently replaced with a different route when the documented one fails.

### 4.2 Screen/test mapping

| Phase | Required coverage |
|---|---|
| P04 | DTO/error/storage/controller tests; refresh/logout integration; critical session isolation |
| P05 | Registration validators/controllers/widgets; auth/parent integration; real dashboard/report/goals/settings |
| P06 | Validators/widgets; one-time reveal; real child CRUD |
| P07 | Critical wrong-credentials; dashboard section states; isolation/logout |
| P08 | Weight/date validators; real selection/confirmation/preferences/tracker |
| P09 | Runner/timer/duplicate guard where available; current blocked state; start/submit/results integration |
| P10 | Poll controller; report widgets; generate/poll/history/enrichment integration |
| P11 | Validators/viewers/progress/history; generation errors and backend-fixed integration |
| P12 | Seven web suites; real endpoints and blocked monitoring |
| All | Real-data provider audit, no fabricated fallback, accessibility, and session-expiry behavior |
