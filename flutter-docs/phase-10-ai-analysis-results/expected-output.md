# Phase 10 — Expected Output & Sign-off

## Deliverables

Flutter child analysis trigger, bare-report polling, processing states, shared real report widgets,
and child/parent results viewers.

## Automated checks

- [ ] `flutter analyze` and `flutter test` pass.
- [ ] Generate/poll/history/insights/weak-topics requests match exact contracts.
- [ ] Poll decodes bare `AnalyticsReport`; no nonexistent status/progress wrapper is required.
- [ ] 202→200, 404→200, timeout, 500, malformed report, and retry transitions pass.
- [ ] Progress remains indeterminate; no server stage/percent is invented.
- [ ] Child triggers with real answers; parent has read-only behavior.
- [ ] Report widgets/charts render response values with text equivalents and empty enrichment states.
- [ ] Real IDs, accessibility, and session expiry are covered.

## Required demos

Current backend: document real Firestore/configuration errors and confirm failure/retry UI contains
no report. Backend-fixed environment: submit actual test answers, generate, poll, and compare every
report/insight/weak-topic field with endpoint JSON for child and parent viewers.

## Real-data audit

- [ ] No static analytics ID, score, report, topic, insight, chart, progress percent, or fallback AI
      text exists in production code.
- [ ] Empty/failed calls never produce local analysis.
- [ ] Any offline report is a labelled previously successful response.

## Gap log

| Gap | Handling |
|---|---|
| #4 missing persisted test/questions | Surface real generate failure |
| #5 synchronous pipeline under 202 | Keep contract-safe polling; no fake job data |
| #7 missing auth/ownership | Send role Bearer and real scoped IDs |
| Bare poll response / placeholder test endpoint | Decode actual bare report; do not consume placeholder |

Sign off only when current errors and applicable real end-to-end results are verified.
