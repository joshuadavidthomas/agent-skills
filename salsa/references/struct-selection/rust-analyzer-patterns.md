# rust-analyzer — The "Intern Every Definition" Pattern

Production struct selection patterns from rust-analyzer (Rust IDE).

## Location Structs: What Gets Interned

Every definition location is a lightweight struct with a container + AST pointer:

```rust
pub struct ItemLoc<N: AstIdNode> {
    pub container: ModuleId,
    pub id: AstId<N>,
}

pub struct AssocItemLoc<N: AstIdNode> {
    pub container: ItemContainerId,
    pub id: AstId<N>,
}

// Concrete type aliases
type FunctionLoc = AssocItemLoc<ast::Fn>;
type StructLoc = ItemLoc<ast::Struct>;
// etc.
```

## The Interning Macro

Each location type gets interned into a `Copy` ID via a macro:

```rust
macro_rules! impl_intern_key {
    ($id:ident, $loc:ident) => {
        #[salsa_macros::interned(no_lifetime, revisions = usize::MAX)]
        #[derive(PartialOrd, Ord)]
        pub struct $id {
            pub loc: $loc,
        }

        impl ::std::fmt::Debug for $id {
            fn fmt(&self, f: &mut ::std::fmt::Formatter<'_>) -> ::std::fmt::Result {
                f.debug_tuple(stringify!($id))
                    .field(&format_args!("{:04x}", self.0.index()))
                    .finish()
            }
        }
    };
}
```

Key details:
- `no_lifetime` — these IDs don't carry `'db`, so they're stable across revisions
- `revisions = usize::MAX` — never garbage collect (these are long-lived definitions)

## 17 Interned Functions: One Per Definition Kind

```rust
#[query_group::query_group]
pub trait InternDatabase: RootQueryDb {
    #[salsa::interned]
    fn intern_use(&self, loc: UseLoc) -> UseId;
    #[salsa::interned]
    fn intern_extern_crate(&self, loc: ExternCrateLoc) -> ExternCrateId;
    #[salsa::interned]
    fn intern_function(&self, loc: FunctionLoc) -> FunctionId;
    #[salsa::interned]
    fn intern_struct(&self, loc: StructLoc) -> StructId;
    #[salsa::interned]
    fn intern_union(&self, loc: UnionLoc) -> UnionId;
    #[salsa::interned]
    fn intern_enum(&self, loc: EnumLoc) -> EnumId;
    #[salsa::interned]
    fn intern_enum_variant(&self, loc: EnumVariantLoc) -> EnumVariantId;
    #[salsa::interned]
    fn intern_const(&self, loc: ConstLoc) -> ConstId;
    #[salsa::interned]
    fn intern_static(&self, loc: StaticLoc) -> StaticId;
    #[salsa::interned]
    fn intern_trait(&self, loc: TraitLoc) -> TraitId;
    #[salsa::interned]
    fn intern_type_alias(&self, loc: TypeAliasLoc) -> TypeAliasId;
    #[salsa::interned]
    fn intern_impl(&self, loc: ImplLoc) -> ImplId;
    #[salsa::interned]
    fn intern_extern_block(&self, loc: ExternBlockLoc) -> ExternBlockId;
    #[salsa::interned]
    fn intern_macro2(&self, loc: Macro2Loc) -> Macro2Id;
    #[salsa::interned]
    fn intern_proc_macro(&self, loc: ProcMacroLoc) -> ProcMacroId;
    #[salsa::interned]
    fn intern_macro_rules(&self, loc: MacroRulesLoc) -> MacroRulesId;
    #[salsa::interned]
    fn intern_block(&self, loc: BlockLoc) -> BlockId;
}
```

## Input Structs: External Data

```rust
#[salsa_macros::input(debug)]
pub struct FileText {
    #[returns(ref)]
    pub text: Arc<str>,
    pub file_id: vfs::FileId,
}

#[salsa_macros::input(debug)]
pub struct FileSourceRootInput {
    pub source_root_id: SourceRootId,
}

#[salsa_macros::input(debug)]
pub struct SourceRootInput {
    pub source_root: Arc<SourceRoot>,
}
```

## Plain Structs Returned from Queries (Not Tracked, Not Interned)

Collection types like `InherentImpls` and `TraitImpls` are plain Rust structs returned wrapped in `Arc` from tracked functions:

```rust
/// Inherent impls defined in some crate.
#[derive(Debug, Eq, PartialEq)]
pub struct InherentImpls {
    map: FxHashMap<TyFingerprint, Vec<ImplId>>,
    invalid_impls: Vec<ImplId>,
}

impl InherentImpls {
    pub(crate) fn inherent_impls_in_crate_query(db: &dyn HirDatabase, krate: Crate) -> Arc<Self> {
        let mut impls = Self { map: FxHashMap::default(), invalid_impls: Vec::default() };
        let crate_def_map = crate_def_map(db, krate);
        impls.collect_def_map(db, crate_def_map);
        impls.shrink_to_fit();
        Arc::new(impls)
    }
}

/// Trait impls defined or available in some crate.
#[derive(Debug, Eq, PartialEq)]
pub struct TraitImpls {
    map: TraitFpMap,
}

impl TraitImpls {
    pub(crate) fn trait_impls_in_crate_query(db: &dyn HirDatabase, krate: Crate) -> Arc<Self> {
        let mut impls = FxHashMap::default();
        Self::collect_def_map(db, &mut impls, crate_def_map(db, krate));
        Arc::new(Self::finish(impls))
    }
}
```

These are not Salsa structs at all — just regular data returned from tracked functions. The tracked function handles the caching and invalidation; the return type is just data.
