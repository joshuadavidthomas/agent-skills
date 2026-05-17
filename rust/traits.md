# Trait Design and Dispatch

Do not default to `dyn Trait`. Pick the dispatch mechanism first, then design the trait to fit it.

The Rust default order:

1. **Closed set** → model it as an `enum`.
2. **Open set, concrete type known at the call site** → use generics / `impl Trait`.
3. **True type erasure** (plugins, heterogeneous collections) → use `dyn Trait`.

This is the same enum-first modeling guidance applied to trait design.

## The Central Decision: How to Dispatch

Make the dispatch choice explicitly. Use this decision path:

```
1. Is the set of variants known at compile time?
   ├─ Yes → Use an enum. Stop.
   └─ No  → Continue.

2. Is the concrete type known at each call site?
   ├─ Yes → Use generics (static dispatch).
   └─ No  → Use dyn Trait (dynamic dispatch).
```

| Mechanism | Dispatch | Allocation | Exhaustive handling | Use when |
|-----------|----------|------------|---------------------|----------|
| `enum` | `match` (direct) | None | Yes | Closed set, per-variant data, state machines |
| Generics (`impl Trait`, `T: Trait`) | Static (monomorphized) | None | N/A | Open set, type known at call site |
| `dyn Trait` | Dynamic (vtable) | Sometimes | No | Type erasure: plugins, heterogeneous collections |

Rules of thumb:
- Prefer `&dyn Trait` for parameters when you truly need dynamic dispatch and don't need ownership.
- Prefer `Box<dyn Trait>` only when you must own/store/return the erased type.

For the deep trade-offs (monomorphization costs, lifetime bounds on trait objects, performance notes), see [references/dispatch-patterns.md](references/dispatch-patterns.md).

## Object Safety (dyn-compatibility) Quick Reference

If you want `dyn Trait`, the trait must be object-safe.

**Authority:** Rust Reference (object safety / dyn compatibility).

A trait is object-safe if:

1. It does **not** require `Self: Sized` as a supertrait.
2. It has **no associated constants**.
3. Every method that is callable on `dyn Trait` is dispatchable:
   - No generic type parameters on the method.
   - Does not return bare `Self`.
   - Uses an object-safe receiver: `&self`, `&mut self`, `self: Box<Self>`, `self: Arc<Self>`, `self: Rc<Self>`, `self: Pin<&Self>`, `self: Pin<&mut Self>`, etc.

### Keep the trait object-safe by opting out specific methods

If one method would break object safety, keep the trait dyn-compatible and opt the method out:

```rust
trait Service {
    fn handle(&self, request: &str) -> String;

    fn into_inner(self) -> Self
    where
        Self: Sized;
}
```

This pattern is standard library practice (many `Iterator` methods are `where Self: Sized` so `dyn Iterator` stays usable).

### E0038: "the trait cannot be made into an object"

Do this, in order:

1. Re-check your dispatch choice. If the set is closed or known, switch to an `enum` or generics.
2. If you truly need `dyn Trait`, remove the object-safety violations:
   - Move generic methods behind `where Self: Sized`.
   - Replace `fn clone(&self) -> Self` with a boxed/cloned-erasure pattern.
   - Remove associated constants.

## Associated Types vs Generic Parameters

Use this decision rule:

- **Associated type** when each implementor has **one** natural choice.
- **Generic parameter** when a type may implement the trait in **multiple** ways.

```rust
// Associated type: one Item per iterator type.
trait MyIterator {
    type Item;
    fn next(&mut self) -> Option<Self::Item>;
}

// Generic parameter: a type can implement Add for different RHS types.
trait MyAdd<Rhs> {
    type Output;
    fn add(self, rhs: Rhs) -> Self::Output;
}
```

**Authority:** std library precedent (`Iterator` uses an associated `Item`, `Add` uses a generic `Rhs`), Rust API Guidelines (trait design sections).

## Trait Design Rules

### Rule 1: Minimize required methods

Make implementors provide a small primitive set. Build everything else as default methods.

**Authority:** `Iterator` requires `next()` and supplies dozens of default methods.

```rust
trait Summary {
    fn core_text(&self) -> &str;

    fn summarize(&self) -> String {
        let text = self.core_text();
        let mut chars = text.chars();
        let mut prefix: String = chars.by_ref().take(100).collect();
        if chars.next().is_some() {
            prefix.push('…');
        }
        prefix
    }
}
```

### Rule 2: Implement common standard traits for *value/domain* types

For domain/value types (IDs, commands, config enums, small records), derive the traits downstream code expects.

Do **not** blindly force these traits onto resource/handle types (files, sockets, locks) where the semantics are wrong.

**Authority:** Rust API Guidelines [C-COMMON-TRAITS], clippy lints, std conventions.

Default checklist for value types:
- `Debug`
- `Clone` (unless intentionally non-cloneable)
- `PartialEq`/`Eq` (when equality is meaningful)
- `Hash` when `Eq` is used as a `HashMap` key
- `Ord`/`PartialOrd` when ordering is meaningful
- `Display` for user-facing strings (don’t reuse `Debug`)

For the full checklist + consistency invariants (`Eq`↔`Hash`, `Ord` implies `Eq`, conversion trait hierarchy, `Deref` rules), see [references/standard-traits.md](references/standard-traits.md).

### Rule 3: Respect coherence (orphan rule)

You can implement a trait only if you own the trait **or** you own the type.

If you need `impl ForeignTrait for ForeignType`, wrap the type in a newtype.

```rust
use std::fmt::{self, Display};

struct PrettyVec(Vec<i32>);

impl Display for PrettyVec {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self.0)
    }
}
```

**Authority:** Rust Reference (coherence / orphan rules). Newtypes are the standard orphan-rule escape hatch.

### Rule 4: Use supertraits only when the *trait* requires them

If your trait’s methods or invariants require `Debug`, `Send`, `Sync`, etc., put them on the trait. Otherwise, put bounds on the functions that need them.

```rust
use std::fmt::Debug;

trait Drawable: Debug {
    fn draw(&self);
}
```

### Rule 5: Prefer `&self` / `&mut self` receivers

A by-value `self` receiver makes dyn usage harder and forces moves.

```rust
// WRONG for most traits: consumes the implementor
trait TransformWrong {
    fn apply(self, input: i32) -> i32;
}

// RIGHT for most traits: works for borrowed values and dyn Trait
trait Transform {
    fn apply(&self, input: i32) -> i32;
}
```

Consume `self` intentionally when that is the domain model (conversion APIs, builders, typestate transitions). When you consume `self` but still want dynamic dispatch, use `self: Box<Self>`.

## Error → Design Question

When you hit a trait-related compiler error, treat it as a design signal.

| Error | Compiler says | Do this |
|-------|--------------|---------|
| E0277 | trait bound not satisfied | Don’t pile on bounds. Decide which layer needs the capability, or change the type so the capability exists. |
| E0038 | trait cannot be made into an object | Re-check dispatch choice first. If `dyn` is required, fix object-safety violations. |
| E0119 | conflicting implementations | Your impls overlap. Narrow bounds, remove a blanket impl, or introduce a newtype boundary. |
| E0210 | orphan rule violation | Newtype the foreign type (or move the impl into the crate that owns the trait/type). |

## Pattern Catalog (use when the decision framework says “traits”)

### Sealed trait (prevent external impls)

Seal traits when external implementations would violate invariants or you need a closed set of implementors.

```rust
mod private {
    pub trait Sealed {}
}

pub trait State: private::Sealed {
    fn name(&self) -> &'static str;
}

pub struct Active;
pub struct Inactive;

impl private::Sealed for Active {}
impl private::Sealed for Inactive {}

impl State for Active { fn name(&self) -> &'static str { "active" } }
impl State for Inactive { fn name(&self) -> &'static str { "inactive" } }
```

**Authority:** Rust API Guidelines [C-SEALED].

### Extension trait (add convenience methods)

Use extension traits to keep a core trait minimal while offering a rich convenience API via defaults.

```rust
pub trait IteratorExt: Iterator {
    fn collect_vec(self) -> Vec<Self::Item>
    where
        Self: Sized,
    {
        self.collect()
    }
}

impl<I: Iterator + ?Sized> IteratorExt for I {}
```

For full patterns (blanket Ext vs sealed Ext, return-type combinators, ecosystem examples), see [references/extension-traits.md](references/extension-traits.md).

### Marker trait (proof of an invariant)

Marker traits are most useful as proofs, not capabilities.

If a marker trait means “this invariant holds”, do not allow downstream crates to assert it. Seal it (or keep it private) and implement it only at the point you establish the invariant.

```rust
mod private {
    pub trait Sealed {}
}

pub trait Validated: private::Sealed {}

pub struct ValidEmail(String);

impl private::Sealed for ValidEmail {}
impl Validated for ValidEmail {}
```

### Blanket impl (be careful: coherence impact)

Blanket impls are powerful but restrict future impl space.

```rust
use std::fmt::Display;

trait Loggable {
    fn log(&self);
}

impl<T: Display> Loggable for T {
    fn log(&self) {
        println!("[LOG] {self}");
    }
}
```

For the broader catalog (conditional impls, newtype delegation, closures vs traits, GATs, etc.), see [references/trait-patterns.md](references/trait-patterns.md).

## Common Mistakes (Agent Failure Modes)

- **`dyn Trait` as the default** → Follow the dispatch decision path. Most of the time the right answer is `enum` or generics.
- **Forcing `dyn Trait` to “be flexible”** → `dyn` is *less* flexible: you lose exhaustiveness, inlining, and usually allocate.
- **Generic parameter where an associated type belongs** → One impl per type → associated type.
- **Over-constrained bounds** → Every bound restricts callers. Require only what the function actually uses.
- **`Deref` for newtype delegation** → `Deref` is for smart pointers. Use `AsRef`, `From`/`TryFrom`, or explicit methods.
- **Marker trait used as proof but publicly implementable** → Seal it.
- **`Hash`/`Eq` inconsistency** → If you manually implement either, manually implement both to keep them consistent.
- **Returning `Box<dyn Trait>` from trait methods by default** → If you have static dispatch, prefer an associated type or return-position `impl Trait` (RPITIT) to avoid allocation. If you need `dyn Trait`, accept the box and document the cost.

## Cross-References

- [references/enums-as-modeling-tool.md](references/enums-as-modeling-tool.md) — Enum-first modeling defaults
- [type-design.md](type-design.md) — Newtype boundaries, typestate, invariants
- [ownership.md](ownership.md) — Trait object lifetimes, `Send`/`Sync` bounds, smart pointers
- [error-handling.md](error-handling.md) — `Error` as a trait, `From` conversions, `Box<dyn Error>`
- [async.md](async.md) — `Send`/`Sync` bounds on futures, `Future` trait, async trait methods

## Review Checklist

1. **Closed set?** Use an `enum`.
2. **Open set + concrete type known at the call site?** Use generics / `impl Trait`.
3. **Only then:** use `dyn Trait` for plugins, heterogeneous collections, or type erasure.
4. **Need `dyn Trait`?** Verify object safety; push non-object-safe methods behind `where Self: Sized`.
5. **Associated type vs generic param:** one impl per type → associated; multiple impls per type → generic param.
6. **Bounds minimal?** Every bound must be used.
7. **New domain/value type:** derive/implement the standard traits downstream needs (Debug/Clone/Eq/Hash/Ord/etc.) unless semantics forbid it.
8. **Orphan rule hit?** Newtype it.
9. **Need a marker trait as a proof?** Seal it.
10. **Any blanket impls?** Check coherence fallout (future impl space).
