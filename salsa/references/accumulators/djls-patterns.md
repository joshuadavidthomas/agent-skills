# django-language-server — Accumulators in Production

A Django template language server (~78 Rust files) that uses Salsa accumulators successfully for diagnostics. This is the most approachable real-world accumulator example — smaller than ty or rust-analyzer but production-quality.

## Two Accumulators for Two Diagnostic Phases

### Parse-Phase Accumulator

```rust
// django-language-server/crates/djls-templates/src/db.rs
#[salsa::accumulator]
pub struct TemplateErrorAccumulator(pub TemplateError);
```

Pushed from the `parse_template` tracked function:

```rust
// django-language-server/crates/djls-templates/src/lib.rs
#[salsa::tracked]
pub fn parse_template(db: &dyn Db, file: File) -> Option<NodeList<'_>> {
    let source = file.source(db);
    if *source.kind() != FileKind::Template {
        return None;
    }

    let (nodes, errors) = parse_template_impl(source.as_ref());

    // Accumulate any errors via Salsa
    for error in errors {
        let template_error = TemplateError::Parser(error.to_string());
        TemplateErrorAccumulator(template_error).accumulate(db);
    }

    Some(NodeList::new(db, nodes))
}
```

### Validation-Phase Accumulator

```rust
// django-language-server/crates/djls-semantic/src/db.rs
#[salsa::accumulator]
pub struct ValidationErrorAccumulator(pub ValidationError);
```

Pushed from multiple validation functions:

```rust
// django-language-server/crates/djls-semantic/src/arguments.rs
// 8+ push sites for different validation errors:
ValidationErrorAccumulator(ValidationError::TooManyArguments {
    tag: tag_name.to_string(),
    max: expected_count,
    got: argument_count,
    span,
}).accumulate(db);

ValidationErrorAccumulator(ValidationError::MissingRequiredArguments {
    tag: tag_name.to_string(),
    missing: missing_args,
    span,
}).accumulate(db);

ValidationErrorAccumulator(ValidationError::InvalidLiteralArgument {
    tag: tag_name.to_string(),
    value: value.clone(),
    expected: choices.clone(),
    span,
}).accumulate(db);
```

```rust
// django-language-server/crates/djls-semantic/src/blocks/builder.rs
// Block structure validation:
ValidationErrorAccumulator(error).accumulate(db);
```

### Collection at IDE Layer

```rust
// django-language-server/crates/djls-ide/src/diagnostics.rs
pub fn collect_diagnostics(
    db: &dyn djls_semantic::Db,
    file: File,
    nodelist: Option<djls_templates::NodeList<'_>>,
) -> Vec<ls_types::Diagnostic> {
    let mut diagnostics = Vec::new();
    let config = db.diagnostics_config();

    // Collect parse errors
    let template_errors =
        djls_templates::parse_template::accumulated::<TemplateErrorAccumulator>(db, file);
    let line_index = file.line_index(db);

    for error_acc in template_errors {
        let mut diagnostic = error_acc.0.as_diagnostic(line_index);
        if let Some(ls_types::NumberOrString::String(code)) = &diagnostic.code {
            let severity = config.get_severity(code);
            if let Some(lsp_severity) = severity.to_lsp_severity() {
                diagnostic.severity = Some(lsp_severity);
                diagnostics.push(diagnostic);
            }
        }
    }

    // Collect validation errors (only if parsing succeeded)
    if let Some(nodelist) = nodelist {
        let validation_errors = djls_semantic::validate_nodelist::accumulated::<
            djls_semantic::ValidationErrorAccumulator,
        >(db, nodelist);

        for error_acc in validation_errors {
            let mut diagnostic = error_acc.0.as_diagnostic(line_index);
            if let Some(ls_types::NumberOrString::String(code)) = &diagnostic.code {
                let severity = config.get_severity(code);
                if let Some(lsp_severity) = severity.to_lsp_severity() {
                    diagnostic.severity = Some(lsp_severity);
                    diagnostics.push(diagnostic);
                }
            }
        }
    }

    diagnostics
}
```

## Why Accumulators Work Here

1. **Single collection point** — `collect_diagnostics` is called only from LSP handlers (push diagnostics, pull diagnostics). It's never called from other queries, so the untracked dependency is harmless.

2. **Small file count** — Django projects have at most hundreds of templates. The overhead of re-collecting accumulated values per revision is negligible.

3. **No suppression tracking** — Django templates have no equivalent of `# type: ignore`, so there's no need to correlate diagnostics with suppressions.

4. **Clean phase separation** — Parse errors (`TemplateErrorAccumulator`) and semantic errors (`ValidationErrorAccumulator`) are separate accumulators with separate collection points, making the diagnostic pipeline clear.

5. **Severity filtering at collection** — The `DiagnosticsConfig` allows per-code severity overrides, and diagnostics with `severity = off` are filtered out during collection. This works naturally with accumulators since all filtering happens at the single collection point.

## Test Pattern for Accumulated Errors

```rust
// django-language-server/crates/djls-semantic/src/arguments.rs (tests)
// Collect accumulated errors, filtering out UnclosedTag errors (test setup issue)
crate::validate_nodelist::accumulated::<ValidationErrorAccumulator>(&db, nodelist)
    .into_iter()
    .filter(|e| !matches!(e.0, ValidationError::UnclosedTag { .. }))
    .collect::<Vec<_>>()
```

This shows accumulator collection in tests — straightforward and ergonomic.

## Architecture Summary (django-language-server, github.com/joshuadavidthomas/django-language-server)

| Crate | Role |
|-------|------|
| `djls-templates` | `TemplateErrorAccumulator` definition, `parse_template` pushes parse errors |
| `djls-semantic` | `ValidationErrorAccumulator` definition, argument + block validation pushes errors |
| `djls-ide` | `collect_diagnostics` — collects both accumulator types |
| `djls-server` | LSP handlers that call `collect_diagnostics` |
