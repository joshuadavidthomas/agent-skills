# ty — The "Almost No Tracked Structs" Pattern

Production struct selection patterns from ty (the Python type checker in the Ruff/ty monorepo).

## Why ty Avoids Tracked Structs

From `InternedConstraintSet` in the type system — the explicit rationale:

```rust
/// A Salsa-interned constraint set. This is only needed to have something appropriately small to
/// put in a [`KnownInstance::ConstraintSet`]. We don't actually manipulate these as part of using
/// constraint sets to check things like assignability; they're only used as a debugging aid in
/// mdtests. In theory, that means there's no need for this to be interned; being tracked would be
/// sufficient. However, we currently think that tracked structs are unsound w.r.t. salsa cycles,
/// so out of an abundance of caution, we are interning the struct.
#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
#[derive(PartialOrd, Ord)]
pub struct InternedConstraintSet<'db> {
    constraints: ConstraintSet<'db>,
}
```

## Input: `File` — The Root of the Computation (ruff_db, shared)

```rust
/// A file that's either stored on the host system's file system or in the vendored file system.
#[salsa::input(heap_size=ruff_memory_usage::heap_size)]
#[derive(PartialOrd, Ord)]
pub struct File {
    /// The path of the file (immutable).
    #[returns(ref)]
    pub path: FilePath,

    /// Unix permissions. Always `None` on Windows or when the file has been deleted.
    #[default]
    pub permissions: Option<u32>,

    /// The file revision. A file has changed if the revisions don't compare equal.
    #[default]
    pub revision: FileRevision,

    // ...
}
```

No `'db` lifetime — `File` is a plain integer ID, safe to store in side tables and pass across revisions.

## Interned Types: The Entire Type System

ty represents every type as an interned struct. Here are representative examples:

```rust
#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
pub struct UnionType<'db> {
    /// The union type includes values in any of these types.
    #[returns(deref)]
    pub elements: Box<[Type<'db>]>,
}

#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
pub struct IntersectionType<'db> {
    /// The intersection type includes only values in all of these types.
    #[returns(ref)]
    positive: FxOrderSet<Type<'db>>,

    /// The intersection type does not include any value in any of these types.
    #[returns(ref)]
    negative: FxOrderSet<Type<'db>>,
}

#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
#[derive(PartialOrd, Ord)]
pub struct CallableType<'db> {
    #[returns(ref)]
    pub(crate) signatures: CallableSignature<'db>,
    kind: CallableTypeKind,
}
```

The pattern: same data → same ID, stable identity during cycle iteration, O(1) equality.

## The Two Exceptions: Tracked Structs With Stability Guarantees

ty uses tracked structs only for stable semantic identities — not computed data:

```rust
/// ## ID stability
/// The `Definition`'s ID is stable when the only field that changes is its `kind` (AST node).
#[salsa::tracked(debug, heap_size=ruff_memory_usage::heap_size)]
#[derive(Ord, PartialOrd)]
pub struct Definition<'db> {
    pub file: File,
    pub(crate) file_scope: FileScopeId,
    pub(crate) place: ScopedPlaceId,

    /// WARNING: Only access this field when doing type inference for the same
    /// file as where `Definition` is defined to avoid cross-file query dependencies.
    #[no_eq]
    #[returns(ref)]
    #[tracked]
    pub kind: DefinitionKind<'db>,

    pub(crate) is_reexported: bool,
}
```

Note the careful field design: `file`, `file_scope`, and `place` are identity fields. `kind` is `#[tracked]` with `#[no_eq]` because AST nodes change on every edit but downstream consumers usually don't care about the exact node — they care about the type.

## The Wrapper Pattern: Interning Non-Salsa Arguments

When a tracked function needs a non-Salsa argument, ty wraps it in an interned struct:

```rust
/// A thin wrapper around `ModuleName` to make it a Salsa ingredient.
#[salsa::interned(debug, heap_size=ruff_memory_usage::heap_size)]
struct ModuleNameIngredient<'db> {
    #[returns(ref)]
    pub(super) name: ModuleName,
    pub(super) mode: ModuleResolveMode,
}

/// Public API: wraps the plain argument, then calls the tracked query.
pub fn resolve_module<'db>(
    db: &'db dyn Db,
    importing_file: File,
    module_name: &ModuleName,
) -> Option<Module<'db>> {
    let interned_name = ModuleNameIngredient::new(db, module_name, ModuleResolveMode::StubsAllowed);
    resolve_module_query(db, interned_name)
        .or_else(|| desperately_resolve_module(db, importing_file, interned_name))
}

#[salsa::tracked(heap_size=ruff_memory_usage::heap_size)]
fn resolve_module_query<'db>(
    db: &'db dyn Db,
    module_name: ModuleNameIngredient<'db>,
) -> Option<Module<'db>> {
    // ... actual resolution logic ...
}
```
