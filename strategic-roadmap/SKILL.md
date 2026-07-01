---
name: strategic-roadmap
description: Use when a user asks “what should I work on in this repo?”, “what’s worth doing next?”, repo audit, tech-debt priorities, architecture priorities, old-plan reconciliation, or repo-grounded opportunity discovery. Produces .agents/ROADMAP.md with generated opportunities, user-seeded ideas, Now/Next/Later sequencing, rejected/not-now items, and next-artifact recommendations. Not for standard product/release roadmaps; if multiple repos are requested, create one roadmap per repo.
---

# Strategic Roadmap

Generate the work worth planning inside one repository. This is an audit-shaped senior judgment stage: mine repo docs, old plans, branches/bookmarks, and code shape; inspect across improvement categories; expand the user's seeds; generate non-obvious opportunities; reject low-value ideas; and sequence the best work.

Treat roadmap work as meta-work: prefer opportunities that improve future work loops, evaluation, verification, autonomy boundaries, standing policies, and plan quality over one-off task completion.

Use the ordinary `roadmap` skill for standard product/release roadmaps. Use this when the user wants repo-grounded opportunity discovery before investing in plan banks or feature planning artifacts. Do not reduce this to ranking a list the user already gave you. The planner is responsible for idea generation and judgment.

## Source Frame

Before producing the roadmap, load the sources that match the scope:

- `improve` for read-only senior-advisor discovery, audit categories, evidence, vetting, leverage ranking, and “not worth doing” verdicts.
- The `coding-standards` skill as the canonical source for standards areas and review vocabulary. Load the matching reference files when a code-shaped opportunity needs that lens; do not restate the standards here.
- `improve-codebase-architecture` when architecture/deepening opportunities are in scope.
- Architecture vocabulary: module, interface, depth, seam, adapter, leverage, locality.
- Project docs: `AGENTS.md`, `README.md`, `CONTEXT.md`, architecture docs, ADRs, old plans, roadmap files, active branches/bookmarks, and relevant issue/ticket notes.

## Workflow

1. **Establish repo scope and goal**
   - Identify the single repository and existing artifacts to mine.
   - Characterize what “better” means for this repo: user value, agent execution quality, architecture leverage, verification confidence, velocity, reliability, or other success criteria.
   - Include the user's seed ideas, but treat them as inputs, not the full set.
   - If the user names multiple repos, create one roadmap per repo or ask which repo to start with.
   - If the repo goal or success criteria are unclear after reading context, ask a short interview question before ranking work.
   - If the repo is too broad to inspect responsibly, ask one narrowing question or propose a bounded first pass.

2. **Recon without implementation**
   - Read project context and existing plans before judging.
   - Identify the project’s verification commands, missing verification baseline, active work state, and churn hotspots.
   - Inspect current work state enough to avoid stale recommendations.
   - Do not edit source code. Only write the roadmap artifact.
   - If credentials or secrets appear, reference only the file path, line, and credential type; never copy secret values into the roadmap.

3. **Audit for opportunities**
   - Audit like `improve`: correctness, security, performance, test coverage, tech debt and architecture, dependencies and migrations, DX and tooling, docs, and direction.
   - Include repo-discovered ideas, architecture/deepening candidates, product/workflow ideas, plan salvage opportunities, obsolete work to retire, and system upgrades that improve future work.
   - Look for decisions the user or agents keep re-litigating; propose standing policies, ADRs, evals, or plan templates when they would compound.
   - For code-shaped opportunities, choose the Standards area from the `coding-standards` skill and load only the matching reference when the ranking or routing depends on it.
   - For architecture candidates, use `improve-codebase-architecture` framing: current friction, files/modules, deepening direction, locality/leverage, testability, and recommendation strength.
   - Use architecture audit probes: where understanding requires bouncing between modules, where the interface is nearly as complex as the implementation, where test-only extraction lost locality, where seams leak, and where the deletion test shows a module is shallow.
   - Do not propose final interfaces at roadmap stage. Name the friction, direction, and next artifact instead.

4. **Vet and sequence**
   - Verify every opportunity you rank by opening the cited code, plan, or artifact yourself; subagent output and old plans are leads, not evidence.
   - Keep only ideas with evidence or a clear user-stated goal.
   - Rank by leverage: impact divided by likely effort, discounted by confidence and fix risk; let verification-baseline and high-confidence security items float up when they unblock or de-risk later work.
   - Separate problems worth fixing from direction options worth considering when they should not be ranked against bugs or verification gaps.
   - Calibrate autonomy by risk: identify what routine executors can do later, what needs design review, and what needs human approval.
   - Record rejected and not-now items so future runs do not rediscover the same low-value ideas.

5. **Write `.agents/ROADMAP.md`**
   - Use the template in [references/roadmap-template.md](references/roadmap-template.md).
   - Create `.agents/` if it does not exist.
   - Prefer Now / Next / Later over fake dates.
   - Put provenance in top-level source material and item evidence, not required per-item source fields.
   - State the coverage boundary: what was reviewed, lightly sampled, or not reviewed.
   - Every item must name the next artifact: `roadmap-to-improve-plans`, `feature-planning-artifacts`, `research/spike`, `user decision`, `defer`, or `drop`.
- For architecture items, include recommendation strength: Strong, Worth exploring, or Speculative.

## Output Rules

- Be evidence-backed. Cite file paths, artifact paths, branch/bookmark names, or user seed text.
- Say what was not reviewed; do not imply whole-repo coverage when the pass was bounded.
- Mark the audit category for each major opportunity unless it is purely user-seeded direction.
- Be willing to say “not worth doing.”
- Define what “better” means for the repo before ranking opportunities; if it is unclear, ask.
- Prefer durable system upgrades over one-off task suggestions when leverage is comparable.
- Do not produce implementation steps here; route selected items to `roadmap-to-improve-plans` or `feature-planning-artifacts`.
- Do not estimate effort unless the user explicitly asks. Prefer confidence, risk, dependency, autonomy boundary, and executor-readiness.
- Do not invent compatibility layers. If a shape should change, favor the clean end state unless real data/public contracts require migration planning.

## Done Criteria

The roadmap is done when a future planner can choose the next artifact without redoing repo discovery: the best opportunities are ranked, rejected ideas are recorded, architecture candidates are framed with standards vocabulary, and the next planning stage is explicit for each item.
