---
name: feature-planning-artifacts
description: "Use when creating or updating the next planning artifact for a complex feature: research questions, research, design discussion, structure outline, or final executor plan. Also use when designing before coding, breaking work into vertical slices, or deepening a high-value roadmap item, NNN improve plan, architecture candidate, or HumanLayer-style task."
---

# Feature Planning Artifacts

Create or update one HumanLayer-style planning artifact at a time. This is for work that needs research, design judgment, vertical slicing, or an executor-safe plan before implementation.

Treat detailed planning as meta-work: each artifact should make future implementation safer by defining success, surfacing decisions, turning recurring choices into policy when appropriate, and specifying evals/regression checks.

Open and resolved questions live in the design discussion. Plan iteration updates the plan itself.

## Source Frame

Before writing or updating planning artifacts, load what applies:

- The selected strategic-roadmap item, opportunity card, architecture candidate, or `NNN-*.md` plan.
- `coding-standards` and matching references for design claims.
- Project docs: `AGENTS.md`, `README.md`, `CONTEXT.md`, architecture docs, ADRs, verification config, current VCS state, and relevant existing plans.

The artifact rules in this skill are canonical. Also read the HumanLayer v2 planning skills at `/home/josh/projects/joshuadavidthomas/qrspi/references/humanlayer-riptide-v2-skills/` and use `improve-codebase-architecture` to preserve their current wording and examples.

## Artifact Sequence

Use the canonical structures in [references/artifact-templates.md](references/artifact-templates.md). Prefer `.agents/plans/<effort-slug>/artifacts/<topic-slug>/` for these artifacts. When working inside an existing HumanLayer task, use `.humanlayer/tasks/<task>/` instead. Write artifacts in chronological order with the next available numeric prefix:

```txt
01-research-questions-<slug>.md
02-research-<slug>.md
03-design-discussion-<slug>.md
04-structure-outline-<slug>.md
05-plan-<slug>.md
```

Create or update exactly one artifact per invocation unless the user explicitly asks for a full sequence. Stop after that artifact and summarize the next recommended artifact.

When working inside `.humanlayer/tasks/<task>/`, use `ls -La` to inspect the directory because it may be a symlink. Do not use glob tools or plain `ls` there. Read task artifacts fully, not partial slices, before updating them.

## Workflow

1. **Set artifact scope and success criteria**
   - Identify the exact roadmap item, plan, or candidate being deepened.
   - Choose the single artifact to create or update. If the user did not name one, inspect existing artifacts and choose the next missing artifact in the sequence.
   - Define what “better” means for this artifact before writing: user outcome, architecture leverage, verification strength, executor readiness, reliability, or another concrete standard.
   - Choose the artifact destination, defaulting to `.agents/plans/<effort-slug>/artifacts/<topic-slug>/` when no project convention exists.
   - Inspect existing artifact files and continue numbering; do not overwrite existing artifacts unless iterating them deliberately.

2. **Research questions artifact**
   - Write questions only about how the current codebase, dependencies, and prior artifacts work today.
   - Do not ask “how should we implement…” or leak a preferred solution into the questions.
   - Stop after writing or updating the research-questions artifact.

3. **Research artifact**
   - Require research questions, a user query, or an explicit research scope.
   - Document current behavior, architecture, data flow, tests, constraints, and relevant prior plans.
   - Research is descriptive only. No recommendations, implementation section, or “should” language.
   - Stop after writing or updating the research artifact.

4. **Design discussion artifact**
   - Require completed research unless the user explicitly provides enough current-state context.
   - Present current state, desired end state, explicit non-goals, proposed architecture, design questions, options, recommendations, and resolved decisions.
   - Use coding-standards vocabulary for the actual design pressure.
   - Use architecture/deepening vocabulary for module/interface/depth/seam/adapter/leverage/locality.
   - Include patterns to follow with file references and concise snippets when they materially guide implementation.
   - Identify recurring decisions that should become a standing policy, ADR, repo instruction, template, or eval.
   - Keep unresolved questions in `Design Questions`; move answered ones to `Resolved Design Questions`.
   - If user input is needed, ask the smallest set of questions and update this same document after answers.
   - Stop after writing or updating the design discussion artifact.

5. **Structure outline artifact**
   - Require a design discussion with chosen or clearly recommended direction.
   - Convert the chosen design into vertical phases.
   - Name files likely touched, key signatures or sketches, and validation per phase.
   - The outline should be specific enough to plan from but not a giant implementation dump.
   - Stop after writing or updating the structure outline artifact.

6. **Final plan artifact**
   - Require a structure outline unless the user explicitly provides an equivalent outline.
   - Write an executor-safe plan from the outline.
   - Include current-state evidence, definition of “better,” desired end state, scope/out-of-scope, phase sequence, automated verification, evals/regression checks, manual checks only when meaningful, autonomy boundary, drift checks, STOP conditions, and rejected approaches.
   - Stop after writing or updating the final plan artifact.

## Update Rules

- Document precedence is: plan > structure outline > design discussion > research > source roadmap/NNN plan.
- When iterating, update the existing artifact at its original path.
- Do not blindly accept user corrections. Verify cited files or claims when possible, then update the artifact.
- If a design fork appears during plan writing, return to the design discussion or structure outline rather than burying the fork in final-plan prose.
- If a decision will recur across future work, record it as a standing policy recommendation in the design discussion rather than leaving it as one-off advice.

## Done Criteria

The artifacts are ready when the research is descriptive, the design discussion records options and decisions, recurring decisions have policy recommendations when useful, the structure outline slices the work vertically, and the final plan can be handed to a fresh executor without relying on hidden conversation context.
