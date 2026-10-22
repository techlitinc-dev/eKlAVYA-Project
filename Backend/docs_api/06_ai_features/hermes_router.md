# Hermes Router API Testing Guide

## Overview

The Hermes router provides the 1-to-1 AI mentor: a Socratic tutor that gives hints instead of answers, tracks syllabus progress through a deterministic micro-topic state machine, enforces the Concept Wall, and produces idempotent daily summaries (motivating student version + factual parent version) in the family's selected language.

Powered by Gemini via the shared `GeminiClient` — default `gemini-2.5-flash-lite` (cheapest tier); if your API key gets a 404 "no longer available to new users", set `GEMINI_MODEL` in `.env` (e.g. `gemini-3.5-flash-lite`). **RAG is not used** — the mentor answers from model knowledge bounded by the student's exam scope. No model training anywhere.

**Base URL:** `http://localhost:8000/api/hermes`

## Authentication

All endpoints require JWT authentication. A **student (child) token** acts as that child automatically; a **parent token** must pass `?child_id=...` and can only access their own child.

```bash
Authorization: Bearer <access_token>
```

| Role | Chat? | Quiz attempts? | Read progress/topics/summaries? |
|---|---|---|---|
| Student | yes | yes | own data |
| Parent | no (403) | no (403) | yes, with `child_id` param |

## Subscription rules

Entitlements live in `data/subscription_plans.json` under each plan's `entitlements` block; the `FeatureGatingService` resolves them from the parent's subscription (unknown/expired → free). Gated endpoints return **403** with an upgrade hint. Payment flow itself is unchanged (`/api/payment/*`).

| Capability | Free | Premium (monthly/yearly) |
|---|---|---|
| Mentor chat | 5 turns/day | 50 turns/day |
| Syllabus progress & micro-topics | ✅ | ✅ |
| Today's plan (`/today`) | ✅ | ✅ |
| XP / streaks / badges | ✅ | ✅ |
| Daily summaries (student + parent, local language) | ❌ 403 | ✅ |
| JEE score prediction (`/score-prediction`) | ❌ 403 | ✅ |
| Weekly parent report (`/parent/weekly`) | ❌ 403 | ✅ |
| Monthly report flag | ❌ | yearly only |

The nightly batch script skips children whose plan is not entitled (`skipped_not_entitled` in its stats), so free accounts never consume summary quota.

## Setup (one-time)

Seed the micro-topic library from `data/syllabus/*.json` (idempotent; safe to re-run):

```bash
curl -X POST "http://localhost:8000/api/hermes/admin/seed-topics" \
  -H "Authorization: Bearer <parent_token>"
```

## Endpoints

### 1. Chat with the mentor

**Endpoint:** `POST /api/hermes/chat` (student token)

```bash
curl -X POST http://localhost:8000/api/hermes/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <child_token>" \
  -d '{
    "message": "A ball is thrown at 20 m/s at 45 degrees. What is the range?",
    "language": "hinglish"
  }'
```

**Expected response (200 OK):**
```json
{
  "message_id": "hm_abc123",
  "session_id": "hs_xyz789",
  "answer": "Hint pehle socho — range ke liye kaunsa formula use hota hai jab launch angle 45° ho? R = u²·sin(2θ)/g. Ab tum values daal kar batao, sin(90°) kitna hota hai? ...",
  "language": "hinglish",
  "tokens_used": 812,
  "mock": false
}
```

Behavior notes:
- The mentor gives **hints/formulas/guiding questions, never final answers** to numericals (SOUL prompt). CBSE board-style answers are the only exception.
- `session_id` omitted → a new session is created; pass it back to continue the conversation.
- `language`: `en`, `hi`, `mr`, or `hinglish`. Omit to inherit the parent's preference.
- Daily cap: `HERMES_DAILY_CHAT_CAP` (default 50) chat turns/student/day → `429` beyond that.

### 2. List sessions

**Endpoint:** `GET /api/hermes/sessions?child_id=...` (parent token needs the param)

```bash
curl -X GET "http://localhost:8000/api/hermes/sessions" \
  -H "Authorization: Bearer <child_token>"
```

### 3. Get session history

**Endpoint:** `GET /api/hermes/sessions/{session_id}/messages?child_id=...`

```bash
curl -X GET "http://localhost:8000/api/hermes/sessions/hs_xyz789/messages" \
  -H "Authorization: Bearer <child_token>"
```

### 4. End a session (rolls up tutor memory)

**Endpoint:** `POST /api/hermes/sessions/{session_id}/end?child_id=...`

```bash
curl -X POST "http://localhost:8000/api/hermes/sessions/hs_xyz789/end" \
  -H "Authorization: Bearer <child_token>"
```

### 5. Record a quiz attempt (drives Micro-State)

**Endpoint:** `POST /api/hermes/quiz/attempt` (student token; parent → 403)

```bash
curl -X POST http://localhost:8000/api/hermes/quiz/attempt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <child_token>" \
  -d '{
    "micro_topic_id": "mt_a1b2c3d4e5f6",
    "score_pct": 80,
    "total_questions": 10
  }'
```

**Expected response (200 OK):**
```json
{
  "micro_topic_id": "mt_a1b2c3d4e5f6",
  "passed": true,
  "state": "LEARNING",
  "consecutive_passes": 1,
  "consecutive_failures": 0,
  "concept_wall_locked": false,
  "events": []
}
```

State rules:
- Score ≥ `HERMES_MASTERY_THRESHOLD` (default 70) = pass. **2 consecutive passes → `MASTERED`** (event `"mastered"`).
- Fail → `LEARNING`. **3 consecutive failures → Concept Wall** (event `"concept_wall_locked"`).
- While a wall is active, attempts on *other* topics return **`409 Conflict`**. Pass the follow-up quiz on the locked topic (revision mode) to clear it (event `"concept_wall_cleared"`).

### 6. List in-scope micro-topics

**Endpoint:** `GET /api/hermes/topics?child_id=...`

Returns the student's exam scope (union of exams from `exam_selections/{child_id}`) with each topic's current state.

### 7. Get progress

**Endpoint:** `GET /api/hermes/progress?child_id=...`

```json
{
  "child_id": "child_xxx",
  "exam_scope": ["JEE_MAIN"],
  "total_in_scope": 214,
  "counts": {"UNTOUCHED": 200, "LEARNING": 13, "MASTERED": 1},
  "completion_pct": 0.47,
  "locked_topics": []
}
```

### 8. Generate a daily summary (idempotent, cron-callable)

**Endpoint:** `POST /api/hermes/summary/generate/{child_id}?date=YYYY-MM-DD`

Parent token required. Safe to call repeatedly — an existing summary is returned unchanged. With **zero activity** for the date, a localized static template is served with **no Gemini call**.

### 9. Get a summary

**Endpoint:** `GET /api/hermes/summary/{child_id}?date=YYYY-MM-DD&audience=student|parent`

```bash
curl -X GET "http://localhost:8000/api/hermes/summary/child_xxx?audience=parent" \
  -H "Authorization: Bearer <parent_token>"
```

```json
{
  "child_id": "child_xxx",
  "date": "2026-10-21",
  "audience": "parent",
  "text": "आज आपके बच्चे ने मेंटर से 3 बातचीत की और 1 क्विज़ पास किया...",
  "language": "hi",
  "generated_at": "2026-10-21T15:43:00+00:00",
  "quiet_day": false,
  "mock": false
}
```

Returns `404` if not yet generated — call endpoint 8 first (or run the nightly script). **Premium** (403 on free).

### 10. Student home — `GET /api/hermes/today` (student token)

Everything the student home screen needs in one cheap, deterministic call: days until exam, today's targets (active Concept Wall topic → weakest LEARNING topics → highest-weightage UNTOUCHED), streak, XP, badges, chat turns used vs plan cap, whether today's summary is ready, and whether score prediction is available on their plan.

### 11. XP / streaks / badges — `GET /api/hermes/gamification` (student token)

```json
{
  "child_id": "child_xxx", "xp": 17, "streak_days": 1,
  "last_active_date": "2026-10-21",
  "counters": {"chat_turns": 1, "quiz_attempts": 1, "quiz_passes": 1, "masteries": 0, "walls_cleared": 0},
  "badges": ["first_steps"]
}
```

XP: chat +2 · quiz attempt +5 · quiz pass +10 · topic mastered +25 · wall cleared +15.
Badges: `first_steps`, `quiz_10_passed`, `first_mastered`, `wall_breaker`, `streak_7`, `streak_30`.

### 12. JEE score prediction — `GET /api/hermes/score-prediction` (student, Premium)

Deterministic estimate from mastery ratio weighted by topic weightage: per-subject predicted marks with a ±10% range, capped at subject maxima (300 total for JEE Main). No LLM call — safe to refresh on every read.

### 13. Parent overview — `GET /api/hermes/parent/overview?child_id=...` (parent token)

7-day activity (active days, chat turns, quiz attempts), progress snapshot, streak/XP, and **attention flags**:
- `inactive_48h` — no activity today or yesterday (Ghosting Protocol surfacing; WhatsApp delivery needs a vendor decision)
- `streak_at_risk` — streak ≥ 3 but no activity today
- `concept_wall_active` — a Concept Wall is locked

### 14. Weekly report — `GET /api/hermes/parent/weekly?child_id=...&date=` (parent, Premium)

Per-day breakdown for the 7-day window ending at `date`, plus the same aggregates and attention flags as the overview. Deterministic — no LLM cost.

## Nightly batch (cron)

The app has no in-process scheduler; use system cron:

```bash
0 21 * * * cd /path/to/MENTOR-AI-onlyapi && venv/bin/python scripts/generate_hermes_summaries.py >> logs/hermes_summaries.log 2>&1
```

Per-child dry run: `--child-id child_xxx --date 2026-10-21`. Zero-API-call run: `HERMES_MOCK=true`.

## Testing Workflow

Complete journey (see `tests/smoke_test_hermes.py` for an executable version):

1. Register/login parent → create child → login student (`tests/create_test_student.py`)
2. `POST /admin/seed-topics` (parent)
3. `GET /topics` → pick a `micro_topic_id`
4. `POST /chat` (student) — verify the reply is a hint, not the final answer
5. `POST /quiz/attempt` with score ≥ threshold → `LEARNING`
6. `POST /summary/generate/{child_id}` (parent) → `GET /summary?audience=student` and `=parent`
7. `GET /progress` — completion % reflects the attempt

## Troubleshooting

### 429 on chat
Daily cap reached (`HERMES_DAILY_CHAT_CAP`, default 50). Resets at midnight server time.

### 409 on quiz/attempt
A Concept Wall is active. Attempt the locked topic (revision), not another topic.

### 404 on summary
Generate it first: `POST /summary/generate/{child_id}` or run the nightly script.

### Answers sound like a mock / "Mock mode:" prefix
`HERMES_MOCK=true` is set. Unset it for real Gemini responses.

### Language is always English
Parent has no `preferences/settings.language` value (valid: `en`, `hi`, `mr`), or the request's `language` override is invalid (falls back to `en`).

## Cost Notes

| Knob | Default | Effect |
|---|---|---|
| `HERMES_CHAT_MAX_TOKENS` | 600 | Max tokens per mentor reply |
| `HERMES_SUMMARY_MAX_TOKENS` | 700 | Max tokens per daily summary |
| `HERMES_DAILY_CHAT_CAP` | 50 | Chat turns/student/day |
| `HERMES_MASTERY_THRESHOLD` | 70 | Quiz pass threshold (%) |
| `HERMES_MEMORY_ROLLUP_TURNS` | 10 | Turns before memory compression |
