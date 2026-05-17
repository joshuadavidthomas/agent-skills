# Error Strategy and Design

Errors are **domain facts**, not formatting exercises. An error type tells callers what went wrong, whether they can recover, and what information is available.

The governing principle: **be empathetic to your caller.** Imagine yourself having to handle the error. Could you write robust recovery code given the error type? Could you translate it into a message the end user can understand? Most error design problems stem from making errors easy for the *author* at the expense of the *caller* — a crate-wide enum, a wrapped dependency type, a bare `String`. Every rule below is an application of this principle.

The central axis: **library or application?** Everything flows from that.

## The Central Rule: Library vs Application

| Context | Crate | Error type | Why |
|---------|-------|-----------|-----|
| **Library** (reusable crate) | `thiserror` | Structured `enum` | Callers need variants to match on for control flow |
| **Application** (binary, server) | `anyhow` | `anyhow::Error` | You control the error boundary; you need context, not types |
| **Boundary** (lib consumed by your app) | Both | thiserror at the edge, anyhow inside | Structured where callers need it, ergonomic where they don't |

This is the ecosystem consensus. BurntSushi, Palmieri, Effective Rust Item 4, and the crate authors themselves all converge on it.

## Library Errors: thiserror

Libraries expose structured error types. Callers match on variants for control flow and recovery. Every variant is a **fact** about what failed.

### Rule 1: One error enum per unit of fallibility

Don't build one `Error` enum for an entire crate. Each public function (or tightly related group) gets its own error type scoped to *its* failure modes.

```rust
// WRONG — crate-wide "ball of mud"
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("connection failed")]
    Connection(#[from] std::io::Error),
    #[error("parse failed")]
    Parse(#[from] serde_json::Error),
    #[error("auth failed")]
    Auth,
    #[error("rate limited")]
    RateLimit { retry_after: Duration },
    // 15 more variants from unrelated subsystems...
}
```

```rust
// RIGHT — scoped to the operation
#[derive(Debug, thiserror::Error)]
pub enum ConnectError {
    #[error("DNS resolution failed for {host}")]
    DnsFailure { host: String, source: std::io::Error },
    #[error("TLS handshake failed")]
    TlsHandshake(#[source] native_tls::Error),
    #[error("connection timed out after {timeout:?}")]
    Timeout { timeout: Duration },
}

#[derive(Debug, thiserror::Error)]
pub enum QueryError {
    #[error("query syntax error at position {position}")]
    Syntax { position: usize },
    #[error("query execution failed")]
    Execution(#[source] sqlx::Error),
}
```

**Why:** A crate-wide enum is *dishonest* — it claims a function can produce errors it never actually does. If `query()` can't produce `ConnectError`, but the crate-wide `Error` includes it, callers must write dead match arms for impossible cases. The compiler can't catch it when someone later modifies the function to throw a new error — the dead arm silently becomes load-bearing. Scoped errors let callers know exactly which failures a function can produce and handle only what's real.

**Authority:** Jewson, "Modular Errors in Rust." Effective Rust Item 4. Parsons, "The Trouble with Typed Errors."

### Rule 2: Variants carry structured data, not strings

Each variant is a data structure. Callers extract fields for logging, retry logic, or user messages. `Error(String)` forces them to parse your prose.

```rust
// WRONG
#[error("invalid config: {0}")]
InvalidConfig(String),

// RIGHT
#[error("config key {key:?} must be a positive integer, got {value:?}")]
InvalidConfigValue { key: String, value: String },
```

**Authority:** std: `io::Error` has `ErrorKind` + optional inner error. `serde_json::Error` has `line()`, `column()`, `classify()`.

### Rule 3: Preserve the error chain with `#[source]`

Every variant wrapping an underlying error must expose it via `source()`. This enables error chain traversal for logging and diagnostics.

```rust
// WRONG — chain broken, cause is lost
#[error("database query failed: {0}")]
Database(String),  // .source() returns None

// RIGHT — chain preserved
#[error("database query failed")]
Database {
    #[source]
    source: sqlx::Error,
    query: String,
},
```

`#[from]` implies `#[source]` and generates a `From` impl. Use `#[from]` when the conversion is unambiguous (one variant per source type). Use `#[source]` when you need additional context fields alongside the cause.

**When to break the chain:** Preserving `#[source]` is the default, but it has a cost — it exposes the dependency type in your public API. If your variant contains `sqlx::Error` via `#[source]`, callers now transitively depend on `sqlx`. When the dependency is an implementation detail (you might swap it later), extract the relevant information into your own fields and let the source error drop. See Rule 7b below.

**Authority:** `std::error::Error::source` + thiserror docs (source chaining).

### Rule 4: Don't auto-derive `From` for everything

`#[from]` generates `From<SourceError> for YourError`. This is convenient but dangerous — it silently wraps errors without context and prevents having multiple variants from the same source type.

```rust
// CAREFUL — auto-conversion loses context about WHICH io operation failed
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("io error")]
    Io(#[from] std::io::Error),  // Which file? Which operation? Lost.
}

// BETTER — explicit conversion adds context
#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("failed to read config from {path}")]
    ReadConfig { source: std::io::Error, path: PathBuf },
    #[error("failed to write output to {path}")]
    WriteOutput { source: std::io::Error, path: PathBuf },
}
```

Use `#[from]` when the source type is unambiguous (e.g., one JSON error variant). Use manual construction when you need to distinguish multiple operations with the same underlying error type.

**Authority:** thiserror docs (`#[from]` constraints) + Jewson (contextful, scoped errors).

### Rule 5: Mark variants `#[non_exhaustive]` for public crates

If you publish a crate, adding a variant is a breaking change unless the enum is `#[non_exhaustive]`. Apply it to public error enums that may grow.

```rust
#[derive(Debug, thiserror::Error)]
#[non_exhaustive]
pub enum ParseError {
    #[error("unexpected token {token:?} at line {line}")]
    UnexpectedToken { token: String, line: usize },
    #[error("unterminated string literal")]
    UnterminatedString,
}
```

Callers will need a `_ =>` arm — this is the correct exception for foreign `#[non_exhaustive]` types.

**Authority:** Rust Reference: `#[non_exhaustive]` + Rust semver expectations for public enums.

### Rule 6: Define a `Result` type alias

Reduce repetition. Follow the std convention (`io::Result`, `fmt::Result`).

```rust
pub type Result<T> = std::result::Result<T, Error>;
```

For full thiserror attribute reference (all derive attributes, `#[error(transparent)]`, backtrace support), see [references/thiserror-patterns.md](references/thiserror-patterns.md).

### Rule 7: Define errors in terms of the problem, not the solution

Error variants should describe **what failed** in domain terms, not **how** you tried to solve it. Wrapping dependency error types directly tells callers your implementation details instead of giving them actionable information.

```rust
// WRONG — tells callers HOW you solve it
#[derive(Debug, thiserror::Error)]
pub enum FetchTxError {
    #[error("io error")]
    Io(#[from] std::io::Error),
    #[error("http error")]
    Http(#[from] http2::Error),
    #[error("serde error")]
    Serde(#[from] serde_cbor::Error),
    #[error("openssl error")]
    Openssl(#[from] openssl::ssl::Error),
}

// RIGHT — tells callers WHAT failed, in domain vocabulary
#[derive(Debug, thiserror::Error)]
pub enum FetchTxError {
    #[error("could not connect to {url}")]
    ConnectionFailed { url: String, reason: String },
    #[error("transaction {0} not found")]
    TxNotFound(Txid),
    #[error("response data is not valid CBOR")]
    InvalidEncoding { error_message: String },
    #[error("public key is malformed")]
    MalformedPublicKey { key_bytes: Vec<u8>, reason: String },
    #[error("signature verification failed for tx {txid}")]
    SignatureVerificationFailed { txid: Txid, pk: Pubkey, sig: Signature },
}
```

**Why wrapping dependency types hurts callers:**
- They must read the *dependency's* docs to understand your error cases (what does `openssl::ssl::Error` even mean here?)
- They must add your transitive dependencies to their `Cargo.toml` to handle your errors
- Swapping a dependency (openssl → rustls, serde_cbor → ciborium) becomes a breaking change
- Low-level errors travel up the stack with no context ("IO error: No such file or directory" — *which file?*)

**Embed, don't wrap:** When multiple dependencies can produce similar failures, flatten them into shared domain variants. A `MalformedPublicKey` variant works whether the underlying crypto library is `ecdsa`, `bls12_381_sign`, or something else. Extract the relevant information (key bytes, reason string) and let the dependency-specific error drop.

**When wrapping is acceptable:**
- `std::io::Error` with sufficient context (operation + paths) — it's universally familiar and carries OS error codes
- Converting a lower-level error to a string and attaching it to a descriptive variant — but check for sensitive data leaks

For extended examples and academic grounding, see [references/designing-error-types.md](references/designing-error-types.md).

### Rule 8: Shrink error types with parse-don't-validate

If a function validates inputs *and* does work, its error type carries both validation failures and operational failures. Extract validation into a dedicated type and the validation variants disappear from the error enum entirely.

```rust
// BEFORE — send_mail validates AND sends, error type is bloated
pub enum SendMailError {
    MalformedAddress { address: String, reason: String },  // validation
    FailedToConnect { source: std::io::Error },            // operational
}

// AFTER — EmailAddress is valid by construction
pub struct EmailAddress(String);  // see [type-design.md](type-design.md)

pub enum SendMailError {
    FailedToConnect { source: std::io::Error },  // only operational errors remain
}
```

Every newtype that enforces an invariant is one fewer variant in every error enum that would otherwise need to validate that invariant. See [type-design.md](type-design.md) for the full parse-don't-validate pattern.

## Application Errors: anyhow

Application code doesn't export error types — it **handles** them. Use `anyhow` for ergonomic propagation with context.

### Rule 9: Use `anyhow::Result` as your return type

```rust
use anyhow::{Context, Result};
use std::path::Path;

fn load_config(path: &Path) -> Result<Config> {
    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read config from {}", path.display()))?;
    let config: Config = toml::from_str(&content)
        .context("failed to parse config as TOML")?;
    Ok(config)
}
```

Every `?` propagates with the full error chain intact. `context()` and `with_context()` add layers of "what was happening when this failed."

### Rule 10: Add context at every abstraction boundary

Bare `?` propagates the error but loses *what you were trying to do*. Add context so the error chain reads like a stack trace of intent.

```rust
use anyhow::{Context, Result};
use std::path::Path;

// WRONG — bare propagation (no context)
fn setup_wrong(config_path: &Path) -> Result<()> {
    let config = load_config(config_path)?;     // "file not found" — which file?
    let _db = connect_db(&config)?;             // "connection refused" — to what?
    Ok(())
}

// RIGHT — context at each boundary
fn setup(config_path: &Path) -> Result<()> {
    let config = load_config(config_path)
        .context("failed to load application config")?;
    let _db = connect_db(&config)
        .context("failed to connect to database")?;
    Ok(())
}
```

**Output with `{:#}`:**
```
failed to connect to database: connection refused: Connection refused (os error 111)
```

Use `.context("static string")` for fixed messages. Use `.with_context(|| format!(...))` when you need runtime values — the closure is only evaluated on error.

### Rule 11: Use `bail!` and `ensure!` for early returns

```rust
use anyhow::{bail, ensure, Result};

fn validate_port(port: u16) -> Result<()> {
    ensure!(port != 0, "port must be non-zero");
    Ok(())
}

fn process_command(cmd: &str) -> Result<()> {
    if cmd.is_empty() {
        bail!("empty command");
    }
    // ...
    Ok(())
}
```

`bail!(...)` is `return Err(anyhow!(...))`. `ensure!(cond, ...)` is `if !cond { bail!(...) }`. Both accept format strings.

For the full anyhow API reference (display formats, chain iteration, downcasting), see [references/anyhow-patterns.md](references/anyhow-patterns.md).

## Result and Option Combinators

The `?` operator handles the common case. Combinators handle the rest. Don't write `match` when a combinator expresses intent more clearly.

### The essential combinators

| Combinator | On | Does | Use when |
|---|---|---|---|
| `map` | `Result`/`Option` | Transform the success/some value | Adapting the inner type |
| `map_err` | `Result` | Transform the error | Adding context or converting error types |
| `and_then` | `Result`/`Option` | Chain a fallible operation | Next step can also fail |
| `unwrap_or` | `Result`/`Option` | Provide a default | Fallback value is cheap |
| `unwrap_or_else` | `Result`/`Option` | Provide a lazy default | Fallback is expensive to compute |
| `unwrap_or_default` | `Result`/`Option` | Use `Default::default()` | Type has a sensible default |
| `ok_or` / `ok_or_else` | `Option` | Convert to `Result` | `None` is an error condition |
| `transpose` | `Option<Result>` | Flip to `Result<Option>` | Working with optional fallible ops |

```rust
// map_err: convert between error types at boundaries
let id = input.parse::<u64>()
    .map_err(|e| ApiError::InvalidId { raw: input.into(), source: e })?;

// ok_or_else: Option → Result when absence is an error
let user = users.get(&id)
    .ok_or_else(|| ApiError::NotFound { id })?;

// and_then: chain fallible operations
let config = std::env::var("CONFIG_PATH")
    .ok()
    .and_then(|p| std::fs::read_to_string(p).ok());
```

For the full combinator quick-reference with more examples, see [references/combinators.md](references/combinators.md).

## When to Panic

Panics are for **bugs**, not errors. A panic means "this is a programmer mistake and the program cannot continue." User input failures, network errors, file-not-found — these are expected conditions, not panics.

### `panic!` is correct for:

- **Internal invariant violations** — a state your code guarantees can't happen
- **Unrecoverable system failures** — `mmap` failed, allocator OOM
- **Unreachable code paths** — `unreachable!()` after exhaustive checks

### `expect()` over `unwrap()`

When you know a value is `Some`/`Ok` due to prior logic, use `expect()` with a message explaining **why** it's safe:

```rust
// After validation that guarantees non-empty
let first = validated_items.first()
    .expect("validated_items is non-empty after validation");

// Static regex that is known valid at compile time
let re = Regex::new(r"^\d{4}-\d{2}-\d{2}$")
    .expect("date regex is valid");
```

`unwrap()` is acceptable in tests and when the safety is obvious from the immediately surrounding code. In production code, prefer `expect()` with a message or propagate with `?`.

### Never panic for:

- User input (parse it, return `Result`)
- File/network I/O (always `Result`)
- Configuration errors (return `Result`, let the caller decide)
- Missing optional data (use `Option`)

**Authority:** BurntSushi, "unwrap is not that bad." Effective Rust Item 3.

## Error Boundary Rules

Errors cross abstraction boundaries. Handle the translation deliberately.

### Log once, at the edge

Don't log errors at every layer. Each layer **propagates** (via `?` or context). The outermost handler — `main()`, the HTTP middleware, the CLI runner — logs once with the full chain.

```rust
// WRONG — logging at every layer
fn read_config() -> Result<Config> {
    let content = std::fs::read_to_string("config.toml")
        .map_err(|e| {
            log::error!("Failed to read config: {}", e);  // logged here
            AppError::Config(e)
        })?;
    Ok(parse(content)?)
}

// RIGHT — propagate, log at the edge
fn read_config() -> Result<Config> {
    let content = std::fs::read_to_string("config.toml")
        .context("failed to read config.toml")?;
    Ok(parse(content).context("failed to parse config")?)
}

fn main() {
    if let Err(err) = run() {
        // Log ONCE with full chain
        eprintln!("Error: {:#}", err);
        std::process::exit(1);
    }
}
```

### Translate at layer boundaries

When crossing from one abstraction to another (e.g., database → domain → HTTP), translate the error into the vocabulary of the outer layer. Don't leak `sqlx::Error` through your API boundary.

```rust
// Domain layer — speaks domain language
#[derive(Debug, thiserror::Error)]
pub enum UserError {
    #[error("user {id} not found")]
    NotFound { id: UserId },
    #[error("email {email} already registered")]
    DuplicateEmail { email: String },
    #[error("internal database error")]
    Internal(#[source] sqlx::Error),
}

// Repository translates database errors into domain errors
impl UserRepo {
    pub fn find(&self, id: UserId) -> Result<User, UserError> {
        self.db.query(/* ... */)
            .map_err(|e| match e {
                sqlx::Error::RowNotFound => UserError::NotFound { id },
                other => UserError::Internal(other),
            })
    }
}
```

### Retryability as a method

If callers need to decide whether to retry, expose it as a method — don't make them match on variant names they can't rely on.

```rust
impl ApiError {
    pub fn is_retryable(&self) -> bool {
        matches!(self,
            Self::RateLimit { .. } |
            Self::ServiceUnavailable { .. } |
            Self::Timeout { .. }
        )
    }
}
```

## Common Mistakes (Agent Failure Modes)

- **`Error(String)` in a library** → Callers can't match. Define structured variants.
- **One giant error enum for the whole crate** → Scope errors to operations. Callers handle only what a function can actually produce.
- **`#[from]` on every variant** → Silent conversions lose context. Use `#[from]` only when conversion is unambiguous.
- **`anyhow` in a library's public API** → Callers lose the ability to match. Use `thiserror` for public errors; `anyhow` is for your binary.
- **Bare `?` without context in application code** → The error chain says *what* failed but not *what you were doing*. Add `.context()`.
- **Logging errors at every layer** → Log once at the outermost handler. Inner layers propagate.
- **`unwrap()` on user input or I/O** → These are expected failure modes. Use `?` or combinators.
- **`Box<dyn Error>` as the public error type** → Callers can't match without downcasting, which requires they depend on the exact same semver version of the inner error type. Boxed errors also can't be cloned or serialized (problematic when errors cross process boundaries). If callers need programmatic access to error data, embed the relevant bits as fields on your enum variants — don't force them to downcast.

## Cross-References

- [type-design.md](type-design.md) — domain modeling and parse-don't-validate defaults
- [type-design.md](type-design.md) — Newtype errors, parse-don't-validate at boundaries
- [ownership.md](ownership.md) — Owned vs borrowed data in error types, `Send + Sync` bounds
- [traits.md](traits.md) — `Error` trait, `From` implementations, trait objects for error erasure
- [async.md](async.md) — `?` in async functions, `JoinError` handling, error propagation across tasks

## Review Checklist

1. **Empathy check:** Could *you* write robust recovery code given this error type? Could you translate it into a user-facing message?
2. **Library or application?** Libraries use `thiserror` enums. Applications use `anyhow`. At the boundary, use both.
3. **Is the error type scoped to its operation?** One crate-wide `Error` enum is dishonest — it claims impossible failures. Each public function (or related group) should have its own error type.
4. **Does every variant carry structured data?** No `Error(String)`. Callers must be able to extract fields, not parse messages.
5. **Does the error describe the problem, not the solution?** Variants named after dependency types (`IoError`, `HttpError`) leak implementation details. Name them after *what failed* (`ConnectionFailed`, `InvalidEncoding`).
6. **Is the error chain preserved *appropriately*?** Use `#[source]` when the cause is useful to callers. Break the chain when it would expose an implementation-detail dependency — extract relevant data into your own fields instead.
7. **Is `#[from]` used only where unambiguous?** Multiple variants from the same source type? Use manual construction with context fields instead.
8. **Does application code add context at every `?`?** Bare propagation loses intent. Add `.context()` or `.with_context()`.
9. **Are panics reserved for bugs?** User input, I/O, and network errors use `Result`. `panic!` is for invariant violations and unreachable code.
10. **Are errors logged once, at the edge?** Inner layers propagate. The outermost handler logs with `{:#}` for the full chain.
11. **Could a newtype eliminate a variant?** If a function validates inputs, consider parse-don't-validate to remove validation errors from the enum entirely.
12. **Is there a `Result` type alias?** `pub type Result<T> = std::result::Result<T, Error>;` reduces boilerplate within each module.
