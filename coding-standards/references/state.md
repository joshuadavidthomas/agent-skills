# State

State is the part of the model that decides what can happen next. Good code keeps the allowed states visible, the allowed transitions narrow, and illegal combinations hard to create.

## Non-negotiables

- Illegal lifecycle combinations are not normal domain values.
- Phase-specific data belongs to the phase that owns it, not in nullable fields callers must interpret.
- Repeated transition checks are moved to the transition owner.
- State changes that require authority name where that authority comes from.
- Long-running work, retries, queues, sync, and background tasks name their loop owner and persisted progress.

## State Space Is Design

Every representation defines a state space. If the representation permits more combinations than the system allows, every caller inherits the job of remembering which combinations are real.

Prefer representations that make the domain state obvious:

- one lifecycle field instead of several phase flags
- explicit variants instead of nullable clusters
- separate constructed values for before/after validation
- transition functions or methods instead of scattered mutation
- persistence constraints when storage is the real transition boundary

Do not make normal code carry illegal combinations and hope checks catch them later.

## Lifecycle Before Flags

Flags are fine for independent facts. They are bad when they encode one lifecycle.

Avoid:

```text
isDraft
isPublished
isArchived
publishedAt?
archivedAt?
```

when the real model is one state:

```text
Draft
Published(publishedAt)
Archived(publishedAt, archivedAt)
```

The first shape allows nonsense. The second names the legal phases and puts phase-specific data where it belongs.

## State-Space Thresholds

Examples use TypeScript-like syntax only for concreteness; translate the shape into the host language's native tools.

Escalate from flags/nullables to an explicit state model when any of these are true:

- two or more booleans describe one lifecycle instead of independent facts
- a field is meaningful only when another field has a specific value
- most combinations are illegal or nonsensical
- callers repeat `if status is X then field Y exists` checks
- transitions must reject invalid source states, missing authority, or stale versions

Avoid nullable phase data:

```ts
type Article = {
  isPublished: boolean;
  publishedAt?: Instant;
};
```

Prefer phase-specific data:

```ts
type Article =
  | { kind: 'draft'; id: ArticleId }
  | { kind: 'published'; id: ArticleId; publishedAt: Instant };

function publish(article: Article, actor: Publisher, publishedAt: Instant): PublishOutcome {
  if (article.kind !== 'draft') {
    return { kind: 'rejected', reason: 'already-published' };
  }
  if (!actor.canPublish(article.id)) {
    return { kind: 'rejected', reason: 'not-authorized' };
  }

  return {
    kind: 'published',
    article: { kind: 'published', id: article.id, publishedAt },
  };
}
```

If the language cannot make the illegal state impossible, put construction and transitions behind a small API and keep the raw representation private.

## Transitions Own Rules

A transition is the place where the system decides whether change is allowed.

Put the rule at the transition point:

- source state required
- target state produced
- authority needed
- invariant checked
- effect performed
- expected failure returned
- persisted state updated

Avoid scattering “can this happen?” checks across callers. If every caller checks the same rule, the transition does not own its contract.

For transition failure contracts, see `error-handling.md`. For effects performed during transitions, retries, idempotency, and crash windows, see `effects.md`.

## Loops and Workflows

Long-running behavior is usually a loop:

```text
observe state -> decide -> perform effects -> record new state -> repeat
```

Jobs, sync engines, queues, retries, background tasks, streams, subscriptions, and protocols all need a visible loop owner.

Name the owner of:

- persisted progress
- retry and idempotency policy
- cancellation and shutdown
- partial failure recovery
- duplicate event handling
- stuck or terminal states

A background task without state ownership becomes hidden control flow.

Avoid a loop that hides progress in a local variable or caller memory:

```text
syncAllUsersSince(lastSeenCursor)
```

Prefer a visible workflow state owned by the sync loop:

```text
UserSyncRun(cursor, retryCount, owner, cancellationPolicy, terminalState)
```

The loop owner decides when the cursor is persisted, how duplicate events are handled, which failures retry, and when the run reaches a terminal state.

## Authority and Ownership

Some state changes require authority. The code should show who may transition the state and where that authority comes from.

Authority can be a credential, session, role, capability, transaction, lock, owner object, or service boundary. Avoid ambient authority where distant globals, implicit sessions, or hidden mutation can change state from anywhere.

## Temporary Invalid State

Some code must pass through an invalid or incomplete shape while parsing, migrating, editing, or reconciling. Keep that shape local and short-lived.

Name the step that resolves it:

```text
raw input -> parsed draft -> valid command
```

Do not let temporary invalid state escape as normal domain data.

## Rejected Framings

- **“It is just a couple flags.”** Count the combinations. If most are illegal, the representation is lying.
- **“The caller knows the order.”** Then the lifecycle is implicit and the interface is leaking state.
- **“This state only exists briefly.”** Brief invalid state still leaks through async work, callbacks, logs, tests, and errors.
- **“The framework manages it.”** Name the framework lifecycle and keep its assumptions at the boundary.
- **“We validate before saving.”** Persisting is only one transition. Callers still need valid state before they decide, render, publish, or retry.

## Review Checklist

- What states can this thing be in?
- Which combinations are illegal but representable?
- Where are transitions named and enforced?
- What authority is required to transition state?
- Are phase-specific fields only present in the phase that owns them?
- Who owns the loop for jobs, retries, sync, or background work?
- Can temporary invalid state escape into normal code?
- Would an explicit state model remove repeated checks or caller memory?
