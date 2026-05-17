# Transform Over Mutate

## The Smell

Defaulting to `&mut self` setters for every modification, even when consuming `self` and returning would be cleaner and more composable.

```rust
// WRONG — mutation-heavy API
impl Config {
    fn set_host(&mut self, host: &str) { self.host = host.to_string(); }
    fn set_port(&mut self, port: u16) { self.port = port; }
    fn enable_tls(&mut self) { self.tls = true; }
}

// Usage requires mutable binding and separate statements
let mut config = Config::default();
config.set_host("localhost");
config.set_port(8080);
config.enable_tls();
```

## The Idiomatic Alternative

### Consuming builder-style methods

```rust
impl Config {
    fn host(mut self, host: &str) -> Self {
        self.host = host.to_string();
        self
    }

    fn port(mut self, port: u16) -> Self {
        self.port = port;
        self
    }

    fn tls(mut self) -> Self {
        self.tls = true;
        self
    }
}

// Clean, chainable, no mutable binding needed
let config = Config::default()
    .host("localhost")
    .port(8080)
    .tls();
```

No extra allocation — the compiler moves the value through the chain.

### Functional transformation for small types

```rust
impl Point {
    fn translate(self, dx: f64, dy: f64) -> Self {
        Self { x: self.x + dx, y: self.y + dy }
    }

    fn scale(self, factor: f64) -> Self {
        Self { x: self.x * factor, y: self.y * factor }
    }
}

let point = Point::new(1.0, 2.0)
    .translate(3.0, 4.0)
    .scale(2.0);
```

### Non-consuming builders: `&mut self -> &mut Self`

When construction involves reuse, loops, or non-`Clone` intermediate state, a non-consuming builder is often better:

```rust
#[derive(Default)]
struct ServerConfigBuilder {
    port: Option<u16>,
    host: Option<String>,
    workers: Option<usize>,
}

impl ServerConfigBuilder {
    fn port(&mut self, port: u16) -> &mut Self {
        self.port = Some(port);
        self
    }

    fn host(&mut self, host: impl Into<String>) -> &mut Self {
        self.host = Some(host.into());
        self
    }

    fn build(&self) -> Result<ServerConfig, ConfigError> {
        Ok(ServerConfig {
            port: self.port.ok_or(ConfigError::MissingPort)?,
            host: self.host.clone().unwrap_or_else(|| "localhost".into()),
            workers: self.workers.unwrap_or(4),
        })
    }
}

// Usage — note the `let mut` binding
let mut b = ServerConfigBuilder::default();
b.port(8080).host("0.0.0.0");
let config = b.build()?;
```

**Choosing between the two:**
- **Consuming (`self -> Self`)** — simple one-shot configuration, no reuse needed. `Config::default().host("x").port(8080)`
- **Non-consuming (`&mut self -> &mut Self`)** — reusable builders, loop-friendly, or when `build()` must be called multiple times with variations. This is what `std::process::Command` and `std::thread::Builder` use.

For advanced builder patterns (typestate builders, derive macros, validation strategies), see [type-design.md](../type-design.md).

## The Principle

For **configuration and construction**, prefer consuming `self` with method chaining. For **live objects being operated on**, prefer `&mut self`.

The dividing line: is this object being *built* or being *operated on*?

## When `&mut self` Is Right

- **Large, heap-heavy structs.** Moving a `Vec<String>` with 10,000 elements through a chain is technically a memcpy. Usually optimized away, but `&mut self` avoids the question.
- **The caller keeps using the value.** Updating a live object (database connection, UI widget, server) — mutation is the natural model.
- **Interior mutability.** `RefCell`, `Mutex` contents are mutated through shared references.
- **Collection APIs.** `Vec::push`, `HashMap::insert` — mutating in place is the expected API.

## Common Source Languages

- **Java / C#** — everything is a reference; mutation through setters is the norm
- **Python** — mutable by default; methods return `None` and mutate in place
- **JavaScript** — object mutation is the default pattern
