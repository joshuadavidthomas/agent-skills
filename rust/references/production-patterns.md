# Production Patterns

## Graceful Shutdown

Production services must shut down cleanly: stop accepting new work, finish in-progress work, flush buffers, close connections. Three parts:

1. **Detect** the shutdown signal
2. **Propagate** it to all tasks
3. **Wait** for tasks to finish

### Detecting shutdown

```rust
use tokio::signal;

// Wait for ctrl+c
signal::ctrl_c().await.expect("failed to listen for ctrl+c");

// Or combine multiple signals with select
tokio::select! {
    _ = signal::ctrl_c() => {},
    _ = shutdown_rx.recv() => {}, // internal shutdown request
}
```

### Propagating shutdown with `CancellationToken`

`CancellationToken` (from `tokio-util`) is a broadcast signal. Clone it for each task. Cancel it once; every listener is notified.

```rust
use tokio_util::sync::CancellationToken;

let token = CancellationToken::new();

// Give each worker a clone
for _ in 0..num_workers {
    let token = token.clone();
    tokio::spawn(async move {
        loop {
            tokio::select! {
                _ = token.cancelled() => {
                    // Clean up and exit
                    flush_buffers().await;
                    return;
                }
                msg = rx.recv() => {
                    match msg {
                        Some(m) => process(m).await,
                        None => return, // channel closed
                    }
                }
            }
        }
    });
}

// On shutdown signal
token.cancel();
```

**Advantages over `watch` channel:**
- Semantically clear: it's a one-time signal, not a value
- `cancelled()` returns a future that is always cancellation-safe
- Supports child tokens: `token.child_token()` creates a token that cancels when the parent does, but can also be cancelled independently

### Waiting for tasks with `TaskTracker`

`TaskTracker` (from `tokio-util`) collects spawned tasks and waits for all to complete.

```rust
use tokio_util::task::TaskTracker;

let tracker = TaskTracker::new();

for request in requests {
    tracker.spawn(handle_request(request));
}

// Signal that no more tasks will be spawned
tracker.close();

// Wait for all tasks to finish
tracker.wait().await;
```

### Complete shutdown flow

```rust
use tokio::signal;
use tokio_util::sync::CancellationToken;
use tokio_util::task::TaskTracker;

#[tokio::main]
async fn main() {
    let token = CancellationToken::new();
    let tracker = TaskTracker::new();

    // Spawn workers
    for i in 0..4 {
        let token = token.clone();
        tracker.spawn(worker(i, token));
    }

    // Wait for shutdown signal
    signal::ctrl_c().await.unwrap();
    println!("shutting down...");

    // Signal all tasks to stop
    token.cancel();

    // No more tasks will be spawned
    tracker.close();

    // Wait for everything to finish (with timeout)
    if tokio::time::timeout(
        Duration::from_secs(30),
        tracker.wait(),
    ).await.is_err() {
        eprintln!("shutdown timed out, forcing exit");
    }
}
```

**Authority:** Tokio topics, "Graceful Shutdown."

## Timeouts

### On individual operations

```rust
use tokio::time::{timeout, Duration};

let result = timeout(Duration::from_secs(5), client.get("key")).await;
match result {
    Ok(Ok(value)) => handle(value),
    Ok(Err(e)) => handle_error(e),
    Err(_) => handle_timeout(),
}
```

### On entire request pipelines

```rust
async fn handle_request(req: Request) -> Response {
    match timeout(Duration::from_secs(30), process(req)).await {
        Ok(resp) => resp,
        Err(_) => Response::gateway_timeout(),
    }
}
```

### Retry with exponential backoff

```rust
use tokio::time::{sleep, Duration};

async fn retry<F, Fut, T, E>(mut f: F, max_retries: u32) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
{
    let mut delay = Duration::from_millis(100);

    for attempt in 0..max_retries {
        match f().await {
            Ok(val) => return Ok(val),
            Err(e) if attempt == max_retries - 1 => return Err(e),
            Err(_) => {
                sleep(delay).await;
                delay = (delay * 2).min(Duration::from_secs(30));
            }
        }
    }
    unreachable!()
}
```

For production retries, use the `backoff` or `again` crate rather than rolling your own.

## Backpressure

Backpressure means slowing down producers when consumers can't keep up. Without it, memory grows unbounded.

### Channel-based backpressure

Bounded `mpsc` channels provide natural backpressure. When the channel is full, `send().await` yields until space is available.

```rust
let (tx, mut rx) = mpsc::channel(100);

// Producer slows down when channel is full
tx.send(item).await.unwrap(); // blocks if 100 items queued

// Consumer processes at its own pace
while let Some(item) = rx.recv().await {
    process(item).await;
}
```

### Semaphore-based concurrency limiting

```rust
use tokio::sync::Semaphore;
use std::sync::Arc;

let sem = Arc::new(Semaphore::new(50)); // max 50 concurrent

loop {
    let conn = listener.accept().await?;
    let permit = sem.clone().acquire_owned().await?;

    tokio::spawn(async move {
        handle_connection(conn).await;
        drop(permit); // release on completion
    });
}
```

### Load shedding

When overloaded, reject new work rather than queue it. Combine `try_send` with error responses:

```rust
match tx.try_send(request) {
    Ok(()) => { /* queued successfully */ }
    Err(TrySendError::Full(_)) => {
        return Response::service_unavailable("server overloaded");
    }
    Err(TrySendError::Closed(_)) => {
        return Response::internal_error("service shutting down");
    }
}
```

## Cancellation Safety

When `tokio::select!` completes one branch, it drops all others. A future that was in the middle of work loses its progress.

### Safe pattern: loop with select

```rust
let mut buf = Vec::new();

loop {
    tokio::select! {
        // This branch is cancellation-safe (recv doesn't lose data)
        Some(data) = rx.recv() => {
            buf.extend(data);
        }
        _ = flush_interval.tick() => {
            flush(&mut buf).await;
        }
        _ = token.cancelled() => {
            flush(&mut buf).await; // final flush
            return;
        }
    }
}
```

### Unsafe pattern: read in select

```rust
// WRONG — if the timeout branch wins, bytes read so far are lost
let mut buf = vec![0u8; 1024];
tokio::select! {
    n = stream.read(&mut buf) => { /* ... */ }
    _ = sleep(Duration::from_secs(5)) => { /* bytes lost! */ }
}
```

**Fix:** Move the read into its own task, communicate via channel:

```rust
let (tx, mut rx) = mpsc::channel(1);
tokio::spawn(async move {
    let mut buf = vec![0u8; 1024];
    loop {
        let n = stream.read(&mut buf).await.unwrap();
        if n == 0 { break; }
        tx.send(buf[..n].to_vec()).await.unwrap();
    }
});

// Now this is cancellation-safe
tokio::select! {
    Some(data) = rx.recv() => process(data),
    _ = sleep(Duration::from_secs(5)) => timeout(),
}
```

### Which operations are cancellation-safe?

| Operation | Safe? | Why |
|-----------|-------|-----|
| `mpsc::Receiver::recv` | ✅ | Returns whole message or nothing |
| `oneshot::Receiver` | ✅ | Single value, atomic |
| `tokio::time::sleep` | ✅ | Stateless timer |
| `TcpListener::accept` | ✅ | Returns whole connection |
| `AsyncReadExt::read` | ❌ | May have read partial bytes into buffer |
| `AsyncReadExt::read_exact` | ❌ | Partial progress lost |
| `BufReader::read_line` | ❌ | Partial line data lost |
| `tokio::io::copy` | ❌ | Partial transfer lost |

**Rule:** If a future mutates external state incrementally (buffers, counters, partial writes), it is not cancellation-safe. Move it to a dedicated task.

## Structured Concurrency with `JoinSet`

`JoinSet` manages a dynamic set of spawned tasks, letting you await them as they complete:

```rust
use tokio::task::JoinSet;

let mut set = JoinSet::new();

for url in urls {
    set.spawn(async move {
        fetch(url).await
    });
}

// Process results as they arrive
while let Some(result) = set.join_next().await {
    match result {
        Ok(data) => process(data),
        Err(e) => eprintln!("task failed: {e}"),
    }
}
```

**Advantages over collecting `JoinHandle`s in a `Vec`:**
- Results arrive in completion order, not spawn order
- Dropping a `JoinSet` cancels all remaining tasks
- Integrates with `select!` via `join_next()`
