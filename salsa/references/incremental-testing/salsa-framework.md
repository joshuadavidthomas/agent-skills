# Salsa Framework — Test Infrastructure

Salsa's own test infrastructure for verifying incremental behavior.

## Salsa's Own Test Infrastructure

Salsa's test suite uses four specialized database types, each filtering for different event categories:

### LoggerDatabase — Manual Log Strings

No event capture. Tracked functions call `db.push_log()` manually.

```rust
#[salsa::db]
#[derive(Clone, Default)]
pub struct LoggerDatabase {
    storage: Storage<Self>,
    logger: Logger,
}
```

### EventLoggerDatabase — All Events

Captures every event as a debug string.

```rust
impl Default for EventLoggerDatabase {
    fn default() -> Self {
        let logger = Logger::default();
        Self {
            storage: Storage::new(Some(Box::new({
                let logger = logger.clone();
                move |event| logger.push_log(format!("{:?}", event.kind))
            }))),
            logger,
        }
    }
}
```

### ExecuteValidateLoggerDatabase — Execution vs Validation

Captures only `WillExecute`, `DidValidateMemoizedValue`, and cycle events.

```rust
move |event| match event.kind {
    salsa::EventKind::WillExecute { .. }
    | salsa::EventKind::WillIterateCycle { .. }
    | salsa::EventKind::DidFinalizeCycle { .. }
    | salsa::EventKind::DidValidateInternedValue { .. }
    | salsa::EventKind::DidValidateMemoizedValue { .. } => {
        logger.push_log(format!("salsa_event({:?})", event.kind));
    }
    _ => {}
}
```

### DiscardLoggerDatabase — Garbage Collection

Captures only `WillDiscardStaleOutput` and `DidDiscard`.

```rust
move |event| match event.kind {
    salsa::EventKind::WillDiscardStaleOutput { .. }
    | salsa::EventKind::DidDiscard { .. } => {
        logger.push_log(format!("salsa_event({:?})", event.kind));
    }
    _ => {}
}
```

All four use `db.assert_logs(expect![[...]])` for snapshot-based assertions via the `expect_test` crate.
