# rust-analyzer — Durability by Source Kind

Production durability patterns from rust-analyzer (Rust IDE).

## rust-analyzer: Durability by Source Kind

rust-analyzer assigns durability based on whether a source root is a library or workspace code.

### Two Helper Functions

```rust
// rust-analyzer/crates/base-db/src/change.rs

fn source_root_durability(source_root: &SourceRoot) -> Durability {
    if source_root.is_library { Durability::MEDIUM } else { Durability::LOW }
}

fn file_text_durability(source_root: &SourceRoot) -> Durability {
    if source_root.is_library { Durability::HIGH } else { Durability::LOW }
}
```

Note the split: source root **structure** (which files belong to a root) gets MEDIUM for libraries, but file **text** gets HIGH. The reasoning is that the file list might change when dependencies are added/removed, but the actual source text of crates.io dependencies is effectively immutable.

### Applying Durability During Change Application

```rust
// rust-analyzer/crates/base-db/src/change.rs — FileChange::apply()

// Source roots: structure gets appropriate durability
for (idx, root) in roots.into_iter().enumerate() {
    let root_id = SourceRootId(idx as u32);
    let durability = source_root_durability(&root);
    for file_id in root.iter() {
        db.set_file_source_root_with_durability(file_id, root_id, durability);
    }
    db.set_source_root_with_durability(root_id, Arc::new(root), durability);
}

// File text: content gets appropriate durability
for (file_id, text) in self.files_changed {
    let source_root_id = db.file_source_root(file_id);
    let source_root = db.source_root(source_root_id.source_root_id(db));
    let durability = file_text_durability(&source_root.source_root(db));
    let text = text.unwrap_or_default();
    db.set_file_text_with_durability(file_id, &text, durability)
}
```

### Check-Before-Update on Crate Metadata

```rust
// rust-analyzer/crates/base-db/src/input.rs — CrateGraph::set_in_db()

let crate_input = match crates_map.0.entry(unique_crate_data) {
    Entry::Occupied(entry) => {
        let old_crate = *entry.get();
        
        // Each field guarded by equality check
        if crate_data != *old_crate.data(db) {
            old_crate.set_data(db).with_durability(Durability::MEDIUM).to(crate_data);
        }
        if krate.extra != *old_crate.extra_data(db) {
            old_crate.set_extra_data(db).with_durability(Durability::MEDIUM).to(krate.extra.clone());
        }
        if krate.cfg_options != *old_crate.cfg_options(db) {
            old_crate.set_cfg_options(db).with_durability(Durability::MEDIUM).to(krate.cfg_options.clone());
        }
        if krate.env != *old_crate.env(db) {
            old_crate.set_env(db).with_durability(Durability::MEDIUM).to(krate.env.clone());
        }
        if krate.ws_data != *old_crate.workspace_data(db) {
            old_crate.set_workspace_data(db).with_durability(Durability::MEDIUM).to(krate.ws_data.clone());
        }
        old_crate
    }
    Entry::Vacant(entry) => {
        // New crate: all fields at MEDIUM
        let input = Crate::builder(crate_data, krate.extra.clone(), krate.ws_data.clone(),
                                    krate.cfg_options.clone(), krate.env.clone())
            .durability(Durability::MEDIUM)
            .new(db);
        entry.insert(input);
        input
    }
};
```

### Global Flags at HIGH

```rust
// rust-analyzer/crates/hir-def/src/test_db.rs
this.set_expand_proc_attr_macros_with_durability(true, Durability::HIGH);

// rust-analyzer/crates/ide-db/src/lib.rs
_ = base_db::LibraryRoots::builder(Default::default())
    .durability(Durability::MEDIUM)
    .new(&db);
_ = base_db::LocalRoots::builder(Default::default())
    .durability(Durability::MEDIUM)
    .new(&db);
```

### Durability Summary Table (rust-analyzer)

| Input | Durability | Why |
|-------|------------|-----|
| Library file text | HIGH | crates.io source is immutable |
| Project file text | LOW | Actively edited by user |
| Library source root structure | MEDIUM | Changes on dependency add/remove |
| Project source root structure | LOW | Changes with workspace files |
| Crate data, cfg_options, env | MEDIUM | Changes on Cargo.toml edit |
| Proc macro expansion flag | HIGH | Set once at startup |
| LibraryRoots, LocalRoots sets | MEDIUM | Changes on workspace restructure |

