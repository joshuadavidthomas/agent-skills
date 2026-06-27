# Verification

Verification is evidence for a claim. A passing test is useful only when it proves the behavior, invariant, transition, boundary, failure mode, or compatibility promise the change depends on.

Examples use lightweight pseudocode/test syntax; use the project's native test framework and validation tools.

## Non-negotiables

- Tests verify the caller-visible claim, not private helper choreography.
- Do not export internals, add alternate production paths, or broaden constructors only to make tests easy.
- Mock or fake outside systems only at real seams; do not mock away the behavior under review.
- A happy-path test does not prove invalid states, boundary failures, expected failures, retries, cancellation, or compatibility.
- Claims about performance, migration, compatibility, or behavior preservation need evidence matched to that claim.

## Name the Claim First

Before choosing a test shape, name what must be true.

Claims usually fall into one of these buckets:

- a domain rule holds
- a state transition is legal or rejected
- boundary input becomes the right internal representation
- an expected failure is exposed to callers
- an operational failure preserves useful context
- an interface hides sequencing or policy from callers
- a refactor preserves observable behavior
- a migration preserves or intentionally changes data shape
- a performance or resource-cost claim holds under measured conditions

Do not let available mocks, fixtures, helper functions, or easy assertions decide the claim.

## Evidence Must Match the Claim

Choose the narrowest evidence that honestly proves the claim; narrowest does not mean easiest, most mocked, or least realistic. Do not substitute a weaker gate for a stronger promise.

Good matches:

- domain rules -> examples, tables, or property tests
- illegal states -> construction and transition tests
- boundary translation -> valid, malformed, missing, and versioned source shapes
- expected failures -> caller-visible failure cases
- operational failures -> retry/reporting/context behavior
- effect contracts -> idempotency, retry, cancellation, resource cleanup, and bounded-concurrency tests
- public interfaces -> tests through the surface callers use
- refactors -> characterization tests before change, behavior tests after
- performance claims -> measurement, not vibes

A type check does not prove runtime behavior. A happy-path test does not prove failure handling. A mock assertion does not prove the real collaborator contract.

Use topic-specific contracts to choose evidence: for effect claims, see `effects.md`; for failure contracts and diagnostics, see `error-handling.md`; for compatibility, migrations, and refactors, see `maintainability.md`; for state transitions and illegal states, see `state.md`; for boundary translation, see `boundaries.md`.

## Test Through Real Seams

Prefer tests that exercise the interface callers actually use. Replace outside systems when necessary, but do not replace the behavior under review.

Good seams:

- public module or service boundary
- application command or endpoint
- adapter boundary with a dependency-native fake
- repository/storage boundary with a real temporary store when setup cost, runtime, and flakiness do not obscure the claim
- clock, ID generator, randomness, or scheduler injected as a capability

Bad seams:

- private helpers exported only for tests
- module mocks that skip the code path being evaluated
- spies asserting internal call order when observable behavior would prove the claim
- broad constructors or alternate code paths added only for tests

## Interaction Tests Are a Smell, Not a Ban

Interaction tests can be right when the interaction is the contract: publish this event, call this external API once, acquire this lock, start this transaction, or avoid duplicate sends.

They are weak when they only freeze private choreography. If the caller does not care whether the implementation used three helpers or one, the test should not care either.

## Characterize Before Risky Change

When existing behavior matters but is poorly understood, first record what the system does. Characterization tests are especially useful near parsers, migrations, sync logic, public APIs, legacy workflows, and bug-prone edge cases.

Characterization is a safety rail, not a design endorsement. After the behavior is understood, preserve the real contract and improve the shape.

Characterization tests should record observable behavior through a real seam. Do not turn accidental helper steps, old field names, or private call order into permanent contracts.

## Production Surface Is Not for Tests

Do not make private choreography public to make tests easy. A test-only helper that production callers can use is production API.

If the code is hard to test, ask what design problem is being exposed:

- too much effectful work mixed with decision logic
- no real seam at a dependency boundary
- hidden state or ambient authority
- an interface that is too shallow
- a contract that returns vague errors or raw shapes

Fix the seam or contract; do not publish internals.

## Worked Example: Mock Theater

Avoid tests that prove private choreography:

```text
expect(client.fetchUser).calledWith(providerId)
expect(mapper.toProfile).calledOnce()
expect(repository.save).calledWith(mappedProfile)
```

This mostly proves the implementation steps. A refactor that keeps behavior but changes the steps breaks the test.

Prefer proving the caller-visible claim through a real seam:

```text
handleProviderWebhook(providerPayload)

expect(loadUserProfile(userId)).equals(expectedProfile)
expect(recordedFailures()).isEmpty()
```

Fake the external provider if needed, but let the boundary under review parse, map, persist, and report through its real interface.

## Rejected Framings

- **“The helper is easier to test.”** Maybe the helper is private choreography. Prove the caller-facing claim first.
- **“Mocks make it isolated.”** Isolated from what? If the test bypasses the behavior under review, it is proving the mock setup.
- **“The happy path passes.”** Name the important invalid states, boundary failures, and expected failures.
- **“The compiler/linter passed.”** Good; now name what runtime claim remains unproven.
- **“We need to export this for tests.”** Name the production caller. If none exists, find a real seam or keep it private.
- **“This preserves behavior.”** Show characterization or behavior-level evidence.

## Review Checklist

- What claim does this change depend on?
- What evidence would actually prove that claim?
- Does the test exercise the caller-facing seam?
- Are invalid states, boundary failures, and expected failures covered where they matter?
- Is the test pinning private choreography?
- Did test needs expand production surface?
- Are project-native validation gates used?
- Is any performance, migration, or compatibility claim backed by the right evidence?
