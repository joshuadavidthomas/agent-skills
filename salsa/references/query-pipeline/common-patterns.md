# Common Query Pipeline Patterns

Distilled patterns for designing robust and efficient Salsa query pipelines.

## The Wrapper Function Pattern

Salsa tracked functions require all arguments to be Salsa ingredients (inputs, tracked, or interned). When you need to pass a plain Rust type as an argument, wrap it in an interned struct.

### Problem
You have a complex Rust type that isn't a Salsa ingredient, but it's used as a lookup key:

```rust
pub struct ModuleName {
    pub segments: Vec<String>,
}

// ❌ Error: ModuleName is not a Salsa ingredient
#[salsa::tracked]
fn resolve_module_query(db: &dyn Db, name: ModuleName) -> Option<Module> { ... }
```

### Solution: The Wrapper
1. Create an interned struct to wrap the plain type.
2. Provide a public non-tracked function that interns the argument and delegates to a private tracked function.

```rust
// 1. Interned wrapper
#[salsa::interned]
struct ModuleNameIngredient<'db> {
    #[returns(ref)]
    pub name: ModuleName,
}

// 2. Public API (not tracked)
pub fn resolve_module(db: &dyn Db, name: &ModuleName) -> Option<Module> {
    let interned = ModuleNameIngredient::new(db, name.clone());
    resolve_module_query(db, interned)
}

// 3. Private tracked implementation
#[salsa::tracked]
fn resolve_module_query(db: &dyn Db, name: ModuleNameIngredient) -> Option<Module> {
    let name = name.name(db); // Extract the plain type
    // ... actual resolution logic ...
}
```

This pattern is used extensively in **ty**'s module resolver and type inference system.

## Tracked Methods on Input Structs

You can compute derived properties directly on input structs using `#[salsa::tracked]` on an `impl` block. This is cleaner than free functions and enables natural chaining.

```rust
#[salsa::input]
pub struct File {
    #[return_ref]
    pub text: String,
}

#[salsa::tracked]
impl File {
    #[salsa::tracked]
    pub fn containing_ingot(self, db: &dyn Db) -> Option<Ingot<'_>> {
        // Query some global workspace state
        db.workspace().containing_ingot(db, self.url(db))
    }

    #[salsa::tracked(return_ref)]
    pub fn path(self, db: &dyn Db) -> Option<Utf8PathBuf> {
        // Depends on containing_ingot
        self.containing_ingot(db)
            .and_then(|ingot| db.workspace().get_relative_path(db, ingot.base(db), self))
    }

    #[salsa::tracked]
    pub fn kind(self, db: &dyn Db) -> Option<FileKind> {
        // Depends on path
        self.path(db).as_ref().map(|p| classify_path(p))
    }
}
```

**Payoff:**
- **Granular reuse:** If the workspace layout changes but a file's `containing_ingot` stays the same, `path` and `kind` reuse their cached results.
- **Fluent API:** Callers use `file.kind(db)` instead of `kind(db, file)`.

Used in **Fe** (for ingot/path resolution) and **django-language-server** (for revision-based invalidation).

## The Dual-Query (or Triple-Split) Pattern

To maximize early cutoff, separate what changes **cosmetically** (whitespace, comments, spans) from what changes **semantically** (signatures, types, logic).

### Implementation
Compute both in one internal (non-tracked) function, then wrap them in separate tracked functions.

```rust
// Internal helper: computes both together
fn lower_function_with_source_map(db: &dyn Db, func: FunctionId)
    -> (Arc<Signature>, SourceMap) { ... }

// Tracked Query 1: Semantic signature
// Downstream queries (type inference) should depend ONLY on this.
#[salsa::tracked]
pub fn function_signature(db: &dyn Db, func: FunctionId) -> Arc<Signature> {
    lower_function_with_source_map(db, func).0
}

// Tracked Query 2: Cosmetic source map
// Only IDE features (hover, go-to-def) depend on this.
#[salsa::tracked]
pub fn function_source_map(db: &dyn Db, func: FunctionId) -> SourceMap {
    lower_function_with_source_map(db, func).1
}
```

**Early Cutoff in Action:**
1. User adds a comment to a function.
2. `function_signature` re-executes, returns an **equal** `Arc<Signature>` → **Backdated**.
3. Downstream type inference (which depends only on `function_signature`) is **skipped entirely**.
4. `function_source_map` re-executes with new spans → **Propagated** (only to IDE features).

Used in **BAML** (triple-split for signature/body/source-map) and **rust-analyzer** (`body_with_source_map`).

## Non-Salsa Context Bundling

Tracked functions can become unwieldy if they take many arguments. When a computation needs results from multiple tracked queries, bundle them into a plain Rust struct.

```rust
pub struct ResolutionContext {
    pub classes: HashSet<Name>,
    pub enums: HashSet<Name>,
    pub aliases: HashSet<Name>,
}

impl ResolutionContext {
    pub fn new(db: &dyn Db, project: Project) -> Self {
        Self {
            classes: db.class_names(project).names(db).clone(),
            enums: db.enum_names(project).names(db).clone(),
            aliases: db.alias_names(project).names(db).clone(),
        }
    }
}

#[salsa::tracked]
fn infer_types(db: &dyn Db, func: FunctionId) -> InferenceResult {
    let ctx = ResolutionContext::new(db, func.project(db));
    // Use ctx.classes, ctx.enums, etc.
}
```

The context struct is **not** a Salsa ingredient — it's a short-lived transient object used within a query. This is cleaner than passing three separate tracked struct references.

Used in **BAML** (`TypeResolutionContext`).
