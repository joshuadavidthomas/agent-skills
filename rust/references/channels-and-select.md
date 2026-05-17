# Channels, Select, and the Actor Pattern

## Channel Types in Detail

### `mpsc` — Multi-Producer, Single-Consumer

The workhorse channel. Many tasks send; one task receives.

```rust
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel::<String>(32); // bounded, capacity 32

// Clone tx for additional producers
let tx2 = tx.clone();

tokio::spawn(async move {
    tx.send("from task 1".into()).await.unwrap();
});
tokio::spawn(async move {
    tx2.send("from task 2".into()).await.unwrap();
});

// Receiver loop — exits when all senders are dropped
while let Some(msg) = rx.recv().await {
    println!("received: {msg}");
}
```

**Key behaviors:**
- `send().await` blocks (yields) when the channel is full — this is backpressure
- `recv().await` returns `None` when all `Sender`s are dropped — natural shutdown signal
- `try_send()` returns immediately; useful when you'd rather drop a message than wait
- Channel capacity is the primary backpressure mechanism

**Choosing capacity:** Start with 32. If producers frequently block, increase it. If memory grows unbounded, you have a throughput mismatch — fix the consumer or add more.

### `oneshot` — Single-Producer, Single-Consumer, One Value

Used for getting a response back from a task. Always paired with another channel.

```rust
use tokio::sync::oneshot;

let (tx, rx) = oneshot::channel::<u64>();

// Sender (inside a task)
tx.send(42).unwrap(); // send is NOT async — always immediate

// Receiver
let value = rx.await.unwrap(); // await the single value
```

**Key behaviors:**
- `send()` is synchronous — never blocks, never waits
- Cannot be cloned (single producer, single consumer)
- `rx.await` returns `Err(RecvError)` if the sender was dropped without sending
- Lightweight: no buffer, no capacity, minimal overhead

### `broadcast` — Multi-Producer, Multi-Consumer (Every Receiver Sees Every Message)

Each receiver gets a copy of every message. Messages are cloned for each receiver.

```rust
use tokio::sync::broadcast;

let (tx, _rx) = broadcast::channel::<String>(16);

let mut rx1 = tx.subscribe();
let mut rx2 = tx.subscribe();

tx.send("hello".into()).unwrap();

assert_eq!(rx1.recv().await.unwrap(), "hello");
assert_eq!(rx2.recv().await.unwrap(), "hello");
```

**Key behaviors:**
- Messages must implement `Clone`
- If a receiver falls behind, it gets a `RecvError::Lagged(n)` error — the oldest
  messages were dropped
- New subscribers only see messages sent after subscribing
- `send()` returns `Err` only if there are zero active receivers

**Use cases:** Event notification, pub/sub, broadcasting configuration updates when every consumer must see every change.

### `watch` — Multi-Producer, Multi-Consumer (Latest Value Only)

Receivers always see the most recent value. No history. Useful for shared state that changes infrequently.

```rust
use tokio::sync::watch;

let (tx, mut rx) = watch::channel(AppConfig::default());

// Producer updates the value
tx.send(new_config).unwrap();

// Consumer waits for changes
loop {
    rx.changed().await.unwrap();
    let config = rx.borrow().clone();
    apply_config(&config);
}
```

**Key behaviors:**
- `rx.borrow()` returns a `Ref` to the current value — no allocation
- `rx.changed().await` resolves when a new value is sent after the last `borrow()`
- Multiple receivers, multiple senders (via `tx.clone()`)
- `tx.send()` is synchronous — never blocks
- Returns `Err` on `rx.changed()` when all senders are dropped — shutdown signal

**Use cases:** Configuration reloading, shutdown signaling, health status.

## The Actor Pattern

The actor pattern isolates state behind a task. Other code communicates with it via messages (channels). This is the most common pattern for shared mutable resources in async Rust.

### Structure

```
┌─────────────┐     mpsc      ┌──────────────┐
│ Handle      │──────────────▶│ Actor task   │
│ (Clone)     │               │ (owns state) │
│             │◀──────────────│              │
│             │   oneshot     │              │
└─────────────┘   (per req)   └──────────────┘
```

### Implementation

```rust
use tokio::sync::{mpsc, oneshot};

// Messages the actor handles
enum Command {
    Get {
        key: String,
        resp: oneshot::Sender<Option<String>>,
    },
    Set {
        key: String,
        value: String,
        resp: oneshot::Sender<()>,
    },
}

// The actor — owns the state, runs in its own task
struct CacheActor {
    receiver: mpsc::Receiver<Command>,
    store: HashMap<String, String>,
}

impl CacheActor {
    fn new(receiver: mpsc::Receiver<Command>) -> Self {
        Self {
            receiver,
            store: HashMap::new(),
        }
    }

    async fn run(&mut self) {
        while let Some(cmd) = self.receiver.recv().await {
            match cmd {
                Command::Get { key, resp } => {
                    let _ = resp.send(self.store.get(&key).cloned());
                }
                Command::Set { key, value, resp } => {
                    self.store.insert(key, value);
                    let _ = resp.send(());
                }
            }
        }
    }
}

// The handle — cloneable, used by callers
#[derive(Clone)]
pub struct CacheHandle {
    sender: mpsc::Sender<Command>,
}

impl CacheHandle {
    pub fn new() -> Self {
        let (sender, receiver) = mpsc::channel(64);
        let mut actor = CacheActor::new(receiver);
        tokio::spawn(async move { actor.run().await });
        Self { sender }
    }

    pub async fn get(&self, key: String) -> Option<String> {
        let (resp_tx, resp_rx) = oneshot::channel();
        let _ = self.sender.send(Command::Get { key, resp: resp_tx }).await;
        resp_rx.await.expect("actor task dropped")
    }

    pub async fn set(&self, key: String, value: String) {
        let (resp_tx, resp_rx) = oneshot::channel();
        let _ = self.sender.send(Command::Set { key, value, resp: resp_tx }).await;
        resp_rx.await.expect("actor task dropped")
    }
}
```

### Actor Pattern Rules

1. **Spawn the task in the handle's constructor** — not inside the actor. Keep `tokio::spawn` in one place.
2. **Separate handle from actor struct** — the handle has the `Sender`, the actor has the `Receiver`. They never share a struct.
3. **Use `oneshot` for responses** — embed it in the command enum. The actor sends the response; the handle awaits it.
4. **Shutdown is automatic** — when all handles are dropped, all senders are dropped, `recv()` returns `None`, the actor loop exits.
5. **Ignore send errors on response** — use `let _ = resp.send(result)`. The requester may have been cancelled.

**Authority:** Ryhl, "Actors with Tokio."

## `tokio::select!`

Races multiple futures. The first to complete wins; the rest are dropped.

### Basic usage

```rust
use tokio::sync::mpsc;
use tokio::time::{sleep, Duration};

let (tx, mut rx) = mpsc::channel::<String>(32);

loop {
    tokio::select! {
        Some(msg) = rx.recv() => {
            handle_message(msg);
        }
        _ = sleep(Duration::from_secs(60)) => {
            println!("no messages for 60s, exiting");
            break;
        }
    }
}
```

### Receiving from multiple channels

```rust
loop {
    tokio::select! {
        Some(msg) = chan1.recv() => handle_type1(msg),
        Some(msg) = chan2.recv() => handle_type2(msg),
        else => break, // both channels closed
    }
}
```

The `else` branch runs when all patterns fail to match (both channels return `None`). Use it to detect shutdown.

### Cancellation safety

When `select!` completes one branch, it drops all others. A future that was partially executed loses its progress.

**Cancellation-safe operations** (safe to drop mid-await):
- `mpsc::Receiver::recv()`
- `oneshot::Receiver` (the await itself)
- `tokio::time::sleep`
- `tokio::signal::ctrl_c`

**NOT cancellation-safe** (may lose data if dropped):
- `tokio::io::AsyncReadExt::read()` — bytes read into the buffer are lost
- `tokio::io::BufReader::read_line()` — partial line data lost
- Any future that performs a partial write then awaits

**Mitigation:** For non-cancellation-safe operations in `select!`, use `tokio::pin!` with manual state management, or restructure to move the I/O into its own task that communicates via channels.

## Avoiding Deadlocks in Channel Cycles

If actors send messages to each other via bounded channels, you can deadlock: Actor A waits to send to B (B's channel full), B waits to send to A (A's channel full).

**Rules:**
- Break cycles by having at least one channel in the cycle be unbounded or use `try_send`
- Use `oneshot` for responses (its `send` is always immediate)
- If actors must form a cycle, have one use `select!` on its inbound channel so it can drain messages even when sending blocks

**Authority:** Ryhl, "Actors with Tokio" — deadlock section.
