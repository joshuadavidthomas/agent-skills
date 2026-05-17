# Cancellation: Salsa Framework Internals

How cancellation is implemented at the framework level.

## The Cancelled Type

```rust
// src/cancelled.rs

#[derive(Debug)]
#[non_exhaustive]
pub enum Cancelled {
    Local,
    PendingWrite,
    PropagatedPanic,
}

impl Cancelled {
    #[cold]
    pub(crate) fn throw(self) -> ! {
        // resume_unwind avoids panic hooks and backtrace collection
        std::panic::resume_unwind(Box::new(self));
    }

    pub fn catch<F, T>(f: F) -> Result<T, Cancelled>
    where
        F: FnOnce() -> T + std::panic::UnwindSafe,
    {
        match std::panic::catch_unwind(f) {
            Ok(t) => Ok(t),
            Err(payload) => match payload.downcast::<Cancelled>() {
                Ok(cancelled) => Err(*cancelled),
                Err(payload) => std::panic::resume_unwind(payload), // Re-throw non-Salsa panics
            },
        }
    }
}
```

## CancellationToken (Per-Handle)

```rust
// src/zalsa_local.rs

#[derive(Default, Clone, Debug)]
pub struct CancellationToken(Arc<AtomicU8>);

impl CancellationToken {
    const CANCELLED_MASK: u8 = 0b01;
    const DISABLED_MASK: u8 = 0b10;

    pub fn cancel(&self) {
        self.0.fetch_or(Self::CANCELLED_MASK, Ordering::Relaxed);
    }

    pub fn is_cancelled(&self) -> bool {
        self.0.load(Ordering::Relaxed) & Self::CANCELLED_MASK != 0
    }

    fn should_trigger_local_cancellation(&self) -> bool {
        // Only trigger if CANCELLED bit is set and DISABLED bit is NOT set
        // (Disabled during cycle fixpoint iteration)
        self.0.load(Ordering::Relaxed) == Self::CANCELLED_MASK
    }
}
```

## Automatic Check Points

```rust
// src/function/fetch.rs — every tracked function call checks
pub(crate) fn fetch<'db, C: Configuration>(&self, db: &'db C::DbView, ...) -> &'db C::Output<'db> {
    zalsa.unwind_if_revision_cancelled(zalsa_local);
    // ... actual query execution
}

// src/zalsa.rs — the check itself
pub(crate) fn unwind_if_revision_cancelled(&self, zalsa_local: &ZalsaLocal) {
    if zalsa_local.should_trigger_local_cancellation() {
        zalsa_local.unwind_cancelled();  // throws Cancelled::Local
    }
    if self.runtime().load_cancellation_flag() {
        zalsa_local.unwind_pending_write();  // throws Cancelled::PendingWrite
    }
}
```

## Coordination for Writes

Salsa ensures that before any mutation occurs, all other handles are cancelled and their queries have finished unwinding.

```rust
// src/storage.rs

struct Coordinate {
    /// Counter of the number of clones of actor. Begins at 1.
    /// Incremented when cloned, decremented when dropped.
    clones: Mutex<usize>,
    cvar: Condvar,
}

impl<Db: Database> Storage<Db> {
    fn cancel_others(&mut self) -> &mut Zalsa {
        // 1. Set global flag — all other threads will see PendingWrite
        self.handle.zalsa_impl.runtime().set_cancellation_flag();

        // 2. Block until all other handles drop (all queries unwound)
        // Every handle (snapshot) is a clone of the original StorageHandle.
        // We wait for the clone count in the shared Coordinate to return to 1.
        let mut clones = self.handle.coordinate.clones.lock();
        while *clones != 1 {
            clones = self.handle.coordinate.cvar.wait(clones);
        }

        // 3. Uniqueness guaranteed — we can now safely get a mutable reference
        let zalsa = Arc::get_mut(&mut self.handle.zalsa_impl).unwrap();

        // 4. Reset flag — write can proceed safely
        zalsa.runtime_mut().reset_cancellation_flag();
        zalsa
    }
}
```
