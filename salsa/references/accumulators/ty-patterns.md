# ty — Why They Chose Return-Value Diagnostics

How ty (the Python type checker) handles diagnostics without Salsa accumulators.

## ty — Why They Chose Return-Value Diagnostics

### The InferContext Pattern (ty_python_semantic)

ty collects diagnostics through an `InferContext` that uses `RefCell` for interior mutability:

```rust
// ruff/crates/ty_python_semantic/src/types/context.rs
pub(crate) struct InferContext<'db, 'ast> {
    db: &'db dyn Db,
    scope: ScopeId<'db>,
    file: File,
    module: &'ast ParsedModuleRef,
    diagnostics: std::cell::RefCell<TypeCheckDiagnostics>,
    bomb: DebugDropBomb,  // prevents forgetting to call finish()
}
```

The `DebugDropBomb` is a safety mechanism — if you drop `InferContext` without calling `.finish()`, it panics in debug mode, preventing accidental diagnostic loss.

### Guard-Based Diagnostic API (ty_python_semantic)

ty uses RAII guards for diagnostic creation, which handles suppression checking automatically:

```rust
// Reporting a diagnostic
let Some(builder) = context.report_lint(&INVALID_ASSIGNMENT, target) else {
    return;  // suppressed by # type: ignore or similar
};
let mut diag = builder.into_diagnostic("Cannot assign to ...");
diag.set_primary_message("...");
// Diagnostic automatically added when guard drops
```

The `report_lint` method returns `None` if the lint is suppressed at that location. The guard's `Drop` impl adds the diagnostic and records which suppression was used.

### Explicit Merging from Nested Queries

When a scope's inference calls a nested query, it explicitly merges the nested diagnostics:

```rust
// ruff/crates/ty_python_semantic/src/types/infer/builder.rs
fn extend_definition(&mut self, inference: &DefinitionInference<'db>) {
    if let Some(extra) = &inference.extra {
        self.context.extend(&extra.diagnostics);  // merge diagnostics
        // ... also merge other extra data
    }
}
```

This is more verbose than accumulators but gives complete control over the data flow.

### The Top-Level Collector

```rust
// ruff/crates/ty_python_semantic/src/types.rs
pub fn check_types(db: &dyn Db, file: File) -> Vec<Diagnostic> {
    let index = semantic_index(db, file);
    let mut diagnostics = TypeCheckDiagnostics::default();

    for scope_id in index.scope_ids() {
        let result = infer_scope_types(db, scope_id, TypeContext::default());
        if let Some(scope_diagnostics) = result.diagnostics() {
            diagnostics.extend(scope_diagnostics);
        }
    }

    // Also add semantic syntax errors
    diagnostics.extend_diagnostics(
        index.semantic_syntax_errors().iter()
            .map(|error| Diagnostic::invalid_syntax(file, error, error)),
    );

    let diagnostics = check_suppressions(db, file, diagnostics);
    diagnostics
}
```

### Performance Rationale

From ty's commit history (Dec 2024):

> Salsa adds an "untracked" dependency to every query reading accumulated values. This has the effect that the query re-runs on every revision. For example, a possible future query `unused_suppression_comments(db, file)` would re-run on every incremental change and for every file.
>
> Salsa collects the accumulated values by traversing the entire query dependency graph. It can skip over sub-graphs if it is known that they contain no accumulated values. This makes accumulators a great tool for when they are rare; diagnostics are a good example. Unfortunately, suppressions are more common, and they often appear in many different files.

