# Improve Plan Bank Index Template

```markdown
# <Effort Title>

**Source roadmap:** <path>
**Planned at:** <date, VCS revision/bookmark/branch>
**Scope:** <project/feature area>
**Planner:** <name/session, if relevant>

## Purpose

<Why this effort exists and what it unlocks.>

## What Better Means

<Success criteria for this plan bank: user-visible outcomes, architecture leverage, verification strength, agent execution quality, or other concrete standards.>

## Current State

<Brief evidence-backed summary with links to key files/artifacts.>

## Desired End State

<What will be true after all plans land.>

## Source Audit Summary

| Opportunity | Audit category | Standards concern | Impact | Effort | Risk | Confidence | Source evidence |
|---|---|---|---|---|---|---|---|
| <title> | <category> | <from the `coding-standards` skill, or N/A> | <payoff> | S/M/L | LOW/MED/HIGH | HIGH/MED/LOW | <paths/artifacts> |

## Plan Order

| Plan | Status | Audit category | Standards concern | Depends on | Ready for routine execution? | Needs deeper planning? | Autonomy boundary | Notes |
|---|---|---|---|---|---|---|---|---|
| [001-title](001-title.md) | Not started | <category> | <from the `coding-standards` skill, or N/A> | None | Yes/No | Yes/No | <routine execution / design review / human approval> | ... |

## Dependency Notes

<Sequencing constraints and why order matters.>

## Verification Baseline

- `<command>` — <what it proves>
- `<command>` — <what it proves>

If no reliable command exists, say so and point to the plan that establishes one.

## Evals / Regression Checks

<Checks that catch the plan bank making the repo worse: behavior regressions, architecture regression, executor failure modes, flaky validation, or policy drift.>

## Autonomy Boundary

| Action type | Routine execution allowed? | Needs design review? | Needs human approval? |
|---|---|---|---|
| <routine implementation within a plan> | <yes/no> | <yes/no> | <yes/no> |
| <design fork or API shape change> | <yes/no> | <yes/no> | <yes/no> |

## Drift Checks Before Any Plan

- Re-read project instructions and this index.
- Check current VCS state against `Planned at`.
- Re-open files named by the plan before editing.
- Stop if architecture, APIs, or validation commands have changed materially.

## Deeper Planning Candidates

Use this for low-confidence audit items, unsettled architecture, speculative recommendations, or user decisions that should not be buried inside an implementation plan.

| Plan/opportunity | Why it needs depth | Suggested next artifact |
|---|---|---|

## Standing Policies / Decisions

| Decision or policy | Why it should not be re-litigated | Where to record or enforce it |
|---|---|---|

## Considered and Rejected

| Idea | Audit category | Reason rejected | Revisit if |
|---|---|---|---|

## Deferred

| Idea | Why deferred | Trigger to revisit |
|---|---|---|

## Reconciliation Log

- `<date>` — <what changed in the plan bank and why>
```
