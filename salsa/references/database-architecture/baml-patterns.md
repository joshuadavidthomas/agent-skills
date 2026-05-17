# BAML — 6-Layer Database Hierarchy with Boilerplate Problem

Production database architecture from BAML (AI/LLM function compiler).

## 6-Layer Trait Hierarchy

```
baml_workspace::Db           (base: project context)
  → baml_compiler_hir::Db    (HIR: name resolution, lowering)
    → baml_compiler_tir::Db  (TIR: type checking, inference)
      → baml_compiler_vir::Db (VIR: validated IR, code generation)
        → baml_compiler_mir::Db (MIR: control flow graph)
          → salsa::Database  (root)
```

## Trait Definitions — Minimal Supertrait Chaining

Each layer extends the previous with a bare marker trait:

```rust
// baml/baml_language/crates/baml_workspace/src/lib.rs:39-42
#[salsa::db]
pub trait Db: salsa::Database {
    fn project(&self) -> Project;  // Only required method in the whole hierarchy
}

// baml/baml_language/crates/baml_compiler_hir/src/lib.rs:68-69
#[salsa::db]
pub trait Db: baml_workspace::Db {}

// baml/baml_language/crates/baml_compiler_tir/src/lib.rs:147-148
#[salsa::db]
pub trait Db: baml_compiler_hir::Db {}

// baml/baml_language/crates/baml_compiler_vir/src/lib.rs:81-82
#[salsa::db]
pub trait Db: baml_compiler_tir::Db {}

// baml/baml_language/crates/baml_compiler_mir/src/lib.rs:60-61
#[salsa::db]
pub trait Db: baml_compiler_vir::Db {}
```

**Key insight:** Only the base trait (`baml_workspace::Db`) has a required method (`fn project()`). All other traits are empty — they exist solely for the supertrait chain. Tracked functions use `db: &dyn Db` with the appropriate layer's `Db` trait.

## Production Database — `ProjectDatabase`

```rust
// baml/baml_language/crates/baml_project/src/db.rs:45-80
#[salsa::db]
#[derive(Clone)]
pub struct ProjectDatabase {
    storage: salsa::Storage<ProjectDatabase>,
    next_file_id: Arc<AtomicU32>,
    project: Option<Project>,
    file_map: HashMap<PathBuf, SourceFile>,         // Side-table: path → Salsa input
    file_id_to_path: HashMap<FileId, PathBuf>,      // Side-table: reverse lookup
}

#[salsa::db]
impl salsa::Database for ProjectDatabase {}

#[salsa::db]
impl baml_workspace::Db for ProjectDatabase {
    fn project(&self) -> Project {
        self.project
            .expect("project must be set before querying - call set_project_root first")
    }
}

#[salsa::db]
impl baml_compiler_hir::Db for ProjectDatabase {}
#[salsa::db]
impl baml_compiler_tir::Db for ProjectDatabase {}
#[salsa::db]
impl baml_compiler_vir::Db for ProjectDatabase {}
#[salsa::db]
impl baml_compiler_mir::Db for ProjectDatabase {}
```

**Side-table pattern:** `file_map` and `file_id_to_path` are `HashMap`s outside Salsa for file lookup. Salsa doesn't provide enumeration of inputs, so the database maintains its own index. This matches ty's `Files` `DashMap` pattern but uses plain `HashMap` (BAML is single-threaded).

**Event callback support:**

```rust
// baml/baml_language/crates/baml_project/src/db.rs:90-100
pub fn new_with_event_callback(callback: EventCallback) -> Self {
    Self {
        storage: salsa::Storage::new(Some(callback)),
        // ...
    }
}
```

## The 6-Layer Boilerplate Problem

Every test database must repeat 6 `#[salsa::db] impl` blocks — one for each layer:

```rust
// baml/baml_language/crates/baml_tests/src/bytecode.rs:52-80
#[salsa::db]
#[derive(Clone)]
pub struct TestDatabase {
    storage: salsa::Storage<Self>,
    next_file_id: Arc<AtomicU32>,
    project: Option<baml_workspace::Project>,
}

#[salsa::db]
impl salsa::Database for TestDatabase {}

#[salsa::db]
impl baml_workspace::Db for TestDatabase {
    fn project(&self) -> baml_workspace::Project {
        self.project.expect("project must be set before querying")
    }
}

#[salsa::db]
impl baml_compiler_hir::Db for TestDatabase {}

#[salsa::db]
impl baml_compiler_tir::Db for TestDatabase {}

#[salsa::db]
impl baml_compiler_vir::Db for TestDatabase {}

#[salsa::db]
impl baml_compiler_mir::Db for TestDatabase {}
```

**This exact pattern appears 3 times** — identical boilerplate in:
- `baml_workspace::TestDatabase` (base test database)
- `baml_tests::bytecode::TestDatabase` (full-stack tests)
- `baml_compiler_emit` test database (compiler tests)

Each adds layer-specific helpers (`add_file()`, `set_project()`, `load_builtin_files()`) but the 6 `impl` blocks are copy-pasted. This is what Cairo's blanket-impl pattern (`impl<T: Database> Group for T {}`) solves — BAML uses the standard approach and pays the boilerplate cost.

## File Management Pattern

```rust
// baml/baml_language/crates/baml_project/src/db.rs (add_or_update_file)
pub fn add_or_update_file(&mut self, path: &Path, content: &str) -> SourceFile {
    let canonical_path = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());

    if let Some(&existing_file) = self.file_map.get(&canonical_path) {
        // Update existing file using Salsa's setter
        existing_file.set_text(self).to(content.to_string());
        existing_file
    } else {
        // Create new file
        let file = self.add_file_internal(&canonical_path, content);
        let file_id = file.file_id(self);
        self.file_map.insert(canonical_path.clone(), file);
        self.file_id_to_path.insert(file_id, canonical_path);

        // Update project files list
        if let Some(project) = self.project {
            let mut files: Vec<SourceFile> = project.files(self).clone();
            files.push(file);
            project.set_files(self).to(files);
        }
        file
    }
}
```

**Key pattern:** When a file already exists, call `set_text()` (Salsa setter) to update it. When it's new, create a `SourceFile` input AND update the `Project.files` input list. This dual update is needed because Salsa tracks changes to both the file content and the file list independently.

## Builtin File Loading

```rust
// baml/baml_language/crates/baml_project/src/db.rs (load_builtin_baml_files)
fn load_builtin_baml_files(&mut self) -> Vec<SourceFile> {
    let mut builtin_files = Vec::new();
    for builtin_source in baml_builtins::baml_sources() {
        let path = PathBuf::from(builtin_source.path);  // e.g., "<builtin>/baml/llm.baml"
        let file = self.add_file_internal(&path, builtin_source.source.to_string());
        let file_id = file.file_id(self);
        // Register for diagnostics but NOT in file_map (avoids spurious errors)
        self.file_id_to_path.insert(file_id, path);
        builtin_files.push(file);
    }
    builtin_files
}
```

**Design choice:** Builtin files use virtual paths (`<builtin>/baml/llm.baml`) and are loaded into Salsa as regular `SourceFile` inputs. They're registered in `file_id_to_path` for diagnostic display but NOT in `file_map` — this prevents them from appearing in `check()` diagnostics, since builtin files reference internal compiler types that aren't defined as BAML types.

## Workspace-Level TestDatabase (Simplest)

```rust
// baml/baml_language/crates/baml_workspace/src/lib.rs:71-80
#[salsa::db]
#[derive(Clone)]
pub struct TestDatabase {
    pub storage: salsa::Storage<Self>,
    pub next_file_id: Arc<AtomicU32>,
    pub project: Option<Project>,
}

#[salsa::db]
impl salsa::Database for TestDatabase {}
```

This is the simplest database — only implements `salsa::Database`, not any compiler layers. Used for workspace-level tests that don't need HIR/TIR.
