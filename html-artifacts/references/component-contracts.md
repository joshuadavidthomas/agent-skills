# Component Contracts

Use these components when the artifact needs their job. They provide deterministic geometry, responsive behavior, state styling, and accessibility mechanics while leaving typography, palette, and subject-specific composition open.

## Required Setup

Add the component style slot, then run the inliner:

```html
<style id="html-artifacts-components"></style>
```

```bash
python scripts/inline-components.py /absolute/path/to/artifact.html
```

The script inserts the complete contents of `assets/artifact-components.css` and is safe to rerun after the stylesheet changes. Do not link to the file: the artifact must remain one offline document.

Keep the component slot and all subject overrides in `<head>`, in this order, then apply `ha-root` to `<body>` or the artifact's top-level wrapper:

```html
<head>
  <style id="html-artifacts-components"></style>
  <style id="artifact-theme">
    .ha-root {
      --ha-canvas: #f4f0e7;
      --ha-surface: #fffdf8;
      --ha-ink: #25241f;
      --ha-muted: #625f56;
      --ha-accent: #9b3f23;
      --ha-accent-soft: #f4dfd5;
      --ha-positive: #126b68;
      --ha-positive-soft: #dceceb;
      --ha-negative: #8c3a28;
      --ha-negative-soft: #f4dfd5;
    }
  </style>
</head>
<body class="ha-root">…</body>
```

Override tokens; do not fork component geometry unless the component cannot represent the explanation. Keep the artifact's own typography, spacing rhythm, and decorative language outside the component file.

## Page Grid and Figure Breakout

Keep the section lead-in and follow-up aligned with neighboring sections. Break out the visual itself:

```html
<section class="ha-shell ha-section-grid">
  <div class="ha-section-rail">
    <p>One purposeful interaction</p>
    <p>Reader question: …</p>
  </div>

  <h2 class="ha-section-main">Where does each safeguard intervene?</h2>

  <figure class="ha-figure ha-breakout">
    <!-- Figure frame -->
  </figure>

  <div class="ha-section-main">
    <!-- Static equivalent and follow-up -->
  </div>
</section>
```

Do not make the entire section full-width merely because the figure needs more span.

## Stepper Figure

Use the stepper geometry for a discrete process, algorithm trace, protocol, lifecycle, or staged comparison. The base component is static: figure header, ordered steps, and caption. Add the selection control and outcome panels only when selecting a stage answers a named reader question. Use the canonical inline SVG connectors; do not draw arrows with characters, borders, clip paths, or pseudo-elements. CSS positions each SVG, while SVG owns the stroke and arrowhead on one coordinate system. The component hides connectors when it recomposes vertically.

```html
<figure class="ha-figure" aria-labelledby="workflow-title" aria-describedby="workflow-caption">
  <div class="ha-figure-frame" data-treatment="inline">
    <header class="ha-figure-header">
      <div>
        <h3 class="ha-figure-title" id="workflow-title">Move a request through the workflow</h3>
        <p class="ha-figure-summary">The complete process stays visible while the selected stage explains its responsibility and consequence.</p>
      </div>

      <!-- Optional: include only when stage selection teaches something. -->
      <fieldset class="ha-control ha-controls">
        <legend class="ha-visually-hidden">Workflow stage</legend>
        <div class="ha-control-meta">
          <span>Selected stage</span>
          <output class="ha-control-output" id="stage-output" for="stage-control" role="status">3 · Outline</output>
        </div>
        <div class="ha-control-row">
          <input
            class="ha-range"
            id="stage-control"
            name="workflow-stage"
            type="range"
            min="1"
            max="7"
            step="1"
            value="3"
            aria-label="Selected workflow stage"
            aria-valuetext="Stage 3, Outline"
          >
          <button class="ha-button" id="reset-stage" type="button">Reset</button>
        </div>
        <div class="ha-control-ends" aria-hidden="true">
          <span>Frame</span>
          <span>Deliver</span>
        </div>
      </fieldset>
    </header>

    <div class="ha-stepper-region">
      <!-- Give the marker a unique ID when a page contains more than one stepper. -->
      <svg class="ha-svg-defs" aria-hidden="true" focusable="false">
        <defs>
          <marker
            id="workflow-arrowhead"
            viewBox="0 0 8 8"
            refX="8"
            refY="4"
            markerWidth="8"
            markerHeight="8"
            markerUnits="userSpaceOnUse"
            orient="auto"
          >
            <path class="ha-step-arrowhead" d="M 0 0 L 8 4 L 0 8 Z"></path>
          </marker>
        </defs>
      </svg>

      <ol class="ha-stepper" role="list" style="--ha-step-count: 7">
        <li class="ha-step" data-state="complete">
          <span class="ha-step-node">1</span>
          <h4 class="ha-step-name">Frame</h4>
          <p class="ha-step-detail">request → question</p>
          <p class="ha-step-state">Complete</p>
          <svg class="ha-step-connector" aria-hidden="true" focusable="false">
            <line x1="0" y1="50%" x2="100%" y2="50%" marker-end="url(#workflow-arrowhead)"></line>
          </svg>
        </li>
        <li class="ha-step" data-state="complete">
          <span class="ha-step-node">2</span>
          <h4 class="ha-step-name">Ground</h4>
          <p class="ha-step-detail">sources → ledger</p>
          <p class="ha-step-state">Complete</p>
          <svg class="ha-step-connector" aria-hidden="true" focusable="false">
            <line x1="0" y1="50%" x2="100%" y2="50%" marker-end="url(#workflow-arrowhead)"></line>
          </svg>
        </li>
        <li class="ha-step" data-state="active" aria-current="step">
          <span class="ha-step-node">3</span>
          <h4 class="ha-step-name">Outline</h4>
          <p class="ha-step-detail">ledger → argument</p>
          <p class="ha-step-state">Active stage</p>
          <svg class="ha-step-connector" aria-hidden="true" focusable="false">
            <line x1="0" y1="50%" x2="100%" y2="50%" marker-end="url(#workflow-arrowhead)"></line>
          </svg>
        </li>
        <!-- Continue with the remaining stages; omit the connector from the final step. -->
      </ol>
    </div>

    <!-- Optional: changed content remains navigable; stage-output is the sole live status. -->
    <div class="ha-outcomes">
      <section class="ha-outcome">
        <h4 class="ha-outcome-label">Selected responsibility</h4>
        <p class="ha-outcome-copy" id="responsibility-output">Write the argument before choosing visual chrome.</p>
      </section>
      <section class="ha-outcome" data-tone="negative">
        <h4 class="ha-outcome-label">Blocked · generic pressure</h4>
        <p class="ha-outcome-copy" id="blocked-output">A chrome-first page with no governing question.</p>
      </section>
      <section class="ha-outcome" data-tone="positive">
        <h4 class="ha-outcome-label">Preserved · useful capacity</h4>
        <p class="ha-outcome-copy" id="preserved-output">A focused spatial model chosen for the reader's task.</p>
      </section>
    </div>
  </div>

  <figcaption class="ha-figure-caption" id="workflow-caption">
    <strong>Textual equivalent:</strong> …
  </figcaption>
</figure>
```

### Figure treatment

- Use `data-treatment="inline"` by default in document mode. It removes the app-like outer frame while preserving the component's internal geometry and rules.
- Omit `data-treatment` only when the interactive model is a genuinely separate tool or work surface that needs a bounded region.
- Do not choose the framed treatment merely to make the visual feel important.

### Selection enhancement

- Start with the static stepper. Add `.ha-controls` and `.ha-outcomes` only when the interaction passes the reader question → action → immediate answer test.
- Use the `<output role="status">` as the only live announcement. Keep outcomes available in normal reading order; do not make the full outcome region live.
- Use `<fieldset>` and `<legend>` to name the control group.
- The reset button restores the authored default state, not necessarily stage 1.

### Stepper invariants

- Keep every `.ha-step` as a direct child of `.ha-stepper`.
- Set `--ha-step-count` to the actual number of children.
- Use only `complete`, `active`, or `pending` for `data-state`.
- Keep exactly one active step and set `aria-current="step"` on it.
- Preserve the node, name, detail, and state elements in that order. Add one `.ha-step-connector` SVG after the state in every non-final step; omit it from the final step.
- Use one unique marker ID per stepper and reference it from every connector line in that stepper.
- Do not add arrow characters, CSS-drawn arrowheads, per-step padding, or margins that shift nodes inside their grid cells. Connector geometry belongs to the SVG component.
- At the wide layout, leave equal visual clearance between the source node and stem and between the arrow tip and target node. The stem must meet the arrowhead base without a visible break, and all connector parts must share the nodes' vertical centerline. Browser-measured clearances, joins, and centerlines must agree within one CSS pixel.
- Keep labels concise. If names or details cannot fit at the wide composition width, simplify the labels or choose another representation.
- For more than nine stages, group them into phases or choose a different visual.

### Interaction update contract

When the selected stage changes, update all representations in one render function:

```javascript
function renderStage(stageNumber) {
  const index = stageNumber - 1;
  const stage = stages[index];

  control.value = String(stageNumber);
  control.setAttribute("aria-valuetext", `Stage ${stageNumber}, ${stage.name}`);
  output.textContent = `${stageNumber} · ${stage.name}`;
  responsibility.textContent = stage.responsibility;
  blocked.textContent = stage.blocked;
  preserved.textContent = stage.preserved;

  stepElements.forEach((element, elementIndex) => {
    const current = elementIndex + 1;
    const state = current < stageNumber ? "complete" : current === stageNumber ? "active" : "pending";
    element.dataset.state = state;
    if (state === "active") {
      element.setAttribute("aria-current", "step");
    } else {
      element.removeAttribute("aria-current");
    }
    element.querySelector(".ha-step-state").textContent =
      state === "complete" ? "Complete" : state === "active" ? "Active stage" : "Not reached";
  });
}
```

## Outcome Panels Without a Stepper

Use `.ha-outcomes` and `.ha-outcome` independently for a three-part explanatory contrast such as observed/risk/implication or current/problem/proposed. Outcomes are neutral by default. Add `data-tone="negative"` or `data-tone="positive"` only when the content has that actual semantic meaning; do not color every three-part comparison.

At intermediate widths, the first outcome spans the row and the two contrasting peers align below it. At narrow widths, all outcomes stack. Do not override this with viewport-only CSS.

## Secondary Wide Content

Use `.ha-scroll-region` only for irreducibly wide secondary material such as a dense evidence table. Give it a visible cue, label, and keyboard focus:

```html
<div>
  <p class="ha-scroll-cue" id="evidence-scroll-cue">Scroll horizontally to see all evidence columns →</p>
  <div
    class="ha-scroll-region"
    tabindex="0"
    aria-label="Scrollable evidence table"
    aria-describedby="evidence-scroll-cue"
  >
    <table>…</table>
  </div>
</div>
```

Do not use this class to rescue a primary narrative visual. Recompose the visual instead.

## What Not to Standardize

Do not add shared components for:

- hero sections or page headers
- generic cards, badges, or KPI tiles
- fixed palettes, fonts, shadows, or decorative motifs
- universal architecture, timeline, or data-chart visuals
- prose hierarchy that should reflect the subject and audience

Add a component only after the same geometry or browser-mechanics failure appears across materially different artifacts. A component earns its place by removing repeatable implementation judgment, not by capturing one artifact's appearance.
