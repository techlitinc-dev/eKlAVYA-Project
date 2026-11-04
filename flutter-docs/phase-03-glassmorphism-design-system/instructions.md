# Phase 03 — Instructions

Execute in order. Token values in `text.md` §2 are normative. Flutter work is under
`Android_App/lib/core/design_system/`; web work remains under `Frontend_Website/`.

## Part A — Flutter design system

### Step 1. Verify the Phase 02 scaffold

```bash
cd Android_App
flutter analyze
flutter test
```

**Verify:** both pass before design-system changes.

### Step 2. Create color, shape, spacing, and motion tokens

Create `tokens/colors.dart`, `tokens/shapes.dart`, `tokens/spacing.dart`, and `tokens/motion.dart`.
Use Dart `static const` values corresponding one-to-one to `text.md` §2. Use `Color(0x...)` ARGB
values exactly, `BorderRadius.circular` for radii, logical pixels for spacing, and `Duration` for
motion. Do not introduce per-feature color constants.

**Verify:** token unit tests check every value, including alpha channels.

### Step 3. Create typography and theme extensions

Create `tokens/typography.dart` with the seven `TextStyle` values in `text.md` §2.7 and the system
font family. Create `eklavya_theme.dart` with a dark Material 3 `ThemeData` and a `ThemeExtension`
that exposes all custom tokens to widgets.

**Verify:** `flutter analyze` passes and theme tests resolve every token from the same extension.

### Step 4. Add shared motion and blur capability flags

Create `glass_capabilities.dart`. Read reduced motion from `MediaQuery.of(context).disableAnimations`
and make animated widgets snap to their final state when true. Centralize `blurEnabled`; disable it
when the target/rendering path fails the documented performance check. Do not scatter platform
version checks through widgets.

**Verify:** widget tests show static skeletons and instant state changes with animations disabled.

### Step 5. Implement the glass background and surface

Create `glass_background.dart` and `glass_surface.dart`:

- full-size fixed three-stop gradient behind the screen;
- clipped `BackdropFilter` with `ImageFilter.blur` only behind the translucent surface;
- content drawn outside the filter so text remains crisp;
- 1-pixel border, top highlight, radius, and shadow from tokens;
- `GlassFallbackSolid` without backdrop alpha when blur is disabled.

**Verify:** golden tests cover blur-enabled and opaque-fallback surfaces. No filter wraps text.

### Step 6. Implement basic components

Create in `components/`:

1. `glass_card.dart` — non-interactive surface with caller-provided child.
2. `status_pill.dart` — `EklavyaStatus` plus mandatory label and matching icon.
3. `glass_button.dart` — primary/secondary/ghost/danger, loading, disabled, and icon-button forms;
   minimum 48 logical-pixel target and loading announcement.
4. `glass_chip.dart` — selectable and filter variants with selected semantics.

**Verify:** widget/golden tests cover every applicable state. Labels come from callers.

### Step 7. Implement inputs, dialogs, and sheets

1. `glass_text_field.dart` — persistent label, bound error semantics, counter, enabled/focus states.
2. `glass_dialog.dart` — title/text/actions, destructive variant, initial focus, 45% black scrim.
3. `glass_bottom_sheet.dart` — Material 3 modal sheet, glass styling, focus return, reduced motion.

**Verify:** tests cover keyboard interaction, error announcements, disabled actions, and focus return.

### Step 8. Implement progress and endpoint-backed feature-card components

1. `glass_progress.dart` — determinate/indeterminate progress with value semantics.
2. `test_question_card.dart` — required question number, stem, options, selection, and callback.
3. `result_card.dart` — required API-derived percentage, score, marks, and exam type; `CustomPaint`
   ring with equivalent text semantics.
4. `analysis_card.dart` — required analysis rows from the caller.
5. `schedule_card.dart` — required day, date, topics, completion, and progress values.

**Verify:** constructors cannot omit required domain values. Production components contain no default
question, score, analysis row, schedule topic, exam, or ID.

### Step 9. Implement loading, empty, and error states

Create `empty_state.dart`, `error_state.dart`, and `skeleton_loader.dart`. Empty and error messages
are caller-provided from the real request state. Skeletons indicate loading only and never resolve
into fabricated records.

**Verify:** widget tests verify retry callbacks, live-region/semantics behavior, and static reduced-
motion skeletons.

### Step 10. Add the development-only Flutter catalog

Add `design_system_catalog_page.dart` and register `/design-system` only in debug/development
configuration. Show every component and applicable state. Fixed catalog labels are visual fixtures;
keep them in this file/tests and never inject them into production feature providers.

```bash
flutter run --dart-define=EKLAVYA_BASE_URL=http://10.0.2.2:8000
flutter test test/core/design_system --update-goldens
flutter test test/core/design_system
```

**Verify:** every component renders; goldens are reviewed; no catalog route is enabled in release.

### Step 11. Accessibility and performance sign-off

Run Flutter accessibility scanner/semantics checks, text scaling, keyboard navigation where
supported, and reduced-motion checks. Compare blur/fallback frames on lower-performance targets.

**Verify:** contrast targets in `text.md` §8 hold, targets are at least 48 logical pixels, no long
list applies per-row blur, and no frame-blocking blur loop exists.

## Part B — Superadmin web

### Step 12. Create the token layer

Create `Frontend_Website/src/styles/tokens.css` per `text.md` §5: Tailwind v4 `@theme` tokens,
`.glass`, `.glass-strong`, `.glass-border`, `.glass-fallback`, and `@supports` fallback. Import it
in `src/index.css` after `@import "tailwindcss";`.

**Verify:** all variables match the shared values and the import order is correct.

### Step 13. Create web glass components

Create one file per component in `src/components/glass/`: `GlassCard.tsx`, `GlassButton.tsx`,
`GlassIconButton.tsx`, `GlassTextField.tsx`, `GlassChip.tsx`, `GlassFilterChip.tsx`,
`GlassDialog.tsx`, `GlassBottomSheet.tsx`, `GlassProgress.tsx`, `StatusPill.tsx`,
`TestQuestionCard.tsx`, `ResultCard.tsx`, `AnalysisCard.tsx`, `ScheduleCard.tsx`, `EmptyState.tsx`,
`ErrorState.tsx`, `SkeletonLoader.tsx`, `DataTable.tsx`, `FilterBar.tsx`, `ConfirmDialog.tsx`, and
`PermissionDeniedState.tsx`.

Use token classes, existing `lucide-react` and KaTeX support, ARIA labels/alerts/sort states, and
keyboard-operable controls. Data rows and feature-card values are required props from real API data;
no component supplies fallback records.

**Verify:** all components exist and the project type-checks.

### Step 14. Add the web preview route

Add `/design-system` inside `BrowserRouter`, outside `AppShell`, rendering
`src/pages/DesignSystemPreview.tsx`. Local state toggles are allowed for visual states only. This
development page must not become a source of production feature data.

**Verify:** the route renders every web component and is not linked as a production feature.

### Step 15. Build and check the browser

```bash
cd Frontend_Website
npm run build
npm run dev
```

Open `http://localhost:3000/design-system`.

**Verify:** build succeeds, every component renders, contrast spot-checks pass, and emulated
`prefers-reduced-motion: reduce` disables shimmer/transitions.

### Step 16. Complete sign-off

Run Flutter analyze/tests/goldens and the web build, then check every item in `expected-output.md`.
