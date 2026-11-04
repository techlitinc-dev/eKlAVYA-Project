# Phase 01 — Expected Output & Sign-off

## Deliverables of this phase

1. `text.md` contains: repository analysis (§1–§8), the complete endpoint inventory with all
   eleven required fields per endpoint (§9), the endpoint traceability check (§10), the
   consolidated `BACKEND CHANGE REQUIRED` list (§11), and seed identities (§12).
2. `instructions.md` lets anyone re-verify the analysis against the live server.

## Verification checklist

- [ ] `git log -1` prints `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`.
- [ ] `Android_App/` and `Super_Admin/` confirmed to contain no application code.
- [ ] Backend boots via `./run.sh backend`; `GET /health` responds.
- [ ] Live `/api/openapi.json` path list matches §9 (modulo the documented question_router absence).
- [ ] Every router in `Backend/routers/` appears in §9 or §10.
- [ ] Every endpoint row carries: Endpoint, Purpose, AuthN, AuthZ, Input, Validation, Success,
      Errors, Consumer, UI feature, Phase, Source.
- [ ] §10 accounts for all 285 listed endpoints (279 mounted + 6 unreachable); per-router row
      counts were mechanically counted from the §9 tables.
- [ ] Flutter-consumed set = 59 endpoints; superadmin set = 16 (`demo-session` excluded).
- [ ] §11 lists every gap encountered later in phases 04–13 (16 items), each with file:line evidence.

## Traceability summary (must match §10)

| Classification | Count | Where integrated |
|---|---|---|
| flutter (consumed by Flutter app) | 59 | Phases 04–11 |
| superadmin (consumed by superadmin panel) | 16 | Phase 12 |
| web (existing Frontend_Website; not re-documented) | 65 | — |
| internal (health, RAG, v1 playground, seeding) | 108 | — |
| unused (shadowed, unmounted, mock, or out-of-workflow) | 37 | — |

## Sign-off rule

A later phase may be started only when every box above is checked. If the running backend
disagrees with this document, fix the document and record the drift; if the drift is a genuine
backend defect, append it to §11 with file:line evidence.
