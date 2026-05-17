# Testing Ecosystem and Strategies

Write tests to force **correctness properties** to become explicit, checkable, and cheap to run.

## Defaults (apply unless you can justify an exception)

1. **Start with std**: `#[test]` + `assert_*` + integration tests in `tests/`. Add crates only when you can name the gap.
   **Authority:** The Rust Book ch 11.

2. **Test behavior, not wiring**: prefer real test doubles (in-memory impls, fake clock, temp dirs) over mocks.
   **Authority:** Meszaros, *xUnit Test Patterns*.

3. **One test = one property**: a test should fail for one reason. If you need multiple cases for the same property, use parameterization.
   **Authority:** Meszaros (Focused tests).

4. **Tests are parallel by default**: assume tests run concurrently; no shared mutable globals.
   **Authority:** `cargo test` executes tests in parallel unless `-- --test-threads=1`.

5. **Prefer deterministic assertions**: avoid time, randomness, and ordering sensitivity unless the point of the test is to exercise them.

## Pick the smallest tool that gives the confidence you need

Use this as your default selection table:

| You need confidence in… | Use | Add when |
|---|---|---|
| A function/type’s local behavior | Unit tests (`#[test]`) | Always |
| A crate’s public API surface | Integration tests (`tests/`) | Always for libs |
| Invariants across many inputs | **proptest** | Parsers, serializers, roundtrips, algebraic laws |
| Output stability (complex strings/JSON/diagnostics) | **insta** | Hand-written `assert_eq!` becomes brittle |
| Many cases / shared setup | **rstest** | 3+ cases or fixtures |
| Trait-based mocking | **mockall** | Only when no real test double is feasible |
| Perf regressions | **criterion** or **divan** | You have a hot path and a baseline |
| Crash/UB discovery on untrusted input | **cargo-fuzz** | Parsers/protocols/deserializers |
| Faster runner / better CI ergonomics | **cargo-nextest** | Any non-trivial suite |

If you’re testing async code, use `#[tokio::test]` and follow the runtime rules in [async.md](async.md).

## Test organization (non-negotiable structure rules)

### Unit tests: colocate

- Put unit tests in the same module/file as the code under test.
- Use `#[cfg(test)] mod tests { ... }` + `use super::*;`.

### Integration tests: `tests/`

Each file in `tests/` is a separate test **crate** (it only sees your public API).

Correct layout:

```text
my-crate/
└── tests/
    ├── api_tests.rs
    └── common/
        └── mod.rs
```

Incorrect → correct:

```text
# WRONG (becomes a test target with 0 tests)
my-crate/tests/common.rs

# RIGHT (a helper module, not a test target)
my-crate/tests/common/mod.rs
```

**Authority:** The Rust Book ch 11.

### Doc tests

- Prefer doc tests for “happy path” API examples.
- Use `no_run` for examples that shouldn’t execute (network/process).
- Avoid `ignore` (it skips compilation).

**Authority:** Rust Book ch 11; rustdoc behavior.

### Binary crates

If you want integration tests, keep logic in `src/lib.rs` and make `src/main.rs` thin.

## Test style rules

### Name tests for the property

```rust
#[test]
fn parse_rejects_empty_input() {
    // ...
}
```

### Prefer `Result`-returning tests for `?` chains

```rust
#[test]
fn parse_uses_question_mark() -> Result<(), Box<dyn std::error::Error>> {
    let n: u32 = "42".parse()?;
    assert_eq!(n, 42);
    Ok(())
}
```

Use `expect("…")` when a failure should carry a reason. Use bare `unwrap()` only when the reason is obvious from the surrounding lines.

### One property per test (split unrelated assertions)

```rust
// WRONG: multiple independent properties; failure is ambiguous
#[test]
fn user_behavior_mixed() {
    let name = "alice";
    assert!(!name.is_empty());
    assert!(name.starts_with('a'));
    assert_eq!(name.to_uppercase(), "ALICE");
}

// RIGHT: each test asserts one thing
#[test]
fn name_is_non_empty() {
    assert!(!"alice".is_empty());
}

#[test]
fn name_uppercase_is_expected() {
    assert_eq!("alice".to_uppercase(), "ALICE");
}
```

## Tool playbook (use these patterns)

### rstest: fixtures + parameterization

Use **rstest** when you have shared setup or “same assertion, many inputs”.

```rust
use rstest::*;

#[derive(Clone)]
struct TestDb;

impl TestDb {
    fn new_in_memory() -> Self {
        Self
    }
}

#[fixture]
fn db() -> TestDb {
    TestDb::new_in_memory()
}

#[rstest]
#[case("", false)]
#[case("user@example.com", true)]
fn email_shape(#[case] input: &str, #[case] expected: bool, _db: TestDb) {
    let ok = input.contains('@');
    assert_eq!(ok, expected);
}
```

**Authority:** rstest docs.

### mockall: mock at the trait boundary (last resort)

Only mock when you can’t build a real test double.

```rust
use mockall::{automock, predicate::*};

#[derive(Debug, Clone, PartialEq, Eq)]
struct User {
    id: u64,
}

#[cfg_attr(test, automock)]
trait UserRepo {
    fn find(&self, id: u64) -> Option<User>;
}

struct UserService<R> {
    repo: R,
}

impl<R: UserRepo> UserService<R> {
    fn new(repo: R) -> Self {
        Self { repo }
    }

    fn exists(&self, id: u64) -> bool {
        self.repo.find(id).is_some()
    }
}

#[test]
fn exists_is_false_for_missing_user() {
    let mut repo = MockUserRepo::new();
    repo.expect_find().with(eq(42)).times(1).return_const(None);

    let svc = UserService::new(repo);
    assert!(!svc.exists(42));
}
```

**Authority:** mockall docs.

### proptest: property tests for invariants

Use **proptest** when example-based tests will miss edge cases.

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn sort_preserves_length(v in prop::collection::vec(any::<i32>(), 0..100)) {
        let mut v = v;
        let len = v.len();
        v.sort();
        prop_assert_eq!(v.len(), len);
    }
}
```

For strategies, shrinking, and `Arbitrary`, see [references/property-testing.md](references/property-testing.md).

**Authority:** proptest book.

### insta: snapshot tests for complex output

Use snapshots when the output is large, nested, or tedious to assert by hand.

```rust
#[test]
fn rendered_output_snapshot() {
    let output = format!("user={} status={}", 42, "active");
    insta::assert_snapshot!(output);
}
```

Workflow: generate → diff → accept via `cargo insta review`.

For redactions, inline snapshots, CI setup, and the mdtest pattern, see
[references/snapshot-testing.md](references/snapshot-testing.md).

**Authority:** insta docs.

### criterion/divan: benchmarks (never “bench” with `#[test]`)

- Put benchmarks in `benches/`.
- Use **criterion** for statistical rigor; use **divan** for lightweight iteration.
- Use `black_box` to prevent optimization.

See [references/benchmarking-and-fuzzing.md](references/benchmarking-and-fuzzing.md).

**Authority:** criterion/divan docs.

### cargo-fuzz: fuzz untrusted input boundaries

Fuzz anything that parses bytes/strings from the outside world.

See [references/benchmarking-and-fuzzing.md](references/benchmarking-and-fuzzing.md).

**Authority:** Rust Fuzz Book.

### nextest: fast runner and better CI

Use `cargo-nextest` as a drop-in runner for unit + integration tests.

```bash
cargo nextest run
cargo test --doc
```

**Authority:** nextest docs.

## `#[should_panic]` and `#[ignore]`

- `#[should_panic]` must include `expected = "…"` so unrelated panics don’t pass the test.
- `#[ignore]` is for slow/environment-dependent tests. Run them explicitly: `cargo test -- --ignored`.

## Common Mistakes (Agent Failure Modes)

- **Shared mutable state between tests** → tests are parallel by default; isolate setup per test.
- **`tests/common.rs` instead of `tests/common/mod.rs`** → you created a 0-test integration target.
- **Mocks everywhere** → you tested wiring, not behavior. Prefer real in-memory implementations.
- **Snapshot tests that auto-update in CI** → set `INSTA_UPDATE=no` (or rely on `CI=true`) so diffs fail.
- **Property tests with overly hand-rolled strategies** → start with `any::<T>()` / library strategies; let shrinking work.
- **Benchmarking with `#[test]` + timers** → use criterion/divan.
- **Fuzzing without a corpus** → keep interesting seeds and regressions in version control.

## Cross-References

- [type-design.md](type-design.md) — structuring test data with newtypes/enums; exhaustive matching of error variants
- [error-handling.md](error-handling.md) — testing error variants and error chains; `Result`-returning tests
- [type-design.md](type-design.md) — property testing invariants for domain types
- [async.md](async.md) — `#[tokio::test]`, async timeouts, cancellation-safe tests

## Review Checklist

1. Are you using std `#[test]`/integration tests first, and only adding crates when the gap is explicit?
2. Are unit tests colocated (`#[cfg(test)] mod tests`) and integration tests in `tests/`?
3. Are shared integration helpers in `tests/common/mod.rs` (not `tests/common.rs`)?
4. Does each test name the property it asserts?
5. Does each test assert one property (or use rstest for multiple cases)?
6. Are tests deterministic and parallel-safe (no shared mutable globals)?
7. Are you using proptest for invariants and edge cases (parsers/roundtrips/laws)?
8. Are you using insta for complex output, with `cargo insta review` as the acceptance workflow?
9. Are benchmarks done with criterion/divan (not timers inside tests), and do they use `black_box`?
10. Are untrusted input boundaries fuzzed with cargo-fuzz, with a saved corpus/regressions?
