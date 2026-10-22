# Updated Plan: AI Tutor Agent & Hermes Platform

**Date:** 2026-10-21 (Part B Hermes requirements added same day)
**Status:** Proposed — awaiting approval to start Phase 1
**Related docs:** `userflow.md`, `docs/design-doc.md`, `.kiro/specs/study-center-learning-journey/`

## Contents

- **Part A** — Friendly AI Tutor Agent (original short-term plan; §1–§9 below)
- **Part B** — Hermes Platform Requirements (full 27-requirement spec, appended)
- **Part C** — Reconciliation: stack divergence, requirement mapping, unified roadmap, open decisions

---

# Part A — Friendly AI Tutor Agent with Daily Summaries & Local Language

---

## 1. Objective

Build an AI tutor that acts as a **friendly, motivating mentor** for each student — it knows the student's real progress, encourages and nudges them, and produces a **daily summary in the student's local language** (student-facing + parent-facing versions).

This is a persona-driven LLM feature, **not** an autonomous agent framework. No LangChain/CrewAI. Four boring things done well: persona prompt + real data, cheap memory, a nightly batch job, and language done right.

## 2. Current State Assessment

| Area | Status | Location |
|---|---|---|
| Gemini client (sync/async/stream, retry, quota errors) | ✅ Ready | `utils/gemini_client.py` (`GeminiClient:153`) |
| AI tutor endpoints | ⚠️ **Stubbed** — `/tutor/ask` returns hardcoded mock text | `routers/ai_features_router.py:41` |
| Chat history endpoint | ⚠️ Stubbed — returns empty | `routers/ai_features_router.py:78` |
| Prompt/context infrastructure | ✅ Ready | `utils/analytics_context_builder.py`, `utils/analytics_prompt_templates.py` |
| Batch/scheduled generation | ✅ Ready | `services/gemini_scheduler_service.py`, `services/batch_queue_manager.py`, `services/gemini_batch_service.py` |
| Progress / streaks / gamification state | ✅ Ready | `services/progress_tracker.py`, `routers/gamification_router.py` |
| Language preference | ✅ Stored at onboarding | `POST /api/onboarding/preferences` → `language` |
| Material caching pattern (cache-first, 10 gen/hr/student) | ✅ Proven | `services/study_center_service.py` |
| Test path without live quota | ✅ Ready | `utils/mock_gemini_client.py` |
| Push notifications | ❌ Not implemented (design-doc only) | — |

Key implication: Phases 1–3 are **purely backend**. No frontend or infra changes are blockers.

## 3. Architecture

```
Student chat / Today screen / Parent dashboard
        │
        ▼
routers/ai_features_router.py          (real endpoints, replaces stubs)
        │
        ▼
services/tutor_agent_service.py        NEW — persona + context assembly + Gemini call
        │
        ├──► Context: today plan, streaks, weak topics, recent scores, exam countdown
        │      (reads progress_tracker, gamification, schedule, analytics)
        ├──► Memory: services/tutor_memory_service.py  NEW — rolling summary, not transcripts
        └──► Language: preferences.language → response_language
        │
Nightly: services/gemini_scheduler_service.py (batch_queue_manager)
        └──► One summary per active student → daily_summaries (idempotent)
```

## 4. Phased Implementation Plan

### Phase 1 — Real tutor chat (replace the stub)

1.1. `models/tutor_models.py` (new): `TutorChatRequest` {student_id, message, session_id?, response_language?}, `TutorChatResponse` {message_id, session_id, answer, key_points, examples, related_topics, practice_questions, resources}. Reuse `AITutorRequest/AITutorResponse` shape where possible — check `models/ai_models.py` first; extend rather than duplicate.

1.2. `services/tutor_agent_service.py` (new):
- Persona system prompt: friendly JEE/NEET mentor; encouraging but never shaming; scope-locked to study topics.
- `build_student_context(student_id)`: today's scheduled tasks, current streak, last N practice scores, weakest topics (from analytics), days-until-exam countdown.
- `chat(student_id, message, language)`: system prompt + context + recent session summary → `GeminiClient.generate_content_async`.

1.3. Rewrite `ask_ai_tutor` in `routers/ai_features_router.py:41` to call the service. Keep response schema backward-compatible.

1.4. Language: read `language` from preferences when `response_language` not passed; prompt instructs Gemini to reply **entirely in that language**, keeping technical terms bilingual (e.g., न्यूटन का प्रथम नियम (Newton's First Law)). Fallback: English.

**Acceptance:** real Gemini responses; tone safety checklist passes (see §6); bilingual terms present for non-English requests; mock client path works with `MOCK_GEMINI=true`.

### Phase 2 — Memory & persistence

2.1. Firestore collections:
- `tutor_sessions` — {session_id, student_id, started_at, language, message_count}
- `tutor_chat_history` — {session_id, student_id, role, content, tokens, created_at} (append-only)
- `tutor_memory` — {student_id, rolling_summary, struggling_with[], responds_well_to, updated_at}

2.2. `services/tutor_memory_service.py` (new):
- Append messages on each turn.
- When a session crosses ~10 turns (or ends), have Gemini compress the session into `tutor_memory.rolling_summary` — the prompt carries the summary, not transcripts.

2.3. Implement `GET /tutor/history/{student_id}` (`routers/ai_features_router.py:78`) against `tutor_chat_history`; add `DELETE` semantics later if privacy policy requires.

**Acceptance:** tutor references yesterday's struggle in today's chat; prompt token cost stays flat as history grows.

### Phase 3 — Daily summary (nightly batch)

3.1. `services/tutor_summary_service.py` (new): `generate_daily_summary(student_id)` — one Gemini call producing **two versions**:
- `student_version`: motivational, in local language — what they did today, streak, tomorrow's first task, one specific encouragement.
- `parent_version`: factual — study minutes, topics completed, test scores, syllabus coverage delta, areas needing attention.

3.2. Scheduler: register a nightly job (e.g., 21:00 local) in `services/gemini_scheduler_service.py` iterating active students via `batch_queue_manager.py` (parallelism + failure isolation already there).

3.3. Firestore `daily_summaries`: doc id = `{student_id}_{yyyy-mm-dd}` → **idempotent**; rerun-safe; store tokens_used.

3.4. Endpoints:
- `GET /api/ai/tutor/daily-summary/{student_id}?date=` — student version
- `GET /api/parent/daily-summary/{child_id}?date=` — parent version (add to `parent_dashboard_router.py`)

3.5. Cache-first + cost controls: skip generation if the student had zero activity that day (serve "quiet day" template without a Gemini call); cap output tokens; honor the 10 generations/student/hour pattern from Study Center.

**Acceptance:** summaries present for all active students each morning; duplicate runs don't duplicate docs; zero-activity students cost 0 tokens.

### Phase 4 (later) — Proactive nudges & parent letter

- FCM push (design-doc dependency — needs Firebase Cloud Messaging setup): streak-at-risk alert, "first task of the day" nudge.
- Weekly parent "mentor letter": deeper Gemini reflection on the week, generated in the parent's language, added to `parent_dashboard_router` reports.
- Exam-countdown milestones (30/7/1 days): special motivational summaries.

## 5. API Surface Changes

| Endpoint | Change |
|---|---|
| `POST /api/ai/tutor/ask` | **Behavior change** — real Gemini, accepts `response_language` |
| `GET /api/ai/tutor/history/{student_id}` | **Implement** — real data |
| `GET /api/ai/tutor/daily-summary/{student_id}` | New |
| `GET /api/parent/daily-summary/{child_id}` | New |
| `POST /api/onboarding/preferences` | Unchanged; `language` is the source of truth (optionally add child-level override later) |

Auth: all student endpoints use `get_current_user` (child token); parent endpoints use parent token + ownership check (existing convention in `middleware/auth_middleware.py`).

## 6. Guardrails (decided up front — minors + cost)

**Safety/tone**
- System prompt: encouraging tone, never shame-based motivation; no comparing to other students.
- Output validation layer: reject responses containing demeaning/pressuring language before persisting (simple keyword + classifier check; log violations).
- Scope lock: off-topic or "give me the answer" requests get a redirect response ("let's work through it together"), per persona config.
- All chats with minors are logged; define retention in privacy policy.

**Cost**
- Batch summaries off-peak; skip quiet days (template, no LLM call).
- Rolling memory keeps chat prompts small and flat.
- Per-student generation caps (reuse Study Center's 10/hour pattern).
- Token logging on every call (pattern exists in study center material cache).

**Reliability**
- Gemini failures: retry via existing `retry_with_backoff`; degrade to cached/last-good summary rather than 500.
- Language fallback: if detected output language ≠ requested, regenerate once in English, flag for review.

## 7. Testing Strategy

- Use `utils/mock_gemini_client.py` for unit/integration tests; add tutor cases to `tests/` (existing pytest setup).
- New tests: `tests/test_tutor_agent.py` (persona + context assembly), `tests/test_tutor_memory.py` (rolling summary), `tests/test_daily_summary.py` (idempotency, dual versions, quiet-day skip), tone-safety regression cases.
- Manual QA with Hindi/Marathi/English profiles; verify bilingual technical terms.

## 8. Rollout & Success Metrics

1. Merge Phase 1 behind the existing endpoint (no frontend flag needed — schema unchanged).
2. Phase 2 + 3 together; monitor nightly job via `logs/` and `batch_monitor_service.py`.
3. Metrics: daily summary generation success rate, tokens/student/day, tutor chat turns/student/week, streak retention uplift vs. pre-tutor cohort, parent report open rate.

## 9. Out of Scope (for now)

- Voice tutor / TTS (design-doc mentions Google TTS — separate track)
- WhatsApp/SMS delivery of summaries
- Multi-agent setups or tool-calling frameworks
- Real-time streaming chat UI work (backend streaming exists in `GeminiClient`, frontend wiring is a separate task)

---

# Part B — Hermes Platform Requirements

> Source-of-truth spec as provided 2026-10-21. Hermes is an autonomous, voice-enabled AI coaching platform for JEE aspirants in India.

## Introduction

Hermes is an autonomous, voice-enabled AI coaching platform for JEE (Joint Entrance Examination) aspirants in India. The system provides each student with a dedicated 1-to-1 AI mentor agent capable of resolving doubts via voice input, rendering visual solutions on a whiteboard canvas, tracking syllabus progress deterministically, and keeping parents informed through a localized portal. The platform is designed to achieve 90%+ gross profit margins by combining semantic caching, prompt caching, and a strict rate-limiting strategy on expensive API calls. An autonomous AI Calling Agent — built on Vobiz telephony, Sarvam AI speech, and OpenRouter LLMs — places scheduled outbound calls to students and parents to deliver spoken feedback and listen to parent concerns, and answers inbound calls from parents. All syllabus coverage is strictly scoped to each student's selected exams, which now include CBSE Class 11 and Class 12 board examinations alongside JEE.

## Glossary

- **Hermes Agent**: The isolated AI mentor instance provisioned for each student, powered by DeepSeek V4-Flash.
- **Student**: A JEE aspirant (Grade 11, Grade 12, or Dropper) who is the primary user of the platform.
- **Parent**: The purchaser/guardian who monitors student progress via a separate portal.
- **Session ID**: A unique identifier linking a student to their dedicated Hermes Agent and memory database.
- **SOUL Prompt**: A strict system prompt that constrains the AI to behave as a Socratic mentor (hints and formulas) rather than an answer engine (raw solutions).
- **Micro-Topic**: An atomic unit of the JEE syllabus (e.g., "Projectile Motion — Range Formula Derivation"), one of 1,500+ stored in PostgreSQL.
- **Micro-State**: The progression status of a Micro-Topic: UNTOUCHED → LEARNING → MASTERED.
- **STT**: Speech-to-Text, handled by Sarvam AI Saaras V3.
- **TTS**: Text-to-Speech, handled by Sarvam AI Bulbul V2.
- **Excalidraw JSON**: A structured JSON array describing vector elements (diagrams, graphs, FBDs) rendered client-side by the Excalidraw React component.
- **Semantic Cache**: A pgvector-backed PostgreSQL store that matches incoming doubts to previously solved ones to avoid redundant API calls.
- **Concept Wall**: A hard progression lock triggered when a student fails the same topic 3 times, requiring mandatory revision before proceeding.
- **Ghosting Protocol**: An automated parent notification triggered when a student is inactive for 48 hours.
- **OTP Login**: One-time password authentication via Indian mobile number, used by both students and parents.
- **Razorpay/UPI**: Indian payment gateways used for subscription billing.
- **pgvector**: A PostgreSQL extension enabling vector similarity search for semantic caching.
- **OpenRouter**: API gateway used to access DeepSeek V4-Flash with prompt-caching headers.
- **n8n**: A workflow automation tool used for scheduling daily cron orchestration jobs.
- **PWA**: Progressive Web App, the Next.js-based web client for Hermes.
- **Hinglish**: A code-mixed language combining Hindi and English, natively supported by Sarvam AI.
- **Mind Map**: A hierarchical visual diagram representing relationships between Micro-Topics, subjects, and concepts, rendered client-side.
- **AI Podcast**: A synthesized multi-voice audio episode (10–20 minutes) covering a JEE chapter or topic cluster, generated by Hermes and delivered to the student.
- **Generated Content Store**: A PostgreSQL table storing all AI-generated artifacts (Excalidraw JSON, TTS audio URLs, podcast episodes, mind map JSON) keyed by a content hash for reuse.
- **Excalidraw Vision Check**: A server-side pipeline that renders Excalidraw JSON to a PNG image and submits it to DeepSeek Vision to verify diagram correctness before delivery to the student.
- **Vobiz**: Cloud telephony API used to place and receive AI-driven phone calls on Indian mobile numbers.
- **AI Calling Agent**: An autonomous voice agent that places outbound calls to students and parents and answers inbound parent calls, conversing via Sarvam Saaras STT, an OpenRouter LLM, and Sarvam Bulbul TTS in a real-time loop.
- **Parent Feedback Call**: A scheduled outbound call in which the AI Calling Agent delivers a spoken progress summary in the parent's native language and records the parent's spoken concerns.
- **Exam Scope**: The union of Micro-Topics tagged to the examinations a student has selected (JEE Main, JEE Advanced, CBSE Class 11, CBSE Class 12); the only material the Hermes Agent may teach.
- **CBSE**: Central Board of Secondary Education — Class 11 and Class 12 board examinations supported alongside JEE, with NCERT-mapped Micro-Topics.

## Requirements

### Requirement 1: Isolated Student Agent Provisioning

**User Story:** As a student, I want a dedicated AI mentor that knows only my history and progress, so that my learning experience is private and personalized.

1. WHEN a new student completes registration, THE Hermes Platform SHALL provision a unique Session ID and an isolated memory database record scoped exclusively to that student.
2. WHILE a student session is active, THE Hermes Agent SHALL load only the memory and progress data associated with that student's Session ID.
3. IF two students submit identical doubts, THEN THE Hermes Platform SHALL resolve each doubt within the context of the respective student's individual session without sharing session state.
4. THE Hermes Platform SHALL enforce data isolation such that no student can access or influence the session data of another student.

### Requirement 2: Persistent Micro-Topic Memory

**User Story:** As a student, I want the AI to remember which topics I struggle with across sessions, so that it can proactively help me address my weak areas over my 2-year preparation cycle.

1. THE Hermes Agent SHALL maintain a persistent record of each Micro-Topic's Micro-State (UNTOUCHED, LEARNING, or MASTERED) for every student across sessions.
2. WHEN a student completes a quiz attempt on a Micro-Topic, THE Hermes Platform SHALL update that Micro-Topic's Micro-State based on the quiz performance result.
3. WHILE a student's Micro-Topic is in the LEARNING state, THE Hermes Agent SHALL prioritize related doubts and practice problems for that topic in session recommendations.
4. THE Hermes Platform SHALL persist Micro-State data in PostgreSQL and retain it for the full duration of the student's active subscription.

### Requirement 3: SOUL Prompt — Mentor Behavior Enforcement

**User Story:** As a student, I want the AI to guide me with hints rather than just give me answers, so that I actually develop problem-solving skills instead of becoming dependent on the AI.

1. THE Hermes Agent SHALL apply the SOUL Prompt as a non-overridable system instruction on every DeepSeek API call.
2. WHEN a student requests a direct answer to a numerical problem, THE Hermes Agent SHALL respond with a targeted hint, the relevant formula, or a guiding question instead of the complete solution.
3. IF a student's message attempts to instruct the agent to ignore the SOUL Prompt or adopt a different persona, THEN THE Hermes Agent SHALL disregard the instruction and respond with a mentor-appropriate clarification.
4. THE Hermes Agent SHALL structure its Excalidraw JSON output to illustrate concepts and intermediate steps rather than final answer diagrams.

### Requirement 4: Voice Doubt Intake (STT)

**User Story:** As a student, I want to record my doubt in Hindi or English, so that I can ask questions naturally without typing complex equations.

1. WHEN a student submits a voice recording of up to 45 seconds, THE Hermes Platform SHALL transcribe the audio using Sarvam Saaras V3 STT within 10 seconds of submission.
2. THE Hermes Platform SHALL accept voice input in Hinglish (Hindi-English code-mixed speech) and produce an accurate text transcription.
3. WHILE a student's daily voice quota (maximum 7 queries) is not exhausted, THE Hermes Platform SHALL process voice submissions and decrement the remaining quota count.
4. WHEN a student's daily voice quota reaches zero, THE Hermes Platform SHALL automatically switch the interaction mode to Text and Whiteboard Mode and notify the student of the switch.
5. IF the STT service returns an error or the audio is unintelligible, THEN THE Hermes Platform SHALL prompt the student to re-record or switch to text input.

### Requirement 5: Visual Whiteboard Output (Excalidraw)

**User Story:** As a student, I want to see diagrams and step-by-step visuals for my doubts, so that I can understand complex physics and math problems more intuitively.

1. WHEN THE Hermes Agent generates a response to a doubt, THE Hermes Platform SHALL include an Excalidraw JSON array representing the relevant diagram, graph, or free-body diagram.
2. THE Hermes Platform SHALL render the Excalidraw JSON client-side using the Excalidraw React component without server-side image generation.
3. THE Hermes Agent SHALL produce Excalidraw JSON with valid coordinates and element types such that the rendered output is visually coherent and correctly labeled.
4. WHILE the student views the whiteboard, THE Hermes Platform SHALL allow the student to pan and zoom the Excalidraw canvas without altering the AI-generated content.

### Requirement 6: Audio Hint Output (TTS)

**User Story:** As a student, I want to hear a short verbal explanation of the concept, so that I can quickly grasp the key idea without reading a long text response.

1. WHEN THE Hermes Agent generates a doubt response, THE Hermes Platform SHALL synthesize a 10–15 second conceptual audio hint using Sarvam Bulbul V2 TTS.
2. THE Hermes Platform SHALL deliver the TTS audio asynchronously so that the Excalidraw canvas renders before or simultaneously with audio playback.
3. THE Hermes Platform SHALL generate TTS audio in Hinglish to match the student's preferred communication style.
4. IF the TTS service fails to generate audio within 8 seconds, THEN THE Hermes Platform SHALL display the text response alone and log the TTS failure for monitoring.

### Requirement 7: Semantic Cache for Cost Optimization

**User Story:** As a platform operator, I want repeated or similar doubts to be served from cache, so that API costs remain within the ₹90–₹120 per user per month budget.

1. BEFORE invoking the DeepSeek or Sarvam APIs, THE Hermes Platform SHALL query the pgvector semantic cache using a vector similarity search on the incoming doubt.
2. WHEN the semantic cache returns a match with a similarity score above the configured threshold, THE Hermes Platform SHALL serve the cached Excalidraw JSON and audio response without calling external APIs.
3. WHEN the semantic cache does not return a qualifying match, THE Hermes Platform SHALL call the DeepSeek and Sarvam APIs, then store the new response in the semantic cache for future use.
4. THE Hermes Platform SHALL achieve a semantic cache hit rate of 60% or higher by the end of Month 6 of production operation.
5. THE Hermes Platform SHALL use OpenRouter prompt-caching headers on all DeepSeek API calls to minimize token billing costs.

### Requirement 8: Deterministic Syllabus State Machine

**User Story:** As a student, I want my syllabus progress to be tracked accurately based on what I actually know, so that my study plan reflects my real preparation level.

1. THE Hermes Platform SHALL store a hardcoded list of 1,500 or more Micro-Topics across the JEE and CBSE syllabi in PostgreSQL, each tagged with its applicable exams (exam_codes) and NCERT chapter mapping where relevant, independent of LLM memory.
2. WHEN a student completes a quiz on a Micro-Topic and scores below the mastery threshold, THE Hermes Platform SHALL set that Micro-Topic's Micro-State to LEARNING.
3. WHEN a student completes a quiz on a Micro-Topic and scores at or above the mastery threshold on two consecutive attempts, THE Hermes Platform SHALL set that Micro-Topic's Micro-State to MASTERED.
4. THE Hermes Platform SHALL calculate a student's overall syllabus completion percentage from the ratio of MASTERED Micro-Topics to the total Micro-Topic count.

### Requirement 9: Concept Wall — Progression Lock

**User Story:** As a student, I want the platform to intervene when I keep failing the same topic, so that I am forced to revise it properly before moving on.

1. WHEN a student fails the same Micro-Topic on 3 consecutive quiz attempts, THE Hermes Platform SHALL activate the Concept Wall for that Micro-Topic and lock further syllabus progression.
2. WHILE the Concept Wall is active for a Micro-Topic, THE Hermes Platform SHALL present the student with a mandatory interactive Excalidraw revision session for that topic before allowing progression.
3. WHEN the student successfully completes the mandatory Excalidraw revision session and passes a follow-up quiz, THE Hermes Platform SHALL deactivate the Concept Wall and restore syllabus progression.

### Requirement 10: Daily Autonomous Orchestration (Cron Jobs)

**User Story:** As a student, I want the platform to automatically update my daily targets and study schedule, so that I stay on track without needing to manage my own plan.

1. THE Hermes Platform SHALL execute a daily cron job at 6:00 AM IST to push personalized study targets to each active student.
2. THE Hermes Platform SHALL execute a daily cron job at 8:00 PM IST to audit each student's progress and recalculate the dynamic study schedule for the following day.
3. IF a student has had no platform activity for 48 consecutive hours, THEN THE Hermes Platform SHALL trigger the Ghosting Protocol by sending a WhatsApp notification to the student's registered parent contact.

### Requirement 11: Parent Portal — OTP Login

**User Story:** As a parent, I want to log in quickly using my mobile number, so that I can check my child's progress without creating or remembering a password.

1. WHEN a parent enters their registered Indian mobile number on the login screen, THE Hermes Platform SHALL send a one-time password (OTP) to that number via SMS within 30 seconds.
2. WHEN the parent submits the correct OTP within 5 minutes of issuance, THE Hermes Platform SHALL grant access to the parent portal scoped to their linked student's data.
3. IF the parent submits an incorrect OTP 3 times, THEN THE Hermes Platform SHALL lock the OTP session and require the parent to request a new OTP.

### Requirement 12: Parent Portal — Localized Progress Summaries

**User Story:** As a parent, I want to receive my child's progress report in my native language, so that I can understand their preparation status without needing English or technical knowledge.

1. THE Hermes Platform SHALL generate weekly progress summaries for each student translated into the parent's selected native language (Hindi, Marathi, or Telugu) using DeepSeek.
2. THE Hermes Platform SHALL synthesize a voice-note version of the weekly progress summary using Sarvam Bulbul V2 TTS in the parent's selected language.
3. THE Hermes Platform SHALL deliver the weekly progress summary and voice note to the parent via WhatsApp and within the parent portal.
4. WHERE a parent has opted into mental health updates, THE Hermes Platform SHALL include a student well-being indicator derived from activity patterns in the weekly summary.

### Requirement 13: Subscription Billing via Razorpay/UPI

**User Story:** As a parent, I want to pay the monthly subscription easily using UPI or a standard Indian payment method, so that managing billing is frictionless.

1. THE Hermes Platform SHALL present a 1-click payment flow integrated with Razorpay supporting UPI, debit card, and net banking payment methods for the ₹1,500 monthly subscription.
2. WHEN a payment is successfully processed, THE Hermes Platform SHALL activate or extend the student's subscription and issue a digital invoice within 60 seconds.
3. WHEN a subscription payment fails or is not renewed within 3 days of the due date, THE Hermes Platform SHALL restrict the student's access to AI doubt resolution while retaining their progress data.
4. IF a subscription is cancelled, THEN THE Hermes Platform SHALL retain the student's Micro-State and session data for 90 days before permanent deletion.

### Requirement 14: Student & Parent Authentication

**User Story:** As a student or parent, I want to securely log in using my Indian mobile number, so that account access is simple and does not require remembering passwords.

1. WHEN a new user registers with an Indian mobile number, THE Hermes Platform SHALL verify the number via OTP before creating the account.
2. THE Hermes Platform SHALL maintain separate authenticated sessions for students and parents, each scoped to their respective portal and data access permissions.
3. IF an authenticated session is idle for 30 minutes, THEN THE Hermes Platform SHALL invalidate the session token and require re-authentication.

### Requirement 15: Excalidraw Vision Quality Check

**User Story:** As a student, I want every diagram I receive to be visually accurate and correct, so that I am not misled by a poorly generated figure.

1. WHEN THE Hermes Agent generates an Excalidraw JSON response, THE Hermes Platform SHALL render the JSON to a PNG image server-side and submit it to the DeepSeek Vision model for a correctness check before delivering the diagram to the student.
2. WHEN the DeepSeek Vision model identifies an error or incoherence in the rendered diagram, THE Hermes Platform SHALL regenerate the Excalidraw JSON up to 2 additional times until the vision check passes.
3. IF the Excalidraw JSON fails the vision check after 3 attempts, THEN THE Hermes Platform SHALL deliver the best available diagram with a visible warning label and log the failure for review.
4. THE Hermes Platform SHALL store the vision-verified Excalidraw JSON and its rendered PNG in the Generated Content Store for reuse in future matching doubts.

### Requirement 16: Generated Content Store (Reuse All Artifacts)

**User Story:** As a platform operator, I want all AI-generated content to be stored and reused, so that compute costs drop as the content library grows.

1. THE Hermes Platform SHALL store every generated artifact — including Excalidraw JSON, TTS audio file URLs, podcast episode URLs, and mind map JSON — in the Generated Content Store keyed by a deterministic content hash derived from the input parameters.
2. BEFORE generating any artifact, THE Hermes Platform SHALL query the Generated Content Store for an existing entry matching the content hash and serve it directly if found.
3. WHEN a new artifact is generated and passes quality checks, THE Hermes Platform SHALL write the artifact and its metadata (type, topic, creation timestamp, usage count) to the Generated Content Store.
4. THE Hermes Platform SHALL increment the usage count of a Generated Content Store entry each time it is served to a student, enabling popularity-based prioritization.

### Requirement 17: AI-Generated Topic Mind Maps

**User Story:** As a student, I want to see a visual mind map of a JEE chapter, so that I can understand how all the sub-topics connect before diving into details.

1. WHEN a student requests a mind map for a JEE chapter or Micro-Topic cluster, THE Hermes Platform SHALL generate a hierarchical mind map JSON using DeepSeek and render it client-side as an interactive Excalidraw diagram.
2. THE Hermes Platform SHALL apply the Excalidraw Vision Check to every generated mind map before delivering it to the student.
3. THE Hermes Platform SHALL store generated mind maps in the Generated Content Store and serve cached versions for subsequent requests on the same topic.
4. WHILE viewing a mind map, THE Hermes Platform SHALL allow the student to tap any node to launch a targeted doubt session for that Micro-Topic within the Hermes Agent.

### Requirement 18: AI-Generated Chapter Podcasts

**User Story:** As a student, I want to listen to an AI-generated podcast episode on a JEE chapter while commuting, so that I can learn passively without screen time.

1. WHEN a student requests a podcast for a JEE chapter, THE Hermes Platform SHALL generate a 10–20 minute multi-voice audio episode using DeepSeek for the script and Sarvam Bulbul V2 TTS for voice synthesis, in Hinglish.
2. THE Hermes Platform SHALL store the generated podcast episode in the Generated Content Store and serve the cached audio URL for all subsequent requests on the same chapter.
3. THE Hermes Platform SHALL present podcast episodes within a dedicated in-app player with playback controls (play, pause, seek, 15-second skip).
4. WHEN a student listens to a podcast episode, THE Hermes Platform SHALL log the episode as a study activity and credit the relevant Micro-Topics as LEARNING state if they were previously UNTOUCHED.
5. THE Hermes Platform SHALL limit podcast generation to a maximum of 2 new episodes per student per day to manage TTS API costs.

### Requirement 19: Internet Research Mode

**User Story:** As a student, I want the AI mentor to fetch up-to-date reference material or solved examples from the web when needed, so that my doubt resolution is grounded in the latest resources.

1. WHEN the Hermes Agent determines that a doubt requires external reference material not available in its training context, THE Hermes Platform SHALL perform a targeted web search and incorporate the retrieved content into the DeepSeek reasoning context.
2. THE Hermes Platform SHALL cite the source URL for any web-retrieved content included in the student's response.
3. THE Hermes Platform SHALL sanitize all web-retrieved content to remove advertisements, irrelevant HTML, and non-educational material before passing it to the DeepSeek model.
4. THE Hermes Platform SHALL rate-limit internet research calls to a maximum of 3 searches per doubt session per student to control latency and costs.
5. IF the web search returns no relevant results, THEN THE Hermes Platform SHALL resolve the doubt using the Hermes Agent's internal knowledge and indicate to the student that no external sources were found.

### Requirement 20: Parent Analytics Dashboard

**User Story:** As a parent, I want a detailed visual dashboard showing my child's progress, study habits, and performance trends, so that I can make informed decisions about their preparation.

1. THE Hermes Platform SHALL provide a parent-facing analytics dashboard displaying the student's Micro-Topic Micro-State distribution (UNTOUCHED, LEARNING, MASTERED) as a subject-wise breakdown chart.
2. THE Hermes Platform SHALL display a 30-day study activity heatmap showing daily session counts, voice query usage, and time-on-platform for the linked student.
3. THE Hermes Platform SHALL display a performance trend graph showing quiz accuracy per subject (Physics, Chemistry, Mathematics) over the past 30 days.
4. WHEN the student's performance in any subject drops by 15% or more over a 7-day window, THE Hermes Platform SHALL highlight the decline with a visual alert on the parent dashboard.
5. THE Hermes Platform SHALL present all dashboard data in the parent's selected native language (Hindi, Marathi, or Telugu).

### Requirement 21: Gamification — XP, Streaks, and Badges

**User Story:** As a student, I want to earn points and badges for studying consistently, so that I stay motivated during the long JEE preparation journey.

1. THE Hermes Platform SHALL award Experience Points (XP) to students for completing quiz attempts, resolving doubts, maintaining daily streaks, and finishing podcast episodes, with XP values defined per activity type.
2. WHEN a student completes platform activity on consecutive calendar days, THE Hermes Platform SHALL maintain and display a daily streak counter, and reset it to zero if a day is missed.
3. THE Hermes Platform SHALL award milestone badges to students upon reaching defined thresholds such as first MASTERED topic, 7-day streak, 50 doubts resolved, and full chapter mind map explored.
4. THE Hermes Platform SHALL display the student's current XP total, streak count, and earned badges on the student home screen.
5. WHEN a student earns a new badge, THE Hermes Platform SHALL display an in-app animation and send a WhatsApp notification to the student's parent.

### Requirement 22: Group Study Rooms with Chat

**User Story:** As a student, I want to study with peers in a shared session, so that I can collaborate on problems and stay accountable.

1. THE Hermes Platform SHALL allow a student to create a Group Study Room and invite up to 5 other registered students via a shareable room code.
2. WHILE a Group Study Room session is active, THE Hermes Platform SHALL provide a real-time text chat channel accessible to all room members.
3. WHILE a Group Study Room session is active, THE Hermes Platform SHALL allow any room member to submit a doubt to a shared Hermes Agent instance and display the Excalidraw and audio response to all room members simultaneously.
4. THE Hermes Platform SHALL deduct voice query quota from the student who submits the voice doubt in a group session, not from all participants.
5. IF a room member sends a message containing abusive or inappropriate content, THEN THE Hermes Platform SHALL filter the message and issue a warning to that member.
6. THE Hermes Platform SHALL cap Group Study Room sessions at 120 minutes per session to manage compute resource usage.

### Requirement 23: JEE Score Predictor

**User Story:** As a student, I want to see a predicted JEE score range based on my current preparation level, so that I can benchmark my readiness and adjust my study plan.

1. THE Hermes Platform SHALL compute a predicted JEE Main score range for the student based on the ratio of MASTERED to total Micro-Topics, weighted by topic frequency in past JEE papers, and display the prediction on the student dashboard.
2. THE Hermes Platform SHALL refresh the score prediction after every 5 quiz completions or on a daily basis, whichever occurs first.
3. THE Hermes Platform SHALL present the score prediction as a range (e.g., 180–210 out of 300) with a subject-wise breakdown showing predicted marks in Physics, Chemistry, and Mathematics.
4. WHERE a student has completed a full-length mock test, THE Hermes Platform SHALL incorporate the mock test score as a weighted data point in the score prediction model.
5. THE Hermes Platform SHALL display a historical graph of the student's predicted score trajectory over the past 60 days to show improvement trends.

### Requirement 24: AI Calling Agent — Student Check-in Calls

**User Story:** As a student, I want my AI mentor to call me on my phone to review my progress and keep me on track, so that I feel guided even when I am not using the app.

1. WHEN a scheduled check-in time arrives, THE Hermes Platform SHALL place an outbound call to the student's registered mobile number via Vobiz.
2. DURING the call, THE AI Calling Agent SHALL converse in the student's preferred language (Hindi, Hinglish, or English) using Sarvam Saaras V3 STT for listening, an OpenRouter LLM for reasoning, and Sarvam Bulbul V2 TTS for speaking.
3. THE AI Calling Agent SHALL deliver a spoken summary of the student's weekly progress, Concept Wall status, and upcoming daily targets, and SHALL answer syllabus-scoped questions asked by the student during the call.
4. THE Hermes Platform SHALL record the call transcript and a structured call summary (topics discussed, commitments made, sentiment) in PostgreSQL, scoped to the student's Session ID.
5. IF the student does not answer, THEN THE Hermes Platform SHALL retry the call once after 2 hours and fall back to a WhatsApp summary if the retry is unanswered.
6. THE Hermes Platform SHALL place calls only within the consent window configured at onboarding (default 9:00 AM – 8:00 PM IST) and SHALL honor a student or parent opt-out request immediately and permanently.

### Requirement 25: AI Calling Agent — Parent Feedback and Listening Calls

**User Story:** As a parent, I want the platform to call me with my child's progress and listen to my concerns in my own language, so that I stay involved in their preparation without needing to use the app.

1. THE Hermes Platform SHALL place a weekly outbound call to the parent's registered mobile number via Vobiz at a parent-selected time slot.
2. DURING the parent call, THE AI Calling Agent SHALL deliver a spoken progress summary in the parent's selected native language (Hindi, Marathi, or Telugu), covering syllabus completion, recent quiz performance, and well-being indicators where opted in.
3. AFTER delivering the summary, THE AI Calling Agent SHALL invite and record the parent's spoken feedback, concerns, and requests, transcribing them via Sarvam Saaras V3.
4. WHEN a parent raises an actionable concern (e.g., "reduce study load", "focus more on Chemistry"), THEN THE Hermes Platform SHALL store it in a parent_feedback table, flag it for the student's study schedule recalculation, and display its status in the parent portal.
5. THE Hermes Platform SHALL support inbound calls: WHEN a parent calls the platform's Vobiz number, THE AI Calling Agent SHALL authenticate the caller via the registered caller ID, answer questions about the linked student's progress, and listen to feedback.
6. THE Hermes Platform SHALL enforce a maximum call duration of 10 minutes per call and rate-limit outbound calls to 2 per recipient per day.

### Requirement 26: Exam-Scoped Syllabus Restriction

**User Story:** As a student, I want the mentor to teach only what my selected exams require, so that no study time is wasted on out-of-syllabus material.

1. WHEN a student selects target examinations during onboarding (one or more of JEE Main, JEE Advanced, CBSE Class 11, CBSE Class 12), THE Hermes Platform SHALL compute the student's Exam Scope as the union of Micro-Topics tagged to those exams.
2. THE Hermes Agent SHALL answer doubts, generate mind maps, podcasts, quizzes, and call scripts strictly within the student's Exam Scope.
3. WHEN a student asks a question outside their Exam Scope, THEN THE Hermes Agent SHALL politely decline, explain that the topic is outside the selected exam syllabus, and redirect the student to a relevant in-scope topic.
4. THE Hermes Platform SHALL include only in-scope Micro-Topics when computing syllabus completion percentage, daily targets, and score predictions.
5. WHEN a student adds or removes an exam selection, THEN THE Hermes Platform SHALL recompute the Exam Scope while preserving existing Micro-State records for topics that remain in scope.

### Requirement 27: CBSE Exam Support

**User Story:** As a Class 11 or 12 student, I want to prepare for my CBSE board exams alongside JEE on the same platform, so that both exams are covered in one place.

1. THE Hermes Platform SHALL store CBSE Class 11 and Class 12 Micro-Topics for Physics, Chemistry, Mathematics, and Biology, each tagged with its exam code (cbse_11, cbse_12) and NCERT chapter mapping.
2. WHERE a student's Exam Scope includes a CBSE exam, WHEN the student explicitly requests a board-style answer, THE Hermes Agent SHALL provide NCERT-derived definitions, derivations, and marking-scheme-structured answers as a scoped exception to the hint-first SOUL Prompt behavior.
3. THE Hermes Platform SHALL provide CBSE-mode quizzes with both subjective and objective question types aligned to the CBSE marking scheme.
4. THE Hermes Platform SHALL compute a separate CBSE board readiness percentage alongside the JEE score prediction for students with CBSE in their Exam Scope.
5. THE AI Calling Agent SHALL include CBSE preparation status in student check-in calls and parent feedback calls for students with CBSE in their Exam Scope.

---

# Part C — Reconciliation & Unified Roadmap

## C.1 Stack divergence (decision point)

The Hermes spec implies a **platform pivot** from the current Mentor AI stack. This is the single biggest decision before any build work:

| Layer | Mentor AI (current codebase) | Hermes (spec) |
|---|---|---|
| LLM | Gemini API (`utils/gemini_client.py`) | DeepSeek V4-Flash via OpenRouter + prompt-caching headers |
| Database | Firebase Firestore | PostgreSQL + pgvector |
| Speech | — (design-doc TTS only) | Sarvam AI: Saaras V3 STT, Bulbul V2 TTS (Hinglish-native) |
| Telephony | — | Vobiz (outbound + inbound AI calls) |
| Orchestration | `gemini_scheduler_service.py` / `batch_queue_manager.py` | n8n cron (6:00 AM / 8:00 PM IST) |
| Auth | JWT, email + child username/password | OTP over Indian mobile (students + parents) |
| Caching | `query_cache_service.py`, Study Center material cache | pgvector semantic cache + Generated Content Store (content-hash keyed) + OpenRouter prompt caching |
| Diagrams | — | Excalidraw JSON (client-rendered) + DeepSeek Vision server-side check |
| Messaging | — (design-doc FCM only) | WhatsApp (Ghosting Protocol, weekly summaries, badge alerts) |
| Frontend | Next.js | Next.js PWA + Excalidraw component |

**Option A — Greenfield Hermes backend** (recommended if Hermes is the go-forward product): new FastAPI (or other) service on Postgres/pgvector; Mentor AI codebase stays as-is for reference. The existing repo's value is its syllabus data (`data/syllabus/`, `data/exam_patterns/`), question-generation/validation logic (`question_generator.py`, `question_validator.py`, `test_pattern_service.py`), and cost-control patterns — all portable.

**Option B — Evolve Mentor AI in place**: keep Firestore/Gemini and bolt Hermes features on. Not recommended — Req 2/7/8 (Postgres-persisted Micro-State, pgvector semantic cache) and the cost model in Req 7 don't map cleanly onto Firestore, and you'd maintain two mental models of "progress."

## C.2 Requirement mapping — what we already have vs. net-new

**Covered by existing codebase / Part A plan (reuse or adapt):**

| Hermes Req | Existing anchor |
|---|---|
| Req 1 (isolated agent + Session ID) | Part A Phase 1–2 (session-scoped tutor + Firestore/Postgres memory) |
| Req 2/8 (Micro-Topic memory + deterministic state machine) | `syllabus_coverage_tracker.py`, `progress_tracker.py` — but must be re-grounded in Postgres micro-topic table (1,500+ rows), not LLM memory |
| Req 3 (SOUL Prompt) | Part A persona — **merge**: friendly/motivating tone from Part A becomes the wrapper; hint-first Socratic behavior is stricter and wins for numericals. CBSE board-style answers are the scoped exception (Req 27.2) |
| Req 10 (cron orchestration) + Ghosting Protocol | Part A Phase 3 nightly job; n8n replaces `gemini_scheduler_service.py` |
| Req 12 (localized parent summaries) | Part A Phase 3 dual-version daily/weekly summary — upgraded: weekly cadence, voice note via Sarvam, WhatsApp delivery, well-being indicator (opt-in) |
| Req 13 (Razorpay/UPI) | `payment_router.py` / `razorpay_client.py` — add ₹1,500/mo UPI 1-click flow, 3-day grace restriction, 90-day data retention |
| Req 20 (parent analytics dashboard) | `parent_dashboard_router.py`, `analytics_service.py` — add heatmap, 30-day trends, 15% drop alert, native-language UI |
| Req 21 (gamification) | `gamification_router.py` — add XP values per activity, WhatsApp notify to parent on badge |
| Req 26/27 (exam scope + CBSE) | `exam_router.py`, `data/syllabus/` — add cbse_11/cbse_12 tagging + NCERT mapping; Exam Scope union logic |

**Net-new build (no current anchor):**

- Req 4/6 — Sarvam STT/TTS integration, 45 s / 7-per-day voice quota, auto-switch to text mode, 8 s TTS timeout fallback
- Req 5/15/17 — Excalidraw JSON generation, client rendering, PNG render → DeepSeek Vision check (3-attempt cap, warning label), mind maps with node→doubt-session linking
- Req 7/16 — pgvector semantic cache (60% hit-rate target by Month 6) + Generated Content Store with deterministic content hash and usage counts
- Req 9 — Concept Wall (3 consecutive failures → lock → mandatory Excalidraw revision → follow-up quiz)
- Req 11/14 — OTP auth (SMS OTP, 5-min expiry, 3-strike lock, 30-min idle session invalidation)
- Req 18/19/22/23 — podcasts (2/day cap), internet research mode (3 searches/session cap), group study rooms (≤5 members, 120-min cap, abuse filter), JEE score predictor
- Req 24/25 — AI Calling Agent: Vobiz outbound/inbound, real-time Sarvam↔OpenRouter↔Sarvam loop, call transcripts + sentiment summaries in Postgres, consent window + permanent opt-out, 10-min cap, 2 calls/day cap, parent feedback table wired into schedule recalculation

## C.3 Unified roadmap (supersedes Part A phasing if Option A is chosen)

| Phase | Scope | Hermes reqs | Exit criteria |
|---|---|---|---|
| **0 — Foundation** | Stack decision; Postgres + pgvector + n8n stood up; seed 1,500+ micro-topics (JEE + CBSE, exam_codes + NCERT mapping); OTP auth | 8 (data), 11, 14, 26, 27 (data) | Micro-topic table queryable; OTP login E2E |
| **1 — Core agent (text)** | Hermes Agent service: Session ID isolation, SOUL Prompt (merged Part A persona), OpenRouter client with prompt-caching headers + retry; chat memory (rolling summary); quiz loop driving Micro-State transitions | 1, 2, 3, 8 | Text doubt loop E2E; state transitions verified; prompt-injection refusal tested |
| **2 — Cost layer** | pgvector semantic cache (embed + threshold), Generated Content Store (content-hash), usage accounting per student, quota middleware | 7, 16 | Cache hit/miss path tested; per-user cost dashboard shows ₹/user/mo within ₹90–120 target |
| **3 — Voice** | Sarvam STT intake (45 s, Hinglish), 7/day quota + auto text-mode switch, Bulbul TTS hints (10–15 s, async, 8 s timeout fallback) | 4, 6 | Voice doubt E2E < 10 s transcription; quota exhaustion path verified |
| **4 — Whiteboard** | Excalidraw JSON generation + client component; PNG render + DeepSeek Vision check (≤3 attempts, warning label); mind maps with node→doubt linking | 5, 15, 17 | Vision check pass/fail paths tested; mind map renders + launches session |
| **5 — Parent loop** | Parent portal (OTP), localized weekly summary + Sarvam voice note, WhatsApp delivery, parent analytics dashboard (heatmap, trends, 15% drop alert), well-being indicator (opt-in) | 12, 20 | Parent receives weekly summary + voice note in Hindi/Marathi/Telugu |
| **6 — Orchestration** | n8n crons (6 AM targets, 8 PM recalc), Ghosting Protocol (48 h → WhatsApp to parent), adaptive daily targets from Micro-State | 10 (extends Part A Phase 3) | Both crons run reliably for 7 consecutive days |
| **7 — Billing** | Razorpay UPI 1-click, ₹1,500/mo, invoices, 3-day grace restriction, 90-day retention | 13 | Payment → entitlement → restriction flow tested in Razorpay test mode |
| **8 — Calling agent** | Vobiz outbound/inbound, real-time STT↔LLM↔TTS loop, consent window + opt-out, transcripts + sentiment in Postgres, parent feedback table → schedule recalculation, retry + WhatsApp fallback | 24, 25 | Test call E2E in all 3 languages; opt-out honored permanently |
| **9 — Growth features** | Podcasts (2/day cap), research mode (3/search cap), group study rooms (≤5, 120 min, abuse filter), score predictor + 60-day trajectory, Concept Wall | 9, 18, 19, 22, 23 | Each feature behind quota; Concept Wall lock/unlock verified |

Part A's guardrails carry forward unchanged: tone safety (now enforced *by* the SOUL Prompt, Req 3.3), minors' data handling, token/cost caps, mock-client test paths (mock Sarvam/Vobiz/OpenRouter clients mirroring `mock_gemini_client.py`).

## C.4 Cost architecture (Req 7 — 90%+ gross margin)

Three caching layers stack multiplicatively: **semantic cache** (pgvector, similar-doubt reuse) → **Generated Content Store** (deterministic content hash across students) → **OpenRouter prompt caching** (system prompt + SOUL + syllabus context). Plus behavioral quotas: 7 voice queries/day, 2 podcasts/day, 3 research searches/session, 2 outbound calls/day, 10-min call cap. Unit economics must be instrumented from Phase 2 onward: log tokens, STT/TTS seconds, and call minutes per student per day, with the ₹90–120/user/month budget as a CI-visible metric.

## C.5 Open decisions (need your call before Phase 0)

1. **Greenfield vs. evolve** (C.1, Option A vs. B) — drives everything else.
2. **Migration of Mentor AI assets**: syllabus data + question validators are portable; existing users/Firestore data — migrate, freeze, or sunset?
3. **WhatsApp provider** — the spec requires WhatsApp (Ghosting, summaries, badge alerts) but names no vendor; options: WhatsApp Business API (Meta direct vs. an aggregator like Gupshup/AiSensy/Twilio).
4. **n8n hosting** — self-hosted (cost, ops burden) vs. cloud (speed).
5. **DeepSeek model pinning** — "V4-Flash" availability/pricing on OpenRouter should be validated before Phase 1; fallback model choice needed.
6. **Sarvam/Vobiz sandbox access** — dev/test accounts and rate limits to confirm before Phases 3 and 8.
7. **Well-being indicator scope** (Req 12.4) — activity-pattern heuristics only, or clinician-reviewed? Legal/privacy review warranted since users are minors.
8. **Group rooms moderation** (Req 22.5) — keyword filter vs. classifier; human review queue or fully automated?
