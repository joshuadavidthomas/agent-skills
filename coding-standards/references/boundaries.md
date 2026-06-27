# Boundaries

A boundary is where meaning changes. Treat APIs, storage, files, queues, CLIs, webhooks, framework objects, config, serialization, providers, processes, and runtime hops as translation points, not places to smuggle raw shapes inward.

## Non-negotiables

- Boundary code returns refined internal values, not raw data plus a memory that validation happened.
- Provider, protocol, storage, framework, and DTO vocabulary stays at the edge unless the product domain truly depends on it.
- Compatibility handling names the user, data, protocol, deployment, or public contract that requires it.
- Unknown provider/runtime failures are classified near the boundary before becoming local failures.
- Boundary diagnostics preserve safe context without leaking secrets, credentials, raw request bodies, or full provider payloads.

## Boundary Code Has a Job

Boundary code should turn less-trusted or externally-shaped input into values the rest of the system can reason about.

It usually owns:

- parsing and decoding
- normalization
- trust classification, authentication, and boundary-local authorization checks
- protocol or provider quirks
- version and compatibility handling with a named obligation and removal condition
- error mapping
- source-of-truth decisions
- mapping into internal representations

A boundary that validates and then passes the same raw shape inward has not finished the job.

Boundary authentication does not mean every authorization rule belongs at the edge. The boundary may prove who the actor is and what external claims are trusted. Domain authorization for a state transition belongs with the transition or use case that owns the rule.

## Parse, Then Pass Refined Values

Validation that returns `true` is weak when later code still accepts the original raw value.

Prefer:

```text
raw request -> parsed command -> domain operation
```

over:

```text
validate(raw request)
domain operation(raw request)
```

After a boundary accepts data, core code should not keep remembering which fields were checked, decoded, normalized, authorized, or defaulted.

Examples use TypeScript-like syntax only for concreteness; translate the shape into the host language's native tools.

Avoid validating and then passing raw data inward:

```ts
function httpCreateCustomer(body: unknown) {
  if (!isCreateCustomerBody(body)) return badRequest();

  return createCustomer(body);
}
```

Prefer parsing into the internal command:

```ts
function parseCreateCustomer(body: unknown): ParseOutcome<CreateCustomerCommand> {
  const decoded = decodeCreateCustomerBody(body);
  if (decoded.kind === 'failed') {
    return { kind: 'failed', error: createCustomerBodyError(decoded.error) };
  }

  const displayName = DisplayName.parse(decoded.value.display_name);
  if (displayName.kind === 'failed') {
    return { kind: 'failed', error: displayName.error };
  }

  return { kind: 'parsed', value: { displayName: displayName.value } };
}

function httpCreateCustomer(body: unknown) {
  const command = parseCreateCustomer(body);
  if (command.kind === 'failed') return badRequest(command.error);

  return createCustomer(command.value);
}
```

The internal operation never learns the wire field name, optionality, decoding rules, or validation memory.

If the boundary accepts old and new shapes for compatibility, translate both into one internal command at the edge. Name the compatibility obligation and removal condition; otherwise delete the old parser. See `maintainability.md`.

## Source Shape Is Not Domain Shape

DTOs, database rows, framework payloads, CLI JSON, provider responses, and webhook events are shaped by transport, storage, compatibility, or third-party contracts. They may resemble domain data; they are not domain data by default.

Map deliberately:

```text
source shape -> internal model -> target shape
```

This translation is the anti-corruption layer. It protects the internal model from external vocabulary, and it protects external contracts from internal churn. It is not a wrapper whose only job is to hide a dependency; it changes shape, trust, failure model, ownership, or source-of-truth semantics.

Do not let one provider's field names, nullability, pagination, timestamps, IDs, or error codes become the language of the whole system unless the product truly depends on them.

## Native Types at the Edge

Use dependency-native, framework-native, provider-native, or protocol-native types where they are actually native: at the edge.

Do not wrap a dependency just to pretend it is gone. Wrap or adapt it when the code needs translation, policy, error mapping, source-of-truth protection, or a narrower contract.

A wrapper that merely forwards is a shallow wrapper. An adapter that translates meaning is a boundary.

## Source of Truth

When systems disagree, decide who owns the fact.

Ask per fact:

- Which system is authoritative?
- Which values are projections, caches, views, local intents, or working copies?
- Which side owns conflicts?
- Which changes must be persisted before effects run?
- Which stale data is acceptable, and for how long?

Without a source-of-truth decision, sync code becomes scattered exceptions and reconciliation folklore.

```text
CRM owns legal customer name.
Billing owns invoice delivery email.
Search owns only projections.
```

When CRM and billing disagree, sync code updates the projection or raises a conflict; it does not let whichever payload arrived last become truth.

## Trust Changes

Crossing a boundary often changes trust. External input, persisted data, cached data, generated code, config, migrations, and dependency output all need different assumptions.

Trusted once does not mean trusted forever. Data can become stale, revoked, migrated, partially written, or invalid under a newer schema. Name what the boundary proves now.

## Boundary Failures

Boundary failures should be translated near the boundary while the source context is still available.

Keep enough context to diagnose:

- operation
- provider or protocol
- entity identity
- field or version
- retry state
- upstream status or failure category

Do not leak secrets, credentials, raw untrusted payloads, or private provider details into user-facing errors. Do not erase causes so early that debugging becomes archaeology.

For failure-shape granularity, defects, operational causes, cancellation, and safe diagnostics, see `error-handling.md`.

## Worked Example: Provider Payload

Avoid leaking provider vocabulary inward:

```text
handleWebhook(provider_payload)
syncUser(provider_payload.user.id, provider_payload.user.display_name)
```

Core sync logic now knows provider field names, ID shape, nullability, and payload layout.

Prefer boundary translation:

```text
ProviderUserPayload -> ExternalAccountLink + UserProfileProjection
syncUserProfile(accountLink, profileProjection)
```

The boundary owns provider IDs, timestamp parsing, optional display fields, and provider error mapping. Core sync logic reasons about internal identity and profile projection instead of memorizing the provider payload.

## Rejected Framings

- **“This is just the API shape.”** Good; keep it at the API edge.
- **“The value was already validated.”** Pass the refined value inward, not raw data plus a memory of validation.
- **“This wrapper hides the dependency.”** Hiding is not enough. Name the translation, policy, or contract it owns.
- **“Both systems are sources of truth.”** Usually one owns each fact; the other owns a projection, cache, queue, local intent, or conflict.
- **“The database already guarantees it.”** Then storage is the boundary for that invariant; do not pretend earlier code owns the same proof.

## Review Checklist

- Where does data change trust, protocol, runtime, storage, ownership, or meaning?
- What refined value leaves the boundary?
- Which source shape is leaking into core logic?
- What is the source of truth for each fact?
- What provider/framework quirks should stay at the edge?
- Are boundary failures translated with useful context?
- Does the adapter translate meaning or merely forward calls?
