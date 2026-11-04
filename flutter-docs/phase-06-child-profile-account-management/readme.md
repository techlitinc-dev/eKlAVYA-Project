# Phase 06 — Child Profile & Account Management

**Purpose:** Let a parent create, view, edit, and delete the real child profile in Flutter. Creating
the profile also creates the child login account and returns the actual backend record.

This phase writes implementation documentation only; an implementer executes it.

## Scope

- `ChildProfileCreatePage`: validated child/academic/credentials form and real POST.
- One-time credentials reveal using only values entered by the parent and the confirmed response.
- `ChildProfileViewPage` / `ChildProfileEditPage`: real GET and PUT for name, age, grade, level.
- Delete confirmation and real DELETE followed by refreshed parent/onboarding state.
- Real `GET /api/onboarding/status` integration.

Out of scope: parent dashboard (P05), child login (P07), and scheduling (P08).

## Dependencies

| Phase | Requirement |
|---|---|
| 02 | Flutter project, feature-first architecture, Riverpod, go_router |
| 03 | Glass widgets and accessible dialog/form components |
| 04 | Dio, active parent Bearer token, isolated sessions, `ApiResult` |
| 05 | Parent navigation and real parent/child resolution |

## Real-data and credential rules

1. Profile fields and onboarding flags come only from endpoint responses or current form input.
2. No fake child profile, fixed child ID, static credential, placeholder account, or locally invented
   creation success. The UI advances only after the real 201 response.
3. One child per parent is backend truth. A second child is not offered or simulated.
4. Passwords exist only in memory for the one-time reveal; never log, persist, cache, or GET them.
5. Username/password updates are silently dropped by the backend (gap #2); reset stays disabled and
   no proposed endpoint is called.
6. Use `parent_id` from the parent session and `child_id` from real responses; always send Bearer.

## Endpoints

`POST/GET /api/onboarding/child`, `PUT/DELETE /api/onboarding/child/{child_id}`, and
`GET /api/onboarding/status`. Exact contracts and source citations are in `text.md`.

## Deliverable files

- `instructions.md` — Flutter DTOs, Dio data source, repository, pages, controllers, tests.
- `text.md` — API JSON, validation, credential security, screen/state specifications, file map.
- `expected-output.md` — live CRUD verification, security checks, real-data audit, gap log.
