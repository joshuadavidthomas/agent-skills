# ty — Universal Heap Tracking + Manual GC

Production memory management patterns from the Ruff/ty monorepo.

## Ruff/ty Monorepo: Universal Heap Tracking + Manual GC

### The `heap_size` Infrastructure (ruff_memory_usage — shared infrastructure)

The Ruff/ty monorepo applies `heap_size` to virtually every Salsa ingredient. The function uses a thread-local tracker to avoid double-counting shared `Arc<T>` allocations:

```rust
// ruff/crates/ruff_memory_usage/src/lib.rs
use get_size2::{GetSize, StandardTracker};

thread_local! {
    pub static TRACKER: RefCell<Option<StandardTracker>> = const { RefCell::new(None) };
}

/// Returns the memory usage of the provided object, using a global tracker to avoid
/// double-counting shared objects.
pub fn heap_size<T: GetSize>(value: &T) -> usize {
    with_tracker(|tracker| {
        if let Some(tracker) = tracker {
            value.get_heap_size_with_tracker(tracker).0
        } else {
            value.get_heap_size()
        }
    })
}
```

Used everywhere:
```rust
#[salsa::input(heap_size=ruff_memory_usage::heap_size)]
pub struct File { ... }

#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
pub struct UnionType<'db> { ... }

#[salsa::tracked(returns(ref), no_eq, heap_size=ruff_memory_usage::heap_size, lru=200)]
pub fn parsed_module(db: &dyn Db, file: File) -> ParsedModule { ... }
```

### Parsed Module: LRU + no_eq + Manual GC (ruff_db — shared infrastructure)

The most sophisticated memory management in the monorepo is on `parsed_module`:

```rust
// ruff/crates/ruff_db/src/parsed.rs

#[salsa::tracked(returns(ref), no_eq, heap_size=ruff_memory_usage::heap_size, lru=200)]
pub fn parsed_module(db: &dyn Db, file: File) -> ParsedModule {
    let _span = tracing::trace_span!("parsed_module", ?file).entered();
    let parsed = parsed_module_impl(db, file);
    ParsedModule::new(file, parsed)
}

/// The actual parse implementation, separated so it can be called for re-parsing.
pub fn parsed_module_impl(db: &dyn Db, file: File) -> Parsed<ModModule> {
    let source = source_text(db, file);
    let ty = file.source_type(db);
    let target_version = db.python_version();
    let options = ParseOptions::from(ty).with_target_version(target_version);
    parse_unchecked(&source, options)
        .try_into_module()
        .expect("PySourceType always parses into a module")
}
```

The `ParsedModule` struct implements manual garbage collection within a revision:

```rust
pub struct ParsedModule {
    file: File,
    inner: Arc<ArcSwapOption<indexed::IndexedModule>>,
}

impl ParsedModule {
    /// Load the AST. If it was cleared (GC'd), re-parse on demand.
    pub fn load(&self, db: &dyn Db) -> ParsedModuleRef {
        let parsed = match self.inner.load_full() {
            Some(parsed) => parsed,
            None => {
                // Re-parse — the AST was collected mid-revision
                let parsed = indexed::IndexedModule::new(parsed_module_impl(db, self.file));
                tracing::debug!(
                    "File `{}` was reparsed after being collected in the current Salsa revision",
                    self.file.path(db)
                );
                self.inner.store(Some(parsed.clone()));
                parsed
            }
        };
        ParsedModuleRef { module: self.clone(), indexed: parsed }
    }

    /// Clear the parsed module, dropping the AST once all references are dropped.
    pub fn clear(&self) {
        self.inner.store(None);
    }
}
```

**Why this design:**
- `lru=200` — Salsa evicts across revisions (at revision boundaries)
- `ArcSwapOption` — allows eviction *within* a revision (for memory pressure in long LSP sessions)
- `load()` re-parses on demand if the AST was cleared — correctness preserved
- `no_eq` — AST offsets change on every edit; comparing is O(AST size) and almost always unequal

### Semantic Index: Coarse + Fine-Grained Extraction (ty_python_semantic)

```rust
// ruff/crates/ty_python_semantic/src/semantic_index.rs

// Coarse: entire file analysis. no_eq because SemanticIndex is enormous.
#[salsa::tracked(returns(ref), no_eq, heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn semantic_index(db: &dyn Db, file: File) -> SemanticIndex<'_> {
    let _span = tracing::trace_span!("semantic_index", ?file).entered();
    let module = parsed_module(db, file).load(db);
    SemanticIndexBuilder::new(db, file, &module).build()
}

// Fine-grained: one scope's place table. returns(deref) unwraps Arc<PlaceTable> → &PlaceTable.
#[salsa::tracked(returns(deref), heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn place_table<'db>(db: &'db dyn Db, scope: ScopeId<'db>) -> Arc<PlaceTable> {
    let file = scope.file(db);
    let _span = tracing::trace_span!("place_table", scope=?scope.as_id(), ?file).entered();
    let index = semantic_index(db, file);
    Arc::clone(&index.place_tables[scope.file_scope_id(db)])
}

// Fine-grained: one scope's use-def map.
#[salsa::tracked(returns(deref), heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn use_def_map<'db>(db: &'db dyn Db, scope: ScopeId<'db>) -> Arc<UseDefMap<'db>> {
    let file = scope.file(db);
    let _span = tracing::trace_span!("use_def_map", scope=?scope.as_id(), ?file).entered();
    let index = semantic_index(db, file);
    Arc::clone(&index.use_def_maps[scope.file_scope_id(db)])
}

// Fine-grained: file-level imported modules.
#[salsa::tracked(returns(deref), heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn imported_modules<'db>(db: &'db dyn Db, file: File) -> Arc<FxHashSet<ModuleName>> {
    semantic_index(db, file).imported_modules.clone()
}
```

The `SemanticIndex` stores sub-structures in `Arc`:

```rust
pub(crate) struct SemanticIndex<'db> {
    place_tables: IndexVec<FileScopeId, Arc<PlaceTable>>,
    scopes: IndexVec<FileScopeId, Scope>,
    use_def_maps: IndexVec<FileScopeId, Arc<UseDefMap<'db>>>,
    imported_modules: Arc<FxHashSet<ModuleName>>,
    // ... more fields
}
```

**How incremental reuse works:**
1. Source text changes → `semantic_index` re-executes (always, due to `no_eq`)
2. Each extraction query (`place_table`, `use_def_map`) re-executes
3. Extraction queries return `Arc::clone(...)` — if the builder reused the same allocation, the `Arc` pointer is identical
4. Salsa compares the `Arc<PlaceTable>` values — if equal (cheap check), dependents of that scope don't re-run
5. Result: only scopes with actual changes trigger downstream re-execution

### Source Text: Equality ON, No LRU (ruff_db — shared infrastructure)

```rust
// ruff/crates/ruff_db/src/source.rs

#[salsa::tracked(heap_size=ruff_memory_usage::heap_size)]
pub fn source_text(db: &dyn Db, file: File) -> SourceText {
    let path = file.path(db);
    let _span = tracing::trace_span!("source_text", file = %path).entered();

    if let Some(source) = file.source_text_override(db) {
        return source.clone();
    }

    let kind = if is_notebook(db.system(), path) {
        file.read_to_notebook(db).unwrap_or_else(|error| {
            tracing::debug!("Failed to read notebook '{path}': {error}");
            Notebook::empty()
        }).into()
    } else {
        file.read_to_string(db).unwrap_or_else(|error| {
            tracing::debug!("Failed to read file '{path}': {error}");
            String::new()
        }).into()
    };

    SourceText { inner: Arc::new(SourceTextInner { kind, read_error: None }) }
}
```

**Why no `no_eq` here:** Source text changes are the *root cause* of all downstream invalidation. When source text is unchanged (e.g., re-reading the same file on disk), equality comparison is cheap (string compare) and prevents all downstream queries from re-executing. This is the opposite trade-off from ASTs.

**Why no `lru`:** Source text is cheap to store (just a string). The bottleneck is parsing, not reading.

