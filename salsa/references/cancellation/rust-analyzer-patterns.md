# Cancellation: rust-analyzer Patterns

Production cancellation usage from rust-analyzer (Rust IDE / LSP).

## Cancellable Type Alias

```rust
// rust-analyzer/crates/ide/src/lib.rs

pub type Cancellable<T> = Result<T, Cancelled>;
```

Every public query method returns `Cancellable<T>`. This makes cancellation explicit in the API.

## The with_db Wrapper

```rust
// rust-analyzer/crates/ide/src/lib.rs

impl Analysis {
    fn with_db<F, T>(&self, f: F) -> Cancellable<T>
    where
        F: FnOnce(&RootDatabase) -> T + UnwindSafe,
    {
        hir::attach_db_allow_change(&self.db, || Cancelled::catch(|| f(&self.db)))
    }

    // Every public method uses with_db:
    pub fn diagnostics(&self, file: FileId) -> Cancellable<Vec<Diagnostic>> {
        self.with_db(|db| diagnostics::diagnostics(db, file))
    }

    pub fn hover(&self, position: FilePosition) -> Cancellable<Option<HoverResult>> {
        self.with_db(|db| hover::hover(db, position))
    }
}
```

## Host/Snapshot Split

```rust
// rust-analyzer/crates/ide/src/lib.rs

impl AnalysisHost {
    pub fn analysis(&self) -> Analysis {
        Analysis { db: self.db.clone() } // Cheap snapshot
    }

    pub fn apply_change(&mut self, change: ChangeWithProcMacros) {
        self.db.apply_change(change);
    }

    pub fn trigger_cancellation(&mut self) {
        self.db.trigger_cancellation();
    }
}
```

## Apply Change = Cancel First

```rust
// rust-analyzer/crates/ide-db/src/apply_change.rs

impl RootDatabase {
    pub fn apply_change(&mut self, change: ChangeWithProcMacros) {
        let _p = tracing::info_span!("RootDatabase::apply_change").entered();
        self.trigger_cancellation(); // Cancel all snapshots BEFORE applying
        tracing::trace!("apply_change {:?}", change);
        change.apply(self);
    }
}
```

## Dispatch: Retry Classification by Variant

```rust
// rust-analyzer/crates/rust-analyzer/src/handlers/dispatch.rs

fn on_with_thread_intent<const ALLOW_RETRYING: bool, R>(
    &mut self, intent: ThreadIntent,
    f: fn(GlobalStateSnapshot, R::Params) -> anyhow::Result<R::Result>,
    on_cancelled: fn() -> ResponseError,
) -> &mut Self {
    // ... setup, spawn thread ...

    let result = panic::catch_unwind(move || f(world, params));
    match thread_result_to_response::<R>(req.id.clone(), result) {
        Ok(response) => Task::Response(response),

        // PendingWrite or PropagatedPanic → retry (data changed or transient failure)
        Err(HandlerCancelledError::Inner(
            Cancelled::PendingWrite | Cancelled::PropagatedPanic,
        )) if ALLOW_RETRYING => Task::Retry(req),

        // Local → client cancelled this request explicitly
        Err(HandlerCancelledError::Inner(Cancelled::Local)) => Task::Response(Response {
            id: req.id,
            result: None,
            error: Some(ResponseError {
                code: lsp_server::ErrorCode::RequestCanceled as i32,
                message: "canceled by client".to_owned(),
                data: None,
            }),
        }),

        // Other cancellation → use handler's default error
        Err(_cancelled) => {
            let error = on_cancelled();
            Task::Response(Response { id: req.id, result: None, error: Some(error) })
        }
    }
}
```

## Panic Payload Inspection

```rust
// rust-analyzer/crates/rust-analyzer/src/handlers/dispatch.rs

fn thread_result_to_response<R>(
    id: RequestId,
    result: thread::Result<anyhow::Result<R::Result>>,
) -> Result<lsp_server::Response, HandlerCancelledError> {
    match result {
        Ok(result) => result_to_response::<R>(id, result),
        Err(panic) => {
            let panic_message = panic.downcast_ref::<String>()
                .map(String::as_str)
                .or_else(|| panic.downcast_ref::<&str>().copied());

            if let Ok(cancelled) = panic.downcast::<Cancelled>() {
                tracing::error!("Cancellation propagated out of salsa! This is a bug");
                return Err(HandlerCancelledError::Inner(*cancelled));
            };

            // Real panic — return InternalError
            Ok(lsp_server::Response::new_err(
                id, lsp_server::ErrorCode::InternalError as i32, message,
            ))
        }
    }
}
```

Note the `tracing::error!` — rust-analyzer considers it a **bug** if `Cancelled` reaches this point as a panic rather than being caught by `with_db`.

## Cache Priming with Cancellation

```rust
// rust-analyzer/crates/ide-db/src/prime_caches.rs

// Worker: catch cancellation per work item, send through channel
let handle_def_map = |crate_id, crate_name| {
    progress_sender.send(BeginCrateDefMap { crate_id, crate_name })?;

    let cancelled = Cancelled::catch(|| {
        _ = hir::crate_def_map(&db, crate_id);
    });

    match cancelled {
        Ok(()) => progress_sender.send(EndCrateDefMap { crate_id })?,
        Err(cancelled) => progress_sender.send(Cancelled(cancelled))?,
    }
    Ok::<_, SendError<_>>(())
};

// Coordinator: check cancellation between dispatching work
loop {
    db.unwind_if_revision_cancelled(); // Manual check in coordinator loop
    // ... select next crate, dispatch to worker ...
}

// Coordinator: re-throw cancellation received from worker
ParallelPrimeCacheWorkerProgress::Cancelled(cancelled) => {
    std::panic::resume_unwind(Box::new(cancelled)); // Propagate up
}
```

## Spawning Workers with Snapshots

```rust
// rust-analyzer/crates/rust-analyzer/src/main_loop.rs

self.task_pool.handle.spawn_with_sender(ThreadIntent::Worker, {
    let analysis = AssertUnwindSafe(self.snapshot().analysis);
    move |sender| {
        sender.send(Task::PrimeCaches(PrimeCachesProgress::Begin)).unwrap();
        let res = analysis.parallel_prime_caches(num_worker_threads, |progress| {
            sender.send(Task::PrimeCaches(PrimeCachesProgress::Report(progress))).unwrap();
        });
        sender
            .send(Task::PrimeCaches(PrimeCachesProgress::End {
                cancelled: res.is_err(),
            }))
            .unwrap();
    }
});
```

## Diagnostics: Graceful Degradation

```rust
// rust-analyzer/crates/rust-analyzer/src/main_loop.rs

let diags = std::panic::catch_unwind(|| {
    fetch_native_diagnostics(&snapshot, subscriptions.clone(), slice.clone(), kind)
})
.unwrap_or_else(|_| {
    // On panic OR cancellation: return empty diagnostics
    subscriptions.iter().map(|&id| (id, Vec::new())).collect::<Vec<_>>()
});
```

## Architecture Comparison: ty vs rust-analyzer

| Aspect | ty (Ruff/ty monorepo) | rust-analyzer |
|--------|------|---------------|
| **Return type** | Varies by layer | `Cancellable<T>` everywhere |
| **Primary catch point** | Per-handler, nested layers | `with_db` wrapper |
| **Retry mechanism** | `client.retry(request)` | `Task::Retry(req)` |
| **User cancellation** | Separate `CancellationToken` | Salsa's `CancellationToken::cancel()` → `Cancelled::Local` |
| **Panic boundary** | Worker pool `abort()` | `tracing::error!` (considered a bug) |
| **Cache priming** | N/A | Channel-based with per-item catch |
| **Diagnostic fetch** | Nested catch (per-file) | `unwrap_or_else` empty fallback |
