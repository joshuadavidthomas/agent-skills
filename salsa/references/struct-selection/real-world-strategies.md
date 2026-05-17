# Real-World Struct Selection Strategies

Detailed struct selection patterns from production Salsa projects.

## ty: "Almost No Tracked Structs"

ty's type system uses **interned types + tracked functions** exclusively. Its 50+ type representations (`UnionType`, `CallableType`, `IntersectionType`, etc.) are all interned:

```rust
// ty pattern: interned types for everything
#[salsa::interned]
pub struct UnionType<'db> {
    #[returns(ref)]
    pub elements: Box<[Type<'db>]>,
}

#[salsa::interned]
pub struct CallableType<'db> {
    // ... fields ...
}
```

**Why?** Python type inference is inherently cyclic (classes reference their own methods, mutual module imports, recursive types). The ty team discovered that **tracked structs are unsound with Salsa's cycle/fixpoint iteration**. Interned types have value-based identity that remains stable during cycle iteration.

ty has only ~2 tracked structs (`Definition`, `ScopeId`) — both represent stable semantic identities with explicit stability guarantees, not computed type data.

**The wrapper pattern** — when a tracked function needs a non-Salsa argument, ty wraps it in an interned struct:

```rust
// ModuleName is a plain Rust type — can't be a tracked fn argument
#[salsa::interned]
struct ModuleNameIngredient<'db> {
    #[returns(ref)]
    pub name: ModuleName,
}

// Public API wraps the argument then calls the real query
pub fn resolve_module(db: &dyn Db, name: &ModuleName) -> Option<Module> {
    let interned = ModuleNameIngredient::new(db, name.clone());
    resolve_module_query(db, interned)
}

#[salsa::tracked]
fn resolve_module_query(db: &dyn Db, name: ModuleNameIngredient) -> Option<Module> {
    // ... actual resolution ...
}
```

For more, see [ty-patterns.md](ty-patterns.md).

## rust-analyzer: "Intern Every Definition Location"

rust-analyzer interns every AST definition location into a typed ID (`FunctionId`, `StructId`, `TraitId`, etc. — 17+ types). These IDs are `Copy` integers that cheaply identify items without loading the AST:

```rust
// Location struct with container + AST pointer
pub struct ItemLoc<N: AstIdNode> {
    pub container: ModuleId,
    pub id: AstId<N>,
}

// Interned into a lightweight ID
// (uses impl_intern_key! macro internally)
#[salsa::interned]
fn intern_struct(&self, loc: StructLoc) -> StructId;
fn intern_function(&self, loc: FunctionLoc) -> FunctionId;
// ... 15 more
```

Usage pattern:
```rust
fn analyze_struct(db: &dyn Db, id: StructId) {
    // Cheap to pass around, compare, store in collections
    let loc = id.lookup(db);       // Only resolve when needed
    let source = loc.source(db);   // Load AST lazily
}
```

rust-analyzer uses tracked structs sparingly — mainly for caching collection queries like `InherentImpls` and `TraitImpls`, not for individual definitions.

For more, see [rust-analyzer-patterns.md](rust-analyzer-patterns.md).

## BAML: "Interned Locations with Type-Alias Re-Exports"

BAML (an AI/LLM function compiler) interns definition locations into typed IDs, like rust-analyzer, but with a cleaner explicit re-export pattern instead of macros:

```rust
// loc.rs — Interned location structs (the Salsa-facing types)
#[salsa::interned]
pub struct FunctionLoc<'db> {
    pub file: SourceFile,
    pub id: LocalItemId<FunctionMarker>,
}

#[salsa::interned]
pub struct ClassLoc<'db> {
    pub file: SourceFile,
    pub id: LocalItemId<ClassMarker>,
}
// ... 5 more (EnumLoc, TypeAliasLoc, ClientLoc, TestLoc, GeneratorLoc)
```

```rust
// ids.rs — Clean type-alias re-exports (the user-facing API)
pub use crate::loc::FunctionLoc as FunctionId;
pub use crate::loc::ClassLoc as ClassId;
pub use crate::loc::EnumLoc as EnumId;
// ...
```

This is more approachable than rust-analyzer's `impl_intern_key!` macro because the mapping is explicit and greppable. The `Loc` suffix on the interned struct signals "this is a location," while the `Id` alias signals "use this in APIs."

**Tracked struct wrapper pattern** — BAML wraps every collection return value in a tracked struct with `#[tracked] #[returns(ref)]` fields, avoiding lifetime issues and enabling field-level tracking:

```rust
#[salsa::tracked]
pub struct FileItems<'db> {
    #[tracked]
    #[returns(ref)]
    pub items: Vec<ItemId<'db>>,
}

#[salsa::tracked]
pub fn file_items(db: &dyn Db, file: SourceFile) -> FileItems<'_> {
    let item_tree = file_item_tree(db, file);
    let items = intern_all_items(db, file, &item_tree);
    FileItems::new(db, items)
}
```

BAML uses this pattern 15 times (FileItems, ProjectItems, LoweringResult, SymbolTable, ClassFields, EnumVariantsMap, TypingContextMap, etc.). It's the "textbook" approach for tracked functions that need to return collections of Salsa types.

For more, see [baml-patterns.md](baml-patterns.md).

## Mun: "Generic Location + Intern Macros" [Legacy API/Architecture]

Mun uses Salsa 2018 (v0.16.1). It interns 4 definition types using a generic `ItemLoc<N>` struct and macros to generate ID types with `Intern`/`Lookup` traits:

```rust
// mun_hir/src/ids.rs — Generic location struct parameterized by AST node type
pub struct ItemLoc<N: ItemTreeNode> {
    pub module: ModuleId,
    pub id: ItemTreeId<N>,
}

// AssocItemLoc adds a container (module or impl block)
pub struct AssocItemLoc<N: ItemTreeNode> {
    pub container: ItemContainerId,
    pub id: ItemTreeId<N>,
}

// Concrete location types are just type aliases
pub(crate) type StructLoc = ItemLoc<Struct>;
pub(crate) type FunctionLoc = AssocItemLoc<Function>;
pub(crate) type TypeAliasLoc = ItemLoc<TypeAlias>;
pub(crate) type ImplLoc = ItemLoc<Impl>;
```

The `impl_intern!` macro generates boilerplate for each ID type:

```rust
macro_rules! impl_intern {
    ($id:ident, $loc:ident, $intern:ident, $lookup:ident) => {
        impl_intern_key!($id);

        impl Intern for $loc {
            type ID = $id;
            fn intern(self, db: &dyn DefDatabase) -> $id {
                db.$intern(self)
            }
        }

        impl Lookup for $id {
            type Data = $loc;
            fn lookup(&self, db: &dyn DefDatabase) -> $loc {
                db.$lookup(*self)
            }
        }
    };
}

// Usage — one line per definition type
impl_intern!(StructId, StructLoc, intern_struct, lookup_intern_struct);
impl_intern!(FunctionId, FunctionLoc, intern_function, lookup_intern_function);
impl_intern!(TypeAliasId, TypeAliasLoc, intern_type_alias, lookup_intern_type_alias);
impl_intern!(ImplId, ImplLoc, intern_impl, lookup_intern_impl);
```

The corresponding interned queries in the database:
```rust
#[salsa::query_group(InternDatabaseStorage)]
pub trait InternDatabase: SourceDatabase {
    #[salsa::interned] fn intern_function(&self, loc: FunctionLoc) -> FunctionId;
    #[salsa::interned] fn intern_struct(&self, loc: StructLoc) -> StructId;
    #[salsa::interned] fn intern_type_alias(&self, loc: TypeAliasLoc) -> TypeAliasId;
    #[salsa::interned] fn intern_impl(self, loc: ImplLoc) -> ImplId;
}
```

This approach is closest to rust-analyzer's `impl_intern_key!` macro pattern but uses a generic `ItemLoc<N>` to avoid duplicating the location struct definition for each item type. BAML's type-alias re-export pattern (`FunctionLoc as FunctionId`) is more approachable; Mun's macro approach is more scalable when you need `Intern`/`Lookup` trait impls.

Mun also defines a union enum for heterogeneous item collections:
```rust
pub enum ItemDefinitionId {
    ModuleId(ModuleId),
    FunctionId(FunctionId),
    StructId(StructId),
    TypeAliasId(TypeAliasId),
    PrimitiveType(PrimitiveType),
}
```

This serves the same purpose as BAML's `ItemId` enum — a type-safe container for mixed item references.

## django-language-server: "All Four Struct Types in 78 Files"

django-language-server (a Django template LSP) is the simplest complete example of all four struct types working together in a real project:

```rust
// Inputs — external data entering the system
#[salsa::input]
pub struct File {
    #[returns(ref)]
    pub path: Utf8PathBuf,
    pub revision: u64,            // Bumped to invalidate cached queries
}

#[salsa::input]
pub struct Project {
    #[returns(ref)]
    pub root: Utf8PathBuf,
    #[returns(ref)]
    pub interpreter: Interpreter,
    // ...
}

// Interned — template name deduplication for fast equality
#[salsa::interned]
pub struct TemplateName {
    #[returns(ref)]
    pub name: String,
}

// Tracked — intermediate entities with field-level tracking
#[salsa::tracked]
pub struct Template<'db> {
    pub name: TemplateName<'db>,  // Interned field for identity
    pub file: File,               // Input field linking to source
}

#[salsa::tracked]
pub struct Tag<'db> {
    #[returns(ref)]
    pub name: String,
    #[returns(ref)]
    pub arguments: Vec<String>,
    pub span: Span,
}

#[salsa::tracked(debug)]
pub struct NodeList<'db> {
    #[tracked]
    #[returns(ref)]
    pub nodelist: Vec<Node>,      // Vec of PLAIN Rust types
}

// Plain Rust — too fine-grained to track individually
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Node {
    Tag { name: String, bits: Vec<String>, span: Span },
    Comment { content: String, span: Span },
    Text { span: Span },
    Variable { var: String, filters: Vec<String>, span: Span },
    Error { span: Span, full_span: Span, error: ParseError },
}
```

This project demonstrates the classic granularity choice: `NodeList` is a tracked struct, but the `Node` entries inside it are plain Rust enums. Changes to any node invalidate the entire `nodelist` field — the tracking boundary is at the file level, not the node level. This is exactly the "reasonably coarse" approach that works well for small-to-medium projects.

Total: 2 inputs, 1 interned, ~7 tracked structs, ~12 tracked functions, plus plain Rust types for AST nodes.

For full code references, see [djls-patterns.md](djls-patterns.md).

## Fe: "Workspace-as-Container Input" and "Interned Collections"

Fe makes two distinctive struct choices not seen in other surveyed projects:

**1. Single input containing all files** — Instead of individual `File` inputs looked up via a side-table (`DashMap` in ty, `HashMap` in BAML), Fe puts the entire file collection inside one `Workspace` input using an immutable trie:

```rust
#[salsa::input]
pub struct Workspace {
    files: StringTrie<Url, File>,   // URL → File mapping (immutable trie)
    paths: IndexMap<File, Url>,     // Reverse lookup
}

// Adding a file replaces the entire trie
pub fn set(&self, db: &mut dyn InputDb, url: Url, file: File) {
    let files = self.files(db);
    self.set_files(db).to(files.insert(url.clone(), file));  // New trie version
}
```

Individual `File` inputs exist but are minimal — just `text`:
```rust
#[salsa::input]
pub struct File {
    #[return_ref]
    pub text: String,
}
```

**Trade-off:** Adding/removing any file invalidates all queries that read the workspace file list (e.g., "what files are in this ingot?"). But individual `File.text` queries are unaffected — editing a file's content only invalidates text-dependent queries, not workspace-structure queries. This is the inverse of ty's pattern where the `DashMap` side-table is outside Salsa entirely.

**When to use which:**
| Approach | File structure changes | File content changes | Concurrency |
|----------|----------------------|---------------------|-------------|
| Container input (Fe) | Invalidates workspace queries | Isolated to File | Single-writer (needs `&mut db`) |
| Side-table + individual inputs (ty) | Outside Salsa, manual | Isolated to File | Concurrent reads via `DashMap` |

**2. Interned collection types** — Fe systematically interns `Vec<T>` containers as separate interned structs, not just individual values:

```rust
#[salsa::interned]
pub struct AttrListId<'db> {
    #[return_ref]
    pub data: Vec<Attr<'db>>,
}

#[salsa::interned]
pub struct GenericArgListId<'db> {
    #[return_ref]
    pub data: Vec<GenericArg<'db>>,
    pub is_given: bool,
}

#[salsa::interned]
pub struct FuncParamListId<'db> {
    #[return_ref]
    pub data: Vec<FuncParam<'db>>,
}
// ... 10+ more collection types (FieldDefListId, VariantDefListId, WhereClauseId, etc.)
```

This gives structural sharing: two functions with identical parameter lists get the same `FuncParamListId`. It also makes these collections cheap to pass around (`Copy` integer IDs) while providing `#[return_ref]` access to the underlying `Vec`. This is distinct from ty's approach (which interns individual types like `UnionType`, not their containers) and rust-analyzer's approach (which interns definition locations, not collections).

For more, see [fe-patterns.md](fe-patterns.md).

## Cairo: "Macro-Generated Interned IDs at Scale"

Cairo (the StarkNet smart contract language compiler) interns 38+ definition types via a `define_short_id!` macro that generates `#[salsa::interned]` structs:

```rust
// One-liner generates the interned struct + Intern/Debug impls
define_short_id!(FunctionId, FunctionLongId<'db>);
define_short_id!(StructId, StructLongId<'db>);
define_short_id!(TypeId, TypeLongId<'db>);
// ... 35+ more
```

The macro expands to:
```rust
#[salsa::interned(revisions = usize::MAX)]
pub struct FunctionId<'db> {
    #[returns(ref)]
    pub long: FunctionLongId<'db>,
}
```

**Key detail: `revisions = usize::MAX`** — This disables Salsa's interned value garbage collection, making IDs immortal. Cairo needs this because interned IDs are stored in serialized cache files and must survive across revisions. Without it, IDs could be recycled by GC and refer to wrong data.

**When to use `revisions = usize::MAX`:**
- IDs are stored outside Salsa (serialized caches, external data structures)
- The program is short-lived (compiler, not LSP) so GC isn't needed
- ID stability across revisions is required for correctness

**When NOT to use it:**
- Long-running processes (LSP servers) where memory growth matters
- Values that are truly ephemeral and should be reclaimed

Cairo also uses 127+ tracked functions (not tracked structs for types) and has no accumulators — diagnostics flow through return values. This is a third real-world strategy distinct from ty's "all interned" and rust-analyzer's "intern + tracked" approaches.

For more, see [cairo-patterns.md](cairo-patterns.md).
