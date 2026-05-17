# Trait Patterns

Catalog of trait design patterns in idiomatic Rust. Use with [traits.md](../traits.md) when implementation details matter for sealed traits, extension traits, marker traits, and blanket impls.

## Sealed Trait

Prevents external crates from implementing your trait. Gives you the same exhaustiveness guarantee as an enum but with trait dispatch ergonomics.

```rust
mod private {
    pub trait Sealed {}
}

pub trait Format: private::Sealed {
    fn extension(&self) -> &'static str;
    fn mime_type(&self) -> &'static str;
}

pub struct Json;
pub struct Yaml;

impl private::Sealed for Json {}
impl private::Sealed for Yaml {}

impl Format for Json {
    fn extension(&self) -> &'static str { "json" }
    fn mime_type(&self) -> &'static str { "application/json" }
}

impl Format for Yaml {
    fn extension(&self) -> &'static str { "yaml" }
    fn mime_type(&self) -> &'static str { "application/x-yaml" }
}
```

**When to seal:**
- The trait is a closed set of implementations (typestate bounds, format types)
- Adding external implementations would violate safety invariants
- You want to add methods to the trait without breaking downstream

**When NOT to seal:**
- The trait is designed for user extension (plugins, strategies, test doubles)
- You're publishing a crate and want ecosystem adoption

**Authority:** Rust API Guidelines [C-SEALED]. std: `Pattern`, `Termination`, `SliceIndex` are effectively sealed.

## Extension Trait

Adds methods to types or traits you don't own. Two variants: **blanket Ext** (adds methods to every implementor of a trait, e.g., `AsyncReadExt` for all `AsyncRead`) and **sealed Ext** (adds methods to a specific type, e.g., Axum's `RequestExt`).

This pattern is pervasive — Tokio, futures, Tower, itertools, and Axum all use it.

For the full reference (both variants, implementation guide, combinator return types, Ext vs newtype decision, naming conventions), see [extension-traits.md](extension-traits.md).

## Marker Trait

A trait with no methods. Signals a property the compiler or downstream code can check at compile time.

```rust
/// Types that have been validated and are safe to persist.
trait Validated {}

fn save_to_db<T: Validated + Serialize>(item: &T) -> Result<(), DbError> {
    // Only validated types can be saved.
    todo!()
}
```

**std marker traits:** `Send`, `Sync`, `Copy`, `Eq`, `Sized`, `Unpin`.

**Design guidance:**
- Marker traits should represent an *invariant*, not a *capability*.
- `Copy: Clone` makes sense — "bitwise copy is valid" refines "can be duplicated."
- If the trait has behavior, add methods. If it tags a property, keep it empty.

## Blanket Implementation

Implements a trait for all types meeting a constraint.

```rust
trait Greet {
    fn greet(&self) -> String;
}

// Every Display type gets Greet automatically
impl<T: Display> Greet for T {
    fn greet(&self) -> String {
        format!("Hello, {}!", self)
    }
}
```

**Coherence implications:** Once you add a blanket impl, no one (including you) can add a more specific impl that overlaps. This is deliberate — it prevents ambiguity — but means blanket impls should be added carefully.

```rust
// After the blanket impl above, this is ILLEGAL:
impl Greet for String {
    fn greet(&self) -> String {
        format!("Hey {}, nice string!", self)
    }
}
// ERROR: conflicting implementations of trait `Greet` for type `String`
```

**std examples:**
- `impl<T: Display> ToString for T` — every `Display` type gets `.to_string()`
- `impl<T> From<T> for T` — every type converts from itself
- `impl<T, U: From<T>> Into<U> for T` — every `From` gets `Into` for free

## Conditional Implementation

Implement a trait only when the type parameter satisfies additional bounds.

```rust
struct Wrapper<T>(T);

// Available for all T
impl<T> Wrapper<T> {
    fn new(val: T) -> Self { Wrapper(val) }
}

// Only available when T: Display
impl<T: Display> Display for Wrapper<T> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Wrapper({})", self.0)
    }
}

// Only available when T: Clone + Debug
impl<T: Clone + Debug> Wrapper<T> {
    fn clone_and_debug(&self) -> String {
        format!("{:?}", self.0.clone())
    }
}
```

**Authority:** std: `Vec<T>` implements `Clone` only when `T: Clone`. `Option<T>` implements `Ord` only when `T: Ord`.

## Newtype Delegation

When a newtype wraps a type that implements traits you want, delegate explicitly instead of using `Deref`.

```rust
struct UserId(u64);

// ❌ WRONG — Deref is for smart pointers, not delegation
impl Deref for UserId {
    type Target = u64;
    fn deref(&self) -> &u64 { &self.0 }
}

// ✅ RIGHT — explicit delegation via From/Display/etc.
impl Display for UserId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "user-{}", self.0)
    }
}

impl From<u64> for UserId {
    fn from(id: u64) -> Self { UserId(id) }
}

impl UserId {
    pub fn as_u64(&self) -> u64 { self.0 }
}
```

**Why not `Deref`:** `Deref` coercion happens implicitly and makes the newtype transparent to method resolution. A `UserId` would silently act like a `u64`, defeating the purpose of the newtype. Use `Deref` only for smart pointer types (`Box`, `Arc`, `MutexGuard`, your own smart pointer).

**Authority:** Effective Rust Item 12 (Deref anti-patterns). clippy: `deref_addrof`.

## Closure-Based Strategy

When a "trait" has exactly one method, consider accepting a closure instead.

```rust
// Trait-based (more structure, supports state)
trait Predicate<T> {
    fn test(&self, item: &T) -> bool;
}

// Closure-based (simpler, ergonomic)
fn filter<T>(items: &[T], predicate: impl Fn(&T) -> bool) -> Vec<&T> {
    items.iter().filter(|item| predicate(item)).collect()
}

// Usage is more natural
let adults = filter(&users, |u| u.age >= 18);
```

**Use a trait when:** the strategy has state, multiple methods, or needs to be named/stored. **Use a closure when:** it's a single operation and inline definition is natural.

**Authority:** std: `Iterator::filter`, `sort_by`, `map` all take closures. `Read`, `Write` are traits because they have multiple methods and state.

## Supertraits with Defaults

Combine supertrait requirements with default method implementations to give implementors rich behavior from minimal input.

```rust
trait Named {
    fn name(&self) -> &str;
}

trait Greetable: Named {
    fn greeting(&self) -> String {
        format!("Hello, {}!", self.name())  // Uses Named::name
    }
}

struct User { name: String }

impl Named for User {
    fn name(&self) -> &str { &self.name }
}

// User gets greeting() for free by implementing Named
impl Greetable for User {}
```

## Associated Type Defaults (Nightly / Future)

Associated types can have defaults when most implementors use the same type:

```rust
trait Container {
    type Item = u8;  // Default, overridable
    fn get(&self, index: usize) -> Option<&Self::Item>;
}
```

Associated type defaults are unstable on stable Rust (as of Rust 1.90) and require `#![feature(associated_type_defaults)]` on nightly. On stable Rust, use a concrete type or make implementors specify it explicitly.

## Generic Associated Types (GATs)

Stable since Rust 1.65. Use when an associated type needs a lifetime or type parameter.

```rust
trait LendingIterator {
    type Item<'a> where Self: 'a;

    fn next(&mut self) -> Option<Self::Item<'_>>;
}

// Implementation that lends references to its own data
struct WindowIter<'data> {
    data: &'data [u8],
    pos: usize,
}

impl<'data> LendingIterator for WindowIter<'data> {
    type Item<'a> = &'a [u8] where Self: 'a;

    fn next(&mut self) -> Option<Self::Item<'_>> {
        if self.pos + 3 <= self.data.len() {
            let window = &self.data[self.pos..self.pos + 3];
            self.pos += 1;
            Some(window)
        } else {
            None
        }
    }
}
```

**Use GATs when:** an associated type needs to borrow from `self` or is parameterized over a lifetime/type that varies per method call.

**Don't use GATs when:** a simple associated type or generic parameter suffices. GATs add complexity — reach for them only when simpler alternatives fail.
