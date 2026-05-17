# Cairo — Immortal Interned IDs + Automatic heap_size

Production memory management patterns from Cairo (StarkNet smart contract compiler).

## Cairo: Immortal Interned IDs + Automatic `heap_size`

### `revisions = usize::MAX`: Disabling Interned Value GC

Cairo uses `revisions = usize::MAX` on all interned types (38+), disabling garbage collection entirely:

```rust
// cairo/crates/cairo-lang-utils/src/lib.rs — inside define_short_id! macro
#[cairo_lang_proc_macros::interned(revisions = usize::MAX)]
pub struct $short_id<'db> {
    #[returns(ref)]
    pub long: $long_id,
}
```

And on Sierra generator types:

```rust
// cairo/crates/cairo-lang-sierra-generator/src/db.rs
#[salsa::interned(revisions = usize::MAX)]
struct ConcreteLibfuncIdLongWrapper {
    id: cairo_lang_sierra::program::ConcreteLibfuncLongId,
}

#[salsa::interned(revisions = usize::MAX)]
struct SierraGeneratorTypeLongIdWrapper<'db> {
    id: SierraGeneratorTypeLongId<'db>,
}
```

**Why?** Cairo stores interned IDs in serialized cache files on disk. If GC recycles an ID between revisions, the cached reference would point to wrong data. Making IDs immortal ensures cache correctness.

**Trade-off:** In an LSP server, interned values accumulate indefinitely. Acceptable for Cairo's primary use case (short-lived compiler invocations).

### Proc Macro Wrappers for Universal `heap_size`

Cairo's `#[cairo_lang_proc_macros::interned]` and `#[cairo_lang_proc_macros::tracked]` automatically inject `heap_size`:

```rust
// cairo/crates/cairo-lang-proc-macros/src/lib.rs
#[proc_macro_attribute]
pub fn interned(attr: TokenStream, item: TokenStream) -> TokenStream {
    let mut args = parse_args(attr);

    let has_heap_size = args.iter()
        .any(|meta| matches!(meta, Meta::NameValue(nv) if nv.path.is_ident("heap_size")));

    if !has_heap_size {
        let heap_size: Meta = syn::parse_quote!(heap_size = cairo_lang_utils::HeapSize::heap_size);
        args.push(heap_size);
    }

    let salsa_attr = quote! { #[salsa::interned(#args)] };
    // ...
}
```

This ensures **every** Salsa ingredient in Cairo has heap tracking without manual annotation — the same coverage ty achieves with explicit `heap_size=ruff_memory_usage::heap_size` on each attribute, but enforced at the macro level.

### No LRU, No `no_eq`

Cairo uses zero LRU caches and zero `no_eq` annotations. As a compiler (not an LSP server), memory growth from unbounded caching isn't a concern — the process exits after compilation. This is a valid design choice for batch-mode tools.

### Comparison: All Three Projects

| Aspect | Ruff/ty monorepo | rust-analyzer | Cairo |
|--------|------|---------------|-------|
| LRU queries | 1 (`parsed_module` at 200) | 5+ (16 to 2024) | 0 |
| `no_eq` usage | `parsed_module`, `semantic_index` | Less common | None |
| `heap_size` | Explicit on every attribute | Not used | Auto-injected via proc macro |
| Interned GC | Default (aggressive in tests) | `revisions = usize::MAX` | `revisions = usize::MAX` |
| Manual GC | `ArcSwapOption` for mid-revision | None | None |
| Compile optimization | N/A | `ManuallyDrop` on storage | N/A |
| Return modes | `ref`, `deref` extensively | `ref`, `clone`, `deref`, `as_deref` | `ref` extensively |
| Primary use case | LSP server (long-running) | LSP server (long-running) | Compiler (batch) |
