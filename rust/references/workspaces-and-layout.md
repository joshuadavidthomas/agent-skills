# Workspaces and Layout

Use a workspace when you have multiple packages that must be developed together and share a lockfile/build output (Cargo Book: Workspaces).

## Pick the workspace shape

### Virtual workspace (recommended default for multi-crate repos)

Use this when there is no single “primary” root crate.

```toml
# Cargo.toml (workspace root)
[workspace]
members = ["crates/*"]
resolver = "3"
```

Rules:
- In a virtual workspace, set `resolver` explicitly (Cargo Book: Workspaces; Resolver versions).
- Do not put dependencies in the root manifest unless they are `workspace.dependencies`.

### Root package workspace (app-first repos)

Use this when the repository is “an application” and supporting crates live alongside it.

```toml
# Cargo.toml (workspace root)
[workspace]
members = ["crates/*"]
resolver = "3"

[package]
name = "my-app"
edition = "2024"
```

Rules:
- Set `resolver` explicitly even with a root package so edition changes don’t silently change resolution behavior (Cargo Book: Workspaces; Resolver versions).
- When you add `[package]` at the root, commands run at the root default to the root package unless you use `--workspace` / `-p`.

## Module file layout: `foo.rs` vs `foo/mod.rs`

Rule (Rust Reference; Edition Guide; Rust Book): prefer the Rust 2018+ convention that avoids `mod.rs`.

Prefer:

```
src/
  lib.rs
  foo.rs
  foo/
    bar.rs
```

Avoid (still supported, but scales poorly in editors):

```
src/
  lib.rs
  foo/
    mod.rs
    bar.rs
```

Hard constraints:
- Never have both `foo.rs` and `foo/mod.rs` for the same module (compiler error; Rust Reference).
- Don’t mix the two conventions arbitrarily within a crate; it’s harder to navigate (Rust Book calls out the “many `mod.rs` files” downside).

## Canonical folder layout

Prefer:

```
Cargo.toml          # workspace root (virtual or root package)
Cargo.lock
crates/
  my_app/
    Cargo.toml
    src/main.rs
  my_lib/
    Cargo.toml
    src/lib.rs
  my_proc_macro/
    Cargo.toml
    src/lib.rs
xtask/
  Cargo.toml
  src/main.rs
```

Rules:
- Put each package in its own directory with its own `Cargo.toml`.
- Keep crates small and with one reason to change. If a crate has many unrelated optional subsystems, you probably want more crates, not more features.
- Proc-macro crates must be separate packages. Keep the proc-macro crate’s public API tiny and re-export macros from the “main” crate if you want ergonomic access.

## Centralize metadata and versions

### `workspace.package`

For multi-crate repos, inherit common metadata (edition, license, repository, rust-version, version).

```toml
# workspace root
[workspace.package]
edition = "2024"
rust-version = "1.84"
license = "MIT OR Apache-2.0"
repository = "https://github.com/you/repo"

# crates/my_lib/Cargo.toml
[package]
name = "my_lib"
edition.workspace = true
rust-version.workspace = true
license.workspace = true
repository.workspace = true
```

Cargo Book note: `workspace.package` and `workspace.dependencies` require MSRV 1.64+.

### `workspace.dependencies`

Use this to pin versions once and avoid drift.

```toml
# workspace root
[workspace.dependencies]
anyhow = "1"
thiserror = "2"
serde = { version = "1", features = ["derive"] }

# crates/my_app/Cargo.toml
[dependencies]
anyhow.workspace = true
thiserror.workspace = true
serde.workspace = true
```

Rules:
- Use this for shared libraries across many members.
- If a crate needs a feature variation, declare that dependency locally (feature sets differ per dependency edge).

## Commit `Cargo.lock` intentionally

Rules of thumb:
- **Application/product workspaces**: commit `Cargo.lock`. Your deployed artifact depends on exact versions.
- **Published library crates**: locking is not required for consumers, but your workspace may still contain binaries/tests; choose based on whether you ship executables.

## Workspace selection and scoping

Use these commands deliberately:
- `cargo check --workspace` / `cargo test --workspace` to validate everything.
- `cargo test -p my_crate` to target one crate.
- `cargo tree --workspace` to inspect full dependency graph.

If you want `cargo test` at the workspace root to run only a subset by default, set `default-members` (Cargo Book: `default-members`).

## Shared lints (optional but recommended)

Cargo supports `workspace.lints` so you can keep lint policy centralized. Prefer enforcing lints in CI, and keep local dev friction low.

Start conservative: `warnings` in CI, do not `deny` everything on day 1.
