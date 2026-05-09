# Sources

This file records where the current `skill-authoring` skill came from and what each source contributed. It is maintainer provenance, not runtime instruction.

## Source Inventory

| Source | Trust | Contribution | Constraints |
|--------|-------|--------------|-------------|
| [Agent Skills specification](spec/specification.md) | High | Format constraints, required frontmatter, optional directories, progressive disclosure, validation | Local copy can become stale; refresh from agentskills.io |
| [What are skills?](spec/what-are-skills.md) | High | Discovery, activation, execution model | Conceptual overview only |
| [skills-ref](spec/skills-ref/) | High | Structural validation reference implementation | Validator checks structure, not skill quality |
| `sources/anthropic/` | High | Official skill-creator patterns, packaging expectations, scripts/references/assets model | Upstream snapshot lacks per-source commit provenance in this repo |
| `sources/everyinc/` | Medium | Router patterns, workflow templates, progressive disclosure examples | Source is project-specific and may include local assumptions |
| `sources/obra/` | Medium | TDD-style skill testing, pressure scenarios, persuasion/rationalization handling | Strongest for discipline-enforcing skills; can be too heavy for reference skills |
| `sources/pproenca/` | Medium | Granular authoring rules organized by impact | Curated guidance; verify against current spec when rules conflict |
| `sources/pytorch/` | Medium | Simple single-file skill-writing approach | Project-specific Claude conventions may not generalize |
| David Cramer, "Skill Synthesis" (`https://cra.mr/skill-synthesis`) | Medium | Source-backed synthesis loop, use of project history, false-positive/false-negative refinement | Blog/article source; adapt principles rather than copying implementation details |
| `sources/getsentry/` | Medium | `SOURCES.md` provenance convention, precision-before-addition, mode selection, holdout examples, `SKILL.md` as router | Sentry workflow is heavier and more Claude-specific than this repository should adopt wholesale |

## Synthesis Decisions

- Decision: Keep `SKILL.md` concise and use it as a runtime router rather than a teaching essay.
  - Supported by: Agent Skills spec, Anthropic source, EveryInc source, Sentry `skill-writer`.
  - Reason: The audience is an LLM agent that needs operational routing, constraints, examples, and validation steps more than conceptual explanation.

- Decision: Add `workflows/synthesize.md` rather than folding synthesis guidance into `create.md`.
  - Supported by: Skill Synthesis article and Sentry `skill-writer` synthesis path.
  - Reason: Source-backed synthesis is important but not required for every small skill.

- Decision: Use `SOURCES.md` as an optional maintainer artifact for material synthesis work.
  - Supported by: Sentry `skill-writer`.
  - Reason: Provenance, trust, decisions, and gaps matter for maintainers but usually should not consume runtime context.

- Decision: Add precision-before-addition as a rule.
  - Supported by: Sentry `skill-writer` and local repository preference for reducing entropy.
  - Reason: Skill quality often improves by narrowing existing guidance, not by adding more files.

- Decision: Mention holdout examples for behavior-sensitive skills.
  - Supported by: Sentry `skill-writer` iteration evidence and the existing local testing workflow.
  - Reason: Prevents overfitting skill changes to the last failure case.

## Coverage and Gaps

- Covered: Agent Skills format, trigger-focused descriptions, progressive disclosure, creation, testing, debugging, refinement, source-backed synthesis, provenance, precision passes.
- Gaps: Per-source commit provenance for `sources/*` is missing because `.source` files are not present. `update-sources.sh` can regenerate them later.
- Needs validation: Whether `SOURCES.md` should become a recommended convention for all complex skills in this repository or only for skill-authoring and synthesis-heavy skills.

## Change Log

- 2026-05-08: Added Sentry/David Cramer skill synthesis practices: source-backed synthesis workflow, provenance convention, precision-before-addition, and holdout examples.
- 2026-05-08: Vendored `getsentry/skills` `skill-writer` under `sources/getsentry/` and added update-script provenance.
- 2026-05-08: Reworked `SKILL.md` from a teaching document into an agent-facing workflow guide with path selection, inline fallback, cardinal rules, placement rules, and output format.
