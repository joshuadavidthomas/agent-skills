# anyhow Patterns

`anyhow` provides a single error type (`anyhow::Error`) that wraps any `std::error::Error` and accumulates context. Use it in **application** code — binaries, servers, CLIs — where you control the error boundary and callers don't need to match on specific variants.

## Core API

### `anyhow::Result<T>`

Type alias for `Result<T, anyhow::Error>`. Use as your default return type in application functions:

```rust
use anyhow::Result;

fn main() -> Result<()> {
    let config = load_config()?;
    run_server(config)?;
    Ok(())
}
```

Any error type implementing `std::error::Error + Send + Sync + 'static` converts automatically via `?`.

### `context()` and `with_context()`

Attach "what were you doing" information to errors. The most important `anyhow` API.

```rust
use anyhow::{Context, Result};
use std::path::Path;

fn read_config(path: &Path) -> Result<Config> {
    // Static context — always evaluated (cheap for string literals)
    let bytes = std::fs::read(path)
        .context("failed to read config file")?;

    // Dynamic context — closure only runs on error (use for format!)
    let config: Config = serde_json::from_slice(&bytes)
        .with_context(|| format!("failed to parse {} as JSON", path.display()))?;

    Ok(config)
}
```

**Always use `with_context()` when the message involves `format!`.** The closure avoids allocating the string on the success path.

`Context` also works on `Option<T>`, converting `None` to an error:

```rust
let home = std::env::var("HOME")
    .ok()  // Result → Option
    .context("HOME environment variable not set")?;
```

### `anyhow!` — Ad-hoc errors

Create an `anyhow::Error` from a format string or existing error:

```rust
use anyhow::anyhow;

// From a format string
return Err(anyhow!("port {} is already in use", port));

// From an existing error (preserves source chain)
return Err(anyhow!(io_error));
```

### `bail!` — Return early with an error

Equivalent to `return Err(anyhow!(...))`:

```rust
use anyhow::bail;

fn parse_mode(s: &str) -> Result<Mode> {
    match s {
        "fast" => Ok(Mode::Fast),
        "safe" => Ok(Mode::Safe),
        other => bail!("unknown mode: {other:?}"),
    }
}
```

### `ensure!` — Conditional bail

Equivalent to `if !cond { bail!(...) }`:

```rust
use anyhow::ensure;

fn validate(workers: usize, port: u16) -> Result<()> {
    ensure!(workers > 0, "worker count must be positive");
    ensure!(port > 0 && port < 65535, "invalid port: {port}");
    Ok(())
}
```

## Display Formats

`anyhow::Error` supports four display modes:

| Format | Output |
|--------|--------|
| `{}` | Outermost message only |
| `{:#}` | Full chain, single line (colon-separated) |
| `{:?}` | Full chain + backtrace (multi-line, "Caused by:" format) |
| `{:#?}` | Struct-style debug output |

For application `main()`, use `{:#}` for single-line logs or `{:?}` for detailed diagnostics:

```rust
fn main() {
    if let Err(err) = run() {
        eprintln!("Error: {:#}", err);  // "outer: middle: inner"
        std::process::exit(1);
    }
}
```

Or for full detail:

```rust
fn main() {
    if let Err(err) = run() {
        eprintln!("Error: {:?}", err);
        // Error: outer context
        //
        // Caused by:
        //     0: middle context
        //     1: root cause
        std::process::exit(1);
    }
}
```

## Error Chain Iteration

Walk the chain programmatically:

```rust
fn main() {
    if let Err(err) = run() {
        eprintln!("error: {}", err);
        for cause in err.chain().skip(1) {
            eprintln!("  caused by: {}", cause);
        }
    }
}
```

## Downcasting

Recover the original error type when needed:

```rust
match err.downcast_ref::<SqlError>() {
    Some(SqlError::UniqueViolation { column }) => {
        // Handle duplicate specifically
    }
    _ => return Err(err),
}
```

Downcasting works through context layers — `anyhow` preserves the original error even after `.context()` wrapping.

Three forms: `downcast::<T>()` (by value), `downcast_ref::<T>()` (by reference), `downcast_mut::<T>()` (by mutable reference).

## Backtrace Support

`anyhow` captures backtraces automatically when the environment variable is set:

| Variable | Effect |
|----------|--------|
| `RUST_BACKTRACE=1` | Backtraces for both panics and errors |
| `RUST_LIB_BACKTRACE=1` | Backtraces for errors only |
| `RUST_BACKTRACE=1` + `RUST_LIB_BACKTRACE=0` | Backtraces for panics only |

No code changes needed. The backtrace appears in `{:?}` output.

## When NOT to Use anyhow

- **Library public APIs** — callers can't match on `anyhow::Error` variants. Use `thiserror` for public error types.
- **When callers need to recover from specific errors** — structured enums are the right tool.
- **In `From` impls for library error types** — don't depend on `anyhow` in your library's public interface.

It's fine to use `anyhow` **internally** in a library (private functions, tests) — just don't expose it in the public API.
