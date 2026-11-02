# Phase 06 — Expected Output & Sign-off

## Deliverables of this phase

1. `text.md` — verified contracts for E1–E5, the credentials security model, the proposed
   non-functional reset contract (gap #2), validation mirror, screen/state specs.
2. `instructions.md` — ordered build steps for API layer, validator, three screens, and
   navigation.
3. Running app code (built by the implementer from the docs): child create with one-time
   credentials reveal, view/edit, delete dialog — all inside the parent session.

## Verification checklist

### Contracts

- [ ] `POST /api/onboarding/child?parent_id=` is called with body
      `{name, age, grade, current_level, username, password}` and 201 response parsed as
      `ChildProfileResponse` with exactly `child_id, parent_id, name, age, grade,
      current_level, username, created_at, updated_at` (no `password`).
- [ ] Client validation matches `Backend/models/child_models.py:48-252`: name 2–100,
      age 14–19, grade 9–12, level enum, username 3–30 `^[a-zA-Z0-9_@.]+$`, password 8–50
      with ≥1 letter and ≥1 digit.
- [ ] Second create attempt surfaces the one-child 400
      (`child_service.py:122-128`) as a navigational hint, not a crash.
- [ ] Duplicate username surfaces the 400 from `child_service.py:148-153` inline.
- [ ] PUT body contains only `name/age/grade/current_level`; update DTO has no
      username/password fields.
- [ ] `GET /api/onboarding/child` 404 maps to the empty/create state.
- [ ] Delete success parses only `message`; after delete the UI returns to the parent
      dashboard and refreshes `GET /api/onboarding/status`.
- [ ] `parent_id` on every call comes from the parent session; `Authorization: Bearer`
      header attached via phase-04 `SessionManager`.

### Security

- [ ] Credentials reveal step shows username + password once, immediately after create.
- [ ] Copy and Share affordances present on the reveal step.
- [ ] No log statement contains the password; Retrofit/OkHttp logging redacts the E1 body.
- [ ] Password never persisted; leaving the reveal step destroys it.
- [ ] Edit screen shows username only; "Reset password" row is disabled with the gap-2 note.
- [ ] No call is made to the proposed `reset-credentials` endpoint (verified by code search
      for "reset-credentials" returning no call sites).

### States & accessibility

- [ ] Loading / empty(404) / error(401, network, other) / success states present on view.
- [ ] Inline field errors announced (LiveRegion) and associated with fields.
- [ ] Delete dialog requires typed child-name match; consequence text includes
      "Your child's login will stop working immediately."

## Manual demo script

Prereqs: backend running (`./run.sh backend`), app pointing at it
(`EKLAVYA_BASE_URL=http://10.0.2.2:8000`), parent logged in (phase-05), no child yet.

1. Parent dashboard → "Child profile" → empty state shows "Create child profile".
2. Create: enter name "Aarav Sharma", age 16, grade 11, level "intermediate", username
   `aarav_jee2026`, password `Passw0rd1`. Submit.
3. Credentials reveal step appears with the username and password. Copy the password;
   share the username; tap "I've saved these".
4. Backend cross-check:
   ```bash
   curl -s "http://localhost:8000/api/onboarding/child?parent_id=<parent-id>"
   ```
   Expect 200 with the created profile (fields per `text.md` §2.3; no password field).
5. Repeat the create attempt → the one-child 400 is rendered as the "already have a
   profile" panel.
6. Edit: change grade to 12 and level to "advanced"; save; profile reflects both changes;
   `GET /api/onboarding/status` shows `child_profile_completed: true`.
7. Type a wrong value (age 10) → inline error before submit; submit stays disabled.
8. Delete: open dialog, type "Aarav Sharma" (exact), Delete. Dialog closes; dashboard
   refreshed; `GET /api/onboarding/child?parent_id=<id>` now returns 404.
9. Child login check (phase-07 preview): `POST /api/auth/login/child` with the deleted
   child's credentials → 401, proving the login stopped working.
10. Wrong-credential hygiene: with a fresh profile, confirm the reveal step cannot be
    re-opened from view/edit.

## Gap log

| Gap (phase-01 §11) | Where encountered | How this phase handles it |
|---|---|---|
| #1 — child password stored/compared plaintext (`child_service.py:172`, `login_service.py:789-793`) | Create + credentials reveal | Show-once flow; no logging/persistence/re-display; noted as dev-only. |
| #2 — no child credential reset (`child_service.py:416-428`) | Edit screen credential section | Reset row disabled; proposed `POST /api/onboarding/child/{child_id}/reset-credentials` documented as non-functional (`text.md` §8). `BACKEND CHANGE REQUIRED`. |
| #7 — no observable ownership enforcement; auth header ignored in testing mode (`testing_auth.py:20-42`) | All E1–E5 calls | App always scopes by session-derived `parent_id`; sends Bearer header anyway; 403 treated as error state. |
| Backend defect (new observation) — PUT/DELETE handlers reference `current_user` without declaring the dependency (`child_router.py:352`, `:453`) | E3/E4 | Empty `parent_id` → NameError → 500. App never sends empty `parent_id` (session-derived). Logged here for the backend team. |
| Backend defect (new observation) — DELETE docstring claims a `child_id` key the service does not return (`child_router.py:414-420` vs `child_service.py:535-537`) | E4 response parsing | App parses `message` only. Logged here. |
| Backend defect (new observation) — deleted child's Firebase Auth user is never removed (`child_service.py:504-537`) | Delete consequence copy | Copy says login stops working (true: login queries `children`); copy must not claim Firebase-side cleanup. Logged here. |

## Sign-off rule

Every checklist box is checked and the demo script passes end-to-end before phase-07
starts. Any backend drift found during implementation is added to the gap log above, with
`path:line` evidence, and — if it is a genuine backend defect — flagged
`BACKEND CHANGE REQUIRED` with the phase-01 §11 gap number it belongs to (or recorded as a
new observation, as above).
