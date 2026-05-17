
# Accumulators: Side-Channel Output from Tracked Functions

Tracked functions are memoized — side effects like `eprintln!` only fire on first execution. When the function returns its cached value, side effects are silently skipped. Accumulators are Salsa's solution: a structured way to emit values (diagnostics, warnings, logs) that are correctly replayed across memoized executions.

## Quick Start

1. **Define** the accumulator:
   ```rust
   #[salsa::accumulator]
   pub struct Diagnostics(Diagnostic);
   ```

2. **Push** values inside a tracked function:
   ```rust
   use salsa::Accumulator;

   #[salsa::tracked]
   fn type_check(db: &dyn Db, item: Item) {
       if found_error {
           Diagnostic::new("error message").accumulate(db);
       }
   }
   ```

3. **Collect** values at the top-level:
   ```rust
   let diags: Vec<Diagnostic> = type_check::accumulated::<Diagnostics>(db, item);
   ```

## Key Behaviors

### Deduplication and Order
- **Deduplication**: If a tracked function is called multiple times with the same arguments, its values appear **once** in the parent's result.
- **Execution Order**: Values appear in the order they were pushed, following a depth-first walk of the call tree.

### Memoization and Backdating
- **Persistence**: When a result is reused from cache, Salsa "replays" the accumulated values without re-executing the function.
- **Backdating**: If a function re-executes but produces the same return value, the accumulated values are still updated to the new ones.

### Critical Constraints
- **Untracked Dependency**: Calling `accumulated()` adds an untracked dependency to the caller. The calling query will re-execute on **every revision**. Use it only at top-level entry points.
- **Cycles**: Accumulators **cannot** be used in queries participating in fixed-point iteration (`cycle_fn`). This will cause a runtime panic.

## Decision: Accumulators vs. Return Values

Accumulators are excellent for small-to-medium projects (like `django-language-server`). However, major projects like **ty**, **Cairo**, and **rust-analyzer** skip them in favor of embedding diagnostics in return values.

| Factor | Accumulators | Return-Value Diagnostics |
|--------|-------------|--------------------------|
| **Scale (>10k files)** | Poor (untracked deps) | Good (standard caching) |
| **Suppression** | Difficult | Natural |
| **Setup** | Minimal | More wiring |

**Recommendation:** Start with accumulators. If you need suppression tracking (e.g., `# type: ignore`) or if diagnostic collection becomes a performance bottleneck, migrate to return-value diagnostics.

## Examples and Patterns

- [references/salsa-framework.md](references/accumulators/salsa-framework.md) — Canonical Calc example and deduplication behavior.
- [references/djls-patterns.md](references/accumulators/djls-patterns.md) — Production usage in `django-language-server` (2 diagnostic phases).
- [references/fe-patterns.md](references/accumulators/fe-patterns.md) — Hybrid approach: accumulators for parser, return values for analysis.
- [references/large-scale-diagnostics.md](references/accumulators/large-scale-diagnostics.md) — Deep dive into why ty, Cairo, and BAML avoid accumulators.

## Bridging External Error Systems to Accumulators

**[Legacy API/Architecture: stc]** When wrapping a non-Salsa library that has its own error reporting mechanism (callbacks, emitters, loggers), create an adapter that collects errors into a `Vec`, then push them to a Salsa accumulator after the library finishes. stc does this to bridge SWC's `Handler`/`Emitter` diagnostic system: a custom `Emitter` backed by `Arc<Mutex<Vec<Diagnostic>>>` collects errors during type checking, then each error is pushed to a `Diagnostics` accumulator. This pattern generalizes to any external library with callback-based error reporting.

For the full stc external checker bridge pattern, see the [query-pipeline.md](query-pipeline.md) skill's stc reference.

## Common Mistakes

- **Pushing outside a tracked function**: This will panic. Values must be pushed during a tracked function's execution.
- **Reading inside a hot query**: Don't call `accumulated()` in queries that are themselves called frequently; the untracked dependency will kill performance.
- **Forgetting the import**: You must `use salsa::Accumulator` to get the `.accumulate()` method.
- **Using in cycles**: If your query has `cycle_fn`, use return-value diagnostics instead.
