# thiserror Patterns

`thiserror` is a derive macro for `std::error::Error`. It generates `Display`, `Error::source()`, and optionally `From` impls. It adds **zero** runtime cost beyond what you'd write by hand, and its types never appear in your public API.

## Derive Attributes Reference

### `#[error("...")]` — Display message

Applied to each variant. Supports field interpolation:

```rust
#[derive(Debug, thiserror::Error)]
pub enum ParseError {
    // Positional tuple field
    #[error("unexpected character: {0}")]
    UnexpectedChar(char),

    // Named struct fields
    #[error("expected {expected}, found {found} at line {line}")]
    Mismatch { expected: String, found: String, line: usize },

    // Debug formatting
    #[error("invalid token {token:?}")]
    InvalidToken { token: String },

    // Extra format args (arbitrary expressions)
    #[error("invalid lookahead_frames {0} (expected < {max})", max = i32::MAX)]
    InvalidLookahead(u32),
}
```

Access fields with `.field_name` / `.0` in additional format args:

```rust
use thiserror::Error;

fn first_char(s: &str) -> char {
    s.chars().next().unwrap_or('\0')
}

#[derive(Debug)]
struct Limits {
    lo: usize,
    hi: usize,
}

#[derive(Error, Debug)]
pub enum Error {
    #[error("first letter must be lowercase but was {:?}", first_char(.0))]
    WrongCase(String),

    #[error(
        "invalid index {idx}, expected at least {} and at most {}",
        .limits.lo,
        .limits.hi
    )]
    OutOfBounds { idx: usize, limits: Limits },
}
```

### `#[source]` — Error chain

Marks a field as the underlying cause. Generates `Error::source()` returning `Some(&self.field)`.

```rust
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("failed to read from disk")]
    DiskRead {
        #[source]
        cause: std::io::Error,
        path: PathBuf,
    },

    #[error("serialization failed")]
    Serialize {
        #[source]
        cause: serde_json::Error,
    },
}
```

A field named `source` is treated as `#[source]` automatically. Be explicit with the attribute when the field has a different name — clarity over convention.

### `#[from]` — Auto-conversion

Generates a `From<SourceType>` impl **and** implies `#[source]`. The variant must contain only the source error (plus an optional backtrace field).

```rust
#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("IO error")]
    Io(#[from] std::io::Error),

    #[error("TOML parse error")]
    Toml(#[from] toml::de::Error),

    #[error("missing required key: {0}")]
    MissingKey(String),  // No #[from] — constructed manually
}
```

**Constraint:** At most one variant per source type. If you need two variants from `io::Error` (read vs write), don't use `#[from]` — construct them manually with context.

### `#[error(transparent)]` — Delegate Display and source

Forwards both `Display` and `source()` to the inner error. Two uses:

**Catch-all variant:**
```rust
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("config invalid: {0}")]
    Config(String),

    #[error(transparent)]
    Other(#[from] anyhow::Error),
}
```

**Opaque public wrapper** (private impl can change freely):
```rust
#[derive(Debug, thiserror::Error)]
#[error(transparent)]
pub struct Error(#[from] ErrorImpl);

#[derive(Debug, thiserror::Error)]
enum ErrorImpl {
    #[error("connection lost")]
    ConnectionLost,
    #[error("protocol violation")]
    Protocol,
}
```

Callers see `Error`. The internal representation is a private implementation detail.

### Backtrace support

Requires nightly or Rust 1.73+. A field of type `std::backtrace::Backtrace` is automatically detected and exposed via `Error::provide()`.

```rust
use std::backtrace::Backtrace;

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("io failed")]
    Io {
        #[from]
        source: std::io::Error,
        backtrace: Backtrace,  // Captured in the generated From impl
    },
}
```

## Structuring Error Enums

### The struct + kind pattern

For errors that share context fields, use a struct wrapper with an inner kind enum. This avoids repeating shared fields across variants.

```rust
#[derive(Debug, thiserror::Error)]
#[error("{kind} at {path}:{line}")]
pub struct ParseError {
    pub kind: ParseErrorKind,
    pub path: PathBuf,
    pub line: usize,
}

#[derive(Debug, thiserror::Error)]
pub enum ParseErrorKind {
    #[error("unexpected token {token:?}")]
    UnexpectedToken { token: String },
    #[error("unterminated string")]
    UnterminatedString,
    #[error("invalid escape sequence")]
    InvalidEscape,
}
```

Callers can match on `kind` while having guaranteed access to `path` and `line` on every error.

### Layered errors across modules

Each module defines its own error type. Higher-level modules wrap lower-level errors explicitly:

```rust
// storage/mod.rs
#[derive(Debug, thiserror::Error)]
pub enum StorageError {
    #[error("key not found: {key}")]
    NotFound { key: String },
    #[error("storage backend failed")]
    Backend(#[source] std::io::Error),
}

// service/mod.rs
#[derive(Debug, thiserror::Error)]
pub enum ServiceError {
    #[error("failed to load user data")]
    Storage(#[from] StorageError),
    #[error("validation failed: {reason}")]
    Validation { reason: String },
}
```

Each layer speaks its own vocabulary. `ServiceError::Storage` wraps `StorageError` without leaking `io::Error` to the caller.

## Implementing Helpers on Error Types

Error types are regular types. Add methods for behavior callers need:

```rust
impl ApiError {
    /// HTTP status code for this error.
    pub fn status_code(&self) -> u16 {
        match self {
            Self::NotFound { .. } => 404,
            Self::Unauthorized => 401,
            Self::RateLimit { .. } => 429,
            Self::Internal { .. } => 500,
        }
    }

    /// Whether the client should retry.
    pub fn is_retryable(&self) -> bool {
        matches!(self, Self::RateLimit { .. } | Self::Internal { .. })
    }
}
```

## What thiserror Does NOT Do

- **No runtime overhead** — generates exactly the code you'd write by hand
- **No types in your public API** — `thiserror` is a build dependency only; generated code uses only `std` types
- **No backtraces by default** — opt-in with a `Backtrace` field
- **No error context/wrapping** — that's `anyhow`'s job. thiserror defines the error shapes; anyhow attaches context to them.
