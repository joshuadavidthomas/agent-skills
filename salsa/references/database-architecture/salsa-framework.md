# Salsa Framework — Database Examples

Patterns from Salsa's own examples and shared testing infrastructure.

## The Calc Example: Minimal Database

The simplest complete database — good starting point:

```rust
#[salsa::db]
#[derive(Clone)]
struct CalcDatabaseImpl {
    storage: salsa::Storage<Self>,

    #[cfg(test)]
    logs: Arc<Mutex<Option<Vec<String>>>>,
}

#[cfg(test)]
impl Default for CalcDatabaseImpl {
    fn default() -> Self {
        let logs = <Arc<Mutex<Option<Vec<String>>>>>::default();
        Self {
            storage: salsa::Storage::new(Some(Box::new({
                let logs = logs.clone();
                move |event| {
                    eprintln!("Event: {event:?}");
                    if let Some(logs) = &mut *logs.lock().unwrap() {
                        if let salsa::EventKind::WillExecute { .. } = event.kind {
                            logs.push(format!("Event: {event:?}"));
                        }
                    }
                }
            }))),
            logs,
        }
    }
}

impl CalcDatabaseImpl {
    #[cfg(test)]
    pub fn enable_logging(&self) {
        let mut logs = self.logs.lock().unwrap();
        if logs.is_none() {
            *logs = Some(vec![]);
        }
    }

    #[cfg(test)]
    pub fn take_logs(&self) -> Vec<String> {
        let mut logs = self.logs.lock().unwrap();
        if let Some(logs) = &mut *logs {
            std::mem::take(logs)
        } else {
            vec![]
        }
    }
}

#[salsa::db]
impl salsa::Database for CalcDatabaseImpl {}
```

## Incrementality Test Helpers (ruff_db — shared infrastructure)

ruff_db provides reusable helpers for verifying query execution:

```rust
/// Assert a tracked function was NOT re-executed for a given input.
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
            panic!("Expected query {query_name}({id:?}) not to have run but it did: \
                    {will_execute_event:?}\n\n{events:#?}");
        }
    });
}

/// Assert a tracked function WAS re-executed for a given input.
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
```

Usage in tests:

```rust
#[test]
fn test_source_text_not_rerun_on_permission_change() {
    let mut db = TestDb::new();
    let file = write_to_db(&mut db, "/test.py", "print('hello')");

    // First execution — populates cache
    let _ = source_text(&db, file);
    db.clear_salsa_events();

    // Change only permissions, not content
    file.set_permissions(&mut db).to(Some(0o755));

    // Re-execute
    let _ = source_text(&db, file);
    let events = db.take_salsa_events();

    // source_text should NOT have re-executed (content unchanged)
    assert_function_query_was_not_run(&db, source_text, file, &events);
}
```

