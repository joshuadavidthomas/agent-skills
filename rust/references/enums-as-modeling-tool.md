# Enums as the Primary Modeling Tool

Rust enums are algebraic sum types — they represent "exactly one of these variants." They carry per-variant data, enable exhaustive matching, and make invalid states unrepresentable. They are the **first tool** to reach for when modeling a domain.

## The Smell

A struct with a "kind" or "type" field plus `Option` fields that are "only valid when kind is X."

```rust
// WRONG — invalid states are representable
struct Event {
    kind: EventKind,
    x: Option<f64>,           // Only valid for Click
    y: Option<f64>,           // Only valid for Click
    key: Option<KeyCode>,     // Only valid for KeyPress
    width: Option<u32>,       // Only valid for Resize
    height: Option<u32>,      // Only valid for Resize
}

enum EventKind { Click, KeyPress, Resize }

// What's event.key when kind is Click? None? What if someone sets it?
// What's event.x when kind is Resize? The type allows it.
```

## The Idiomatic Alternative

```rust
// RIGHT — each variant carries exactly the data it needs
enum Event {
    Click { x: f64, y: f64 },
    KeyPress { key: KeyCode, modifiers: Modifiers },
    Resize { width: u32, height: u32 },
}

match event {
    Event::Click { x, y } => handle_click(x, y),
    Event::KeyPress { key, modifiers } => handle_key(key, modifiers),
    Event::Resize { width, height } => handle_resize(width, height),
}
```

No `Option` fields. No invalid combinations. Pattern matching handles each case.

## State Machines

Enums naturally represent state machines where different states have different data.

```rust
enum Order {
    Draft { items: Vec<Item> },
    Submitted { items: Vec<Item>, submitted_at: DateTime<Utc> },
    Paid { items: Vec<Item>, submitted_at: DateTime<Utc>, payment: Payment },
    Shipped { tracking: TrackingNumber, shipped_at: DateTime<Utc> },
    Delivered { tracking: TrackingNumber, delivered_at: DateTime<Utc> },
    Cancelled { reason: String, cancelled_at: DateTime<Utc> },
}
```

Just from the type, you know:
- A `Draft` has no timestamp (it hasn't been submitted)
- A `Paid` order always has payment info
- A `Shipped` order always has tracking
- You can't access `tracking` on a `Draft` — it doesn't exist

Transition functions consume the current state and produce the next:

```rust
impl Order {
    fn ship(self, tracking: TrackingNumber) -> Result<Order, OrderError> {
        match self {
            Order::Paid { .. } => Ok(Order::Shipped {
                tracking,
                shipped_at: Utc::now(),
            }),
            other => Err(OrderError::InvalidTransition {
                from: other.status_name(),
                to: "Shipped",
            }),
        }
    }
}
```

For compile-time transition enforcement (not just runtime), see the typestate pattern in [type-design.md](../type-design.md).

## Enum Methods and Shared Behavior

Implement methods on the enum rather than scattering match arms across the codebase:

```rust
impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
            Shape::Rectangle { width, height } => width * height,
            Shape::Triangle { base, height } => 0.5 * base * height,
        }
    }
}
```

For computed properties shared across some variants:

```rust
impl Message {
    fn sender(&self) -> Option<UserId> {
        match self {
            Message::Text { sender, .. } | Message::Image { sender, .. } => Some(*sender),
            Message::System { .. } => None,
        }
    }
}
```

## Enum vs Trait Object Decision

| Question | Enum | Trait Object |
|----------|------|-------------|
| Know all variants at compile time? | ✅ | — |
| Variants carry different data shapes? | ✅ | ❌ (common interface only) |
| Need exhaustive matching? | ✅ | ❌ |
| Need to add variants without recompilation? | ❌ | ✅ |
| Need heterogeneous collections of unknown types? | ❌ | ✅ |
| Dispatch overhead matters? | ✅ (zero-cost) | ❌ (vtable) |

**Default to enum.** Switch to trait object when the set is genuinely open.

### The Hybrid Pattern

A mostly-closed set with an escape hatch:

```rust
enum LogOutput {
    Stdout,
    Stderr,
    File(PathBuf),
    Custom(Box<dyn Write + Send>),
}
```

Exhaustive matching for common cases, trait object for extensibility. Use sparingly.

## `#[non_exhaustive]` for Library Enums

If your library enum might gain variants, mark it `#[non_exhaustive]`:

```rust
#[non_exhaustive]
pub enum DatabaseError {
    ConnectionFailed,
    QueryFailed,
    Timeout,
}
```

This forces downstream crates to include a `_ =>` arm — the one case where wildcard matching is required.

## Bool-to-Enum Migration Strategy

When you spot correlated boolean fields that should be an enum:

1. List all the boolean fields on the struct that relate to state.
2. Enumerate the valid combinations — these become your enum variants.
3. Identify data that's only meaningful in certain states — attach it to those variants.
4. Replace the booleans with a single `state: YourEnum` field.
5. Let the compiler guide you: every non-exhaustive match shows code that was implicitly assuming state relationships.

**Test for independence:** Can every combination of your boolean fields actually occur? If some combinations are impossible or nonsensical, you want an enum.

## Standard Library Evidence

| Enum | Purpose |
|------|---------|
| `Option<T>` | Presence or absence |
| `Result<T, E>` | Success or failure |
| `Cow<'a, B>` | Borrowed or owned |
| `IpAddr` | IPv4 or IPv6 |
| `Ordering` | Less, Equal, Greater |
| `Entry<K, V>` | Occupied or Vacant map entry |

## Common Source Languages

- **Python** — no algebraic data types; state tracked with attributes and flags
- **Java** — enums exist but don't carry data; "kind" + optional fields is the path of least resistance
- **Go** — no sum types at all; booleans or iota constants are the only option
- **C** — union + tag is possible but not enforced by the type system
- **TypeScript** — discriminated unions exist and are the closest analog; developers who use them adapt fastest
