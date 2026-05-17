# Allocation and Data Structure Wins

Most Rust performance work is not “make LLVM smarter”. It is “allocate less, copy less, pick the right container, stop doing O(n²) work”.

## Preallocate when you can estimate size

**Incorrect (growth reallocations):**

```rust
let xs = vec![1u32, 2, 3];

let mut out = Vec::new();
for x in xs.iter() {
    out.push(*x * 2);
}
```

**Correct (one allocation):**

```rust
let xs = vec![1u32, 2, 3];

let mut out = Vec::with_capacity(xs.len());
for x in xs.iter() {
    out.push(*x * 2);
}
```

Also consider `String::with_capacity` for hot string building.

**Authority:** Rust Performance Book “Heap Allocations” (Vec/String growth).

## Prefer `extend` over “collect then append”

If you only need to append transformed items, avoid allocating an intermediate `Vec`.

**Incorrect (extra allocation):**

```rust
let xs = vec![1u32, 2, 3];
let ys = vec![4u32, 5, 6];

let mut out = xs;
let mut tmp: Vec<u32> = ys.into_iter().map(|x| x * 2).collect();
out.append(&mut tmp);
```

**Correct (no intermediate Vec):**

```rust
let xs = vec![1u32, 2, 3];
let ys = vec![4u32, 5, 6];

let mut out = xs;
out.extend(ys.into_iter().map(|x| x * 2));
```

**Authority:** Rust Performance Book “Iterators” (`collect` and `extend`).

## Avoid hot `format!` when a buffer works

`format!` produces a new `String` (allocation). In hot paths, prefer writing into an existing buffer.

**Incorrect:**

```rust
let id = 123u64;
let s = format!("user:{id}");
```

**Correct:**

```rust
use std::fmt::Write;

let id = 123u64;
let mut s = String::with_capacity(32);
write!(&mut s, "user:{id}").unwrap();
```

Or avoid allocation entirely if a borrowed representation is acceptable.

**Authority:** Rust Performance Book “Heap Allocations” (`format!`).

## `clone_from` can reuse allocations

When overwriting an existing allocation (e.g. reusing a buffer), prefer `clone_from`.

```rust
let mut buf = String::with_capacity(1024);
let next = "small".to_owned();
buf.clone_from(&next); // reuses allocation when possible
```

**Authority:** Rust Performance Book “Heap Allocations” (`clone_from`).

## Use `HashMap::entry` and capacity

**Incorrect (double lookup):**

```rust
use std::collections::HashMap;

let mut m: HashMap<&str, usize> = HashMap::new();
let k = "key";

if !m.contains_key(k) {
    m.insert(k, 0);
}
*m.get_mut(k).unwrap() += 1;
```

**Correct (single lookup):**

```rust
use std::collections::HashMap;

let mut m: HashMap<&str, usize> = HashMap::new();
let k = "key";

*m.entry(k).or_insert(0) += 1;
```

Also: `HashMap::with_capacity(n)` when you can estimate size.

**Authority:** std `Entry` API; Rust Performance Book “Heap Allocations”.

## Faster hashers are a threat-model decision

If hashing is hot and HashDoS attacks are not a concern, switching to `rustc_hash`/`ahash` can produce real wins. Do not do this as a default in network-exposed code.

To enforce consistency, use Clippy’s `disallowed_types` in `clippy.toml`.

```toml
disallowed-types = ["std::collections::HashMap", "std::collections::HashSet"]
```

**Authority:** Rust Performance Book “Hashing” + “Linting”.

## Use asymptotically better ops in hot loops

- Use `Vec::swap_remove` instead of `Vec::remove` when order does not matter.
- Use `Vec::retain` for bulk deletion.
- Use `VecDeque` for queue semantics (push/pop at both ends).

**Authority:** Rust Performance Book “Standard Library Types”.
