# django-language-server — Simplest Production Salsa LSP

A Django template language server showing the minimal viable Salsa LSP architecture. Much simpler than ty or rust-analyzer — a good starting point for new projects.

## Architecture Overview

```
Editor (VS Code, etc.)
  ↓ LSP protocol
DjangoLanguageServer (async handler)
  → Session (owns mutable DjangoDatabase + Workspace)
     ├── Workspace (buffer management + OverlayFileSystem)
     └── DjangoDatabase (Salsa storage + side state)
  → SessionSnapshot (cloned database for background tasks)
```

## Session: The Mutable Owner

```rust
// django-language-server/crates/djls-server/src/session.rs
pub struct Session {
    workspace: Workspace,      // Buffer management
    client_info: ClientInfo,   // Client capabilities
    db: DjangoDatabase,        // Salsa database (mutable)
}

impl Session {
    pub fn snapshot(&self) -> SessionSnapshot {
        SessionSnapshot::new(self.db.clone(), self.client_info.clone())
    }

    pub fn db(&self) -> &DjangoDatabase { &self.db }
    pub fn db_mut(&mut self) -> &mut DjangoDatabase { &mut self.db }
}
```

## SessionSnapshot: Immutable Clone for Background Work

```rust
// django-language-server/crates/djls-server/src/session.rs
#[derive(Clone)]
pub struct SessionSnapshot {
    db: DjangoDatabase,
    client_info: ClientInfo,
}
```

Used for background tasks like project initialization:

```rust
// django-language-server/crates/djls-server/src/server.rs
self.with_session_task(move |session| async move {
    if let Some(project) = session.db().project() {
        project.initialize(session.db());
    }
    Ok(())
}).await;
```

## Server: Async LSP Handler

```rust
// django-language-server/crates/djls-server/src/server.rs
pub struct DjangoLanguageServer {
    client: Client,
    session: Arc<Mutex<Session>>,  // Tokio mutex for async access
    queue: Queue,                   // Background task queue
    _log_guard: WorkerGuard,
}
```

All LSP handlers go through `with_session` (read) or `with_session_mut` (write):

```rust
impl DjangoLanguageServer {
    pub async fn with_session<F, R>(&self, f: F) -> R
    where F: FnOnce(&Session) -> R {
        let session = self.session.lock().await;
        f(&session)
    }

    pub async fn with_session_mut<F, R>(&self, f: F) -> R
    where F: FnOnce(&mut Session) -> R {
        let mut session = self.session.lock().await;
        f(&mut session)
    }
}
```

## Document Lifecycle

### Open Document

```rust
// django-language-server/crates/djls-server/src/session.rs
pub fn open_document(&mut self, text_document: &TextDocumentItem) -> Option<TextDocument> {
    let path = text_document.uri.to_utf8_path_buf()?;
    let document = self.workspace.open_document(
        &mut self.db, &path, &text_document.text, text_document.version, kind,
    )?;
    self.handle_file(document.file());  // Warm caches immediately
    Some(document)
}
```

### Update Document (Incremental)

```rust
pub fn update_document(&mut self, text_document: &VersionedTextDocumentIdentifier,
    changes: Vec<TextDocumentContentChangeEvent>) -> Option<TextDocument>
{
    let path = text_document.uri.to_utf8_path_buf()?;
    let document = self.workspace.update_document(
        &mut self.db, &path, changes.to_document_changes(), text_document.version,
        self.client_info.position_encoding(),
    )?;
    self.handle_file(document.file());  // Re-warm caches
    Some(document)
}
```

### Close Document (Revert to Disk)

```rust
pub fn close_document(&mut self, text_document: &TextDocumentIdentifier)
    -> Option<TextDocument>
{
    let path = text_document.uri.to_utf8_path_buf()?;
    self.workspace.close_document(&mut self.db, &path)
}
```

## Overlay File System

The workspace provides an overlay file system that Salsa reads through:

```rust
// django-language-server/crates/djls-workspace/src/workspace.rs
pub struct Workspace {
    buffers: Buffers,                     // Open document contents
    overlay: Arc<OverlayFileSystem>,      // Buffers → disk fallback
}
```

When the database reads a file via `db.read_file(path)`, the overlay:
1. Checks the buffer map for the path
2. If found, returns buffer content (editor's version)
3. If not found, reads from disk

This is simpler than ty's `source_text_override` pattern — no Salsa-level override, just a file system abstraction.

## Revision-Based Invalidation

Instead of tracking file metadata (modification time, permissions, etc.), django-language-server uses a simple revision counter:

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
        let _ = self.revision(db);  // CRITICAL: Creates Salsa dependency
        let path = self.path(db);
        db.read_file(path).unwrap_or_default()
    }
}
```

The `let _ = self.revision(db)` line is essential — without it, changing the revision wouldn't invalidate the `source` query. This creates an explicit dependency on the revision input.

When a document changes:

```rust
// django-language-server/crates/djls-source/src/db.rs
fn bump_file_revision(&mut self, file: File) {
    let current_rev = file.revision(self);
    file.set_revision(self).to(current_rev + 1);
}
```

## Warm-on-Open Pattern

When a template file is opened or changed, django-language-server immediately triggers parsing and validation:

```rust
// django-language-server/crates/djls-server/src/session.rs
fn handle_file(&self, file: File) {
    if FileKind::from(file.path(&self.db)) == FileKind::Template {
        if let Some(nodelist) = djls_templates::parse_template(&self.db, file) {
            djls_semantic::validate_nodelist(&self.db, nodelist);
        }
    }
}
```

This ensures:
1. The parse cache is warm before the user requests diagnostics
2. Validation errors are accumulated (via `ValidationErrorAccumulator`)
3. Subsequent diagnostic requests are fast (cache hits)

## Diagnostic Publication

```rust
// django-language-server/crates/djls-server/src/server.rs
async fn publish_diagnostics(&self, document: &TextDocument) {
    // Skip if client supports pull diagnostics (they'll request when ready)
    if self.with_session(|s| s.client_info().supports_pull_diagnostics()).await {
        return;
    }

    let diagnostics = self.with_session_mut(|session| {
        let db = session.db();
        let file = db.get_or_create_file(&path);
        let nodelist = djls_templates::parse_template(db, file);
        djls_ide::collect_diagnostics(db, file, nodelist)
    }).await;

    self.client.publish_diagnostics(uri, diagnostics, Some(document.version())).await;
}
```

Supports both push (publish) and pull (diagnostic request) modes based on client capabilities.

## Key Differences from ty/rust-analyzer

| Aspect | django-language-server | ty | rust-analyzer |
|--------|----------------------|-----|---------------|
| Concurrency | Tokio mutex on Session | Thread pool + snapshots | Thread pool + snapshots |
| File invalidation | Revision counter bump | File metadata sync | Change application |
| Buffer management | OverlayFileSystem | source_text_override | vfs::ChangeKind |
| Cancellation | None (early stage) | Full retry logic | Full retry + classification |
| Multi-project | Single project | Per-project databases | Single database |
| Background tasks | Queue with snapshots | Schedule trait | Dispatcher + threadpool |

## Architecture Summary (django-language-server, github.com/joshuadavidthomas/django-language-server)

| Crate | Role |
|-------|------|
| `djls-server` | LSP handlers, Session/SessionSnapshot, concrete DjangoDatabase |
| `djls-workspace` | Workspace + OverlayFileSystem |
| `djls-source` | File input + revision pattern, SourceDb trait |
| `djls-ide` | Diagnostic collection (accumulator reads) |
