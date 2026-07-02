# feature-planning-artifacts

Creates staged HumanLayer-style planning artifacts for high-value features, architecture candidates, or selected NNN plans. Use it when the work needs a coherent feature/design bundle: a README index, gated design discussion, structure outline, and optional final executor plan.

The skill is intentionally gated: write or update the current-stage artifact, stop for review, then continue only after acceptance or explicit instruction. The usual path is design discussion → review/iteration → structure outline → review/iteration → final plan, with research questions and research used when current-state uncertainty is high enough to deserve durable artifacts.

Open and resolved questions are handled inside the design discussion. Artifacts should define success, evals/regression checks, autonomy boundaries, standing-policy recommendations, and whether implementation should proceed directly or be split into an improvement plan batch.

## References

- `SKILL.md` — runtime workflow and update rules.
- `references/artifact-templates.md` — concise artifact shapes.

## Source notes

Synthesized from the vendored HumanLayer Riptide v2 planning skills in `reference/humanlayer-riptide-v2-skills/`, this repository's `coding-standards` skill, and the `improve-codebase-architecture` skill.
