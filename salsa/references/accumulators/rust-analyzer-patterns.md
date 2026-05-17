# rust-analyzer — Diagnostic Collection via Methods

How rust-analyzer handles diagnostics without Salsa accumulators.

## rust-analyzer — Diagnostic Collection via Methods

rust-analyzer uses a completely different pattern: explicit `diagnostics()` methods on HIR types.

### The AnyDiagnostic Enum

```rust
// rust-analyzer/crates/hir/src/diagnostics.rs
diagnostics![AnyDiagnostic<'db> ->
    AwaitOutsideOfAsync,
    BreakOutsideOfLoop,
    CastToUnsized<'db>,
    ExpectedFunction<'db>,
    InactiveCode,
    IncoherentImpl,
    IncorrectCase,
    InvalidCast<'db>,
    MacroError,
    MismatchedArgCount<'db>,
    MissingFields<'db>,
    MissingMatchArms<'db>,
    NeedMut<'db>,
    // ... 40+ diagnostic types
];
```

### Collection Methods on HIR Types

```rust
// rust-analyzer/crates/hir/src/lib.rs
impl Module {
    pub fn diagnostics(self, db: &dyn HirDatabase, acc: &mut Vec<AnyDiagnostic>) {
        // Walk all items in the module
        // For each: read cached query results, translate to diagnostics
    }
}

impl Function {
    pub fn diagnostics(self, db: &dyn HirDatabase, acc: &mut Vec<AnyDiagnostic>) {
        let body = db.body_with_source_map(self.id);
        // Read inference diagnostics from cached results
        // Run body validation (also returns diagnostics, not accumulates)
    }
}

impl GenericDef {
    pub fn diagnostics(self, db: &dyn HirDatabase, acc: &mut Vec<AnyDiagnostic>) {
        let source_map = /* fetch from db */;
        expr_store_diagnostics(db, acc, &source_map);
        push_ty_diagnostics(db, acc, db.generic_defaults_with_diagnostics(def).1, &source_map);
    }
}
```

### Key Pattern: Diagnostics Are Derived From Cached Query Results

rust-analyzer's diagnostic methods don't store diagnostics during inference. Instead, the inference result contains enough information to reconstruct diagnostics later:

```rust
// InferenceDiagnostic is stored in the InferenceResult (a query result)
pub enum InferenceDiagnostic {
    TypeMismatch { expr_or_pat: ExprOrPatId, expected: Ty, actual: Ty },
    BreakOutsideOfLoop { expr: ExprId, is_break: bool },
    // ...
}

// Diagnostic collection reads InferenceResult and converts
for d in infer.diagnostics.iter() {
    match d {
        InferenceDiagnostic::TypeMismatch { expr_or_pat, expected, actual } => {
            // Convert to AnyDiagnostic using source maps
            acc.push(TypeMismatch { /* ... */ }.into());
        }
        // ...
    }
}
```

This means the cached inference result contains a compact representation of diagnostics, and the full user-facing diagnostic (with source locations, message text, etc.) is constructed on demand.

## Summary: Three Approaches

| Approach | Used By | Complexity | Incremental Performance |
|----------|---------|------------|------------------------|
| `#[salsa::accumulator]` | Salsa calc example | Low | OK for small projects; untracked dependency on collection |
| Diagnostics in return values | ty | Medium | Good — diagnostics cached alongside results |
| Diagnostic methods on HIR types | rust-analyzer | High | Good — diagnostics derived from cached results on demand |
