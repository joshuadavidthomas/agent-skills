# rust-analyzer — Tiered LRU + ManuallyDrop

Production memory management patterns from rust-analyzer (Rust IDE).

## rust-analyzer: Tiered LRU + ManuallyDrop

### LRU Capacity Constants

```rust
// rust-analyzer/crates/base-db/src/lib.rs
pub const DEFAULT_FILE_TEXT_LRU_CAP: u16 = 16;
pub const DEFAULT_PARSE_LRU_CAP: u16 = 128;
pub const DEFAULT_BORROWCK_LRU_CAP: u16 = 2024;
```

### Tiered LRU Across the Pipeline

```rust
// Parse: 128 entries
// rust-analyzer/crates/base-db/src/lib.rs
#[salsa::invoke(parse)]
#[salsa::lru(128)]
fn parse(&self, file_id: EditionedFileId) -> Parse<ast::SourceFile>;

// AST ID map: 1024 entries (small metadata, cheap to keep)
// rust-analyzer/crates/hir-expand/src/db.rs
#[salsa::lru(1024)]
fn ast_id_map(&self, file_id: HirFileId) -> Arc<AstIdMap>;

// Macro expansion: 512 entries
// rust-analyzer/crates/hir-expand/src/db.rs
#[salsa::lru(512)]
fn parse_macro_expansion(
    &self,
    macro_file: MacroFileId,
) -> ExpandResult<(Parse<SyntaxNode>, Arc<ExpansionSpanMap>)>;

// Function bodies + source maps: 512 entries
// rust-analyzer/crates/hir-def/src/db.rs
#[salsa::invoke(Body::body_with_source_map_query)]
#[salsa::lru(512)]
fn body_with_source_map(&self, def: DefWithBodyId) -> (Arc<Body>, Arc<BodySourceMap>);

// Borrow checking: 2024 entries (most expensive, cache aggressively)
// rust-analyzer/crates/hir-ty/src/db.rs
#[salsa::invoke(crate::mir::borrowck_query)]
#[salsa::lru(2024)]
fn borrowck(&self, def: DefWithBodyId) -> Result<Arc<[BorrowckResult]>, MirLowerError>;
```

**Pattern:** Cache sizes grow with computational cost:
```
File text (16) → Parse (128) → Macro expand (512) → Body (512) → Borrow check (2024)
```

### Runtime LRU Configuration (Currently Disabled)

rust-analyzer had runtime-adjustable LRU before its Salsa migration. The infrastructure remains:

```rust
// rust-analyzer/crates/rust-analyzer/src/config.rs
lru_capacity: Option<u16> = None,
lru_query_capacities: FxHashMap<Box<str>, u16> = FxHashMap::default(),
```

```rust
// rust-analyzer/crates/ide-db/src/lib.rs
// FIXME(salsa-transition): bring this back; allow changing LRU settings at runtime.
pub fn update_base_query_lru_capacities(&mut self, _lru_capacity: Option<u16>) {
    // Currently no-op during salsa migration
}

pub fn update_lru_capacities(&mut self, _lru_capacities: &FxHashMap<Box<str>, u16>) {
    // Previously allowed per-query configuration
}
```

The commented-out code reveals the intended design:
- Parse capacity configurable by user
- Macro expansions get 4× parse capacity ("usually rather small")
- Body source maps capped at 2048
- Borrow check at a fixed 2024

### ManuallyDrop for Compile-Time Optimization

```rust
// rust-analyzer/crates/ide-db/src/lib.rs
pub struct RootDatabase {
    // We use `ManuallyDrop` here because every codegen unit that contains a
    // `&RootDatabase -> &dyn OtherDatabase` cast will instantiate its drop glue in the vtable,
    // which duplicates `Weak::drop` and `Arc::drop` tens of thousands of times, which makes
    // compile times of all `ide_*` and downstream crates suffer greatly.
    storage: ManuallyDrop<salsa::Storage<Self>>,
    files: Arc<Files>,
    crates_map: Arc<CratesMap>,
    nonce: Nonce,
}

impl Drop for RootDatabase {
    fn drop(&mut self) {
        unsafe { ManuallyDrop::drop(&mut self.storage) };
    }
}
```

This is not a runtime optimization — it reduces compile times by preventing the compiler from generating duplicate drop glue for every trait object cast involving the database.

### Return Mode Usage

```rust
// returns(ref) — borrow from Salsa storage
// rust-analyzer/crates/hir-def/src/signatures.rs
#[salsa::tracked(returns(ref))]
pub fn function_signature(db: &dyn DefDatabase, func: FunctionId) -> FunctionSignature { ... }

// returns(clone) — explicit clone (default, but stated for clarity)
#[salsa::tracked(returns(clone))]
pub fn trait_signature(db: &dyn DefDatabase, trait_: TraitId) -> TraitSignature { ... }

// returns(deref) — deref smart pointer
#[salsa::tracked(returns(deref))]
pub fn enum_signature(db: &dyn DefDatabase, e: EnumId) -> Arc<EnumSignature> { ... }

// returns(as_deref) — for Option<Arc<T>> → Option<&T>
#[salsa::tracked(returns(as_deref))]
fn closure_captures_map(db: &dyn HirDatabase, def: DefWithBodyId) -> Option<Arc<CapturesMap>> { ... }
```

## Comparison: Ruff/ty Monorepo vs rust-analyzer Memory Strategies

| Aspect | Ruff/ty monorepo | rust-analyzer |
|--------|------|---------------|
| LRU queries | 1 (`parsed_module` at 200) | 5+ (16 to 2024) |
| `no_eq` usage | `parsed_module`, `semantic_index` | Less common (uses backdating more) |
| `heap_size` | On everything, with shared-object tracker | Not used (no `heap_size` attributes) |
| Manual GC | `ArcSwapOption` for mid-revision clearing | None (relies on LRU at revision boundaries) |
| Compile optimization | N/A | `ManuallyDrop` on database storage |
| Return modes | `ref`, `deref` extensively | `ref`, `clone`, `deref`, `as_deref` |
| Extraction pattern | `semantic_index` → `place_table`/`use_def_map` | Less prominent |

**Key takeaway:** The Ruff/ty monorepo invests heavily in memory profiling (`heap_size` everywhere) and uses fewer, larger LRU caches with manual mid-revision GC. rust-analyzer uses many tiered LRU caches without heap tracking, relying on the LRU sizes being "good enough" based on years of tuning.

