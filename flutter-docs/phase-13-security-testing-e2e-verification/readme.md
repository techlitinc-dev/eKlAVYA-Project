# Phase 13 — Security, Testing & End-to-End Verification

**Purpose:** Final sign-off for the Flutter app and React superadmin: freeze security posture, run
Flutter/web test strategies, execute the 14-step real-backend workflow, re-check endpoint
traceability, and record blockers honestly.

This phase changes no application or backend code. It executes against Phases 02–12 deliverables.

## Sources

- Phase 01 §4, §6, §7.B–I, §9–§12 for contracts, workflows, traceability, gaps, and seeded identities.
- Backend token/auth evidence in `token_service.py`, `child_service.py`, `testing_auth.py`, and
  `superadmin_router.py`.
- Flutter app `Android_App/` from Phases 02–11.
- React panel `Frontend_Website/` from Phase 12.

## Fixed decisions

1. Flutter tokens use `flutter_secure_storage` with Android Keystore/iOS Keychain and separate
   parent/child namespaces. Dio attaches only the active role's Bearer token.
2. All Dart logging passes `LogSanitizer`; raw secret-bearing `debugPrint`/HTTP logs are forbidden.
3. Tests use `flutter_test`, controlled Dio transport for protocol behavior, golden/widget tests,
   and `integration_test` against the running backend. No `Fake*` production or controller-test
   repository layer supplies domain records.
4. Coverage gate: ≥70% line coverage on data repositories/mappers/validators and Riverpod controllers.
5. Web uses vitest + Testing Library and the existing Phase 12 security controls.
6. Backend gaps are recorded, never hidden with fake/dummy/hardcoded data or local success paths.

## What this phase contains

- `instructions.md` — security audit, Flutter/web commands, 14-step demo, traceability, sign-off.
- `text.md` — hardening contract, test matrix, E2E script/matrix, and screen coverage.
- `expected-output.md` — release checklist, executed matrix, consolidated gaps, final decision.

## Dependencies

Requires Phases 01–12 complete. Nothing depends on this phase; it is the release gate.

## Non-goals

- No backend modification to make blocked steps pass.
- No fabricated API responses presented as live verification.
- No infrastructure penetration or load testing beyond the listed checks.
