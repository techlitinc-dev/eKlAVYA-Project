# Technical Architecture & System Design: MARKS Application

## Table of Contents
1. [Architectural Overview & Layering](#1-architectural-overview--layering)
2. [Module & Package Responsibilities](#2-module--package-responsibilities)
3. [Key Classes & Structural Relationships](#3-key-classes--structural-relationships)
4. [State Management, Threading & Concurrency](#4-state-management-threading--concurrency)
5. [Networking Layer Architecture](#5-networking-layer-architecture)
6. [End-to-End Data Flow (UI $\to$ Network $\to$ Storage)](#6-end-to-end-data-flow)
7. [Security-Relevant Design & Hardening](#7-security-relevant-design--hardening)
8. [Security Findings](#8-security-findings)
9. [Gaps & Open Questions](#9-gaps--open-questions)

---

## 1. Architectural Overview & Layering

The **MARKS** mobile application is engineered following the **Android Clean Architecture** guidelines and the **Model-View-ViewModel (MVVM)** pattern with **Dagger Hilt** dependency injection. It enforces a strict separation of concerns across Presentation, Domain/Repository, and Data (Remote & Local) layers:

```mermaid
flowchart TD
    subgraph PresentationLayer ["Presentation Layer (MVVM + Jetpack UI)"]
        UI_Activities["Activities & Fragments<br/>(HomeActivity, QuestionActivityV4, CustomTestActivity)"]
        UI_State["UI State Holders (StateFlow / LiveData)<br/>(e.g., ChapterProgressUiState, TwMainUiState)"]
        ViewModels["Jetpack ViewModels<br/>(QuestionViewModel, CustomTestViewModel, AuthViewModel)"]
    end

    subgraph DomainLayer ["Repository & Use Case Layer"]
        Repos["Data Repositories<br/>(MainRepository, QuestionRepository, AuthRepository)"]
        AppHelpers["API Helpers & Network Checkers<br/>(ev / ApiHelperImpl, cx / ApiV1Helper, ui9 / NetworkHelper)"]
    end

    subgraph DataLayer ["Data & Persistence Layer"]
        RetrofitClient["Retrofit 2 REST Engine<br/>(541 Endpoints across fv, ex, tu, qu, gx, nu, ix)"]
        OkHttp["OkHttpClient Engine<br/>(AuthInterceptor, Token Refresh, Timeout: 60s)"]
        RoomDB["Room Database (MARKS_DB v14)<br/>(UserDao, QuestionFilterDao, CustomTestSubmitTestDao)"]
        WorkMgr["WorkManager Background Engine<br/>(MARKSFileDownloadWorker, BookDownloadWorker)"]
        VdoDRM["VdoCipher Aegis DRM Engine<br/>(Encrypted Offline Video Caching)"]
    end

    UI_Activities --> ViewModels
    ViewModels --> UI_State
    ViewModels --> Repos
    Repos --> AppHelpers
    AppHelpers --> RetrofitClient
    RetrofitClient --> OkHttp
    Repos --> RoomDB
    Repos --> WorkMgr
    Repos --> VdoDRM
```

---

## 2. Module & Package Responsibilities

The codebase in `/home/techlit/Documents/mentor ai/Decompile/marks/com/scoremarks/marks` is organized into modular packages:

| Package Namespace | Primary Responsibility & Role | Key Classes Included |
| :--- | :--- | :--- |
| `com.scoremarks.marks` | Application lifecycle, global crash handling, WorkManager recovery. | `BaseApplication.java`, `MyFirebaseMessagingService.java` |
| `com.scoremarks.marks.data.api` | API helper facades bridging repositories and Retrofit interfaces. | `ApiHelperImpl.java`, `ApiDevV1HelperImpl.java` |
| `com.scoremarks.marks.data.local` | Room database definition, type converters, and migration routines. | `MarksDb.java`, `Converters.java`, `AddressConverter.java` |
| `com.scoremarks.marks.data.local.dao` | Room Data Access Objects (DAOs) for database entity operations. | `UserDao.java`, `DailyGoalDao.java`, `CustomTestSubmitTestDao.java` |
| `com.scoremarks.marks.data.models` | POJOs and DTOs representing server payloads and local entities. | `User.java`, `SubmitTestRequest.java`, `QuestionFilters.java` |
| `com.scoremarks.marks.ui.activities` | Root activities managing primary screens and navigation routers. | `HomeActivity.java`, `SplashActivity.java`, `OnBoardingActivity.java` |
| `com.scoremarks.marks.ui.marks3` | Modern v4 core: question solving engine, CPYQ, and notebooks. | `QuestionActivityV4.java`, `CPYQFlowActivity.java`, `BookmarkedQsListActivity.java` |
| `com.scoremarks.marks.ui.custom_test` | Custom test generator (CTG), test taking, and analytics. | `CustomTestActivity.java`, `CustomTestQuestionActivity.java` |
| `com.scoremarks.marks.ui.marks_courses` | Video courses, video solutions, and PDF class note viewers. | `MarksCoursesActivity.java`, `PdfActivity.java`, `VideoSolActivity.java` |
| `com.scoremarks.marks.ui.marks_assignments` | B2B2C Teacher assignment creation and student homework submission. | `MarksAssignmentTeacherActivity.java`, `MAStudentActivity.java` |
| `com.scoremarks.marks.medical` | Dedicated NEET-UG ecosystem: NCERT modules, revision zones, bookmarks. | `MedicalActivity.java`, `MedicalPremiumActivity.java`, `DailyDoseActivity.java` |
| `com.scoremarks.marks.other` | Custom UI components, app widget receivers, and background workers. | `ExamWidgetBootReceiver.java`, `ExamWidgetMidnightReceiver.java`, `MARKSFileDownloadWorker.java` |
| `defpackage` | Flattened/obfuscated network services, Dagger components, and utilities. | `qh3.java` (NetworkModule), `fv.java` (ApiDevV4), `ex.java` (ApiV1) |

---

## 3. Key Classes & Structural Relationships

```mermaid
classDiagram
    class BaseApplication {
        +onCreate()
        +setupWebEngage()
        +fixWorkManagerDb()
    }

    class MarksDb {
        +getUserDao() UserDao
        +getCustomTestSubmitTestDao() CustomTestSubmitTestDao
        +getDailyGoalLocalDao() MyDailyGoalDao
        +downloadedBookDao() BookLocalDao
    }

    class qh3 {
        <<Dagger NetworkModule>>
        +provideApiDevV4Service(h4c) fv
        +provideApiService(h4c) ex
        +provideApiDevV2Service(h4c) qu
        +provideApiV3Service(h4c) tu
        +provideOkHttpClient() ou9
        +provideRoomDatabase() MarksDb
    }

    class fv {
        <<Retrofit Interface - v4>>
        +allSubmissionsSave()
        +getChapterDetails()
        +createCustomTest()
        +getOtpVideoPlayback()
    }

    class ex {
        <<Retrofit Interface - v1>>
        +getQuestionsList()
        +getChapterSummary()
    }

    class ev {
        <<ApiHelperImpl>>
        -fv a
        -ui9 b
        +executeRequest()
    }

    class QuestionActivityV4 {
        -QuestionViewModel viewModel
        +renderQuestion()
        +onOptionSelected()
        +saveBookmark()
    }

    BaseApplication --> qh3 : Initializes Dagger Graph
    qh3 --> MarksDb : Builds MARKS_DB v14
    qh3 --> fv : Builds Retrofit v4
    qh3 --> ex : Builds Retrofit v1
    ev --> fv : Delegates calls
    QuestionActivityV4 --> ev : Consumes endpoints
    QuestionActivityV4 --> MarksDb : Reads/writes offline cache
```

- **`BaseApplication` (`BaseApplication.java`):** Entry point initializing Firebase Messaging, WebEngage SDK, and Microsoft Clarity. Includes an explicit fix (`fixWorkManagerDb()`) to purge corrupted `workmanager.db` SQLite files.
- **`MarksDb` (`MarksDb.java`):** Room Database abstract class declaring 17 DAO accessors and 17 Type Converters (`Converters.class`, `CustomTestConverters.class`).
- **`qh3` (`qh3.java`):** Central Dagger Hilt dependency injection module configuring 10 Retrofit service instances across 5 base URL domains, custom Gson deserializers, and OkHttp connection pools.
- **`fv` (`defpackage/fv.java`):** Master Retrofit 2 interface declaring 245 endpoints for the primary v4 backend (`production.getmarks.app/api/v4/`).
- **`ev` (`defpackage/ev.java`):** Concrete implementation of `uu` (ApiHelper) wrapping `fv` with connectivity validation via `ui9` (`NetworkHelper`).

---

## 4. State Management, Threading & Concurrency

### 4.1. Reactive State Pipeline
The app employs **Kotlin Coroutines (`StateFlow` & `SharedFlow`)** combined with **Android Architecture Components `ViewModel`**:
1. **UiState Sealed Interfaces:** Each major screen declares a dedicated UI state model (e.g., `ChapterProgressUiState`, `TwMainUiState`, `ModuleAnalysisState`).
2. **State Propagation:** ViewModels execute API calls within `viewModelScope.launch(Dispatchers.IO)`. Results are emitted into `MutableStateFlow<UiState>` instances consumed by Compose or XML data binding in `Dispatchers.Main`.

### 4.2. Threading & Worker Pools
- **Network Dispatchers:** All network calls run on `Dispatchers.IO` using OkHttp's asynchronous thread pool.
- **Database Dispatchers:** Room database reads/writes are performed asynchronously using Kotlin `suspend` functions and Coroutines.
- **WorkManager Background Tasks:**
  - `MARKSFileDownloadWorker` (`MARKSFileDownloadWorker.java`): Manages multi-threaded downloads of digital book assets and PDF notes.
  - `BookDownloadWorker` (`BookDownloadWorker.java`): Downloads offline chapter modules.
  - `ExamWidgetMidnightReceiver` (`ExamWidgetMidnightReceiver.java`): Scheduled exact alarm receiver updating widget state at midnight without keeping the app awake.

---

## 5. Networking Layer Architecture

```mermaid
sequenceDiagram
    autonumber
    actor UI as View / Activity
    participant VM as ViewModel
    participant Rep as Repository (ev / cx)
    participant Net as NetworkHelper (ui9)
    participant Ok as OkHttpClient (ou9)
    participant API as Remote Server (production.getmarks.app)
    participant DB as Room DB (MarksDb)

    UI->>VM: User initiates action (e.g., Load Chapter Questions)
    VM->>Rep: Fetch questions (subjectId, chapterId)
    Rep->>Net: Check connectivity (ui9.a())
    alt No Network Available
        Net-->>Rep: false (Disconnected)
        Rep->>DB: Query cached questions from Room DB
        DB-->>Rep: Return cached QuestionFilters & responses
        Rep-->>VM: Emit Offline Data
        VM-->>UI: Render offline banner + cached questions
    else Network Active
        Net-->>Rep: true (Connected)
        Rep->>Ok: Execute Retrofit call (fv.java#z2)
        Ok->>Ok: Intercept request -> Inject Bearer JWT Token
        Ok->>API: HTTP GET /api/v4/cpyqb/exam/{examId}/...
        alt 401 Unauthorized
            API-->>Ok: HTTP 401
            Ok->>API: POST /api/v1/auth/refresh-token
            API-->>Ok: Returns fresh idToken
            Ok->>API: Replay original request with fresh token
        end
        API-->>Ok: HTTP 200 OK (JSON Payload)
        Ok-->>Rep: Parsed Response DTO (k3c<MedicalAllPyqsReponse>)
        Rep->>DB: Asynchronously update Room cache
        Rep-->>VM: Emit Success(data)
        VM-->>UI: Update UI state & dismiss loaders
    end
```

### 5.1. Client Setup & OkHttp Configuration (`qh3.java`)
- **Connection Timeout:** 60 seconds.
- **Read / Write Timeout:** 60 seconds.
- **Gson Configuration:** Instantiated with `SafeTypeAdapterFactory` to prevent crashes when backend fields return unexpected nulls or type mutations. Custom deserializers handle polymorphic question models:
  - `QuestionData.DataStateDeserializer`
  - `AnalysisSolution.DataQuestionSolutionsStateDeserializer`
  - `QuestionId.NotebookQuestionIdDeserializer`
  - `Quiz.AnalysisQuizStateStateDeserializer`
  - `CustomTest.DataStateDeserializer`

### 5.2. Multi-Host Retrofit Routing

| Retrofit Interface | Injected Base URL | Domain / Functionality |
| :--- | :--- | :--- |
| `fv.class` | `https://production.getmarks.app/api/v4/` | Core v4 Question bank, CTG, VdoCipher video OTP, Payments, Assignments. |
| `nu.class` | `https://production.getmarks.app/api/v1/` | User authentication, OTP dispatch, session refresh. |
| `ex.class` | `https://production.getmarks.app/api/v1/` | Legacy v1 PYQs, chapter listing, topic taxonomy. |
| `qu.class` | `https://production.getmarks.app/api/v2/` | Custom test synthesis and submission v2. |
| `gx.class` | `https://production.getmarks.app/api/v2/` | Exam categories, subscription catalog v2. |
| `tu.class` | `https://production.getmarks.app/api/v3/` | Smart Notebooks, question status, solving modes v3. |
| `ix.class` | `https://production.getmarks.app/api/v3/` | Weekly leaderboards, leagues, user points v3. |
| `zde.class` | `https://prod-tracker-api.getmarks.app/api/` | Exam countdown tracking and widget sync. |
| `ot2.class` | `https://countriesnow.space/api/v0.1/` | Country, state, and city lookup for profile editing. |

---

## 6. End-to-End Data Flow

```mermaid
flowchart LR
    subgraph UI_Layer ["1. UI Event"]
        UserClick["User selects option 'C' on NAT question"] --> VMAction["ViewModel.submitAnswer()"]
    end

    subgraph Domain_Layer ["2. Repository Coordination"]
        VMAction --> RepCall["QuestionRepository.saveAttempt()"]
        RepCall --> LocalSave["Save to Room SubmitTestRequest"]
    end

    subgraph Network_Layer ["3. Remote Synchronization"]
        LocalSave --> NetCheck{"Online?"}
        NetCheck -- Yes --> RetrofitCall["POST /api/v4/solving-modes/practice/start"]
        RetrofitCall --> ServerUpdate["Remote Database Updated"]
        NetCheck -- No --> EnqueueSync["Enqueue WorkManager Job"]
        EnqueueSync -.-> SyncLater["Sync when network restored"]
    end

    subgraph Persistence_Layer ["4. Local Persistence"]
        LocalSave --> RoomTable["Table: SubmitTestRequest (MARKS_DB)"]
        RoomTable --> LiveObserve["Room Invalidation Tracker"]
        LiveObserve --> UIUpdate["UI reflects submitted state"]
    end
```

---

## 7. Security-Relevant Design & Hardening

### 7.1. Code Obfuscation & Mapping
The production APK was compiled with **R8 / ProGuard** in shrinking and obfuscation mode. Network interfaces (`fv`, `ex`, `qu`, `tu`, `gx`, `nu`, `ix`, `zde`, `ot2`), Dagger modules (`qh3`), and data helpers (`ev`, `cx`, `pu`, `ui9`) were mapped to short 2-3 letter names in `defpackage/`. However, all `@Metadata` annotations were retained, allowing full deobfuscation of method names, parameter signatures, and return types.

### 7.2. Video DRM & Anti-Piracy Architecture
Video lectures and solutions are hosted on **VdoCipher**. The client never receives direct MP4/HLS URLs:
1. Client requests OTP from `POST /api/v4/courses/.../video/otp` (`fv.java#f`).
2. Server validates user subscription and returns `{ otp: "...", playbackInfo: "..." }`.
3. The VdoCipher Aegis SDK (`com.vdocipher.aegis`) initializes an encrypted secure player pipeline with hardware DRM (Widevine Modular L1/L3) and dynamic watermarking (displaying the student's email/phone overlay to deter screen capture).

### 7.3. Payment Gateway Security
The application delegates payment collection to **Cashfree Payment Gateway** (`com.cashfree.pg`):
- No credit card or UPI VPA data ever traverses MARKS servers or client storage.
- The client initiates an order via `POST /api/v4/payment/checkout/order` and receives a temporary `cftoken` / `order_token`.
- The native Cashfree SDK launches installed UPI applications (`upi://pay`) or web checkout, returning an order status verified via server-side polling.

---

## 8. Security Findings

> [!WARNING]
> Hardcoded credentials and secrets were identified in the decompiled source. Secrets are **REDACTED** below with their source locations:

| Finding ID | Component / Description | Redacted Key Value | Exact Code Citation | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Mixpanel Project Token | `76fe371aeb70********************` | `defpackage/qh3.java#114` | High |
| **SEC-002** | WebEngage Account Key (Base64) | `in~311c****` (`aW5+MzExYzQ3MDg=`) | `com/scoremarks/marks/BaseApplication.java#66` | High |
| **SEC-003** | Google OAuth2 Web Client ID | `406420339924-ketncqif4a********************.apps.googleusercontent.com` | `res/values/strings.xml` (`default_web_client_id`) | Medium |
| **SEC-004** | Firebase Database Host | `https://marks-62f26.firebaseio.com` | `res/values/strings.xml` (`firebase_database_url`) | Medium |
| **SEC-005** | Google Firebase Application ID | `1:406420339924:android:c87f3afa************` | `res/values/strings.xml` (`google_app_id`) | Medium |

---

## 9. Gaps & Open Questions

1. **Certificate Pinning:** No OkHttp `CertificatePinner` configuration was observed in `qh3.java`. Network traffic is secured via standard TLS/HTTPS validation `[INFERRED]`.
2. **WebSocket Support:** No active WebSocket connections were found in the Retrofit or OkHttp network graph. Real-time updates rely on FCM push notifications and client-side polling `[INFERRED]`.
3. **Database Encryption:** `MarksDb` relies on standard unencrypted SQLite. Sensitive cached user data in `UserDao` is accessible on rooted devices `[UNKNOWN]`.
