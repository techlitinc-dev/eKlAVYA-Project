# Phase 02 — Expected Output & Sign-off

## Deliverables of this phase

1. `Android_App/` is a greenfield Android project that **syncs, builds, and installs**: Gradle
   files, manifest, network security config, Application/Activity, and a compiling package
   skeleton for `core/` / `data/` / `domain/` / `ui/` / `di/` / `navigation/`.
2. The backend runs via `./run.sh backend`; `/health` and `/api/openapi.json` respond.
3. Superadmin-panel conventions recorded with `file:line` citations (no web code changed).

## Verification checklist

### Backend

- [ ] `./run.sh backend` starts uvicorn on `http://localhost:8000`.
- [ ] `curl -s http://localhost:8000/health` returns a JSON health body (`Backend/main.py:212`).
- [ ] `curl -s http://localhost:8000/api/openapi.json` returns the OpenAPI spec
      (`Backend/main.py:132`).

### Android project

- [ ] `Android_App/settings.gradle.kts` exists with `rootProject.name = "eklavya-android"` and
      `include(":app")`.
- [ ] `Android_App/gradle/libs.versions.toml` exists and every `version.ref` resolves
      (values exactly as in `instructions.md` Step 4).
- [ ] `Android_App/gradle/wrapper/gradle-wrapper.properties` pins `gradle-8.10.2`; `gradlew`
      is executable.
- [ ] `Android_App/app/build.gradle.kts`: namespace and applicationId `ai.eklavya.app`,
      minSdk 26, targetSdk/compileSdk 35, JVM 17, `buildFeatures { compose = true; buildConfig =
      true }`, both build types declare `EKLAVYA_BASE_URL`.
- [ ] `cd Android_App && ./gradlew clean :app:assembleDebug --console=plain` succeeds from a
      clean tree.
- [ ] APK installs on an API-35 emulator; `ai.eklavya.app/.MainActivity` launches and shows the
      "eKlAVYA scaffold" text (screenshot saved).
- [ ] Debug build contains `http://10.0.2.2:8000` as `BuildConfig.EKLAVYA_BASE_URL`
      (strings scan of the APK), and `-PeklavyaBaseUrl=...` overrides it.
- [ ] `AndroidManifest.xml` declares `INTERNET`, `usesCleartextTraffic="true"`, and
      `@xml/network_security_config`; that XML denies cleartext by default and permits it only
      for `10.0.2.2` and `localhost`.
- [ ] `EklavyaApp` is annotated `@HiltAndroidApp`; `MainActivity` is `@AndroidEntryPoint`.

### File tree (must match `text.md` §3 exactly)

- [ ] `core/network/`: `ApiResult.kt`, `ApiError.kt`, `AuthInterceptor.kt`,
      `TokenAuthenticator.kt`.
- [ ] `core/session/`: `SessionScope.kt`, `Session.kt`, `SessionStorage.kt`,
      `SessionManager.kt`, `TokenEncryption.kt`.
- [ ] `data/datastore/SessionDataStore.kt`; empty `.gitkeep` packages: `core/designsystem`,
      `data/dto`, `data/api`, `data/repository`, `domain`, `ui/{auth,parent,child,common}`.
- [ ] `di/`: `DataStoreModule.kt`, `SessionModule.kt`, `NetworkModule.kt`,
      `RepositoryModule.kt` (last one empty by design).
- [ ] `navigation/`: `Routes.kt`, `EklavyaNavHost.kt`, `RootGraph.kt`, `AuthGraph.kt`,
      `ParentNavGraph.kt`, `ChildNavGraph.kt`.
- [ ] `res/values/strings.xml` (`app_name` = eKlAVYA), `res/values/themes.xml`,
      `res/xml/network_security_config.xml`.

### Contract conformance (spot checks)

- [ ] `Session` has exactly the seven fields of `text.md` §5.1; `SessionManager` exposes
      `saveParentSession`, `saveChildSession`, `activeSession`, `clear`, `switchTo`.
- [ ] `SessionDataStore` uses two DataStore files (`parent_session`, `child_session`).
- [ ] `AuthInterceptor` adds `Authorization: Bearer` and contains no token logging.
- [ ] `TokenAuthenticator` retries exactly once after refresh; refresh endpoints match
      phase-01 §9.2 (parent vs child paths).
- [ ] `ApiErrorMapper` handles both envelopes (`error.code` and `detail`) plus the
      `success:false` catch-all.
- [ ] `Routes.kt` route strings match `text.md` §6.2 verbatim, including
      `child/test_taking/{testId}`.

### Superadmin conventions (no code changes)

- [ ] `api.ts` conventions recorded: base URL default `http://localhost:8000`, Bearer
      interceptor, `apiFetch`.
- [ ] Token keys `eklavya_token` / `eklavya_user` confirmed in `AuthContext.tsx`.
- [ ] Superadmin routes in `App.tsx` and URL-inferred role in `AppShell.tsx` recorded.
- [ ] `package.json` stack recorded (React 19 / Vite 6 / TS 5.6 / Tailwind v4 / RR v7).

## Gap log

| # | Gap (phase-01 §11 reference) | Impact on this phase | Handling |
|---|---|---|---|
| 1 | #7 auth bypass / no ownership enforcement | Client cannot observe auth failure in dev; app still sends `Authorization` everywhere | Documented in `text.md` §7; enforced scoping by ids-from-own-login |
| 2 | #1 child plaintext credentials | Scaffold must never log credentials | `AuthInterceptor`/logging verified to omit tokens; noted for phase-04+ |
| 3 | #12 dead JWT expiry env vars | Client must use `expires_in` from responses, never assume | `Session.expiresInSeconds` field exists per §5.1 |

Any new backend defect found while executing this phase: append it here with `path/file.py:line`
evidence and cite the matching §11 entry (or add a new numbered entry if genuinely new).

## Sign-off rule

Phases 03 and 04 may start only when every box above is checked. If the build files here
conflict with a newer Android toolchain, update the version set as a whole (AGP + Gradle +
Kotlin + KSP together) and record the change in this file's gap log.
