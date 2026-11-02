# Phase 02 — Instructions

Execute the steps in order. Every step ends with a **Verify** hint — do not proceed until it
passes. Commands are run from the repository root (`/home/tushka/eKlAVYA-Project`) unless a step
says `cd Android_App`. This phase writes scaffolding only; guardrails are in `readme.md`.

## Part A — Backend health (precondition)

### Step 1. Start the backend and confirm health

```bash
./run.sh backend
```

In a second terminal:

```bash
curl -s http://localhost:8000/health
curl -s http://localhost:8000/api/openapi.json | head -c 200
```

**Verify:** `/health` returns a JSON health body (`Backend/main.py:212`) and the OpenAPI spec is
served at `/api/openapi.json` (`Backend/main.py:132`). Leave the backend running for the rest of
the phase. Note: the API lives under path prefixes `/api/*` — there is **no** `/api/v1` usage for
the workflow stack (phase-01 §2); only Stack-1 `/api/*` endpoints are consumed.

## Part B — Android greenfield scaffold (in `Android_App/`)

### Step 2. Confirm prerequisites

- Android Studio (latest stable) installed with **Android SDK 35** and **JDK 17** (Android
  Studio's bundled JBR 17 is acceptable).
- Either a system Gradle 8.x (to generate the wrapper in Step 6) or Android Studio (it generates
  the wrapper on first sync).

```bash
java -version          # must report 17.x
ls "$ANDROID_HOME/platforms" | grep 35    # or check SDK Manager; must show android-35
```

**Verify:** `java -version` prints 17.x and SDK platform 35 is present.

### Step 3. Create `settings.gradle.kts`

Create `Android_App/settings.gradle.kts`:

```kotlin
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "eklavya-android"
include(":app")
```

**Verify:** `test -f Android_App/settings.gradle.kts && echo OK`.

### Step 4. Create the version catalog `gradle/libs.versions.toml`

Create `Android_App/gradle/libs.versions.toml` with exactly this content (these versions are
mutually compatible; do not bump individual entries):

```toml
[versions]
agp = "8.7.3"
kotlin = "2.1.0"
ksp = "2.1.0-1.0.29"
hilt = "2.53.1"
compose-bom = "2024.12.01"
core-ktx = "1.15.0"
lifecycle = "2.8.7"
activity-compose = "1.9.3"
navigation-compose = "2.8.5"
hilt-navigation-compose = "1.2.0"
retrofit = "2.11.0"
retrofit-kotlinx-serialization = "1.0.0"
okhttp = "4.12.0"
kotlinx-serialization-json = "1.7.3"
coroutines = "1.9.0"
datastore = "1.1.1"
coil = "2.7.0"
junit = "4.13.2"
androidx-junit = "1.2.1"
espresso = "3.6.1"
turbine = "1.2.0"

[libraries]
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version.ref = "core-ktx" }
androidx-lifecycle-runtime-ktx = { group = "androidx.lifecycle", name = "lifecycle-runtime-ktx", version.ref = "lifecycle" }
androidx-activity-compose = { group = "androidx.activity", name = "activity-compose", version.ref = "activity-compose" }
compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "compose-bom" }
compose-ui = { group = "androidx.compose.ui", name = "ui" }
compose-ui-graphics = { group = "androidx.compose.ui", name = "ui-graphics" }
compose-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview" }
compose-material3 = { group = "androidx.compose.material3", name = "material3" }
compose-ui-tooling = { group = "androidx.compose.ui", name = "ui-tooling" }
compose-ui-test-manifest = { group = "androidx.compose.ui", name = "ui-test-manifest" }
compose-ui-test-junit4 = { group = "androidx.compose.ui", name = "ui-test-junit4" }
navigation-compose = { group = "androidx.navigation", name = "navigation-compose", version.ref = "navigation-compose" }
hilt-android = { group = "com.google.dagger", name = "hilt-android", version.ref = "hilt" }
hilt-compiler = { group = "com.google.dagger", name = "hilt-compiler", version.ref = "hilt" }
hilt-navigation-compose = { group = "androidx.hilt", name = "hilt-navigation-compose", version.ref = "hilt-navigation-compose" }
hilt-android-testing = { group = "com.google.dagger", name = "hilt-android-testing", version.ref = "hilt" }
retrofit = { group = "com.squareup.retrofit2", name = "retrofit", version.ref = "retrofit" }
retrofit-kotlinx-serialization = { group = "com.jakewharton.retrofit", name = "retrofit2-kotlinx-serialization-converter", version.ref = "retrofit-kotlinx-serialization" }
okhttp = { group = "com.squareup.okhttp3", name = "okhttp", version.ref = "okhttp" }
okhttp-logging-interceptor = { group = "com.squareup.okhttp3", name = "logging-interceptor", version.ref = "okhttp" }
okhttp-mockwebserver = { group = "com.squareup.okhttp3", name = "mockwebserver", version.ref = "okhttp" }
kotlinx-serialization-json = { group = "org.jetbrains.kotlinx", name = "kotlinx-serialization-json", version.ref = "kotlinx-serialization-json" }
kotlinx-coroutines-android = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-android", version.ref = "coroutines" }
kotlinx-coroutines-test = { group = "org.jetbrains.kotlinx", name = "kotlinx-coroutines-test", version.ref = "coroutines" }
datastore-preferences = { group = "androidx.datastore", name = "datastore-preferences", version.ref = "datastore" }
coil-compose = { group = "io.coil-kt", name = "coil-compose", version.ref = "coil" }
junit = { group = "junit", name = "junit", version.ref = "junit" }
androidx-junit = { group = "androidx.test.ext", name = "junit", version.ref = "androidx-junit" }
espresso-core = { group = "androidx.test.espresso", name = "espresso-core", version.ref = "espresso" }
turbine = { group = "app.cash.turbine", name = "turbine", version.ref = "turbine" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
kotlin-compose = { id = "org.jetbrains.kotlin.plugin.compose", version.ref = "kotlin" }
ksp = { id = "com.google.devtools.ksp", version.ref = "ksp" }
hilt = { id = "com.google.dagger.hilt.android", version.ref = "hilt" }
```

**Verify:** `grep -c '=' Android_App/gradle/libs.versions.toml` is greater than 60, and every
`version.ref` named in `[libraries]`/`[plugins]` exists under `[versions]`.

### Step 5. Create root `build.gradle.kts` and `gradle.properties`

`Android_App/build.gradle.kts`:

```kotlin
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.compose) apply false
    alias(libs.plugins.ksp) apply false
    alias(libs.plugins.hilt) apply false
}
```

`Android_App/gradle.properties`:

```properties
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
kotlin.code.style=official
```

**Verify:** both files exist; `grep "apply false" Android_App/build.gradle.kts | wc -l` prints 5.

### Step 6. Generate the Gradle wrapper

```bash
cd Android_App
gradle wrapper --gradle-version 8.10.2   # if a system Gradle 8.x is installed
# OR: open the folder in Android Studio and let it sync once (it generates the wrapper)
cd ..
```

If you use Android Studio, close it after sync and continue from the CLI.

**Verify:** `test -x Android_App/gradlew` and
`grep distributionUrl Android_App/gradle/wrapper/gradle-wrapper.properties` shows
`gradle-8.10.2-bin.zip`.

### Step 7. Create `app/build.gradle.kts`

Create `Android_App/app/build.gradle.kts`:

```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

val eklaVyaBaseUrl: String =
    (project.findProperty("eklavyaBaseUrl") as String?) ?: "http://10.0.2.2:8000"

android {
    namespace = "ai.eklavya.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "ai.eklavya.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        debug {
            buildConfigField("String", "EKLAVYA_BASE_URL", "\"$eklaVyaBaseUrl\"")
        }
        release {
            buildConfigField("String", "EKLAVYA_BASE_URL", "\"$eklavyaBaseUrl\"")
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("debug") // scaffold only; real signing in phase-13
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

dependencies {
    implementation(platform(libs.compose.bom))
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.navigation.compose)
    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.navigation.compose)
    implementation(libs.retrofit)
    implementation(libs.retrofit.kotlinx.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging.interceptor)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.datastore.preferences)
    implementation(libs.coil.compose)

    debugImplementation(libs.compose.ui.tooling)
    debugImplementation(libs.compose.ui.test.manifest)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.turbine)

    androidTestImplementation(platform(libs.compose.bom))
    androidTestImplementation(libs.compose.ui.test.junit4)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.espresso.core)
    androidTestImplementation(libs.hilt.android.testing)
    androidTestImplementation(libs.okhttp.mockwebserver)
}
```

**Verify:** `cd Android_App && ./gradlew help --console=plain` succeeds (exit code 0).

### Step 8. Manifest, resources, and network security config

Create these files under `Android_App/app/src/main/`:

`AndroidManifest.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:name=".EklavyaApp"
        android:allowBackup="false"
        android:icon="@android:drawable/sym_def_app_icon"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.Eklavya"
        android:usesCleartextTraffic="true"
        android:networkSecurityConfig="@xml/network_security_config">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
```

`res/values/strings.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">eKlAVYA</string>
</resources>
```

`res/values/themes.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Eklavya" parent="android:Theme.Material.NoActionBar" />
</resources>
```

`res/xml/network_security_config.xml` (dev loopback only; cleartext is denied everywhere
except the emulator loopback and localhost):

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="false" />
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="false">10.0.2.2</domain>
        <domain includeSubdomains="false">localhost</domain>
    </domain-config>
</network-security-config>
```

`res/drawable/` and `res/mipmap/` stay empty for now; the manifest uses a framework icon so the
scaffold builds. Phase-03 adds the real launcher icon as part of the design-system asset set.

**Verify:** `ls Android_App/app/src/main/res/xml/network_security_config.xml` exists and
`grep -c "usesCleartextTraffic" Android_App/app/src/main/AndroidManifest.xml` prints 1.

### Step 9. Application class and MainActivity

`Android_App/app/src/main/java/ai/eklavya/app/EklavyaApp.kt`:

```kotlin
package ai.eklavya.app

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class EklavyaApp : Application()
```

`Android_App/app/src/main/java/ai/eklavya/app/MainActivity.kt`:

```kotlin
package ai.eklavya.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                Surface {
                    // Phase-02 scaffold: phase-03 replaces this with EklavyaTheme + NavHost.
                    Text("eKlAVYA scaffold")
                }
            }
        }
    }
}
```

**Verify:** `cd Android_App && ./gradlew :app:assembleDebug --console=plain` succeeds. The APK is
at `app/build/outputs/apk/debug/app-debug.apk`.

### Step 10. `core/session` — session model, storage contract, Keystore wrapper

Create the session layer (see `text.md` §5 for the contract these files must satisfy):

- `core/session/SessionScope.kt` — `enum class SessionScope { PARENT, CHILD }`.
- `core/session/Session.kt` — `@Serializable data class Session` with fields `token`,
  `refreshToken`, `actorId`, `displayName`, `isStudent`, `obtainedAtEpochMs`, `expiresInSeconds`.
- `core/session/SessionStorage.kt` — `interface SessionStorage` with `suspend fun read(scope:
  SessionScope): Session?`, `suspend fun write(scope: SessionScope, session: Session)`,
  `suspend fun clear(scope: SessionScope)`.
- `core/session/SessionManager.kt` — `interface SessionManager` exposing
  `suspend fun saveParentSession(session: Session)`, `suspend fun saveChildSession(session:
  Session)`, `val activeSession: Flow<Session?>`, `suspend fun clear(scope: SessionScope)`,
  `suspend fun switchTo(scope: SessionScope)`. Implement it as `SessionManagerImpl` in the same
  file or a sibling file, delegating to `SessionStorage` and persisting the active scope choice.
- `core/session/TokenEncryption.kt` — Android Keystore wrapper (`AndroidKeyStore`, AES/GCM, one
  key alias `eklavya_session_key`) exposing `fun encrypt(plain: String): String` and
  `fun decrypt(cipherText: String): String`. Store only the **token** and **refreshToken**
  strings encrypted; metadata fields stay plaintext in DataStore.

Skeletons must compile; real DataStore wiring lands in Step 12.

**Verify:** `cd Android_App && ./gradlew :app:assembleDebug --console=plain` succeeds.

### Step 11. `core/network` — result type and error mapper

- `core/network/ApiResult.kt` — `sealed interface ApiResult<out T>` with `data class Success<T>(val
  value: T)`, `data class Failure(val error: ApiError)`.
- `core/network/ApiError.kt` — `sealed class ApiError` with subtypes `Network`, `Http(val code:
  Int, val backendCode: String?, val message: String, val requestId: String?)`, `Auth`,
  `Parse`, `Unknown`; plus `object ApiErrorMapper { fun fromHttp(code: Int, body: String?):
  ApiError }` that parses **both** backend envelopes (phase-01 §4: v1 `{"error":{"code",
  "message","details","request_id"}}` from `core/errors.py:139`; legacy `{"detail": str}` from
  `core/errors.py:167`; catch-all `{"success":false,"error":{...}}` from `main.py:169`). Exact
  mapping table is in `text.md` §7.

**Verify:** `./gradlew :app:assembleDebug` succeeds; `grep -c "detail" core/network/ApiError.kt`
is at least 1 (legacy envelope handled).

### Step 12. `core/network` — AuthInterceptor and TokenAuthenticator

- `core/network/AuthInterceptor.kt` — `class AuthInterceptor @Inject constructor(private val
  sessionManager: SessionManager) : Interceptor`: reads the active session and adds
  `Authorization: Bearer <token>`; adds no header when no active session. It must never log the
  header value.
- `core/network/TokenAuthenticator.kt` — `class TokenAuthenticator @Inject constructor(private
  val sessionManager: SessionManager) : Authenticator`: on HTTP 401, refreshes via the stored
  refresh token and retries once; returns null (fail) when there is no session or refresh fails.
  The refresh endpoint is `POST /api/auth/token/refresh` (parent) / `POST
  /api/auth/token/refresh/child` (child) (phase-01 §9.2); implement the call with OkHttp
  directly (not Retrofit) to avoid circular dependencies; rotation semantics per phase-01 §6.2.

**Verify:** `./gradlew :app:assembleDebug` succeeds.

### Step 13. `data/datastore` — dual DataStore session storage

- `data/datastore/SessionDataStore.kt` — `class SessionDataStore @Inject constructor(...) :
  SessionStorage` backed by **two** DataStore Preferences files (top-level extension properties
  `Context.parentSessionDataStore` named `"parent_session"` and `Context.childSessionDataStore`
  named `"child_session"`), selecting the file by `SessionScope`. Write/read/clear the seven
  `Session` fields (token and refreshToken via `TokenEncryption`).

**Verify:** `./gradlew :app:assembleDebug` succeeds.

### Step 14. `di/` — Hilt modules

Create (providers exact per `text.md` §4):

- `di/DataStoreModule.kt` — `@Module @InstallIn(SingletonComponent::class) object DataStoreModule`
  providing both DataStore instances.
- `di/SessionModule.kt` — binds `SessionStorage` to `SessionDataStore` and provides the
  `SessionManager` singleton.
- `di/NetworkModule.kt` — provides `Json` (kotlinx-serialization, `ignoreUnknownKeys = true`),
  `OkHttpClient` (AuthInterceptor, TokenAuthenticator, HttpLoggingInterceptor at `HEADERS` level
  in debug only, 30 s timeouts), `Retrofit` (base URL `BuildConfig.EKLAVYA_BASE_URL`, the
  kotlinx-serialization converter), and a no-op `Converter.Factory` binding if needed.
- `di/RepositoryModule.kt` — `@Module @InstallIn(SingletonComponent::class) abstract class
  RepositoryModule` with an empty body and a comment: repository bindings are added per feature
  in phases 05–11.

**Verify:** `./gradlew :app:assembleDebug` succeeds (KSP/Hilt codegen runs; errors here are
usually missing `@InstallIn`).

### Step 15. `navigation/` — route constants and graphs

Create (topology per `text.md` §6):

- `navigation/Routes.kt` — `object Routes` with the exact route strings from `text.md` §6.2.
- `navigation/EklavyaNavHost.kt` — `EklavyaNavHost(navController)` hosting the graphs.
- `navigation/RootGraph.kt` — start-destination decision by active session role (scaffold: a
  `NavHost` composable with three nested graphs; the role logic itself is a phase-04 TODO that
  defaults to the auth graph).
- `navigation/AuthGraph.kt`, `navigation/ParentNavGraph.kt`, `navigation/ChildNavGraph.kt` —
  `NavGraphBuilder` extensions with nested `navigation(...)` blocks whose leaf `composable`s
  render placeholder `Text(route)` for now.

**Verify:** `./gradlew :app:assembleDebug` succeeds; `grep -c "composable("
navigation/ParentNavGraph.kt` ≥ 1.

### Step 16. Placeholder packages for later phases

Create empty (`.gitkeep`) packages so later phases land in the fixed layout:

```bash
mkdir -p Android_App/app/src/main/java/ai/eklavya/app/{core/designsystem,data/{dto,api,repository},domain,ui/{parent,child,auth,common}}
touch Android_App/app/src/main/java/ai/eklavya/app/core/designsystem/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/data/dto/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/data/api/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/data/repository/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/domain/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/ui/parent/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/ui/child/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/ui/auth/.gitkeep
touch Android_App/app/src/main/java/ai/eklavya/app/ui/common/.gitkeep
```

**Verify:** `find Android_App/app/src/main/java -type d | sort` matches the tree in `text.md` §3.

### Step 17. Clean build and install on an emulator

```bash
cd Android_App
./gradlew clean :app:assembleDebug
# Start an emulator with API 35 (or: ./gradlew :app:installDebug with a device attached)
./gradlew :app:installDebug
adb shell am start -n ai.eklavya.app/.MainActivity
```

**Verify:** `adb shell dumpsys window | grep -i "mCurrentFocus"` shows `ai.eklavya.app`; the
screen shows the text "eKlAVYA scaffold". Capture a screenshot for `expected-output.md`:
`adb exec-out screencap -p > /tmp/phase02-scaffold.png`.

### Step 18. Confirm the debug base URL made it into BuildConfig

```bash
cd Android_App
for d in classes.dex classes2.dex classes3.dex; do
  unzip -p app/build/outputs/apk/debug/app-debug.apk "$d" 2>/dev/null
done | strings | grep -m1 "http://10.0.2.2:8000"
```

**Verify:** the string `http://10.0.2.2:8000` appears (it is the debug `EKLAVYA_BASE_URL`). To
override per build type: `./gradlew :app:assembleDebug -PeklavyaBaseUrl=http://192.168.1.5:8000`.

## Part C — Superadmin panel conventions (read-and-record; no code changes)

### Step 19. Record the web client conventions

Read and confirm (do not modify):

1. `Frontend_Website/src/lib/api.ts` — axios instance: `API_BASE_URL` from
   `VITE_API_BASE_URL`, default `http://localhost:8000` (`api.ts:3-4`); request interceptor
   injects `Authorization: Bearer ${eklavya_token}` (`api.ts:13-19`); `apiFetch` helper
   (`api.ts:21-43`).
2. `Frontend_Website/src/context/AuthContext.tsx` — token keys `eklavya_token` /
   `eklavya_user` (`AuthContext.tsx:57-58`, `:73-74`, `:79`).
3. `Frontend_Website/src/App.tsx` — superadmin routes `/superadmin/{dashboard,users,questions,
   content,ai-settings}` all render `SuperAdminPortal` inside `AppShell` (`App.tsx:118-157`).
4. `Frontend_Website/src/components/AppShell.tsx` — active role is inferred from the URL
   (`AppShell.tsx:39-43`), superadmin nav items at `AppShell.tsx:73-79`, icons from
   `lucide-react`.
5. `Frontend_Website/package.json` — React 19, Vite 6, TypeScript 5.6, Tailwind v4
   (`@tailwindcss/vite`), `react-router-dom` v7, `axios`, `lucide-react`, `katex`.
6. `Frontend_Website/src/index.css` — Tailwind v4 CSS-first via `@import "tailwindcss"`, Inter
   as the base body font (`index.css:1-9`).

**Verify:** `grep -n "eklavya_token" Frontend_Website/src/lib/api.ts Frontend_Website/src/context/AuthContext.tsx`
shows hits in both files; `grep -n "startsWith('/superadmin')" Frontend_Website/src/components/AppShell.tsx`
shows the role inference.

### Step 20. Sign-off

Work through every checkbox in `expected-output.md`. Record any backend defects encountered in
the phase gap log, citing phase-01 §11 gap numbers.
