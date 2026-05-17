# `Option` Over Sentinel Values

## The Smell

Using magic values like `-1`, `0`, `""`, or `u32::MAX` to indicate "no value."

```rust
// WRONG — C-style sentinels
struct Employee {
    name: String,
    manager_id: i64,    // -1 means "no manager"
    department: String,  // "" means "unassigned"
    salary: u32,         // 0 means "not yet determined"
}
```

The type `i64` doesn't communicate that `-1` is special. Every function that handles `manager_id` must remember to check. Forget once, and you're querying the database for employee #-1.

## The Idiomatic Alternative

```rust
struct Employee {
    name: String,
    manager_id: Option<EmployeeId>,
    department: Option<Department>,
    salary: Option<u32>,
}
```

The compiler forces you to handle the `None` case. You literally cannot forget:

```rust
match employee.manager_id {
    Some(id) => println!("Reports to: {}", id),
    None => println!("Top-level employee"),
}
```

## `NonZero*` Types for Niche Optimization

`Option<NonZeroU64>` is the same size as `u64`. The compiler uses 0 as the internal `None` representation, but you never see that sentinel. Safety of `Option` with the memory efficiency of a sentinel.

```rust
use std::num::NonZeroU64;

struct Record {
    id: NonZeroU64,                // guaranteed non-zero
    parent_id: Option<NonZeroU64>, // same size as u64, None = no parent
}
```

## Common Replacements

| Sentinel | Type | Replacement |
|---|---|---|
| `-1` for "not found" | `i32` / `i64` | `Option<usize>` |
| `0` for "unset" | numeric types | `Option<NonZeroU32>` or `Option<u32>` |
| `""` for "no value" | `String` | `Option<String>` |
| `null` pointer | `*const T` | `Option<&T>` or `Option<NonNull<T>>` |
| `NaN` for "no result" | `f64` | `Option<f64>` |
| `u32::MAX` for "infinity" | `u32` | A dedicated enum or newtype |

## When Sentinels Are Acceptable

- **FFI boundaries.** C APIs use sentinels everywhere. Match the C convention at the FFI layer, convert to `Option` immediately inside Rust.
- **Dense arrays with known-invalid values.** Billion-element array where `Option<T>` would double the size. Wrap in a safe abstraction.
- **Wire formats.** Protocols define sentinel values. Parse them into `Option` at the deserialization boundary.

## Common Source Languages

- **C** — `NULL`, `-1`, `0` are the universal absence markers
- **C++** — `std::string::npos`, `-1` from legacy C patterns
- **Java** — `null` for references, `-1` from C habits; `Optional` exists but is underused
- **Go** — zero values serve as sentinels by design (`""`, `0`, `nil`)
