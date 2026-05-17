# salsa

Salsa guidance for building incremental Rust systems: query databases, tracked functions, input/tracked/interned structs, accumulators, cancellation, LSP integration, memory management, cycles, durability, and production architecture.

## What This Covers

- The core Salsa mental model: inputs, tracked functions, dependencies, revisions, backdating, and red-green reuse.
- Choosing between `#[salsa::input]`, `#[salsa::tracked]`, `#[salsa::interned]`, and plain Rust types.
- Designing query pipelines, database traits, side tables, test databases, and crate boundaries.
- Handling cycles, cancellation, durability, memory growth, and incremental-reuse tests.
- Using accumulators for diagnostics and knowing when return-value diagnostics fit better.
- Integrating Salsa with LSP servers, file systems, snapshots, worker pools, and production compiler/checker architectures.

## File Layout

- `SKILL.md` — core mental model, vocabulary, examples, and links to focused topic files.
- `struct-selection.md`, `query-pipeline.md`, `database-architecture.md`, etc. — focused topic guides for deeper design decisions.
- `references/` — topic-scoped supporting notes from Salsa itself and real-world projects such as rust-analyzer, ty, Cairo, BAML, Fe, django-language-server, stc, wgsl-analyzer, and Mun.

## Activation Examples

Should trigger:

- "How should I structure this `#[salsa::db]`?"
- "Should this value be an input, tracked struct, interned struct, or plain Rust type?"
- "Why did this tracked function re-run after an unrelated edit?"
- "How do I test that Salsa reused this query result?"
- "This LSP server needs cancellation around Salsa queries."
- "Should diagnostics use accumulators or return values?"
- "How do I bound Salsa memory usage with LRU?"

Should not trigger:

- "Explain Rust ownership."
- "Review this non-Salsa compiler architecture."
- "Create a Todoist task for learning Salsa."
- "Format this markdown file."

Good holdout prompts:

- "Can this tracked struct become an interned ID plus side table?"
- "Is this durability assignment safe, or will it hide invalidation?"
- "This cycle reaches a fixed point locally but oscillates in one project. What should change?"
