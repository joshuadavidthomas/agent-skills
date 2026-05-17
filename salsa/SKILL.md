---
name: salsa
description: >
  Mental-model reset for Salsa, the incremental computation framework for Rust.
  Use when building or reviewing Salsa databases, tracked functions, input/
  tracked/interned structs, query pipelines, accumulators, cancellation,
  durability, LSP integration, memory management, cycles, or production Salsa
  architecture. Triggers on #[salsa::db], #[salsa::input], #[salsa::tracked],
  #[salsa::interned], #[salsa::accumulator], salsa::Storage, memoization,
  revisions, backdating, red-green algorithm, WillExecute,
  DidValidateMemoizedValue, Cancelled, returns(ref), no_eq, lru, cycle_fn,
  cycle_result, durability, or salsa::Event.
---

# Salsa: Incremental Computation for Rust

Salsa is a framework for **incremental recomputation**. You define inputs and pure functions over them. Salsa memoizes every function call. When inputs change, it re-executes only the functions whose dependencies actually changed — skipping everything else.

Salsa powers [rust-analyzer](https://rust-analyzer.github.io/) (Rust IDE), [ty](https://docs.astral.sh/ty/) (Python type checker), and [Cairo](https://github.com/starkware-libs/cairo), all of which need sub-second response times on large codebases after small edits.

## The Mental Model

```
                    Salsa Database
                    ┌─────────────────────────────────────┐
 External world     │                                     │
 (editor, CLI,      │  Inputs ──→ Tracked Fns ──→ Output  │
  filesystem)       │    │            │                    │
        │           │    └── memoized ┘                    │
        │           │    dependencies tracked automatically│
        ▼           └─────────────────────────────────────┘
  Mutate inputs             │
  (new revision)            ▼
                    Only re-run what changed
```

The core loop:

```rust
let db = MyDatabase::default();

// 1. Create inputs
let file = SourceFile::new(&db, "fn main() {}".into(), path);

// 2. Compute (Salsa memoizes everything)
let result = analyze(&db, file);

// 3. Mutate an input (starts a new "revision")
file.set_text(&mut db).to("fn main() { 42 }".into());

// 4. Re-compute — Salsa reuses what it can
let result = analyze(&db, file);  // Only re-runs what depends on text
```

## Core Concepts

### The Database

A struct with `#[salsa::db]` that stores all cached data. It's the single source of truth — every Salsa operation takes a `&db` or `&mut db`.

```rust
#[salsa::db]
#[derive(Default, Clone)]
pub struct Database {
    storage: salsa::Storage<Self>,
}

#[salsa::db]
impl salsa::Database for Database {}
```

→ Deep dive: [database-architecture.md](database-architecture.md) for layered traits, test vs production, and side tables.

### Inputs — The Roots

External data entering the system. The only mutable Salsa structs. Just newtypes around integer IDs (`Copy`, no lifetime).

```rust
#[salsa::input]
pub struct SourceFile {
    #[returns(ref)]
    pub text: String,
    pub path: PathBuf,
}
```

### Tracked Functions — The Computation

Pure functions whose results are memoized. Salsa records which inputs/fields each call reads. On re-execution, it checks if those dependencies changed.

```rust
#[salsa::tracked]
fn parse(db: &dyn Db, file: SourceFile) -> Ast<'_> {
    let text = file.text(db);  // dependency recorded
    // ... parse ...
    Ast::new(db, statements)
}
```

→ Deep dive: [query-pipeline.md](query-pipeline.md) for return modes, LRU, `no_eq`, `specify`, and granularity.

### Tracked Structs — Intermediate Entities

Created inside tracked functions. Have per-field change tracking. Carry a `'db` lifetime.

```rust
#[salsa::tracked]
pub struct Function<'db> {
    #[id]
    pub name: Word<'db>,         // used for cross-revision matching
    #[tracked]
    #[returns(ref)]
    pub body: Expression<'db>,   // per-field tracking
}
```

### Interned Structs — Cheap Equality

Same data → same integer ID. Used for identifiers, type representations, module paths. Carry a `'db` lifetime.

```rust
#[salsa::interned]
pub struct Word<'db> {
    #[returns(ref)]
    pub text: String,
}
```

→ Deep dive: [struct-selection.md](struct-selection.md) for the decision framework, including ty's "no tracked structs" and rust-analyzer's "intern every definition" styles.

### Accumulators — Side-Channel Output

Report diagnostics from tracked functions without affecting the return value.

```rust
#[salsa::accumulator]
pub struct Diagnostics(Diagnostic);

// Inside a tracked function:
Diagnostics::push(db, Diagnostic { message: "type error".into(), .. });
```

→ Deep dive: [accumulators.md](accumulators.md).

### Revisions and the Red-Green Algorithm

Every input mutation increments a **revision counter**. When you call a tracked function, Salsa checks its dependencies since the last cached result. If they changed, it re-executes; if the new result equals the old one (**backdating**), it stops propagation.

### Durability — Optimization Hint

Inputs can be tagged with `LOW`, `MEDIUM`, or `HIGH` durability. When only `LOW`-durability inputs change, Salsa skips validating stable subgraphs.

→ Deep dive: [durability.md](durability.md).

## Where to Go Deeper

- For a complete walkthrough of a calculator project: see [references/overview/minimal-example.md](references/overview/minimal-example.md).

| I want to... | Read |
|---------------|------|
| Choose between input, tracked, and interned | [struct-selection.md](struct-selection.md) |
| Design my tracked functions and query graph | [query-pipeline.md](query-pipeline.md) |
| Structure my database with layered traits | [database-architecture.md](database-architecture.md) |
| Handle recursive/cyclic queries | [cycle-handling.md](cycle-handling.md) |
| Support cancellation in an LSP or CLI | [cancellation.md](cancellation.md) |
| Optimize with durability levels | [durability.md](durability.md) |
| Test that incremental reuse actually works | [incremental-testing.md](incremental-testing.md) |
| Control memory with LRU and `no_eq` | [memory-management.md](memory-management.md) |
| Build an LSP server backed by Salsa | [lsp-integration.md](lsp-integration.md) |
| Report diagnostics via accumulators | [accumulators.md](accumulators.md) |
| Move from prototype to production scale | [production-patterns.md](production-patterns.md) |
| Access low-level plumbing and "Level 4" patterns | [advanced-plumbing.md](advanced-plumbing.md) |

## Key Vocabulary

- **Revision**: A version of the database between input mutations.
- **Ingredient**: Any Salsa-managed item (input, tracked struct, interned struct, tracked fn, accumulator).
- **Backdating**: If a re-executed function produces the same result, it's marked unchanged to prevent downstream re-execution.
- **Red-green algorithm**: Salsa's strategy for deciding what to re-execute.
- **Durability**: A promise about how often an input changes.
- **LRU**: Least Recently Used eviction for bounding cache size.
- **`no_eq`**: Skip equality comparison on result — always propagate changes.
- **Cycle**: When tracked functions form a dependency loop.

## Real-World Scale

- **ty**: 2 inputs, 0 tracked structs for types (all interned), 60+ cycle sites.
- **rust-analyzer**: 5+ inputs, tracked structs for collection caches, 6-layer DB hierarchy.
- **Cairo**: 4 singleton inputs, 127+ tracked functions, 29 cycle sites, parallel compilation via `CloneableDatabase`.
- **django-language-server**: 1 input, 2 accumulators, 5-layer DB (~78 Rust files — very approachable).
- **BAML**: 15 tracked structs, 6-layer DB, documented early cutoff strategies.
- **Fe**: marker traits for compilation phase enforcement, hybrid accumulator/return-value diagnostics.
- **stc** [Legacy API]: 7 tracked functions wrapping the SWC TypeScript ecosystem — the "thin Salsa shell" approach to incrementalizing an existing tool.
- **wgsl-analyzer** [Legacy API]: ~30 queries across 4 layers (~110 Rust files) — validates the rust-analyzer LSP architecture in a GPU shader language.
- **Mun** [Legacy API]: ~40 queries across 6 query groups (~150 Rust files) — the only project extending Salsa through LLVM codegen to shared library output, with a hot-reloading compiler daemon.

The hardest part of Salsa is the design decisions about granularity, identity, and what to track. **django-language-server** and **BAML** are the best starting points for learning. **stc** [Legacy API] is the best example of wrapping an existing non-Salsa library with minimal Salsa code. **Mun** [Legacy API] is the best example of extending Salsa queries all the way to machine code generation and hot reloading.

## Further Reading

- **Salsa book**: https://salsa-rs.github.io/salsa/
- **Salsa repo**: https://github.com/salsa-rs/salsa (see `examples/calc/`, `examples/lazy-input/`)
- **ty**: `crates/ty_*` and `crates/ruff_db` in https://github.com/astral-sh/ruff
- **rust-analyzer**: https://github.com/rust-lang/rust-analyzer
- **Cairo**: https://github.com/starkware-libs/cairo
- **BAML**: https://github.com/BoundaryML/baml
- **Fe**: https://github.com/argotorg/fe
- **django-language-server**: https://github.com/joshuadavidthomas/django-language-server
- **stc** [Legacy API]: https://github.com/dudykr/stc
- **Mun** [Legacy API]: https://github.com/mun-lang/mun
