# Phase 12 — SuperAdmin Functionality

**Purpose:** Deliver the superadmin governance panel inside the **existing** React 19 + Vite +
TypeScript + Tailwind v4 SPA (`Frontend_Website/`). This phase consumes all 16 endpoints of
`Backend/routers/superadmin_router.py` (prefix `/api/superadmin`, phase-01 §7.I and §9.6), extends
the existing `SuperAdminPortal` page, and specifies — but does not implement against — the
workflow-monitoring surface the backend lacks (`BACKEND CHANGE REQUIRED`, phase-01 §11 gap #8).

**This phase writes documentation only. No application code is written by this document's author;
an implementer (intern or coding model) executes `instructions.md`.**

## Source references (verified)

| Item | Value |
|---|---|
| Backend router | `Backend/routers/superadmin_router.py` (898 lines; every contract in `text.md` was read directly from this file, not inferred) |
| Existing panel | `Frontend_Website/src/pages/SuperAdminPortal.tsx` (939 lines, 5 tabs) |
| Router shell | `Frontend_Website/src/App.tsx` (superadmin routes at `:117-157`), `Frontend_Website/src/components/AppShell.tsx` (superadmin nav at `:73-79`) |
| HTTP layer | `Frontend_Website/src/lib/api.ts` (axios instance + `apiFetch`; Bearer interceptor at `:13-19`) |
| Session layer | `Frontend_Website/src/context/AuthContext.tsx` (`UserSession`, `eklavya_token`/`eklavya_user` localStorage keys) |
| LaTeX renderer | `Frontend_Website/src/components/LatexRenderer.tsx` (unsanitized `dangerouslySetInnerHTML` at `:61-62`) |
| Anchor phase | `flutter-docs/phase-01-repository-analysis-endpoint-inventory/` — §7.I (superadmin trace), §9.6 (16-endpoint inventory), §11 (gap list), §12 (demo identities) |

## Fixed decisions (binding for this phase)

1. **No new framework.** Work extends `Frontend_Website/` (React 19, react-router-dom v7, axios,
   Tailwind v4, Vite 6, TS 5.6 — `Frontend_Website/package.json`). No Next.js, no new state
   library, no component kit beyond what is listed below.
2. **Token storage.** Session tokens and user objects live in `localStorage` under `eklavya_token`
   and `eklavya_user`, written/read exactly as `Frontend_Website/src/context/AuthContext.tsx:54-75`
   already does. The axios interceptor in `src/lib/api.ts:13-19` already attaches the Bearer
   token; reuse it, do not duplicate it.
3. **HTTP client.** All panel calls go through the shared axios instance exported from
   `src/lib/api.ts:6-11` (base URL `import.meta.env.VITE_API_BASE_URL`, default
   `http://localhost:8000` — `src/lib/api.ts:3-4`).
4. **Design system.** Visual language comes from the phase-03 web glassmorphism set: tokens
   (`--color-primary`, `--color-medical`, `--color-wall`, `--color-danger`, `--color-review`,
   `--heatmap-0..4`, dark slate glass surfaces) and shared components `DataTable`, `FilterBar`,
   `ConfirmDialog`, `StatusPill`, `PermissionDeniedState`. The current portal's slate palette
   (`bg-slate-950/900/800` glass cards, amber governance accent) is preserved; tokens map onto it
   as documented in `text.md` §6.
5. **Endpoint discipline.** The panel consumes **only** the 16 endpoints classified `superadmin`
   in phase-01 §9.6, plus the `POST /api/superadmin/demo-session` switcher already used by the
   existing shell (classified `internal` — kept, not expanded). It never calls `web`-classified
   endpoints.
6. **Honesty rule.** Anything the backend does not provide is specified as `BACKEND CHANGE
   REQUIRED` with a clearly labeled **PROPOSED** contract. Missing features are never presented as
   existing, never mocked silently, and every blocked page renders the real `BlockingNotice`
   component (not a fake table of fabricated data).

## What this phase contains

- `instructions.md` — sequential implementation steps: shared infrastructure, then the 10 routes,
  then the blocked workflow-monitoring pages, then hardening (DOMPurify, security banner, local
  audit log).
- `text.md` — the reference: exact request/response JSON for all 16 endpoints (verified line by
  line against `superadmin_router.py`), the PROPOSED endpoint table for gap #8, full UI specs per
  screen, accessibility requirements, and the security warning banner specification.
- `expected-output.md` — acceptance criteria, verification commands (curl + browser walkthrough),
  the demo script, and the phase gap log.

## Security posture (stated plainly, per phase-01 §11 gap #8)

- The superadmin login **does not verify any password** today: any email containing the substring
  `admin` receives a valid JWT (`superadmin_router.py:413-421`). The panel must display the
  `SuperadminSecurityNotice` warning banner on every superadmin screen, must never describe the
  login as secure, and `text.md` documents the PROPOSED password-verification fix.
- None of the 16 endpoints checks authentication. The panel still sends the Bearer token (so the
  backend can enforce it once gap #8 lands) and documents the requirement.
- Passwords, tokens, and secrets are never displayed anywhere in the panel (hard rule, `text.md` §9).

## Dependencies and dependents

- Depends on Phase 01 (endpoint truth), Phase 02 (existing axios/localStorage conventions), Phase 03
  (shared web tokens/components), and Phase 04 (backend error-envelope semantics). The Flutter app
  uses separate secure storage; it does not share the web panel's localStorage session.
- Phase-13 (security & E2E verification) depends on this phase: it executes the panel test plan
  and the superadmin steps of the end-to-end demo script.
