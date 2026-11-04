# Phase 03 — Reference (text.md)

One design system, two implementations: Flutter/Dart and superadmin CSS. Token values are normative.
Dart uses lower-camel identifiers corresponding to the semantic names below; CSS uses the listed
variables. Alpha conversions: 8% `0x14`, 14% `0x24`, 25% `0x40`, 45% `0x73`, 4% `0x0A`, 24%
`0x3D`, 30% `0x4D`, 60% `0x99`, 72% `0xB8`, 38% `0x61`.

## 1. Principles

1. Glass communicates hierarchy, not decoration.
2. Contrast wins: translucent surfaces sit only over the fixed gradient; otherwise use `#1B2547`.
3. Every status uses icon + text, never color alone.
4. Motion uses 150/250/400 ms and becomes instant under reduced motion.
5. Components render caller data. Production callers supply real endpoint models; no component owns
   a fallback domain dataset.

## 2. Tokens

### 2.1 Colors

| Semantic Dart token / CSS variable | Value | Use |
|---|---|---|
| `glassBgGradientStart` / `--color-glass-bg-gradient-start` | `#0B1026` | Gradient top |
| `glassBgGradientMid` / `--color-glass-bg-gradient-mid` | `#141E3A` | Gradient middle |
| `glassBgGradientEnd` / `--color-glass-bg-gradient-end` | `#0B1026` | Gradient bottom |
| `primary` / `--color-primary` | `#6C5CE7` | Brand/actions/progress |
| `primaryVariant` / `--color-primary-variant` | `#A29BFE` | Focus/links/accents |
| `secondary` / `--color-secondary` | `#00CEC9` | Indeterminate progress |
| `success` / `--color-success` | `#00B894` | Success |
| `warning` / `--color-warning` | `#FDCB6E` | Warning |
| `error` / `--color-error` | `#D63031` | Error/danger |
| `glassSurface` / `--color-glass-surface` | `#14FFFFFF` / white 8% | Default surface |
| `glassSurfaceStrong` / `--color-glass-surface-strong` | `#24FFFFFF` / white 14% | Inputs/rows/chips |
| `glassBorder` / `--color-glass-border` | `#40FFFFFF` / white 25% | Borders |
| `glassHighlight` / `--color-glass-highlight` | `#73FFFFFF` / white 45% | Top highlight |
| `textPrimary` / `--color-text-primary` | `#F5F6FA` | Primary text |
| `textSecondary` / `--color-text-secondary` | `#B8F5F6FA` | Supporting text |
| `textDisabled` / `--color-text-disabled` | `#61F5F6FA` | Inactive only |
| `glassFallbackSolid` / `--color-glass-fallback-solid` | `#1B2547` | Opaque fallback |
| `pressedOverlay` / `--color-pressed-overlay` | `#0AFFFFFF` | Press feedback |
| `focusRing` | `#99A29BFE` | 2-pixel outer focus ring |

### 2.2 Blur and fallback

| Token | Value | Use |
|---|---|---|
| `blurSmall` / `--blur-sm` | 8 logical px / 8 px | Chips/inputs |
| `blurMedium` / `--blur-md` | 16 logical px / 16 px | Cards/dialogs |
| `blurLarge` / `--blur-lg` | 24 logical px / 24 px | Sheets/modals |

Flutter uses clipped `BackdropFilter` with `ImageFilter.blur` behind the surface only. A shared
`GlassCapabilities.blurEnabled` flag selects the opaque fallback when the rendering/device path fails
the performance criteria. Content stays outside the filter. Web uses `@supports (backdrop-filter:
blur(1px))` and otherwise `.glass-fallback`. Never apply translucent glass over moving content.

### 2.3 Elevation

Shadow color is `#4D000000`. `elevationLow=2`, `elevationMedium=6`, `elevationHigh=12` logical
pixels for chips/inputs, cards/buttons, and dialogs/sheets respectively. Web shadow is
`0 Npx 3Npx 0 rgba(0,0,0,0.30)`.

### 2.4 Semantic states

| State | Surface | Border | Content | Extra |
|---|---|---|---|---|
| default | `glassSurface` | `glassBorder` | `textPrimary` | top highlight |
| pressed | `glassSurfaceStrong` | `glassBorder` | `textPrimary` | `pressedOverlay` |
| focused | component surface | `primaryVariant` | `textPrimary` | outer `focusRing` |
| selected | primary at 24% | `primaryVariant` | `textPrimary` | check/leading icon |
| disabled | `glassSurface` | reduced border alpha | `textDisabled` | non-clickable |
| loading | component surface | component border | `textSecondary` | spinner + announcement |
| success | success at 12% | `success` | `textPrimary` | icon + label |
| warning | warning at 12% | `warning` | `textPrimary` | icon + label |
| error | error at 12% | `error` | `textPrimary` | icon + label |

### 2.5 Radii and spacing

`radiusS=8`, `radiusM=16`, `radiusL=24`, `radiusXL=32` logical pixels/CSS px.

`space1=4`, `space2=8`, `space3=12`, `space4=16`, `space6=24`, `space8=32`, `space12=48`.
CSS variables use `--radius-*` and `--space-*` with the same values.

### 2.6 Typography

Flutter uses the system font without a network dependency; web retains Inter.

| Slot | Size / height / weight | Flutter | CSS |
|---|---|---|---|
| Display | 32 / 40 / 700 | `display` | 32px/40px/700 |
| H1 | 24 / 32 / 600 | `h1` | 24px/32px/600 |
| H2 | 20 / 28 / 600 | `h2` | 20px/28px/600 |
| Body | 16 / 24 / 400 | `body` | 16px/24px/400 |
| BodySmall | 14 / 20 / 400 | `bodySmall` | 14px/20px/400 |
| Caption | 12 / 16 / 500 | `caption` | 12px/16px/500 |
| Button | 14 / 20 / 600 | `button` | 14px/20px/600 |

Use `height = lineHeight / fontSize` in Flutter `TextStyle`.

### 2.7 Motion

`motionFast=150ms`, `motionBase=250ms`, `motionSlow=400ms`. Flutter easing is
`Curves.fastOutSlowIn`; CSS is `cubic-bezier(0.2,0,0,1)`.

Flutter reads `MediaQuery.disableAnimations`; when true, skeletons are static and sheets/dialogs
snap to final state. Web `@media (prefers-reduced-motion: reduce)` reduces animation/transition
durations to effectively instant.

### 2.8 Icons and targets

Flutter uses Material `Icons`/`IconData`, outlined by default and filled for selected where
appropriate. Web uses existing `lucide-react`. Inline icons are 20, navigation/empty-state icons 24.
Flutter touch targets are at least 48 logical pixels; web targets at least 44 px. Every icon-only
Flutter control has a semantics label; every web control has `aria-label`.

## 3. Glass surface anatomy

Bottom to top:

1. Fixed full-bleed gradient backdrop.
2. Clipped Flutter `BackdropFilter` or web `backdrop-filter`, only behind the surface.
3. `glassSurface`/`glassSurfaceStrong`, or `glassFallbackSolid` when blur is disabled.
4. One-pixel rounded `glassBorder`.
5. One-pixel top `glassHighlight` with corner fade.
6. Token shadow.
7. Crisp, unfiltered content.

## 4. Component specifications

All visual states in §2.4 apply where relevant. Domain values are required inputs, never defaults.

### 4.1 GlassCard

Flutter: `child`, optional surface/blur/radius; web: `children`, `className`, `strong?`. Cards are
not interactive themselves. Use `MergeSemantics` only when the grouped announcement helps; web uses
a plain container.

### 4.2 GlassButton and GlassIconButton

Kinds: primary, secondary, ghost, danger. Inputs: label, optional icon, loading, enabled, callback.
Minimum height 48/44. Loading replaces the label area without changing width and announces loading.
Disabled uses the actual disabled control. Icon buttons require semantic/ARIA labels.

### 4.3 GlassTextField

Persistent visible label, input on strong surface, optional counter and error. Flutter uses a
`TextEditingController` owned by the caller, label/error semantics, and appropriate keyboard type.
Web binds `<label for>` and `role="alert"`. Limits do not silently truncate input.

### 4.4 GlassChip and GlassFilterChip

Strong surface, small radius, selected/disabled/pressed states, selected semantics, optional leading
icon and clear affordance. Labels come from the caller or endpoint-backed filter model.

### 4.5 GlassDialog

Title, text, confirm/dismiss labels, callbacks, destructive variant. Large radius/blur and 45% black
scrim. Confirm dialogs do not dismiss on scrim tap. Manage initial focus and return focus on close.

### 4.6 GlassBottomSheet

Material 3 `showModalBottomSheet` on Flutter and fixed bottom panel on web. Large top radius/blur,
drag handle, accessible dismissal, focus management, and reduced-motion behavior.

### 4.7 GlassProgress

Flutter `progress` is `double` in 0..1. Four-pixel track on strong surface; primary determinate or
secondary indeterminate indicator. Expose value semantics/`aria-valuenow` and pair with text.

### 4.8 StatusPill

| Status | Flutter icon / web icon | Color |
|---|---|---|
| SCHEDULED | schedule / Clock | primaryVariant |
| IN_PROGRESS | play_arrow / Play | secondary |
| COMPLETED | check_circle / CheckCircle2 | success |
| FAILED | error / XCircle | error |
| PENDING | hourglass_top / Hourglass | warning |
| INFO | info / Info | primaryVariant |

Small radius, status color at 12%, border, 20-pixel icon, mandatory caption label.

### 4.9 TestQuestionCard

Required question number, stem, option list, selected option, and selection callback. Option rows
are at least 48 pixels and use single-select semantics. Production options/stems come from the test
endpoint. KaTeX is retained on web; Flutter math rendering is added only if Phase 09 requires it.

### 4.10 ResultCard

Required percentage, total score, total marks, and exam type. Flutter `CustomPaint` draws the ring;
text exposes "Scored X of Y (P%)". No pass/fail or score is inferred when the backend does not
provide enough data.

### 4.11 AnalysisCard

Required analysis rows containing subject/topic, accuracy, and priority. Map backend `HIGH`,
`MEDIUM`, `LOW` and `strong`, `moderate`, `weak` to labelled visual states without changing values.

### 4.12 ScheduleCard

Required day number, date, topics, per-topic hours/completion, and progress. Backend status and
priority values remain authoritative. No generated topic appears in the widget itself.

### 4.13 EmptyState

Icon, title, message, optional action/callback. Used for genuine empty endpoint results or blocked
capabilities; never populated with substitute records.

### 4.14 ErrorState

Real mapped error message and optional retry. Error semantics/live region and retry button are
mandatory when retry is offered.

### 4.15 SkeletonLoader

Width, height, and radius inputs. Strong-surface shimmer over `motionBase`; static under reduced
motion. Announces loading and disappears when real data/error/empty state arrives.

## 5. Web token mapping

`Frontend_Website/src/styles/tokens.css` contains Tailwind v4 `@theme` entries for every value in
§2, plus `.glass`, `.glass-strong`, `.glass-border`, and `.glass-fallback`. The core pattern is:

```css
@theme {
  --color-glass-bg-gradient-start: #0B1026;
  --color-glass-bg-gradient-mid: #141E3A;
  --color-glass-bg-gradient-end: #0B1026;
  --color-primary: #6C5CE7;
  --color-primary-variant: #A29BFE;
  --color-secondary: #00CEC9;
  --color-success: #00B894;
  --color-warning: #FDCB6E;
  --color-error: #D63031;
  --color-glass-surface: rgba(255,255,255,0.08);
  --color-glass-surface-strong: rgba(255,255,255,0.14);
  --color-glass-border: rgba(255,255,255,0.25);
  --color-glass-highlight: rgba(255,255,255,0.45);
  --color-text-primary: #F5F6FA;
  --color-text-secondary: rgba(245,246,250,0.72);
  --color-text-disabled: rgba(245,246,250,0.38);
  --color-glass-fallback-solid: #1B2547;
  --color-pressed-overlay: rgba(255,255,255,0.04);
  --blur-sm: 8px; --blur-md: 16px; --blur-lg: 24px;
  --radius-s: 8px; --radius-m: 16px; --radius-l: 24px; --radius-xl: 32px;
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-6: 24px; --space-8: 32px; --space-12: 48px;
  --motion-fast: 150ms; --motion-base: 250ms; --motion-slow: 400ms;
}
.glass { border: 1px solid var(--color-glass-border); }
@supports (backdrop-filter: blur(1px)) {
  .glass { background: var(--color-glass-surface); backdrop-filter: blur(var(--blur-md)); }
}
@supports not (backdrop-filter: blur(1px)) {
  .glass { background: var(--color-glass-fallback-solid); }
}
```

Web components use these classes/tokens only, not ad-hoc hex or filters.

## 6. Web-only superadmin components

- `DataTable`: real `rows` prop, sortable keyboard controls, pagination, caption, `aria-sort`, and
  skeleton loading rows. Never invents rows when empty.
- `FilterBar`: caller-provided filters/options, reset action, active-count announcement, responsive
  bottom sheet.
- `ConfirmDialog`: destructive actions require exact typed confirmation or acknowledgement checkbox.
- `PermissionDeniedState`: shield icon, message, and back action for actual role denial.

## 7. Do / Don't

- DO use the fixed gradient/fallback; DON'T place glass over images, video, or scrolling content.
- DO use primary/secondary text tokens; DON'T use low-contrast accent text for body copy.
- DO pair status color with icon + label.
- DO use only the three blur tokens and avoid animated blur.
- DO honor reduced motion and keyboard/focus behavior.
- DO pass real domain values into feature cards; DON'T embed production-looking records in widgets.

## 8. Accessibility matrix

| Foreground | On `#0B1026` | On `#141E3A` | On `#1B2547` | Target |
|---|---|---|---|---|
| TextPrimary | 17.5:1 | 12.1:1 | 13.9:1 | ≥4.5:1 |
| TextSecondary | 9.3:1 | 6.4:1 | 7.9:1 | ≥4.5:1 |
| TextDisabled | 3.3:1 | 2.4:1 | 2.8:1 | inactive only |
| PrimaryVariant | 7.7:1 | 5.3:1 | 6.1:1 | ≥4.5:1 |
| Secondary | 9.5:1 | 6.5:1 | 7.5:1 | ≥4.5:1 |
| Success | 7.4:1 | 5.1:1 | 5.9:1 | ≥4.5:1 text |
| Warning | 12.4:1 | 8.5:1 | 9.8:1 | ≥4.5:1 |
| Error/Primary | 3.9:1 | 2.7:1 | 3.1:1 | large/non-text only; use carefully |

All interactive elements need visible focus, accessible names, appropriate roles/states, and touch
targets. Dynamic text scaling must not obscure API content or actions.

## 9. Backend-derived display values

| Surface | Allowed source values |
|---|---|
| Test status | `pending`, `in_progress`, `completed`, `expired`, `cancelled`, plus real `scheduled` literal until gap #4 is fixed |
| Schedule status | `active`, `completed`, `abandoned` |
| Schedule topic priority | `critical`, `high`, `medium`, `low` |
| Analytics priority | `HIGH`, `MEDIUM`, `LOW` |
| Performance | `strong`, `moderate`, `weak` |
| Preparation status | backend free strings documented in Phase 01 §7.E |
| Exam types | `JEE_MAIN`, `JEE_ADVANCED`, `JEE_COMBO`, `NEET` |

Unknown values render a labelled INFO state. Labels can be human-readable mappings, but values and
records must originate from endpoint responses.

## 10. Performance rules

1. Blur only the static gradient; never images, video, or scrolling content.
2. Keep backdrop/filter layers bounded and const where possible; do not animate blur or rebuild a
   blurred bitmap unnecessarily.
3. At most six medium/small and two large blurred surfaces per screen; overflow uses opaque fallback.
4. `ListView`/long lists use opaque strong rows without per-row blur.
5. At most three concurrent skeleton shimmer animations per viewport; zero under reduced motion.
