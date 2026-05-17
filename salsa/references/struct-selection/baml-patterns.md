# BAML — The "Interned Locations with Type-Alias Re-Exports" Pattern

Production struct selection patterns from BAML (AI/LLM function compiler, ~1545 Rust files).

## Inputs (2)

```rust
// baml/baml_language/crates/baml_base/src/files.rs:14
#[salsa::input]
pub struct SourceFile {
    #[returns(ref)]
    pub text: String,
    pub path: PathBuf,
    pub file_id: FileId,
}

// baml/baml_language/crates/baml_workspace/src/lib.rs:50
#[salsa::input]
pub struct Project {
    pub root: PathBuf,
    #[returns(ref)]
    pub files: Vec<SourceFile>,
}
```

**Design choice:** `SourceFile` carries a `FileId` (a plain `u32` newtype) for creating lightweight `Span` values in tokens without referencing the full Salsa-tracked entity. `Project` stores its file list as an input field — Salsa tracks changes to the list (files added/removed) as well as changes to individual files via `SourceFile` setters.

**Where they live:** `SourceFile` is in `baml_base` (lowest-level crate), `Project` is in `baml_workspace` (one level up). `Project` lives here rather than in `baml_project` to avoid circular dependencies — lower-level crates like `baml_compiler_hir` and `baml_compiler_tir` need `Project` in their query signatures.

## Interned Structs (7) — Location-Based IDs

```rust
// baml/baml_language/crates/baml_compiler_hir/src/loc.rs:36-87
#[salsa::interned]
pub struct FunctionLoc {
    pub file: SourceFile,
    pub id: LocalItemId<FunctionMarker>,
}

#[salsa::interned]
pub struct ClassLoc {
    pub file: SourceFile,
    pub id: LocalItemId<ClassMarker>,
}

#[salsa::interned]
pub struct EnumLoc { pub file: SourceFile, pub id: LocalItemId<EnumMarker> }

#[salsa::interned]
pub struct TypeAliasLoc { pub file: SourceFile, pub id: LocalItemId<TypeAliasMarker> }

#[salsa::interned]
pub struct ClientLoc { pub file: SourceFile, pub id: LocalItemId<ClientMarker> }

#[salsa::interned]
pub struct TestLoc { pub file: SourceFile, pub id: LocalItemId<TestMarker> }

#[salsa::interned]
pub struct GeneratorLoc { pub file: SourceFile, pub id: LocalItemId<GeneratorMarker> }
```

Each location uniquely identifies where an item is defined: which file (`SourceFile`) and where in that file's `ItemTree` (`LocalItemId<T>`). `LocalItemId<T>` packs a 16-bit name hash and 16-bit collision index into a `u32`, using `PhantomData<T>` marker types for type safety.

## The Re-Export Pattern: `FunctionLoc` → `FunctionId`

```rust
// baml/baml_language/crates/baml_compiler_hir/src/ids.rs:18-28
pub use crate::loc::FunctionLoc as FunctionId;
pub use crate::loc::ClassLoc as ClassId;
pub use crate::loc::EnumLoc as EnumId;
pub use crate::loc::TypeAliasLoc as TypeAliasId;
pub use crate::loc::ClientLoc as ClientId;
pub use crate::loc::TestLoc as TestId;
pub use crate::loc::GeneratorLoc as GeneratorId;
```

In modern Salsa, interned types ARE their own IDs — the `#[salsa::interned]` macro creates the type directly. BAML re-exports the `*Loc` types as `*Id` type aliases for clarity. Callers import `FunctionId` (the semantic concept) while the implementation uses `FunctionLoc` (the interning detail). This is simpler than rust-analyzer's `impl_intern_key!` macro.

## ItemId Union Enum (Plain Rust Type)

```rust
// baml/baml_language/crates/baml_compiler_hir/src/ids.rs:83-91
#[derive(Clone, Copy, PartialEq, Eq, Hash, salsa::Update)]
pub enum ItemId<'db> {
    Function(FunctionId<'db>),
    Class(ClassId<'db>),
    Enum(EnumId<'db>),
    TypeAlias(TypeAliasId<'db>),
    Client(ClientId<'db>),
    Generator(GeneratorId<'db>),
    Test(TestId<'db>),
}
```

**Why a plain enum?** `ItemId` is used in `Vec<ItemId>` inside tracked structs. It doesn't need its own Salsa identity — it's too fine-grained. The `salsa::Update` derive is needed because it appears inside tracked struct fields.

## Tracked Struct Wrappers for Collections (15 instances)

BAML wraps every collection return in a tracked struct with `#[tracked] #[returns(ref)]` fields:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:80-91
#[salsa::tracked]
pub struct FileItems<'db> {
    #[tracked]
    #[returns(ref)]
    pub items: Vec<ItemId<'db>>,
}

#[salsa::tracked]
pub struct ProjectItems<'db> {
    #[tracked]
    #[returns(ref)]
    pub items: Vec<ItemId<'db>>,
}
```

The same pattern appears 15 times across HIR and TIR:

| Crate | Tracked Struct | Field Type |
|-------|---------------|------------|
| `baml_compiler_hir` | `FileItems` | `Vec<ItemId<'db>>` |
| `baml_compiler_hir` | `ProjectItems` | `Vec<ItemId<'db>>` |
| `baml_compiler_hir` | `LoweringResult` | `Arc<ItemTree>` + `Vec<HirDiagnostic>` |
| `baml_compiler_hir` | `ClassFields` | `Vec<(Name, TypeRef)>` |
| `baml_compiler_hir` | `ProjectClassFields` | `Vec<(Name, Vec<(Name, TypeRef)>)>` |
| `baml_compiler_hir` | `ProjectTypeNames` | `Vec<Name>` |
| `baml_compiler_hir` | `SymbolTable` | `HashMap<Name, SymbolInfo<'db>>` (multiple fields) |
| `baml_compiler_parser` | `ParseResult` | `GreenNode` + `Vec<ParseError>` |
| `baml_compiler_tir` | `EnumVariantsMap` | `HashMap<Name, Vec<Name>>` |
| `baml_compiler_tir` | `TypingContextMap` | `HashMap<Name, Ty>` |
| `baml_compiler_tir` | `ClassFieldTypesMap` | `HashMap<Name, HashMap<Name, Ty>>` |
| `baml_compiler_tir` | `TypeAliasesMap` | `HashMap<Name, Ty>` |
| `baml_compiler_tir` | `ClassNamesSet` | `HashSet<Name>` |
| `baml_compiler_tir` | `EnumNamesSet` | `HashSet<Name>` |
| `baml_compiler_tir` | `TypeAliasNamesSet` | `HashSet<Name>` |

**Why not return the collection directly?** Returning `Vec<ItemId<'db>>` from a tracked function would create lifetime issues — the `'db` lifetime in `ItemId` ties to the database borrow, and Salsa's memoization needs to own the return value. Wrapping in a tracked struct solves this: the struct owns the data, and callers access it via `.items(db)`.

## Plain Rust Types (Not Tracked)

These types are too fine-grained for Salsa:

- **`ItemTree`** — Per-file item storage. Contains `HashMap<LocalItemId<T>, T>` for functions, classes, enums, etc. Stored inside `LoweringResult` as `Arc<ItemTree>`.
- **`Function`, `Class`, `Enum`, `TypeAlias`** — Individual item definitions. Fields like `name: Name`, `fields: Vec<Field>`. Position-independent (no spans).
- **`FunctionSignature`, `FunctionBody`** — Signature has `params` and `return_type`; body is an enum (LLM prompt or expression IR). Both returned from separate tracked functions for independent caching.
- **`TypeRef`** — HIR-level type representation before resolution.
- **`Ty`** — TIR-level resolved type.
- **`InferenceResult`** — Contains expr types, errors, resolutions. Returned from `function_type_inference` wrapped in `Arc`.

## Marker Types for Type-Safe IDs

```rust
// baml/baml_language/crates/baml_compiler_hir/src/loc.rs:17-33
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct FunctionMarker;
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct ClassMarker;
// ... 5 more marker types

// baml/baml_language/crates/baml_compiler_hir/src/ids.rs:118-137
pub struct LocalItemId<T> {
    packed: u32,          // upper 16: hash, lower 16: collision index
    _phantom: PhantomData<T>,
}
```

`LocalItemId<FunctionMarker>` and `LocalItemId<ClassMarker>` are different types — you can't accidentally pass a class ID where a function ID is expected, even though both are `u32` internally. The hash-based design means IDs survive insertions/deletions elsewhere in the file.
