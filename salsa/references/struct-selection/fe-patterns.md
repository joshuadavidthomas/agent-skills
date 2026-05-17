# Fe — Workspace-as-Container Input and Interned Collections

Fe is a smart contract language (github.com/argotorg/fe). It makes two distinctive struct choices not seen in other surveyed projects.

## Inputs (3): File, Workspace, DependencyGraph

### File Input — Minimal, with Tracked Methods

Fe's `File` input is minimal — just `text`. All derived properties are tracked methods:

```rust
#[salsa::input(constructor = __new_impl)]
#[derive(Debug)]
pub struct File {
    #[return_ref]
    pub text: String,
}

#[salsa::tracked]
impl File {
    #[salsa::tracked]
    pub fn containing_ingot(self, db: &dyn InputDb) -> Option<Ingot<'_>> {
        self.url(db)
            .and_then(|url| db.workspace().containing_ingot(db, url))
    }

    #[salsa::tracked(return_ref)]
    pub fn path(self, db: &dyn InputDb) -> Option<Utf8PathBuf> {
        self.containing_ingot(db)
            .and_then(|ingot| db.workspace().get_relative_path(db, ingot.base(db), self))
    }

    #[salsa::tracked]
    pub fn kind(self, db: &dyn InputDb) -> Option<IngotFileKind> {
        self.path(db).as_ref().and_then(|path| {
            if path.as_str().ends_with(".fe") {
                Some(IngotFileKind::Source)
            } else if path.as_str().ends_with("fe.toml") {
                Some(IngotFileKind::Config)
            } else {
                None
            }
        })
    }

    pub fn url(self, db: &dyn InputDb) -> Option<Url> {
        db.workspace().get_path(db, self)
    }
}
```

**Design choice:** Tracked methods on an input struct means `containing_ingot`, `path`, and `kind` are each independently cached. Changing the workspace structure can invalidate `containing_ingot` without re-deriving `kind` if the ingot assignment didn't change.

### Workspace Input — Single Container with Immutable Trie

Instead of individual `File` inputs looked up via a side-table (`DashMap` in ty, `HashMap` in BAML), Fe puts the entire file collection inside one input:

```rust
#[salsa::input]
#[derive(Debug)]
pub struct Workspace {
    files: StringTrie<Url, File>,   // URL → File mapping (immutable trie)
    paths: IndexMap<File, Url>,     // Reverse lookup
}

#[salsa::tracked]
impl Workspace {
    pub fn default(db: &dyn InputDb) -> Self {
        Workspace::new(db, Trie::new(), IndexMap::default())
    }

    pub(crate) fn set(
        &self,
        db: &mut dyn InputDb,
        url: Url,
        file: File,
    ) -> Result<File, InputIndexError> {
        let paths = self.paths(db);
        if let Some(existing_url) = paths.get(&file)
            && existing_url != &url
        {
            return Err(InputIndexError::CannotReuseInput);
        }

        let files = self.files(db);
        self.set_files(db).to(files.insert(url.clone(), file));
        let mut paths = self.paths(db);
        paths.insert(file, url);
        self.set_paths(db).to(paths);
        Ok(file)
    }

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
        if let Some(_file) = self.files(db).get(url) {
            let files = self.files(db);
            if let (files, Some(file)) = files.remove(url) {
                self.set_files(db).to(files);
                let mut paths = self.paths(db);
                paths.remove(&file);
                Some(file)
            } else {
                None
            }
        } else {
            None
        }
    }

    pub fn get(&self, db: &dyn InputDb, url: &Url) -> Option<File> {
        self.files(db).get(url).cloned()
    }

    #[salsa::tracked]
    pub fn items_at_base(self, db: &dyn InputDb, base: Url) -> StringPrefixView<'_, Url, File> {
        self.files(db).view_subtrie(base)
    }
}
```

**Trade-off:** Adding/removing any file replaces the trie and invalidates all queries that read the workspace file list. But individual `File.text` queries are unaffected — editing content only invalidates text-dependent queries.

## Interned Collection Types (10+)

Fe systematically interns `Vec<T>` containers as separate interned structs:

```rust
#[salsa::interned]
#[derive(Debug)]
pub struct GenericArgListId<'db> {
    #[return_ref]
    pub data: Vec<GenericArg<'db>>,
    pub is_given: bool,
}

impl<'db> GenericArgListId<'db> {
    pub fn none(db: &'db dyn HirDb) -> Self {
        Self::new(db, vec![], false)
    }

    pub fn given(db: &'db dyn HirDb, data: Vec<GenericArg<'db>>) -> Self {
        Self::new(db, data, true)
    }
}
```

Other interned collection types: `AttrListId`, `FuncParamListId`, `GenericParamListId`,
`EffectParamListId`, `FieldDefListId`, `VariantDefListId`, `WhereClauseId`, `TupleTypeId`.

This gives structural sharing: two functions with identical parameter lists get the same `FuncParamListId`. It also makes collections cheap to pass around (`Copy` integer IDs) with `#[return_ref]` access to the underlying `Vec`.

Also interned: `IdentId` (identifiers), `PathId` (paths), `TypeId` (HIR types), `TyId` (lowered types), `TraitInstId` (trait instantiations), `IntegerId`, `StringId`.
