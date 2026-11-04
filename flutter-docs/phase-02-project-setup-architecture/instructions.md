# Phase 02 — Instructions

Execute in order from the repository root unless a step says otherwise. Every step ends with a
**Verify** check. This phase creates scaffolding only and no runtime feature data.

## Part A — Backend precondition

### Step 1. Start and inspect the real backend

```bash
./run.sh backend
```

In another terminal:

```bash
curl --fail --silent http://localhost:8000/health
curl --fail --silent http://localhost:8000/api/openapi.json > /tmp/eklavya-openapi.json
python3 -c 'import json; print(len(json.load(open("/tmp/eklavya-openapi.json"))["paths"]))'
```

**Verify:** health returns JSON and the OpenAPI path count agrees with Phase 01, subject to its
recorded router caveats. Leave the backend running for integration checks.

## Part B — Flutter scaffold

### Step 2. Confirm the toolchain

Install Flutter stable, Android Studio/SDK, and Xcode on macOS when iOS verification is required.

```bash
flutter doctor -v
java -version
```

**Verify:** `flutter doctor` reports no issue that blocks the selected target. Do not create a
Kotlin native app or edit Kotlin host code for application features.

### Step 3. Create the project

```bash
flutter create --org ai.eklavya --project-name eklavya_app --platforms=android,ios Android_App
cd Android_App
```

Set the Android `applicationId` and iOS bundle identifier to `ai.eklavya.app` in the generated host
configuration. Keep Dart package imports as `package:eklavya_app/...`.

**Verify:** `flutter analyze` succeeds before customization and native IDs match the fixed value.

### Step 4. Add the approved dependencies

Add current Flutter-stable-compatible versions and commit the resolved lockfile:

```bash
flutter pub add flutter_riverpod dio go_router flutter_secure_storage shared_preferences \
  json_annotation cached_network_image
flutter pub add --dev build_runner json_serializable mocktail
```

Add the SDK-provided `integration_test` dependency under `dev_dependencies` using the Flutter
project's normal pubspec syntax. Do not add a second state-management, routing, or HTTP stack.

**Verify:** `flutter pub get` and `flutter analyze` succeed; `pubspec.lock` resolves one coherent
version set.

### Step 5. Configure linting

Keep Flutter's standard lints in `analysis_options.yaml`. Enable language features supported by the
selected stable Dart SDK and treat invalid runtime configuration as an error in application code.

**Verify:** `flutter analyze` reports no issues.

### Step 6. Add application configuration

Create `lib/core/config/app_config.dart` according to `text.md` §8. Read the base URL from
`String.fromEnvironment`. Allow platform-specific localhost defaults only in debug mode; require an
explicit HTTPS URL in release mode. Do not put credentials, JWTs, API secrets, user IDs, or response
content in configuration.

**Verify:** debug configuration resolves on the selected emulator/simulator; a release build without
a valid URL fails the documented configuration check.

### Step 7. Configure development networking in native hosts

Declare Internet access in the Flutter-generated Android host. Restrict cleartext traffic to the
documented development loopback/LAN use; do not enable arbitrary cleartext in release. Apply the
corresponding scoped ATS development exception on iOS only when required by the local backend.

**Verify:** release configuration does not permit arbitrary cleartext. No native host contains a
hardcoded user, token, profile, test, report, or schedule.

### Step 8. Create the architecture directories

Create the tree in `text.md` §3 under `lib/`, `test/`, and `integration_test/`. Add only compiling
contracts and empty stubs. Remote data-source interfaces must describe real endpoint calls; do not
add memory repositories, sample records, demo lists, or static feature responses.

**Verify:** no production Dart file contains fabricated domain objects or fallback API responses.

### Step 9. Add core network contracts

Create:

- `ApiResult<T>` with success and failure outcomes;
- typed `ApiError` values;
- `ApiErrorMapper` for all three backend error envelopes, timeouts, socket failures, and decoding
  failures;
- a `dioProvider` with JSON content type, 30-second connect/receive/send timeouts, and the base URL.

Use a separate bare Dio for refresh so refresh cannot recursively trigger the auth interceptor.
Logging is debug-only and passes through `LogSanitizer`; authorization and request bodies containing
credentials are redacted.

**Verify:** focused parser tests cover real contract shapes and malformed responses. No error path
returns a made-up domain model.

### Step 10. Add session contracts and secure storage

Implement the seven-field `Session`, `SessionScope`, secure storage, and `SessionManager` exactly as
specified in `text.md` §5. Use role-prefixed secure-storage keys. Store only the active-role pointer
in `shared_preferences`.

**Verify:** automated storage tests show parent and child values are isolated, child logout preserves
the parent session, and tokens never appear in preferences or logs.

### Step 11. Add the root application and router stubs

Create `main.dart`, `app.dart`, `routes.dart`, and `app_router.dart`. Wrap the app in `ProviderScope`
and use `MaterialApp.router`. Add the routes in `text.md` §6 with placeholder pages containing only
route names—no profile cards, dashboards, exams, tests, or schedules.

The session-aware redirect remains a stub until Phase 04 implements restoration.

**Verify:** every declared route opens its stub and unknown IDs are not replaced with fixed values.

### Step 12. Add the initial tests

Add unit tests for configuration, error mapping, route parsing, and session isolation. Use controlled
transport responses only to verify protocol behavior. Do not create fake repository providers used by
the app. Real feature flows are exercised against the running backend in their implementing phases.

```bash
flutter test
flutter analyze
```

**Verify:** both commands pass and tests contain no production data-source override.

### Step 13. Build and run the scaffold

Android emulator:

```bash
flutter run -d <android-device-id> \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
flutter build apk --debug \
  --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

iOS simulator, where supported:

```bash
flutter run -d <ios-device-id> \
  --dart-define=EKLAVYA_BASE_URL=http://localhost:8000
```

For a physical device, replace the value with the host machine's reachable LAN address.

**Verify:** the app launches, displays the scaffold, and does not make feature calls or show invented
content. Confirm the backend remains reachable from the device.

## Part C — Existing superadmin conventions

### Step 14. Record web conventions without changing web code

Read `Frontend_Website/src/lib/api.ts`, `App.tsx`, `components/AppShell.tsx`,
`context/AuthContext.tsx`, `package.json`, and `index.css`. Confirm the conventions in `text.md` §9.

**Verify:** Phase 12 has a precise extension contract and no `Frontend_Website/` file was modified.

### Step 15. Complete sign-off

Run:

```bash
flutter analyze
flutter test
flutter build apk --debug --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
```

Check every item in `expected-output.md`, including the real-data audit, before starting Phase 03.
