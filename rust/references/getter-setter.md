# Public Fields Over Trivial Getters

## The Smell

Mechanically wrapping every field in `get_x()` and `set_x()` methods, mirroring Java's encapsulation conventions.

```rust
// WRONG — Java-brain
pub struct Point {
    x: f64,
    y: f64,
}

impl Point {
    pub fn get_x(&self) -> f64 { self.x }
    pub fn set_x(&mut self, x: f64) { self.x = x; }
    pub fn get_y(&self) -> f64 { self.y }
    pub fn set_y(&mut self, y: f64) { self.y = y; }
}
```

This adds ceremony with zero value. The getters and setters don't enforce any invariants — they're just indirection.

## The Idiomatic Alternative

### No invariants → make fields public

```rust
pub struct Point {
    pub x: f64,
    pub y: f64,
}
// Usage: point.x = 3.0;
```

Rust doesn't have the "everything must be encapsulated" culture of Java. Public fields are a deliberate, supported choice.

### Real invariants → expose a focused API

```rust
pub struct Temperature {
    kelvin: f64, // private — must be non-negative
}

impl Temperature {
    pub fn new(kelvin: f64) -> Result<Self, InvalidTemperature> {
        if kelvin < 0.0 { return Err(InvalidTemperature); }
        Ok(Self { kelvin })
    }

    pub fn kelvin(&self) -> f64 { self.kelvin }
    pub fn as_celsius(&self) -> f64 { self.kelvin - 273.15 }
    pub fn as_fahrenheit(&self) -> f64 { self.kelvin * 9.0 / 5.0 - 459.67 }
}
```

### Accessors return borrowed data — let callers clone

When you do have accessors, return references rather than owned values. Callers who need ownership can clone explicitly.

```rust
// WRONG — allocates on every access
impl User {
    pub fn name(&self) -> String { self.name.clone() }
    pub fn roles(&self) -> Vec<Role> { self.roles.clone() }
}

// RIGHT — zero-cost access; caller decides if they need to clone
impl User {
    pub fn name(&self) -> &str { &self.name }
    pub fn roles(&self) -> &[Role] { &self.roles }
}
```

Return `&str` not `&String`, `&[T]` not `&Vec<T>`, `&Path` not `&PathBuf`. Accept the most general borrowed form. See [borrow-by-default.md](borrow-by-default.md) for the full rationale and table.

### Rust naming conventions

```rust
impl Foo {
    fn name(&self) -> &str { &self.name }          // getter: bare field name, NOT get_name()
    fn set_name(&mut self, name: String) { ... }    // setter only if there are invariants
    fn into_inner(self) -> Inner { self.inner }     // consuming accessor
    fn as_bytes(&self) -> &[u8] { ... }             // conversion view
}
```

The `get_` prefix is reserved for methods that do meaningful work or could fail (like `HashMap::get` which returns `Option`).

## The Decision

Ask: "If someone set this field to any value of its type, would that always be valid?"

- **Yes** → `pub` field
- **No** → private field, validated constructor, accessor methods

## When Getters Are Appropriate

- **Trait implementations.** If a trait requires getter methods.
- **Future-proofing library APIs.** Published crate where adding validation later must preserve semver. For application code, this rarely applies.
- **Computed fields.** `area()` on a `Rectangle` isn't a getter — it's a derived value.

## Common Source Languages

- **Java** — getters/setters are required by convention and many frameworks
- **C#** — properties make this less verbose but the pattern persists
- **Kotlin** — data classes reduce this, but Java habits carry over
