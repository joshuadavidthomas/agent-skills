# Complexity

Complexity is the reasoning burden a design imposes beyond the problem itself. Some complexity is essential; this file targets accidental complexity: structure, indirection, generality, and ceremony that carry no meaning.

Examples use TypeScript-like syntax only for concreteness; translate the shape into the host language's native control flow, types, and tests.

## Non-negotiables

- Structure that carries no invariant, policy, boundary, effect, variation, or caller leverage is removed.
- A seam with no translation, volatility, substitution pressure, or boundary ownership is speculative.
- A helper, layer, wrapper, or file split must reduce reader state or caller burden.
- Duplication is kept when the shared abstraction would couple different meanings, owners, lifecycles, or recovery paths.
- Test-only surface area, private scaffolding, and obsolete compatibility glue are not architecture.

## Complexity Is Reader State

Measure complexity by what a maintainer must keep in their head to answer simple questions:

- What can happen?
- Who owns the fact?
- Which state is legal?
- What does this call do besides return a value?
- Where is the rule enforced?
- What breaks if this changes?

Small files are not automatically simple. A system split into many tiny pieces can require more reader state than one direct function.

## Indirection Maze

An indirection maze scatters one operation across helpers, services, managers, factories, adapters, hooks, listeners, or layers. Each piece looks tidy, but the behavior only appears after following the chain.

Collapse or regroup when:

- names describe mechanics instead of domain decisions
- every helper is used once
- helpers must be read in order to understand the caller
- stack depth grows while caller burden stays the same
- tests pin call order instead of behavior

Split again only when a piece owns a real concept, invariant, boundary, effect, or repeated policy.

## Shallow Wrapper

A shallow wrapper adds a name without reducing caller burden.

Common forms:

- `FooService` that forwards to `FooClient`
- repository methods that mirror database calls one-for-one
- adapters that do not adapt anything
- helpers that rename a single expression
- managers/processors/handlers with no domain ownership

Delete the wrapper, use the dependency directly at the boundary, or make the wrapper own real translation, policy, sequencing, error mapping, or resource lifetime.

For deeper module/interface tests and pass-through wrapper examples, see `modules.md`.

## Overengineering

Overengineering is structure beyond the force currently present in the problem.

Watch for:

- strategies with one strategy
- providers with one provider
- config switches nobody can explain
- generic abstractions before real variation exists
- extension points without an extension pressure
- multi-layer architecture around a local operation

Do not confuse “easy to change later” with “already abstract.” Code is easier to change when the current model is honest and small.

## Over-modeling

Over-modeling turns implementation detail into domain vocabulary.

Examples:

- parser phases exposed to callers
- storage rows passed through core logic
- framework payloads named as domain objects
- optimization crumbs given public types
- test fixtures shaping production interfaces

The fix is not under-modeling. Keep real domain concepts; move private scaffolding behind boundaries and interfaces.

## Ceremony

Ceremony is surface area that signals seriousness without adding proof, clarity, or leverage.

Forms:

- files created only to satisfy a pattern
- comments that repeat names
- types that carry no rule
- abstractions that only mirror layers
- boilerplate config for hypothetical variation
- sectioning that makes a small idea look architectural

Ceremony is not the same as explicitness. Good explicitness reveals a rule; ceremony repeats mechanics.

## Wrong DRY

Duplication is cheaper than the wrong abstraction when two pieces only look similar.

Do not merge code until the shared concept is real:

- same shape but different meaning
- same steps but different policy owner
- same fields but different source of truth
- same provider today but different lifecycle tomorrow
- same validation text but different recovery path

A false abstraction couples change for the wrong reason. Let small duplication live until the shared force is visible.

## Speculative Generality

Speculative generality is flexibility before pressure.

Ask:

- What second case exists now?
- Who will use the option?
- What behavior varies independently?
- What boundary or provider is actually volatile?
- What code gets simpler because this exists?

If the answers are hypothetical, delete the flexibility and keep the code easy to change later.

## Worked Example: Helper Maze

Avoid splitting one decision into named crumbs that do not stand alone:

```ts
function shouldProcess(item: ImportItem) {
  return hasRequiredFields(item)
    && isAllowedType(item)
    && isFreshEnough(item)
    && isNotDuplicate(item);
}

function hasRequiredFields(item: ImportItem) { ... }
function isAllowedType(item: ImportItem) { ... }
function isFreshEnough(item: ImportItem) { ... }
function isNotDuplicate(item: ImportItem) { ... }
```

when every helper is used once and the domain rule is “eligible for import.” The reader still has to chase every helper to understand one decision.

Prefer grouping the rule where the decision is made:

```ts
function isEligibleForImport(item: ParsedImportItem, seen: ImportedIds, now: ClockTime): boolean {
  const supportedKind = item.kind === 'invoice' || item.kind === 'credit-note';
  const freshEnough = item.updatedAt > now.minus({ days: 30 });
  const notImported = !seen.has(item.externalId);

  return supportedKind && freshEnough && notImported;
}
```

If required fields are still uncertain, parse or refine the raw item at the boundary first; do not hide raw-shape checks inside eligibility. See `boundaries.md`. Split again only when a check carries reusable domain meaning or a separate policy owner.

## Rejected Framings

- **“This is cleaner.”** Cleaner for which reader question? If the behavior is harder to trace, it is not cleaner.
- **“Small functions are better.”** Small functions help when they name real decisions, not when they hide one operation in fragments.
- **“We might need another implementation.”** Add the seam when variation or boundary pressure exists.
- **“This avoids duplication.”** If the concepts change for different reasons, the abstraction is lying.
- **“This follows the architecture.”** Architecture that adds no local leverage is ceremony.
- **“It is explicit.”** Explicitness that does not reveal a rule is noise.

## Review Checklist

- What must a reader hold in their head to understand this?
- Which names carry decisions, and which narrate mechanics?
- What abstraction would disappear without spreading real work?
- What flexibility has no second case?
- What duplication is cheaper than the abstraction?
- Which private details became public concepts?
- Would collapsing files, helpers, or layers make the model more honest?
