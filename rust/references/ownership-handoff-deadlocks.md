# Ownership-Handoff Deadlocks

Not every concurrency bug is a memory-ordering bug.

A frequent failure mode is an **exclusivity barrier** that waits for unique ownership (or clone count == 1), while your code accidentally keeps an extra owner alive.

## Pattern

### Anti-pattern: clone before entering exclusive mutation path

```rust
// Conceptual pattern (anti-pattern)
fn with_mut(&mut self) {
    // self.handle count == 1
    let handle = self.handle.clone(); // count == 2

    // Internals try to wait for exclusivity (count == 1)
    mutate_using(handle); // blocks forever waiting for itself
}
```

If mutation code waits for all other handles to drop, cloning the handle right before mutation can create a self-deadlock.

### Correct pattern: move out, do work, then restore

```rust
fn with_mut(&mut self) {
    let handle = std::mem::replace(&mut self.handle, Handle::placeholder());
    // count remains effectively unique from the exclusivity check's perspective

    let mut state = into_mutable_state(handle);
    do_mutation(&mut state);

    self.handle = state.into_handle();
}
```

The key is **ownership transfer**, not cloning.

## Salsa Case Study

Salsa's mutation path sets cancellation, then waits until the clone count returns to 1 before mutating. LSP hosts that keep extra snapshots alive can accidentally extend that wait.

This makes Salsa a clear demonstration of the general rule: if an API enforces exclusivity by waiting on shared-handle counts, cloning before mutation is dangerous.

## Diagnostic Checklist

1. Does mutation code wait for uniqueness/exclusive access?
2. Did we clone a guard/handle/token just before mutation?
3. Is there any long-lived owner that prevents uniqueness from being reached?
4. Can we move ownership out (`mem::replace`, `Option::take`) instead of cloning?
5. Are fields dropped in an order that actually releases all references before waiting?

## How this relates to atomics

- This bug often appears next to atomic cancellation flags and coordination.
- But the root cause is usually **lifetime/ownership topology**, not weak ordering.
- Fix ownership first; tune orderings second.
