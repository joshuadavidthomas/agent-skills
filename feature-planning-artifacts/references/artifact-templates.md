# Feature Planning Artifact Templates

## Research Questions

```markdown
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
```

## Design Discussion

```markdown
---
type: design-discussion
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
---

# Design Discussion: <topic>

## Summary of Change Request

<What is being designed and why.>

## What Better Means

<Concrete success criteria and what would count as regression.>

## Standards / Design Pressure

<Selected `coding-standards` skill concern and reference, if applicable. Do not restate the whole standard; explain how it applies to this design.>

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
```

## Structure Outline

```markdown
---
type: structure-outline
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
---

# Structure Outline: <topic>

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
```

## Final Plan

```markdown
---
type: plan
repo: <repo name>
branch: <current branch/bookmark>
sha: <current revision>
---

# Implementation Plan: <topic>

> **Executor instructions:** Follow this plan with no hidden session context. You can assume the executor is competent at explicit instructions and weak at filling gaps, resolving ambiguity, or knowing when to stop. If a STOP condition occurs, write a handback instead of improvising.

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
