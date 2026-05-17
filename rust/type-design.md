# Type-Driven Domain Modeling

Use Rust’s type system to **encode domain facts** so the compiler rejects invalid states.

This topic is the implementation toolbox for Rust's modeling defaults: enum-first, newtype-heavy, no wildcard matches on owned enums, and parse-don’t-validate.

## Rules of thumb (defaults)

- **Parse at boundaries.** Convert `String`/`Vec`/wire formats into domain types once. Don’t “re-validate” everywhere.
- **Prefer types that make misuse impossible.** If a call sequence is invalid, make it not compile.
- **Keep invariants behind privacy.** If callers can construct the type directly, the invariant is optional.

## Pattern catalog

### 1) Newtype (tuple struct) — distinguish + enforce invariants

Do this when a primitive has *domain meaning*.

Bad (invariants bypassable):
```rust
pub struct EmailAddress(pub String);
```

Good (invariants enforced by module privacy):
```rust
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct EmailAddress(String);

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum EmailError {
    MissingAt,
}

impl EmailAddress {
    pub fn parse(raw: String) -> Result<Self, EmailError> {
        if !raw.contains('@') {
            return Err(EmailError::MissingAt);
        }
        Ok(Self(raw))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}
```

Preserve the invariant by keeping the inner field private. This is the Rust API Guidelines’ intent for newtypes.

**Authority:** Rust API Guidelines (C-NEWTYPE, C-CUSTOM-TYPE). std: `NonZero*`, `PathBuf`. Ecosystem: `url::Url`, `semver::Version`.

Implementation details (trait impl strategy, serde, `derive_more`, interop accessors):
- [references/newtype-patterns.md](references/newtype-patterns.md)

### 2) Typestate — state machine encoded in types

Do this when operations are only valid in some states and misuse is common.

Pattern: each state is a *different type*; transitions **consume `self`** and return the next state.

```rust
use std::marker::PhantomData;

pub struct Door<S> {
    _state: PhantomData<S>,
}

pub struct Closed;
pub struct Open;
pub struct Locked;

impl Door<Closed> {
    pub fn new() -> Self {
        Self { _state: PhantomData }
    }

    pub fn open(self) -> Door<Open> {
        Door { _state: PhantomData }
    }

    pub fn lock(self) -> Door<Locked> {
        Door { _state: PhantomData }
    }
}

impl Door<Open> {
    pub fn close(self) -> Door<Closed> {
        Door { _state: PhantomData }
    }
    // No lock() here: cannot lock an open door.
}

impl Door<Locked> {
    pub fn unlock(self) -> Door<Closed> {
        Door { _state: PhantomData }
    }
}
```

If a transition is invalid, **don’t implement it**. Let method absence enforce correctness.

**Authority:** Cliffle (“The Typestate Pattern in Rust”). Production typestate: `serde::Serializer`/`SerializeStruct`.

Advanced patterns (state-with-data, sealed state bounds, fallible transitions, builder-typestate hybrid):
- [references/typestate-patterns.md](references/typestate-patterns.md)

### 3) Builder — complex construction without “boolean soup”

Do this when construction takes many optional parameters, needs cross-field validation, or needs a stable call site.

Prefer a **non-consuming** builder (`&mut self -> &mut Self`) when you want reuse or loop-friendly configuration.

```rust
#[derive(Debug, Clone)]
pub struct ServerConfig {
    port: u16,
    host: String,
    workers: usize,
}

#[derive(Default)]
pub struct ServerConfigBuilder {
    port: Option<u16>,
    host: Option<String>,
    workers: Option<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConfigError {
    MissingPort,
}

impl ServerConfigBuilder {
    pub fn port(&mut self, port: u16) -> &mut Self {
        self.port = Some(port);
        self
    }

    pub fn host(&mut self, host: impl Into<String>) -> &mut Self {
        self.host = Some(host.into());
        self
    }

    pub fn workers(&mut self, n: usize) -> &mut Self {
        self.workers = Some(n);
        self
    }

    pub fn build(&self) -> Result<ServerConfig, ConfigError> {
        let default_workers = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(1);

        Ok(ServerConfig {
            port: self.port.ok_or(ConfigError::MissingPort)?,
            host: self.host.clone().unwrap_or_else(|| "localhost".to_string()),
            workers: self.workers.unwrap_or(default_workers),
        })
    }
}

fn main() -> Result<(), ConfigError> {
    let mut b = ServerConfigBuilder::default();
    b.port(8080).host("0.0.0.0");

    let _config = b.build()?;
    Ok(())
}
```

Use a **consuming** builder (`self -> Self`) when `build()` must move non-`Clone` fields out.

**Authority:** Rust API Guidelines (C-BUILDER). std: `std::process::Command`, `std::thread::Builder`.

More patterns (validation strategies, derive macros, consuming vs non-consuming tradeoffs):
- [references/builder-patterns.md](references/builder-patterns.md)

### 4) Phantom types — type-level tags with zero runtime representation

Do this when two values have the same runtime representation but *different meaning*.

```rust
use std::marker::PhantomData;

struct Meters;
struct Feet;

struct Length<Unit> {
    value: f64,
    _unit: PhantomData<Unit>,
}

impl<U> Length<U> {
    fn new(value: f64) -> Self {
        Self { value, _unit: PhantomData }
    }
}

fn add<U>(a: Length<U>, b: Length<U>) -> Length<U> {
    Length::new(a.value + b.value)
}
```

Use this for “validated/unvalidated” markers, permission tokens, and unit systems.

**Authority:** std: `PhantomData`, `PhantomPinned`.

### 5) Sealed traits — close a trait’s implementation set

Do this when you must prevent external implementations (typestate bounds, exhaustive dispatch).

```rust
mod private {
    pub trait Sealed {}
}

pub trait ConnectionState: private::Sealed {
    fn name(&self) -> &'static str;
}

pub struct Connected;
pub struct Disconnected;

impl private::Sealed for Connected {}
impl private::Sealed for Disconnected {}

impl ConnectionState for Connected {
    fn name(&self) -> &'static str {
        "connected"
    }
}

impl ConnectionState for Disconnected {
    fn name(&self) -> &'static str {
        "disconnected"
    }
}
```

**Authority:** Rust API Guidelines (C-SEALED). std uses sealing patterns around fundamental traits.

## Decision framework

- Primitive with domain meaning → **Newtype**.
- Operation valid only in some states → **Typestate** (or a runtime enum if states are dynamic).
- Many optional construction parameters → **Builder**.
- Same representation, different meaning → **Phantom type**.
- Trait must not be externally implemented → **Sealed trait**.

If you have a struct with a `kind` field plus variant-only `Option` fields: delete it and model as an enum.

## Common mistakes (agent failure modes)

- **`pub struct Email(pub String)`** → public inner fields bypass invariants.
- **Typestate transitions take `&self`** → they must consume `self` or you can keep using the old state.
- **Builder panics on missing fields** → return `Result` from `build()`.
- **Builder uses `&mut self` but examples chain from temporaries** → non-consuming builders chain on a `let mut b = …` binding.
- **Phantom type parameter without `PhantomData`** → you’re not actually carrying the type information.
- **Typestate explosion** → prefer a runtime enum when states/transitions are large or runtime-driven.

## Cross-references

- [references/enums-as-modeling-tool.md](references/enums-as-modeling-tool.md) — enum-first modeling details
- [ownership.md](ownership.md) — consuming `self`, borrowing in builder APIs
- [traits.md](traits.md) — trait design, object safety, and sealing patterns
- [error-handling.md](error-handling.md) — error types for fallible construction and parsing

## Review checklist

1. Is a primitive type (`String`, `i64`, `u16`, `bool`) carrying domain meaning? Wrap it in a newtype.
2. Does a newtype have a public inner field? Make it private; enforce invariants in constructors.
3. Are you “validating” repeatedly? Parse once at the boundary into a type that proves validity.
4. Are operations only legal in some states? Consider typestate; transitions should consume `self`.
5. Does construction have many optional parameters or cross-field rules? Use a builder with `build() -> Result`.
6. Are you trying to distinguish identical representations (units, validated/unvalidated, permissions)? Use phantom types.
7. Do you need to prevent external impls (typestate bounds, exhaustive dispatch)? Seal the trait.
8. Did you model variants as `kind + Option fields`? Replace with an enum carrying per-variant data.
