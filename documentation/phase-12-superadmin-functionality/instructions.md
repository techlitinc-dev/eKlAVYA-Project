# Phase 12 — Instructions

Execute the steps in order. Each step is small and verifiable. **Guardrails** state what not to
do. Where the backend lacks a capability, the step says so and tells you to render the real
blocked state — never to fake the feature.

Working directory for all steps: `Frontend_Website/`. Backend assumed running at
`http://localhost:8000` (start with `./run.sh backend` from the repo root; verify with
`curl -s http://localhost:8000/health`).

---

## Step 0 — Prerequisites and verification of the running backend

1. From the repo root run `./run.sh backend` (or `cd Backend && source venv/bin/activate && uvicorn main:app --reload`).
2. `curl -s http://localhost:8000/health` returns a JSON health body.
3. `curl -s -X POST http://localhost:8000/api/superadmin/login -H 'Content-Type: application/json' -d '{"email":"admin@eklavya.ai","password":"anything"}' | python3 -m json.tool` returns HTTP 200 with `status`, `token`, `admin_id: "superadmin_root"`, `role: "superadmin"`, and `demo_accounts`. Note that the password was ignored — that is the documented gap #8 behavior; do not "fix" it client-side.
4. `npm install` inside `Frontend_Website/` (Node 18+). `npm run build` succeeds before you touch anything.

Guardrail: do not modify anything under `Backend/`. All backend deficiencies in this phase are
documented in `text.md` as `BACKEND CHANGE REQUIRED` with PROPOSED contracts.

## Step 1 — New dependencies (panel-side hardening only)

1. `npm install dompurify` and `npm install -D @types/dompurify`.
2. Confirm `package.json` still contains only the existing runtime deps plus `dompurify`
   (`Frontend_Website/package.json`). No router/state/UI libraries may be added.

Guardrail: DOMPurify is the only new runtime dependency allowed in this phase. It exists to close
the XSS hole described in Step 3.

## Step 2 — Shared superadmin infrastructure

Create `src/superadmin/` (new directory; the existing page stays untouched until Step 14's wiring
is proven). Implement, in this order:

1. `src/superadmin/types.ts` — TypeScript interfaces transcribed **verbatim** from the response
   shapes in `text.md` §2 (`OverviewResponse`, `Kpis`, `Distributions`, `ConceptWallEntry`,
   `SystemHealth`, `AuditLogEntry`, `UsersResponse`, `ParentRow`, `StudentRow`, `MicroTopicCounts`,
   `QuestionsResponse`, `PyqQuestion`, `FlashcardsResponse`, `FlashCard`, `CollegesResponse`,
   `College`, `Branch`, `AssessmentsResponse`, `SystemConfigResponse`, `UserActionRequest`,
   `UserActionResponse`). Field names match `superadmin_router.py` exactly (camelCase as written
   there: `totalCount`, `plan_id`, `child_id`, `pyq_by_subject`, etc.). Do not rename fields.
2. `src/superadmin/api.ts` — one typed function per endpoint, all calling the shared axios
   instance from `src/lib/api.ts` (`import api from '../lib/api'`). List:
   `loginSuperAdmin`, `getOverview`, `getUsers`, `executeUserAction`, `getQuestions`,
   `createQuestion`, `updateQuestion`, `deleteQuestion`, `getFlashcards`, `createFlashcard`,
   `deleteFlashcard`, `getColleges`, `updateCollegeCutoffs`, `getAssessments`,
   `getSystemConfig`, `updateSystemConfig`. No `demo-session` function: role switching stays in
   `AuthContext.switchDemoRole` (`src/context/AuthContext.tsx:61-69`) — do not duplicate it.
3. Error mapping helper `toPanelError(err: unknown): PanelError` that unwraps the axios error and
   reads the FastAPI `{"detail": string}` envelope (phase-01 §4) — `detail` if present, else
   `HTTP <status>`, else a generic message. Panel surfaces show `detail` text, never raw axios
   objects, never stack traces.
4. Local audit log `src/superadmin/localAudit.ts` — `logLocalAudit(action: string, targetId:
   string, detail: string)` appends `{ts: ISO-8601, actor: <current admin email from
   AuthContext>, action, targetId, detail}` to `localStorage` key `eklavya_superadmin_audit` (cap
   500 entries, newest first) and returns the entry. Every successful mutating call in Steps 6-10
   must invoke it. This is the panel-side "who/when/what" trail; the server-side trail is visible
   via `GET /api/superadmin/system-config` → `audit_logs` (shown on the AI Settings page).
5. `src/superadmin/components/BlockingNotice.tsx` — renders the standard blocked-feature panel:
   amber `StatusPill` labeled `BACKEND CHANGE REQUIRED`, the gap citation text (e.g.
   "phase-01 text.md §11 gap #8"), a short explanation, and the PROPOSED endpoint table passed in
   as props. Used by Steps 11-12. It renders only real information; it fetches nothing.
6. `src/superadmin/components/SuperadminSecurityNotice.tsx` — the non-dismissible warning banner
   specified in `text.md` §8. It appears at the top of every authenticated superadmin screen
   (render it once in the panel layout, Step 13).

Guardrail: never `console.log` tokens, request bodies containing secrets, or full response
objects. The login response contains a `token`; store it, never print it (hard rule `text.md` §9).

## Step 3 — Sanitized LaTeX rendering (panel-side XSS fix)

1. Modify `src/components/LatexRenderer.tsx` minimally: after the existing KaTeX/markdown
   `useMemo` transformation and **before** `dangerouslySetInnerHTML` (currently at
   `LatexRenderer.tsx:61-62`), run the produced HTML through
   `DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })`. Sanitize at render time, not at
   save time — the same component renders both trusted dataset content and freshly authored CMS
   content.
2. Add a `data-testid="latex-rendered"` attribute on the wrapper div so tests can target it.
3. Verify: create a PYQ whose `statementHtml` contains `<img src=x onerror=alert(1)>`; the
   rendered preview must show no `onerror` attribute in DevTools (DOMPurify strips it).

Guardrail: this is a deliberate, minimal behavioral change to a shared component. Do not rewrite
the KaTeX pipeline. Do not sanitize away LaTeX delimiters — DOMPurify's HTML profile keeps text
nodes (`$...$`, `$$...$$`) intact.

## Step 4 — Route scaffolding and guards

1. In `src/App.tsx`, extend the superadmin route block (`:117-157`) from 5 routes to 10, each
   rendering `AppShell` + the new `SuperadminPanel` layout with the right initial section
   (paths in `text.md` §5): `/superadmin/dashboard`, `/superadmin/users`,
   `/superadmin/questions`, `/superadmin/content`, `/superadmin/assessments`,
   `/superadmin/ai-settings`, `/superadmin/monitoring/tests`,
   `/superadmin/monitoring/submissions`, `/superadmin/monitoring/ai-results`,
   `/superadmin/monitoring/schedules`.
2. Implement `RequireSuperadmin` wrapper in `src/superadmin/components/RequireSuperadmin.tsx`:
   reads `useAuth()`; if `user?.role !== 'superadmin'` render `PermissionDeniedState` (phase-03
   component) with a link back to `/login`; else render children. Apply it inside each
   superadmin route element.
3. Extend `superAdminNav` in `src/components/AppShell.tsx:73-79` with the two new groups:
   `Assessments` (`/superadmin/assessments`, icon `ClipboardCheck`) and a "Workflow Monitoring"
   group containing Tests (`FileBarChart`), Submissions (`Inbox`), AI Results (`Brain`), Schedules
   (`CalendarDays`) — each with a "Blocked" badge. Import the four icons from `lucide-react`
   (already a dependency).

Guardrail: keep the existing five routes working — the old `SuperAdminPortal` remains reachable
until Step 14. No route may be removed in this step.

## Step 5 — Login screen (`/superadmin/login` section state)

1. Build `src/superadmin/pages/SuperAdminLogin.tsx` per `text.md` §5.1: email + password fields,
   submit calls `loginSuperAdmin`. On 200, call `loginWithSession` from `useAuth()` with
   `{ token, role: 'superadmin', name, email, userId: admin_id }` (fields per the login response
   in `text.md` §2.1) and navigate to `/superadmin/dashboard`.
2. On 401 show the server's `detail` ("Invalid SuperAdmin credentials") as a form error.
3. Render `SuperadminSecurityNotice` **above** the form (not below — it must be visible without
   scrolling on a 768px-tall viewport).
4. The form's helper copy must use the exact honest wording from `text.md` §8 ("This login does
   not verify passwords in the current backend…"). Never the word "secure".

## Step 6 — Dashboard (`/superadmin/dashboard`)

1. `useEffect` + `getOverview()` on mount; render skeleton cards while loading; error state with
   Retry button (re-fetches).
2. KPI cards (12, from `kpis` — `text.md` §2.3): the 4 headline cards first (total accounts =
   `total_parents` + `total_students`, `active_premium_subscriptions`, `total_revenue_inr`
   formatted with `toLocaleString('en-IN')` and ₹ prefix, `total_pyq_questions` +
   `total_flashcards`), then a secondary grid with the remaining 8 KPIs (`total_ncert_modules`,
   `total_colleges_tracked`, `syllabus_micro_topics`, `custom_tests_generated`,
   `homework_assignments`, `active_concept_walls`).
3. `distributions.pyq_by_subject` and `pyq_by_exam` as horizontal bars (percentage of max),
   labeled with counts.
4. `active_concept_walls` list (student name + topic name); empty → "No active Concept Walls".
5. `system_health` rendered as a StatusPill row (`fastapi_backend`, `firestore_db`,
   `gemini_ai_engine`, `sse_streaming_hub`, `nta_cbt_engine`).
6. `recent_audit_logs` table: `timestamp` (local, short), `actor`, `action` (StatusPill), `detail`.

## Step 7 — Users page (`/superadmin/users`)

1. `getUsers()` on mount; single `DataTable` with a `FilterBar` (role segment: All | Parents |
   Students; search input matching name/email/username/ids; see `text.md` §5.3). Two tabs are
   also acceptable, but the FilterBar is mandatory.
2. Parent columns: name, email, phone, plan (`plan_name` via `StatusPill`: active→success,
   cancelled/free→neutral), `subscription_status`, `created_at`, actions.
3. Student columns: name, username, grade, `exam_scope` (joined), `completion_pct` (with bar),
   micro-topic counts (`counts.UNTOUCHED/LEARNING/MASTERED` as three mini-pills), `xp`,
   `streak_days`, badges count, `weekly_league_points`, actions.
4. Row click opens the detail drawer (`text.md` §5.3): full field list per role, including
   `locked_topics` for students and `badges` chips.
5. Actions use `ConfirmDialog` per `text.md` §2.4: parent rows → Grant Premium, Revoke Premium;
   student rows → Unlock Concept Wall (when `locked_topics.length > 0`), Trigger Concept Wall
   (when 0), Award XP (prompts for points, default 100), Reset Chat Cap. Destructive-ish actions
   (revoke, trigger) require the typed confirmation: the admin must type the target id (parent or
   child id) into the dialog before the Confirm button enables.
6. On success: show the response `message`, `logLocalAudit(...)`, refresh the table. On error:
   show `detail` and still `logLocalAudit(action, targetId, 'FAILED: ' + detail)`.
7. Child rows render a "Reset credentials" menu item that is **always disabled** with the
   tooltip: "BACKEND CHANGE REQUIRED (phase-01 §11 gap #2) — POST /api/superadmin/users/action
   action=reset_child_credentials is PROPOSED, not implemented." Implementing the call is
   forbidden (`text.md` §2.4).

## Step 8 — PYQ CMS (`/superadmin/questions`)

1. `getQuestions()` with server-side filters wired to `FilterBar` (`examId`, `subjectId`,
   `search` — the GET supports exactly these three query params, `text.md` §2.5). DataTable
   columns: id, exam, year, subject, chapter, topic, type, difficulty, answer key
   (`correctOption ?? numericalAnswer`), actions (Edit, Delete).
2. Delete → `ConfirmDialog` with typed confirmation of the question id → `deleteQuestion` →
   refresh + `logLocalAudit`.
3. Editor drawer (create + edit): form fields per `PYQQuestionUpsertRequest` (`text.md` §2.5).
   Client validation before submit: `statementHtml` and `solutionHtml` non-empty; `year` 1990–
   current year+1; `correctMarks`/`negativeMarks` integers; MCQ requires 4 `options` (objects
   `{id, text}` with ids A–D) and `correctOption ∈ {A,B,C,D}`; NAT requires `numericalAnswer`
   numeric and `numericalTolerance > 0`. Show inline errors per field; disable Save while invalid.
4. Live preview: the sanitized `LatexRenderer` from Step 3 rendering the current
   `statementHtml`/`solutionHtml` (same pattern the existing form uses,
   `SuperAdminPortal.tsx:624-627`).
5. Save → `createQuestion` (no `id`) or `updateQuestion(id)`. On 201/200 show `message`, refresh,
   `logLocalAudit`.

## Step 9 — Content CMS: flashcards + colleges (`/superadmin/content`)

1. Flashcards: `getFlashcards()` → DataTable (cardId, subjectId, chapterName, title, truncated
   frontText, actions). Create drawer (fields per `FlashCardCreateRequest`, `text.md` §2.6) with
   validation (`title`, `frontText`, `backFormulaHtml` required) and sanitized preview.
   Delete → typed `ConfirmDialog`. Mutations call `logLocalAudit`.
2. Colleges: `getColleges()` → DataTable (name, city/state if present, branch count, per-branch
   cutoffs preview). Branch editor drawer: select branch by `branchCode`, edit `cutoffs` map for
   a chosen `year` (default "2025"), optional `seats` → `updateCollegeCutoffs` (`text.md` §2.7`).
   Note the backend silently no-ops a nonexistent `branchCode` (it only 404s an unknown college —
   `superadmin_router.py:844-855`); the drawer must therefore populate the branch select from the
   college's own `branches[]` rather than free text.

## Step 10 — Assessments read-only (`/superadmin/assessments`)

1. `getAssessments()` → three sections (`custom_tests`, `custom_attempts`, `assignments`,
   `text.md` §2.8), each a `DataTable` with the columns listed in `text.md` §5.6, all read-only.
2. Empty sections render the standard empty state ("No custom tests recorded yet").

## Step 11 — AI settings (`/superadmin/ai-settings`)

1. `getSystemConfig()` → config form (`text.md` §2.9): `free_daily_chat_cap`,
   `premium_daily_chat_cap` (integers ≥ 0), `mastery_threshold_pct` (0–100),
   `rate_limit_per_minute` (≥ 1), `maintenance_mode` (toggle). Save → `updateSystemConfig` with
   only the five PUT-elitable keys (`passes_for_mastery`, `failures_for_concept_wall`,
   `gemini_model` are returned by GET but rejected by the PUT model — display them read-only).
2. Render `soul_prompt` in a read-only `<pre>` with a copy-to-clipboard button (clipboard write
   only; it is a prompt, not a secret — see `text.md` §9 for what counts as a secret).
3. `audit_logs` table (newest first — the server already inserts at index 0,
   `superadmin_router.py:60-70`): timestamp, actor, action pill, detail. Cap the render at 100.

## Step 12 — Workflow monitoring, four blocked pages

Implement `src/superadmin/pages/monitoring/TestsMonitoring.tsx`, `SubmissionsMonitoring.tsx`,
`AiResultsMonitoring.tsx`, `SchedulesMonitoring.tsx` per `text.md` §5.7:

1. Each page renders: (a) its full UI specification — the `DataTable` columns, `FilterBar`
   fields, and detail-drawer fields from `text.md` §7, so the page is ready to light up the day
   the backend lands; (b) a `BlockingNotice` at the top citing phase-01 §11 gap #8 with the
   matching PROPOSED endpoint row(s) from `text.md` §3.
2. The pages make **no network calls**. They must not fabricate rows. The empty DataTable renders
   the "Waiting for backend endpoint" empty state.
3. A shared `src/superadmin/pages/monitoring/spec.ts` may hold the column/filter/drawer specs to
   avoid duplication.

Guardrail: shipping fake data, seeded demo rows, or a "preview mode" is a phase failure. The
verification of these pages is visual: banner + column headers + empty state.

## Step 13 — Panel layout, states, accessibility

1. `src/superadmin/components/SuperadminPanel.tsx` — the section shell: renders
   `SuperadminSecurityNotice`, the section switcher (same five + five destinations as the AppShell
   nav, driven by the URL), and the active section. Replace the five old routes' element in
   `src/App.tsx` with this layout; keep `SuperAdminPortal.tsx` file in place (referenced by no
   route after this step — delete only if the implementer's own review confirms zero imports;
   otherwise leave it).
2. Every data page implements the four cross-cutting states exactly once (shared skeleton and
   error components are encouraged): loading skeleton (pulsing placeholder rows), error with
   Retry, empty state, and the permission-denied state via `RequireSuperadmin`.
3. Accessibility pass per `text.md` §10: arrow-key row/cell movement in `DataTable` with
   `aria-label`d sort buttons announcing direction via `aria-sort`; `ConfirmDialog` focus trap,
   initial focus on Cancel, Esc closes, `aria-modal`, labeled buttons; all icon-only buttons get
   `aria-label`; forms associate `<label htmlFor>`; banner has `role="alert"`.

## Step 14 — Verification and sign-off

1. `npm run build` — zero TypeScript errors.
2. Run the `expected-output.md` curl verification block (§"API verification") — all green.
3. Walk the browser checklist in `expected-output.md` top to bottom; record results in the gap
   log section there.

Guardrail: if any documented contract differs from observed behavior, the **document** is wrong
only when the code matches phase-01; otherwise record the drift in the phase gap log. Never patch
the backend to make a check pass.
