# Unsafe Rust: Soundness, Invariants, and UB Avoidance

Unsafe Rust is not a performance feature and not a borrow-checker escape hatch. It is a proof obligation.

`unsafe` means: “the compiler stops checking some rules; you must uphold them.” It does not make undefined behavior acceptable. Rust programs are incorrect if they exhibit UB, including inside `unsafe` blocks and `unsafe fn`. (Authority: Rust Reference, “Behavior considered undefined”.)

Your goal when writing unsafe code is **soundness**: no possible safe caller can trigger UB through your API. If safe code can misuse your unsafe code to cause UB, your code is unsound.

## 1) First question: do you actually need unsafe?

Do not introduce unsafe unless one of these is true:

- You are implementing a safe abstraction that cannot be expressed in safe Rust (custom allocators, intrusive collections, lock-free primitives, arena/slot-map internals, self-referential layout behind `Pin`, etc.).
- You are crossing a trust boundary where the type system cannot help (kernel/syscall boundary, hardware registers, inline asm). If this is cross-language integration (C ABI, C++, Python, JS/WASM), handle the boundary design with [interop.md](interop.md); this topic stays focused on unsafe Rust correctness (soundness, validity, aliasing, initialization).
- You need uninitialized memory / partial initialization for performance and can prove initialization before read (`MaybeUninit`).
- You are forced into raw pointer manipulation by an external representation or API.

If none apply, delete the unsafe and redesign using ownership/lifetimes/typestate. “I’m fighting the borrow checker” is an [ownership.md](ownership.md) problem, not a justification for unsafe.

## 2) Contain unsafe: smallest surface area, private by default

- Prefer **safe public APIs** with a tiny `unsafe` core inside a private module.
- Make invariants *unrepresentable* in the public API: store proofs in types, not comments.
- Keep unsafe blocks as small as possible: one unsafe block per invariant, with a single purpose.

Pattern:

```rust
pub fn push(&mut self, value: T) {
    // safe checks / bookkeeping
    unsafe { self.push_unchecked(value) }
}

unsafe fn push_unchecked(&mut self, value: T) {
    // SAFETY: caller established capacity, alignment, initialization invariants.
    // ... raw pointer writes ...
}
```

## 3) Document the contract: # Safety and // SAFETY: are mandatory

- Every `pub unsafe fn` and `pub unsafe trait` must have a rustdoc `# Safety` section that states the caller obligations precisely.
- Every `unsafe { ... }` block must have an adjacent `// SAFETY:` comment that explains why the block is sound *in this context*.
- Do not write “SAFETY: this is safe” or restate the code. State the invariant you rely on and why it holds.

Enable and satisfy these lints in codebases that use unsafe:

- `clippy::undocumented_unsafe_blocks` (requires `// SAFETY:` comments).
- `clippy::missing_safety_doc` and avoid `clippy::unnecessary_safety_doc`.
- `unsafe_op_in_unsafe_fn` (forces explicit unsafe blocks even inside `unsafe fn`, making audits tractable).

Deep dive patterns: [references/safety-comments-and-unsafe-contracts.md](references/safety-comments-and-unsafe-contracts.md).

## 4) Know the actual UB triggers (what you must prevent)

The Rust Reference’s UB list is the baseline. If your unsafe code can produce any of these from safe callers, it’s unsound (Authority: Rust Reference “Behavior considered undefined”; Rustonomicon).

### UB you should assume you can trigger accidentally

- **Dangling pointers**: use-after-free, pointer not pointing into a live allocation.
- **Misaligned access**: dereferencing or loading/storing through a misaligned pointer.
- **Invalid values**: e.g. a `bool` that is not 0/1, invalid enum discriminant, invalid `char`, invalid `&T`/`Box<T>` (null, dangling, misaligned).
- **Uninitialized reads**: reading uninitialized bytes as a typed value (except limited union/padding cases).
- **Aliasing violations**: creating references that violate Rust’s aliasing model (`&T` must not observe mutation; `&mut T` must be unique for its live range, except through `UnsafeCell`).
- **Data races**: concurrent unsynchronized access is UB, even if it “works on my machine”.

A practical UB checklist with concrete examples: [references/ub-and-validity.md](references/ub-and-validity.md).

## 5) Prefer the standard unsafe tools (and use them correctly)

### Raw pointers: prefer NonNull<T> for owned/non-null pointers

- Use `NonNull<T>` when null is not a valid state; it makes the invariant explicit.
- Only create `&T` / `&mut T` from a raw pointer when you can prove: non-null (for references), correct alignment, points to initialized memory of the right type, and aliasing rules are satisfied.
- Prefer `ptr::addr_of!` / `ptr::addr_of_mut!` when taking addresses in the presence of `repr(packed)` or when you must avoid creating intermediate references.

### Uninitialized memory: use MaybeUninit<T>, never “pretend init”

- Use `MaybeUninit<T>` to allocate/hold uninitialized storage.
- Do not call `assume_init` until the value is fully initialized.
- If partial initialization can panic, use a guard pattern to drop only initialized elements.

### Drop control: use ManuallyDrop<T> when you must, then re-establish invariants

- Use `ManuallyDrop<T>` to prevent automatic drop in union-like representations or when implementing custom ownership.
- After taking manual drop control, you must prove exactly-once drop and no use-after-drop.

### Layout and repr

- Use `#[repr(C)]` for FFI-facing structs/enums (but still do not assume C is safe; it only gives layout guarantees).
- Treat `#[repr(packed)]` as “no references allowed”: do not take `&field` from packed structs; use raw pointers and `read_unaligned`/`write_unaligned` where appropriate.

## 6) Ban transmute as a default

`mem::transmute` is an admission that you are bypassing type checking. It is almost always the wrong tool.

- Prefer `from_ne_bytes`/`to_ne_bytes`, `cast`/`as` where defined, `ptr::cast`, `MaybeUninit`, `bytemuck` (when you can prove POD invariants), or explicit field-by-field construction.
- If you must use transmute, isolate it in one function, document exact layout/value invariants, and cover it with Miri tests.

## 7) Test unsafe like it’s adversarial code

- Run Miri for unsafe-heavy crates: `cargo +nightly miri test`.
- Use sanitizers (ASan/TSan/UBSan) where possible for extra signal; Miri and sanitizers catch different classes.
- Add property tests and fuzzers for unsafe abstractions; if the input space is large, unit tests are not enough.

Miri workflow and CI patterns: [references/miri-and-unsafe-testing.md](references/miri-and-unsafe-testing.md).

## 8) Common mistakes (agent failure modes)

- Using `unsafe` to “fix” borrow-checker friction. Redesign with ownership/lifetimes; see [ownership.md](ownership.md).
- Writing one giant `unsafe { ... }` block with no local reasoning. Split by invariant; one `// SAFETY:` per operation.
- Creating references (`&T`/`&mut T`) from raw pointers without proving alignment, initialization, and aliasing. Prefer staying in raw-pointer land internally and exposing safe wrappers.
- Using `mem::transmute` for “parsing” bytes or flags. Parse explicitly (match/convert) or use the dedicated `from_*_bytes` APIs.
- Slapping on `unsafe impl Send/Sync` to silence the compiler. If you can’t state the concurrency invariant in a short comment, do not ship the impl.
- Taking `&packed.field` from `#[repr(packed)]` structs. Use raw pointers + `read_unaligned`/`write_unaligned`.
- Letting panics/unwinding cross a language boundary. The boundary must decide a no-unwind policy (or explicitly use an unwind-capable ABI) and translate failures into the host error mechanism; see [interop.md](interop.md) (C ABI: `references/c-ffi.md`).

Incorrect → correct examples you should expect to see in reviews:

```rust
// WRONG: transmute produces UB for any byte other than 0/1.
fn parse_bool(byte: u8) -> bool {
    unsafe { std::mem::transmute(byte) }
}
```

```rust
// RIGHT: explicit parse preserves the validity invariant.
fn parse_bool(byte: u8) -> Result<bool, u8> {
    match byte {
        0 => Ok(false),
        1 => Ok(true),
        other => Err(other),
    }
}
```

```rust
// WRONG: undocumented unsafe Send.
unsafe impl Send for MyType {}
```

```rust
// RIGHT: if you must, state the invariant in the code review surface.
// SAFETY: `MyType` does not permit aliasing mutable access across threads; all internal mutation is synchronized.
unsafe impl Send for MyType {}
```

## Cross-References

- [ownership.md](ownership.md) — borrowing, aliasing intuitions, and how to redesign without unsafe
- [type-design.md](type-design.md) — encode invariants as types so unsafe stays internal
- [performance.md](performance.md) — measure before unsafe micro-optimizations; prefer algorithm/data-structure wins
- [testing.md](testing.md) — property testing, fuzzing, and test organization for high-assurance code

## Review Checklist (run this before approving unsafe)

1. Is unsafe actually necessary, or is this masking an ownership/design problem?
2. Is the unsafe surface area minimized (private module, safe wrapper, narrow blocks)?
3. Does every unsafe block have a local `// SAFETY:` comment that states the relied-on invariants?
4. Do all `pub unsafe fn`/traits have a precise `# Safety` contract? Would a caller understand how to use it correctly?
5. Are you avoiding `transmute` and creating references from raw pointers unless strictly proven sound?
6. Are aliasing and initialization invariants explicit (often via `NonNull`, `MaybeUninit`, `UnsafeCell`, typestate)?
7. Are you respecting alignment and `repr(packed)` rules (no accidental references, unaligned reads/writes only when required)?
8. Are `Send`/`Sync` impls justified with a concurrency invariant (or avoided entirely)?
9. Is there test coverage that would actually detect UB (Miri, sanitizers, fuzz/property tests)?
10. If this is a library, can arbitrary safe callers misuse it to cause UB? If yes: redesign; do not ship unsound code.
