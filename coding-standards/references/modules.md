# Modules

Design deep modules: cohesive behavior behind a low-burden interface at an intentional seam. A module earns its keep when deleting it would push meaningful complexity into callers.

Module roles are responsibilities, not required layers. Do not split code into core/use-case/adapter/composition files by default. Split only when the split buys locality, boundary protection, testability through a real seam, or caller leverage.

## Terms

**Module** — anything with an interface and an implementation: function, type, class, package, endpoint slice, job, adapter, or service boundary.

**Interface** — everything callers must know to use the module correctly: inputs, outputs, invariants, ordering, failures, effects, authority, configuration, and cost.

**Implementation** — what sits behind the interface. It may contain helpers and internal seams; callers should not learn them.

**Seam** — where the interface lives. A seam is real when behavior varies, a boundary translates, or tests substitute through the same surface production uses.

**Adapter** — a concrete implementation at a seam. It translates between the module's interface and a framework, runtime, storage system, protocol, provider, or test substitute.

**Depth** — caller leverage per unit of interface burden. Deep modules let callers do more while knowing less.

## Types First

For a nontrivial module, sketch the types before filling in the implementation. Good types expose the real decisions: input, output, dependencies, authority, state, and failure.

Examples use TypeScript syntax for concreteness. Translate the shapes into the host language's native tools: enums, sum types, structs, protocols, interfaces, traits, classes, or plain functions.

Start with the caller-facing contract:

```ts
type PlaceOrderCommand = {
  customerId: CustomerId;
  lines: OrderLine[];
  paymentMethodId: PaymentMethodId;
  idempotencyKey: IdempotencyKey;
};

type PlaceOrderOutcome =
  | { kind: 'placed'; orderId: OrderId }
  | { kind: 'rejected'; reason: PlaceOrderRejection }
  | { kind: 'failed'; failure: OperationalFailure };

type PlaceOrder = (command: PlaceOrderCommand) => Promise<PlaceOrderOutcome>;
```

Then name only the dependencies the module actually consumes:

```ts
type PlaceOrderDeps = {
  reserveOrder(command: PlaceOrderCommand): Promise<ReserveOrderOutcome>;
  enqueuePaymentRequest(request: PaymentRequest): Promise<EnqueueOutcome>;
};
```

If the types are vague, the module is vague. If the types are ceremonial, the module is ceremonial.

## Responsibilities, Not Layers

Use these roles to identify responsibility. Do not create one file for every role unless each file earns the split.

**Core responsibility**: owns a domain concept, invariant, parser, predicate, calculation, state transition, or pure decision. It does not hide I/O, framework objects, ambient time, random IDs, network calls, or persistence.

```ts
function parseTemplate(raw: string): ParseTemplateOutcome {
  // returns { kind: 'parsed', value } or { kind: 'invalid', error }
}

function invoiceTotal(lines: InvoiceLine[]): Money {
  // pure calculation, no database, no clock, no framework request
}

function approveOrder(order: DraftOrder, actor: Approver): ApproveOrderOutcome {
  // returns { kind: 'approved', order } or { kind: 'rejected', reason }
}
```

A domain module often centers on one primary type or a tight type family. Parsers, smart constructors, predicates, transitions, combinators, formatting, interpreters, and test-data builders can live together when they are cohesive around that concept. That is one responsibility with a clear home, not an architecture layer.

**Use-case responsibility**: owns a workflow or application capability. It composes core decisions and dependency interfaces, sequences effects, classifies dependency failures, and returns caller-visible outcomes.

When the workflow mutates external systems, also apply `effects.md`: name retry/idempotency behavior, crash windows, transaction boundaries, and any background loop owner.

```ts
function makePlaceOrder(deps: PlaceOrderDeps): PlaceOrder {
  return async function placeOrder(command) {
    const reserved = await deps.reserveOrder(command);
    if (reserved.kind === 'duplicate') {
      return replayPlaceOrder(reserved.order);
    }
    if (reserved.kind === 'rejected') {
      return { kind: 'rejected', reason: reserved.reason };
    }
    if (reserved.kind === 'failed') {
      return { kind: 'failed', failure: reserved.failure };
    }

    const queued = await deps.enqueuePaymentRequest(paymentRequestFor(reserved.order));
    if (queued.kind === 'failed') {
      return { kind: 'failed', failure: queued.failure };
    }

    return { kind: 'placed', orderId: reserved.order.id };
  };
}
```

**Adapter responsibility**: owns framework, protocol, persistence, runtime, SDK, or provider mechanics. It converts between external shapes and core/use-case contracts.

```ts
async function httpPlaceOrder(request: Request, placeOrder: PlaceOrder): Promise<Response> {
  const command = parsePlaceOrderRequest(request);
  if (command.kind === 'invalid') return badRequest(command.error);

  const outcome = await placeOrder(command.value);
  return placeOrderResponse(outcome);
}

class SqlOrderWriter {
  async writeOrder(order: OrderToPersist): Promise<WriteOrderOutcome> {
    // SQL rows, transactions, and storage errors stay here
  }
}
```

**Composition responsibility**: wires dependencies, reads config, starts runtimes, registers handlers, and connects entrypoints to use-case modules. It may install authentication, parsing, or middleware at the boundary; it does not own shared business policy.

```ts
const orders = new SqlOrderReservationStore(db);
const paymentRequests = new PaymentRequestOutbox(queue);

const placeOrder = makePlaceOrder({
  reserveOrder: (command) => orders.reserveOrder(command),
  enqueuePaymentRequest: (request) => paymentRequests.enqueue(request),
});

router.post('/orders', (request) => httpPlaceOrder(request, placeOrder));
```

For a small local operation, these responsibilities may live in one module. Split them only when the seam or responsibility is real.

## Non-negotiables

- A module owns one cohesive concept, capability, policy, or boundary.
- The interface hides implementation choices, incidental steps, ordering, and invariants the module can own.
- Core code does not depend on framework objects, raw DTOs, database rows, provider payloads, hidden I/O, ambient time, randomness, or global state.
- Use-case code depends on the smallest behavior it needs, not whole clients, repositories, or dependency bags passed through every call.
- Adapter code translates; it does not let external vocabulary become the core model.
- Entrypoints do not duplicate domain or use-case policy across protocols.
- Tests cross the same interface callers use. Do not export internal helpers to make tests easier.
- Role names do not justify extra files. Each split must buy leverage or locality.

## Depth and Deletion Test

Deep modules have a small cohesive interface and substantial behavior underneath. Callers learn little and get a lot.

Shallow modules have a wide or pass-through interface and thin forwarding underneath. Callers still learn the provider, ordering, flags, DTO shape, failures, and lifecycle rules.

Delete the module in your head. If complexity disappears, it was ceremony. If complexity spreads across callers, it was earning its keep.

## Interface Shape

Callers should say what they want, not perform the module's private checklist.

Avoid making every entrypoint orchestrate the same workflow:

```ts
const parsed = parseOrderRequest(request);
const order = validateOrder(parsed);
const tx = await orders.beginTransaction();
await orders.writeRows(tx, order);
await payments.authorize(order.payment);
await notifications.sendOrderConfirmation(order.customerEmail);
await tx.commit();
```

Prefer an adapter plus use-case interface:

```ts
const command = parseOrderRequest(request);
const outcome = await placeOrder(command);
```

The adapter parses protocol input. The use-case module owns the workflow policy: validation decisions, persistence sequence or transaction policy, payment decisions, notification decisions, idempotency, and expected failures. Storage mechanics stay in adapters. Inside core logic, pass refined domain values, not the raw request accepted by the outer adapter.

## Dependency Shape

Depend on the smallest meaningful behavior at the consumer.

Avoid passing a mega-repository because one operation needs one query:

```ts
type UsersRepository = {
  findById(id: UserId): Promise<User | null>;
  findActiveByEmail(email: EmailAddress): Promise<ActiveUser | null>;
  updateProfile(user: User): Promise<void>;
  delete(id: UserId): Promise<void>;
};

class PasswordReset {
  constructor(private readonly users: UsersRepository) {}
  // This module now learns every repository method, not the one behavior it needs.
}
```

Prefer the behavior the module consumes:

```ts
type ActiveUsersByEmail = {
  find(email: EmailAddress): Promise<ActiveUserLookup>;
};

class PasswordReset {
  constructor(private readonly users: ActiveUsersByEmail) {}

  async start(email: EmailAddress): Promise<PasswordResetStarted | PasswordResetError> {
    const user = await this.users.find(email);
    // reset policy stays here
  }
}
```

The wider adapter can still implement that behavior. The use-case module should not learn unrelated methods.

Avoid interface confetti too:

```ts
type FindUserByEmail = { find(email: EmailAddress): Promise<UserLookup> };
type FindUserById = { find(id: UserId): Promise<UserLookup> };
type UpdateUserProfile = { update(profile: UserProfile): Promise<void> };
type DeleteUser = { delete(id: UserId): Promise<void> };
```

A one-method interface is useful only when the seam is meaningful. Do not create one for every class by habit.

## Dependency Categories

Choose the seam and test strategy from the dependency, not from habit.

1. **In-process** — pure computation or memory. Merge/deepen freely and test through the module interface.
2. **Local-substitutable** — local test stand-in exists, such as an in-memory filesystem or local database. Use the stand-in; do not add an external port only for testing.
3. **Remote but owned** — your own service across a network. Define a port at the seam; production uses a transport adapter; tests can use an in-memory adapter.
4. **True external** — third-party provider. Inject a port; tests usually use a fake, mock, or contract-tested adapter through that seam.

A port with one implementation and no translation, volatility, substitution pressure, or boundary ownership is speculative. A single adapter can still be real when it translates a boundary; a second production adapter or test substitute is evidence, not a requirement.

## Functional Core and Imperative Shell

Functional core owns decisions:

- domain rules
- domain parsers, constructors, and refinements
- state transitions
- calculations
- predicates
- combinators

Imperative shell owns consequences:

- protocol/input parsing at entrypoints
- dependency wiring
- effect sequencing
- persistence and external calls
- telemetry
- time, randomness, and IDs
- dependency failure classification

Do not put domain policy in controllers, CLI handlers, queue handlers, glue code, utilities, or framework callbacks. Entrypoints translate and delegate.

## Resource Ownership

Resource creation and cleanup belong in bootstrap, composition roots, entrypoints, adapter modules, or managed runtime layers.

Imported modules should not start servers, open connections, register handlers, read environment, schedule work, or perform I/O at import/load time. If a framework requires singleton-like behavior, isolate it at the boundary.

## Worked Example: Pass-through Wrapper

Avoid a wrapper that only renames a dependency while callers still own the rules:

```ts
class ObjectStore {
  constructor(private readonly provider: ObjectProvider, private readonly bucket: string) {}

  put(key: string, bytes: Uint8Array) {
    return this.provider.putObject(this.bucket, key, bytes);
  }

  get(key: string) {
    return this.provider.getObject(this.bucket, key);
  }
}
```

Callers still choose keys, serialization, overwrite policy, content type, retries, and failure handling. The wrapper does not reduce caller burden; it only moves the provider call behind another name.

Prefer using the provider-native client at the adapter boundary, or create a module that owns a real operation:

```ts
class InvoicePdfArchive {
  constructor(private readonly objects: ObjectProvider, private readonly bucket: string) {}

  async save(invoiceId: InvoiceId, pdf: PdfBytes): Promise<ArchiveInvoiceResult> {
    const key = `invoices/${invoiceId.value}.pdf`;
    const outcome = await this.objects.putObject(this.bucket, key, pdf.bytes, {
      contentType: 'application/pdf',
      overwrite: false,
    });

    return archivePutOutcome(outcome);
  }

  async load(invoiceId: InvoiceId): Promise<LoadInvoicePdfResult> {
    const key = `invoices/${invoiceId.value}.pdf`;
    const outcome = await this.objects.getObject(this.bucket, key);
    return archiveGetOutcome(outcome);
  }
}
```

Now the module owns key format, content type, overwrite rules, provider-error translation, and the caller's actual task.

## Rejected Framings

- **“A module per noun.”** A module is justified by cohesive behavior, not naming symmetry.
- **“A repository per table.”** Persistence adapters expose capabilities needed by use cases, not raw table mirrors.
- **“An interface for every class.”** Seams are for variation, translation, and real substitution.
- **“Dependency bags are flexible.”** Dependency bags spread ownership and hide contracts when passed through calls instead of owned at construction/composition.
- **“The controller can own the policy.”** Entrypoints translate protocols; shared policy belongs in core or use-case modules.
- **“These are the architecture layers.”** They are responsibilities. Do not split files unless the split buys leverage or locality.
- **“This wrapper clarifies responsibilities.”** Name the responsibility it owns and the caller rule it removes. If both names match the dependency underneath, collapse it.
- **“This is easier to test.”** Name the production seam the test uses. If the seam exists only for tests, redesign or keep it private.

## Review Checklist

- What role is this module playing: core, use case, adapter, composition, or a deliberate mix?
- What types define its contract: input, output, dependencies, authority, state, and failure?
- What does the interface let callers forget?
- What policy, sequence, invariant, translation, lifetime, authority, failure, or cost does it own?
- Is the dependency surface the smallest meaningful behavior?
- Is the seam real, or speculative indirection?
- Are framework, provider, storage, and DTO shapes kept in adapters?
- Did tests force private implementation into public surface?
- Would deletion remove ceremony or spread meaningful complexity?
