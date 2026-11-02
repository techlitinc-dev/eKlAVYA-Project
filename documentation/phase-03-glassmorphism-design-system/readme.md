# Phase 03 — Glassmorphism Design System

**Purpose:** Define exactly one design token set and one component library with two
implementations — Jetpack Compose (Android app, `Android_App/.../core/designsystem`) and
CSS/Tailwind v4 (superadmin panel, `Frontend_Website`) — so that every later phase (04–13)
renders identical, accessible UI without re-deciding visuals.

**Design stance:** glassmorphism is used for hierarchy, not decoration. Readability and contrast
always win: translucent surfaces are rendered **only** over the fixed app gradient background,
body text never sits on uncontrolled imagery, and every status signal pairs an icon with a text
label (never color alone).

## Scope

In scope:

- Design tokens (color, blur, elevation, radii, spacing, typography, icons, motion) with exact
  names and values, mapped to Kotlin constants and Tailwind v4 `@theme` CSS variables using the
  same names.
- Reusable components with anatomy, state matrices (default / pressed / focused / selected /
  disabled / loading / success / warning / error), and accessibility requirements.
- Runtime blur fallbacks: Android `RenderEffect` availability + low-end detection; web
  `@supports (backdrop-filter)` + opaque fallback color.
- Reduced-motion support: Android animator-duration-scale flag; web `prefers-reduced-motion`.
- Preview catalogs on both platforms (`ComponentPreviewActivity`, `/design-system` route) used
  by `expected-output.md` for sign-off.

Out of scope: feature screens (phases 05–11, 12), backend work, new npm dependencies
(Tailwind v4 CSS-first tokens only; the Inter web font is already the base font in
`Frontend_Website/src/index.css:1-9`).

## Dependencies

- Phase-01: status enums and value lists that the components display come only from the backend
  inventory (test status, schedule status, analytics priority/performance levels — cited in
  `text.md` §9).
- Phase-02: the Gradle project, `core/designsystem/` package, Hilt wiring, and the Vite/Tailwind
  pipeline must already build.

## What this phase contains

- `instructions.md` — Android steps (token files, theme, glass modifiers with fallback,
  one step per component file, preview catalog + screenshot) then web steps (`tokens.css` with
  `@theme`, `src/components/glass/*` components, `/design-system` preview route, contrast and
  reduced-motion checks). Every step ends with a verification command.
- `text.md` — the token tables (exact values), per-component specs with props and state
  matrices, do/don't rules, the WCAG 2.1 AA accessibility matrix, and performance rules.
- `expected-output.md` — the acceptance checklist (token values match exactly; catalogs render;
  contrast spot-check passes; reduced-motion verified; every listed component exists in every
  listed state).

## Guardrails

1. Token names and values are normative. Later phases reference the names in this file; do not
   rename or restyle.
2. Never place a glass surface over content that moves or that the app does not control; the
   only valid backdrop is the fixed three-stop gradient (or the opaque fallback color).
3. No status may be communicated by color alone — icon + label is mandatory.
4. Blur is opt-out only via the documented runtime fallbacks; do not add per-screen blur tweaks.
5. Web work adds no npm dependencies and changes no existing routes except adding the
   `/design-system` preview route.
