# Modules Are Namespaces, Not `impl` Blocks

## The Smell

Putting loosely related utility functions as associated functions on a unit struct, using the struct as a namespace.

```rust
// WRONG — struct as a namespace bag
struct StringUtils;

impl StringUtils {
    fn capitalize(s: &str) -> String { todo!() }
    fn truncate(s: &str, max_len: usize) -> String { todo!() }
    fn is_palindrome(s: &str) -> bool { todo!() }
}

let result = StringUtils::capitalize("hello");
```

`StringUtils` has no fields, no state, and you never instantiate it. It exists only as a namespace — that's what modules are for.

## The Idiomatic Alternative

### Module as namespace

```rust
mod string_utils {
    pub fn capitalize(s: &str) -> String { todo!() }
    pub fn truncate(s: &str, max_len: usize) -> String { todo!() }
    pub fn is_palindrome(s: &str) -> bool { todo!() }
}

use string_utils::capitalize;
let result = capitalize("hello");
```

### Extension traits for method syntax on existing types

If you want method-call syntax (`"hello".capitalize()`):

```rust
pub trait StringExt {
    fn capitalize(&self) -> String;
    fn is_palindrome(&self) -> bool;
}

impl StringExt for str {
    fn capitalize(&self) -> String { todo!() }
    fn is_palindrome(&self) -> bool { todo!() }
}

use crate::StringExt;
"hello".capitalize();
```

## When Associated Functions Belong on a Struct

Associated functions are right when they're genuinely related to that struct:

```rust
impl Config {
    pub fn new() -> Self { todo!() }
    pub fn from_file(path: &Path) -> Result<Self, ConfigError> { todo!() }
    pub fn for_testing() -> Self { todo!() }
}
```

**Rule of thumb:** If removing the struct would make the function signature worse (you'd have to pass it as a parameter), it belongs in the impl block. If the function doesn't mention `Self` at all, it belongs in a module.

## Common Source Languages

- **Java** — everything must live in a class; static methods are the only option for free functions
- **C#** — same as Java; static classes serve as namespace substitutes
- **TypeScript** — classes with static methods as utility containers
- **Python** — classmethods and staticmethods on otherwise empty classes
