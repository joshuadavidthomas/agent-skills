# feature-planning-artifacts

Creates staged HumanLayer-style planning artifacts for high-value opportunities or NNN plans. Use it when a broad plan needs reconnaissance, design choices, vertical slicing, and a final executor-safe plan before implementation.

The skill is intentionally gated: write or update the current-stage artifact, stop for review, then continue only after acceptance or explicit instruction. The usual path is design discussion → review/iteration → structure outline → review/iteration → final plan, with research questions and research used when current-state uncertainty is high enough to deserve durable artifacts.

Open and resolved questions are handled inside the design discussion. Artifacts should define success, evals/regression checks, autonomy boundaries, and standing-policy recommendations when useful.

## References

- `SKILL.md` — runtime workflow and update rules.
- `references/artifact-templates.md` — concise artifact shapes.

## Source notes

Synthesized from the vendored HumanLayer Riptide v2 planning skills in `reference/humanlayer-riptide-v2-skills/`, this repository's `coding-standards` skill, and the `improve-codebase-architecture` skill.
