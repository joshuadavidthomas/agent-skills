# rust-analyzer — Layered Query Graph

Production query pipeline patterns from rust-analyzer (Rust IDE).

## rust-analyzer: Layered Query Graph

### Parse (with LRU)

```rust
// rust-analyzer/crates/base-db/src/lib.rs

#[salsa::tracked(lru = 128, returns(ref))]
pub fn parse(db: &dyn RootQueryDb, file_id: EditionedFileId) -> Parse<SourceFile> {
    // ...
}
```

### Macro Expansion (Tiered LRU)

```rust
// rust-analyzer/crates/hir-expand/src/db.rs

#[salsa::tracked(lru = 1024, returns(ref))]
fn parse_macro_expansion(
    db: &dyn ExpandDatabase,
    macro_file: MacroFileId,
) -> ExpandResult<(Parse<SyntaxNode>, Arc<ExpansionSpanMap>)> { ... }

#[salsa::tracked(lru = 512, returns(ref))]
fn parse_macro_expansion_with_eager_placeholders(
    db: &dyn ExpandDatabase,
    macro_file: MacroFileId,
) -> ExpandResult<(Parse<SyntaxNode>, Arc<ExpansionSpanMap>)> { ... }
```

Different LRU sizes based on usage frequency — more frequently accessed expansions get a larger cache.

### Signatures: The Dual-Query Pattern

rust-analyzer frequently uses a pattern where two tracked functions share work:

```rust
// rust-analyzer/crates/hir-def/src/signatures.rs

// Public API: returns only the signature (cheap to compare)
#[salsa::tracked(returns(clone))]
pub fn query(db: &dyn DefDatabase, id: FunctionId) -> Arc<FunctionSignature> {
    Self::query_with_source_map(db, id).0
}

// Internal API: returns signature + source map (needed for IDE go-to-definition)
#[salsa::tracked(returns(clone))]
pub fn query_with_source_map(
    db: &dyn DefDatabase,
    id: FunctionId,
) -> (Arc<FunctionSignature>, Arc<ExpressionStoreSourceMap>) {
    // ... actual lowering work ...
}
```

The dual-query pattern separates data for type checking (signature only) from data for IDE features (signature + source map). When only the source map changes (e.g., whitespace edit), queries depending only on the signature are unaffected.

### Return Mode Variants in Practice

```rust
// returns(ref) — large owned values
#[salsa::tracked(returns(ref))]
pub fn of(db: &dyn DefDatabase, e: EnumId) -> (EnumVariants, Option<ThinVec<InactiveCode>>) { ... }

// returns(deref) — Arc<T> → &T
#[salsa::tracked(returns(deref))]
pub fn firewall(db: &dyn DefDatabase, id: VariantId) -> Arc<VariantFields> { ... }

// returns(clone) — explicit clone of Arc
#[salsa::tracked(returns(clone))]
pub fn query(db: &dyn DefDatabase, id: FunctionId) -> Arc<FunctionSignature> { ... }

// returns(as_deref) — Option<Box<T>> → Option<&T>
#[salsa::tracked(returns(as_deref))]
pub fn upvars_mentioned(db: &dyn HirDatabase, owner: DefWithBodyId) -> Option<Box<FxHashMap<ExprId, Upvars>>> { ... }
```

### Tracked Functions on Impl Blocks

```rust
// rust-analyzer/crates/hir-ty/src/method_resolution.rs

#[derive(Debug, Eq, PartialEq)]
pub struct InherentImpls {
    map: FxHashMap<TyFingerprint, Vec<ImplId>>,
    invalid_impls: Vec<ImplId>,
}

#[salsa::tracked]
impl InherentImpls {
    #[salsa::tracked(returns(ref))]
    pub(crate) fn for_crate(db: &dyn HirDatabase, krate: Crate) -> InherentImpls {
        let mut impls = Self { map: FxHashMap::default(), invalid_impls: Vec::default() };
        let crate_def_map = crate_def_map(db, krate);
        impls.collect_def_map(db, crate_def_map);
        impls.shrink_to_fit();
        impls
    }
}

#[derive(Debug, Eq, PartialEq)]
pub struct TraitImpls {
    map: TraitFpMap,
}

#[salsa::tracked]
impl TraitImpls {
    #[salsa::tracked(returns(ref))]
    pub(crate) fn for_crate(db: &dyn HirDatabase, krate: Crate) -> TraitImpls {
        let mut impls = FxHashMap::default();
        Self::collect_def_map(db, &mut impls, crate_def_map(db, krate));
        Self::finish(impls)
    }

    #[salsa::tracked(returns(ref))]
    pub(crate) fn for_crate_and_deps(db: &dyn HirDatabase, krate: Crate) -> TraitImpls {
        let _p = tracing::info_span!("trait_impls_for_crate_and_deps").entered();
        let mut impls = FxHashMap::default();
        // ... aggregate from crate + all dependencies ...
        Self::finish(impls)
    }
}
```

Note that `InherentImpls` and `TraitImpls` are **plain Rust structs** — not `#[salsa::tracked]` structs. The tracked attribute is on the **impl block**, turning the methods into tracked functions. The struct itself is just data returned from those functions.

### Cycle Recovery via Fallback

```rust
// rust-analyzer/crates/hir-ty/src/infer.rs

#[salsa::tracked(cycle_result)]
fn infer_query(db: &dyn HirDatabase, def: DefWithBodyId) -> Arc<InferenceResult> { ... }

// rust-analyzer/crates/hir-ty/src/db.rs
#[salsa::tracked(cycle_result)]
fn mir_body_query(db: &dyn HirDatabase, def: DefWithBodyId) -> Result<Arc<MirBody>, MirLowerError> { ... }
```

rust-analyzer uses `cycle_result` (simple fallback) rather than `cycle_fn` + `cycle_initial` (fixed-point iteration). This returns a default/error value when a cycle is detected rather than iterating to convergence.

## Pattern Summary

| Pattern | When to Use | Example |
|---------|-------------|---------|
| `returns(ref)` on large types | Always for heap-allocated returns | Parsed ASTs, semantic indices |
| `no_eq` on ASTs | Types where equality is expensive/meaningless | Parsed modules, semantic indices |
| LRU on parse/expansion | Long-running applications (LSP) | `lru=128` for parse, `lru=200` for parsed_module |
| Split pattern | Need per-scope reuse from per-file computation | `semantic_index` → `place_table` / `use_def_map` |
| Wrapper function | Non-Salsa arguments to tracked functions | `ModuleNameIngredient`, `InferScope` |
| Dual-query | Separate data for different consumers | `signature` vs `signature_with_source_map` |
| Tracked impl on struct | Group related queries logically | `InherentImpls::for_crate`, `TraitImpls::for_crate` |
| `returns(deref)` for Arc | Store Arc but expose &T | Fine-grained accessors (`place_table`) |
