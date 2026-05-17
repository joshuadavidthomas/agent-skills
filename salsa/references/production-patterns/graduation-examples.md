# Salsa Graduation: Real-World Transition Examples

This document tracks specific "graduation" moments from simple to sophisticated patterns in the reference projects.

## 1. Diagnostics: From Accumulator to Pyramid
**When to graduate:** When you need "Early Cutoff" for workspace-wide diagnostics.

### Level 1: The Accumulator (djls)
```rust
#[salsa::accumulator]
pub struct ValidationErrorAccumulator(Diagnostic);

#[salsa::tracked]
pub fn validate_template(db: &dyn Db, template: Template) {
    // ... logic ...
    ValidationErrorAccumulator::push(db, diag);
}
```

### Level 3: The Pyramid (Cairo)
Cairo returns diagnostics in a hierarchy of tracked functions:
1. `get_item_diagnostics` (per function/struct)
2. `get_module_diagnostics` (aggregates items)
3. `get_file_diagnostics` (aggregates modules)
4. `get_crate_diagnostics` (aggregates files)

```rust
// cairo/crates/cairo-lang-semantic/src/db.rs
#[salsa::tracked]
pub fn module_semantic_diagnostics(
    db: &dyn SemanticGroup,
    module_id: ModuleId,
) -> Maybe<Diagnostics<SemanticDiagnostic>> {
    // Collect from submodules, items, etc.
    // Returning the Diagnostics struct allows Salsa to see if the 
    // AGGREGATED list changed. If not, downstream queries stop.
}
```

## 2. Entities: From Tracked Struct to Interned ID
**When to graduate:** When creating thousands of objects becomes a memory or revalidation bottleneck.

### Level 1: Tracked Struct (BAML)
```rust
#[salsa::tracked]
pub struct Class<'db> {
    #[id] pub name: Word<'db>,
    #[tracked] pub fields: Vec<Field<'db>>,
}
```

### Level 3: Interned ID (ty)
ty uses zero tracked structs for its type system. Everything is an interned ID.
```rust
// ruff/crates/ty_python_semantic/src/types.rs
#[salsa::interned]
pub struct UnionType<'db> {
    #[returns(ref)]
    pub elements: Vec<Type<'db>>,
}

// Data is associated via tracked functions
#[salsa::tracked]
pub fn type_methods(db: &dyn Db, id: TypeId) -> Arc<Methods> { ... }
```

## 3. Identity: From Salsa-Owned to External Side-Table
**When to graduate:** When file discovery (walking thousands of files) is too slow to run inside the computation graph.

### Level 1: Salsa-Owned (Standard)
A tracked function `discover_files` returns `Vec<File>`.

### Level 3: External Side-Table (ty / ruff_db)
The database struct holds a `DashMap` for file identity. Salsa only tracks the *content* of the files found in the map.
```rust
// ruff/crates/ruff_db/src/files.rs
pub struct Files {
    // Outside Salsa, provides stable identity
    by_path: DashMap<SystemPathBuf, File>, 
}
```

## 4. Stability: From Default to "Immortal"
**When to graduate:** For language built-ins or core types that never change.

### Level 3: Immortal Revisions (Cairo)
Cairo uses the undocumented `revisions` attribute to freeze core IDs.
```rust
// cairo/crates/cairo-lang-sierra/src/ids.rs
#[salsa::interned(revisions = "usize::MAX")]
pub struct ConcreteTypeId {
    pub id: u64,
}
```

## 5. Performance: From On-Demand to Parallel Warm-up
**When to graduate:** When the "first click" after opening a project is too slow.

### Level 3: Cloneable Snapshot (Cairo)
```rust
// cairo/crates/cairo-lang-compiler/src/db.rs
impl CloneableDatabase for RootDatabase {
    fn dyn_clone(&self) -> Box<dyn CloneableDatabase> {
        Box::new(self.clone())
    }
}

// Background task
pub fn warmup_diagnostics(db: &dyn Database) {
    let snapshot = db.snapshot();
    rayon::spawn(move || {
        // Run expensive queries in parallel on the snapshot
        all_modules.par_iter().for_each(|m| snapshot.diagnostics(m));
    });
}
```
