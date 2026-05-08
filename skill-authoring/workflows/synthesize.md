# Synthesizing Skills From Sources

Use this workflow when a skill should encode real domain knowledge, not just a generic procedure.

## Core Idea

Skill synthesis means building the skill from trustworthy evidence, then improving it with real outcomes.

```
Collect sources → Extract patterns → Author skill → Run it → Classify results → Refine → Repeat
```

Generic guidance is a starting point. For domain skills, the best source material is usually the organization's own history: past fixes, regressions, PR comments, incident reviews, support escalations, and examples where humans already corrected the behavior you want the agent to learn.

## Step 1: Define the Skill Boundary

Before collecting sources, write the boundary in one paragraph:

- What task should this skill improve?
- What behavior should it prevent?
- Who or what will use it?
- What is out of scope?

If the boundary contains multiple unrelated jobs, split the skill.

## Step 2: Collect High-Signal Sources

Prefer sources that show real decisions and real failures.

| Source Type | Signal |
|-------------|--------|
| Official docs/specs | Required constraints and supported APIs |
| Existing similar skills | Shape, routing, examples, conventions |
| Project docs/runbooks | Local workflow and terminology |
| Recent commits and patches | Past mistakes and accepted fixes |
| PR review comments | What reviewers repeatedly correct |
| Incidents/postmortems | Failure modes and safeguards |
| Test cases/regressions | Concrete inputs and expected behavior |
| Failed agent outputs | False positives, false negatives, rationalizations |
| Positive examples | What good looks like in this context |

Do not treat all sources equally. A real project fix usually beats a generic blog post. A current official spec beats stale copied guidance.

## Step 3: Record Provenance

For material skill work, create or update `SOURCES.md` at the skill root.

Use this shape:

```markdown
# Sources

## Source Inventory

| Source | Trust | Contribution | Constraints |
|--------|-------|--------------|-------------|
| [Name](url-or-path) | High/Medium/Low | What this source teaches | Known gaps or caveats |

## Synthesis Decisions

- Decision: [What the skill will do]
  - Supported by: [sources]
  - Rejected alternative: [if relevant]
  - Reason: [why]

## Coverage and Gaps

- Covered: [cases backed by sources]
- Gaps: [unknowns, stale areas, missing examples]
- Needs validation: [claims that require testing]

## Change Log

- YYYY-MM-DD: [what changed and why]
```

Keep provenance out of runtime prose unless the agent needs it during execution. `SOURCES.md` is for maintainers.

## Step 4: Extract Patterns Before Writing

Read the sources and extract:

- recurring triggers users actually say
- common failure modes
- positive examples worth copying
- anti-patterns to prevent
- local terminology and abstractions
- constraints the agent must not violate
- validation steps that prove success

Write patterns in concrete language. Avoid abstract advice like "be careful with permissions" when sources show a specific failure like "filter querysets by organization before looking up the object by ID."

## Step 5: Author the Minimum Skill

Before adding content, run a precision check:

1. What is the smallest instruction that changes behavior?
2. Can an existing section be narrowed instead of adding a new one?
3. Does each reference file have a direct "open when..." reason from `SKILL.md`?
4. Is any content only background for maintainers? Put it in `SOURCES.md`, not `SKILL.md`.
5. Is provider-specific machinery necessary? If yes, document the portability cost.

Prefer tightening existing guidance over adding another section.

## Step 6: Build Evaluation Examples

For behavior-sensitive skills, keep examples that can be reused across revisions.

Use three slices:

| Slice | Purpose |
|-------|---------|
| Positive examples | The skill should identify or produce this behavior |
| Negative examples | The skill should avoid flagging or producing this behavior |
| Holdout examples | Do not tune directly against these; use them to check generalization |

Store persistent examples under `references/evidence/` only when they are reusable and safe to keep. Otherwise, summarize anonymized patterns in `SOURCES.md`.

## Step 7: Run and Classify Results

Run the skill against realistic tasks or a representative slice of the codebase/content.

Classify every result:

| Classification | Meaning | Skill Response |
|----------------|---------|----------------|
| True positive | Correctly found or produced desired behavior | Preserve the pattern |
| False positive | Flagged something acceptable | Narrow the trigger or evidence standard |
| False negative | Missed something important | Add a concrete detection or instruction pattern |
| Unclear | Needs human judgment | Record gap; don't overfit |

Feed the classified results back into the skill. This is the meta-optimization loop.

## Step 8: Stop When Reliable Enough

A synthesized skill is ready when:

- the main use cases are backed by sources
- false positives have been narrowed with concrete rules
- false negatives have concrete counterexamples or tests
- activation phrases trigger reliably
- open gaps are documented rather than hidden
- validation has run and remaining risks are explicit

Do not chase perfection. Ship a source-backed skill, use it, and refine from evidence.
