# Multi-language bindings with UniFFI: One Rust Core, Many Language Surfaces

UniFFI generates foreign-language bindings for Rust libraries. It is designed for “shared business logic” crates that need to be called from Swift/Kotlin/Python (and sometimes more via community bindings).

Authority: UniFFI manual (interface description, bindgen workflow, error modeling).

## 1) Model the exported API as a product surface

UniFFI forces you to describe the interface explicitly (UDL or proc macros). Treat that interface as the public API; keep it small, stable, and intentionally versioned.

Defaults:

- Keep a Rust “core” crate with domain logic.
- Keep the UniFFI-exported surface in a thin “api/bindings” module that translates to/from core types.

## 2) Describe the interface using proc macros or UDL (pick one)

### Proc macros

- Use `#[uniffi::export]` for exported functions/methods.
- Set up scaffolding with `uniffi::setup_scaffolding!()`.

Example (manual tutorial):

```rust
#[uniffi::export]
fn add(a: u32, b: u32) -> u32 { a + b }
```

### UDL

- Put a `*.udl` file in `src/` describing the exported functions/types.
- The `namespace` is mandatory and typically matches the crate.

Example (manual tutorial):

```idl
namespace math {
  u32 add(u32 a, u32 b);
};
```

If the UDL describes something that doesn’t exist in Rust, UniFFI fails with a hard error. Use that as a design constraint: the interface must be real and consistent.

## 3) Errors: use a dedicated exported error enum

Use `#[derive(uniffi::Error)]` on an enum and return `Result<T, E>` from exports (manual: Error derive). UniFFI maps errors into foreign exceptions.

Defaults:

- Use a domain error enum (not `String`).
- Decide whether fields are part of your cross-language contract; if not, use `#[uniffi(flat_error)]`.

## 4) Binding generation: prefer `generate --library`

The manual recommends generating bindings from a built library artifact via `uniffi-bindgen generate --library ...` because it is more convenient and some features don’t work otherwise.

Typical shape (manual tutorial):

- `cargo build --release`
- `cargo run --bin uniffi-bindgen generate --library target/release/libyourlib.so --language kotlin --out-dir out`

In a workspace, prefer a dedicated `uniffi-bindgen` crate/bin for repeatable generation.

## 5) Threading and runtime assumptions

Foreign languages have their own concurrency rules; UniFFI generates a bridge, not a permission slip to ignore them.

Defaults:

- Keep exported functions side-effect-free where possible.
- If you expose long-running work, surface it as async/future constructs supported by UniFFI (see manual: futures) and document cancellation semantics.

## 6) Quick audit questions

- Is the exported interface a thin translation layer, or is core domain logic leaking into the boundary types?
- Are errors modeled as enums (stable cross-language surface) instead of ad-hoc strings?
- Is binding generation reproducible (workspace bin + `generate --library`) and checked into the foreign-language build pipeline?
