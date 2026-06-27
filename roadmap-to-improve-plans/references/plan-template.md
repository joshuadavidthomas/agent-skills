# NNN Improve Plan Template

```markdown
# NNN — <Plan Title>

> **Executor instructions:** Follow this plan with no hidden session context. You can assume the executor is competent at explicit instructions and weak at filling gaps, resolving ambiguity, or knowing when to stop. If a STOP condition occurs, write a handback instead of improvising.

**Source roadmap item:** <path or title>
**Effort index:** <README path>
**Planned at:** <date, VCS revision/bookmark/branch>
**Depends on:** <none | NNN-title>
**Executor target:** <routine execution ready? yes/no>

## Purpose

<Why this plan matters and what it unlocks.>

## What Better Means

<The concrete improvement this plan must produce, and what would count as regression.>

## Current-State Evidence

- `path:line-line` — <fact>
- `path` — <artifact or command evidence>

## Desired End State

<Observable state after this plan lands.>

## Scope

- <included>
- <included>

## Out of Scope

- <excluded>
- <excluded>

## Design Claim

<The coding-standards or architecture claim this plan protects: clearer module, better seam, parsed boundary, explicit state, reliable verification, etc.>

## Implementation Sequence

### Step 1 — <title>

<Intent and concrete files likely touched. Prefer sketches over full implementation dumps.>

### Step 2 — <title>

<Intent and concrete files likely touched.>

## Verification

### Automated

- [ ] `<command>` — <what passing proves>
- [ ] `<command>` — <what passing proves>

### Evals / Regression Checks

- [ ] <check that would catch this getting worse later>
- [ ] <executor failure mode or architecture regression check, if relevant>

### Manual

- [ ] <only when useful and specific>

## Autonomy Boundary

Routine execution may include:

- <routine changes allowed without asking>

Design review is required for:

- <design-sensitive choices, architecture shape, unclear failures>

Human approval is required for:

- <product, access, security, data migration, irreversible, or compatibility decisions>

## Drift Checks

Before editing, the executor must:

- [ ] Re-read this plan and the effort index.
- [ ] Check current VCS state and compare with `Planned at`.
- [ ] Re-open cited files and confirm the evidence still matches.
- [ ] Confirm validation commands still exist.

## STOP Conditions

Stop and hand back if:

- cited files or APIs no longer match the plan;
- validation commands are missing or fail before changes;
- a design decision is required that this plan does not answer;
- implementing this plan requires compatibility/migration work not listed here;
- the change grows beyond one independently reviewable PR;
- the work crosses the autonomy boundary above.

## Rejected Approaches

- <approach> — <why rejected>

## Standing Policy Updates

<Any recurring decision this plan should turn into a policy, ADR, template, or repo instruction. Use “None” if not applicable.>

## Executor Notes

<Concrete advice for a fresh agent: conventions, files to avoid, expected pitfalls, and what not to improvise.>
```
