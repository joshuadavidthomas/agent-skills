# Mun LSP & Hot-Reload Patterns [Legacy API/Architecture]

Mun uses Salsa 2018 (v0.16.1). Use for **architectural insights** — adapt to modern Salsa syntax.

## Analysis/AnalysisSnapshot Pattern

Mun's LSP follows the same pattern as rust-analyzer: a mutable `Analysis` struct on the main thread, immutable `AnalysisSnapshot` values for worker threads.

### Analysis (Host)

```rust
// mun_language_server/src/analysis.rs
pub struct Analysis {
    db: AnalysisDatabase,
}

impl Analysis {
    pub fn apply_change(&mut self, change: AnalysisChange) {
        self.db.apply_change(change);
    }

    pub fn snapshot(&self) -> AnalysisSnapshot {
        AnalysisSnapshot { db: self.db.snapshot() }
    }

    pub fn request_cancelation(&mut self) {
        self.db.request_cancelation();
    }
}
```

### AnalysisSnapshot (Worker)

```rust
pub struct AnalysisSnapshot {
    db: Snapshot<AnalysisDatabase>,
}

impl AnalysisSnapshot {
    pub fn parse(&self, file_id: FileId) -> Cancelable<SourceFile> {
        self.with_db(|db| db.parse(file_id).tree())
    }

    pub fn diagnostics(&self, file_id: FileId) -> Cancelable<Vec<Diagnostic>> {
        self.with_db(|db| diagnostics::diagnostics(db, file_id))
    }

    fn with_db<F: FnOnce(&AnalysisDatabase) -> T + UnwindSafe, T>(
        &self, f: F,
    ) -> Cancelable<T> {
        self.db.catch_canceled(f)
    }
}

pub type Cancelable<T> = Result<T, Canceled>;
```

Every public method on `AnalysisSnapshot` returns `Cancelable<T>` — if the database is cancelled mid-query, the error propagates cleanly.

## LanguageServerState — Full LSP Architecture

```rust
// mun_language_server/src/state.rs
pub(crate) struct LanguageServerState {
    pub sender: Sender<lsp_server::Message>,
    pub request_queue: ReqQueue<(String, Instant), RequestHandler>,
    pub config: Config,
    pub thread_pool: threadpool::ThreadPool,
    pub task_sender: Sender<Task>,
    pub task_receiver: Receiver<Task>,
    pub vfs: Arc<RwLock<VirtualFileSystem>>,
    pub vfs_monitor: Box<dyn mun_vfs::Monitor>,
    pub vfs_monitor_receiver: Receiver<mun_vfs::MonitorMessage>,
    pub open_docs: FxHashSet<AbsPathBuf>,
    pub analysis: Analysis,
    pub packages: Arc<Vec<mun_project::Package>>,
    pub shutdown_requested: bool,
}

pub(crate) struct LanguageServerSnapshot {
    pub vfs: Arc<RwLock<VirtualFileSystem>>,
    pub analysis: AnalysisSnapshot,
    pub packages: Arc<Vec<mun_project::Package>>,
}
```

### Event Loop

The main loop multiplexes three event sources:

```rust
fn next_event(&self, receiver: &Receiver<lsp_server::Message>) -> Option<Event> {
    select! {
        recv(receiver) -> msg => msg.ok().map(Event::Lsp),
        recv(self.vfs_monitor_receiver) -> task => Some(Event::Vfs(task.unwrap())),
        recv(self.task_receiver) -> task => Some(Event::Task(task.unwrap()))
    }
}
```

After processing events, diagnostics are computed on the thread pool:

```rust
fn handle_event(&mut self, event: Event) -> anyhow::Result<()> {
    // Process event...
    let state_changed = self.process_vfs_changes();
    if state_changed {
        let snapshot = self.snapshot();
        let task_sender = self.task_sender.clone();
        self.thread_pool.execute(move || {
            let _result = handle_diagnostics(snapshot, task_sender);
        });
    }
    Ok(())
}
```

### VFS→Salsa Bridge

The `process_vfs_changes()` method converts VFS changes to Salsa input mutations:

```rust
pub fn process_vfs_changes(&mut self) -> bool {
    let changed_files = {
        let mut vfs = self.vfs.write();
        vfs.take_changes()
    };
    if changed_files.is_empty() { return false; }

    let vfs = self.vfs.read();
    let mut analysis_change = AnalysisChange::new();
    let mut has_created_or_deleted = false;

    for file in changed_files {
        if file.is_created_or_deleted() {
            has_created_or_deleted = true;
        }
        let bytes = vfs.file_contents(file.file_id)
            .map(Vec::from).unwrap_or_default();
        let text = String::from_utf8(bytes).ok().map(Arc::from);
        analysis_change.change_file(FileId(file.file_id.0), text);
    }

    if has_created_or_deleted {
        analysis_change.set_roots(self.recompute_source_roots());
    }

    self.analysis.apply_change(analysis_change);
    true
}
```

### Graceful Shutdown

```rust
impl Drop for LanguageServerState {
    fn drop(&mut self) {
        self.analysis.request_cancelation();
        self.thread_pool.join();
    }
}
```

## AnalysisChange — Atomic Change Batching

```rust
// mun_language_server/src/change.rs
pub struct AnalysisChange {
    packages: Option<PackageSet>,
    roots: Option<Vec<SourceRoot>>,
    files_changed: Vec<(FileId, Option<Arc<str>>)>,
}

impl AnalysisDatabase {
    pub(crate) fn apply_change(&mut self, change: AnalysisChange) {
        if let Some(package_set) = change.packages {
            self.set_packages(Arc::new(package_set));
        }
        if let Some(roots) = change.roots {
            for (idx, root) in roots.into_iter().enumerate() {
                let root_id = SourceRootId(idx as u32);
                for file_id in root.files() {
                    self.set_file_source_root(file_id, root_id);
                }
                self.set_source_root(root_id, Arc::new(root));
            }
        }
        for (file_id, text) in change.files_changed {
            let text = text.unwrap_or_else(|| Arc::from("".to_owned()));
            self.set_file_text(file_id, text);
        }
    }
}
```

## Custom VFS Implementation

Mun has its own lightweight VFS (`mun_vfs`), simpler than rust-analyzer's:

```rust
// mun_vfs/src/lib.rs
pub struct VirtualFileSystem {
    interner: PathInterner,              // path ↔ FileId mapping
    file_contents: Vec<Option<Vec<u8>>>, // indexed by FileId
    changes: Vec<ChangedFile>,           // change log
}

pub struct ChangedFile {
    pub file_id: FileId,
    pub kind: ChangeKind,
}

pub enum ChangeKind { Create, Modify, Delete }
```

The VFS tracks changes since the last `take_changes()` call. The LSP state reads these changes and converts them to Salsa input mutations.

## Compiler Daemon: File-Watching Hot Reload

Separate from the LSP, Mun's compiler daemon watches source files and incrementally rebuilds changed modules. It uses the `CompilerDatabase` (with LLVM codegen queries) instead of `AnalysisDatabase`:

```rust
// mun_compiler_daemon/src/lib.rs
pub fn compile_and_watch_manifest(
    manifest_path: &Path, config: Config, display_color: DisplayColor,
) -> Result<bool, anyhow::Error> {
    let (package, mut driver) = Driver::with_package_path(manifest_path, config)?;

    let (watcher_tx, watcher_rx) = channel();
    let mut watcher: RecommendedWatcher = Watcher::new(watcher_tx, Duration::from_millis(10))?;
    watcher.watch(&source_directory, RecursiveMode::Recursive)?;

    // Initial compile
    if !driver.emit_diagnostics(&mut stderr(), display_color)? {
        driver.write_all_assemblies(false)?;
    }

    // Watch loop — single-threaded, no snapshots needed
    while !should_quit.load(Ordering::SeqCst) {
        if let Ok(event) = watcher_rx.recv_timeout(Duration::from_millis(1)) {
            match event {
                Write(path) => { driver.update_file(path, contents); }
                Create(path) => { driver.add_file(path, contents); }
                Remove(path) => { driver.remove_file(path); }
                Rename(from, to) => { driver.rename(from, to); }
                _ => {}
            }
            // Re-check diagnostics and rebuild only changed assemblies
            if !driver.emit_diagnostics(&mut stderr(), display_color)? {
                driver.write_all_assemblies(false)?;
            }
        }
    }
    Ok(true)
}
```

The daemon is single-threaded: filesystem event → update Salsa input → diagnostics check → write only changed assemblies. No snapshots, no cancellation, no thread pool. This simplicity works because the daemon doesn't need to serve concurrent client requests.

### Assembly Change Tracking

The Driver tracks `module_to_temp_assembly_path` to avoid writing assemblies that haven't changed. Salsa's memoization means `target_assembly()` returns the same `NamedTempFile` pointer if nothing upstream changed — the Driver compares this pointer to the last written path and skips the copy if identical.

### Filesystem Lock for Hot Reload

The Mun runtime watches the output directory for changed `.munlib` files. To prevent the runtime from reading half-written files, the Driver acquires a filesystem lock (`lockfile::Lockfile`) on the output directory during writes.
