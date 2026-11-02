# Phase 01 — Repository Analysis & Endpoint Inventory

**Purpose:** This is the anchor phase of the documentation set. Every later phase (02–13) cites
the facts established here. Nothing in this phase writes application code; it produces the
verified source-of-truth that the Android app and superadmin implementations are built against.

**Inspected source of truth**

| Item | Value |
|---|---|
| Repository | `https://github.com/techlitinc-dev/eKlAVYA-Project` |
| Branch | `main` |
| Inspected commit | `d8ab4917480c90a7c5c663f7fe6e8a726ce490f4` (2026-11-02, "Add communication, mindmap, notes, planner, scan, speech, and syllabus modules with tests") |
| Analysis date | 2026-11-02 |
| Backend | FastAPI (`Backend/`), Python, app title "Mentor AI Backend" v1.0.0 |
| Existing web app | React 19 + Vite + TypeScript + Tailwind v4 (`Frontend_Website/`) |
| Android app | **Empty** — `Android_App/` contains only `.gitkeep`. All Android work is greenfield. |
| Superadmin app | **No dedicated code** — `Super_Admin/` contains only `README.md`; the superadmin UI currently lives inside `Frontend_Website/src/pages` (`SuperAdminPortal`). |

## How this documentation set is organized

Every phase directory contains exactly four files with fixed semantics:

| File | Semantics |
|---|---|
| `readme.md` | What the phase delivers, its scope, dependencies on other phases, and source references. Read first. |
| `instructions.md` | Sequential, numbered implementation steps for the implementer (intern or coding model). Each step is small, explicit, and verifiable. Guardrails state what **not** to do. Anything the backend does not support is marked `BACKEND CHANGE REQUIRED` — never worked around silently. |
| `text.md` | Reference material for the phase: exact API contracts, request/response JSON, enums, state machines, file paths, and citations into the repository (`path/file.py:line`). |
| `expected-output.md` | Acceptance criteria, verification commands, test checklists, and demo scripts that prove the phase is complete. |

**Golden rules for the implementer (apply to all phases):**

1. Never invent an endpoint, field, role, or response shape. If it is not in `text.md` of the
   relevant phase (or in this phase's endpoint inventory), it does not exist.
2. If a required behavior is missing or broken in the backend, mark it `BACKEND CHANGE REQUIRED`
   exactly where it is encountered, implement nothing against the missing behavior, and record it
   in the phase's `expected-output.md` gap log. The consolidated backend-change list lives in
   `phase-01-repository-analysis-endpoint-inventory/text.md` §11.
3. Parent sessions and child sessions are separate tokens, separately stored, never shared
   (see `text.md` §6 of this phase for the token formats).
4. The Android app consumes **only** endpoints classified `android` in the inventory below.
   The superadmin panel consumes **only** endpoints classified `superadmin`. Anything classified
   `web`, `internal`, `unused`, or `unsafe` must not be called by these clients.

## What this phase contains

- `text.md` — full repository analysis: architecture, both auth systems, storage layers,
  conventions (IDs, timestamps, pagination, error envelopes), every workflow traced through
  route → service → model, the complete endpoint inventory (~295 mounted endpoints, each with
  Endpoint / Purpose / Auth / Input / Validation / Success / Errors / Consumer / UI feature /
  Phase / Source), and the consolidated `BACKEND CHANGE REQUIRED` list.
- `instructions.md` — how to reproduce this analysis and verify the inventory against the live
  OpenAPI spec.
- `expected-output.md` — the endpoint traceability check: every router accounted for, every
  endpoint either consumed by a phase or explicitly classified with a reason.

## Dependents

Phases 02–13 all depend on this phase. Do not start them until this phase is verified.
