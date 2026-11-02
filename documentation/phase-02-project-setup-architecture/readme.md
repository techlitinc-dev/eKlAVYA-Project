# Phase 02 — Project Setup & Architecture

**Purpose:** Greenfield scaffolding of the Android application and fixation of the shared
architecture that the Android app and the superadmin panel both follow. At the end of this phase:

1. `Android_App/` is a buildable, installable Android project (empty-but-compiling stubs only —
   no feature code).
2. The backend is running and its health/OpenAPI endpoints are confirmed reachable.
3. The repository conventions that the phase-12 superadmin work must obey are recorded, with
   citations into the existing `Frontend_Website/` code.

**This phase writes scaffolding only.** Login screens, API services, repositories with real
calls, and the design system are built in phases 04–11. The superadmin panel consumes no new
backend endpoints in this phase (its 16 endpoints are inventoried in phase-01 §9.6, consumer
`superadmin`, integrated in phase-12).

## Decisions fixed by this phase (do not relitigate)

| Area | Decision |
|---|---|
| Application id / package | `ai.eklavya.app` (applicationId and Kotlin package root) |
| Language / UI toolkit | Kotlin 2.x, Jetpack Compose (BOM), Material 3 |
| SDK levels | minSdk 26, targetSdk 35, compileSdk 35, JVM 17 |
| Architecture | MVVM, unidirectional state flow (one `UiState` + `StateFlow` per screen) |
| Asynchrony | Kotlin Coroutines + Flow |
| DI | Hilt (KSP) |
| Network | Retrofit + OkHttp + `retrofit2-kotlinx-serialization-converter` |
| Navigation | Navigation Compose |
| Local storage | DataStore Preferences (sessions); Android Keystore (token encryption) |
| Images | Coil |
| Base URL | `BuildConfig.EKLAVYA_BASE_URL`; debug default `http://10.0.2.2:8000` (Android emulator loopback to host `localhost:8000`), overridable per build type |
| Test stack | JUnit4 + kotlinx-coroutines-test, Turbine (Flow), MockWebServer, Compose `createComposeRule`, Hilt testing |

## Source of truth

- Backend facts (API prefixes, OpenAPI location, health route, error envelopes, auth/token
  formats, gap list) come from `documentation/phase-01-repository-analysis-endpoint-inventory/text.md`
  §2, §4, §6, §8, §11. This phase cites them; it does not re-derive them.
- Superadmin-panel conventions are cited from the running code: `Frontend_Website/src/lib/api.ts`,
  `Frontend_Website/src/App.tsx`, `Frontend_Website/src/components/AppShell.tsx`,
  `Frontend_Website/src/context/AuthContext.tsx`, `Frontend_Website/package.json`,
  `Frontend_Website/src/index.css`.

## What this phase contains

- `instructions.md` — numbered steps: run and health-check the backend; create the Gradle build
  files (settings, root/app build scripts, version catalog, properties, wrapper); manifest +
  network security config; Application class; package skeleton for `core/` / `data/` / `domain/`
  / `ui/` / `di/` / `navigation/`; build and install on an emulator; then read-and-record the
  superadmin web conventions. Every step ends with a verification command.
- `text.md` — the architecture contract: module dependency rules, package tree, Hilt module map,
  dual-session model and `SessionManager` API surface, navigation graph topology with exact
  routes, error-mapping strategy for both backend envelopes, build variants, and the superadmin
  conventions with file:line citations.
- `expected-output.md` — the acceptance checklist and gap log.

## Dependents

- Phase-03 consumes the `core/designsystem/` package location and both build pipelines.
- Phase-04 implements networking/session against this phase's `core/network`, `core/session`,
  and `di/` contracts.
- Phases 05–11 implement feature screens inside this phase's `ui/` + `navigation/` structure.
- Phase-12 extends `Frontend_Website` per this phase's recorded conventions.

## Guardrails (apply to this phase)

1. Never modify anything under `Backend/` — backend defects are logged as
   `BACKEND CHANGE REQUIRED` (see phase-01 `text.md` §11), never worked around in the client.
2. No feature code in the Android scaffold: stub classes must compile and do nothing else.
3. No new npm dependencies in `Frontend_Website` in this phase (design tokens in phase-03 use
   Tailwind v4 CSS-first configuration only).
4. All network targets are `http://10.0.2.2:8000` (emulator) in debug builds; the app must still
   send `Authorization: Bearer <token>` on every authenticated call even though the default
   backend ignores it (phase-01 §6.1, gap #7).
