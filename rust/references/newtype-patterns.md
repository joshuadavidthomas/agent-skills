# Newtype Implementation Patterns

Deep-dive on newtype implementation: trait derivation, serde integration, accessor patterns, and when to use derive_more.

## Basic Structure

```rust
/// A validated email address.
///
/// Invariant: contains exactly one '@' with non-empty local and domain parts.
pub struct EmailAddress(String);
```

The inner field is **private by default** in Rust. This is critical — it forces construction through your validated constructor.

## Trait Derivation

Derive traits that make sense for your domain:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct UserId(i64);
```

**What to derive:**

| Trait | Derive when... |
|-------|----------------|
| `Debug` | Almost always — needed for error messages |
| `Clone` | Value should be copyable (most newtypes) |
| `Copy` | Inner type is Copy and newtype is small |
| `PartialEq`, `Eq` | Values can be compared for equality |
| `Hash` | Used as HashMap/HashSet key |
| `PartialOrd`, `Ord` | Ordering is meaningful |
| `Default` | There's a sensible default value |

**What NOT to derive:**

- `Ord` on types without meaningful ordering (EmailAddress, UserId)
- `Default` when zero/empty violates invariants (Port, NonEmptyVec)
- `Copy` on large types — prefer explicit `.clone()`

## Accessor Patterns

### Simple accessor

```rust
impl EmailAddress {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```

### AsRef for generic contexts

```rust
impl AsRef<str> for EmailAddress {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

// Now works with functions that take impl AsRef<str>
fn send_email(to: impl AsRef<str>) { /* ... */ }
send_email(&email);
```

### Deref for transparent access

**Use sparingly.** Deref implies IS-A relationship and allows silent coercion.

```rust
use std::ops::Deref;

impl Deref for Username {
    type Target = str;
    fn deref(&self) -> &str {
        &self.0
    }
}

// Now username.len(), username.starts_with(), etc. work directly
```

Deref is appropriate for:
- Smart pointer-like types (your type "is a" pointer to the inner type)
- Types where transparent string/slice access is the primary use case

Deref is inappropriate for:
- Types with domain invariants (users might bypass them)
- Types where the newtype semantics should be explicit

### Borrow for collection lookups

```rust
use std::borrow::Borrow;

impl Borrow<str> for Username {
    fn borrow(&self) -> &str {
        &self.0
    }
}

// Now HashMap<Username, _>::get() accepts &str
let map: HashMap<Username, Profile> = /* ... */;
let profile = map.get("alice");  // Works without constructing Username
```

## Construction Patterns

### Infallible construction (type distinction only)

```rust
impl Miles {
    pub fn new(value: f64) -> Self {
        Self(value)
    }
}
```

### Fallible construction (with invariants)

```rust
impl Port {
    pub fn new(n: u16) -> Result<Self, PortError> {
        if n == 0 {
            return Err(PortError::Zero);
        }
        Ok(Self(n))
    }

    /// Create a port without validation.
    ///
    /// # Safety
    /// Caller must ensure n != 0.
    pub const unsafe fn new_unchecked(n: u16) -> Self {
        Self(n)
    }
}
```

Provide `new_unchecked` for const contexts or performance-critical code where the caller can guarantee the invariant.

### TryFrom for standard conversion

```rust
impl TryFrom<u16> for Port {
    type Error = PortError;

    fn try_from(n: u16) -> Result<Self, Self::Error> {
        Self::new(n)
    }
}

// Now: let port: Port = 8080u16.try_into()?;
```

### FromStr for parsing

```rust
impl FromStr for EmailAddress {
    type Err = EmailError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Self::parse(s.to_owned())
    }
}

// Now: let email: EmailAddress = "user@example.com".parse()?;
```

## Serde Integration

### Transparent serialization

For newtypes that should serialize as their inner type:

```rust
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
#[serde(transparent)]
pub struct UserId(i64);
```

JSON: `42` (not `{"UserId": 42}`)

### With validation on deserialization

```rust
use serde::{Deserialize, Deserializer};

impl<'de> Deserialize<'de> for Port {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        let n = u16::deserialize(d)?;
        Port::new(n).map_err(serde::de::Error::custom)
    }
}
```

This ensures deserialized values satisfy invariants. Malformed input fails deserialization rather than constructing an invalid `Port`.

### Combined transparent + validation

```rust
use serde::{Deserialize, Deserializer, Serialize};

#[derive(Serialize)]  // Serialize as inner type
pub struct Port(u16);

impl<'de> Deserialize<'de> for Port {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        let n = u16::deserialize(d)?;
        if n == 0 {
            return Err(serde::de::Error::custom("port cannot be zero"));
        }
        Ok(Port(n))
    }
}
```

## derive_more for Boilerplate Reduction

The `derive_more` crate eliminates pass-through boilerplate:

```rust
use derive_more::{AsRef, Deref, Display, From, Into};

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
#[derive(Display, AsRef, Deref)]  // from derive_more
pub struct Username(String);

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[derive(From, Into)]  // from derive_more
pub struct UserId(i64);
```

**Available derives:**
- `From` — `impl From<Inner> for Newtype`
- `Into` — `impl Into<Inner> for Newtype`
- `AsRef` — `impl AsRef<Inner> for Newtype`
- `Deref` — `impl Deref<Target=Inner> for Newtype`
- `Display` — delegates to inner's Display
- `FromStr` — delegates to inner's FromStr
- `Add`, `Sub`, etc. — arithmetic operations

Use `derive_more` when you have many newtypes with similar boilerplate. For one or two newtypes, manual impls are clearer.

## Ecosystem Examples

### std library

| Type | Wraps | Pattern |
|------|-------|---------|
| `String` | `Vec<u8>` | Invariant (UTF-8), Deref to str |
| `PathBuf` | `OsString` | Encapsulation, AsRef<Path> |
| `NonZero<u32>` | `u32` | Invariant (non-zero) |
| `Wrapping<T>` | `T` | Behavior change (overflow) |

### Ecosystem

| Type | Crate | Pattern |
|------|-------|---------|
| `Url` | `url` | Invariant (valid URL), Display |
| `Version` | `semver` | Invariant (semver format) |
| `Uuid` | `uuid` | Type distinction, FromStr |
| `HeaderName` | `http` | Invariant (valid header name) |

## When to Expose the Inner Value

**Provide `.into_inner()` when:**
- The invariant is construction-only (no ongoing guarantee needed)
- Users legitimately need the raw value for interop
- The type is a wrapper for type distinction, not invariant enforcement

```rust
impl Username {
    pub fn into_inner(self) -> String {
        self.0
    }
}
```

**Don't provide `.into_inner()` when:**
- The invariant could be violated by modification
- You want to change the inner representation later
- The wrapped value has different semantics than your type
