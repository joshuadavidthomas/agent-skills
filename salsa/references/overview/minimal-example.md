# Minimal Complete Example: Calc

A calculator language with incremental compilation (from Salsa's `calc` example).

## ir.rs — Define the Data

```rust
#[salsa::input]
pub struct SourceProgram {
    #[returns(ref)]
    pub text: String,
}

#[salsa::interned]
pub struct FunctionId<'db> {
    #[returns(ref)]
    pub text: String,
}

#[salsa::tracked]
pub struct Function<'db> {
    pub name: FunctionId<'db>,
    #[tracked]
    #[returns(ref)]
    pub body: Expression<'db>,
}

// Expressions are plain Rust — too fine-grained to track
#[derive(Eq, PartialEq, Hash, Debug, salsa::Update)]
pub enum ExpressionData<'db> {
    Number(OrderedFloat<f64>),
    Variable(VariableId<'db>),
    Op(Box<Expression<'db>>, Op, Box<Expression<'db>>),
}

#[salsa::accumulator]
pub struct Diagnostic { /* fields */ }
```

## db.rs — The Database

```rust
#[salsa::db]
#[derive(Default, Clone)]
pub struct CalcDatabase {
    storage: salsa::Storage<Self>,
}

#[salsa::db]
impl salsa::Database for CalcDatabase {}
```

## parser.rs — Tracked Function

```rust
#[salsa::tracked]
fn parse(db: &dyn Db, source: SourceProgram) -> Program<'_> {
    // ...reads source.text(db), returns tracked Program...
}
```

## main.rs — The Driver Loop

```rust
fn main() {
    let db = CalcDatabase::default();
    let source = SourceProgram::new(&db, input_text);

    // First run — computes everything
    compile(&db, source);

    // User edits the source
    source.set_text(&mut db).to(new_text);

    // Second run — Salsa reuses what it can
    compile(&db, source);

    // Collect diagnostics
    let diags = compile::accumulated::<Diagnostic>(&db, source);
}
```
