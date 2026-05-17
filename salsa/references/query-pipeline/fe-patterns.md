# Fe — Tracked Methods on Input Structs and Cycle Handling

Fe (github.com/argotorg/fe) demonstrates tracked methods on input structs and a fixed-point-only cycle strategy.

## Tracked Methods on Input Structs

Fe's `File` input has tracked methods that derive computed properties, each independently cached:

```rust
#[salsa::input(constructor = __new_impl)]
#[derive(Debug)]
pub struct File {
    #[return_ref]
    pub text: String,
}

#[salsa::tracked]
impl File {
    // Each tracked method is independently memoized
    #[salsa::tracked]
    pub fn containing_ingot(self, db: &dyn InputDb) -> Option<Ingot<'_>> {
        self.url(db)
            .and_then(|url| db.workspace().containing_ingot(db, url))
    }

    #[salsa::tracked(return_ref)]
    pub fn path(self, db: &dyn InputDb) -> Option<Utf8PathBuf> {
        self.containing_ingot(db)
            .and_then(|ingot| db.workspace().get_relative_path(db, ingot.base(db), self))
    }

    #[salsa::tracked]
    pub fn kind(self, db: &dyn InputDb) -> Option<IngotFileKind> {
        self.path(db).as_ref().and_then(|path| {
            if path.as_str().ends_with(".fe") {
                Some(IngotFileKind::Source)
            } else if path.as_str().ends_with("fe.toml") {
                Some(IngotFileKind::Config)
            } else {
                None
            }
        })
    }

    // Non-tracked method — no caching, just a lookup
    pub fn url(self, db: &dyn InputDb) -> Option<Url> {
        db.workspace().get_path(db, self)
    }
}
```

**Why tracked methods on inputs?** Each method is independently memoized. Changing workspace structure invalidates `containing_ingot` but `kind` reuses its cached result if the ingot assignment didn't change. This creates a natural granularity cascade: workspace → ingot → path → kind.

## Fixed-Point Cycle Handling (5 sites, all cycle_fn + cycle_initial)

Fe uses exclusively the fixed-point iteration strategy — zero `cycle_result` fallbacks. This is the simplest project to study the `cycle_fn` + `cycle_initial` approach across multiple domains.

### 1. Import Resolution — Converges Over Multiple Passes

```rust
#[salsa::tracked(return_ref, cycle_fn=resolve_imports_cycle_recover, cycle_initial=resolve_imports_cycle_initial)]
pub fn resolve_imports<'db>(
    db: &'db dyn HirAnalysisDb,
    ingot: Ingot<'db>,
) -> (Vec<ImportDiag<'db>>, ResolvedImports<'db>) {
    let resolver = import_resolver::ImportResolver::new(db, ingot);
    let (imports, diags) = resolver.resolve_imports();
    (diags, imports)
}

fn resolve_imports_cycle_initial<'db>(
    db: &'db dyn HirAnalysisDb,
    ingot: Ingot<'db>,
) -> (Vec<ImportDiag<'db>>, ResolvedImports<'db>) {
    (Vec::new(), ResolvedImports::default())
}

fn resolve_imports_cycle_recover<'db>(
    db: &'db dyn HirAnalysisDb,
    _value: &(Vec<ImportDiag<'db>>, ResolvedImports<'db>),
    count: u32,
    ingot: Ingot<'db>,
) -> salsa::CycleRecoveryAction<(Vec<ImportDiag<'db>>, ResolvedImports<'db>)> {
    salsa::CycleRecoveryAction::Iterate
}
```

### 2. Type Lowering — Invalid Type on Cycle

```rust
#[salsa::tracked(cycle_fn=lower_hir_ty_cycle_recover, cycle_initial=lower_hir_ty_cycle_initial)]
pub fn lower_hir_ty<'db>(
    db: &'db dyn HirAnalysisDb,
    ty: HirTyId<'db>,
    scope: ScopeId<'db>,
    assumptions: PredicateListId<'db>,
) -> TyId<'db> {
    match ty.data(db) {
        HirTyKind::Ptr(pointee) => {
            let pointee = lower_opt_hir_ty(db, *pointee, scope, assumptions);
            let ptr = TyId::ptr(db);
            TyId::app(db, ptr, pointee)
        }
        HirTyKind::Path(path) => lower_path(db, scope, *path, assumptions),
        HirTyKind::Tuple(tuple_id) => {
            let elems = tuple_id.data(db);
            let tuple = TyId::tuple(db, elems.len());
            elems.iter().fold(tuple, |acc, &elem| {
                let elem_ty = lower_opt_hir_ty(db, elem, scope, assumptions);
                TyId::app(db, acc, elem_ty)
            })
        }
        HirTyKind::Array(hir_elem_ty, len) => {
            let elem_ty = lower_opt_hir_ty(db, *hir_elem_ty, scope, assumptions);
            let len_ty = ConstTyId::from_opt_body(db, *len);
            let len_ty = TyId::const_ty(db, len_ty);
            let array = TyId::array(db, elem_ty);
            TyId::app(db, array, len_ty)
        }
        HirTyKind::Never => TyId::never(db),
    }
}

fn lower_hir_ty_cycle_initial<'db>(
    db: &'db dyn HirAnalysisDb,
    _ty: HirTyId<'db>,
    _scope: ScopeId<'db>,
    _assumptions: PredicateListId<'db>,
) -> TyId<'db> {
    TyId::invalid(db, InvalidCause::Other)
}
```

### 3. Type Alias Lowering — Tracks Cycle Chain

```rust
#[salsa::tracked(return_ref, cycle_fn=lower_type_alias_cycle_recover, cycle_initial=lower_type_alias_cycle_initial)]
pub(crate) fn lower_type_alias<'db>(
    db: &'db dyn HirAnalysisDb,
    alias: HirTypeAlias<'db>,
) -> TyAlias<'db> {
    crate::core::semantic::lower_type_alias_body(db, alias)
}

fn lower_type_alias_cycle_initial<'db>(
    db: &'db dyn HirAnalysisDb,
    alias: HirTypeAlias<'db>,
) -> TyAlias<'db> {
    TyAlias {
        alias,
        alias_to: Binder::bind(TyId::invalid(
            db,
            InvalidCause::AliasCycle(smallvec![alias]),
        )),
        param_set: GenericParamTypeSet::empty(db, alias.scope()),
    }
}
```

The `AliasCycle` variant accumulates the chain of aliases involved, enabling precise diagnostic messages.

### 4. Trait Environment — Empty Environment on Cycle

```rust
#[salsa::tracked(return_ref, cycle_fn=ingot_trait_env_cycle_recover, cycle_initial=ingot_trait_env_cycle_initial)]
pub(crate) fn ingot_trait_env<'db>(db: &'db dyn HirAnalysisDb, ingot: Ingot<'db>) -> TraitEnv<'db> {
    TraitEnv::collect(db, ingot)
}
```

### 5. Effect Classification — Falls Back to "Other"

```rust
#[salsa::tracked(cycle_fn=effect_key_kind_cycle_recover, cycle_initial=effect_key_kind_cycle_initial)]
pub(crate) fn effect_key_kind<'db>(
    db: &'db dyn HirAnalysisDb,
    key_path: PathId<'db>,
    scope: ScopeId<'db>,
) -> EffectKeyKind {
    // Classify whether an effect key refers to a Type, Trait, or Other.
    // Uses multiple resolution strategies to avoid recursive cycles.
    // ...
}

fn effect_key_kind_cycle_initial<'db>(
    _db: &'db dyn HirAnalysisDb,
    _key_path: PathId<'db>,
    _scope: ScopeId<'db>,
) -> EffectKeyKind {
    EffectKeyKind::Other
}
```
