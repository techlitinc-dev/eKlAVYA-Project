# Phase 02 — Expected Output & Sign-off

## Deliverables

1. `Android_App/` is a Flutter project that analyzes, tests, builds, installs, and launches.
2. The backend runs via `./run.sh backend`; `/health` and `/api/openapi.json` respond.
3. The feature-first architecture, Riverpod providers, session contracts, and go_router routes match
   `text.md`.
4. Existing React superadmin conventions are recorded without changing web code.
5. No application feature displays fake, dummy, canned, or hardcoded remote data.

## Verification checklist

### Backend

- [ ] `curl --fail http://localhost:8000/health` returns the real health response.
- [ ] `curl --fail http://localhost:8000/api/openapi.json` returns the real OpenAPI document.

### Flutter project

- [ ] `pubspec.yaml`, `pubspec.lock`, `analysis_options.yaml`, and generated Android/iOS hosts exist.
- [ ] Native application/bundle ID is `ai.eklavya.app`; Dart package is `eklavya_app`.
- [ ] Only the approved Flutter stack is used; there is no Kotlin/Compose/Hilt/Retrofit app layer.
- [ ] `flutter analyze` and `flutter test` pass.
- [ ] `flutter build apk --debug --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000` succeeds.
- [ ] The debug app launches on an emulator and shows only the scaffold.
- [ ] iOS launch is verified on a simulator when iOS is in the implementation target.
- [ ] Release configuration rejects a missing/non-HTTPS base URL.

### Architecture and files

- [ ] `core/config`, `core/network`, `core/session`, `core/design_system`, `core/logging`, `router`,
      and `features/{auth,parent,child}` match `text.md` §3.
- [ ] Presentation, domain, and data dependencies flow only in the allowed direction.
- [ ] Riverpod constructs real repositories; no production provider selects an in-memory repository.
- [ ] go_router paths and required parameters match `text.md` §6 verbatim.
- [ ] `Session` has exactly the seven documented fields and `SessionManager` exposes the documented
      operations.
- [ ] Parent and child secure-storage namespaces are isolated; active role is non-secret metadata.
- [ ] Dio maps all backend error envelopes and never converts an error into a domain record.

### Real endpoint data audit

- [ ] No fake, dummy, sample, demo, or static repository is registered in application code.
- [ ] No Dart feature file contains hardcoded profile names, scores, exam lists, questions, analytics,
      schedules, IDs, or dashboard metrics presented as remote data.
- [ ] No catch/fallback branch returns fabricated content after a failed request.
- [ ] Empty responses render empty UI and failures render error/backend-blocked UI.
- [ ] Contract examples are confined to documentation and protocol tests; end-to-end flows use the
      running backend.
- [ ] Any permitted offline cache contains only previously successful endpoint responses and is
      visibly marked stale.

### Superadmin conventions

- [ ] Existing axios, session-key, route, and Tailwind conventions are cited from `Frontend_Website/`.
- [ ] Phase 12 remains a React extension, not an unapproved Flutter Web rewrite.

## Gap log

| # | Phase 01 reference | Impact | Required handling |
|---|---|---|---|
| 1 | #7 auth bypass / ownership | Dev backend may not enforce caller identity | Send Bearer tokens and session-derived IDs; never fabricate auth errors/data |
| 2 | #1 plaintext child credentials | Credential leakage risk | Never log or persist passwords; secure tokens only |
| 3 | #12 dead JWT expiry config | Client cannot rely on server env names | Store response `expires_in`; never infer user/session data |

Record any newly discovered backend defect with source evidence and a Phase 01 gap reference.

## Sign-off rule

Phases 03 and 04 may start only when all applicable checks pass. If the Flutter stable toolchain
requires a dependency update, resolve and lock a mutually compatible set; do not replace the fixed
architecture or introduce a runtime data substitute.
