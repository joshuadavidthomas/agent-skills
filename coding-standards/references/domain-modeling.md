# Domain Modeling

Domain modeling is deciding which distinctions deserve to exist in the codebase. Expose facts that change behavior; hide facts that only come from parsing, storage, transport, frameworks, tests, or implementation strategy.

## Non-negotiables

- A representation must name a real invariant, identity, behavior difference, authority, lifecycle, or boundary proof.
- Raw source, storage, parser, framework, or test shapes do not become domain vocabulary unless callers genuinely make decisions from them.
- Same-shaped values that must not be mixed are distinguished at the type, constructor, parser, or boundary where mistakes occur.
- Identity is not modeled with paths, labels, positions, slugs, provider handles, or serialized forms when the thing must survive changes to those projections.
- Empty domain wrappers are either given semantic force or deleted.

## Representation Is a Commitment

Every named type, record, enum, class, table shape, module, or field becomes vocabulary someone must learn. Representation pays for itself only when it removes repeated reasoning elsewhere.

Represent a concept when it carries force:

- values with the same machine shape must not be mixed
- construction parses, validates, normalizes, or proves trust
- identity must survive rename, move, sync, migration, or projection changes
- lifecycle state changes legal operations
- variants have different behavior or failure modes
- authority or ownership changes what can happen
- callers would otherwise repeat comments, checks, or tribal knowledge

Do not represent a concept just because it exists in a source format, database row, provider response, parser phase, or test fixture.

## Granularity

The right granularity is where the program makes a meaningful decision. A one-off local distinction can stay local; promote it into shared representation when multiple callers must remember it, the wrong value is easy to pass, or the distinction protects an invariant across time or boundaries.

Too coarse hides decisions:

- `string` for several values that cannot be safely mixed
- maps or blobs where callers must remember keys
- nullable fields standing in for lifecycle states
- comments explaining rules the code does not enforce

Too fine invents decisions:

- empty domain wrappers with no invariant, identity, operation, proof, or boundary
- parser or storage details promoted into domain language
- one operation split into named crumbs that are never meaningful alone
- public concepts that exist only to satisfy a framework or test

If a new representation does not make code safer, clearer, or easier to change at the call site, collapse it.

## Native Types and Domain Types

A native type is right when it already tells the truth where it is used. Do not wrap a date, URL, path, number, string, or ID merely to make the code look more modeled. Do refine or distinguish it when the same machine type can be confused, construction proves trust, or the value carries domain rules.

A domain type is right when it adds semantic force:

```text
TenantId          // cannot be mixed with UserId
NonEmptyTitle     // construction proves the invariant
BillingPeriod     // owns calendar/domain rules
ParsedTemplate    // boundary proof: raw text was parsed
```

An empty domain wrapper is the bad middle: a domain-looking wrapper that carries no rule and creates conversion noise. Add the missing rule or delete the wrapper.

## Primitive vs Domain Type Example

Examples use TypeScript-like syntax only for concreteness; translate the shape into the host language's native tools: named types, newtypes, structs, classes, value objects, enums, sum types, smart constructors, or parser results.

Avoid a primitive when two same-shaped values are easy to swap:

```ts
function addUserToTenant(userId: string, tenantId: string) {
  memberships.insert({ userId: tenantId, tenantId: userId });
}
```

Prefer a representation that carries the distinction:

```ts
type UserId = { kind: 'user-id'; value: string };
type TenantId = { kind: 'tenant-id'; value: string };

function addUserToTenant(userId: UserId, tenantId: TenantId) {
  const membership = Membership.create(userId, tenantId);
  memberships.add(membership);
}
```

But do not create a wrapper with no force:

```ts
type DisplayName = { value: string };

function greet(name: DisplayName) {
  return `Hello ${name.value}`;
}
```

If `DisplayName` does not parse, normalize, constrain, preserve identity, or change behavior, use the native string until that force exists.

## Identity vs Projection

Identity answers: “is this the same thing?” Projection answers: “how is it currently named, displayed, stored, addressed, or serialized?”

Do not use paths, labels, slugs, positions, provider handles, or serialized forms as identity when the thing must survive changes to those values. If moves and renames should not create new things, model stable identity separately.

## Boundary Shapes Stay at Boundaries

DTOs, database rows, framework payloads, CLI JSON, webhook events, and serialized messages are edge shapes. They may resemble the domain model; they are not the domain model by default.

Boundary code should translate:

```text
source shape -> domain representation -> target shape
```

Core logic should not keep remembering which fields were validated, which provider emitted the payload, or which storage column implied the state.

For boundary parsing, trust changes, source-of-truth decisions, and provider/framework seams, see `boundaries.md`.

## Parser Detail Example

A template parser may need internal states for quoted and unquoted strings. That does not mean the rest of the system needs `QuotedTemplateString` and `UnquotedTemplateString`.

Expose the concept callers need:

```text
ParsedTemplate
```

Expose quoting only if callers must preserve it, display it, round-trip it, or choose behavior from it. Otherwise it is parser vocabulary, not domain vocabulary.

## Rejected Framings

- **“The source format has this distinction.”** Keep source-format distinctions at the boundary unless callers need them.
- **“A domain type is safer.”** Name the invariant, identity, proof, operation, authority, or boundary it carries.
- **“This matches the database.”** Storage shape is not automatically domain shape. Name the domain decision that depends on it.
- **“This is more explicit.”** Explicit for whom? If no caller decision, invariant, or boundary proof gets clearer, the name is ceremony.
- **“We might need this later.”** Model the concept when the force exists; keep today's shape honest enough to change.

## Review Checklist

- What distinction is this representation making?
- Where does the program make a decision from that distinction?
- What bug, repeated check, or caller burden disappears?
- Is identity separate from projection data?
- Are boundary shapes leaking into core logic?
- Is private scaffolding becoming public vocabulary?
- Would deleting this representation make the code more honest?
