# rust-analyzer — Count-Based Assertion Helper

Incremental testing infrastructure from rust-analyzer.

## rust-analyzer's Count-Based Assertion Helper

rust-analyzer uses a different approach — counting executions and comparing against expected counts, combined with full event log snapshots.

### Core Helper

```rust
use expect_test::Expect;

fn execute_assert_events(
    db: &TestDB,
    f: impl FnOnce(),
    required: &[(&str, usize)],  // (query_name_substring, expected_count)
    expect: Expect,               // Full log snapshot
) {
    let events = db.log_executed(f);

    // Assert required execution counts
    for (event, count) in required {
        let n = events.iter().filter(|it| it.contains(event)).count();
        assert_eq!(
            n, *count,
            "Expected {event} to be executed {count} times, but only got {n}"
        );
    }

    // Assert full event log matches snapshot
    expect.assert_debug_eq(&events);
}
```

### hir-ty Variant (Returns Both Lists)

```rust
impl TestDB {
    pub(crate) fn log_executed(&self, f: impl FnOnce()) -> (Vec<String>, Vec<salsa::Event>) {
        let events = self.log(f);
        let executed = events
            .iter()
            .filter_map(|e| match e.kind {
                salsa::EventKind::WillExecute { database_key } => {
                    let ingredient = (self as &dyn salsa::Database)
                        .ingredient_debug_name(database_key.ingredient_index());
                    Some(ingredient.to_string())
                }
                _ => None,
            })
            .collect();
        (executed, events)
    }
}

fn execute_assert_events(
    db: &TestDB,
    f: impl FnOnce(),
    required: &[(&str, usize)],
    expect: Expect,
) {
    crate::attach_db(db, || {
        let (executed, events) = db.log_executed(f);

        for (event, count) in required {
            let n = executed.iter().filter(|it| it.contains(event)).count();
            assert_eq!(
                n, *count,
                "Expected {event} to be executed {count} times, got {n}:\n\
                 Executed: {executed:#?}\n\
                 Event log: {events:#?}",
                events = events
                    .iter()
                    .filter(|event| !matches!(
                        event.kind,
                        salsa::EventKind::WillCheckCancellation
                    ))
                    .map(|event| format!("{:?}", event.kind))
                    .collect::<Vec<_>>(),
            );
        }
        expect.assert_debug_eq(&executed);
    });
}
```

### Usage Pattern

```rust
#[test]
fn typing_inside_a_function_should_not_invalidate_def_map() {
    let (mut db, pos) = TestDB::with_position(initial_fixture);
    let krate = db.fetch_test_crate();

    // First run — everything executes
    execute_assert_events(
        &db,
        || { crate_def_map(&db, krate); },
        &[],  // No count requirements for first run
        expect![[r#"["crate_local_def_map", ...]"#]],
    );

    // Change function body (not structure)
    db.set_file_text(pos.file_id, new_text);

    // Second run — def map should NOT re-run
    execute_assert_events(
        &db,
        || { crate_def_map(&db, krate); },
        &[("crate_local_def_map", 0)],  // ← ZERO executions!
        expect![[r#"[]"#]],
    );
}
```

### Key Differences from ruff_db's Approach

| | ruff_db | rust-analyzer |
|---|---|---|
| **Matching** | Exact query name + exact input ID | Query name substring (contains) |
| **Assertion** | Binary: ran or didn't run | Count: ran exactly N times |
| **Scope** | Specific input instance | All inputs for that query |
| **Snapshot** | No (count-only) | Yes (full event log via `expect_test`) |

rust-analyzer's approach is better for queries called on many inputs (e.g., "inference ran for 3 functions, not 10"), while ruff_db's is better for testing specific input isolation ("this file's query didn't run, but that file's did").

