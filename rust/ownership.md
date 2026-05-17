# Ownership, Borrowing, Lifetimes

The borrow checker is not an obstacle — it's a design feedback tool. When it rejects your code, it's telling you the ownership model is unclear. Fix the design, not the symptom.

## Error → Design Question

When you hit a borrow checker error, don't reach for `clone()` first. Ask what the error is telling you about your design.

| Error | Compiler Says | Don't | Ask Instead |
|-------|--------------|-------|-------------|
| E0382 | use of moved value | `.clone()` everywhere | Who should own this data? |
| E0505 | cannot move out of `x` because it is borrowed | Drop the borrow manually | Should this function borrow or take ownership? |
| E0597 | borrowed value does not live long enough | Slap on `'static` | Is the scope boundary in the right place? |
| E0106 | missing lifetime specifier | Add `'a` and hope | What is the actual relationship between these references? |
| E0507 | cannot move out of borrowed content | `clone()` | Should the caller pass ownership instead? |
| E0716 | temporary value dropped while borrowed | `Box::leak` | Why is this a temporary? Bind it to a variable. |
| E0499 | cannot borrow as mutable more than once | `RefCell` | Can you restructure to split the borrow? |
| E0502 | cannot borrow as mutable because also borrowed as immutable | `clone()` the immutable part | Can you finish reading before writing? |

## Function Signature Rules

Function signatures are ownership contracts. Get them right and the borrow checker stays quiet.

### Rule 1: Borrow by default — own when intentional

Functions should borrow unless they need to store, return, or transfer the value. This is the single most impactful rule for reducing borrow checker fights.

**Authority:** Rust API Guidelines (caller controls allocation); Effective Rust (prefer borrowing in APIs).

```rust
// WRONG — takes ownership unnecessarily
fn contains_admin(users: Vec<User>) -> bool {
    users.iter().any(|u| u.is_admin())
}

// RIGHT — borrows; caller keeps ownership
fn contains_admin(users: &[User]) -> bool {
    users.iter().any(|u| u.is_admin())
}
```

**Take ownership when:**
- Storing the value (struct field, collection insertion)
- Transforming and returning it (builder pattern, `into_*` methods)
- Moving to another thread (`spawn`, channel `send`)
- The value is consumed and shouldn't be used again

### Rule 2: Accept the most general borrowed form

Accept `&str` not `&String`. Accept `&[T]` not `&Vec<T>`. Accept `&Path` not `&PathBuf`. The general form works with more caller types and costs nothing.

```rust
// WRONG — forces callers to have a Vec
fn sum(prices: &Vec<f64>) -> f64 { prices.iter().sum() }

// RIGHT — accepts Vec, array, slice
fn sum(prices: &[f64]) -> f64 { prices.iter().sum() }
```

| Instead of | Accept | Works with |
|-----------|--------|------------|
| `&String` | `&str` | `String`, `&str`, string literals, `Cow<'_, str>` |
| `&Vec<T>` | `&[T]` | `Vec<T>`, `[T; N]`, slices |
| `&PathBuf` | `&Path` | `PathBuf`, `&Path`, `&str`, `&OsStr` |
| `&OsString` | `&OsStr` | `OsString`, `&OsStr` |

**Authority:** Rust API Guidelines [C-CALLER-CONTROL]. clippy: `ptr_arg`.

### Rule 3: Return borrowed data from accessors

Methods exposing internal data return references. Callers who need ownership clone explicitly — let them choose.

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

### Rule 4: Use `impl Into<T>` when you need ownership but want flexible callers

When a function must own the value (storing it), accept `impl Into<T>` so callers can pass either owned or convertible types without explicit conversion.

```rust
// ACCEPTABLE — but forces callers to convert
fn new(name: String) -> User { User { name } }

// BETTER — accepts &str, String, Cow, etc.
fn new(name: impl Into<String>) -> User {
    User { name: name.into() }
}
```

Use `impl AsRef<T>` when you only need to borrow.

For the full function signature reference (AsRef, Into, Cow patterns), see [references/function-signatures.md](references/function-signatures.md).

### Rule 5: Use `Cow<'_, T>` when you *might* need to own

`Cow` borrows when it can, allocates only when it must. Use it for functions that sometimes modify their input and sometimes pass it through.

```rust
use std::borrow::Cow;

fn normalize(input: &str) -> Cow<'_, str> {
    if input.contains('\t') {
        Cow::Owned(input.replace('\t', "    "))
    } else {
        Cow::Borrowed(input)  // zero allocation in the common case
    }
}
```

## Smart Pointer Decision Tree

Don't reach for a smart pointer until you've confirmed simple ownership or borrowing won't work.

```
Do you need heap allocation?
├─ No → use stack values and references
└─ Yes
   ├─ Single owner? → Box<T>
   └─ Shared ownership?
      ├─ Single-threaded? → Rc<T>
      └─ Multi-threaded? → Arc<T>

Need to mutate shared data?
├─ Single-threaded → Rc<RefCell<T>>
└─ Multi-threaded → Arc<Mutex<T>> or Arc<RwLock<T>>

Have reference cycles?
└─ Break with Weak<T> on the back-edge
```

| Type | Ownership | Thread-safe | Cost | Use when |
|------|-----------|-------------|------|----------|
| `Box<T>` | Single | Yes (if T: Send) | One heap alloc | Recursive types, large values off stack, trait objects |
| `Rc<T>` | Shared | **No** | Reference count increment | Multiple readers, single thread, graph structures |
| `Arc<T>` | Shared | Yes | Atomic ref count | Multiple readers across threads |
| `Weak<T>` | Non-owning | Same as parent | — | Break cycles in Rc/Arc graphs |
| `Cell<T>` | Single | **No** | Copy on get | Interior mutability for `Copy` types |
| `RefCell<T>` | Single | **No** | Runtime borrow check | Interior mutability, non-`Copy` types |

**When to use `Box<T>`:**
- Recursive types (`Box` breaks infinite size): `enum List { Cons(i32, Box<List>), Nil }`
- Large structs you don't want on the stack
- Trait objects with single ownership: `Box<dyn Error>`

**When to use `Rc<T>` / `Arc<T>`:**
- Graph structures where nodes have multiple parents
- Shared configuration/context passed to many components
- Caches where multiple consumers hold a handle

For the full smart pointer reference (Weak, interior mutability patterns, when Box is unnecessary), see [references/smart-pointers.md](references/smart-pointers.md).

## Lifetime Essentials

Let the compiler infer lifetimes. Only write lifetime parameters when elision fails or when a type stores references (e.g., structs holding `&str`).

### Elision rules (when you don't need annotations)

The compiler applies these rules in order. If they fully determine output lifetimes, you write nothing.

1. Each input reference gets its own lifetime parameter.
2. If there's exactly one input lifetime, it's assigned to all outputs.
3. If one input is `&self` or `&mut self`, `self`'s lifetime is assigned to all outputs.

```rust
// Rule 2 applies — one input lifetime, used for output
fn first_word(s: &str) -> &str { /* ... */ todo!() }
// Compiler sees: fn first_word<'a>(s: &'a str) -> &'a str

// Rule 3 applies — self's lifetime used for output
impl MyStruct {
    fn name(&self) -> &str { /* ... */ todo!() }
    // Compiler sees: fn name<'a>(&'a self) -> &'a str { ... }
}
```

### When you DO need annotations

Annotate when the compiler can't determine which input lifetime the output borrows from:

```rust
// Two input references, compiler can't guess which one the output borrows from
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

Annotate structs that hold references:
```rust
struct Excerpt<'a> {
    text: &'a str,
}
// The struct cannot outlive the data it borrows from.
```

### Common lifetime misconceptions

These trip up both humans and agents:

**`T: 'static` does NOT mean "lives forever."** It means `T` contains no non-`'static` references. All owned types (`String`, `Vec<T>`, `i32`) are `T: 'static`. It's a bound, not a lifetime.

```rust
fn spawn_task<T: Send + 'static>(val: T) { /* ... */ todo!() }

let s = String::from("owned");
spawn_task(s);  // String: 'static — it has no references at all
```

**`&'static T` is different from `T: 'static`.** The former is a reference that lives for the entire program. The latter is a type that *could* live that long (because it doesn't borrow from anything shorter-lived).

**Don't slap `'static` on everything.** If you're adding `'static` bounds to make the compiler happy, you're probably fighting the ownership design instead of fixing it.

For the full lifetime reference (HRTB, variance, multiple lifetime parameters, struct lifetimes), see [references/lifetime-patterns.md](references/lifetime-patterns.md).

## When Clone is Fine

Clone is not a sin. It's a tool. The goal is *intentional* cloning, not *defensive* cloning.

**Clone freely when:**
- The type is `Copy` (primitives, small structs) — it's a bitwise copy, effectively free
- You're in application code and profiling hasn't identified this as a bottleneck
- The data is small and cloning is simpler than restructuring ownership
- You need independent copies that mutate separately

**Clone is a code smell when:**
- You clone to silence E0382 without understanding who should own the data
- You clone inside a hot loop on heap-allocated types
- Every function in a chain clones the same large value
- You could pass `&T` instead

```rust
// FINE — small Copy type, no heap allocation
let x: i32 = 42;
let y = x; // implicitly copied

// FINE — intentional independent copy
let mut config = base_config.clone();
config.override_with(user_prefs);

// SMELL — cloning to dodge the borrow checker
fn process(data: &Data) {
    let owned = data.clone(); // Why? Can you just borrow?
    do_something(owned);
}
```

**The rule:** If you can't explain *why* you're cloning (independent mutation, thread transfer, stored copy), it's probably a design issue. Fix the ownership model, not the symptom.

**Authority:** pretzelhammer ("Tour of Rust's Standard Library Traits" — Clone/Copy); Effective Rust (items on ownership ergonomics).

## Common Mistakes (Agent Failure Modes)

- **`clone()` as first response to E0382** → Ask who should own the data. Often the fix is to borrow, restructure, or use `Rc`/`Arc`.
- **`'static` bounds to silence lifetime errors** → `'static` restricts your API to owned types. Use proper lifetime parameters instead.
- **`&String` / `&Vec<T>` / `&PathBuf` in signatures** → Accept `&str` / `&[T]` / `&Path`. The general form is strictly better.
- **Returning `String` from accessors that could return `&str`** → Return borrowed data; let callers clone if they need ownership.
- **`Box<T>` for everything on the heap** → `Box` is for single ownership. If you need sharing, use `Rc`/`Arc`. If it fits on the stack, don't box it.
- **`RefCell` to dodge the borrow checker** → `RefCell` moves borrow checking to runtime. If your code panics on `borrow_mut()`, the design is wrong.
- **Adding lifetime parameters to every struct** → Most structs should own their data. Structs with `'a` are the exception (iterators, views, zero-copy parsers).
- **Fighting the borrow checker with unsafe** → If safe Rust won't compile your pattern, the pattern is probably wrong. Restructure first.

## Cross-References

- [references/borrow-by-default.md](references/borrow-by-default.md) — borrow-by-default API guidance
- [type-design.md](type-design.md) — Typestate transitions consume `self`, builder ownership patterns
- [error-handling.md](error-handling.md) — Owned vs borrowed data in error types
- [traits.md](traits.md) — Trait object lifetimes (`Box<dyn Trait + 'a>`), Send/Sync bounds
- [async.md](async.md) — `'static` bounds on spawned futures, Send requirements

## Review Checklist

1. **Does the function take ownership it doesn't need?** → Borrow instead. `Vec<T>` → `&[T]`, `String` → `&str`.
2. **Are signatures using the most general borrowed form?** → `&str` not `&String`, `&[T]` not `&Vec<T>`, `&Path` not `&PathBuf`.
3. **Do accessors return owned values they could borrow?** → Return `&str`, `&T`, `&[T]` from getters. Let callers clone.
4. **Is every `clone()` intentional?** → You should be able to explain *why* for each clone: independent mutation, thread transfer, stored copy.
5. **Are lifetime annotations minimal?** → Only annotate what elision can't infer. Don't add `'a` to everything.
6. **Is `'static` used correctly?** → `T: 'static` means "no borrowed data," not "lives forever." Don't use it to silence errors.
7. **Is the smart pointer choice justified?** → `Box` for single owner on heap. `Rc` for single-thread sharing. `Arc` for multi-thread. Don't default to `Arc<Mutex<T>>` when `&mut T` would work.
8. **Are `RefCell` / `Mutex` uses necessary?** → Interior mutability is a last resort, not a default. Prefer restructuring to split borrows.
9. **Do structs own their data?** → Structs with lifetime parameters (`'a`) should be the exception. Iterators, views, and zero-copy parsers are the main use cases.
10. **Is unsafe used to work around the borrow checker?** → Almost never correct. Restructure the code instead.
