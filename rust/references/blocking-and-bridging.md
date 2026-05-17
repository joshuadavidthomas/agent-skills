# Blocking Operations and Sync↔Async Bridging

## The Three Ways to Run Blocking Code

### `spawn_blocking` — Tokio's blocking thread pool

Runs a closure on a separate thread pool (~500 threads). Best for synchronous I/O and moderate CPU work.

```rust
// Sync file I/O inside async context
let content = tokio::task::spawn_blocking(|| {
    std::fs::read_to_string("data.json")
}).await.unwrap()?;

// Diesel database query
let users = tokio::task::spawn_blocking(move || {
    let conn = &mut pool.get()?;
    users::table.load::<User>(conn)
}).await.unwrap()?;
```

**When to use:**
- File system operations (`std::fs::*`)
- Blocking database drivers (diesel, rusqlite)
- Calling into synchronous C libraries
- Moderate CPU work (a few milliseconds)

**When NOT to use:**
- Heavy parallel computation → use `rayon`
- Tasks that run forever → use `std::thread::spawn`

### `rayon` — CPU-parallel computation

A thread pool sized to CPU core count. Designed for data-parallel computation via parallel iterators.

```rust
use rayon::prelude::*;

async fn compute_hashes(data: Vec<Vec<u8>>) -> Vec<String> {
    let (tx, rx) = tokio::sync::oneshot::channel();

    rayon::spawn(move || {
        let results: Vec<String> = data
            .par_iter()
            .map(|chunk| format!("{:x}", sha256(chunk)))
            .collect();
        let _ = tx.send(results);
    });

    rx.await.expect("rayon task panicked")
}
```

**Pattern:** Always bridge with `rayon::spawn` + `oneshot` channel. Never call `rayon::join` or parallel iterators directly from async code — they block until the computation finishes.

**When to use:**
- Image processing, compression, encryption
- Parsing large files
- Any embarrassingly parallel computation
- When you need all CPU cores working

### Dedicated thread — long-running blocking tasks

For tasks that run forever or for a very long time, spawn a dedicated OS thread. Neither `spawn_blocking` nor `rayon` are designed to have threads permanently occupied.

```rust
use std::thread;
use tokio::sync::mpsc;

struct DbCommand {
    query: String,
    resp: tokio::sync::oneshot::Sender<Result<Vec<Row>, DbError>>,
}

fn start_db_thread(mut rx: mpsc::Receiver<DbCommand>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let conn = Connection::open("app.db").unwrap();
        // Use blocking_recv in a std::thread context
        while let Some(cmd) = rx.blocking_recv() {
            let result = conn.execute(&cmd.query);
            let _ = cmd.resp.send(result);
        }
    })
}
```

**When to use:**
- Database connection managers
- Blocking event loops (inotify, USB polling)
- Any task that never returns

## Bridging Sync → Async

When you have a synchronous codebase that needs to call async code.

### `Runtime::block_on` — run async code from sync context

```rust
use tokio::runtime::Runtime;

fn main() {
    let rt = Runtime::new().unwrap();

    let result = rt.block_on(async {
        fetch_data().await
    });

    println!("{result:?}");
}
```

`block_on` blocks the current thread until the future completes. Use it as the bridge at program boundaries (like `main`), not deep inside async code.

**`#[tokio::main]` expands to this:**
```rust
fn main() {
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .unwrap()
        .block_on(async {
            // your async main body
        })
}
```

### The blocking wrapper pattern

Wrap an async client in a synchronous API for consumers that can't use async:

```rust
pub struct BlockingClient {
    inner: AsyncClient,
    rt: tokio::runtime::Runtime,
}

impl BlockingClient {
    pub fn new(addr: &str) -> Result<Self> {
        let rt = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()?;
        let inner = rt.block_on(AsyncClient::connect(addr))?;
        Ok(Self { inner, rt })
    }

    pub fn get(&mut self, key: &str) -> Result<Option<String>> {
        self.rt.block_on(self.inner.get(key))
    }

    pub fn set(&mut self, key: &str, value: &str) -> Result<()> {
        self.rt.block_on(self.inner.set(key, value))
    }
}
```

Use `new_current_thread()` for the embedded runtime — no need for the multi-thread overhead when you're driving it synchronously with `block_on`.

**Authority:** Tokio tutorial, "Bridging with sync code."

### Runtime on a dedicated thread (message-passing bridge)

For full async capabilities inside a sync application:

```rust
use tokio::runtime::Builder;
use tokio::sync::mpsc;

#[derive(Clone)]
pub struct AsyncBridge {
    sender: mpsc::Sender<Task>,
}

impl AsyncBridge {
    pub fn new() -> Self {
        let (tx, mut rx) = mpsc::channel::<Task>(16);

        let rt = Builder::new_current_thread()
            .enable_all()
            .build()
            .unwrap();

        std::thread::spawn(move || {
            rt.block_on(async move {
                while let Some(task) = rx.recv().await {
                    tokio::spawn(handle_task(task));
                }
            });
        });

        Self { sender: tx }
    }

    pub fn submit(&self, task: Task) {
        self.sender.blocking_send(task).unwrap();
    }
}
```

The runtime lives on its own thread. Sync code sends messages; the runtime processes them asynchronously. This is the most flexible pattern but has the most boilerplate.

## Bridging Async → Sync

When async code needs to call a synchronous function.

### Simple: `spawn_blocking`

```rust
async fn process_file(path: PathBuf) -> Result<Data> {
    tokio::task::spawn_blocking(move || {
        let content = std::fs::read_to_string(&path)?;
        parse_data(&content)
    }).await?
}
```

### For methods that need `&self`

`spawn_blocking` requires `'static` data. If you need access to struct fields, clone what you need first:

```rust
impl MyService {
    async fn query(&self, input: &str) -> Result<Output> {
        let conn_str = self.connection_string.clone();
        let input = input.to_owned();

        tokio::task::spawn_blocking(move || {
            let conn = blocking_connect(&conn_str)?;
            conn.query(&input)
        }).await?
    }
}
```

## Runtime Configuration

### Multi-thread (default)

```rust
#[tokio::main] // equivalent to multi_thread
async fn main() { }

// Explicit:
#[tokio::main(flavor = "multi_thread", worker_threads = 4)]
async fn main() { }
```

Spawns worker threads (default: one per CPU core). Tasks can move between threads. Good for servers handling many concurrent connections.

### Current-thread

```rust
#[tokio::main(flavor = "current_thread")]
async fn main() { }
```

All tasks run on a single thread. Lower overhead. Good for:
- CLI tools with light concurrency
- Embedded runtimes inside sync code
- Tests

**Caveat:** Spawned tasks only make progress during `block_on` calls. If you return from `block_on`, spawned tasks freeze.

### Manual builder

```rust
let rt = tokio::runtime::Builder::new_multi_thread()
    .worker_threads(2)
    .thread_name("my-worker")
    .enable_all()
    .build()
    .unwrap();
```

Use the builder when you need custom thread counts, names, or when embedding the runtime in a larger application.
