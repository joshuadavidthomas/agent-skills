# Salsa Framework — Durability Internals and Tests

How durability works inside Salsa, and test patterns for verifying durability behavior.

## The Shallow Verification Algorithm

Salsa maintains a 3-element array tracking the last revision each durability level changed:

```
revisions = [last_low_change, last_medium_change, last_high_change]
```

**Invariant:** `revisions[LOW] >= revisions[MEDIUM] >= revisions[HIGH]` — changing a higher durability also marks all lower ones as changed.

The actual optimization that makes durability worthwhile (from Salsa's internal `maybe_changed_after` logic):

```rust
fn shallow_verify_memo(&self, zalsa: &Zalsa, memo: &Memo<C>) -> ShallowUpdate {
    let verified_at = memo.verified_at.load();
    let revision_now = zalsa.current_revision();

    // Already verified this revision?
    if verified_at == revision_now {
        return ShallowUpdate::Verified;
    }

    // The key optimization:
    let last_changed = zalsa.last_changed_revision(memo.revisions.durability);

    if last_changed <= verified_at {
        // No input at this durability level changed since last verification.
        // Skip all dependency traversal — memo is still valid.
        ShallowUpdate::HigherDurability
    } else {
        // Need to walk dependencies (deep verification)
        ShallowUpdate::No
    }
}
```

**Example scenario:**
- Revision 1: Load stdlib (HIGH durability)
- Revision 5: Query `resolve_type()` runs, depends only on stdlib → durability=HIGH, verified_at=5
- Revisions 6–100: User edits source files (LOW durability changes)
- Revision 100: Call `resolve_type()` again
  - `last_changed_revision(HIGH) = 1`, `verified_at = 5`
  - `1 <= 5` → **Still valid! Zero dependency traversal.**

## Salsa Framework Tests

### Durability Transition Test

Tests that changing an input's durability (even without changing its value) correctly updates dependent queries:

```rust
// tests/durability.rs
#[test]
fn durable_to_less_durable() {
    let mut db = salsa::DatabaseImpl::new();

    let a = N::builder(11).value_durability(Durability::HIGH).new(&db);
    let b = N::builder(22).value_durability(Durability::HIGH).new(&db);
    let c = N::builder(33).value_durability(Durability::HIGH).new(&db);

    assert_eq!(add3(&db, a, b, c), 66);

    // Change durability from HIGH to LOW (value stays 11)
    a.set_value(&mut db).with_durability(Durability::LOW).to(11);
    assert_eq!(add3(&db, a, b, c), 66);

    // Now change the value — must propagate correctly
    a.set_value(&mut db).to(22);
    assert_eq!(add3(&db, a, b, c), 77);
}
```

### Per-Field Durability Test

```rust
// tests/input_field_durability.rs
let input = MyInput::builder(true)
    .required_field_durability(Durability::HIGH)
    .new(&db);

let input = MyInput::builder(true)
    .optional_field(20)
    .optional_field_durability(Durability::HIGH)
    .new(&db);
```

### Setter Preserves Durability Test

```rust
// tests/input_setter_preserves_durability.rs
let input = MyInput::builder(true)
    .required_field_durability(Durability::HIGH)
    .new(&db);

// Setting without explicit durability preserves HIGH
input.set_required_field(&mut db).to(false);
let last_high = db.zalsa().last_changed_revision(Durability::HIGH);

// Setting again still updates the HIGH revision
input.set_required_field(&mut db).to(false);
assert_ne!(db.zalsa().last_changed_revision(Durability::HIGH), last_high);
```
