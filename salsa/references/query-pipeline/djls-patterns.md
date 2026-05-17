# django-language-server — Simplest Complete Query Pipeline

The most approachable production example of a Salsa query pipeline: ~12 tracked functions across 5 crates, with accumulators, tracked methods on inputs, and filesystem-walking queries.

## Pipeline Diagram

```
File (input)
  │
  ├── file.source()        (tracked method — reads revision for dependency)
  │     │
  │     └── parse_template()        (tracked fn, returns Option<NodeList>)
  │           │                      (accumulates TemplateErrorAccumulator)
  │           │
  │           ├── build_block_tree()       (tracked fn, returns BlockTree)
  │           │     │                       (accumulates ValidationErrorAccumulator)
  │           │     └── build_semantic_forest()  (tracked fn, returns SemanticForest)
  │           │
  │           └── validate_nodelist()      (tracked fn, orchestrator)
  │                 └── validate_all_tag_arguments()  (accumulates ValidationErrorAccumulator)
  │
  └── file.line_index()    (tracked method, returns(ref) LineIndex)

Project (input)
  ├── django_available()   (tracked fn — Python subprocess query)
  ├── template_dirs()      (tracked fn — Python subprocess query)
  └── templatetags()       (tracked fn — Python subprocess query)

Cross-file:
  discover_templates()     (tracked fn — walks filesystem directories)
    ├── find_template()    (tracked fn — lookup by TemplateName)
    └── template_reference_index()  (tracked fn — all extends/include refs)
```

## Tracked Methods on Input Structs

django-language-server uses `#[salsa::tracked]` methods directly on the `File` input struct — a clean pattern for deriving computed state from inputs:

```rust
// django-language-server/crates/djls-source/src/file.rs
#[salsa::input]
pub struct File {
    #[returns(ref)]
    pub path: Utf8PathBuf,
    pub revision: u64,
}

#[salsa::tracked]
impl File {
    #[salsa::tracked]
    pub fn source(self, db: &dyn Db) -> SourceText {
        let _ = self.revision(db);  // Create dependency on revision
        let path = self.path(db);
        let source = db.read_file(path).unwrap_or_default();
        SourceText::new(path, source)
    }

    #[salsa::tracked(returns(ref))]
    pub fn line_index(self, db: &dyn Db) -> LineIndex {
        let text = self.source(db);
        LineIndex::from(text.as_str())
    }
}
```

**Key insight:** `self.revision(db)` doesn't use the revision value — it reads it solely to register a dependency. When the LSP layer bumps the revision, Salsa knows `source()` needs re-execution. This is simpler than ty's approach of storing modification timestamps and content hashes.

## Template Parsing Stage

```rust
// django-language-server/crates/djls-templates/src/lib.rs
#[salsa::tracked]
pub fn parse_template(db: &dyn Db, file: File) -> Option<NodeList<'_>> {
    let source = file.source(db);
    if *source.kind() != FileKind::Template {
        return None;
    }

    let (nodes, errors) = parse_template_impl(source.as_ref());

    // Accumulate parse errors via Salsa
    for error in errors {
        let template_error = TemplateError::Parser(error.to_string());
        TemplateErrorAccumulator(template_error).accumulate(db);
    }

    Some(NodeList::new(db, nodes))
}
```

**Notable:** Returns `Option<NodeList>` to handle non-template files. Accumulates errors as a side channel while still returning a usable (partial) AST.

## Semantic Analysis Stage

```rust
// django-language-server/crates/djls-semantic/src/lib.rs
#[salsa::tracked]
pub fn validate_nodelist(db: &dyn Db, nodelist: djls_templates::NodeList<'_>) {
    if nodelist.nodelist(db).is_empty() {
        return;
    }

    let block_tree = build_block_tree(db, nodelist);
    let _forest = build_semantic_forest(db, block_tree, nodelist);
    validate_all_tag_arguments(db, nodelist);
}

// django-language-server/crates/djls-semantic/src/blocks.rs
#[salsa::tracked]
pub fn build_block_tree<'db>(
    db: &'db dyn Db,
    nodelist: djls_templates::NodeList<'db>,
) -> BlockTree<'db> {
    let builder = BlockTreeBuilder::new(db, db.tag_index());
    builder.model(db, nodelist)
}

// django-language-server/crates/djls-semantic/src/semantic.rs
#[salsa::tracked]
pub fn build_semantic_forest<'db>(
    db: &'db dyn Db,
    tree: BlockTree<'db>,
    nodelist: djls_templates::NodeList<'db>,
) -> SemanticForest<'db> {
    // ... builds semantic tree from block tree ...
}
```

**Pipeline shape:** `parse_template` → `validate_nodelist` → (`build_block_tree` + `build_semantic_forest` + `validate_all_tag_arguments`). The validate function orchestrates three parallel analysis passes.

## Cross-File Template Resolution

```rust
// django-language-server/crates/djls-semantic/src/resolution/templates.rs

/// Walk filesystem to discover all templates — depends on template_dirs()
#[salsa::tracked]
pub fn discover_templates(db: &dyn SemanticDb) -> Vec<Template<'_>> {
    if let Some(search_dirs) = db.template_dirs() {
        // Walk directories, create Template tracked structs for each .html file
        // ...
    }
}

/// Look up a template by interned name
#[salsa::tracked]
pub fn find_template<'db>(
    db: &'db dyn SemanticDb,
    template_name: TemplateName<'db>,
) -> Option<Template<'db>> {
    let templates = discover_templates(db);
    templates.iter().find(|t| t.name(db) == template_name).copied()
}

/// Build index of all extends/include references across all templates
#[salsa::tracked]
fn template_reference_index(db: &dyn SemanticDb) -> Vec<TemplateReference<'_>> {
    let templates = discover_templates(db);
    // For each template, parse and find {% extends %} and {% include %} tags
    // Create TemplateReference tracked structs
    // ...
}
```

**Filesystem-walking tracked function:** `discover_templates` walks directories returned by `template_dirs()` (a Python subprocess query). This creates a dependency chain: Django settings → template dirs → discovered templates → template references. Changing Django settings can invalidate the entire template resolution graph.

## External System Queries (Python Inspector)

```rust
// django-language-server/crates/djls-project/src/django.rs

#[salsa::tracked]
pub fn django_available(db: &dyn ProjectDb, _project: Project) -> bool {
    inspector::query(db, &DjangoInitRequest).is_some()
}

#[salsa::tracked]
pub fn template_dirs(db: &dyn ProjectDb, _project: Project) -> Option<TemplateDirs> {
    let response = inspector::query(db, &TemplateDirsRequest)?;
    // ...
}

#[salsa::tracked]
pub fn templatetags(db: &dyn ProjectDb, _project: Project) -> Option<TemplateTags> {
    let response = inspector::query(db, &TemplatetagsRequest)?;
    // ...
}
```

These tracked functions call out to a Python subprocess (the "inspector") to query Django's runtime configuration. The `Project` input parameter creates a dependency — when project settings change, these queries re-execute and fetch fresh data from Python.

## Diagnostic Collection (IDE Layer)

```rust
// django-language-server/crates/djls-ide/src/diagnostics.rs
pub fn collect_diagnostics(
    db: &dyn djls_semantic::Db,
    file: File,
    nodelist: Option<djls_templates::NodeList<'_>>,
) -> Vec<ls_types::Diagnostic> {
    // Collect parse errors via accumulator
    let template_errors =
        djls_templates::parse_template::accumulated::<TemplateErrorAccumulator>(db, file);

    // Collect validation errors via accumulator
    if let Some(nodelist) = nodelist {
        let validation_errors = djls_semantic::validate_nodelist::accumulated::<
            djls_semantic::ValidationErrorAccumulator,
        >(db, nodelist);
        // ...
    }
    // Convert to LSP diagnostics with severity filtering
}
```

**Single collection point:** All accumulators are collected at the IDE layer, not in the semantic analysis. This keeps the semantic layer focused on pushing errors and the IDE layer focused on presentation (severity, filtering, LSP conversion).

## Pipeline by Crate (django-language-server, github.com/joshuadavidthomas/django-language-server)

| Crate | Tracked Functions |
|-------|-------------------|
| `djls-source` | `File::source`, `File::line_index` (tracked methods on input) |
| `djls-templates` | `parse_template` (parsing + error accumulation) |
| `djls-semantic` | `validate_nodelist`, `build_block_tree`, `build_semantic_forest`, `discover_templates`, `find_template`, `template_reference_index` |
| `djls-project` | `django_available`, `template_dirs`, `templatetags` |
| `djls-ide` | `collect_diagnostics` (not tracked — collects accumulators) |
