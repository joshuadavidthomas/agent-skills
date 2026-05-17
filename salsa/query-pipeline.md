
# Designing the Query Pipeline

A Salsa query pipeline is a directed graph of `#[salsa::tracked]` functions flowing from inputs to outputs. Each tracked function is memoized — Salsa caches its result and only re-executes when dependencies change.

## The Typical Pipeline Shape

Most Salsa projects follow a **coarse early, fine later** pattern:

```
File (input)
  → source_text (tracked fn)
    → parsed_module (tracked fn, lru, no_eq)
      → semantic_index (tracked fn, no_eq)
        → place_table / use_def_map (tracked fn, per-scope)
          → type inference (tracked fn, cycle handling)
            → diagnostics
```

Parse the whole file (cheap), but type-check per scope (expensive, enables granular reuse). This is the **split pattern**: one coarse function feeds many fine-grained ones.

- **Simplest example:** [references/djls-patterns.md](references/query-pipeline/djls-patterns.md) (django-language-server)
- **Large-scale example:** [references/cairo-patterns.md](references/query-pipeline/cairo-patterns.md) (Cairo compiler)

## Tracked Function Basics

```rust
#[salsa::tracked]
fn parse_file(db: &dyn crate::Db, file: SourceFile) -> Ast {
    let contents: &str = file.contents(db);
    // ... parse ...
}
```

Requirements:
- First argument: `&dyn YourDb` (or `&dyn salsa::Database`)
- Remaining arguments: Salsa ingredients (inputs, tracked, interned — **not** plain Rust types)
- Return type: `Send + Sync + Clone` (unless using `returns(ref)`)

## Available Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `returns(MODE)` | Control how values are returned | `returns(ref)` |
| `lru = N` | Bound cache to N entries | `lru = 200` |
| `no_eq` | Skip equality check on result | Always re-propagate |
| `specify` | Allow imperatively setting results | For built-in items |
| `cycle_fn` + `cycle_initial` | Fixed-point cycle recovery | Type inference |
| `cycle_result` | Fallback value on cycle | Simple recovery |
| `heap_size = path` | Track memory usage | Profiling |

## Return Modes

The return mode is the most impactful attribute for performance.

| Mode | Stored | Caller Gets | Use When |
|------|--------|-------------|----------|
| *(default)* | `T` | `T` (cloned) | Small `Copy`/cheap-`Clone` types |
| `returns(ref)` | `T` | `&T` | Large owned types (`String`, `Vec`, structs) |
| `returns(deref)` | `T: Deref` | `&T::Target` | `Arc<T>` → caller gets `&T` |
| `returns(clone)` | `T` | `T` (cloned) | Explicit clone when default won't work |
| `returns(as_ref)` | `Option<T>` | `Option<&T>` | Optional large values |
| `returns(as_deref)` | `Option<Box<T>>` | `Option<&T>` | Optional boxed values |

**Style Guide:** Use `returns(ref)` for any heap-allocated return (String, Vec, Arc). It avoids cloning and is the default style in the Cairo codebase.

## LRU Caching

By default, Salsa caches every result forever within a revision. To prevent unbounded memory in LSP servers, set `lru` to bound the cache size.

```rust
#[salsa::tracked(returns(ref), no_eq, lru = 200)]
fn parsed_module(db: &dyn Db, file: File) -> ParsedModule { ... }
```

- **Parse:** `lru = 128` (rust-analyzer)
- **Macros:** `lru = 1024` (rust-analyzer)
- **Runtime tuning:** `parsed_module::set_lru_capacity(db, 256)`

## `no_eq` — Skip Equality Checks

When a tracked function re-executes, Salsa normally compares the new result to the old one. If equal, downstream queries are skipped (**backdating**). Use `no_eq` to skip this check:

- When the type doesn't implement `Eq`.
- When equality checks are more expensive than downstream re-execution.
- When every input change truly changes the output (AST offsets shift on edit).

**Constraint:** `no_eq` cannot be combined with `cycle_fn`.

## Design Patterns

### The Wrapper Function Pattern
Used to pass plain Rust types as arguments by wrapping them in an interned ingredient.
See: [references/common-patterns.md#the-wrapper-function-pattern](references/query-pipeline/common-patterns.md#the-wrapper-function-pattern)

### Tracked Methods on Input Structs
Allows computing derived state (e.g., `file.kind(db)`) directly on inputs.
See: [references/common-patterns.md#tracked-methods-on-input-structs](references/query-pipeline/common-patterns.md#tracked-methods-on-input-structs)

### The Dual-Query / Triple-Split Pattern
Maximizes early cutoff by separating cosmetic changes (spans/comments) from semantic ones (signatures).
See: [references/common-patterns.md#the-dual-query-or-triple-split-pattern](references/query-pipeline/common-patterns.md#the-dual-query-or-triple-split-pattern) and [references/baml-patterns.md](references/query-pipeline/baml-patterns.md).

### The Thin Salsa Shell Over Existing Libraries
**[Legacy API/Architecture: stc]** When you have an existing compiler or tool you want to incrementalize, you don't have to rewrite everything with Salsa. The "thin shell" approach wraps existing library calls in tracked functions — Salsa handles caching and invalidation while the non-Salsa libraries do all the heavy lifting. stc wraps the entire SWC TypeScript parser and its own type checker with just 7 tracked functions in a single crate.
See: [references/stc-patterns.md](references/query-pipeline/stc-patterns.md)

### Extending Queries to Machine Code (LLVM Backend)
**[Legacy API/Architecture: Mun]** Mun is the only surveyed project where Salsa's computation graph extends to binary code generation. A `CodeGenDatabase` query group sits atop the HIR stack, producing LLVM IR and shared libraries as tracked function results. The pipeline: `source_text → parse → item_tree → package_defs → type_inference → module_partition → assembly_ir / target_assembly`. The LLVM `TargetMachine` is not thread-safe, so Mun returns it wrapped as `ByAddress<Rc<TargetMachine>>` — using `Rc` (not `Arc`) and `ByAddress` for pointer-equality caching. This works because the codegen layer is single-threaded. The compiler daemon then watches for file changes and only writes assemblies whose `target_assembly` query results actually changed, enabling hot reloading.
See: [references/mun-patterns.md](references/query-pipeline/mun-patterns.md)

### The Dummy Tracked Parameter
Cairo uses a `Tracked = ()` dummy parameter for 50+ tracked functions to satisfy Salsa's first-parameter optimization when using blanket-impl delegation.
See: [references/cairo-patterns.md#trait-method-tracked-function-delegation](references/query-pipeline/cairo-patterns.md#trait-method-tracked-function-delegation)

### Deriving Metadata from Existing Inputs
**[Legacy API/Architecture: wgsl-analyzer]** Rather than creating new Salsa inputs for file-level metadata like language edition, wgsl-analyzer computes `EditionedFileId` (file + edition) inside a tracked function by inspecting the file path extension (`.wgsl` vs `.wesl`). This avoids input proliferation for data derivable from existing inputs. If a file's language variant can be determined from its path, make it a derived query, not a new input field.

### Diagnostic Aggregation Pipelines
Multi-layer pyramids from per-item → module → file → crate, with parallel warmup via Rayon.
See: [references/cairo-patterns.md#multi-layer-diagnostic-aggregation](references/query-pipeline/cairo-patterns.md#multi-layer-diagnostic-aggregation)

## Common Mistakes

- **Forgetting `returns(ref)` on large types.** Leads to excessive cloning.
- **Setting LRU too low.** Causes "thrashing" where values are evicted and re-computed repeatedly.
- **Tracking at expression granularity.** Tracking overhead per expression usually exceeds the cost of re-evaluation. Track at scope/module/file level instead.
- **Passing non-Salsa ingredients.** Tracked functions can only take ingredients. Use the wrapper pattern for plain Rust types.
- **Using `specify` with `lru`.** These attributes are incompatible.

For full production code examples, see:
- [references/djls-patterns.md](references/query-pipeline/djls-patterns.md) — django-language-server (simplest complete example)
- [references/ty-patterns.md](references/query-pipeline/ty-patterns.md) — ty's layer-by-layer pipeline
- [references/rust-analyzer-patterns.md](references/query-pipeline/rust-analyzer-patterns.md) — rust-analyzer's layered query graph
- [references/cairo-patterns.md](references/query-pipeline/cairo-patterns.md) — Cairo's 8-layer compiler pipeline
- [references/baml-patterns.md](references/query-pipeline/baml-patterns.md) — BAML's HIR/TIR/VIR pipeline
- [references/fe-patterns.md](references/query-pipeline/fe-patterns.md) — Fe's tracked methods and fixed-point cycles
- [references/stc-patterns.md](references/query-pipeline/stc-patterns.md) — **[Legacy API]** stc's "thin Salsa shell" over SWC parser + type checker
- [references/mun-patterns.md](references/query-pipeline/mun-patterns.md) — **[Legacy API]** Mun's LLVM codegen as Salsa query endpoint, hot-reloading compiler daemon
