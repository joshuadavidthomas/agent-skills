
# Structuring the Salsa Database

The database is the central struct in any Salsa application. It holds the `salsa::Storage` plus whatever additional state your application needs. The key design challenge is layering: how to compose domain-specific query groups into a clean hierarchy, and how to handle the divergent needs of test vs production environments.

## The Minimal Database

Every Salsa database follows this pattern:

```rust
#[salsa::db]
#[derive(Clone)]
struct MyDatabase {
    storage: salsa::Storage<Self>,
    // additional non-Salsa fields go here
}

#[salsa::db]
impl salsa::Database for MyDatabase {}
```

The `#[salsa::db]` macro generates the plumbing. The `storage` field is mandatory. You can add any number of additional fields — these live outside Salsa's tracking system.

## The Layered Trait Pattern

Both major Salsa projects build their database as a stack of traits, each adding a domain of functionality. Each layer declares a supertrait bound on the previous:

```
Ruff/ty (4 layers):              rust-analyzer (6 layers):       BAML (6 layers):             django-ls (5 layers):        Fe (6+ layers):
  Db (files) [ruff_db]             SourceDatabase (files)          workspace::Db (files)        SourceDb (files)             InputDb (files)
    → ModuleResolverDb [ty]          → RootQueryDb (parsing)         → hir::Db (names)            ├── WorkspaceDb (fs)         └── HirDb (hir items)
      → SemanticDb [ty]                → ExpandDatabase (macros)       → tir::Db (types)            └── TemplateDb (parse)           ├── LowerHirDb (lowering)
        → ProjectDb [ty]                 → InternDatabase (IDs)          → vir::Db (validation)           └── SemanticDb (analysis)   ├── SpannedHirDb (spans)
          → [LSP Db] [ty]                  → DefDatabase (names)           → mir::Db (lowering)     ProjectDb (config)               └── HirAnalysisDb (types)
                                             → HirDatabase (types)                                                                       → LanguageServerDb
```

Each layer is a trait with a supertrait bound:

```rust
// Layer 1: Base — file system access
#[salsa::db]
pub trait Db: salsa::Database {
    fn system(&self) -> &dyn System;
    fn files(&self) -> &Files;
}

// Layer 2: Module resolution — builds on base
#[salsa::db]
pub trait ModuleResolverDb: Db {
    fn search_paths(&self) -> &SearchPaths;
}

// Layer 3: Semantic analysis — builds on module resolution
#[salsa::db]
pub trait SemanticDb: ModuleResolverDb {
    fn rule_selection(&self, file: File) -> &RuleSelection;
    fn lint_registry(&self) -> &LintRegistry;
}
```

**Why traits?** Each crate defines its own trait with just the methods it needs. This avoids a "god object" database and keeps crate boundaries clean. Tracked functions take `&dyn SomeDb` as their first argument and only see the methods from that layer and below.

### Alternative: Blanket-Implemented Group Traits (Cairo)

Cairo blanket-implements all group traits for `Database`, eliminating explicit trait impls for test databases. See [references/cairo-patterns.md](references/database-architecture/cairo-patterns.md) for full Cairo code examples.

### Marker Traits for Compilation Phase Enforcement (Fe)

Fe uses **marker traits** (traits with no methods) to enforce compilation phase boundaries. This prevents span-dependent code from contaminating cacheable analysis. See [references/fe-patterns.md](references/database-architecture/fe-patterns.md) for implementation details.

### Database Boilerplate Macros (Fe)

Fe reduces database boilerplate with helper macros instead of Cairo's blanket-impl approach. See [references/fe-patterns.md](references/database-architecture/fe-patterns.md) for macro definitions.

## How Many Layers? How Many Concrete Databases?

### Trait Layers: One Per Domain, Aligned with Crate Boundaries

Every surveyed project has 4-8 trait layers:

| Project | Layers | Principle |
|---------|--------|-----------|
| ty / ruff shared | 4 | files → module resolution → semantics → project config |
| rust-analyzer | 6 | files → parsing → macros → interning → definitions → types |
| Cairo | 8 | filesystem → syntax → parser → defs → doc → semantic → lowering → codegen |
| Mun [Legacy] | 6 | files → parsing → interning → definitions → type inference → codegen (LLVM) |
| BAML | 6 | files → HIR → types → validation → MIR |
| Fe | 6+ | files → HIR → {lowering, spans, analysis} → LSP |
| django-language-server | 5 | files → {workspace, templates → semantics}, config |
| wgsl-analyzer [Legacy] | 4 | files → {interning, definitions} → type inference |

The pattern is consistent: **one trait per domain boundary, typically one trait per crate.**

### When to Create a New Trait Layer

Create a new `#[salsa::db]` trait when **any** of these are true:

1. **New crate boundary.** If you're creating a new crate that defines tracked functions, it needs its own Db trait. This is the most common reason — the trait is the crate's "database API surface." Tracked functions in that crate take `&dyn YourDb` and only see what that trait (and its supertraits) expose.

2. **New non-Salsa state.** If a domain needs access to something outside Salsa (a filesystem abstraction, a Python subprocess, a tag spec registry), that access goes in a trait method. A new kind of non-Salsa state usually means a new trait.

3. **Restricting what code can see.** Marker traits (Fe's `LowerHirDb` vs `SpannedHirDb`) exist purely to control which functions can access span-dependent data. The trait carries no methods — it's a compilation-phase boundary.

4. **Different test granularity.** Each trait layer can have its own test database that implements only the layers below it. If you want to test parsing without standing up the type checker, parsing needs its own trait.

### When NOT to Create a New Trait Layer

**"I have more tracked functions"** → Add them to the existing trait's crate. More functions don't require a new layer. ty has 200+ tracked functions across just 4 trait layers.

**"I want to group related queries"** → Use modules within the crate. Trait layers are about crate boundaries and dependency direction, not code organization.

**"My trait has no methods"** → That might be fine (djls's `TemplateDb` is an empty marker). But if the empty trait doesn't serve as a crate boundary or a test isolation point, you probably don't need it.

### Concrete Databases: 1 Production + N Test

Every project has exactly **one production database** — the concrete struct at the top of the trait stack that implements all layers. Test databases are more variable:

| Project | Production | Test DBs | Pattern |
|---------|-----------|----------|---------|
| ty | `ProjectDatabase` | 3-4 | One per testable layer (ruff_db, module resolver, semantic) |
| rust-analyzer | `RootDatabase` | 2-3 | One per major test suite (hir-def, hir-ty) |
| Cairo | `RootDatabase` | Per-crate | `define_input_db!`-like setup in each crate's tests |
| BAML | `ProjectDatabase` | 3 | One per compilation phase (workspace, bytecode, emit) |
| Fe | `DriverDataBase` | Per-crate | `define_input_db!(TestDatabase)` in each crate's tests |
| django-language-server | `DjangoDatabase` | 1 + bench | Shared test DB + minimal benchmark DB |
| Mun [Legacy] | `CompilerDatabase` + `AnalysisDatabase` | 2 | One per major layer (hir, codegen) |
| wgsl-analyzer [Legacy] | `RootDatabase` | 2 | One per major layer (hir-def, hir-ty) |

**The litmus test for a test database:** Can you meaningfully test this layer's tracked functions without standing up the layers above it? If yes, a dedicated test database that implements only the lower layers saves setup complexity and makes tests faster.

### The Dependency Direction Rule

Trait layers form a DAG — each layer depends on the ones below it, never above. This mirrors the crate dependency graph:

```
ProjectDb → SemanticDb → TemplateDb → SourceDb → salsa::Database
    ↑            ↑            ↑            ↑
  djls-project  djls-semantic djls-templates djls-source
```

If you find yourself wanting a lower layer to call into a higher layer, that's a design smell. Either:
- Move the shared logic down to the lower layer
- Create a new intermediate layer
- Use a callback/trait object passed through non-Salsa state

## Non-Salsa State on the Database

Both projects store significant state outside Salsa's tracking system as regular struct fields. This is intentional — not everything benefits from incremental tracking.

### What Goes Outside Salsa

| Pattern | Example | Why Outside |
|---------|---------|-------------|
| File lookup tables | `Files` (DashMap) | On-demand creation with concurrent access |
| System abstraction | `dyn System`, `Arc<dyn FileSystem>` | OS I/O, not a computed value |
| Vendored files | `VendoredFileSystem` | Immutable, bundled data |
| Event capture | `Arc<Mutex<Vec<Event>>>` | Testing infrastructure |
| Crate metadata | `Arc<CratesMap>` | Bulk-updated, not per-field tracked |
| Project state | `Arc<Mutex<Option<Project>>>` | Mutable singleton, set at startup |
| Configuration | `Arc<Mutex<Settings>>` | Updated from LSP notifications |
| Python inspector | `Arc<Inspector>` | Subprocess communication, not a computation |
| External library state | `Arc<Shared>` (source maps, globals) | [Legacy: stc] Bundled non-Salsa state from external libraries, exposed via `Db` trait method |
| LLVM target machine | `ByAddress<Rc<TargetMachine>>` | [Legacy: Mun] Thread-unsafe LLVM state returned from a query, confined to single-threaded codegen layer |
| Reused VFS | `Arc<RwLock<vfs::Vfs>>` | [Legacy: wgsl-analyzer] Imported rust-analyzer's VFS crate as a git dependency for file ID allocation + change tracking |

### The Files Side-Table Pattern

The most important non-Salsa pattern. Both projects use a concurrent hash map to intern files on demand, creating Salsa input structs lazily with appropriate durability.

**Why a side table?** Salsa inputs can't be looked up by value — you need to already have the ID. A `DashMap` provides the path → ID lookup that Salsa doesn't natively offer. See [references/ty-patterns.md](references/database-architecture/ty-patterns.md) for the complete implementation from the Ruff/ty shared infrastructure.

## Singleton Input Pattern

Global configuration that applies across the entire computation should be a singleton Salsa input. This is initialized during database construction and updated via setters when configuration changes.

### Alternative: Input-Behind-Tracked-Function (Cairo)

Cairo uses a different singleton pattern — an input struct with `Option<T>` fields behind a tracked function, with per-layer `init_*_group()` functions. See [references/cairo-patterns.md](references/database-architecture/cairo-patterns.md) for implementation.

## Two Production Databases from One Trait Stack (Mun) [Legacy API/Architecture]

Mun has two separate concrete databases — `CompilerDatabase` (6 query groups including codegen) and `AnalysisDatabase` (5 query groups, no codegen) — built from the same trait hierarchy. The compiler includes LLVM codegen queries; the LSP excludes them. This pattern emerges when your tool has distinct deployment modes with different dependency weight:

- **CompilerDatabase** — CLI compiler and daemon, includes `CodeGenDatabaseStorage` for LLVM. Not `ParallelDatabase` (codegen is single-threaded with `Rc`).
- **AnalysisDatabase** — LSP server, implements `ParallelDatabase` for snapshot concurrency. Excludes codegen (no LLVM dependency in the LSP binary).

Both share `SourceDatabaseStorage`, `AstDatabaseStorage`, `InternDatabaseStorage`, `DefDatabaseStorage`, and `HirDatabaseStorage`. See [references/mun-patterns.md](references/database-architecture/mun-patterns.md) for details.

## CloneableDatabase: Parallel Compilation via Rayon (Cairo)

Cairo defines a `CloneableDatabase` trait for `dyn Database` cloning with Rayon parallel iteration. This enables parallel diagnostic warmup and function compilation without the complexity of snapshots. See [references/cairo-patterns.md](references/database-architecture/cairo-patterns.md) for details.

## Test Databases

Test databases require event capture to verify incremental behavior. They typically include an in-memory filesystem and a way to collect `salsa::Event`s.

### High-Level Patterns

- **Event Capture**: Use a `Mutex<Vec<salsa::Event>>` in a callback passed to `salsa::Storage::new`.
- **Test Builder**: Use a builder to set up files and initial state.
- **Layer Implementation**: A test database at layer N must implement every trait from layer 1 through N.

For complete test database implementations, see:
- [references/ty-patterns.md](references/database-architecture/ty-patterns.md) — Shared test infrastructure with `DbWithTestSystem`.
- [references/rust-analyzer-patterns.md](references/database-architecture/rust-analyzer-patterns.md) — Targeted event logging with `log()` and `log_executed()`.
- [references/cairo-patterns.md](references/database-architecture/cairo-patterns.md) — Minimal boilerplate via blanket-impl traits.
- [references/baml-patterns.md](references/database-architecture/baml-patterns.md) — The boilerplate challenge (6 impl blocks per test DB).

## Production Databases

Production databases differ from test databases in performance tuning and state management.

### Key Production Patterns

- **Conditional Logging**: Only log events when a specific tracing level is enabled.
- **Field Ordering**: Put the `storage` field last if you need mutable access to other `Arc` fields after cancellation.
- **Compile-Time Optimization**: Use `ManuallyDrop` to reduce vtable drop glue bloat (rust-analyzer).
- **Snapshot Isolation**: Use a `Nonce` to distinguish database instances across revisions.
- **Two-Phase Initialization**: Construct the database with placeholders, then initialize singletons that require `&dyn Db`.

For production implementation details, see:
- [references/ty-patterns.md](references/database-architecture/ty-patterns.md) — `ProjectDatabase` with the `storage`-last trick and conditional logging.
- [references/rust-analyzer-patterns.md](references/database-architecture/rust-analyzer-patterns.md) — `RootDatabase` with `ManuallyDrop` and the `Nonce` pattern.
- [references/djls-patterns.md](references/database-architecture/djls-patterns.md) — `DjangoDatabase` settings update pattern.

## Common Mistakes

**Too many or too few trait layers.** Every surveyed project has 4-8 layers, each aligned with a crate boundary. If you have 12+, you're over-separating — use modules within a crate instead.

**Creating trait layers for code organization instead of dependency boundaries.** Trait layers exist to control what tracked functions can see and to define crate APIs.

**Putting query logic in trait methods.** Trait methods should return references to non-Salsa state. Computation goes in tracked functions.

**Capturing all events in production.** Event callbacks run on every query check. Use `None` or gate behind a tracing level check.

**Creating Salsa inputs eagerly.** Use the Files side-table pattern — create inputs on demand with the right durability.

**Storing `Arc` fields before `storage` when using the mutation trick.** If you call `trigger_cancellation()` to get exclusive `Arc` access, `storage` must be declared last so it drops last.

### Approachable Example: django-language-server

django-language-server shows the full layered pattern at a more accessible scale (~78 Rust files). It uses a 5-layer trait hierarchy and an overlay file system. See [references/djls-patterns.md](references/database-architecture/djls-patterns.md) for the full architecture.

For full production code examples, see the references directory.
