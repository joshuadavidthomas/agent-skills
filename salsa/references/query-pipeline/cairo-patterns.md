# Cairo — Multi-Layer Query Pipeline with Trait Delegation

Production query pipeline patterns from Cairo (StarkNet smart contract language compiler). Cairo has 285+ tracked functions across 8 crate layers, making it the largest Salsa query pipeline among surveyed codebases.

## Pipeline Shape: 8-Layer Compiler Architecture

```
CrateInput / FileInput (plain Rust types, set via init functions)
  → FilesGroupInput (singleton input, Option<T> fields)
    → crate_configs, file_content, file_summary (tracked fns)

  → file_syntax_data (tracked fn, returns SyntaxData tracked struct)
    → file_syntax, file_syntax_diagnostics (split: AST vs diagnostics)

  → priv_module_data (tracked fn, per-module)
    → module_items, module_constants, module_submodules (per-item-kind)

  → per-item semantic queries (tracked fns, per item type)
    → free_function_declaration_diagnostics + free_function_body_diagnostics
    → struct_declaration_diagnostics + struct_definition_diagnostics
    → trait_semantic_declaration_diagnostics + trait_semantic_definition_diagnostics
    → impl_semantic_declaration_diagnostics + impl_semantic_definition_diagnostics

  → module_semantic_diagnostics (aggregates all per-item diagnostics)
    → file_semantic_diagnostics (aggregates per-module)

  → priv_function_with_body_multi_lowering (tracked fn, per-function)
    → function_with_body_lowering_diagnostics (per-function)
    → semantic_function_with_body_lowering_diagnostics (per semantic function + generated)
    → module_lowering_diagnostics (aggregates per-module)
    → file_lowering_diagnostics (aggregates per-file)

  → function_with_body_sierra (tracked fn, per-function)
    → Sierra program generation
```

## Trait Method → Tracked Function Delegation

Because Cairo uses blanket-impl group traits (`impl<T: Database + ?Sized> SemanticGroup for T {}`), all methods must delegate to free tracked functions via `self.as_dyn_database()`:

```rust
pub trait SemanticGroup: Database {
    fn module_semantic_diagnostics<'db>(
        &'db self,
        module_id: ModuleId<'db>,
    ) -> Maybe<Diagnostics<'db, SemanticDiagnostic<'db>>> {
        // Delegates to tracked function, inserting Tracked=() dummy
        module_semantic_diagnostics_tracked(self.as_dyn_database(), (), module_id)
    }

    fn file_semantic_diagnostics<'db>(
        &'db self,
        file_id: FileId<'db>,
    ) -> Maybe<Diagnostics<'db, SemanticDiagnostic<'db>>> {
        file_semantic_diagnostics(self.as_dyn_database(), file_id)
    }

    fn lookup_resolved_generic_item_by_ptr<'db>(
        &'db self,
        id: LookupItemId<'db>,
        ptr: ast::TerminalIdentifierPtr<'db>,
    ) -> Option<ResolvedGenericItem<'db>> {
        lookup_resolved_generic_item_by_ptr(self.as_dyn_database(), id, ptr)
    }
    // ... 100+ methods, each a one-liner delegation ...
}

impl<T: Database + ?Sized> SemanticGroup for T {}
```

This pattern creates an ergonomic API (`db.module_semantic_diagnostics(id)`) while keeping all implementations as free tracked functions. The trait serves as a namespace, not as an abstraction boundary.

**Key detail:** Some delegations insert the `Tracked = ()` dummy parameter to satisfy Salsa's first-argument optimization. 53 functions across the codebase use this pattern.

```rust
// Trait method omits Tracked:
fn module_semantic_diagnostics(&self, module_id: ModuleId) -> ... {
    module_semantic_diagnostics_tracked(self.as_dyn_database(), (), module_id)
    //                                                          ^^  inserted
}

// Tracked function requires it:
#[salsa::tracked]
fn module_semantic_diagnostics_tracked(
    db: &dyn Database,
    _tracked: Tracked,       // Always ()
    module_id: ModuleId,
) -> ... { ... }
```

## Parser Layer: Tracked Struct Split

The parser uses a tracked struct to separate the AST from diagnostics, enabling early cutoff:

```rust
// cairo-lang-parser/src/db.rs

#[salsa::tracked]
struct SyntaxData<'db> {
    diagnostics: Diagnostics<'db, ParserDiagnostic<'db>>,
    syntax: Maybe<SyntaxNode<'db>>,
}

// Single computation produces both
#[salsa::tracked(returns(ref))]
fn file_syntax_data(db: &dyn Database, file_id: FileId) -> SyntaxData {
    let mut diagnostics = DiagnosticsBuilder::default();
    let syntax = db.file_content(file_id).to_maybe().map(|s| match file_id.kind(db) {
        FileKind::Module => Parser::parse_file(db, &mut diagnostics, file_id, s).as_syntax_node(),
        FileKind::Expr => Parser::parse_file_expr(db, &mut diagnostics, file_id, s).as_syntax_node(),
        FileKind::StatementList => Parser::parse_file_statement_list(db, &mut diagnostics, file_id, s).as_syntax_node(),
    });
    SyntaxData::new(db, diagnostics.build(), syntax)
}

// Public queries extract fields — callers depend only on what they need
#[salsa::tracked]
fn file_syntax(db: &dyn Database, file_id: FileId) -> Maybe<SyntaxNode> {
    file_syntax_data(db, file_id).syntax(db)
}

#[salsa::tracked(returns(ref))]
fn file_syntax_diagnostics(db: &dyn Database, file_id: FileId) -> Diagnostics<ParserDiagnostic> {
    file_syntax_data(db, file_id).diagnostics(db)
}
```

This is Cairo's version of the signature/body/source-map split pattern. By storing both AST and diagnostics in a tracked struct but exposing them through separate tracked functions, queries that only need the AST don't depend on diagnostics.

## Declaration vs Definition Diagnostic Split

For items with complex structure (structs, enums, traits, impls), Cairo splits diagnostics into declaration (signature/header) and definition (body/members):

```rust
// Per-item diagnostic queries — separate granularity
db.free_function_declaration_diagnostics(free_function)  // Signature errors
db.free_function_body_diagnostics(free_function)          // Body errors
db.struct_declaration_diagnostics(struct_id)               // Struct header errors
db.struct_definition_diagnostics(struct_id)                // Struct field errors
db.trait_semantic_declaration_diagnostics(trait_id)         // Trait signature errors
db.trait_semantic_definition_diagnostics(trait_id)          // Trait method errors
db.impl_semantic_declaration_diagnostics(impl_def_id)      // Impl header errors
db.impl_semantic_definition_diagnostics(impl_def_id)       // Impl method errors
db.enum_declaration_diagnostics(enum_id)                   // Enum header errors
db.enum_definition_diagnostics(enum_id)                    // Enum variant errors
```

This split mirrors the signature/body split for types: changing a function's body re-runs only body diagnostics, not declaration diagnostics. Changing a struct's fields re-runs definition diagnostics but not declaration diagnostics.

## Multi-Layer Diagnostic Aggregation

Diagnostics flow upward through tracked function calls at each granularity level:

```
per-item diagnostic queries (finest grain)
  ↑ aggregated by
module_semantic_diagnostics (walks all items in module)
  ↑ aggregated by
file_semantic_diagnostics (walks all modules in file)
  ↑ collected by
DiagnosticsReporter.check() (walks all crates, formats + outputs)
```

Each level is a tracked function, so aggregation results are cached:

```rust
// Module-level aggregation — walks all items and collects their diagnostics
#[salsa::tracked]
fn module_semantic_diagnostics(
    db: &dyn Database,
    module_id: ModuleId,
) -> Maybe<Diagnostics<SemanticDiagnostic>> {
    let mut diagnostics = SemanticDiagnostics::new(module_id);
    // Plugin diagnostics first
    for (_module_id, plugin_diag) in module_id.module_data(db)?.plugin_diagnostics(db).iter().cloned() {
        diagnostics.report(plugin_diag.stable_ptr, SemanticDiagnosticKind::PluginDiagnostic(plugin_diag));
    }
    // Per-item diagnostics
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
            ModuleItemId::Impl(i) => {
                diagnostics.extend(db.impl_semantic_declaration_diagnostics(*i));
                diagnostics.extend(db.impl_semantic_definition_diagnostics(*i));
            }
            // ... 10+ more item types ...
        }
    }
    Ok(diagnostics.build())
}
```

The same pattern repeats for lowering diagnostics:

```rust
// Per-function → per-semantic-function → per-module → per-file
fn function_with_body_lowering_diagnostics(db, function_id) -> ...
fn semantic_function_with_body_lowering_diagnostics(db, _tracked, function_id) -> ...
fn module_lowering_diagnostics(db, _tracked, module_id) -> ...
fn file_lowering_diagnostics(db, file_id) -> ...
```

## Parallel Warmup Pipeline

Cairo uses `CloneableDatabase` + Rayon to pre-compute diagnostics in parallel:

```rust
pub fn ensure_diagnostics(
    db: &dyn CloneableDatabase,
    diagnostic_reporter: &mut DiagnosticsReporter<'_>,
) -> Result<(), DiagnosticsError> {
    if should_warmup() {
        let crates = diagnostic_reporter.crates_of_interest(db);
        let warmup_db = db.dyn_clone();
        let ensure_db = db.dyn_clone();
        rayon::join(
            move || warmup_diagnostics_blocking(warmup_db.as_ref(), crates),
            move || diagnostic_reporter.ensure(ensure_db.as_ref()),
        ).1
    } else {
        diagnostic_reporter.ensure(db)
    }
}

fn warmup_diagnostics_blocking(db: &dyn CloneableDatabase, crates: Vec<CrateInput>) {
    crates.into_par_iter().for_each_with(db.dyn_clone(), |db, crate_input| {
        let db = db.as_ref();
        let crate_id = crate_input.into_crate_long_id(db).intern(db);
        db.crate_modules(crate_id).into_par_iter().for_each_with(
            db.dyn_clone(),
            |db, module_id| {
                // Pre-compute syntax diagnostics per file
                for file_id in db.module_files(*module_id).unwrap_or_default().iter().copied() {
                    db.file_syntax_diagnostics(file_id);
                }
                // Pre-compute semantic and lowering diagnostics per module
                let _ = db.module_semantic_diagnostics(*module_id);
                let _ = db.module_lowering_diagnostics(*module_id);
            },
        );
    });
}
```

The warmup runs in parallel (via `rayon::join`) with the actual diagnostic reporting. Both threads share the same database via `dyn_clone()`. The warmup pre-populates the Salsa cache so that the reporter's sequential walk finds cached results.

There's also a function-level warmup for Sierra generation:

```rust
fn warmup_functions_blocking(
    db: &dyn CloneableDatabase,
    requested_function_ids: Vec<ConcreteFunctionWithBodyId>,
) {
    let processed = &Mutex::new(UnorderedHashSet::<salsa::Id>::default());
    requested_function_ids.into_par_iter().for_each_with(db.dyn_clone(), move |db, func_id| {
        // Recursively warmup function and its callees
        fn handle_func_inner(
            processed: &Mutex<UnorderedHashSet<salsa::Id>>,
            db: &dyn CloneableDatabase,
            func_id: ConcreteFunctionWithBodyId,
        ) {
            if !processed.lock().unwrap().insert(func_id.into()) { return; }
            let _ = db.function_with_body_sierra(func_id);
            if let Ok(callees) = db.lowered_direct_callees_with_body(func_id, ...) {
                for callee in callees { handle_func_inner(processed, db, *callee); }
            }
        }
        handle_func_inner(processed, db.as_ref(), func_id);
    });
}
```

## `returns(ref)` as Default Style

Cairo uses `returns(ref)` on the vast majority of tracked functions — 183+ out of 285+. The convention is: if the return type is anything more than a scalar, use `returns(ref)`:

```rust
// Returns ref for all collection/struct types
#[salsa::tracked(returns(ref))]
fn crate_configs(db: &dyn Database) -> OrderedHashMap<CrateId, CrateConfiguration> { ... }

#[salsa::tracked(returns(ref))]
fn module_items(db: &dyn Database, module_id: ModuleId) -> Vec<ModuleItemId> { ... }

#[salsa::tracked(returns(ref))]
fn file_syntax_diagnostics(db: &dyn Database, file_id: FileId) -> Diagnostics<ParserDiagnostic> { ... }

// Default (clone) only for small types
#[salsa::tracked]
fn is_submodule_inline(db: &dyn Database, submodule_id: SubmoduleId) -> bool { ... }

#[salsa::tracked]
fn type_size(db: &dyn Database, ty: TypeId) -> usize { ... }
```

Cairo does NOT use `returns(deref)`, `returns(as_deref)`, or `returns(clone)`. The pattern is binary: `returns(ref)` for heap types, default for scalars.

## Pipeline Scale by Layer (Cairo, github.com/starkware-libs/cairo)

| Layer | Crate | Tracked Functions |
|-------|-------|-------------------|
| Filesystem | `cairo-lang-filesystem` | 20 (file content, crate config, flags) |
| Syntax | `cairo-lang-syntax` | 3 (green node interning) |
| Parser | `cairo-lang-parser` | 5 (parsing, diagnostics) |
| Definitions | `cairo-lang-defs` | 54 (module structure, item lookup) |
| Documentation | `cairo-lang-doc` | 4 (doc comments) |
| Semantic | `cairo-lang-semantic` | 147 (type checking, diagnostics) |
| Lowering | `cairo-lang-lowering` | 35 (IR lowering, optimization) |
| Sierra Gen | `cairo-lang-sierra-generator` | 16 (Sierra code gen) |
