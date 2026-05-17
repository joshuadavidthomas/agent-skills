
# Building an LSP Server Backed by Salsa

The core challenge of an LSP server is responsiveness under mutation: the user types while the server is computing diagnostics from the previous keystroke. Salsa solves this with the **host/snapshot** pattern — a mutable host applies changes on the main thread while immutable snapshots serve concurrent queries on worker threads.

## The Host/Snapshot Architecture

Every Salsa-backed LSP server has two roles:

- **Host** (main thread) — Owns `&mut Database`. Receives editor notifications, applies changes to Salsa inputs, triggers cancellation of stale queries.
- **Snapshots** (worker threads) — Own cloned `Database` instances (cheap, Arc-based). Execute read-only queries. Automatically cancelled when the host starts a new revision.

```rust
// Simplified host/snapshot flow
struct LspServer { db: MyDatabase }

impl LspServer {
    fn on_file_changed(&mut self, path: &Path, content: String) {
        // Setting any input calls zalsa_mut(), which:
        //   1. Sets cancellation flag
        //   2. Blocks until all snapshots are dropped
        //   3. Applies the change
        let file = self.resolve_file(&path);
        file.set_contents(&mut self.db).to(content);
    }

    fn snapshot(&self) -> MyDatabase { self.db.clone() }
}
```

Salsa's `Storage::cancel_others()` blocks the host until all snapshots unwind and drop. This guarantees no snapshot ever sees a partially-updated database.

## Change Flow: Editor → Salsa Inputs

The typical flow for handling editor changes:

1. **Classify the change** — content edit, file create/delete, config change.
2. **Update Salsa inputs** — set fields on input structs via setters.
3. **Trigger diagnostic refresh** — push (publishDiagnostics) or pull (diagnosticRefresh) diagnostics to client.

### Source Text Override Pattern
LSP servers must handle the divergence between disk content and editor content.
- When editor sends `didChange`: Set a `source_text_override` field on the `File` input.
- When file changes on disk (`didChangeWatchedFiles`): Clear the override and update the revision.
- `source_text(db, file)`: Checks override first, then falls back to disk.

See [references/ty-patterns.md](references/lsp-integration/ty-patterns.md) for the `ruff_db` implementation.

### Change Event Classification
Classify events (Created, Changed, Deleted, Rescan) before applying. Batch-applying changes (e.g., grouped by project root) avoids redundant work during large filesystem operations like `git checkout`.

See [references/ty-patterns.md](references/lsp-integration/ty-patterns.md) for classification enums.

### Deduplication
When applying batched changes, deduplicate file syncs to prevent multiple recomputations of the same file in a single revision.

## Session and Snapshot Management

### The Session Pattern
An LSP session holds the mutable Salsa database(s) and non-Salsa state (index, workspaces, request queue).

**Critical: Drop ordering.** Salsa's cancellation mechanism relies on `Arc` reference counting. Put the database field **last** in your session/snapshot structs. This ensures the database drops last, allowing Salsa's `cancel_others()` to unblock only after all other references (like shared indices) are dropped.

### Creating Snapshots
Snapshots capture a consistent view for background work by cloning the database and other shared state (`Arc` clones).

Detailed implementations:
- [references/ty-patterns.md](references/lsp-integration/ty-patterns.md) (per-project databases)
- [references/rust-analyzer-patterns.md](references/lsp-integration/rust-analyzer-patterns.md) (AnalysisHost/Analysis split)
- [references/djls-patterns.md](references/lsp-integration/djls-patterns.md) (Session/SessionSnapshot)

## Cancellation in LSP Context

### Retry Classification
When a query is cancelled, classify the error to decide the next action:

| Cancelled variant | Meaning | LSP action |
|-------------------|---------|------------|
| `PendingWrite` | User typed, data changed | Retry with fresh snapshot |
| `PropagatedPanic` | Blocked query's thread panicked | Retry (transient) |
| `Local` | Client sent `$/cancelRequest` | Return `RequestCanceled` error |

See [references/rust-analyzer-patterns.md](references/lsp-integration/rust-analyzer-patterns.md) for the dispatch handler implementation.

### Per-Request Cancellation Tokens
For client-initiated cancellation (`$/cancelRequest`), store a `CancellationToken` per request in the host. Calling `token.cancel()` triggers `Cancelled::Local` in the worker thread.

## Diagnostic Refresh Strategies

1. **Push diagnostics** — Server sends `textDocument/publishDiagnostics` after each change.
2. **Pull diagnostics** — Server sends `workspace/diagnosticRefresh` to tell the client to re-request diagnostics. More efficient for large projects.

## Background Worker Patterns

### Thread Pool with Snapshot Isolation
Each task in the thread pool receives its own cloned database (snapshot) and runs the query inside `panic::catch_unwind` or `salsa::Cancelled::catch`.

### Cache Priming
Background workers can prime caches (warming up name resolution, etc.) using parallel snapshots. Workers should call `db.unwind_if_revision_cancelled()` between work items to exit quickly when the user types.

See [references/rust-analyzer-patterns.md](references/lsp-integration/rust-analyzer-patterns.md) for parallel priming examples.

## Real-World Architectures

| Project | Approach | Concurrency |
|---------|----------|-------------|
| **rust-analyzer** | AnalysisHost/Analysis split | Thread pool, classification |
| **ty** | Session with per-project DBs | Thread pool, classify + retry |
| **wgsl-analyzer** [Legacy API] | GlobalState/GlobalStateSnapshot | Thread pool, const-generic retry |
| **djls** | Session/SessionSnapshot | Queue-based, revision bumps |
| **BAML** | Simple ProjectDatabase | Synchronous (no snapshots) |
| **Fe** | Workspace-input management | Single-threaded |
| **Mun** [Legacy API] | Analysis/AnalysisSnapshot + compiler daemon | Thread pool (LSP), single-threaded (daemon) |
| **stc** [Legacy API] | Dedicated thread + mpsc channel | Sequential on spawned thread |

- **Prototype**: Start with **BAML** or **Fe** (synchronous), or **stc**'s dedicated-thread approach [Legacy API] for full isolation of Salsa from async code.
- **Scale up**: Move to **djls** (snapshots) or **ty/rust-analyzer** (full concurrency).
- **Non-Rust domain**: **wgsl-analyzer** [Legacy API] validates the rust-analyzer AnalysisHost/Analysis pattern in a GPU shader language — proving the architecture is domain-portable, not Rust-specific.
- **Compiler daemon (hot reload)**: **Mun** [Legacy API] shows both an LSP server (Analysis/AnalysisSnapshot with `ParallelDatabase`) and a file-watching compiler daemon that incrementally rebuilds and writes only changed shared libraries. The daemon reuses Salsa's cache to skip LLVM codegen for unmodified modules.

## VFS Reuse: Build vs Import

A critical early decision is whether to build a custom Virtual File System or reuse an existing one.

**wgsl-analyzer** [Legacy API] imports rust-analyzer's `vfs` crate directly (as a git dependency), getting file ID allocation, change tracking, path abstraction, and file watching for free. This is viable when your domain has similar file-handling needs without Rust-specific complexity (macros, build scripts). See [references/wgsl-analyzer-patterns.md](references/lsp-integration/wgsl-analyzer-patterns.md) for the VFS→Salsa bridge flow.

**ty** builds its own `Files` side-table (a `DashMap`) with durability-aware file creation, which provides tighter Salsa integration at the cost of more code.

**Rule of thumb**: If your language doesn't need custom file representations (e.g., virtual files, overlays), start by reusing an existing VFS. Customize later if needed.

## Common Mistakes

- **Mutating outside Salsa without cancellation**: If you use non-Salsa state, ensure no snapshots are reading it during mutation.
- **Wrong drop order**: Putting the database field first in a snapshot struct causes deadlocks or `into_inner` failures.
- **Main thread blocking**: Executing queries on the main thread instead of worker threads causes UI lag.
- **Incorrect error codes**: Returning generic errors instead of `ContentModified` (-32801) prevents the client from retrying correctly.

## References
- [references/djls-patterns.md](references/lsp-integration/djls-patterns.md) — Simplest production example: Session/Snapshot, overlay FS, revision-based invalidation.
- [references/ty-patterns.md](references/lsp-integration/ty-patterns.md) — Session management, change application, file sync, source text overrides.
- [references/rust-analyzer-patterns.md](references/lsp-integration/rust-analyzer-patterns.md) — Host/Analysis split, dispatch handler, cache priming, cancellation tokens.
- [references/wgsl-analyzer-patterns.md](references/lsp-integration/wgsl-analyzer-patterns.md) — [Legacy API] VFS reuse from rust-analyzer, GlobalState/Snapshot split, process_changes() flow, const-generic retry dispatch, diagnostic generation tracking.
- [references/baml-patterns.md](references/lsp-integration/baml-patterns.md) — Minimum viable LSP: single-threaded, no snapshots.
- [references/fe-patterns.md](references/lsp-integration/fe-patterns.md) — Workspace-input management details.
- [references/mun-patterns.md](references/lsp-integration/mun-patterns.md) — **[Legacy API]** Mun's Analysis/AnalysisSnapshot LSP + compiler daemon hot-reload loop.
