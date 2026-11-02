# Phase 03 — Reference (text.md)

One design system, two implementations. Token names are normative: Android code references the
Kotlin names, the superadmin web references the CSS-variable names in §5, and all later
documentation phases use these names. Alpha percentages convert to hex alpha as noted once:
8% = `0x14`, 14% = `0x24`, 25% = `0x40`, 45% = `0x73`, 4% = `0x0A`, 24% = `0x3D`, 30% = `0x4D`,
60% = `0x99`, 72% = `0xB8`, 38% = `0x61` (rounded to nearest byte).

## 1. Principles

1. **Glass is hierarchy, not decoration.** A glass surface says "this group belongs together";
   more blur/border = higher elevation.
2. **Contrast first.** Translucent surfaces exist only over the fixed three-stop gradient
   background; body text is never placed over imagery or user content. Opaque fallback color is
   `#1B2547` whenever blur cannot be guaranteed.
3. **Never color alone.** Every status signal is icon + text label.
4. **Motion informs, then gets out of the way.** 150/250/400 ms, standard easing, and instant
   state change under reduced motion.

## 2. Tokens

### 2.1 Color tokens

| Token (Kotlin / CSS var) | Value | Use |
|---|---|---|
| `GlassBgGradientStart` / `--color-glass-bg-gradient-start` | `#0B1026` | Background gradient top stop |
| `GlassBgGradientMid` / `--color-glass-bg-gradient-mid` | `#141E3A` | Background gradient center stop |
| `GlassBgGradientEnd` / `--color-glass-bg-gradient-end` | `#0B1026` | Background gradient bottom stop |
| `Primary` / `--color-primary` | `#6C5CE7` | Brand actions, active accents, progress indicator |
| `PrimaryVariant` / `--color-primary-variant` | `#A29BFE` | Focus rings, links, secondary accents |
| `Secondary` / `--color-secondary` | `#00CEC9` | Indeterminate progress, highlights |
| `Success` / `--color-success` | `#00B894` | Success status |
| `Warning` / `--color-warning` | `#FDCB6E` | Warning status |
| `Error` / `--color-error` | `#D63031` | Error status, danger actions |
| `GlassSurface` / `--color-glass-surface` | white @ 8% = `#14FFFFFF` / `rgba(255,255,255,0.08)` | Default card/sheet fill |
| `GlassSurfaceStrong` / `--color-glass-surface-strong` | white @ 14% = `#24FFFFFF` / `rgba(255,255,255,0.14)` | Pressable rows, inputs, chips |
| `GlassBorder` / `--color-glass-border` | white @ 25% = `#40FFFFFF` / `rgba(255,255,255,0.25)` | Card/sheet/chip border |
| `GlassHighlight` / `--color-glass-highlight` | white @ 45% = `#73FFFFFF` / `rgba(255,255,255,0.45)` | 1 dp top-edge light line on cards |
| `TextPrimary` / `--color-text-primary` | `#F5F6FA` | Body/headline text |
| `TextSecondary` / `--color-text-secondary` | `rgba(245,246,250,0.72)` (`#B8F5F6FA`) | Supporting text, captions on cards |
| `TextDisabled` / `--color-text-disabled` | `rgba(245,246,250,0.38)` (`#61F5F6FA`) | Disabled text/elements only (exempt from contrast minimum — never body text) |
| `GlassFallbackSolid` / `--color-glass-fallback-solid` | `#1B2547` | Opaque fill when blur is unavailable |
| `PressedOverlay` / `--color-pressed-overlay` | white @ 4% = `#0AFFFFFF` | Pressed-state overlay |
| `FocusRing` / derived | `PrimaryVariant` @ 60% = `#99A29BFE` | 2 dp focus ring |

### 2.2 Blur tokens

| Token | Value | Typical use |
|---|---|---|
| `blurSmall` / `--blur-sm` | 8 dp / 8 px | Chips, small cards, inputs |
| `blurMedium` / `--blur-md` | 16 dp / 16 px | Default cards, dialogs |
| `blurLarge` / `--blur-lg` | 24 dp / 24 px | Bottom sheets, modals |

Rules: blur renders **only** over the fixed gradient background (§3). Fallback when blur is
unavailable: replace the translucent fill with `GlassFallbackSolid` (`#1B2547`) and keep the
border/highlight; never keep a translucent fill over moving content.

Runtime detection, spelled out:

- **Android:** `blurEnabled = Build.VERSION.SDK_INT >= 31 && !activityManager.isLowRamDevice`.
  SDK >= 31 renders with `RenderEffect.createBlurEffect` on the surface's background layer
  (content stays crisp). SDK < 31 or low-RAM: opaque fallback, no alpha compositing. Expose via
  `LocalBlurEnabled` (Step 5 of `instructions.md`) so every component reads one flag.
- **Web:** `@supports (backdrop-filter: blur(1px))` (plus `-webkit-` prefix check where relevant)
  applies the glass class; otherwise the `.glass-fallback` class with `background:
  var(--color-glass-fallback-solid)`. No JS detection required.

### 2.3 Elevation / shadows

`shadowColor` = black @ 30% = `#4D000000`. Token `elevationN` maps to Material elevation N:

| Token | Elevation | Use |
|---|---|---|
| `elevationLow` | 2 dp | Chips, inputs at rest |
| `elevationMedium` | 6 dp | Cards, buttons (default) |
| `elevationHigh` | 12 dp | Dialogs, bottom sheets |

Web shadow utility: `0 Npx 3Npx 0 rgba(0,0,0,0.30)` (N = elevation dp) — matches Material's
ambient/penumbra ratio closely enough for the superadmin panel.

### 2.4 Semantic state mapping

| State | Surface | Border | Content | Extra |
|---|---|---|---|---|
| default | `GlassSurface` | `GlassBorder` | `TextPrimary` | top highlight line |
| pressed | `GlassSurfaceStrong` | `GlassBorder` | `TextPrimary` | + `PressedOverlay` (white +4%) |
| focused | surface of the component | `PrimaryVariant` 1 dp | `TextPrimary` | + 2 dp `FocusRing` outside |
| selected | `Primary` @ 24% (`#3D6C5CE7`) over surface | `PrimaryVariant` 1 dp | `TextPrimary` | check/leading icon |
| disabled | `GlassSurface` | `GlassBorder` @ 38% alpha | `TextDisabled` | non-clickable |
| loading | surface of the component | component border | `TextSecondary` | replace icon/label area with spinner |
| success | `Success` @ 12% fill | `Success` 1 dp | `TextPrimary` | `Success`-colored icon + label |
| warning | `Warning` @ 12% fill | `Warning` 1 dp | `TextPrimary` | `Warning` icon + label |
| error | `Error` @ 12% fill | `Error` 1 dp | `TextPrimary` | `Error` icon + label |

Status color semantics: success -> `Success`, warning -> `Warning`, error -> `Error`,
info/neutral -> `PrimaryVariant`.

### 2.5 Corner radii

| Token | Value |
|---|---|
| `radiusS` / `--radius-s` | 8 dp / px (chips, pills, small cards) |
| `radiusM` / `--radius-m` | 16 (cards, inputs, buttons) |
| `radiusL` / `--radius-l` | 24 (bottom sheets, dialogs) |
| `radiusXL` / `--radius-xl` | 32 (hero/empty states) |

### 2.6 Spacing scale

`space1=4, space2=8, space3=12, space4=16, space6=24, space8=32, space12=48` (dp/px). CSS vars
`--space-1` … `--space-12` with the same numbers (Tailwind spacing utilities remain valid;
these exist for parity and for values Tailwind lacks by default, e.g. 48 is default in Tailwind
but the name is fixed regardless).

### 2.7 Typography

Font: superadmin web = **Inter** (already the base body font, `Frontend_Website/src/index.css:1-9`);
Android = system sans-serif (`FontFamily.Default`) — no network font dependency.

| Token | Size / line-height / weight | Android `TextStyle` | CSS utility (font-size/line-height/weight) |
|---|---|---|---|
| `Display` | 32 / 40 / Bold (700) | `display` | `text-[32px] leading-[40px] font-bold` (or `.text-display`) |
| `H1` | 24 / 32 / SemiBold (600) | `h1` | 24/32/600 |
| `H2` | 20 / 28 / SemiBold (600) | `h2` | 20/28/600 |
| `Body` | 16 / 24 / Regular (400) | `body` | 16/24/400 |
| `BodySmall` | 14 / 20 / Regular (400) | `bodySmall` | 14/20/400 |
| `Caption` | 12 / 16 / Medium (500) | `caption` | 12/16/500 |
| `Button` | 14 / 20 / SemiBold (600) | `button` | 14/20/600 |

### 2.8 Motion

| Token | Value | Use |
|---|---|---|
| `motionFast` / `--motion-fast` | 150 ms | Press feedback, toggle, hover |
| `motionBase` / `--motion-base` | 250 ms | Sheet/dialog enter/exit, skeleton shimmer period |
| `motionSlow` / `--motion-slow` | 400 ms | Hero transitions (rare) |

Easing: standard = `FastOutSlowInEasing` (Compose) / `cubic-bezier(0.2, 0.0, 0, 1)` (CSS).

Reduced motion (replaces scale/fade with **instant state change**):

- Android: `EklavyaMotion.resolveMotionEnabled(context)` reads
  `Settings.Global.ANIMATOR_DURATION_SCALE`; `0f` -> disabled. Threaded through
  `LocalMotionEnabled`; animated components (skeleton shimmer, sheet slide) snap to final state.
- Web: `@media (prefers-reduced-motion: reduce)` sets all `transition-duration`/`animation-duration`
  to `1ms`/`0.01ms` for the glass layer and skeletons render static.

### 2.9 Icons and targets

- Superadmin web: `lucide-react` (already a dependency, `Frontend_Website/package.json`). Android:
  Material Symbols (Compose `Icons`/`ImageVector`; use outlined by default, filled for selected).
- Sizes: 20 dp/px default inline; 24 dp/px for navigation and empty-state icons.
- Touch targets: >= 48 dp Android, >= 44 px web (a 20 px icon still sits in a 44 px button).
- Every icon-only control carries `contentDescription` (Android) / `aria-label` (web).

## 3. Glass surface anatomy (normative)

A glass card/sheet is, bottom to top:

1. **Backdrop** (screen root): vertical gradient `GlassBgGradientStart -> GlassBgGradientMid ->
   GlassBgGradientEnd`, fixed, full-bleed, never scrolled content behind it.
2. **Blur layer** (when enabled): blur radius per §2.2 applied to a snapshot of the backdrop
   *under* the surface bounds only. Android: `RenderEffect` on the surface's own background
   layer. Web: `backdrop-filter: blur(Npx) saturate(1.4)`.
3. **Fill**: `GlassSurface` (or `GlassSurfaceStrong`) — or `GlassFallbackSolid` when blur is
   unavailable (§2.2).
4. **Border**: 1 dp `GlassBorder`, rounded per component radius.
5. **Highlight**: 1 dp `GlassHighlight` line along the top inner edge (alpha fade at corners).
6. **Shadow**: per §2.3.

## 4. Component specs (both platforms unless noted)

States column legend: D default, P pressed, F focused, S selected, X disabled, L loading,
+ success/warning/error. "A11y" is mandatory.

### 4.1 GlassCard
Props: `modifier/surface/blur/content` (Android), `className/children/strong?` (web).
Anatomy: §3 anatomy. States: D/P(via child controls only; cards are not pressable)/X(n/a).
A11y: container ` semantics mergeDescendants` (Android) / plain `<div>` (web); never
interactive itself.

### 4.2 GlassButton
Kinds: `PRIMARY` (fill `Primary`, text `GlassBgGradientStart`-on-primary = `#0B1026`, border
none), `SECONDARY` (fill `GlassSurfaceStrong`, border `PrimaryVariant`, text `TextPrimary`),
`GHOST` (transparent, text `PrimaryVariant`), `DANGER` (fill `Error` @ 16%, border `Error`,
text `TextPrimary`, icon `Error`). Props: `kind`, `label`, `icon?`, `loading`, `enabled`,
`onClick`. States: D/P/X/L (spinner replaces label; width stays fixed to avoid layout shift).
A11y: min height 48 dp / 44 px; loading announces "Loading" (`liveRegion` / `aria-live`);
disabled uses `enabled=false`/`disabled` (not a click-swallowing wrapper). `GlassIconButton`:
square 48/44, `icon` + `contentDescription`/`aria-label` mandatory, same state set.

### 4.3 GlassTextField
Props: `value/onValueChange/label/errorText?/counterMax?/enabled/keyboardOptions`. Anatomy:
Caption label always visible above the field; input on `GlassSurfaceStrong` with `radiusM`;
trailing counter `current/max` Caption + `TextSecondary` (error: `Error`); error text BodySmall
`Error` below. States: D/F(`PrimaryVariant` border + FocusRing)/X/error. A11y: label tied via
`labelFor`/`<label for>`; error has `contentDescription="Error: …"` / `role="alert"`;
`counterMax` soft-blocks at limit but does not truncate silently.

### 4.4 GlassChip / GlassFilterChip
Props: `selected/onClick/label/leadingIcon?`. Anatomy: `radiusS` pill, `GlassSurfaceStrong`
fill. States: D/P/S(§2.4 selected mapping)/X. Filter chips add a leading icon slot and a clear
(X) affordance when selected. A11y: `toggle`/Chip semantics; selected state exposed
(`aria-pressed` / `SemanticsProperties.ToggleableValue`).

### 4.5 GlassDialog (alert/confirm)
Props: `title/text/confirmLabel/dismissLabel/onConfirm/onDismiss/destructive?`. Anatomy:
`GlassCard` with `radiusL` + `blurLarge`, scrim black 45%. Destructive variant: confirm button
is `DANGER`. States: D/X(only dialog chrome; scrim click does not dismiss confirm dialogs).
A11y: title as heading; initial focus on confirm; Escape/web and back/Android cancel only for
alert dialogs; `role="alertdialog"`/`Dialog` semantics.

### 4.6 GlassBottomSheet
Props: `onDismiss/content/peekHeight?`. Anatomy: `ModalBottomSheet` (M3) / web fixed bottom
panel, `radiusL` top corners, `blurLarge`, drag handle. States: D/dragging/X. A11y: swipe/fling
or Escape dismisses; focus moves into sheet on open and returns to the trigger on close.

### 4.7 GlassProgressBar + indeterminate spinner
Props: `progress: Float 0..1` / indeterminate variant. Anatomy: 4 dp track `GlassSurfaceStrong`
`radiusS`; indicator `Primary` (determinate) or `Secondary` (indeterminate, 40% width sweep).
A11y: `ProgressBarSemantics` / `role="progressbar"` + `aria-valuenow` (omit for
indeterminate); never the only signal — pair with a label or StatusPill.

### 4.8 StatusPill
Props: `status: EklavyaStatus`, `label`. Enum + mapping (icon, color token):

| Status | Icon (Android / web) | Color |
|---|---|---|
| SCHEDULED | schedule / Clock | `PrimaryVariant` |
| IN_PROGRESS | play_arrow / Play | `Secondary` |
| COMPLETED | check_circle / CheckCircle2 | `Success` |
| FAILED | error / XCircle | `Error` |
| PENDING | hourglass_top / Hourglass | `Warning` |
| INFO | info / Info | `PrimaryVariant` |

Anatomy: `radiusS` pill, status color @ 12% fill + 1 dp border + 20 px icon + Caption label.
A11y: the text label is mandatory — never ship an icon-only pill.

### 4.9 TestQuestionCard
Props: `questionNumber/stem/options: List<String>/selectedOption?/onSelect`. Anatomy: GlassCard
> Caption "Q{number}" + Body stem (KaTeX-capable on web) > option rows (A–D letter Caption in a
`radiusS` square, option text Body; row = `GlassSurfaceStrong`, min height 48; selected per
§2.4). States: option rows D/P/S/X(after submit, locked). A11y: whole card `mergeDescendants`;
options as single-select radio group semantics.

### 4.10 ResultCard (score ring)
Props: `percentage/totalScore/totalMarks/examType`. Anatomy: GlassCard row — `Canvas` ring
(64 dp, track `GlassSurfaceStrong` 8 dp, arc `Primary`, round cap) with H1 percentage centered;
column: H2 `totalScore/totalMarks`, Caption exam type, StatusPill (§4.8) for pass/fail context
where applicable. A11y: ring is decorative; expose "Scored X of Y (P%)" as a text semantics.

### 4.11 AnalysisCard (subject/topic rows with priority)
Props: `rows: List<AnalysisRow(subject/topic, accuracy, priority)>`. Anatomy: GlassCard > per
row: BodySmall subject+topic, `GlassProgressBar(accuracy)` 150 px wide, StatusPill for priority
HIGH(`Error`)/MEDIUM(`Warning`)/LOW(`Success`) with icons (arrow_upward / remove / arrow_downward
on web; equivalent Material Symbols on Android). Backend enums: priority `HIGH|MEDIUM|LOW`,
`performance_level strong|moderate|weak` (phase-01 §7.E); map strong->COMPLETED-pill styling,
moderate->PENDING, weak->FAILED colors but always with labels per §2.4 rule. A11y: row is one
semantics node reading "Subject, Topic, accuracy percent, priority".

### 4.12 ScheduleCard (day card with topics + progress)
Props: `dayNumber/date/topics: List<TopicItem(topic, hours, completed)>/progress`. Anatomy:
GlassCard > H2 "Day {n}" + Caption date > topic rows (BodySmall topic, Caption `{hours}h`, check
icon when `completed` with `TextDisabled` text) > `GlassProgressBar(progress)`. Backend note:
schedule `status` is `active|completed|abandoned` and days carry `completion_percentage`
(phase-01 §7.F); day topics carry `priority: critical|high|medium|low` — render critical/high
with a `Warning`/`Error` left rule, medium/low neutral. A11y: progress has value semantics.

### 4.13 EmptyState
Props: `icon/title/message/actionLabel?/onAction?`. Anatomy: `radiusXL` GlassCard, centered:
24 px `PrimaryVariant` icon, H2 title, BodySmall `TextSecondary` message, optional
`GlassButton(SECONDARY)`. A11y: icon decorative (`contentDescription=null` / `aria-hidden`).

### 4.14 ErrorState
Props: `message/onRetry?`. Anatomy: EmptyState variant with `Error`-colored `error` icon and a
`GlassButton(PRIMARY, label="Retry")`. A11y: message `role="alert"` / `liveRegion`.

### 4.15 SkeletonLoader
Props: `width/height/shape(radiusS|M)`. Anatomy: `GlassSurfaceStrong` block; shimmer sweep
`PrimaryVariant` gradient 20% -> 45% alpha over `motionBase` when motion enabled; static block
under reduced motion. A11y: `contentDescription="Loading"` group semantics; always paired with
at least one real content announcement when data arrives.

## 5. Web token mapping (Tailwind v4, `src/styles/tokens.css`)

CSS-first config inside `@theme { … }` (names = kebab-case of the Kotlin tokens):

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
```

Glass utility classes (single source of truth for all web components):

```css
.glass { border: 1px solid var(--color-glass-border); box-shadow: 0 6px 18px 0 rgba(0,0,0,0.30); }
@supports (backdrop-filter: blur(1px)) {
  .glass { background: var(--color-glass-surface);
           backdrop-filter: blur(var(--blur-md)) saturate(1.4); }
}
@supports not (backdrop-filter: blur(1px)) {
  .glass { background: var(--color-glass-fallback-solid); }
}
.glass-strong { /* same pattern, --color-glass-surface-strong, blur-sm */ }
.glass::before { /* 1px top highlight: var(--color-glass-highlight), radius-m top corners */ }
```

Web components live in `Frontend_Website/src/components/glass/` and may only use these classes
plus Tailwind utilities built on the `@theme` tokens — no inline hex values, no ad-hoc
`backdrop-filter` outside `.glass*`.

## 6. Web-only superadmin components

### 6.1 DataTable
Props: `columns: {key,label,sortable?}[]/rows/sort{key,dir}/onSort/page/pageSize/total/onPage`.
Anatomy: glass surface wrapper > table with Caption-styled headers; sortable headers show a
chevron (asc/desc) and are `<button>`s; pagination footer: "Showing X–Y of Z" + Previous/Next
(>= 44 px). States: D/F(header)/X(prev at page 1)/L(skeleton rows). A11y: `<table>` with
`<caption>`; `aria-sort` on headers; keyboard: sort buttons Tab-focusable, pagination operable
by Enter/Space.

### 6.2 FilterBar
Props: `filters: {key,label,options,multi?}[]/values/onChange/onReset`. Anatomy: row of
`GlassFilterChip`s + ghost "Reset" button; collapses into a `GlassBottomSheet` on narrow
viewports. A11y: chips follow §4.4; the active filter count is announced
(`aria-live="polite"`).

### 6.3 ConfirmDialog
Extends `GlassDialog`. Destructive confirmations (delete PYQ/flashcard, revoke premium, per
phase-01 §7.I mutating actions) require **one** of: typing a confirmation word
(`requireTyping="DELETE"`, input must match exactly) or checking an acknowledgement box
(`requireCheckbox`). Confirm stays disabled until satisfied. A11y: the requirement text is part
of the dialog label; input labelled.

### 6.4 PermissionDeniedState
Props: `message?/onBack`. Anatomy: EmptyState variant, `ShieldOff` icon `Warning`, primary
button "Go back". Used when the URL-inferred role (`AppShell.tsx:39-43`) lacks access to a view.

## 7. Do / Don't

- DO render every screen root on the fixed gradient (or opaque fallback) backdrop. DON'T put
  glass over lists of images, video, or scrolling user content.
- DO use `TextPrimary`/`TextSecondary` for all body copy. DON'T use `Primary` or `Error` for
  body-size text on glass (contrast 3.9:1/2.7:1 — accent and large text only, §8).
- DO pair every status with icon + label. DON'T ship color-only badges, dots, or rings.
- DO keep blur radii to the three tokens. DON'T animate blur radius or re-blur on scroll.
- DO use `PressedOverlay` for press feedback on glass. DON'T darken with black overlays (muddies
  the glass).
- DO snap to final state under reduced motion. DON'T play entrance animations "just once".
- DO keep DataTable/FilterBar keyboard-operable. DON'T implement custom click-only controls.

## 8. Accessibility matrix (WCAG 2.1 AA targets)

Computed contrast (sRGB, rounded to 0.1) — spot re-verification is an `expected-output.md`
item:

| Foreground | On `#0B1026` | On `#141E3A` | On `#1B2547` | Minimum | Pass |
|---|---|---|---|---|---|
| `TextPrimary` `#F5F6FA` | 17.5:1 | 12.1:1 | 13.9:1 | 4.5:1 body | yes |
| `TextSecondary` 72% | 9.3:1 | 6.4:1 | 7.9:1 | 4.5:1 body | yes |
| `TextDisabled` 38% | 3.3:1 | 2.4:1 | 2.8:1 | exempt (inactive only) | n/a |
| `PrimaryVariant` `#A29BFE` | 7.7:1 | 5.3:1 | 6.1:1 | 4.5:1 | yes |
| `Secondary` `#00CEC9` | 9.5:1 | 6.5:1 | 7.5:1 | 4.5:1 | yes |
| `Success` `#00B894` | 7.4:1 | 5.1:1 | 5.9:1 | 4.5:1 (non-text 3:1) | yes |
| `Warning` `#FDCB6E` | 12.4:1 | 8.5:1 | 9.8:1 | 4.5:1 | yes |
| `Error` `#D63031` | 3.9:1 | 2.7:1 | 3.1:1 | 3:1 large/non-text only | restricted |
| `Primary` `#6C5CE7` | 3.9:1 | 2.7:1 | 3.1:1 | 3:1 large/non-text only | restricted |

"Restricted" = use for fills, borders, icons, and text >= 18 pt (14 pt bold) only; supporting
text near an `Error`/`Primary` element uses `TextPrimary`.

| Requirement | Target | Mechanism |
|---|---|---|
| Contrast (body) | >= 4.5:1 | token pairs above; body text only on gradient/fallback |
| Contrast (large text/UI components, focus indicators) | >= 3:1 | focus ring `PrimaryVariant` on all focusables |
| Focus visible | 100% of interactive elements | 2 dp `FocusRing`; web `:focus-visible` + `outline` fallback |
| Labels / names | 100% icon-only controls | `contentDescription` / `aria-label`; form labels bound |
| Status | not color alone | StatusPill icon + label (§4.8) |
| Keyboard (web tables/filters/dialogs) | full operation | §6.1/§6.2/§6.3; focus trap in dialogs, return on close |
| Reduced motion | honored | §2.8 |
| Touch targets | 48 dp / 44 px | §2.9 |

## 9. Backend-derived display values (only sources allowed)

Components display these backend value sets and no others (phase-01 citations):

| UI surface | Allowed values | Source |
|---|---|---|
| Test status pills | `pending`, `in_progress`, `completed`, `expired`, `cancelled` (enum `TestStatus`) + literal `scheduled` written by services until gap #4 is fixed | `Backend/models/diagnostic_test_models.py:28-64`; `exam_service.py:197`; phase-01 §7.C |
| Schedule status | `active`, `completed`, `abandoned` | `Backend/models/schedule_models.py:441-567`; phase-01 §7.F |
| Schedule topic priority | `critical`, `high`, `medium`, `low` | phase-01 §7.F |
| Analytics topic priority | `HIGH`, `MEDIUM`, `LOW` | `Backend/models/analytics_models.py:706-762`; phase-01 §7.E |
| Performance level | `strong`, `moderate`, `weak` | phase-01 §7.E |
| Preparation status (free string) | `Excellent`, `Good`, `Needs Improvement`, `Requires Significant Work` | `Backend/services/performance_analyzer.py:738-744`; phase-01 §7.E |
| Exam types | `JEE_MAIN`, `JEE_ADVANCED`, `JEE_COMBO`, `NEET` (schedule generation rejects `JEE_COMBO`) | phase-01 §7.C, §7.F |

Anything not in this table is unknown to the client and must be rendered with the INFO pill.

## 10. Performance rules

1. Blur only over the static gradient; never over scrolling content, images, or video.
2. Cache: Android — the gradient backdrop is drawn once per screen; `RenderEffect` is applied to
   the surface background layer, not recomputed per frame; the haze/snapshot is reused across
   recompositions (remember the blurred bitmap per bounds). Web — the gradient is a fixed
   full-viewport layer; `backdrop-filter` composites on the GPU; do not animate `blur()` or
   trigger layout on glass elements (animate `transform`/`opacity` only).
3. Limit blurred surfaces per screen: <= 6 medium/small glass surfaces, <= 2 large
   (dialog/sheet). Overflow renders as `GlassFallbackSolid` surfaces (still on-brand, cheaper).
4. Inside `LazyColumn`/long lists use `GlassSurfaceStrong` opaque rows — no per-row blur.
5. Skeleton shimmer runs at most 3 concurrent instances per viewport; reduced-motion renders
   zero animations.
