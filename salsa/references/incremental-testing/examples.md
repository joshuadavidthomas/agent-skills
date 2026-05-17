# Salsa Incremental Testing Examples

This reference contains complete, runnable examples of incrementality tests for various Salsa features.

## Field-Level Granularity Test

This test proves that changing one field of an input doesn't re-execute queries that depend on a different field.

```rust
#[salsa::input(debug)]
struct MyInput {
    x: u32,
    y: u32,
}

#[salsa::tracked]
fn result_depends_on_x(db: &dyn LogDatabase, input: MyInput) -> u32 {
    db.push_log(format!("result_depends_on_x({input:?})"));
    input.x(db) + 1
}

#[salsa::tracked]
fn result_depends_on_y(db: &dyn LogDatabase, input: MyInput) -> u32 {
    db.push_log(format!("result_depends_on_y({input:?})"));
    input.y(db) - 1
}

#[test]
fn test_field_granularity() {
    let mut db = LoggerDatabase::default();
    let input = MyInput::new(&db, 22, 33);

    // 1. Execute: populate caches
    assert_eq!(result_depends_on_x(&db, input), 23);
    assert_eq!(result_depends_on_y(&db, input), 32);
    db.assert_logs(expect![[r#"
        [
            "result_depends_on_x(MyInput { x: 22, y: 33 })",
            "result_depends_on_y(MyInput { x: 22, y: 33 })",
        ]"#]]);

    // 2. Mutate: change only X
    input.set_x(&mut db).to(23);

    // 3. Assert: X-dependent query re-ran, Y-dependent query did NOT
    assert_eq!(result_depends_on_x(&db, input), 24);
    db.assert_logs(expect![[r#"
        [
            "result_depends_on_x(MyInput { x: 23, y: 33 })",
        ]"#]]);

    assert_eq!(result_depends_on_y(&db, input), 32);
    db.assert_logs(expect!["[]"]); // ← EMPTY: not re-executed!
}
```

## Tracked Struct Field Backtracking

This test proves that changing an input propagates through a tracked struct but stops at unchanged fields.

```rust
#[salsa::input(debug)]
struct MyInput { field: u32 }

#[salsa::tracked(debug)]
struct MyTracked<'db> {
    x: u32,
    y: u32,
}

#[salsa::tracked]
fn create_tracked<'db>(db: &'db dyn Db, input: MyInput) -> MyTracked<'db> {
    let field = input.field(db);
    MyTracked::new(db, (field + 1) / 2, field / 2)
}

#[salsa::tracked]
fn read_x(db: &dyn LogDb, input: MyInput) -> u32 {
    db.push_log("read_x".into());
    create_tracked(db, input).x(db)
}

#[salsa::tracked]
fn read_y(db: &dyn LogDb, input: MyInput) -> u32 {
    db.push_log("read_y".into());
    create_tracked(db, input).y(db)
}

#[test]
fn test_tracked_struct_field_backtracking() {
    let mut db = LoggerDatabase::default();
    let input = MyInput::new(&db, 22);
    // x = (22+1)/2 = 11, y = 22/2 = 11

    assert_eq!(read_x(&db, input), 11);
    assert_eq!(read_y(&db, input), 11);
    db.clear_logs();

    // Change field: 22 → 23
    // New: x = (23+1)/2 = 12 (changed!), y = 23/2 = 11 (unchanged!)
    input.set_field(&mut db).to(23);

    assert_eq!(read_x(&db, input), 12);
    db.assert_logs(expect![[r#"["read_x"]"#]]); // Re-ran: x changed

    assert_eq!(read_y(&db, input), 11);
    db.assert_logs(expect!["[]"]); // Did NOT re-run: y unchanged
}
```

This demonstrates Salsa's field-level tracked struct optimization — even though `create_tracked` re-executed (its input changed), downstream queries that only read unchanged fields are not re-executed.

## Accumulator Reuse

```rust
#[salsa::accumulator]
struct Log(String);

#[salsa::tracked]
fn compute(db: &dyn LogDb, list: List) -> u32 {
    db.push_log(format!("compute({list:?})"));
    Log("visited".into()).accumulate(db);

    let value = list.value(db);
    match list.next(db) {
        Some(next) => std::cmp::max(value, compute(db, next)),
        None => value,
    }
}

#[test]
fn test_accumulator_reuse() {
    let mut db = LoggerDatabase::default();
    let l1 = List::new(&db, 1, None);
    let l2 = List::new(&db, 2, Some(l1));

    assert_eq!(compute(&db, l2), 2);
    db.clear_logs();

    // Change l1's value from 1 to 2
    l1.set_value(&mut db).to(2);

    assert_eq!(compute(&db, l2), 2);
    // compute(l2) re-ran (its dependency l1 changed)
    // But the RESULT didn't change (max(2,2) == max(2,1) == 2)
    // so downstream queries of l2 would NOT re-run
}
```
