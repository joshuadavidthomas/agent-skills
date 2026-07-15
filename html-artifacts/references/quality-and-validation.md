# Quality and Validation

Use this as an implementation and release checklist, not as a visual template.

## Document Shell

Every standalone file needs:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Specific artifact title</title>
</head>
```

Set `lang` to the artifact's actual language and make `<title>` identify the subject and mode. Add a short `<meta name="description">` when the file may be shared. Do not add framework, social-card, or application metadata by habit.

## Packaging

The default deliverable is a true offline HTML file:

- inline CSS in `<style>`
- inline JavaScript in `<script>`
- inline SVG for diagrams
- embedded assets as data URIs only when essential
- no CDN scripts, stylesheets, fonts, images, or analytics
- no `fetch`, XHR, WebSockets, service workers, or backend dependency

Prefer system fonts. A “single HTML file” that loads half its interface from the network is not self-contained.

Use a framework only for enough state complexity to justify a build. Bundle and inline the framework, styles, assets, and data into the final file, then test that file offline. Do not ship the project scaffold as the artifact.

Use a bundled directory instead of one file only when large screenshots, video, downloadable datasets, or a graph payload make embedding impractical. State the reason in the delivery note.

## Safe Embedded Data

Prefer inert JSON rather than executable assignments:

```html
<script type="application/json" id="artifact-data">
  {"example":"value"}
</script>
```

When serializing untrusted or source-derived text:

- encode with a real JSON serializer
- replace `<` with `\u003c` before embedding to prevent `</script>` breakout
- parse with `JSON.parse(element.textContent)`
- render text with `textContent`, not `innerHTML`
- HTML-escape code and command output
- omit secrets, environment variables, tokens, credentials, and unrelated private content

If the artifact contains source excerpts, include only the smallest passage needed to support the explanation.

## Information Design

### Hierarchy

- Put the conclusion or governing question before the visual system.
- Use descriptive headings that make the page skimmable.
- Let typography, alignment, and whitespace establish hierarchy before adding containers.
- Use cards only for genuine peers with repeated structure or independent actions.
- Keep primary evidence, caveats, warnings, and required instructions visible.
- Use `<details>` only for secondary material; label the summary specifically.
- Keep material side by side when comparison is the task.

### Composition

Choose one dominant composition and make everything else quiet support:

- **Annotated map:** a restrained thesis column leads into one large system figure, followed by evidence and a source index.
- **Aligned comparison:** before and after share geometry and labels, with the changed relationships annotated between them.
- **Mechanism stage:** the model stays visible while a narrow explanation rail contains the current claim and controls.
- **Investigation spine:** chronology runs in one direction while evidence, hypotheses, and confidence sit beside the relevant event.
- **Data story:** headline finding, directly labeled chart, counterexample/segment, then methods and limits.

These are information arrangements, not visual templates. Vary type, spacing, notation, and color from the subject.

### Visual language

- Derive color and notation from the source project or subject when possible.
- Use a restrained palette with semantic labels; color supports meaning rather than creating it.
- Direct-label lines, nodes, values, and states instead of making readers shuttle to a legend.
- Keep diagrams at one abstraction level.
- Use syntax color sparingly in code excerpts; annotation and emphasis matter more than rainbow highlighting.
- Avoid ornamental dashboard tropes: fake KPIs, pill badges, progress rings, chart chrome, and dense card mosaics.

### Typography and density

- Use a readable body measure, usually around 60–80 characters.
- Keep body text large enough for sustained reading without making headings theatrical.
- Preserve technical density where the reader needs it; do not stretch three paragraphs across six viewport-height sections.
- Wrap long paths and code labels or give them intentional horizontal scrolling.

## Interaction

Use this test for every control:

> What reader question does this answer, what action expresses that question, and what immediately changes?

Good patterns:

- before/after with aligned geometry
- step-through execution with the current boundary and state highlighted
- search/filter for a large evidence set
- details-on-demand while context remains visible
- zoom/pan/reset for an irreducibly large diagram
- sliders or presets for causal variables
- linked highlighting across two representations

Remove:

- decorative theme toggles
- animated backgrounds or particles
- hover effects on non-interactive content
- controls that only rearrange the same information
- autoplay tours
- scrolljacking and forced snapping
- tooltips as the only source of exact values or definitions

For meaningful state in tabs, filters, or disclosures, preserve it in the URL hash or query string when practical. Always provide reset for a manipulated model.

## Accessibility

Minimum contract:

- semantic `header`, `nav`, `main`, `section`, `aside`, and `footer` where they fit
- one clear `h1`, then ordered heading levels
- native controls with accessible names
- all pointer interactions available by keyboard
- visible `:focus-visible` styles
- no hover-only content
- text contrast of at least 4.5:1; large text and meaningful graphics/UI at least 3:1
- no color-only statuses, lines, or state changes
- meaningful SVG `<title>` and `<desc>` plus a nearby textual summary for complex graphics
- decorative SVG hidden from the accessibility tree
- live result changes announced when a screen-reader user otherwise would not detect them
- touch targets at least 24 CSS px in each dimension, preferably larger
- no fixed-height text containers that clip zoomed or translated content

An accessible name such as “diagram” or “line chart” is not an accessible explanation. Describe the message and provide the underlying relationships or values in text/table form.

## Responsive Composition

Test at 320–390 px and at a wide desktop viewport.

- Recompose rather than uniformly shrink.
- Make nested figures respond to their **allocated width** with intrinsic layout or container queries; viewport breakpoints alone are insufficient.
- Set `min-width: 0` on flexible grid/flex children.
- Stack side-by-side regions only when labels still make comparison possible.
- Keep essential chart annotations visible; move secondary notes below the visual.
- Give wide tables and diagrams intentional overflow plus a textual equivalent.
- Keep that overflow inside the intended component: at narrow widths, assert the document's scroll width does not exceed the viewport (allowing a pixel for rounding).
- Make sticky navigation horizontally scrollable or replace it on narrow screens.
- Avoid viewport-height locks and absolute positioning for primary document flow.

Two-dimensional scrolling can be acceptable for a complex diagram or data table, not for the whole page.

## Motion

Use motion only to preserve continuity or encode state, time, causality, or spatial change.

- trigger meaningful motion from user action rather than autoplay
- make animation interruptible
- never use motion as the only indication of a change
- avoid `transition: all`
- honor reduced-motion preferences

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Do not merely remove an explanatory animation in reduced-motion mode. Replace it with immediate state changes, annotations, or static small multiples so the information survives.

## Print

A document-mode artifact should remain useful when printed or saved as PDF.

```css
@media print {
  nav, .controls, .no-print { display: none !important; }
  details { display: block; }
  details > * { display: block !important; }
  body { background: white; color: black; }
  a[href]::after { content: " (" attr(href) ")"; }
  pre, blockquote, figure, table { break-inside: avoid; }
}
```

Adapt the snippet rather than copying it blindly: local anchors should not print as noisy URLs, and interactive models need a canonical annotated state or static small multiples.

## Visual Polish Gate

Run this after the artifact is correct and before calling it composed. Instructions—not shared visual components—own these decisions because the right answer depends on the subject.

1. **Give the dominant composition enough span without abandoning the page grid.** Do not trap a wide diagram, comparison, or interactive model in a prose column. Widen or break out the visual itself while keeping its lead-in and follow-up content aligned with surrounding sections; change the whole section's layout mode only when the narrative genuinely changes mode. At the wide validation viewport, the complete primary overview must fit without horizontal scrolling.
2. **Budget width before styling.** Name the minimum readable width of repeated items. If the allocated width is smaller, span wider, simplify, group, or recompose.
3. **Respond to allocated width.** Use intrinsic layout or a component-level container query when a nested figure can become narrow inside a wide viewport.
4. **Treat overflow as an exception.** Primary narrative visuals must recompose rather than scroll. For an irreducibly wide secondary table or graph, label the scroll region, show a visible overflow affordance, and provide a textual equivalent.
5. **Keep meaningful type above the floor.** No meaningful text below 12 CSS px at 100% zoom; prefer 13–14 px for labels. Do not put prose in a column narrower than roughly 24 characters.
6. **Keep peer geometry parallel.** Repeated peers share type role, padding, alignment, and available width. A difference must encode hierarchy or state, not result from accidental wrapping.
7. **Expose the selected state.** A slider, stepper, tab set, or filter shows its current value beside the control. For seven or fewer discrete states, expose names, marks, or direct step labels.
8. **Prefer direct labels over legends.** Remove a legend when the figure already labels each state or relationship. Never let legend separators orphan when text wraps.
9. **Use one primary containment cue per region.** Choose whitespace, rule, fill, border, or shadow. Add another only when it communicates nesting, interactivity, or state.
10. **Perform a deletion pass.** Remove redundant legends, frames, fills, metadata, instructions, and repeated explanations.
11. **Inspect at 1:1 scale.** Review the dominant composition in a screenshot crop at its actual rendered size, not only as part of a downscaled full-page image. Check type, wrapping, alignment, control finish, and whether the intended first glance is obvious.

Use `assets/artifact-components.css` and the canonical markup in `references/component-contracts.md` for deterministic geometry: page-grid breakout, figure shells, controls, steppers/connectors, outcome panels, and scroll containment. These components own alignment, responsive state layouts, and accessibility mechanics. Customize their tokens for the subject; do not hand-roll an equivalent component or treat the defaults as the artifact's visual identity. Fonts, palette choices, prose hierarchy, charts, diagrams, and decorative language still come from the subject.

## Browser Release Gate

Validate the final artifact in a real browser.

### Rendering

- title and primary conclusion are visible
- hierarchy remains clear when squinting or zooming out
- no clipped, overlapping, or off-canvas content
- process connectors use the canonical inline SVG rather than CSS-drawn arrowheads and are measured, not eyeballed: at the wide layout, source and target clearances match within one CSS pixel, and the SVG line, marker, and nodes share one vertical centerline
- no page-level horizontal overflow at narrow widths; wide tables/diagrams scroll inside their own labeled region
- long paths, code, tables, and diagrams behave intentionally
- desktop and mobile screenshots both look composed
- print output preserves reading order and evidence

### Runtime

- zero uncaught page/console errors
- zero failed resource requests
- zero unexpected network requests in offline mode
- every control works at boundaries and after reset
- keyboard behavior matches pointer behavior
- direct/deep links restore the intended state when implemented
- reduced-motion mode remains comprehensible

### Accuracy

- repository/dataset identity and revision are visible
- every important factual claim maps to a source path, line range, query, or provided input
- before and after are not accidentally reversed
- counts, units, dates, time zones, and denominators are explicit
- inferred and proposed content is labeled
- omissions and unknowns remain visible
- code excerpts match the cited source

### Accessibility

Run an automated accessibility checker when available, then manually verify:

- heading order and landmarks
- keyboard reachability and focus visibility
- accessible names and changed-state announcements
- diagram/chart text alternatives
- contrast and non-color cues
- zoom/reflow at narrow width

Automated checks do not validate whether the explanation itself makes sense.

## Failure Conditions

Do not present the artifact as complete when:

- it depends on a network resource without the user's approval
- primary content is unavailable without interaction
- a diagram is unsupported by source evidence
- the final bundled file was not the file tested
- mobile reflow makes the argument incomprehensible
- a control has no keyboard equivalent
- private material was published or uploaded without explicit permission

Fix the issue or report the exact unverified condition.
