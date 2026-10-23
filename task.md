# Task Breakdown & Checklist (`task.md`)
## eKlAVYA / Mentor AI — Complete React Website, Real Data & SuperAdmin

- [x] **Phase 1: Documentation & Planning**
  - [x] Write comprehensive architectural implementation plan in `plan.md`
  - [x] Write granular engineering checklist in `task.md`

- [x] **Phase 2: Backend Real Data Enrichment & SuperAdmin API (`Backend/`)**
  - [x] Enrich `Backend/data/pyq_and_colleges.json` with comprehensive JEE Main, JEE Advanced, and NEET-UG PYQs (Physics, Chemistry, Mathematics, Biology; MCQ & NAT), NCERT modules, and IIT/NIT/AIIMS college cutoffs
  - [x] Create `Backend/routers/superadmin_router.py` exposing `/api/superadmin/*` endpoints:
    - [x] `POST /api/superadmin/login` (SuperAdmin authentication)
    - [x] `GET /api/superadmin/overview` (Live platform telemetry, counts, revenue, active Concept Walls)
    - [x] `GET /api/superadmin/users`, `POST /api/superadmin/demo-session`, `POST /api/superadmin/users/action`
    - [x] `GET /api/superadmin/questions`, `POST /api/superadmin/questions`, `PUT /api/superadmin/questions/{question_id}`, `DELETE /api/superadmin/questions/{question_id}` (Live PYQ CRUD persisted to disk & memory)
    - [x] `GET /api/superadmin/flashcards`, `POST /api/superadmin/flashcards`, `DELETE /api/superadmin/flashcards/{card_id}` (Live RFC Flashcard CRUD)
    - [x] `GET /api/superadmin/colleges`, `PUT /api/superadmin/colleges/{college_id}` (College cutoff management)
    - [x] `GET /api/superadmin/assessments` (Platform-wide assessment monitoring)
    - [x] `GET /api/superadmin/system-config` & `PUT /api/superadmin/system-config` (AI mentor turn caps, mastery threshold, audit logs)
  - [x] Add resilient fallback / demo seeding in Hermes & Marks services so Student, Parent, and SuperAdmin flows work seamlessly with real data out-of-the-box
  - [x] Register `superadmin_router` and update CORS in `Backend/main.py`

- [x] **Phase 3: React Web Application Setup & Shared Components (`Frontend_Website/`)**
  - [x] Initialize React 19 + TypeScript + Vite + Tailwind CSS project in `Frontend_Website/` (configured on port `3000`)
  - [x] Install dependencies (`axios`, `lucide-react`, `katex`, `react-router-dom`)
  - [x] Build `LatexRenderer` component (`src/components/LatexRenderer.tsx`) for inline `$...$` and block `$$...$$` math + HTML rendering
  - [x] Build API client (`src/lib/api.ts`) & SSE stream reader (`src/lib/sse.ts`)
  - [x] Build `AuthContext` (`src/context/AuthContext.tsx`) supporting Student, Parent, and SuperAdmin sessions + 1-click Demo Role Switcher

- [x] **Phase 4: Public Landing, Authentication & 3-Step Onboarding**
  - [x] Build Interactive Landing Page (`/`) with live platform stats, feature showcase, and 1-click Demo Launchers (Student / Parent / SuperAdmin)
  - [x] Build Parent Login & Registration (`/login`, `/register`) wired to `/api/auth/login/email` and `/api/auth/register/simple`
  - [x] Build 3-Step Parent Onboarding Wizard (`/onboarding`) wired to `/api/onboarding/preferences`, `/api/onboarding/child`, `/api/onboarding/exams/available`, and `/api/onboarding/exam/select`
  - [x] Build Student Login (`/login`) wired to `/api/auth/login/child`

- [x] **Phase 5: Student Portal (`/student/*`)**
  - [x] **Home Dashboard (`/student/dashboard`)**: Exam countdown, Concept Wall alert banner, Daily Dose 5-Q Sprint modal, GitHub-style Monthly Heatmap, Daily Goal editor, Weekly League standings, Badges & AI Score Prediction
  - [x] **Hermes 1-to-1 Socratic AI Mentor (`/student/mentor`)**: Syllabus Micro-Topic state tree (`UNTOUCHED`, `LEARNING`, `MASTERED`, `WALL`), 11-language selector, Socratic Chat (`/api/hermes/chat`), Multi-Stage SSE Streaming Doubt Solver (`/api/ai-hub/chat/stream`), Snap & Solve Vision OCR (`/api/ai-hub/vision/ocr`), and Topic Mastery Quiz (`/api/hermes/quiz/attempt`)
  - [x] **Chapter-wise PYQ Bank & NEET NCERT Hub (`/student/pyq`)**: Multi-facet filter bar, NEET NCERT Line-by-Line modules tab, MCQ & Virtual Numeric Keypad (NAT) problem solver, Bookmark to Smart Notebook modal, and "Generate 3 Similar Questions" modal (`/api/ai-hub/qa/generate-similar-questions`)
  - [x] **Tests, Custom Test Generator & Fullscreen NTA CBT Interface (`/student/tests` & `/student/exam/:testId`)**: 2-Step CTG Wizard, Fullscreen NTA CBT Exam screen with 4-state palette & timer, Diagnostic Report Card & Topper Comparison (`/api/custom-test/analysis/{testId}`), and Homework Assignment code joiner (`/api/assignment/student/id/{code}`)
  - [x] **Revision Hub — Flashcards & Notebooks (`/student/revision`)**: 3D Flip Revision Flash Cards (`/api/rfc/*`), Custom Color-Coded Smart Notebooks (`/api/notebook/*`), and Automated Error Notebook (`/api/notebook/errors`)
  - [x] **Exam Utilities (`/student/tools`)**: AI Rank & Percentile Predictor (`/api/ai-hub/rank/predict`), IIT/NIT/AIIMS Cutoff Explorer (`/api/ai-hub/colleges/cutoffs`), and Physical OMR Sheet Grader (`/api/ai-hub/omr/evaluate`)

- [x] **Phase 6: Parent / Teacher Portal (`/parent/*`)**
  - [x] **Parent Command Center (`/parent/dashboard`)**: 7-day child overview, attention flags, syllabus mastery breakdown
  - [x] **Bilingual Daily & Weekly Reports (`/parent/reports`)**: Localized daily summary generator & voice reader (`/api/hermes/summary/*`) and 7-day weekly report (`/api/hermes/parent/weekly`)
  - [x] **Homework Assignment Builder & Classroom Analytics (`/parent/assignments`)**: PYQ picker, 6-char `joinCode` generator (`/api/assignment/teacher/create`), and classroom leaderboard & question error rate analytics (`/api/assignment/student/id/{code}/analysis`)
  - [x] **Subscription & Billing (`/parent/billing`)**: Subscription plans comparison (`/api/payment/plans`), Razorpay order checkout (`/api/payment/create-order`), and payment verification (`/api/payment/verify`)

- [x] **Phase 7: SuperAdmin Portal (`/superadmin/*` & `Super_Admin/`)**
  - [x] **Executive Overview**: Live KPIs, user/content counts, active Concept Walls, subscription metrics, and 1-click Demo Seed trigger
  - [x] **User & Role Administration**: Inspect/search Parents & Students, unlock/trigger Concept Walls, toggle Premium status, award XP, reset chat caps
  - [x] **PYQ Question Bank CMS**: Live CRUD table + form with KaTeX preview to add/edit/delete JEE & NEET PYQ questions
  - [x] **Flashcards & College Cutoffs CMS**: Add/delete RFC formula cards and edit IIT/NIT/AIIMS branch cutoffs
  - [x] **AI & Syllabus Governance**: Adjust daily AI turn caps & mastery thresholds, inspect SOUL prompt, and view audit logs
  - [x] Populate `Super_Admin/` directory with direct portal documentation

- [x] **Phase 8: Live Server Startup & End-to-End Verification**
  - [x] Start FastAPI backend on port `8000` and verify all endpoints including `/api/superadmin/*`
  - [x] Build & start React frontend on port `3000` and verify zero TypeScript/build errors
  - [x] Run end-to-end verification across Student, Parent, and SuperAdmin workflows
