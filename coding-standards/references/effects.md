# Effects

Effects are consequences outside local computation: I/O, mutation, persistence, network calls, time, randomness, logging, scheduling, locks, retries, resource use, and background work. Effects are not bad. Hidden effects are bugs waiting for a caller.

Examples use TypeScript syntax for concreteness. Translate the shapes into the host language's native tools. Use whatever the host language makes natural: result types, exceptions with explicit contracts, context objects, structured concurrency, resource scopes, or managed runtimes.

## Non-negotiables

- A function that looks like a pure decision does not secretly write, publish, schedule, charge, mutate global state, or call the network.
- Work created by a module is awaited, returned, collected, or handed to explicit detached-work machinery.
- Background work names its owner, lifetime, cancellation behavior, failure reporting, and observability path.
- Mutating operations that may retry define idempotency: identity, deduplication, transition guard, or replay behavior.
- Work over unbounded or externally sized collections names its concurrency policy: bounded, sequential for a stated ordering/locking/rate-limit reason, or delegated to a backpressured runtime.
- Transactions do not stay open across network calls or long-running work unless the external contract requires it and the risk is named.
- Resource creation and cleanup have an owner. Imported modules do not start work at load time.

## Effect Contracts

Make effects visible in the interface when callers must reason about them.

Avoid a harmless-looking lookup that writes and publishes:

```ts
async function getInvoice(id: InvoiceId): Promise<Invoice> {
  const invoice = await db.invoices.find(id);
  await db.auditLog.insert({ action: 'invoice-read', id });
  await analytics.track('invoice-read', { id });
  return invoice;
}
```

Prefer a name and result that expose the consequence:

```ts
async function readInvoiceForAudit(id: InvoiceId): Promise<ReadInvoiceOutcome> {
  const invoice = await invoices.find(id);
  const audit = await auditInvoiceRead(id);
  return { invoice, audit };
}
```

Do not make every tiny log line part of every signature. Make consequential effects visible when they affect correctness, authority, failure handling, cost, or caller expectations.

## Pure Decisions, Effectful Shell

Keep decisions separate from effects when the split reduces confusion.

Prefer:

```ts
type ReminderDecision =
  | { kind: 'send'; invoiceId: InvoiceId; template: ReminderTemplate }
  | { kind: 'skip'; reason: ReminderSkipReason };

function decideReminder(invoice: Invoice, now: ClockTime): ReminderDecision {
  // pure decision
}

async function runReminder(invoice: Invoice, deps: ReminderDeps): Promise<ReminderOutcome> {
  const decision = decideReminder(invoice, deps.clock.now());
  if (decision.kind === 'skip') return decision;
  return deps.email.send(renderReminder(decision));
}
```

Avoid mixing decision, clock, persistence, and email in one branchy function when callers or tests need the decision independently.

## Async Work Ownership

Every async task has an owner. The owner decides whether work is awaited, returned, collected, cancelled, retried, or detached.

Avoid floating work:

```ts
users.map((user) => sendWelcomeEmail(user));
void refreshSearchIndex(orderId);
```

Prefer explicit ownership:

```ts
const results = await mapConcurrent(
  users,
  { concurrency: emailProviderLimit },
  sendWelcomeEmail,
);

await recordWelcomeEmailResults(results);

background.enqueue(
  () => refreshSearchIndex(orderId),
  {
    owner: 'order-created-handler',
    onFailure: reportDetachedFailure,
  },
);
```

Collecting results answers ownership; bounded concurrency answers backpressure. Most real collections need both.

Detached work is still work. If the process exits, request is cancelled, queue retries, or dependency fails, the design needs an answer.

## Cancellation and Lifetime

Lower-level modules should not invent hidden lifetimes when callers already own cancellation, deadlines, request lifetimes, or workflow lifetimes.

Prefer passing a caller-owned cancellation token/options object through effects when the runtime supports it:

```ts
type FindUserOptions = { signal?: AbortSignal };

async function findActiveByEmail(
  email: EmailAddress,
  options: FindUserOptions,
): Promise<UserLookup> {
  return fetchUser(email, { signal: options.signal });
}
```

Avoid replacing the caller's lifetime with an internal timeout or hidden controller:

```ts
async function findActiveByEmail(email: EmailAddress): Promise<UserLookup> {
  const controller = new AbortController();
  setTimeout(() => controller.abort(), 1000);
  return fetchUser(email, { signal: controller.signal });
}
```

A lower layer may add a dependency-specific timeout, but it should compose with the caller's lifetime rather than replace it.

## Concurrency and Backpressure

Independent work can start together. Unbounded work needs a limit chosen from the bottleneck.

Avoid accidental waterfalls:

```ts
for (const user of users) {
  await sendWelcomeEmail(user);
}
```

Avoid unbounded fan-out over user-sized, database-sized, file-sized, queue-sized, or provider-sized collections:

```ts
await Promise.all(users.map((user) => sendWelcomeEmail(user)));
```

Prefer bounded concurrency with a named limit:

```ts
await mapConcurrent(users, { concurrency: emailProviderLimit }, sendWelcomeEmail);
```

Sequential execution is right when ordering, locking, rate limits, backpressure, transactions, or external contracts require it. Otherwise it is often hidden latency, not safety.

## Retries and Idempotency

Any mutating command exposed to clients, queues, schedulers, workflows, humans, or unreliable networks should assume retries.

Avoid retrying create operations that allocate fresh identity each time:

```ts
async function createPayment(request: CreatePaymentRequest) {
  const paymentId = randomPaymentId();
  await payments.insert({ paymentId, ...request });
  await provider.charge(request.card, request.amount);
  return paymentId;
}
```

Prefer stable identity or replay behavior:

```ts
async function createPayment(command: CreatePaymentCommand) {
  return transaction(async (tx) => {
    const existing = await tx.payments.findByIdempotencyKey(command.idempotencyKey);
    if (existing) return replay(existing);

    const payment = Payment.start(command.idempotencyKey, command.amount);
    await tx.payments.insert(payment);
    await tx.outbox.insert(chargePayment(payment));
    return created(payment.id);
  });
}
```

Close the crash window between persistence and external side effects with an outbox, inbox, replay record, transition guard, or workflow state.

If the retry policy depends on persisted progress or lifecycle state, treat it as a state/workflow design too; see `state.md`.

## Transactions and External Calls

Do not hold local locks or database transactions open while waiting on unrelated external systems.

Avoid:

```ts
await transaction(async (tx) => {
  await tx.orders.insert(order);
  await paymentProvider.charge(card, amount);
  await tx.orders.markPaid(order.id);
});
```

Prefer durable state plus separate delivery/transition:

```ts
await transaction(async (tx) => {
  await tx.orders.insert(order);
  await tx.outbox.insert(requestPayment(order.id, amount));
});

await deliverOutbox();
```

If the system truly needs one distributed transaction or lock, name the external contract that requires it and the failure mode it accepts.

## Resource Ownership

Whoever creates a resource owns cleanup unless ownership is explicitly transferred.

Avoid import/load-time effects:

```ts
export const db = connect(process.env.DATABASE_URL);
setInterval(runCleanup, 60_000);
```

Prefer composition-owned resources:

```ts
const db = await connect(config.databaseUrl);
const cleanup = scheduler.every('1m', runCleanup);

try {
  await serve({ db, cleanup });
} finally {
  cleanup.stop();
  await db.close();
}
```

Framework-managed lifetimes are still lifetimes. Keep them at the boundary and know who owns shutdown.

## Diagnostics Without Leaks

Effects are where diagnostics usually happen. Preserve enough context to debug without dumping secrets or raw payloads.

Prefer stable safe fields:

```ts
logger.error('Payment authorization failed', {
  operation: 'placeOrder',
  dependency: 'stripe',
  orderId,
  errorTag: failure.kind,
});
```

Avoid raw context dumps:

```ts
logger.error('Payment failed', { request, response, env, error });
```

More context is not always better. Safe context is better.

For failure contracts and safe error context, see `error-handling.md`.

## Rejected Framings

- **“It is just a helper.”** Helpers can hide writes, network calls, authority, cost, and lifetime.
- **“Fire and forget.”** Detached work still needs an owner.
- **“Sequential is safer.”** Sequential loops hide latency and do not solve overload; use ordering or bounded concurrency deliberately.
- **“POST probably will not retry.”** Retrying mutating commands is normal.
- **“We saved before calling the API.”** Save-then-call still has a crash window.
- **“Timeouts belong everywhere.”** Lower layers compose dependency timeouts with caller lifetime; they do not replace it.
- **“It is only logs.”** Logs, traces, and errors are outputs; they can leak secrets and shape debugging.

## Review Checklist

- What does this code do besides return a value?
- Which effects are hidden behind harmless names?
- Who owns async work, background work, cancellation, and cleanup?
- Which mutating operations can retry, and what prevents duplicates?
- Is concurrency sequential, unbounded, or deliberately bounded?
- Are transactions held across external calls?
- Are resource lifetimes owned at composition, adapter, or runtime boundaries?
- Do diagnostics preserve safe context without leaking secrets or raw payloads?
