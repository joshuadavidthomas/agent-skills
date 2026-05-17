# wgsl-analyzer LSP Integration Patterns [Legacy API/Architecture]

> **API Version**: Salsa 0.17.0-pre.2 (legacy query groups). Do NOT model modern code on these macros/traits.
> Use for **architectural insights** only — the patterns are version-agnostic.
>
> **Repository**: https://github.com/aspect-build/aspect-analyzer (wgsl-analyzer)

wgsl-analyzer is a WebGPU Shading Language LSP built on Salsa. It closely follows
rust-analyzer's LSP architecture but for a simpler domain (no macros, no build scripts,
no proc macros), making it the cleanest reference for the "full rust-analyzer LSP pattern"
without rust-analyzer's complexity.

## VFS Reuse: Importing rust-analyzer's VFS Directly

**Key architectural decision**: wgsl-analyzer does NOT build its own Virtual File System.
It imports the `vfs` crate directly from rust-analyzer as a git dependency:

```toml
# wgsl-analyzer/Cargo.toml
vfs = { git = "https://github.com/rust-lang/rust-analyzer", rev = "a31e10a..." }
```

This gives it:
- `vfs::Vfs` — In-memory file store with `FileId` allocation and change tracking
- `vfs::FileId` — Integer file identifier (used as Salsa input key)
- `vfs::VfsPath` — Abstraction over real and virtual file paths
- `vfs::loader::Handle` trait — Pluggable file loading/watching backend
- `vfs::file_set::FileSet` — Groups files into source roots

The `vfs-notify` crate bridges the `notify` file watcher to VFS changes, running
on a dedicated worker thread.

**Takeaway for new projects**: If your language server needs a VFS, consider
reusing rust-analyzer's implementation rather than building from scratch. It handles
edge cases (path normalization, change deduplication, file exclusion) that are
non-trivial to get right.

## GlobalState / GlobalStateSnapshot Split

The server has two key structs, defined in the main `wgsl-analyzer` crate:

**`GlobalState`** (mutable, main thread):
```
GlobalState
├── analysis_host: AnalysisHost          // Owns the mutable Salsa database
├── vfs: Arc<RwLock<(Vfs, LineEndings)>> // Shared VFS (main thread writes, snapshots read)
├── loader: NotifyHandle + Receiver      // File watcher
├── task_pool: TaskPool<Task>            // Worker thread pool for async requests
├── fmt_pool: TaskPool<Task>             // Separate pool for formatting (never blocks)
├── diagnostics: DiagnosticCollection    // Aggregated diagnostic state
├── in_memory_documents: InMemoryDocuments // Editor-open documents
├── config: Arc<Config>                  // Server configuration
├── source_root_config: SourceRootConfig // Source root partitioning
├── workspaces: Arc<[ProjectWorkspace]>  // Discovered workspaces
├── request_queue: RequestQueue          // Pending LSP requests
├── deferred_task_queue: TaskQueue       // Database-dependent work deferred from sync handlers
└── (operation queues for fetch/prime)
```

**`GlobalStateSnapshot`** (immutable, worker threads):
```
GlobalStateSnapshot
├── analysis: Analysis                   // Salsa snapshot (cloned database)
├── config: Arc<Config>                  // Shared config
├── in_memory_documents: InMemoryDocuments
├── vfs: Arc<RwLock<(Vfs, LineEndings)>> // Read-only access to VFS
└── workspaces: Arc<[ProjectWorkspace]>
```

## AnalysisHost / Analysis Split

The `ide` crate wraps the Salsa database in a host/analysis pair:

```
AnalysisHost                    Analysis
├── database: RootDatabase      ├── database: salsa::Snapshot<RootDatabase>
│                               │
│ fn analysis() → Analysis      │ fn with_db<F>(f: F) → Cancellable<T>
│ fn apply_change(Change)       │   // Wraps f in Cancelled::catch
│                               │
│ fn update_lru_capacity(...)   │ fn diagnostics(...) → Cancellable<Vec<Diagnostic>>
│ fn update_lru_capacities(...) │ fn completions(...) → Cancellable<Option<Vec<...>>>
│                               │ fn hover(...) → Cancellable<Option<HoverResult>>
└───────────────────────────────└── (all query methods return Cancellable<T>)
```

Every `Analysis` method follows the same pattern — wrapping the query in `Cancelled::catch`:

```rust
// wgsl-analyzer ide crate — every Analysis method looks like this
pub fn diagnostics(&self, config: &DiagnosticsConfig, file_id: FileId)
    -> Cancellable<Vec<Diagnostic>>
{
    self.with_db(|database| diagnostics::diagnostics(database, config, file_id))
}
```

## The Change Flow: VFS → Salsa Inputs

The `process_changes()` method on `GlobalState` is the bridge between the VFS and Salsa:

```
Editor notification (didChange/didOpen)
  └─→ Update VFS in-memory content
       └─→ VFS records changed FileIds

File watcher (vfs-notify)
  └─→ Reads file from disk
       └─→ VFS records changed FileIds

Main loop tick
  └─→ process_changes()
       ├── Lock VFS, take_changes() → list of changed FileIds
       ├── For each changed file:
       │   ├── Read content from VFS
       │   ├── Normalize line endings
       │   └── Build Change { file_id, text, path }
       ├── Partition VFS into source roots
       └── analysis_host.apply_change(change)
            └── Change::apply() sets Salsa inputs:
                ├── file_text(file_id) = text
                ├── file_path(file_id) = path
                ├── file_id(path) = file_id
                ├── file_source_root(file_id) = root_id  [Durability::LOW]
                └── source_root(root_id) = SourceRoot    [Durability::LOW]
```

The `Change` struct (defined in the `base_db` crate) batches all mutations before
applying them in a single pass:

```
Change
├── roots: Option<Vec<SourceRoot>>           // Source root reconfiguration
└── files_changed: Vec<(FileId, Option<Arc<String>>, VfsPath)>  // File content changes
```

## Request Dispatch and Cancellation

The `RequestDispatcher` routes LSP requests to handler functions with four dispatch modes:

| Mode | Thread | Use case |
|------|--------|----------|
| `on_sync_mut` | Main thread | State-mutating requests (needs `&mut GlobalState`) |
| `on_sync` | Main thread | Latency-sensitive reads (typing-related) |
| `on` | Worker pool | Normal async reads (diagnostics, completions, hover) |
| `on_fmt_thread` | Format pool | Formatting (separate pool, never blocks workers) |

The `on` method has a const-generic `ALLOW_RETRYING` flag:

```
on::<ALLOW_RETRYING=true, Request>(handler)
  └─→ Take snapshot of GlobalState
       └─→ Spawn on task pool:
            └─→ catch_unwind(|| handler(snapshot, params))
                 ├── Ok(result) → Task::Response(ok)
                 ├── Err(cancelled) if ALLOW_RETRYING → Task::Retry(request)
                 └── Err(cancelled) → Task::Response(content_modified_error)
```

When VFS loading is not complete (`!self.vfs_done`), requests return a default
empty result instead of queuing — this avoids blocking on an incomplete database.

## Diagnostic Collection

Diagnostics are split into three categories tracked independently in a
`DiagnosticCollection` struct:

```
DiagnosticCollection
├── native_syntax: Map<FileId, (Generation, Vec<Diagnostic>)>    // Parse errors
├── native_semantic: Map<FileId, (Generation, Vec<Diagnostic>)>  // Type errors
├── check: Map<FlyCheckId, Map<PackageId, Map<FileId, Vec<Diagnostic>>>>  // External tool
├── check_fixes: Map<FlyCheckId, Map<PackageId, Map<FileId, Vec<Fix>>>>
├── changes: Set<FileId>          // Files with updated diagnostics (pending publish)
└── generation: usize             // Monotonic counter for ordering concurrent updates
```

The generation counter prevents stale diagnostics from overwriting fresh ones when
multiple worker threads compute diagnostics for the same file concurrently.

Diagnostics are fetched on worker threads, collected into `DiagnosticsTaskKind::Syntax`
or `DiagnosticsTaskKind::Semantic`, then merged into the collection on the main thread.

## Database Hierarchy (4 Layers)

```
SourceDatabase (base_db)        — File text, paths, source roots, parse, line index
  └── InternDatabase (hir_def)  — 9 interned item locations (Function, Struct, etc.)
       └── DefDatabase (hir_def) — Item tree, body, signatures, scopes
            └── HirDatabase (hir_ty) — Type inference, interned types, builtins
```

The concrete `RootDatabase` (in `ide-db`) implements all four layers plus
`salsa::ParallelDatabase` for snapshot support.

## Source Root Partitioning

Files are grouped into `SourceRoot`s, each marked as either local (workspace)
or library (external dependency). The `FileLoader` trait resolves paths within
a source root — cross-root file references go through the `SourceDatabase` layer.

The `FileLoaderDelegate<T>` wrapper enables any `SourceDatabase` implementation
to resolve paths:

```
FileLoaderDelegate(&db).resolve_path(anchored_path)
  └── Look up file's source root
       └── Ask source root's FileSet to resolve the path
```

## Generic `Interned<T>` Wrapper

All interned IDs use `Location<T> = InFile<ModuleItemId<T>>` as the interned data —
the file + position where the item was defined, not the item's content. This mirrors
rust-analyzer's approach.

An `intern_id!` macro generates strongly-typed ID wrappers with a `Lookup` trait
for reverse lookups (ID → location):

```
intern_id!(FunctionId, Location<Function>, lookup_intern_function)
  → FunctionId(salsa::InternId)
  → impl Lookup for FunctionId { fn lookup(&self, db) → Location<Function> }
```

Additionally, a generic `Interned<T>` type with `PhantomData<T>` provides type-safe
wrapper semantics for arbitrary interned values.

## EditionedFileId: Language Variant Without Salsa

WGSL has multiple "editions" (like Rust editions). Rather than storing the edition
in a Salsa input, wgsl-analyzer derives it from the file extension at parse time:

```
EditionedFileId { file_id: FileId, edition: Edition }
  .wgsl → Edition::Wgsl
  .wesl → Edition::LATEST
  other → Edition::CURRENT
```

This avoids creating extra Salsa inputs for metadata that can be derived from
existing data.

## Test Database Pattern

Each layer has its own test database. The pattern is minimal:

```
TestDatabase
├── storage: salsa::Storage<Self>
├── impl Database
├── impl ParallelDatabase (snapshot support)
├── impl FileLoader (via FileLoaderDelegate)
└── fn apply_change(Change)     // Convenience method

single_file_db("source code")   // Creates TestDB with one file
  → (TestDatabase, FileId)       // Ready for queries
```

Two test databases exist:
- `hir_def` test DB — 3 storage groups (Source + Def + Intern)
- `hir_ty` test DB — 4 storage groups (Source + Def + Intern + Hir)

## Cycle Recovery

Two cycle recovery sites for type inference:

```
infer(db, DefinitionWithBodyId) → Arc<InferenceResult>
  cycle recovery: return InferenceResult with CyclicType diagnostic

infer_signature(db, ModuleDefinitionId) → Option<Arc<InferenceResult>>
  cycle recovery: return InferenceResult with CyclicType diagnostic
```

Both cycle recovery functions create a diagnostic describing the cycle rather than
returning a generic error, providing useful error messages to the user.

## Return-Value Diagnostics (No Accumulators)

Diagnostics are embedded in return values, not accumulators:

```
InferenceResult
├── type_of_expression: Map<ExpressionId, Type>
├── return_type: Type
└── diagnostics: Vec<InferenceDiagnostic>   ← diagnostics here

Module::diagnostics(db, config, accumulator)
  └── Walk all items in the module
       ├── For each struct: read field_types().1 (diagnostics)
       ├── For each type_alias: read type_alias_type().1 (diagnostics)
       └── For each definition: read infer().diagnostics
```
