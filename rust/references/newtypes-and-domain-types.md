# Newtypes and Domain Types

Newtypes wrap a single inner type to create a distinct type with its own semantics. They are zero-cost — the compiler erases the wrapper. Use them everywhere you have a primitive with domain meaning.

## The Smell

Using `String` or `&str` for values that have a fixed set of possibilities or specific structure — status codes, identifiers, categories, configuration keys.

```rust
// WRONG — stringly-typed
fn send_email(to: String, subject: String, body: String) { todo!() }
// Caller can swap to/subject and the compiler won't blink.
// Typos in string values compile fine.
```

This is the most common pattern from dynamically typed languages where strings are the universal data type. In Rust, you're paying for heap allocation *and* giving up compile-time validation.

## The Three Purposes

### 1. Type Distinction — Prevent Mixing

Different quantities with the same representation must not be interchangeable.

```rust
struct Miles(f64);
struct Kilometers(f64);

fn distance_remaining(total: Miles, traveled: Miles) -> Miles {
    Miles(total.0 - traveled.0)
}

// Compiler prevents: distance_remaining(miles, kilometers)
// The Mars Climate Orbiter crash was exactly this bug.
```

No validation needed — the invariant is identity ("this is miles"), not a data constraint.

Provide explicit conversions:
```rust
impl From<Miles> for Kilometers {
    fn from(m: Miles) -> Self {
        Kilometers(m.0 * 1.60934)
    }
}
```

### 2. Invariant Enforcement — Parse at Construction

When the inner type has constraints, validate once at construction.

```rust
pub struct EmailAddress(String);

impl EmailAddress {
    pub fn new(raw: String) -> Result<Self, EmailError> {
        if !raw.contains('@') { return Err(EmailError::MissingAt); }
        Ok(Self(raw))
    }
}
// After construction, every EmailAddress is valid. No re-checking.
```

**Critical: keep the inner field private.** If callers can construct `EmailAddress("garbage".into())` directly, your invariant is meaningless. Use module boundaries to enforce privacy:

```rust
pub struct Port(u16);

impl Port {
    pub fn new(n: u16) -> Result<Self, PortError> {
        if n == 0 {
            return Err(PortError::Zero);
        }
        Ok(Self(n))
    }

    pub fn get(&self) -> u16 {
        self.0
    }
}
```

```rust
// In a module or separate file
mod network {
    pub struct Port(u16);  // Field is private to this module

    impl Port {
        pub fn new(n: u16) -> Result<Self, PortError> { /* ... */ }
        pub fn get(&self) -> u16 { self.0 }
    }
}

// Outside the module:
// network::Port(0)  // ERROR: constructor is private
// network::Port::new(0)  // Ok — returns Err(PortError::Zero)
```

### 3. Encapsulation — Hide Representation

Newtypes hide the inner type so you can change it later without breaking callers.

```rust
// Today: backed by String
pub struct Username(String);

// Tomorrow: backed by CompactString, Arc<str>, or SmolStr
// All callers still work — they never saw the String.
```

The std library does this extensively: `PathBuf` wraps `OsString`, `String` wraps `Vec<u8>`.

### For typed identifiers

```rust
// WRONG — nothing stops passing a user ID where an order ID is expected
fn get_user(id: &str) -> User { todo!() }
fn get_order(id: &str) -> Order { todo!() }

// RIGHT
struct UserId(u64);
struct OrderId(u64);

fn get_user(id: UserId) -> User { todo!() }
fn get_order(id: OrderId) -> Order { todo!() }
// get_order(user_id);  // type error: expected OrderId, found UserId
```

### For structured strings: parse at the boundary

```rust
// WRONG — passing raw strings around
fn connect(host: &str, port: &str) { todo!() }

// RIGHT — parse once, use typed values everywhere
struct SocketAddr { host: IpAddr, port: u16 }

impl SocketAddr {
    fn parse(input: &str) -> Result<Self, ParseError> { todo!() }
}
```

## Implementation Patterns

### Derive what makes sense

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(i64);
```

Don't derive traits that violate your semantics:
- `Ord` on `EmailAddress`? Probably not meaningful.
- `Default` on `Port`? Only if zero/empty is valid.
- `Copy` on large newtypes? Avoid — prefer explicit cloning.

### Implement standard traits for interop

```rust
impl fmt::Display for EmailAddress {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

impl AsRef<str> for EmailAddress {
    fn as_ref(&self) -> &str { &self.0 }
}

impl FromStr for EmailAddress {
    type Err = EmailError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::new(s.to_owned())
    }
}
```

### Serde integration

```rust
// Simple: serialize as the inner type
#[derive(Serialize, Deserialize)]
#[serde(transparent)]
pub struct UserId(i64);

// With validation on deserialization
impl<'de> Deserialize<'de> for Port {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        let n = u16::deserialize(d)?;
        Port::new(n).map_err(serde::de::Error::custom)
    }
}
```

### Reduce boilerplate with derive_more

```rust
use derive_more::{Display, From, Into, AsRef, Deref};

#[derive(Debug, Clone, PartialEq, Eq, Hash, Display, AsRef, Deref)]
pub struct Username(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, From, Into)]
pub struct UserId(i64);
```

## Standard Library Evidence

| Newtype | Wraps | Purpose |
|---------|-------|---------|
| `String` | `Vec<u8>` | Guarantees UTF-8 validity |
| `PathBuf` | `OsString` | OS-specific path handling |
| `NonZero<u32>` | `u32` | Guarantees non-zero value |
| `Wrapping<T>` | `T` | Changes overflow semantics |
| `Saturating<T>` | `T` | Changes overflow semantics |
| `Pin<P>` | `P` | Prevents moving the pointee |
| `ManuallyDrop<T>` | `T` | Prevents automatic drop |

For advanced newtype patterns (typestate builders, phantom types, zero-sized type markers), see [type-design.md](../type-design.md).

## When NOT to Newtype

- **Truly arbitrary text** with no domain constraints: user comments, log messages, notes.
- **Internal temporaries** that never cross function boundaries.
- **Types already carrying their semantics**: `Duration` doesn't need a `Timeout(Duration)` wrapper unless you have multiple duration-typed fields that could be confused.
- **Display-only values.** If you never branch on it, never compare it, never validate it — a string is fine.
- **Prototyping.** Strings let you move fast. Replace them with types once the domain stabilizes.

The test: "Can passing the wrong value cause a bug the compiler could catch?" If yes → newtype. If no → bare type is fine.

## Common Source Languages

- **Python / Ruby / JavaScript** — strings are the default data type for almost everything
- **Go** — type aliases on strings exist but are weakly enforced
- **PHP** — stringly-typed to its core
- **Java** — `String` parameters everywhere, no lightweight wrapper pattern
