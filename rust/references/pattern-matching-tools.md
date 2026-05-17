# Right-Size Your Pattern Matching

## The Smell

Using a full `match` expression when you only care about one variant.

```rust
// WRONG — unnecessarily verbose
match user.email {
    Some(email) => send_welcome(&email),
    _ => {},
}

// WRONG — match to extract + bind, discarding other cases
let name = match user.nickname {
    Some(n) => n,
    None => return Err(Error::NoNickname),
};
```

## The Right Tool for the Job

### `matches!` — boolean check (is it this variant?)

```rust
let is_admin = matches!(user.role, Role::Admin);
let is_high_priority = matches!(task.priority, Priority::High | Priority::Critical);
```

### `if let` — one variant, discard the rest

```rust
if let Some(email) = user.email {
    send_welcome(&email);
}

if let Ok(Command::Quit) = parse_command(input) {
    break;
}
```

### `let ... else` — one variant, bail on the rest

```rust
let Some(name) = user.nickname else {
    return Err(Error::NoNickname);
};
// `name` is bound for the rest of the scope
process(name);
```

`let-else` is powerful because it inverts nesting:

```rust
// WRONG — indentation creep
if let Some(user) = get_user(id) {
    if let Some(email) = user.email {
        if let Ok(validated) = validate_email(&email) {
            send_to(validated);
        }
    }
}

// RIGHT — flat control flow
let Some(user) = get_user(id) else { return };
let Some(email) = user.email else { return };
let Ok(validated) = validate_email(&email) else { return };
send_to(validated);
```

### `while let` — repeated extraction

```rust
while let Some(item) = stack.pop() {
    process(item);
}
```

### `match` — two or more variants, or exhaustiveness matters

```rust
match event {
    Event::Click { x, y, button: MouseButton::Left } => handle_left_click(x, y),
    Event::Click { button: MouseButton::Right, .. } => show_context_menu(),
    Event::Scroll { delta, .. } => scroll(delta),
    _ => {},
}
```

## Summary Table

| Variants Handled | Tool |
|---|---|
| Boolean check (is it this variant?) | `matches!()` |
| One variant, discard rest | `if let` |
| One variant, bail on rest | `let ... else` |
| Repeated extraction | `while let` |
| Two+ variants | `match` |
| All variants (exhaustive) | `match` without `_` |

## When Full `match` Is Better

- **Two or more variants need handling.** Clearer than chained `if let`/`else if let`.
- **Exhaustiveness matters.** Adding a new enum variant triggers a compiler warning with `match` but not with `if let`.
- **Complex destructuring.** Binding multiple fields across several variants.

## Common Source Languages

- **C / Go / Java** — switch statements enumerate all cases; no `if let` equivalent
- **Python** — `match`/`case` (3.10+) is new; `if isinstance()` chains are the norm
- **JavaScript** — no pattern matching; `if/else` chains or switch statements
