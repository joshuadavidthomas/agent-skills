# ty — Event-Based Assertion Helpers

Incremental testing infrastructure from ruff_db (shared Ruff/ty infrastructure).

## ruff_db's Event-Based Assertion Helpers (shared infrastructure)

ruff_db provides generic helper functions that search the Salsa event stream for `WillExecute` events matching a specific query function and input ID.

### Core Helpers

```rust
use salsa::plumbing::AsId;

/// Assert that a tracked function WAS re-executed for the given input.
pub fn assert_function_query_was_run<Db, Q, QDb, I, R>(
    db: &Db,
    query: Q,
    input: I,
    events: &[salsa::Event],
) where
    Db: salsa::Database,
    Q: Fn(QDb, I) -> R,
    I: salsa::plumbing::AsId + std::fmt::Debug + Copy,
{
    let id = input.as_id();
    let (query_name, will_execute_event) = find_will_execute_event(db, query, input, events);

    db.attach(|_| {
        assert!(
            will_execute_event.is_some(),
            "Expected query {query_name}({id:?}) to have run but it did not:\n{events:#?}"
        );
    });
}

/// Assert that a tracked function was NOT re-executed for the given input.
pub fn assert_function_query_was_not_run<Db, Q, QDb, I, R>(
    db: &Db,
    query: Q,
    input: I,
    events: &[salsa::Event],
) where
    Db: salsa::Database,
    Q: Fn(QDb, I) -> R,
    I: salsa::plumbing::AsId + std::fmt::Debug + Copy,
{
    let id = input.as_id();
    let (query_name, will_execute_event) = find_will_execute_event(db, query, input, events);

    db.attach(|_| {
        if let Some(will_execute_event) = will_execute_event {
            panic!(
                "Expected query {query_name}({id:?}) not to have run but it did: \
                 {will_execute_event:?}\n\n{events:#?}"
            );
        }
    });
}

/// For tracked functions with no input parameters (singletons).
pub fn assert_const_function_query_was_not_run<Db, Q, QDb, R>(
    db: &Db,
    query: Q,
    events: &[salsa::Event],
) where
    Db: salsa::Database,
    Q: Fn(QDb) -> R,
{
    let query_name = query_name(&query);

    let event = events.iter().find(|event| {
        if let salsa::EventKind::WillExecute { database_key } = event.kind {
            db.ingredient_debug_name(database_key.ingredient_index()) == query_name
        } else {
            false
        }
    });

    db.attach(|_| {
        if let Some(will_execute_event) = event {
            panic!(
                "Expected query {query_name}() not to have run but it did: \
                 {will_execute_event:?}\n\n{events:#?}"
            );
        }
    });
}

/// Search the event stream for a WillExecute event matching the query and input.
fn find_will_execute_event<'a, Q, I>(
    db: &dyn salsa::Database,
    query: Q,
    input: I,
    events: &'a [salsa::Event],
) -> (&'static str, Option<&'a salsa::Event>)
where
    I: salsa::plumbing::AsId,
{
    let query_name = query_name(&query);

    let event = events.iter().find(|event| {
        if let salsa::EventKind::WillExecute { database_key } = event.kind {
            db.ingredient_debug_name(database_key.ingredient_index()) == query_name
                && database_key.key_index() == input.as_id()
        } else {
            false
        }
    });

    (query_name, event)
}

/// Extract the short name of a query function from its type name.
/// e.g., `crate::source::source_text` → `source_text`
fn query_name<Q>(_query: &Q) -> &'static str {
    let full_qualified_query_name = std::any::type_name::<Q>();
    full_qualified_query_name
        .rsplit_once("::")
        .map(|(_, name)| name)
        .unwrap_or(full_qualified_query_name)
}
```

### Usage Pattern

```rust
#[test]
fn test_incrementality() {
    let mut db = TestDb::new();

    let hello = Input::new(&db, "Hello, world!".to_string());
    let goodbye = Input::new(&db, "Goodbye!".to_string());

    // Populate caches
    assert_eq!(len(&db, hello), 13);
    assert_eq!(len(&db, goodbye), 8);

    // Change only one input
    goodbye.set_text(&mut db).to("Bye".to_string());
    db.clear_salsa_events();

    // Re-execute
    assert_eq!(len(&db, goodbye), 3);
    let events = db.take_salsa_events();

    // Assert
    assert_function_query_was_run(&db, len, goodbye, &events);
    assert_function_query_was_not_run(&db, len, hello, &events);
}
```

### Key Implementation Details

- Uses `std::any::type_name::<Q>()` to extract the query function name at compile time
- Matches on `database_key.ingredient_index()` (query identity) AND `database_key.key_index()` (input identity)
- Requires `db.attach()` to access the thread-local database context for debug formatting
- The `AsId` trait bound converts Salsa input/tracked/interned structs to their underlying ID

