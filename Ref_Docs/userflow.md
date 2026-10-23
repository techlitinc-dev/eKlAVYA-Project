# User Journeys & Interaction Sequences: MARKS Application

## Table of Contents
1. [Journey 1: Onboarding & Authentication](#1-journey-1-onboarding--authentication)
2. [Journey 2: Chapter-wise PYQ Solving (Practice & Test Mode)](#2-journey-2-chapter-wise-pyq-solving)
3. [Journey 3: Custom Test Generator (CTG) & Examination](#3-journey-3-custom-test-generator-ctg--examination)
4. [Journey 4: DRM Video Solutions & Course Streaming](#4-journey-4-drm-video-solutions--course-streaming)
5. [Journey 5: Smart Notebooks & Bookmark Management](#5-journey-5-smart-notebooks--bookmark-management)
6. [Journey 6: Homework Assignment Flow (Teacher $\to$ Student)](#6-journey-6-homework-assignment-flow)
7. [Journey 7: Premium Study Pack Checkout (Cashfree)](#7-journey-7-premium-study-pack-checkout)
8. [Journey 8: Daily Goals, Heatmaps & Account Settings](#8-journey-8-daily-goals-heatmaps--account-settings)
9. [Gaps & Open Questions](#9-gaps--open-questions)

---

## 1. Journey 1: Onboarding & Authentication

### 1.1. Description & Context
A prospective student opens the app for the first time, provides their mobile phone number, receives an SMS OTP, configures their academic profile (target exam, target year, class), and is routed to the personalized dashboard.

### 1.2. Sequence Flowchart

```mermaid
flowchart TD
    Start([App Cold Launch]) --> Splash["SplashActivity"]
    Splash --> CheckAuth{"User Token in Room DB?<br/>(UserDao.getUser())"}
    CheckAuth -- Token Exists --> ValidateToken["POST /api/v4/user/me"]
    ValidateToken -- Valid --> Home["HomeActivity"]
    ValidateToken -- Expired/Invalid --> PhoneAuth["PhoneAuthActivity"]
    CheckAuth -- No Token --> PhoneAuth

    PhoneAuth --> InputPhone["Student enters 10-digit Phone Number"]
    InputPhone --> ReqOTP["POST /api/v1/auth/request-otp"]
    ReqOTP --> OTPWait["PhoneAuthOtpActivity<br/>(60-second Timer)"]

    OTPWait --> EnterOTP["Student inputs 6-digit code"]
    EnterOTP --> VerifyCall["POST /api/v1/auth/verify-otp"]
    VerifyCall --> ValidOTP{"OTP Valid?"}

    ValidOTP -- No --> OTPError["Display Error Snack<br/>(Remaining attempts: N)"]
    OTPError --> OTPWait

    ValidOTP -- Yes --> SaveToken["Store idToken & refreshToken in SharedPreferences & Room"]
    SaveToken --> CheckNewUser{"Is Profile Complete?"}

    CheckNewUser -- Incomplete --> OnboardingOB1["OnboardingProfileActivity"]
    OnboardingOB1 --> SelectExam["Select Exam (JEE Main / NEET / BITSAT)"]
    SelectExam --> SelectYear["Select Target Year (2025 / 2026 / 2027)"]
    SelectYear --> SelectClass["Select Class (11th / 12th / Dropper)"]
    SelectClass --> PostProfile["POST /api/v4/user/profile/onboarding"]
    PostProfile --> Home

    CheckNewUser -- Complete --> Home
```

### 1.3. Screens & Endpoints Touched
- **Screens Touched:** `SplashActivity` $\to$ `PhoneAuthActivity` $\to$ `PhoneAuthOtpActivity` $\to$ `OnboardingProfileActivity` $\to$ `HomeActivity`.
- **Endpoints Touched:**
  - `POST https://production.getmarks.app/api/v1/auth/request-otp` (`nu.java#b`)
  - `POST https://production.getmarks.app/api/v1/auth/verify-otp` (`nu.java#d`)
  - `POST https://production.getmarks.app/api/v4/user/profile/onboarding` (`fv.java#O`)
  - `GET https://production.getmarks.app/api/v4/user/me` (`fv.java#u3`)

---

## 2. Journey 2: Chapter-wise PYQ Solving (Practice & Test Mode)

### 2.1. Description & Context
A student selects a subject and chapter (e.g., Mathematics $\to$ "Definite Integration"), configures their filters (e.g., JEE Main 2024, Numerical only), and attempts problems in either Practice Mode (immediate solution verification) or Test Mode.

### 2.2. Sequence Flowchart

```mermaid
flowchart TD
    Home["HomeActivity (PYQ Tab)"] --> SelectExam["CPYQFlowActivity<br/>(Select Target Exam: JEE Main)"]
    SelectExam --> SelectSubject["Select Subject (Physics / Chem / Maths)"]
    SelectSubject --> SelectChapter["ChapterActivity<br/>(Display Chapters with Question Counts)"]
    SelectChapter --> SelectModePrompt{"Choose Solving Mode"}

    SelectModePrompt -- Practice Mode --> PracticeMode["QuestionActivityV4 (Mode: Practice)"]
    SelectModePrompt -- Test Mode --> TestMeta["TestModeMetaActivity (Timed Mode)"]
    TestMeta --> PracticeMode

    PracticeMode --> FetchQs["GET /api/v4/cpyqb/exam/{examId}/subject/{subjectId}/chapter/{chapterId}/questions"]
    FetchQs --> RenderQ["Render Question HTML & LaTeX via ExpandableHtmlTextView"]

    RenderQ --> UserInput{"Question Type"}
    UserInput -- Single Correct MCQ --> SelectOpt["Tap Option Radio Button (A, B, C, D)"]
    UserInput -- Numerical NAT --> InputNum["Virtual Numeric Keypad Entry"]

    SelectOpt --> CheckAction["Tap 'Check Answer'"]
    InputNum --> CheckAction

    CheckAction --> PostAttempt["POST /api/v4/solving-modes/practice/start"]
    PostAttempt --> EvaluateAns{"Is Answer Correct?"}

    EvaluateAns -- Correct --> GreenBanner["Show Green 'Correct' Card (+4 Marks)"]
    EvaluateAns -- Incorrect --> RedBanner["Show Red 'Incorrect' Card (-1 Mark)"]

    GreenBanner --> ShowSolution["Display Written Step-by-Step Solution"]
    RedBanner --> ShowSolution

    ShowSolution --> VideoAction{"Watch Video Explanation?"}
    VideoAction -- Yes --> LaunchVideo["VideoSolActivity (VdoCipher Player)"]
    VideoAction -- No --> NextQ["Tap 'Next Question' -> Next Question in Queue"]
```

### 2.3. Screens & Endpoints Touched
- **Screens Touched:** `HomeActivity` $\to$ `CPYQFlowActivity` $\to$ `ChapterActivity` $\to$ `QuestionActivityV4` $\to$ `VideoSolActivity`.
- **Endpoints Touched:**
  - `GET https://production.getmarks.app/api/v4/cpyqb/exam/{examId}/subject/{subjectId}/chapter/{chapterId}/questions` (`fv.java#z2`)
  - `POST https://production.getmarks.app/api/v4/solving-modes/practice/start` (`fv.java#y`)
  - `GET https://production.getmarks.app/api/v4/questions/{questionId}/hint/feedback-status` (`fv.java#G`)

---

## 3. Journey 3: Custom Test Generator (CTG) & Examination

### 3.1. Description & Context
A student creates a personalized practice examination tailored to their current revision schedule by picking chapters and time limits, taking the exam under NTA CBT conditions, and reviewing their performance.

### 3.2. Sequence Flowchart

```mermaid
flowchart TD
    Home["HomeActivity (Custom Tests Tab)"] --> CTGDash["CustomTestDashboardActivity"]
    CTGDash --> TapCreate["Tap 'Create Custom Test'"]
    TapCreate --> Step1["CustomTestActivity (Step 1)"]

    Step1 --> FetchStep1["GET /api/v4/custom-test/build/step1"]
    FetchStep1 --> SelectSubjects["Select Subjects (Physics, Chemistry, Maths)"]
    SelectSubjects --> Step2["CustomTestActivity (Step 2)"]

    Step2 --> FetchStep2["POST /api/v4/custom-test/build/step2"]
    FetchStep2 --> SelectChapters["Pick Chapters & Set Question Allocation per Chapter"]
    SelectChapters --> SetTimer["Configure Time Duration (30m - 180m)"]
    SetTimer --> SubmitBuild["POST /api/v4/custom-test/generate"]

    SubmitBuild --> TestCreated["Test Created -> Launch CustomTestQuestionActivity"]
    TestCreated --> StartCBT["NTA CBT Test Screen (Timer Counting Down)"]

    loop Question Loop
        StartCBT --> ViewQ["Display Question & Options"]
        ViewQ --> AnsAction{"Student Response"}
        AnsAction -- Answer --> SaveNext["Save & Next -> Turn Green in Palette"]
        AnsAction -- Mark --> MarkNext["Mark for Review -> Turn Purple in Palette"]
        AnsAction -- Clear --> ResetAns["Clear Response"]
    end

    StartCBT --> TimeUp{"Timer Expiry or Tap 'Submit'?"}
    TimeUp -- Yes --> ConfirmModal["Show Attempt Summary Confirmation Modal"]
    ConfirmModal --> ConfirmYes["Confirm Submission"]

    ConfirmYes --> PostSubmit["POST /api/v4/custom-test/submit"]
    PostSubmit --> ReportCard["CustomTestRepordCardActivity"]

    ReportCard --> ViewAnalytics["Display Score, Negative Marks, Accuracy %, Percentile"]
    ViewAnalytics --> TapSolutions["Tap 'Review Solutions' -> CustomTestSolutionActivity"]
```

### 3.3. Screens & Endpoints Touched
- **Screens Touched:** `CustomTestDashboardActivity` $\to$ `CustomTestActivity` $\to$ `CustomTestQuestionActivity` $\to$ `CustomTestRepordCardActivity` $\to$ `CustomTestSolutionActivity`.
- **Endpoints Touched:**
  - `GET https://production.getmarks.app/api/v4/custom-test/build/step1` (`fv.java#n`)
  - `POST https://production.getmarks.app/api/v4/custom-test/build/step2` (`fv.java#q`)
  - `POST https://production.getmarks.app/api/v4/custom-test/submit` (`fv.java#T`)
  - `GET https://production.getmarks.app/api/v4/custom-test/analysis/{testId}` (`fv.java#r`)

---

## 4. Journey 4: DRM Video Solutions & Course Streaming

### 4.1. Description & Context
A student studying a complex concept taps "Watch Video Solution" on a difficult question or navigates through an enrolled video course. The app securely acquires an OTP token and launches the VdoCipher hardware-encrypted player.

### 4.2. Sequence Flowchart

```mermaid
flowchart TD
    QuestionScreen["QuestionActivityV4 / MarksCoursesActivity"] --> TapVideo["Tap 'Watch Video'"]
    TapVideo --> CheckSub{"Is User Subscribed or Demo Lecture?"}

    CheckSub -- Not Subscribed --> PremiumPrompt["MarksPremiumSelectionActivity (Upsell Modal)"]

    CheckSub -- Authorized --> ReqOTP["POST /api/v4/courses/.../content/{contentId}/video/otp"]
    ReqOTP --> ServerVerify["Server verifies user entitlements"]
    ServerVerify --> ReturnToken["Return { otp: '...', playbackInfo: '...' }"]

    ReturnToken --> LaunchPlayer["VideoSolActivity / PlayerActivity"]
    LaunchPlayer --> InitVdo["VdoCipher Aegis SDK initializes Widevine DRM pipeline"]
    InitVdo --> RenderStream["Encrypted playback starts with dynamic user watermark"]

    loop Every 15 Seconds of Watch Time
        RenderStream --> SendHeartbeat["POST /api/v4/courses/video/progress { position, duration }"]
    end

    RenderStream --> Finished{"Video Finished?"}
    Finished -- Yes --> MarkDone["POST /api/v4/courses/.../mark-video-complete"]
```

### 4.3. Screens & Endpoints Touched
- **Screens Touched:** `QuestionActivityV4` $\to$ `VideoSolActivity` / `MarksCoursesActivity`.
- **Endpoints Touched:**
  - `GET https://production.getmarks.app/api/v4/courses/.../content/{contentId}/video/otp` (`fv.java#f`, `fv.java#v`)
  - `POST https://production.getmarks.app/api/v4/courses/video/mark` (`fv.java#g`)

---

## 5. Journey 5: Smart Notebooks & Bookmark Management

### 5.1. Description & Context
While practicing, a student flags tricky questions into custom notebooks (e.g., "Organic Reaction Mechanisms") and reviews them before an exam.

### 5.2. Sequence Flowchart

```mermaid
flowchart TD
    QuestionScreen["QuestionActivityV4"] --> TapBookmark["Tap 'Bookmark' Icon"]
    TapBookmark --> FetchNotebooks["GET /api/v4/notebook/smart"]
    FetchNotebooks --> ShowSheet["Show 'Add to Notebook' Bottom Sheet"]

    ShowSheet --> OptionAction{"Choose Action"}
    OptionAction -- Existing Notebook --> SelectNB["Select existing notebook checkbox"]
    OptionAction -- Create New Notebook --> CreateNew["Input Notebook Title & Color Tag"]
    CreateNew --> PostCreateNB["POST /api/v4/notebook"]
    PostCreateNB --> SelectNB

    SelectNB --> AddNoteText["Optional: Enter personal student note"]
    AddNoteText --> SaveAction["Tap 'Save to Notebook'"]
    SaveAction --> PostQuestion["POST /api/v4/notebook/question"]
    PostQuestion --> UpdateLocalDB["Update Room DB (NotebookFilterDao)"]
    UpdateLocalDB --> DismissSheet["Show 'Question Bookmarked' Toast"]
```

### 5.3. Screens & Endpoints Touched
- **Screens Touched:** `QuestionActivityV4` $\to$ `NotebookListActivity` $\to$ `BookmarkedQsListActivity`.
- **Endpoints Touched:**
  - `GET https://production.getmarks.app/api/v4/notebook/smart` (`fv.java#z3`)
  - `POST https://production.getmarks.app/api/v4/notebook` (`fv.java#z`)
  - `POST https://production.getmarks.app/api/v4/notebook/question` (`fv.java#z0`)

---

## 6. Journey 6: Homework Assignment Flow (Teacher $\to$ Student)

### 6.1. Description & Context
A coaching teacher selects 15 PYQs from the question repository, sets a deadline, and shares a deep link on WhatsApp. A student opens the link, completes the assignment on their phone, and the teacher reviews classroom analytics.

### 6.2. Sequence Flowchart

```mermaid
flowchart TD
    TeacherHome["MarksAssignmentTeacherActivity"] --> CreatePrompt["Tap 'Create Homework Assignment'"]
    CreatePrompt --> PickQuestions["Select Subject -> Chapter -> Pick 15 Questions"]
    PickQuestions --> SetDue["Set Assignment Title & Due Date"]
    SetDue --> PostAssignment["POST /api/v4/assignment/teacher/create"]
    PostAssignment --> GenLink["Generate Deep Link: https://link.getmarks.app/assignment/student?code=6X9A21"]
    GenLink --> ShareWA["Share link via WhatsApp intent"]

    ShareWA --> StudentClick["Student taps link on phone"]
    StudentClick --> LaunchStudent["App intercepts link -> Opens MAStudentActivity"]
    LaunchStudent --> FetchDetail["GET /api/v4/assignment/student/id/{assignmentId}"]
    FetchDetail --> AttemptQs["Student solves questions under assignment timer"]
    AttemptQs --> SubmitAssignment["POST /api/v4/assignment/student/submit"]
    SubmitAssignment --> StudentScore["Display Student Score & Rank"]

    SubmitAssignment --> TeacherNotify["Teacher Dashboard receives submission"]
    TeacherNotify --> ViewClassAnalytics["AnalysisActivity (Class Average, Hardest Questions)"]
```

### 6.3. Screens & Endpoints Touched
- **Screens Touched:** `MarksAssignmentTeacherActivity` $\to$ `AssignmentQuestionsListFragment` $\to$ `MAStudentActivity` $\to$ `AnalysisActivity`.
- **Endpoints Touched:**
  - `POST https://production.getmarks.app/api/v4/assignment/teacher/create` (`fv.java#s`)
  - `GET https://production.getmarks.app/api/v4/assignment/student/id/{assignmentId}` (`fv.java#S`)
  - `GET https://production.getmarks.app/api/v4/assignment/student/id/{assignmentId}/analysis` (`fv.java#v2`)

---

## 7. Journey 7: Premium Study Pack Checkout (Cashfree)

### 7.1. Description & Context
A student unlocks the "JEE Main 2026 Ultimate Video Solutions Pack" using native UPI checkout powered by Cashfree.

### 7.2. Sequence Flowchart

```mermaid
flowchart TD
    Home["HomeActivity (Profile / Store)"] --> StoreView["MarksPremiumSelectionActivity"]
    StoreView --> FetchPacks["GET /api/v4/marks-premium/platform/mobile"]
    FetchPacks --> RenderPacks["Render Study Pack Cards & Discount Offers"]

    RenderPacks --> SelectPack["Student selects 'Ultimate PYQ Pack (Rs. 999)'"]
    SelectPack --> TapCheckout["Tap 'Proceed to Checkout'"]
    TapCheckout --> CheckoutScreen["NewPaymentCheckoutActivity"]

    CheckoutScreen --> ApplyCoupon{"Apply Promo Code?"}
    ApplyCoupon -- Yes --> PostCoupon["POST /api/v4/payment/coupon/apply"]
    PostCoupon --> UpdateAmount["Update payable total"]
    ApplyCoupon -- No --> CreateOrder

    UpdateAmount --> CreateOrder["POST /api/v4/payment/checkout/order"]
    CreateOrder --> ReturnToken["Cashfree returns { order_token: '...', order_id: '...' }"]

    ReturnToken --> LaunchCashfree["CashfreeNativeCheckoutActivity opens native UPI sheet"]
    LaunchCashfree --> UserPays["User selects GPay / PhonePe -> Authorizes UPI PIN"]
    UserPays --> CashfreeCallback["Cashfree SDK notifies checkout activity of intent result"]

    CashfreeCallback --> PollStatus["Loop: GET /api/v4/payment/checkout/order/status?orderId=..."]
    PollStatus --> CheckPaid{"Status == 'PAID'?"}

    CheckPaid -- Pending --> WaitPoll["Wait 2s -> Poll again (max 5 retries)"]
    WaitPoll --> PollStatus

    CheckPaid -- Failed --> ShowFail["Display 'Payment Failed' Dialog + Support Email"]
    CheckPaid -- Paid --> ShowSuccess["Display 'Payment Successful' Confetti Dialog"]
    ShowSuccess --> UnlockEntitlement["Update Room DB & refresh user entitlements"]
```

### 7.3. Screens & Endpoints Touched
- **Screens Touched:** `MarksPremiumSelectionActivity` $\to$ `NewPaymentCheckoutActivity` $\to `CashfreeNativeCheckoutActivity`.
- **Endpoints Touched:**
  - `GET https://production.getmarks.app/api/v4/marks-premium/platform/mobile` (`fv.java#x0`)
  - `POST https://production.getmarks.app/api/v4/payment/checkout/order` (`fv.java#u`)
  - `GET https://production.getmarks.app/api/v4/payment/checkout/order/status` (`fv.java#y1`)

---

## 8. Journey 8: Daily Goals, Heatmaps & Account Settings

### 8.1. Description & Context
A student checks their daily goal progress, visualizes their monthly consistency heatmap, and manages notifications or logs out.

### 8.2. Sequence Flowchart

```mermaid
flowchart TD
    Home["HomeActivity (Dashboard Tab)"] --> ViewStreak["Display Today's Goal: '24 / 30 Questions Solved'"]
    ViewStreak --> TapHeatmap["Tap 'View Activity'"]
    TapHeatmap --> GoalScreen["DailyGoalActivity"]

    GoalScreen --> FetchHeatmap["GET /api/v4/targets/heatmap?month=2026-10"]
    FetchHeatmap --> RenderGrid["Render GitHub-style daily solved green boxes"]

    GoalScreen --> ChangeGoalPrompt{"Edit Daily Target?"}
    ChangeGoalPrompt -- Yes --> InputNewTarget["Select new target: 50 Questions/day"]
    InputNewTarget --> PostNewTarget["POST /api/v4/targets/update"]
    PostNewTarget --> UpdateLocalGoal["Update Room DB (DailyGoalDao)"]

    GoalScreen --> Settings["Navigate to Settings"]
    Settings --> TapLogout["Tap 'Logout'"]
    TapLogout --> ConfirmLogout["Confirm Logout Modal"]
    ConfirmLogout --> ClearData["Clear SharedPreferences & purge Room DB tables"]
    ClearData --> NavLogin["Navigate to OnBoardingActivity (clearing back-stack)"]
```

---

## 9. Gaps & Open Questions

1. **UPI Timeout Handling:** If the native UPI application crashes or takes longer than 60 seconds to respond, does the client cancel the order token automatically? This should be verified with live Cashfree logs `[INFERRED]`.
2. **Offline Goal Sync:** If a student solves 20 questions offline, does the heatmap reflect those attempts immediately using Room data, or only after the background sync worker completes? `[INFERRED]`.
