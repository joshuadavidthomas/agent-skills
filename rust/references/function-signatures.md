# Function Signature Patterns

## Accept borrowed forms — the general rule

Every owned type has a borrowed counterpart that's more flexible. Accept the borrowed form unless you need ownership.

| Owned form | Borrowed form | Works with callers holding |
|-----------|--------------|----------------------------|
| `String` | `&str` | `String`, `&str`, string literals, `Cow<'_, str>`, `Box<str>`, `Rc<String>`, `Arc<String>` |
| `Vec<T>` | `&[T]` | `Vec<T>`, arrays (`[T; N]`), slices, `Box<[T]>` |
| `PathBuf` | `&Path` | `PathBuf`, `&Path`, `&str` (via `AsRef<Path>`) |
| `OsString` | `&OsStr` | `OsString`, `&OsStr`, `&str` (via `AsRef<OsStr>`) |
| `CString` | `&CStr` | `CString`, `&CStr` |

**Why this matters:** A function accepting `&str` works for callers holding `String`, `&str`, or string literals — zero allocation, zero conversion. A function accepting `&String` forces callers with `&str` to allocate a `String` first.

**Authority:** Rust API Guidelines [C-CALLER-CONTROL]. clippy: `ptr_arg`.

## `impl AsRef<T>` — generic borrows

When your function needs to work with multiple types that can provide a reference to `T`, use `AsRef<T>`:

```rust
use std::path::{Path, PathBuf};

fn read_config(path: impl AsRef<Path>) -> std::io::Result<String> {
    std::fs::read_to_string(path.as_ref())
}

fn main() -> std::io::Result<()> {
    let _ = read_config("config.toml")?;                // &str
    let _ = read_config(Path::new("config.toml"))?;     // &Path
    let _ = read_config(PathBuf::from("config.toml"))?; // PathBuf
    let _ = read_config(String::from("config.toml"))?;  // String
    Ok(())
}
```

Common `AsRef` bounds:
- `AsRef<Path>` — filesystem operations
- `AsRef<str>` — string operations
- `AsRef<[u8]>` — byte operations
- `AsRef<OsStr>` — OS string operations

**Don't use `AsRef` when a simple `&T` works.** If your function only ever gets one type, `&str` is simpler than `impl AsRef<str>`.

**Authority:** std: `fs::read_to_string(path: impl AsRef<Path>)`.

## `impl Into<T>` — flexible ownership transfer

When a function needs to **own** the value, `Into<T>` lets callers pass either the target type or anything convertible to it.

```rust
use std::path::PathBuf;

struct Config {
    name: String,
    path: PathBuf,
}

impl Config {
    fn new(name: impl Into<String>, path: impl Into<PathBuf>) -> Self {
        Self {
            name: name.into(),
            path: path.into(),
        }
    }
}

fn main() {
    let app_name = String::from("my-app");
    let config_path = PathBuf::from("/etc/my-app");

    let _c1 = Config::new("my-app", "/etc/my-app"); // &str → String, &str → PathBuf
    let _c2 = Config::new(app_name, config_path);     // String → String, PathBuf → PathBuf
}
```

**Use `Into<T>` when:**
- The function stores the value (struct fields, collections)
- Callers commonly have `&str` when you need `String`
- You want ergonomic constructors

**Don't use `Into<T>` when:**
- You only need to read the data — use `&str` / `&[T]` / `AsRef`
- The conversion could fail — use `TryInto<T>` or a `parse`/`new` method
- There's only one reasonable input type — just take that type directly

## `Cow<'a, T>` — conditional ownership

`Cow` (Clone on Write) borrows when possible, owns when necessary. Use it when a function sometimes returns a reference to its input and sometimes creates a new value.

```rust
use std::borrow::Cow;

fn escape_html(input: &str) -> Cow<'_, str> {
    if input.contains('&') || input.contains('<') || input.contains('>') {
        // Must allocate to hold the escaped version
        Cow::Owned(
            input
                .replace('&', "&amp;")
                .replace('<', "&lt;")
                .replace('>', "&gt;"),
        )
    } else {
        // No escaping needed — borrow the original
        Cow::Borrowed(input)
    }
}

fn main() {
    let output = escape_html("hello"); // Cow::Borrowed — zero alloc
    println!("{output}");

    let output = escape_html("a < b"); // Cow::Owned — one alloc
    println!("{output}");
}
```

### When to use Cow

Use it for "usually borrowed, sometimes owned" APIs: string processing that mostly passes through, normalization where most inputs are already normal, configs with borrowed defaults overridden by owned values, and zero-copy deserialization fast paths.

### When NOT to use Cow

If you always modify input, return `String`. If you never modify input, return `&str`. Otherwise, don't pay `Cow`'s complexity cost.

### Cow in structs

```rust
use std::borrow::Cow;

#[derive(Clone, Copy)]
enum LogLevel {
    Info,
}

struct LogEntry<'a> {
    message: Cow<'a, str>,
    level: LogLevel,
}

impl<'a> LogEntry<'a> {
    fn new(message: impl Into<Cow<'a, str>>, level: LogLevel) -> Self {
        Self {
            message: message.into(),
            level,
        }
    }

    fn into_owned(self) -> LogEntry<'static> {
        LogEntry {
            message: Cow::Owned(self.message.into_owned()),
            level: self.level,
        }
    }
}
```

## Conversion naming conventions

Function names signal ownership transfer. Follow std conventions:

| Prefix | Signature pattern | Cost | Examples |
|--------|------------------|------|---------|
| `as_` | `&self → &T` | Free | `str::as_bytes`, `Option::as_ref` |
| `to_` | `&self → T` | Expensive (allocates or computes) | `str::to_string`, `str::to_lowercase` |
| `into_` | `self → T` | Consumes, may be free | `String::into_bytes`, `Vec::into_boxed_slice` |

```rust
struct MyType {
    inner: String,
}

impl MyType {
    fn as_str(&self) -> &str { &self.inner }
    fn to_string(&self) -> String { self.inner.clone() }
    fn into_inner(self) -> String { self.inner }
}

fn main() {
    let t = MyType { inner: "hi".to_string() };
    let _s: &str = t.as_str();
}
```

**Authority:** Rust API Guidelines [C-CONV].

## Pattern: splitting borrows

When the borrow checker complains about borrowing two parts of the same struct, split the borrow by accessing fields directly:

```rust
struct Item {
    name: String,
}

struct State {
    items: Vec<Item>,
    log: Vec<String>,
}

impl State {
    fn log_processed(&mut self, name: &str) {
        self.log.push(format!("processed {name}"));
    }
}

// WRONG — holds an immutable borrow of `state.items` across the loop,
// then tries to borrow all of `state` mutably via `&mut self`.
fn process_wrong(state: &mut State) {
    for item in &state.items {
        state.log_processed(&item.name); // E0502
    }
}

// RIGHT — split the struct borrow; mutate only the field you need.
fn process_right(state: &mut State) {
    let State { items, log } = state;
    for item in items.iter() {
        log.push(format!("processed {}", &item.name));
    }
}
```

This works because the compiler can see that `items` and `log` don't overlap. Destructuring makes this visible.

## Pattern: bind temporaries to extend their lifetime

Temporaries live only for the statement that creates them (unless directly bound in a `let`). When you need the borrowed data to outlive the statement, bind the temporary to a variable first.

```rust
// WRONG — temporary String is dropped after push; vec holds a dangling borrow
let mut refs: Vec<&str> = Vec::new();
refs.push(&String::from("hello"));  // E0716: temporary value dropped while borrowed

// RIGHT — bind the temporary, borrow from the binding
let owned = String::from("hello");
let mut refs: Vec<&str> = Vec::new();
refs.push(&owned);  // owned lives as long as refs — no issue
```

The binding extends the value's lifetime to the enclosing scope.

**Authority:** Rust API Guidelines [C-CALLER-CONTROL], [C-CONV]. Effective Rust (borrowing and API ergonomics). The Rust Book ch 4.
