# Booleans Instead of Enums

## The Smell

Using `bool` fields to track what is really a state machine, or `bool` parameters that are meaningless at the call site.

```rust
// WRONG — parameter
fn print_page(double_sided: bool, color: bool) { todo!() }
print_page(true, false); // Which is which?

// WRONG — correlated state fields
struct Connection {
    is_connected: bool,
    is_authenticated: bool,
    is_encrypting: bool,
}
// 2³ = 8 states, most of which are invalid.
// Nothing prevents is_authenticated: true while is_connected: false.
```

## The Idiomatic Alternative

### Parameters

```rust
enum Sides { Single, Double }
enum Output { Color, BlackAndWhite }

fn print_page(sides: Sides, output: Output) { todo!() }
print_page(Sides::Double, Output::BlackAndWhite); // Reads like prose
```

When a third option appears (`Sides::Booklet`), enums extend naturally. A boolean requires a breaking API change.

### State fields

```rust
enum ConnectionState {
    Disconnected,
    Connected,
    Authenticated { session_id: u64 },
    Encrypted { session_id: u64, cipher: Cipher },
}

struct Connection {
    state: ConnectionState,
}
```

Benefits:
- **Invalid states are unrepresentable.** Can't be authenticated without being connected.
- **Exhaustive matching.** Add a state → compiler tells you every place that needs updating.
- **Data attached to states.** `session_id` only exists when meaningful.

### Struct fields

```rust
// WRONG
struct DisplayProps { monochrome: bool, fg_color: RgbColor }
// What's fg_color when monochrome is true? Who enforces that?

// RIGHT
enum Color { Monochrome, Foreground(RgbColor) }
struct DisplayProps { color: Color }
```

## Migration Strategy

1. List all boolean fields on the struct that relate to state.
2. Enumerate the valid combinations — these become your enum variants.
3. Identify data meaningful only in certain states — attach it to those variants.
4. Replace the booleans with a single `state: YourEnum` field.
5. Let the compiler guide you: every non-exhaustive match shows code that was implicitly assuming state relationships.

## At Serde Boundaries

Wire formats and database schemas often use booleans. Don't let that leak into your domain model — keep the enum internally and convert at the boundary:

```rust
#[derive(serde::Deserialize)]
struct UserDto {
    is_active: bool,
}

enum UserStatus { Active, Disabled }

impl From<UserDto> for User {
    fn from(dto: UserDto) -> Self {
        let status = if dto.is_active {
            UserStatus::Active
        } else {
            UserStatus::Disabled
        };
        User { status, /* ... */ }
    }
}
```

This is the parse-don't-validate principle applied at the deserialization boundary. See [serde.md](../serde.md) for the full pattern.

## When Booleans Are Fine

- **Genuinely independent, orthogonal properties.** `is_visible` and `is_enabled` on a UI widget, where all four combinations are valid.
- **Serialization compatibility.** Wire formats use booleans — but keep the enum as your internal representation, convert at the boundary (see above).
- **Performance-critical bitfields.** Rare. Profile first.
- **FFI boundaries.** C APIs use booleans. Match the C struct, then convert.

**Test:** Can every combination of your boolean fields actually occur in practice? If some combinations are impossible or nonsensical, you want an enum.

## Common Source Languages

- **Python** — no algebraic data types; state tracked with boolean attributes
- **Java** — enums exist but don't carry data; boolean fields are the path of least resistance
- **Go** — no sum types; booleans or iota constants are the only option
- **C** — bitfields and boolean flags are idiomatic *in C*
