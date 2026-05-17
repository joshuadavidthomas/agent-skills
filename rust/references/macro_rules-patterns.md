# macro_rules! patterns you should reach for first

This file is not a tutorial. It is a small set of patterns that prevent the most common macro_rules failures: double evaluation, bad diffs, hygiene breakage, and unhelpful errors.

**Authority:** Rust Reference “Macros by example”; TLBORM (patterns, building blocks).

## 1) Accept trailing commas in lists

```rust
macro_rules! my_list {
    ( $( $x:expr ),* $(,)? ) => {{
        vec![ $( $x ),* ]
    }}
}
```

Use `$(,)?` for the optional final comma, and keep the main repetition `,`-separated.

## 2) Single-evaluate `$expr` inputs

Never paste an `$expr:expr` twice unless you first bind it once.

```rust
macro_rules! ensure {
    ($cond:expr, $err:expr $(,)?) => {{
        if !$cond {
            return Err($err);
        }
    }};
}
```

If you need the value, bind it:

```rust
macro_rules! with_parsed {
    ($expr:expr, |$name:ident| $body:expr $(,)?) => {{
        let $name = $expr; // evaluated exactly once
        $body
    }};
}
```

For more complex control flow, prefer `match` so you can avoid temporary name collisions and keep borrow scopes obvious:

```rust
macro_rules! ok_or_return {
    ($opt:expr, $err:expr $(,)?) => {{
        match $opt {
            Some(v) => v,
            None => return Err($err),
        }
    }};
}
```

## 3) Prefer fragment specifiers over `tt`

If you can say what you mean, say it.

- `path` for `foo::bar::Baz`
- `ty` for types
- `expr` for expressions
- `meta` for attribute meta content

Using `tt` everywhere makes matching brittle and error messages worse. Use `tt` only for “token muncher” style macros (custom DSLs, recursive parsing).

## 4) `$crate` for exported macros

If the macro expansion refers back into your own crate, use `$crate`.

```rust
#[macro_export]
macro_rules! my_macro {
    () => {{
        $crate::internal::do_the_thing()
    }};
}
```

This keeps the expansion correct even if your crate is renamed in Cargo.toml.

Also prefer absolute core/std paths for builtins used by the expansion:

```rust
macro_rules! my_option {
    ($x:expr) => {{
        ::core::option::Option::Some($x)
    }};
}
```

## 5) Make errors loud and local with `compile_error!`

If you can recognize an invalid form, match it and emit a good message.

```rust
macro_rules! only_ident {
    ($name:ident) => { /* ... */ };
    ($($other:tt)*) => {
        ::core::compile_error!("expected an identifier: only_ident!(name)")
    };
}
```

This is often better than relying on “no rules expected this token”.

## 6) Avoid local ambiguity by adding delimiters or keywords

This fails:

```rust,compile_fail
macro_rules! bad {
    ($($i:ident)* $j:ident) => {};
}
```

`macro_rules!` does not do lookahead. Fix by separating modes with a delimiter or keyword:

```rust
macro_rules! good {
    (many: $( $i:ident )* ; last: $j:ident $(,)?) => {};
}
```

## 7) Forwarding matched fragments has restrictions

When you forward `$e:expr` into another macro, that second macro sees an opaque expr AST and cannot match literal tokens inside it. If you need literal-token matching, match `tt` (or restructure the API).

**Authority:** Rust Reference “Forwarding a matched fragment”.

## 8) Push-down accumulation (token muncher) via internal `@rules`

When you need to parse a sequence of tokens into a structured result, use the TLBORM “token muncher” pattern:

- Expose a small public entry rule.
- Recurse through the remaining tokens via internal rules prefixed with `@...`.
- Thread an explicit accumulator so you never need macro “lookahead”.

Example: count identifiers without ambiguity (accumulator is an `expr`):

```rust
macro_rules! count_idents {
    (@acc $n:expr; ) => { $n };
    (@acc $n:expr; $head:ident $( $tail:ident )* ) => {
        count_idents!(@acc ($n + 1); $( $tail )* )
    };
    ( $( $i:ident )* ) => {
        count_idents!(@acc 0; $( $i )* )
    };
}

const N: usize = count_idents!(a b c);
```

Defaults:

- Use an explicit delimiter/keyword before internal rules (the `@acc ...;` above) so the matcher is never locally ambiguous.
- Keep the public surface small; internal rules are implementation details.
- If you find yourself inventing a large custom DSL with lots of `tt`, stop and reconsider: prefer Rust fragments + normal types, or move to a proc macro if you truly need item-level structure.
