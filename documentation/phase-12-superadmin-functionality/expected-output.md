# Phase 12 — Expected Output & Sign-off

## Deliverables of this phase

1. Ten authenticated superadmin routes live in the SPA (plus the login flow), consuming exactly
   the 16 `superadmin`-classified endpoints of phase-01 §9.6.
2. Four workflow-monitoring pages exist and are visibly blocked: `BlockingNotice` citing
   phase-01 §11 gap #8 with the PROPOSED endpoint table from `text.md` §3, spec'd-but-inert
   tables, zero network calls, zero fabricated rows.
3. `LatexRenderer` sanitizes HTML through DOMPurify before `dangerouslySetInnerHTML`.
4. `SuperadminSecurityNotice` renders on every superadmin screen; no panel copy anywhere claims
   the login is secure.
5. Every mutating action writes a local audit entry (`eklavya_superadmin_audit`: who/when/what).

## API verification (run against the live backend)

Backend on `http://localhost:8000`. Each command's observed output must match `text.md` §2.

```bash
# 1. Login succeeds with an arbitrary password (documents gap #8 — banner must say so)
curl -s -X POST localhost:8000/api/superadmin/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@eklavya.ai","password":"literally-anything"}'
# expect 200, status:true, admin_id:"superadmin_root", demo_accounts.parent_id set

# 2. Non-admin email rejected
curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8000/api/superadmin/login \
  -H 'Content-Type: application/json' -d '{"email":"parent_demo_eklavya@x.ai","password":"x"}'
# expect 401

# 3. Overview KPI envelope
curl -s localhost:8000/api/superadmin/overview | python3 -c \
  "import json,sys; d=json.load(sys.stdin); assert d['status'] and len(d['kpis'])==12 and 'pyq_by_subject' in d['distributions']; print('overview OK')"

# 4. Users envelope
curl -s localhost:8000/api/superadmin/users | python3 -c \
  "import json,sys; d=json.load(sys.stdin); p=d['parents'][0]; s=d['students'][0]; \
assert {'plan_id','plan_name','subscription_status'} <= p.keys(); \
assert {'counts','locked_topics','xp','streak_days','badges','weekly_league_points','exam_scope','completion_pct'} <= s.keys(); \
print('users OK')"

# 5. Action round-trip on the demo parent, then restore is NOT required for the demo identity
curl -s -X POST localhost:8000/api/superadmin/users/action -H 'Content-Type: application/json' \
  -d '{"action":"award_xp","target_id":"child_demo_aarav","value":10}'
# expect {"status": true, "message": "Awarded +10 XP to child_demo_aarav"}

# 6. Unknown action → 400 {"detail":"Unsupported action: ..."}
curl -s -X POST localhost:8000/api/superadmin/users/action -H 'Content-Type: application/json' \
  -d '{"action":"delete_everything","target_id":"x"}' | grep -o 'Unsupported action'

# 7. Questions filter contract
curl -s 'localhost:8000/api/superadmin/questions?examId=all&subjectId=physics' | python3 -c \
  "import json,sys; d=json.load(sys.stdin); assert d['status'] and isinstance(d['totalCount'],int); print('questions OK')"

# 8. System-config envelope incl. SOUL prompt + audit logs
curl -s localhost:8000/api/superadmin/system-config | python3 -c \
  "import json,sys; d=json.load(sys.stdin); assert 'soul_prompt' in d and 'audit_logs' in d and 'config' in d; print('config OK')"
```

## Browser verification checklist

- [ ] `/superadmin` (any superadmin URL) while logged in as another role shows
      `PermissionDeniedState`.
- [ ] Login page shows the security warning banner above the form; logging in with
      `admin@eklavya.ai` / any password succeeds and lands on the dashboard.
- [ ] Dashboard: 12 KPI cards render with demo-seeded values; distribution bars; audit table.
- [ ] Users: FilterBar role segment and search work; parent row Grant/Revoke prompts; student
      row Unlock/Trigger prompts; revoke/trigger require typing the target id; Award XP accepts
      a custom positive integer; actions refresh the table and append to the local audit log
      (visible via DevTools → localStorage `eklavya_superadmin_audit`).
- [ ] "Reset credentials" menu item on student rows is disabled with the gap #2 tooltip; no
      network call is made when clicked.
- [ ] Questions: filter bar drives server-side params; creating an MCQ with a blank
      `statementHtml` is blocked by client validation; live preview renders LaTeX; a statement
      containing `<img src=x onerror=alert(1)>` is stripped of `onerror` in the DOM; delete
      requires typing the question id.
- [ ] Content: flashcard create/delete; college branch editor only offers branches present in
      the loaded college.
- [ ] Assessments: three sections render (possibly empty); no crash on unexpected row shapes.
- [ ] AI settings: five editable fields save and reload; three read-only fields present;
      SOUL prompt visible read-only with working copy button; audit-log table renders.
- [ ] Monitoring (4 pages): amber `BACKEND CHANGE REQUIRED` banner citing gap #8 + PROPOSED
      endpoint row; spec'd column headers; "Waiting for backend endpoint" empty state; DevTools
      Network tab shows **no** `/api/superadmin/tests|submissions|analytics|schedules|
      workflow-stats` calls.
- [ ] Accessibility: Tab reaches all interactive elements; sort buttons expose `aria-sort`;
      dialog traps focus, Esc cancels; icon buttons have `aria-label`s.
- [ ] `npm run build` exits 0.

## Demo script (superadmin portion)

1. Log in with `admin@eklavya.ai` (any password) — point out the security banner and state
   plainly that the password is not verified (gap #8).
2. Dashboard: walk the 12 KPIs, distributions, health row, audit trail.
3. Users: search the demo student `aarav_jee2026`; open the drawer; Award +100 XP; observe the
   xp cell update; show the local audit entry; show the disabled "Reset credentials" and its
   gap #2 tooltip.
4. Questions: filter by Physics; create a PYQ with inline LaTeX; show the sanitized live
   preview; delete it with typed confirmation.
5. AI settings: bump `free_daily_chat_cap` 5 → 6, save, reload, show the new value; show the
   server audit log entry `UPDATE_SYSTEM_CONFIG`.
6. Monitoring: open the four pages; show each `BlockingNotice` and explain that tests/
   submissions/AI-results/schedules monitoring is `BACKEND CHANGE REQUIRED` (gap #8), with the
   PROPOSED endpoints displayed on the page.

## Gap log (must be copied into the phase-13 consolidation)

| Gap (phase-01 §11) | Where encountered | Disposition in this phase |
|---|---|---|
| #8 superadmin login has no password verification | Login page, security banner §8 of text.md | Documented; banner rendered; PROPOSED fix recorded in text.md §2.1. No client-side fake auth added. |
| #8 no auth on the other 15 endpoints | All pages (token still sent) | Documented; PROPOSED JWT enforcement recorded in text.md §3. |
| #8 no workflow-domain monitoring (tests/submissions/analytics/schedules) | Four monitoring pages | Pages ship blocked with `BlockingNotice`; PROPOSED P1–P5 contracts in text.md §3; UI specs ready in text.md §7. |
| #2 no child credential reset | Users page student drawer | Control ships disabled with tooltip; PROPOSED `reset_child_credentials` action recorded in text.md §2.4. |
| (hardening, unnumbered) LatexRenderer XSS | Questions/flashcards rendering | Fixed panel-side with DOMPurify (instructions Step 3); server-side sanitization recommended to backend team. |

## Sign-off rule

All checklist items green and the gap log copied into phase-13's release checklist → this phase
is complete. Any drift between this documentation and the running backend is recorded above
before sign-off; the backend is never modified to force a pass.
