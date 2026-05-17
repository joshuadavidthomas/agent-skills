# ty — Layer-by-Layer Pipeline

Production query pipeline patterns from the Ruff/ty monorepo.

## Ruff/ty Monorepo: Layer-by-Layer Pipeline

### Layer 1: Source Text (ruff_db — shared infrastructure)

The entry point — reads file contents with error resilience and editor override support.

```rust
// ruff/crates/ruff_db/src/source.rs
#[salsa::tracked(heap_size=ruff_memory_usage::heap_size)]
pub fn source_text(db: &dyn Db, file: File) -> SourceText {
    let path = file.path(db);
    let _span = tracing::trace_span!("source_text", file = %path).entered();

    // Editor-open files use the override (unsaved edits)
    if let Some(source) = file.source_text_override(db) {
        return source.clone();
    }

    // Handle both Python files and notebooks
    let kind = if is_notebook(db.system(), path) {
        file.read_to_notebook(db)
            .unwrap_or_else(|error| {
                tracing::debug!("Failed to read notebook '{path}': {error}");
                Notebook::empty()
            })
            .into()
    } else {
        file.read_to_string(db)
            .unwrap_or_else(|error| {
                tracing::debug!("Failed to read file '{path}': {error}");
                String::new()
            })
            .into()
    };

    SourceText {
        inner: Arc::new(SourceTextInner { kind, read_error }),
    }
}
```

**Key choices:**
- No `returns(ref)` — `SourceText` wraps `Arc` internally, so cloning is cheap
- No `lru` — source text is small relative to ASTs
- `heap_size` — memory profiling support
- Error resilience: returns empty content on failure rather than panicking
- `source_text_override()` — LSP injects unsaved editor content here

### Layer 2: Parsed Module (ruff_db — shared infrastructure)

```rust
// ruff/crates/ruff_db/src/parsed.rs

/// The LRU capacity of 200 was picked without any empirical evidence that it's optimal,
/// instead it's a wild guess that it should be unlikely that incremental changes involve
/// more than 200 modules. Parsed ASTs within the same revision are never evicted by Salsa.
#[salsa::tracked(returns(ref), no_eq, heap_size=ruff_memory_usage::heap_size, lru=200)]
pub fn parsed_module(db: &dyn Db, file: File) -> ParsedModule {
    let _span = tracing::trace_span!("parsed_module", ?file).entered();
    let parsed = parsed_module_impl(db, file);
    ParsedModule::new(file, parsed)
}

// Non-tracked helper — does the actual parsing
pub fn parsed_module_impl(db: &dyn Db, file: File) -> Parsed<ModModule> {
    let source = source_text(db, file);  // Dependency on layer 1
    let ty = file.source_type(db);
    let target_version = db.python_version();
    let options = ParseOptions::from(ty).with_target_version(target_version);
    parse_unchecked(&source, options)
        .try_into_module()
        .expect("PySourceType always parses into a module")
}
```

**Key choices:**
- `returns(ref)` — ASTs are large, avoid cloning
- `no_eq` — AST comparison is expensive, and the Python AST doesn't even implement `Eq`. Every offset changes on any edit.
- `lru=200` — prevents unbounded memory growth across revisions
- Separate `parsed_module_impl()` — non-tracked helper keeps the tracked function thin

### Layer 3: Semantic Index — Coarse (ty_python_semantic)

```rust
// ruff/crates/ty_python_semantic/src/semantic_index.rs

#[salsa::tracked(returns(ref), no_eq, heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn semantic_index(db: &dyn Db, file: File) -> SemanticIndex<'_> {
    let _span = tracing::trace_span!("semantic_index", ?file).entered();
    let module = parsed_module(db, file).load(db);  // Dependency on layer 2
    SemanticIndexBuilder::new(db, file, &module).build()
}
```

**Key choices:**
- `no_eq` — complex nested data, expensive to compare
- Computes everything for the file in one pass (coarse)
- Returns the full index — fine-grained accessors extract specific data

### Layer 3.5: Fine-Grained Accessors — The Split (ty_python_semantic)

```rust
// ruff/crates/ty_python_semantic/src/semantic_index.rs

/// Using [`place_table`] over [`semantic_index`] has the advantage that
/// Salsa can avoid invalidating dependent queries if this scope's place table
/// is unchanged.
#[salsa::tracked(returns(deref), heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn place_table<'db>(db: &'db dyn Db, scope: ScopeId<'db>) -> Arc<PlaceTable> {
    let file = scope.file(db);
    let index = semantic_index(db, file);  // Depends on coarse index
    Arc::clone(&index.place_tables[scope.file_scope_id(db)])
}

/// Using [`use_def_map`] over [`semantic_index`] has the advantage that
/// Salsa can avoid invalidating dependent queries if this scope's use-def map
/// is unchanged.
#[salsa::tracked(returns(deref), heap_size=ruff_memory_usage::heap_size)]
pub(crate) fn use_def_map<'db>(db: &'db dyn Db, scope: ScopeId<'db>) -> Arc<UseDefMap<'db>> {
    let file = scope.file(db);
    let index = semantic_index(db, file);
    Arc::clone(&index.use_def_maps[scope.file_scope_id(db)])
}
```

**Key choices:**
- `returns(deref)` — stores `Arc<T>`, caller gets `&T`
- No `no_eq` — `Arc` equality is cheap (pointer comparison), and this is the whole point: if the `Arc` for a scope's place table didn't change, downstream queries for that scope are skipped
- This is the split pattern: coarse `semantic_index` feeds fine-grained per-scope accessors

### Layer 4: Type Inference — With Cycle Handling (ty_python_semantic)

```rust
// ruff/crates/ty_python_semantic/src/types/infer.rs

/// Infer types for a Definition. Use when resolving a place or public type.
#[salsa::tracked(
    returns(ref),
    cycle_initial=definition_cycle_initial,
    cycle_fn=|db, cycle, previous: &DefinitionInference<'db>, inference: DefinitionInference<'db>, _| {
        inference.cycle_normalized(db, previous, cycle)
    },
    heap_size=ruff_memory_usage::heap_size
)]
pub(crate) fn infer_definition_types<'db>(
    db: &'db dyn Db,
    definition: Definition<'db>,
) -> DefinitionInference<'db> {
    let file = definition.file(db);
    let module = parsed_module(db, file).load(db);
    let index = semantic_index(db, file);
    TypeInferenceBuilder::new(db, InferenceRegion::Definition(definition), index, &module)
        .finish_definition()
}

fn definition_cycle_initial<'db>(
    db: &'db dyn Db,
    id: salsa::Id,
    definition: Definition<'db>,
) -> DefinitionInference<'db> {
    DefinitionInference::cycle_initial(definition.scope(db), Type::divergent(id))
}
```

**Key choices:**
- `cycle_initial` returns `Type::divergent(id)` — bottom value for iteration
- `cycle_fn` normalizes by comparing with previous iteration
- See [cycle-handling.md](../../cycle-handling.md) for cycle strategies

### The Wrapper Pattern: Interning Non-Salsa Arguments (ty_python_semantic)

When a tracked function needs extra context beyond Salsa ingredients:

```rust
// ruff/crates/ty_python_semantic/src/types/infer.rs

// TypeContext is a plain Rust type — can't be a tracked fn argument directly
pub(crate) fn infer_scope_types<'db>(
    db: &'db dyn Db,
    scope: ScopeId<'db>,
    tcx: TypeContext<'db>,  // Not a Salsa ingredient!
) -> &'db ScopeInference<'db> {
    // Wrap into an interned struct to make it a Salsa ingredient
    infer_scope_types_impl(db, InferScope::new(db, scope, tcx))
}

/// A ScopeId with an optional TypeContext, interned for use as a tracked fn argument.
#[derive(Debug, Clone, Copy, Eq, Hash, PartialEq, salsa::Supertype, salsa::Update)]
pub(super) enum InferScope<'db> {
    Bare(ScopeId<'db>),
    WithContext(ScopeWithContext<'db>),
}

#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
pub(super) struct ScopeWithContext<'db> {
    scope: ScopeId<'db>,
    tcx: TypeContext<'db>,
}

#[salsa::tracked(
    returns(ref),
    cycle_initial=|_, id, _| ScopeInference::cycle_initial(Type::divergent(id)),
    cycle_fn=|db, cycle, previous: &ScopeInference<'db>, inference: ScopeInference<'db>, _| {
        inference.cycle_normalized(db, previous, cycle)
    },
    heap_size=ruff_memory_usage::heap_size
)]
pub(crate) fn infer_scope_types_impl<'db>(
    db: &'db dyn Db,
    input: InferScope<'db>,
) -> ScopeInference<'db> {
    let (scope, tcx) = input.into_inner(db);
    // ... actual inference using both scope and type context ...
}
```

### Module Resolution: The Classic Wrapper (ty_module_resolver)

```rust
// ruff/crates/ty_module_resolver/src/resolve.rs

/// A thin wrapper around ModuleName to make it a Salsa ingredient.
#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
struct ModuleNameIngredient<'db> {
    #[returns(ref)]
    pub(super) name: ModuleName,
    pub(super) mode: ModuleResolveMode,
}

/// Public API: accepts plain ModuleName, interns it, delegates to tracked fn.
pub fn resolve_module<'db>(
    db: &'db dyn Db,
    importing_file: File,
    module_name: &ModuleName,
) -> Option<Module<'db>> {
    let interned_name = ModuleNameIngredient::new(db, module_name, ModuleResolveMode::StubsAllowed);
    resolve_module_query(db, interned_name)
        .or_else(|| desperately_resolve_module(db, importing_file, interned_name))
}

/// Private tracked query — takes only Salsa ingredients.
#[salsa::tracked(heap_size=ruff_memory_usage::heap_size)]
fn resolve_module_query<'db>(
    db: &'db dyn Db,
    module_name: ModuleNameIngredient<'db>,
) -> Option<Module<'db>> {
    let name = module_name.name(db);
    let mode = module_name.mode(db);
    let _span = tracing::trace_span!("resolve_module", %name).entered();
    // ... resolution logic ...
}
```

