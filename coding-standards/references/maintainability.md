# Maintainability

Maintainability is the ability to understand, repair, and change code without rediscovering the whole system. It comes from stable contracts, local reasoning, honest boundaries, behavior evidence, and deletion of obsolete shape. It does not come from maximum abstraction.

Examples use TypeScript syntax for concreteness. Translate the shapes into the host language's native tools.

## Non-negotiables

- Protect real contracts: public APIs, persisted data, protocols, documented behavior, CLI flags, environment/config shape, queue messages, user-visible flows, and active integrations.
- Do not protect accidental structure: private helpers, file layout, old names, test choreography, framework leakage, or obsolete implementation detail.
- Before deleting or replacing weird code, identify the real obligation it may encode. If the obligation is real, preserve it in a clearer shape. If it is gone, delete it.
- Refactors that claim behavior preservation need evidence through real seams, not confidence from private helper tests.
- Compatibility glue names the user, data, protocol, deployment, or public contract that requires it and the condition for removing it.
- When a contract intentionally changes and no compatibility obligation remains, move to the end-state shape. Do not leave aliases, dual parsers, bridge routes, or fallback fields behind.
- Temporary scaffolding has a removal condition. Permanent “temporary” code is just complexity with a bad name.

## Contracts vs Internals

A contract is what callers and stored data can rely on. Internals are allowed to change.

Contracts include:

- exported functions, classes, types, endpoints, events, jobs, and commands
- database rows, migrations, files, queue messages, cache keys, and serialized state
- CLI flags, config fields, environment variables, URLs, status codes, and exit codes
- documented behavior, user-visible flows, permissions, and support/runbook expectations
- performance or ordering promises callers depend on

Internals include private helpers, private file organization, local variable names, one-off parsing phases, dependency choices behind adapters, and tests that only mirror implementation choreography.

If changing a helper breaks three callers, ask whether the helper was accidentally public. If changing internals breaks many tests but no behavior changed, the tests are protecting choreography instead of the contract.

## Keep Compatibility at the Boundary

Compatibility is a boundary concern unless the old shape is the internal model.

Avoid carrying old and new names through core logic:

```ts
type CreateCustomerCommand = {
  name?: string;
  displayName?: string;
};

async function createCustomer(command: CreateCustomerCommand) {
  const displayName = command.displayName ?? command.name;
  if (!displayName) return { kind: 'rejected', reason: 'missing-name' };

  return customers.insert({ displayName });
}
```

This makes every caller and test learn a migration detail.

Prefer translating compatibility shapes at the edge:

```ts
type CreateCustomerCommand = {
  displayName: DisplayName;
};

function parseCreateCustomerV1(body: unknown): ParseOutcome<CreateCustomerCommand> {
  const parsed = parseV1Body(body);
  if (parsed.kind === 'failed') return parsed;

  const displayName = DisplayName.parse(parsed.value.name);
  if (displayName.kind === 'failed') {
    return { kind: 'failed', error: displayName.error };
  }

  return { kind: 'parsed', value: { displayName: displayName.value } };
}

function parseCreateCustomerV2(body: unknown): ParseOutcome<CreateCustomerCommand> {
  const parsed = parseV2Body(body);
  if (parsed.kind === 'failed') return parsed;

  const displayName = DisplayName.parse(parsed.value.displayName);
  if (displayName.kind === 'failed') {
    return { kind: 'failed', error: displayName.error };
  }

  return { kind: 'parsed', value: { displayName: displayName.value } };
}

async function createCustomer(command: CreateCustomerCommand) {
  return customers.insert({ displayName: command.displayName });
}
```

If version 1 has no real user, data, or public-contract obligation, delete `parseCreateCustomerV1`. Do not keep it “just in case.”

For boundary translation rules, see `boundaries.md`; for migration/refactor evidence, see `verification.md`.

## Chesterton's Fence

A strange branch, sleep, retry, field, constraint, adapter, or test may encode a real incident. Do not remove it because it looks ugly; do not keep it because nobody remembers why it exists.

Use this sequence:

1. Find the original reason: issue, comment, test, migration, incident, support case, provider behavior, data shape, or commit/change note.
2. Classify the reason: current contract, historical migration, provider quirk, performance guard, security rule, test workaround, or dead code.
3. Preserve the requirement in a clearer place when it is still real.
4. Characterize behavior first when the reason matters but is unclear.
5. Delete the fence when no obligation remains.

Avoid anonymous special cases:

```ts
if (invoice.total.cents === 0) {
  return;
}
```

Prefer naming the rule where future readers can verify it:

```ts
function decideInvoiceCharge(invoice: Invoice): ChargeDecision {
  if (invoice.total.cents === 0) {
    return {
      kind: 'skip',
      reason: 'zero-total-invoices-do-not-enter-payment-provider',
    };
  }

  return { kind: 'charge', request: chargeRequestFor(invoice) };
}
```

Then cover the rule with a behavior test. If the rule was only a workaround for deleted code or migrated data that no longer exists, remove it.

## Refactoring Discipline

A refactor changes structure while preserving behavior. A behavior change changes the contract. Mixing them is allowed only when the evidence stays clear.

Before a risky refactor:

- name the contract that must stay true
- characterize poorly understood behavior through the public seam
- identify which tests protect behavior and which only protect private choreography
- move or create a seam only when the current change needs it
- remove any staging helpers after the end-state shape is in place

Avoid refactors that first export internals for tests:

```ts
export function normalizeProviderPayloadForTestOnly(payload: ProviderPayload) {
  // private choreography made public
}
```

Prefer testing through the surface that owns the behavior:

```ts
const outcome = await syncProviderProfile(providerPayload);

expect(outcome).toEqual({ kind: 'synced', userId });
expect(await profiles.load(userId)).toEqual(expectedProfile);
```

If the behavior is too hard to reach, fix the seam or boundary. Do not publish private steps as production API.

See `verification.md` for characterization tests and evidence matching.

## Clean End-State Changes

When the intended contract changes, do the change directly enough that the codebase ends in one coherent shape.

Prefer an end-state rename that updates the model everywhere:

```ts
type AccountProfile = {
  displayName: DisplayName;
};
```

Avoid permanent dual vocabulary:

```ts
type AccountProfile = {
  name?: string;
  displayName?: string;
};

function getDisplayName(profile: AccountProfile) {
  return profile.displayName ?? profile.name ?? 'Unknown';
}
```

Dual shapes are acceptable only for a named compatibility obligation: existing persisted data, active API users, rolling deploys, queued messages, external integrations, or documented contracts. Keep the dual shape at the boundary, add migration or translation tests, and name the removal condition.

## Temporary Code and Migration Scaffolding

Temporary code is honest only when it can be removed.

A compatibility block should name:

- the obligation it protects
- the boundary where it belongs
- the evidence that it is still needed
- the removal condition
- the tests that fail if it is removed too early

Avoid vague scaffolding:

```ts
// TODO: remove later
const displayName = row.display_name ?? row.name;
```

Prefer a bounded compatibility adapter:

```ts
function readAccountProfile(row: AccountProfileRow): AccountProfile {
  if (row.schemaVersion === 1) {
    return migrateV1Profile(row);
  }

  return readCurrentProfile(row);
}
```

with a migration check or deployment condition that tells maintainers when `migrateV1Profile` can be deleted. If there is no condition, the code is not temporary.

## Local Convention and Coherent Shape

Follow local convention when it communicates the model and keeps changes predictable. Break convention when it preserves a lie, leaks a boundary shape, hides effects, or forces callers to remember obsolete rules.

Do not introduce a one-off style because it is personally cleaner. If the old pattern is wrong, move the local area to the better shape. If the old pattern is merely different, keep the area coherent.

A small inconsistent improvement can be worse than a larger coherent change when it creates two local idioms that future changes must reconcile.

## Comments and Documentation

Comments are maintainability tools when they preserve facts code cannot express well:

- why a rule exists
- which contract or incident it protects
- why a tradeoff was chosen
- what removal condition applies
- which external behavior or provider quirk forced the shape

Avoid comments that narrate mechanics, excuse unclear code, or preserve stale history.

```ts
// Stripe retries webhooks for up to three days. Keep processed event IDs
// until the retry window expires so duplicate delivery stays idempotent.
await processedWebhookIds.remember(event.id, { ttl: days(3) });
```

That comment earns its keep: it names the external contract and the invariant.

## Rejected Framings

- **“We should keep both shapes to be safe.”** Name the user, data, protocol, or deployment that needs both. If none exists, keep one shape.
- **“It is only internal.”** Internal code can still be an accidental contract if callers, tests, migrations, or operators depend on it.
- **“No one knows why this exists.”** That is a research task, not a reason to keep or delete blindly.
- **“This refactor is behavior-preserving.”** Show behavior-level evidence through the real seam.
- **“We can remove the cleanup later.”** Later needs a removal condition.
- **“Consistency does not matter because this is better.”** Better locally can be worse globally if it creates two idioms for one concept.
- **“The test broke, so behavior changed.”** Maybe the test pinned choreography. Check the caller-visible claim.

## Review Checklist

- What contract must this change preserve or intentionally change?
- Is the code protecting a real obligation or accidental structure?
- Does compatibility glue name its user/data/protocol/deployment and removal condition?
- Are old and new shapes kept at the boundary instead of leaking through core logic?
- Is weird code understood, characterized, clarified, or deleted?
- Does refactoring evidence prove behavior through a real seam?
- Did the change leave temporary helpers, aliases, flags, bridge routes, or dual fields behind?
- Does the local area end in one coherent shape?
- Do comments explain durable constraints instead of narrating mechanics?
