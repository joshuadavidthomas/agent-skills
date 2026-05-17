# Extension Traits

The Ext pattern adds methods to types or traits you don't own — or separates a minimal core trait from a rich convenience API. This is one of the most common patterns in the Rust ecosystem. If you've used `.read_to_string()` on a Tokio `AsyncRead` or `.map()` on a `Stream`, you've used an extension trait.

## The Two Variants

### 1. Blanket Ext — add methods to every implementor of a trait

The dominant pattern in Tokio, Tower, futures, and itertools. A trait with a supertrait bound, all default methods, and an empty blanket impl.

```rust
// Core trait — minimal, defines the capability
pub trait AsyncRead {
    fn poll_read(
        self: Pin<&mut Self>,
        cx: &mut Context<'_>,
        buf: &mut ReadBuf<'_>,
    ) -> Poll<io::Result<()>>;
}

// Extension trait — rich convenience API
pub trait AsyncReadExt: AsyncRead {
    fn read<'a>(&'a mut self, buf: &'a mut [u8]) -> Read<'a, Self>
    where
        Self: Unpin,
    {
        read(self, buf)
    }

    fn read_to_end<'a>(&'a mut self, buf: &'a mut Vec<u8>) -> ReadToEnd<'a, Self>
    where
        Self: Unpin,
    {
        read_to_end(self, buf)
    }

    // ... 10+ more convenience methods, all with default impls
}

// Blanket impl — every AsyncRead gets these methods for free
impl<R: AsyncRead + ?Sized> AsyncReadExt for R {}
```

**How it works:**
1. The supertrait bound (`AsyncReadExt: AsyncRead`) ensures only `AsyncRead` types get the extension methods.
2. Every method has a default implementation — there are **no required methods**.
3. The blanket `impl<R: AsyncRead + ?Sized> AsyncReadExt for R {}` activates the defaults for all qualifying types, including trait objects (`?Sized`).
4. Default methods typically delegate to free functions that return concrete future/combinator types — zero-cost, no `Box<dyn Future>`.

**Why separate the traits?**
- **Core stays minimal.** Implementors of `AsyncRead` only write `poll_read`. They don't have to think about `read_to_string` or `read_exact`.
- **Extensions are free.** Every type that implements the core trait automatically gets the convenience methods.
- **Backward compatible.** Adding methods to the Ext trait doesn't break existing core trait implementors.
- **Coherence-safe.** You can define extension methods for a foreign trait without violating the orphan rule.

### 2. Sealed Ext — add methods to a specific type

Used when extension methods target one concrete type (or a small set). Axum uses this for `RequestExt`.

```rust
mod sealed {
    pub trait Sealed {}
    impl Sealed for http::Request<Body> {}
}

pub trait RequestExt: sealed::Sealed + Sized {
    fn extract<E, M>(self) -> impl Future<Output = Result<E, E::Rejection>> + Send
    where
        E: FromRequest<(), M> + 'static,
        M: 'static;
}

impl RequestExt for Request<Body> {
    fn extract<E, M>(self) -> impl Future<Output = Result<E, E::Rejection>> + Send
    where
        E: FromRequest<(), M> + 'static,
        M: 'static,
    {
        self.extract_with_state(&())
    }
}
```

**How it works:**
1. A private `Sealed` trait limits who can implement the Ext trait.
2. Methods have actual implementations (not just defaults).
3. Only the designated type(s) get the extensions.

**When to use this over blanket:**
- You're extending a specific foreign type, not a whole trait hierarchy
- You want to prevent external implementations
- You don't want these methods available on every implementor of some base trait

## Choosing Between the Variants

| Question | Blanket Ext | Sealed Ext |
|----------|-------------|------------|
| Extending a trait or a type? | Trait | Type |
| Should third-party impls get methods? | Yes | No |
| Need trait object support? | Yes (`?Sized`) | No (`Sized` required) |
| Who can implement? | Anyone (via base trait) | Only you |
| Can you add methods later? | Yes (non-breaking) | Yes (non-breaking) |
| `impl Trait` in return position? | Yes, but the method must be `where Self: Sized` (so it won't work on `dyn`) | Yes |

**Rule of thumb:** If you're defining a core trait that others implement, use a blanket Ext. If you're adding convenience methods to a specific foreign type, use a sealed Ext.

## Ecosystem Examples

| Crate | Extension Trait | Base | Variant |
|-------|----------------|------|---------|
| `tokio` | `AsyncReadExt` | `AsyncRead` | Blanket |
| `tokio` | `AsyncWriteExt` | `AsyncWrite` | Blanket |
| `tokio-stream` | `StreamExt` | `Stream` | Blanket |
| `futures` | `FutureExt` | `Future` | Blanket |
| `futures` | `StreamExt` | `Stream` | Blanket |
| `futures` | `SinkExt` | `Sink` | Blanket |
| `tower` | `ServiceExt` | `Service` | Blanket |
| `itertools` | `Itertools` | `Iterator` | Blanket |
| `axum` | `RequestExt` | `Request<Body>` | Sealed |
| `axum` | `RequestPartsExt` | `request::Parts` | Sealed |

Note: `itertools::Itertools` breaks the `{Name}Ext` convention — it just uses the crate name. Both styles work; `{Base}Ext` is more common.

## Implementation Guide

### Blanket Ext (step by step)

```rust
// 1. Define the extension trait with supertrait bound
pub trait IteratorExt: Iterator {
    /// Returns the first and last elements, or None if empty.
    fn first_last(mut self) -> Option<(Self::Item, Self::Item)>
    where
        Self: Sized,
        Self::Item: Clone,
    {
        let first = self.next()?;
        match self.last() {
            Some(last) => Some((first, last)),
            None => Some((first.clone(), first)),
        }
    }

    /// Collects into a Vec, but only up to `limit` elements.
    fn collect_limit(self, limit: usize) -> Vec<Self::Item>
    where
        Self: Sized,
    {
        self.take(limit).collect()
    }
}

// 2. Blanket impl — one line
impl<I: Iterator + ?Sized> IteratorExt for I {}

// 3. Re-export from your crate root or prelude
// In lib.rs:
pub use crate::iter_ext::IteratorExt;
```

### Making it available to users

Extension methods require an explicit import. Make this easy:

```rust
// Option A: re-export at crate root
// In lib.rs:
pub use crate::ext::IteratorExt;
// User: use my_crate::IteratorExt;

// Option B: prelude module (for crates with multiple Ext traits)
// In lib.rs:
pub mod prelude {
    pub use crate::ext::{IteratorExt, StreamExt, FutureExt};
}
// User: use my_crate::prelude::*;
```

The prelude pattern is common for crates that export many Ext traits. Tokio, futures, and diesel all use it.

### Methods that return combinators

For zero-cost async/iterator combinators, each method returns a concrete type rather than `Box<dyn Future>` or `Box<dyn Iterator>`:

```rust
// The combinator type
pub struct Map<S, F> {
    stream: S,
    f: F,
}

// In the Ext trait
pub trait StreamExt: Stream {
    fn map<T, F>(self, f: F) -> Map<Self, F>
    where
        Self: Sized,
        F: FnMut(Self::Item) -> T,
    {
        Map { stream: self, f }
    }
}
```

This pattern is why the Ext trait needs `Self: Sized` on combinator methods — the return type includes `Self` as a type parameter, which requires a known size.

## Common Bounds on Ext Methods

| Bound | Why | Example |
|-------|-----|---------|
| `Self: Sized` | Method takes `self` by value or return type includes `Self` | Combinator methods (`map`, `filter`, `chain`) |
| `Self: Unpin` | Method takes `&mut self` and needs to pin internally | `read`, `write`, `next` on async types |
| `Self::Item: Clone` | Method needs to duplicate stream/iterator items | `first_last`, `peek` |

Methods with `Self: Sized` bounds are **not available on trait objects** (`dyn Trait`). This is intentional — combinators need to know the concrete type.

## When Ext vs When Newtype

Both patterns add methods to types you don't own. Choose based on:

| Ext trait | Newtype |
|-----------|---------|
| Adds behavior, no new invariants | Adds invariants (validation, restricted API) |
| Works transparently on the original type | Creates a distinct type |
| Requires import to activate | Always available |
| Zero wrapping cost | Zero wrapping cost (but needs `From`/`Into`) |
| Can't hide or restrict methods | Can hide unwanted methods |

**Use Ext when:** you're adding convenience methods and the original type's API is fine. **Use newtype when:** you need to restrict, validate, or distinguish the type.

## Naming Conventions

| Pattern | Example |
|---------|---------|
| `{BaseTrait}Ext` | `AsyncReadExt`, `StreamExt`, `FutureExt`, `ServiceExt` |
| `{Type}Ext` | `RequestExt`, `PathExt`, `StrExt` |
| Crate name | `itertools::Itertools` (less common, but works) |

Stick with `{Base}Ext` unless you have a strong reason not to. It's immediately recognizable and tells users which base trait or type is being extended.
