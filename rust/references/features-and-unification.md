# Features and Unification (Cargo)

Cargo features are a conditional compilation mechanism with one defining property: when a crate appears multiple times in the dependency graph, it is built once with the **union** of all requested features (Cargo Book: Features → Feature unification). This is why features must be additive.

## Hard rules

### 1) Assume `default-features = false` can be overridden

If any other edge in the graph enables defaults, defaults are on.

Action: when debugging, do not stare at `Cargo.toml`; inspect the resolved graph.

```bash
cargo tree -e features -i yourdep
```

### 2) Features must be additive

A feature may enable additional code paths, but it must not disable existing behavior in a way that breaks other users who didn’t ask for the feature.

Authority: Cargo Book (Feature unification); Effective Rust Item 26.

### 3) Avoid mutually exclusive features

If you cannot make the crate support both simultaneously, prefer separate crates. If you must keep one crate, enforce exclusivity:

```rust
#[cfg(all(feature = "backend-a", feature = "backend-b"))]
compile_error!("backend-a and backend-b cannot be enabled together");
```

Cargo Book calls mutually exclusive features “rare cases” and recommends alternative designs (split crates, choose precedence, runtime selection).

### 4) Never feature-gate public struct fields or public trait methods

This creates downstream compilation ambiguity: downstream code cannot reliably know which fields/methods exist because feature unification can enable them “from elsewhere”.

Authority: Effective Rust Item 26.

Prefer:
- Feature-gating **impls** (e.g. `impl serde::Serialize for T`) instead of the type definition.
- Feature-gating a private module and re-exporting a stable public facade.

## Workspace anti-pattern: “internal separation” features

Symptom: a workspace crate does this to “separate concerns”:

```toml
# crates/core/Cargo.toml
[features]
parser = ["dep:ruff_python_parser"]

[dependencies]
ruff_python_parser = { version = "...", optional = true }
ruff_python_ast = "..." # heavy dep, always on
```

Problems:
- The gate is on the wrong dependency (the heavy dep is unconditional).
- In a workspace, if any crate enables `core/parser`, Cargo builds `core` with `parser` enabled everywhere it appears anyway.

Fix:
- If you need optional compilation for consumers, keep features but gate the heavy dependency.
- If you need internal separation, move the parser into its own crate (`crates/parser/`) and make the dependency boundary real.

## Resolver versions (why `resolver = "2"` / `"3"` matters)

The resolver is a workspace-global setting (Cargo Book: Resolver versions). A dependency’s own `resolver` key is ignored; only the workspace root matters.

- `resolver = "2"` is the resolver Cargo infers for a workspace with a root package on edition 2021 (changes some feature-unification behavior for dev-deps/build-deps/targets).
- `resolver = "3"` is the resolver Cargo infers for a workspace with a root package on edition 2024.
- In a virtual workspace (no root `[package]`), you must set `resolver` explicitly; member package editions do not affect it.

Rule: set the resolver explicitly in the workspace root so behavior doesn’t depend on where you run cargo.

## Debugging playbook

### “Who enabled this feature?”

```bash
cargo tree -e features -i somecrate
```

### Compact view (which features per package)

```bash
cargo tree -f "{p} {f}" -e features
```

### “Why is this dependency present?”

```bash
cargo tree -i depname
```

### “Why do I have two versions of the same crate?”

```bash
cargo tree -d
```

Then align version requirements (workspace deps), or use `[patch]`/`[replace]` at the workspace root only (Cargo Book: Workspaces).

## Testing feature sets

Feature combinations blow up exponentially. Don’t pretend you’ll test all `2^N` combos; do the minimum that catches most breakage:
- `cargo test` (defaults)
- `cargo test --all-features`
- `cargo test --no-default-features` (if your crate supports it)

For published libraries with meaningful optional features, add CI coverage for “feature families” (e.g. each backend separately) rather than enumerating all combinations.
