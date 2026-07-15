# HTML Artifacts

Generate self-contained HTML explanations that are easier to inspect, compare, or explore than a Markdown response.

Use this skill for visual codebase walkthroughs, feature explanations, PR and diff reviews, implementation recaps, investigation timelines, data reports, causal interactives, and live presentations. It defaults to a local, offline, document-style artifact: a durable explanation rather than a miniature website or a deck of oversized title slides.

## What It Contains

- [`SKILL.md`](SKILL.md) — the generation workflow, grounding rules, output modes, and delivery contract
- [`references/content-patterns.md`](references/content-patterns.md) — structures for codebases, features, diffs, recaps, incidents, data, comparisons, mechanisms, and presentations
- [`references/component-contracts.md`](references/component-contracts.md) — canonical markup and invariants for deterministic layout and interaction components
- [`assets/artifact-components.css`](assets/artifact-components.css) — inlinable page-grid, figure, control, stepper, outcome, overflow, responsive, focus, motion, and print foundations
- [`scripts/inline-components.py`](scripts/inline-components.py) — deterministically embeds the component stylesheet into the standalone artifact
- [`references/quality-and-validation.md`](references/quality-and-validation.md) — offline packaging, safe data embedding, interaction, accessibility, responsive/print behavior, and browser QA
- [`references/research-basis.md`](references/research-basis.md) — detailed source notes and the reasoning behind the skill's boundaries

The skill deliberately ships no universal page template or visual identity. It does ship a small component foundation for browser mechanics that models should not redraw: grid breakout, figure containment, controls, aligned process connectors, responsive state layouts, outcome panels, and overflow handling. Typography, palette, diagrams, data visuals, and decorative language still come from the subject.

## Sources and Scope

The skill was prompted by Armin Ronacher's joke about agents producing polished-looking HTML “slop” after a task, then synthesized from Thariq Shihipar's writing and example gallery, Anthropic's Artifact documentation and builder skill, Matt Pocock's visual architecture reports, explorable-explanation and information-design guidance, WCAG/MDN, and open-source artifact generators and test harnesses.

It generates ordinary standalone `.html` files. It does not require or emulate Claude's hosted Artifact runtime, and it is not a replacement for production frontend development.
