# Parse, Don't Validate

The core distinction: **validation** checks data and throws away the proof. **Parsing** checks data and encodes the result in the type system. After parsing, the type guarantees validity — no downstream re-checking.

## The Smell

Validation scattered throughout the codebase, with downstream code trusting that "someone validated upstream."

```rust
fn process_order(items: Vec<Item>, customer_id: String) -> Result<(), OrderError> {
    if items.is_empty() { return Err(OrderError::EmptyOrder); }
    if customer_id.is_empty() { return Err(OrderError::MissingCustomer); }

    let first_item = items.first().unwrap(); // "we already checked" — but the type doesn't know
    // ...
}
```

Every function downstream must either re-validate (redundant), trust upstream (`unwrap()`), or accept `Option` and handle `None` again. This is **shotgun parsing** — validation scattered everywhere, hoping every path checks everything.

## The Idiomatic Alternative

```rust
struct NonEmptyVec<T>(Vec<T>);

impl<T> NonEmptyVec<T> {
    pub fn try_from_vec(v: Vec<T>) -> Result<Self, EmptyVecError> {
        if v.is_empty() { return Err(EmptyVecError); }
        Ok(Self(v))
    }

    pub fn first(&self) -> &T {
        &self.0[0] // Always safe — guaranteed non-empty
    }
}

struct CustomerId(String);

impl CustomerId {
    pub fn parse(raw: String) -> Result<Self, InvalidCustomerId> {
        if raw.is_empty() { return Err(InvalidCustomerId::Empty); }
        Ok(Self(raw))
    }
}
```

Now the processing function:
```rust
fn process_order(items: NonEmptyVec<Item>, customer: CustomerId) -> Result<(), OrderError> {
    let first_item = items.first(); // No unwrap. Type guarantees it exists.
    // customer is guaranteed valid — no re-checking.
}
```

The **caller** parses at the boundary. The processing function receives already-valid types.

## Boundary Architecture

```
External World (raw data)
  HTTP body, CLI args, config file, DB rows, JSON
                    │
                    │ parse (can fail)
                    ▼
Boundary Layer
  raw → domain type conversion
  String → EmailAddress, u64 → PositiveAmount, etc.
  All validation errors surface HERE, not deeper
                    │
                    │ domain types (guaranteed valid)
                    ▼
Domain Logic
  Works with EmailAddress, CustomerId, NonEmptyVec, etc.
  No validation. No unwrap. No "should never happen."
```

## Boundary Examples

### HTTP handler

```rust
async fn create_user(Json(body): Json<CreateUserRequest>) -> Result<Json<User>, ApiError> {
    let email = EmailAddress::parse(body.email)?;
    let username = Username::parse(body.username)?;
    let age = Age::try_from(body.age)?;

    // Past this point: only domain types. No validation.
    let user = user_service.create(email, username, age).await?;
    Ok(Json(user))
}

// The service never sees raw strings
impl UserService {
    async fn create(&self, email: EmailAddress, username: Username, age: Age) -> Result<User, CreateUserError> {
        // All arguments guaranteed valid. No re-checking.
    }
}
```

### CLI arguments

```rust
fn main() -> Result<(), Box<dyn Error>> {
    let args = Args::parse(); // clap

    let port = Port::try_from(args.port)?;
    let host = HostName::parse(&args.host)?;
    let config = Config::from_path(&args.config)?;

    run(host, port, config) // only validated types
}
```

### Config files

```rust
// Raw config (from TOML/YAML/JSON)
#[derive(Deserialize)]
struct RawConfig {
    port: u16,
    host: String,
    max_connections: usize,
}

// Validated config (used throughout the app)
struct Config {
    port: Port,
    host: HostName,
    max_connections: NonZeroUsize,
}

impl Config {
    fn parse(raw: RawConfig) -> Result<Self, ConfigError> {
        Ok(Self {
            port: Port::try_from(raw.port)?,
            host: HostName::parse(&raw.host)?,
            max_connections: NonZeroUsize::try_from(raw.max_connections)
                .map_err(|_| ConfigError::ZeroConnections)?,
        })
    }
}
```

## Standard Library Parsers

| Raw type | Parsed type | What's guaranteed |
|----------|-------------|-------------------|
| `u32` | `NonZero<u32>` | Value is not zero |
| `String` | `IpAddr` | Valid IPv4 or IPv6 |
| `String` | `SocketAddr` | Valid IP + port |
| `&str` | `http::Method` | Valid HTTP method |
| `&str` | `url::Url` | Valid URL with scheme, host, etc. |

## Common Mistakes

**Parsing then discarding.** Parsing into a type but then extracting the raw value and passing that forward — you've lost the proof.

```rust
// WRONG — parses then immediately discards the result
let email = EmailAddress::parse(raw)?;
send_email(email.as_str()); // Back to &str — other code can't trust it

// RIGHT — pass the domain type through
let email = EmailAddress::parse(raw)?;
send_email(&email); // Callee receives proof of validity
```

**Validating in multiple places.** If you find yourself checking the same invariant in multiple functions, you haven't parsed — you've scattered validation.

**"Parsing" that doesn't restrict.** A newtype with `pub fn new(s: String) -> Self` (no validation) isn't parsing — it's wrapping. Exception: newtypes for type distinction (Miles vs Kilometers) don't need validation because the invariant is identity, not a data constraint.

## When Parsing Is Overkill

- The value has no domain constraints (truly arbitrary text)
- The value is internal and ephemeral (loop counter, temporary buffer)
- The overhead of a newtype harms readability more than it helps correctness

The test: "Would passing the wrong value here cause a bug that the compiler could have caught?" If yes, parse into a domain type. If no, a bare type is fine.

## Common Source Languages

- **Python / JavaScript** — validation functions return booleans; no type-level encoding of "already validated"
- **Java** — checked exceptions are the closest parallel but don't produce a more-specific type
- **Go** — validation returns `error` but the original untyped value is still what you pass around
