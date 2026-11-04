# Phase 13 — Expected Output & Sign-off

## Release checklist

### A. Cross-phase completion

- [ ] Phases 01–12 checklists are green or have explicit backend-blocked entries with evidence.
- [ ] Every production remote value is traceable to a real endpoint response or current user input.

### B. Security gate

- [ ] Tokens use role-isolated `flutter_secure_storage`; no token is in preferences/source/logs.
- [ ] Parent/child coexistence and independent logout integration test passes.
- [ ] Dio active-role Bearer, single-flight refresh, rotation, and retry-once tests pass.
- [ ] Dart `LogSanitizer` and web sanitizer checks pass; release HTTP logging is absent.
- [ ] Release HTTPS/config validation passes; optional pinning never bypasses certificate checks.
- [ ] Flutter/web secret scans are clean.
- [ ] Phase 12 XSS, security-banner, audit, confirmation, and blocked-monitoring checks pass.
- [ ] Backend authorization gaps #7/#8/#9 are tracked as pre-production blockers.

### C. Test gate

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] `flutter test --coverage` reports ≥70% on data repositories/mappers/validators and controllers.
- [ ] Flutter `integration_test` runs against the real backend, including blocked-state assertions.
- [ ] Critical registration, child-login, timer/submit (when available), duplicate-guard, and session-
      isolation tests pass.
- [ ] `npm test` and `npm run build` pass for superadmin.
- [ ] No `Fake*` repository or static domain dataset supplies app/controller state.

### D. Fourteen-step verification matrix

Fill actual status and evidence; never infer pass from a mock.

| # | Flow | Expected real endpoint/result | Actual / blocker |
|---|---|---|---|
| 1 | Parent registration | `POST /api/auth/register/simple` → 201 | |
| 2 | Parent login/profile | login + `/me` → real parent session/profile | |
| 3 | Child creation | `POST /api/onboarding/child` → 201 record | |
| 4 | Exam selection | `POST /api/onboarding/exam/select` → 201 + diagnostic ID | |
| 5 | Child login | `POST /api/auth/login/child` → separate child session | |
| 6 | Assigned tests | student test GET → actual list / gap #4 blocker | |
| 7 | Start/answer | real start/full test / gap #4 blocker | |
| 8 | Submit | real submit/results / gap #4 blocker | |
| 9 | Generate analytics | 202 + real analytics ID / configuration blocker | |
| 10 | View results | bare report/list/insights / blocker | |
| 11 | Generate schedule | 201 real `Schedule` / gap #6 blocker | |
| 12 | Schedule/progress | real schedule/progress response / blocker | |
| 13 | Role isolation | independent stores/logouts and scoped requests | |
| 14 | Superadmin | 16 real endpoints; unavailable monitors blocked gap #8 | |

Run mode: default / backend-fixed / mixed. Flutter commit: `__________`; web commit: `__________`.

### E. Traceability and real-data gate

- [ ] 59 `flutter` + 16 `superadmin` endpoint mappings reconcile with Phase 01.
- [ ] No web/internal/unused endpoint is called by Flutter.
- [ ] Every screen has state/controller/widget coverage and live verification where backend permits.
- [ ] No fake/dummy/canned/hardcoded runtime profile, test, score, analytics, schedule, or success
      response exists.
- [ ] Loading/empty/error/backend-blocked states contain no substitute domain records.

## Consolidated gap log

Carry forward Phase 01 gaps #1–#16 and each phase's observations with source evidence. In particular,
plaintext child credentials (#1), reset omissions (#2/#3), diagnostic lifecycle (#4), synchronous
analytics (#5), collection mismatches (#6), auth/ownership (#7), superadmin auth/monitoring (#8), and
password-check skip (#9) remain explicit production considerations.

## Sign-off rule

Mark the release approved only when security and real-data gates pass, automated suites are green,
and every E2E row is either verified against a real response or explicitly accepted as a documented
backend blocker by the responsible reviewer.
