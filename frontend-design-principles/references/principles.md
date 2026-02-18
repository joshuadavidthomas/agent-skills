# Technical Principles

Implementation details for the craft foundations. Load when you need specific values, code patterns, or dark mode guidance.


## Spacing System

All spacing uses a base unit. Pick 4px or 8px and use multiples throughout.

| Value | Use |
|-------|-----|
| 4px | Micro spacing (icon gaps, tight elements) |
| 8px | Tight spacing (within components) |
| 12px | Standard spacing (between related elements) |
| 16px | Comfortable spacing (section padding) |
| 24px | Generous spacing (between sections) |
| 32px+ | Major separation |

Every spacing value should be explainable as "X times the base unit." Random values signal no system.

## Symmetrical Padding

Padding should be balanced. If top is 16px, bottom should be 16px. Horizontal can differ from vertical when content needs it, but avoid arbitrary asymmetry.

```css
/* Good */
padding: 16px;
padding: 12px 16px; /* horizontal needs more room */

/* Bad - arbitrary asymmetry */
padding: 24px 16px 12px 16px;
```


## Surface & Token Architecture

Professional interfaces don't pick colors randomly — they build systems.

### The Primitive Foundation

Every color should trace back to a small set of primitives:

- **Foreground** — text colors (primary, secondary, muted)
- **Background** — surface colors (base, elevated, overlay)
- **Border** — edge colors (default, subtle, strong)
- **Brand** — your primary accent
- **Semantic** — functional colors (destructive, warning, success)

Don't invent new colors. Map everything to these primitives.

### Surface Elevation Hierarchy

Surfaces stack. A dropdown sits above a card which sits above the page. Build a numbered system:

```
Level 0: Base background (the app canvas)
Level 1: Cards, panels (same visual plane as base)
Level 2: Dropdowns, popovers (floating above)
Level 3: Nested dropdowns, stacked overlays
Level 4: Highest elevation (rare)
```

In dark mode, higher elevation = slightly lighter. In light mode, higher elevation = slightly lighter or uses shadow.

### The Subtlety Principle

The difference between elevation levels should be subtle — a few percentage points of lightness, not dramatic jumps. In dark mode, surface-100 might be 7% lighter than base, surface-200 might be 9%, surface-300 might be 12%. You can barely see it, but you feel it.

### Text Hierarchy via Tokens

Build four levels:

- **Primary** — default text, highest contrast
- **Secondary** — supporting text, slightly muted
- **Tertiary** — metadata, timestamps, less important
- **Muted** — disabled, placeholder, lowest contrast

Use all four consistently. If you're only using two, your hierarchy is too flat.


## oklch Color Implementation

Use oklch for all color definitions. It has perceptually uniform lightness, making programmatic manipulation predictable.

```css
/* oklch(lightness chroma hue / alpha) */
--accent: oklch(55% 0.24 264);
--surface: oklch(98% 0 0);

/* Lightness: 0% (black) to 100% (white) */
/* Chroma: 0 (gray) to ~0.4 (vivid) — most UI uses 0.1-0.25 */
/* Hue: 0-360 (0=pink, 90=yellow, 180=cyan, 270=blue) */
```

Use `color-mix()` for derived colors instead of manual calculation:

```css
--accent-hover: color-mix(in oklch, var(--accent), black 10%);
--accent-subtle: color-mix(in oklch, var(--accent), transparent 90%);
--accent-light: color-mix(in oklch, var(--accent), white 80%);
```

### Contrast Hierarchy Example

```css
--foreground: oklch(15% 0 0);  /* Primary text */
--secondary: oklch(40% 0 0);   /* Supporting text */
--muted: oklch(55% 0 0);       /* Tertiary, less important */
--faint: oklch(75% 0 0);       /* Placeholder, disabled */
```


## Border Radius Consistency

Pick a system and commit. Sharper feels technical, rounder feels friendly:

- **Sharp**: 4px, 6px, 8px
- **Soft**: 8px, 12px, 16px
- **Minimal**: 2px, 4px, 6px

Don't mix systems within one interface. Use small radius for inputs and buttons, medium for cards, large for modals.


## Depth Strategies

Choose ONE approach and commit:

### Borders-only (flat)

Clean, technical, dense. Just subtle borders to define regions. Works for utility-focused tools.

```css
--border: oklch(0% 0 0 / 0.08);
--border-subtle: oklch(0% 0 0 / 0.05);
border: 0.5px solid var(--border);
```

### Single shadow

Soft lift without complexity.

```css
--shadow: 0 1px 3px oklch(0% 0 0 / 0.08);
```

### Layered shadows

Rich, premium, dimensional. Multiple layers for realistic depth.

```css
--shadow-layered:
  0 0 0 0.5px oklch(0% 0 0 / 0.05),
  0 1px 2px oklch(0% 0 0 / 0.04),
  0 2px 4px oklch(0% 0 0 / 0.03),
  0 4px 8px oklch(0% 0 0 / 0.02);
```

### Surface color shifts

Background tints establish hierarchy. A card at `oklch(100% 0 0)` on `oklch(98% 0 0)` already feels elevated.

Mixing approaches within one interface creates visual inconsistency.


## Typography Scale

Use a constrained scale:

- **Display**: 32px, 24px (headlines, hero text)
- **Body**: 16px, 14px (primary content)
- **Small**: 13px, 12px, 11px (labels, captions, metadata)

Headlines: 600 weight, tight letter-spacing (-0.02em).
Body: 400-500 weight, standard tracking.
Labels: 500 weight, slight positive tracking for uppercase.

### Monospace for Data

Numbers, IDs, codes, timestamps belong in monospace. Use `font-variant-numeric: tabular-nums` for columnar alignment.


## Animation

- **Micro-interactions**: 150ms
- **Transitions**: 200-250ms
- **Easing**: `cubic-bezier(0.25, 1, 0.5, 1)` or similar smooth curves

No bouncy/spring effects in professional interfaces.


## Dark Mode

Use CSS `light-dark()` for automatic theming:

```css
:root {
  color-scheme: light dark;

  --surface: light-dark(oklch(100% 0 0), oklch(15% 0 0));
  --text: light-dark(oklch(20% 0 0), oklch(95% 0 0));
  --border: light-dark(oklch(0% 0 0 / 0.08), oklch(100% 0 0 / 0.1));
}
```

Dark mode considerations:

- **Borders over shadows** — shadows are less visible on dark backgrounds
- **Reduce chroma for status colors** — vivid colors feel harsh on dark
- **Same hierarchy structure, inverted lightness values**
- **Higher elevation = slightly lighter** (opposite of light mode shadows)


## Custom Controls

Never use native form elements (`<select>`, `<input type="date">`) for styled UI. They render OS-native widgets that can't be styled. Build custom components:

- Custom select: trigger button + positioned dropdown
- Custom date picker: input + calendar popover
- Custom checkbox/radio: styled div with state management

Custom select triggers must use `display: inline-flex` with `white-space: nowrap` to keep text and chevron icons on the same row.


## Iconography

Use a consistent icon library (Phosphor, Lucide, Heroicons). Icons should clarify, not decorate — if removing an icon loses no meaning, remove it.

Give standalone icons presence with subtle background containers. Icons next to text should align optically, not mathematically.


## States

Every interactive element needs states:

- **Default** — resting state
- **Hover** — mouse over
- **Active** — being clicked/pressed
- **Focus** — keyboard focused (visible focus ring)
- **Disabled** — not interactive

Data displays need states too:

- **Loading** — skeleton or spinner
- **Empty** — helpful empty state, not just blank
- **Error** — clear error message with recovery path

Missing states feel broken.
