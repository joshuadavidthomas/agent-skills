# UB and Validity: What Unsafe Code Must Prevent

This file is a practical restatement of the Rust Reference’s “Behavior considered undefined” list, with the obligations phrased as reviewable checks. Unsafe code is correct only if it prevents UB for all safe callers.

Primary authority: Rust Reference `behavior-considered-undefined`; additional context: Rustonomicon chapters on aliasing, uninitialized memory, and casting.

## The mental model

- `unsafe` does not change what UB is; it only changes who is responsible for avoiding it.
- “It passed tests” is not evidence; UB can sit latent until the optimizer exploits it.

## 1) Pointer and reference checks

### Dangling pointers

You must not read/write through a pointer unless all bytes it points to are within the same live allocation.

Common footguns:

- Storing `ptr = vec.as_ptr()` and then pushing/reallocating the Vec before using `ptr`.
- Returning a pointer to stack data.

### Alignment

A misaligned pointer is not automatically UB; UB happens when you load/store through a place based on a misaligned pointer (Rust Reference).

Rules:

- If you need to access possibly unaligned data, use `ptr::read_unaligned` / `ptr::write_unaligned`.
- Do not create references (`&T` / `&mut T`) to misaligned data.

### Creating references from raw pointers

Creating a reference is a strong claim: non-null, aligned, points to a valid initialized `T`, and obeys aliasing rules.

Bad (creates `&mut` without uniqueness proof):

```rust
unsafe fn bad(p: *mut u32) -> &'static mut u32 {
    &mut *p
}
```

Good (often: don’t create a reference at all; keep raw pointers internal, expose safe APIs):

```rust
pub fn write_at(p: *mut u32, v: u32) {
    // SAFETY: caller must ensure p is non-null, aligned, and points to a live u32 for the duration of this call.
    unsafe { p.write(v) }
}
```

If you must create a reference, ensure the reference does not outlive the proven validity window.

## 2) Invalid values (immediate UB)

The compiler assumes values are valid for their type. Producing an invalid value is immediate UB (Rust Reference).

Examples:

- `bool` must be 0 or 1. Reading a random byte into a bool via transmute is UB.
- Enums must have a valid discriminant.
- `char` must be a valid Unicode scalar value.
- References and `Box<T>` must be non-null, aligned, non-dangling, and (for wide pointers) have valid metadata.

Bad:

```rust
let b: bool = unsafe { std::mem::transmute(2u8) }; // UB
```

Good:

```rust
let b = match byte {
    0 => false,
    1 => true,
    _ => return Err(ParseError::InvalidBool(byte)),
};
```

## 3) Uninitialized memory

Reading uninitialized memory as a typed value is UB, except for limited cases like reading union fields or padding bytes (see Rust Reference validity note).

Rules:

- Allocate uninitialized storage with `MaybeUninit<T>`.
- Initialize every field/element before calling `assume_init`.
- If you must do partial initialization of arrays/slices, use a guard to drop only initialized elements on panic.

## 4) Aliasing and `UnsafeCell`

Rust’s aliasing rules are subtle and not fully specified, but the operational guidance is stable enough to write sound code:

- While a shared reference `&T` is live, the referenced bytes must not be mutated, except through `UnsafeCell`.
- A mutable reference `&mut T` must be unique for its live range: no other reads/writes through other pointers not derived from it.

Practical rules:

- Do not create overlapping `&mut` references into the same allocation.
- Do not keep `&T` alive across mutation of the same memory.
- If you need interior mutability, use `UnsafeCell<T>` at the boundary of the mutability (and then provide safe methods that synchronize/sequence access).

## 5) Data races

Data races are UB. If multiple threads can access the same memory and at least one access is a write, you must synchronize.

Rules:

- Use `Mutex`, `RwLock`, atomics, or other correct synchronization primitives.
- If you claim `Send`/`Sync`, you are asserting thread-safety properties; be able to explain them.

## 6) Function ABI and unwinding

Calling a function with the wrong ABI or unwinding across boundaries that forbid it is UB (Rust Reference).

Rules:

- Do not `transmute` function pointers across ABIs.
- For FFI, explicitly pick the correct ABI and unwind strategy (`"C"` vs `"C-unwind"`) and enforce it consistently.

## Review table: unsafe operation → required proof

| Operation | You must prove |
|----------|----------------|
| `ptr.read()` / `ptr.write()` | in-bounds live allocation, correct alignment for `T`, initialized for reads, no data race |
| `slice::from_raw_parts` | pointer valid for `len * size_of::<T>()`, alignment, initialized, `len` correct, total size <= isize::MAX |
| `Vec::from_raw_parts` | pointer came from `Vec` with the same allocator, capacity/len correct, elements initialized up to len, unique ownership |
| `&*p` / `&mut *p` | all of the above plus aliasing uniqueness constraints |
| `transmute::<A, B>` | layout and validity invariants of B hold for every possible A value used |

If you cannot write the proof as a short `// SAFETY:` comment, you do not have the proof.
