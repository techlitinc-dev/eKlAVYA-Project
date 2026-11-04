# Phase 05 — Parent Registration, Login & Dashboard

**Purpose:** Deliver the parent experience in Flutter: role selection, registration, email/phone
verification, login/session restore, dashboard, weekly report, goals, settings, and the Phase 10
results entry.

Backend authority is Phase 01 plus `simple_register_router.py`, `auth_router.py`,
`verification_router.py`, `login_router.py`, and `parent_dashboard_router.py` with their services
and models at inspected commit `d8ab491`.

## Fixed Flutter decisions

- Native ID `ai.eklavya.app`; Dart/Flutter, Riverpod, Dio, go_router, `json_serializable`.
- Phase 04 is the only auth/session path. This phase adds real parent/onboarding remote data sources
  and repositories, not another HTTP or session stack.
- Parent and child sessions remain separate. Switch-to-child opens child login without reusing the
  parent token.
- Phase 03 widgets/tokens are mandatory.
- Base URL comes from `--dart-define=EKLAVYA_BASE_URL`.

## Real-data rule

Every profile, onboarding flag, child ID, dashboard metric, weekly report, goal, notification setting,
and results list comes from its documented endpoint. No hardcoded parent/child, score, weak area,
goal, report, notification state, or demo dashboard. Loading, genuine empty, error, and documented
backend-gap states remain content-free. Offline cache, where used, contains only prior successful
responses and is labelled stale.

## Scope

Flutter pages/controllers for Welcome, ParentRegister, VerifyEmail, VerifyPhone, ParentLogin,
ParentDashboard, WeeklyReport, Goals, Settings, and ParentResults entry; go_router parent branch;
session restore; validation; real request/error states; and integration tests against the backend.

## Endpoints consumed

| Endpoint | Screen/use |
|---|---|
| `POST /api/auth/register/simple` | Primary parent registration |
| `POST /api/auth/register/parent/email` / `/phone` / `/google` | Optional documented alternates |
| `POST /verify/email/send` / `/confirm` | Email verification |
| `POST /verify/phone/send` / `/confirm` | Phone verification |
| `POST /api/auth/login/email` (+ documented phone/Google) | Parent login |
| `GET /api/auth/me`, `POST /api/auth/logout` | Restore/profile/logout |
| `GET /api/onboarding/status?parent_id=` | Real onboarding state |
| `GET /api/onboarding/child?parent_id=` | Resolve the parent's child |
| `GET /api/parent/dashboard/{child_id}` | Dashboard |
| `GET /api/parent/reports/weekly/{child_id}?week_start=` | Weekly report |
| `GET`/`POST /api/parent/goals/{child_id}`, `PUT /api/parent/goals/{child_id}/{goal_id}` | Goals |
| `GET`/`PUT /api/parent/notifications/settings` | Settings |

## Backend realities

1. Registration returns no token; successful registration routes to real login.
2. Backend permits one child per parent; do not fabricate a multi-child selector.
3. Parent profile keys vary by registration method; DTOs accept all documented variants.
4. Development verification codes may appear in responses but production never depends on them.
5. Gap #3: no forgot-password endpoint. Show only an honest unavailable state; never simulate reset.
6. Gap #6 can leave dashboard weak areas/score empty. Render the real response/empty state, not
   invented analytics.
7. Gap #7: always use session-derived IDs and Bearer tokens.

## Dependents

Phase 06 reuses child resolution and parent navigation; Phase 08 consumes dashboard actions; Phase
10 supplies the results screen.

## Files

`instructions.md` gives ordered Flutter steps; `text.md` retains exact contracts, screens, state
machines, accessibility, and gaps; `expected-output.md` defines live verification and sign-off.
