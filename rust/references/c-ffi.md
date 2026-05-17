# C ABI FFI (extern "C"): Build a Small, Explicit Contract

C ABI FFI is where Rust’s type system and aliasing rules stop. Treat the boundary as hostile: foreign code can pass null, lie about lengths, call on the wrong thread, and free with the wrong allocator.

Authorities: Rustonomicon (FFI chapter); Rust Reference (ABI, unwinding across FFI, UB); Cargo Book (crate types); bindgen and cbindgen docs.

## 1) Rule zero: decide who owns memory (and write it down)

Before you write any `extern "C"` signature, answer all of these for every pointer/string/buffer:

- Who allocates it?
- Who frees it?
- With which allocator?
- Is it a call-scoped borrow, or is the pointer retained after the call?
- Which thread may free it?

If you cannot answer these precisely, stop and redesign the API.

## 2) Do not expose Rust types in a C ABI

Do not put these in `extern "C"` signatures:

- `String`, `&str`
- `Vec<T>`, slices, or `&[T]` (unless you model as `(ptr, len)` explicitly)
- `bool` (Rust Reference: `bool` has a validity invariant; foreign code can violate it by passing non-0/1 values)
- `Result<T, E>`, `Option<T>`
- Rust enums (layout is not stable unless you intentionally design a `#[repr(C)]` representation, and even then you must be conservative)

Prefer C-stable primitives and explicit layouts:

- `core::ffi::{c_char, c_int, c_void, ...}`
- `*const T` / `*mut T` where `T` is `#[repr(C)]` or opaque
- `(ptr, len)` pairs for buffers
- integer error codes (and/or an out-param for richer error information)

Pattern: explicit buffer contract

```rust
use core::ffi::c_uchar;
use core::slice;

#[no_mangle]
pub extern "C" fn sum_bytes(ptr: *const c_uchar, len: usize) -> u64 {
    if ptr.is_null() {
        return 0;
    }

    // SAFETY: caller provided a non-null pointer to `len` readable bytes.
    let bytes = unsafe { slice::from_raw_parts(ptr, len) };
    bytes.iter().map(|b| *b as u64).sum()
}
```

## 3) Treat null pointers as a real input case

Foreign callers can pass null. Handle it explicitly at the boundary:

- Return an error code / sentinel
- Or accept `*const T` / `*mut T` and check before use
- Only convert to `&T` / `&mut T` after you have proven non-null + alignment + validity

Never do this:

```rust
// WRONG: UB if ptr is null or misaligned.
let x: &T = unsafe { &*ptr };
```

## 4) Strings: use CStr/CString; define encoding

- Use `CStr` for borrowed C string inputs.
- Use `CString` for owned outputs.
- Define the encoding (almost always UTF-8) and validate at the boundary.

```rust
use core::ffi::{c_char, CStr};

#[no_mangle]
pub extern "C" fn name_len(name: *const c_char) -> usize {
    if name.is_null() {
        return 0;
    }

    // SAFETY: `name` is non-null and points to a NUL-terminated string.
    let cstr = unsafe { CStr::from_ptr(name) };

    match cstr.to_str() {
        Ok(s) => s.len(),
        Err(_) => 0,
    }
}
```

If you return a pointer that Rust allocated, also provide a `*_free` function that deallocates using Rust’s allocator.

## 5) Panics and unwinding: do not let them cross the boundary

Unwinding across an FFI boundary is undefined behavior unless you intentionally use unwind-capable ABIs and both sides agree (Rust Reference).

Defaults:

- Treat panics as bugs.
- Wrap exported functions that might panic in `catch_unwind` and convert to an error code.
- If you need an unwind-capable ABI, use it intentionally (e.g. `extern "C-unwind"`) and document it.

## 6) Layout rules: `#[repr(C)]` is necessary, not sufficient

- Use `#[repr(C)]` for any struct passed by value or where C will interpret fields.
- Keep FFI structs simple: integers, floats, pointers, and other `#[repr(C)]` structs.
- Prefer `#[repr(transparent)]` for newtypes that must be ABI-compatible with their inner type.
- Avoid Rust enums in the ABI. If you need a sum type, design a tagged representation you control (tag + payload), or expose constructor/accessor functions instead.
- Treat `#[repr(packed)]` as “no references”: do not take `&field`; use raw pointers + `read_unaligned` / `write_unaligned`.

## 7) Prefer opaque handles for complex state

If the other side needs to “hold onto something”, expose an opaque handle type and provide explicit lifecycle functions.

```rust
use core::ffi::c_void;

struct MyState;

impl MyState {
    fn new() -> Self {
        Self
    }
}

#[repr(transparent)]
pub struct MyHandle(*mut c_void);

#[no_mangle]
pub extern "C" fn my_new() -> MyHandle {
    let boxed = Box::new(MyState::new());
    MyHandle(Box::into_raw(boxed).cast())
}

#[no_mangle]
pub extern "C" fn my_free(h: MyHandle) {
    if h.0.is_null() {
        return;
    }

    // SAFETY: `h` came from `my_new` and has not been freed yet.
    unsafe { drop(Box::from_raw(h.0.cast::<MyState>())) };
}
```

Do not export raw `*mut MyState` directly as your public surface; wrap it in a distinct handle newtype so it can’t be accidentally mixed with other pointers.

## 8) Callbacks: use (function pointer, context pointer)

C callbacks almost always need a user-data pointer.

- Take `extern "C" fn(*mut c_void, ...)` + `*mut c_void` context.
- Store the context pointer opaquely and treat it as borrowed or owned according to your contract.
- If Rust will call back into foreign code, specify threading rules: which thread the callback will run on, and whether reentrancy is allowed.

## 9) bindgen and cbindgen: generate, don’t hand-maintain

- Use bindgen when consuming a C header. Treat generated bindings as generated artifacts: don’t hand-edit; prefer allowlists/blocklists so you don’t bind the world.
- Use cbindgen when producing a C header for your Rust API. Keep the ABI surface intentionally small and versioned; document ownership and threading in header comments.

## 10) Contain unsafe in the boundary module

The `extern` surface is where validation and `unsafe` live. Convert foreign inputs into safe internal Rust types at the boundary; beyond that, the code should be safe Rust.

If you’re writing lots of unsafe outside the boundary, route the work through [unsafe.md](../unsafe.md) and treat it as a soundness audit problem.
