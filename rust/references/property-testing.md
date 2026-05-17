# Property-Based Testing with proptest

Property tests verify that invariants hold across randomly generated inputs. Instead of hand-picking examples, you describe the **shape** of valid inputs and the **property** that must hold. proptest generates hundreds of cases and, when one fails, **shrinks** it to the minimal reproducing input.

## Setup

```toml
[dev-dependencies]
proptest = "1"
```

## The `proptest!` Macro

Use this macro to declare property tests. Each test function declares parameters with strategies:

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn addition_is_commutative(a in 0..1000i32, b in 0..1000i32) {
        prop_assert_eq!(a + b, b + a);
    }
}
```

**What happens:**
1. proptest generates random values for `a` and `b` using the given strategies
2. Runs the body 256 times (default, configurable)
3. On failure, shrinks inputs to find the minimal case
4. Persists the failing case to `proptest-regressions/` for regression testing

**Assertion macros inside proptest:**
- `prop_assert!(condition)` — like `assert!` but integrates with shrinking
- `prop_assert_eq!(left, right)` — like `assert_eq!` with shrinking
- `prop_assert_ne!(left, right)` — like `assert_ne!` with shrinking
- Use these instead of `assert!` / `assert_eq!` inside `proptest!` blocks

## Strategies

A strategy defines how to generate values and how to shrink them. proptest provides strategies for all standard types.

### Built-in strategies

| Type | Strategy | Example |
|------|----------|---------|
| Integer ranges | `min..max` | `0..100i32` |
| Any value of type | `any::<T>()` | `any::<String>()` |
| Regex-generated strings | `"regex"` | `"[a-z]{1,10}"` |
| Booleans | `any::<bool>()` | — |
| Options | `prop::option::of(strategy)` | `prop::option::of(0..10i32)` |
| Vectors | `prop::collection::vec(strategy, range)` | `prop::collection::vec(any::<i32>(), 0..50)` |
| HashMaps | `prop::collection::hash_map(k, v, range)` | `prop::collection::hash_map(any::<String>(), 0..10i32, 0..5)` |
| HashSets | `prop::collection::hash_set(strategy, range)` | `prop::collection::hash_set(0..100i32, 0..10)` |
| Tuples | Combine strategies in tuples | `(any::<bool>(), 0..10i32)` |
| Just a value | `Just(value)` | `Just(42)` |
| One of several values | `prop_oneof![...]` | `prop_oneof![Just(1), Just(2), Just(3)]` |

### `prop_oneof!` — weighted choice

```rust
let status_strategy = prop_oneof![
    Just(Status::Active),
    Just(Status::Inactive),
    Just(Status::Pending),
];

// With weights (10x more Active than others):
let weighted = prop_oneof![
    10 => Just(Status::Active),
    1 => Just(Status::Inactive),
    1 => Just(Status::Pending),
];
```

### Strategy combinators

Transform strategies to produce derived values:

```rust
// Map: transform the generated value
let even_numbers = (0..100i32).prop_map(|x| x * 2);

// Filter: reject values that don't match (use sparingly — slow if filter rejects often)
let non_empty = any::<String>().prop_filter("must not be empty", |s| !s.is_empty());

// FlatMap: generate a value, then use it to create another strategy
let vec_and_index = prop::collection::vec(any::<i32>(), 1..100)
    .prop_flat_map(|vec| {
        let len = vec.len();
        (Just(vec), 0..len)
    });
```

## `prop_compose!` — Reusable Strategy Builders

Build strategies for complex types by composing simpler strategies:

```rust
use proptest::prelude::*;

prop_compose! {
    fn valid_email()(
        local in "[a-z][a-z0-9]{0,15}",
        domain in "[a-z]{1,10}",
        tld in prop_oneof![Just("com"), Just("org"), Just("net")],
    ) -> String {
        format!("{}@{}.{}", local, domain, tld)
    }
}

prop_compose! {
    fn user_strategy()(
        name in "[A-Z][a-z]{1,15}",
        email in valid_email(),
        age in 18..120u8,
    ) -> User {
        User { name, email, age }
    }
}

proptest! {
    #[test]
    fn user_email_contains_at(user in user_strategy()) {
        prop_assert!(user.email.contains('@'));
    }
}
```

**Pattern:** Build small, composable strategy functions. Combine them into complex type strategies. Name them after the domain concept they generate.

## The `Arbitrary` Trait

Define a canonical strategy for a type so `any::<MyType>()` works:

```rust
use proptest::prelude::*;
use proptest::arbitrary::Arbitrary;

#[derive(Debug, Clone)]
struct Temperature {
    celsius: f64,
}

impl Arbitrary for Temperature {
    type Parameters = ();
    type Strategy = BoxedStrategy<Self>;

    fn arbitrary_with(_: Self::Parameters) -> Self::Strategy {
        (-273.15..1000.0f64)
            .prop_map(|c| Temperature { celsius: c })
            .boxed()
    }
}

// Now this works:
proptest! {
    #[test]
    fn temperature_above_absolute_zero(temp in any::<Temperature>()) {
        prop_assert!(temp.celsius >= -273.15);
    }
}
```

**When to implement `Arbitrary`:**
- The type has a natural "any valid value" concept
- Multiple tests need the same strategy
- You want `any::<MyType>()` to work

**When to use `prop_compose!` instead:**
- You need multiple strategies for the same type (e.g., valid vs invalid inputs)
- The strategy is test-specific, not universally applicable

## Shrinking

When proptest finds a failing input, it automatically shrinks it to the minimal case. Shrinking uses binary search on the `ValueTree`:

1. `simplify()` → tries a "simpler" value (smaller number, shorter string)
2. `complicate()` → steps back toward the original if simplification went too far
3. Repeat until the minimal failing case is found

**Example:** If `vec![100, 42, 99, 7, 200]` triggers a failure, proptest might shrink it to `vec![42]` — the smallest input that still fails.

**Rules for good shrinking:**
- Use `any::<T>()` and built-in strategies — they have shrinking built in
- `prop_compose!` preserves shrinking from the component strategies
- `prop_filter` and `prop_flat_map` can interfere with shrinking — use `prop_map` when possible
- Custom `ValueTree` implementations are rarely needed

## Failure Persistence

When a test fails, proptest writes the failing seed to `proptest-regressions/<test_file>.txt`. On subsequent runs, it replays that seed first, ensuring the regression is caught.

**Commit `proptest-regressions/` to version control.** These files are your property-test regression suite.

## Common Property Patterns

### Roundtrip (encode/decode)
```rust
proptest! {
    #[test]
    fn json_roundtrip(input in any::<MyStruct>()) {
        let json = serde_json::to_string(&input).unwrap();
        let output: MyStruct = serde_json::from_str(&json).unwrap();
        prop_assert_eq!(input, output);
    }
}
```

### Idempotency
```rust
proptest! {
    #[test]
    fn normalize_is_idempotent(input in any::<String>()) {
        let once = normalize(&input);
        let twice = normalize(&once);
        prop_assert_eq!(once, twice);
    }
}
```

### Oracle (compare two implementations)
```rust
proptest! {
    #[test]
    fn optimized_matches_naive(input in prop::collection::vec(any::<i32>(), 0..100)) {
        prop_assert_eq!(sort_naive(&input), sort_optimized(&input));
    }
}
```

### Invariant preservation
```rust
proptest! {
    #[test]
    fn sorted_output_is_sorted(input in prop::collection::vec(any::<i32>(), 0..100)) {
        let sorted = sort(&input);
        for window in sorted.windows(2) {
            prop_assert!(window[0] <= window[1]);
        }
    }
}
```

### No panic (crash testing)
```rust
proptest! {
    #[test]
    fn parser_never_panics(input in "\\PC*") {
        let _ = parse(&input); // just don't panic
    }
}
```

## Configuration

```rust
proptest! {
    // Run more cases for thorough testing
    #![proptest_config(ProptestConfig::with_cases(1000))]

    #[test]
    fn thorough_test(x in any::<i32>()) {
        // ...
    }
}
```

Key config options:
- `cases` — number of test cases (default: 256)
- `max_shrink_iters` — shrinking effort (default: large)
- `fork` — run in a subprocess (catches segfaults, stack overflows)

**Authority:** proptest book; Hypothesis (Python) design principles (proptest is Rust's port of the Hypothesis approach).
