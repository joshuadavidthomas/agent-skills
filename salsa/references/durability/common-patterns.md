# Common Durability Patterns

Standard patterns for assigning and managing durability in Salsa.

## Per-Field Durability on Inputs

A single input struct can have fields at different durability levels. This is powerful when one part of the struct is stable while another changes frequently.

### Pattern: The File Input

This pattern (distilled from `ruff_db`) separates the immutable identity (`path`) and stable metadata (`status`) from the frequently-changing content (`text`).

```rust
#[salsa::input]
pub struct File {
    pub path: FilePath,       // HIGH: never changes after creation
    pub status: FileStatus,   // MEDIUM: might be created/deleted
    pub text: String,         // LOW (project) or HIGH (library)
    pub permissions: u32,     // Same as text
    pub revision: FileRevision, // Same as text
}

// At creation:
File::builder(path)
    .durability(durability)              // text, permissions, revision from root
    .path_durability(Durability::HIGH)   // path is immutable identity
    .status_durability(Durability::MEDIUM.max(durability))  // at least MEDIUM
    .new(&db)
```

**Result:** Queries that only read `path` get HIGH durability and are never revalidated when file contents change. Queries that read `text` get the root's durability and are revalidated accordingly.

## Derived Durability

Instead of hardcoding durability per file, derive it from context (like the source root or file root kind).

### Example: ruff_db (Shared Infrastructure)
Durability follows the file root kind:

```rust
let durability = self.root(db, &path)
    .map_or(Durability::default(), |root| root.durability(db));
```

### Example: rust-analyzer
Durability follows whether the source root is a library:

```rust
fn file_text_durability(source_root: &SourceRoot) -> Durability {
    if source_root.is_library { Durability::HIGH } else { Durability::LOW }
}
```

## Check-Before-Update

Always guard setters with an equality check to avoid spurious revision bumps.

```rust
// Guarding updates to crate metadata in rust-analyzer
if crate_data != *old_crate.data(db) {
    old_crate.set_data(db)
        .with_durability(Durability::MEDIUM)
        .to(crate_data);
}
```
