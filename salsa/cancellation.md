
# Handling Cancellation in Salsa

Salsa queries are cancellation points. When inputs change (new revision), outstanding queries unwind via `salsa::Cancelled`. Interactive tools — LSP servers, CLI watchers — must catch this and either retry or report gracefully.

## How Cancellation Works

Salsa uses **unwinding** (panic machinery) rather than `Result` to signal cancellation. This avoids pervasive error handling throughout the query graph — cancellation is exceptional, not expected.

Three things trigger cancellation:

1. **Pending write** — A thread calls `zalsa_mut()` (to modify an input), which sets a global flag. All other threads' in-flight queries detect this at the next cancellation check and unwind with `Cancelled::PendingWrite`.
2. **Local cancellation** — Code calls `CancellationToken::cancel()` on a specific database handle. That handle's queries unwind with `Cancelled::Local`.
3. **Propagated panic** — A thread blocked on another thread's query result receives `Cancelled::PropagatedPanic` when that thread panics.

Cancellation checks happen **automatically** at every tracked function invocation and during result verification. Between query calls, Salsa does not check — so long-running loops within a single query need manual checks.

## The Cancelled Type

```rust
#[non_exhaustive]
pub enum Cancelled {
    Local,           // Per-handle cancellation token was triggered
    PendingWrite,    // Another thread is applying a new revision
    PropagatedPanic, // Blocked thread panicked
}
```

`Cancelled` uses `resume_unwind` (not `panic!`) to avoid triggering panic hooks and collecting backtraces. This is a deliberate performance optimization — cancellation happens frequently in interactive systems.

## Catching Cancellation

The primary API is `Cancelled::catch`, which wraps a closure in `catch_unwind` and downcasts Salsa cancellation panics:

```rust
match salsa::Cancelled::catch(|| my_query(&db)) {
    Ok(result) => use_result(result),
    Err(Cancelled::PendingWrite) => { /* data changed, retry or discard */ }
    Err(Cancelled::Local) => { /* explicitly cancelled, stop */ }
    Err(Cancelled::PropagatedPanic) => { /* another thread failed */ }
}
```

Non-Salsa panics pass through — `Cancelled::catch` only catches `Cancelled` payloads. Real bugs still crash.

## Manual Cancellation Checks

Between query calls, add manual checks in expensive loops:

```rust
#[salsa::tracked]
fn check_all_files(db: &dyn Db, files: Vec<File>) -> Vec<Diagnostic> {
    let mut results = vec![];
    for file in files {
        db.unwind_if_revision_cancelled(); // Check between iterations
        results.extend(check_file(db, file));
    }
    results
}
```

This is only needed for loops that don't call other tracked functions (which would check automatically).

## Key Patterns

### Pattern 1: CLI — Catch and Discard

Wrap the entire operation, log cancellation, and discard stale results. Used by ty's CLI. No retry logic — the user can just run the command again.

```rust
rayon::spawn(move || {
    match salsa::Cancelled::catch(|| db.check()) {
        Ok(result) => sender.send(result).unwrap(),
        Err(cancelled) => {
            tracing::debug!("Check cancelled: {cancelled:?}");
            // Discard — CLI will re-run if needed
        }
    }
});
```

### Pattern 2: LSP — Classify and Retry

LSP servers must distinguish cancellation types to decide whether to retry or return an error. rust-analyzer and ty_server use exactly this classification:

```rust
// In the request handler:
match panic::catch_unwind(AssertUnwindSafe(|| handle_request(&snapshot, params))) {
    Ok(result) => send_response(result),
    Err(payload) => {
        if payload.downcast_ref::<salsa::Cancelled>().is_some() {
            // Data changed mid-query — retry with fresh snapshot
            client.retry(request);
        } else {
            // Real panic — return internal error
            send_error(ErrorCode::InternalError, "handler panicked");
        }
    }
}
```

| Variant | Meaning | Action |
|---------|---------|--------|
| `PendingWrite` | Input changed during query | Retry (fresh data available) |
| `PropagatedPanic` | Blocked thread panicked | Retry (transient failure) |
| `Local` | Explicitly cancelled by client | Return `RequestCanceled` error |

### Pattern 3: Snapshot-Based Concurrency

The host/snapshot split enables concurrent queries without blocking writes. Worker threads get immutable snapshots (cheap clone). If the host applies changes, the snapshot's queries get cancelled.

```rust
// Main thread owns the host
let snapshot = host.analysis(); // calls db.clone()
thread::spawn(move || {
    match Cancelled::catch(|| snapshot.diagnostics(file)) {
        Ok(diags) => send(diags),
        Err(_) => { /* stale snapshot, discard */ }
    }
});

// Main thread applies changes
host.trigger_cancellation(); // 1. Signal cancellation
host.apply_change(change);   // 2. Apply change (synchronizes)
```

**Critical:** `apply_change` must call `trigger_cancellation()` **before** applying changes.

### Pattern 4: Nested Panic + Cancellation Layers (ty Pattern)

When you need to distinguish "cancelled" from "panicked" in code that must handle both: wrap `Cancelled::catch` inside `panic::catch_unwind`. ty uses this for per-file checking.

```rust
fn safe_check(db: &dyn Db, file: File) -> Result<Option<Vec<Diagnostic>>, Diagnostic> {
    match panic::catch_unwind(|| {
        // Inner: convert cancellation to None
        salsa::Cancelled::catch(|| check_file(db, file)).ok()
    }) {
        Ok(result) => Ok(result),         // Some(diags) or None (cancelled)
        Err(panic) => Err(to_diagnostic(panic)), // Real panic → error diagnostic
    }
}
```

### Pattern 5: Cooperative Cancellation with Tokens

For operations that mutate the world (applying fixes, writing files) where unwinding is unsafe, use an explicit `CancellationToken` and check it cooperatively (returning `Result`).

```rust
fn fix_all(db: &dyn Db, files: &[File], token: &CancellationToken) -> Result<(), Canceled> {
    for file in files {
        if token.is_cancelled() {
            return Err(Canceled);
        }
        apply_fix(db, file);
    }
    Ok(())
}
```

## Common Mistakes

- **Not catching cancellation at all.** If `Cancelled` propagates to your main thread or thread pool boundary uncaught, it looks like a panic.
- **Catching cancellation too eagerly.** Don't catch inside individual queries — let it propagate through the query graph to the handler boundary.
- **Retrying on Local cancellation.** `Cancelled::Local` means someone explicitly cancelled this operation. Retrying defeats the purpose.
- **Forgetting manual checks in long loops.** If your function iterates over thousands of items without calling other tracked functions, it won't check for cancellation until the loop finishes.
- **Applying changes without triggering cancellation first.** Snapshot threads may read a partially-updated database if you don't cancel them before the write.

For full production code and more patterns, see:
- [references/salsa-framework.md](references/cancellation/salsa-framework.md) — framework internals
- [references/ty-patterns.md](references/cancellation/ty-patterns.md) — CLI catch, nested panic layers, retry traits, worker pool abort, cooperative tokens
- [references/rust-analyzer-patterns.md](references/cancellation/rust-analyzer-patterns.md) — `Cancellable<T>`, `with_db` wrapper, host/snapshot split, dispatch retry, cache priming

### Additional Reference: wgsl-analyzer [Legacy API/Architecture]

wgsl-analyzer's `RequestDispatcher` uses a const-generic `ALLOW_RETRYING` flag on its `on_with_thread_intent` method to control cancellation behavior per-request type. When retrying is allowed and cancellation occurs, the request is re-queued as `Task::Retry(request)`. Otherwise, it returns `content_modified_error` (LSP error code -32801). This is a cleaner parameterization than branching on error type at the call site. For the full dispatch flow, see the [lsp-integration.md](lsp-integration.md) skill's wgsl-analyzer reference.

### Additional Reference: Mun [Legacy API/Architecture]

Mun's `AnalysisDatabase` demonstrates the **salsa_event-based cancellation** pattern from the Salsa 2018 era. The database overrides both `on_propagated_panic` and `salsa_event` to inject cancellation checks:

```rust
impl salsa::Database for AnalysisDatabase {
    fn on_propagated_panic(&self) -> ! {
        Canceled::throw()  // Convert panic to clean cancellation
    }
    fn salsa_event(&self, event: salsa::Event) {
        match event.kind {
            salsa::EventKind::DidValidateMemoizedValue { .. }
            | salsa::EventKind::WillExecute { .. } => {
                self.check_canceled();  // Check on every query execution
            }
            _ => (),
        }
    }
}
```

The `Canceled` type uses `resume_unwind` (not `panic!`) to avoid triggering panic hooks — the same optimization used by the modern `salsa::Cancelled` type:

```rust
impl Canceled {
    pub fn throw() -> ! {
        std::panic::resume_unwind(Box::new(Canceled::new()))
    }
}
```

Cancellation is triggered by `synthetic_write(Durability::LOW)` when the host wants to apply new changes. The `catch_canceled` method wraps `catch_unwind` and downcasts `Canceled` payloads:

```rust
pub fn catch_canceled<F, T>(&self, f: F) -> Result<T, Canceled>
where
    Self: Sized + panic::RefUnwindSafe,
    F: FnOnce(&Self) -> T + panic::UnwindSafe,
{
    panic::catch_unwind(|| f(self)).map_err(|err| match err.downcast::<Canceled>() {
        Ok(canceled) => *canceled,
        Err(payload) => panic::resume_unwind(payload),  // Real panics pass through
    })
}
```

This is the pattern that modern Salsa's `Cancelled::catch` encapsulates. For the full LSP architecture, see [lsp-integration.md](lsp-integration.md) and its Mun reference.
