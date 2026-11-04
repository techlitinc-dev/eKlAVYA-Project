# Phase 02 — Project Setup & Architecture

**Purpose:** Create the greenfield Flutter application and fix the shared architecture used by
Phases 03–11. At the end of this phase:

1. `Android_App/` is a buildable Flutter project with Android and iOS targets and compiling stubs
   only—no feature screens or repositories with fake data.
2. The backend is running and its health/OpenAPI endpoints are reachable.
3. The conventions that the Phase 12 React superadmin panel must follow are recorded with citations.

**This phase writes scaffolding only.** Registration, login, real API repositories, and the design
system are implemented in Phases 03–11.

## Decisions fixed by this phase

| Area | Decision |
|---|---|
| Project root | `Android_App/`; Dart package `eklavya_app`; native application/bundle id `ai.eklavya.app` |
| Language / UI | Dart, Flutter stable, Material 3 with the Phase 03 custom theme |
| Architecture | Feature-first presentation/domain/data separation; unidirectional state |
| State and DI | Riverpod; one immutable `UiState` and one `Notifier` per screen |
| Asynchrony | Dart `async`/`await`, `Stream`, and `Future` |
| Network | Dio; JSON DTOs generated with `json_serializable` |
| Navigation | `go_router`, with separate auth, parent, and child branches |
| Secret storage | `flutter_secure_storage`, with isolated parent/child key namespaces |
| Non-secret preferences | `shared_preferences` for active role and non-sensitive settings only |
| Images | `cached_network_image`; remote URLs must come from API data |
| Base URL | `--dart-define=EKLAVYA_BASE_URL=...`; platform-appropriate development defaults |
| Tests | `flutter_test`, `integration_test`, `mocktail` for transport behavior, golden tests |

## Real-data contract

1. The only remote data source is Dio calling endpoints classified `flutter` in Phase 01.
2. Do not create fake repositories, demo collections, canned dashboards, hardcoded exam/topic/test
   lists, or fallback scores. A repository either returns the parsed endpoint response or an error.
3. Loading, empty, error, and `BACKEND CHANGE REQUIRED` states are real UI states, not places to
   insert fabricated content.
4. Cached content is permitted only when it is a previously successful endpoint response, stored
   with its fetch time and visibly identified as stale while offline. It must never replace a live
   request with invented data.
5. Contract JSON in the documentation and protocol fixtures used by automated tests are not runtime
   application data sources. End-to-end sign-off uses the running backend.

## Source of truth

- Backend facts come from `flutter-docs/phase-01-repository-analysis-endpoint-inventory/text.md`
  §2, §4, §6, §8, §9, and §11.
- Superadmin conventions come from `Frontend_Website/src/lib/api.ts`, `src/App.tsx`,
  `src/components/AppShell.tsx`, `src/context/AuthContext.tsx`, `package.json`, and `src/index.css`.

## What this phase contains

- `instructions.md` — backend health check, Flutter scaffold, dependencies, configuration,
  feature-first directories, secure-session contracts, router stubs, analysis, tests, and build.
- `text.md` — architecture rules, directory tree, provider map, dual-session API, routes, error
  mapping, build configuration, and superadmin conventions.
- `expected-output.md` — acceptance checks, real-data checks, verification commands, and gap log.

## Dependents

- Phase 03 implements `core/design_system/` and the web token counterpart.
- Phase 04 implements `core/network/`, `core/session/`, and remote auth data sources.
- Phases 05–11 implement feature screens and repositories inside `features/`.
- Phase 12 extends the existing React panel using the recorded web conventions.

## Guardrails

1. Never modify `Backend/`; record defects as `BACKEND CHANGE REQUIRED`.
2. No feature code or runtime data in this scaffold.
3. No new npm dependencies in `Frontend_Website/` in this phase.
4. Parent and child credentials/tokens are never logged or stored together.
5. Do not introduce Kotlin, Jetpack Compose, Hilt, Retrofit, or native Android ViewModels.
