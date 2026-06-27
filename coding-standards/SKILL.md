---
name: coding-standards
description: Use when reviewing code quality, asking whether a refactor or design is good, looking for code smells, or evaluating architecture tradeoffs. Identifies shallow interfaces, invalid state models, unclear boundaries, hidden effects, weak failure contracts, over-mocking, over-abstraction, compatibility glue, and clean-looking code that preserves bad models.
---

# Coding Standards

> “Thus, programs must be written for people to read, and only incidentally for machines to execute.”  
> — Abelson and Sussman, *Structure and Interpretation of Computer Programs*

> “In this connection it might be worth-while to point out that the purpose of abstracting is not to be vague, but to create a new semantic level in which one can be absolutely precise.”  
> — Edsger W. Dijkstra, “The Humble Programmer”

Good code solves a real problem through a model people can understand, use, change, and repair. It tells the truth at the right grain: concepts named where they matter, valid states made clear, boundaries translated, consequences visible, failures classified, behavior verified, and unnecessary structure deleted.

Borrow design pressure, not ecosystem ceremony: impossible states and explicit failure/effect boundaries from Rust; domain modules and algebraic modeling from ML traditions; anti-corruption boundaries from integration-heavy systems. Translate the idea into the host language's native tools.

## Core Tenets

- **Code communicates a model.** Names, types, modules, tests, and interfaces should reveal what is true in the domain and what must not happen.
- **Represent meaning at the right grain.** Make important distinctions explicit; do not turn every primitive, parser detail, or storage artifact into domain vocabulary.
- **Make valid states and transitions explicit.** Prefer states, variants, lifecycle rules, and transition points over boolean blindness, nullable phases, and hidden ordering requirements.
- **Shape deep modules.** Put cohesive behavior behind low-burden interfaces at real seams; a shallow wrapper mostly gives the same work another name.
- **Translate at boundaries.** External, persisted, framework-shaped, protocol-shaped, or runtime-hop data should be mapped into the internal model before it reaches core logic.
- **Make consequences legible.** IO, mutation, time, network, async work, authority, retries, resource cost, and other effects should be visible where they affect reasoning.
- **Handle errors as part of the design.** Expected failures belong in contracts; defects and operational causes need different recovery, reporting, and diagnostics.
- **Verify the real claim.** Tests and checks should prove behavior, invariants, transitions, boundaries, and failure modes through real seams, not private choreography.
- **Delete what does not carry meaning.** Collapse speculative generality, indirection mazes, stale shapes, duplicate concepts, and test-only surfaces unless they protect a real obligation.

## Non-negotiables

These are not style preferences. Treat them as design failures unless the surrounding code has a real constraint that explains them.

- Raw boundary data flows through core logic after being “validated.”
- Illegal states are normal representable values.
- Private parsing, storage, optimization, or test scaffolding becomes public vocabulary.
- A pass-through wrapper is presented as architecture.
- Consequential effects, authority, or expected failures are hidden from callers.
- Tests prove mocks, spies, or helper choreography instead of observable behavior.

## Tradeoffs

Do not hard-pivot from one dogma to its opposite. Every design accepts costs; choose the smallest honest shape with the information available.

## Rejected Framings

Reject these when they avoid modeling the real problem.

- **“The value was already validated earlier.”** Parse or translate at the boundary, pass the refined value inward, and make later code hard to call with the wrong shape.
- **“This is just the API/DB/framework shape.”** Boundary shapes can be used at the edge; they should not become the internal model by accident.
- **“The existing code throws, so this can throw too.”** Preserve unsafe failure contracts only when compatibility requires it; new local logic should distinguish expected failures from defects.
- **“This wrapper clarifies responsibilities.”** A wrapper earns its keep only when it hides complexity, owns policy or sequencing, protects an invariant, or translates across a real seam.
- **“This distinction exists in the source format.”** A distinction can be real and still be an implementation detail. Expose it only when callers need it.
- **“This interface gives us future flexibility.”** A seam is real when behavior varies, a boundary translates, or tests substitute through an intentional seam.
- **“Mocks make this isolated.”** Module mocks often isolate the wrong thing. Replace behavior through real seams and verify observable outcomes.
- **“The old shape might still be used.”** Check for a real user, data, or public-contract obligation. If the contract is intentionally changing, move to the end-state shape.
- **“A lint/type/test suppression fixes it.”** Suppressions need a narrow reason and a safety invariant; otherwise they hide contracts.

## How to Apply

1. **Understand the local code first.** Follow existing conventions when they communicate the model; change them deliberately when they preserve the wrong model.
2. **Classify the concern.** Domain model, state, module, boundary, effect, error, verification, complexity, or maintainability.
3. **Find the caller burden.** Ask what a caller or future maintainer must remember that the code could make explicit or enforce.
4. **Choose the smallest honest shape.** Do not simplify by lying; do not model so much that the truth becomes harder to see.
5. **Verify the claim.** Use project-native tests and checks that prove the behavior or contract the change depends on.
6. **Remove obsolete scaffolding.** Once the real obligation is understood, keep the requirement and delete the leftover shape.

A review finding is ready only when it names the concrete code shape, the caller or maintainer burden, the standard it violates, and the smallest honest change. Drop findings that do not have code evidence or a real cost.

## Reference Map

For nontrivial reviews or design advice, load only the reference files that match the concern below. Do not read every reference by default, and do not treat this root summary as the full standard.

| Concern | Read |
|---|---|
| Shared terms need clarification | [`references/vocabulary.md`](references/vocabulary.md) |
| Domain distinctions, granularity, identity, or implementation details leaking into the model | [`references/domain-modeling.md`](references/domain-modeling.md) |
| Flags, nullable lifecycle fields, invalid combinations, transitions, loops, or authority | [`references/state.md`](references/state.md) |
| Deep modules, module roles, seams, dependency shape, resource ownership, or pass-through wrappers | [`references/modules.md`](references/modules.md) |
| Raw API/DB/framework/provider shapes, parsing, DTOs, source-of-truth conflicts, or trust changes | [`references/boundaries.md`](references/boundaries.md) |
| IO, mutation, authority, async/background work, retries, idempotency, or hidden consequences | [`references/effects.md`](references/effects.md) |
| Expected failures, defects, operational failures, diagnostics, or human-facing failure facts | [`references/error-handling.md`](references/error-handling.md) |
| Behavior tests, brittle mocks, characterization tests, evidence, or weak verification | [`references/verification.md`](references/verification.md) |
| Overengineering, over-modeling, indirection mazes, speculative generality, or reasoning-cost smells | [`references/complexity.md`](references/complexity.md) |
| Contracts, internal freedom, Chesterton's fence, refactoring, compatibility obligations, or clean end-state changes | [`references/maintainability.md`](references/maintainability.md) |
