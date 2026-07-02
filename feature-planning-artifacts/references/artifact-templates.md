# Feature Planning Artifact Templates

## Feature Bundle README

```markdown
# <Feature Title>

**Source roadmap item:** <path/title or N/A>
**Source improvement plan:** <path/title or N/A>
**Planned at:** <date, VCS revision/bookmark/branch>
**Status:** <designing / design accepted / outlining / outline accepted / ready for execution / superseded>
**Current gate:** <what needs review or approval next>

## Purpose

<Why this feature/design effort exists and what it unlocks.>

## What Better Means

<Success criteria for the whole effort, plus what would count as regression.>

## Artifact Index

| Artifact | Status | Purpose | Notes |
|---|---|---|---|
| [001-design-discussion](001-design-discussion.md) | In review | Decide the shape | <key review point> |

## Current Shape

<The current accepted or recommended shape in a few bullets. Keep detailed rationale in the design discussion.>

## Accepted Decisions

- <Decision> — <why it stands>

## Open Gates

- <Decision, review, evidence, or approval still needed>

## Implementation Routing

<Direct execution from the outline/plan, split into an improvement plan batch, or pending decision.>

## Rejected or Deferred

| Item | Reason | Revisit if |
|---|---|---|
```

## Research Questions

```markdown
---
type: research-questions
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
status: complete
---

# Research Questions: <topic>

## Source Request

<Selected roadmap item, opportunity, or plan being researched.>

## Questions

1. <How does the current system ...?>
2. <Where is ... represented today?>
3. <What tests or fixtures cover ...?>

## Out of Scope

- Recommendations
- Proposed implementation
- Future design

## Stop Gate

Stop here. The next artifact is research, unless the user supplies enough verified context to move directly to design discussion.
```

## Research

```markdown
---
date: <ISO timestamp with timezone>
git_commit: <current revision>
branch: <current branch/bookmark>
repository: <repo name>
topic: <topic>
type: research
status: complete
source_questions: <path or N/A>
---

# Research: <topic>

## Research Question

<Questions answered.>

## Methodology

This document describes current behavior only. It does not recommend implementation changes.

## Summary

<2-4 focused paragraphs synthesizing current behavior, architecture, data flow, tests, and constraints.>

## Detailed Findings

### 1. <Concept>

<How it works today with citations. Organize by concept, not file order. Use tables, diagrams, code snippets, or pseudocode only when they clarify current behavior.>

#### Testing patterns

<Existing tests, fixtures, commands, mocking/fake patterns, or explicit absence.>

## Code References

- `path:line-line` — <fact>

## Architecture Documentation

<Current architecture, module boundaries, conventions, and design decisions.>

## Open Questions

<Genuine unknowns about current behavior, or “None.”>

## Stop Gate

Stop here. Recommendations belong in the design discussion, not this research document.
```

## Design Discussion

```markdown
---
type: design-discussion
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
status: in-review
source_research: <path(s) or reconnaissance summary>
---

# Design Discussion: <topic>

## Summary of Change Request

<What is being designed and why.>

## Review Status

- **Status:** In review / Accepted / Superseded
- **Review needed:** <specific decisions, risks, or open questions the user should inspect>
- **Next artifact after acceptance:** Structure outline

## What Better Means

<Concrete success criteria and what would count as regression.>

## Standards / Design Pressure

<Selected `coding-standards` skill concern and reference, if applicable. Do not restate the whole standard; explain how it applies to this design.>

## Reconnaissance Summary

- <Thread or subagent/scout: current implementation, tests, patterns, docs, external dependency, standards. Include only load-bearing findings.>

## Current State

- <User/system behavior today. Keep product/domain description here; use file references in architecture and patterns sections.>

## Desired End State

- <What will be true when this work is done.>

## What We're Not Doing

- <Explicit non-goals.>

## Proposed End State Architecture

Before:

```mermaid
<diagram or remove if not useful>
```

After:

```mermaid
<diagram or remove if not useful>
```

<Concise outline, pseudocode, or interface sketch for the proposed architecture.>

## Design Questions

### <Question>

<Option framing with tradeoffs.>

- Option A: <description, pros, cons>
- Option B: <description, pros, cons>
- Recommendation: <recommended choice and why>

## Resolved Design Questions

### <Question>

<Decision, rationale, and rejected options.>

## Patterns to Follow

### <Pattern title>

<Why this existing pattern should be followed.>

- `path:line-line` — <evidence>

```<language>
<small existing-code snippet showing the pattern>
```

```<language>
<small proposed-shape sketch, if useful>
```

## Standing Policy / Eval Recommendations

<Recurring decisions, repo instructions, ADRs, templates, or evals this design should create or update. Use “None” if not applicable.>

## Stop Gate

Stop here for design review. Do not write the structure outline until this document is accepted or the user explicitly asks to proceed.
```

## Structure Outline

```markdown
---
type: structure-outline
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
status: in-review
source_design_discussion: <path>
---

# Structure Outline: <topic>

## Review Status

- **Status:** In review / Accepted / Superseded
- **Review needed:** <phase boundaries, validation, risky slices, or open questions>
- **Next artifact after acceptance:** Final plan

## Desired End State

- <What will be true when this is done.>

## Implementation Overview

- [ ] Phase 1: <title>
- [ ] Phase 2: <title>

## Phase 1: <title>

<What this vertical slice accomplishes.>

### File Changes

- `path` — <change intent>

```<language>
<optional signature, type, diff, or pseudocode sketch>
```

### Validation

#### Automated

- [ ] `<command>` — <what passing proves>

#### Evals / Regression Checks

- [ ] <check that catches the design getting worse>

#### Manual

- [ ] <only if meaningful>

## Open Questions

- <Questions about outline structure, or “None.”>

## Stop Gate

Stop here for outline review. Do not write the final plan until this outline is accepted or the user explicitly asks to proceed.
```

## Final Plan

```markdown
---
type: plan
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
status: ready-for-execution
source_structure_outline: <path>
---

# Implementation Plan: <topic>

> **Executor instructions:** Follow this plan with no hidden session context. You can assume the executor is competent at explicit instructions and weak at filling gaps, resolving ambiguity, or knowing when to stop. If a STOP condition occurs, write a handback instead of improvising.

## Planning Sources

- **Design discussion:** <path>
- **Structure outline:** <path>
- **Research:** <path(s) or N/A>

## Overview

<What will be implemented and why.>

## Standards Concern

<Selected `coding-standards` skill concern/reference, or N/A.>

## What Better Means

<Concrete success criteria carried forward from the design discussion.>

## Current-State Evidence

- `path:line-line` — <fact>

## Desired End State

<Observable state after implementation.>

## Scope

- <included>

## Out of Scope

- <excluded>

## Implementation Approach

<Chosen approach and rationale. Do not reopen resolved design questions.>

## Implementation Routing

<State whether this plan is intended for direct execution or should be split into an improvement plan batch first. If splitting, name the slices and dependencies.>

## Phases

### Phase 1 — <title>

#### Overview

<What this phase accomplishes.>

#### Changes Required

##### 1.1 <Component/File Group>

**File:** `path/to/file.ext`  
**Changes:** <specific change summary; include location hints where useful>

```diff
<small example diff, signature, or code sketch when it materially reduces executor ambiguity>
```

#### Success Criteria

##### Automated Verification

- [ ] `<command>` — <what passing proves>

##### Evals / Regression Checks

- [ ] <check that catches behavior, architecture, or executor handoff getting worse>

##### Manual Verification

- [ ] <only when useful and specific>

## Autonomy Boundary

- **Routine execution may include:** <routine work allowed>
- **Design review required:** <design-sensitive choices>
- **Human approval required:** <product, access, security, data, irreversible, or compatibility decisions>

## Drift Checks

- [ ] Re-open cited files and confirm assumptions still hold.
- [ ] Confirm validation commands still exist.

## STOP Conditions

- <condition that requires handback instead of improvisation>

## Rejected Approaches

- <approach> — <why rejected>

## Executor Notes

<Concrete guidance for a fresh executor. Policy recommendations belong in the design discussion; only mention deltas discovered after that document.>
```
