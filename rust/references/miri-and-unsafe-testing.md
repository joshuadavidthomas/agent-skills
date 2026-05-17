# Miri and Unsafe Testing Workflow

Miri is a UB detector that executes Rust code in an interpreter with extra checks: out-of-bounds, use-after-free, uninitialized reads, alignment, basic type validity, and (experimentally) aliasing models. Authority: rust-lang/miri.

This file is not a tutorial; it is the default workflow for validating unsafe abstractions.

## 1) When to use Miri

Use Miri when:

- You wrote or changed unsafe code.
- You provide a safe wrapper around raw pointers, manual initialization, or `Send`/`Sync` claims.
- A test fails nondeterministically and you suspect UB.

Do not expect Miri to prove soundness; it can only find UB in explored executions. If Miri finds UB, your code is unsound. If it finds nothing, you still need contracts, reviews, and more tests.

## 2) Local usage

Install Miri (nightly):

```sh
rustup +nightly component add miri
cargo +nightly miri setup
```

Run tests under Miri:

```sh
cargo +nightly miri test
```

Run a specific test:

```sh
cargo +nightly miri test my_test_name
```

Run a binary:

```sh
cargo +nightly miri run --bin my_bin
```

## 3) Explore more executions (nondeterminism)

Miri can vary schedules and allocation addresses via seeds. This is useful for catching bugs that depend on “incidental alignment” or specific thread interleavings.

```sh
MIRIFLAGS="-Zmiri-many-seeds=0..16" cargo +nightly miri test
```

If a bug only shows under some seeds, treat that as a real bug, not flakiness.

## 4) Handling unsupported operations

Miri intentionally isolates the program from many host APIs (networking, many syscalls, most FFI). If you hit an “unsupported operation” error, that is usually telling you your test exercised an operation Miri cannot emulate.

Patterns:

- Move OS/FFI calls behind interfaces and test the unsafe logic with pure-Rust inputs.
- Use `#[cfg_attr(miri, ignore)]` to skip tests that cannot run under Miri, but only after you have unit tests that still cover the unsafe parts.

Example:

```rust
#[test]
#[cfg_attr(miri, ignore)]
fn integration_test_that_uses_networking() {
    // ...
}
```

## 5) CI integration

Add a Miri job for crates that contain unsafe code or provide unsafe-backed safe abstractions.

GitHub Actions sketch:

```yaml
miri:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - run: rustup toolchain install nightly --component miri
    - run: cargo +nightly miri setup
    - run: cargo +nightly miri test
```

If Miri is too slow, run it on changed crates only or on a nightly schedule, but do not let unsafe code ship without it.

## 6) Complementary tools (sanitizers and fuzzing)

Miri is not the only UB signal. Prefer layered defenses:

- Sanitizers (ASan/TSan/UBSan) for native execution paths and FFI-heavy code.
- Property tests and fuzzers for unsafe abstractions: invariants tend to fail at the edges.

Route to [testing.md](../testing.md) for fuzz/property testing defaults.

## 7) What to do when Miri reports UB

- Treat the report as actionable: reduce to a minimal reproducer.
- Identify the violated invariant (alignment, initialization, aliasing, lifetime, race).
- Fix the code by strengthening the invariant in the type/API, not by “making the test pass”.
- Add a regression test that specifically would have caught the bug.

If the only way to explain “why it’s safe” is “it works in release”, the code is wrong.
