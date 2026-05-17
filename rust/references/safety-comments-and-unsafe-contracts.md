# Safety Comments and Unsafe Contracts

Unsafe code must be auditable. The only scalable way to audit it is to require explicit contracts (`# Safety`) and local justifications (`// SAFETY:`) everywhere.

Authorities: Rust stdlib conventions; clippy lints `undocumented_unsafe_blocks` and `missing_safety_doc`.

## 1) `# Safety` in rustdoc is the caller contract

Write `# Safety` for any `pub unsafe fn`, `pub unsafe trait`, and any function where safety depends on undocumented preconditions.

Bad (vague, untestable):

```rust
/// # Safety
/// The caller must ensure this is safe.
pub unsafe fn read(ptr: *const u8) -> u8 {
    ptr.read()
}
```

Good (states concrete obligations and scope):

```rust
/// Reads one byte from `ptr`.
///
/// # Safety
///
/// The caller must ensure all of the following:
/// - `ptr` is non-null and properly aligned for `u8` (alignment 1, so alignment is trivially satisfied here).
/// - `ptr` points to a live allocation that is valid for reads of 1 byte for the duration of this call.
/// - No data race occurs: if other threads access the same memory, those accesses must be synchronized.
pub unsafe fn read_byte(ptr: *const u8) -> u8 {
    // SAFETY: caller contract.
    unsafe { ptr.read() }
}
```

Rules:

- State obligations as a checklist the caller can actually satisfy.
- Use “must” language; avoid “should”.
- Include concurrency assumptions (`Send`/`Sync`, data races) when relevant.
- If the function creates references from raw pointers, include aliasing and initialization requirements explicitly.

## 2) `// SAFETY:` explains why a specific unsafe block is sound

The `# Safety` section describes what the caller must provide. The `// SAFETY:` comment explains what this function has established at this point and why the unsafe operation is permitted.

Bad (restates code):

```rust
unsafe {
    // SAFETY: write the value.
    ptr.write(value);
}
```

Good (mentions invariants and why they hold):

```rust
// SAFETY: `ptr` was obtained from `Vec::as_mut_ptr()` and `index < len`, so it is in-bounds, properly aligned, and points to initialized memory.
unsafe { ptr.add(index).write(value) }
```

Rules:

- Place the `// SAFETY:` comment immediately above the unsafe block/operation.
- Reference the exact invariant you rely on (in-bounds, aligned, initialized, unique access, correct provenance/layout).
- If the invariant is established by a preceding check, point at it (“we just checked `index < len`”).

## 3) One unsafe block per invariant

If a function performs multiple unsafe operations with different justifications, split them into separate unsafe blocks, each with its own `// SAFETY:` comment. Do not hide multiple obligations inside one `unsafe { ... }`.

## 4) Prefer `unsafe_op_in_unsafe_fn`

Enable `unsafe_op_in_unsafe_fn` so that unsafe operations inside `unsafe fn` still require `unsafe { ... }`. This keeps “where are the proof obligations?” mechanically searchable.

Pattern:

```rust
pub unsafe fn f(p: *mut T) {
    // SAFETY: ...
    unsafe { p.write_bytes(0, 1) }
}
```

## 5) Unsafe traits and `Send`/`Sync`

If you define an `unsafe trait`, the `# Safety` section must describe what implementors must uphold. If you write `unsafe impl Send/Sync for X`, document the concurrency invariant.

Bad:

```rust
unsafe impl Send for MyType {}
```

Good:

```rust
// SAFETY: `MyType` only contains an owning `NonNull<T>` and does not permit aliasing mutable access across threads; all internal mutation is synchronized.
unsafe impl Send for MyType {}
```

If you cannot state the invariant in one or two sentences, you do not understand it well enough to ship it.

## 6) Lint configuration

In crates with unsafe code, enable lints so reviewers don’t have to enforce policy manually.

Cargo workspace lints (example):

```toml
[workspace.lints.rust]
unsafe_op_in_unsafe_fn = "deny"

[workspace.lints.clippy]
undocumented_unsafe_blocks = "deny"
missing_safety_doc = "deny"
unnecessary_safety_doc = "warn"
```

Use crate-level inheritance (`[lints] workspace = true`) to keep the rules consistent.
