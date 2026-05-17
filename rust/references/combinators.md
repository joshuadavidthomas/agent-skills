# Result and Option Combinators

The `?` operator handles propagation. Combinators handle transformation. Don't write `match` blocks when a combinator expresses intent more clearly and concisely.

## Result Combinators

### `map` — Transform the success value

```rust
let len: Result<usize, io::Error> =
    std::fs::read_to_string("file.txt").map(|s| s.len());
```

### `map_err` — Transform the error value

Use at boundaries to translate between error types:

```rust
let id: Result<u64, ApiError> = input.parse::<u64>()
    .map_err(|e| ApiError::InvalidId { raw: input.into(), source: e });
```

### `and_then` — Chain fallible operations

The success value feeds into the next fallible function:

```rust
let config: Result<Config, Error> = std::fs::read_to_string("config.toml")
    .map_err(Error::Io)
    .and_then(|s| toml::from_str(&s).map_err(Error::Parse));
```

Prefer `?` when you're in a function that returns `Result`. Use `and_then` in expression contexts (closures, iterators, chains).

### `or_else` — Fallback with a different fallible operation

```rust
let config = load_from_env()
    .or_else(|_| load_from_file("config.toml"))
    .or_else(|_| Ok(Config::default()));
```

### `unwrap_or` / `unwrap_or_else` / `unwrap_or_default` — Extract with fallback

```rust
let port: u16 = env_port().unwrap_or(8080);
let name: String = lookup_name(id).unwrap_or_else(|_| format!("user_{id}"));
let items: Vec<Item> = fetch_items().unwrap_or_default();
```

Use `unwrap_or_else` when the default is expensive to compute — the closure only runs on `Err`.

### `inspect` / `inspect_err` — Side effects without consuming

Useful for logging without breaking the chain:

```rust
let result = do_work()
    .inspect(|val| tracing::debug!("got result: {val:?}"))
    .inspect_err(|err| tracing::warn!("operation failed: {err}"));
```

## Option Combinators

### `ok_or` / `ok_or_else` — Convert Option to Result

When `None` is an error condition:

```rust
let user = users.get(&id)
    .ok_or(UserError::NotFound { id })?;

// Lazy version — only allocates on None
let home = std::env::var("HOME").ok()
    .ok_or_else(|| anyhow::anyhow!("HOME not set"))?;
```

### `map` — Transform the inner value

```rust
let upper: Option<String> = name.map(|s| s.to_uppercase());
```

### `and_then` — Chain optional operations

```rust
let port: Option<u16> = config.get("port")
    .and_then(|s| s.parse().ok());
```

### `filter` — Keep only if predicate holds

```rust
let admin: Option<&User> = user.filter(|u| u.is_admin());
```

### `unwrap_or` / `unwrap_or_else` / `unwrap_or_default`

Same semantics as `Result`:

```rust
let name = display_name.unwrap_or("anonymous");
let count = cached_count.unwrap_or_default();  // 0 for numeric types
```

### `flatten` — Collapse nested Options

```rust
let x: Option<Option<i32>> = Some(Some(42));
let y: Option<i32> = x.flatten();  // Some(42)
```

## Cross-Type Conversions

### `Result::ok()` — Discard the error, get Option

```rust
let maybe_port: Option<u16> = std::env::var("PORT").ok()
    .and_then(|s| s.parse().ok());
```

### `Result::err()` — Discard the success, get Option of error

```rust
let errors: Vec<ParseError> = inputs.iter()
    .map(|s| s.parse::<Config>())
    .filter_map(Result::err)
    .collect();
```

### `Option::ok_or()` — Convert to Result (see above)

### `transpose` — Flip Option<Result> ↔ Result<Option>

```rust
// When you have Option<Result<T, E>> but need Result<Option<T>, E>
let maybe_config: Option<Result<Config, Error>> =
    path.map(|p| load_config(p));
let config: Result<Option<Config>, Error> = maybe_config.transpose();
```

This is essential when working with optional fields that might fail to parse:

```rust
// In a deserialization context
let timeout: Option<Duration> = raw.timeout
    .map(parse_duration)  // Option<Result<Duration, E>>
    .transpose()?;        // Result<Option<Duration>, E>, then propagate
```

## Iterator Error Patterns

### `collect` into `Result`

Collecting an iterator of `Result` values yields a single `Result`. Stops at the first error:

```rust
let numbers: Result<Vec<i32>, _> = strings.iter()
    .map(|s| s.parse::<i32>())
    .collect();
```

### `filter_map` with `Result::ok()`

When you want to skip errors silently (appropriate for best-effort operations):

```rust
let valid: Vec<Config> = paths.iter()
    .map(load_config)
    .filter_map(Result::ok)
    .collect();
```

### Partition successes and failures

When you need both:

```rust
let (successes, failures): (Vec<_>, Vec<_>) = items.iter()
    .map(process)
    .partition(Result::is_ok);

let successes: Vec<Item> = successes.into_iter().map(Result::unwrap).collect();
let failures: Vec<Error> = failures.into_iter().map(Result::unwrap_err).collect();
```

## When to Use `?` vs Combinators

| Situation | Prefer |
|-----------|--------|
| Propagating in a function body | `?` |
| Transforming inside a closure or chain | Combinator |
| Converting Option to Result | `ok_or` / `ok_or_else` |
| Adding context in anyhow code | `.context()` |
| Converting between error types | `.map_err()` |
| Multiple fallible steps in sequence | `?` on each step |
| Expression-level error handling | Combinators |

The `?` operator is syntactic sugar for `match` + `From`. Combinators are methods that express transformation intent. Use whichever reads more clearly at the call site.
