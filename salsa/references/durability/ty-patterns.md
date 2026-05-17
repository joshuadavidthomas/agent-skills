# ty — Durability by File Root

Production durability patterns from the Ruff/ty monorepo.

## Ruff/ty Shared Infrastructure: Durability by File Root

ruff_db assigns durability based on where a file lives — project files are LOW, library files are HIGH.

### FileRootKind → Durability Mapping (ruff_db)

```rust
// ruff/crates/ruff_db/src/files/file_root.rs

#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum FileRootKind {
    Project,
    LibrarySearchPath,
}

impl FileRootKind {
    const fn durability(self) -> Durability {
        match self {
            FileRootKind::Project => Durability::LOW,
            FileRootKind::LibrarySearchPath => Durability::HIGH,
        }
    }
}
```

### File Creation with Per-Field Durability (ruff_db)

```rust
// ruff/crates/ruff_db/src/files.rs — Files::system()

fn system(&self, db: &dyn Db, path: &SystemPath) -> File {
    let absolute = SystemPath::absolute(path, db.system().current_directory());

    *self.inner.system_by_path
        .entry(absolute.clone())
        .or_insert_with(|| {
            let metadata = db.system().path_metadata(path);

            // Derive durability from the file's root
            let durability = self.root(db, &absolute)
                .map_or(Durability::default(), |root| root.durability(db));

            let builder = File::builder(FilePath::System(absolute))
                .durability(durability)              // Content: LOW (project) or HIGH (library)
                .path_durability(Durability::HIGH);  // Path: never changes

            let builder = match metadata {
                Ok(metadata) if metadata.file_type().is_file() => builder
                    .permissions(metadata.permissions())
                    .revision(metadata.revision()),
                Ok(metadata) if metadata.file_type().is_directory() => {
                    builder.status(FileStatus::IsADirectory)
                }
                _ => builder
                    .status(FileStatus::NotFound)
                    // Not-found files: at least MEDIUM (might be created),
                    // but library files stay at HIGH (won't appear mid-session)
                    .status_durability(Durability::MEDIUM.max(durability)),
            };

            builder.new(db)
        })
}
```

### Program Config at HIGH (ty_python_semantic)

```rust
// ruff/crates/ty_python_semantic/src/program.rs

pub fn from_settings(db: &dyn Db, settings: ProgramSettings) -> Self {
    let ProgramSettings { python_version, python_platform, search_paths } = settings;

    search_paths.try_register_static_roots(db);

    // Everything about the program is HIGH durability —
    // Python version, platform, and search paths are set once at startup
    Program::builder(python_version, python_platform, search_paths)
        .durability(Durability::HIGH)
        .new(db)
}
```

### Project with Mixed Durability (ty_project)

```rust
// ruff/crates/ty_project/src/lib.rs

let project = Project::builder(Box::new(metadata), Box::new(settings), diagnostics)
    .durability(Durability::MEDIUM)          // Metadata/settings: config-level stability
    .open_fileset_durability(Durability::LOW) // Which files are open: changes constantly
    .file_set_durability(Durability::LOW)     // File list: changes as files are added/removed
    .new(db);
```

### Durability Summary Table (Ruff/ty monorepo)

| Input | Crate | Field | Durability | Why |
|-------|-------|-------|------------|-----|
| `Program` | ty_python_semantic | all fields | HIGH | Set once at startup |
| `File` (project) | ruff_db | text, permissions, revision | LOW | Under active editing |
| `File` (library) | ruff_db | text, permissions, revision | HIGH | Stdlib/site-packages |
| `File` (any) | ruff_db | path | HIGH | Immutable identity |
| `File` (not found, project) | ruff_db | status | MEDIUM | Might be created |
| `File` (not found, library) | ruff_db | status | HIGH | Won't appear mid-session |
| `FileRoot` | ruff_db | all fields | (varies by kind) | Project=LOW, Library=HIGH |
| `Project` | ty_project | metadata, settings | MEDIUM | Config files |
| `Project` | ty_project | open_fileset | LOW | Editor state |
| `Project` | ty_project | file_set | LOW | File additions/removals |

