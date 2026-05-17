# Rust ↔ C++ with `cxx`: Prefer a Typed Bridge Over Raw C ABI

Use `cxx` when you have a C++ codebase and you want safer, higher-level interop than “flatten everything into `extern "C"`”. `cxx` is intentionally opinionated and restrictive so it can provide stronger guarantees than a raw ABI.

Authority: cxx book (dtolnay/cxx).

## 1) Default: use `cxx::bridge` as the boundary module

Put all Rust↔C++ signatures in one `#[cxx::bridge]` module. This module is your contract surface.

- `extern "Rust"` lists Rust types and functions that C++ may call.
- `extern "C++"` lists C++ types and functions that Rust may call, and `include!("...")` lists the header(s) that declare them.

```rust
#[cxx::bridge]
mod ffi {
    struct BlobMetadata {
        size: usize,
        tags: Vec<String>,
    }

    extern "Rust" {
        type MultiBuf;
        fn next_chunk(buf: &mut MultiBuf) -> &[u8];
    }

    unsafe extern "C++" {
        include!("demo/include/blobstore.h");

        type BlobstoreClient;
        fn new_blobstore_client() -> UniquePtr<BlobstoreClient>;
        fn put(&self, parts: &mut MultiBuf) -> u64;
        fn metadata(&self, blobid: u64) -> BlobMetadata;
    }
}
```

The bridge module should not contain business logic; it should be a translation layer.

## 2) Shared vs opaque types: pick intentionally

`cxx` distinguishes:

- Shared structs (fields visible to both sides) for simple POD-ish data.
- Opaque types (fields hidden) for complex state; pass them behind references or smart pointers.

Defaults:

- Prefer opaque types for anything with invariants, ownership, or internal pointers.
- Prefer shared structs for “records”: a snapshot of data to pass across the boundary.

## 3) Prefer `UniquePtr`/`SharedPtr` over raw pointers

Use the supported smart-pointer types (`UniquePtr<T>`, `SharedPtr<T>`, `Box<T>`) to make ownership explicit.

Avoid “naked” `*mut T` unless you are forced into it.

## 4) Fallibility: use `Result<T>` and understand the exception boundary

`Result<T>` is allowed as an extern return type in either direction; `cxx` translates it to/from C++ exceptions.

Key behaviors (cxx book: Result):

- If a C++ function throws an exception but is not declared as returning `Result`, the program calls `std::terminate`.
- If a Rust panic occurs in an `extern "Rust"` function, the program logs and aborts (don’t rely on “panic = exception”).

Defaults:

- Declare fallible extern functions as returning `Result<T>` in the bridge.
- On the Rust implementation side, any error type is allowed as long as it implements `Display` (cxx wraps it into a `rust::Error` on the C++ side).
- Do not let panics be part of your error story; treat them as bugs.

## 5) Keep types boring at the boundary

Only a limited set of types is supported across the bridge (see cxx book: built-in bindings). Do not try to smuggle generic Rust types or C++ templates across.

Defaults:

- Use `rust::String`/`rust::Str` (`String`/`&str` on Rust side) for text.
- Use slices / `Vec<T>` for owned buffers only where supported and where you can tolerate copying.
- For large data, design streaming APIs (iterative reads/writes) rather than “return a giant Vec”.

## 6) Build system: choose one owner of the boundary

`cxx` needs codegen and headers in sync. Decide where the source of truth lives and keep it in one place.

- If Rust owns the boundary, write the bridge signatures in Rust and include C++ declarations in headers.
- If C++ owns the boundary, consider generating Rust views via bindgen where it makes sense, but keep the high-level bridge contract stable.

If you end up with both bindgen and cxx and hand-written shims, stop and redesign the layering.
