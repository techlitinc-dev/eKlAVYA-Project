# Phase 03 — Expected Output & Sign-off

## Deliverables of this phase

1. Android: `core/designsystem/` contains the full token set (`Color`, `Type`, `Shape`,
   `Spacing`, `Motion`, `Theme`, `Glass`) and every component in `components/`; a
   `ComponentPreviewActivity` renders them all on device.
2. Web: `Frontend_Website/src/styles/tokens.css` exposes the same names as Tailwind v4
   `@theme` tokens + `.glass*` utilities with `@supports` fallback; `src/components/glass/`
   contains every component; `/design-system` renders the catalog in the browser.
3. Accessibility: contrast spot-check passes, reduced motion verified on both platforms.

## Verification checklist

### Token exactness (values must match `text.md` §2 verbatim)

- [ ] Colors: `GlassBgGradientStart/End #0B1026`, `GlassBgGradientMid #141E3A`,
      `Primary #6C5CE7`, `PrimaryVariant #A29BFE`, `Secondary #00CEC9`, `Success #00B894`,
      `Warning #FDCB6E`, `Error #D63031`, `GlassSurface #14FFFFFF` (8%),
      `GlassSurfaceStrong #24FFFFFF` (14%), `GlassBorder #40FFFFFF` (25%),
      `GlassHighlight #73FFFFFF` (45%), `TextPrimary #F5F6FA`,
      `TextSecondary #B8F5F6FA` (72%), `TextDisabled #61F5F6FA` (38%),
      `GlassFallbackSolid #1B2547`, `PressedOverlay #0AFFFFFF` (4%), focus ring
      `PrimaryVariant @ 60%`.
- [ ] Blur: `blurSmall 8`, `blurMedium 16`, `blurLarge 24` (dp and px).
- [ ] Elevation: shadow black @ 30%, elevations 2 / 6 / 12.
- [ ] Radii: `radiusS 8`, `radiusM 16`, `radiusL 24`, `radiusXL 32`.
- [ ] Spacing: `space1 4`, `space2 8`, `space3 12`, `space4 16`, `space6 24`, `space8 32`,
      `space12 48`.
- [ ] Type: Display 32/40 Bold, H1 24/32 SemiBold, H2 20/28 SemiBold, Body 16/24 Regular,
      BodySmall 14/20 Regular, Caption 12/16 Medium, Button 14/20 SemiBold (Android
      `TextStyle`s + CSS sizes match).
- [ ] Motion: `motionFast 150ms`, `motionBase 250ms`, `motionSlow 400ms`; standard easing;
      reduced-motion path exists on both platforms.
- [ ] Web CSS vars in `tokens.css` are the kebab-case of every Kotlin token (spot-check 10).

### Android

- [ ] `cd Android_App && ./gradlew clean :app:assembleDebug` succeeds.
- [ ] `ComponentPreviewActivity` launches on an API-26 emulator (fallback solid visible) and an
      API-35 emulator (blur path); screenshots `/tmp/phase03-component-catalog.png` saved.
- [ ] Catalog shows every component from `instructions.md` Steps 7–10 in its applicable states
      (default/pressed/selected/disabled/loading + success/warning/error for StatusPill).
- [ ] Reduced motion: with `animator_duration_scale 0`, skeleton is static and sheets appear
      instantly; screenshot saved; scale restored to 1.
- [ ] No `AndroidRuntime` crash in logcat after catalog launch.

### Web

- [ ] `npm run build` (includes `tsc -b`) exits 0 in `Frontend_Website`.
- [ ] `src/components/glass/` contains all 20 files listed in `instructions.md` Step 14.
- [ ] `http://localhost:3000/design-system` renders every component with working state toggles;
      browser screenshot saved.
- [ ] Every icon-only control has `aria-label`; sortable table headers have `aria-sort`;
      error text uses `role="alert"` (`grep` spot-checks pass).
- [ ] No new dependency added to `package.json` (`git diff Frontend_Website/package.json` is
      empty).

### Accessibility

- [ ] Contrast spot-check (DevTools/accessible scanner on both platforms): `TextPrimary` and
      `TextSecondary` on gradient start/mid and on `#1B2547` meet >= 4.5:1 (targets per
      `text.md` §8: 17.5 / 12.1 / 13.9 and 9.3 / 6.4 / 7.9).
- [ ] `Error`/`Primary` are used only for large text, icons, fills, borders (no body-size
      accent-colored text on glass).
- [ ] Every status indicator on both catalogs shows icon + text label (visual inspection).
- [ ] Focus indicator visible on buttons, chips, inputs, table headers (Tab-through test).
- [ ] Touch targets: no web control smaller than 44 px, no Android control smaller than 48 dp.

### Reduced motion

- [ ] Android flag honored (`text.md` §2.8 mechanism) — verified in Step 12.
- [ ] Web `prefers-reduced-motion: reduce` emulation: transitions instant, skeletons static —
      verified in Step 17.

## Gap log

| # | Item | Handling |
|---|---|---|
| 1 | Backend writes literal test status `scheduled` that is not in the `TestStatus` enum (phase-01 §11 gap #4) | StatusPill accepts it and maps it to SCHEDULED; documented in `text.md` §9 |
| 2 | Android uses system sans, web uses Inter (per decision in `text.md` §2.7) | Intentional divergence; visual parity is by scale/weight, not glyph identity |

## Sign-off rule

Phases 04+ may start only when every box above is checked. Any token rename or restyle after
sign-off requires updating this phase's `text.md` and re-running the full checklist.
