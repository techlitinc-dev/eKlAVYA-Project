# Phase 13 — Expected Output & Sign-off (Final Release Checklist)

## Deliverables of this phase

1. Security audit findings recorded for both clients (instructions Steps 1–2); every `text.md`
   §1 item ticked with evidence (file path or test name).
2. All test suites executed with results; coverage gate report attached.
3. The 14-step E2E matrix filled (PASS / BLOCKED(gap #n) / FAIL-with-note) for the default
   backend run, plus a backend-fixed run for steps 8–10 when available.
4. Traceability re-check signed (§"Traceability").
5. Consolidated gap log below copied from all phases.

## Release checklist

### A. Cross-phase completion (gate: all green)

- [ ] Phases 01–11 checklists green (per each phase's `expected-output.md`).
- [ ] Phase 12 checklist green (10 routes, blocked monitoring pages, DOMPurify, banner, local
      audit, a11y pass).
- [ ] Phase 13 items B–E below green.

### B. Security gate

- [ ] T1–T6 token handling verified (Keystore at rest; role-scoped attach; refresh-once; no
      token in logs/UI).
- [ ] S1–S5 session separation verified; instrumented isolation test green.
- [ ] LogSanitizer in place on both clients; CI grep for raw `Log.`/`console.*` clean.
- [ ] §1.4 authorization table delivered to the backend team (tracked as pre-production
      blockers, gaps #7/#8/#9); client 401/403 handling implemented per §1.4.
- [ ] Secrets scan: `grep -rn "AIza\|BEGIN PRIVATE KEY\|JWT_SECRET" Android_App/
      Frontend_Website/` → no server secrets.
- [ ] Cert pinning present in release flavor (recommendation §1.6).
- [ ] Panel: DOMPurify sanitize asserted by test; no-secret-display grep clean; security banner
      on all superadmin screens; monitoring pages fetch nothing.

### C. Test gate

- [ ] `./gradlew test` — all unit + MockWebserver integration tests pass.
- [ ] `./gradlew connectedDebugAndroidTest` — device/emulator tests pass, including the five
      critical: registration validation; child login wrong-credentials; runner timer
      autosubmit; submission duplicate-guard; session isolation.
- [ ] JaCoCo line coverage ≥ 70% on `data/` + ViewModels (report path recorded).
- [ ] `cd Frontend_Website && npm test` — vitest suites 1–7 of `text.md` §2.6 pass.
- [ ] `cd Backend && pytest -q` result recorded (informational; failures logged, not fixed).

### D. E2E verification matrix (14 rows)

| # | Step | Result (PASS / BLOCKED / FAIL) | Evidence (screenshot/log/test) | Blocker (gap #) |
|---|---|---|---|---|
| 1 | Parent register → verify → login | | | |
| 2 | Create child profile | | | |
| 3 | Child account exists; immediate login | | | |
| 4 | Parent schedules test | | | |
| 5 | Child login on child screen | | | |
| 6 | Child sees assigned test | | | |
| 7 | Open/complete/submit test | | | #4 (501) unless backend-fixed run |
| 8 | Backend processes submission | | | #4 unless backend-fixed run |
| 9 | AI analysis trigger + poll | | | — |
| 10 | Schedule generation | | | #6 unless backend-fixed run |
| 11 | Child views results + schedule | | | follows 9/10 |
| 12 | Parent views status/analysis/schedule | | | #6 partial |
| 13 | Session separation | | | #7 (client-scoping mode today) |
| 14 | Superadmin monitoring | | | #8 (4 pages blocked) |

Run mode recorded here: default backend / backend-fixed / mixed. Client commit hashes at
sign-off: Android `__________`, web `__________`.

### E. Traceability

- [ ] §4.1 mapping walked; every android (62) and superadmin (16) endpoint integrated in exactly
      one phase; no double-integration; unused/web/internal untouched.
- [ ] §4.2 screen-coverage matrix walked; every phase screen has ≥1 covering test; no empty
      cells.

## Consolidated gap log (copy of record)

| Gap (phase-01 §11) | Status at sign-off | Where visible |
|---|---|---|
| #1 child plaintext passwords | Open — backend | Never logged client-side; show-once UX |
| #2 no child credential reset | Open — backend | Disabled control + tooltip (P12) |
| #3 no parent password reset | Open — backend | No reset UI shipped |
| #4 mock diagnostic-test lifecycle | Open — backend | E2E steps 7–8 blocked on default backend |
| #5 synchronous analytics under 202/poll contract | Open — backend (contract-safe) | Step 9 note |
| #6 collection-name mismatches (schedule + parent dashboard) | Open — backend | E2E step 10 blocked; step 12 degraded |
| #7 no authorization enforcement | Open — backend (pre-production blocker) | Step 13 client-scoping mode; §1.4 checklist |
| #8 superadmin: unauthenticated, no password check, no workflow monitoring | Open — backend (pre-production blocker) | P12 banner + blocked pages; step 14 |
| #9 silent password-check skip without FIREBASE_API_KEY | Open — backend | §1.8 |
| #10 question_router unmounted | Open — backend (no client impact) | phase-01 §11 |
| #11 duplicate /api/diagnostic-test routers | Open — backend (client uses diagnostic-router surface) | phase-01 §11 |
| #12 dead config keys | Open — backend (no client impact) | phase-01 §11 |

## Sign-off rule

All A–E boxes checked; matrix filled; gap log copied. Remaining open items are exclusively the
backend gaps above — the clients ship behind their documented banners, blocked states, and
client-side scoping. Any new drift discovered during this phase is appended to this log and to
phase-01 §11 before sign-off.
