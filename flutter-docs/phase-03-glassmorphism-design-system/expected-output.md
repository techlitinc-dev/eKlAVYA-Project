# Phase 03 — Expected Output & Sign-off

## Deliverables

1. Flutter `core/design_system/` contains the full token set, theme, glass surface/background, all
   shared components, and a development-only catalog with golden tests.
2. Web exposes equivalent Tailwind v4 tokens, glass utilities, all components, and `/design-system`.
3. Contrast, semantics, keyboard/focus, touch targets, reduced motion, and blur fallback pass.
4. Neither components nor catalogs provide fabricated runtime feature data.

## Verification checklist

### Token exactness

- [ ] Colors match `text.md` §2.1, including all ARGB alpha values and `GlassFallbackSolid #1B2547`.
- [ ] Blur is 8/16/24; elevations are 2/6/12 with black at 30%.
- [ ] Radii are 8/16/24/32 and spacing is 4/8/12/16/24/32/48.
- [ ] Typography is Display 32/40 Bold, H1 24/32 SemiBold, H2 20/28 SemiBold, Body 16/24 Regular,
      BodySmall 14/20 Regular, Caption 12/16 Medium, Button 14/20 SemiBold.
- [ ] Motion is 150/250/400 ms and reduced-motion behavior works on Flutter and web.
- [ ] CSS variables map one-to-one to Dart token semantics.

### Flutter

- [ ] `cd Android_App && flutter analyze && flutter test` succeeds.
- [ ] `flutter test test/core/design_system` passes all widget and golden tests.
- [ ] Catalog renders every component/state on blur-capable and fallback configurations.
- [ ] `BackdropFilter` affects only the backdrop; text and icons remain crisp.
- [ ] `MediaQuery.disableAnimations` produces static skeletons and instant component transitions.
- [ ] `/design-system` is unavailable in release configuration.
- [ ] Long lists use opaque rows without per-row blur.

### Web

- [ ] `npm run build` succeeds in `Frontend_Website`.
- [ ] All components listed in `instructions.md` Step 13 exist.
- [ ] `/design-system` renders every component and state toggle.
- [ ] Icon-only controls have `aria-label`; sortable headers have `aria-sort`; errors use alerts.
- [ ] No npm dependency was added.

### Accessibility

- [ ] `TextPrimary` and `TextSecondary` meet contrast targets on gradient and opaque fallback.
- [ ] `Error`/`Primary` are restricted to large text, icons, fills, and borders.
- [ ] Every status uses icon + text, never color alone.
- [ ] Focus is visible; dialogs/sheets trap and restore focus appropriately.
- [ ] Flutter targets are at least 48 logical pixels; web targets are at least 44 px.
- [ ] Dynamic text scaling does not hide labels, errors, scores, or actions.

### Real-data audit

- [ ] Feature-card constructors require caller-provided values and contain no default domain records.
- [ ] Production questions, scores, analytics, exams, schedules, and status values come from parsed
      endpoint models.
- [ ] Fixed labels/state inputs exist only in design-system tests/catalogs and are not production data.
- [ ] Empty, loading, and error components do not fabricate content.
- [ ] Backend-derived value sets match Phase 01; unknown values use a labelled INFO state.

## Gap log

| # | Item | Handling |
|---|---|---|
| 1 | Backend writes `scheduled` outside `TestStatus` (Phase 01 gap #4) | Accept/map the real literal to SCHEDULED; never invent another status |
| 2 | Flutter system sans vs web Inter | Intentional; parity is scale/weight, not glyph identity |
| 3 | Blur performance varies by Flutter renderer/device | Use shared opaque fallback after real performance verification |

## Sign-off rule

Phases 04+ start only when all applicable checks pass. Token changes require updating this phase and
re-running Flutter golden/accessibility checks and the web build.
