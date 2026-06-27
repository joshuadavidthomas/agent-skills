# Strategic Roadmap Template

```markdown
# Strategic Roadmap: <repo name>

## Purpose

<Who this is for, what repository/horizon it covers, and what decision this roadmap should support.>

## What Better Means

<Define the repo-level success criteria before ranking work: user value, agent execution quality, architecture leverage, verification confidence, velocity, reliability, or another concrete standard.>

## Source Material Reviewed

- `<path or artifact>` — <why it mattered>
- `<branch/bookmark/plan/user seed>` — <what it contributed>

## Audit Coverage / Not Reviewed

- **Reviewed deeply:** <areas/artifacts>
- **Sampled lightly:** <areas/artifacts>
- **Not reviewed:** <areas/artifacts>
- **Audit categories covered:** <correctness, security, performance, tests, architecture, dependencies, DX/tooling, docs, direction>
- **Coverage risk:** <what the roadmap might miss because of this boundary>

## Strategic Read

<2-4 paragraphs: where the leverage is, what should not be done yet, what is stale or newly important, and what kind of planning should happen next.>

## Now

| Opportunity | Audit category | Why now | Impact / leverage | Standards area | Evidence | First strategic slice | Risk / uncertainty | Autonomy boundary | Confidence | Next artifact |
|---|---|---|---|---|---|---|---|---|---|---|
| <title> | <tests / architecture / direction / etc.> | <why this belongs first> | <payoff relative to effort and risk> | <Domain Modeling / Modules / Boundaries / Verification / etc., or N/A> | <paths/artifacts/user seed> | <first coherent planning target> | <unknowns or decision points> | <routine execution, design review, or human approval> | High/Medium/Low | `roadmap-to-improve-plans` / `feature-planning-artifacts` / `research/spike` / `user decision` |

## Next

| Opportunity | Audit category | Why next | Impact / leverage | Standards area | Evidence | Prerequisite | Autonomy boundary | Confidence | Likely next artifact |
|---|---|---|---|---|---|---|---|---|---|
| <title> | <category> | <why it matters after Now> | <payoff relative to effort and risk> | <standards area or N/A> | <paths/artifacts/user seed> | <what must happen first> | <routine execution, design review, or human approval> | High/Medium/Low | <artifact or defer> |

## Later

- **<Opportunity>** — <Why it remains plausible; what signal would pull it forward.>

## System Upgrades / Standing Policies

Include this section only when evidence shows repeated decisions, bottlenecks, or durable system upgrades worth preserving. Examples: evals, regression checks, planning templates, ADRs, coding policies, memory/promotion rules, verification baselines, or autonomy boundaries.

| Upgrade or policy | Repeated decision or bottleneck | Proposed durable artifact | Evidence | Owner / next artifact |
|---|---|---|---|---|
| <policy/eval/template> | <what stops being re-litigated> | <where it should live> | <paths/artifacts> | <next step> |

## Architecture / Deepening Candidates

Include this section only when architecture leverage is central. Do not propose final interfaces here; name the friction, deepening direction, and artifact needed to decide the design.

| Candidate | Current friction | Audit probe | Deepening direction | Recommendation strength | Evidence | Recommended next artifact |
|---|---|---|---|---|---|---|
| <candidate> | <caller burden, shallow module, poor seam, etc.> | <deletion test / bounced-between-modules / interface cost / lost locality / leaking seam> | <module/interface/depth/seam/adapter/leverage/locality direction> | Strong / Worth exploring / Speculative | <paths/artifacts> | <artifact> |

## Reconcile Existing Plans

Include this section only if old plans, branches, tickets, or roadmaps were reviewed.

| Artifact | Keep / revise / retire | Reason | Next |
|---|---|---|---|
| `<path or branch>` | <verdict> | <why> | <action> |

## Not Now / Rejected

| Idea | Audit category | Reason | What would change the verdict |
|---|---|---|---|
| <idea> | <category or N/A> | <why not worth planning now> | <signal that would make it relevant> |

## Recommended Next Move

<The 1-3 artifacts to create next and why. Include any routine-execution, design-review, or human-approval boundary.>
```
