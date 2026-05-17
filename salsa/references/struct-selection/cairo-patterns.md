# Cairo — The "Macro-Generated Interned IDs" Pattern

Production struct selection patterns from Cairo (StarkNet smart contract language compiler).

## The `define_short_id!` Macro: 38+ Interned Types from One-Liners

Cairo uses a macro to generate interned structs at scale. Each call creates an interned type with `revisions = usize::MAX` (immortal — never garbage-collected):

```rust
// In cairo-lang-utils/src/lib.rs
macro_rules! define_short_id {
    ($short_id:ident, $long_id:path) => {
        #[cairo_lang_proc_macros::interned(revisions = usize::MAX)]
        pub struct $short_id<'db> {
            #[returns(ref)]
            pub long: $long_id,
        }

        impl<'db> cairo_lang_utils::Intern<'db, $short_id<'db>> for $long_id {
            fn intern(self, db: &'db dyn salsa::Database) -> $short_id<'db> {
                $short_id::new(db, self)
            }
        }
        // ... Debug, Lookup impls ...
    };
}
```

Usage — one line per type:

```rust
// Filesystem layer
define_short_id!(CrateId, CrateLongId<'db>);
define_short_id!(FileId, FileLongId<'db>);
define_short_id!(SmolStrId, SmolStr);
define_short_id!(BlobId, BlobLongId);

// Semantic layer — type system
define_short_id!(TypeId, TypeLongId<'db>);
define_short_id!(ConcreteStructId, ConcreteStructLongId<'db>);
define_short_id!(ConcreteEnumId, ConcreteEnumLongId<'db>);
define_short_id!(ConcreteTraitId, ConcreteTraitLongId<'db>);
define_short_id!(FunctionId, FunctionLongId<'db>);
define_short_id!(ImplId, ImplLongId<'db>);
// ... 25+ more
```

## Definition Location IDs via Another Macro

Cairo also has a `define_language_element_id_basic!` macro for AST-backed definitions. It generates interned IDs similar to rust-analyzer's pattern:

```rust
macro_rules! define_language_element_id_basic {
    ($short_id:ident, $long_id:ident, $ast_ty:ty) => {
        #[derive(Clone, PartialEq, Eq, Hash, Debug, salsa::Update, HeapSize)]
        pub struct $long_id<'db>(
            pub ModuleId<'db>,
            pub <$ast_ty as TypedSyntaxNode<'db>>::StablePtr,
        );
        define_short_id!($short_id, $long_id<'db>);
        // ... LanguageElementId impl ...
    };
}
```

This pattern is strikingly similar to rust-analyzer's `impl_intern_key!` — both create interned ID types from (container, AST pointer) pairs.

## Singleton Inputs: Option Fields Behind Tracked Functions

Cairo's input structs use `Option<T>` fields, initialized to `None` by the tracked function and set to `Some(value)` by init functions:

```rust
#[salsa::input]
pub struct FilesGroupInput {
    #[returns(ref)]
    pub crate_configs: Option<OrderedHashMap<CrateInput, CrateConfigurationInput>>,
    #[returns(ref)]
    pub file_overrides: Option<OrderedHashMap<FileInput, Arc<str>>>,
    #[returns(ref)]
    pub flags: Option<OrderedHashMap<FlagLongId, Flag>>,
    #[returns(ref)]
    pub cfg_set: Option<CfgSet>,
}

#[salsa::tracked]
pub fn files_group_input(db: &dyn Database) -> FilesGroupInput {
    FilesGroupInput::new(db, None, None, None, None)
}

// Initialization — called during database construction
pub fn init_files_group(db: &mut dyn Database) {
    let inp = files_group_input(db);
    inp.set_file_overrides(db).to(Some(Default::default()));
    inp.set_crate_configs(db).to(Some(Default::default()));
    inp.set_flags(db).to(Some(Default::default()));
    inp.set_cfg_set(db).to(Some(Default::default()));
}
```

Cairo has 4 such singleton inputs (FilesGroupInput, DefsGroupInput, SemanticGroupInput, LoweringGroupInput), each behind a tracked function, each initialized by a separate `init_*_group()` function.

## `CloneableDatabase`: Parallel Compilation

Cairo enables parallel query execution via a custom trait:

```rust
pub trait CloneableDatabase: salsa::Database + Send {
    fn dyn_clone(&self) -> Box<dyn CloneableDatabase>;
}

impl Clone for Box<dyn CloneableDatabase> {
    fn clone(&self) -> Self { self.dyn_clone() }
}
```

Used with Rayon for parallel diagnostic computation:

```rust
fn warmup_diagnostics_blocking(db: &dyn CloneableDatabase, crates: Vec<CrateInput>) {
    crates.into_par_iter().for_each_with(db.dyn_clone(), |db, crate_input| {
        let crate_id = crate_input.into_crate_long_id(db.as_ref()).intern(db.as_ref());
        db.crate_modules(crate_id).into_par_iter().for_each_with(
            db.dyn_clone(),
            |db, module_id| {
                let _ = db.module_semantic_diagnostics(*module_id);
                let _ = db.module_lowering_diagnostics(*module_id);
            },
        );
    });
}
```

## Proc Macro Wrappers for Automatic `heap_size`

Cairo's `#[cairo_lang_proc_macros::interned]` and `#[cairo_lang_proc_macros::tracked]` automatically inject `heap_size = cairo_lang_utils::HeapSize::heap_size` into the Salsa attribute, ensuring every struct and function has memory profiling:

```rust
// User writes:
#[cairo_lang_proc_macros::tracked(returns(ref))]
fn my_query(db: &dyn Database) -> LargeResult { ... }

// Macro expands to:
#[salsa::tracked(returns(ref), heap_size = cairo_lang_utils::HeapSize::heap_size)]
fn my_query(db: &dyn Database) -> LargeResult { ... }
```
