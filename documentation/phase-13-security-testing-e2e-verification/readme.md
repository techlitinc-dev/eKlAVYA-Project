# Phase 13 — Security, Testing & End-to-End Verification

**Purpose:** Final phase. (a) Freeze the security posture of both clients and the superadmin
panel, citing the phase-01 gaps that the backend must close before production. (b) Define the
full test strategy (Android unit/integration/Compose, web vitest + Testing Library, coverage
targets, run commands). (c) Execute the 14-step end-to-end verification of the required workflow
with a pass/fail matrix and explicitly documented blockers. (d) Re-check phase-01 §10 endpoint
traceability and per-phase screen test coverage.

**This phase writes documentation only.** It executes against code produced by phases 02–12; it
changes no application code and no backend code. Where the backend blocks a step, the step is
marked blocked with its phase-01 §11 gap number — never worked around.

## Source references

| Item | Value |
|---|---|
| Anchor facts | `documentation/phase-01-repository-analysis-endpoint-inventory/text.md` — §4 (error envelopes), §6 (auth & tokens), §7.B–I (workflow traces), §10 (traceability), §11 (gap list), §12 (demo identities) |
| Backend evidence for security claims | `Backend/services/token_service.py:34-35,53,66-143,375-557` (JWT), `Backend/services/child_service.py:172` (plaintext child password, gap #1), `Backend/middleware/testing_auth.py:20-42` (auth bypass, gap #7), `Backend/routers/superadmin_router.py:413-421` (superadmin password never verified, gap #8) |
| Web client | `Frontend_Website/` — security behavior delivered by phase-12 (DOMPurify in `LatexRenderer`, `SuperadminSecurityNotice`, no-secret-display rule) |
| Android client | `Android_App/` — phases 02–11 (Keystore-backed token storage, DataStore sessions, Clean MVVM, Hilt, Retrofit, MockWebserver test stack per the phase-02 architecture) |

## Fixed decisions (binding)

1. Android security stack: tokens encrypted at rest via Android Keystore (Keystore-backed
   encryption of the token store); parent and child sessions in **separate DataStore entries**;
   OkHttp `AuthInterceptor` injects `Authorization: Bearer`; release builds recommend cert
   pinning (OkHttp `CertificatePinner`).
2. Token/log hygiene: a `LogSanitizer` wrapper gates every log statement (rule in `text.md` §2.3).
3. Test stack: JUnit5 + fakes for unit tests; OkHttp `MockWebServer` for integration tests;
   Compose UI tests (`createComposeRule`) for screens; JaCoCo for coverage; web side uses
   vitest + Testing Library (dev dependencies to add — `Frontend_Website/package.json` ships
   none today).
4. Coverage gate: line coverage ≥ 70% on the Android `data/` layer + ViewModels.
5. Honesty rule (same as all phases): backend gaps are cited, never faked.

## What this phase contains

- `instructions.md` — the executable sequence: security audit checklist, test runs, the 14-step
  demo script, traceability re-check, sign-off.
- `text.md` — the security hardening checklist (§2), the complete test strategy (§3), the E2E
  verification script + matrix (§4), and the traceability re-check with the phase → screen →
  test mapping (§5).
- `expected-output.md` — the consolidated final release checklist: every phase's checklist
  green, the consolidated gap log, the executed demo matrix with blockers.

## Dependencies

Requires phases 01–12 complete (phase-12 gap log feeds §"Consolidated gap log" here). Nothing
depends on this phase; it is the sign-off gate for the whole documentation set.

## Non-goals

- No penetration testing of infrastructure beyond the listed checks.
- No load testing.
- No modification of the backend to make blocked steps pass. The E2E matrix records blockers;
  a backend-fixed environment may be used for steps 8–10 and this is stated per step.
