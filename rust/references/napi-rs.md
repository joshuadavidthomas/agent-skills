# Node.js ↔ Rust with napi-rs (Node-API): Never Block the Event Loop

Use napi-rs when you are building a Node.js addon via Node-API / N-API. The host constraints are non-negotiable: JS runs an event loop, and your addon must not block it.

Authority: napi-rs crate README and examples; @napi-rs/cli docs.

## 1) Build shape: `cdylib` + `napi-build`

Defaults:

- Build the Rust crate as a `cdylib`.
- Add `napi-build` as a build dependency and call `napi_build::setup()` in `build.rs`.

```toml
[lib]
crate-type = ["cdylib"]

[dependencies]
napi = "3"
napi-derive = "3"

[build-dependencies]
napi-build = "1"
```

```rust
// build.rs
fn main() {
    napi_build::setup();
}
```

## 2) API shape: `#[napi]` surfaces only; keep Rust internals private

- Export functions and types using `#[napi]`.
- Treat the napi boundary as DTO translation: accept JS-friendly inputs, convert to typed Rust, run Rust logic, convert outputs.

## 3) Error mapping: return `Result<T>`; do not panic for recoverable errors

napi-rs expects fallible exports to return `Result<T>` (napi::Result). These map to JS exceptions / promise rejections.

Defaults:

- Return `Result<T>` everywhere errors can occur.
- Use meaningful status codes (`napi::Status`) when constructing errors.
- Treat panics as bugs; don’t use panic as a control-flow error.

## 4) Async is the default escape hatch (requires the `async` feature)

If an operation might block (file I/O, network I/O, CPU-heavy compute), it must not run synchronously on the JS thread.

Defaults:

- Prefer `#[napi] pub async fn ... -> Result<T>` and enable `napi = { ..., features = ["async"] }`.
- If you need to spawn work, do it within the async runtime and return a promise to JS.

Example shape (from napi-rs docs):

```rust
use napi::bindgen_prelude::*;
use napi_derive::napi;

#[napi]
pub async fn read_file_async(path: String) -> Result<Buffer> {
    Ok(tokio::fs::read(path).await?.into())
}
```

## 5) Bytes and buffers: prefer JS typed arrays / Buffer types

Avoid “stringify bytes” or JSON for bulk binary data.

Defaults:

- Use `Buffer` / `Uint8Array` for binary.
- For large transfers, design APIs that minimize copies and avoid repeated boundary crossings.

## 6) Callbacks across threads: use `ThreadsafeFunction`

If Rust needs to call back into JS from a non-JS thread, you must use the framework’s thread-safe callback mechanism. Do not call into JS directly from worker threads.

## 7) Packaging and distribution: use `@napi-rs/cli`

Use `@napi-rs/cli` to build and package `.node` artifacts reliably across platforms:

- `napi build --release` for local builds.
- Use `napi create-npm-dirs` / `napi pre-publish` for multi-platform npm packages when distributing binaries.

## 8) Quick audit questions

- Is any CPU-heavy work running in a sync `#[napi] fn` (bug: blocks event loop)?
- Are panics reachable from JS inputs (bug: process crash)?
- Are callbacks invoked from non-JS threads without a `ThreadsafeFunction` (bug: UB/crash)?
- Are byte payloads being moved via JSON/text (bug: slow + lossy) instead of typed arrays?
