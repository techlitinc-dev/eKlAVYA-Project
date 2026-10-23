# Specification: MARKS Application (Reverse-Engineered)

## Table of Contents
1. [Executive Summary & Purpose](#1-executive-summary--purpose)
2. [Module Breakdown & Feature Catalog](#2-module-breakdown--feature-catalog)
3. [Functional Requirements (FR-001 to FR-045)](#3-functional-requirements)
4. [Non-Functional Requirements (NFR-001 to NFR-025)](#4-non-functional-requirements)
5. [Third-Party SDKs & Library Roles](#5-third-party-sdks--library-roles)
6. [Build Flavors, Configuration & Environments](#6-build-flavors-configuration--environments)
7. [Local Data Models & Storage Architecture](#7-local-data-models--storage-architecture)
8. [Security Findings (Redacted Secrets & Vulnerabilities)](#8-security-findings)
9. [Gaps & Open Questions](#9-gaps--open-questions)

---

## 1. Executive Summary & Purpose

The **MARKS** mobile application (Package: `com.scoremarks.marks`, Version `2.0.8`, Version Code `119`), developed by **ScoreMarks / MathonGo**, is a competitive examination preparation and self-assessment ecosystem for Indian students preparing for engineering and medical entrance examinations (JEE Main, JEE Advanced, NEET-UG, BITSAT, WBJEE, MHT-CET, KCET, COMEDK, NDA) and Class 10/12 CBSE Board examinations.

The platform provides a comprehensive learning and assessment loop:
- Chapter-wise and topic-wise Previous Years Questions (PYQs) with granular filtering and bookmarks.
- Dynamic **Custom Test Generator (CTG)** allowing students to assemble timed CBT exams across custom subjects and chapters.
- **Revision Flash Cards (RFC)** and **Formula Cards** for rapid conceptual revision.
- **Daily Practice Problems (DPP)** and gamified **Daily Dose** challenges.
- Encrypted video lectures and video solutions powered by **VdoCipher DRM**.
- Monetization and subscription packs integrated via **Cashfree Payment Gateway**.
- Teacher-student homework assignment distribution with deep-link onboarding.
- Local persistence and offline test execution backed by **Room Database** (`MARKS_DB`).

---

## 2. Module Breakdown & Feature Catalog

| Module | Purpose & Scope | Key Code Evidence (File Paths & Classes) |
| :--- | :--- | :--- |
| **Authentication & Onboarding** | Phone number OTP verification, Google OAuth2 sign-in, academic target profile setup (Exam, Year, Dropper status). | `com/scoremarks/marks/ui/activities/PhoneAuthActivity.java`, `PhoneAuthOtpActivity.java`, `OnBoardingOB1Activity.java`, `OnboardingProfileActivity.java` |
| **Chapter-wise PYQ (CPYQB)** | Repository of 20+ years of solved entrance questions filtered by shift, year, single-correct/numerical, and difficulty. | `com/scoremarks/marks/ui/marks3/cpyqb/CPYQFlowActivity.java`, `QuestionActivityV4.java`, `ChapterActivity.java`, `defpackage/fv.java` |
| **Custom Test Generator (CTG)** | Step-by-step test synthesis (exam selection, subject selection, chapter weightage, timed CBT interface, auto-grading). | `com/scoremarks/marks/ui/custom_test/CustomTestActivity.java`, `CustomTestQuestionActivity.java`, `CustomTestRepordCardActivity.java`, `defpackage/fv.java` |
| **Revision Flash Cards (RFC)** | Digital flashcard deck with progressive mastery tracking and chapter-level concept cards. | `com/scoremarks/marks/ui/revision_flash_card/RFCMainActivity.java`, `RFCTopicsActivity.java`, `RFCActivity.java` |
| **Smart Notebooks & Bookmarks** | Categorization of bookmarked and incorrect questions into custom notebooks with tag filtering. | `com/scoremarks/marks/ui/notebook/notebook_list/ui/NotebookListActivity.java`, `com/scoremarks/marks/ui/marks3/notebook_v2/BookmarkedQsListActivity.java` |
| **Video Solutions & Courses** | DRM-protected streaming video explanations and full-length video courses with OTP tokenization. | `com/scoremarks/marks/ui/video_solutions/VideoSolActivity.java`, `com/scoremarks/marks/ui/marks_courses/MarksCoursesActivity.java`, `com/vdocipher/aegis/` |
| **Marks Selected Digital Books** | Curated digital problem books and practice modules with question-by-question attempt tracking. | `com/scoremarks/marks/ui/marks_selected/MarksSelectedActivity.java`, `defpackage/fv.java` |
| **Daily Dose & Goals** | Daily practice habit builder with streak tracking, target setting, and month-basis completion heatmaps. | `com/scoremarks/marks/ui/daily_goal/DailyGoalActivity.java`, `com/scoremarks/marks/medical/dashboard/dailydose/DailyDoseActivity.java` |
| **Teacher & Student Assignments** | B2B2C homework creation by teachers with shareable link generation and student attempt grading. | `com/scoremarks/marks/ui/marks_assignments/teacher_flow/MarksAssignmentTeacherActivity.java`, `com/scoremarks/marks/ui/marks_assignments/student_flow/MAStudentActivity.java` |
| **Medical / NEET Ecosystem** | Dedicated NEET-UG hub with NCERT line-by-line modules, biology diagram questions, and revision zones. | `com/scoremarks/marks/medical/MedicalActivity.java`, `MedicalPremiumActivity.java`, `com/scoremarks/marks/medical/ncert_modules/` |
| **Premium Store & Checkout** | Subscription plans, study packs, video solution access, and native/web Cashfree payment checkout. | `com/scoremarks/marks/ui/home/marks_premium/MarksPremiumSelectionActivity.java`, `NewPaymentCheckoutActivity.java`, `com/cashfree/pg/` |
| **Widgets & System Integration** | Android Home Screen exam countdown widgets with boot and midnight receivers. | `com/scoremarks/marks/other/ExamWidgetBootReceiver.java`, `ExamWidgetMidnightReceiver.java`, `WidgetDashboardActivity.java` |

---

## 3. Functional Requirements

### 3.1. Authentication & Onboarding
- **FR-001 (Phone OTP Request):** The system shall accept a 10-digit Indian mobile number and send an OTP via SMS (`PhoneAuthActivity.java`, `defpackage/nu.java#b`).
- **FR-002 (OTP Verification):** The system shall verify the 6-digit OTP and return a JWT Bearer access token and refresh token (`PhoneAuthOtpActivity.java`, `defpackage/nu.java#d`).
- **FR-003 (Google OAuth2 Sign-In):** The app shall support Google Sign-In using Google Play Services credentials (`OnBoardingAuthActivity.java`, `SignInHubActivity`).
- **FR-004 (Academic Profile Setup):** The user shall select their primary exam category (JEE Main, JEE Advanced, NEET, BITSAT), target year (e.g., 2026), class (11th, 12th, Dropper), and coaching status (`OnboardingProfileActivity.java`, `defpackage/fv.java#O`).
- **FR-005 (Referral Code Application):** The system shall allow users to redeem referral codes to unlock trial benefits (`defpackage/fv.java#k`).

### 3.2. Question Bank & PYQ Engine
- **FR-006 (Hierarchical Navigation):** The app shall support navigation: Exam $\to$ Subject $\to$ Chapter $\to$ Topic $\to$ Question Set (`CPYQFlowActivity.java`, `defpackage/fv.java#z2`).
- **FR-007 (Question Metadata Rendering):** Each question shall display its exam name, year, shift/session, question type (Single Correct MCQ, Numerical NAT), and marks (`QuestionActivityV4.java`).
- **FR-008 (Question Solving Mode):** The user shall be able to solve questions in "Practice Mode" (instant answer check) or "Test Mode" (timed submission) (`PracticeModeMetaActivity.java`, `TestModeMetaActivity.java`).
- **FR-009 (Granular Filtering):** The app shall filter questions by year range, difficulty, attempt status (Unattempted, Correct, Incorrect), and question type (`QuestionFilterDao.java`, `defpackage/fv.java#a`).
- **FR-010 (Numerical Input Keypad):** The app shall provide a custom virtual numerical keypad for NAT questions supporting decimals and negative signs (`QuestionActivityV4.java`).

### 3.3. Custom Test Generator (CTG)
- **FR-011 (Step 1 Selection):** The user shall select the target exam and choose one or more subjects (`CustomTestActivity.java`, `defpackage/fv.java#m`).
- **FR-012 (Step 2 Chapter Allocation):** The user shall select specific chapters and allocate question counts per chapter (`defpackage/fv.java#M`).
- **FR-013 (Test Synthesis):** The system shall synthesize a custom test and persist the attempt session (`defpackage/fv.java#T`).
- **FR-014 (CBT Exam Interface):** The test screen shall provide a question palette, countdown timer, question status flags, and subject switcher (`CustomTestQuestionActivity.java`).
- **FR-015 (Auto-Submission & Report Card):** On timer expiration or manual submission, the app shall calculate total marks, negative penalties, accuracy, and percentile rank (`CustomTestRepordCardActivity.java`, `defpackage/fv.java#y1`).

### 3.4. Revision Flash Cards (RFC) & Formula Cards
- **FR-016 (RFC Subject & Topic Selection):** The user shall select a chapter to load revision cards categorized by key concepts (`RFCMainActivity.java`, `RFCTopicsActivity.java`).
- **FR-017 (Card Flip & Formula Review):** Each card shall support front/back flip showing concept definition and LaTeX formula equations (`RFCActivity.java`, `FCViewActivity.java`).
- **FR-018 (Mastery Logging):** The user shall mark cards as "Got it" or "Needs Revision", persisting mastery state to the server (`defpackage/fv.java#w2`).

### 3.5. Smart Notebooks & Bookmarks
- **FR-019 (Create Custom Notebook):** Users shall create named notebooks (e.g., "Rotational Motion Traps") with custom color tags (`NotebookListActivity.java`, `defpackage/fv.java#z`).
- **FR-020 (Bookmark Question to Notebook):** Users shall add any question to one or more notebooks along with optional personal notes (`BookmarkedQsListActivity.java`, `defpackage/fv.java#z0`).
- **FR-021 (Notebook Archive/Pin):** Users shall pin or archive notebooks (`defpackage/fv.java#x2`).

### 3.6. Courses & Video Lectures
- **FR-022 (Course Catalog):** The app shall display available video courses with syllabus outlines (`MarksCoursesActivity.java`, `defpackage/fv.java#v`).
- **FR-023 (DRM Playback Tokenization):** The app shall obtain a dynamic OTP and playback token from the server to initialize the VdoCipher player (`defpackage/fv.java#f`).
- **FR-024 (Video Progress Heartbeat):** The player shall transmit periodic playback progress to record video completion (`defpackage/fv.java#h`).
- **FR-025 (PDF Class Notes Viewer):** The app shall render attached PDF lecture notes with offline download caching (`PdfActivity.java`).

### 3.7. Teacher & Student Assignments
- **FR-026 (Teacher Assignment Creation):** A teacher shall select questions from the PYQ repository, specify due dates, and generate an assignment (`MarksAssignmentTeacherActivity.java`, `defpackage/fv.java#s`).
- **FR-027 (Shareable Deep Link):** The teacher can generate a short shareable link or 6-character code (`AssignmentQuestionsListFragment.java`).
- **FR-028 (Student Assignment Attempt):** A student shall join via code/link and attempt the assignment under timed conditions (`MAStudentActivity.java`, `defpackage/fv.java#v2`).
- **FR-029 (Classroom Performance Analytics):** The teacher can view student attempt ranks, average time spent, and question-level error rates (`AnalysisActivity.java`).

### 3.8. Gamification, Daily Dose & Leaderboards
- **FR-030 (Daily Goal Configuration):** Users shall set a target number of daily questions (e.g., 30 questions/day) (`DailyGoalActivity.java`, `DailyGoalDao.java`).
- **FR-031 (Completion Heatmap):** The app shall render a GitHub-style monthly activity heatmap displaying daily questions solved (`defpackage/fv.java#v1`).
- **FR-032 (Daily Dose Challenge):** The system shall serve daily 5-question sprint quizzes with weekly streak bonuses (`DailyDoseActivity.java`, `defpackage/fv.java#y3`).
- **FR-033 (Leagues & Leaderboards):** The app shall rank users weekly across Bronze, Silver, Gold, Diamond, and Master leagues based on points (`MarksLeaderboardActivity.java`, `MarksLeaderboardLeaguesActivity.java`, `defpackage/fv.java#w0`).

### 3.9. Subscriptions & Payments
- **FR-034 (Study Pack Catalog):** The app shall fetch active subscription tiers, pricing, and discount coupons (`MarksPremiumSelectionActivity.java`, `defpackage/fv.java#x0`).
- **FR-035 (Cashfree Order Creation):** The app shall initiate payment orders via Cashfree API, receiving an `order_token` (`NewPaymentCheckoutActivity.java`, `defpackage/fv.java#u`).
- **FR-036 (Native UPI & Seamless Checkout):** The app shall trigger native UPI apps (GPay, PhonePe, Paytm) via Cashfree SDK (`CashfreeNativeCheckoutActivity.java`).
- **FR-037 (Order Status Polling):** After checkout, the app shall poll server status to unlock purchased courses and test packs (`defpackage/fv.java#y1`).

### 3.10. Medical / NEET Specific Features
- **FR-038 (NCERT Line-by-Line Modules):** Students shall access chapter modules linked to NCERT page paragraphs (`com/scoremarks/marks/medical/ncert_modules/`, `defpackage/fv.java#W`).
- **FR-039 (Revision Zones):** Questions categorized into High Yield, Must Revise, and Trap Zones (`com/scoremarks/marks/medical/zones/`, `defpackage/fv.java#z2`).
- **FR-040 (NCERT Audio/Visual Quick Revision):** Audio summaries and flash concept players for biological taxonomies (`PlayerActivity.java`).

### 3.11. System & Widgets
- **FR-041 (Android Home Screen Widget):** The app shall provide an Android AppWidget displaying countdown days to JEE Main / NEET (`ExamWidgetBootReceiver.java`, `ExamWidgetMidnightReceiver.java`).
- **FR-042 (Midnight Widget Alarm):** The system shall schedule a midnight exact alarm to decrement countdown days (`ExamWidgetMidnightReceiver.java`).
- **FR-043 (Daily Horoscope / Mindset):** The app displays daily motivational mindset quotes and study tips based on user date of birth (`HoroscopeActivity.java`, `defpackage/fv.java#x1`).
- **FR-044 (In-App Updates):** The app checks for mandatory and flexible updates via Google Play In-App Updates (`defpackage/fv.java#b`).
- **FR-045 (In-App Review):** The app triggers Google Play In-App Review after milestones.

---

## 4. Non-Functional Requirements

### 4.1. Authentication & Security
- **NFR-001 (Bearer Token Transmission):** All authenticated requests shall transmit a JWT in the `Authorization: Bearer <token>` header (`defpackage/fv.java`, `qh3.java`).
- **NFR-002 (Token Refresh):** The OkHttpClient shall intercept 401 Unauthorized responses and trigger token refresh without terminating the user session (`defpackage/qh3.java`).
- **NFR-003 (DRM Protection):** Video lectures shall be protected using VdoCipher AES encryption; direct video URLs are never exposed to the client (`com/vdocipher/aegis/`).
- **NFR-004 (Payment Security):** Payment tokens are generated server-side; client only passes order identifiers to Cashfree SDK (`NewPaymentCheckoutActivity.java`).

### 4.2. Performance & Low Latency
- **NFR-005 (Target SDK & Minimum OS):** Minimum SDK 21 (Android 5.0), Target SDK 35 (Android 15), Compile SDK 35 (`AndroidManifest.xml`).
- **NFR-006 (Cold Start Time):** Cold launch time $\le 2.0$ seconds on low-tier devices (`SplashActivity.java`).
- **NFR-007 (Image & SVG Caching):** Formula diagrams and question figures cached in disk via Glide and GlideToVectorYou (`com/github/twocoffeesoneteam/glidetovectoryou/`).

### 4.3. Offline Capability & Local Storage
- **NFR-008 (Offline Question Cache):** All questions of an active Custom Test or DPP are saved in Room DB (`CustomTestSubmitTestDao.java`, `MarksDb.java`).
- **NFR-009 (Offline Attempt Queue):** Test submissions attempted without network connectivity are enqueued in SQLite and uploaded via WorkManager (`MARKSFileDownloadWorker.java`, `BookDownloadWorker.java`).
- **NFR-010 (Destructive Migration Fallback):** Room database handles schema versioning (Version 14) with fallback to destructive migration if migrations fail (`MarksDb.java`, `qh3.java#77`).

### 4.4. Analytics & Crash Reporting
- **NFR-011 (Mixpanel Event Tracking):** Product analytics and funnel conversions tracked via Mixpanel (`qh3.java#114`).
- **NFR-012 (WebEngage Marketing & Push):** Push notifications, in-app popups, and automated user journeys tracked via WebEngage (`BaseApplication.java#64`).
- **NFR-013 (Microsoft Clarity Session Replay):** In-app user behavior and touch heatmaps logged via Microsoft Clarity (`com/microsoft/clarity/`).
- **NFR-014 (Firebase Crashlytics & Analytics):** Unhandled native and JVM exceptions reported to Firebase (`BaseApplication.java#42`).

### 4.5. Device Permissions Found in Code
The application declares and checks the following Android permissions (`AndroidManifest.xml`):

| Permission String | Purpose in Code |
| :--- | :--- |
| `android.permission.INTERNET` | All backend network communications (`Retrofit`, `OkHttp`). |
| `android.permission.ACCESS_NETWORK_STATE` | Network connectivity checks before launching network operations (`ui9.java`). |
| `android.permission.ACCESS_WIFI_STATE` | Wi-Fi status detection for heavy video downloads. |
| `android.permission.POST_NOTIFICATIONS` | Push notification delivery on Android 13+ (API 33+). |
| `android.permission.VIBRATE` | Haptic feedback on timer expiry and quiz submission. |
| `android.permission.SCHEDULE_EXACT_ALARM` | Daily midnight exam countdown widget refresh (`ExamWidgetMidnightReceiver.java`). |
| `android.permission.RECEIVE_BOOT_COMPLETED` | Rescheduling countdown alarms upon device reboot (`ExamWidgetBootReceiver.java`). |
| `android.permission.FOREGROUND_SERVICE` | Video and PDF background downloads (`MARKSFileDownloadWorker.java`). |
| `android.permission.FOREGROUND_SERVICE_DATA_SYNC` | Offline test attempt synchronization worker. |
| `android.permission.ACCESS_COARSE_LOCATION` | Analytics and Cashfree fraud detection `[INFERRED]`. |
| `android.permission.ACCESS_FINE_LOCATION` | Analytics and regional content personalization `[INFERRED]`. |
| `android.permission.BLUETOOTH` | Audio playback routing for video lectures. |

---

## 5. Third-Party SDKs & Library Roles

| Library / SDK | Version / Artifact | Primary Role in Application |
| :--- | :--- | :--- |
| **Retrofit 2** | `com.squareup.retrofit2:retrofit` | Declarative REST API client for `production.getmarks.app` (`fv.java`, `ex.java`). |
| **OkHttp 3** | `com.squareup.okhttp3:okhttp` | HTTP engine, connection pooling, header injection, logging (`nu9.java`, `ou9.java`). |
| **Gson** | `com.google.code.gson:gson` | JSON serialization/deserialization with custom type adapters (`SafeTypeAdapterFactory.java`). |
| **Dagger Hilt** | `com.google.dagger:hilt-android` | Dependency injection container for Singletons, Repositories, ViewModels (`qh3.java`, `rh3.java`). |
| **Room Database** | `androidx.room:room-runtime:2.5+` | SQLite abstraction for user sessions, goals, cached tests, bookmarks (`MarksDb.java`). |
| **Cashfree PG SDK** | `com.cashfree.pg:android-sdk` | Payment gateway for study pack purchases, native UPI intent launcher (`CashfreeNativeCheckoutActivity.java`). |
| **VdoCipher Aegis** | `com.vdocipher.aegis:vdocipher-android` | DRM-protected video streaming, encrypted offline caching, OTP playback (`com/vdocipher/aegis/`). |
| **Mixpanel Android** | `com.mixpanel.android:mixpanel-android` | User behavioral tracking, event funnels, cohort segmentation (`MixpanelAPI`). |
| **WebEngage SDK** | `com.webengage.sdk.android:android-sdk` | In-app messaging, push notification routing, engagement campaigns (`BaseApplication.java`). |
| **Microsoft Clarity** | `com.microsoft.clarity:clarity` | Session recording, UI dead-clicks, scroll heatmaps (`com/microsoft/clarity/`). |
| **Firebase Suite** | `com.google.firebase:*` | FCM push notifications, Remote Config, Crashlytics, Analytics (`MyFirebaseMessagingService.java`). |
| **MPAndroidChart** | `com.github.PhilJay:MPAndroidChart` | Graphical rendering of accuracy charts, monthly heatmaps, performance graphs. |
| **Glide & PhotoView** | `com.github.bumptech.glide` | Image caching and pinch-to-zoom for detailed mathematical diagram inspection. |
| **UCrop / ImagePicker** | `com.yalantis.ucrop`, `crocodile8.image_picker_plus` | Avatar image cropping and community doubt screenshot attachment. |
| **WorkManager** | `androidx.work:work-runtime` | Background synchronization of offline test attempts and book assets (`MARKSFileDownloadWorker.java`). |

---

## 6. Build Flavors, Configuration & Environments

### 6.1. Build Flavors Found in Code
The application binary contains evidence of the following build variant:
- **Build Flavor:** `app_engineeringProdRelease` (found in `@Metadata(..., d2 = {"...app_engineeringProdRelease"})` across all Kotlin classes, e.g., `BaseApplication.java#35`, `fv.java#219`).
- **Product Type:** Engineering & Medical Entrance Prep (`ProdRelease`).

### 6.2. Environment URLs Found in Code

| Environment Key | Base URL String | Source File & Class Citation |
| :--- | :--- | :--- |
| **API Version 4 (Primary)** | `https://production.getmarks.app/api/v4/` | `defpackage/qh3.java#139`, `defpackage/fv.java` |
| **API Version 1 (Auth/Core)** | `https://production.getmarks.app/api/v1/` | `defpackage/qh3.java#363`, `defpackage/qh3.java#382`, `defpackage/nu.java`, `defpackage/ex.java` |
| **API Version 2 (Exams/CT)** | `https://production.getmarks.app/api/v2/` | `defpackage/qh3.java#415`, `defpackage/qh3.java#440`, `defpackage/qu.java`, `defpackage/gx.java` |
| **API Version 3 (Notebooks/LB)** | `https://production.getmarks.app/api/v3/` | `defpackage/qh3.java#458`, `defpackage/qh3.java#476`, `defpackage/qh3.java#555`, `defpackage/tu.java`, `defpackage/ix.java` |
| **Tracker API** | `https://prod-tracker-api.getmarks.app/api/` | `defpackage/qh3.java#590`, `defpackage/zde.java` |
| **Asset CDN** | `https://cdn-assets.getmarks.app/` | `defpackage/km7.java#54`, `defpackage/s40.java#54` |
| **Deep Link Gateway** | `https://link.getmarks.app/` | `defpackage/ll7.java#58`, `defpackage/le.java#326` |
| **Web Access Portal** | `https://getmarks.app/` | `defpackage/bz8.java#54`, `defpackage/dc3.java#169` |
| **Payment Redirect Host** | `https://www.mathongo.com/marks/android/pay/` | `StudyResourceWebviewActivity.java#89`, `VSPaymentWebViewActivity.java#168` |
| **Country/State Utility** | `https://countriesnow.space/api/v0.1/` | `defpackage/qh3.java#570`, `defpackage/ot2.java` |

---

## 7. Local Data Models & Storage Architecture

### 7.1. Room Database (`MARKS_DB`) Specification
- **Database Class:** `com.scoremarks.marks.data.local.MarksDb` (`MarksDb.java#44`)
- **Database Name:** `"MARKS_DB"` (`qh3.java#77`)
- **Schema Version:** `14` (`MarksDb.java#42`)
- **Export Schema:** `true`

#### Entity to Table & DAO Mapping:
| Entity Class | DAO Interface | Storage Purpose |
| :--- | :--- | :--- |
| `User.class` | `UserDao` | Cached authenticated student profile, tokens, category. |
| `WeekMap.class` | `WeeklyGoalDao` | Weekly question target counters and status flags. |
| `LBProgress.class` | `MyDailyGoalDao` | Daily goal progress and league leaderboard counters. |
| `Notification.class` | `NotificationDao` | Archive of received push notifications. |
| `ExamCategory.class` | `ExamCategoryDao` | Hierarchical list of supported competitive exams. |
| `QuestionFilters.class` | `QuestionFilterDao` | User's active question filter settings per chapter. |
| `ChapterFilters.class` | `ChapterFilterDao` | User's active chapter filter settings. |
| `VidSolChapterFilters.class` | `VidSolChapterFilterDao` | Filter settings for video solutions library. |
| `NotebookFilters.class` | `NotebookFilterDao` | Active notebook filter selections. |
| `ChapterSort.class` | `ChapterSortDao` | Sorting preference for chapter lists (e.g., Weightage). |
| `VidSolChapterSort.class` | `VidSolChapterSortDao` | Sorting preference for video solutions. |
| `QuestionSort.class` | `QuestionSortDao` | Sorting preference for question lists (e.g., Year Desc). |
| `SubmitTestRequest.class` | `CustomTestSubmitTestDao` | Offline attempt queue for tests pending network upload. |
| `TrackedExamColor.class` | `TrackedExamsColorDao` | Visual color palette configured for home screen exams. |
| `RecentSearch.class` | `QCRecentSearchDao` | Recent search queries in Quick Concept lookup. |
| `BookLocal.class` | `BookLocalDao` | Offline downloaded Marks Selected book metadata. |

### 7.2. Shared Preferences Usage
The app stores non-relational flags in Android `SharedPreferences`:
- `MARKS_PREFS`: Session flags (`is_logged_in`, `auth_token`, `refresh_token`, `selected_exam_id`, `target_year`).
- `THEME_PREFS`: Light / Dark mode preference (`LightDarkValues.java`).
- `WIDGET_PREFS`: Countdown widget target exam and dates (`ExamWidgetMidnightReceiver.java`).
- `HINT_POPUP_PREFS`: User preference to suppress question hint popups (`DisableHintPopupResponse.java`).

---

## 8. Security Findings

> [!WARNING]
> Hardcoded credentials and secrets were detected in the decompiled Java/Kotlin source and decoded application resources. To comply with security rules, the secret values are **REDACTED** below with their exact source locations documented for remediation:

| Finding ID | Secret / Credential Type | Redacted Preview | Exact Source File & Line | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-001** | Mixpanel Project Token | `76fe371aeb70********************` | `defpackage/qh3.java#114` | High |
| **SEC-002** | WebEngage Account Key (Base64) | `in~311c****` (`aW5+MzExYzQ3MDg=`) | `com/scoremarks/marks/BaseApplication.java#66` | High |
| **SEC-003** | Google OAuth2 Web Client ID | `406420339924-ketncqif4a********************.apps.googleusercontent.com` | `res/values/strings.xml` (`default_web_client_id`) | Medium |
| **SEC-004** | Firebase Project Database URL | `https://marks-62f26.firebaseio.com` | `res/values/strings.xml` (`firebase_database_url`) | Medium |
| **SEC-005** | Google Firebase App ID | `1:406420339924:android:c87f3afa************` | `res/values/strings.xml` (`google_app_id`) | Medium |
| **SEC-006** | GCM / FCM Default Sender ID | `406420339924` | `res/values/strings.xml` (`gcm_defaultSenderId`) | Low |

---

## 9. Gaps & Open Questions

1. **Token Refresh Rotation:** While `nu.java` exposes token refresh mechanisms, the exact concurrency locking behavior during simultaneous 401 interceptor calls should be verified via live traffic capture `[INFERRED]`.
2. **Cashfree Webhook vs Client Polling:** The app uses client-side polling (`/payment/checkout/order/status`) to confirm payment completion; whether a fallback server-to-server webhook exists requires backend confirmation `[INFERRED]`.
3. **VdoCipher OTP Lifetime:** The exact time-to-live of the video playback OTP generated by `/courses/.../video/otp` is not statically defined in the client and is determined server-side `[UNKNOWN]`.
4. **WebSocket / Real-time Sync:** No WebSocket connections were found in the native Retrofit interfaces; push notifications (FCM / WebEngage) appear to drive real-time notifications `[INFERRED]`.
