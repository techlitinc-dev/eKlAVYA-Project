# Phase 06 — Expected Output & Sign-off

## Deliverables

Flutter child create, one-time credentials reveal, view, edit, delete, and onboarding integration
using real parent-scoped endpoints.

## Verification checklist

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] Exact DTO/request coverage exists for E1–E5.
- [ ] Every validation rule blocks invalid input before submission.
- [ ] Create success requires actual 201; one-child 400 and other errors show no success page.
- [ ] Credentials appear once only after creation and are never logged/persisted.
- [ ] View/edit use real GET/PUT values; username/password are never updated.
- [ ] Delete requires typed confirmation and real success before state invalidation/navigation.
- [ ] Onboarding/dashboard refresh from real endpoints after create/edit/delete.
- [ ] Parent session survives all child-profile operations.
- [ ] Semantics, errors, focus, and touch targets pass accessibility checks.

## Real-backend demo

Create a child through the UI, verify the returned record with GET, edit supported fields and verify
PUT/GET, then delete and verify subsequent GET/onboarding behavior. Use a parent created through the
real registration endpoint and scrub credentials from evidence.

## Real-data audit

- [ ] No fixed child ID/profile/account/credentials or local creation-success fallback.
- [ ] Form values and endpoint responses are the only displayed data sources.
- [ ] Gap #2 reset remains disabled; proposed endpoint is never called.
- [ ] Errors do not leave fabricated profile or onboarding state.

## Gap log

| Gap | Handling |
|---|---|
| #1 plaintext child password | Memory-only reveal; no logging/persistence |
| #2 credential reset dropped | Disabled row with honest explanation |
| #7 ownership/auth bypass | Parent Bearer and session/response-derived IDs |

Sign off only after the real CRUD flow and security audit pass.
