# ty — 4-Layer Database Hierarchy

Production database architecture from the Ruff/ty monorepo.

## Ruff/ty Monorepo: 4-Layer Database Hierarchy

### Layer 1: Base Db Trait (ruff_db — shared infrastructure)

The foundation. Provides file system access, vendored file system, and global Python version:

```rust
/// Most basic database that gives access to files, the host system, source code, and parsed AST.
#[salsa::db]
pub trait Db: salsa::Database {
    fn vendored(&self) -> &VendoredFileSystem;
    fn system(&self) -> &dyn System;
    fn files(&self) -> &Files;
    fn python_version(&self) -> PythonVersion;
}
```

Every tracked function in `ruff_db` takes `&dyn Db` — it only sees files and system access, nothing domain-specific.

### Layer 2: Module Resolver (ty_module_resolver)

Adds Python module search paths:

```rust
#[salsa::db]
pub trait Db: SourceDb {  // SourceDb is alias for ruff_db::Db
    fn search_paths(&self) -> &SearchPaths;
}
```

### Layer 3: Semantic Analysis (ty_python_semantic)

Adds linting, analysis settings, and file filtering:

```rust
#[salsa::db]
pub trait Db: ModuleResolverDb {
    fn should_check_file(&self, file: File) -> bool;
    fn rule_selection(&self, file: File) -> &RuleSelection;
    fn lint_registry(&self) -> &LintRegistry;
    fn analysis_settings(&self, file: File) -> &AnalysisSettings;
    fn verbose(&self) -> bool;
}
```

### Layer 4: Project (ty_project)

Adds project management and dynamic cloning for trait objects:

```rust
#[salsa::db]
pub trait Db: SemanticDb {
    fn project(&self) -> Project;
    fn dyn_clone(&self) -> Box<dyn Db>;
}
```

### Production Database: `ProjectDatabase` (ty_project)

The concrete struct implementing all 4 layers:

```rust
#[salsa::db]
#[derive(Clone)]
pub struct ProjectDatabase {
    project: Option<Project>,
    files: Files,

    // IMPORTANT: Never return clones of `system` outside `ProjectDatabase` (only return references)
    // or the "trick" to get a mutable `Arc` in `Self::system_mut` is no longer guaranteed to work.
    system: Arc<dyn System + Send + Sync + RefUnwindSafe>,

    // IMPORTANT: This field must be the last because we use `trigger_cancellation`
    // (drops all other storage references) to drop all other references to the database,
    // which gives us exclusive access to other `Arc`s stored on this db.
    // However, for this to work it's important that the `storage` is dropped AFTER any `Arc`
    // that we try to mutably borrow using `Arc::get_mut` (like `system`).
    storage: salsa::Storage<ProjectDatabase>,
}

impl ProjectDatabase {
    pub fn new<S>(project_metadata: ProjectMetadata, system: S) -> anyhow::Result<Self>
    where
        S: System + 'static + Send + Sync + RefUnwindSafe,
    {
        let mut db = Self {
            project: None,  // Will be set after singletons are initialized
            storage: salsa::Storage::new(
                if tracing::enabled!(tracing::Level::TRACE) {
                    Some(Box::new(move |event: Event| {
                        if matches!(event.kind, salsa::EventKind::WillCheckCancellation) {
                            return;
                        }
                        tracing::trace!("Salsa event: {event:?}");
                    }))
                } else {
                    None
                }
            ),
            files: Files::default(),
            system: Arc::new(system),
        };

        // Phase 2: initialize singletons
        let program_settings = project_metadata
            .to_program_settings(db.system(), db.vendored())?;
        Program::from_settings(&db, program_settings);
        db.project = Some(Project::from_metadata(&db, project_metadata)?);

        Ok(db)
    }

    /// Get mutable access to the system by triggering cancellation first.
    pub fn system_mut(&mut self) -> &mut dyn System {
        self.trigger_cancellation();
        Arc::get_mut(&mut self.system).expect(
            "ref count should be 1 because `trigger_cancellation` drops all other DB references.",
        )
    }
}
```

### Implementation of All Layers for `ProjectDatabase`

```rust
// Layer 1: Base
#[salsa::db]
impl SourceDb for ProjectDatabase {
    fn vendored(&self) -> &VendoredFileSystem {
        ty_vendored::file_system()  // Global singleton — bundled typeshed
    }

    fn system(&self) -> &dyn System { &*self.system }
    fn files(&self) -> &Files { &self.files }

    fn python_version(&self) -> PythonVersion {
        Program::get(self).python_version(self)  // Delegate to singleton
    }
}

// Layer 2: Module resolver
#[salsa::db]
impl ty_module_resolver::Db for ProjectDatabase {
    fn search_paths(&self) -> &SearchPaths {
        Program::get(self).search_paths(self)  // Delegate to singleton
    }
}

// Layer 3: Semantic analysis
#[salsa::db]
impl SemanticDb for ProjectDatabase {
    fn should_check_file(&self, file: File) -> bool {
        self.project
            .is_some_and(|project| project.should_check_file(self, file))
    }

    fn rule_selection(&self, file: File) -> &RuleSelection {
        let settings = file_settings(self, file);
        settings.rules(self)  // Per-file rules via settings query
    }

    fn lint_registry(&self) -> &LintRegistry {
        &ty_python_semantic::lint::LINT_REGISTRY
    }

    fn analysis_settings(&self, file: File) -> &AnalysisSettings {
        let settings = file_settings(self, file);
        settings.analysis(self)
    }

    fn verbose(&self) -> bool { false }
}

// Layer 4: Project
#[salsa::db]
impl Db for ProjectDatabase {
    fn project(&self) -> Project {
        self.project.unwrap()
    }

    fn dyn_clone(&self) -> Box<dyn Db> {
        Box::new(self.clone())
    }
}

#[salsa::db]
impl salsa::Database for ProjectDatabase {}
```

### Files Side-Table: On-Demand Input Creation (ruff_db — shared infrastructure)

The `Files` struct lives outside Salsa and manages path-to-`File` lookups using concurrent hash maps:

```rust
#[derive(Default, Clone)]
pub struct Files {
    inner: Arc<FilesInner>,
}

#[derive(Default)]
struct FilesInner {
    system_by_path: FxDashMap<SystemPathBuf, File>,
    system_virtual_by_path: FxDashMap<SystemVirtualPathBuf, VirtualFile>,
    vendored_by_path: FxDashMap<VendoredPathBuf, File>,
    roots: std::sync::RwLock<FileRoots>,
}

impl Files {
    fn system(&self, db: &dyn Db, path: &SystemPath) -> File {
        let absolute = SystemPath::absolute(path, db.system().current_directory());

        *self.inner.system_by_path
            .entry(absolute.clone())
            .or_insert_with(|| {
                let metadata = db.system().path_metadata(path);

                // Durability from file root type (project=LOW, library=HIGH)
                let durability = self
                    .root(db, &absolute)
                    .map_or(Durability::default(), |root| root.durability(db));

                let builder = File::builder(FilePath::System(absolute))
                    .durability(durability)
                    .path_durability(Durability::HIGH);  // Paths never change

                let builder = match metadata {
                    Ok(metadata) if metadata.file_type().is_file() => builder
                        .permissions(metadata.permissions())
                        .revision(metadata.revision()),
                    _ => builder
                        .status(FileStatus::NotFound)
                        .status_durability(Durability::MEDIUM.max(durability)),
                };

                builder.new(db)
            })
    }
}
```

Key patterns:
- `DashMap` for concurrent thread-safe lookups
- `Arc` wrapper for cheap cloning with the database
- Durability assigned per file root type
- Non-existent files tracked at `MEDIUM` durability (they might be created soon)
- Path field at `HIGH` durability (paths almost never change)

### Singleton Input: `Program` (ty_python_semantic)

Global Python settings stored as a Salsa singleton:

```rust
#[salsa::input(singleton)]
pub struct Program {
    #[returns(ref)]
    pub python_version_with_source: PythonVersionWithSource,

    #[returns(ref)]
    pub python_platform: PythonPlatform,

    #[returns(ref)]
    pub search_paths: SearchPaths,
}

impl Program {
    pub fn from_settings(db: &dyn Db, settings: ProgramSettings) -> Self {
        Program::builder(
            settings.python_version,
            settings.python_platform,
            settings.search_paths,
        )
        .durability(Durability::HIGH)  // Config rarely changes
        .new(db)
    }

    pub fn update_from_settings(self, db: &mut dyn Db, settings: ProgramSettings) {
        // Only update fields that actually changed — avoids spurious invalidation
        if self.search_paths(db) != &settings.search_paths {
            self.set_search_paths(db).to(settings.search_paths);
        }
        if &settings.python_platform != self.python_platform(db) {
            self.set_python_platform(db).to(settings.python_platform);
        }
        if &settings.python_version != self.python_version_with_source(db) {
            self.set_python_version_with_source(db).to(settings.python_version);
        }
    }
}
```

### Test Database with Event Capture (ruff_db — shared infrastructure)

```rust
type Events = Arc<Mutex<Vec<salsa::Event>>>;

#[salsa::db]
#[derive(Default, Clone)]
pub(crate) struct TestDb {
    storage: salsa::Storage<Self>,
    files: Files,
    system: TestSystem,
    vendored: VendoredFileSystem,
    events: Events,
}

impl TestDb {
    pub(crate) fn new() -> Self {
        let events: Events = Default::default();
        Self {
            storage: salsa::Storage::new(Some(Box::new({
                let events = events.clone();
                move |event| {
                    tracing::trace!("event: {:?}", event);
                    events.lock().unwrap().push(event);
                }
            }))),
            events,
            ..Default::default()
        }
    }

    pub(crate) fn take_salsa_events(&mut self) -> Vec<salsa::Event> {
        std::mem::take(&mut *self.events.lock().unwrap())
    }

    pub(crate) fn clear_salsa_events(&mut self) {
        self.events.lock().unwrap().clear();
    }
}
```

### DbWithTestSystem Trait (ruff_db — shared infrastructure)

ruff_db provides a trait for test databases that use the in-memory test file system:

```rust
pub trait DbWithTestSystem: Db {
    fn test_system(&self) -> &TestSystem;
    fn test_system_mut(&mut self) -> &mut TestSystem;
}

impl DbWithTestSystem for TestDb {
    fn test_system(&self) -> &TestSystem { &self.system }
    fn test_system_mut(&mut self) -> &mut TestSystem { &mut self.system }
}
```

This avoids downcasting when writing test helpers that need to manipulate the in-memory filesystem.

### Module Resolver Test DB with Builder (ty_module_resolver)

```rust
#[salsa::db]
#[derive(Clone)]
pub(crate) struct TestDb {
    storage: salsa::Storage<Self>,
    files: Files,
    system: TestSystem,
    vendored: VendoredFileSystem,
    search_paths: Arc<SearchPaths>,
    python_version: PythonVersion,
    events: Events,
}

impl TestDb {
    pub(crate) fn with_search_paths(mut self, search_paths: SearchPaths) -> Self {
        self.set_search_paths(search_paths);
        self
    }

    pub(crate) fn with_python_version(mut self, python_version: PythonVersion) -> Self {
        self.python_version = python_version;
        self
    }
}
```

