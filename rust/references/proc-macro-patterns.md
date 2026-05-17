# Procedural macro patterns (derive / attribute / function-like)

This file is a set of defaults for proc-macro crates: structure, parsing, quoting, error reporting, and name-resolution robustness.

**Authority:** Rust Reference “Procedural macros”; syn/quote/darling docs; proc-macro-workshop.

## 1) Crate layout: thin proc-macro crate, testable core

Default layout:

- `my-macro/` (proc-macro = true)
  - `src/lib.rs`: entrypoints only, tiny adapters
- `my-macro-core/` (normal lib)
  - parsing + validation + codegen helpers

Why: `proc-macro` crates cannot export normal APIs for consumers to call at runtime, are awkward to unit test, and slow rebuilds. Putting most logic in a normal crate makes it testable and reusable.

## 2) The canonical derive skeleton (syn + quote)

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MyDerive, attributes(my_derive))]
pub fn my_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);

    match expand_my_derive(input) {
        Ok(tokens) => tokens.into(),
        Err(err) => err.to_compile_error().into(),
    }
}

fn expand_my_derive(input: DeriveInput) -> syn::Result<proc_macro2::TokenStream> {
    let ident = input.ident;
    Ok(quote! {
        impl #ident {
            pub fn generated() {}
        }
    })
}
```

Defaults:

- Return `syn::Result<proc_macro2::TokenStream>` from internal helpers.
- Convert errors with `to_compile_error()`.
- Prefer `proc_macro2` types internally so you can test helpers outside proc-macro context.

## 3) Error reporting: spanned `syn::Error`, not panic

User input errors should produce diagnostics that point at the relevant token in the user’s code.

```rust
return Err(syn::Error::new_spanned(
    &some_ast_node,
    "expected #[my_attr(...)] on a named-field struct",
));
```

Then bubble the error to the entrypoint and return `to_compile_error()`.

Panics are for bugs in your macro implementation, not for invalid user input.

**Authority:** syn README “spans and error reporting”; Rust Reference “procedural macros can panic” (but that’s the worst UX).

## 4) Name resolution: treat proc-macro output as if it was handwritten at the call site

Procedural macros are unhygienic.

Defaults:

- Use absolute core/std paths: `::core::option::Option`, `::core::result::Result`, `::core::marker::PhantomData`.
- Do not rely on call-site `use` statements.
- Avoid generating `use` statements unless you control the entire module you are expanding into.

For internal helper items, use collision-resistant names:

- Prefix with `__my_macro_...`.
- Use `quote::format_ident!` for constructed idents.

## 5) Attribute parsing: prefer structured parsing over manual token poking

If you accept helper attributes, parse them into typed structs.

- Use `syn::Attribute::parse_nested_meta` or `syn::Meta` parsing for simple cases.
- Use `darling` when your attribute syntax becomes non-trivial (defaults, rename, validation, “did you mean” suggestions).

**Authority:** darling README (FromMeta / FromDeriveInput, validation + good errors).

## 6) Determinism: behave like a compiler pass, not like a script

- No network access.
- No nondeterministic outputs (timestamps, random suffixes that change per build).
- If you must read files for codegen, make it explicit and document exactly what gets read.

**Authority:** Rust Reference: proc macros have the same resource-access concerns as build scripts.
