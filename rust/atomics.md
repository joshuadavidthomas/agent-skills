# Rust Atomics and Memory Ordering

Use atomics for memory-model synchronization, not as a default replacement for `Mutex` or channels.

Default stance: make it correct first, then weaken ordering only with a written proof and measurements.

Authority: standard library `std::sync::atomic` docs, Rustonomicon atomics chapter, Rust Reference UB rules, and _Rust Atomics and Locks_.

## Start Here: Should You Use Atomics?

Before writing `Ordering` code, answer these in order:

1. Is this shared mutable state with complex invariants?
   - Yes → Use `Mutex` / `RwLock` / channels.
   - No → continue.
2. Is this a simple flag, counter, or single state transition?
   - Yes → atomics are a good fit.
3. Are you publishing data from one thread to another?
   - Yes → use Acquire/Release (or `SeqCst`).
4. Can you explain the ordering proof in one short paragraph?
   - No → use `SeqCst`.

If you need async architecture or lock-across-await guidance, see [async.md](async.md).

## Ordering Rules (Practical)

### Rule 1: Start with `SeqCst` unless you can justify weaker ordering

`SeqCst` is usually easiest to reason about across threads. Weaken only after profiling and review.

### Rule 2: `Relaxed` is for independent state, not publication

Use `Relaxed` for counters/stats/IDs where no other memory visibility depends on the value.

### Rule 3: Use Release/Acquire as a pair on the same atomic

Use `store(..., Release)` on producer and `load(..., Acquire)` on consumer when a flag publishes earlier writes.

### Rule 4: `compare_exchange` failure ordering is restricted

- Success ordering: `Relaxed`, `Acquire`, `Release`, `AcqRel`, `SeqCst`
- Failure ordering: `Relaxed`, `Acquire`, `SeqCst`
- Failure ordering cannot be `Release` or `AcqRel`

(Authority: `compare_exchange` API contract in std docs.)

See [references/ordering-cheatsheet.md](references/ordering-cheatsheet.md) for intent-to-ordering defaults.

### Rule 5: Avoid fences unless operation-local orderings cannot express the edge

Prefer expressing ordering directly on atomic operations. Use `fence` only for multi-atomic coordination with a written rationale.

## Model Protocol State Explicitly (Enum + Newtype)

Do not model multi-state protocols as loose booleans. Encode the state machine so invalid states are unrepresentable from safe APIs.

Incorrect (ambiguous state space):

```rust
use std::sync::atomic::AtomicBool;

struct WorkerFlags {
    is_ready: AtomicBool,
    is_closed: AtomicBool,
}
```

Correct (explicit state machine, private representation):

```rust
use std::sync::atomic::{AtomicU8, Ordering::{Acquire, Release}};

#[repr(u8)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum WorkerState {
    Init = 0,
    Ready = 1,
    Closed = 2,
}

struct WorkerStateCell(AtomicU8);

impl WorkerStateCell {
    fn new() -> Self {
        Self(AtomicU8::new(WorkerState::Init as u8))
    }

    fn load(&self) -> WorkerState {
        match self.0.load(Acquire) {
            0 => WorkerState::Init,
            1 => WorkerState::Ready,
            2 => WorkerState::Closed,
            tag => panic!("invalid WorkerState tag: {tag}"),
        }
    }

    fn store(&self, state: WorkerState) {
        self.0.store(state as u8, Release);
    }
}
```

Do not use `_ =>` when decoding protocol tags. Handle each valid tag explicitly and fail loudly on impossible values.

## Canonical Patterns

### Pattern A: CAS increment loop

Use when lock-free increment/update must retry under contention.

```rust
use std::sync::atomic::{AtomicU32, Ordering::Relaxed};

fn increment(a: &AtomicU32) {
    let mut current = a.load(Relaxed);
    loop {
        let new = current + 1;
        match a.compare_exchange(current, new, Relaxed, Relaxed) {
            Ok(_) => return,
            Err(observed) => current = observed,
        }
    }
}
```

Reference: `reference/rust-atomics-and-locks/examples/ch2-11-increment-with-compare-exchange.rs`

### Pattern B: Publish data with Release/Acquire flag

Incorrect (no publication edge):

```rust
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering::Relaxed};

static DATA: AtomicU64 = AtomicU64::new(0);
static READY: AtomicBool = AtomicBool::new(false);

fn broken_producer() {
    DATA.store(123, Relaxed);
    READY.store(true, Relaxed);
}

fn broken_consumer() -> Option<u64> {
    if READY.load(Relaxed) {
        Some(DATA.load(Relaxed))
    } else {
        None
    }
}
```

Correct (publication edge via Release/Acquire):

```rust
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering::{Acquire, Relaxed, Release}};

static DATA: AtomicU64 = AtomicU64::new(0);
static READY: AtomicBool = AtomicBool::new(false);

fn producer() {
    DATA.store(123, Relaxed);
    READY.store(true, Release);
}

fn consumer() -> Option<u64> {
    if READY.load(Acquire) {
        Some(DATA.load(Relaxed))
    } else {
        None
    }
}
```

Reference: `reference/rust-atomics-and-locks/examples/ch3-06-release-acquire.rs`

### Pattern C: SeqCst for global ordering sanity

Use when multiple atomics coordinate and correctness proof is unclear. Start with `SeqCst`, then weaken only with evidence.

Reference: `reference/rust-atomics-and-locks/examples/ch3-10-seqcst.rs`

### Pattern D: Ownership-handoff deadlocks (not an ordering bug)

If mutation waits for exclusive ownership (for example, waiting for clone count to drop to 1), cloning right before mutation can deadlock.

Fix: move ownership out (`mem::replace`, `Option::take`), mutate, then restore.

See [references/ownership-handoff-deadlocks.md](references/ownership-handoff-deadlocks.md) for the generic pattern and a Salsa case study.

For additional source-backed examples, see [references/patterns-from-rust-atomics-and-locks.md](references/patterns-from-rust-atomics-and-locks.md).

## Error → Design Question

| Symptom | Don’t just do | Ask instead |
|---|---|---|
| “Fails only under load” | Sprinkle `SeqCst` everywhere | Which write must become visible to which read? |
| “Works on x86, fails elsewhere” | Assume compiler bug | Did we rely on stronger hardware ordering accidentally? |
| CAS loop spins forever | Add sleeps blindly | Are success/failure orderings correct? Is the update monotonic? |
| Multiple atomics + non-atomic data | Use `Relaxed` everywhere | Where is the synchronization edge? |

## Common Unsound Patterns

- Mixing atomic and non-atomic accesses to the same shared location.
- Using `Relaxed` for publication or handoff.
- Using wildcard decoding (`_ =>`) for protocol tags stored in atomics.
- Building custom lock-free structures without a documented invariant.
- Adding `unsafe impl Send/Sync` without proving synchronization invariants.

For UB boundaries and unsafe obligations, see [references/ub-boundaries.md](references/ub-boundaries.md).

## Review Checklist

1. Is atomics the right primitive, or would a lock/channel simplify correctness?
2. Is there a clear happens-before story between producer and consumer?
3. Are all `compare_exchange` success/failure orderings valid and intentional?
4. If protocol state has more than two states, is it modeled as an enum-backed atomic wrapper instead of loose booleans?
5. Are atomic protocol tags decoded explicitly (no `_ =>` swallowing impossible states)?
6. Are we avoiding mixed atomic/non-atomic shared access?
7. If weakening from `SeqCst`, is there a benchmark and reasoning note?

## Cross-references

- [async.md](async.md) — async task scheduling, lock-across-await issues, channel architecture.
- [ownership.md](ownership.md) — `Send`/`Sync` boundaries, interior mutability tradeoffs.
- [unsafe.md](unsafe.md) — custom primitives, raw pointers, manual `Send`/`Sync` impls.
- [type-design.md](type-design.md) — enum-first domain modeling, newtypes, making illegal states unrepresentable.
- Salsa cancellation and LSP integration — Salsa host/snapshot cancellation mechanics.
