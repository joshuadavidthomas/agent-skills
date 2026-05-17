# `Option<bool>` and Nested Options

## The Smell

Using `Option<bool>` to represent a three-state value, or `Option<Option<T>>` for four states. The semantics are opaque.

```rust
// WRONG — what does this mean?
struct UserPreference {
    notifications: Option<bool>,  // None = ???, Some(true) = ???, Some(false) = ???
}

// WRONG — even worse
struct CacheEntry {
    value: Option<Option<String>>,  // None vs Some(None) vs Some(Some("..."))
}
```

The reader must guess or check docs for what `None` means vs `Some(false)`. Is `None` "not set"? "Use default"? "Not applicable"?

## The Idiomatic Alternative

Make each state a named variant:

```rust
enum NotificationPreference {
    Enabled,
    Disabled,
    UseAccountDefault,
}

enum CacheEntry {
    /// Key doesn't exist in cache
    Miss,
    /// Key exists but value is null/absent in source
    ExplicitNull,
    /// Key exists with a value
    Hit(String),
}
```

Now the code reads naturally:

```rust
match preference {
    NotificationPreference::Enabled => send_notification(),
    NotificationPreference::Disabled => {},
    NotificationPreference::UseAccountDefault => check_account_settings(),
}
```

## Boundary Conversion

When `Option<bool>` comes from an external source, convert it at the boundary:

```rust
impl From<Option<bool>> for NotificationPreference {
    fn from(value: Option<bool>) -> Self {
        match value {
            Some(true) => Self::Enabled,
            Some(false) => Self::Disabled,
            None => Self::UseAccountDefault,
        }
    }
}
```

## Recognizing the Pattern

Any time you see:
- `Option<bool>` — three-state value, name the states
- `Option<Option<T>>` — "missing vs null vs present"
- `Result<Option<T>, E>` — sometimes fine, but consider if absence is an error
- `(bool, bool)` tuples for state — same as the bool-to-enum smell

## When `Option<bool>` Is Fine

- **Generic code.** A generic container wrapping `Option<T>` where `T` happens to be `bool` — the `Option` has a consistent meaning ("present or absent") independent of `T`.
- **SQL interop at the ORM layer.** Nullable boolean columns map to `Option<bool>`. Convert to an enum in your domain model.

## Common Source Languages

- **SQL** — nullable booleans are common and map naturally to `Option<bool>`
- **JavaScript** — `undefined` vs `null` vs `false` is the three-state trap
- **C#** — `Nullable<bool>` / `bool?` is a standard pattern
