# Content Patterns

Choose the pattern that matches the governing question. Combine patterns only when each earns a distinct section; do not turn one artifact into a general-purpose portal.

## Codebase Overview

**Question:** How is this system shaped, and where should a reader start?

Include:

1. **Orientation:** purpose, users, runtime, and source identity/revision.
2. **System context:** what is inside the system and which external actors or services touch it.
3. **Major boundaries:** a small set of runtime or domain modules with responsibilities—not a decorated directory tree.
4. **Representative journey:** trace one real request, command, event, or data item from entry to outcome.
5. **State and effects:** where state lives and which boundaries perform I/O.
6. **Change map:** which areas tend to move together, only when source evidence supports it.
7. **Where to start:** concrete files/symbols for common reading goals.
8. **Source index:** paths, line ranges, revision, commands used, and known gaps.

Prefer a context diagram plus a focused sequence over a single graph of every file. Label inferred boundaries as inferred.

## Feature Explanation

**Question:** How does this capability work in the current system?

Include:

1. User-visible promise and trigger.
2. Entry point and preconditions.
3. Happy-path flow.
4. State transitions and data transformations.
5. External calls and side effects.
6. Failure, retry, rollback, and permission paths.
7. Configuration or feature flags.
8. Tests that demonstrate behavior.
9. Extension points and current limitations.

A good interaction couples two representations—for example, stepping through a request while highlighting the state and code boundary that changes. Keep a complete static numbered flow beside it.

## PR or Diff Walkthrough / Review

**Question:** What changes, why does it matter, and what deserves review attention?

First distinguish the requested job:

- **Overview/walkthrough:** explain the change and guide a reader through its evidence.
- **Review:** also judge correctness against the stated intent and report concrete findings.

Include:

1. **Intent:** PR description, linked issue/specification, and relevant author context; state when unavailable.
2. **Outcome:** the user/system behavior introduced, removed, or corrected.
3. **Scope:** base and target revisions, diff stats, and complete changed-file list.
4. **Before/after:** aligned behavioral or architectural comparison.
5. **Execution path:** how the changed behavior runs end to end.
6. **File map:** each changed file's role; group by behavior, not file extension.
7. **Contracts:** API, type, schema, configuration, dependency, migration, or persistence changes.
8. **Validation:** what tests and CI prove, what failed, and what remains untested.
9. **Risk review:** blast radius, compatibility assumptions, security/performance implications, rollout concerns, existing review discussion, and unknowns.
10. **Review guide:** specific questions or hotspots, each tied to evidence.

For a review, add a findings section ordered by impact. Each finding needs a specific claim, source locator, consequence, and suggested correction; include confidence when evidence is incomplete. Say explicitly when no findings remain, and distinguish “no findings” from “not checked.”

Do not create a celebratory recap by default. Preserve ambiguity and negative evidence. Never claim “safe,” “complete,” or “covered” without the checks that establish it.

Useful interaction:

- before/after toggle when alignment remains stable
- filter by behavior area or risk category
- expandable code evidence
- linked overview/detail highlighting

Avoid tabbing before and after states when the reader needs to compare them simultaneously.

## Implementation Recap

**Question:** What work was completed, and how does the resulting system behave?

Use after a substantial implementation when a visual handoff is more useful than a chat summary.

Include:

1. Delivered outcome, not a task diary.
2. Final architecture or execution flow.
3. Key decisions and rejected alternatives that still matter.
4. Behavior demonstrated by tests or manual validation.
5. Operational changes: configuration, data, deployment, migration, or support impact.
6. Follow-up work and known limitations.
7. Source/revision and validation evidence.

Do not turn elapsed steps, tool calls, or token usage into content. Explain the end state.

## Incident or Investigation Timeline

**Question:** What happened, how do we know, and where is uncertainty left?

Include:

1. Executive finding and current status.
2. Scope and evidence sources.
3. Chronology with exact timestamps and time zone.
4. Causal chain, clearly distinguished from temporal coincidence.
5. Competing hypotheses and disconfirming evidence.
6. Impact and affected boundaries.
7. Detection, mitigation, and recovery points.
8. Open questions and next evidence to collect.

Use a timeline for chronology and a separate causal graph for mechanism. Do not imply causality with a single left-to-right timeline.

## Data Report

**Question:** What does the dataset show, and what decision follows?

Include:

1. Headline finding with population, time range, and units.
2. Dataset source, collection method, transformations, exclusions, and freshness.
3. Directly labeled chart or table chosen for the comparison.
4. Baseline, denominator, and uncertainty where relevant.
5. Important segments, outliers, and counterexamples.
6. Reproducible calculation notes or embedded raw summary data.
7. Decision implication and limits.

Never fabricate values to fill visual space. Keep raw data separate from display transforms. Use interaction for filtering or details-on-demand only when the default view already makes the main finding visible.

## Interactive Illustration or Mechanism Explainer

**Question:** How does this behave, change, or fit together?

Choose the explanatory action that matches the subject:

- **Causal model:** vary a meaningful assumption and show its effect.
- **Algorithm or protocol trace:** step, play, pause, and reset while state and the active operation stay linked.
- **Spatial or structural illustration:** select an element to reveal its role while the full context remains visible.
- **Coupled representation:** manipulate or step through one view while highlighting the corresponding code, state, geometry, or output in another.

Build around one claim or learning objective:

1. State it in ordinary language.
2. Show a useful default case that already demonstrates it.
3. Give the reader one meaningful action.
4. Update the outcome and explanatory annotation immediately.
5. Keep surrounding context stable so the reader can compare states.
6. Offer reset and a few revealing presets or examples when useful.
7. Explain model assumptions and where the analogy stops.
8. Provide a static summary, numbered trace, relationship list, or small multiples for non-interactive use.

Example contract:

> **Question:** Why does a cache stampede happen?  
> **Action:** Adjust request concurrency and cache expiry alignment.  
> **Answer:** The timeline immediately shows duplicate origin work and labels the point where request coalescing changes the outcome.

An empty sandbox is not an explanation. Author the default state and guide the reader toward the meaningful contrast.

## Option Comparison

**Question:** Which option fits the stated constraints?

Include:

1. Decision and constraints.
2. Options described at the same abstraction level.
3. Shared criteria with evidence or explicit judgment labels.
4. Aligned small multiples or a semantic comparison table.
5. Tradeoffs, irreversible choices, and sensitivity to changed assumptions.
6. Recommendation strength and what would change it.

Use a control only if changing a weight or assumption genuinely changes the recommendation. Do not hide criteria behind tabs.

## Presentation

**Question:** What should a live audience understand in this session?

Only use presentation mode when a speaker controls pacing.

Include:

- one claim or relationship per view
- visible progress and direct slide navigation
- Arrow/PageUp/PageDown/Home/End keyboard support
- speaker notes or self-contained captions for evidence
- a printable/readable document fallback
- reduced-motion behavior for staged transitions

Do not emulate PowerPoint mechanically. A long technical reference belongs in document mode even if it has sections.

## Diagram Rules

Every diagram must have:

- a title phrased as the question or claim it answers
- an explicit scope or abstraction level
- named elements with responsibilities
- directional relationships labeled with specific actions or data
- a legend for any non-obvious shape, line, or color
- direct annotations near the evidence
- a concise textual equivalent

Prefer inline SVG or structured HTML. Use automatic graph layout only when relationships are too numerous for a hand-authored diagram, and cap or group nodes before the result becomes unreadable.
