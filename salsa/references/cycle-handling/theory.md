# Cycle Handling Theory and API

This file contains theoretical background and API details for Salsa's cycle handling mechanism.

## The Convergence Contract

Fixed-point iteration requires three properties:

1. **Deterministic** — Same inputs → same outputs.
2. **Monotone** — Outputs are always "≥" (more refined than) the inputs in your partial order.
3. **Bounded height** — The partial order has a maximum/top value, so iteration can't go forever.

If your function oscillates between two values without converging, you'll hit the 200-iteration limit and panic.

## The Fixed-Point Mechanism

1. Query Q calls itself transitively → Salsa detects the cycle.
2. Q becomes the **cycle head** and calls `cycle_initial` → returns bottom value.
3. All cycle participants compute provisional results using this initial value.
4. When the result returns to Q, `cycle_fn` is called with the previous and new values.
5. If the new value equals the previous → **convergence**, result is final.
6. Otherwise, iterate (max 200 iterations before panic).

## The Cycle API

The `salsa::Cycle` struct passed to `cycle_fn`:

```rust
impl Cycle<'_> {
    /// Returns an iterator over all cycle head IDs.
    fn head_ids(&self) -> impl Iterator<Item = salsa::Id>;
    
    /// Returns the current query's ID.
    fn id(&self) -> salsa::Id;
    
    /// Returns the current iteration count (0-based).
    fn iteration(&self) -> u32;
}
```

Use `head_ids()` to check if a value contains types from the current cycle (e.g., to detect self-referential types). Use `iteration()` to impose custom limits.

## Attribute Signatures

### cycle_initial
Signature: `fn(db: &dyn Db, id: salsa::Id, ...params...) -> ReturnType`
Returns the **bottom** value in your partial order — the most conservative starting point.

### cycle_fn
Signature: `fn(db: &dyn Db, cycle: &salsa::Cycle, last_provisional: &ReturnType, value: ReturnType, ...params...) -> ReturnType`
Called after each iteration to decide if it should continue or stop.

### cycle_result
Signature: `fn(db: &dyn Db, id: salsa::Id, ...params...) -> ReturnType`
Used for non-iterative fallback. All participants in the cycle receive this result.
