# ty LSP Integration Patterns

Production code from ty's LSP server (`ty_server`) showing how Salsa integrates with LSP.

## LSP Database Trait (ty_server)

The LSP layer adds a thin trait on top of `ProjectDb` for document resolution:

```rust
// ruff/crates/ty_server/src/db.rs
#[salsa::db]
pub(crate) trait Db: ProjectDb {
    fn document(&self, file: File) -> Option<&Document>;
}

impl Db for ProjectDatabase {
    fn document(&self, file: File) -> Option<&Document> {
        self.system()
            .as_any()
            .downcast_ref::<LSPSystem>()
            .and_then(|system| match file.path(self) {
                FilePath::System(path) => system.system_path_to_document(path),
                FilePath::SystemVirtual(path) => system.system_virtual_path_to_document(path),
                FilePath::Vendored(_) => None,
            })
    }
}
```

The `System` abstraction allows injecting LSP-specific behavior (document lookup) without LSP dependencies in the core database.

## Document Change Handler (ty_server)

Handles `textDocument/didChange` — the user is typing:

```rust
// ruff/crates/ty_server/src/server/api/notifications/did_change.rs
impl SyncNotificationHandler for DidChangeTextDocumentHandler {
    fn run(
        session: &mut Session,
        client: &Client,
        params: DidChangeTextDocumentParams,
    ) -> Result<()> {
        let DidChangeTextDocumentParams {
            text_document: VersionedTextDocumentIdentifier { uri, version },
            content_changes,
        } = params;

        let mut document = session
            .document_handle(&uri)
            .with_failure_code(ErrorCode::InternalError)?;

        document
            .update_text_document(session, content_changes, version)
            .with_failure_code(ErrorCode::InternalError)?;

        publish_diagnostics_if_needed(&document, session, client);

        Ok(())
    }
}
```

The flow: get document handle → apply LSP text edits → set `source_text_override` on the Salsa input → trigger diagnostic refresh.

## File Watch Handler (ty_server)

Handles `workspace/didChangeWatchedFiles` — external file system changes:

```rust
// ruff/crates/ty_server/src/server/api/notifications/did_change_watched_files.rs
impl SyncNotificationHandler for DidChangeWatchedFiles {
    fn run(session: &mut Session, client: &Client, params: DidChangeWatchedFilesParams) -> Result<()> {
        let mut events_by_db: FxHashMap<_, Vec<ChangeEvent>> = FxHashMap::default();

        for change in params.changes {
            let path = DocumentKey::from_url(&change.uri).into_file_path();
            let system_path = match path {
                AnySystemPath::System(system) => system,
                AnySystemPath::SystemVirtual(path) => {
                    tracing::debug!("Ignoring virtual path from change event: `{path}`");
                    continue;
                }
            };

            let Some(db) = session.project_db_for_path(&system_path) else {
                tracing::trace!("Ignoring change for `{system_path}` - not in any workspace");
                continue;
            };

            let change_event = match change.typ {
                FileChangeType::CREATED => ChangeEvent::Created {
                    path: system_path, kind: CreatedKind::Any,
                },
                FileChangeType::CHANGED => ChangeEvent::Changed {
                    path: system_path, kind: ChangedKind::Any,
                },
                FileChangeType::DELETED => ChangeEvent::Deleted {
                    path: system_path, kind: DeletedKind::Any,
                },
                _ => continue,
            };

            events_by_db
                .entry(db.project().root(db).to_path_buf())
                .or_default()
                .push(change_event);
        }

        // Batch-apply changes per project root
        for (root, changes) in events_by_db {
            session.apply_changes(&AnySystemPath::System(root.clone()), changes);
            publish_settings_diagnostics(session, client, root);
        }

        // Trigger diagnostic refresh
        if client_capabilities.supports_workspace_diagnostic_refresh() {
            client.send_request::<WorkspaceDiagnosticRefresh>(session, (), |_, ()| {});
        } else {
            for key in session.text_document_handles() {
                publish_diagnostics_if_needed(&key, session, client);
            }
        }

        Ok(())
    }
}
```

Key pattern: events are grouped by project root before applying. This ensures each project database receives its relevant changes as a batch.

## Change Event Classification (ty_project)

```rust
// ruff/crates/ty_project/src/watch.rs
pub enum ChangeEvent {
    Opened(SystemPathBuf),
    Created { path: SystemPathBuf, kind: CreatedKind },
    Changed { path: SystemPathBuf, kind: ChangedKind },
    Deleted { path: SystemPathBuf, kind: DeletedKind },
    CreatedVirtual(SystemVirtualPathBuf),
    ChangedVirtual(SystemVirtualPathBuf),
    DeletedVirtual(SystemVirtualPathBuf),
    Rescan,
}

pub enum CreatedKind { File, Directory, Any }
pub enum ChangedKind { FileContent, FileMetadata, Any }
pub enum DeletedKind { File, Directory, Any }
```

The `Any` variant lets file watchers be conservative when they can't distinguish change types.

## Change Application (ty_project)

The core of how editor changes become Salsa input updates:

```rust
// ruff/crates/ty_project/src/db/changes.rs (simplified)
fn apply_changes(&mut self, changes: Vec<ChangeEvent>) -> ApplyChangesResult {
    let mut synced_files = FxHashSet::default();
    let mut sync_recursively = BTreeSet::new();
    let mut result = ApplyChangesResult::default();

    // Pre-scan for structural changes (config files)
    for change in &changes {
        if let Some(path) = change.system_path() {
            if matches!(path.file_name(), Some(".gitignore" | "ty.toml" | "pyproject.toml")) {
                result.project_changed = true;
            }
        }
    }

    for change in changes {
        match change {
            ChangeEvent::Changed { path, .. } | ChangeEvent::Opened(path) => {
                if synced_files.insert(path.clone()) {
                    let absolute = SystemPath::absolute(&path, self.system().cwd());
                    File::sync_path_only(self, &absolute);
                    // Library roots bump revision (invalidates module discovery)
                    // Project roots don't (avoids cascading invalidation)
                    if let Some(root) = self.files().root(self, &absolute) {
                        if root.kind(self) == FileRootKind::LibrarySearchPath {
                            root.set_revision(self).to(FileRevision::now());
                        }
                    }
                }
            }
            ChangeEvent::Created { kind, path } => {
                match kind {
                    CreatedKind::File => {
                        if synced_files.insert(path.clone()) {
                            File::sync_path(self, &path);
                        }
                    }
                    CreatedKind::Directory | CreatedKind::Any => {
                        sync_recursively.insert(path.clone());
                    }
                }
            }
            ChangeEvent::Deleted { kind, path } => {
                if kind != DeletedKind::Directory {
                    if synced_files.insert(path.clone()) {
                        File::sync_path(self, &path);
                    }
                    if let Some(file) = self.files().try_system(self, &path) {
                        project.remove_file(self, file);
                    }
                }
            }
            ChangeEvent::Rescan => {
                Files::sync_all(self);
            }
        }
    }

    // Deduplicate recursive syncs (skip nested directories)
    let mut last = None;
    for path in sync_recursively {
        if let Some(ref last) = last {
            if path.starts_with(last) { continue; }
        }
        Files::sync_recursively(self, &path);
        last = Some(path);
    }

    // Reload project if config changed
    if result.project_changed {
        let metadata = ProjectMetadata::discover(&project_root, self.system());
        // ... update program settings, reload project ...
    }

    result
}
```

Key optimization: project roots don't bump revision on individual file changes (avoids invalidating directory-level queries), but library search paths do bump (must invalidate module discovery).

## File Sync Implementation (ruff_db — shared infrastructure)

How individual files are synced with the filesystem:

```rust
// ruff/crates/ruff_db/src/files.rs
fn sync_system_path(db: &mut dyn Db, path: &SystemPath, file: Option<File>) {
    let Some(file) = file.or_else(|| db.files().try_system(db, path)) else {
        return;
    };

    let (status, revision, permission) = match db.system().path_metadata(path) {
        Ok(metadata) if metadata.file_type().is_file() => (
            FileStatus::Exists,
            metadata.revision(),
            metadata.permissions(),
        ),
        _ => (FileStatus::NotFound, FileRevision::zero(), None),
    };

    let mut clear_override = false;

    if file.status(db) != status {
        file.set_status(db).to(status);
        clear_override = true;
    }

    if file.revision(db) != revision {
        file.set_revision(db).to(revision);
        clear_override = true;
    }

    if file.permissions(db) != permission {
        file.set_permissions(db).to(permission);
    }

    // Clear editor override when disk state changes
    if clear_override && file.source_text_override(db).is_some() {
        file.set_source_text_override(db).to(None);
    }
}
```

Each field update uses a Salsa setter. Changing `revision` invalidates all queries reading file content. The override is cleared when disk state changes, ensuring disk changes take precedence over stale editor content.

## Source Text Override (ruff_db — shared infrastructure)

The tracked function checks for editor overrides before reading from disk:

```rust
// ruff/crates/ruff_db/src/source.rs
#[salsa::tracked(heap_size=ruff_memory_usage::heap_size)]
pub fn source_text(db: &dyn Db, file: File) -> SourceText {
    if let Some(source) = file.source_text_override(db) {
        return source.clone();
    }
    // Accessing revision(db) creates a Salsa dependency on file changes
    let _ = file.revision(db);
    let kind = if is_notebook(db.system(), file.path(db)) {
        file.read_to_notebook(db).unwrap_or_else(|e| {
            // ... error handling, return empty notebook
        }).into()
    } else {
        file.read_to_string(db).unwrap_or_else(|e| {
            // ... error handling, return empty string
        }).into()
    };
    SourceText { inner: Arc::new(SourceTextInner { kind, read_error }) }
}
```

## Session Snapshots (ty_server)

Two snapshot types for different use cases:

```rust
// ruff/crates/ty_server/src/session.rs

// For single-document requests (hover, completion)
pub(crate) struct DocumentSnapshot {
    resolved_client_capabilities: ResolvedClientCapabilities,
    global_settings: Arc<GlobalSettings>,
    workspace_settings: Arc<WorkspaceSettings>,
    position_encoding: PositionEncoding,
    document: DocumentHandle,
}

// For workspace-wide operations (diagnostics refresh)
pub(crate) struct SessionSnapshot {
    index: Arc<Index>,
    global_settings: Arc<GlobalSettings>,
    position_encoding: PositionEncoding,
    resolved_client_capabilities: ResolvedClientCapabilities,
    revision: u64,

    /// IMPORTANT: databases must come last for correct drop ordering.
    /// Salsa's cancellation blocks until all clones drop — if the db drops
    /// before other Arc fields, cancel_others() unblocks while we still
    /// hold the Index, and Arc::into_inner fails.
    projects: Vec<ProjectDatabase>,
}

impl Session {
    pub(crate) fn snapshot_session(&self) -> SessionSnapshot {
        SessionSnapshot {
            projects: self.projects.values()
                .map(|p| &p.db)
                .cloned()          // Salsa snapshot (cheap)
                .collect(),
            index: self.index.clone().unwrap(),
            global_settings: self.global_settings.clone(),
            // ...
        }
    }
}
```

## Cancellation Retry in LSP (ty_server)

```rust
// ruff/crates/ty_server/src/server/api.rs
fn panic_response<R: RetriableRequestHandler>(
    id: &RequestId,
    client: &Client,
    error: &PanicError,
    request: Option<lsp_server::Request>,
) {
    if error.payload.downcast_ref::<salsa::Cancelled>().is_some() {
        if let Some(request) = request {
            // Re-queue for retry — data changed, query likely to succeed now
            client.retry(request);
        } else {
            // No original request to retry — return ContentModified
            respond_silent_error(id.clone(), client, R::salsa_cancellation_error());
        }
    } else {
        // Real panic — internal error
        respond::<R>(id, Err(Error {
            code: ErrorCode::InternalError,
            error: anyhow!("request handler {error}"),
        }), client);
    }
}

// Default cancellation error
fn salsa_cancellation_error() -> ResponseError {
    ResponseError {
        code: ErrorCode::ContentModified as i32,
        message: "content modified".to_string(),
        data: None,
    }
}
```

## Index Mutation Guard (ty_server)

For mutating non-Salsa state shared via `Arc`, ty_server uses a guard pattern that ensures exclusive access:

```rust
// ruff/crates/ty_server/src/session.rs
fn index_mut(&mut self) -> MutIndexGuard<'_> {
    let index = self.index.take().unwrap();

    // Remove index from each database, ensuring no other Arc clones exist
    for db in self.projects_mut() {
        db.system_mut().downcast_mut::<LSPSystem>().unwrap().take_index();
    }

    // Now safe to get exclusive access
    let index = Arc::into_inner(index).unwrap();

    MutIndexGuard { session: self, index: Some(index) }
}

impl Drop for MutIndexGuard<'_> {
    fn drop(&mut self) {
        if let Some(index) = self.index.take() {
            let index = Arc::new(index);
            for db in self.session.projects_mut() {
                db.system_mut().downcast_mut::<LSPSystem>().unwrap()
                    .set_index(index.clone());
            }
            self.session.index = Some(index);
        }
    }
}
```

## Fix Application with Override Guard (ty_project)

For speculative changes (applying fixes), ty uses a guard that restores the original source on failure:

```rust
// ruff/crates/ty_project/src/fixes.rs
struct WithUpdatedSourceGuard<'db> {
    db: &'db mut dyn Db,
    file: File,
    old_source: Option<SourceText>,
}

impl<'db> WithUpdatedSourceGuard<'db> {
    fn new(db: &'db mut dyn Db, file: File, old_source: &SourceText, new_source: SourceText) -> Self {
        file.set_source_text_override(db).to(Some(new_source));
        Self { db, file, old_source: Some(old_source.clone()) }
    }
    fn defuse(&mut self) { self.old_source = None; }
}

impl Drop for WithUpdatedSourceGuard<'_> {
    fn drop(&mut self) {
        if let Some(old_source) = self.old_source.take() {
            self.file.set_source_text_override(self.db).to(Some(old_source));
        }
    }
}

// Usage: test fix, verify no syntax errors, then commit
let mut guard = WithUpdatedSourceGuard::new(db, file, &source, new_source);
let parsed = parsed_module(guard.db(), file);
if parsed.has_syntax_errors() {
    continue;  // Guard drops, restoring original source
}
write_to_disk(guard.db(), file, &new_source)?;
guard.defuse();  // Success — keep the override
```

## Session Revision Tracking (ty_server)

The session tracks its own revision counter (separate from Salsa's internal revision) for debouncing expensive operations like workspace diagnostics:

```rust
// ruff/crates/ty_server/src/session.rs
pub(crate) fn apply_changes(&mut self, path: &AnySystemPath, changes: Vec<ChangeEvent>) {
    self.bump_revision();  // Increment session revision
    self.project_db_mut(path).apply_changes(changes, overrides.as_ref());
}

fn bump_revision(&mut self) {
    self.revision += 1;
}
```
