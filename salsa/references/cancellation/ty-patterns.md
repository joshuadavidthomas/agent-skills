# Cancellation: ty Patterns

Production cancellation usage from ty (Python type checker) and its LSP server (ty_server).

## ty CLI: Catch-and-Log

```rust
// ruff/crates/ty/src/lib.rs

rayon::spawn(move || {
    let mut reporter = IndicatifReporter::from(self.printer);
    let bar = reporter.bar.clone();

    match salsa::Cancelled::catch(|| {
        db.check_with_reporter(&mut reporter);
        reporter.bar.finish_and_clear();
        reporter.collector.into_sorted(&db)
    }) {
        Ok(result) => {
            sender.send(MainLoopMessage::CheckCompleted { result, revision }).unwrap();
        }
        Err(cancelled) => {
            bar.finish_and_clear();
            tracing::debug!("Check has been cancelled: {cancelled:?}");
        }
    }
});
```

## Nested Panic + Cancellation Defense (ty_project)

```rust
// ruff/crates/ty_project/src/lib.rs

fn catch<F, R>(db: &dyn Db, file: File, f: F) -> Result<Option<R>, Diagnostic>
where
    F: FnOnce() -> R + UnwindSafe,
{
    match ruff_db::panic::catch_unwind(|| {
        // Inner: cancellation → None (silently discarded)
        salsa::Cancelled::catch(f).ok()
    }) {
        Ok(result) => Ok(result),  // Some(value) or None (cancelled)
        Err(error) => {
            // Real panic → convert to diagnostic with backtrace
            let message = error.to_diagnostic_message(Some(file.path(db)));
            let mut diagnostic = Diagnostic::new(DiagnosticId::Panic, Severity::Fatal, message);
            diagnostic.add_bug_sub_diagnostics("%5Bpanic%5D");

            if let Some(backtrace) = error.backtrace {
                match backtrace.status() {
                    BacktraceStatus::Disabled => {
                        diagnostic.sub(SubDiagnostic::new(
                            SubDiagnosticSeverity::Info,
                            "run with `RUST_BACKTRACE=1` environment variable...",
                        ));
                    }
                    BacktraceStatus::Captured => {
                        diagnostic.sub(SubDiagnostic::new(
                            SubDiagnosticSeverity::Info,
                            format!("Backtrace:\n{backtrace}"),
                        ));
                    }
                    _ => {}
                }
            }

            Err(diagnostic)
        }
    }
}
```

## Custom Panic Hook — No Backtrace for Cancellation (ruff_db — shared infrastructure)

```rust
// ruff/crates/ruff_db/src/panic.rs

fn install_hook() {
    static ONCE: OnceLock<()> = OnceLock::new();
    ONCE.get_or_init(|| {
        let prev = std::panic::take_hook();
        std::panic::set_hook(Box::new(move |info| {
            let should_capture = CAPTURE_PANIC_INFO.with(Cell::get);
            if !should_capture {
                return (*prev)(info); // Salsa's resume_unwind never reaches here
            }
            // Only captures backtrace for real panics (caught by catch_unwind)
            let location = info.location().map(Location::to_string);
            let backtrace = Some(std::backtrace::Backtrace::capture());
            LAST_BACKTRACE.set(CapturedPanicInfo {
                backtrace,
                location,
                salsa_backtrace: salsa::Backtrace::capture(),
            });
        }));
    });
}
```

Key insight: Salsa's `resume_unwind` **bypasses panic hooks entirely** — this is by design. Only real panics (via `panic!`) trigger the hook and collect backtraces.

## LSP: Detect Salsa Cancellation and Retry (ty_server)

```rust
// ruff/crates/ty_server/src/server/api.rs

fn panic_response<R>(
    id: &RequestId,
    client: &Client,
    error: &PanicError,
    request: Option<lsp_server::Request>,
    log_guidance: &str,
) where
    R: traits::RetriableRequestHandler,
{
    if error.payload.downcast_ref::<salsa::Cancelled>().is_some() {
        if let Some(request) = request {
            tracing::debug!(
                "request id={} method={} was cancelled by salsa, re-queueing for retry",
                request.id, request.method
            );
            client.retry(request); // Re-queue for fresh execution
        } else {
            respond_silent_error(id.clone(), client, R::salsa_cancellation_error());
        }
    } else {
        // Real panic — return internal error to client
        respond::<R>(
            id,
            Err(Error {
                code: lsp_server::ErrorCode::InternalError,
                error: anyhow!("request handler {error}"),
            }),
            client, log_guidance,
        );
    }
}
```

## Trait-Based Retry Opt-In (ty_server)

```rust
// ruff/crates/ty_server/src/server/api/traits.rs

pub(super) trait RetriableRequestHandler: RequestHandler {
    const RETRY_ON_CANCELLATION: bool = false;

    fn salsa_cancellation_error() -> lsp_server::ResponseError {
        lsp_server::ResponseError {
            code: lsp_server::ErrorCode::ContentModified as i32,
            message: "content modified".to_string(),
            data: None,
        }
    }
}
```

Handlers opt in to retry by setting `RETRY_ON_CANCELLATION = true`. The `ContentModified` error code (-32801) is the LSP standard for "data changed, please re-request."

## Pre-Execution Cancellation Check (ty_server)

```rust
// ruff/crates/ty_server/src/server/api.rs — handler scheduling

let cancellation_token = session
    .request_queue()
    .incoming()
    .cancellation_token(&id)
    .expect("request should have been tested for cancellation before scheduling");

Box::new(move |client| {
    // Check user cancellation before running handler
    if cancellation_token.is_cancelled() {
        tracing::debug!("Ignoring request id={id} — cancelled");
        return;
    }

    if let Err(error) = ruff_db::panic::catch_unwind(|| {
        R::handle_request(&id, snapshot.0, client, params);
    }) {
        panic_response::<R>(&id, client, &error, retry, log_guidance);
    }
})
```

Two-level cancellation: user tokens checked **before** execution (saves CPU), Salsa cancellation caught **during** execution (retry with fresh data).

## Worker Pool: Abort on Uncaught Cancellation (ty_server)

```rust
// ruff/crates/ty_server/src/server/schedule/thread/pool.rs

if let Err(error) = std::panic::catch_unwind(AssertUnwindSafe(job.f)) {
    if let Some(msg) = error.downcast_ref::<String>() {
        tracing::error!("Worker thread panicked with: {msg}; aborting");
    } else if let Some(cancelled) = error.downcast_ref::<salsa::Cancelled>() {
        tracing::error!("Worker thread got cancelled: {cancelled}; aborting");
    } else {
        tracing::error!("Worker thread panicked with: {error:?}; aborting");
    }
    std::process::abort(); // Cancellation must never escape handler boundary
}
```

## CancellationTokenSource — Non-Salsa Cancellation (ruff_db — shared infrastructure)

```rust
// ruff/crates/ruff_db/src/cancellation.rs

#[derive(Debug, Clone)]
pub struct CancellationTokenSource {
    cancelled: Arc<AtomicBool>,
}

impl CancellationTokenSource {
    pub fn new() -> Self {
        Self { cancelled: Arc::new(AtomicBool::new(false)) }
    }

    pub fn token(&self) -> CancellationToken {
        CancellationToken { cancelled: self.cancelled.clone() }
    }

    pub fn cancel(&self) {
        self.cancelled.store(true, Relaxed);
    }
}

#[derive(Debug, Clone)]
pub struct CancellationToken {
    cancelled: Arc<AtomicBool>,
}

impl CancellationToken {
    pub fn is_cancelled(&self) -> bool {
        self.cancelled.load(Relaxed)
    }
}
```

## Cooperative Cancellation in Fix Application (ty_project)

```rust
// ruff/crates/ty_project/src/fixes.rs

pub fn suppress_all_diagnostics(
    db: &mut dyn Db,
    mut diagnostics: Vec<Diagnostic>,
    cancellation_token: &CancellationToken,
) -> Result<SuppressAllResult, Canceled> {
    let mut by_file: BTreeMap<File, Vec<_>> = BTreeMap::new();

    for diagnostic in diagnostics.extract_if(.., |d| d.primary_span().is_some()) {
        let span = diagnostic.primary_span().unwrap();
        by_file.entry(span.expect_ty_file()).or_default().push(diagnostic);
    }

    let mut fixed_count = 0usize;
    for (&file, file_diagnostics) in &mut by_file {
        // Cooperative check — returns Result, doesn't unwind
        if cancellation_token.is_cancelled() {
            return Err(Canceled);
        }

        let Some(path) = file.path(db).as_system_path() else { continue };
        // ... apply fixes to file ...
    }

    Ok(SuppressAllResult { diagnostics, count: fixed_count })
}
```

## Per-Request Cancellation Tokens (ty_server)

```rust
// ruff/crates/ty_server/src/session/request_queue.rs

struct PendingRequest {
    start_time: Instant,
    method: String,
    cancellation_token: OnceCell<RequestCancellationToken>, // Lazy — only for background requests
}

#[derive(Debug, Default)]
pub(crate) struct RequestCancellationToken(Arc<AtomicBool>);

impl RequestCancellationToken {
    pub(crate) fn is_cancelled(&self) -> bool {
        self.0.load(Relaxed)
    }

    fn cancel(&self) {
        self.0.store(true, Relaxed);
    }
}

// When client sends $/cancelRequest:
pub(super) fn cancel(&mut self, request_id: &RequestId) -> Option<String> {
    self.pending.remove(request_id).map(|mut pending| {
        if let Some(cancellation_token) = pending.cancellation_token.take() {
            cancellation_token.cancel();
        }
        pending.method
    })
}
```
