# stc Patterns — Thin Salsa Shell Over a TypeScript Type Checker

> **[Legacy API/Architecture]** stc uses the old Salsa 2022 jar-based API (`#[salsa::jar(db = Db)]`,
> `salsa::DbWithJar<Jar>`, `salsa::Storage<Self>`). **Do not use its syntax as a model for modern Salsa
> code.** The architectural patterns described here are version-agnostic — they apply to any Salsa version.
> For modern API syntax, see the `calc` example or BAML/djls patterns.

## Overview

stc is a TypeScript type checker that wraps the SWC (Speedy Web Compiler) ecosystem — parser, AST, source
maps — with a thin layer of 7 Salsa tracked functions in a single crate (`stc_ts_lang_server`, 6 files).
All heavy lifting (parsing, type checking, module loading) is done by non-Salsa libraries. Salsa serves
purely as an orchestration and caching layer.

This is the **"incrementalize an existing tool"** approach — distinct from building everything Salsa-native
(ty, rust-analyzer) or building a compiler from scratch on Salsa (Cairo, BAML, Fe).

## The "Thin Shell" Architecture

```
stc architecture:

  ┌─────────────────────────────────────────────┐
  │  Salsa shell (1 crate, 6 files, 7 tracked)  │
  │    SourceFile (input)                        │
  │    → parse_ast (tracked) → ParsedFile        │
  │    → prepare_input (tracked)                 │
  │    → check_type (tracked) → ModuleTypeData   │
  │    → tsconfig_for / parse_ts_config          │
  │    → get_module_loader                       │
  └──────────┬──────────────────────────────────-┘
             │ calls into
  ┌──────────▼──────────────────────────────────-┐
  │  Non-Salsa libraries (~30 crates)            │
  │    swc_ecma_parser   (parsing)               │
  │    stc_ts_type_checker (type checking)       │
  │    stc_ts_module_loader (module resolution)  │
  │    stc_ts_env         (configuration)        │
  │    swc_common          (source maps, spans)  │
  └─────────────────────────────────────────────-┘
```

**Key insight:** The non-Salsa libraries know nothing about Salsa. They take plain Rust types (file names,
AST nodes, config structs) and return plain Rust types. The Salsa shell is responsible for:
- Storing external data as inputs (`SourceFile`)
- Wrapping library calls in tracked functions (caching + invalidation)
- Bridging error reporting (external `Emitter` → Salsa accumulator)
- Providing non-Salsa state via the `Db` trait (`shared()` method)

## Pattern 1: External Parser Bridge

Wrapping a non-Salsa parser in a tracked function. The general pattern:
1. Read source text from a Salsa input
2. Create parser-specific state from non-Salsa database state (e.g., `SourceMap`)
3. Call the external parser
4. Wrap the result in a tracked struct with `no_eq` (external ASTs don't have meaningful Salsa equality)

```
stc/crates/stc_ts_lang_server/src/parser.rs
```

The tracked struct uses `#[no_eq]` on both fields because:
- `filename` is redundant (it's already tracked via the input)
- `program` (the AST) is an external type without meaningful equality — if the input changed, the AST changed

The tracked function:
- Gets the source map from non-Salsa state (`db.shared().cm`)
- Creates a new SWC source file (registers with the shared SourceMap)
- Calls `swc_ecma_parser::parse_file_as_program` — a plain function, not Salsa-aware
- Wraps errors and comments via SWC's callback API (`Some(&db.shared().comments)`)
- Returns a tracked struct wrapping the external AST

**General lesson:** When bridging an external parser, the tracked function acts as an adapter. It translates
Salsa ingredients (inputs) into the external parser's expected arguments, calls the parser, and wraps the
result back into Salsa-tracked form.

## Pattern 2: External Type Checker Bridge with Error Capture

Wrapping a non-Salsa type checker and capturing its errors for Salsa's accumulator system.

```
stc/crates/stc_ts_lang_server/src/type_checker.rs
```

The `check_type` function demonstrates the general pattern:

1. **Create an error bridge** — A custom `Emitter` implementation backed by `Arc<Mutex<Vec<Diagnostic>>>`.
   The external type checker reports errors through SWC's `Handler`/`Emitter` API. The bridge collects them.

2. **Set up the non-Salsa context** — Source map, globals, environment. These come from non-Salsa state
   on the database (`db.shared()`), not from Salsa queries.

3. **Run the external checker** — `Checker::new(...)` and `checker.check(...)` know nothing about Salsa.
   They operate on plain Rust types.

4. **Drain errors and push to accumulator** — After the checker finishes, take the collected errors from
   the bridge and push each one to the Salsa accumulator: `Diagnostics::push(db, err)`.

5. **Wrap the result** — The type checker's output (`Type`) is stored in a tracked struct (`ModuleTypeData`).

**General lesson:** When an external library has its own error reporting mechanism (callbacks, emitters,
loggers), create an adapter that collects errors into a `Vec`, then push them to a Salsa accumulator
after the external library finishes. This bridges the library's error system to Salsa's incremental
diagnostic infrastructure.

## Pattern 3: `DebugIgnore<T>` — Bridging Non-Debug External Types

External library types often don't implement `Debug`, which Salsa requires for tracked struct fields.
stc solves this with a simple wrapper:

```
stc/crates/stc_utils/src/lib.rs (approximate — the type is re-exported from stc_utils)
```

The concept:
```rust
// A wrapper that satisfies Debug by printing a placeholder
pub struct DebugIgnore<T>(pub T);

impl<T> fmt::Debug for DebugIgnore<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("<ignored>")
    }
}
```

Used on tracked struct fields that hold external types:
- `DebugIgnore<Env>` — SWC environment (configuration + builtins)
- `DebugIgnore<Arc<dyn LoadModule>>` — Module loader trait object

**General lesson:** When integrating external libraries whose types don't implement `Debug`, wrap them
in a newtype that provides a placeholder `Debug` impl. Pair with `#[no_eq]` on the tracked struct field
since these types typically don't implement `Eq` either. This is a pragmatic bridge — not elegant, but
effective for incremental adoption.

## Pattern 4: Non-Salsa State via Db Trait Method

stc stores all external library state in a shared struct, exposed through the `Db` trait:

```
stc/crates/stc_ts_lang_server/src/lib.rs (Db trait and Shared struct)
```

The `Shared` struct holds:
- `client: Client` — LSP client for sending notifications
- `cm: Arc<SourceMap>` — SWC source map (thread-safe, accumulated during parsing)
- `globals: Arc<Globals>` — SWC thread-local globals workaround
- `stable_env: StableEnv` — Environment configuration
- `comments: StcComments` — SWC comment storage

The `Db` trait exposes it:
```rust
pub trait Db: salsa::DbWithJar<Jar> {
    fn shared(&self) -> &Arc<Shared>;
    fn read_file(&self, path: &Arc<FileName>) -> SourceFile;
}
```

**General lesson:** When an external library needs mutable shared state that tracked functions access
(source maps, global registries), store it in a struct exposed through the database trait. This keeps
the external state accessible from tracked functions while maintaining Salsa's ownership model. The
`read_file` method doubles as the file side-table lookup.

## Pattern 5: Simplest Possible Salsa LSP

stc's LSP architecture is the simplest possible: a single dedicated thread processes all Salsa
operations sequentially via an `mpsc` channel. No snapshots, no cancellation, no thread pool.

```
stc/crates/stc_ts_lang_server/src/lib.rs (Project struct)
```

The architecture:
1. Async LSP handler receives notifications (open, change)
2. Sends a `Request` enum via `std::sync::mpsc::Sender`
3. A single `spawn_blocking` thread owns the `Database` and loops on `rx.recv()`
4. For each request: update inputs → run queries → send diagnostics back via async task

This is simpler than BAML's approach (which calls Salsa synchronously in the LSP handler) because
it fully isolates Salsa on its own thread. The tradeoff: no concurrent queries, no cancellation of
in-progress work.

**Complexity progression for Salsa LSPs:**

| Level | Architecture | Example |
|-------|-------------|---------|
| 1 | Dedicated thread + mpsc | **stc** [Legacy API] |
| 2 | Synchronous in handler | **BAML** |
| 3 | Snapshots + queue | **djls** |
| 4 | Snapshots + thread pool | **Fe** |
| 5 | Host/snapshot + cancellation + retry | **ty**, **rust-analyzer** |

## When to Use the "Thin Shell" Approach

**Good fit when:**
- You have an existing compiler/tool that works and you want to incrementalize it
- The existing tool's API is function-oriented (takes inputs, returns outputs)
- You're exploring whether Salsa provides value before committing to a full rewrite
- The tool's internal state is mostly functional / can be reconstructed from inputs

**Poor fit when:**
- The existing tool has pervasive internal mutable state that's hard to snapshot
- You need fine-grained incremental reuse within the tool (e.g., per-function re-type-checking)
- The tool's API doesn't support partial results (all-or-nothing computation)

The thin shell gives you coarse-grained incrementality: if the input file didn't change, the entire
parse/check result is cached. For finer-grained incrementality (only re-checking changed functions),
you'd need to restructure the inner libraries to expose more granular query points — which is what
ty and rust-analyzer have done.

## File Locations

All Salsa usage in stc is in one crate:

| File | Contains |
|------|----------|
| `stc/crates/stc_ts_lang_server/src/lib.rs` | Jar, Db trait, Database struct, LSP server, Project/mpsc architecture |
| `stc/crates/stc_ts_lang_server/src/ir.rs` | `SourceFile` input |
| `stc/crates/stc_ts_lang_server/src/config.rs` | `ParsedTsConfig` tracked struct, tsconfig queries |
| `stc/crates/stc_ts_lang_server/src/parser.rs` | `ParserInput` input, `ParsedFile` tracked struct, `parse_ast` |
| `stc/crates/stc_ts_lang_server/src/module_loader.rs` | `ProjectEnv` tracked struct, `get_module_loader` |
| `stc/crates/stc_ts_lang_server/src/type_checker.rs` | `TypeCheckInput`, `ModuleTypeData`, `Diagnostics` accumulator, `check_type` |
