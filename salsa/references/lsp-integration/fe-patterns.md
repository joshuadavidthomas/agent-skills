# Fe — Workspace-Input File Management in LSP

Fe (github.com/argotorg/fe) manages files through a single `Workspace` input rather than individual file setters or a side-table.

## Backend Architecture

Single mutable database, no snapshots or cancellation:

```rust
pub struct Backend {
    pub(super) client: ClientSocket,
    pub(super) db: DriverDataBase,
    pub(super) workers: tokio::runtime::Runtime,
    pub(super) builtin_files: Option<BuiltinFiles>,
    pub(super) readonly_warnings: FxHashSet<Url>,
}

impl Backend {
    pub fn new(client: ClientSocket) -> Self {
        let db = DriverDataBase::default();
        let builtin_files = BuiltinFiles::new(&db).ok();
        Self { client, db, workers: /* ... */, builtin_files, readonly_warnings: FxHashSet::default() }
    }
}
```

## LSP Notification Handlers

File changes are emitted as `FileChange` events, then handled in `handle_file_change`:

```rust
pub async fn handle_did_open_text_document(
    backend: &Backend,
    message: DidOpenTextDocumentParams,
) -> Result<(), ResponseError> {
    let _ = backend.client.clone().emit(FileChange {
        uri: message.text_document.uri,
        kind: ChangeKind::Open(message.text_document.text),
    });
    Ok(())
}

pub async fn handle_did_change_text_document(
    backend: &Backend,
    message: DidChangeTextDocumentParams,
) -> Result<(), ResponseError> {
    let _ = backend.client.clone().emit(FileChange {
        uri: message.text_document.uri,
        kind: ChangeKind::Edit(Some(message.content_changes[0].text.clone())),
    });
    Ok(())
}
```

## File Change Application — Through Workspace Methods

All file mutations go through the `Workspace` input's methods:

```rust
pub async fn handle_file_change(
    backend: &mut Backend,
    message: FileChange,
) -> Result<(), ResponseError> {
    match message.kind {
        ChangeKind::Open(contents) => {
            if let Ok(url) = Url::from_file_path(&path) {
                backend.db.workspace().update(&mut backend.db, url, contents);
            }
        }
        ChangeKind::Create => {
            let contents = read_file_text_optional(path.clone()).await?;
            if let Ok(url) = Url::from_file_path(&path) {
                backend.db.workspace().update(&mut backend.db, url, contents);
            }
        }
        ChangeKind::Edit(contents) => {
            let contents = contents.unwrap_or_else(|| read_file(path));
            if let Ok(url) = Url::from_file_path(&path) {
                backend.db.workspace().update(&mut backend.db, url, contents);
            }
        }
        ChangeKind::Delete => {
            if let Ok(url) = Url::from_file_path(path) {
                backend.db.workspace().remove(&mut backend.db, &url);
            }
        }
    }

    // Trigger diagnostics after every change
    let _ = backend.client.emit(NeedsDiagnostics(message.uri));
    Ok(())
}
```

## Workspace Methods (touch/update/remove)

The `Workspace` input wraps file management in convenience methods:

```rust
impl Workspace {
    pub fn touch(&self, db: &mut dyn InputDb, url: Url, initial_content: Option<String>) -> File {
        if let Some(file) = self.get(db, &url) {
            return file;
        }
        let initial = initial_content.unwrap_or_default();
        let input_file = File::__new_impl(db, initial);
        self.set(db, url, input_file).expect("Failed to create file")
    }

    pub fn update(&self, db: &mut dyn InputDb, url: Url, content: String) -> File {
        let file = self.touch(db, url, None);
        file.set_text(db).to(content);
        file
    }

    pub fn remove(&self, db: &mut dyn InputDb, url: &Url) -> Option<File> {
        // Remove from trie and reverse lookup
    }
}
```

**Trade-off vs ty/BAML pattern:** `update` calls `touch` (which calls `self.set` → replaces the trie) then `set_text`. This means both the workspace structure AND the file content change in the same revision. In ty's pattern, the `DashMap` side-table is outside Salsa, so file creation doesn't trigger any Salsa invalidation — only the content setter does.
