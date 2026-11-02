# Phase 02 — Reference (text.md)

Architecture contract for the Android app and the superadmin panel conventions. Backend facts
are cited from phase-01 `text.md` (§/¶ numbers refer to that file) and from source
`path/file.py:line`. Nothing here invents backend behavior.

---

## 1. Architecture rationale

**MVVM + unidirectional data flow.** Every screen is:

```
Route (navigation) -> Screen (@Composable, stateless-ish) -> ViewModel (StateFlow<UiState>)
                                                              |
        Repository (ApiResult<T>)  <-  data layer (Retrofit + DataStore)
```

- The ViewModel is the only holder of screen state, exposed as a hot `StateFlow<UiState>` built
  with `stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), UiState.Loading)`.
- UiState is a sealed interface per screen: `Loading`, `Content(...)`, `Error(message, retry)`.
  No two sources of truth for the same data (no separate `isLoading` booleans).
- The Screen composable renders UiState and forwards user events to the ViewModel as functions
  (`onEvent(...)` or lambda props). State flows one way; events flow the other. This keeps every
  screen testable with `createComposeRule` + a fake ViewModel, and every ViewModel testable with
  `kotlinx-coroutines-test` + Turbine.
- Why not MVI/command queue: the app is CRUD-heavy with two simple roles; a sealed `UiEvent` +
  `when` in the ViewModel is sufficient and cheaper for a junior team. Keep it consistent.

**Coroutines + Flow everywhere.** No callbacks, no `LiveData`. Room/DataStore/Retrofit (via
`suspend`) all compose into Flows at the repository edge.

**Hilt for DI** so every class takes its dependencies via constructor and unit tests substitute
fakes without service-locator gymnastics.

**Dual-session model (parent and child sessions stored separately)** because the backend treats
them as disjoint token families: parent tokens carry `parent_id` claims, child tokens carry
`child_id`/`student_id` claims (phase-01 §6.2, §6.3), sessions live in one Firestore collection
differentiated by `user_type` server-side (`login_service.py:884-894`), and refresh/logout
endpoints are per-role (`/api/auth/token/refresh` vs `/api/auth/token/refresh/child`, phase-01
§9.2). Never merge the two into one "current user" bag.

## 2. Module dependency rules

Layers and allowed dependencies (an arrow means "may import"):

```
ui  ->  domain  ->  data  ->  core
 ^        ^         ^         ^
 |________|_________|_________|
           di (wires everything; imports any layer)
navigation -> ui, domain (knows Routes; never the reverse)
```

Rules:

1. `ui/` (feature packages: `ui/parent/...`, `ui/child/...`, `ui/auth/...`, `ui/common/...`)
   may import `domain`, `core`, `navigation` (for route constants and `navigate` lambdas only),
   and framework classes. Each feature package contains `*Screen.kt`, `*ViewModel.kt`,
   `*UiState.kt`, and registers its route in the matching graph file.
2. `domain/` (optional, keep light) holds thin models and use cases that compose repositories.
   No Android imports, no DTOs leaking up.
3. `data/` holds `dto/` (kotlinx-serialization mirrors of backend JSON), `api/` (Retrofit
   interfaces), `repository/` (interface impls returning `ApiResult`), `datastore/`. May import
   `core`. Never import `ui/` or `domain/` interfaces it does not implement.
4. `core/` is bottom: `core/designsystem` (phase-03), `core/network` (ApiResult, error mapper,
   interceptors), `core/session` (models + contracts). May import only the framework and
   `BuildConfig`.
5. **`ui/` is imported only by `navigation/` (to host screens in graphs) and `di/`.** `data` and
   `domain` never import `ui`; if they ever need to trigger navigation, expose a Flow/event and
   let the screen navigate.
6. `di/` and `navigation/` are the only places allowed to see multiple layers.

## 3. Package tree (target state after this phase)

```
Android_App/
├── settings.gradle.kts
├── build.gradle.kts
├── gradle.properties
├── gradle/libs.versions.toml
├── gradlew / gradlew.bat / gradle/wrapper/gradle-wrapper.properties
└── app/
    ├── build.gradle.kts
    └── src/main/
        ├── AndroidManifest.xml
        ├── java/ai/eklavya/app/
        │   ├── EklavyaApp.kt                  @HiltAndroidApp Application
        │   ├── MainActivity.kt                @AndroidEntryPoint, setContent (phase-03 swaps theme)
        │   ├── core/
        │   │   ├── designsystem/              (phase-03; .gitkeep now)
        │   │   ├── network/
        │   │   │   ├── ApiResult.kt           sealed Success/Failure
        │   │   │   ├── ApiError.kt            sealed errors + ApiErrorMapper (both envelopes)
        │   │   │   ├── AuthInterceptor.kt     Bearer header from active session
        │   │   │   └── TokenAuthenticator.kt  401 -> refresh (parent|child) -> retry once
        │   │   └── session/
        │   │       ├── SessionScope.kt        enum PARENT, CHILD
        │   │       ├── Session.kt             @Serializable data class (7 fields, §5.1)
        │   │       ├── SessionStorage.kt      interface read/write/clear
        │   │       ├── SessionManager.kt      interface + SessionManagerImpl
        │   │       └── TokenEncryption.kt     Android Keystore AES/GCM wrapper
        │   ├── data/
        │   │   ├── dto/                       (.gitkeep; phase-04+)
        │   │   ├── api/                       (.gitkeep; phase-04+)
        │   │   ├── repository/                (.gitkeep; phase-05+)
        │   │   └── datastore/
        │   │       └── SessionDataStore.kt    SessionStorage impl, two files (§5.3)
        │   ├── domain/                        (.gitkeep; optional, keep light)
        │   ├── ui/
        │   │   ├── auth/  parent/  child/  common/   (.gitkeep; feature packages)
        │   ├── di/
        │   │   ├── DataStoreModule.kt
        │   │   ├── SessionModule.kt
        │   │   ├── NetworkModule.kt
        │   │   └── RepositoryModule.kt        (empty; bindings added per feature)
        │   └── navigation/
        │       ├── Routes.kt                  exact route strings (§6.2)
        │       ├── EklavyaNavHost.kt
        │       ├── RootGraph.kt               role-deciding start
        │       ├── AuthGraph.kt
        │       ├── ParentNavGraph.kt
        │       └── ChildNavGraph.kt
        └── res/
            ├── values/strings.xml
            ├── values/themes.xml
            ├── xml/network_security_config.xml
            └── drawable/ mipmap/              (launcher icon arrives in phase-03)
```

## 4. DI module map

| Module | InstallIn | Provides / binds | Key details |
|---|---|---|---|
| `DataStoreModule` | `SingletonComponent` | `DataStore<Preferences>` named `"parent_session"` and `"child_session"` (separate `@Named` qualifiers) | Top-level `Context.parentSessionDataStore` / `childSessionDataStore`; never share one file |
| `SessionModule` | `SingletonComponent` | Binds `SessionStorage -> SessionDataStore`; provides `SessionManager` singleton | `SessionManagerImpl` holds the active-scope choice and exposes `Flow<Session?>` |
| `NetworkModule` | `SingletonComponent` | `Json` (`ignoreUnknownKeys = true`, `explicitNulls = false`), `OkHttpClient`, `Retrofit` | OkHttp: `AuthInterceptor`, `TokenAuthenticator`, `HttpLoggingInterceptor` (HEADERS level, **debug only**), 30 s connect/read/write. Retrofit: `baseUrl(BuildConfig.EKLAVYA_BASE_URL)` + `asConverterFactory("application/json".toMediaType())` |
| `RepositoryModule` | `SingletonComponent` | empty abstract class | `@Binds` added per feature (phases 05–11) |

Rules: one Hilt component per app (SingletonComponent) + `@AndroidEntryPoint` on
`MainActivity`/`EklavyaApp`. ViewModels use `@HiltViewModel`. No component depends on
`ActivityRetainedComponent` beyond the default. Never construct Retrofit/OkHttp outside
`NetworkModule`.

## 5. Session manager — contract

### 5.1 `Session` fields (stored per scope)

| Field | Type | Source |
|---|---|---|
| `token` | String (encrypted at rest) | login response `token` (phase-01 §8) |
| `refreshToken` | String (encrypted at rest) | login response `refresh_token` |
| `actorId` | String | parent login: `parent_id`; child login: `child_id` (== `student_id`, phase-01 §7.H) |
| `displayName` | String? | parent: `email`; child: `name` (fallback `username`) |
| `isStudent` | Boolean | login response `is_student` — **the role discriminator** (phase-01 §6.3) |
| `obtainedAtEpochMs` | Long | client clock at login |
| `expiresInSeconds` | Long | login response `expires_in` (currently always 86400; hardcoded server-side — `token_service.py:34-35`) |

### 5.2 `SessionManager` API surface

```kotlin
interface SessionManager {
    suspend fun saveParentSession(session: Session)   // writes PARENT scope + sets active
    suspend fun saveChildSession(session: Session)    // writes CHILD scope + sets active
    val activeSession: Flow<Session?>                 // null when logged out
    suspend fun clear(scope: SessionScope)            // logout; clears that scope only
    suspend fun switchTo(scope: SessionScope)         // parent<->child switching when both exist
}
```

Semantics:

- `saveParentSession`/`saveChildSession` **never** overwrite the other scope; saving a session
  also makes that scope active.
- `activeSession` re-emits on every save/clear/switch; cold-start reads the persisted
  active-scope pointer first.
- `clear(scope)` clears only that scope; if it was active, `activeSession` becomes null until a
  `switchTo` to the remaining scope (if any) or a new login.
- Tokens are encrypted with Android Keystore (alias `eklavya_session_key`, AES/GCM) before
  touching DataStore. Rotation: when a refresh succeeds, both token fields are replaced in the
  same scope (server rotates both — phase-01 §6.2).

### 5.3 Storage layout

Two DataStore Preferences files: `parent_session` and `child_session`, selected by
`SessionScope`. Keys (within each file): `token`, `refresh_token`, `actor_id`, `display_name`,
`is_student`, `obtained_at`, `expires_in`. Active-scope pointer: a third tiny preference
`active_session_scope` inside a `session_meta` file (or a keyspaced entry — pick one and keep
it; the requirement is only that parent and child sessions themselves are isolated).

## 6. Navigation graph topology

### 6.1 Topology

```
RootNavHost (route "root")
├── AuthGraph       (route "auth_graph",       start "auth/login_parent")
├── ParentNavGraph  (route "parent_graph",     start "parent/dashboard")
└── ChildNavGraph   (route "child_graph",      start "child/dashboard")
```

Root start-destination rule (implemented for real in phase-04; scaffold defaults to
`auth_graph`): read `SessionManager.activeSession` once — `isStudent == true` -> `child_graph`,
`isStudent == false` -> `parent_graph`, null -> `auth_graph`. There is deliberately no
cross-graph deep link in phase-02; role switching re-navigates from the root.

### 6.2 Exact routes and arguments (`navigation/Routes.kt`)

Route constants (later phases must use these exact strings):

| Constant | Route | Arguments |
|---|---|---|
| `LOGIN_PARENT` | `auth/login_parent` | — |
| `REGISTER_PARENT` | `auth/register_parent` | — |
| `LOGIN_CHILD` | `auth/login_child` | — |
| `PARENT_DASHBOARD` | `parent/dashboard` | — |
| `PARENT_CHILD_PROFILE` | `parent/child_profile` | — |
| `PARENT_SCHEDULE_TEST` | `parent/schedule_test` | — |
| `PARENT_RESULTS` | `parent/results` | optional `analyticsId` (String, nullable query arg) |
| `CHILD_DASHBOARD` | `child/dashboard` | — |
| `CHILD_TEST_LIST` | `child/test_list` | — |
| `CHILD_TEST_TAKING` | `child/test_taking/{testId}` | required `testId` (String) |
| `CHILD_RESULTS` | `child/results/{testId}` | required `testId` (String) |
| `CHILD_SCHEDULE` | `child/schedule` | optional `scheduleId` (String, nullable) |

Argument rules: path arguments for ids that must exist to render the screen (`testId`);
nullable query-style arguments (`analyticsId`, `scheduleId`) when the screen has a sensible
default. `child/test_taking/{testId}` maps to backend `test_id` values of shape
`test_{12 hex chars}` (phase-01 §4) — never invent id formats.

## 7. Error mapping strategy (both envelopes)

The backend returns two different error envelopes (phase-01 §4):

- v1 `/api/v1/*`: `{"error": {"code", "message", "details", "request_id"}}`
  (`core/errors.py:139`) — not consumed by this app, but the parser must still recognise it.
- Legacy `/api/*` (the workflow stack the app consumes): `{"detail": str}`
  (`core/errors.py:167`); plus a global catch-all 500 `{"success": false, "error": {...}}`
  (`main.py:169`).

`ApiErrorMapper.fromHttp(status, body)` algorithm:

1. If body parses as JSON with `error.code` (v1) -> `ApiError.Http(status, code, message,
   request_id)`.
2. Else if body parses as JSON with `detail` (legacy) -> `ApiError.Http(status, null, detail,
   null)`.
3. Else if body parses as JSON with `success == false` and `error.message` -> `ApiError.Http`.
4. Else -> `ApiError.Http(status, null, fallbackByStatus(status), null)`.

Status mapping (fallbackByStatus):

| HTTP | ApiError subtype | UI default copy |
|---|---|---|
| 401 | `Auth` | "Session expired. Please log in again." |
| 403 | `Http(403, ...)` | "You do not have access to this." |
| 404 | `Http(404, ...)` | "Not found." |
| 409 | `Http(409, ...)` | "This action conflicts with the current state." |
| 422 | `Http(422, ...)` | "Please check the highlighted fields." |
| 429 | `Http(429, ...)` | "Too many attempts. Try again shortly." |
| 500/502/503 | `Http(...)` | "Something went wrong on our side." (503 can be `PROVIDER_UNAVAILABLE` when code present) |
| network/timeout | `Network` | "No connection. Check your network." |
| JSON parse failure | `Parse` | "Unexpected server response." |

All messages are overridable per screen. Because ownership is not enforced server-side today
(phase-01 §6.1, gap #7), the UI additionally treats any 404 for a foreign id as "not found" and
never reveals existence — the app only ever requests ids returned by its own login flow.

## 8. Build variants

| Variant | EKLAVYA_BASE_URL | Notes |
|---|---|---|
| `debug` (default) | `http://10.0.2.2:8000` (override: `-PeklavyaBaseUrl=...`) | Emulator loopback to host `localhost:8000`; cleartext allowed only for `10.0.2.2`/`localhost` via `network_security_config.xml`; logging-interceptor enabled |
| `release` | same property, no baked default beyond the dev value (must be set to an `https://` URL before shipping) | `isMinifyEnabled = false` in scaffold; R8/proguard config is phase-13; signed with debug key only until phase-13 |

Backend endpoints the client targets are all under `/api/*` (phase-01 §2); OpenAPI at
`/api/openapi.json`; health at `/health`.

## 9. Superadmin panel conventions (existing `Frontend_Website` — phase-12 extends this)

Verified in the code at the inspected commit:

| Convention | Value | Source |
|---|---|---|
| HTTP client | single axios instance `api` + `apiFetch` helper | `Frontend_Website/src/lib/api.ts:6-11`, `:21-43` |
| Base URL | `VITE_API_BASE_URL` env, default `http://localhost:8000` | `api.ts:3-4` |
| Auth header | request interceptor reads `localStorage["eklavya_token"]` -> `Authorization: Bearer ...` | `api.ts:13-19` |
| Session keys | `eklavya_token` (string), `eklavya_user` (JSON) | `Frontend_Website/src/context/AuthContext.tsx:57-58`, `:73-74`, `:79` |
| Routing | `react-router-dom` v7; superadmin routes `/superadmin/dashboard`, `/users`, `/questions`, `/content`, `/ai-settings` all render `SuperAdminPortal` inside `AppShell` | `Frontend_Website/src/App.tsx:118-157` |
| Role model | active role inferred from URL (`pathname.startsWith('/superadmin')`), nav array per role, icons via `lucide-react` | `Frontend_Website/src/components/AppShell.tsx:39-43`, `:73-79` |
| Stack | React 19, Vite 6, TypeScript 5.6, Tailwind v4 (`@tailwindcss/vite`), axios, katex, lucide-react | `Frontend_Website/package.json` |
| Styles | Tailwind v4 CSS-first (`@import "tailwindcss"`), Inter base font, JetBrains Mono for code | `Frontend_Website/src/index.css:1-9` |
| Superadmin API | consumes **only** `/api/superadmin/*` (16 endpoints; no auth dependency on any today — phase-01 §7.I, gap #8) | phase-01 §9.6 |

Phase-12 extension rules (fixed now so superadmin work never drifts): new superadmin UI goes in
`Frontend_Website/src/components` (shared) and `src/pages` (screens) under the existing
`/superadmin/*` routes; all data access goes through the `api` instance / `apiFetch`; no new
token storage keys; no new axios instances; the URL-inferred role model in `AppShell` stays the
single source of role truth for the shell.

## 10. Backend facts this phase relies on (citations)

| Fact | Source |
|---|---|
| API under `/api/*` prefixes; OpenAPI at `/api/openapi.json`; health at `/health` | phase-01 §2; `Backend/main.py:132`, `Backend/main.py:212` |
| Two error envelopes + catch-all | phase-01 §4; `Backend/core/errors.py:139`, `:167`, `Backend/main.py:169` |
| Login response carries `is_student`; child `student_id` == `child_id` | phase-01 §6.3, §7.H, §8 |
| Token expiries hardcoded 86400 s / 30 d | phase-01 §6.2; `Backend/services/token_service.py:34-35` |
| Refresh/logout endpoints per role | phase-01 §9.2 (`login_router.py:409`, `:830`, `:501`, `:922`) |
| Auth header ignored in default TESTING_MODE; ownership unenforced | phase-01 §6.1; gap #7 |
| Child credentials stored plaintext (never log them; treat as dev-only) | phase-01 §11 gap #1; `Backend/services/child_service.py:172` |
