# Serde: Serialization Defaults

Serde is a boundary tool. Treat serialization as schema design, not “make it compile”. Your goal is a stable, explicit, debuggable wire representation with type-driven guarantees inside Rust.

**Authority:** serde.rs documentation (attributes + enum representations + custom serialization); Rust API Guidelines (type-driven design); Effective Rust (newtype pattern to bypass orphan rule; derive macros and helper attributes).

## Cross-references

- Use [type-design.md](type-design.md) to model the domain; serialize the model deliberately.
- Use [error-handling.md](error-handling.md) for conversion errors at the boundary (`try_from`, custom deserializers).
- Use [ownership.md](ownership.md) when doing zero-copy deserialization (`'de`, `Cow`, borrowing).

## 1) First question: are you defining a schema, or adapting to one?

- If you **define the schema** (your API/storage format): choose an explicit enum representation and naming conventions; document them; add forward/backward compatibility rules.
- If you **consume someone else’s schema**: isolate it in DTO types, then convert into your internal domain types. Do not leak “wire quirks” into core domain modeling.

Default: introduce `*Dto` structs/enums at the boundary when the wire format is not identical to your internal model.

## 2) Derive-first, customize with attributes, implement traits last

Default order of tools:

1. `#[derive(Serialize, Deserialize)]` with well-chosen attributes.
2. `serde_with` / `#[serde(with = "...")]` adapters for field-level tweaks.
3. `#[serde(from = ...)]` / `#[serde(try_from = ...)]` / `#[serde(into = ...)]` to keep the custom logic in normal Rust conversions.
4. Manual `impl Serialize` / `impl Deserialize` only when the representation cannot be expressed with the above.

**Why:** derived impls are consistent across formats and tend to produce better, more local errors than ad-hoc parsing.

## 3) Type rules at the boundary

### Rule 1: Do not serialize “bare strings with meaning”

If a string has domain meaning, make it a newtype (ID, slug, email, currency code). Derive serde for the newtype.

```rust
#[derive(Debug, Clone, PartialEq, Eq, serde::Serialize, serde::Deserialize)]
#[serde(transparent)]
pub struct UserId(String);
```

`#[serde(transparent)]` is the default for “newtype that should serialize like the inner field”.

### Rule 2: Do not model domain state as `bool` in serde types

If a field is a domain state (not a pure yes/no), use an enum internally. If the wire format is a bool flag, parse it into your enum at the boundary.

```rust
use serde::Deserialize;

#[derive(Deserialize)]
struct UserDto {
    is_active: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum UserStatus {
    Active,
    Disabled,
}

struct User {
    status: UserStatus,
}

impl From<UserDto> for User {
    fn from(dto: UserDto) -> Self {
        let status = if dto.is_active {
            UserStatus::Active
        } else {
            UserStatus::Disabled
        };
        User { status }
    }
}
```

### Rule 3: Do not use `serde_json::Value` as your internal representation

- `Value` is acceptable as an **ingress/egress shim** at the boundary.
- Convert into typed structs/enums immediately and keep type-driven invariants inside.

This is [type-design.md](type-design.md) (“parse, don’t validate”) applied to serialization.

## 4) Attribute defaults (the 80/20 set)

Full lists live in serde docs; this is the set you should reach for first.

### Container (struct/enum) attributes

- Prefer `#[serde(rename_all = "camelCase")]` (or another case) over per-field renames.
- Prefer explicit enum representation: `#[serde(tag = "type")]` (internally tagged) or `#[serde(tag = "t", content = "c")]` (adjacently tagged) for JSON-facing APIs.
- Use `#[serde(deny_unknown_fields)]` when you need strictness (security-sensitive inputs, config formats), but know it is incompatible with `#[serde(flatten)]`.
- Use `#[serde(default)]` (container) only when “missing fields default” is part of your compatibility story.
- Use `#[serde(from = "T")]` / `#[serde(try_from = "T")]` / `#[serde(into = "T")]` to express “serialize/deserialize via an intermediate type” without writing manual serde impls.

### Field attributes

- Use `#[serde(default)]` on a field for backward compatibility when an older payload may omit it.
- Prefer `Option<T>` for “field is semantically optional”; prefer `#[serde(default)]` for “field exists but older versions didn’t send it”. These are different.
- Use `#[serde(skip_serializing_if = "Option::is_none")]` for optional fields in JSON-style schemas.
- Use `#[serde(with = "path")]` (module with `serialize`/`deserialize`) for format tweaks; prefer `serde_with` when you can reuse a battle-tested adapter.
- Use `#[serde(flatten)]` to factor shared fields or capture unknown fields into a map, but don’t combine with `deny_unknown_fields`.
- Use `#[serde(alias = "oldName")]` for renamed fields (deserialize old name, serialize new name).

### Variant attributes (enums)

- Use `#[serde(other)]` on a unit variant inside tagged enums to handle unknown future variants.
- Avoid `#[serde(untagged)]` unless you can prove variants are non-overlapping and order-stable.

Deep dives: see `references/attributes-cheatsheet.md`.

## 5) Enum wire representation: pick intentionally (decision table)

**Authority:** serde.rs “Enum representations”.

| Goal | Prefer | Avoid | Why |
|------|--------|-------|-----|
| Works across many formats, simplest | Externally tagged (default) | Untagged | External tagging is the broadest-compat default in Serde |
| Readable JSON API, stable dispatch | Internally tagged (`tag = "type"`) | Tuple variants | Internally tagged cannot represent tuple variants |
| JSON API with non-struct payload variants | Adjacently tagged (`tag` + `content`) | Untagged | Adjacently tagged handles tuple/newtype variants with explicit content |
| “Input can be X or Y” legacy shape | Custom deserialize or carefully ordered `untagged` | Blind `untagged` | Untagged tries variants in order; errors are worse and performance can be costly |

### Hard rule: untagged is a last resort

`#[serde(untagged)]` means “try each variant in order and take the first that works”. This is fragile:

- Reordering variants becomes a breaking change.
- Ambiguous shapes can deserialize to the wrong variant.
- When no variant matches, the error is usually unhelpful (serde docs recommend `expecting` to improve this).

If the schema is yours, add a tag.

#### Incorrect → correct: JSON enum dispatch

Incorrect (order-dependent, ambiguous):

```rust
use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[serde(untagged)]
enum Op {
    Add { a: i64, b: i64 },
    Mul { a: i64, b: i64 },
}
```

Correct (explicit, order-independent):

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
enum Op {
    Add { a: i64, b: i64 },
    Mul { a: i64, b: i64 },
}
```

## 6) Adapting third-party types: newtype or adapter, not orphan impls

You cannot `impl serde::Serialize for somecrate::SomeType` (orphan rule). Default patterns:

1. Newtype wrap the foreign type (Effective Rust: newtype pattern bypasses orphan rule).
2. Or keep the foreign type but serialize it via `serde_with` or `#[serde(with = "...")]` at field sites.

Example: serialize a `url::Url` as a string via `Display`/`FromStr`.

```rust
use serde::{Deserialize, Serialize};
use serde_with::{serde_as, DisplayFromStr};

#[serde_as]
#[derive(Debug, Serialize, Deserialize)]
struct EndpointDto {
    #[serde_as(as = "DisplayFromStr")]
    url: url::Url,
}
```

Deep dive: `references/adapters-and-custom-impls.md`.

## 7) Defaults, missing fields, and “optional”

### Rule 1: Missing field policy must be explicit

- If a missing field is an error: leave it required.
- If missing is acceptable for compatibility: add `#[serde(default)]` (field) or model it as `Option<T>`.

Do not add `default` “to make deserialization succeed” unless the default is semantically correct.

### Rule 2: Avoid `Option<T>` + `#[serde(default)]` unless you mean it

`Option<T>` already defaults to `None` when combined with `#[serde(default)]`, but that communicates “field might be absent” twice. Choose the clearer signal for your schema.

### Rule 3: When many fields are `Option`, use `serde_with::skip_serializing_none`

If you have many `Option` fields and you want `None` to disappear from JSON output, prefer the container-level helper instead of repeating `skip_serializing_if` everywhere.

## 8) `flatten` and strictness

`#[serde(flatten)]` is powerful and dangerous.

Defaults:

- Use it to factor shared fields, or to capture “unknown fields” into `BTreeMap<String, serde_json::Value>` when you need forward compatibility.
- Do not combine it with `#[serde(deny_unknown_fields)]` (serde docs: unsupported combination).
- Treat flattening as a schema decision; add tests that lock in the resulting JSON shape.

## 9) Zero-copy deserialization: use only with a measured need

Defaults:

- Own data (`String`, `Vec<u8>`) unless you have a concrete performance reason.
- If you do borrow, use the standard patterns: `Cow<'de, str>` and `#[serde(borrow)]`.
- Keep borrowed data from escaping the boundary layer; convert into owned domain types when storing or caching.

## 10) Custom Serialize/Deserialize: keep the logic in conversions

If you need a custom representation, prefer implementing conversions and letting serde drive them:

- `#[serde(from = "FromType")]` for infallible conversions.
- `#[serde(try_from = "FromType")]` for fallible conversions (propagate good error messages).
- `#[serde(into = "IntoType")]` for serialization via an intermediate.

Manual serde impls are appropriate when:

- The representation depends on the format (use `Serializer::is_human_readable()` / `Deserializer::is_human_readable()` patterns).
- You must accept multiple legacy representations with tight control over error messages.

Deep dive: `references/adapters-and-custom-impls.md`.

## 11) Common mistakes (agent failure modes)

- Adding `#[serde(untagged)]` to “make it work” without proving non-overlap and order stability.
- Using `flatten` and `deny_unknown_fields` together (serde docs: unsupported).
- Sprinkling `rename = "..."` on every field instead of using `rename_all`.
- Using `default` to accept invalid/missing data instead of modeling the schema.
- Serializing domain types directly when the wire format is legacy/unstable; introduce DTOs.
- Hand-writing `Serialize`/`Deserialize` when `from`/`try_from`/`into` would be simpler and testable.

## 12) Review checklist

1. Is this code defining a schema or adapting to one? If adapting, are DTO types isolated at the boundary?
2. Are domain-significant strings and booleans represented as domain types/enums, not bare primitives?
3. Are enums tagged explicitly (internal/adjacent) for JSON APIs, with a plan for unknown variants (`other`) if needed?
4. Is `untagged` avoided, or justified with a non-overlap proof + stable ordering + tests?
5. Are `default`, `Option`, and missing-field behavior intentional and documented?
6. Is `flatten` used intentionally, and not combined with `deny_unknown_fields`?
7. Are third-party types handled via newtype or adapters (serde_with / with-modules), not impossible orphan impls?
8. If custom serialization exists, is it expressed via `from`/`try_from`/`into` where possible, and covered by round-trip tests?
