# Project Structure, Workspaces, and API Surfaces

Use Rust ecosystem defaults that keep the codebase buildable, reviewable, and semver-stable as it grows. This is not about syntax; it is about boundaries: crates, modules, features, visibility, and documentation.

Authority: Cargo Book (workspaces, features, resolver); Edition Guide (editions); Rust API Guidelines; Effective Rust (Items 22, 23, 26, 27).

## First Question: One Crate or Many?

Start with intent, not with folders.

- **One package, one binary** (most apps): start as a single crate (`src/main.rs`) with internal modules. Split into crates only when you have a real boundary (reusability, compile-time isolation, optional heavy deps, proc-macro companion).
- **Library crate intended for reuse**: start as a single crate (`src/lib.rs`) with a deliberately small public API surface. Treat `pub` as a semver commitment.
- **Product made of multiple independently meaningful crates** (app + core lib + proc-macro + integration crates): use a workspace.

If you cannot name the boundary, it is not a crate yet.

## Workspace Rules (Cargo Book: Workspaces)

1. **Use a workspace to manage multiple packages together.** Workspaces share `Cargo.lock` and `target/`, and cargo commands can operate across the whole set (`cargo check --workspace`).
2. **Prefer a virtual workspace for multi-crate repos.** Put only `[workspace]` in the root `Cargo.toml` when there is no single “primary” root package.
3. **Set the resolver explicitly in a virtual workspace.** Cargo requires this because there is no root package edition to infer it from.

Recommended root `Cargo.toml` skeleton:

```toml
[workspace]
members = ["crates/*"]
resolver = "3" # Cargo Book: in a virtual workspace you must set this explicitly; do not rely on member package editions

[workspace.package]
edition = "2024"
rust-version = "1.84" # set intentionally; for published crates, treat MSRV as a compatibility commitment
license = "MIT OR Apache-2.0"
repository = "https://example.com/your/repo"

[workspace.dependencies]
anyhow = "1"
thiserror = "2"
```

4. **Centralize versions and metadata with `workspace.package` and `workspace.dependencies`.** This reduces dependency drift and makes upgrades mechanical (Cargo Book: `workspace.package`, `workspace.dependencies`).
5. **Commit `Cargo.lock` for applications/products.** Lockfiles are part of reproducibility for binaries and deployed services. (For published libraries, locking is usually not required, but a workspace that builds an app should still commit the lockfile.)

For concrete layout patterns (`crates/*`, `xtask`, shared lints), see [references/workspaces-and-layout.md](references/workspaces-and-layout.md).

Module file layout rule (Rust Reference; Edition Guide):
- Prefer the Rust 2018+ convention `foo.rs` + `foo/bar.rs` over `foo/mod.rs` + `foo/bar.rs`.
- Never have both `foo.rs` and `foo/mod.rs`.
- Do not mix conventions arbitrarily inside one crate; it makes navigation harder (Rust Book notes the “many mod.rs tabs” problem).

## Features: What They Are For (and What They Are Not)

Cargo features are for conditional compilation and optional dependencies, and they are globally unified across the dependency graph.

**Non-negotiable facts (Cargo Book: Features → Feature unification):**
- Features are **additive**: the compiled feature set is the **union** of all requests from the graph.
- `default-features = false` is not a force field: if any other path enables defaults, they are enabled.
- This is why “features for internal organization” in a workspace is usually ceremony.

### Rule 1: Do not use feature flags to separate internal concerns inside a workspace

If you want “component A sometimes exists and sometimes doesn’t” inside a workspace, make it a **separate crate** and depend on it conditionally at the top level (or have two binaries). Feature flags are for *consumers*; crate boundaries are for *architecture*.

This rule exists because of feature unification: if any workspace member enables a feature, the dependency is built with that feature everywhere it appears.

### Rule 2: Features must be additive and combinable

Do not implement “either/or” behavior via features unless you also enforce exclusivity (Cargo Book: mutually exclusive features) and you are willing to make it everybody’s problem.

If two features are truly incompatible, prefer splitting into separate crates. If you must keep one crate, add:

```rust
#[cfg(all(feature = "foo", feature = "bar"))]
compile_error!("features \"foo\" and \"bar\" cannot be enabled together");
```

### Rule 3: Never feature-gate public struct fields or public trait methods

This breaks downstream code unpredictably under feature unification and is a semver footgun (Effective Rust Item 26).

Instead:
- Feature-gate **impl blocks** (e.g. `impl Serialize for T`) or whole private modules.
- Provide separate types behind features and re-export a stable facade.

For the full rulebook (with failure cases and `cargo tree -e features` debugging), see [references/features-and-unification.md](references/features-and-unification.md).

## Crate = Boundary; `lib.rs` = Facade

Treat `src/lib.rs` (or `src/main.rs`) as the place where you choose what exists for callers.

### Rule 1: Minimize visibility

Default everything to private. Promote visibility only when you have a caller that needs it.

- Prefer `pub(crate)` for crate-internal APIs.
- Prefer private struct fields + constructors/builders for invariants.

Authority: Effective Rust Item 22; Rust API Guidelines [C-STRUCT-PRIVATE].

### Rule 2: Export a small public surface using `pub use`

Use an internal module tree for organization, but re-export the intended API from the crate root (or a dedicated `api` module).

```rust
// src/lib.rs
mod error {
    #[derive(Debug)]
    pub struct Error;
}

mod parse {
    pub struct Parser;
}

pub use crate::error::Error;
pub use crate::parse::Parser;
```

Do not make your module tree your API by accident (`pub mod everything;`). When callers import `yourcrate::foo::bar::Baz`, you have committed to that path.

### Rule 3: Avoid wildcard imports in library code

`use crate::*;` and `use super::*;` make it harder to see what a module depends on and increase the chance of name clashes during refactors.

Authority: Effective Rust Item 23; clippy lint `wildcard_imports`.

For patterns like “facade module”, “prelude module”, and “re-exporting dependency types that appear in your API”, see [references/public-api-surface.md](references/public-api-surface.md).

## Cargo.toml Metadata Is Part of the Product

For any crate that is intended to be reused or published, fill in the basics early.

Authority: Rust API Guidelines [C-METADATA]; Cargo Book: manifest fields.

Minimum:
- `edition` (default to the latest stable; Cargo uses the latest edition for `cargo new` — Edition Guide: “Creating a new project”)
- `rust-version` (set intentionally; treat MSRV as a compatibility commitment if you publish)
- `license`, `repository`, `description`

## Documentation and Examples Defaults

1. **Crate-level docs belong in `//!` at the crate root.** They are what docs.rs shows as the landing page (Effective Rust Item 27; Rust API Guidelines [C-CRATE-DOC]).
2. **Public items should have examples when non-trivial.** Doc tests compile and run with `cargo test`.
3. **In docs, prefer `?` over `unwrap`.** Authority: Rust API Guidelines [C-QUESTION-MARK].
4. **Enable link checking for rustdoc.** Add `#![deny(broken_intra_doc_links)]` in library crates so link rot fails CI (Effective Rust Item 27).
5. **Use `examples/` for larger usage samples.** Use `required-features` in `Cargo.toml` to avoid broken examples when optional features are off.

## Common Mistakes (Agent Failure Modes)

- **“Workspace = folders”**: splitting into crates with no boundary. Fix: stay single-crate until you can name the boundary (reusability, compile-time isolation, optional heavy deps, proc-macro companion).
- **“Feature flags for internal separation”**: adding `cfg(feature = "...")` throughout workspace crates. Fix: make separation real with crate boundaries; remember feature unification.
- **“My module tree is my API”**: exporting everything with `pub mod ...;`. Fix: keep modules private and re-export a curated facade from `lib.rs`.
- **“Public API changes under features”**: feature-gating public fields/methods. Fix: gate impls or private modules; keep public types stable.
- **“Debug by guessing”**: staring at `Cargo.toml` instead of the resolved graph. Fix: use `cargo tree` (see below).

Incorrect → correct (public module tree as accidental API):

```rust
// Bad: makes `yourcrate::foo::Foo` part of the public API.
pub mod foo {
    pub struct Foo;
}

pub mod bar {
    pub struct Bar;
}
```

```rust
// Good: keep modules private; re-export the stable API surface.
mod foo {
    pub struct Foo;
}

mod bar {
    pub struct Bar;
}

pub use crate::bar::Bar;
pub use crate::foo::Foo;
```

### Common “Cargo is Weird” Symptoms → Actions

| Symptom | Likely cause | Do this |
|---|---|---|
| `default-features = false` “does nothing” | feature unification | `cargo tree -e features -i yourdep` |
| “Why is this dependency even here?” | transitive dep pulls it | `cargo tree -i depname` |
| Multiple versions of the same crate in the graph | conflicting semver ranges | `cargo tree -d`, align versions via workspace deps |
| “Feature X got enabled and I didn’t ask for it” | some other crate asked | `cargo tree -e features -i depname` |

## Cross-References

- [type-design.md](type-design.md) — model boundaries with types; avoid “configuration by bool/string”; parse at the boundary
- [error-handling.md](error-handling.md) — library vs application error type choices affect crate layout (thiserror vs anyhow)
- [serde.md](serde.md) (when added) — keep serde behind additive features without breaking your public API

## Review Checklist

1. Is the crate/workspace boundary real (reusability, optional heavy deps, compile-time isolation), not just “folder organization”?
2. If multi-crate: is there a workspace, and is `resolver` set explicitly (especially for virtual workspaces)?
3. Are `workspace.dependencies` and `workspace.package` used to prevent version/metadata drift?
4. Are features used only for optional capabilities/optional deps, and are they additive under feature unification?
5. Are there any feature-gated public fields or trait methods (remove them)?
6. Is the public API surface intentionally small (facade via `pub use`, minimal `pub`, `pub(crate)` by default)?
7. Are there any wildcard imports in library modules that should be explicit?
8. Does `Cargo.toml` include edition + rust-version + license + repository + description (where relevant)?
9. Are crate-level docs present (`//!`), with runnable examples, and is `broken_intra_doc_links` enforced?
10. Are examples/tests/benches gated with `required-features` where necessary, and is CI running at least `cargo test`, `cargo test --all-features`, and `cargo test --no-default-features` (when meaningful)?
