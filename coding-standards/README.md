# coding-standards

Language-agnostic coding standards for design-level code review and implementation judgment. Use this skill when the question is whether code tells the truth about the model: domain concepts, state, boundaries, modules, effects, failures, verification, complexity, and maintainability.

This is not a formatter, linter, framework guide, or language-specific style guide. The TypeScript-shaped examples in the references are concrete examples only; translate the shapes into the host language's native tools.

## Contents

- `SKILL.md` — compact doctrine, workflow, and task-oriented routing table.
- `references/vocabulary.md` — shared terms.
- `references/domain-modeling.md` — representation, grain, identity, and domain concepts.
- `references/state.md` — state space, transitions, lifecycle, authority, and loops.
- `references/modules.md` — deep modules, responsibilities, seams, dependencies, and adapters.
- `references/boundaries.md` — parsing, refined values, DTOs, anti-corruption layers, and source-of-truth conflicts.
- `references/effects.md` — IO, mutation, async work, retries, idempotency, and resource ownership.
- `references/error-handling.md` — expected failures, defects, operational failures, diagnostics, and user-facing failure facts.
- `references/verification.md` — claims, evidence, real seams, characterization tests, and mock-theater smells.
- `references/complexity.md` — overengineering, over-modeling, shallow wrappers, indirection, and reasoning cost.
- `references/maintainability.md` — contracts, internal freedom, Chesterton's fence, refactoring, compatibility obligations, and clean end-state changes.

## Source notes

This skill adapts ideas from dmmulroy's coding-standards work, especially the current [`dmmulroy/skills` coding-standards skill](https://github.com/dmmulroy/skills/tree/main/coding-standards) and the earlier [`coding-standards-draft.md` gist](https://gist.github.com/dmmulroy/9c80f1f499b031aa0b6525b5d9ae25f0).

Specific borrowed inspirations include parse-at-the-seam guidance, refined/domain values, OCaml-style domain modules, Rust-like safety/invariant pressure, and keeping database/provider/framework shapes inside boundary adapters. This version generalizes those ideas into a reusable skill instead of preserving TypeScript, Effect, or Cloudflare-specific rules.
