# rust-analyzer — 6-Layer Database Hierarchy

Production database architecture from rust-analyzer (Rust IDE).

## rust-analyzer: 6-Layer Database Hierarchy

### Layer 1: SourceDatabase

The file I/O foundation. Provides file text, source roots, and crate graph:

```rust
#[salsa_macros::db]
pub trait SourceDatabase: salsa::Database {
    fn file_text(&self, file_id: vfs::FileId) -> FileText;
    fn set_file_text(&mut self, file_id: vfs::FileId, text: &str);
    fn set_file_text_with_durability(&mut self, file_id: vfs::FileId, text: &str, durability: Durability);
    fn source_root(&self, id: SourceRootId) -> SourceRootInput;
    fn set_source_root_with_durability(&mut self, id: SourceRootId, root: Arc<SourceRoot>, durability: Durability);
    fn resolve_path(&self, path: AnchoredPath<'_>) -> Option<FileId>;
}
```

Input structs:

```rust
#[salsa_macros::input(debug)]
pub struct FileText {
    #[returns(ref)]
    pub text: Arc<str>,
    pub file_id: vfs::FileId,
}

// Singletons for workspace structure
#[salsa::input(singleton, debug)]
pub struct LibraryRoots {
    #[returns(ref)]
    pub roots: FxHashSet<SourceRootId>,
}

#[salsa::input(singleton, debug)]
pub struct LocalRoots {
    #[returns(ref)]
    pub roots: FxHashSet<SourceRootId>,
}
```

### Layer 2: RootQueryDb — Parsing

```rust
#[query_group::query_group]
pub trait RootQueryDb: SourceDatabase + salsa::Database {
    #[salsa::lru(128)]
    fn parse(&self, file_id: EditionedFileId) -> Parse<ast::SourceFile>;

    #[salsa::transparent]
    fn parse_errors(&self, file_id: EditionedFileId) -> Option<&[SyntaxError]>;

    // WARNING: "do not use this query in hir-* crates! It kills incrementality
    // across crate metadata modifications"
    #[salsa::input]
    fn all_crates(&self) -> Arc<Box<[Crate]>>;
}
```

### Layer 3: ExpandDatabase — Macro Expansion

```rust
#[query_group::query_group]
pub trait ExpandDatabase: RootQueryDb {
    #[salsa::input]
    fn proc_macros(&self) -> Arc<ProcMacros>;

    #[salsa::lru(1024)]
    fn ast_id_map(&self, file_id: HirFileId) -> Arc<AstIdMap>;

    #[salsa::lru(512)]
    fn parse_macro_expansion(&self, macro_file: MacroCallId)
        -> ExpandResult<(Parse<SyntaxNode>, Arc<ExpansionSpanMap>)>;

    // CRITICAL: No LRU on proc macros — they're non-deterministic!
    fn expand_proc_macro(&self, call: MacroCallId) -> ExpandResult<Arc<tt::TopSubtree>>;
}
```

### Layer 4: InternDatabase — Definition Interning

17+ interning queries, one per definition kind:

```rust
#[query_group::query_group]
pub trait InternDatabase: RootQueryDb {
    #[salsa::interned]
    fn intern_function(&self, loc: FunctionLoc) -> FunctionId;
    #[salsa::interned]
    fn intern_struct(&self, loc: StructLoc) -> StructId;
    #[salsa::interned]
    fn intern_enum(&self, loc: EnumLoc) -> EnumId;
    #[salsa::interned]
    fn intern_trait(&self, loc: TraitLoc) -> TraitId;
    // ... 13 more
}
```

### Layer 5: DefDatabase — Name Resolution

```rust
#[query_group::query_group]
pub trait DefDatabase: InternDatabase + ExpandDatabase + SourceDatabase {
    #[salsa::transparent]
    fn file_item_tree(&self, file_id: HirFileId) -> &ItemTree;

    // Signature/source_map split pattern
    #[salsa::tracked]
    fn trait_signature(&self, trait_: TraitId) -> Arc<TraitSignature>;
    fn trait_signature_with_source_map(&self, trait_: TraitId)
        -> (Arc<TraitSignature>, Arc<ExpressionStoreSourceMap>);

    #[salsa::lru(512)]
    fn body_with_source_map(&self, def: DefWithBodyId) -> (Arc<Body>, Arc<BodySourceMap>);
}
```

### Layer 6: HirDatabase — Type Inference

```rust
#[query_group::query_group]
pub trait HirDatabase: DefDatabase + std::fmt::Debug {
    #[salsa::cycle(cycle_result = crate::mir::mir_body_cycle_result)]
    fn mir_body(&self, def: DefWithBodyId) -> Result<Arc<MirBody>, MirLowerError>;

    #[salsa::lru(2024)]
    fn borrowck(&self, def: DefWithBodyId) -> Result<Arc<[BorrowckResult]>, MirLowerError>;

    #[salsa::transparent]
    fn ty<'db>(&'db self, def: TyDefId) -> EarlyBinder<'db, Ty<'db>>;

    #[salsa::cycle(cycle_result = layout_of_ty_cycle_result)]
    fn layout_of_ty(&self, ty: StoredTy, env: StoredParamEnvAndCrate)
        -> Result<Arc<Layout>, LayoutError>;
}
```

### Production Database: `RootDatabase`

```rust
#[salsa_macros::db]
pub struct RootDatabase {
    // ManuallyDrop avoids vtable bloat — every &RootDatabase -> &dyn OtherDatabase
    // cast instantiates drop glue, duplicating Arc::drop tens of thousands of times
    storage: ManuallyDrop<salsa::Storage<Self>>,
    files: Arc<Files>,
    crates_map: Arc<CratesMap>,
    nonce: Nonce,
}

impl std::panic::RefUnwindSafe for RootDatabase {}

impl Drop for RootDatabase {
    fn drop(&mut self) {
        unsafe { ManuallyDrop::drop(&mut self.storage) };
    }
}

impl Clone for RootDatabase {
    fn clone(&self) -> Self {
        Self {
            storage: self.storage.clone(),
            files: self.files.clone(),
            crates_map: self.crates_map.clone(),
            nonce: Nonce::new(),  // Fresh nonce per clone!
        }
    }
}
```

### Initialization with Durability

```rust
impl RootDatabase {
    pub fn new(lru_capacity: Option<u16>) -> RootDatabase {
        let mut db = RootDatabase {
            storage: ManuallyDrop::new(salsa::Storage::default()),
            files: Default::default(),
            crates_map: Default::default(),
            nonce: Nonce::new(),
        };

        // Initialize empty crate list first (prevents panics)
        db.set_all_crates(Arc::new(Box::new([])));
        CrateGraphBuilder::default().set_in_db(&mut db);

        // Singletons with appropriate durability
        db.set_proc_macros_with_durability(Default::default(), Durability::MEDIUM);
        _ = base_db::LibraryRoots::builder(Default::default())
            .durability(Durability::MEDIUM)
            .new(&db);
        _ = base_db::LocalRoots::builder(Default::default())
            .durability(Durability::MEDIUM)
            .new(&db);

        // HIGH durability — almost never changes
        db.set_expand_proc_attr_macros_with_durability(false, Durability::HIGH);
        db.update_base_query_lru_capacities(lru_capacity);

        db
    }
}
```

### Test Database with Event Logging

```rust
#[salsa_macros::db]
pub(crate) struct TestDB {
    storage: salsa::Storage<Self>,
    files: Arc<base_db::Files>,
    crates_map: Arc<CratesMap>,
    events: Arc<Mutex<Option<Vec<salsa::Event>>>>,
    nonce: Nonce,
}

impl Default for TestDB {
    fn default() -> Self {
        let events = <Arc<Mutex<Option<Vec<salsa::Event>>>>>::default();
        let mut this = Self {
            storage: salsa::Storage::new(Some(Box::new({
                let events = events.clone();
                move |event| {
                    let mut events = events.lock().unwrap();
                    if let Some(events) = &mut *events {
                        events.push(event);
                    }
                }
            }))),
            events,
            files: Default::default(),
            crates_map: Default::default(),
            nonce: Nonce::new(),
        };
        // Same initialization as RootDatabase
        this.set_all_crates(Arc::new(Box::new([])));
        CrateGraphBuilder::default().set_in_db(&mut this);
        // ...
        this
    }
}

impl TestDB {
    /// Enable event capture, run closure, return events.
    pub(crate) fn log(&self, f: impl FnOnce()) -> Vec<salsa::Event> {
        *self.events.lock().unwrap() = Some(Vec::new());
        f();
        self.events.lock().unwrap().take().unwrap()
    }

    /// Run closure, return names of executed queries.
    pub(crate) fn log_executed(&self, f: impl FnOnce()) -> Vec<String> {
        let events = self.log(f);
        events
            .into_iter()
            .filter_map(|e| match e.kind {
                salsa::EventKind::WillExecute { database_key } => {
                    let ingredient = (self as &dyn salsa::Database)
                        .ingredient_debug_name(database_key.ingredient_index());
                    Some(ingredient.to_string())
                }
                _ => None,
            })
            .collect()
    }
}
```

### Nonce Pattern

```rust
static NEXT_NONCE: AtomicUsize = AtomicUsize::new(0);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Nonce(usize);

impl Nonce {
    pub fn new() -> Nonce {
        Nonce(NEXT_NONCE.fetch_add(1, std::sync::atomic::Ordering::SeqCst))
    }
}

// Used to distinguish database instances:
fn nonce_and_revision(&self) -> (Nonce, salsa::Revision) {
    (self.nonce, self.zalsa().current_revision())
}
```

