# Error Handling

Expected failures are part of the contract. Defects are not. Operational causes need enough context to diagnose without becoming the caller's whole error model.

Examples use TypeScript syntax for concreteness. Translate the shapes into the host language's native tools: result values, sum types, checked outcomes, documented exceptions, tagged errors, or framework-native failures.

## Non-negotiables

- If callers can recover, branch, retry, compensate, ask for different input, or render materially different safe copy because the consequence or next action differs, the failure is visible in the local contract.
- Defects stay loud: impossible branches, broken invariants, deployment/runtime misconfiguration after bootstrap validation, and unimplemented paths are not ordinary recovery.
- Boundary code classifies unknown thrown/raised values, rejected async work, status codes, and provider errors before translating them.
- Module interfaces expose precise local failures, not a broad application error blob.
- Raw strings, context-free exception/error values, and catch-all failure shapes are not contracts.
- Required lookup absence is a failure. Optional lookup is explicit in the operation name or return type.
- Error messages, logs, traces, snapshots, and panic summaries do not include secrets, credentials, raw request bodies, full provider payloads, or arbitrary serialized causes.

## Failure Contracts

Design the failure shape with the success shape. Do not implement the happy path first and bolt errors on later.

Prefer a caller-visible outcome:

```ts
type FindActiveUserOutcome =
  | { kind: 'found'; user: ActiveUser }
  | { kind: 'not-found'; email: EmailAddress }
  | { kind: 'unavailable'; failure: OperationalFailure };

async function findActiveUser(email: EmailAddress): Promise<FindActiveUserOutcome> {
  // lookup implementation
}
```

Avoid hidden ordinary failures:

```ts
async function findActiveUser(email: EmailAddress): Promise<ActiveUser> {
  throw new Error('not found');
}
```

A framework may require throwing at its boundary. Keep the local module precise, then translate at the adapter:

```ts
const outcome = await findActiveUser(email);

if (outcome.kind === 'not-found') {
  throw httpNotFound('User not found');
}
```

Do not let the framework's error style become the core contract.

## Expected Failure vs Defect

Expected failures are normal outcomes the caller may handle:

- invalid user input
- parse failure
- authorization denial
- required value not found
- conflict or duplicate request
- rejected state transition
- cancellation or timeout the caller owns
- dependency unavailable when the interface promises a recoverable outcome
- user-supplied CLI, project, file, request, or environment config the caller can correct

Defects are bugs or violated assumptions:

- impossible branch
- corrupt internal state
- invariant broken after construction
- unhandled case in a closed set
- deployment/runtime configuration missing or invalid after bootstrap validation
- temporary not-implemented path during development

Classify config by audience and ownership. A service missing required deployment configuration at startup is a defect or deploy-time failure. A CLI command reading a project config file, an API parsing request config, or an installer checking user-provided settings should return an expected boundary failure with file/field/path details and a safe next action.

Use defects to stop bad assumptions, not to avoid modeling ordinary failure.

```ts
function renderPaymentState(state: PaymentState): string {
  switch (state.kind) {
    case 'pending': return 'Pending';
    case 'paid': return 'Paid';
    case 'failed': return 'Failed';
  }

  return shouldNeverHappen(state);
}
```

## Operational Causes

Operational failure names the cause class: network, disk, provider, rate limit, resource exhaustion, lock contention, malformed dependency data, or runtime interruption. It may be exposed as an expected failure at a boundary, but callers should not have to understand every provider detail.

Prefer translating provider failures into local failure tags with safe context:

```ts
type UserStoreUnavailable = {
  kind: 'user-store-unavailable';
  operation: 'findActiveUser';
  provider: 'postgres';
  diagnosticId: DiagnosticId;
};
```

The caller branches on `kind`. The caller-visible failure keeps `operation`, `provider`, safe IDs, retry state, and typed tags. Keep the original cause in an internal diagnostic channel, attached exception chain, trace/span, or non-serialized field only when that surface is guaranteed not to cross a trust, process, API, or human-facing boundary. If the failure object may be logged, returned, rendered, persisted, or serialized, carry a safe cause summary or diagnostic ID instead of the raw cause.

## Boundary Catch and Classification

Only boundary, adapter, rendering, or orchestration code should catch unknown failures as a normal integration task.

Prefer:

```ts
async function fetchUserProfile(id: ProviderUserId): Promise<FetchUserProfileOutcome> {
  try {
    const response = await provider.fetchUser(id);
    return parseProviderProfile(response);
  } catch (cause: unknown) {
    const diagnosticId = recordFailureCause(cause, {
      operation: 'fetchUserProfile',
      provider: 'user-api',
      providerUserId: id,
    });

    if (isCancellation(cause)) {
      return { kind: 'cancelled', operation: 'fetchUserProfile', diagnosticId };
    }

    if (isRateLimit(cause)) {
      return {
        kind: 'rate-limited',
        operation: 'fetchUserProfile',
        retryAfter: retryAfter(cause),
        diagnosticId,
      };
    }

    return {
      kind: 'provider-unavailable',
      operation: 'fetchUserProfile',
      provider: 'user-api',
      diagnosticId,
    };
  }
}
```

Avoid:

```ts
catch (error) {
  logger.error(error.message);
  throw error;
}
```

The avoided version assumes the thrown value is an `Error`, may leak the message, and preserves no local failure contract.

## Lookup Absence

Required lookup absence is a typed failure:

```ts
type LoadInvoiceOutcome =
  | { kind: 'loaded'; invoice: Invoice }
  | { kind: 'not-found'; invoiceId: InvoiceId }
  | { kind: 'store-unavailable'; failure: OperationalFailure };
```

Optional lookup is explicit:

```ts
type MaybeFindCouponOutcome =
  | { kind: 'found'; coupon: Coupon }
  | { kind: 'absent' }
  | { kind: 'store-unavailable'; failure: OperationalFailure };
```

Do not use `null`, `nil`, `None`, `undefined`, empty strings, or empty collections when the caller must distinguish absent, not found, not loaded, denied, unavailable, and invalid.

## Error Granularity

Expose the failures the caller can act on. Hide the failures it cannot.

Too broad:

```ts
type CreateAccountOutcome =
  | { kind: 'created'; account: Account }
  | { kind: 'failed'; error: AppError };
```

Better:

```ts
type CreateAccountOutcome =
  | { kind: 'created'; account: Account }
  | { kind: 'rejected'; reason: 'email-taken' | 'weak-password' }
  | { kind: 'unavailable'; failure: OperationalFailure };
```

Do not expose ten provider-specific failure variants when the caller can only report “temporarily unavailable.” Do not collapse semantically different domain failures into one provider-shaped blob.

Split failure variants when at least one caller decision changes:

- retry now, retry later, do not retry, or require idempotency/duplicate protection
- ask for different input, show a field-level correction, or preserve a draft
- report a different safe human-facing consequence: saved, not saved, charged, not charged, sent, not sent, unchanged, or unknown
- choose a different status code, exit code, queue disposition, compensation, rollback, or state transition
- use a different security posture, such as generic copy instead of specific detail
- route to a different owner, alert, support path, or operational runbook

Merge failures when callers take the same action and only diagnostics differ. Keep provider-specific detail in safe diagnostics, not in the branch shape.

## Safe Diagnostics

Error context should help debugging without dumping raw data.

Prefer stable safe fields:

```ts
return {
  kind: 'provider-unavailable',
  operation: 'authorizePayment',
  provider: 'stripe',
  orderId,
  diagnosticId,
};
```

Avoid raw context:

```ts
throw new Error(`Payment failed: ${JSON.stringify({ request, response, env })}`);
```

Safe fields include operation names, dependency names, stable domain IDs, state tags, retry counts, and typed failure tags. Unsafe fields include tokens, credentials, request bodies, raw provider payloads, environment dumps, and arbitrary serialized causes.

Do not put raw causes on failure values that can be rendered, serialized, persisted, returned over an API, snapshotted, or logged by generic middleware.

## Human-Facing Error Messages

Good error contracts preserve the facts a UI, CLI, API response, operator alert, or support workflow needs to tell the truth. For detailed message-writing rules, use the `writing-error-messages` skill. This file decides what facts the system must preserve; that skill decides the prose.

Carry enough safe structure to answer:

- what action failed
- what was saved, sent, charged, deleted, unchanged, or left unknown
- why it happened, when known and safe
- what the reader can do next
- what support/debugging handle exists: request ID, log path, field path, error code, or retry state

Prefer message-ready facts:

```ts
type SaveSettingsOutcome =
  | { kind: 'saved' }
  | {
      kind: 'not-saved';
      reason: 'connection-lost';
      preservedDraft: true;
      requestId: RequestId;
    };
```

That shape lets the surface say: “We couldn't save your settings. Your draft is still open. Check your connection and try again. If this keeps happening, contact support with request ID ...”

Avoid prose as the contract:

```ts
type SaveSettingsOutcome =
  | { kind: 'saved' }
  | { kind: 'failed'; message: string };
```

The caller cannot safely infer whether data was saved, whether retry risks duplication, whether the cause is user-correctable, or whether the message leaks detail in a different context.

For human-facing surfaces, preserve these contract facts and rendering decisions:

- Preserve the failed action so the surface does not have to fall back to “Something went wrong,” unless the action itself is unknown or security-sensitive.
- Preserve consequence facts: saved/not saved, sent/not sent, charged/not charged, duplicated, unchanged, or unknown.
- Include the next action or backup path when the reader can do something.
- Security-sensitive flows use generic messages and consistent observable behavior when detail would reveal account existence, permissions, lock/disabled state, fraud signals, private state, system internals, or security policy.
- Empty results are not errors. Model “no matches” separately from “search failed.”
- CLI/developer errors include the command, file, field, or resource; expected vs received; and the next command or fix.
- Message text is not the data model. Carry tags and fields; render prose at the surface.

## Cancellation and Interruption

Cancellation is not just another dependency failure. Classify it before wrapping unknown causes.

```ts
catch (cause: unknown) {
  const diagnosticId = recordFailureCause(cause, { operation: 'sendReminder' });

  if (isCancellation(cause)) {
    return { kind: 'cancelled', operation: 'sendReminder', diagnosticId };
  }

  return { kind: 'email-unavailable', operation: 'sendReminder', diagnosticId };
}
```

If the caller owns cancellation, preserve that control path. Do not hide it inside a generic unavailable/error branch unless the local contract explicitly treats cancellation as indistinguishable.

## Rejected Framings

- **“The controller catches it anyway.”** Boundary translation does not excuse hidden local failure contracts.
- **“Recoverable exception.”** If the caller recovers locally, put the failure in the local contract.
- **“Everything is AppError.”** Broad unions erase caller decisions.
- **“Not found is null.”** Required absence is a failure; optional absence is explicit.
- **“It should never happen.”** If it can happen, model it. If it cannot, treat it as a defect and preserve the invariant.
- **“The provider error is good enough.”** Provider failures need local meaning and safe context.
- **“More context is always better.”** Raw context leaks data. Use safe fields.
- **“The message can fix it.”** Copy cannot recover facts the error contract discarded.
- **“Cancellation is an error.”** It is a control path; classify it before wrapping.

## Review Checklist

- Which failures can callers actually handle?
- Are expected failures visible in the local contract?
- Are defects kept loud instead of normalized into ordinary outcomes?
- Are boundary catches classifying `unknown` causes before translating?
- Is lookup absence required, optional, denied, unavailable, or invalid?
- Are failure unions precise enough for caller decisions but not provider-shaped noise?
- Do diagnostics include safe context without secrets or raw payloads?
- Can human-facing surfaces explain what happened, what was affected, and what to do next without parsing prose?
- Is cancellation/interruption classified before generic dependency failure?
