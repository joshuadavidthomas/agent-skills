# Cycle Handling Patterns

This file contains detailed implementation examples and real-world patterns for handling cycles in Salsa, migrated from the main `SKILL.md`.

## Detailed Examples

### Example: Graph Shortest Path (Fixed-Point)

Computing minimum cost to a start node in a potentially cyclic graph. This uses `cycle_initial` to return a "bottom" value (`usize::MAX`) that iteration refines downward.

```rust
#[salsa::tracked(cycle_initial=max_initial)]
fn cost_to_start<'db>(db: &'db dyn Database, node: Node<'db>) -> usize {
    let mut min_cost = usize::MAX;
    let graph = create_graph(db, node.graph(db));

    for edge in node.edges(db) {
        if edge.to == 0 {
            min_cost = min_cost.min(edge.cost);
        }
        let edge_cost = cost_to_start(db, graph.nodes[edge.to]);
        if edge_cost == usize::MAX {
            continue; // Cycle — skip this edge
        }
        min_cost = min_cost.min(edge.cost + edge_cost);
    }
    min_cost
}

fn max_initial(_db: &dyn Database, _id: salsa::Id, _node: Node) -> usize {
    usize::MAX // Bottom value: "unreachable" — iteration will find cheaper paths
}
```

### Example: Simple Fallback (Fallback Result)

Simple two-query cycle returning a static value.

```rust
#[salsa::tracked(cycle_result=cycle_result)]
fn query_a(db: &dyn salsa::Database) -> i32 {
    query_b(db) + 1
}

#[salsa::tracked(cycle_result=cycle_result)]
fn query_b(db: &dyn salsa::Database) -> i32 {
    query_a(db)
}

fn cycle_result(_db: &dyn salsa::Database, _id: salsa::Id) -> i32 {
    1  // Both participants get 1, regardless of call order
}
```

## Real-World Patterns

### Pattern: Error Type Fallback (rust-analyzer)

The most common pattern in rust-analyzer — return an error type when a cycle is detected.

```rust
#[salsa::tracked(returns(ref), cycle_result = infer_cycle_result)]
pub fn for_body(db: &dyn HirDatabase, def: DefWithBodyId) -> InferenceResult {
    infer_query(db, def)
}

fn infer_cycle_result(
    db: &dyn HirDatabase, _: salsa::Id, _: DefWithBodyId,
) -> InferenceResult {
    InferenceResult {
        has_errors: true,
        ..InferenceResult::new(Ty::new_error(db, ErrorGuaranteed))
    }
}
```

### Pattern: Divergent Sentinel (ty)

ty tags the cycle's bottom value with the cycle's `salsa::Id`, allowing downstream code to detect and filter out self-referential types.

```rust
fn definition_cycle_initial<'db>(
    db: &'db dyn Db, id: salsa::Id, definition: Definition<'db>,
) -> DefinitionInference<'db> {
    DefinitionInference::cycle_initial(
        definition.scope(db),
        Type::divergent(id),  // Tagged with cycle id for later detection
    )
}
```

### Pattern: Domain-Specific Error Cycle Initial (ty)

For class hierarchy resolution, return a domain-specific error rather than a type.

```rust
fn try_mro_cycle_initial<'db>(
    db: &'db dyn Db, _id: salsa::Id,
    class: StaticClassLiteral<'db>,
    specialization: Option<Specialization<'db>>,
) -> Result<Mro<'db>, StaticMroError<'db>> {
    Err(StaticMroError::cycle(db, class.apply_optional_specialization(db, specialization)))
}
```

### Pattern: Per-Expression Cycle Normalization (ty)

When inference results contain many sub-types, normalize each one individually.

```rust
fn cycle_normalized(
    mut self, db: &'db dyn Db,
    previous_inference: &ScopeInference<'db>,
    cycle: &salsa::Cycle,
) -> ScopeInference<'db> {
    for (expr, ty) in &mut self.expressions {
        let previous_ty = previous_inference.expression_type(*expr);
        *ty = ty.cycle_normalized(db, previous_ty, cycle);
    }
    self
}
```

### Pattern: iteration-Limited Recovery (Salsa tests)

Use `cycle.iteration()` to impose custom iteration limits.

```rust
fn cycle_recover(
    _db: &dyn Db, cycle: &salsa::Cycle,
    last: &Value, value: Value, _inputs: Inputs,
) -> Value {
    if &value == last { value }                           // Converged
    else if value.is_out_of_bounds() { Value::OutOfBounds } // Domain error
    else if cycle.iteration() > 3 { Value::TooManyIterations } // Bail
    else { value }                                        // Keep iterating
}
```

### Pattern: "Is there a cycle?" Heuristic (Cairo)

Used for declaration cycles, type size computation, trait resolution, deref chains.

```rust
#[salsa::tracked(cycle_result=final_contains_call_cycle_handle_cycle)]
fn final_contains_call_cycle(db: &dyn Database, function_id: ConcreteFunctionWithBodyId) -> Maybe<bool> {
    for callee in db.lowered_direct_callees_with_body(function_id, ...)? {
        if db.final_contains_call_cycle(*callee)? {
            return Ok(true);
        }
    }
    Ok(false)
}

fn final_contains_call_cycle_handle_cycle(
    _db: &dyn Database, _id: salsa::Id, _function_id: ConcreteFunctionWithBodyId,
) -> Maybe<bool> {
    Ok(true)  // A cycle in the call graph means "yes, contains a cycle"
}
```

### Pattern: Import Resolution Convergence (Cairo/Fe)

Used where the initial "unknown" state refines as more modules resolve.

```rust
#[salsa::tracked(
    returns(ref),
    cycle_fn=module_imported_modules_cycle_fn,
    cycle_initial=module_imported_modules_initial,
)]
fn module_imported_modules(db: &dyn Database, module_id: ModuleId) -> OrderedHashMap<ModuleId, ImportData> { ... }

fn module_imported_modules_initial(
    db: &dyn Database, _id: salsa::Id, module_id: ModuleId,
) -> OrderedHashMap<ModuleId, ImportData> {
    // Bottom value: only direct imports (no glob re-exports resolved yet)
    // ... computes partial result without following glob imports ...
}
```

## ty's Monotonicity Strategy

ty ensures monotonicity by **unioning** each iteration's result with the previous:

```rust
// From Type::cycle_normalized — the core convergence strategy
match (previous, self) {
    (Type::GenericAlias(prev), Type::GenericAlias(curr))
        if prev.origin(db) == curr.origin(db) => self,
    (Type::FunctionLiteral(prev), Type::FunctionLiteral(curr))
        if prev.definition(db) == curr.definition(db) => self,
    _ => {
        if has_divergent_in_cycle(previous) && !has_divergent_in_cycle(self) {
            self
        } else {
            UnionType::from_elements_cycle_recovery(db, [previous, self])
        }
    }
}
```
