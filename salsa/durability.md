
# Tuning with Durability Levels

Durability is a promise about how often an input changes. When only low-durability inputs change (the common case), Salsa can skip validating any query that depends exclusively on higher-durability inputs — without walking the dependency graph at all.

## The Mental Model: Shallow Verification

Salsa tracks the last revision each durability level changed. When validating a cached result:
1. Check the query's **combined durability** (minimum of all inputs).
2. If no input at that level (or higher) has changed since the result was memoized, the result is still valid.
3. **Zero dependency traversal** is performed. This is "shallow verification."

| Level | Change Frequency | Typical Use |
|-------|------------------|-------------|
| `Durability::LOW` | Every keystroke | Workspace files, editor state |
| `Durability::MEDIUM` | Occasionally | Config files (Cargo.toml), metadata |
| `Durability::HIGH` | Rarely/Never | Stdlib, library dependencies |

**The Win:** A user edit (LOW) allows Salsa to validate queries depending only on HIGH-durability inputs (stdlib) in O(1) instead of walking the graph.

## Core API

### Setting Durability (Builder)
The builder generates `<field_name>_durability(Durability)` methods for each field.

```rust
let file = File::builder(path)
    .durability(Durability::LOW)           // Default for content
    .path_durability(Durability::HIGH)     // Path never changes
    .new(&db);
```

### Updating Durability (Setter)
Call `.with_durability()` on the setter. If omitted, the setter **preserves** the existing durability of the field.

```rust
file.set_text(&mut db)
    .with_durability(Durability::LOW)
    .to(new_contents);
```

## Essential Patterns

### 1. The Check-Before-Update Pattern
Setting an input **always** bumps the revision counter, even if the value is unchanged. Guard updates with an equality check to prevent spurious invalidation of the entire downstream graph.

```rust
if new_val != *input.field(db) {
    input.set_field(db).to(new_val);
}
```

### 2. Derived Durability
Don't hardcode durability per-file. Derive it from the root kind (e.g., Library vs. Project).

### 3. Per-Field Durability
Mix durability levels on a single struct to isolate stable identity/metadata from frequently changing content.

## Common Mistakes

- **Defaulting to LOW for everything:** The single biggest performance killer. Stdlib and dependencies MUST be MEDIUM or HIGH.
- **Setting durability too high:** If a HIGH input changes, Salsa treats it as "the world changed" and revalidates everything.
- **Poisoning the chain:** A single LOW-durability input in a query chain makes the entire chain LOW. Keep high-durability queries isolated from low-durability inputs.
- **Blind setters:** Forgetting the check-before-update guard on config reloads.

## References

- [references/common-patterns.md](references/durability/common-patterns.md) — Implementation details for per-field and derived durability.
- [references/ty-patterns.md](references/durability/ty-patterns.md) — ty's durability-by-file-root strategy.
- [references/rust-analyzer-patterns.md](references/durability/rust-analyzer-patterns.md) — rust-analyzer's durability-by-source-kind strategy.
- [references/salsa-framework.md](references/durability/salsa-framework.md) — Shallow verification algorithm internals and durability tests.
