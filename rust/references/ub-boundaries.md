# UB Boundaries for Atomics and Unsafe Concurrency

Atomics are safe APIs, but concurrency code becomes unsound quickly when unsafe code, aliasing violations, or mixed access models are involved.

## Ground Truth

- Rust Reference: `reference/rust-reference/src/behavior-considered-undefined.md`
- Rustonomicon atomics overview: `reference/rust-nomicon/src/atomics.md`

## High-Risk UB Areas

### Data races

Unsynchronized concurrent access where at least one access is a write is UB.

### Mixed atomic and non-atomic shared access

Do not read/write the same shared location atomically in one place and non-atomically elsewhere without proper synchronization.

### Aliasing violations

If you create references or mutable aliases that violate Rust aliasing rules (`&T` immutability expectations, `&mut T` uniqueness), behavior can be undefined.

### Invalid values / uninitialized reads

Unsafe manipulations that produce invalid values or read uninitialized data are UB, independent of atomics.

## `Send` / `Sync` Manual Impl Hazard

Manual `unsafe impl Send` or `unsafe impl Sync` is a proof obligation. If you cannot clearly state the synchronization invariant, do not implement it.

Related source:
- `reference/rust-book/src/ch16-04-extensible-concurrency-sync-and-send.md`

## Interior Mutability Reminder

Interior mutability types shift checks to runtime or synchronization primitives. `RefCell` is not thread-safe; use thread-safe primitives for cross-thread mutation.

Related source:
- `reference/rust-book/src/ch15-05-interior-mutability.md`

## Minimum Safety Checklist for Unsafe Concurrency

1. Is every shared mutation synchronized?
2. Is there a clear happens-before edge for visibility-sensitive reads?
3. Are aliasing rules preserved for all references?
4. Are manual `Send`/`Sync` impls justified in comments/docs?
5. Are there tests under contention and cancellation conditions?

If any answer is unclear, prefer a higher-level primitive (`Mutex`, channels) and re-evaluate.
