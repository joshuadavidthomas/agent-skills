# Public API Surface (lib.rs as a facade)

Public API design is project structure. In Rust, `pub` is not “make it accessible”; it is “make it part of the compatibility contract” (Effective Rust Item 22; Cargo semver expectations).

## Visibility discipline

Rules:
- Default to private.
- Prefer `pub(crate)` over `pub` for internal cross-module helpers.
- Prefer private fields + constructors/builders for invariants (Rust API Guidelines [C-STRUCT-PRIVATE]).
- Treat making something `pub` as a review-worthy change.

## Facade pattern: internal modules, curated exports

Organize code internally however you want; export a deliberately small surface.

```rust
// src/lib.rs
mod api;
mod internal;
mod parse;

pub use crate::api::{Client, Config};
pub use crate::internal::Error;
```

```rust
// src/api.rs
pub struct Client { /* private fields */ }
pub struct Config { /* private fields */ }
```

Rules:
- Prefer `pub use` from crate root for top-level types.
- Avoid `pub mod internal;` unless you intend downstream callers to depend on that module path.
- When you move types between modules internally, the facade keeps downstream imports stable.

## Prelude modules (use sparingly)

A `prelude` exists to make common trait imports ergonomic (iterators, extension traits). It must be small and stable.

Rule: if importing the prelude is required to use the crate, your API is probably too implicit.

## Avoid wildcard imports

Authority: Effective Rust Item 23.

Rules:
- In libraries, avoid `use crate::*;` and `use super::*;` except in small test modules.
- Prefer explicit imports so refactors are localized and reviewers can see dependencies.

## Re-export dependency types that appear in your API

If your public types mention `dep::Type`, you have effectively made `dep` part of your API. Consider re-exporting that dependency (Effective Rust Item 24) so downstream users can name the types without pulling in and version-resolving the dependency themselves.

Typical pattern:

```rust
pub use http;

pub fn build(req: http::Request<Vec<u8>>) -> http::Response<Vec<u8>> { todo!() }
```

Rule: do this only when the dependency is truly part of the API contract, not for convenience re-exports.

## Documentation placement

Authority: Effective Rust Item 27; Rust API Guidelines documentation checklist.

Rules:
- Put crate-level docs in `//!` in `src/lib.rs` (docs.rs landing page).
- Put “how to choose this crate” content in `README.md` (crates.io landing page).
- Put runnable examples in doc comments and `examples/`.
- Add `#![deny(broken_intra_doc_links)]` in library crates.

## Semver implications of structure

Rust’s semver hazards are often structural:
- Making a private item public is usually backwards-compatible; making public items private is breaking.
- Adding enum variants is breaking unless the enum is `#[non_exhaustive]`.
- Adding public struct fields is breaking unless construction is prevented (private fields or `#[non_exhaustive]`).

Rule: keep the public surface minimal so that future refactors remain possible.
