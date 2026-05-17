# Async Patterns and Tokio

Async Rust is cooperative multitasking. The runtime can only switch tasks at `.await` points. Everything flows from this: don't block, don't hold locks across awaits, don't starve the executor.

**The one rule:** Async code should never spend a long time without reaching an `.await`. A good threshold is 10–100 microseconds between yields.

**Authority:** Alice Ryhl, "Async: What is blocking?"; Tokio tutorial; Async Book.

## CPU-Bound or I/O-Bound?

This is the first question. The answer determines your entire approach.

| Workload | Where to run | Why |
|----------|-------------|-----|
| Network I/O, timers, async DB | `async fn` + `.await` | Non-blocking; yields at I/O boundaries |
| File system I/O, blocking DB (diesel) | `spawn_blocking` | File I/O is blocking on most OSes |
| Expensive computation (parsing, crypto, compression) | `rayon` or `spawn_blocking` | CPU doesn't yield; starves the executor |
| Busy CPU loop / polling loop (no `.await`) | Dedicated thread or redesign to yield | A task that never yields starves runtime workers |

**Decision:**
- I/O-bound → `async`/`.await` with tokio
- CPU-bound, many parallel tasks → `rayon`
- CPU-bound, simple/few → `spawn_blocking`
- Runs forever without `.await` → dedicated thread or redesign

For deep dives on `spawn_blocking` vs `rayon` vs dedicated threads, and sync↔async bridging, see [references/blocking-and-bridging.md](references/blocking-and-bridging.md).

## Core Rules

### Rule 1: Never block the async runtime

Blocking calls prevent the runtime from switching tasks. Other tasks on the same thread stop making progress.

```rust
// WRONG — blocks the runtime thread
async fn read_config() -> String {
    std::fs::read_to_string("config.toml").unwrap() // blocks!
}

// RIGHT — use async I/O
async fn read_config() -> String {
    tokio::fs::read_to_string("config.toml").await.unwrap()
}
```

Common blocking operations that need `spawn_blocking` or async alternatives:
- `std::fs::*` → `tokio::fs::*`
- `std::thread::sleep` → `tokio::time::sleep`
- `std::net::*` → `tokio::net::*`
- Synchronous HTTP clients → `reqwest` (async)
- `diesel` queries → `spawn_blocking`

**Authority:** Ryhl, "Async: What is blocking?" — "Async code should never spend a long time without reaching an `.await`."

### Rule 2: Don't hold mutex guards across `.await`

Holding a `std::sync::MutexGuard` across `.await` is a correctness and latency risk. If another task tries to lock it, the runtime worker thread blocks, stalling unrelated futures. It can also create logical deadlocks if the awaited operation needs the same lock.

```rust
// WRONG — MutexGuard held across await
async fn update(state: &Mutex<State>) {
    let mut guard = state.lock().unwrap();
    guard.data = fetch_remote().await; // DEADLOCK RISK
}

// RIGHT — lock, extract, drop, then await
async fn update(state: &Mutex<State>) {
    let current = {
        let guard = state.lock().unwrap();
        guard.data.clone()
    }; // guard dropped here
    let new_data = fetch_remote().await;
    let mut guard = state.lock().unwrap();
    guard.data = new_data;
}
```

**When to use which mutex:**
- `std::sync::Mutex` — default choice. Lock only in non-async methods (the wrapper struct pattern). Fast, no overhead.
- `tokio::sync::Mutex` — only when you *must* hold the lock across `.await`. Slower. Rarely needed.

**Authority:** Tokio tutorial (shared state); Ryhl, "Shared mutable state."

### Rule 3: Spawned tasks require `Send + 'static`

`tokio::spawn` moves the future to a different thread. The future must own all its data (`'static`) and be safely transferable between threads (`Send`).

```rust
// WRONG — Rc is not Send
use std::rc::Rc;
async fn broken() {
    let data = Rc::new(42);
    tokio::spawn(async move {
        println!("{}", data); // ERROR: Rc is not Send
    });
}

// RIGHT — use Arc for shared ownership across tasks
use std::sync::Arc;
async fn works() {
    let data = Arc::new(42);
    tokio::spawn(async move {
        println!("{}", data);
    });
}
```

**Key:** the `Send` check applies to data held *across* `.await` points. If a non-Send type is created and dropped before the next `.await`, it's fine:

```rust
tokio::spawn(async {
    {
        let rc = Rc::new("local");
        println!("{}", rc);
    } // dropped before await
    tokio::time::sleep(Duration::from_secs(1)).await;
});
```

**Authority:** Tokio tutorial (spawning, Send bound).

### Rule 4: Use `async move` to transfer ownership into tasks

Spawned tasks can't borrow from the caller. Move data in with `async move`:

```rust
let config = load_config().await;
tokio::spawn(async move {
    // config is owned by this task
    start_server(config).await;
});
// config is no longer available here
```

If multiple tasks need the same data, clone it (or wrap in `Arc`) before moving:

```rust
let shared = Arc::new(config);
for _ in 0..num_workers {
    let shared = Arc::clone(&shared);
    tokio::spawn(async move {
        process(&shared).await;
    });
}
```

### Rule 5: Bound your concurrency

Every `tokio::spawn`, channel, and queue introduces concurrency. Unbounded concurrency eventually exhausts memory.

- Use bounded channels: `mpsc::channel(capacity)`, not unbounded
- Limit concurrent connections (e.g., `tokio::sync::Semaphore`)
- Set timeouts on all external operations

```rust
use tokio::sync::Semaphore;
use std::sync::Arc;

let sem = Arc::new(Semaphore::new(100)); // max 100 concurrent

for request in requests {
    let permit = sem.clone().acquire_owned().await.unwrap();
    tokio::spawn(async move {
        handle(request).await;
        drop(permit); // releases on completion
    });
}
```

**Authority:** Tokio tutorial (backpressure and bounded channels).

## Channel Type Selection

Channels are the primary communication mechanism between async tasks. Pick the right one.

| Channel | Direction | Values | Buffering | Use when |
|---------|-----------|--------|-----------|----------|
| `mpsc` | Many → 1 | Many | Bounded | Task receives work from multiple producers |
| `oneshot` | 1 → 1 | One | N/A | Request-response; getting a result back from a task |
| `broadcast` | Many → Many | Many | Bounded | Every receiver sees every message (pub/sub) |
| `watch` | Many → Many | Latest | 1 (latest) | Configuration changes; receivers only need current value |

**Rules of thumb:**
- Default to `mpsc` + `oneshot` for the actor pattern (request with response)
- Use `watch` for shared configuration or shutdown signals
- Use `broadcast` when all consumers need all messages
- For multi-consumer where each message goes to one consumer, use
  `async-channel` crate (not in tokio)

For the full channel reference (actor pattern, select!, cycle avoidance), see [references/channels-and-select.md](references/channels-and-select.md).

## The Shared State Pattern

Wrap `Arc<Mutex<T>>` in a newtype. Isolate all lock calls to non-async methods. This prevents accidentally holding locks across `.await`.

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

#[derive(Clone)]
pub struct AppState {
    inner: Arc<Mutex<AppStateInner>>,
}

struct AppStateInner {
    users: HashMap<u64, User>,
}

impl AppState {
    pub fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(AppStateInner {
                users: HashMap::new(),
            })),
        }
    }

    // Non-async — lock cannot be held across .await
    pub fn get_user(&self, id: u64) -> Option<User> {
        let lock = self.inner.lock().unwrap();
        lock.users.get(&id).cloned()
    }

    // Non-async — safe
    pub fn insert_user(&self, id: u64, user: User) {
        let mut lock = self.inner.lock().unwrap();
        lock.users.insert(id, user);
    }
}
```

**Why not pass `Arc<Mutex<HashMap<...>>>` directly?**
- Lock calls scattered everywhere — easy to hold across `.await`
- Implementation detail leaked into every signature
- Can't swap `Mutex` for `RwLock` or `dashmap` without touching all callers

**Authority:** Ryhl, "Shared mutable state in Rust."

## Spawning and Task Structure

### `tokio::spawn` — fire-and-forget concurrent tasks

Returns a `JoinHandle`. The task runs independently. Dropping the handle does **not** cancel the task.

```rust
let handle = tokio::spawn(async {
    expensive_work().await
});

// Later, get the result
let result = handle.await.unwrap();
```

### `tokio::spawn_blocking` — offload blocking work

Runs a closure on Tokio's blocking thread pool (default max is 512 threads; configurable). Use for synchronous I/O or moderate CPU work.

```rust
let result = tokio::task::spawn_blocking(|| {
    // OK to block here
    std::fs::read_to_string("large-file.txt")
}).await.unwrap();
```

### `tokio::join!` — concurrent awaiting, no spawning

Runs multiple futures concurrently on the **same task**. No `Send` requirement. All branches must complete.

```rust
let (users, posts) = tokio::join!(
    fetch_users(),
    fetch_posts(),
);
```

### `tokio::select!` — race multiple futures

Returns when the **first** branch completes. Remaining branches are dropped (cancelled).

```rust
tokio::select! {
    result = do_work() => handle_result(result),
    _ = tokio::signal::ctrl_c() => println!("interrupted"),
    _ = tokio::time::sleep(Duration::from_secs(30)) => println!("timed out"),
}
```

**Cancellation safety:** when `select!` drops a branch, any in-progress work in that future is lost. Not all futures are cancellation-safe. `mpsc::recv()` is safe; partial `read` into a buffer is not.

### When to use what

| Goal | Tool |
|------|------|
| Run task independently | `tokio::spawn` |
| Wait for multiple things at once | `tokio::join!` |
| React to first of several events | `tokio::select!` |
| Run blocking code | `tokio::task::spawn_blocking` |
| CPU-parallel computation | `rayon::spawn` + `oneshot` channel |

## Timeouts and Production Patterns

Every external operation should have a timeout. No exceptions.

```rust
use tokio::time::{timeout, Duration};

match timeout(Duration::from_secs(5), fetch_data()).await {
    Ok(result) => handle(result),
    Err(_elapsed) => handle_timeout(),
}
```

For more granular control, use `tokio::time::sleep` with `select!`:

```rust
tokio::select! {
    data = connection.read() => process(data),
    _ = tokio::time::sleep(Duration::from_secs(30)) => {
        connection.close().await;
    }
}
```

For graceful shutdown (`CancellationToken`, `TaskTracker`), retry with backoff, backpressure, cancellation safety reference, and `JoinSet`, see [references/production-patterns.md](references/production-patterns.md).

## Common Mistakes (Agent Failure Modes)

- **`std::thread::sleep` in async code** → Blocks the runtime. Use `tokio::time::sleep(..).await`.
- **`std::fs::*` in async code** → Blocks the runtime. Use `tokio::fs::*` or `spawn_blocking`.
- **Holding `MutexGuard` across `.await`** → Deadlock risk. Lock in non-async methods, or restructure to lock-extract-drop-await.
- **Using `Rc` in spawned tasks** → Not `Send`. Use `Arc` instead.
- **`Arc<tokio::sync::Mutex<T>>` as default** → Overkill. Use `std::sync::Mutex` wrapped in a newtype with non-async methods. Only use `tokio::sync::Mutex` when you must hold the lock across `.await` (rare).
- **Unbounded channels/queues** → Memory grows without limit under load. Always use bounded channels and handle backpressure.
- **No timeout on external calls** → A stalled peer hangs your task forever. Wrap every network/IO operation in `tokio::time::timeout`.
- **Ignoring cancellation safety in `select!`** → A cancelled future loses progress. Use cancellation-safe operations or manage state explicitly.
- **`tokio::spawn` + immediate `.await`** → No concurrency gained. Just call the future directly, or use `join!` if combining with other work.
- **Blocking CPU work on the async runtime** → Starves other tasks. Use `spawn_blocking` for moderate work, `rayon` for heavy parallelism.

## Cross-References

- [ownership.md](ownership.md) — `'static` bounds on spawned futures, `Arc`/`Rc` choice, `Send`/`Sync`
- [traits.md](traits.md) — `Send`, `Sync`, `Future` trait, object safety with async
- [error-handling.md](error-handling.md) — `anyhow` in async contexts, `?` in async functions, `JoinError` handling
- [type-design.md](type-design.md) — Enum-based message types for actor channels, newtype wrappers for state

## Review Checklist

1. **Is every blocking call off the runtime?** `std::fs`, `std::thread::sleep`, synchronous HTTP, diesel queries → `spawn_blocking` or async alternative.
2. **Are mutex guards confined to non-async methods?** Use the wrapper struct pattern. Lock, read/write, drop — never across `.await`.
3. **Do spawned tasks own their data?** `async move` with `Arc`/`Clone` for shared data. No borrowed references into spawned tasks.
4. **Are all channels bounded?** Every `mpsc::channel` has an explicit capacity. Handle the backpressure case (drop, log, reject).
5. **Does every external call have a timeout?** Wrap network, database, and file operations in `tokio::time::timeout`.
6. **Is the channel type correct?** `mpsc` for work queues, `oneshot` for responses, `watch` for config/signals, `broadcast` for pub/sub.
7. **Is `select!` used with cancellation-safe futures?** Check that dropped branches don't lose partial progress.
8. **Is CPU-bound work off the async runtime?** Heavy computation goes to `rayon` or `spawn_blocking`, not inline in async functions.
9. **Is concurrency bounded?** Semaphores, channel capacity, or connection limits prevent resource exhaustion under load.
10. **Is graceful shutdown implemented?** `CancellationToken` or `watch` channel for signaling, `TaskTracker` or `JoinHandle` collection for waiting.
