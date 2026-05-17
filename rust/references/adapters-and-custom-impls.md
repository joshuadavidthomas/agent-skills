# Adapters and custom impls (serde_with, with-modules, from/try_from/into)

Use this reference when derives + simple attributes are not enough.

**Authority:** serde.rs (field `with`, custom serialization, enum representations); serde_with user guide/README; Effective Rust (newtype pattern and orphan rule).

## 1) Default ladder (least custom → most custom)

1. Derive + attributes.
2. `serde_with` adapter (reusable, tested).
3. `#[serde(with = "...")]` module adapter (local, explicit).
4. `#[serde(from / try_from / into)]` via an intermediate type.
5. Manual `Serialize`/`Deserialize`.

Do not jump to (5) unless you have a representation that cannot be expressed with (2)-(4).

## 2) Prefer serde_with when a standard adapter exists

`serde_with` exists to eliminate bespoke adapter code. Reach for it when you need any of the following:

- “Serialize as Display, deserialize as FromStr” (`DisplayFromStr`).
- Durations in seconds/millis, RFC3339 timestamps, hex/base64 bytes, etc.
- Arrays larger than 32 elements / const generic arrays via `serde_as`.
- Eliding `None` fields across a whole struct (`#[skip_serializing_none]`).

### Pattern: Display/FromStr adapter

```rust
use serde::{Deserialize, Serialize};
use serde_with::{serde_as, DisplayFromStr};

#[serde_as]
#[derive(Serialize, Deserialize)]
struct ConfigDto {
    #[serde_as(as = "DisplayFromStr")]
    endpoint: url::Url,
}
```

Default: if an adapter exists, use it; don’t write a custom `deserialize_with` that just calls `FromStr`.

## 3) `#[serde(with = "module")]`: write a symmetric adapter module

`with` is the standard “local adapter” mechanism. The module provides two functions:

- `serialize<T, S>(value: &T, serializer: S) -> Result<S::Ok, S::Error>`
- `deserialize<'de, D>(deserializer: D) -> Result<T, D::Error>`

### Example: parse-and-print a domain newtype as a string

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UserId(String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UserIdParseError {
    Empty,
}

impl std::fmt::Display for UserIdParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            UserIdParseError::Empty => write!(f, "user id cannot be empty"),
        }
    }
}

impl std::error::Error for UserIdParseError {}

impl UserId {
    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for UserId {
    type Error = UserIdParseError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        if value.is_empty() {
            return Err(UserIdParseError::Empty);
        }
        Ok(UserId(value))
    }
}

mod user_id_as_string {
    use serde::{Deserialize, Deserializer, Serializer};

    use super::UserId;

    pub fn serialize<S>(id: &UserId, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(id.as_str())
    }

    pub fn deserialize<'de, D>(deserializer: D) -> Result<UserId, D::Error>
    where
        D: Deserializer<'de>,
    {
        let s = String::deserialize(deserializer)?;
        UserId::try_from(s).map_err(serde::de::Error::custom)
    }
}

#[derive(Serialize, Deserialize)]
struct PayloadDto {
    #[serde(with = "user_id_as_string")]
    user_id: UserId,
}
```

Defaults:

- Keep adapters symmetric (`with`), not one-sided `serialize_with` / `deserialize_with`, unless asymmetry is intentional.
- Route fallible parsing errors through `serde::de::Error::custom` and give a message that helps the caller.
- Keep adapter modules small and local to the schema boundary.

## 4) Prefer `from` / `try_from` / `into` for whole-type remapping

When the serialized shape is “the same data, but represented differently”, serialize/deserialize via an intermediate type.

### Example: deserialize from a string but keep a richer internal type

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct UserId(String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UserIdParseError {
    Empty,
}

impl std::fmt::Display for UserIdParseError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            UserIdParseError::Empty => write!(f, "user id cannot be empty"),
        }
    }
}

impl std::error::Error for UserIdParseError {}

impl TryFrom<String> for UserId {
    type Error = UserIdParseError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        if value.is_empty() {
            return Err(UserIdParseError::Empty);
        }
        Ok(UserId(value))
    }
}

impl From<UserId> for String {
    fn from(id: UserId) -> Self {
        id.0
    }
}
```

Note: `#[serde(into = "T")]` serializes via `Clone` (because `Serialize` works with `&self`). Keep the type cheap to clone, or prefer a field-level adapter.

Default: conversions are normal Rust code, which makes them easier to test and reuse than embedding logic inside a `Visitor`.

## 5) Manual impls: when you need format awareness or tight control

Manual `Serialize`/`Deserialize` is justified when:

- You need to switch representation based on `is_human_readable()`.
- You must accept multiple legacy input shapes and produce a single canonical output shape.
- You need highly targeted diagnostics that derived impls cannot express.

### Pattern: human-readable string, binary bytes

```rust
impl serde::Serialize for Blob {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        if serializer.is_human_readable() {
            serializer.serialize_str(&hex::encode(&self.0))
        } else {
            serializer.serialize_bytes(&self.0)
        }
    }
}
```

Defaults:

- If you implement one side manually, you almost always need to implement the other; keep round-tripping in mind.
- Prefer expressing “multiple legacy shapes” via an intermediate `enum` and then converting into your internal type; avoid `untagged` directly on your core domain type.
- Write round-trip tests that lock in the wire format for representative examples (including error cases).

## 6) “String or struct” inputs: avoid unbounded ambiguity

If you need to accept inputs like either `"id"` or `{ "id": "..." }`, you have three options:

1. Make the schema explicit (preferred): require a tag or a single shape.
2. Use a small DTO `enum` with `#[serde(untagged)]`, convert immediately, and keep it out of the domain layer.
3. Implement `Deserialize` manually if you need better diagnostics and stronger validation.

Default: (2) is acceptable if you can prove the shapes are non-overlapping and you add tests; (3) only if you need better errors or more control.
