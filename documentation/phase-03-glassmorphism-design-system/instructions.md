# Phase 03 — Instructions

Execute steps in order. Every step ends with a **Verify** hint — do not proceed until it passes.
Token names/values are normative (`text.md` §2); copy them exactly.

## Part A — Android (`Android_App/app/src/main/java/ai/eklavya/app/core/designsystem/`)

### Step 1. Prerequisite: phase-02 scaffold builds

```bash
cd Android_App && ./gradlew :app:assembleDebug --console=plain
```

**Verify:** build succeeds. Delete the `.gitkeep` in `core/designsystem/`.

### Step 2. `Color.kt` — color tokens

Create `Color.kt` with an `object EklavyaColors` containing exactly the tokens in `text.md`
§2.1 (hex values with alpha, e.g. `val Primary = Color(0xFF6C5CE7)`, `val GlassSurface =
Color(0x14FFFFFF)`), plus the `PressedOverlay` and `FocusRing` semantic tokens from §2.4.

**Verify:** `grep -c "0x" core/designsystem/Color.kt` ≥ 18; `./gradlew :app:assembleDebug`
succeeds.

### Step 3. `Type.kt` — typography scale

Create `Type.kt` with a `data class EklavyaTypography` (seven `TextStyle` slots: display, h1,
h2, body, bodySmall, caption, button) and a default instance matching `text.md` §2.7 exactly
(32/40 Bold, 24/32 SemiBold, 20/28 SemiBold, 16/24 Normal, 14/20 Normal, 12/16 Medium,
14/20 SemiBold). Font family decision: **system sans-serif** (`FontFamily.Default`) so the app
never depends on network fonts; the superadmin web UI uses Inter (already its base font).

**Verify:** `grep -c "TextStyle" core/designsystem/Type.kt` = 7 (plus the data class usage);
build succeeds.

### Step 4. `Shape.kt`, `Spacing.kt`, `Motion.kt`

Create the three remaining token files per `text.md` §2.5, §2.6, §2.8:

- `Shape.kt`: `object EklavyaShapes` with `radiusS/M/L/XL` (8/16/24/32 dp) + a `toShape()` or
  direct `RoundedCornerShape` vals.
- `Spacing.kt`: `object EklavyaSpacing` with `space1/2/3/4/6/8/12` (4/8/12/16/24/32/48 dp).
- `Motion.kt`: `object EklavyaMotion` with `motionFast/Base/Slow = 150/250/400` ms + a
  `data class MotionTokens(animateScaleInEnabled: Boolean)` and
  `fun resolveMotionEnabled(context: Context): Boolean` reading
  `Settings.Global.getFloat(context.contentResolver, Settings.Global.ANIMATOR_DURATION_SCALE,
  1f) > 0f` (reduced motion = instant state change; see `text.md` §2.8).

**Verify:** build succeeds; `grep -c "val space" core/designsystem/Spacing.kt` = 7.

### Step 5. `Theme.kt` — theme + blur capability

Create `Theme.kt`:

- `EklavyaTheme(content: @Composable () -> Unit)` — dark-only `MaterialTheme` wired with the
  tokens; hosts the fixed gradient background behind every screen (see Step 6).
- `LocalBlurEnabled: ProvidableCompositionLocal<Boolean>` set once per composition:
  `Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !activityManager.isLowRamDevice`.
- `LocalMotionEnabled: ProvidableCompositionLocal<Boolean>` set from
  `EklavyaMotion.resolveMotionEnabled(context)` so every animated component snaps when false.

**Verify:** build succeeds; `grep -c "CompositionLocal" core/designsystem/Theme.kt` ≥ 2.

### Step 6. `Glass.kt` — glass modifiers with fallback

Create `Glass.kt` per `text.md` §3:

- `Modifier.glassCard(surface: Color = GlassSurface, border: Color = GlassBorder, blur: Dp =
  blurMedium)` — rounded (`radiusM`) translucent surface + 1 dp border + top-edge highlight
  (a 1 dp `GlassHighlight` line drawn at the top inner edge) + shadow (black 30%, elevation 6).
- Blur implementation order: if `LocalBlurEnabled.current` and SDK >= 31 use
  `Modifier.graphicsLayer { renderEffect = RenderEffect.createBlurEffect(blurPx, blurPx,
  Shader.TileMode.CLAMP) }` applied to the background layer only (content stays crisp); else
  fall back to the opaque solid `#1B2547` fill (`EklavyaColors.GlassFallbackSolid`) with no
  alpha compositing of the backdrop.
- `GlassBackgroundBox(content)` — `Box` with a vertical gradient brush
  (GlassBgGradientStart -> GlassBgGradientMid -> GlassBgGradientEnd), filling max size; every
  screen root wraps content in this.

**Verify:** build succeeds; on an API-26 emulator screenshot the fallback solid is visible (Part
C catalog step).

### Step 7. Components — cards, pills, buttons, chips

Create in `core/designsystem/components/` (specs in `text.md` §4):

1. `GlassCard.kt` — `GlassCard(modifier, surface, blur, content)` delegating to `glassCard`.
2. `StatusPill.kt` — `StatusPill(status: EklavyaStatus, label: String)`; `enum class
   EklavyaStatus { SCHEDULED, IN_PROGRESS, COMPLETED, FAILED, PENDING, INFO }` mapped per
   `text.md` §2.4/§4.7 (icon + label; never color alone). Icon names: Material Symbols
   `schedule`, `play_arrow`, `check_circle`, `error`, `hourglass_top`, `info`.
3. `GlassButton.kt` — `GlassButton(kind: GlassButtonKind = PRIMARY|SECONDARY|GHOST|DANGER,
   loading: Boolean = false, enabled: Boolean = true, icon: ImageVector? = null, onClick,
   label)`; minimum height 48 dp; `GlassIconButton(icon, contentDescription, onClick)` 48 dp
   touch target; loading swaps icon/label for `CircularProgressIndicator` and disables input.
4. `GlassChip.kt` — `GlassChip(selected, onClick, label)` and
   `GlassFilterChip(selected, onClick, label, leadingIcon?)`; selected state per §2.4.

**Verify:** `./gradlew :app:assembleDebug` succeeds.

### Step 8. Components — inputs, dialogs, sheets

1. `GlassTextField.kt` — `GlassTextField(value, onValueChange, label, errorText: String? = null,
   counterMax: Int? = null, enabled, keyboardOptions)`; label always visible (not floating-only);
   error text in `Error` color with `contentDescription = "Error: $errorText"` semantics; counter
   `len/max` in Caption style.
2. `GlassDialog.kt` — `GlassDialog(title, text, confirmLabel, dismissLabel, onConfirm,
   onDismiss, destructive: Boolean = false)` on `Dialog`; focus request to confirm on open; no
   dimmed scrim blur over content (scrim is `Color.Black.copy(alpha = 0.45f)`).
3. `GlassBottomSheet.kt` — `GlassBottomSheet(onDismiss, content)` using
  `ModalBottomSheet` (Material 3) restyled with glass surface over the gradient.

**Verify:** build succeeds.

### Step 9. Components — progress, feature cards

1. `GlassProgress.kt` — `GlassProgressBar(progress: Float, modifier)` (determinate) and
   `GlassProgressIndeterminate()`; track `GlassSurfaceStrong`, indicator `Primary` (or
   `Secondary` when indeterminate), minimum height 4 dp.
2. `TestQuestionCard.kt` — question number Caption, stem Body, options A–D as selectable
   `GlassSurfaceStrong` rows (selected state per §2.4), 48 dp minimum row height.
3. `ResultCard.kt` — `ResultCard(percentage: Float, totalScore: Float, totalMarks: Float,
   examType: String)`; score ring = `Canvas` arc (Primary arc on GlassSurfaceStrong track,
   percentage in H1 at ring center, Caption label below).
4. `AnalysisCard.kt` — rows of (subject/topic, accuracy bar `GlassProgressBar`, priority
   `StatusPill` for HIGH/MEDIUM/LOW per `text.md` §4.10).
5. `ScheduleCard.kt` — day-number H2, date Caption, topic list with per-topic estimated hours;
   completion `GlassProgressBar`; `completed` rows use `TextDisabled` with a check icon.

**Verify:** build succeeds.

### Step 10. Components — empty, error, skeleton

1. `EmptyState.kt` — `EmptyState(icon, title, message, actionLabel?, onAction?)` centered in a
   `GlassCard`, icon 24 dp `PrimaryVariant`.
2. `ErrorState.kt` — `ErrorState(message, onRetry)`; icon `error` in `Error` color + retry
   `GlassButton(PRIMARY)`.
3. `SkeletonLoader.kt` — `SkeletonLoader(width, height, shape)` shimmering block (animated value
   from `EklavyaMotion.motionBase`, shimmer sweep PrimaryVariant 20% -> 45%); when
   `LocalMotionEnabled` is false render the static GlassSurfaceStrong block instead.

**Verify:** build succeeds.

### Step 11. Preview catalog and screenshot

1. Create `core/designsystem/ComponentPreviewActivity.kt`: `@AndroidEntryPoint` (or plain —
   no DI needed) activity, `android:exported="false"`, rendering every component from Steps
   7–10 in one scrollable column on `GlassBackgroundBox`, one instance per state row
   (default/pressed/selected/disabled/loading/success/warning/error as applicable). Register it
   in the manifest.
2. Add `@Preview` composables inside each component file (default + one non-default state each)
   for Android Studio preview use.
3. Run and capture:

```bash
cd Android_App
./gradlew :app:installDebug
adb shell am start -n ai.eklavya.app/.core.designsystem.ComponentPreviewActivity
adb exec-out screencap -p > /tmp/phase03-component-catalog.png
```

**Verify:** the catalog screen renders every component listed in Step 7–10 (check the
screenshot); no crash (`adb logcat -d | grep -i "AndroidRuntime" | grep -i eklavya` is empty
after a fresh launch).

### Step 12. Reduced-motion verification (Android)

```bash
adb shell settings put global animator_duration_scale 0
adb shell am start -n ai.eklavya.app/.core.designsystem.ComponentPreviewActivity
adb exec-out screencap -p > /tmp/phase03-reduced-motion.png
adb shell settings put global animator_duration_scale 1
```

**Verify:** with scale 0 the skeleton shows the static block (no shimmer) and dialogs/sheets
appear instantly; screenshot pair saved.

## Part B — Superadmin web (`Frontend_Website/`)

### Step 13. Token layer `src/styles/tokens.css`

Create `src/styles/tokens.css` per `text.md` §5: a Tailwind v4 `@theme` block mapping the exact
same token names to CSS custom properties (colors incl. alpha hex, radii, spacing, blur, motion
durations, font sizes/line-heights/weights, shadows), plus `.glass`, `.glass-strong`,
`.glass-border`, `.glass-fallback` utility classes and the `@supports (backdrop-filter: blur(1px))`
rule with the `.glass-fallback` opaque `#1B2547` path. Import it in `src/index.css` **after**
`@import "tailwindcss";` (order matters).

**Verify:** `grep -c -- "--color-" src/styles/tokens.css` ≥ 15;
`grep -n "tokens.css" src/index.css` shows the import.

### Step 14. Glass components `src/components/glass/`

Create one file per component (props in `text.md` §6): `GlassCard.tsx`, `GlassButton.tsx`
(+ `GlassIconButton`), `GlassTextField.tsx`, `GlassChip.tsx` (+ `GlassFilterChip.tsx`),
`GlassDialog.tsx`, `GlassBottomSheet.tsx`, `GlassProgress.tsx`, `StatusPill.tsx`,
`TestQuestionCard.tsx`, `ResultCard.tsx`, `AnalysisCard.tsx`, `ScheduleCard.tsx`,
`EmptyState.tsx`, `ErrorState.tsx`, `SkeletonLoader.tsx`, and the superadmin set
`DataTable.tsx` (sortable columns + pagination controls, keyboard-operable), `FilterBar.tsx`,
`ConfirmDialog.tsx` (destructive actions require typing the confirmation word or checking a
box — props `requireTyping?: string` / `requireCheckbox?: boolean`), `PermissionDeniedState.tsx`.
Rules: class-only styling via the token utilities; `aria-label` on every icon-only control;
`aria-sort` on sortable headers; `role="alert"` on error text; touch targets ≥ 44 px; icons from
`lucide-react`; KaTeX is already available for question stems (`katex` in package.json) — render
stem/solution math with the existing LatexRenderer where present.

**Verify:** `ls src/components/glass | wc -l` = 20;
`grep -rl "aria-" src/components/glass | wc -l` ≥ 15.

### Step 15. Preview route `/design-system`

Add a route in `src/App.tsx` **inside** `BrowserRouter` (it must not inherit `AppShell` chrome):
`/design-system` rendering `src/pages/DesignSystemPreview.tsx`, which stacks every Part-B
component with state toggles (a small local `useState` switchboard is fine; this page is dev
tooling, not production UI).

**Verify:** `grep -n "design-system" src/App.tsx` shows the route; the build in Step 16 passes.

### Step 16. Build and browser check

```bash
cd Frontend_Website
npm run build
npm run dev   # http://localhost:3000/design-system
```

**Verify:** `npm run build` exits 0 (this runs `tsc -b` first); open
`http://localhost:3000/design-system` and confirm every component renders; capture a browser
screenshot for `expected-output.md`.

### Step 17. Contrast and reduced-motion spot checks (web)

1. Contrast: using DevTools, sample body text (`TextPrimary`) on the gradient and on
   `.glass-fallback`; compare against `text.md` §8 minimums (4.5:1 body, 3:1 large text/UI).
2. Reduced motion: DevTools Rendering -> "Emulate CSS media feature prefers-reduced-motion"
   set to `reduce`; confirm skeletons show static blocks and transitions are instant
   (`transition-duration` overridden per `text.md` §2.8).

**Verify:** both checks pass; screenshots saved.

### Step 18. Sign-off

Work through every checkbox in `expected-output.md`.
