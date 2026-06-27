---
name: roadmap-to-improve-plans
description: Use when turning a roadmap, repo priorities, architecture priorities, chosen opportunities, or “roadmap to plans” request into implementation plans or a plan bank for future executors. Writes README.md indexes, 001-*.md/NNN-style plans, optional memo-*.md files, verification gates, drift checks, STOP conditions, rejected approaches, and executor handoff notes.
---

# Roadmap to Improve Plans

Turn selected strategic-roadmap opportunities into a broad bank of numbered implementation plans. This is the wide planning stage: enough detail for future executors to work safely, without spending full feature-planning-artifact effort on every idea.

Treat plan writing as meta-work: the output should improve future execution loops by making success criteria, regression checks, approval boundaries, and STOP conditions explicit.

This owns this pipeline's NNN plan-bank contract directly.

## Source Frame

Before writing plans, load what applies:

- The selected `.agents/ROADMAP.md` or equivalent roadmap/opportunity artifact.
- `coding-standards` and only the reference files matching the selected work.
- `improve-codebase-architecture` for architecture/deepening candidates.
- DLS-style exemplar plans when present in the target repo, especially effort indexes, numbered plans, memos, rejected/deferred notes, and reconciliation logs.
- Project docs and commands: `AGENTS.md`, `README.md`, `CONTEXT.md`, architecture docs, ADRs, package/test config, CI config, and current VCS state.

## Workflow

1. **Select plan scope**
   - Start from selected roadmap items or ask the user which items to plan.
   - Keep one effort directory coherent. Split unrelated projects or unrelated outcomes into separate efforts.
   - Preserve dependency order from the roadmap; do not flatten everything into parallel tasks.

2. **Reconcile current state**
   - Read current project instructions and existing plans.
   - Check current VCS state and active branch/bookmark so the plan does not assume stale code.
   - Identify exact validation commands and any missing verification baseline.
   - Carry forward the roadmap's definition of “better”; if missing, define the plan-bank success criteria before decomposing work.

3. **Decompose into numbered plans**
   - Each `NNN-*.md` should be independently landable or have an explicit dependency on an earlier plan.
   - Prefer vertical slices over layer-by-layer rewrites.
   - Include architecture/deepening language when relevant: module, interface, depth, seam, adapter, leverage, locality.
   - Use coding standards to state the design claim each plan protects.

4. **Write the effort index and plans**
   - Prefer `.agents/plans/<effort-slug>/` unless the repo already has an established planning convention.
   - Use [references/index-template.md](references/index-template.md) for `README.md`.
   - Use [references/plan-template.md](references/plan-template.md) for each numbered plan.
   - Use [references/memo-template.md](references/memo-template.md) only when a design fork or handback needs a durable answer.
   - Choose the next available `NNN-` prefix by inspecting the destination directory.

5. **Mark feature-planning-artifact candidates and autonomy boundaries**
   - In the effort index, mark plans that deserve `feature-planning-artifacts` treatment because of high leverage, high risk, unclear architecture, or user decisions.
   - For each plan, state what can be done as routine execution, what needs design review, and what requires human approval.

## Plan Requirements

Every numbered plan must be self-contained for an executor with no planning-session context. Assume competence at following explicit instructions and weakness at filling gaps. Each plan must include:

- purpose and payoff;
- definition of “better” for this plan;
- current-state evidence with paths and line ranges where possible;
- desired end state;
- scope and out of scope;
- implementation sequence at PR-sized granularity;
- exact automated verification commands;
- evals or regression checks that catch the change getting worse;
- manual verification only when it proves something automation cannot;
- autonomy boundary for routine execution, design review, and human approval;
- drift checks to run before implementation;
- STOP conditions for stale assumptions, missing commands, design forks, or failed validation;
- rejected approaches and why they are not being used;
- executor handoff notes for a fresh executor.

## Guardrails

- Do not implement source changes.
- Do not write giant all-or-nothing plans.
- Do not hide unresolved design questions in TODO prose; either stop for feature planning artifacts or write a memo request.
- Do not leave recurring decisions as repeated advice; turn them into a policy, memo, ADR suggestion, or plan-bank rule when durable.
- Do not keep old shapes by default. Prefer the intended end state unless migration compatibility is required.
- Do not invent validation commands. If commands are unknown, make establishing the verification baseline an explicit first plan or STOP condition.

## Done Criteria

The effort is done when the index explains plan order and readiness, each numbered plan can be handed to a fresh executor, and the highest-risk plans are flagged for feature planning artifacts instead of being marked ready prematurely.
