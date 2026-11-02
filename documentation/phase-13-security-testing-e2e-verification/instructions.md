# Phase 13 — Instructions

Execute in order. Steps 1–4 are audit/test work; step 5 is the live demo; step 6 the
traceability re-check; step 7 sign-off. Record every result in `expected-output.md`.

Repo root is the working directory unless a step says otherwise. Backend at
`http://localhost:8000` (`./run.sh backend`). Android app in `Android_App/`, web app in
`Frontend_Website/`.

## Step 1 — Security audit (Android)

Work through `text.md` §2.1–§2.4 as a checklist. For each item: verify in code, then tick.

1. Token storage: locate the token store (phase-04 deliverable). Confirm tokens are not in plain
   SharedPreferences — they must be encrypted with a key held in Android Keystore
   (`AndroidKeystore`/`MasterKey` from `androidx.security:security-crypto` or equivalent).
2. Session separation: confirm parent session and child session are separate DataStore entries
   with distinct names (e.g. `parent_session.pb` / `child_session.pb`); confirm child logout
   deletes only the child entry. Run the isolation instrumented test
   (`SessionIsolationTest`, §3.4) on an emulator: `./gradlew :app:connectedDebugAndroidTest
   -Pandroid.testInstrumentationRunnerArguments.class=<fqcn>`.
3. LogSanitizer: confirm every `Log.`/`Timber` call site passes through `LogSanitizer.sanitize`;
   grep for direct `Log.d(token…)` style calls and fix any hits (this is an audit — file
   findings; if the finding is in phase-authored code, route it back to that phase's owner).
4. Secrets: confirm no `JWT_SECRET`, `FIREBASE_CREDENTIALS_PATH`, `GOOGLE_API_KEY`, service-account
   JSON, or hardcoded API keys in `Android_App/` (`grep -rn "AIza\|BEGIN PRIVATE KEY\|JWT_SECRET"
   Android_App/` returns nothing). Confirm Firebase `google-services.json` values are the client
   config (api-key is not a server secret) and the file is in `.gitignore` if the project policy
   says so.
5. Cert pinning: confirm the release build flavor defines an OkHttp `CertificatePinner` for the
   API host (recommendation §2.6); debug builds may keep it disabled to allow MockWebserver.
6. AuthInterceptor: confirm it reads only the **active-role** token and attaches
   `Authorization: Bearer`; confirm 401 handling triggers the refresh flow
   (`POST /api/auth/token/refresh` or `/child` variant) exactly once, then logs out on repeated
   401.
7. Input validation: confirm each screen's validators match the recap in `text.md` §2.9
   (registration, child profile, exam selection sum=100, submission answers, schedule
   `daily_study_hours` 2–8).

## Step 2 — Security audit (web / superadmin panel)

1. Confirm `LatexRenderer` runs DOMPurify before `dangerouslySetInnerHTML` (phase-12 Step 3);
   add no other `dangerouslySetInnerHTML` call sites in superadmin code
   (`grep -rn "dangerouslySetInnerHTML" Frontend_Website/src/` lists only the sanitized one).
2. Confirm the no-secret-display rule: `grep -rni "token\|password" Frontend_Website/src/superadmin/`
   shows storage/handling only, no rendering of values; the Users detail drawer never renders a
   `password` field even if present in a response.
3. Confirm `SuperadminSecurityNotice` renders on every superadmin screen (layout-level) and the
   login helper copy matches `phase-12 text.md` §8 verbatim.
4. Confirm localStorage usage is limited to `eklavya_token`, `eklavya_user`,
   `eklavya_all_demo_sessions`, `eklavya_exam`, `eklavya_superadmin_audit` — nothing else.
5. Confirm the four monitoring pages make zero network calls (DevTools Network filter
   `/api/superadmin/(tests|submissions|analytics|schedules|workflow-stats)`).

## Step 3 — Test suites

1. Android unit + integration: `./gradlew test` (or `testDebugUnitTest`). JaCoCo report:
   `./gradlew jacocoTestReport`; verify line coverage ≥ 70% on `data/` + `ui/*/ViewModel*`
   per `text.md` §3.5.
2. Android Compose UI: boot an emulator (`./run.sh android` if provided, else a system-image
   AVD), then `./gradlew connectedDebugAndroidTest`. The five critical tests from §3.4 must
   pass: registration validation, child login wrong-credentials, test-runner timer + autosubmit,
   submission duplicate-guard, session isolation.
3. Web: `cd Frontend_Website && npm install && npm test` (adds the vitest script per §3.6 if
   missing). All suites green.
4. Backend sanity (informational only): `cd Backend && source venv/bin/activate && pytest -q`
   — record the pass/fail count; backend failures are recorded, not fixed (phase rule).

## Step 4 — Backend precondition note

Read `text.md` §4 intro before demoing. Steps 8–10 of the demo (submission persistence,
AI-analysis end-to-end, schedule generation) are **blocked on the default backend** (gaps #4 and
#6). For the demo, either (a) mark them blocked in the matrix, or (b) run them against a
backend-fixed environment and label the matrix column "backend-fixed run". Both are acceptable;
silently skipping is not.

## Step 5 — End-to-end demo script

Execute the 14 steps of `text.md` §4.1 in order using the seeded demo identities where faster
(phase-01 §12: parent `parent_demo_eklavya`, child `child_demo_aarav` / `aarav_jee2026`) — but
execute steps 1–2 with a **freshly registered** parent at least once, since registration is part
of the required workflow. For each step fill the matrix row in `expected-output.md`: endpoints
called, observed result, pass criteria met (yes/no), blockers.

Session-separation mini-procedure within step 13 (today's backend, gap #7):
1. Log in as parent; note the parent dashboard loads.
2. Log in as child **in the same app** without logging the parent out (role switch); confirm the
   parent session entry still exists in DataStore (dump via the debug screen or the isolation
   test).
3. Child-logout; confirm parent entry intact and parent dashboard loads again without re-login.
4. On a backend with gap #7 fixed: repeat with raw calls — child token against
   `GET /api/parent/dashboard/{child_id}` must return 403.

## Step 6 — Traceability re-check

1. Walk the phase-01 §10 mapping table reproduced in `text.md` §5.1; confirm each
   android-classified router group is consumed by exactly the listed phases and each
   superadmin endpoint by phase 12. Confirm no android/superadmin endpoint is consumed by two
   phases and none is unaccounted.
2. Walk the screen-coverage matrix `text.md` §5.2; confirm every phase's screens have at least
   one listed test. Where a cell is empty, that is a release blocker — add the test before
   sign-off.

## Step 7 — Sign-off

1. Every box in `expected-output.md` checked; blockers documented in the consolidated gap log
   with gap numbers.
2. The E2E matrix filled for all 14 steps (PASS / BLOCKED(gap #n) / FAIL-with-note).
3. Record the git commit hash of both clients at sign-off time in `expected-output.md`.
