# Cairo — Blanket-Impl Trait Hierarchy with Init Functions

Production database architecture from Cairo (StarkNet smart contract compiler).

## Cairo: Blanket-Impl Trait Hierarchy with Init Functions

### 8-Layer Blanket-Implemented Trait Hierarchy

Cairo's group traits are all blanket-implemented for `Database` — no explicit trait impls needed per database struct:

```rust
// Layer 1: File system access
pub trait FilesGroup: Database {
    fn crate_configs(&self) -> &OrderedHashMap<CrateId, CrateConfiguration> {
        crate_configs(self.as_dyn_database())
    }
    fn file_content(&self, file_id: FileId) -> Option<&str> {
        file_content(self.as_dyn_database(), file_id).as_ref().map(|c| c.as_ref())
    }
    // ... more methods ...
}
impl<T: Database + ?Sized> FilesGroup for T {}  // Blanket impl!

// Layer 5: Semantic analysis
pub trait SemanticGroup: Database {
    fn lookup_resolved_generic_item_by_ptr(&self, ...) -> Option<ResolvedGenericItem> {
        lookup_resolved_generic_item_by_ptr(self.as_dyn_database(), ...)
    }
    // ... 100+ methods delegating to tracked functions ...
}
impl<T: Database + ?Sized> SemanticGroup for T {}

// Every layer follows this pattern — 8 layers total:
// FilesGroup, FlagsGroup, SyntaxGroup, ParserGroup, DefsGroup,
// SemanticGroup, LoweringGroup, SierraGenGroup, DocGroup
```

### Singleton Inputs via Option + Tracked Function

Each layer has a singleton input struct with `Option<T>` fields, created by a tracked function:

```rust
#[salsa::input]
pub struct LoweringGroupInput {
    #[returns(ref)]
    pub optimizations: Option<Optimizations>,
    #[returns(ref)]
    code_size_estimator: Option<CodeSizeEstimator>,
}

#[salsa::tracked(returns(ref))]
pub fn lowering_group_input(db: &dyn Database) -> LoweringGroupInput {
    LoweringGroupInput::new(db, None, None)
}

// Init function sets the defaults
pub fn init_lowering_group(
    db: &mut dyn Database,
    optimizations: Optimizations,
    code_size_estimator: Option<CodeSizeEstimator>,
) {
    lowering_group_input(db).set_optimizations(db).to(Some(optimizations));
    lowering_group_input(db).set_code_size_estimator(db).to(code_size_estimator);
}
```

### RootDatabase: Builder Pattern + Init Chain

```rust
#[salsa::db]
#[derive(Clone)]
pub struct RootDatabase {
    storage: salsa::Storage<RootDatabase>,
}

#[salsa::db]
impl salsa::Database for RootDatabase {}
// NO other trait impls needed — all group traits are blanket-implemented!

impl RootDatabase {
    fn new(plugin_suite: PluginSuite, optimizations: Optimizations) -> Self {
        let mut res = Self { storage: Default::default() };
        // Init chain — order matters!
        init_external_files(&mut res);
        init_files_group(&mut res);
        init_lowering_group(&mut res, optimizations, Some(estimate_code_size));
        init_defs_group(&mut res);
        init_semantic_group(&mut res);
        init_sierra_gen_group(&mut res);
        res.set_default_plugins_from_suite(plugin_suite);
        res
    }

    pub fn builder() -> RootDatabaseBuilder {
        RootDatabaseBuilder::new()
    }

    pub fn snapshot(&self) -> RootDatabase {
        RootDatabase { storage: self.storage.clone() }
    }
}
```

### Test Databases: Minimal Boilerplate

Because traits are blanket-implemented, test databases are trivially simple:

```rust
#[salsa::db]
#[derive(Clone)]
pub struct FilesDatabaseForTesting {
    storage: salsa::Storage<FilesDatabaseForTesting>,
}

#[salsa::db]
impl salsa::Database for FilesDatabaseForTesting {}

impl Default for FilesDatabaseForTesting {
    fn default() -> Self {
        let mut res = Self { storage: Default::default() };
        init_files_group(&mut res);  // Just call the init function
        res
    }
}
// All group traits (FilesGroup, FlagsGroup, etc.) are automatic!
```

Compare with ty/rust-analyzer where each test database must explicitly implement every trait in the hierarchy.

### `CloneableDatabase`: Parallel Query Execution

Cairo uses a trait to enable cloning `dyn Database` for Rayon:

```rust
pub trait CloneableDatabase: salsa::Database + Send {
    fn dyn_clone(&self) -> Box<dyn CloneableDatabase>;
}

impl Clone for Box<dyn CloneableDatabase> {
    fn clone(&self) -> Self { self.dyn_clone() }
}
```

Parallel diagnostic computation:

```rust
pub fn ensure_diagnostics(
    db: &dyn CloneableDatabase,
    reporter: &mut DiagnosticsReporter<'_>,
) -> Result<(), DiagnosticsError> {
    if rayon::current_num_threads() > 1 {
        let crates = reporter.crates_of_interest(db);
        let warmup_db = db.dyn_clone();
        let ensure_db = db.dyn_clone();
        rayon::join(
            move || warmup_diagnostics_blocking(warmup_db.as_ref(), crates),
            move || reporter.ensure(ensure_db.as_ref()),
        ).1
    } else {
        reporter.ensure(db)
    }
}
```

This is simpler than rust-analyzer's snapshot pattern — appropriate for compilers that don't need cancellation.

### Convenience Macros for Input Mutation

Cairo provides macros for common mutation patterns on singleton inputs:

```rust
// Set crate configuration
#[macro_export]
macro_rules! set_crate_config {
    ($self:expr, $crt:expr, $root:expr) => {
        let crate_configs = update_crate_configuration_input_helper($self, $crt, $root);
        set_crate_configs_input($self, Some(crate_configs));
    };
}

// Override file content (for LSP/tests)
#[macro_export]
macro_rules! override_file_content {
    ($self:expr, $file:expr, $content:expr) => {
        let file = $self.file_input($file).clone();
        let overrides = update_file_overrides_input_helper($self, file, $content);
        files_group_input($self).set_file_overrides($self).to(Some(overrides));
    };
}
```
