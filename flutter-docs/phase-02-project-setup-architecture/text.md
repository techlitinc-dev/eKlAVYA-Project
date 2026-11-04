# Phase 02 — Reference (text.md)

Architecture contract for the Flutter app and the existing superadmin panel. Backend facts are
cited from Phase 01 and from repository source files. Nothing here invents backend behavior.

---

## 1. Architecture rationale

**Feature-first layers with unidirectional state.** Every screen follows:

```text
go_router route → Page (widget) → Riverpod Notifier<UiState>
                                      ↓
                              domain repository contract
                                      ↓
                         remote data source (Dio) → real API
```

- A page watches one immutable `UiState` (`loading`, `content`, `empty`, or `error` as appropriate)
  and sends user intent to its `Notifier`. It does not fetch data directly.
- A repository maps DTOs to domain models and returns `ApiResult<T>`. It has no in-memory demo
  implementation. Its remote implementation calls the documented endpoint on every live load.
- DTOs remain in the data layer. Domain models and UI never depend on Dio types.
- Riverpod providers construct dependencies and allow transport behavior to be controlled in tests.
  Tests may simulate HTTP status and parsing behavior; application providers never select fake data.
- `Future`/`Stream` are used consistently; no callback-based parallel state channel.

**Dual sessions remain mandatory.** Parent and child tokens use different endpoints and claims and
must remain independently stored, refreshed, and cleared. Neither role may read the other's token.

## 2. Dependency rules

```text
features/*/presentation → features/*/domain → features/*/data → core
router → feature pages and route constants
shared design system → Flutter only
```

1. Presentation contains pages, widgets, controllers, and immutable UI state.
2. Domain contains models and repository contracts; it imports no Flutter, Dio, or storage package.
3. Data contains DTOs, remote data sources, repository implementations, and response caching only
   where a later phase explicitly permits it.
4. `core/` contains configuration, network, session, logging, and design-system code.
5. Data/domain never import presentation or router code. Navigation is triggered by UI events.
6. Every runtime list, metric, profile, report, question, and schedule originates in an API response.
   Missing records produce empty UI; failures produce error UI. No fallback dataset is allowed.

## 3. Project tree

```text
Android_App/
├── pubspec.yaml
├── pubspec.lock
├── analysis_options.yaml
├── android/                         Flutter-generated Android host
├── ios/                             Flutter-generated iOS host
├── integration_test/
│   └── app_flow_test.dart           real-backend flows added in later phases
├── lib/
│   ├── main.dart                    ProviderScope + EklavyaApp
│   ├── app.dart                     MaterialApp.router stub
│   ├── core/
│   │   ├── config/app_config.dart
│   │   ├── design_system/            Phase 03
│   │   ├── logging/log_sanitizer.dart
│   │   ├── network/
│   │   │   ├── api_error.dart
│   │   │   ├── api_error_mapper.dart
│   │   │   ├── api_result.dart
│   │   │   ├── auth_interceptor.dart
│   │   │   └── dio_provider.dart
│   │   └── session/
│   │       ├── session.dart
│   │       ├── session_scope.dart
│   │       ├── session_manager.dart
│   │       ├── secure_session_storage.dart
│   │       └── session_providers.dart
│   ├── router/
│   │   ├── app_router.dart
│   │   └── routes.dart
│   └── features/
│       ├── auth/{data,domain,presentation}/
│       ├── parent/{data,domain,presentation}/
│       └── child/{data,domain,presentation}/
└── test/
    ├── core/
    └── helpers/                     test utilities only, never app data providers
```

## 4. Riverpod provider map

| Provider | Lifetime | Responsibility |
|---|---|---|
| `appConfigProvider` | singleton | validated base URL and build-mode flags |
| `secureStorageProvider` | singleton | `FlutterSecureStorage` instance |
| `sessionStorageProvider` | singleton | role-isolated encrypted token/metadata storage |
| `sessionManagerProvider` | singleton | active scope and session stream |
| `refreshDioProvider` | singleton | bare Dio used only for token refresh; no auth interceptor |
| `dioProvider` | singleton | configured Dio with auth/refresh and sanitized debug logging |
| repository providers | singleton | real remote repository implementations only |
| screen controller providers | auto-dispose where appropriate | immutable screen state and user intent |

Do not override repository providers with demo implementations in `main.dart`, previews, or release
code. Design-system catalogs render component states with fixed visual labels only; they must not
pretend to be production feature screens or records.

## 5. Session contract

### 5.1 Fields

| Field | Dart type | Source |
|---|---|---|
| `token` | `String` | login response `token`; secure storage |
| `refreshToken` | `String` | login response `refresh_token`; secure storage |
| `actorId` | `String` | parent `parent_id`; child `child_id` |
| `displayName` | `String?` | login/profile response, never a hardcoded name |
| `isStudent` | `bool` | login response `is_student` |
| `obtainedAtEpochMs` | `int` | client clock at login |
| `expiresInSeconds` | `int` | login response `expires_in` |

### 5.2 API surface

```dart
abstract interface class SessionManager {
  Future<void> saveParentSession(Session session);
  Future<void> saveChildSession(Session session);
  Stream<Session?> get activeSession;
  Future<void> clear(SessionScope scope);
  Future<void> switchTo(SessionScope scope);
  Future<String> requireToken(SessionScope scope);
}
```

Saving one role never overwrites the other. Saving sets that role active. Clearing a role removes
only that role's values. Refresh replaces both tokens atomically within that role's namespace.

### 5.3 Storage layout

Use separate secure-storage prefixes `parent_session.*` and `child_session.*` for token, refresh
token, actor id, display name, role flag, obtained-at, and expiry. Only `active_session_scope` and
non-sensitive preferences belong in `shared_preferences`. Android uses encrypted shared preferences
and Keystore-backed keys through `flutter_secure_storage`; iOS uses Keychain. Never put tokens in
`shared_preferences`, source code, logs, or dart-defines.

## 6. Navigation contract

### 6.1 Topology

```text
GoRouter refreshListenable: session state
├── auth routes: /auth/login-parent, /auth/register-parent, /auth/login-child
├── parent shell: /parent/dashboard and Phase 05–11 children
└── child shell: /child/dashboard and Phase 07–11 children
```

The redirect reads restored session state: child session → child branch, parent session → parent
branch, no session → auth. Role switching never carries a token across branches.

### 6.2 Route names and paths

| Constant | Path | Arguments |
|---|---|---|
| `loginParent` | `/auth/login-parent` | — |
| `registerParent` | `/auth/register-parent` | — |
| `loginChild` | `/auth/login-child` | — |
| `parentDashboard` | `/parent/dashboard` | — |
| `parentChildProfile` | `/parent/child-profile` | — |
| `parentScheduleTest` | `/parent/schedule-test` | — |
| `parentResults` | `/parent/results` | optional `analyticsId` query parameter |
| `childDashboard` | `/child/dashboard` | — |
| `childTestList` | `/child/tests` | — |
| `childTestTaking` | `/child/tests/:testId` | required path id returned by backend |
| `childResults` | `/child/results/:testId` | required path id returned by backend |
| `childSchedule` | `/child/schedule` | optional `scheduleId` query parameter |

IDs are always session- or endpoint-derived. Never type a fixed ID into router or repository code.

## 7. Error mapping

`ApiErrorMapper.fromResponse` recognizes all backend envelopes:

1. `{"error":{"code","message","details","request_id"}}`.
2. `{"detail":"..."}` including FastAPI validation detail lists.
3. `{"success":false,"error":{"type","message",...}}`.
4. Non-JSON or unexpected bodies, mapped without inventing server messages.

| Condition | Client meaning | Default UI behavior |
|---|---|---|
| 401 | authentication required | role-scoped refresh once, then re-auth |
| 403 | permission denied | denial state; never refresh/retry loop |
| 404 | missing or inaccessible record | not-found/empty state |
| 409 | conflicting state | conflict message and refresh when documented |
| 400/422 | invalid input | field/global validation error |
| 429 | rate limited | retry only after user action/backoff |
| 500/502/503 | server/provider failure | error and retry |
| timeout/socket failure | offline/unreachable | offline state and retry |
| decoding failure | contract drift | generic parse error; log sanitized details |

No mapper manufactures domain records on error.

## 8. Configuration and builds

`AppConfig` reads `String.fromEnvironment('EKLAVYA_BASE_URL')`. In debug mode an empty value may
resolve to `http://10.0.2.2:8000` for Android emulators and `http://localhost:8000` for iOS
simulators. Physical devices must receive the development machine's reachable LAN URL explicitly.
Release builds require an explicit HTTPS URL and fail fast when it is absent or invalid.

```bash
flutter run --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
flutter build apk --release --dart-define=EKLAVYA_BASE_URL=https://api.example.org
```

Cleartext is development-only and restricted by the native host configuration. No server secret is
compiled into the Flutter application.

## 9. Superadmin panel conventions

Phase 12 continues the existing React application; it is not rewritten as Flutter Web.

| Convention | Value | Source |
|---|---|---|
| HTTP | shared axios instance / `apiFetch` | `Frontend_Website/src/lib/api.ts:6-43` |
| Base URL | `VITE_API_BASE_URL`, default `http://localhost:8000` | `api.ts:3-4` |
| Session keys | `eklavya_token`, `eklavya_user` | `AuthContext.tsx:57-79` |
| Routes | existing `/superadmin/*` routes | `App.tsx:118-157` |
| Stack | React 19, Vite, TypeScript, Tailwind v4 | `Frontend_Website/package.json` |
| Endpoint scope | only 16 `superadmin` endpoints plus existing demo-session switcher | Phase 01 §9.6 |

## 10. Backend facts retained

- APIs are under `/api/*`; health is `/health`; OpenAPI is `/api/openapi.json`.
- Parent and child sessions are separate and refresh rotates both tokens.
- Child `student_id` equals `child_id`.
- Current backend auth gaps do not permit omitting Bearer headers or using arbitrary IDs.
- Backend mocks and hardcoded responses identified in Phase 01 are defects/limitations, not a
  license to add another fabricated client-side data layer.
