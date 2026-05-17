# rust-analyzer LSP Integration Patterns

Production code from rust-analyzer showing how Salsa integrates with the IDE/LSP layer.

## The Host/Analysis Split

rust-analyzer uses a strict two-type separation between mutable and immutable database access:

```rust
// rust-analyzer/crates/ide/src/lib.rs

/// AnalysisHost stores the current state of the world.
pub struct AnalysisHost {
    db: RootDatabase,
}

impl AnalysisHost {
    /// Returns a snapshot of the current state for querying.
    pub fn analysis(&self) -> Analysis {
        Analysis { db: self.db.clone() }  // Cheap snapshot via Arc
    }

    /// Applies changes. If outstanding snapshots exist, they will be canceled.
    pub fn apply_change(&mut self, change: ChangeWithProcMacros) {
        self.db.apply_change(change);  // Triggers cancellation first
    }

    pub fn trigger_cancellation(&mut self) {
        self.db.trigger_cancellation();
    }
}

/// Analysis is an immutable snapshot. All methods return Cancellable<T>.
pub struct Analysis {
    db: RootDatabase,
}

pub type Cancellable<T> = Result<T, Cancelled>;
```

## The with_db Wrapper

Every public IDE operation is wrapped to handle cancellation transparently:

```rust
// rust-analyzer/crates/ide/src/lib.rs
impl Analysis {
    fn with_db<F, T>(&self, f: F) -> Cancellable<T>
    where
        F: FnOnce(&RootDatabase) -> T + std::panic::UnwindSafe,
    {
        hir::attach_db_allow_change(&self.db, || {
            Cancelled::catch(|| f(&self.db))
        })
    }

    // Every public API method follows the same pattern:
    pub fn file_text(&self, file_id: FileId) -> Cancellable<Arc<str>> {
        self.with_db(|db| SourceDatabase::file_text(db, file_id).text(db).clone())
    }

    pub fn parse(&self, file_id: FileId) -> Cancellable<SourceFile> {
        self.with_db(|db| {
            let editioned = EditionedFileId::current_edition_guess_origin(&self.db, file_id);
            db.parse(editioned).tree()
        })
    }

    pub fn diagnostics(&self, config: &DiagnosticsConfig, ...) -> Cancellable<Vec<Diagnostic>> {
        self.with_db(|db| diagnostics::diagnostics(db, config, ...))
    }

    // 100+ more methods, all using with_db
}
```

## Change Application with Cancellation

```rust
// rust-analyzer/crates/ide-db/src/apply_change.rs
impl RootDatabase {
    pub fn apply_change(&mut self, change: ChangeWithProcMacros) {
        let _p = tracing::info_span!("RootDatabase::apply_change").entered();
        self.trigger_cancellation();  // Cancel all in-flight queries FIRST
        tracing::trace!("apply_change {:?}", change);
        change.apply(self);           // Then apply changes to Salsa inputs
    }
}
```

The ordering is critical: cancel first, then apply. This ensures no snapshot sees a partially-updated database.

## RootDatabase Structure

```rust
// rust-analyzer/crates/ide-db/src/lib.rs
#[salsa_macros::db]
pub struct RootDatabase {
    // ManuallyDrop avoids massive compile-time bloat from vtable drop glue.
    // Every &RootDatabase → &dyn OtherDatabase cast instantiates drop in the
    // vtable, duplicating Arc::drop tens of thousands of times.
    storage: ManuallyDrop<salsa::Storage<Self>>,
    files: Arc<Files>,
    crates_map: Arc<CratesMap>,
    nonce: Nonce,
}

impl std::panic::RefUnwindSafe for RootDatabase {}

#[salsa_macros::db]
impl salsa::Database for RootDatabase {}

impl Drop for RootDatabase {
    fn drop(&mut self) {
        unsafe { ManuallyDrop::drop(&mut self.storage) };
    }
}

impl Clone for RootDatabase {
    fn clone(&self) -> Self {
        Self {
            storage: self.storage.clone(),    // Salsa storage clone (cheap)
            files: self.files.clone(),        // Arc clone
            crates_map: self.crates_map.clone(), // Arc clone
            nonce: Nonce::new(),              // Fresh nonce for snapshot
        }
    }
}
```

Key details:
- `ManuallyDrop` with explicit `Drop` impl is a compile-time optimization
- `RefUnwindSafe` is required because Salsa uses `resume_unwind` for cancellation
- Non-Salsa state (`files`, `crates_map`) is stored as `Arc` for cheap snapshot cloning
- Each snapshot gets a unique `Nonce` for debugging/tracking

## GlobalState and Snapshots

```rust
// rust-analyzer/crates/rust-analyzer/src/global_state.rs
pub(crate) struct GlobalStateSnapshot {
    pub(crate) config: Arc<Config>,
    pub(crate) analysis: Analysis,          // Salsa snapshot
    pub(crate) check_fixes: CheckFixes,
    mem_docs: MemDocs,
    pub(crate) semantic_tokens_cache: Arc<Mutex<FxHashMap<Url, SemanticTokens>>>,
    vfs: Arc<RwLock<(vfs::Vfs, FxHashMap<FileId, LineEndings>)>>,
    pub(crate) workspaces: Arc<Vec<ProjectWorkspace>>,
    pub(crate) proc_macros_loaded: bool,
    pub(crate) flycheck: Arc<[FlycheckHandle]>,
}

impl std::panic::UnwindSafe for GlobalStateSnapshot {}

impl GlobalState {
    pub(crate) fn snapshot(&self) -> GlobalStateSnapshot {
        GlobalStateSnapshot {
            config: Arc::clone(&self.config),
            analysis: self.analysis_host.analysis(),  // db.clone()
            vfs: Arc::clone(&self.vfs),
            check_fixes: Arc::clone(&self.diagnostics.check_fixes),
            mem_docs: self.mem_docs.clone(),
            semantic_tokens_cache: Arc::clone(&self.semantic_tokens_cache),
            proc_macros_loaded: !self.config.expand_proc_macros()
                || self.fetch_proc_macros_queue.last_op_result().copied().unwrap_or(false),
            workspaces: Arc::clone(&self.workspaces),
            flycheck: self.flycheck.clone(),
        }
    }
}
```

## Request Dispatch Handler

The dispatch handler routes LSP requests to handler functions on worker threads:

```rust
// rust-analyzer/crates/rust-analyzer/src/handlers/dispatch.rs
pub(crate) struct RequestDispatcher<'a> {
    pub(crate) req: Option<lsp_server::Request>,
    pub(crate) global_state: &'a mut GlobalState,
}

impl RequestDispatcher<'_> {
    /// Sync-mut: runs on main thread with &mut GlobalState
    pub(crate) fn on_sync_mut<R>(
        &mut self,
        f: fn(&mut GlobalState, R::Params) -> anyhow::Result<R::Result>,
    ) -> &mut Self { /* ... */ }

    /// Sync: runs on main thread with snapshot
    pub(crate) fn on_sync<R>(
        &mut self,
        f: fn(GlobalStateSnapshot, R::Params) -> anyhow::Result<R::Result>,
    ) -> &mut Self { /* ... */ }

    /// Async: dispatched to thread pool with snapshot
    pub(crate) fn on<const ALLOW_RETRYING: bool, R>(
        &mut self,
        f: fn(GlobalStateSnapshot, R::Params) -> anyhow::Result<R::Result>,
    ) -> &mut Self {
        // If VFS not ready, return default
        if !self.global_state.vfs_done {
            if let Some(req) = self.req.take_if(|it| it.method == R::METHOD) {
                self.global_state.respond(Response::new_ok(req.id, R::Result::default()));
            }
            return self;
        }
        self.on_with_thread_intent::<false, ALLOW_RETRYING, R>(
            ThreadIntent::Worker, f, Self::content_modified_error,
        )
    }

    /// Latency-sensitive: higher priority thread intent
    pub(crate) fn on_latency_sensitive<const ALLOW_RETRYING: bool, R>(
        &mut self,
        f: fn(GlobalStateSnapshot, R::Params) -> anyhow::Result<R::Result>,
    ) -> &mut Self {
        self.on_with_thread_intent::<false, ALLOW_RETRYING, R>(
            ThreadIntent::LatencySensitive, f, Self::content_modified_error,
        )
    }
}
```

### The Core Dispatch Implementation

```rust
// rust-analyzer/crates/rust-analyzer/src/handlers/dispatch.rs
fn on_with_thread_intent<const RUSTFMT: bool, const ALLOW_RETRYING: bool, R>(
    &mut self,
    intent: ThreadIntent,
    f: fn(GlobalStateSnapshot, R::Params) -> anyhow::Result<R::Result>,
    on_cancelled: fn() -> ResponseError,
) -> &mut Self {
    let (req, params, panic_context) = match self.parse::<R>() {
        Some(it) => it,
        None => return self,
    };

    let world = self.global_state.snapshot();

    // Store cancellation token for $/cancelRequest
    self.global_state
        .cancellation_tokens
        .insert(req.id.clone(), world.analysis.cancellation_token());

    // Spawn on thread pool
    self.global_state.task_pool.handle.spawn(intent, move || {
        let result = panic::catch_unwind(move || {
            let _pctx = DbPanicContext::enter(panic_context);
            f(world, params)
        });
        match thread_result_to_response::<R>(req.id.clone(), result) {
            Ok(response) => Task::Response(response),

            // Retry on PendingWrite/PropagatedPanic (data changed or transient failure)
            Err(HandlerCancelledError::Inner(
                Cancelled::PendingWrite | Cancelled::PropagatedPanic,
            )) if ALLOW_RETRYING => Task::Retry(req),

            // Return RequestCanceled for explicit client cancellation
            Err(HandlerCancelledError::Inner(Cancelled::Local)) => Task::Response(Response {
                id: req.id,
                result: None,
                error: Some(ResponseError {
                    code: ErrorCode::RequestCanceled as i32,
                    message: "canceled by client".to_owned(),
                    data: None,
                }),
            }),

            // Default: ContentModified error
            Err(_cancelled) => {
                let error = on_cancelled();
                Task::Response(Response { id: req.id, result: None, error: Some(error) })
            }
        }
    });

    self
}
```

### Cancellation Detection in Panic Handling

```rust
// rust-analyzer/crates/rust-analyzer/src/handlers/dispatch.rs
fn thread_result_to_response<R>(
    id: RequestId,
    result: thread::Result<anyhow::Result<R::Result>>,
) -> Result<Response, HandlerCancelledError> {
    match result {
        Ok(result) => result_to_response::<R>(id, result),
        Err(panic) => {
            let panic_message = panic
                .downcast_ref::<String>()
                .map(String::as_str)
                .or_else(|| panic.downcast_ref::<&str>().copied());

            let mut message = "request handler panicked".to_owned();
            if let Some(panic_message) = panic_message {
                message.push_str(": ");
                message.push_str(panic_message);
            } else if let Ok(cancelled) = panic.downcast::<Cancelled>() {
                // Cancellation that escaped Cancelled::catch — should not happen
                tracing::error!("Cancellation propagated out of salsa! This is a bug");
                return Err(HandlerCancelledError::Inner(*cancelled));
            };

            Ok(Response::new_err(id, ErrorCode::InternalError as i32, message))
        }
    }
}
```

## Cache Priming with Parallel Workers

```rust
// rust-analyzer/crates/ide-db/src/prime_caches.rs
pub fn parallel_prime_caches(
    db: &RootDatabase,
    num_worker_threads: usize,
    cb: &(dyn Fn(ParallelPrimeCachesProgress) + Sync),
) {
    // Work queues: def maps → import maps → symbols → sema
    let (def_map_work_sender, def_map_work_receiver) = crossbeam_channel::unbounded();
    let (sema_work_sender, sema_work_receiver) = crossbeam_channel::unbounded();
    // ...

    // Each worker gets its own snapshot and wraps queries in Cancelled::catch
    let prime_caches_worker = move |db: RootDatabase| {
        let handle_def_map = |crate_id, crate_name| {
            progress_sender.send(BeginCrateDefMap { crate_id, crate_name })?;
            let cancelled = Cancelled::catch(|| {
                _ = hir::crate_def_map(&db, crate_id);
            });
            match cancelled {
                Ok(()) => progress_sender.send(EndCrateDefMap { crate_id })?,
                Err(cancelled) => progress_sender.send(Cancelled(cancelled))?,
            }
            Ok(())
        };

        // Worker loop with manual cancellation check
        loop {
            db.unwind_if_revision_cancelled();  // Check between items

            crossbeam_channel::select_biased! {
                recv(def_map_work_receiver) -> work => {
                    let Ok((crate_id, name)) = work else { break };
                    handle_def_map(crate_id, name)?;
                }
                recv(sema_work_receiver) -> work => {
                    let Ok(crate_id) = work else { break };
                    handle_sema(crate_id)?;
                }
                // ... more work receivers
            }
        }
    };

    // Spawn workers with cloned (snapshot) databases
    for id in 0..num_worker_threads {
        stdx::thread::Builder::new(ThreadIntent::Worker, format!("PrimeCaches#{id}"))
            .allow_leak(true)
            .spawn({
                let worker = prime_caches_worker.clone();
                let db = db.clone();  // Snapshot per worker
                move || worker(db)
            })
            .expect("failed to spawn thread");
    }

    // Coordinator: propagate cancellation from workers
    for progress in progress_receiver {
        match progress {
            Cancelled(cancelled) => {
                // Re-throw to caller
                std::panic::resume_unwind(Box::new(cancelled));
            }
            // ... handle progress updates
        }
    }
}
```

Key patterns:
- Each worker gets its own database snapshot via `db.clone()`
- Workers call `unwind_if_revision_cancelled()` between items
- Each query is wrapped in `Cancelled::catch`
- Cancellation propagates from worker → progress channel → coordinator → caller

## Main Loop: Snapshot Usage

```rust
// rust-analyzer/crates/rust-analyzer/src/main_loop.rs

// Cache priming: snapshot sent to worker thread
fn prime_caches(&mut self, cause: String) {
    let num_threads = self.config.prime_caches_num_threads();
    self.task_pool.handle.spawn_with_sender(ThreadIntent::Worker, {
        let analysis = AssertUnwindSafe(self.snapshot().analysis);
        move |sender| {
            sender.send(Task::PrimeCaches(PrimeCachesProgress::Begin)).unwrap();
            let res = analysis.parallel_prime_caches(num_threads, |progress| {
                sender.send(Task::PrimeCaches(PrimeCachesProgress::Report(progress))).unwrap();
            });
            sender.send(Task::PrimeCaches(PrimeCachesProgress::End {
                cancelled: res.is_err()
            })).unwrap();
        }
    });
}

// Diagnostic updates: snapshot per chunk of files
fn update_diagnostics(&mut self) {
    let snapshot = self.snapshot();
    let subscriptions = /* filter to workspace files */;

    // Split work across threads (limited to 1/4 of pool)
    let max_tasks = self.config.main_loop_num_threads().div(4).max(1);
    for chunk in subscriptions.chunks(chunk_length) {
        let snapshot = snapshot.clone();
        self.task_pool.handle.spawn(ThreadIntent::Worker, move || {
            let diagnostics = chunk.iter()
                .filter_map(|&file_id| {
                    fetch_native_diagnostics(&snapshot, file_id, generation).ok()
                })
                .collect();
            Task::Diagnostics(diagnostics)
        });
    }
}

// Change application: triggers cancellation of all snapshots
Task::LoadProcMacros(ProcMacroProgress::End(change)) => {
    self.analysis_host.apply_change(change);  // Cancels all snapshots
}
```

## The Nonce Pattern

Each database instance gets a unique identifier for tracking and debugging:

```rust
// rust-analyzer/crates/base-db/src/lib.rs
pub struct Nonce(u32);

static NONCE: AtomicU32 = AtomicU32::new(0);

impl Nonce {
    pub fn new() -> Self {
        Nonce(NONCE.fetch_add(1, Ordering::SeqCst))
    }
}
```

Used in `RootDatabase::clone()` — each snapshot gets a fresh nonce, making it easy to identify which database instance a log message came from.

## Thread Intent

rust-analyzer classifies thread pool tasks by priority:

```rust
pub enum ThreadIntent {
    Worker,            // Normal priority (diagnostics, analysis)
    LatencySensitive,  // High priority (completion, hover)
}
```

Latency-sensitive requests (typing-related) get higher scheduling priority than background work like diagnostics. This ensures the UI stays responsive even when the server is busy computing diagnostics.

## ContentModified Error

The standard error returned when a query is cancelled due to content changes:

```rust
fn content_modified_error() -> ResponseError {
    ResponseError {
        code: lsp_server::ErrorCode::ContentModified as i32,  // -32801
        message: "content modified".to_owned(),
        data: None,
    }
}
```

LSP clients interpret this as "the result is stale, re-request if needed" — different from `RequestCanceled` (-32800) which means "client explicitly cancelled."
