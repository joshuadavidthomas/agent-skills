# Serde attributes cheat sheet (practical defaults)

This is the “reach for these first” subset, with the gotchas that regularly bite agents.

**Authority:** serde.rs documentation: container attributes, field attributes, variant attributes, enum representations.

## Container attributes (struct/enum)

### Naming

- `#[serde(rename = "Name")]`: rename the container itself.
- `#[serde(rename_all = "camelCase")]`: rename all fields (struct) or all variants (enum). Prefer this over per-field/per-variant `rename`.
- `#[serde(rename_all_fields = "camelCase")]`: apply `rename_all` to the fields of every struct-variant in an enum.

### Unknown fields

- `#[serde(deny_unknown_fields)]`: fail on unknown fields.
  - Use for security-sensitive inputs and strict config formats.
  - Do not combine with `#[serde(flatten)]` (unsupported).

### Enum representations

- Default: externally tagged.
- `#[serde(tag = "type")]`: internally tagged.
  - Does not support tuple variants.
  - Requires `serde`’s `alloc` feature for deserialization (enabled by default).
- `#[serde(tag = "t", content = "c")]`: adjacently tagged.
  - Handles tuple/newtype variants with explicit content.
  - Requires `alloc` for deserialization (enabled by default).
- `#[serde(untagged)]`: untagged.
  - Tries variants in order; errors are less informative; performance can be costly.

### Defaults

- `#[serde(default)]`: missing fields default from `Default` (container) or `Default::default()` (field).
- `#[serde(default = "path")]`: missing defaults from a function.

Default: use `default` only as part of a compatibility story; do not use it to paper over schema uncertainty.

### Conversions (prefer these over manual impls)

- `#[serde(from = "FromType")]`: deserialize to `FromType`, then `From<FromType>`.
- `#[serde(try_from = "FromType")]`: deserialize to `FromType`, then `TryFrom<FromType>`.
- `#[serde(into = "IntoType")]`: serialize after converting via `Into<IntoType>` (requires `Clone`).

### Newtypes

- `#[serde(transparent)]`: serialize/deserialize a single-field struct exactly like the inner field. Default for “domain newtype should be wire-compatible with inner type”.

### Diagnostics

- `#[serde(expecting = "...")]`: improve deserialization error messages (especially useful with `untagged`).

## Field attributes

### Naming and compatibility

- `#[serde(rename = "newName")]`: rename this field.
- `#[serde(alias = "oldName")]`: accept an old name on input while keeping the new name on output.

### Presence and shape

- `#[serde(default)]` / `#[serde(default = "path")]`: accept missing field and fill in a value.
- `#[serde(skip_serializing_if = "path")]`: elide field when serializing (e.g. `Option::is_none`).
- `#[serde(skip)]`, `skip_serializing`, `skip_deserializing`: hard exclude.

Default: prefer `Option<T>` for semantically optional fields; use `default` for backward compatibility.

### Structure

- `#[serde(flatten)]`: merge the field’s map/struct fields into the parent.
  - Great for factoring shared fields or collecting “extra” keys into a map.
  - Not supported with `deny_unknown_fields`.

### Adapters

- `#[serde(with = "module")]`: module must provide `serialize` and `deserialize`.
- `#[serde(serialize_with = "path")]` / `#[serde(deserialize_with = "path")]`: function hooks.
  - Prefer `with`/`serde_with` for symmetry; use one-sided hooks only when the asymmetry is intentional.

### Borrowing

- `#[serde(borrow)]`: enable zero-copy borrowing from the input when the type supports it (e.g. `Cow<'de, str>`).

## Variant attributes (enums)

- `#[serde(rename = "...")]` / `alias = "..."`: rename/compat.
- `#[serde(other)]`: catch-all for unknown tags in internally or adjacently tagged enums; only valid on a unit variant.
- `#[serde(untagged)]` (variant-level): force this variant to serialize/deserialize without the enum tag; untagged variants must be last.

## Gotchas that should trigger a review comment

- `deny_unknown_fields` + `flatten`.
- Internally tagged enums containing tuple variants.
- `untagged` used without tests and without a “non-overlap + stable ordering” argument.
- Blanket `default` added to “make deserialization pass” without semantic justification.
