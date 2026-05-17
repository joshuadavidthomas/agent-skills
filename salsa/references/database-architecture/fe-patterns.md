# Fe — Marker Traits, Boilerplate Macros, and 6-Layer Hierarchy

Fe (github.com/argotorg/fe) demonstrates marker traits for compilation phase enforcement and macros for database boilerplate reduction.

## Marker Traits for Phase Enforcement

Fe's trait hierarchy uses blanket-implemented marker traits to restrict which code can access span-dependent information:

```rust
// Marker: code that requires LowerHirDb may depend on span-sensitive data
// during AST → HIR lowering. Analysis functions must NOT take this trait.
pub trait LowerHirDb: salsa::Database + HirDb {}
impl<T> LowerHirDb for T where T: HirDb {}

// Marker: code that requires SpannedHirDb may read span information.
// Analysis tracked functions must NOT take this trait — only diagnostic
// rendering code should.
pub trait SpannedHirDb: salsa::Database + HirDb {}
impl<T> SpannedHirDb for T where T: HirDb {}

// Combined marker for diagnostic finalization
#[salsa::db]
pub trait SpannedHirAnalysisDb:
    salsa::Database + HirDb + SpannedHirDb + HirAnalysisDb
{
}

#[salsa::db]
impl<T> SpannedHirAnalysisDb for T where T: HirAnalysisDb + SpannedHirDb {}
```

**How this enforces position-independent caching:** Analysis tracked functions take `&dyn HirAnalysisDb`, which does NOT extend `SpannedHirDb`. They physically cannot access span data. Diagnostic rendering takes `&dyn SpannedHirAnalysisDb`, which adds span access. Since analysis results are cached without spans, whitespace changes don't invalidate them.

## `define_input_db!` Macro for Boilerplate Reduction

Fe provides macros that generate a complete database struct with standard fields and trait implementations:

```rust
macro_rules! impl_input_db {
    ($db_type:ty) => {
        #[salsa::db]
        impl $crate::InputDb for $db_type {
            fn workspace(&self) -> $crate::file::Workspace {
                self.index.clone().expect("Workspace not initialized")
            }
            fn dependency_graph(&self) -> $crate::dependencies::DependencyGraph {
                self.graph.clone().expect("Graph not initialized")
            }
        }
    };
}

macro_rules! impl_db_default {
    ($db_type:ty) => {
        impl Default for $db_type
        where
            $db_type: $crate::stdlib::HasBuiltinCore + $crate::stdlib::HasBuiltinStd,
        {
            fn default() -> Self {
                let mut db = Self {
                    storage: salsa::Storage::default(),
                    index: None,
                    graph: None,
                };
                let index = $crate::file::Workspace::default(&db);
                db.index = Some(index);
                let graph = $crate::dependencies::DependencyGraph::default(&db);
                db.graph = Some(graph);
                $crate::stdlib::HasBuiltinCore::initialize_builtin_core(&mut db);
                $crate::stdlib::HasBuiltinStd::initialize_builtin_std(&mut db);
                db
            }
        }
    };
}

macro_rules! define_input_db {
    ($db_name:ident) => {
        #[derive(Clone)]
        #[salsa::db]
        pub struct $db_name {
            storage: salsa::Storage<Self>,
            index: Option<$crate::file::Workspace>,
            graph: Option<$crate::dependencies::DependencyGraph>,
        }

        #[salsa::db]
        impl salsa::Database for $db_name {
            fn salsa_event(&self, _event: &dyn Fn() -> salsa::Event) {}
        }

        $crate::impl_input_db!($db_name);
        $crate::impl_db_default!($db_name);
    };
}
```

Usage is a one-liner:

```rust
define_input_db!(DriverDataBase);   // Production database
define_input_db!(TestDatabase);     // Test databases (used in 3+ test modules)
```

This is a middle ground between Cairo's blanket-impl pattern (which eliminates ALL trait impls) and BAML's manual approach (which repeats 6 `#[salsa::db] impl` blocks per database).

## Production Database

The `DriverDataBase` created by `define_input_db!` gets additional methods for running analysis:

```rust
define_input_db!(DriverDataBase);

impl DriverDataBase {
    pub fn run_on_top_mod<'db>(&'db self, top_mod: TopLevelMod<'db>) -> DiagnosticsCollection<'db> {
        self.run_on_file_with_pass_manager(top_mod, initialize_analysis_pass())
    }

    pub fn run_on_ingot<'db>(&'db self, ingot: Ingot<'db>) -> DiagnosticsCollection<'db> {
        self.run_on_ingot_with_pass_manager(ingot, initialize_analysis_pass())
    }

    pub fn top_mod(&self, input: File) -> TopLevelMod<'_> {
        map_file_to_mod(self, input)
    }
}
```

## LSP Backend — Mutable Database, No Snapshots

Fe's LSP uses a simple mutable database pattern (no snapshot/cancellation):

```rust
pub struct Backend {
    pub(super) client: ClientSocket,
    pub(super) db: DriverDataBase,
    pub(super) workers: tokio::runtime::Runtime,
    pub(super) builtin_files: Option<BuiltinFiles>,
    pub(super) readonly_warnings: FxHashSet<Url>,
}

impl Backend {
    pub fn new(client: ClientSocket) -> Self {
        let db = DriverDataBase::default();
        let builtin_files = BuiltinFiles::new(&db).ok();
        // ...
    }
}
```

File changes go through the `Workspace` input's methods:

```rust
// File opened or edited — update workspace with new content
backend.db.workspace().update(&mut backend.db, url, contents);

// File created — touch creates if needed
backend.db.workspace().touch(&mut backend.db, url, Some(contents));

// File deleted — remove from workspace
backend.db.workspace().remove(&mut backend.db, &url);
```
