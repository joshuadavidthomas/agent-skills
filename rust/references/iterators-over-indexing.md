# Iterators Over Index Loops

## The Smell

C-style indexed loops when iterators would be clearer, safer, and often faster.

```rust
// WRONG
let mut sum = 0;
for i in 0..values.len() {
    sum += values[i];
}

// WRONG — index + manual bounds management
for i in 0..names.len() {
    if names[i].starts_with("A") {
        println!("{}: {}", i, names[i]);
    }
}
```

Index-based loops bypass Rust's iterator optimizations, introduce potential off-by-one errors, and obscure intent.

## The Idiomatic Alternative

```rust
// Direct iteration
let sum: i64 = values.iter().sum();

// With index when you need it
for (i, name) in names.iter().enumerate() {
    if name.starts_with("A") {
        println!("{}: {}", i, name);
    }
}

// Chained iterator adaptors
let result: Vec<String> = items
    .iter()
    .filter(|item| item.is_active)
    .map(|item| item.name.clone())
    .collect();
```

### Common replacements

```rust
// Finding an element
items.iter().find(|item| item.id == target)

// Checking a condition on all elements
items.iter().all(|item| item.valid)

// Transforming in place
for item in &mut items { item.value *= 2; }

// Windowed/sliding access
for window in items.windows(2) {
    process(&window[0], &window[1]);
}

// Parallel iteration over two collections
for (a, b) in a_items.iter().zip(b_items.iter()) {
    process(a, b);
}
```

## Why Iterators Are Often Faster

Rust's iterators aren't just syntactic sugar:

- **Bounds check elimination.** The compiler can prove iterator access is in bounds and remove the runtime check. `values[i]` requires a bounds check on every access unless the optimizer can prove safety.
- **Vectorization.** Iterator chains express data flow more clearly, making auto-vectorization more likely.
- **Fusion.** `.iter().map().filter().collect()` can compile into a single pass with no intermediate allocations.
- **Preallocation via `size_hint()`.** When you `.collect()`, the iterator's `size_hint()` tells the allocator how much space to reserve. This means one allocation instead of repeated growth.

## Pipeline Patterns

### Avoid intermediate `collect()` — keep the pipeline going

```rust
// WRONG — allocates a Vec just to iterate again
let tmp: Vec<u32> = items.iter().map(|x| x + 1).collect();
let sum: u32 = tmp.iter().map(|x| x * 2).sum();

// RIGHT — fuse the pipeline, zero intermediate allocation
let sum: u32 = items.iter().map(|x| x + 1).map(|x| x * 2).sum();
```

### Return `impl Iterator` instead of `Vec` when callers just iterate

```rust
// WRONG — forces allocation even if caller only needs to iterate
fn active_users(users: &[User]) -> Vec<&User> {
    users.iter().filter(|u| u.is_active).collect()
}

// RIGHT — caller decides whether to collect
fn active_users(users: &[User]) -> impl Iterator<Item = &User> {
    users.iter().filter(|u| u.is_active)
}
```

### Use `.copied()` for small `Copy` types

```rust
let ids: Vec<u64> = raw_ids.iter().copied().collect();
// Clearer intent than .cloned(), and signals the items are small/cheap.
```

## When Index Loops Are Appropriate

- **Simultaneous access to different indices.** Comparing/swapping elements at positions `i` and `j`:
  ```rust
  for i in 0..items.len() {
      for j in (i + 1)..items.len() {
          if items[i] > items[j] { items.swap(i, j); }
      }
  }
  ```
- **Algorithms that are naturally index-based.** Binary search, quicksort partitioning.
- **Performance-critical inner loops with known bounds.** Rare — profile before reaching for `get_unchecked`.

## Common Source Languages

- **C / C++** — indexed loops are the only primitive loop construct
- **Java** — `for (int i = 0; ...)` is muscle memory, even with enhanced for-each
- **Python** — `for i in range(len(items))` instead of `for item in items`
- **Go** — `for i := 0; i < len(items); i++` is standard
