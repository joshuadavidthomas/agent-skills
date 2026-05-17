
# Salsa Advanced Plumbing: Level 4 Patterns

These patterns move beyond the standard `#[salsa::...]` macros and into the low-level "engine" of Salsa. They are used by projects like `rust-analyzer` and `Cairo` to solve niche architectural problems.

## 1. `specify`: Overriding Tracked Functions
Sometimes you want a tracked function to have a "default" implementation but allow certain instances to have a hardcoded or "late-bound" value.

```rust
#[salsa::tracked(specify)]
fn type_of(db: &dyn Db, expr: Expr) -> Type {
    // default: look at AST
}

// Elsewhere, for a built-in:
let builtin = Expr::new(db, ...);
type_of::specify(db, builtin, Type::Int); 
```
*   **Use case:** Built-in functions in a compiler, or "filling in" data that is discovered in a later phase but belongs logically to an earlier struct.

## 2. `singleton` Inputs
For project-wide state that should only ever have one instance.

```rust
#[salsa::input(singleton)]
pub struct ProjectConfig {
    pub python_path: PathBuf,
}

// Access without passing an ID:
let config = ProjectConfig::get(db); 
```
*   **Use case:** `Cairo` uses this for its various "Group" layers to store per-layer global configuration.

## 3. `attach`: Thread-Local Database
Passing `&db` through every single method in a large system can be noisy. `attach` allows you to store the database in a thread-local for a specific scope.

```rust
// In your database impl:
db.attach(|db| {
    // Inside here, code can call `salsa::with_attached_database`
    // to get access to the &db without it being passed in.
});
```
*   **Use case:** Implementing `Display` or `Debug` for interned types where you need the database to look up the string values but the trait doesn't provide it.

## 4. Persistence (Serde Integration)
With the `persistence` feature, Salsa can serialize the entire state of the database to disk.

```rust
// Serialize
let bytes = db.as_serialize();

// Deserialize into a fresh DB
db.deserialize(deserializer);
```
*   **Use case:** `rust-analyzer` uses similar mechanisms to provide fast cold-starts by loading index data from disk instead of re-parsing the entire standard library.

## 5. Synthetic Writes & Runtime Inspection
For profiling and advanced telemetry.

*   **`db.synthetic_write(Durability::HIGH)`**: Forces a revision bump as if a high-durability input changed. Useful for benchmarking incrementality.
*   **`db.ingredient_debug_name(index)`**: Resolves a low-level `IngredientIndex` to a human-readable name.
*   **`db.memory_usage()`**: (Unstable) Returns a `DatabaseInfo` struct with per-query and per-struct memory breakdown.

## Summary: When to use Plumbing

| Feature | Use it when... |
| :--- | :--- |
| **`specify`** | You have "special cases" like built-ins that skip normal logic. |
| **`singleton`** | You have exactly one "Project" or "Global" config. |
| **`attach`** | You are trapped in a third-party trait (like `Display`) and need a DB. |
| **`persistence`** | Cold-start time for your project is > 5 seconds. |
| **`synthetic_write`** | You are writing a benchmark or stress-test for Salsa. |
