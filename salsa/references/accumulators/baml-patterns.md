# BAML — Diagnostics via Return Values with Centralized Collection

Production diagnostic patterns from BAML (AI/LLM function compiler). Uses return-value diagnostics with a centralized collection function — no Salsa accumulators.

## The Approach: Multi-Phase Return-Value Collection

BAML embeds diagnostics in tracked function return values (like ty, rust-analyzer, and Cairo), then collects them in a single non-tracked function that walks all phases:

```
Phase 1: Parse errors         → parse_errors(db, file) → Vec<ParseError>
Phase 2: HIR lowering          → file_lowering(db, file).diagnostics(db) → Vec<HirDiagnostic>
Phase 3: Cross-file validation → validate_hir(db, project) → HirValidationResult
Phase 4: Type inference        → infer_function(db, ...) → InferenceResult { errors }
```

## LoweringResult: Diagnostics as Tracked Struct Field

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
```

Diagnostics are collected during lowering via a non-Salsa `LoweringContext`:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:127-148
struct LoweringContext {
    file_id: FileId,
    diagnostics: Vec<HirDiagnostic>,
}

impl LoweringContext {
    fn push_diagnostic(&mut self, diagnostic: HirDiagnostic) {
        self.diagnostics.push(diagnostic);
    }
    fn finish(self) -> Vec<HirDiagnostic> {
        self.diagnostics
    }
}
```

The tracked function packages both outputs:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:162-167
#[salsa::tracked]
pub fn file_lowering(db: &dyn Db, file: SourceFile) -> LoweringResult<'_> {
    let tree = syntax_tree(db, file);
    let file_id = file.file_id(db);
    let (item_tree, diagnostics) = lower_file_with_ctx(&tree, file_id);
    LoweringResult::new(db, Arc::new(item_tree), diagnostics)
}
```

## InferenceResult: Type Errors in Return Value

```rust
// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:462-480
pub struct InferenceResult {
    pub return_type: Ty,
    pub param_types: HashMap<Name, Ty>,
    pub expr_types: HashMap<ExprId, Ty>,
    pub errors: Vec<TirTypeError>,           // ← Diagnostics embedded here
    pub expr_resolutions: ResolutionMap,
    // ... additional fields for IDE features
}
```

## Position-Independent Error Locations

BAML's type errors use `ErrorLocation` instead of `Span` to survive whitespace changes:

```rust
// baml/baml_language/crates/baml_compiler_hir/src/source_map.rs (conceptual)
pub enum ErrorLocation {
    Expression(ExprId),         // Points to an expression in the body
    Statement(StmtId),          // Points to a statement
    Parameter(usize),           // Points to a parameter by index
    ReturnType,                 // Points to the return type annotation
    TypeItem(Name),             // Points to a type definition by name
}
```

`ErrorLocation` is resolved to a `Span` only at diagnostic display time, using source maps. This means type inference results remain cached even when whitespace changes — the `InferenceResult` compares equal because it contains `ErrorLocation`s (stable) not `Span`s (offset-sensitive).

## `collect_diagnostics()` — Centralized Collection Function

```rust
// baml/baml_language/crates/baml_project/src/check.rs:52-160
pub fn collect_diagnostics(
    db: &ProjectDatabase,
    project: Project,
    source_files: &[SourceFile],
) -> Vec<Diagnostic> {
    let mut diagnostics = Vec::new();
    let type_spans = project_type_item_spans(db, project);

    // Phase 1: Parse errors
    for source_file in source_files {
        let parse_errors = baml_compiler_parser::parse_errors(db, *source_file);
        for error in &parse_errors {
            diagnostics.push(error.to_diagnostic());
        }
    }

    // Phase 2: HIR lowering diagnostics (per-file validation)
    for source_file in source_files {
        let lowering_result = file_lowering(db, *source_file);
        for diag in lowering_result.diagnostics(db) {
            diagnostics.push(diag.to_diagnostic());
        }
    }

    // Phase 3: Cross-file validation (duplicates, reserved names)
    let validation_result = baml_compiler_hir::validate_hir(db, project);
    for diag in &validation_result.hir_diagnostics {
        diagnostics.push(diag.to_diagnostic());
    }
    for error in &validation_result.name_errors {
        diagnostics.push(error.to_diagnostic());
    }

    // Phase 3.5: Cycle detection (requires resolved types)
    let class_fields = class_field_types(db, project).classes(db).clone();
    let type_aliases_map = type_aliases(db, project).aliases(db).clone();
    // ... validate_type_alias_cycles, validate_class_cycles

    // Phase 4: Type errors from function inference
    for source_file in source_files {
        for item in file_items(db, *source_file).items(db) {
            if let ItemId::Function(func_loc) = item {
                let body = function_body(db, *func_loc);
                if let FunctionBody::Expr(expr_body, hir_source_map) = &*body {
                    let result = baml_compiler_tir::infer_function(db, ...);
                    for type_error in &result.errors {
                        diagnostics.push(type_error.to_diagnostic(
                            ToString::to_string,
                            |loc| loc.to_span(hir_source_map, &type_spans),
                        ));
                    }
                }
            }
        }
    }

    diagnostics
}
```

**Key design choice:** `collect_diagnostics()` is NOT a tracked function. It's called from `ProjectDatabase::check()` and the LSP server. This means it's not cached by Salsa — but the individual phases it calls (parse_result, file_lowering, file_items, infer_function) ARE cached. The collection itself is cheap; the expensive work is memoized.

## The `ToDiagnostic` Trait — Unified Conversion

```rust
// baml/baml_language/crates/baml_compiler_diagnostics/src/lib.rs (conceptual)
pub trait ToDiagnostic {
    fn to_diagnostic(&self) -> Diagnostic;
}

// For type errors with position-independent locations:
impl<Ctx: TypeErrorContext> TypeError<Ctx> {
    fn to_diagnostic(
        &self,
        format_type: impl Fn(&Ctx::Type) -> String,
        resolve_location: impl Fn(&Ctx::Location) -> Span,
    ) -> Diagnostic { /* ... */ }
}
```

Type errors carry generic contexts (`TirContext<Ty>`) that are resolved to concrete spans only during diagnostic display. The `resolve_location` closure looks up `ErrorLocation` → `Span` using the source map and type item spans.

## Usage from ProjectDatabase

```rust
// baml/baml_language/crates/baml_project/src/check.rs:168-196
impl ProjectDatabase {
    pub fn check(&self) -> CheckResult {
        let project = self.get_project().unwrap();
        let source_files: Vec<SourceFile> = self.files().collect();

        // Build file metadata for rendering
        let mut sources = HashMap::new();
        let mut file_paths = HashMap::new();
        for sf in &source_files {
            sources.insert(sf.file_id(self), sf.text(self).clone());
            file_paths.insert(sf.file_id(self), sf.path(self));
        }

        let diagnostics = collect_diagnostics(self, project, &source_files);
        CheckResult { diagnostics, sources, file_paths }
    }
}
```

## Comparison with Other Approaches

| Aspect | BAML | ty/rust-analyzer | Cairo | django-language-server |
|--------|------|------------------|-------|----------------------|
| Mechanism | Return values + centralized collection | Return values embedded in per-query results | 4-level tracked function pyramid | Salsa accumulators |
| Diagnostic location | `ErrorLocation` (IDs) → resolved to `Span` at display | `Span` or similar | Per-item tracked fns | Accumulated during traversal |
| Collection point | `collect_diagnostics()` (not tracked) | Per-query collection | Multi-level aggregation | `accumulator::accumulated()` |
| Phases | 4 (parse, HIR, validation, type inference) | Multiple per-query | Declaration + definition per item | 2 (template errors + validation) |
| Complexity | Medium | High | Highest | Simplest |
