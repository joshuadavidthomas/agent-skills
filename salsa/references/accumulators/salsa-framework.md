# Salsa Framework — Accumulator Examples and Behavior

The canonical accumulator usage from the Calc example, plus detailed behavior tests.

## Salsa Calc Example — The Reference Implementation

The calc example is the canonical accumulator usage. It demonstrates every aspect of the API.

### Accumulator Definition

```rust
// examples/calc/ir.rs
#[salsa::accumulator]
#[derive(Debug)]
pub struct Diagnostic {
    pub start: usize,
    pub end: usize,
    pub message: String,
}
```

### Pushing from a Parser

```rust
// examples/calc/parser.rs
impl<'db> Parser<'_, 'db> {
    fn report_error(&self) {
        let next_position = match self.peek() {
            Some(ch) => self.position + ch.len_utf8(),
            None => self.position,
        };
        Diagnostic {
            start: self.position,
            end: next_position,
            message: "unexpected character".to_string(),
        }
        .accumulate(self.db);
    }
}
```

### Pushing from a Type Checker

```rust
// examples/calc/type_check.rs
impl<'db> CheckExpression<'_, 'db> {
    fn check(&self, expression: &Expression<'db>) {
        match &expression.data {
            ExpressionData::Variable(v) => {
                if !self.names_in_scope.contains(v) {
                    self.report_error(
                        expression.span,
                        format!("the variable `{}` is not declared", v.text(self.db)),
                    );
                }
            }
            ExpressionData::Call(f, args) => {
                if self.find_function(*f).is_none() {
                    self.report_error(
                        expression.span,
                        format!("the function `{}` is not declared", f.text(self.db)),
                    );
                }
                for arg in args {
                    self.check(arg);
                }
            }
            // ...
        }
    }

    fn report_error(&self, span: Span, message: String) {
        Diagnostic::new(span.start(self.db), span.end(self.db), message)
            .accumulate(self.db);
    }
}
```

### Collecting at the Top Level

```rust
// examples/calc/type_check.rs (tests)
let diagnostics: Vec<Diagnostic> =
    type_check_program::accumulated::<Diagnostic>(db, program);
```

### Incremental Behavior in Tests

The calc example demonstrates that after editing source code, re-collecting accumulated values gives the correct updated diagnostics:

```rust
// Apply edit: fix the undeclared variable
source_program.set_text(&mut db).to(new_source_text.to_string());

let program = parse_statements(db, source_program);
let diagnostics = type_check_program::accumulated::<Diagnostic>(db, program);
// Diagnostics now reflect the edited source — fixed errors disappear
```

## Accumulator Behavior: Deduplication

When a tracked function is called from multiple paths in the dependency graph, its accumulated values appear only once:

```
Call graph:
  push_logs → push_a_logs → (push values for a)
            → push_b_logs → push_a_logs (same call!)
                           → (push values for b)

Result: a's values appear once, not twice
```

```rust
#[salsa::tracked]
fn push_logs(db: &dyn Database, input: MyInput) {
    push_a_logs(db, input);  // pushes "log_a(0 of 2)", "log_a(1 of 2)"
    push_b_logs(db, input);  // calls push_a_logs again, then pushes "log_b(0 of 3)", ...
}

#[salsa::tracked]
fn push_b_logs(db: &dyn Database, input: MyInput) {
    push_a_logs(db, input);  // same function+args as above — deduped
    // ... push b logs ...
}

// push_logs::accumulated::<Log>(db, input) returns:
// ["log_a(0 of 2)", "log_a(1 of 2)", "log_b(0 of 3)", "log_b(1 of 3)", "log_b(2 of 3)"]
// Note: a's logs appear only once despite push_a_logs being called twice
```

However, same function with **different arguments** produces separate values:

```rust
// From tests/accumulate-no-duplicates.rs
push_a_logs(db, MyInput::new(db, 1));  // produces "log a" + calls to b, c, d, e
// Later, from a nested call:
push_a_logs(db, MyInput::new(db, 2));  // produces "log a" + calls to b
// Both "log a" values appear because the inputs differ
```

## Accumulator Behavior: Execution Order

Values follow depth-first execution order:

```rust
fn a(db) {
    Log("log a").accumulate(db);
    b(db);    // pushes "log b", then calls d() which pushes "log d"
    c(db);    // pushes "log c"
    d(db);    // already executed by b — deduped, not added again
}
// Result: ["log a", "log b", "log d", "log c"]
// Note: d appears after b (its caller), not after c
```

## Accumulator Behavior: Chain Through Non-Accumulating Functions

Values propagate through intermediate functions that don't push anything:

```rust
fn push_logs(db) { push_a_logs(db); }
fn push_a_logs(db) { Log("log a").accumulate(db); push_b_logs(db); }
fn push_b_logs(db) { /* no logs */ push_c_logs(db); }
fn push_c_logs(db) { /* no logs */ push_d_logs(db); }
fn push_d_logs(db) { Log("log d").accumulate(db); }

// push_logs::accumulated::<Log>(db) returns ["log a", "log d"]
// Values survive the chain through b and c even though they push nothing
```

## Accumulator Behavior: Reuse Without Re-execution

When a nested function's return value changes but its accumulated values don't, the parent can be skipped:

```rust
#[salsa::tracked]
fn compute(db: &dyn LogDatabase, input: List) -> u32 {
    Integers(0).accumulate(db);  // always pushes 0
    if let Some(next) = input.next(db) {
        let next_integers = compute::accumulated::<Integers>(db, next);
        input.value(db) + next_integers.iter().sum::<u32>()
    } else {
        input.value(db)  // return value changes when input changes
    }
}

// After changing l1's value from 1 to 2:
// compute(l1) re-executes (input changed), but still pushes Integers(0)
// compute(l2) reads accumulated values from l1 — they haven't changed (still [0])
// But l2 must still re-execute because accumulated adds an untracked dependency
```

## Accumulator Behavior: Backdating

Accumulated values update correctly even when the return value is backdated:

```rust
#[salsa::tracked]
fn parse(db: &dyn LogDatabase, input: File) -> u32 {
    match input.content(db).parse::<u32>() {
        Ok(value) => value,
        Err(error) => {
            Log(error.to_string()).accumulate(db);
            0  // fallback value
        }
    }
}

// content = "0" → parse returns 0, no accumulated logs
// content = "a" → parse returns 0 (same!), but now has accumulated error log
// Even though the return value didn't change, accumulated values are updated
```

