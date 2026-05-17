# Restructure Ownership Before `Rc<RefCell<T>>`

Two related smells: sprinkling `.clone()` wherever the borrow checker complains, and wrapping everything in `Rc<RefCell<T>>` to "make it work." Both trade compile-time safety for runtime costs — clones for performance, `RefCell` for potential panics.

## The Smell: `.clone()` as Escape Hatch

```rust
// WRONG — cloning to avoid borrow conflicts
fn process(data: &mut Database) {
    let items = data.get_items().clone(); // clone to release the borrow
    for item in &items {
        data.update(item.id, item.value * 2);
    }
}
```

## The Smell: `Rc<RefCell<T>>` as First Resort

```rust
// WRONG — everything wrapped in Rc<RefCell>
struct App {
    users: Rc<RefCell<Vec<User>>>,
    logger: Rc<RefCell<Logger>>,
    config: Rc<RefCell<Config>>,
}
```

You've traded compile-time borrow checking for runtime borrow checking. A `borrow_mut()` while something else holds a `borrow()` will **panic at runtime** — the exact class of bugs Rust's ownership system is designed to prevent.

## The Idiomatic Alternatives

### Restructure to avoid simultaneous borrows

```rust
// Collect what you need first, then mutate
fn process(data: &mut Database) {
    let updates: Vec<(Id, i64)> = data
        .get_items()
        .iter()
        .map(|item| (item.id, item.value * 2))
        .collect();

    for (id, value) in updates {
        data.update(id, value);
    }
}
```

### Split borrows on different struct fields

```rust
struct State {
    config: Config,
    data: Vec<Item>,
}

fn process(state: &mut State) {
    let State { config, data } = state;
    for item in data.iter_mut() {
        item.apply(config); // destructured borrows are independent
    }
}
```

### Pass data through function parameters

```rust
// WRONG — shared mutable state via Rc<RefCell>
fn update_ui(state: Rc<RefCell<AppState>>) {
    let state = state.borrow();
    render(&state.widgets);
}

// RIGHT — borrow what you need
fn update_ui(widgets: &[Widget]) {
    render(widgets);
}
```

### Use indices for graphs and trees

```rust
// WRONG — tree with parent references via Rc
struct Node {
    value: i32,
    parent: Option<Rc<RefCell<Node>>>,
    children: Vec<Rc<RefCell<Node>>>,
}

// RIGHT — arena-based tree with indices
struct Tree {
    nodes: Vec<Node>,
}

struct Node {
    value: i32,
    parent: Option<usize>,
    children: Vec<usize>,
}
```

Arena allocation (`Vec<T>` with indices, or crates like `slotmap`, `thunderdome`, `indextree`) is the standard pattern for graphs and trees in Rust.

### Borrow instead of own

```rust
// WRONG — takes ownership, forces clone at call site
fn greet(name: String) { println!("Hello, {}", name); }
greet(name.clone()); // clone because we "might need it later"

// RIGHT
fn greet(name: &str) { println!("Hello, {}", name); }
greet(&name); // borrows, no clone
```

## Diagnostic Questions

Before reaching for `.clone()` or `Rc<RefCell<T>>`:

1. **Could this function take `&T` instead of `T`?** Most functions only read.
2. **Am I cloning to work around a simultaneous borrow?** Separate the read and write phases.
3. **Is this the last use?** If so, move instead of clone.
4. **Can I split the struct?** Sometimes one struct does too many things. Split it, and the borrow conflicts disappear.
5. **Can I use an arena/index approach?** For trees and graphs, almost always yes.
6. **Is the clone actually cheap?** `Arc::clone` = cheap (ref count bump). `Vec<String>::clone` = not cheap.

## In Async Code: Even Worse

`Arc<Mutex<T>>` across `.await` points compounds the problem. Holding a `std::sync::MutexGuard` across an `.await` can stall the entire runtime worker thread — other unrelated tasks stop making progress. It can also cause logical deadlocks if the awaited operation needs the same lock.

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
    state.lock().unwrap().data = new_data;
}
```

**Which mutex to use:**
- `std::sync::Mutex` — default choice. Lock only in short, non-async sections.
- `tokio::sync::Mutex` — only when you *must* hold the lock across `.await`. Slower. Rarely needed.

If you find yourself reaching for `Arc<Mutex<T>>` in async code, the same restructuring strategies above apply: pass data through parameters, split borrows, use channels instead of shared state. See [async.md](../async.md) for the full pattern.

## When `Rc<RefCell<T>>` Is the Right Tool

- **Graph structures** that genuinely need shared ownership and can't use an arena.
- **Callback/observer patterns** where multiple closures capture and mutate shared state.
- **GUI frameworks** (e.g., GTK bindings) where the framework's architecture requires shared mutable state.
- **Prototyping.** Get it working, then refactor the ownership.

`Arc<Mutex<T>>` is the thread-safe equivalent — same concerns, plus potential deadlocks.

## When `.clone()` Is Fine

- **Small, `Copy`-like types.** Cloning an `Arc`, a small `String`, or a config struct is cheap.
- **Thread boundaries.** Sending owned data to another thread often requires it.
- **The alternative is worse.** Sometimes restructuring makes the code significantly harder to follow.

The smell is cloning *reflexively* rather than *deliberately*.

## Common Source Languages

- **Java / C# / Python / JS** — garbage collection means shared mutable state "just works." `Rc<RefCell>` is the closest Rust equivalent, which is exactly why GC-language developers reach for it first.
