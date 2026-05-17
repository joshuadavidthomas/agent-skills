# BAML — Complete Query Pipeline with Triple-Split Early Cutoff

Production query pipeline from BAML (AI/LLM function compiler). Demonstrates the cleanest "textbook-style" Salsa pipeline with well-documented early cutoff strategies.

## The Full Pipeline

```
SourceFile (input)
  → lex_file (tracked fn, salsa::Database)
    → parse_result (tracked fn → ParseResult tracked struct)
      → syntax_tree (helper, not tracked)
        → file_lowering (tracked fn → LoweringResult: item_tree + diagnostics)
          → file_item_tree (helper, Arc clone)
            → file_items (tracked fn, interns all items)
              → project_items (tracked fn, aggregates across files)
                → typing_context (tracked fn → TypingContextMap)
                → class_field_types (tracked fn → ClassFieldTypesMap)
                → enum_variants (tracked fn → EnumVariantsMap)
                → type_aliases (tracked fn → TypeAliasesMap)
                  → function_type_inference (tracked fn → Arc<InferenceResult>)
                    → collect_diagnostics (not tracked, walks all phases)
```

## Stage 1: Lexing

```rust
// baml/baml_language/crates/baml_compiler_lexer/src/lib.rs:14-18
#[salsa::tracked]
pub fn lex_file(db: &dyn salsa::Database, file: SourceFile) -> Vec<Token> {
    let text = file.text(db);
    lex_lossless(text, file.file_id(db))
}
```

**Note:** Takes `&dyn salsa::Database` (not `&dyn Db`) — lexing has no dependencies on higher-level traits, so it works with the base database.

## Stage 2: Parsing — Tracked Struct Split

```rust
// baml/baml_language/crates/baml_compiler_parser/src/lib.rs:14-39
#[salsa::tracked]
pub struct ParseResult<'db> {
    #[tracked]
    pub green: GreenNode,
    #[tracked]
    pub errors: Vec<ParseError>,
}

#[salsa::tracked]
pub fn parse_result(db: &dyn salsa::Database, file: SourceFile) -> ParseResult<'_> {
    let tokens = lex_file(db, file);
    let (green, errors) = parse_file(&tokens);
    ParseResult::new(db, green, errors)
}
```

**Why a tracked struct?** Splitting into two tracked fields enables independent access — callers that only need the green tree don't depend on error changes and vice versa. Helper functions provide ergonomic access:

```rust
// baml/baml_language/crates/baml_compiler_parser/src/lib.rs:41-53
pub fn parse_green(db: &dyn salsa::Database, file: SourceFile) -> GreenNode {
    parse_result(db, file).green(db)
}

pub fn parse_errors(db: &dyn salsa::Database, file: SourceFile) -> Vec<ParseError> {
    parse_result(db, file).errors(db)
}

pub fn syntax_tree(db: &dyn salsa::Database, file: SourceFile) -> SyntaxNode {
    SyntaxNode::new_root(parse_green(db, file))
}
```

## Stage 3: HIR Lowering — LoweringResult with Diagnostics

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:103-113
#[salsa::tracked]
pub struct LoweringResult<'db> {
    #[tracked]
    #[returns(ref)]
    pub item_tree: Arc<ItemTree>,
    #[tracked]
    #[returns(ref)]
    pub diagnostics: Vec<HirDiagnostic>,
}

// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:162-167
#[salsa::tracked]
pub fn file_lowering(db: &dyn Db, file: SourceFile) -> LoweringResult<'_> {
    let tree = syntax_tree(db, file);
    let file_id = file.file_id(db);
    let (item_tree, diagnostics) = lower_file_with_ctx(&tree, file_id);
    LoweringResult::new(db, Arc::new(item_tree), diagnostics)
}
```

**Convenience wrapper (not tracked):**

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:174-176
pub fn file_item_tree(db: &dyn Db, file: SourceFile) -> Arc<ItemTree> {
    file_lowering(db, file).item_tree(db).clone()
}
```

`file_item_tree` is NOT a tracked function — it's a convenience wrapper that calls the tracked `file_lowering` and clones the `Arc` (O(1)). This avoids adding a separate tracked function for a trivial extraction.

## Stage 4: Item Interning — Per-File then Per-Project

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:186-205
#[salsa::tracked]
pub fn file_items(db: &dyn Db, file: SourceFile) -> FileItems<'_> {
    let item_tree = file_item_tree(db, file);
    let items = intern_all_items(db, file, &item_tree);
    FileItems::new(db, items)
}

#[salsa::tracked]
pub fn project_items(db: &dyn Db, root: baml_workspace::Project) -> ProjectItems<'_> {
    let mut all_items = Vec::new();
    for file in root.files(db) {
        let items_struct = file_items(db, *file);
        all_items.extend(items_struct.items(db).iter().copied());
    }
    ProjectItems::new(db, all_items)
}
```

**The coarse-then-fine pattern:** `project_items` aggregates `file_items` across all files. When one file changes, only that file's `file_items` re-executes; `project_items` re-executes too but quickly because most `file_items` results are cached.

## The Signature / Body / Source-Map Triple Split

BAML's most sophisticated early cutoff strategy splits function metadata into three independently cached queries:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:251-278
#[salsa::tracked]
pub fn function_signature<'db>(
    db: &'db dyn Db, function: FunctionLoc<'db>,
) -> Arc<FunctionSignature> {
    let (signature, _source_map) = function_signature_with_source_map(db, function);
    signature
}

#[salsa::tracked]
pub fn function_signature_source_map<'db>(
    db: &'db dyn Db, function: FunctionLoc<'db>,
) -> SignatureSourceMap {
    let (_signature, source_map) = function_signature_with_source_map(db, function);
    source_map
}

#[salsa::tracked]
pub fn function_body<'db>(db: &'db dyn Db, function: FunctionLoc<'db>) -> Arc<FunctionBody> {
    // ... reads syntax tree, lowers function body
}
```

**How early cutoff works:**

1. Both `function_signature` and `function_signature_source_map` delegate to the same internal helper (`function_signature_with_source_map`)
2. When whitespace or comments change, `function_signature` returns an equal `Arc<FunctionSignature>` — Salsa's early cutoff kicks in and downstream queries like `function_type_inference` are NOT re-executed
3. `function_signature_source_map` returns updated spans — but only IDE queries (hover, go-to-def) depend on it, not type inference

**The consumer that benefits:**

```rust
// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:963-978
#[salsa::tracked]
pub fn function_type_inference<'db>(
    db: &'db dyn Db, function: FunctionLoc<'db>,
) -> Arc<InferenceResult> {
    // NOTE: We intentionally don't call function_signature_source_map here.
    // This allows Salsa early cutoff: when only whitespace/comments change,
    // function_signature returns an equal value, so this query is cached.
    let signature = baml_compiler_hir::function_signature(db, function);
    let body = baml_compiler_hir::function_body(db, function);
    // ... build context, run inference
}
```

## Stage 5: Type-Level Queries — Project-Wide Aggregation

```rust
// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:218-328
#[salsa::tracked]
pub fn enum_variants(db: &dyn Db, project: Project) -> EnumVariantsMap<'_> { /* ... */ }

#[salsa::tracked]
pub fn typing_context(db: &dyn Db, project: Project) -> TypingContextMap<'_> { /* ... */ }

#[salsa::tracked]
pub fn class_field_types(db: &dyn Db, project: Project) -> ClassFieldTypesMap<'_> { /* ... */ }

#[salsa::tracked]
pub fn type_aliases(db: &dyn Db, project: Project) -> TypeAliasesMap<'_> { /* ... */ }

#[salsa::tracked]
pub fn class_names(db: &dyn Db, project: Project) -> ClassNamesSet<'_> { /* ... */ }

#[salsa::tracked]
pub fn enum_names(db: &dyn Db, project: Project) -> EnumNamesSet<'_> { /* ... */ }

#[salsa::tracked]
pub fn type_alias_names(db: &dyn Db, project: Project) -> TypeAliasNamesSet<'_> { /* ... */ }
```

All take `Project` as input and aggregate across all files. Each returns a tracked struct wrapping a `HashMap` or `HashSet`. This is the "project-wide index" pattern — compute once, cache until any relevant file changes.

## Non-Salsa Context Struct for Bundling Query Results

```rust
// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:437-453
pub struct TypeResolutionContext {
    pub class_names: HashSet<Name>,
    pub enum_names: HashSet<Name>,
    pub type_alias_names: HashSet<Name>,
}

impl TypeResolutionContext {
    pub fn new(db: &dyn Db, project: Project) -> Self {
        Self {
            class_names: class_names(db, project).names(db).clone(),
            enum_names: enum_names(db, project).names(db).clone(),
            type_alias_names: type_alias_names(db, project).names(db).clone(),
        }
    }
}
```

**Pattern:** When a computation needs results from multiple tracked queries, bundle them into a plain struct. This avoids passing 3+ tracked struct references around. The context struct is NOT tracked — it's a short-lived convenience created inside other tracked functions.

## Per-Item Queries via Interned IDs

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:213-235
#[salsa::tracked]
pub fn function_generic_params(_db: &dyn Db, _func: FunctionId<'_>) -> Arc<GenericParams> { /* ... */ }

#[salsa::tracked]
pub fn class_generic_params(_db: &dyn Db, _class: ClassId<'_>) -> Arc<GenericParams> { /* ... */ }

#[salsa::tracked]
pub fn class_fields<'db>(db: &'db dyn Db, class: ClassLoc<'db>) -> ClassFields<'db> { /* ... */ }
```

**Granularity:** Per-item queries take an interned ID as input. When class A's fields change, queries depending on class B's fields are unaffected — Salsa tracks the dependency on the specific `ClassLoc`, not on all classes.

## Pipeline Summary

| Query | Input | Output | Layer | Notes |
|-------|-------|--------|-------|-------|
| `lex_file` | `SourceFile` | `Vec<Token>` | lexer | Base `salsa::Database` |
| `parse_result` | `SourceFile` | `ParseResult` (green + errors) | parser | Tracked struct split |
| `file_lowering` | `SourceFile` | `LoweringResult` (tree + diags) | HIR | Diagnostics in return value |
| `file_items` | `SourceFile` | `FileItems` (interned IDs) | HIR | Per-file granularity |
| `project_items` | `Project` | `ProjectItems` | HIR | Aggregation |
| `function_signature` | `FunctionLoc` | `Arc<FunctionSignature>` | HIR | Early cutoff split |
| `function_signature_source_map` | `FunctionLoc` | `SignatureSourceMap` | HIR | Early cutoff split |
| `function_body` | `FunctionLoc` | `Arc<FunctionBody>` | HIR | Most invalidated |
| `class_fields` | `ClassLoc` | `ClassFields` | HIR | Per-item |
| `typing_context` | `Project` | `TypingContextMap` | TIR | Project-wide index |
| `class_field_types` | `Project` | `ClassFieldTypesMap` | TIR | Project-wide index |
| `function_type_inference` | `FunctionLoc` | `Arc<InferenceResult>` | TIR | Per-function, early cutoff |
| `project_schema` | `Project` | `VirSchema` | VIR | Final output for codegen |
