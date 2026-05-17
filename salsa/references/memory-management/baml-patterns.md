# BAML — Minimal Memory Management: `returns(ref)` Only

Memory management patterns from BAML (AI/LLM function compiler). The simplest production approach — only `returns(ref)` on tracked struct fields, with no LRU, no `no_eq`, no `heap_size`.

## Systematic `returns(ref)` on All Collection Fields

Every tracked struct field that holds a collection uses `#[returns(ref)]`:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:80-91
#[salsa::tracked]
pub struct FileItems<'db> {
    #[tracked]
    #[returns(ref)]
    pub items: Vec<ItemId<'db>>,
}

#[salsa::tracked]
pub struct ProjectItems<'db> {
    #[tracked]
    #[returns(ref)]
    pub items: Vec<ItemId<'db>>,
}
```

```rust
// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:155-204
#[salsa::tracked]
pub struct EnumVariantsMap<'db> {
    #[tracked]
    #[returns(ref)]
    pub enums: HashMap<Name, Vec<Name>>,
}

#[salsa::tracked]
pub struct TypingContextMap<'db> {
    #[tracked]
    #[returns(ref)]
    pub functions: HashMap<Name, Ty>,
}

#[salsa::tracked]
pub struct ClassFieldTypesMap<'db> {
    #[tracked]
    #[returns(ref)]
    pub classes: HashMap<Name, HashMap<Name, Ty>>,
}
```

All 15 tracked structs follow this pattern. Callers receive `&Vec<...>` or `&HashMap<...>` instead of clones.

## Where `Arc` Supplements `returns(ref)`

For values that need to escape tracked function contexts, BAML wraps in `Arc`:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:103-108
#[salsa::tracked]
pub struct LoweringResult<'db> {
    #[tracked]
    #[returns(ref)]
    pub item_tree: Arc<ItemTree>,     // Arc for cheap cloning via file_item_tree()
    #[tracked]
    #[returns(ref)]
    pub diagnostics: Vec<HirDiagnostic>,
}
```

The convenience wrapper `file_item_tree()` calls `.clone()` on the `Arc<ItemTree>` — an O(1) reference count increment, avoiding a deep clone of the entire item tree:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:174-176
pub fn file_item_tree(db: &dyn Db, file: SourceFile) -> Arc<ItemTree> {
    file_lowering(db, file).item_tree(db).clone()  // Arc::clone, not ItemTree::clone
}
```

Functions that return `Arc`-wrapped values use `Arc` on the return type itself:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:251-256
#[salsa::tracked]
pub fn function_signature<'db>(
    db: &'db dyn Db, function: FunctionLoc<'db>,
) -> Arc<FunctionSignature> { /* ... */ }

// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:963-967
#[salsa::tracked]
pub fn function_type_inference<'db>(
    db: &'db dyn Db, function: FunctionLoc<'db>,
) -> Arc<InferenceResult> { /* ... */ }
```

## What BAML Does NOT Use

| Feature | Used? | Why Not |
|---------|-------|---------|
| LRU eviction | No | Short-lived compiler process; cache doesn't grow unbounded |
| `no_eq` | No | No AST offset sensitivity (spans are separate from type data) |
| `heap_size` | No | No memory profiling infrastructure |
| `returns(deref)` | No | `returns(ref)` + `Arc` covers all cases |

## Memory Strategy Comparison

| Project | `returns(ref)` | LRU | `no_eq` | `heap_size` | Notes |
|---------|---------------|-----|---------|-------------|-------|
| **BAML** | ✅ All tracked fields | ❌ | ❌ | ❌ | Simplest approach |
| **django-language-server** | ✅ Some fields | ❌ | ❌ | ❌ | Also minimal |
| **ty** | ✅ + `returns(deref)` | `lru=200` on parsed_module | ✅ on parsed/semantic | ✅ via feature flag | Production LSP |
| **rust-analyzer** | ✅ + `returns(deref)` + `returns(as_deref)` | Multiple (`lru=128`, `lru=512`, `lru=1024`, `lru=2024`) | ❌ | ❌ | Runtime-tunable LRU |
| **Cairo** | ✅ (183+ functions) | ❌ | ❌ | ✅ via proc macro | Auto-injected heap_size |

**Bottom line:** `returns(ref)` on collection fields is the universal starting point. Add LRU, `no_eq`, and `heap_size` only when memory profiling reveals specific problems — and only for long-running processes (LSP servers, watch-mode CLIs).
