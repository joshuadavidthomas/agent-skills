# Why Major Projects Skip Accumulators

Neither ty (the Python type checker in the Ruff/ty monorepo) nor rust-analyzer (Rust IDE) uses Salsa accumulators for diagnostics. This is a deliberate architectural choice made by the two largest Salsa projects.

## The Problem: Untracked Dependencies

Salsa adds an **untracked dependency** to every query that reads accumulated values via `accumulated()`. This has a cascading effect on incrementality:

1. **Re-execution on every revision**: A query calling `accumulated()` must re-execute every time *any* input changes, because Salsa cannot know if the accumulated values changed without re-collecting them from the dependency graph.
2. **Compound overhead**: While acceptable for a single top-level entry point, this overhead becomes prohibitive if intermediate queries need to read diagnostics (e.g., for suppression tracking or "fail fast" logic).
3. **Scale bottlenecks**: In projects with 100k+ files, having the diagnostic collection query re-run on every keystroke for every file creates a significant performance floor.

## Alternative: Diagnostics in Return Values

Instead of using a side channel, major projects embed diagnostics directly in query return values. This allows diagnostics to travel through the standard Salsa memoization and dependency system.

| Project | Approach | Key Benefit |
|---------|----------|-------------|
| **ty** | `ScopeInferenceExtra` struct in return value | Diagnostics cached with types; handles suppression tracking. |
| **rust-analyzer** | Non-Salsa diagnostic collection methods | Diagnostics computed by reading cached query results on demand. |
| **Cairo** | 4-layer aggregation pyramid | Fine-grained reuse (header vs body); parallel warmup via Rayon. |
| **BAML** | Tracked struct field | Simplest implementation: `Result.diagnostics(db)` is a tracked field. |
| **Fe** | Hybrid approach | Accumulators for simple parser errors; return values for complex analysis. |

### ty's Approach: Diagnostics in Return Values

ty returns a struct containing both the primary result and an optional "extra" payload for diagnostics:

```rust
#[derive(Debug, Default)]
struct ScopeInferenceExtra<'db> {
    diagnostics: TypeCheckDiagnostics,
    used_suppressions: FxHashSet<TextRange>,
    // ...
}
```

**Why this works:**
- **Cached with types**: When types are reused, diagnostics are automatically reused.
- **Suppression correlation**: Naturally correlates diagnostics with `# type: ignore` comments.
- **Memory efficiency**: Uses `Option<Box<Extra>>` so clean code pays zero overhead.

### Cairo's Approach: Aggregation Pyramid

Cairo uses a hierarchy of tracked functions to aggregate diagnostics from fine to coarse granularity:

1. **Per-item split**: `free_function_declaration_diagnostics` vs `free_function_body_diagnostics`.
2. **Module aggregation**: `module_semantic_diagnostics` walks items and merges.
3. **Top-level walk**: `DiagnosticsReporter` walks crates and modules.

**Why this works:**
- **Parallelism**: The aggregation can be warmed up in parallel using Rayon.
- **Granular reuse**: Changing a function body doesn't invalidate its signature (declaration) diagnostics.

### BAML's Approach: Tracked Fields

BAML stores diagnostics as a field on a tracked struct:

```rust
#[salsa::tracked]
pub struct LoweringResult<'db> {
    #[tracked] #[returns(ref)]
    pub item_tree: Arc<ItemTree>,
    #[tracked] #[returns(ref)]
    pub diagnostics: Vec<HirDiagnostic>,
}
```

A centralized walker then calls `file_lowering(db, file).diagnostics(db)` for every file.

## Decision Framework

| Factor | Accumulators | Return-Value Diagnostics |
|--------|-------------|--------------------------|
| **Setup cost** | Minimal — one macro | More wiring — merge logic needed |
| **Scale (>10k files)** | Poor — untracked dependencies | Good — standard caching |
| **Suppression** | Difficult | Natural — same data structure |
| **Deduplication** | Automatic | Manual (you merge) |
| **Code clarity** | Implicit side channel | Explicit data flow |

**Recommendation:** Start with accumulators for prototypes and small projects (like django-language-server). Switch to return-value diagnostics if you need suppression tracking, per-scope collection, or if `accumulated()` becomes a performance bottleneck in your hot path.
