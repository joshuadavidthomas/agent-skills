# Early-Stage Event Infrastructure

This reference covers how projects like BAML and django-language-server wire up Salsa event capture before they are ready to write full incrementality tests.

## BAML: Basic Callback Wiring

BAML provides a constructor that accepts an `EventCallback`, allowing tests (or the LSP) to inject a closure for event logging.

```rust
// baml_project/src/db.rs
pub type EventCallback = Box<dyn Fn(salsa::Event) + Send + Sync + 'static>;

impl ProjectDatabase {
    pub fn new_with_event_callback(callback: EventCallback) -> Self {
        Self {
            storage: salsa::Storage::new(Some(callback)),
            // ...
        }
    }
}
```

## django-language-server: Conditional Logging

django-language-server uses a `logs` field on the database struct, enabled only in `#[cfg(test)]`. It filters for `WillExecute` events and stores them as strings.

```rust
// django-language-server/crates/djls-server/src/db.rs
#[salsa::db]
#[derive(Clone)]
pub struct DjangoDatabase {
    // ...
    storage: salsa::Storage<Self>,
    #[cfg(test)]
    #[allow(dead_code)]
    logs: Arc<Mutex<Option<Vec<String>>>>,
}

#[cfg(test)]
impl Default for DjangoDatabase {
    fn default() -> Self {
        let logs = <Arc<Mutex<Option<Vec<String>>>>>::default();
        Self {
            // ...
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
```

## Mun: Scoped Event Capture [Legacy API/Architecture]

Mun uses Salsa 2018 (v0.16.1). Both `mun_hir` and `mun_codegen` have MockDatabase structs with scoped event capture using the `Option<Vec>` pattern (same as rust-analyzer):

```rust
// mun_hir/src/mock.rs, mun_codegen/src/mock.rs (identical pattern)
pub(crate) struct MockDatabase {
    storage: salsa::Storage<Self>,
    events: Mutex<Option<Vec<salsa::Event>>>,
}

impl salsa::Database for MockDatabase {
    fn salsa_event(&self, event: salsa::Event) {
        let mut events = self.events.lock();
        if let Some(events) = &mut *events {
            events.push(event);
        }
    }
}

impl MockDatabase {
    /// Capture events during closure, return them all.
    pub fn log(&self, f: impl FnOnce()) -> Vec<salsa::Event> {
        *self.events.lock() = Some(Vec::new()); // Enable capture
        f();                                     // Run code
        self.events.lock().take().unwrap()       // Extract & disable
    }

    /// Capture only WillExecute events, returning query names.
    pub fn log_executed(&self, f: impl FnOnce()) -> Vec<String> {
        let events = self.log(f);
        events.into_iter()
            .filter_map(|e| match e.kind {
                salsa::EventKind::WillExecute { database_key } => {
                    Some(format!("{:?}", database_key.debug(self)))
                }
                _ => None,
            })
            .collect()
    }
}
```

This pattern is the **scoped event capture** approach: events are only recorded between enabling and extraction. The codegen MockDatabase adds `with_single_file()` for quick test setup. Both MockDatabases follow the exact same pattern as rust-analyzer's test databases.

## The Progression of Testing

Incrementality testing typically follows this progression:

1. **First:** Get the pipeline correct (unit tests for each query).
2. **Then:** Wire up event capture infrastructure (BAML and django-language-server are here).
3. **Finally:** Write incrementality tests proving cache reuse (ty and rust-analyzer are here).

If your project has the event infrastructure but no incrementality tests, you're in good company — just don't ship a long-running LSP server without eventually verifying reuse.
