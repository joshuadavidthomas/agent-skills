
# Choosing the Right Salsa Struct Type

Every piece of data in a Salsa program needs a home. The struct type you choose determines what Salsa can optimize, what lifetimes you deal with, and how your incremental system behaves under change.

There are three Salsa struct types and one non-Salsa option:

| Type | Purpose | Mutable? | Lifetime | Identity |
|------|---------|----------|----------|----------|
| `#[salsa::input]` | External data entering the system | Yes (setters) | None | Integer ID |
| `#[salsa::tracked]` | Intermediate results with field-level tracking | No | `'db` | Pointer + hash |
| `#[salsa::interned]` | Values needing fast equality via deduplication | No | `'db` | Integer ID (same data → same ID) |
| Plain Rust types | Fine-grained data not worth tracking individually | N/A | N/A | Structural |

## Decision Flowchart

Ask these questions in order:

**1. Does this data come from outside the computation?** (files, config, user edits)
→ **`#[salsa::input]`**

**2. Do you need same-data-same-ID deduplication or fast equality?** (names, type representations, module paths)
→ **`#[salsa::interned]`**

**3. Is this an intermediate entity with identity that benefits from field-level change tracking?** (a parsed function where the name may stay stable but the body changes)
→ **`#[salsa::tracked]`** — but read the warnings below first

**4. Is it too fine-grained to track individually?** (expressions, tokens, individual AST nodes)
→ **Plain Rust types** with `#[derive(salsa::Update)]`

## The Three Struct Types

### `#[salsa::input]` — The Roots

Inputs are the entry points to your computation graph. They're the only structs with setters.

```rust
#[salsa::input]
pub struct SourceFile {
    #[returns(ref)]
    pub text: String,
    pub path: PathBuf,
}

// Create with &db
let file = SourceFile::new(&db, contents, path);

// Read with &db
let text = file.text(&db);

// Mutate with &mut db (outside tracked functions only)
file.set_text(&mut db).to(new_contents);
```

Key properties:
- **No `'db` lifetime** — just a newtype around an integer ID, always `Copy`
- **Setters require `&mut db`** — can't mutate inside tracked functions
- **Each set increments the revision counter** — even if the value is unchanged
- **Per-field durability** — via setter builder: `file.set_text(&mut db).with_durability(Durability::HIGH).to(val)`

Use for: files, configuration, feature flags, external dependency data.

### `#[salsa::interned]` — Value Deduplication

Interned structs guarantee that identical data maps to the same ID. Two calls with the same fields return the same struct.

```rust
#[salsa::interned]
pub struct Word<'db> {
    #[returns(ref)]
    pub text: String,
}

let w1 = Word::new(&db, "hello".into());
let w2 = Word::new(&db, "hello".into());
assert_eq!(w1, w2); // Same ID — pointer equality
```

Key properties:
- **`'db` lifetime** — prevents use across revisions (IDs may be recycled by GC)
- **Can be created anywhere** with `&db` (not just in tracked functions)
- **No dependency tracking on field access** — reading fields doesn't register a dependency
- **Fields must be `Eq + Hash + Clone + Send + Sync`**

Use for: identifiers, names, type representations, module paths, any small value where you want O(1) equality.

### `#[salsa::tracked]` — Intermediate Entities

Tracked structs represent intermediate computation results with per-field change detection.

```rust
#[salsa::tracked]
pub struct Function<'db> {
    pub name: Word<'db>,

    #[tracked]
    #[returns(ref)]
    pub args: Vec<Word<'db>>,

    #[tracked]
    #[returns(ref)]
    pub body: Expression<'db>,
}
```

Key properties:
- **`'db` lifetime** — tied to the creating `&db`
- **Created only inside tracked functions** — can't create in setup code
- **Per-field tracking** — if only `body` changes but `args` stays the same, queries depending only on `args` won't re-execute
- **`#[id]` optimization** — marks fields used for cross-revision matching (see below)
- **Deleted when not re-created** — if the tracked function doesn't recreate a struct in a new revision, it's removed

**⚠️ Warning: Tracked structs have known soundness issues with Salsa's cycle/fixpoint iteration.** If your computation has cyclic queries (common in type systems), prefer interned structs. See the "Two Real-World Strategies" section.

### Plain Rust Types — Too Fine-Grained to Track

For data below your tracking granularity, use plain Rust types:

```rust
#[derive(Eq, PartialEq, Debug, Hash, salsa::Update)]
pub enum Expression<'db> {
    Op(Box<Expression<'db>>, Op, Box<Expression<'db>>),
    Number(f64),
    Variable(Word<'db>),
    Call(Word<'db>, Vec<Expression<'db>>),
}
```

Derive `salsa::Update` so these can be stored inside tracked struct fields. Changes to any expression invalidate the entire containing tracked struct's field — that's the granularity tradeoff.

## The `#[id]` Field Optimization

By default, tracked structs match across revisions by creation order. If items reorder (e.g., a function moves in the file), Salsa may think different functions changed. Mark identity fields with `#[id]` to match by value instead:

```rust
#[salsa::tracked]
pub struct Function<'db> {
    #[id]
    pub name: Word<'db>,  // Match by name across revisions

    #[tracked]
    #[returns(ref)]
    pub body: Expression<'db>,
}
```

`#[id]` is purely an optimization — it never affects correctness, only reuse quality.

## Real-World Strategies

Production Salsa projects use different combinations of struct types based on their domain.

| Strategy | Project | Key Choice |
|----------|---------|------------|
| **Almost No Tracked Structs** | ty (Ruff) | Interned types + tracked functions (avoids unsoundness in cyclic type systems). |
| **Intern Every Definition** | rust-analyzer | 17+ interned ID types for definition locations; tracked structs for collections only. |
| **Interned Locations** | BAML | Explicit `*Loc` interned structs re-exported as `*Id` type aliases. |
| **Location-Based Interning** | wgsl-analyzer [Legacy] | 9 interned types keyed by `Location<T> = InFile<ModuleItemId<T>>` (file + AST position). Generic `Interned<T>` wrapper with `PhantomData`. |
| **Generic Location + Macro** | Mun [Legacy] | 4 interned types using generic `ItemLoc<N>` (module + AST ID). `impl_intern!` macro generates ID types + `Intern`/`Lookup` traits. |
| **Container Input** | Fe | Single `Workspace` input with immutable trie for all files vs individual `File` inputs. |
| **Immortal IDs** | Cairo | `revisions = usize::MAX` on 38+ interned types for serialization stability. |
| **All Four Types** | djls | Simplest complete example: 2 inputs, 1 interned, 7 tracked, plain AST nodes. |

For detailed implementation patterns and code examples for each strategy, see [references/real-world-strategies.md](references/struct-selection/real-world-strategies.md).

## How Many Inputs? (The Cardinality Question)

The decision flowchart above tells you *when* to use `#[salsa::input]`. But there's a practical question it doesn't answer: **how many input types should a project have?**

The answer from every surveyed project: **very few.**

| Project | Input Types | What They Are |
|---|---|---|
| ty / ruff shared | 2 | `File` (source files), `Program` (config) |
| rust-analyzer | ~5 | `FileText`, `FileSourceRootInput`, `SourceRootInput`, `LibraryRoots`, `LocalRoots` |
| Cairo | 4 | One singleton per layer (`FilesGroupInput`, `DefsGroupInput`, etc.) |
| BAML | 2 | `SourceFile`, `Project` |
| Fe | 3 | `File`, `Workspace`, `DependencyGraph` |
| django-language-server | 2 | `File`, `Project` |

Every project has 2-5 input types. Not 10, not 20. **Inputs are the rarest Salsa struct type.**

### The Decision Rule for New Inputs

Create a new `#[salsa::input]` only when **all three** of these are true:

1. **The data comes from outside the computation graph.** It's pushed in by external code (LSP handler, CLI, file watcher), not derived from other Salsa data.

2. **It has its own mutation lifecycle.** It changes independently of your other inputs, at different times, for different reasons. If it always changes when something else changes, it should be a field on that something else, or a tracked function reading that something else.

3. **You need a setter.** Inputs have `set_*` methods. Tracked structs don't. If external code needs to mutate it, it's an input. If it's computed, it's tracked.

### When NOT to Create a New Input

**"It's a different kind of file"** → Probably not a new input. ty has ONE `File` input for Python source files, stub files, vendored files, config files — everything. The file kind is a derived property (tracked function or plain method), not a separate input type. django-language-server follows the same pattern: Python source files and template files are both `File`.

**"It has extra metadata"** → Use a tracked struct wrapping the existing input. In django-language-server, `Template` wraps `File` + `TemplateName`. The metadata is *derived during discovery*, not pushed in externally, so it's tracked, not input.

**"It changes rarely"** → That's durability, not a new input. Mark the existing input's fields with high durability. Don't create a parallel input type just because something is more stable.

**"It comes from a different source (subprocess, network, etc.)"** → The *data* comes from outside, but does the *identity and lifecycle* come from outside? If a subprocess returns data that maps to files on disk, those files are still `File` inputs. The subprocess result can be cached in a tracked function that reads from those inputs.

### When You DO Need a New Input

- **`Project`** / **`Program`** — Project root, interpreter path, Python version, search paths. Completely different lifecycle from individual files: set once at startup, updated on config change, not on every keystroke.
- **`DependencyGraph`** (Fe) — The dependency structure between crates is external configuration, not derivable from file content.
- **`Workspace`** (Fe) — Contains the full file collection in an immutable trie. A deliberate design choice (see "Fe" section above) trading invalidation granularity for simplicity.

### The Litmus Test

Ask: **"Who calls the setter?"**

- If the answer is "the same code path that handles file changes," you probably don't need a new input — add a field to `File` or derive it in a tracked function.
- If the answer is "a completely different code path" (config reload, project initialization, CLI flag parsing), a new input may be warranted.

### Example: Wrapping Instead of Creating

A Django template LSP discovers Python templatetag libraries on disk. Should `TagLibrary` be a new input?

**No.** The library is a file on disk → it's already a `File` input. The library-specific metadata (load name, module path) is *derived during discovery*, not pushed in from outside. The correct pattern:

```rust
// WRONG: creating a new input for something that wraps an existing one
#[salsa::input]
pub struct TagLibrary {
    pub file: File,          // Already an input!
    pub load_name: String,
    pub module_path: String,
}

// RIGHT: tracked struct wrapping the existing input
#[salsa::tracked]
pub struct TagLibrary<'db> {
    pub file: File,                    // Existing input
    pub load_name: TemplateName<'db>,  // Interned for dedup
    #[returns(ref)]
    pub module_path: String,
}

// Created inside a tracked function during discovery
#[salsa::tracked]
pub fn discover_tag_libraries(db: &dyn Db) -> Vec<TagLibrary<'_>> {
    // Walk filesystem, create TagLibrary tracked structs
    // wrapping existing File inputs...
}
```

The distinction: `File` is an input because external code (the file watcher, the LSP handler) pushes content changes into it. `TagLibrary` is tracked because discovery is a computation that *reads* existing inputs.

## When to Choose What: Summary

| Situation | Use | Example |
|-----------|-----|---------|
| External data that changes | `input` (expect 2-5 total) | File contents, config, feature flags |
| Data derived from existing inputs | `tracked` (not input!) | Template wrapping File + name |
| Names, identifiers, small strings | `interned` | Variable names, module paths |
| Type representations | `interned` | Union types, callable types, tuple types |
| Definition locations (AST pointers) | `interned` | FunctionId, StructId, TraitId |
| Non-Salsa query arguments | `interned` (wrapper) | ModuleNameIngredient wrapping ModuleName |
| Parsed items with field-level tracking | `tracked` (if no cycles) | Function with separate name/args/body |
| Stable semantic identities | `tracked` | Definition, ScopeId (with explicit stability) |
| AST nodes, expressions, tokens | Plain Rust | Expression enum, Statement struct |
| Collections of items | Plain Rust in `Arc` | `Arc<Vec<ImplId>>` returned from tracked fn |

## Common Mistakes

**Proliferating input types.** Every surveyed project has 2-5 inputs. If you're creating a new input, ask "who calls the setter?" — if it's the same code path as file changes, you probably want a tracked struct wrapping an existing input, not a new input type. See the "How Many Inputs?" section above.

**Making everything tracked.** Tracked structs have overhead (identity hashing, per-field revisions, deletion tracking). Most data is better as interned or plain types.

**Using tracked structs in cyclic computations.** If your computation has cycles (type inference, class hierarchies, mutual recursion), prefer interned structs. This is a known issue.

**Forgetting `#[returns(ref)]` on large fields.** Without it, field access clones the value. Use `#[returns(ref)]` for `String`, `Vec`, `Arc`, and other heap-allocated types.

**External types lacking `Debug` or `Eq`.** **[Legacy API/Architecture: stc]** When integrating external libraries, their types may not implement `Debug` (required by Salsa for tracked struct fields) or `Eq`. Wrap them in a newtype: `struct DebugIgnore<T>(pub T)` with a placeholder `Debug` impl, and pair with `#[no_eq]` on the field. This is a pragmatic bridge for incremental adoption of existing libraries. For the full stc `DebugIgnore<T>` pattern, see the [query-pipeline.md](query-pipeline.md) skill's stc reference.

**Tracking at too fine a granularity.** Don't make every expression a tracked struct. Track at "reasonably coarse" boundaries (functions, scopes, modules). Finer tracking means more overhead with diminishing returns.

**Storing tracked/interned structs across revisions.** Both carry `'db` lifetimes. You can't hold onto them while mutating the database. Inputs (which are just integer IDs without `'db`) are safe to store long-term.

For full production code examples, see:
- [references/real-world-strategies.md](references/struct-selection/real-world-strategies.md) — Comparative overview of strategies
- [references/ty-patterns.md](references/struct-selection/ty-patterns.md) — ty's "almost no tracked structs" approach
- [references/rust-analyzer-patterns.md](references/struct-selection/rust-analyzer-patterns.md) — rust-analyzer's "intern every definition" approach
- [references/djls-patterns.md](references/struct-selection/djls-patterns.md) — django-language-server's "all four types in 78 files" (simplest complete example)
- [references/cairo-patterns.md](references/struct-selection/cairo-patterns.md) — Cairo's "macro-generated interned IDs" approach
- [references/baml-patterns.md](references/struct-selection/baml-patterns.md) — BAML's "interned locations with type-alias re-exports" and tracked struct wrapper pattern (15 instances)
- [references/fe-patterns.md](references/struct-selection/fe-patterns.md) — Fe's "Workspace-as-container input" (single input with immutable trie vs side-table pattern), interned collection types (10+ `Vec<T>` wrappers like `AttrListId`, `GenericArgListId`, `FuncParamListId`), tracked methods on inputs
