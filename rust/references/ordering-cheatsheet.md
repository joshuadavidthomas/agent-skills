# Ordering Cheatsheet

Use this as a quick mapping from intent to `Ordering`.

## Orderings at a Glance

| Ordering | Guarantees | Typical use |
|---|---|---|
| `Relaxed` | Atomicity only (no cross-thread visibility guarantees) | Counters, metrics, ID allocation, statistics |
| `Release` | Prevents prior ops from moving after this op | Producer publish/store side of a handoff |
| `Acquire` | Prevents later ops from moving before this op | Consumer load side of a handoff |
| `AcqRel` | Acquire + Release in one RMW op | Read-modify-write synchronization ops |
| `SeqCst` | Strong global order among SeqCst ops | Start here when unsure; simplify reasoning |

## Intent → Recommended Ordering

| Intent | Producer | Consumer |
|---|---|---|
| Shared stop/progress flag only | `Relaxed` store | `Relaxed` load |
| Publish data behind ready flag | `Release` store to flag | `Acquire` load of same flag |
| Atomic counter for stats | `Relaxed` fetch_add | `Relaxed` load |
| Unsure / complex interaction | `SeqCst` | `SeqCst` |

## `compare_exchange` Combinations

Remember:
- Success can be `Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`
- Failure can be `Relaxed`, `Acquire`, `SeqCst`
- Failure cannot be `Release` or `AcqRel`

Common combinations:

| Case | Success | Failure |
|---|---|---|
| Pure numeric update/counter | `Relaxed` | `Relaxed` |
| Acquire lock / transition into critical state | `Acquire` or `AcqRel` | `Relaxed` or `Acquire` |
| Strictly conservative while validating | `SeqCst` | `SeqCst` |

## When to Use Fences

Prefer encoding ordering on atomics themselves.

Use `fence` only when:
- synchronization must connect multiple atomics, and
- operation-local orderings cannot directly express the required edge.

Example reference: `reference/rust-atomics-and-locks/examples/ch3-11-fence.rs`

## Practical Downgrade Strategy

1. Make it correct with `SeqCst`.
2. Add tests/benchmarks.
3. Weaken one edge at a time (`SeqCst` → `Acquire/Release` → `Relaxed` where justified).
4. Keep a short reasoning note in code review or comments.
