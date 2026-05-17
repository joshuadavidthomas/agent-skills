# Standard Trait Reference

Which std traits to implement, when to derive vs implement manually, and the conversion trait hierarchy. Use with [traits.md](../traits.md) when the full standard-trait picture matters.

## The Standard Trait Checklist

For every new type, consider each trait. Derive what you can, implement the rest manually when semantics require it.

### Always derive (unless you have a reason not to)

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
struct MyType {
    // ...
}
```

| Trait | What it gives you | Derive unless |
|-------|------------------|---------------|
| `Debug` | `{:?}` formatting | You need a custom format or must hide fields |
| `Clone` | `.clone()` explicit duplication | Type is intentionally non-cloneable (e.g., file handles) |
| `PartialEq` | `==` and `!=` | Equality has custom semantics (ignoring a field, floating point) |
| `Eq` | Marker: reflexive equality (`x == x`) | Type contains `f32`/`f64` (NaN ≠ NaN) |

### Derive when appropriate

| Trait | Derive when | Don't derive when |
|-------|------------|-------------------|
| `Hash` | `Eq` is derived or all fields contribute to equality | Manual `Eq` uses a subset of fields |
| `Copy` | Small, stack-only, all fields are `Copy` | Type has heap data, is large, or you want move semantics |
| `Default` | A sensible zero/empty value exists | "Empty" is meaningless for this type |
| `PartialOrd` + `Ord` | Field order matches desired ordering | Custom ordering needed |

### Implement manually

| Trait | Implement when |
|-------|---------------|
| `Display` | User-facing text representation (error messages, CLI output) |
| `FromStr` | Type can be parsed from a string |
| `From<T>` / `TryFrom<T>` | Natural conversions from other types |
| `FromIterator<T>` | Type is a collection that can be built from an iterator |
| `IntoIterator` | Type can be iterated over |
| `Error` | Type is an error (also requires `Display` + `Debug`) |
| `Drop` | Cleanup logic beyond freeing memory |
| `AsRef<T>` / `AsMut<T>` | Cheap reference-to-reference conversion |

## Consistency Rules

These invariants **must** hold. Violating them causes subtle bugs with `HashMap`, `BTreeMap`, sorting, and other std containers.

### `Eq` + `Hash` agreement

If `a == b`, then `hash(a) == hash(b)`.

If you derive both, this holds automatically. If you implement either manually, implement both manually and ensure they agree.

```rust
// ❌ Bug: derived Hash includes all fields, manual Eq ignores `cached`
#[derive(Hash)]
struct Record {
    id: u64,
    name: String,
    cached_display: Cell<Option<String>>,
}

impl PartialEq for Record {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id && self.name == other.name
        // Ignores cached_display — correct for equality
    }
}
impl Eq for Record {}
// Hash includes cached_display — WRONG, breaks HashMap
```

```rust
// ✅ Both use the same fields
impl PartialEq for Record {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id && self.name == other.name
    }
}
impl Eq for Record {}

impl Hash for Record {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.id.hash(state);
        self.name.hash(state);
    }
}
```

### `Ord` implies `PartialOrd` + `Eq` + `PartialEq`

When implementing `Ord`, derive or implement all four. They must be consistent: `a.partial_cmp(b) == Some(a.cmp(b))`.

```rust
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct Priority(u8);
```

### `Copy` implies `Clone`

`Copy` is a marker that says "bitwise copy is valid." It refines `Clone`. Always derive both together.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Point { x: i32, y: i32 }
```

**Don't implement `Copy` for:**
- Types with heap data (`String`, `Vec<T>`)
- Types larger than ~128 bytes (implicit copy is expensive)
- Types where move semantics are important (file handles, locks)

## The Conversion Trait Hierarchy

```
Infallible conversions:
  From<T> → implement this one
  Into<T> → blanket impl, never implement directly

Fallible conversions:
  TryFrom<T> → implement this one
  TryInto<T> → blanket impl, never implement directly

Borrowing conversions:
  AsRef<T>  → cheap &Self → &T
  AsMut<T>  → cheap &mut Self → &mut T
  Borrow<T> → like AsRef but with Eq/Ord/Hash consistency guarantee
  BorrowMut<T>

Display conversions:
  Display   → user-facing string representation
  ToString  → blanket impl from Display, never implement directly
  FromStr   → parse from &str
```

### `From<T>` / `Into<T>`

Implement `From<T>` for infallible conversions. The blanket impl gives you `Into<T>` for free.

```rust
struct UserId(u64);

// ✅ Implement From
impl From<u64> for UserId {
    fn from(id: u64) -> Self { UserId(id) }
}

// ❌ Never implement Into directly
// impl Into<UserId> for u64 { ... }  // NO

// Usage — both work
let id = UserId::from(42);
let id: UserId = 42.into();
```

### `TryFrom<T>` / `TryInto<T>`

For fallible conversions. Same pattern — implement `TryFrom`, get `TryInto` free.

```rust
struct Port(u16);

impl TryFrom<u32> for Port {
    type Error = PortError;

    fn try_from(value: u32) -> Result<Self, Self::Error> {
        let port = u16::try_from(value).map_err(|_| PortError::OutOfRange)?;
        if port == 0 { return Err(PortError::Zero); }
        Ok(Port(port))
    }
}
```

### `AsRef<T>` / `Borrow<T>`

Both provide `&Self → &T`. The difference:

- **`AsRef<T>`** — general cheap reference conversion. No semantic guarantees.
- **`Borrow<T>`** — guarantees that borrowed form has identical `Eq`, `Ord`, and `Hash` behavior. Required for `HashMap::get` to accept borrowed keys.

```rust
// AsRef — cheap conversion, no semantic guarantee
impl AsRef<str> for Username {
    fn as_ref(&self) -> &str { &self.0 }
}

// Borrow — same hash/eq behavior guaranteed
impl Borrow<str> for Username {
    fn borrow(&self) -> &str { &self.0 }
}
// Now HashMap<Username, V>::get can accept &str
```

**Rule of thumb:** Implement `AsRef` for general-purpose borrowing. Implement `Borrow` only when you need `HashMap`/`BTreeMap` key lookups with the borrowed form.

### `Display` / `ToString` / `FromStr`

- Implement `Display` — you get `ToString` (via blanket impl) for free.
- Implement `FromStr` for the reverse direction (parsing).

```rust
impl Display for UserId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "user-{}", self.0)
    }
}
// Now UserId has .to_string() automatically

impl FromStr for UserId {
    type Err = ParseUserIdError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let id = s.strip_prefix("user-")
            .ok_or(ParseUserIdError::MissingPrefix)?
            .parse::<u64>()
            .map_err(ParseUserIdError::InvalidNumber)?;
        Ok(UserId(id))
    }
}
```

## `Deref` / `DerefMut` — Smart Pointers Only

`Deref` enables transparent access to an inner type through the outer type. **Use it exclusively for smart pointer types.**

```rust
// ✅ Correct — MyBox is a smart pointer
struct MyBox<T>(Box<T>);

impl<T> Deref for MyBox<T> {
    type Target = T;
    fn deref(&self) -> &T { &self.0 }
}
```

```rust
// ❌ WRONG — UserId is not a smart pointer
impl Deref for UserId {
    type Target = u64;
    fn deref(&self) -> &u64 { &self.0 }
}
// This makes UserId transparently act like u64,
// defeating the purpose of the newtype.
```

**Why this matters:** `Deref` coercion is implicit. Method resolution follows `Deref` chains. If `UserId` derefs to `u64`, then `user_id.pow(2)` compiles — that's not what you want from a domain type.

**For newtypes:** Use `AsRef`, `From`, or explicit accessor methods instead.

**Authority:** std `Deref` docs: "Deref should only be implemented for smart pointers to avoid confusion." Effective Rust Item 12.

## Collection Traits

For types that act as collections:

```rust
// Enable .collect() into your type
impl<T> FromIterator<T> for MyVec<T> {
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        let mut v = MyVec::new();
        for item in iter {
            v.push(item);
        }
        v
    }
}

// Enable .extend() to append
impl<T> Extend<T> for MyVec<T> {
    fn extend<I: IntoIterator<Item = T>>(&mut self, iter: I) {
        for item in iter {
            self.push(item);
        }
    }
}

// Enable for loops (owned)
impl<T> IntoIterator for MyVec<T> {
    type Item = T;
    type IntoIter = std::vec::IntoIter<T>;

    fn into_iter(self) -> Self::IntoIter {
        self.0.into_iter()
    }
}

// Enable for loops (borrowed)
impl<'a, T> IntoIterator for &'a MyVec<T> {
    type Item = &'a T;
    type IntoIter = std::slice::Iter<'a, T>;

    fn into_iter(self) -> Self::IntoIter {
        self.0.iter()
    }
}
```

**Authority:** Rust API Guidelines [C-COLLECT]. std: `Vec`, `HashMap`, `BTreeMap` all implement `FromIterator`, `Extend`, and `IntoIterator` (owned and borrowed).

## Quick Decision Table

| I need to... | Implement |
|-------------|-----------|
| Print for debugging | `Debug` (derive) |
| Print for users | `Display` (manual) |
| Compare equality | `PartialEq` + `Eq` (derive) |
| Use as HashMap key | `Eq` + `Hash` (derive both) |
| Sort / order | `PartialOrd` + `Ord` (derive both, plus `Eq` + `PartialEq`) |
| Convert from another type | `From<T>` (manual) |
| Parse from string | `FromStr` (manual) |
| Provide a default value | `Default` (derive or manual) |
| Make iterable | `IntoIterator` (manual) |
| Enable `.collect()` | `FromIterator` (manual) |
| Cheap reference conversion | `AsRef<T>` (manual) |
| HashMap key lookup with borrowed form | `Borrow<T>` (manual) |
