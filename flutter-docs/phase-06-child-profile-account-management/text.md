# Phase 06 — Child Profile & Account Management (text.md)

Reference material. Every claim cites `path/file.py:line` in the backend at commit
`d8ab4917480c90a7c5c663f7fe6e8a726ce490f4`. The canonical conventions (IDs, timestamps,
error envelopes, two pagination systems, auth modes) are defined in phase-01 `text.md`
§4 and §6 — they apply here unchanged.

---

## 1. Endpoints consumed in this phase

| # | Endpoint | Method/Purpose | Success | Source |
|---|---|---|---|---|
| E1 | `/api/onboarding/child?parent_id=` | POST — create child profile **and** child login account | 201 `ChildProfileResponse` | `routers/child_router.py:41-161` |
| E2 | `/api/onboarding/child?parent_id=` | GET — fetch the parent's child profile | 200 `ChildProfileResponse` / 404 | `routers/child_router.py:164-259` |
| E3 | `/api/onboarding/child/{child_id}?parent_id=` | PUT — update profile fields | 200 `ChildProfileResponse` | `routers/child_router.py:262-378` |
| E4 | `/api/onboarding/child/{child_id}?parent_id=` | DELETE — delete child profile | 200 dict / 403 / 404 | `routers/child_router.py:381-478` |
| E5 | `/api/onboarding/status?parent_id=` | GET — onboarding checklist flags | 200 `Dict[str, bool]` | `routers/exam_router.py:492-630` |

Router prefix `/api/onboarding` (`child_router.py:35-38`). AuthN: `?parent_id=` query
param; the testing bypass returns the constant string `"test_parent_123"`
(`middleware/testing_auth.py:20-42`) so the header is ignored in the default dev backend
(phase-01 §6.1). **The app must still send `Authorization: Bearer <parent token>` from the
phase-04 `SessionManager` and must take `parent_id` from its own parent session.**

## 2. E1 — Create child profile (POST /api/onboarding/child)

### 2.1 Request body — `ChildProfileRequest` (`models/child_models.py:22-265`)

| Field | Type | Rule | Enforcement |
|---|---|---|---|
| `name` | string | 2–100 chars; stripped; not blank/whitespace-only after strip | `child_models.py:48-53`, `:88-116` |
| `age` | int | 14–19 inclusive | `child_models.py:55-60`, `:118-139` |
| `grade` | int | 9–12 inclusive | `child_models.py:62-67`, `:141-162` |
| `current_level` | enum string | exactly `beginner` \| `intermediate` \| `advanced` | `child_models.py:69-72`, `:164-186` |
| `username` | string | 3–30 chars after strip; regex `^[a-zA-Z0-9_@.]+$` (letters, digits, `_`, `@`, `.`) | `child_models.py:74-79`, `:188-221` |
| `password` | string | 8–50 chars; ≥1 letter `[a-zA-Z]`; ≥1 digit `[0-9]` | `child_models.py:81-86`, `:223-252` |

Violation of any rule → HTTP **422** (`VALIDATION_ERROR`; body `{"detail": ...}` per the
legacy envelope, phase-01 §4). The app must reproduce these rules client-side so errors are
inline and pre-submit.

### 2.2 Server-side behavior (`services/child_service.py:119-210`)

1. **One-child rule.** If the parent already has a `children` doc → 400,
   detail `"Parent can only have one child profile. Delete existing profile to create a new one."`
   (`child_service.py:122-128`). The app must surface this as a navigational hint
   ("You already have a child profile — manage it") rather than a form error.
2. **Firebase Auth user is created** with email `f"{username}@mentor-ai.local"` — or the raw
   username if it already contains `@` (`child_service.py:133-137`) — and the supplied
   password (`:140-146`). Duplicate email → 400
   `"Username '<username>' is already taken. Please choose a different username."`
   (`:148-153`). This 400 is **not** listed in the router docstring; handle HTTP 400 on this
   call with both messages.
3. **Firestore write.** `child_id = "child_" + uuid4().hex[:12]` (`:159`); doc fields:
   `child_id, parent_id, firebase_uid, name, age, grade, current_level, username, email,
   password, created_at, updated_at` (`:162-175`). **The `password` field is written in
   plaintext (`:172`, comment "In production, this should be hashed") — gap #1.**

> **Therefore: in this backend, creating the child profile DOES create the child's login
> account**, with the username and the exact password the parent supplied. State this in the
> UI copy. The response never echoes the password — the app already holds it from the form.

### 2.3 Response — 201 `ChildProfileResponse` (`models/child_models.py:268-359`)

```json
POST /api/onboarding/child?parent_id=<parent-id>
{"name":"Aarav Sharma","age":16,"grade":11,"current_level":"intermediate","username":"aarav_jee2026","password":"Passw0rd1"}
→ 201
{"child_id":"child_abc123def456","parent_id":"<parent-id>","name":"Aarav Sharma","age":16,"grade":11,"current_level":"intermediate","username":"aarav_jee2026","created_at":"2026-11-02T10:30:00Z","updated_at":"2026-11-02T10:30:00Z"}
```

Field order and names are fixed: `child_id, parent_id, name, age, grade, current_level,
username, created_at, updated_at`. **No `password` field exists in the response model.**

## 3. E2 — Get child profile (GET /api/onboarding/child)

- 200 `ChildProfileResponse` (same shape as §2.3). The service reads the first `children`
  doc where `parent_id ==` the query value (`child_service.py:241-270`).
- **404** when absent, detail `"Child profile not found for parent: <parent_id>"`
  (`child_service.py:246-251`). The app treats 404 on this endpoint as "no child yet"
  (empty state → create CTA), not as an error.
- `username` falls back to `""` if the doc predates the field (`child_service.py:267`).

## 4. E3 — Update child profile (PUT /api/onboarding/child/{child_id})

### 4.1 Request body — `ChildProfileUpdate` (`models/child_models.py:362-608`)

All fields optional; each carries the same validator as the create model:
`name` (2–100), `age` (14–19), `grade` (9–12), `current_level` (enum),
`username` (3–30, regex), `password` (8–50, letter+digit).

### 4.2 What the server actually applies — only name/age/grade/current_level

`ChildService.update_child_profile` builds `update_data` from exactly four fields
(`child_service.py:415-428`). `username` and `password` are **silently dropped** — no error,
no effect, Firebase Auth untouched. This is **BACKEND CHANGE REQUIRED** (phase-01 §11
gap #2). Client consequences:

1. The edit form must **not** offer username/password editing bound to this endpoint.
2. Sending `{"username": ...}` or `{"password": ...}` in the PUT body is a silent no-op;
   the app must not pretend it worked. The UI shows the credential reset row as **disabled**
   with the note "Not available yet — backend change required (gap #2)".
3. An empty update object (no applicable field present) → **400** `"No fields provided to
   update"` (`child_service.py:430-436`).

### 4.3 Ownership and errors

- 404 `"Child profile not found: <child_id>"` (`child_service.py:399-404`).
- **403** `"You do not have permission to update this child profile"` when the doc's
  `parent_id` differs from the query param (`child_service.py:406-413`). The app passes the
  `child_id` of its own child (from E2) and `parent_id` from its own session, so 403 should
  be unreachable; treat it as an error state.
- Router quirk: the update handler does not declare the `current_user` dependency but
  references it if `parent_id` is empty (`routers/child_router.py:305-309` vs `:352`), which
  raises `NameError` → 500. **Always send a non-empty `parent_id`** (the app always does,
  from session). Same quirk on E4 (`:453`).
- Response: 200 `ChildProfileResponse` reflecting the merged doc (`child_service.py:446-461`).

## 5. E4 — Delete child profile (DELETE /api/onboarding/child/{child_id})

- Success: **200** `{"message": "Child profile deleted successfully"}` — the service returns
  only the `message` key (`child_service.py:535-537`); the docstring example that also shows
  `child_id` (`child_router.py:414-420`) does **not** match the implementation. Parse
  `message`, do not rely on a `child_id` key.
- 404 (`child_service.py:514-519`), 403 on ownership mismatch (`:521-528`) — same semantics as E3.
- Effect: the `children` doc is removed (`child_service.py:530-531`). Child login queries the
  `children` collection by username (`login_service.py:776-779`), so **after deletion the
  child login stops working**. That sentence is the required consequence text in the delete
  dialog. The Firebase Auth user is **not** deleted (no code path) — a backend defect worth
  noting in the gap log; the app copy must not claim Firebase cleanup happens.

## 6. E5 — Onboarding status (GET /api/onboarding/status)

200 `Dict[str, bool]` (`routers/exam_router.py:492-621`):

```json
{"preferences_completed": true, "child_profile_completed": true,
 "exam_selected": false, "onboarding_complete": false}
```

`onboarding_complete = preferences_completed && child_profile_completed && exam_selected`
(`exam_router.py:605-610`). `child_profile_completed` is derived by attempting E2
(`:585-588`). The app re-fetches this after create/update/delete so the parent dashboard
flags stay correct.

## 7. Credentials security model (CRITICAL)

Backend reality: the child password is stored **plaintext** in Firestore (gap #1,
`child_service.py:172`; compared in plaintext at login, `login_service.py:789-793`). The
app cannot fix this; it must contain exposure:

1. **Show once.** After a successful E1, the app shows username + password on a dedicated
   credentials-reveal step, with explicit copy-to-clipboard and platform share affordances.
2. **Never log.** No debugPrint, crash-report breadcrumb, or analytics event may include the
   password (or the full E1 body). Dio request logging must exclude this body and is off in release.
3. **Never persist.** The password is held only in Riverpod controller memory for the reveal step.
   It is never written to `shared_preferences`, `flutter_secure_storage`, saved state, cache, or the
   parent session. After the user leaves (confirm, back, or process death), it is gone—**no GET
   endpoint returns it**, so it cannot be recovered (E2/E3 responses never contain it).
4. **Reveal step gate.** The reveal step appears only immediately after E1 succeeds. It is
   unreachable from view/edit (there is nothing to reveal). The confirm action
   ("I've saved these") is the only exit and returns to the parent dashboard.
5. Treat credentials as dev-only until gap #1 is fixed (phase-01 §11 #1 says the same).

## 8. Proposed (non-functional) credential-reset contract — BACKEND CHANGE REQUIRED gap #2

What exists today: `ChildProfileUpdate.username/password` accepted but dropped
(`child_service.py:416-428`); no other endpoint touches child credentials. There is **no**
functional reset path.

Target contract (proposal only — phase-01 §11 #2; the backend team owns the final shape):

```
POST /api/onboarding/child/{child_id}/reset-credentials?parent_id=<parent-id>
{"new_password": "<8-50, ≥1 letter, ≥1 digit>"}
→ 200 ChildProfileResponse          (unchanged shape; username untouched)
   400 validation error
   403 parent does not own child
   404 child not found
```

Semantics the proposal assumes: update Firestore `password` (hashed, per the gap #1 fix)
**and** update the Firebase Auth user's password to the same value
(`child_service.py:130-146` shows the Firebase user is created with the profile password;
it must stay in sync). **The platform app must not implement or call this endpoint** until the
backend ships it; the edit screen keeps the disabled reset row.

## 9. Client-side validation rules (mirror of §2.1)

Implement exactly; message strings are UI copy, rule values are contractual.

| Field | Client rule | Inline error (suggested copy) |
|---|---|---|
| name | trimmed length 2–100, non-blank | "Name must be 2–100 characters" |
| age | integer 14–19 | "Age must be between 14 and 19" |
| grade | integer 9–12 | "Grade must be between 9 and 12" |
| current_level | one of 3 enum values (selector, not free text) | n/a (selector) |
| username | trimmed length 3–30; `^[a-zA-Z0-9_@.]+$` | "3–30 characters; letters, numbers, _ @ . only" |
| password | length 8–50; ≥1 letter; ≥1 digit | "8–50 characters with at least one letter and one number" |

Notes: the server strips `name`/`username` before length checks (`child_models.py:105-106`,
`:205-206`) — trim client-side first. `password` is **not** length-capped by a `max_length`
violation path below 8 (`:241`) and the field cap is 50 (`:82-86`). Empty `parent_id` must
never be sent (§4.3).

## 10. Screen specifications

### 10.1 ChildProfileCreate

Sections (single scrollable Flutter form, phase-03 glass components):

1. **Child details** — name field; age field (numeric); grade selector (9–12).
2. **Current level** — three-option selector (`beginner` / `intermediate` / `advanced`);
   single-select cards with descriptions.
3. **Login credentials** — username field; password field with show/hide toggle; helper
   text: "These are the username and password your child will use to log in. You will see
   them once more after the profile is created."

Inline validation per §9 on field blur and on submit; submit enabled only when all rules
pass. On submit: E1 with `parent_id` from the parent session. Success → replace the form
with the **CredentialsRevealStep** (§7.1) showing `username` (from response) and `password`
(from form state). 400 with the one-child message → navigational hint state; 400 with the
username-taken message → inline username error (§2.2); 422 → map `detail` to the matching
field if possible, else a generic banner; 401 → session-expired handling from phase-04;
network error → retry banner.

### 10.2 CredentialsRevealStep (part of the create flow)

- Displays username and password in a secured card; **Copy** button per field (writes to
  clipboard with a "sensitive — clears shortly" hint where the platform supports it) and a
  **Share** button (platform share sheet, user picks the destination).
- Warning line: "This is the only time the password is shown. Save it now."
- Single primary action: **"I've saved these"** → pop back to the parent dashboard.
- No back-navigation restoration of the password: if the user navigates away any other way,
  the in-memory password is cleared.

### 10.3 ChildProfileView / ChildProfileEdit

- Entry: parent dashboard → "Child profile". Loads E2 (parent session `parent_id`).
  404 → empty state with "Create child profile" CTA (routes to §10.1). 401 → phase-04
  re-auth. Other errors → error state with retry.
- View state shows: name, age, grade, current level, username; `created_at`/`updated_at`
  formatted locally.
- Edit mode: name, age, grade, level editable (same §9 rules; PUT E3 with the session's
  `parent_id` and the E2 `child_id`). Success → view state with updated data + refresh E5.
  400 "No fields provided to update" → treat as "nothing changed" (return to view state).
- **Credentials section (view-only):** row "Username" = response `username`; row "Reset
  password" is **disabled** with caption "Coming soon — requires a backend change
  (gap #2)". No password is ever displayed or requested.
- **Delete entry:** destructive row → §10.4.

### 10.4 ChildProfileDelete

- `GlassDialog` (phase-03) with typed confirmation: the parent must type the child's name
  (as returned by E2) to enable the Delete button.
- Consequence text (required): "Deleting this profile is permanent. **Your child's login
  will stop working immediately.** You can create a new child profile afterwards."
- On confirm: E4; 200 → dismiss + navigate to parent dashboard + refresh E5; 403/404 →
  error snackbar + refresh E2 (profile may have changed); network error → keep dialog with
  retry.

## 11. State machines

**ChildProfileCreate** — `Idle(validating per field) → Submitting → Created(credentials) |
Error(422-mapped | 400-one-child | 400-username-taken | 401 | network)`.
Leaving `Created` (by any path) clears the in-memory password and returns to `Idle`.

**ChildProfileView** — `Loading → Empty(404) | Ready(profile) | Error(401 | network | other)`.
`Ready → Editing(dirty) → Saving → Ready(updated) | SaveError(...)`.

**ChildProfileDelete** — `Hidden → ConfirmOpen(typed-name mismatch → button disabled) →
Deleting → Deleted(navigate away) | DeleteError(message, stays open)`.

## 12. Accessibility

- Every form field has a persistent Flutter label/error semantics connection; errors are announced
  through an appropriate live region.
- Level and grade selectors expose single-selection semantics and selected-state descriptions.
- Credentials reveal values are selectable for explicit copy/share actions; buttons are labelled and
  screen-reader order is warning → username → password → actions.
- Delete uses Flutter `AlertDialog` semantics with consequence text read before the typed-name field.

## 13. Files (under `Android_App/lib/`)

| Path | Contents |
|---|---|
| `features/child/data/datasources/child_profile_remote_data_source.dart` | E1–E5 real Dio calls |
| `features/child/data/dto/child_profile_dtos.dart` | Exact request/response/update mirrors |
| `features/child/data/repositories/child_profile_repository_impl.dart` | Real CRUD returning `ApiResult` |
| `features/child/presentation/pages/child_profile_create_page.dart` | §10.1–§10.2 |
| `features/child/presentation/controllers/child_profile_create_controller.dart` | Validation, POST, memory-only reveal |
| `features/child/presentation/pages/child_profile_view_page.dart` | §10.3 real GET |
| `features/child/presentation/pages/child_profile_edit_page.dart` | §10.3 real PUT |
| `features/child/presentation/controllers/child_profile_edit_controller.dart` | Edit state and response handling |
| `features/child/presentation/widgets/child_profile_delete_dialog.dart` | §10.4 `GlassDialog` |
| `router/parent_routes.dart` | `child_profile_create` / `child_profile_view` parent routes |

Both routes require the parent session, are opened by the parent dashboard, and return to it. No
file contains a static child profile, fixed ID, or fabricated CRUD response.
