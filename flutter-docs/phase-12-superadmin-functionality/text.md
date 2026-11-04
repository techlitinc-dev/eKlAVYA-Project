# Phase 12 — Reference (text.md)

Every contract below was read directly from `Backend/routers/superadmin_router.py` (898 lines)
at the phase-01 inspected commit. Citations are `path:line`. Error envelopes follow phase-01 §4:
legacy routers raise `HTTPException`, so error bodies are `{"detail": "<message>"}` with the
matching HTTP status.

Router prefix and tag: `router = APIRouter(prefix="/api/superadmin", tags=["SuperAdmin Portal"])`
(`superadmin_router.py:34`). AuthN on all 16 endpoints: **none** (phase-01 §11 gap #8) — the
panel still sends `Authorization: Bearer <eklavya_token>` so enforcement can be switched on
server-side without a client change.

---

## 1. Endpoint index (16 existing + 5 PROPOSED)

| # | Method & path | Handler | Status |
|---|---|---|---|
| 1 | POST `/api/superadmin/login` | `superadmin_login` `:413` | existing |
| 2 | POST `/api/superadmin/demo-session` | `create_demo_session` `:435` | existing, **not a panel flow** (see §2.2) |
| 3 | GET `/api/superadmin/overview` | `get_superadmin_overview` `:454` | existing |
| 4 | GET `/api/superadmin/users` | `list_platform_users` `:535` | existing |
| 5 | POST `/api/superadmin/users/action` | `execute_user_admin_action` `:609` | existing |
| 6 | GET `/api/superadmin/questions` | `list_all_pyq_questions` `:710` | existing |
| 7 | POST `/api/superadmin/questions` | `create_pyq_question` `:737` | existing |
| 8 | PUT `/api/superadmin/questions/{question_id}` | `update_pyq_question` `:758` | existing |
| 9 | DELETE `/api/superadmin/questions/{question_id}` | `delete_pyq_question` `:777` | existing |
| 10 | GET `/api/superadmin/flashcards` | `list_all_flashcards` `:794` | existing |
| 11 | POST `/api/superadmin/flashcards` | `create_flashcard` `:800` | existing |
| 12 | DELETE `/api/superadmin/flashcards/{card_id}` | `delete_flashcard` `:820` | existing |
| 13 | GET `/api/superadmin/colleges` | `list_all_colleges` `:831` | existing |
| 14 | PUT `/api/superadmin/colleges/{college_id}` | `update_college_cutoffs` `:838` | existing |
| 15 | GET `/api/superadmin/assessments` | `list_platform_assessments` `:867` | existing |
| 16 | GET `/api/superadmin/system-config` | `get_system_config` `:882` | existing |
| 17 | PUT `/api/superadmin/system-config` | `update_system_config` `:892` | existing |
| P1 | GET `/api/superadmin/tests` | — | **PROPOSED** (gap #8) |
| P2 | GET `/api/superadmin/submissions` | — | **PROPOSED** (gap #8) |
| P3 | GET `/api/superadmin/analytics` | — | **PROPOSED** (gap #8) |
| P4 | GET `/api/superadmin/schedules` | — | **PROPOSED** (gap #8) |
| P5 | GET `/api/superadmin/workflow-stats` | — | **PROPOSED** (gap #8) |

(Numbering: 17 rows are live; the table lists 16 endpoint paths because GET/PUT
`/system-config` share one path. Phase-01 §9.6 counts 16 endpoints.)

## 2. Existing contracts (verified)

### 2.1 POST `/api/superadmin/login` — `superadmin_router.py:413-432`

Request model `SuperAdminLoginRequest` (`:106-108`): `{ "email": string (default
"admin@eklavya.ai"), "password": string (default "SuperAdmin123!") }`.

Authorization logic (`:416-421`): the email (trimmed, lowercased) must be one of
`{"admin@eklavya.ai", "superadmin@eklavya.ai", "root@eklavya.ai"}` **or** contain the substring
`"admin"`; otherwise 401 `{"detail": "Invalid SuperAdmin credentials"}`. **The password field is
never read — any value succeeds.** This call also seeds the demo accounts (parent
`parent_demo_eklavya`, child `child_demo_aarav`, premium subscription, session tokens —
`ensure_demo_accounts_seeded` `:180-408`) and writes a `SUPERADMIN_LOGIN` audit entry.

Success 200 — shape (assembled at `:424-432` from `seeded["superadmin"]` `:400-406`):

```json
{
  "status": true,
  "message": "SuperAdmin login successful",
  "token": "<jwt: parent-format token, parent_id=\"superadmin_root\", role claim absent—see note>",
  "admin_id": "superadmin_root",
  "name": "eKlAVYA SuperAdmin",
  "email": "admin@eklavya.ai",
  "role": "superadmin",
  "demo_accounts": { "parent_id": "parent_demo_eklavya", "child_id": "child_demo_aarav" }
}
```

Client note: the token is minted by `token_service.generate_access_token(parent_id=
"superadmin_root", email=...)` (`:372-374`), i.e. a parent-format JWT. The panel must not
inspect claims beyond storage; it treats `role: "superadmin"` from the JSON body as the session
role. Errors: 401 invalid email; 500 possible via catch-all (phase-01 §4).

`BACKEND CHANGE REQUIRED` (phase-01 §11 gap #8): verify a superadmin password hash before
issuing the token. PROPOSED (server-side): keep the request shape; on failure return the same
401 `{"detail": "Invalid SuperAdmin credentials"}` so the panel flow does not change.

### 2.2 POST `/api/superadmin/demo-session` — `:435-451`

Request: `{ "role": "student" | "parent" | "superadmin" }` (default `"student"`; any other value
is silently coerced to `"student"` — `:442-444`). Response 200:

```json
{
  "status": true,
  "role": "student",
  "active_session": { "token": "...", "...": "role-specific session object" },
  "all_sessions": { "parent": {...}, "student": {...}, "superadmin": {...}, "micro_topics_seeded": 126 }
}
```

**Panel disposition:** this is the 1-click demo role switcher already consumed by
`AuthContext.switchDemoRole` (`Frontend_Website/src/context/AuthContext.tsx:61-69`) and the
AppShell portal switcher (`Frontend_Website/src/components/AppShell.tsx:45-55`). It is classified
`internal` in phase-01 §9.6 and is **not part of any panel flow** — no panel page calls it
directly, and this phase adds no new usage.

### 2.3 GET `/api/superadmin/overview` — `:454-532`

No params. Success 200:

```json
{
  "status": true,
  "timestamp": "<ISO-8601 UTC>",
  "kpis": {
    "total_parents": 1,
    "total_students": 1,
    "active_premium_subscriptions": 1,
    "total_revenue_inr": 7999,
    "total_pyq_questions": 18,
    "total_flashcards": 12,
    "total_ncert_modules": 4,
    "total_colleges_tracked": 3,
    "syllabus_micro_topics": 126,
    "custom_tests_generated": 0,
    "homework_assignments": 1,
    "active_concept_walls": 1
  },
  "distributions": { "pyq_by_subject": { "Physics": 6 }, "pyq_by_exam": { "JEE Main": 10 } },
  "active_concept_walls": [
    { "child_id": "child_demo_aarav", "student_name": "Aarav Sharma",
      "micro_topic_id": "mt_...", "topic_name": "Moment of Inertia & Rolling Motion" }
  ],
  "system_health": {
    "fastapi_backend": "healthy",
    "firestore_db": "connected",
    "gemini_ai_engine": "gemini-2.5-flash-lite",
    "sse_streaming_hub": "operational",
    "nta_cbt_engine": "operational"
  },
  "recent_audit_logs": [
    { "id": "aud_01", "timestamp": "<ISO-8601 UTC>", "actor": "admin@eklavya.ai",
      "action": "SYSTEM_STARTUP", "detail": "..." }
  ]
}
```

Field notes (verified): `total_revenue_inr` is computed from `amount_paid` **in paise divided by
100** (`:500`) — the seeder writes `amount_paid: 799900` (`:272`), so display is rupees. Values
shown above are seed-state examples, not constants. `recent_audit_logs` is the newest 10 of an
in-memory ring (100 max, `:60-71`). `system_health.gemini_ai_engine` echoes the configured model
name from runtime config (`:46`), not a liveness probe.

### 2.4 GET `/api/superadmin/users` — `:535-606`  and  POST `/api/superadmin/users/action` — `:609-705`

**GET** — no params. Success 200:

```json
{
  "status": true,
  "total_parents": 1,
  "total_students": 1,
  "parents": [
    {
      "parent_id": "parent_demo_eklavya",
      "name": "Dr. Rajesh Sharma",
      "email": "rajesh.sharma@eklavya.ai",
      "phone": "+919876543210",
      "language": "en",
      "plan_id": "premium_yearly",
      "plan_name": "Premium Yearly",
      "subscription_status": "active",
      "created_at": "2026-11-02T05:00:00+00:00"
    }
  ],
  "students": [
    {
      "child_id": "child_demo_aarav",
      "parent_id": "parent_demo_eklavya",
      "name": "Aarav Sharma",
      "username": "aarav_jee2026",
      "grade": 12,
      "age": 17,
      "exam_scope": ["JEE_MAIN", "JEE_ADVANCED"],
      "completion_pct": 14.3,
      "counts": { "UNTOUCHED": 100, "LEARNING": 10, "MASTERED": 6 },
      "locked_topics": ["mt_rotational_001"],
      "xp": 740,
      "streak_days": 7,
      "badges": ["first_steps", "first_mastered", "quiz_10_passed", "streak_7"],
      "weekly_league_points": 640
    }
  ]
}
```

Verified details: parent `plan_id`/`plan_name`/`subscription_status` default to
`"free"`/`"Free Plan"`/`"free"` when no subscription doc exists (`:556-558`); `created_at` is a
stringified Firestore value (`:559`). Student `counts` keys are exactly `UNTOUCHED`,
`LEARNING`, `MASTERED`; on a telemetry failure the handler falls back to
`{UNTOUCHED:0, LEARNING:0, MASTERED:0}` and `exam_scope: ["JEE_MAIN"]` (`:575-579`).
`weekly_league_points` defaults to **640** when the student has no entry (`:596`).
`locked_topics` is the list of micro-topic ids with `wall_locked == true`.

**POST action** — request model `UserAdminActionRequest` (`:115-121`):
`{ "action": "grant_premium" | "revoke_premium" | "unlock_concept_wall" | "trigger_concept_wall" | "award_xp" | "reset_chat_cap", "target_id": "<parent_id or child_id>", "value": <optional any> }`.
The handler lowercases `action` (`:613`). Per-action behavior, all verified:

| action | target | effect (`:616-703`) | success body |
|---|---|---|---|
| `grant_premium` | parent id | writes `subscriptions/{tid}` = premium_yearly, status `active`, 365-day end, `amount_paid: 799900` | `{"status": true, "message": "Premium Yearly activated for <tid>"}` |
| `revoke_premium` | parent id | plan `free`, status `cancelled` | `{"status": true, "message": "Subscription downgraded to Free for <tid>"}` |
| `unlock_concept_wall` | child id | clears **all** `wall_locked` topics for the student, resets `consecutive_failures` to 0 | `{"status": true, "message": "Cleared N Concept Wall(s) for <tid>", "cleared_topics": ["mt_..."]}` |
| `trigger_concept_wall` | child id | locks `value` (or first in-scope topic) with `state: LEARNING`, `consecutive_failures: 3`, `wall_locked: true` | `{"status": true, "message": "Concept Wall locked on <mt_id> for <tid>"}` — **404** `{"detail": "No in-scope topics found for student"}` when the student has no in-scope topics (`:670-671`) |
| `award_xp` | child id | adds `int(value or 100)` to `hermes_gamification.xp` and to weekly league points | `{"status": true, "message": "Awarded +<pts> XP to <tid>"}` |
| `reset_chat_cap` | child id | zeroes today's `hermes_usage/{tid}_{today}.chat_turns` | `{"status": true, "message": "Daily chat turns reset to 0 for <tid>"}` |
| anything else | — | — | **400** `{"detail": "Unsupported action: <action>"}` (`:705`) |

Panel rules: `unlock`/`trigger` apply to **concept walls**, never to passwords; `award_xp`
validates `value` is a positive integer before sending; every action is confirmed via
`ConfirmDialog`, and `revoke_premium` / `trigger_concept_wall` / both deletes require **typed
confirmation** (admin types the target id). Every call — success or failure — is written to the
panel's local audit log (`eklavya_superadmin_audit`, who/when/what) and the server also writes
its own `_log_audit` entry (`:634,648,660,684,694,702`).

**Child credential reset does not exist** (`BACKEND CHANGE REQUIRED`, phase-01 §11 gap #2):
`ChildProfileUpdate.username/password` are declared but dropped by
`child_service.update_child_profile` (`child_service.py:416-442`), and no superadmin action
resets credentials. Intended UX (implemented as a disabled control only): Users page → student
detail drawer → "Reset credentials" button, always `disabled`, tooltip:
"BACKEND CHANGE REQUIRED (phase-01 §11 gap #2) — backend has no credential-reset path".
PROPOSED (server-side): extend `UserAdminActionRequest` with
`action: "reset_child_credentials"`, `target_id: <child_id>`, `value: <new_password>`; server
updates Firestore (hashed) + Firebase Auth user `{username}@mentor-ai.local`; response
`{"status": true, "message": "Credentials reset for <child_id>"}`; on validation failure 422.
The panel must not call this until it exists.

### 2.5 PYQ CMS — `:710-789`

**GET** `/api/superadmin/questions?examId=&subjectId=&search=` — filters are case-insensitive
exact matches on `examId`/`subjectId` unless the param equals `"all"` (or is empty); `search`
substring-matches `statementHtml`, `chapter`, `topic`, `id` (`:720-732`). Success 200:
`{"status": true, "totalCount": <int>, "questions": [ <question objects> ]}`. Each question
carries the fields written by the seeder/CMS: `id`, `examId`, `exam`, `subjectId`, `subject`,
`chapterId`, `chapter`, `topicId`, `topic`, `year`, `shift`, `type` (`MCQ`/`NAT`), `difficulty`,
`revisionZone`, `ncertPages`, `statementHtml`, `options` (`List[{id, text}]`), `correctOption`,
`numericalAnswer`, `numericalTolerance`, `correctMarks`, `negativeMarks`, `solutionHtml`,
`commonMistakeType`, plus CMS-added `hasVideoSolution: true` and `videoContentId` (`:745-746`).

**POST** — body `PYQQuestionUpsertRequest` (`:124-148`). Required by the model: `statementHtml`,
`solutionHtml`; everything else has defaults (see the model for exact defaults — `examId
"jee_main"`, `year 2025`, `type "MCQ"`, `correctMarks 4`, `negativeMarks -1`, etc.). Server
assigns `id = request.id or f"q_{examId}_{year}_{subjectId[:2]}_{uuid4.hex[:4]}"` (`:742`),
sets the video fields, **replaces any question with the same id** (`:749`), prepends, persists to
`Backend/data/pyq_and_colleges.json`, and hot-reloads the CPYQB/ecosystem/AI-hub services
(`:74-82`). 201: `{"status": true, "message": "PYQ Question saved and hot-reloaded",
"question": {...}}`.

**PUT** `/api/superadmin/questions/{question_id}` — same body; merges over the stored question
keeping the path id (`:765`); **404** `{"detail": "Question not found: <id>"}` (`:769`). 200:
`{"status": true, "message": "PYQ Question updated", "question": {...}}`.

**DELETE** `/api/superadmin/questions/{question_id}` — **404** if unknown (`:783-784`). 200:
`{"status": true, "message": "Deleted <id>"}`.

XSS note: `statementHtml`/`solutionHtml` are rendered by `LatexRenderer` via unsanitized
`dangerouslySetInnerHTML` (`Frontend_Website/src/components/LatexRenderer.tsx:61-62`). The
panel-side fix (mandatory): DOMPurify sanitization inside `LatexRenderer` before injection —
see instructions Step 3. Server-side sanitization is `BACKEND CHANGE REQUIRED` (recommendation,
gap #8-adjacent hardening; not numbered separately in phase-01 §11).

### 2.6 Flashcards — `:794-828`

**GET** → `{"status": true, "totalCount": <int>, "cards": [ ... ]}` (cards from the live RFC
ecosystem service). **POST** — body `FlashCardCreateRequest` (`:151-160`): `title`,
`frontText`, `backFormulaHtml` required; `cardId` optional (server default
`rfc_custom_<6hex>`, `:802`); `subjectId`, `chapterId`, `chapterName`, `topicName`,
`keyTakeaways` optional. 201: `{"status": true, "message": "Flashcard added to RFC deck",
"card": {...}}`. **DELETE** `/{card_id}` → `{"status": true, "message": "Deleted <card_id>"}`
(no 404 on unknown id — the handler just filters, `:823-826`). `backFormulaHtml` may contain
LaTeX; render only through the sanitized `LatexRenderer`.

### 2.7 Colleges — `:831-862`

**GET** → `{"status": true, "totalCount": <int>, "colleges": [ { "id", "name", "branches":
[ { "branchCode", "branchName", "seats"?, "cutoffs": { "<year>": { "<category>": <int rank> } }
} ] } ]}` (field names as stored in `data/pyq_and_colleges.json`).

**PUT** `/api/superadmin/colleges/{college_id}` — body `CollegeCutoffUpdateRequest`
(`:163-167`): `{ "branchCode": string (required), "year": string (default "2025"),
"cutoffs": { "<category>": <int> }, "seats": int? }`. Branch match is case-insensitive
(`:849`). Sets `branch.cutoffs[year] = cutoffs` and optionally `seats` (`:850-852`). **404**
only when the *college* id is unknown (`:854-855`); a wrong `branchCode` silently matches
nothing and still returns 200 — the panel must populate `branchCode` choices from the loaded
college's own `branches[]`. 200: `{"status": true, "message": "College cutoffs updated",
"college": <full updated college object>}`.

### 2.8 Assessments — `:867-879`

GET → `{"status": true, "custom_tests": [ ... ], "custom_attempts": [ ... ], "assignments":
[ ... ]}` — raw values of in-memory state dicts (`_CPYQB_STATE["custom_tests"]` keyed by test
id; `_CPYQB_STATE["custom_attempts"]` excluding keys starting `by_test_`; `_ECOSYSTEM_STATE
["assignments"]`). Schemas for the row objects are not enforced by a Pydantic model — the panel
must render defensively (optional chaining, fallbacks) and tolerate schema drift. Read-only.

### 2.9 System config — `:882-898`

**GET** → `{"status": true, "config": {...}, "soul_prompt": "<SOUL_PROMPT text>",
"audit_logs": [ ...newest-first, up to 100... ] }`. Config defaults (`:38-47`):
`free_daily_chat_cap: 5`, `premium_daily_chat_cap: 50`, `mastery_threshold_pct: 70.0`,
`passes_for_mastery: 2`, `failures_for_concept_wall: 3`, `rate_limit_per_minute: 200`,
`maintenance_mode: false`, `gemini_model: <env GEMINI_MODEL || "gemini-2.5-flash-lite">`.
`soul_prompt` is imported from `services.hermes_agent_service` (`:27`) — display read-only.

**PUT** — body `SystemConfigUpdateRequest` (`:170-175`): only `free_daily_chat_cap`,
`premium_daily_chat_cap`, `mastery_threshold_pct`, `rate_limit_per_minute`,
`maintenance_mode` are accepted; `None` fields are skipped (`:895`), so partial updates work.
200: `{"status": true, "message": "System configuration updated", "config": <full config>}`.
`passes_for_mastery`, `failures_for_concept_wall`, `gemini_model` are read-only in the UI.

## 3. PROPOSED workflow-monitoring endpoints (`BACKEND CHANGE REQUIRED`, phase-01 §11 gap #8)

Phase-01 §11 gap #8: "Superadmin cannot monitor the workflow domain… Add read-only
`GET /api/superadmin/tests`, `/submissions`, `/analytics`, `/schedules` + stats". The panel
implements the four pages (instructions Step 12) in a permanently blocked state until these
exist. Contracts below are **PROPOSED** — proposals only; the backend team owns final contracts.

| # | Method & path | Auth (required) | PROPOSED response shape |
|---|---|---|---|
| P1 | GET `/api/superadmin/tests` | JWT, superadmin role | `{ "status": true, "total": int, "tests": TestMetadata[] }` — rows from `diagnostic_tests`; fields per `TestMetadata` (`diagnostic_test_models.py:523` handler region): `test_id`, `child_id`, `exam_type`, `scheduled_date`, `duration_minutes`, `total_questions`, `status` |
| P2 | GET `/api/superadmin/submissions` | JWT, superadmin role | `{ "status": true, "total": int, "submissions": TestSubmission[] }` — persisted `test_submissions`; fields per `TestSubmission` (`diagnostic_test_models.py:120-177`): `test_id`, `student_id`, `answers` (`Dict[int,str]`), `time_taken`, `submission_time`; include scored `total_score`/`percentage` if the persistence layer stores them |
| P3 | GET `/api/superadmin/analytics` | JWT, superadmin role | `{ "status": true, "total": int, "reports": AnalyticsReport[] }` — `analytics_reports` docs; fields per `AnalyticsReport` (`analytics_models.py:706-762`): `analytics_id?`, `overview`, `subject_analysis`, `topic_analysis`, `ai_insights?`, `priority_topics`, `metadata`, `generated_at`; support `?student_id=` and `?test_id=` filters |
| P4 | GET `/api/superadmin/schedules` | JWT, superadmin role | `{ "status": true, "total": int, "schedules": Schedule[] }` — `schedules` docs; fields per `Schedule` (`schedule_models.py:441-567`): `schedule_id`, `student_id`, `analytics_id`, `exam_type`, `exam_date`, `generated_date`, `total_days`, `daily_study_hours`, `status`, `days` (truncatable), `revision_days`, `practice_test_days`, `buffer_days`, `priority_topics` |
| P5 | GET `/api/superadmin/workflow-stats` | JWT, superadmin role | `{ "status": true, "tests_by_status": {...}, "submissions_24h": int, "analytics_by_status": {...}, "schedules_by_status": {...}, "pipeline_lag_seconds": {...} }` — aggregate KPIs for the monitoring landing strip |

All PROPOSED endpoints return the legacy error envelope (`{"detail": ...}`) and 401 for
missing/non-superadmin JWT. They are read-only by design — no write path is proposed for the
workflow domain.

## 4. Consumer matrix (phase-01 classification)

| Endpoint | Consumer | Phase |
|---|---|---|
| All 16 rows of §1 (paths 1, 3–17) | superadmin | P12 (this phase) |
| `POST /demo-session` | internal (existing switcher only) | — |

## 5. Screen specifications

Routes (all inside `AppShell`, all guarded by `RequireSuperadmin`):

| Route | Section | Data source |
|---|---|---|
| `/superadmin/login` (section of `/login`) | Login | `POST /login` |
| `/superadmin/dashboard` | Dashboard | `GET /overview` |
| `/superadmin/users` | Users | `GET /users`, `POST /users/action` |
| `/superadmin/questions` | PYQ CMS | questions endpoints |
| `/superadmin/content` | Flashcards + Colleges | flashcards + colleges endpoints |
| `/superadmin/assessments` | Assessments | `GET /assessments` |
| `/superadmin/ai-settings` | AI settings | system-config endpoints |
| `/superadmin/monitoring/tests` | Workflow monitoring (blocked) | — (P1) |
| `/superadmin/monitoring/submissions` | Workflow monitoring (blocked) | — (P2) |
| `/superadmin/monitoring/ai-results` | Workflow monitoring (blocked) | — (P3) |
| `/superadmin/monitoring/schedules` | Workflow monitoring (blocked) | — (P4, P5) |

### 5.1 Login screen
Card-centered form: email, password, submit "Sign in to SuperAdmin". States: idle, submitting
(button spinner), 401 error banner (server `detail`), network error banner. Above the form:
`SuperadminSecurityNotice` (§8). On success: `loginWithSession`, navigate to dashboard.

### 5.2 Dashboard
12 KPI cards (§2.3), two distribution bar charts, active-concept-walls list, system-health pill
row, recent-audit-log table. Refresh button re-fetches; skeletons on load; error+retry on failure.

### 5.3 Users
`DataTable` + `FilterBar` (role segment All/Parents/Students; search across name/email/username/
ids). Parent columns: name, email, phone, plan pill, status pill, created, actions (Grant,
Revoke). Student columns: name, username, grade, exam_scope, completion bar, three count pills
(UNTOUCHED neutral / LEARNING warning / MASTERED success), xp, streak, badges count, league
points, actions (Unlock or Trigger wall, Award XP, Reset cap, disabled Reset credentials).
Detail drawer: all fields of the row plus `locked_topics` list (student) and `badges` chips.
Action dialogs per §2.4; typed confirmation for revoke/trigger.

### 5.4 Questions CMS
FilterBar (exam, subject, search → server params `examId`, `subjectId`, `search`). DataTable
columns per §2.5. Editor drawer with validated form (client rules in instructions Step 8) and
live sanitized KaTeX preview. Delete via typed-confirm dialog.

### 5.5 Content (flashcards + colleges)
Two stacked sections. Flashcards: create drawer (validated) + table + delete. Colleges: table +
branch editor drawer (branch select populated from `branches[]`; year select default "2025";
cutoff category inputs; optional seats).

### 5.6 Assessments
Three read-only DataTables (`custom_tests`, `custom_attempts`, `assignments`) with defensive
rendering; each with its own empty state.

### 5.7 Workflow monitoring (four blocked pages)
Each page: `BlockingNotice` (top) + fully specified-but-inert UI: DataTable column headers,
FilterBar fields, detail-drawer field list from §7, and the "Waiting for backend endpoint" empty
state. No fetches, no fabricated rows.

### 5.8 AI settings
Config form (5 editable fields, 3 read-only fields), read-only SOUL prompt with copy button,
audit-log table (100 rows max, paginated client-side).

## 6. Design tokens and components

Shared phase-03 web components (import, do not rebuild): `DataTable` (sortable, keyboard-nav,
`aria-sort`), `FilterBar`, `ConfirmDialog` (focus-trapped), `StatusPill` (success/warning/
danger/neutral/info), `PermissionDeniedState`. Token mapping onto the existing portal palette:
`--color-primary` → sky-400 accents (active nav, links); `--color-medical` → emerald-400
(success pills); `--color-wall` → amber-400 (governance accent, warning banner border);
`--color-danger` → rose-400 (destructive actions); `--color-review` → violet-400 (info pills);
glass surfaces remain `bg-slate-900/60` + `border-slate-800` + `backdrop-blur` per the current
portal (`SuperAdminPortal.tsx` passim). The monitoring "Blocked" badge uses `--color-wall`.

## 7. Monitoring page UI specifications (ready-to-light-up)

Column specs below reuse the exact models from phase-01 §7.C/D/E/F.

**Tests** (P1; model `TestMetadata`, phase-01 §7.C): columns test_id, child_id, exam_type,
scheduled_date, duration_minutes, total_questions, status pill. Filters: status, exam_type,
child_id search. Drawer: full `TestMetadata` row.

**Submissions** (P2; model `TestSubmission`, phase-01 §7.D): columns test_id, student_id,
submission_time, time_taken (formatted h:mm:ss), attempted count (from `answers`), scored
percentage when present. Filters: test_id, student_id, date range. Drawer: answers map
(question → answer), all scalar fields.

**AI Results** (P3; model `AnalyticsReport`, phase-01 §7.E): columns analytics_id, student_id
(from `overview.student_id`), exam_type (`overview.exam_type`), percentage
(`overview.percentage`), generated_at, priority_topics count. Filters: student_id, test_id, min
percentage. Drawer: overview block, subject_analysis bars, top-3 weak topics
(`priority_topics[:3]`), `ai_insights.overall_assessment`.

**Schedules** (P4; model `Schedule`, phase-01 §7.F): columns schedule_id, student_id, exam_type,
exam_date, generated_date, total_days, daily_study_hours, status pill, days count. Filters:
status, exam_type, student_id. Drawer: header fields, revision/practice/buffer day counts, first
5 `days[]` summaries. Landing strip reserved for P5 aggregates (tests_by_status etc.).

## 8. SuperadminSecurityNotice (banner specification)

Rendered on **every** authenticated superadmin screen (layout-level), non-dismissible,
`role="alert"`, amber (`--color-wall`) glass styling with a `ShieldAlert` icon. Copy (exact):

> "Security warning: this superadmin login does not verify passwords in the current backend
> (phase-01 §11 gap #8). Any email containing 'admin' receives full access, and none of the
> /api/superadmin endpoints check authentication yet. Use this panel for development and demo
> only; do not expose it to a network you do not trust. BACKEND CHANGE REQUIRED: superadmin
> password verification + JWT enforcement on all /api/superadmin/* routes."

The login screen shows the same notice above the form. The banner must never coexist with any
copy claiming the login is secure.

## 9. Hard rules

1. **Never display secrets.** No password, token, Firebase credential, JWT payload, or
   `password` field may be rendered anywhere — including the Users detail drawer (the backend
   `/users` response does not include passwords; if it ever does, the panel must filter the
   field out before rendering). The SOUL prompt is an AI instruction, not a secret: read-only
   display is allowed.
2. **Never claim the login is secure.** See §8.
3. **Blocked means blocked.** The four monitoring pages render `BlockingNotice` + spec'd empty
   tables only; no calls, no mock rows.
4. **Field names are backend names.** Types in `src/superadmin/types.ts` mirror the JSON exactly.
5. **Errors surface `detail`.** FastAPI errors are `{"detail": ...}`; the panel shows that text.
