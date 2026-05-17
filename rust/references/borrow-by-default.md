# Borrow by Default — Own When Intentional

## The Smell

Functions taking ownership of data they only need to read.

```rust
// WRONG — takes ownership unnecessarily
fn contains_admin(users: Vec<User>) -> bool { todo!() }
fn greet(name: String) { println!("Hello, {}", name); }

let name = "Alice".to_string();
greet(name.clone()); // forced to clone because greet consumes
greet(name);
```

## The Idiomatic Alternative

```rust
// RIGHT — borrows the data it only needs to read
fn contains_admin(users: &[User]) -> bool { todo!() }
fn greet(name: &str) { println!("Hello, {}", name); }

let name = "Alice".to_string();
greet(&name); // borrows, no clone
greet(&name); // can borrow again
```

### Accept the most general borrowed form

| Instead of | Accept | Why |
|---|---|---|
| `&String` | `&str` | Works with `String`, `&str`, `Cow<str>`, string literals |
| `&Vec<T>` | `&[T]` | Works with `Vec`, arrays, slices |
| `&PathBuf` | `&Path` | Works with `PathBuf`, `Path`, `OsStr` |
| `&Box<T>` | `&T` | No reason to require the Box |

This follows the Rust API Guidelines [C-CALLER-CONTROL] principle: let the caller decide the storage, and accept the most general borrow.

### Return borrowed data from accessors

Methods exposing internal data should return references. Callers who need ownership clone explicitly — let them choose.

```rust
// WRONG — allocates on every access
impl Config {
    fn database_url(&self) -> String {
        self.database_url.clone()
    }
}

// RIGHT — zero-cost access
impl Config {
    fn database_url(&self) -> &str {
        &self.database_url
    }
}
```

This applies to all accessor patterns: return `&str` not `String`, `&[T]` not `Vec<T>`, `&T` not `T`. See also [getter-setter.md](getter-setter.md) for when to use accessors vs public fields.

## When to Take Ownership

Ownership is a **decision**, not a default. Take ownership when:

- **Storing the value.** Struct fields, collection insertion.
- **Transforming and returning.** Builder pattern, `into_*` methods.
- **Moving to another thread.** `send` to a channel, `spawn` a task.
- **The function consumes the value.** Destructors, serializers that write-and-drop.

### The `Into` pattern for flexible ownership

When you need to store a `String` but want to accept both `&str` and `String`:

```rust
fn set_name(mut self, name: impl Into<String>) -> Self {
    self.name = name.into();
    self
}

// Caller can pass either:
builder.set_name("literal")           // &str → String allocation
builder.set_name(computed_string)     // String → no extra allocation
```

## `Cow` for Conditional Ownership

When a function *sometimes* needs to allocate:

```rust
use std::borrow::Cow;

fn normalize_path(path: &str) -> Cow<'_, str> {
    if path.contains("//") {
        Cow::Owned(path.replace("//", "/"))
    } else {
        Cow::Borrowed(path) // no allocation
    }
}
```

## Common Source Languages

- **Garbage-collected languages (Java, Python, Go, JS)** — all values are references managed by the GC; there's no ownership concept, so "just take the value" is the instinct
- **C++** — has ownership concepts but `const&` vs move semantics require active thought; Rust makes this explicit
