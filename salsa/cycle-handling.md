
# Dealing with Cycles in Salsa

Cycles happen when query A transitively calls itself: A → B → C → A. By default, Salsa panics. Two opt-in strategies let you recover:

1. **Fixed-point iteration** (`cycle_fn` + `cycle_initial`) — Start from a bottom value, iterate until convergence. For monotone functions on a partial order with bounded height.
2. **Fallback values** (`cycle_result`) — Always return a static fallback when any cycle is detected. No iteration. Simpler but less precise.

This is fundamental to recursive analysis. ty (Python type checker) has **60+ cycle sites**, Cairo has 29, and rust-analyzer has ~15.

## Strategy 1: Fixed-Point Iteration

Use when you need precise results from recursive computations like type inference or dataflow analysis.

```rust
#[salsa::tracked(cycle_fn=my_cycle_fn, cycle_initial=my_cycle_initial)]
fn my_query(db: &dyn Db, key: MyKey) -> MyValue { ... }

fn my_cycle_initial(db: &dyn Db, _id: salsa::Id, key: MyKey) -> MyValue {
    MyValue::bottom() // e.g., Never type, empty set, usize::MAX
}

fn my_cycle_fn(db: &dyn Db, cycle: &salsa::Cycle, prev: &MyValue, curr: MyValue, key: MyKey) -> MyValue {
    if &curr == prev { curr } // Converged
    else { curr }            // Keep iterating
}
```

- **Mechanism:** See [references/theory.md](references/cycle-handling/theory.md)
- **Examples:** Shortest path, ty's divergent sentinel, Cairo's import resolution in [references/patterns.md](references/cycle-handling/patterns.md)

## Strategy 2: Fallback Values

Use when a safe default (error type, empty result) suffices. No iteration occurs.

```rust
#[salsa::tracked(cycle_result=my_fallback)]
fn my_query(db: &dyn Db, key: MyKey) -> MyValue { ... }

fn my_fallback(_db: &dyn Db, _id: salsa::Id, _key: MyKey) -> MyValue {
    MyValue::error()
}
```

- **Critical Difference:** In `cycle_result`, **all cycle participants** get their fallback values, ensuring results don't depend on call order.
- **Examples:** rust-analyzer error types, Cairo's cycle detection in [references/patterns.md](references/cycle-handling/patterns.md)

## Choosing a Strategy

| Feature | Fixed-Point (`cycle_fn` + `cycle_initial`) | Fallback (`cycle_result`) |
|---|---|---|
| **Best for** | Precise results (type inference) | Error reporting, simple defaults |
| **Complexity** | High (must prove monotonicity) | Low (trivial 5-line handler) |
| **Performance** | Up to 200 iterations | 0 iterations |
| **Real-world** | ty: 60+ sites, Fe: 5 sites | rust-analyzer: ~15 sites, Cairo: 25 sites, wgsl-analyzer [Legacy]: 2 sites |

## Critical Rules

### All Potential Cycle Heads Need Handlers
In a cycle A ↔ B, **both** must have handlers. Salsa picks the cycle head based on call order. If only A has a handler but B is called first, B becomes head and panics.

### Monotonicity is Required
For fixed-point, your `cycle_fn` must be monotone (results only get more "refined"). Oscillation causes panics at 200 iterations. ty guarantees this by **unioning** with previous results. See [references/patterns.md](references/cycle-handling/patterns.md).

### API Reference
See [references/theory.md](references/cycle-handling/theory.md) for detailed `salsa::Cycle` API and attribute signatures.

## Common Mistakes
- **Handling only one direction:** All cycle participants must have handlers.
- **Non-monotone recovery:** Ensure your iteration converges.
- **Re-entering the cycle:** Avoid triggering new computations inside handlers.
- **Over-complicating:** Use `cycle_result` if a simple error fallback is enough.
