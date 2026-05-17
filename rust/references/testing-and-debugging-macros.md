# Testing and debugging macros (cargo expand, trybuild)

Macros are code generation. You must be able to see what you generated, and you must lock in your diagnostics.

**Authority:** syn README (cargo expand + trybuild); cargo-expand docs.

## 1) Debugging expansions

### Use cargo-expand as the default tool

From a crate that *uses* the macro:

- `cargo expand` (expand the whole crate)
- `cargo expand --bin mybin`
- `cargo expand --test my_test`

Look for:

- Missing absolute paths (`::core::...`) leading to unresolved names.
- Helper identifiers colliding with user identifiers.
- Generated impls missing bounds / where-clauses.

### When cargo-expand is unavailable

Nightly rustc can show expansions (less ergonomic than cargo-expand):

- `cargo rustc -Zunpretty=expanded` (toolchain-dependent)

Prefer cargo-expand whenever possible.

## 2) Testing macros

### A) “Should compile” tests

- Create small integration test crates or test modules that use the macro in the intended ways.
- Assert runtime behavior only if the macro generates runtime code; otherwise compile-only tests are fine.

### B) “Should fail with a good diagnostic” tests (trybuild)

Use `trybuild` to lock in error messages and spans.

Skeleton:

```rust
#[test]
fn ui() {
    let t = trybuild::TestCases::new();
    t.compile_fail("tests/ui/*.rs");
    t.pass("tests/ui-pass/*.rs");
}
```

Workflow:

1. Add a failing example `tests/ui/bad_input.rs`.
2. Run tests once; trybuild writes expected `.stderr` files.
3. Commit the `.stderr` files so diagnostics are stable.

This prevents regressions where an error becomes “no rules expected this token” or points at the wrong place.

## 3) Debugging checklist

1. Can you reproduce the failure in a minimal crate that uses the macro?
2. Did you inspect the expansion (`cargo expand`) in that crate?
3. Is name resolution robust (absolute paths, no reliance on call-site imports)?
4. Are user errors returned as `syn::Error` / `compile_error!` with spans (no unwrap/panic)?
5. Is the macro deterministic (no environment-dependent behavior unless explicitly documented)?
