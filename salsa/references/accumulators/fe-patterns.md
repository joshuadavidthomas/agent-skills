# Fe — Hybrid Accumulator + Return-Value Diagnostics

Fe (github.com/argotorg/fe) is the only surveyed project using BOTH Salsa accumulators and return-value diagnostics.

## Accumulators for Parse-Phase Errors

Two accumulators for errors during AST lowering to HIR:

```rust
#[salsa::accumulator]
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ParserError {
    pub file: File,
    pub error: parser::ParseError,
}

#[salsa::accumulator]
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SelectorError {
    pub kind: SelectorErrorKind,
    pub file: common::file::File,
    pub primary_range: parser::TextRange,
}
```

Pushed during tracked function execution:

```rust
#[salsa::tracked]
pub fn parse_file_impl<'db>(db: &'db dyn HirDb, top_mod: TopLevelMod<'db>) -> GreenNode {
    let file = top_mod.file(db);
    let text = file.text(db);
    let (node, parse_errors) = parser::parse_source_file(text);

    for error in parse_errors {
        ParserError { file, error }.accumulate(db);
    }
    node
}
```

## DiagnosticVoucher — Lazy Span Resolution for Return-Value Diagnostics

Analysis-phase diagnostics use the `DiagnosticVoucher` trait, which stores errors WITHOUT span information to avoid cache invalidation. Spans are resolved lazily only at display time:

```rust
/// All diagnostics accumulated in salsa-db should implement
/// [`DiagnosticVoucher`] which defines the conversion into
/// [`CompleteDiagnostic`].
///
/// All types that implement `DiagnosticVoucher` must NOT have a span
/// information which invalidates cache in salsa-db. Instead, all
/// information is given by [`SpannedHirDb`] to allow evaluating span lazily.
///
/// The reason we use `DiagnosticVoucher` is that we want to evaluate span
/// lazily to avoid invalidating cache in salsa-db.
pub trait DiagnosticVoucher: Send + Sync {
    fn to_complete(&self, db: &dyn SpannedHirAnalysisDb) -> CompleteDiagnostic;
}

impl DiagnosticVoucher for CompleteDiagnostic {
    fn to_complete(&self, _db: &dyn SpannedHirAnalysisDb) -> CompleteDiagnostic {
        self.clone()
    }
}
```

**Key insight:** `to_complete()` takes `&dyn SpannedHirAnalysisDb`, not `&dyn HirAnalysisDb`. The `SpannedHirAnalysisDb` marker trait gates access to span-dependent information:

```rust
#[salsa::db]
pub trait SpannedHirAnalysisDb:
    salsa::Database + crate::HirDb + crate::SpannedHirDb + HirAnalysisDb
{
}

#[salsa::db]
impl<T> SpannedHirAnalysisDb for T where T: HirAnalysisDb + SpannedHirDb {}
```

Analysis tracked functions take `&dyn HirAnalysisDb` (no span access), while diagnostic rendering takes `&dyn SpannedHirAnalysisDb`. This enforces position-independent caching by construction.

## AnalysisPassManager — Collecting Both Kinds

The `AnalysisPassManager` provides a unified collection interface over both accumulator-based and return-value diagnostics:

```rust
pub trait ModuleAnalysisPass {
    fn run_on_module<'db>(
        &mut self,
        db: &'db dyn HirAnalysisDb,
        top_mod: TopLevelMod<'db>,
    ) -> Vec<Box<dyn DiagnosticVoucher + 'db>>;
}

#[derive(Default)]
pub struct AnalysisPassManager {
    module_passes: Vec<Box<dyn ModuleAnalysisPass>>,
}

impl AnalysisPassManager {
    pub fn run_on_module<'db>(
        &mut self,
        db: &'db dyn HirAnalysisDb,
        top_mod: TopLevelMod<'db>,
    ) -> Vec<Box<dyn DiagnosticVoucher + 'db>> {
        let mut diags = vec![];
        for pass in self.module_passes.iter_mut() {
            diags.extend(pass.run_on_module(db, top_mod));
        }
        diags
    }

    pub fn run_on_module_tree<'db>(
        &mut self,
        db: &'db dyn HirAnalysisDb,
        tree: &'db ModuleTree<'db>,
    ) -> Vec<Box<dyn DiagnosticVoucher + 'db>> {
        let mut diags = vec![];
        for module in tree.all_modules() {
            for pass in self.module_passes.iter_mut() {
                diags.extend(pass.run_on_module(db, module));
            }
        }
        diags
    }
}
```

Parse-phase passes collect accumulated diagnostics; analysis passes return diagnostics directly:

```rust
// Accumulator-based pass — collects from tracked function
impl ModuleAnalysisPass for ParsingPass {
    fn run_on_module<'db>(
        &mut self,
        db: &'db dyn HirAnalysisDb,
        top_mod: TopLevelMod<'db>,
    ) -> Vec<Box<dyn DiagnosticVoucher>> {
        parse_file_impl::accumulated::<ParserError>(db, top_mod)
            .into_iter()
            .map(|d| Box::new(d.clone()) as _)
            .collect::<Vec<_>>()
    }
}

impl ModuleAnalysisPass for MsgLowerPass {
    fn run_on_module<'db>(
        &mut self,
        db: &'db dyn HirAnalysisDb,
        top_mod: TopLevelMod<'db>,
    ) -> Vec<Box<dyn DiagnosticVoucher>> {
        scope_graph_impl::accumulated::<SelectorError>(db, top_mod)
            .into_iter()
            .map(|d| Box::new(d.clone()) as _)
            .collect::<Vec<_>>()
    }
}

// Return-value analysis passes (DefConflict, Import, AdtDef, TypeAlias,
// Trait, Impl, ImplTrait, Func, Body, Contract, MsgSelector) each implement
// ModuleAnalysisPass and return Vec<Box<dyn DiagnosticVoucher>> directly.
```

## Production Database — Ordered Pass Registration

```rust
fn initialize_analysis_pass() -> AnalysisPassManager {
    let mut pass_manager = AnalysisPassManager::new();
    // Accumulator-based passes first
    pass_manager.add_module_pass(Box::new(ParsingPass {}));
    pass_manager.add_module_pass(Box::new(MsgLowerPass {}));
    pass_manager.add_module_pass(Box::new(MsgSelectorAnalysisPass {}));
    // Return-value analysis passes
    pass_manager.add_module_pass(Box::new(DefConflictAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(ImportAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(AdtDefAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(TypeAliasAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(TraitAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(ImplAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(ImplTraitAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(FuncAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(BodyAnalysisPass {}));
    pass_manager.add_module_pass(Box::new(ContractAnalysisPass {}));
    pass_manager
}
```

## Lazy Finalization with Span Resolution

`DiagnosticsCollection` holds vouchers and resolves spans only when displaying:

```rust
pub struct DiagnosticsCollection<'db>(Vec<Box<dyn DiagnosticVoucher + 'db>>);

impl DiagnosticsCollection<'_> {
    fn finalize(&self, db: &DriverDataBase) -> Vec<CompleteDiagnostic> {
        let mut diags: Vec<_> = self.0.iter().map(|d| d.as_ref().to_complete(db)).collect();
        diags.sort_by(|lhs, rhs| match lhs.error_code.cmp(&rhs.error_code) {
            std::cmp::Ordering::Equal => lhs.primary_span().cmp(&rhs.primary_span()),
            ord => ord,
        });
        diags
    }
}
```

`to_complete(db)` is where spans are finally resolved — the `db` parameter provides access to span-dependent information through the `SpannedHirAnalysisDb` trait. This means all cached analysis results are position-independent, and only the final display step touches span data.
