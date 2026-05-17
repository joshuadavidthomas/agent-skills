
# Controlling Salsa Memory Usage

Salsa caches every tracked function result forever by default. In a long-running application (LSP server, watch-mode CLI), this means unbounded memory growth. Salsa provides four levers to control this:

| Lever | What It Does | When to Use |
|-------|-------------|-------------|
| `lru = N` | Evict least-recently-used results | Expensive queries with many inputs (parse, macro expand) |
| `no_eq` | Skip equality check on result | Large values where comparison is expensive (ASTs, indexes) |
| `returns(ref)` / `returns(deref)` | Avoid cloning on access | Large return values (Arc, Vec, String) |
| `heap_size = fn` | Track heap allocations | Memory profiling and reporting |

## LRU Eviction

Add `lru = N` to a tracked function to cap its cache:

```rust
#[salsa::tracked(lru = 128)]
fn parse(db: &dyn Db, file: SourceFile) -> Arc<Ast> { ... }
```

Salsa keeps at most 128 memoized results. Eviction happens at the start of each new revision (triggered by any input mutation). Without `lru`, every result lives forever.

**Key Insight:** Functions without `lru` use a zero-overhead no-op eviction policy. Only add `lru` where you actually need it.

### How to Size LRU Caches

Sizes usually grow with computational cost. Expensive queries get bigger caches.

| Project | Query | LRU Size | Rationale |
|---------|-------|----------|-----------|
| ruff_db | `parsed_module` | 200 | Empirical guess |
| rust-analyzer | `parse` | 128 | Base capacity |
| rust-analyzer | `parse_macro_expansion` | 512 | Moderate frequency |
| rust-analyzer | `borrowck` | 2024 | Most expensive computation |

For tiered LRU patterns (128 → 512 → 2024), see [references/rust-analyzer-patterns.md](references/memory-management/rust-analyzer-patterns.md).

## Equality Skipping with `no_eq`

By default, Salsa compares the new result to the old one after re-execution. If equal, dependents don't re-run (backdating). For large structures like ASTs, this comparison is expensive and rarely finds "equal" due to byte offset shifts.

```rust
#[salsa::tracked(returns(ref), no_eq, lru = 200)]
fn parsed_module(db: &dyn Db, file: File) -> ParsedModule { ... }
```

**Trade-off:** Dependents always re-run when the function re-executes. Pair with the **Granular Extraction Pattern** to mitigate this.

### The Granular Extraction Pattern

Combine `no_eq` on a coarse query with fine-grained extraction queries that use equality:

```rust
// Coarse: recomputes entire file-level index. no_eq skips expensive comparison.
#[salsa::tracked(returns(ref), no_eq)]
fn semantic_index(db: &dyn Db, file: File) -> SemanticIndex<'_> { ... }

// Fine: extracts one scope's data. Salsa compares Arc pointers — O(1).
// If this scope's PlaceTable didn't change, dependents don't re-run.
#[salsa::tracked(returns(deref))]
fn place_table<'db>(db: &'db dyn Db, scope: ScopeId<'db>) -> Arc<PlaceTable> {
    let index = semantic_index(db, scope.file(db));
    Arc::clone(&index.place_tables[scope.file_scope_id(db)])
}
```

## Return Mode Optimization

Tracked function results live in Salsa's storage. By default, accessing a result clones it. For large values, use return modes to borrow or dereference instead.

| Mode | Returns | Use Case |
|------|---------|----------|
| `(default)` | `T` | Copy types or cheap Arc clones |
| `returns(ref)` | `&T` | Large owned values (Vec, String) |
| `returns(deref)` | `&T::Target` | Smart pointers (Arc, Box) |
| `returns(as_ref)` | `Option<&T>` | Optional large values |
| `returns(as_deref)` | `Option<&T::Target>` | Optional smart pointers |

For systematic `returns(ref)` usage in collection-heavy projects, see [references/baml-patterns.md](references/memory-management/baml-patterns.md).

## Memory Profiling with `heap_size`

Add `heap_size` to any Salsa struct or tracked function to track heap allocations. This is essential for identifying which queries are consuming the most memory in production.

```rust
#[salsa::tracked(heap_size = heap_size)]
fn compute(db: &dyn Db, input: MyInput) -> String { ... }
```

Query memory usage at runtime (requires `salsa_unstable` feature):
```rust
let info = <dyn salsa::Database>::memory_usage(&db);
// Iterate over info.structs and info.queries to report usage
```

### Advanced Profiling Patterns

- **Shared-Object Tracking:** ty uses a thread-local tracker to avoid double-counting `Arc` allocations. See [references/ty-patterns.md](references/memory-management/ty-patterns.md).
- **Automatic Injection:** Cairo uses custom proc macro wrappers to auto-inject `heap_size` on every ingredient. See [references/cairo-patterns.md](references/memory-management/cairo-patterns.md).

## Disabling Interned GC: `revisions = usize::MAX`

Salsa garbage-collects interned values that haven't been read in recent revisions. For short-lived processes or when IDs are stored externally (e.g., serialized caches), disable GC entirely:

```rust
#[salsa::interned(revisions = usize::MAX)]
pub struct TypeId<'db> { ... }
```

With `revisions = usize::MAX`, interned IDs are **immortal** — they're never reclaimed. The `RevisionQueue` inside Salsa detects this constant and skips all GC logic at zero cost. See [references/cairo-patterns.md](references/memory-management/cairo-patterns.md) for real-world usage in serialized caches.

## Compile-Time Memory: `ManuallyDrop` Optimization

Large databases can suffer from slow compile times due to duplicated drop glue in vtables. Wrapping storage in `ManuallyDrop` eliminates this bloat. See [references/rust-analyzer-patterns.md](references/memory-management/rust-analyzer-patterns.md) for the implementation details.

## Common Mistakes

- **No LRU on any query:** Leads to unbounded growth in LSPs. Add LRU to expensive queries like parse and macro expansion.
- **LRU on cheap queries:** Adds unnecessary overhead. Only use for expensive-to-recompute functions.
- **Forgetting `returns(ref)` on large values:** Causes excessive cloning. Use for all heap-allocated return types.
- **Using `no_eq` without extraction:** Causes massive re-computation downstream. Pair with `Arc`-based extraction queries.

For detailed real-world patterns and internal mechanics, see:
- [references/salsa-internals.md](references/memory-management/salsa-internals.md) — Runtime LRU adjustment, zero-cost policy, and ArcSwap GC.
- [references/ty-patterns.md](references/memory-management/ty-patterns.md) — Universal heap tracking and shared-object counters.
- [references/rust-analyzer-patterns.md](references/memory-management/rust-analyzer-patterns.md) — Tiered LRU and `ManuallyDrop`.
- [references/cairo-patterns.md](references/memory-management/cairo-patterns.md) — Immortal IDs and automatic `heap_size`.
- [references/baml-patterns.md](references/memory-management/baml-patterns.md) — Minimalist `returns(ref)`-only strategy.
