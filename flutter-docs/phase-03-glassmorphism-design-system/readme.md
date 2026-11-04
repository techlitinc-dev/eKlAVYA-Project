# Phase 03 — Glassmorphism Design System

**Purpose:** Define one design token set and two implementations—Flutter widgets in
`Android_App/lib/core/design_system/` and CSS/Tailwind v4 in `Frontend_Website/`—so later phases
share accessible visuals without re-deciding them.

Glassmorphism is used for hierarchy, not decoration. Readability and contrast always win. Statuses
always pair an icon with a text label.

## Scope

In scope:

- Exact color, blur, elevation, radii, spacing, typography, icon, and motion tokens.
- Flutter `ThemeData`/`ThemeExtension`, reusable widgets, state matrices, semantics, and golden
  tests.
- Flutter `BackdropFilter` with a centralized opaque fallback; web `@supports` fallback.
- Flutter `MediaQuery.disableAnimations`; web `prefers-reduced-motion`.
- Development-only catalogs: a Flutter `/design-system` route and the existing web preview route.
- Web superadmin components required by Phase 12.

Out of scope: production feature screens, backend changes, new npm dependencies, and runtime feature
records in either catalog.

## Real-data boundary

Catalog labels and fixed component-state inputs are visual test fixtures only. They must live in
catalog/test code, never in production repositories or feature pages. `TestQuestionCard`,
`ResultCard`, `AnalysisCard`, and `ScheduleCard` require caller-provided values; production callers
must pass models parsed from real endpoint responses. No component contains default scores,
questions, exams, analytics, schedules, names, or IDs.

## Dependencies

- Phase 01 supplies every backend enum/value set displayed by components.
- Phase 02 supplies the Flutter project, `core/design_system/`, Riverpod, go_router, and web build.

## What this phase contains

- `instructions.md` — Flutter tokens/theme/widgets/catalog/tests, then web tokens/components/build.
- `text.md` — normative tokens, component props, states, accessibility, and performance rules.
- `expected-output.md` — exact-token, catalog, golden-test, accessibility, and real-data checks.

## Guardrails

1. Token values are normative; do not rename or restyle them per screen.
2. Glass appears only over the fixed gradient or opaque fallback, never uncontrolled moving content.
3. No status is communicated by color alone.
4. Blur and motion use the shared capability flags; no per-screen tweaks.
5. Web adds no npm dependencies and changes no existing route except `/design-system`.
6. Compose/Kotlin files and native preview activities are not used.
