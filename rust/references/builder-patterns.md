# Builder Implementation Patterns

Deep-dive on builder pattern: consuming vs non-consuming, derive macros, validation, and typestate-builder hybrids.

## When to Use a Builder

**Use a builder when:**
- More than 3-4 optional parameters
- Complex validation across multiple fields
- Construction has side effects (I/O, resource allocation)
- The same configuration is reused to create multiple instances
- Field ordering doesn't matter (unlike positional arguments)

**Don't use a builder when:**
- Simple struct with few required fields → use `Struct { field: value }`
- All fields always required → constructor function
- Fields naturally ordered → tuple struct or `new(a, b, c)`

## Non-Consuming Builder (Preferred)

Builder methods take `&mut self` and return `&mut Self`. Build method takes `&self` (not consuming the builder).

```rust
#[derive(Default)]
pub struct RequestBuilder {
    method: Option<Method>,
    url: Option<Url>,
    headers: Vec<(String, String)>,
    body: Option<Vec<u8>>,
}

impl RequestBuilder {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn method(&mut self, method: Method) -> &mut Self {
        self.method = Some(method);
        self
    }

    pub fn url(&mut self, url: impl Into<Url>) -> &mut Self {
        self.url = Some(url.into());
        self
    }

    pub fn header(&mut self, key: impl Into<String>, value: impl Into<String>) -> &mut Self {
        self.headers.push((key.into(), value.into()));
        self
    }

    pub fn body(&mut self, body: impl Into<Vec<u8>>) -> &mut Self {
        self.body = Some(body.into());
        self
    }

    pub fn build(&self) -> Result<Request, BuildError> {
        let method = self.method.clone().ok_or(BuildError::MissingMethod)?;
        let url = self.url.clone().ok_or(BuildError::MissingUrl)?;

        Ok(Request {
            method,
            url,
            headers: self.headers.clone(),
            body: self.body.clone(),
        })
    }
}
```

**Usage patterns:**

```rust
// One-liner chaining
let req = RequestBuilder::new()
    .method(Method::POST)
    .url("https://api.example.com")
    .build()?;

// Incremental construction
let mut builder = RequestBuilder::new();
builder.method(Method::GET);
builder.url(base_url);

for (k, v) in custom_headers {
    builder.header(k, v);
}

let req = builder.build()?;

// Reuse for multiple requests
let mut template = RequestBuilder::new();
template.url("https://api.example.com");
template.header("Authorization", "Bearer ...");

let get_req = template.method(Method::GET).build()?;
let post_req = template.method(Method::POST).body(data).build()?;
```

**Pros:**
- Reusable — same builder creates multiple instances
- Works in loops — easy to add items incrementally
- No ownership juggling — caller keeps the builder

**Cons:**
- Fields must be cloneable (build takes `&self`)
- Or use `Option::take()` in build (but then builder is in indeterminate state)

## Consuming Builder

Builder methods take `self` by value and return `Self`. Build method also consumes `self`.

```rust
pub struct CommandBuilder {
    program: String,
    args: Vec<String>,
    env: Vec<(String, String)>,
    stdout: Option<Box<dyn Write + Send>>,
}

impl CommandBuilder {
    pub fn new(program: impl Into<String>) -> Self {
        Self {
            program: program.into(),
            args: Vec::new(),
            env: Vec::new(),
            stdout: None,
        }
    }

    pub fn arg(mut self, arg: impl Into<String>) -> Self {
        self.args.push(arg.into());
        self
    }

    pub fn env(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.env.push((key.into(), value.into()));
        self
    }

    pub fn stdout(mut self, out: Box<dyn Write + Send>) -> Self {
        self.stdout = Some(out);
        self
    }

    pub fn build(self) -> Command {
        Command {
            program: self.program,
            args: self.args,
            env: self.env,
            stdout: self.stdout,
        }
    }
}
```

**Use consuming builders when:**
- Fields contain non-Clone types (`Box<dyn Trait>`, file handles)
- Builder should not be reused after build
- One-liner chaining is the primary use case

**Cons:**
- Cannot reuse builder
- Incremental construction requires reassignment: `builder = builder.arg("x")`

## Validation Strategies

### Return Result from build()

The standard approach — validate at build time, return `Result`:

```rust
pub fn build(&self) -> Result<Config, ConfigError> {
    let port = self.port.ok_or(ConfigError::MissingPort)?;
    let host = self.host.clone().ok_or(ConfigError::MissingHost)?;

    if port == 0 {
        return Err(ConfigError::InvalidPort(0));
    }

    Ok(Config { port, host, /* ... */ })
}
```

### Panic for programmer errors

Some builders panic for truly impossible combinations (double-set of exclusive options). Use sparingly:

```rust
pub fn compression(mut self, algo: Compression) -> Self {
    if self.raw_mode {
        panic!("cannot enable compression in raw mode");
    }
    self.compression = Some(algo);
    self
}
```

Consider whether the API should make the illegal state unrepresentable instead.

### Typestate for required fields

Use type parameters to track which required fields are set. Build only exists when all requirements are met. See [typestate-patterns.md](typestate-patterns.md) for the full pattern.

## Derive Macros

### derive_builder

The `derive_builder` crate generates builder boilerplate:

```rust
use derive_builder::Builder;

#[derive(Builder)]
#[builder(setter(into))]
pub struct Server {
    host: String,
    port: u16,
    #[builder(default = "4")]
    workers: usize,
    #[builder(default)]
    tls: Option<TlsConfig>,
}

// Generates ServerBuilder with:
// - host(&mut self, impl Into<String>) -> &mut Self
// - port(&mut self, impl Into<u16>) -> &mut Self  
// - workers(&mut self, impl Into<usize>) -> &mut Self
// - tls(&mut self, impl Into<Option<TlsConfig>>) -> &mut Self
// - build(&self) -> Result<Server, ServerBuilderError>
```

**Attributes:**
- `#[builder(default)]` — use `Default::default()` if not set
- `#[builder(default = "expr")]` — use expression if not set
- `#[builder(setter(into))]` — setter accepts `impl Into<T>`
- `#[builder(setter(strip_option))]` — setter takes `T`, wraps in `Some(T)`
- `#[builder(try_setter)]` — setter returns `Result` for validation
- `#[builder(pattern = "owned")]` — consuming builder style

### typed-builder

Alternative with typestate for required fields:

```rust
use typed_builder::TypedBuilder;

#[derive(TypedBuilder)]
pub struct Server {
    host: String,
    port: u16,
    #[builder(default = 4)]
    workers: usize,
}

// ServerBuilder::<(), ()>::new() — host and port not set
// .host("...") returns ServerBuilder::<(String,), ()>
// .port(8080) returns ServerBuilder::<(String,), (u16,)>
// .build() only exists on ServerBuilder::<(String,), (u16,)>
```

The type signature tracks which fields are set. `build()` is only available when all required fields are provided. Compile-time enforcement, no runtime checks.

## Real-World Examples

### std::process::Command

Non-consuming builder with `&mut self` methods:

```rust
let output = Command::new("git")
    .arg("status")
    .arg("--short")
    .current_dir("/my/repo")
    .output()?;
```

Note: `spawn()` and `output()` take `&mut self`, allowing reuse.

### reqwest::ClientBuilder

Consuming builder for one-time configuration:

```rust
let client = reqwest::Client::builder()
    .timeout(Duration::from_secs(10))
    .user_agent("my-app/1.0")
    .build()?;
```

### thread::Builder

Mix of required (spawn function) and optional (name, stack size):

```rust
let handle = thread::Builder::new()
    .name("worker".into())
    .stack_size(4 * 1024 * 1024)
    .spawn(|| {
        // thread code
    })?;
```

## Common Mistakes

**Panic on missing required fields** — Use `Result` instead. Panics are for programmer errors (logic bugs), not user errors (missing config).

**Non-consuming builder with non-Clone fields** — Either clone in build(), use `Option::take()` (leaves builder in odd state), or switch to consuming builder.

**Inconsistent return types** — All setter methods should return the same type (`&mut Self` or `Self`). Mixing breaks chaining.

**Forgetting Default derive** — Non-consuming builders usually need `#[derive(Default)]` for `Builder::new()` or `Builder::default()`.

**Validation scattered across setters** — Prefer validating in `build()` to keep setters simple and predictable. Exception: early rejection of obviously invalid values.

## Pattern Comparison

| Aspect | Non-Consuming | Consuming | Typestate |
|--------|---------------|-----------|-----------|
| Setter signature | `&mut self -> &mut Self` | `self -> Self` | `self -> Builder<NewState>` |
| Build signature | `&self -> Result<T, E>` | `self -> T` or `Result<T, E>` | `self -> T` (only when valid) |
| Reusable | Yes | No | No |
| Loop-friendly | Yes | Awkward | Awkward |
| Non-Clone fields | Needs workarounds | Natural | Natural |
| Required field enforcement | Runtime | Runtime | Compile-time |
| Complexity | Low | Low | High |

**General guidance:**
- Start with non-consuming builder (most flexible)
- Switch to consuming if you have non-Clone fields
- Add typestate only if compile-time required-field checking is worth the complexity
