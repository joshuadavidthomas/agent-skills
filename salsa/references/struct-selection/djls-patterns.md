# django-language-server — All Four Struct Types in One Project

The simplest complete real-world example of struct type selection. Every Salsa struct type is used exactly where it should be.

## Inputs (2)

```rust
// django-language-server/crates/djls-source/src/file.rs
#[salsa::input]
pub struct File {
    #[returns(ref)]
    pub path: Utf8PathBuf,
    /// Revision number bumped to invalidate cached queries
    pub revision: u64,
}

// django-language-server/crates/djls-project/src/project.rs
#[salsa::input]
#[derive(Debug)]
pub struct Project {
    #[returns(ref)]
    pub root: Utf8PathBuf,
    #[returns(ref)]
    pub interpreter: Interpreter,
    #[returns(ref)]
    pub settings_module: Option<String>,
    #[returns(ref)]
    pub pythonpath: Vec<Utf8PathBuf>,
}
```

**Design choice:** `File` uses a `revision: u64` field for invalidation instead of tracking modification timestamps or content hashes. The LSP layer bumps the revision on every document change, and the `source()` tracked method reads `self.revision(db)` to create a dependency — so any revision bump automatically invalidates the cached source text.

## Interned (1)

```rust
// django-language-server/crates/djls-semantic/src/primitives.rs
#[salsa::interned]
pub struct TemplateName {
    #[returns(ref)]
    pub name: String,
}
```

**Why interned?** Template names like `"base.html"` appear in `{% extends "base.html" %}` and `{% include "base.html" %}` across many files. Interning ensures O(1) equality comparison when resolving template references.

## Tracked Structs (7)

```rust
// django-language-server/crates/djls-semantic/src/primitives.rs
#[salsa::tracked]
pub struct Template<'db> {
    pub name: TemplateName<'db>,
    pub file: File,
}

#[salsa::tracked]
pub struct Tag<'db> {
    #[returns(ref)]
    pub name: String,
    #[returns(ref)]
    pub arguments: Vec<String>,
    pub span: Span,
}

// django-language-server/crates/djls-templates/src/nodelist.rs
#[salsa::tracked(debug)]
pub struct NodeList<'db> {
    #[tracked]
    #[returns(ref)]
    pub nodelist: Vec<Node>,
}

// django-language-server/crates/djls-semantic/src/blocks/tree.rs
#[salsa::tracked]
pub struct BlockTree<'db> {
    #[returns(ref)]
    pub roots: Vec<BlockId>,
    #[returns(ref)]
    pub blocks: Blocks,
}

// django-language-server/crates/djls-semantic/src/semantic/forest.rs
#[salsa::tracked]
pub struct SemanticForest<'db> {
    #[returns(ref)]
    pub roots: Vec<SemanticNode>,
    #[returns(ref)]
    pub tag_spans: Vec<Span>,
}

// django-language-server/crates/djls-semantic/src/blocks/grammar.rs
#[salsa::tracked(debug)]
pub struct TagIndex<'db> {
    #[tracked]
    #[returns(ref)]
    openers: FxHashMap<String, EndMeta>,
    #[tracked]
    #[returns(ref)]
    closers: FxHashMap<String, String>,
    #[tracked]
    #[returns(ref)]
    intermediate_to_openers: FxHashMap<String, Vec<String>>,
}

// django-language-server/crates/djls-semantic/src/resolution/templates.rs
#[salsa::tracked]
pub struct TemplateReference<'db> {
    pub source: Template<'db>,
    pub target: TemplateName<'db>,
    pub tag: Tag<'db>,
}
```

**Design choices:**
- `NodeList` wraps a `Vec<Node>` — the Vec of plain types is the tracked field. Changes to any node invalidate the whole list.
- `TagIndex` has 3 `#[tracked]` fields — if only openers change but closers don't, queries reading only closers won't re-execute.
- `TemplateReference` combines tracked (Template, Tag) and interned (TemplateName) fields — mixing struct types in one tracked struct.

## Plain Rust Types

```rust
// django-language-server/crates/djls-templates/src/nodelist.rs
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Node {
    Tag { name: String, bits: Vec<String>, span: Span },
    Comment { content: String, span: Span },
    Text { span: Span },
    Variable { var: String, filters: Vec<String>, span: Span },
    Error { span: Span, full_span: Span, error: ParseError },
}
```

**Why plain?** Individual AST nodes are too fine-grained to track. The parser produces a flat list of nodes — tracking each one would add more overhead than re-parsing. The tracking boundary is at the `NodeList` level: the entire node list is one tracked field.

Similarly, `BlockId`, `BlockNode`, `Blocks`, `Span`, `SemanticNode`, `BranchKind`, `EndMeta`, `TagClass`, `CloseValidation`, and all error types are plain Rust types.

## Struct Selection Summary

| Type | Struct | Why This Type |
|------|--------|---------------|
| `input` | `File` | External: content comes from editor or disk |
| `input` | `Project` | External: project root, settings, interpreter |
| `interned` | `TemplateName` | Fast equality for template name dedup |
| `tracked` | `Template` | Identity: maps name → file, stable across revisions |
| `tracked` | `Tag` | Identity: named tag with span, created during parsing |
| `tracked` | `NodeList` | Container: wraps Vec of plain Node types |
| `tracked` | `BlockTree` | Container: wraps block hierarchy data |
| `tracked` | `SemanticForest` | Container: wraps semantic analysis results |
| `tracked` | `TagIndex` | Multi-field tracking: 3 independent FxHashMaps |
| `tracked` | `TemplateReference` | Identity: cross-template reference with source/target |
| Plain | `Node` | Fine-grained: individual AST node in flat list |
| Plain | `BlockId`, `Blocks` | Fine-grained: block tree internal data |
| Plain | `SemanticNode` | Fine-grained: semantic tree node |
| Plain | All error types | Values: no identity, just data |

## Struct Type Inventory (django-language-server, github.com/joshuadavidthomas/django-language-server)

| Struct | Type | Crate |
|--------|------|-------|
| `File` | input | `djls-source` |
| `Project` | input | `djls-project` |
| `TemplateName` | interned | `djls-semantic` |
| `Template`, `Tag` | tracked | `djls-semantic` |
| `NodeList` | tracked | `djls-templates` |
| `BlockTree`, `TagIndex` | tracked | `djls-semantic` |
| `SemanticForest`, `TemplateReference` | tracked | `djls-semantic` |
| `Node`, `BlockId`, `Blocks`, `SemanticNode` | plain Rust | various |
