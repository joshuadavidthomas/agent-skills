# Lifetime Patterns

## Elision rules in detail

The compiler applies three rules in order. If they fully determine all output lifetimes, you write nothing.

**Rule 1:** Each input reference gets a distinct lifetime parameter.
```rust
fn foo(x: &str, y: &str)
// becomes: fn foo<'a, 'b>(x: &'a str, y: &'b str)
```

**Rule 2:** If there's exactly one input lifetime, all output lifetimes get it.
```rust
fn first_word(s: &str) -> &str
// becomes: fn first_word<'a>(s: &'a str) -> &'a str
```

**Rule 3:** If `&self` or `&mut self` is an input, `self`'s lifetime is used for all outputs.
```rust
impl Parser {
    fn next_token(&self) -> &Token
    // becomes: fn next_token<'a>(&'a self) -> &'a Token
}
```

**When elision fails:** Two+ input references and no `self`. The compiler can't guess which input the output borrows from.
```rust
// WON'T COMPILE — ambiguous
fn pick(a: &str, b: &str) -> &str { todo!() }

// FIX — tell the compiler the relationship
fn pick<'a>(a: &'a str, b: &'a str) -> &'a str { todo!() }
```

## Struct lifetimes

A struct that borrows data must declare the relationship. The struct cannot outlive what it borrows from.

```rust
struct Excerpt<'a> {
    text: &'a str,
}

// The Excerpt cannot outlive the string it borrows from
let novel = String::from("Call me Ishmael. Some years ago...");
let excerpt = Excerpt { text: &novel[..16] };
// If novel drops here, excerpt would be a dangling reference → compiler error
```

### When structs should NOT have lifetimes

**Most structs should own their data.** Lifetime parameters on structs are the exception, not the rule.

Good reasons for `'a` on a struct:
- **Iterators** — borrow from the collection they iterate over
- **Views / windows** — temporary read-only projections of larger data
- **Zero-copy parsers** — borrow directly from the input buffer
- **Builder intermediate states** — borrow config during construction

If you find yourself adding `'a` to a struct because the borrow checker complains, stop and ask: should this struct own its data instead?

```rust
// PROBABLY WRONG — adding 'a to make it compile
struct UserProfile<'a> {
    name: &'a str,
    email: &'a str,
}

// PROBABLY RIGHT — User owns its data
struct UserProfile {
    name: String,
    email: String,
}
```

### Multiple lifetime parameters

Use distinct lifetimes when references have genuinely different scopes:

```rust
struct Context<'src, 'cfg> {
    source: &'src str,    // input source code — lives for the parse
    config: &'cfg Config, // config — may live longer than any parse
}
```

If all references have the same scope, one lifetime is fine. Don't add unnecessary lifetime parameters.

## `'static` — the most misunderstood lifetime

### `T: 'static` (a bound)

Means: `T` contains no non-`'static` references. **All owned types satisfy this.**

```rust
// These all satisfy T: 'static
let s: String = String::from("hello");     // owned, no references
let n: i32 = 42;                           // Copy, no references
let v: Vec<u8> = vec![1, 2, 3];           // owned, no references
```

This is why `thread::spawn` requires `F: Send + 'static` — the closure must not borrow from the spawning thread's stack. Owned values are fine.

```rust
let data = vec![1, 2, 3];
std::thread::spawn(move || {
    // data is moved (owned), satisfies 'static
    println!("{:?}", data);
});
```

### `&'static T` (a reference)

Means: a reference valid for the entire program duration. String literals and values leaked with `Box::leak` are `&'static`.

```rust
let s: &'static str = "string literal";  // baked into the binary
```

### When `'static` is wrong

If you're adding `'static` to make code compile, you're usually fighting the wrong battle:

```rust
// WRONG — restricts to only 'static data
fn process(data: &'static str) { /* ... */ todo!() }

// RIGHT — works with any lifetime
fn process(data: &str) { /* ... */ todo!() }
```

Don't use `'static` bounds on function parameters unless you genuinely need the data to outlive the current scope (spawning threads, returning from a function that creates the data, storing in a global).

## Common lifetime misconceptions (from pretzelhammer)

### `T` includes reference types

`T` is a superset of `&T` and `&mut T`. A generic `T` can be `&str`, `&mut Vec<i32>`, etc. Don't assume `T` means "owned type."

### Boxed trait objects have lifetimes

`Box<dyn Trait>` is actually `Box<dyn Trait + 'static>` — the default trait object lifetime. If the trait object holds references, you need:

```rust
// Holds references with lifetime 'a
fn make_processor<'a>(data: &'a [u8]) -> Box<dyn Process + 'a> {
    Box::new(SliceProcessor { data })
}
```

### Lifetimes don't shrink or grow at runtime

Lifetimes are a purely compile-time concept. The compiler picks a single lifetime for each annotation that satisfies all constraints. There's no runtime "lifetime tracking."

### Closures don't follow elision rules

Functions get lifetime elision. Closures do not.

```rust
fn fn_elided(x: &i32) -> &i32 { x }       // elision works
// let closure_elided = |x: &i32| -> &i32 { x }; // WON'T COMPILE

// Closures need explicit annotation or type inference from context
fn apply<F>(f: F) -> i32
where F: for<'a> Fn(&'a i32) -> &'a i32
{
    let x = 42;
    *f(&x)
}
```

## Higher-Ranked Trait Bounds (HRTB)

`for<'a>` means "for any lifetime `'a`." Used when you need a function/closure that works with any borrow, not just one specific lifetime.

```rust
// F must work with ANY lifetime, not just one specific one
fn apply_to_ref<F>(f: F) -> String
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    let owned = String::from("hello world");
    f(&owned).to_string()
}
```

You rarely write `for<'a>` directly. The compiler desugars `Fn(&str) -> &str` in trait bounds to `for<'a> Fn(&'a str) -> &'a str` automatically. You need it explicitly when:
- Writing trait bounds on associated types
- Lifetime relationships are complex in generic contexts
- You're storing closures in structs that need this flexibility

## Subtyping and variance

This is an advanced topic. Know it exists; look it up when variance errors confuse you.

- `&'a T` is **covariant** in `'a` — a longer lifetime can be used where a shorter one is expected. `&'long str` can serve as `&'short str`.
- `&'a mut T` is **invariant** in `'a` — the lifetime must match exactly.
- `T` in `&'a T` is **covariant** — `&'a SubType` can serve as `&'a SuperType`.
- `T` in `&'a mut T` is **invariant** — must be the exact type.

The practical impact: mutable references are stricter than immutable references. If you're getting confusing lifetime errors with `&mut` but not `&`, variance is usually the reason.

**Authority:** Common Rust Lifetime Misconceptions (pretzelhammer). The Rust Book ch 10.3, ch 15. Rust Reference: lifetime elision, subtyping. Effective Rust (lifetimes and borrowing).
