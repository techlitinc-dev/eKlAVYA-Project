# Phase 13 — Instructions

Run from the repository root with the real backend at `http://localhost:8000`. Flutter lives in
`Android_App/`; superadmin lives in `Frontend_Website/`.

## Step 1 — Flutter security audit

1. Verify access/refresh tokens exist only in role-prefixed `flutter_secure_storage` keys and never
   in `shared_preferences`, Dart source, dart-defines, logs, or screenshots.
2. Run session isolation: parent login → child login → both remain → child logout → parent remains.
3. Verify every Dart log passes `LogSanitizer`; no auth body, token, password, OTP, or response token
   is logged. Release has no HTTP logger.
4. Scan `Android_App/` for server secrets/private keys. Confirm release requires HTTPS and any
   optional pinning validates current+next pins without accepting arbitrary certificates.
5. Verify Dio attaches only active-role Bearer, refreshes once per concurrent 401 group, retries once,
   and clears only the affected role on refresh failure.
6. Verify no fake/demo repository or hardcoded remote record is registered in production providers.

## Step 2 — Web security audit

Confirm DOMPurify in `LatexRenderer`, `SuperadminSecurityNotice` on every panel screen, no-secret
rendering, capped audit entries without secrets, destructive confirmations, and real `BlockingNotice`
for gap #8 monitoring. Run the secrets scan on `Frontend_Website/`.

## Step 3 — Flutter automated suites

```bash
cd Android_App
dart run build_runner build --delete-conflicting-outputs
flutter analyze
flutter test
flutter test --coverage
flutter test integration_test --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Verify controller/repository/mapper/validator coverage is ≥70%, golden/widget tests pass, and these
critical flows are covered: registration validation, child wrong-password, timer/autosubmit where
backend is available, duplicate-submit prevention, and session isolation. Current-backend blocked
paths must pass their explicit unavailable-state tests.

Protocol tests may use controlled Dio adapters for status/JSON behavior. They must not introduce
`Fake*` repositories or static domain datasets into app/controller providers. Live integration uses
real endpoint-created identities and responses.

## Step 4 — Web suites

```bash
cd Frontend_Website
npm test
npm run build
```

Verify the seven Phase 12 suites and production build pass.

## Step 5 — Execute the 14-step real-backend workflow

Follow `text.md` §3 exactly:

1. Register parent. 2. Login parent. 3. Create child. 4. Select exam/schedule diagnostic.
5. Login child without losing parent. 6. Read assigned tests. 7. Start/answer test. 8. Submit.
9. Generate analytics. 10. View child/parent results. 11. Generate schedule. 12. View/update child
schedule. 13. Verify role isolation/logout. 14. Verify superadmin reads/mutations and blocked monitors.

At every step capture the real endpoint/status and compare UI values to the response. Mark backend-
blocked steps blocked with gap numbers; do not use fallback endpoints, local records, or mock success
to mark them passed. Use a backend-fixed environment for otherwise blocked happy paths and label the
run mode.

## Step 6 — Traceability re-check

Confirm all 59 `flutter` endpoints are consumed only by Phases 04–11, all 16 superadmin endpoints by
Phase 12, and web/internal/unused endpoints stay out of the Flutter app. Reconcile every phase screen
with its unit/widget/integration coverage and real-data audit.

## Step 7 — Sign-off

Fill every result in `expected-output.md`, including commit hashes, run mode, actual coverage, test
commands, 14-row matrix, and consolidated gaps. Release remains blocked for any unmet security gate,
red test, fabricated data path, or unacknowledged backend production blocker.
