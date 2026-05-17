# Python ↔ Rust with PyO3: Bind a Pythonic API, Run Rust Inside

PyO3 provides a safe(ish) boundary for Python integration, but the boundary still has rules: interpreter attachment, object lifetimes, and the host runtime’s concurrency model.

Authority: PyO3 guide (conversions, parallelism, building & distribution).

## 1) Choose the integration mode first

- Python extension module (most common): Rust builds a shared library that Python imports.
- Rust binary embedding Python: Rust hosts the interpreter.

Do not mix assumptions between the two; the build/link story differs (PyO3 guide: Building and distribution).

## 2) API shape: expose Python-friendly surfaces, not your Rust module tree

Defaults:

- Export a small set of `#[pyfunction]` and `#[pyclass]` surfaces.
- Keep Rust domain types internal; translate at the boundary.
- Use Python exceptions for “programmer errors” and structured exceptions for domain errors.

## 3) Lifetimes and object ownership: never store borrowed Python references

- Anything tied to `Python<'py>` / `Bound<'py, T>` is a borrow scoped to an attached interpreter token.
- If you need to store a Python object beyond the call, store an owned `Py<T>` (or `Py<PyAny>`), not `&PyAny`.

This is the boundary version of [ownership.md](../ownership.md): “borrow is scoped; retained state must be owned”.

## 4) Conversions: prefer Rust std types unless profiling proves otherwise

PyO3 supports converting many Python types directly into Rust standard types (PyO3 guide: conversions tables). Defaults for `#[pyfunction]` signatures:

- Accept `String`/`PathBuf`/`Vec<T>`/`HashMap<K, V>` when you want typed Rust logic and you can pay conversion cost once.
- Accept Python-native types (`&PyList`, `&PyDict`, `Bound<'py, PyString>`, etc.) only when you need to avoid conversion cost and you will stay “Pythonic” (iterating Python objects, calling Python methods).

The moment you accept Python-native types, you have moved work back onto the Python runtime; do it intentionally.

## 5) Release the interpreter lock / thread-state for long-running Rust work

Do not hold the interpreter hostage while you do CPU-bound Rust work.

- Use `Python::detach(|| ...)` to temporarily detach from the interpreter while executing Rust code so other Python threads can run (PyO3 guide: Parallelism).
- If your detached code spawns threads (rayon, std::thread), detaching is mandatory to avoid deadlocks where the caller thread waits while holding the interpreter state.

Rule of thumb: if the code inside the closure does not touch Python objects, it should run detached.

## 6) Errors: return `PyResult<T>` / `Result<T, E>` and map to exceptions intentionally

Defaults:

- Use `PyResult<T>` or `Result<T, E>` where `E: Into<PyErr>`.
- Translate domain errors into specific exception types, not `RuntimeError("...")` everywhere.
- Do not panic for recoverable errors; panics should be bugs.

## 7) Packaging: prefer maturin; understand `abi3`

Defaults for extension modules:

- Use maturin unless you have a strong reason not to (PyO3 guide: Packaging tools).
- Build as `cdylib` and let maturin handle naming/wheel layout.
- If you need one wheel to support multiple Python versions, use PyO3’s `abi3` features and choose the minimum Python version you support (PyO3 guide: `Py_LIMITED_API`/`abi3`).

## 8) Quick audit questions

- Are any `&PyAny` / `Bound<'py, PyAny>` values being stored in structs (bug: lifetime escape)?
- Is CPU work running while attached (bug: blocks Python threads)?
- Are Rust errors being turned into the right exception classes (bug: impossible to catch correctly)?
- Is the packaging story reproducible (maturin/wheels; not “it works on my machine”)?
