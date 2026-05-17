# One Struct Per Entity, Not Parallel Collections

## The Smell

Multiple `HashMap`s (or `Vec`s) sharing keys, where data about the same entity is scattered across parallel data structures.

```rust
// WRONG — parallel maps, nothing guarantees they stay in sync
struct UserDatabase {
    names: HashMap<UserId, String>,
    emails: HashMap<UserId, String>,
    roles: HashMap<UserId, Role>,
    last_login: HashMap<UserId, DateTime>,
}

fn get_user_display(db: &UserDatabase, id: &UserId) -> String {
    let name = db.names.get(id).unwrap();    // might panic if maps are out of sync
    let email = db.emails.get(id).unwrap();
    format!("{} <{}>", name, email)
}
```

Adding a user requires inserting into four maps. Deleting requires removing from four. Forget one → subtle inconsistency bug.

## The Idiomatic Alternative

```rust
struct User {
    name: String,
    email: String,
    role: Role,
    last_login: DateTime,
}

struct UserDatabase {
    users: HashMap<UserId, User>,
}

fn get_user_display(db: &UserDatabase, id: &UserId) -> Option<String> {
    db.users.get(id).map(|user| format!("{} <{}>", user.name, user.email))
}
```

Benefits:
- **Atomicity.** A user either exists completely or not at all.
- **Single lookup.** One hash lookup instead of four.
- **No sync bugs.** Can't forget to update one of the maps.
- **Better cache locality.** Related data is adjacent in memory.

## Migration Strategy

1. Create a struct that holds all the data for a single entity.
2. Create a single `HashMap<Key, YourStruct>`.
3. Migrate insertions: build the struct, insert once.
4. Migrate lookups: single `.get()`, access fields on the result.
5. Fields that are truly optional become `Option` on the struct.

## When Parallel Collections (SoA) Are Legitimate

- **ECS game engines** (`bevy`, `hecs`) deliberately use Struct-of-Arrays for cache efficiency when iterating a single component across thousands of entities. But they use a proper ECS framework, not raw HashMaps.
- **SIMD / vectorization.** Processing one field across many records benefits from contiguous memory for that field.
- **Sparse components.** Not every entity has every field — separate maps avoid wasting memory on `Option` wrappers.
- **Different update cadences.** Data updated at different frequencies or from different sources may reflect genuinely separate concerns.

If you need SoA, use a library designed for it (ECS, arrow/columnar formats) rather than ad-hoc parallel HashMaps.

## Common Source Languages

- **Python** — dicts of lists / pandas DataFrames encourage columnar thinking
- **JavaScript** — object-per-field patterns from JSON APIs
- **Go** — historically no generics; parallel slices with shared indices were common
