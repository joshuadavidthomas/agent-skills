# Exhaustive Matching — No Wildcard `_ =>` Arms

## The Smell

Using `_ =>` as a catch-all on enums you control, silencing the compiler when new variants are added.

```rust
// WRONG — adding a variant won't produce compile errors
match status {
    Status::Active => handle_active(),
    Status::Inactive => handle_inactive(),
    _ => handle_other(), // Swallows future variants silently
}
```

This is the most dangerous kind of "works today" code. When someone adds `Status::Suspended` next month, the compiler stays silent. The new variant falls into the wildcard arm, which may do the completely wrong thing.

## The Idiomatic Alternative

```rust
// RIGHT — compiler enforces completeness
match status {
    Status::Active => handle_active(),
    Status::Inactive => handle_inactive(),
    Status::Suspended => handle_suspended(),
}
```

Add a variant → every match that doesn't handle it becomes a compile error. This is one of Rust's most valuable safety features. Don't opt out of it.

## The Only Acceptable Uses of `_ =>`

- **Foreign `#[non_exhaustive]` types.** The library author explicitly requires a wildcard arm because they intend to add variants.
- **Primitives.** `u32`, `char`, string literals — exhaustive listing is impossible or impractical.
- **Or-patterns covering the rest.** When you've handled the special cases and the remaining N variants all get the same treatment, listing them all is better than `_ =>`, but a pragmatic `_ =>` is acceptable if N is large and the enum is foreign.

For enums you control: **list every variant. Always.**

## Combining with `matches!`

When you only need a boolean check:

```rust
// Good — still exhaustive-thinking, just concise
let is_terminal = matches!(state, State::Completed | State::Failed | State::Cancelled);
```

This doesn't trigger compiler warnings on new variants (it's a boolean expression, not a match), but it's a conscious decision to treat unknown states as non-terminal, which is usually the correct default.

## `#[non_exhaustive]` from the Author Side

If you're writing a library and your enum might gain variants:

```rust
#[non_exhaustive]
pub enum ApiError {
    RateLimited,
    Unauthorized,
    // Can add variants in future minor versions
}
```

Use deliberately — it makes the API less ergonomic for consumers. Prefer semver-major bumps when practical.

This decision applies especially to **public error enums**. Library error types commonly grow new variants as the library evolves. Marking them `#[non_exhaustive]` means adding a variant is a non-breaking change, but callers are forced into `_ =>` arms — losing the compile-time exhaustiveness you're trying to preserve. The tradeoff:

- **Small, stable error enums** → don't mark `#[non_exhaustive]`; use semver-major bumps when adding variants. Consumers get full exhaustiveness.
- **Large, evolving error enums** → mark `#[non_exhaustive]`; consumers use `_ =>` and handle unknown variants gracefully. Common for HTTP clients, database drivers, and protocol libraries.

See [error-handling.md](../error-handling.md) Rule 5 for the full guidance on error enum evolution.

## Common Source Languages

- **C / C++** — `switch` with `default:` is standard practice; no exhaustiveness checking
- **Java** — `switch` requires `default` in many contexts; enhanced switch (14+) has exhaustiveness but it's new
- **Python** — `match`/`case` (3.10+) has no exhaustiveness enforcement
- **Go** — `switch` with implicit fallthrough avoidance but no exhaustiveness checking
- **TypeScript** — discriminated unions with `never` in default enable exhaustiveness, but it's opt-in
