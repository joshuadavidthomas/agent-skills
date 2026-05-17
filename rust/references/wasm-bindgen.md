# JS ↔ Rust via WebAssembly with wasm-bindgen: Minimize Crossings, Own the Types

WASM interop is not “FFI with pointers”, it’s a structured ABI with generated glue. Performance and correctness come from choosing boundary types that avoid repeated boundary crossings and unnecessary copies.

Authority: wasm-bindgen guide; Rust and WebAssembly book (rustwasm/book).

## 1) Choose wasm-bindgen (not raw imports) for JS integration

Defaults:

- Use `#[wasm_bindgen]` for exported/imported functions and types.
- Use `js-sys` and `web-sys` for standard JS/Web APIs rather than hand-writing bindings.

## 2) Prefer a small, DTO-style boundary

- Export a small set of functions/types.
- Convert `JsValue` into typed Rust structures at the edge (often via serde) and do real work in Rust.
- Avoid lots of tiny calls across the boundary; boundary crossings have overhead.

## 3) Type mapping: avoid `JsValue` in your “real” code

Defaults:

- Use Rust primitives and wasm-bindgen-supported types for “simple” APIs.
- If the shape is complex, use serde at the boundary instead of building a large `JsValue` object graph manually.

wasm-bindgen recommendation for complex data: `serde-wasm-bindgen` (wasm-bindgen guide: arbitrary data with serde).

## 4) Async: map `Promise` ↔ `Future` intentionally

Use `wasm-bindgen-futures` to bridge:

- Convert a JS `Promise` into a Rust `Future` via `JsFuture`.
- Export `async fn` from Rust; it becomes a JS `Promise`.

From the wasm-bindgen guide (Promises and Futures):

```rust
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;

async fn get_from_js() -> Result<JsValue, JsValue> {
    let promise = js_sys::Promise::resolve(&42.into());
    let result = JsFuture::from(promise).await?;
    Ok(result)
}

#[wasm_bindgen]
pub async fn foo() -> Result<JsValue, JsValue> {
    get_from_js().await
}
```

Defaults:

- Return `Result<T, JsValue>` from exported async functions so rejections carry structured information.
- Do not block; if you need CPU-heavy work, break it up or move it off the main thread via web workers (host-level concern).

## 5) Bytes and bulk data: use typed arrays, not JSON

For large binary payloads:

- Prefer `Uint8Array` / `ArrayBuffer` patterns.
- Minimize copying; design APIs that operate in fewer, larger calls.

If you serialize, do it intentionally (and measure): JSON can be faster than “lots of JS object manipulation” but increases code size and may lose fidelity.

## 6) Deployment: pick the right `wasm-bindgen` target

The generated JS glue differs by deployment target (wasm-bindgen guide: Deploying):

- `--target bundler` (default) for webpack/vite/etc.
- `--target web` for direct browser ES module loading (no npm deps).
- `--target nodejs` or node ESM targets for server-side WASM.

If you can’t explain why you chose the target, you haven’t finished the packaging story.

## 7) Panics and errors: decide policy

Defaults:

- Treat panics as bugs.
- Convert recoverable errors into `Result` and surface them as thrown exceptions / rejected promises (depending on how you expose the API).
- If you need a panic hook for better errors, add it explicitly in initialization code (host-facing choice).
