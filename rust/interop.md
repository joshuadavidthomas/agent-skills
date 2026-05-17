# Cross-Language Integration: Make the Boundary Explicit

Interop is where Rust’s guarantees stop. The other side does not share Rust’s aliasing model, lifetimes, or panic semantics, so your job is to design a boundary that is (1) small, (2) explicit about ownership, (3) explicit about type mapping, and (4) resilient to foreign misuse.

Authority: Rustonomicon (FFI); Rust Reference (ABI, unwinding, UB); Cargo Book (cdylib); PyO3 guide; napi-rs docs; wasm-bindgen guide; cxx book; UniFFI manual.

## Entry Question: What are you bridging to?

Pick the target first; then use the right tool. Do not reach for raw `extern "C"` unless you actually need a C ABI.

| Target | Preferred tool | Read this reference |
|---|---|---|
| C ABI (C, Zig, many other languages via C) | raw `extern "C"` + `#[no_mangle]` + cbindgen/bindgen | [references/c-ffi.md](references/c-ffi.md) |
| C++ (modern C++ codebase, want higher-level safe bindings) | `cxx` (`cxx::bridge`, `UniquePtr`, `CxxString`) | [references/cxx.md](references/cxx.md) |
| Python extension module or embedding Python | PyO3 (+ maturin/setuptools-rust) | [references/pyo3.md](references/pyo3.md) |
| Node.js native addon (N-API / Node-API) | napi-rs (`#[napi]`, generated .d.ts) | [references/napi-rs.md](references/napi-rs.md) |
| WebAssembly (browser / JS host) | wasm-bindgen (+ wasm-bindgen-futures, web-sys/js-sys) | [references/wasm-bindgen.md](references/wasm-bindgen.md) |
| Swift/Kotlin/Python multi-language bindings from one Rust library | UniFFI (UDL or proc-macro interface) | [references/uniffi.md](references/uniffi.md) |

## Universal Rules (apply to every interop boundary)

### 1) Treat the boundary as a protocol, not as “calling Rust from X”

Do this up front, in writing:

- Define the boundary types (DTOs) separately from your internal domain types.
- Define ownership (who allocates, who frees, which allocator, which thread is allowed to free).
- Define lifetime rules (“call-scoped borrow” vs “retained handle”).
- Define error mapping (exception vs error code vs tagged union).

Then implement the boundary as a thin translation layer.

This is the same principle as [type-design.md](type-design.md) (“parse, don’t validate”) applied to foreign inputs: convert at the edge, operate on typed Rust inside.

### 2) Keep the ABI surface small and boring

- Put all boundary code in one module/crate (`ffi`, `bindings`, `py`, `napi`, `wasm`).
- Expose a stable, minimal set of functions/types; do not leak internal module paths, generic types, or lifetime-heavy APIs.
- Prefer “handle + methods” over “expose my whole Rust struct graph”. In C ABI terms: opaque pointer with constructor/destructor and methods.

### 3) Never let a panic unwind across the boundary

Defaults:

- For C ABI: unwinding across `extern "C"` is UB unless you intentionally use unwind-capable ABIs and both sides agree (Rust Reference). Prefer `catch_unwind` and convert to an error.
- For Python/JS/WASM: convert Rust errors to the host’s error mechanism (exceptions / rejected promises) and keep panics as process-fatal bugs unless you have an explicit policy.

If you need a panic policy, make it explicit at the boundary (e.g. abort; log and error; catch and translate). Don’t “accidentally” let it happen.

### 4) Make ownership and mutability explicit in the API shape

- Foreign code does not understand Rust borrowing. Do not expose borrowed references across calls unless the framework enforces lifetimes (PyO3’s `Python<'py>` token; cxx references) and the borrow is call-scoped.
- Prefer owned, self-contained boundary values (bytes + len, owned strings, owned structs) unless copying is provably too expensive.
- If you expose a pointer/handle that is retained, the API must include an explicit destructor/free function or a framework-managed handle type.

### 5) Map errors into domain facts, not strings

Even across languages, keep structured errors.

- C ABI: return an error code + an optional “last error” getter, or return a tagged struct `{ code, message_ptr }` with a matching free function.
- Python: return `PyResult<T>` / `Result<T, E>` where `E: Into<PyErr>`; map domain errors to the right Python exception types.
- JS: return `Result<T, napi::Error>` or `Result<T, JsValue>` depending on framework; rejected promises must carry actionable information.

This is [error-handling.md](error-handling.md) applied across a boundary: the “shape” of errors is part of the API.

### 6) Concurrency rules are owned by the host runtime

- Python: the GIL exists; do not block the interpreter thread; release the GIL for long-running Rust work via PyO3’s APIs.
- Node.js: do not block the JS event loop thread; use async or background tasks; be explicit about thread-safe callbacks.
- WebAssembly: assume a single-threaded host unless you intentionally opt into wasm threads + shared memory; design APIs that don’t require cross-thread Send/Sync unless you can enforce it.

### 7) Build artifacts and packaging are part of the API contract

- Decide whether you ship a `cdylib`, a `staticlib`, or a `bin` that embeds the runtime.
- Version your boundary as a product surface (semver for the Rust crate, and an explicit compatibility story for the foreign packaging format: wheels, npm packages, wasm bundles).
- Test the packaged artifact, not just `cargo test`.

## Common Mistakes (agent failure modes)

- Exposing `String`/`Vec<T>`/`Result<T, E>` directly in a C ABI and hoping it works.
- Returning pointers with no free function (leaks) or freeing on the wrong side (UB).
- Using “boolean flags” in boundary APIs instead of an enum/tagged config object (hard to evolve without breaking callers).
- Letting panics/unwinding cross the boundary.
- Doing “validation” at every layer instead of converting once at the boundary into typed domain values.
- Blocking the host runtime thread (Python GIL, Node event loop, browser main thread) and then blaming Rust.

## Cross-References

- [unsafe.md](unsafe.md) — unsafe blocks, UB triggers, pointer validity, `// SAFETY:` discipline
- [ownership.md](ownership.md) — correct ownership signatures before you design an interop API
- [type-design.md](type-design.md) — DTOs vs internal domain types; newtypes for IDs/handles
- [error-handling.md](error-handling.md) — structured error types and boundary translation
- [async.md](async.md) — async runtimes, blocking avoidance, cancellation
- [serde.md](serde.md) (when added) — serialization as a boundary strategy (JSON vs native bridging)

## Review Checklist

1. Is the target/runtime chosen first (PyO3 vs napi-rs vs wasm-bindgen vs cxx vs raw C ABI), instead of defaulting to raw `extern "C"`?
2. Is the interop surface small and contained in a dedicated module/crate (no boundary logic leaking through the codebase)?
3. Is ownership explicit for every retained value (who allocates, who frees, which allocator, which thread)?
4. Are boundary types separate from internal domain types (convert once at the edge; typed Rust inside)?
5. Are there any panics/unwinding paths that can cross the boundary (fixed via policy + `catch_unwind` where needed)?
6. Are errors structured and mapped into the host’s error mechanism (not `String`ly-typed)?
7. Are runtime constraints respected (GIL/event loop/browser thread); is blocking moved off the host thread?
8. Is the build/packaging story correct (`cdylib`/wheels/npm/wasm bundle) and tested as an artifact?
9. Are boundary invariants documented where callers will see them (headers, docstrings, generated .d.ts, UDL docs)?
10. Is unsafe code constrained to the smallest possible boundary layer, with precise `// SAFETY:` comments and tests?
