# Cairo — Multi-Layer Diagnostic Aggregation via Return Values

Cairo has the most sophisticated return-value diagnostic system among surveyed Salsa codebases. With zero accumulators, it uses a 4-level tracked function aggregation pipeline to collect diagnostics from 285+ tracked functions across 8 compiler layers.

## Architecture: Diagnostic Aggregation Pyramid

```
DiagnosticsReporter.check()              ← Non-Salsa: walks crates, formats output
  ├── file_syntax_diagnostics(file_id)    ← Per-file parser diagnostics
  ├── module_semantic_diagnostics(mod_id) ← Aggregates all per-item semantic diagnostics
  │     ├── free_function_declaration_diagnostics(fn_id)
  │     ├── free_function_body_diagnostics(fn_id)
  │     ├── struct_declaration_diagnostics(struct_id)
  │     ├── struct_definition_diagnostics(struct_id)
  │     ├── trait_semantic_declaration_diagnostics(trait_id)
  │     ├── trait_semantic_definition_diagnostics(trait_id)
  │     ├── impl_semantic_declaration_diagnostics(impl_id)
  │     ├── impl_semantic_definition_diagnostics(impl_id)
  │     ├── enum_declaration_diagnostics(enum_id)
  │     ├── enum_definition_diagnostics(enum_id)
  │     ├── use_semantic_diagnostics(use_id)
  │     ├── extern_function_declaration_diagnostics(fn_id)
  │     ├── extern_type_declaration_diagnostics(type_id)
  │     └── macro_declaration_diagnostics(macro_id)
  └── module_lowering_diagnostics(mod_id)  ← Aggregates all per-function lowering diagnostics
        ├── semantic_function_with_body_lowering_diagnostics(fn_id)
        │     ├── function_with_body_lowering_diagnostics(fn_id)    ← base function
        │     └── function_with_body_lowering_diagnostics(gen_id)   ← generated functions
        └── ... (same for impl methods, trait methods, etc.)
```

Every level in this pyramid is a tracked function. Salsa caches each level independently — changing one function body only re-runs that function's diagnostics and the module-level aggregation, not diagnostics for other functions.

## Per-Item Diagnostic Split: Declaration vs Definition

Cairo's key insight: separate errors from an item's **header** (type signature, generics, visibility) from errors in its **body** (implementation, field types, method bodies):

```rust
// Per-item: two separate tracked functions per item type
#[salsa::tracked(returns(ref))]
fn free_function_declaration_diagnostics(db: &dyn Database, id: FreeFunctionId)
    -> Diagnostics<SemanticDiagnostic> { ... }

#[salsa::tracked(returns(ref))]
fn free_function_body_diagnostics(db: &dyn Database, id: FreeFunctionId)
    -> Diagnostics<SemanticDiagnostic> { ... }
```

The payoff: changing a function's body only re-runs body diagnostics. If nothing in the header changed, declaration diagnostics are cached. For items like impls with many methods, this avoids re-checking the impl header when only one method body changes.

## Module-Level Aggregation: The Item Walker

The module diagnostic query walks all items and merges their diagnostics:

```rust
#[salsa::tracked]
fn module_semantic_diagnostics(
    db: &dyn Database,
    module_id: ModuleId,
) -> Maybe<Diagnostics<SemanticDiagnostic>> {
    let mut diagnostics = SemanticDiagnostics::new(module_id);

    // Plugin diagnostics (from macro expansion, etc.)
    for (_module_id, plugin_diag) in module_id.module_data(db)?.plugin_diagnostics(db).iter().cloned() {
        diagnostics.report(plugin_diag.stable_ptr,
            SemanticDiagnosticKind::PluginDiagnostic(plugin_diag));
    }

    // Per-item diagnostics — match on every item type
    for item in module_id.module_data(db)?.items(db).iter() {
        match item {
            ModuleItemId::FreeFunction(f) => {
                diagnostics.extend(db.free_function_declaration_diagnostics(*f));
                diagnostics.extend(db.free_function_body_diagnostics(*f));
            }
            ModuleItemId::Struct(s) => {
                diagnostics.extend(db.struct_declaration_diagnostics(*s));
                diagnostics.extend(db.struct_definition_diagnostics(*s));
            }
            ModuleItemId::Enum(e) => {
                diagnostics.extend(db.enum_definition_diagnostics(*e));
                diagnostics.extend(db.enum_declaration_diagnostics(*e));
            }
            ModuleItemId::Trait(t) => {
                diagnostics.extend(db.trait_semantic_declaration_diagnostics(*t));
                diagnostics.extend(db.trait_semantic_definition_diagnostics(*t));
            }
            ModuleItemId::Impl(i) => {
                diagnostics.extend(db.impl_semantic_declaration_diagnostics(*i));
                diagnostics.extend(db.impl_semantic_definition_diagnostics(*i));
            }
            // ... 6+ more item types (Use, ExternType, ExternFunction, Constant, etc.)
        }
    }
    Ok(diagnostics.build())
}
```

The same pattern repeats for the lowering layer, but aggregates function-level lowering diagnostics:

```rust
#[salsa::tracked]
fn module_lowering_diagnostics(
    db: &dyn Database,
    _tracked: Tracked,
    module_id: ModuleId,
) -> Maybe<Diagnostics<LoweringDiagnostic>> {
    let mut diagnostics = DiagnosticsBuilder::default();
    for item in module_id.module_data(db)?.items(db).iter() {
        match item {
            ModuleItemId::FreeFunction(f) => {
                let function_id = FunctionWithBodyId::Free(*f);
                diagnostics.extend(db.semantic_function_with_body_lowering_diagnostics(function_id)?);
            }
            ModuleItemId::Impl(i) => {
                // Walk all impl functions
                for impl_func in db.impl_functions(*i)?.values() {
                    let function_id = FunctionWithBodyId::Impl(*impl_func);
                    diagnostics.extend(
                        db.semantic_function_with_body_lowering_diagnostics(function_id)?
                    );
                }
            }
            // ... trait methods, etc.
        }
    }
    Ok(diagnostics.build())
}
```

## Top-Level Collection: DiagnosticsReporter

The final layer is a non-Salsa `DiagnosticsReporter` struct with a builder API:

```rust
pub struct DiagnosticsReporter<'a> {
    callback: Option<Box<dyn DiagnosticCallback + 'a>>,
    ignore_all_warnings: bool,
    ignore_warnings_crate_ids: Vec<CrateInput>,
    crates: Option<Vec<CrateInput>>,       // None = all crates
    allow_warnings: bool,
    skip_lowering_diagnostics: bool,
}

impl DiagnosticsReporter<'_> {
    pub fn stderr() -> Self { ... }
    pub fn write_to_string(string: &mut String) -> Self { ... }
    pub fn callback(f: impl FnMut(FormattedDiagnosticEntry)) -> Self { ... }
    pub fn with_crates(self, crates: &[CrateInput]) -> Self { ... }
    pub fn allow_warnings(self) -> Self { ... }
    pub fn skip_lowering_diagnostics(self) -> Self { ... }
}
```

The `check()` method walks all crates → all modules → collects syntax + semantic + lowering diagnostics:

```rust
pub fn check(&mut self, db: &dyn Database) -> bool {
    let mut found_diagnostics = false;
    for crate_input in &self.crates_of_interest(db) {
        let crate_id = crate_input.clone().into_crate_long_id(db).intern(db);
        let modules = db.crate_modules(crate_id);
        for module_id in modules.iter() {
            // Phase 1: Syntax diagnostics per file (parser layer)
            for file_id in db.module_files(*module_id)?.iter() {
                found_diagnostics |= self.check_diag_group(
                    db, db.file_syntax_diagnostics(*file_id).clone(), ...);
            }
            // Phase 2: Semantic diagnostics per module
            if let Ok(group) = db.module_semantic_diagnostics(*module_id) {
                found_diagnostics |= self.check_diag_group(db, group, ...);
            }
            // Phase 3: Lowering diagnostics per module (optional)
            if !self.skip_lowering_diagnostics {
                if let Ok(group) = db.module_lowering_diagnostics(*module_id) {
                    found_diagnostics |= self.check_diag_group(db, group, ...);
                }
            }
        }
    }
    found_diagnostics
}
```

## Parallel Warmup

Cairo pre-computes diagnostics in parallel before the reporter's sequential walk:

```rust
pub fn ensure_diagnostics(
    db: &dyn CloneableDatabase,
    reporter: &mut DiagnosticsReporter<'_>,
) -> Result<(), DiagnosticsError> {
    if should_warmup() {
        let crates = reporter.crates_of_interest(db);
        rayon::join(
            move || warmup_diagnostics_blocking(db.dyn_clone().as_ref(), crates),
            move || reporter.ensure(db.dyn_clone().as_ref()),
        ).1
    } else {
        reporter.ensure(db)
    }
}
```

The warmup thread pre-populates the Salsa cache (`file_syntax_diagnostics`, `module_semantic_diagnostics`, `module_lowering_diagnostics`) so the reporter finds cached results.

## Comparison with Other Return-Value Approaches

| Aspect | Cairo | ty | rust-analyzer | BAML |
|--------|-------|-----|---------------|------|
| Granularity | Per-item split (decl vs def) | Per-scope | Per-body | Per-file |
| Aggregation | 4 tracked fn levels | Manual in `check_types` | Non-Salsa methods | Centralized walker |
| Parallel collection | Rayon + CloneableDatabase | Not applicable (LSP) | Not applicable | Not applicable |
| Warning suppression | DiagnosticsReporter builder | `used_suppressions` in Extra | Inline ignore tracking | None |
| Diagnostic storage | `Diagnostics<T>` collection type | `TypeCheckDiagnostics` | `Vec<AnyDiagnostic>` | `Vec<HirDiagnostic>` |
| Phase separation | Syntax / Semantic / Lowering | Type inference only | HIR / Ty / Validation | Parse / HIR / Validate / Infer |

## Key Crates (Cairo, github.com/starkware-libs/cairo)

- `cairo-lang-parser` — `SyntaxData` tracked struct, `file_syntax` + `file_syntax_diagnostics`
- `cairo-lang-semantic` — per-item declaration/definition diagnostic split, `module_semantic_diagnostics` aggregation
- `cairo-lang-lowering` — `module_lowering_diagnostics` aggregation
- `cairo-lang-compiler` — `DiagnosticsReporter` builder + `check()`, parallel warmup via `ensure_diagnostics` + `warmup_diagnostics_blocking`
