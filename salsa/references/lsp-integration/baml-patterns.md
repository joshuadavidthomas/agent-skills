# BAML — Simplest Possible Salsa LSP (No Snapshots, No Cancellation)

LSP integration patterns from BAML (AI/LLM function compiler). Demonstrates the absolute minimum viable Salsa-backed LSP.

## Architecture: Single-Threaded, No Snapshots

```
Editor
  → did_open / did_change / did_save / did_close
    → BamlProject (manages disk files + unsaved buffers)
      → sync_files_to_db() pushes ALL files into ProjectDatabase
        → ProjectDatabase owns salsa::Storage
          → check() collects diagnostics
            → publish diagnostics back to editor
```

No thread pool, no snapshot cloning, no cancellation handling. All queries run synchronously on the main thread.

## BamlProject: Dual-Layer File State

```rust
// baml/engine/language_server/src/baml_project/mod.rs
pub struct BamlProject {
    pub root_dir_name: PathBuf,
    pub files: HashMap<DocumentKey, TextDocument>,          // Saved disk files
    pub unsaved_files: HashMap<DocumentKey, TextDocument>,  // Editor buffers
    pub cached_runtime: Option<(u64, Result<BamlRuntime, Diagnostics>)>,
}
```

The LSP manages two layers of file state:
- **`files`** — Content as last saved to disk
- **`unsaved_files`** — Unsaved editor buffers (overrides `files` when present)

When the user types, the LSP updates `unsaved_files`. When the user saves, the content moves from `unsaved_files` to `files`.

## Syncing to the Salsa Database

```rust
// baml/baml_language/crates/baml_project/src/db.rs
impl ProjectDatabase {
    pub fn add_or_update_file(&mut self, path: &Path, content: &str) -> SourceFile {
        let canonical_path = path.canonicalize().unwrap_or_else(|_| path.to_path_buf());

        if let Some(&existing_file) = self.file_map.get(&canonical_path) {
            // Update existing file using Salsa's setter
            existing_file.set_text(self).to(content.to_string());
            existing_file
        } else {
            // Create new SourceFile input + update Project.files list
            let file = self.add_file_internal(&canonical_path, content);
            self.file_map.insert(canonical_path.clone(), file);
            if let Some(project) = self.project {
                let mut files = project.files(self).clone();
                files.push(file);
                project.set_files(self).to(files);
            }
            file
        }
    }

    pub fn remove_file(&mut self, path: &Path) {
        if let Some(file) = self.file_map.remove(&canonical_path) {
            let file_id = file.file_id(self);
            self.file_id_to_path.remove(&file_id);
            // Remove from project files list
            if let Some(project) = self.project {
                let files = project.files(self).iter()
                    .filter(|f| f.file_id(self) != file_id)
                    .copied().collect();
                project.set_files(self).to(files);
            }
        }
    }
}
```

**Pattern:** On every file change, call `set_text()` on the existing `SourceFile` input. This triggers Salsa to re-evaluate any queries that depended on the file's text. For new files, create a `SourceFile` AND update the `Project.files` input list.

## File Change Handlers

```rust
// baml/engine/language_server/src/baml_project/mod.rs
impl BamlProject {
    pub fn set_unsaved_file(&mut self, document_key: &DocumentKey, content: Option<String>) {
        if let Some(content) = content {
            self.unsaved_files.insert(document_key.clone(), TextDocument::new(content, 0));
        } else {
            self.unsaved_files.remove(document_key);
        }
        self.cached_runtime = None;  // Invalidate runtime cache
    }

    pub fn save_file(&mut self, document_key: &DocumentKey, content: &str) {
        self.files.insert(document_key.clone(), TextDocument::new(content.to_string(), 0));
        self.unsaved_files.remove(document_key);
        self.cached_runtime = None;
    }
}
```

## Diagnostic Collection

```rust
// baml/baml_language/crates/baml_project/src/check.rs:168-196
impl ProjectDatabase {
    pub fn check(&self) -> CheckResult {
        let project = self.get_project().unwrap();
        let source_files: Vec<SourceFile> = self.files().collect();

        let diagnostics = collect_diagnostics(self, project, &source_files);
        CheckResult { diagnostics, sources, file_paths }
    }
}
```

Diagnostics are collected by walking all compilation phases (parse → HIR → validation → type inference). Each phase's queries are Salsa-tracked, so only changed files trigger recomputation.

## Why This Works for BAML

- **Small files:** BAML configuration files are typically small (< 1000 lines)
- **Fast compilation:** The full pipeline (lex → parse → HIR → TIR → VIR) completes in milliseconds
- **Low concurrency needs:** Users don't need concurrent queries or background analysis
- **Salsa still provides value:** Even without snapshots, the incremental caching means only changed files are reprocessed

## LSP Complexity Progression

| Level | Project | Snapshots | Cancellation | Concurrency |
|-------|---------|-----------|--------------|-------------|
| 1 | **BAML** | No | No | Single-threaded |
| 2 | django-language-server | Session/SessionSnapshot | No | Queue-based |
| 3 | ty | Full snapshot isolation | Cancelled::catch + retry | Thread pool |
| 4 | rust-analyzer | AnalysisHost/Analysis | Full classification | Multi-worker + prime_caches |

Start with BAML's approach for prototypes, evolve as latency demands increase.

## What's Missing (Evolution Path)

When BAML outgrows this pattern, it would need:

1. **Snapshots** for concurrent queries (→ django-language-server's `Session`/`SessionSnapshot` pattern)
2. **Cancellation** for responsive editing (→ ty's `Cancelled::catch` + retry pattern)
3. **Background analysis** for large projects (→ rust-analyzer's worker thread + prime_caches pattern)
4. **Durability** for stdlib/config optimization (→ ty's `FileRootKind::durability()` pattern)
