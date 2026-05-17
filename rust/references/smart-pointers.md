# Smart Pointer Reference

## Box<T> — Single-owner heap allocation

`Box<T>` is the simplest smart pointer: one owner, heap-allocated, freed when the owner drops. Use it for three main cases.

### Recursive types

Recursive types have unknown size at compile time. `Box` provides indirection.

```rust
// WON'T COMPILE — infinite size
enum List {
    Cons(i32, List),
    Nil,
}

// COMPILES — Box provides known-size indirection
enum List {
    Cons(i32, Box<List>),
    Nil,
}
```

### Trait objects with single ownership

```rust
fn make_error(msg: &str) -> Box<dyn std::error::Error> {
    msg.into()
}
```

### Large values off the stack

Moving a large struct through function calls copies it each time (on the stack). Box it once, pass the pointer.

```rust
struct LargeBuffer { data: [u8; 10240] }

fn process(_: Box<LargeBuffer>) {}

fn main() {
    process(Box::new(LargeBuffer { data: [0; 10240] }));
}
```

### When Box is unnecessary

Don't box small types. Don't box just because "it's on the heap." If you have a `Vec<T>` or `String`, the data is already heap-allocated — boxing the handle adds an unnecessary indirection.

```rust
fn main() {
    // WRONG — Vec already heap-allocates its contents
    let _boxed: Box<Vec<i32>> = Box::new(vec![1, 2, 3]);

    // RIGHT — Vec handles its own heap allocation
    let _plain: Vec<i32> = vec![1, 2, 3];
}
```

## Rc<T> — Single-threaded shared ownership

`Rc<T>` (reference counted) lets multiple owners share immutable access to the same heap data. Cloning an `Rc` increments a counter; dropping decrements it. When the count reaches zero, the data is freed.

```rust
use std::rc::Rc;

struct Config;
struct Handler(Rc<Config>);

fn main() {
    let config = Rc::new(Config);
    let _a = Handler(Rc::clone(&config));
    let _b = Handler(Rc::clone(&config));
}
```

**Use `Rc::clone(&x)` not `x.clone()`.** The former makes it clear you're incrementing a reference count, not deep-copying the data. clippy enforces this.

### Rc is NOT thread-safe

`Rc` does not use atomic operations. It is `!Send` and `!Sync`. Using it across threads won't compile. Use `Arc` instead.

### Rc creates immutable data by default

`Rc<T>` gives you `&T`, never `&mut T`. If you need mutation, combine with
`RefCell`: `Rc<RefCell<T>>`.

## Arc<T> — Multi-threaded shared ownership

`Arc<T>` (atomically reference counted) is `Rc` with atomic operations. It's `Send + Sync` when `T: Send + Sync`.

```rust
use std::sync::Arc;

struct Config;

fn main() {
    let config = Arc::new(Config);

    let handle = std::thread::spawn({
        let config = Arc::clone(&config);
        move || {
            let _cfg: &Config = &config; // Arc<T> derefs to T
        }
    });

    handle.join().unwrap();
}
```

**Use `Arc::clone(&x)` not `x.clone()`.** Same reason as `Rc` — clarity about what's being cloned.

### Arc + Mutex for shared mutable state

```rust
use std::sync::{Arc, Mutex};

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = Vec::new();

    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        handles.push(std::thread::spawn(move || *counter.lock().unwrap() += 1));
    }

    for h in handles {
        h.join().unwrap();
    }
}
```

Prefer `RwLock` over `Mutex` when reads vastly outnumber writes.

### Rc vs Arc — choose by context

| Question | Rc | Arc |
|----------|-----|------|
| Thread-safe? | No | Yes |
| Overhead | Non-atomic increment | Atomic increment |
| When | Single-threaded sharing | Cross-thread sharing |

Don't use `Arc` in single-threaded code. The atomic operations are unnecessary overhead. clippy: `rc_buffer`, `arc_with_non_send_sync`.

## Weak<T> — Breaking reference cycles

`Weak<T>` is a non-owning handle to `Rc`/`Arc` data. It doesn't prevent deallocation. Use it to break cycles in graph structures.

```rust
use std::rc::{Rc, Weak};
use std::cell::RefCell;

struct Node {
    value: i32,
    parent: RefCell<Weak<Node>>,     // Weak: doesn't keep parent alive
    children: RefCell<Vec<Rc<Node>>>, // Strong: keeps children alive
}
```

**Pattern:** Parent → children with `Rc` (strong). Child → parent with `Weak`. The parent keeps children alive. When the parent drops, children drop too (if no other strong references exist).

Access the data with `weak.upgrade()` → `Option<Rc<T>>`. Returns `None` if the data has been freed.

## Cell<T> and RefCell<T> — Interior mutability

Interior mutability lets you mutate data behind a shared reference (`&T`). This is the escape hatch when the borrow checker's static analysis is too conservative.

### Cell<T> — for Copy types

`Cell<T>` provides `get()` and `set()` with no runtime cost. Only works for `Copy` types because it copies the value in and out.

```rust
use std::cell::Cell;

struct Counter { count: Cell<u32> }

impl Counter {
    fn increment(&self) {
        self.count.set(self.count.get() + 1);
    }
}
```

### RefCell<T> — for non-Copy types

`RefCell<T>` enforces borrow rules at runtime instead of compile time. Violating them panics.

```rust
use std::cell::RefCell;

fn main() {
    let data = RefCell::new(vec![1, 2, 3]);

    // Runtime borrow check: this panics because an immutable borrow is still active.
    let _borrowed = data.borrow();
    let _mut_borrow = data.borrow_mut();
}
```

**Prefer `try_borrow()` / `try_borrow_mut()` in production code.** They return `Result` instead of panicking, letting you handle conflicts gracefully.

### When interior mutability is appropriate

Use it for: caches/memoization behind `&self`, observer/listener registration, and test doubles that record calls.

### When interior mutability is a code smell

If you're using `RefCell` everywhere to dodge the borrow checker, if `borrow_mut()` panics in practice, or if you're wrapping large subsystems, the design needs clearer ownership boundaries.

## Decision summary

```
I just need heap allocation for one owner
  → Box<T>

Multiple parts of my code need to read the same data
  → Same thread? Rc<T>
  → Cross threads? Arc<T>

I have a graph with cycles
  → Strong refs one direction, Weak the other

I need to mutate through &self
  → Copy type? Cell<T>
  → Non-Copy type? RefCell<T>
  → Cross threads? Mutex<T> or RwLock<T>

I need shared AND mutable
  → Same thread? Rc<RefCell<T>>
  → Cross threads? Arc<Mutex<T>> or Arc<RwLock<T>>
```

**Authority:** The Rust Book ch 15. Effective Rust (smart pointers and ownership tradeoffs). std library design.
