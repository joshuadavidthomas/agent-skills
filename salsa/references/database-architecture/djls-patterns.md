# django-language-server — 5-Layer Database Architecture

A Django template language server (~78 Rust files) with a clean, approachable database architecture.

## Trait Hierarchy

```
SourceDb (file creation/reading) [djls-source]
  → WorkspaceDb (file system) [djls-workspace]
    → TemplateDb (parsing) [djls-templates]
      → SemanticDb (analysis) [djls-semantic]
  → ProjectDb (config/Python env) [djls-project]
```

Note: `ProjectDb` extends `salsa::Database` directly, not `SemanticDb`. The layers form a partial order, not a strict linear chain.

### Layer 1: SourceDb

```rust
// django-language-server/crates/djls-source/src/db.rs
#[salsa::db]
pub trait Db: salsa::Database {
    fn create_file(&self, path: &Utf8Path) -> File;
    fn get_file(&self, path: &Utf8Path) -> Option<File>;
    fn read_file(&self, path: &Utf8Path) -> std::io::Result<String>;

    // Default implementations for convenience:
    fn get_or_create_file(&self, path: &Utf8Path) -> File { /* ... */ }
    fn bump_file_revision(&mut self, file: File) { /* ... */ }
    fn invalidate_file(&mut self, path: &Utf8Path) -> File { /* ... */ }
}
```

Notable: default method implementations on the trait provide `get_or_create_file`, `bump_file_revision`, and `invalidate_file`. This reduces boilerplate in implementors.

### Layer 2: WorkspaceDb

```rust
// django-language-server/crates/djls-workspace/src/db.rs
#[salsa::db]
pub trait Db: SourceDb {
    fn fs(&self) -> Arc<dyn FileSystem>;
}
```

Minimal — just provides file system access. The `FileSystem` trait is an abstraction over real disk I/O or in-memory file systems for testing.

### Layer 3: TemplateDb

```rust
// django-language-server/crates/djls-templates/src/db.rs
#[salsa::db]
pub trait Db: SourceDb {}
```

Empty marker trait — template parsing is done through tracked functions (`parse_template`), not trait methods. The trait exists to mark the boundary for accumulator collection.

### Layer 4: SemanticDb

```rust
// django-language-server/crates/djls-semantic/src/db.rs
#[salsa::db]
pub trait Db: TemplateDb {
    fn tag_specs(&self) -> TagSpecs;
    fn tag_index(&self) -> TagIndex<'_>;
    fn template_dirs(&self) -> Option<Vec<Utf8PathBuf>>;
    fn diagnostics_config(&self) -> DiagnosticsConfig;
}
```

Provides semantic analysis configuration: tag specifications (what Django tags exist), tag grammar index, template search directories, and diagnostic configuration.

### Layer 5: ProjectDb

```rust
// django-language-server/crates/djls-project/src/db.rs
#[salsa::db]
pub trait Db: salsa::Database {
    fn project(&self) -> Option<Project>;
    fn inspector(&self) -> Arc<Inspector>;
    fn project_root_or_cwd(&self) -> Utf8PathBuf { /* default impl */ }
}
```

Project metadata and Python environment access. The `Inspector` is a Python subprocess that queries Django's runtime for template directories, installed templatetags, etc.

## Concrete Database

```rust
// django-language-server/crates/djls-server/src/db.rs
#[salsa::db]
#[derive(Clone)]
pub struct DjangoDatabase {
    fs: Arc<dyn FileSystem>,
    files: Arc<FxDashMap<Utf8PathBuf, File>>,
    project: Arc<Mutex<Option<Project>>>,
    settings: Arc<Mutex<Settings>>,
    inspector: Arc<Inspector>,
    storage: salsa::Storage<Self>,
}
```

### Non-Salsa State

| Field | Type | Purpose |
|-------|------|---------|
| `fs` | `Arc<dyn FileSystem>` | Overlay file system (buffers → disk fallback) |
| `files` | `Arc<FxDashMap<Utf8PathBuf, File>>` | File lookup side-table (like ty's `Files`) |
| `project` | `Arc<Mutex<Option<Project>>>` | Mutable singleton, set during initialization |
| `settings` | `Arc<Mutex<Settings>>` | LSP configuration, updated via `didChangeConfiguration` |
| `inspector` | `Arc<Inspector>` | Python subprocess for runtime queries |

### Settings Update Pattern

```rust
impl DjangoDatabase {
    pub fn set_settings(&mut self, settings: Settings) {
        let project_needs_update = {
            let old = self.settings();
            old.venv_path() != settings.venv_path()
                || old.django_settings_module() != settings.django_settings_module()
        };
        *self.settings.lock().unwrap() = settings;
        if project_needs_update {
            if let Some(project) = self.project() {
                let root = project.root(self).clone();
                self.set_project(&root, &self.settings());
            }
        }
    }
}
```

## Test Database Pattern

In-module test databases implement all required layers:

```rust
// django-language-server/crates/djls-semantic/src/blocks/tree.rs (tests)
#[salsa::db]
#[derive(Clone)]
struct TestDatabase {
    storage: salsa::Storage<Self>,
    fs: Arc<Mutex<InMemoryFileSystem>>,
}

#[salsa::db] impl salsa::Database for TestDatabase {}
#[salsa::db] impl djls_source::Db for TestDatabase { /* ... */ }
#[salsa::db] impl djls_templates::Db for TestDatabase {}
#[salsa::db] impl crate::Db for TestDatabase { /* ... */ }
```

Each test module that needs a database defines its own `TestDatabase` with just the layers it needs. This is simpler than ty's shared test database because the project is smaller.

## Benchmark Database

```rust
// django-language-server/crates/djls-bench/src/db.rs
#[salsa::db]
#[derive(Clone)]
pub struct Db {
    sources: Arc<FxDashMap<Utf8PathBuf, String>>,
    storage: salsa::Storage<Self>,
}
```

A minimal database for benchmarks — no file system, no project, just in-memory sources.

## Layer Summary (django-language-server, github.com/joshuadavidthomas/django-language-server)

| Crate | Role |
|-------|------|
| `djls-source` | Layer 1: SourceDb trait |
| `djls-workspace` | Layer 2: WorkspaceDb trait |
| `djls-templates` | Layer 3: TemplateDb trait + TemplateErrorAccumulator |
| `djls-semantic` | Layer 4: SemanticDb trait + ValidationErrorAccumulator |
| `djls-project` | Layer 5: ProjectDb trait |
| `djls-server` | Concrete `DjangoDatabase` implementing all layers |
| `djls-bench` | Benchmark database (minimal) |
