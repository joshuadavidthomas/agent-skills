# Dispatch Patterns

Deep reference for choosing between static dispatch (generics), dynamic dispatch (trait objects), and enum dispatch. Use with [traits.md](../traits.md) when implementation details need more than the decision framework.

## Static Dispatch (Generics / `impl Trait`)

The compiler generates a specialized copy of the function for each concrete type used. This is called **monomorphization**.

### How monomorphization works

```rust
fn print_it<T: Display>(val: T) {
    println!("{}", val);
}

print_it(42_i32);
print_it("hello");
```

The compiler generates:

```rust
fn print_it_i32(val: i32) { println!("{}", val); }
fn print_it_str(val: &str) { println!("{}", val); }
```

**Advantages:**
- Zero runtime overhead — no vtable lookup, no indirection
- Enables inlining — the optimizer sees through the abstraction
- No heap allocation required

**Costs:**
- Binary size increases with each instantiation
- Compile time increases (more code to generate and optimize)
- Each instantiation is a separate function in the binary

### `impl Trait` in argument position

Syntactic sugar for a generic parameter. These are identical:

```rust
fn process(reader: impl Read) -> io::Result<Vec<u8>> { todo!() }
fn process<R: Read>(reader: R) -> io::Result<Vec<u8>> { todo!() }
```

Use `impl Trait` when you don't need to name the type parameter (e.g., for turbofish `::<R>` or to use it in multiple positions).

Use the named parameter when:
- The same type appears in multiple positions: `fn foo<T: Clone>(a: T, b: T)`
- You need to specify the type explicitly: `foo::<String>(...)`
- You need the type in a where clause with complex bounds

### `impl Trait` in return position

Returns an opaque type — the caller can't name it, but it's still a concrete single type resolved at compile time.

```rust
fn evens(v: &[i32]) -> impl Iterator<Item = &i32> {
    v.iter().filter(|&&x| x % 2 == 0)
}
```

**Limitations:**
- You can only return ONE concrete type. This does NOT compile:

```rust
fn make_iter(ascending: bool) -> impl Iterator<Item = i32> {
    if ascending {
        (0..10).into_iter()       // Type A
    } else {
        (0..10).rev().into_iter() // Type B — different type!
    }
    // ERROR: `if` and `else` have incompatible types
}
```

**Fix:** Use `Box<dyn Iterator<Item = i32>>` when you need to return different concrete types, or restructure to avoid the branch.

### Multiple trait bounds

```rust
// + syntax
fn process<T: Read + Write + Debug>(stream: T) { todo!() }

// where clause (cleaner for complex bounds)
fn process<T>(stream: T)
where
    T: Read + Write + Debug,
    T: Send + 'static,
{
    todo!()
}
```

Use `where` clauses when:
- Bounds are long or numerous
- Bounds involve relationships between type parameters
- The function signature would be unreadable with inline bounds

## Dynamic Dispatch (`dyn Trait`)

A trait object (`dyn Trait`) erases the concrete type. Method calls go through a vtable — a struct of function pointers generated for each concrete type.

### Memory layout

A trait object is a **fat pointer**: two machine words.

```
dyn Trait = (data_ptr, vtable_ptr)
```

- `data_ptr` — pointer to the concrete value
- `vtable_ptr` — pointer to a table of function pointers for this concrete type

The vtable contains:
- `drop` function
- `size` and `alignment`
- One function pointer per trait method

### Common forms

```rust
// Owned, heap-allocated
let x: Box<dyn Trait> = Box::new(concrete_value);

// Borrowed reference
fn process(x: &dyn Trait) { /* ... */ }

// Mutable reference
fn mutate(x: &mut dyn Trait) { /* ... */ }

// In collections
let items: Vec<Box<dyn Trait>> = vec![...];
```

### Trait object lifetimes

Trait objects have implicit lifetime bounds. The compiler adds `'static` by default in some positions:

```rust
// Box<dyn Trait> means Box<dyn Trait + 'static> in most contexts
fn store(item: Box<dyn Trait>) { /* ... */ }  // 'static implied

// Borrowed trait objects get the reference lifetime
fn process(item: &dyn Trait) { /* ... */ }    // lifetime of the reference

// Explicit lifetime when needed
fn process<'a>(item: &'a dyn Trait, data: &'a str) { /* ... */ }

// Struct holding a trait object needs explicit lifetime
struct Container<'a> {
    handler: Box<dyn Handler + 'a>,  // Must specify if not 'static
}
```

**Rule:** If a trait object lives in a struct or is stored, it's usually `Box<dyn Trait + Send + Sync + 'static>`. If it's a function parameter, let lifetime elision handle it.

### Multiple traits in a trait object

You can combine a trait with auto traits (`Send`, `Sync`, `Unpin`):

```rust
Box<dyn Handler + Send + Sync>
```

You **cannot** combine two regular traits:

```rust
// ❌ This does NOT work
Box<dyn Read + Write>
```

**Workaround:** Define a supertrait:

```rust
trait ReadWrite: Read + Write {}
impl<T: Read + Write> ReadWrite for T {}

Box<dyn ReadWrite>  // ✅ Works
```

## Enum Dispatch

For closed sets, enums outperform both generics (no code bloat) and trait objects (no vtable, no allocation).

```rust
enum Shape {
    Circle(f64),
    Rectangle(f64, f64),
    Triangle(f64, f64),
}

impl Shape {
    fn area(&self) -> f64 {
        match self {
            Shape::Circle(r) => std::f64::consts::PI * r * r,
            Shape::Rectangle(w, h) => w * h,
            Shape::Triangle(b, h) => 0.5 * b * h,
        }
    }
}
```

**Advantages over trait objects:**
- Stack-allocated (no `Box`)
- No vtable indirection
- Exhaustive matching — compiler catches missing variants
- Per-variant data without `Any` downcasting

**Disadvantage:** Adding a variant requires modifying every `match`. This is a *feature* for closed sets (compiler-enforced completeness) but a maintenance cost for semi-open sets.

### The `enum_dispatch` crate

If you have both a trait and an enum and want to avoid boilerplate `match` arms that just delegate:

```rust
use enum_dispatch::enum_dispatch;

#[enum_dispatch]
trait Area {
    fn area(&self) -> f64;
}

#[enum_dispatch(Area)]
enum Shape {
    Circle(Circle),
    Rectangle(Rectangle),
}
```

This generates the `match`-based `impl Area for Shape` automatically. Use it when you have many methods and many variants. Don't reach for it for small enums.

## Performance Comparison

| Aspect | Enum | Generic | `dyn Trait` |
|--------|------|---------|-------------|
| Method call cost | Direct (match branch) | Direct (monomorphized) | Indirect (vtable load + call) |
| Inlining | Yes | Yes | Rarely |
| Heap allocation | No | No | Usually (Box) |
| Binary size per variant/type | One match arm | Full function copy | One vtable entry |
| Cache behavior | Variant data inline | Good (specialized) | Pointer chase |
| Compile time impact | Minimal | Higher (monomorphization) | Minimal |

**When the difference matters:** Hot loops processing millions of items. In application glue code (config, setup, one-off decisions), the difference is negligible — optimize for clarity.

## Decision Examples

| Scenario | Choice | Why |
|----------|--------|-----|
| HTTP method (GET, POST, PUT...) | Enum | Closed set, known variants |
| Storage backend (disk, S3, memory) | Trait + generics | Open set, one backend per app instance |
| Middleware pipeline | `Vec<Box<dyn Middleware>>` | Heterogeneous, runtime-composed |
| AST node types | Enum | Closed set, per-variant data |
| Serialization format | Trait + generics | Open set, known at call site |
| Event handlers in GUI | `Vec<Box<dyn Handler>>` | User-defined, runtime-registered |
| Comparison strategy (sort) | Generic (`Fn`) | Closure, known at call site |
| Log output targets | Trait + generics (or `dyn`) | Open set, may need runtime selection |
