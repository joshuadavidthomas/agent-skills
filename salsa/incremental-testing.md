
# Proving Incremental Reuse in Salsa

The most important property of a Salsa application is that queries are **not re-executed** when their inputs haven't changed. But memoization is invisible — you can't tell from the outside whether a function ran or used its cache. You need to observe Salsa's internal events.

## The Core Test Pattern

Every incrementality test follows the same structure:

```
1. Setup:   Create inputs, populate the database
2. Execute: Run queries to populate caches
3. Clear:   Discard accumulated events
4. Mutate:  Change one input
5. Execute: Run queries again
6. Assert:  Check which queries re-ran vs used cache
```

The key insight: **empty logs = memoization success**. If a query doesn't appear in the event stream after re-execution, Salsa returned the cached result without calling your function.

## Event Types That Matter for Testing

Salsa fires events at key execution points. The three you'll use most in tests:

| Event | Meaning | Test implication |
|-------|---------|-----------------|
| `WillExecute { database_key }` | Function is about to run | Query **was** re-executed |
| `DidValidateMemoizedValue { database_key }` | Cached result confirmed valid | Query was **not** re-executed |
| `DidSetCancellationFlag` | New revision started (fires on every `set_*` call) | Boundary marker between revisions |

Other events useful for specialized tests:

| Event | Meaning |
|-------|---------|
| `WillDiscardStaleOutput` | A tracked struct was output in the previous revision but not this one |
| `DidDiscard` | A tracked struct or memo was freed |
| `WillIterateCycle` / `DidFinalizeCycle` | Cycle fixpoint iteration started/completed |
| `DidInternValue` / `DidReuseInternedValue` / `DidValidateInternedValue` | Interned value lifecycle |

## Setting Up a Test Database with Event Capture

Salsa fires events through an optional callback passed to `Storage::new()`. Your test database captures these events into a shared vector.

### Minimal Test DB

```rust
use std::sync::{Arc, Mutex};

#[salsa::db]
#[derive(Clone)]
pub struct TestDb {
    storage: salsa::Storage<Self>,
    events: Arc<Mutex<Vec<salsa::Event>>>,
}

impl TestDb {
    pub fn new() -> Self {
        let events: Arc<Mutex<Vec<salsa::Event>>> = Default::default();
        Self {
            storage: salsa::Storage::new(Some(Box::new({
                let events = events.clone();
                move |event| {
                    events.lock().unwrap().push(event);
                }
            }))),
            events,
        }
    }

    /// Extract all captured events, clearing the buffer.
    pub fn take_events(&mut self) -> Vec<salsa::Event> {
        std::mem::take(&mut *self.events.lock().unwrap())
    }

    /// Discard captured events (call between setup and the operation under test).
    pub fn clear_events(&mut self) {
        self.take_events();
    }
}

#[salsa::db]
impl salsa::Database for TestDb {}
```

### Scoped Event Capture (rust-analyzer style)

rust-analyzer uses an `Option<Vec>` pattern for scoped capture — events are only recorded when explicitly enabled:

```rust
pub struct TestDb {
    storage: salsa::Storage<Self>,
    events: Arc<Mutex<Option<Vec<salsa::Event>>>>,
}

impl TestDb {
    /// Capture events during a closure, then return them.
    pub fn log(&self, f: impl FnOnce()) -> Vec<salsa::Event> {
        *self.events.lock().unwrap() = Some(Vec::new()); // Enable capture
        f();                                              // Run code
        self.events.lock().unwrap().take().unwrap()       // Extract & disable
    }

    /// Capture only WillExecute events, returning query names.
    pub fn log_executed(&self, f: impl FnOnce()) -> Vec<String> {
        self.log(f)
            .into_iter()
            .filter_map(|e| match e.kind {
                salsa::EventKind::WillExecute { database_key } => {
                    let name = (self as &dyn salsa::Database)
                        .ingredient_debug_name(database_key.ingredient_index());
                    Some(name.to_string())
                }
                _ => None,
            })
            .collect()
    }
}
```

This is cleaner than clear/take when you want to observe a specific operation without setup noise.

## Assertion Strategies

### Strategy 1: Manual Log Strings (Salsa's own tests)

Tracked functions push log entries manually. After re-execution, check which entries appeared:

```rust
#[salsa::tracked]
fn result_depends_on_y(db: &dyn LogDatabase, input: MyInput) -> u32 {
    db.push_log(format!("result_depends_on_y({input:?})"));
    input.y(db) - 1
}

// After mutating field X (not Y):
input.set_x(&mut db).to(23);
assert_eq!(result_depends_on_y(&db, input), 32);
db.assert_logs(expect!["[]"]); // Empty = not re-executed!
```

**Pros:** Simple, readable, no event infrastructure needed.
**Cons:** Requires modifying tracked functions with log calls, only works for your own code.

### Strategy 2: Event Stream Inspection (ruff_db's approach)

Check the event stream for `WillExecute` events matching a specific query and input:

```rust
// After mutating one input but not another:
db.clear_salsa_events();
assert_eq!(len(&db, goodbye), 3);
let events = db.take_salsa_events();

assert_function_query_was_run(&db, len, goodbye, &events);
assert_function_query_was_not_run(&db, len, hello, &events);
```

These helpers search the event stream for `WillExecute` events matching both the query function name and the input's Salsa ID. See [references/ty-patterns.md](references/incremental-testing/ty-patterns.md) for the implementation.

### Strategy 3: Execution Count (rust-analyzer's approach)

Count how many times a specific query executed during an operation:

```rust
let executed = db.log_executed(|| {
    crate_def_map(&db, krate);
});

// Assert exact counts
let n = executed.iter().filter(|it| it.contains("crate_local_def_map")).count();
assert_eq!(n, 0, "Expected crate_local_def_map to not re-run");
```

rust-analyzer wraps this in a helper that checks multiple queries and also snapshots the full log:

```rust
fn execute_assert_events(
    db: &TestDB,
    f: impl FnOnce(),
    required: &[(&str, usize)],  // (query_name_substring, expected_count)
    expect: Expect,               // Full log snapshot
) {
    let events = db.log_executed(f);
    for (event, count) in required {
        let n = events.iter().filter(|it| it.contains(event)).count();
        assert_eq!(n, *count, "Expected {event} to execute {count} times, got {n}");
    }
    expect.assert_debug_eq(&events);
}
```

**Pros:** Precise count assertions (not just ran/didn't-run), catches unexpected extra executions via full log snapshot.

### Strategy 4: Event Kind Matching (validation vs execution)

Distinguish "validated but not re-executed" from "fully re-executed":

```rust
// After a synthetic_write (bumps revision without changing data):
db.synthetic_write(Durability::LOW);
assert_eq!(tracked_fn(&db, input), 44);

db.assert_logs(expect![[r#"
    [
        "salsa_event(DidValidateMemoizedValue { database_key: tracked_fn(Id(0)) })",
    ]"#]]);
// DidValidateMemoizedValue = Salsa walked the deps, confirmed nothing changed
// WillExecute would mean it actually re-ran the function
```

## What To Test

### Always Test

- **Field-level granularity:** Changing field X doesn't re-execute queries that only read field Y
- **Tracked struct backtracking:** Intermediate tracked struct re-created but downstream unaffected when output fields match
- **Cross-query isolation:** Changing input A doesn't re-execute queries over input B

### Test When Relevant

- **Durability optimization:** LOW-durability change doesn't revalidate HIGH-durability queries
- **LRU eviction:** Evicted query re-executes correctly when called again
- **Cycle convergence:** Fixed-point iteration produces correct results and converges
- **Deletion:** Tracked structs no longer output are properly discarded

## Common Mistakes

**Forgetting to clear events before the operation under test.** Setup queries fire `WillExecute` events too. If you don't clear, you'll see setup events in your assertions and draw wrong conclusions.

**Asserting on the wrong event type.** `WillExecute` means the function ran. `DidValidateMemoizedValue` means Salsa confirmed the cache is valid (walked deps but didn't run the function). Both appear in the event stream — if you only check for `WillExecute` absence, you might miss that Salsa still did dependency-walking work.

**Not calling the query after mutation.** Salsa is lazy — changing an input doesn't trigger re-execution. You must call the query again to see whether it re-executes or uses cache.

**Testing with `synthetic_write` when you meant `set_*`.** `synthetic_write(Durability::LOW)` bumps the revision counter without changing any actual input. It's useful for testing that HIGH-durability queries aren't revalidated on LOW-durability changes. But it doesn't test real input changes.

**Snapshot tests without count assertions.** Full event log snapshots catch unexpected changes but are brittle — they break when Salsa's internal event ordering changes. Pair them with count-based assertions for the properties you actually care about.

For implementation details and complete examples, see:
- [references/examples.md](references/incremental-testing/examples.md) — Complete runnable tests for field granularity, backtracking, and accumulators
- [references/early-stage-infrastructure.md](references/incremental-testing/early-stage-infrastructure.md) — How BAML, django-language-server, and Mun [Legacy API] set up capture before writing tests
- [references/ty-patterns.md](references/incremental-testing/ty-patterns.md) — ruff_db's event-based assertion helpers
- [references/rust-analyzer-patterns.md](references/incremental-testing/rust-analyzer-patterns.md) — rust-analyzer's count-based assertion helpers
- [references/salsa-framework.md](references/incremental-testing/salsa-framework.md) — Salsa's own test infrastructure
