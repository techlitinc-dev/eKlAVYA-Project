# End-to-End User Journeys & Interaction Flows (`userflow.md`)
## eKlAVYA / Mentor AI — Web Application & Android Application

> **Scope:** Unified behavioral and API interaction flows for both the **Next.js / React Web Application** and the **Kotlin / Jetpack Compose Android Application**, covering the **Parent Portal** and **Student Portal** across all 18 backend domains in [endpoints.md](file:///home/tushka/Projects/eKlAVYA/endpoints.md).

---

## Table of Contents

1. [Journey 1: Parent Registration, Child Onboarding & Exam Selection](#1-journey-1-parent-registration-child-onboarding--exam-selection)
2. [Journey 2: Student Login, Home Dashboard & Daily Habit Loop (Daily Dose + Heatmap)](#2-journey-2-student-login-home-dashboard--daily-habit-loop)
3. [Journey 3: Hermes 1-to-1 Socratic AI Mentor, Micro-Topic Quiz & Concept Wall](#3-journey-3-hermes-1-to-1-socratic-ai-mentor-micro-topic-quiz--concept-wall)
4. [Journey 4: Chapter-wise PYQ Bank (CPYQB), Practice Mode & Automated Error Notebook](#4-journey-4-chapter-wise-pyq-bank-cpyqb-practice-mode--automated-error-notebook)
5. [Journey 5: Multi-Step Custom Test Generator (CTG) & NTA CBT Examination](#5-journey-5-multi-step-custom-test-generator-ctg--nta-cbt-examination)
6. [Journey 6: AI Hub — Snap & Solve Vision OCR, SSE Streaming Doubt Solver & Similar Questions](#6-journey-6-ai-hub--snap--solve-vision-ocr-sse-streaming-doubt-solver--similar-questions)
7. [Journey 7: Revision Flash Cards (RFC), Smart Notebooks & Spaced Repetition](#7-journey-7-revision-flash-cards-rfc-smart-notebooks--spaced-repetition)
8. [Journey 8: Teacher / Parent Homework Assignment Creation, Join Code & Classroom Analytics](#8-journey-8-teacher--parent-homework-assignment-creation-join-code--classroom-analytics)
9. [Journey 9: AI Rank Predictor, College Cutoff Explorer & Physical OMR Grader](#9-journey-9-ai-rank-predictor-college-cutoff-explorer--physical-omr-grader)
10. [Journey 10: Parent Monitoring, Bilingual Daily Summaries & Subscription Checkout](#10-journey-10-parent-monitoring-bilingual-daily-summaries--subscription-checkout)

---

## 1. Journey 1: Parent Registration, Child Onboarding & Exam Selection

### 1.1. Context & Platform Behavior
- **Web App:** Multi-step onboarding wizard at `/onboarding` after parent signup at `/register`.
- **Android App:** `OnBoardingAuthActivity` $\to$ `ParentPreferencesActivity` $\to$ `CreateChildProfileActivity` $\to$ `ExamSelectionActivity`.
- **Goal:** Register a parent, set preferred language (`en`, `hi`, `mr`, `hinglish`, etc.), create the student's login credentials, select target exam (`JEE_MAIN`, `JEE_ADVANCED`, `NEET`), and seed syllabus micro-topics.

### 1.2. Flowchart
```mermaid
flowchart TD
    Start([Parent Opens Web / Android App]) --> RoleSelect["Choose 'I am a Parent'"]
    RoleSelect --> RegForm["Enter Name, Email, Mobile, Password"]
    RegForm --> CallReg["POST /api/auth/register/simple"]
    CallReg --> CallLogin["POST /api/auth/login/email"]
    CallLogin --> SaveParentJWT["Store Parent JWT & parent_id"]

    SaveParentJWT --> PrefStep["Step 1: Select Language (Hindi/English/Marathi) & Notifications"]
    PrefStep --> CallPref["POST /api/onboarding/preferences?parent_id={id}"]

    CallPref --> ChildStep["Step 2: Create Child Profile & Student Credentials<br/>(Name, Age, Grade, Username, Password)"]
    ChildStep --> CallChild["POST /api/onboarding/child?parent_id={id}"]
    CallChild --> SaveChildId["Store child_id"]

    SaveChildId --> ExamStep["Step 3: Fetch Available Exams"]
    ExamStep --> CallAvail["GET /api/onboarding/exams/available"]
    CallAvail --> PickExam["Select Exam (JEE_MAIN / NEET), Target Date & Subject Weightages"]
    PickExam --> CallSelectExam["POST /api/onboarding/exam/select?parent_id={pid}&child_id={cid}"]
    CallSelectExam --> SeedTopics["POST /api/hermes/admin/seed-topics"]
    SeedTopics --> ParentDash["Redirect to Parent Command Center (/parent/dashboard)"]
```

---

## 2. Journey 2: Student Login, Home Dashboard & Daily Habit Loop

### 2.1. Context & Platform Behavior
- **Web App:** Student logs in at `/login/student` and lands on `/student/dashboard`.
- **Android App:** Student logs in via `StudentLoginActivity` and lands on `HomeActivity` (Bottom Tab 1: Dashboard) + syncs the Android Home Screen Countdown Widget (`ExamWidgetMidnightReceiver`).

### 2.2. Flowchart
```mermaid
flowchart TD
    Start([Student Launch]) --> Login["POST /api/auth/login/child<br/>{ username, password }"]
    Login --> StoreToken["Save Student JWT & student_id"]
    StoreToken --> ParallelLoad["Parallel Dashboard Hydration"]

    ParallelLoad --> CallToday["GET /api/hermes/today<br/>(Countdown, Concept Wall, Daily Chat Cap)"]
    ParallelLoad --> CallHeatmap["GET /api/targets/heatmap?month=YYYY-MM<br/>(GitHub-Style Consistency Grid)"]
    ParallelLoad --> CallLeagues["GET /api/leaderboard/achievements<br/>(Bronze -> Master League Rank)"]
    ParallelLoad --> CallDose["GET /api/targets/daily-dose?examId=jee_main<br/>(5-Question Daily Sprint)"]

    CallDose --> StartSprint{"Tap 'Start Daily Dose (5 Qs)'"}
    StartSprint -- Yes --> Solve5["Solve 5 Rapid Questions (3-Min Sprint Timer)"]
    Solve5 --> SubmitSprint["POST /api/targets/daily-dose/submit"]
    SubmitSprint --> AwardPts["Earn +15 pts/correct + 25 Streak Bonus"]
    AwardPts --> RefreshDashboard["Heatmap Green Cell Lit + League Rank Climbs"]
```

---

## 3. Journey 3: Hermes 1-to-1 Socratic AI Mentor, Micro-Topic Quiz & Concept Wall

### 3.1. Context & Platform Behavior
- **Core Rule:** Hermes never hands out final numerical answers. It guides the student with formulas and Socratic questions in their chosen language (`en`, `hi`, `hinglish`, `mr`, etc.).
- **Micro-State Machine:** Every syllabus micro-topic transitions `UNTOUCHED` $\to$ `LEARNING` $\to$ `MASTERED` (2 consecutive passes $\ge 70\%$). Three consecutive failures lock a **Concept Wall**, steering all mentor sessions to revise that topic until cleared.

### 3.2. Flowchart
```mermaid
flowchart TD
    OpenMentor["Open Hermes Mentor (/student/mentor or HermesChatActivity)"] --> LoadTopics["GET /api/hermes/topics & GET /api/hermes/progress"]
    LoadTopics --> CheckWall{"Is a Concept Wall Active?"}

    CheckWall -- Yes --> BannerLock["Show Amber Banner: 'Concept Wall Active on Rotational Motion'"]
    CheckWall -- No --> PickTopic["Student Selects Any In-Scope Micro-Topic"]

    BannerLock --> SendChat["POST /api/hermes/chat<br/>{ message, micro_topic_id, language }"]
    PickTopic --> SendChat

    SendChat --> RenderReply["Render Socratic Hint + KaTeX Formulas + Remaining Daily Turns"]
    RenderReply --> TakeQuiz{"Tap 'Verify Mastery Quiz'?"}

    TakeQuiz -- Yes --> RunQuiz["Student Attempts 5–10 Topic Questions"]
    RunQuiz --> PostAttempt["POST /api/hermes/quiz/attempt<br/>{ micro_topic_id, score_pct, total_questions }"]
    PostAttempt --> EvalState{"Evaluate Transition"}

    EvalState -- "2nd Consecutive Pass (>=70%)" --> Mastered["State -> MASTERED (+25 XP, Badge Check)"]
    EvalState -- "1st Pass (>=70%)" --> Learning["State -> LEARNING (Wall Cleared if Active)"]
    EvalState -- "3rd Consecutive Fail (<70%)" --> LockWall["Lock Concept Wall -> Force Targeted Revision"]
```

---

## 4. Journey 4: Chapter-wise PYQ Bank (CPYQB), Practice Mode & Automated Error Notebook

### 4.1. Context & Platform Behavior
- Students browse 20+ years of JEE Main, JEE Advanced, and NEET PYQs, filter by shift, year, question type (`MCQ` / `NAT`), attempt status (`unattempted`, `incorrect`, `starred`), or NEET Revision Zone (`high_yield`, `must_revise`, `trap_zone`), and verify answers one-by-one.

### 4.2. Flowchart
```mermaid
flowchart TD
    NavPYQ["Open PYQ Bank (/student/pyq or CPYQFlowActivity)"] --> SelectTree["Select Exam -> Subject -> Chapter -> Topic"]
    SelectTree --> ApplyFilters["Apply Chips: Year (2024), Type (MCQ/NAT), Zone (High Yield / Trap Zone)"]
    ApplyFilters --> FetchQs["GET /api/cpyqb/questions?examId=...&subjectId=...&chapterId=..."]

    FetchQs --> RenderQuestion["Render Question Statement (LaTeX/HTML) + Shift Tag + NCERT Page Badge"]
    RenderQuestion --> InputType{"Question Type?"}

    InputType -- MCQ --> PickOption["Select Option A / B / C / D"]
    InputType -- NAT --> EnterKeypad["Enter Decimal Value on Virtual Numeric Keypad"]

    PickOption --> SubmitPractice["POST /api/solving-modes/practice/start"]
    EnterKeypad --> SubmitPractice

    SubmitPractice --> CheckResult{"isCorrect == true?"}
    CheckResult -- Yes --> GreenCard["Show Green Banner (+4 Marks, +5 Points) + Step-by-Step Solution"]
    CheckResult -- No --> RedCard["Show Red Banner (-1 Mark, Auto-Logged to Error Notebook)"]

    RedCard --> GenSimilar{"Tap 'Practice 3 Similar Questions'?"}
    GenSimilar -- Yes --> CallSimilar["POST /api/ai-hub/qa/generate-similar-questions"]
    CallSimilar --> SolveIsomorphic["Attempt 3 AI-Synthesized Isomorphic Variants"]
```

---

## 5. Journey 5: Multi-Step Custom Test Generator (CTG) & NTA CBT Examination

### 5.1. Context & Platform Behavior
- **Web App:** Fullscreen NTA-style CBT interface with section tabs, countdown timer, and color-coded question palette (`Answered`, `Not Answered`, `Marked for Review`).
- **Android App:** `CustomTestActivity` (Wizard) $\to$ `CustomTestQuestionActivity` (Hardware Back-Press Guarded CBT) $\to$ `CustomTestReportCardActivity`.

### 5.2. Flowchart
```mermaid
flowchart TD
    OpenCTG["Open Custom Tests (/student/custom-test)"] --> Step1["GET /api/custom-test/build/step1"]
    Step1 --> ChooseSubj["Select Exam (JEE Main / NEET) & Subjects (Physics, Chemistry, Maths)"]
    ChooseSubj --> Step2["POST /api/custom-test/build/step2"]
    Step2 --> AllocCh["Select Chapters, Allocate Question Counts & Pick Duration (30m–180m)"]
    AllocCh --> Synthesize["POST /api/custom-test/generate"]

    Synthesize --> LaunchCBT["Enter Fullscreen NTA CBT Exam Screen (Timer Starts)"]
    loop Question Navigation Loop
        LaunchCBT --> ReadQ["View Question + Section Switcher + Question Palette"]
        ReadQ --> Action{"Student Action"}
        Action -- "Save & Next" --> MarkAnswered["status = 'answered' (Green Palette Badge)"]
        Action -- "Mark for Review" --> MarkReview["status = 'marked_for_review' (Purple Palette Badge)"]
        Action -- "Clear Response" --> ClearAns["status = 'unattempted'"]
    end

    LaunchCBT --> SubmitExam["Timer Expires or Student Confirms Submit<br/>POST /api/custom-test/submit"]
    SubmitExam --> ReportCard["Load Report Card: Score, Accuracy %, Percentile, Subject Breakdown"]
    ReportCard --> DeepAnalysis["GET /api/custom-test/analysis/{testId}<br/>(Topper Comparison, Speed/Question, Weak Topics, Solutions)"]
```

---

## 6. Journey 6: AI Hub — Snap & Solve Vision OCR, SSE Streaming Doubt Solver & Similar Questions

### 6.1. Context & Platform Behavior
- A student takes a photo (Android Camera / UCrop) or drags-and-drops a screenshot (Web) of a tough Physics/Math problem, extracts the LaTeX via Vision OCR, and streams a real-time step-by-step explanation over Server-Sent Events (`text/event-stream`).

### 6.2. Flowchart
```mermaid
flowchart TD
    OpenAIHub["Open AI Doubt Hub (/student/ai-hub or VisionDoubtActivity)"] --> UploadImg["Snap Photo or Upload Image of Question"]
    UploadImg --> CallOCR["POST /api/ai-hub/vision/ocr (multipart/form-data)"]
    CallOCR --> PreviewOCR["Display Extracted LaTeX Preview + Detected Subject Badge<br/>(Student can edit text before sending)"]

    PreviewOCR --> ChooseMode{"Select Explanation Mode"}
    ChooseMode -- "Socratic Hint Mode" --> StreamHint["POST /api/ai-hub/chat/stream { mode: 'socratic_hint' }"]
    ChooseMode -- "Step-by-Step Solution" --> StreamStep["POST /api/ai-hub/chat/stream { mode: 'step_by_step' }"]

    StreamHint --> RenderSSE["Render Real-Time SSE Chunks:<br/>Stage 1: analyzing -> Stage 2: reasoning -> Stage 3: solution -> [DONE]"]
    StreamStep --> RenderSSE
```

---

## 7. Journey 7: Revision Flash Cards (RFC), Smart Notebooks & Spaced Repetition

### 7.1. Flowchart
```mermaid
flowchart TD
    OpenRev["Open Revision Hub (/student/revision)"] --> ChooseTool{"Select Revision Tool"}

    ChooseTool -- "Flashcards & Formula Deck" --> LoadDeck["GET /api/rfc/subject/{subjectId}/chapter/{chapterId}/cards"]
    LoadDeck --> FlipCard["Tap Card to Flip (Front Prompt -> Back LaTeX Formula & Key Takeaways)"]
    FlipCard --> SwipeMastery["Swipe Right ('Got It' / mastered) or Left ('Needs Revision')"]
    SwipeMastery --> PostMastery["POST /api/rfc/mastery { cardId, masteryLevel }"]

    ChooseTool -- "Smart Notebooks" --> LoadNB["GET /api/notebook/smart"]
    LoadNB --> CreateNB["POST /api/notebook { title, colorHex, subjectId }"]
    CreateNB --> ViewSaved["GET /api/notebook/{notebookId}/questions<br/>(Review Bookmarked Questions & Personal Notes)"]

    ChooseTool -- "Error Notebook" --> LoadErr["GET /api/notebook/errors?status=unresolved&mistakeType=formula_mixup"]
    LoadErr --> ReattemptErr["Re-solve Historical Mistake -> Tap 'Mark Mastered'"]
    ReattemptErr --> ResolveCall["POST /api/notebook/errors/{errorId}/resolve (+10 League Points)"]
```

---

## 8. Journey 8: Teacher / Parent Homework Assignment Creation, Join Code & Classroom Analytics

### 8.1. Flowchart
```mermaid
flowchart TD
    TeacherStart["Parent / Teacher Opens Assignment Builder (/parent/assignments)"] --> PickPYQs["Filter PYQs & Select Question IDs + Set Due Date & Time Limit"]
    PickPYQs --> CallCreate["POST /api/assignment/teacher/create"]
    CallCreate --> ShowCode["Display 6-Char Join Code (e.g., 6X9A21) & Deep Link<br/>Share via WhatsApp / Copy Link"]

    ShowCode --> StudentJoin["Student Enters Join Code or Clicks Deep Link"]
    StudentJoin --> FetchAssn["GET /api/assignment/student/id/6X9A21"]
    FetchAssn --> AttemptTimed["Student Solves Assignment Under Countdown Timer"]
    AttemptTimed --> SubmitAssn["POST /api/assignment/student/id/6X9A21/submit"]
    SubmitAssn --> ShowRank["Show Student Score & Live Classroom Rank"]

    ShowRank --> TeacherAnalytics["Parent / Teacher Views Classroom Analytics<br/>GET /api/assignment/student/id/6X9A21/analysis"]
    TeacherAnalytics --> RenderCharts["Render Class Average, Leaderboard & Question-Level Error Rates"]
```

---

## 9. Journey 9: AI Rank Predictor, College Cutoff Explorer & Physical OMR Grader

### 9.1. Flowchart
```mermaid
flowchart TD
    OpenTools["Open Exam Utilities (/student/tools)"] --> ToolChoice{"Choose Utility"}

    ToolChoice -- "Physical OMR Grader" --> UploadOMR["Upload Photo of Bubbled OMR Sheet + Select Template (JEE/NEET)"]
    UploadOMR --> CallOMR["POST /api/ai-hub/omr/evaluate"]
    CallOMR --> OMRResult["Show Detected Bubbles, Correct/Incorrect Count & Net Marks"]

    OMRResult --> PipeMarks["Pipe Raw Marks into AI Rank Predictor"]
    ToolChoice -- "Rank & College Predictor" --> PipeMarks

    PipeMarks --> CallPredict["POST /api/ai-hub/rank/predict<br/>{ exam, rawMarks, maxMarks, category, shiftDifficulty }"]
    CallPredict --> ShowAIR["Display Predicted Percentile, All India Rank (AIR), Category Rank & 2-Year Trend"]
    ShowAIR --> CheckColleges["GET /api/ai-hub/colleges/cutoffs?exam=...&category=...&studentAir={predictedAIR}"]
    CheckColleges --> RenderEligibility["Highlight Eligible IIT / NIT / AIIMS Branches in Green ('Eligible')"]
```

---

## 10. Journey 10: Parent Monitoring, Bilingual Daily Summaries & Subscription Checkout

### 10.1. Flowchart
```mermaid
flowchart TD
    ParentLogin["Parent Opens Dashboard (/parent/dashboard)"] --> FetchOverview["GET /api/hermes/parent/overview?child_id={cid}"]
    FetchOverview --> CheckFlags{"Any attention_flags?"}

    CheckFlags -- "concept_wall_active / streak_at_risk / inactive_48h" --> AlertCard["Render High-Priority Action Alert Card"]
    CheckFlags -- "None" --> GreenStatus["Render 'On Track' Consistency Card"]

    AlertCard --> GenSummary["POST /api/hermes/summary/generate/{cid}"]
    GreenStatus --> GenSummary
    GenSummary --> ReadSummary["GET /api/hermes/summary/{cid}?audience=parent<br/>(Rendered in Parent's Preferred Local Language)"]

    ReadSummary --> UpgradeCheck{"Unlock Unlimited Hermes Turns, Score Prediction & Weekly Reports?"}
    UpgradeCheck -- Yes --> FetchPlans["GET /api/payment/plans"]
    FetchPlans --> CreateOrder["POST /api/payment/create-order { parent_id, plan_id }"]
    CreateOrder --> RazorpayCheckout["Complete Razorpay / UPI Checkout"]
    RazorpayCheckout --> VerifyPay["POST /api/payment/verify -> Unlock Premium Entitlements"]
```
