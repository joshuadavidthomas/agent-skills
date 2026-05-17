# Salsa Memory Management: Internal Details

Detailed implementation notes and internal behaviors of Salsa's memory management levers.

## LRU Eviction Internals

### Runtime Adjustment API

Tracked functions with an `lru` attribute generate a `set_lru_capacity` method:

```rust
// Only available for functions with lru attribute
parse::set_lru_capacity(db, 256);

// Set to 0 to keep everything (effectively disables eviction)
parse::set_lru_capacity(db, 0);
```

### Zero-Cost Policy

Functions without `lru` use `NoopEviction`. This policy is a zero-sized type with inline no-op methods, ensuring that the eviction logic compiles away entirely for the majority of queries that don't need it.

### Dependency Info Survives Eviction

When a result is evicted from the LRU cache, Salsa discards the *value* but keeps the *dependency metadata*. 

If a downstream query later requests the evicted value:
1. Salsa checks if the dependencies have changed.
2. If dependencies are unchanged, Salsa re-executes the query to recompute the value.
3. This re-computation does **not** trigger a cascade of re-validations downstream if the new value is equal to the old one (or if it's `no_eq`).
4. The system remains correct while saving memory.

## Equality Comparison and Backdating

### The `no_eq` Trade-off

By default, Salsa performs "backdating": if a query re-executes but produces the same result (as determined by `Eq`), its dependents are considered valid and do not re-execute.

`no_eq` disables this check. This is beneficial when:
1. Comparison is more expensive than re-running dependents.
2. The result is almost certain to change (e.g., ASTs with byte offsets).

### Manual Garbage Collection (ArcSwap Pattern)

The `ArcSwapOption` pattern (used in Ruff/ty) allows for garbage collection *within* a single revision. This is useful for clearing large ASTs immediately after use if memory pressure is high, without waiting for the next revision boundary.

```rust
pub struct ParsedModule {
    file: File,
    inner: Arc<ArcSwapOption<IndexedModule>>,
}

impl ParsedModule {
    pub fn load(&self, db: &dyn Db) -> IndexedModule {
        if let Some(m) = self.inner.load_full() { return m; }
        // Re-parse on demand if cleared
        let m = parse(db, self.file);
        self.inner.store(Some(m.clone()));
        m
    }
    
    pub fn clear(&self) {
        self.inner.store(None);
    }
}
```

## Heap Size Tracking Internals

### shared-object tracker

When using `heap_size`, use a tracker to avoid over-counting shared `Arc` allocations:

```rust
use get_size2::{GetSize, StandardTracker};

pub fn heap_size<T: GetSize>(value: &T) -> usize {
    TRACKER.with(|tracker| {
        let mut tracker = tracker.borrow_mut();
        match tracker.as_mut() {
            Some(t) => value.get_heap_size_with_tracker(t).0,
            None => value.get_heap_size(),
        }
    })
}
```

This ensures that if multiple queries reference the same `Arc<T>`, its heap size is only counted once in the total database memory usage report.
