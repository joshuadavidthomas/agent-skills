# Rust Macros: The Defaults

Macros are compile-time code generation. They are a power tool.

Default to **not** writing a macro.

- If a function works, write a function.
- If generics + traits work, use generics + traits.
- If a proc-macro seems convenient for boilerplate, check whether `#[derive(...)]` already exists in the ecosystem (serde, thiserror, clap, strum, etc.).

**Authority:** Rust Reference (macros, procedural macros); TLBORM (macro_rules patterns); syn/quote docs (proc-macro ecosystem); proc-macro-workshop (real-world proc macro shapes).

## Cross-references

- Use [type-design.md](type-design.md) and [traits.md](traits.md) when reaching for macros to “avoid boilerplate” or to model domain structure. Prefer types, enums, and traits first.
- Use [error-handling.md](error-handling.md) when generated runtime APIs need a consistent error strategy. Macros should still emit good compile-time diagnostics.

## 1) First question: do you need a macro at all?

Write a macro only if at least one is true:

- You need a **variadic interface** or non-Rust syntax surface (`println!`, `vec!`, DSL-like configuration blocks).
- You need **token-level manipulation**: you must accept identifiers/types/paths as tokens, not values.
- You are generating impls/items based on the **shape of a struct/enum/trait** (derive/attribute macros).
- You need to enforce a **compile-time rule** about code structure (e.g. `#[sorted]` in proc-macro-workshop).

If what you want is “avoid writing boilerplate”, prefer:

- `#[derive(...)]` from existing crates.
- Generic helper traits.
- `impl<T> ...` + blanket impls.
- `macro_rules!` before proc macros.

## 2) Choose the right macro kind (decision table)

| Need | Use | Why |
|------|-----|-----|
| Repeat simple patterns, accept Rust fragments (`expr`, `ty`, `pat`) | `macro_rules!` | Fast to compile, good error spans, hygienic-ish, no extra crate |
| Inspect Rust item structure (fields, attrs, generics) and generate impls | `#[proc_macro_derive]` | Intended for “derive boilerplate”, best UX for users |
| Transform an item (rewrite/augment fn/impl/module) | `#[proc_macro_attribute]` | Operates on the annotated item |
| Custom syntax that is not Rust fragments | `#[proc_macro]` function-like | You own parsing; use only when necessary |

Default ordering:

1. No macro.
2. `macro_rules!`.
3. Derive macro.
4. Attribute macro.
5. Function-like proc macro.

## 3) `macro_rules!` defaults (macros by example)

### Rule 1: Make the input grammar real Rust fragments

- Prefer `expr`, `ty`, `path`, `ident`, `item`, `meta` fragment specifiers.
- Use `tt` only when you truly need token trees (most `tt` macros are unparseable DSLs with bad errors).

**Authority:** Rust Reference “Macros by example” (fragment specifiers, no lookahead).

### Rule 2: Avoid local ambiguity; design for one-token-at-a-time parsing

`macro_rules!` does not do parser lookahead. If the invocation is ambiguous, you get “local ambiguity”.

- Separate ambiguous parts with delimiters (`;`, `,`, `=>`, braces) so the matcher can decide immediately.
- Prefer explicit keywords inside the macro syntax when there are multiple modes.

**Authority:** Rust Reference “When matching, no lookahead is performed”.

### Rule 3: Do not evaluate inputs more than once

If you accept an `$expr:expr`, you must treat it as potentially side-effecting.

- If you use it twice, bind it once (`let tmp = $expr;`) and use the tmp.
- For fallible extraction, use a `match` to bind and control evaluation.

See: [references/macro_rules-patterns.md](references/macro_rules-patterns.md) for the “single evaluation” building block.

### Rule 4: Always support trailing commas in list-like macros

If your macro takes a comma-separated list, accept an optional trailing comma:

- `$( $x:expr ),* $(,)?`

This mirrors the standard library and improves diffs.

### Rule 5: Exported macros must be path-stable and crate-renaming-safe

If a macro expands to refer to items in *your* crate:

- Use `$crate::...` inside the expansion for crate-local paths.
- Use absolute `::core::...` / `::std::...` paths for std/core types used by the expansion.

This prevents breakage when callers rename dependencies in Cargo.toml.

**Authority:** Rust Reference: `$crate` metavariable.

### Rule 6: Prefer path-based macro invocation in non-trivial codebases

- Prefer `crate::my_macro!()` / `my_crate::my_macro!()` / `use my_crate::my_macro;` over relying on textual scoping.
- Avoid `#[macro_use]` except when maintaining legacy code.

**Authority:** Rust Reference: textual vs path-based scope.

### Rule 7: Make errors loud and local

- For invalid forms, match them and emit `compile_error!`.
- Prefer “fail with a targeted message” over “no rules expected this token”.

## 4) Procedural macro defaults

Procedural macros are compiled Rust programs that run during compilation. They are powerful and expensive.

**Authority:** Rust Reference “Procedural macros”; syn/quote docs; proc-macro-workshop.

### Rule 1: Put logic in a normal crate; keep the proc-macro crate thin

Default project layout for proc macros:

- `my-macro/` (proc-macro = true): `#[proc_macro_*]` entrypoints only.
- `my-macro-core/` (normal lib): parsing + validation + codegen helpers.

Why: proc-macro crates are harder to test and slow down incremental builds; core crates are testable and reusable.

### Rule 2: Use `syn` + `quote` + `proc_macro2` as the default stack

- Parse with `syn` (e.g. `DeriveInput`, `ItemFn`, `ItemImpl`).
- Generate tokens with `quote!`.
- Use `proc_macro2::TokenStream` internally; convert at the boundary.

Deep dive patterns: [references/proc-macro-patterns.md](references/proc-macro-patterns.md).

### Rule 3: Never `unwrap()` macro parsing in a published macro

- Parse with `parse_macro_input!` or `syn::parse`.
- Convert parse/validation failures into `syn::Error` with spans and return `to_compile_error()`.
- Panicking is acceptable only for “this is a bug in the macro implementation”, not for user input.

**Authority:** Rust Reference: macros can panic; syn docs: spans + error reporting; proc-macro-workshop: compile-time diagnostics.

### Rule 4: Generate code that is robust to name resolution

Procedural macros are unhygienic: output behaves like it was written at the call site.

Defaults:

- Use absolute paths for standard library types: `::core::option::Option`, `::core::result::Result`.
- For your own runtime crate, prefer a path that is stable under renaming. If you require callers to depend on both `my-macro` and `my-runtime`, document the canonical rename and enforce it (or accept a `#[my_macro(crate = "...")]` helper attr).
- Generate internal helper identifiers with a low collision risk (e.g. `__my_macro_*`), and use `quote::format_ident!` when concatenating.

**Authority:** Rust Reference: “procedural macros are unhygienic”; quote docs: `format_ident!`.

### Rule 5: For derives, be conservative about inferred trait bounds

Derive macros that "guess" bounds often guess wrong.

Defaults:

- Prefer emitting impls that compile under obvious, minimal bounds.
- If you must add bounds, do so using syn’s generics APIs and keep them targeted to the exact type params used.
- When in doubt, require explicit bounds from the user (document it), rather than emitting an impl that is unsound or overly restrictive.

(Proc-macro-workshop’s `CustomDebug` is the canonical real-world example of this pitfall.)

### Rule 6: Treat proc macros like build scripts: deterministic, no surprises

- Do not access the network.
- Do not read arbitrary files unless your macro’s documented purpose is codegen from files.
- Make expansion deterministic (no timestamps, no random names that change per build).

**Authority:** Rust Reference: proc macros have the same resource access concerns as build scripts.

## 5) Debugging and testing defaults

### Debugging expansions

- Use `cargo expand` from the consumer crate to see final expanded code.
- When debugging name resolution, inspect the expansion for missing `::core` / `$crate` / runtime crate paths.

### Testing

- For “should compile” behavior: regular unit/integration tests using the macro.
- For “should fail with a good error”: use `trybuild` (compile-fail tests) and lock in diagnostics.

**Authority:** syn README: recommends trybuild and cargo expand.

Deep dive: [references/testing-and-debugging-macros.md](references/testing-and-debugging-macros.md).

## 6) Common mistakes (agent failure modes)

- Writing a proc macro when `macro_rules!` (or a function/trait) would do. Proc macros add a build-dependency and increase compile time.
- Using `tt` matchers as the default input type. This creates an unparseable DSL and terrible diagnostics; prefer real fragment specifiers.
- Expanding `$expr` more than once (double evaluation) and accidentally duplicating side effects. Bind once or `match`.
- Exporting a macro that refers to crate items without `$crate::...`, breaking when the crate is renamed.
- In proc macros: `unwrap()`/`expect()` on user input, causing a panic instead of a spanned diagnostic.
- Generated code that relies on call-site `use` statements or unqualified names (`Result`, `Error`, `Vec`), causing name resolution failures.
- Nondeterministic expansions (timestamps, random IDs) that break reproducible builds.

## 7) Review checklist (use in code review)

1. Is a macro necessary, or can this be a function/trait/derive from an existing crate?
2. If it’s `macro_rules!`: are fragment specifiers specific (not `tt` everywhere), and is the invocation grammar unambiguous (no local ambiguity)?
3. If it’s `macro_rules!`: does it avoid double-evaluating `$expr` inputs?
4. If it’s exported: does it use `$crate::...` for crate-local references and `::core`/`::std` for std types?
5. If it’s a proc macro: is the proc-macro crate thin, with logic in a normal crate?
6. Does the proc macro return spanned `compile_error!` output for user errors (no unwrap/panic on bad input)?
7. Does generated code avoid name collisions and avoid depending on call-site imports?
8. Are there `cargo expand` instructions (at least for contributors) and `trybuild` tests for expected diagnostics?
