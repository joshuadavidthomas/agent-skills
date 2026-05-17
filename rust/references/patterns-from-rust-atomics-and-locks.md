# Patterns from Rust Atomics and Locks

This file maps concrete examples from `reference/rust-atomics-and-locks` to practical usage patterns.

## Core Atomic Patterns

### 1) Retry CAS loop

- File: `reference/rust-atomics-and-locks/examples/ch2-11-increment-with-compare-exchange.rs`
- Use when: lock-free update under contention.
- Key idea: load current value, attempt CAS, retry with observed value on failure.

### 2) Producer/consumer publish edge

- File: `reference/rust-atomics-and-locks/examples/ch3-06-release-acquire.rs`
- Use when: one thread writes data and signals readiness.
- Key idea: writer uses `Release` on flag; reader uses `Acquire` on same flag.

### 3) Conservative global ordering

- File: `reference/rust-atomics-and-locks/examples/ch3-10-seqcst.rs`
- Use when: multiple atomics interact and reasoning is unclear.
- Key idea: `SeqCst` establishes a stronger global order and avoids subtle weak-order bugs.

### 4) Fence-based cross-atomic coordination

- File: `reference/rust-atomics-and-locks/examples/ch3-11-fence.rs`
- Use when: visibility edge spans multiple atomics and operation-local orderings are insufficient.
- Key idea: check readiness, then `fence(Acquire)` before reading data.

## Custom Primitive Example

### Spin lock with `UnsafeCell` + atomics

- File: `reference/rust-atomics-and-locks/src/ch4_spin_lock/s3_guard.rs`
- Use when: educational/custom primitive work (not as first choice for application code).
- Key ideas:
  - `AtomicBool` controls lock state.
  - `UnsafeCell<T>` holds mutably accessed protected value.
  - Guard drop uses `Release` to unlock.
  - Requires unsafe `Sync` impl with explicit invariants.

## Practical Guidance

Prefer standard library primitives in product code:
- `Mutex`, `RwLock`, channels

Reach for custom lock-free or custom lock primitives only when:
- measured performance requires it,
- invariants are documented, and
- unsafe review/testing is in place.
