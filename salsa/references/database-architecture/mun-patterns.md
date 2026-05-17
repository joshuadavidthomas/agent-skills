# Mun Database Architecture [Legacy API/Architecture]

Mun uses Salsa 2018 (v0.16.1) with `#[salsa::query_group]` and `#[salsa::database]` macros. Use for **architectural insights** — adapt to modern `#[salsa::db]` syntax.

## Two Concrete Databases from One Trait Stack

Mun uniquely has **two production databases** built from the same trait hierarchy:

### CompilerDatabase (CLI + Daemon)

```rust
// mun_compiler/src/db.rs
#[salsa::database(
    mun_hir_input::SourceDatabaseStorage,
    mun_hir::InternDatabaseStorage,
    mun_hir::AstDatabaseStorage,
    mun_hir::DefDatabaseStorage,
    mun_hir::HirDatabaseStorage,
    CodeGenDatabaseStorage  // ← Includes LLVM codegen
)]
pub struct CompilerDatabase {
    storage: salsa::Storage<Self>,
}

impl CompilerDatabase {
    pub fn new(config: &Config) -> Self {
        let mut db = CompilerDatabase { storage: salsa::Storage::default() };
        db.set_config(config);
        db
    }

    pub fn set_config(&mut self, config: &Config) {
        self.set_target(config.target.clone());
        self.set_optimization_level(config.optimization_lvl);
    }
}

impl salsa::Database for CompilerDatabase {}
// NOTE: No ParallelDatabase impl — codegen uses Rc<TargetMachine> (not Send)
```

### AnalysisDatabase (LSP)

```rust
// mun_language_server/src/db.rs
#[salsa::database(
    mun_hir_input::SourceDatabaseStorage,
    mun_hir::DefDatabaseStorage,
    mun_hir::HirDatabaseStorage,
    mun_hir::AstDatabaseStorage,
    mun_hir::InternDatabaseStorage
    // NOTE: No CodeGenDatabaseStorage — LSP doesn't need LLVM
)]
pub(crate) struct AnalysisDatabase {
    storage: salsa::Storage<Self>,
}

impl AnalysisDatabase {
    pub fn request_cancelation(&mut self) {
        self.salsa_runtime_mut().synthetic_write(Durability::LOW);
    }
}

impl salsa::Database for AnalysisDatabase {
    fn on_propagated_panic(&self) -> ! {
        Canceled::throw()
    }
    fn salsa_event(&self, event: salsa::Event) {
        match event.kind {
            salsa::EventKind::DidValidateMemoizedValue { .. }
            | salsa::EventKind::WillExecute { .. } => {
                self.check_canceled();
            }
            _ => (),
        }
    }
}

// LSP database supports snapshots for concurrent queries
impl salsa::ParallelDatabase for AnalysisDatabase {
    fn snapshot(&self) -> Snapshot<Self> {
        Snapshot::new(AnalysisDatabase {
            storage: self.storage.snapshot(),
        })
    }
}
```

### Why Two Databases?

| Concern | CompilerDatabase | AnalysisDatabase |
|---------|-----------------|-------------------|
| LLVM dependency | Yes (inkwell) | No |
| Concurrency | Single-threaded | ParallelDatabase (snapshots) |
| Cancellation | None needed | salsa_event + on_propagated_panic |
| Use case | CLI compile, daemon hot-reload | LSP diagnostics, completions |

The trait stack is shared: both databases implement `SourceDatabase → AstDatabase → InternDatabase → DefDatabase → HirDatabase`. The compiler adds `CodeGenDatabase` on top. This means all parsing, name resolution, and type inference queries are shared — only the codegen layer differs.

## 6-Layer Trait Hierarchy

```rust
// Layer 1: mun_hir_input/src/db.rs
#[salsa::query_group(SourceDatabaseStorage)]
pub trait SourceDatabase: salsa::Database {
    #[salsa::input] fn file_text(&self, file_id: FileId) -> Arc<str>;
    #[salsa::input] fn file_source_root(&self, file_id: FileId) -> SourceRootId;
    #[salsa::input] fn packages(&self) -> Arc<PackageSet>;
    #[salsa::input] fn source_root(&self, id: SourceRootId) -> Arc<SourceRoot>;
    fn file_relative_path(&self, file_id: FileId) -> RelativePathBuf;
    fn module_tree(&self, package: PackageId) -> Arc<ModuleTree>;
    fn line_index(&self, file_id: FileId) -> Arc<LineIndex>;
}

// Layer 2: mun_hir/src/db.rs
#[salsa::query_group(AstDatabaseStorage)]
pub trait AstDatabase: SourceDatabase {
    fn parse(&self, file_id: FileId) -> Parse<ast::SourceFile>;
    fn ast_id_map(&self, file_id: FileId) -> Arc<AstIdMap>;
}

// Layer 3: mun_hir/src/db.rs
#[salsa::query_group(InternDatabaseStorage)]
pub trait InternDatabase: SourceDatabase {
    #[salsa::interned] fn intern_function(&self, loc: FunctionLoc) -> FunctionId;
    #[salsa::interned] fn intern_struct(&self, loc: StructLoc) -> StructId;
    #[salsa::interned] fn intern_type_alias(&self, loc: TypeAliasLoc) -> TypeAliasId;
    #[salsa::interned] fn intern_impl(self, loc: ImplLoc) -> ImplId;
}

// Layer 4: mun_hir/src/db.rs
#[salsa::query_group(DefDatabaseStorage)]
pub trait DefDatabase: InternDatabase + AstDatabase {
    fn item_tree(&self, file_id: FileId) -> Arc<ItemTree>;
    fn struct_data(&self, id: StructId) -> Arc<StructData>;
    fn fn_data(&self, func: FunctionId) -> Arc<FunctionData>;
    fn package_defs(&self, package_id: PackageId) -> Arc<PackageDefs>;
    fn body(&self, def: DefWithBodyId) -> Arc<Body>;
    fn body_with_source_map(&self, def: DefWithBodyId) -> (Arc<Body>, Arc<BodySourceMap>);
    fn expr_scopes(&self, def: DefWithBodyId) -> Arc<ExprScopes>;
    // ... more queries
}

// Layer 5: mun_hir/src/db.rs
#[salsa::query_group(HirDatabaseStorage)]
pub trait HirDatabase: DefDatabase {
    #[salsa::input] fn target(&self) -> Target;
    fn target_data_layout(&self) -> Arc<abi::TargetDataLayout>;
    fn infer(&self, def: DefWithBodyId) -> Arc<InferenceResult>;
    fn lower_struct(&self, def: Struct) -> Arc<LowerTyMap>;
    fn callable_sig(&self, def: CallableDef) -> FnSig;
    fn inherent_impls_in_package(&self, package: PackageId) -> Arc<InherentImpls>;
    // ... more queries
}

// Layer 6 (compiler only): mun_codegen/src/db.rs
#[salsa::query_group(CodeGenDatabaseStorage)]
pub trait CodeGenDatabase: mun_hir::HirDatabase {
    #[salsa::input] fn optimization_level(&self) -> inkwell::OptimizationLevel;
    fn module_partition(&self) -> Arc<ModulePartition>;
    fn target_machine(&self) -> ByAddress<Rc<inkwell::targets::TargetMachine>>;
    fn assembly_ir(&self, module_group: ModuleGroupId) -> Arc<AssemblyIr>;
    fn target_assembly(&self, module_group: ModuleGroupId) -> Arc<TargetAssembly>;
}
```

## Test Databases

Both `mun_hir` and `mun_codegen` have their own MockDatabase with event logging:

```rust
// mun_hir/src/mock.rs
#[salsa::database(
    mun_hir_input::SourceDatabaseStorage,
    crate::AstDatabaseStorage,
    crate::InternDatabaseStorage,
    crate::DefDatabaseStorage,
    crate::HirDatabaseStorage
)]
pub(crate) struct MockDatabase {
    storage: salsa::Storage<Self>,
    events: Mutex<Option<Vec<salsa::Event>>>,
}

impl MockDatabase {
    pub fn log(&self, f: impl FnOnce()) -> Vec<salsa::Event> {
        *self.events.lock() = Some(Vec::new());
        f();
        self.events.lock().take().unwrap()
    }

    pub fn log_executed(&self, f: impl FnOnce()) -> Vec<String> {
        let events = self.log(f);
        events.into_iter()
            .filter_map(|e| match e.kind {
                salsa::EventKind::WillExecute { database_key } => {
                    Some(format!("{:?}", database_key.debug(self)))
                }
                _ => None,
            })
            .collect()
    }
}
```

The codegen MockDatabase adds a convenience constructor:

```rust
// mun_codegen/src/mock.rs
impl MockDatabase {
    pub fn with_single_file(text: &str) -> (MockDatabase, FileId) {
        let mut db = MockDatabase::default();
        let mut source_root = SourceRoot::default();
        let file_id = FileId(0);
        db.set_file_text(file_id, Arc::from(text.to_owned()));
        db.set_file_source_root(file_id, SourceRootId(0));
        source_root.insert_file(file_id, RelativePathBuf::from("mod.mun"));
        db.set_source_root(SourceRootId(0), Arc::new(source_root));
        let mut packages = PackageSet::default();
        packages.add_package(SourceRootId(0));
        db.set_packages(Arc::new(packages));
        db.set_optimization_level(OptimizationLevel::None);
        (db, file_id)
    }
}
```

## The Driver: Stateful Compiler Frontend

The `Driver` manages file state outside Salsa and coordinates incremental compilation:

```rust
// mun_compiler/src/driver.rs
pub struct Driver {
    db: CompilerDatabase,
    out_dir: PathBuf,
    source_root: SourceRoot,
    path_to_file_id: HashMap<RelativePathBuf, FileId>,
    file_id_to_path: HashMap<FileId, RelativePathBuf>,
    next_file_id: usize,
    module_to_temp_assembly_path: HashMap<Module, PathBuf>,
    emit_ir: bool,
}
```

The `path_to_file_id` map serves the same role as ty's `Files` side-table — it provides path→FileId lookup that Salsa doesn't natively offer. File IDs are reused across edits for cache stability.
