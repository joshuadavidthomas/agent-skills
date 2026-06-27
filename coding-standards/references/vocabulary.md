# Vocabulary

Shared terms for explanations, reviews, and code-facing design notes across this skill. Topic files may define only topic-local terms near their rules.

## Modeling

**Model**: The simplified representation of the problem that the code maintains. Use **domain model** when the subject is business or product meaning rather than a technical shape.

**Domain concept**: A problem-level idea, rule, workflow state, permission, protocol fact, or persistent identity that callers or maintainers need to reason correctly.

**Representation**: The chosen code shape for a concept: primitive, record, enum, class, type, table row, message, file format, or protocol value. Representations determine which states are easy, impossible, or only prevented by convention.

**Granularity (grain)**: The level of detail at which code names and separates concepts. Too coarse hides real differences; too fine makes readers reassemble one idea from many pieces.

**Identity**: What makes a thing the same thing over time, even when its path, display name, label, location, or provider handle changes.

**Projection**: A current name, path, label, position, serialized form, provider handle, or display shape for a thing. A projection may change without changing identity.

**Invariant**: A fact that must remain true for the system to be valid. Protect invariants with valid states, constructors, parsers, transitions, constraints, and interfaces instead of comments or scattered checks.

## State

**State**: The condition a system, object, workflow, connection, request, job, or protocol is in at a moment. State matters when behavior changes by phase, lifecycle, authority, ownership, or prior events.

**State space**: The set of possible states a representation allows. Boolean blindness, nullable phase fields, and loosely related flags often create more states than the system actually permits.

**Transition**: A move from one state to another. Checks, authorization, validation, effects, persistence, and error decisions usually belong at transition points.

**Lifecycle**: The expected sequence of states a thing passes through. Files, jobs, requests, sessions, connections, tasks, orders, subscriptions, caches, and resources all have lifecycles.

**Illegal state (impossible state)**: A combination the real system should never permit. Make illegal states unrepresentable, or confine them to a small controlled place with a named transition that resolves them.

**Boolean blindness (flag soup)**: Booleans or loosely related flags erase the meaning of choices and secretly encode one state machine. Replace them with explicit states, variants, lifecycle types, or constrained transitions when the flags describe one phase.

## Modules and Interfaces

**Module**: Anything with an interface and an implementation: function, type, class, package, endpoint slice, job, adapter, or service boundary.

**Interface**: Everything callers must know to use a module correctly: inputs, outputs, invariants, ordering, failures, effects, authority, configuration, and cost.

**Implementation**: What sits behind the interface. It may contain helpers and internal seams; callers should not learn them.

**Contract**: What callers and implementers can rely on: valid inputs, outputs, errors, effects, ownership, lifecycle constraints, relevant performance expectations, and compatibility obligations.

**Depth**: Caller leverage per unit of interface burden. A module is deep when a small cohesive interface hides substantial behavior.

**Leverage**: What callers get when one interface gives them a lot of capability without exposing private mechanics.

**Locality**: What maintainers get when behavior, invariants, bugs, and verification concentrate in one module instead of spreading across callers.

**Deep module (deep interface)**: A small, cohesive surface backed by substantial owned behavior. It hides policy, sequencing, translation, invariants, coordination, resource lifetime, or error handling so callers can know less.

**Shallow wrapper (shallow module)**: A name or layer that does not reduce what callers must know. It often forwards, renames, configures, splits files, or wraps a dependency while leaving the same complexity exposed.

**Caller burden**: Everything a caller must know to use code correctly. Hidden preconditions, order dependencies, option bags, boolean traps, implicit globals, leaked storage shapes, and provider-specific details all increase it.

## Boundaries

**Boundary**: A place where data, control, trust, runtime, protocol, persistence, ownership, or meaning changes. Good boundaries translate raw external shapes into the internal model before core logic uses them.

**Seam**: An intentional point where behavior can vary, dependencies can be substituted, or models can be mapped. Real seams mark volatility, ownership, trust, protocol, provider behavior, or meaningful test boundaries.

**Adapter**: Code that maps one model, protocol, or dependency surface into another. Good adapters own translation, normalization, error mapping, and provider quirks that callers should not care about.

**Anti-corruption layer**: Boundary translation that protects the internal model from external vocabulary and protects external contracts from internal churn. It maps source shape → internal model → target shape, including trust, failure, ownership, and source-of-truth decisions.

**DTO / wire representation**: Data shaped for a wire, API, queue, file, database, or framework boundary. Treat it as an edge shape unless it truly is the domain model.

**Source of truth**: The place that owns a fact when systems disagree. Decide which data is canonical and which is a cache, projection, view, transport copy, local intent, or working state.

**Raw boundary data**: Input or output still shaped by an external source, storage system, framework, protocol, provider, file, queue, CLI, or runtime. It may be decoded or validated, but it is not yet the internal model.

**Refined value**: A value produced by parsing, validation, normalization, authorization, or translation that carries the proof core logic needs.

**Boundary proof**: The fact a refined value carries because it crossed a boundary successfully: parsed, trusted, authorized, normalized, version-translated, or source-of-truth-resolved.

## Consequences

**Effect**: Anything code does besides compute and return a value: IO, mutation, persistence, network calls, time, randomness, logging, scheduling, locking, retries, or resource consumption.

**Authority / ownership**: The ability and responsibility to do something consequential: read, write, delete, publish, schedule, retry, mutate state, or transition a lifecycle. It may be embodied in a credential, handle, object, session, service, transaction, role, capability, or ownership token.

**Resource cost**: The CPU, memory, allocation, IO, network, query, lock, retry, fan-out, or contention work a design implies. Code should not make expensive or unbounded work look free.

**Action at a distance**: Behavior changed by ambient state, hidden mutation, magic registration, global configuration, lifecycle hooks, or distant effects. Contain it at known boundaries when a framework or runtime makes it unavoidable.

## Errors

**Expected failure (expected error)**: A failure mode the interface deliberately exposes and callers can reasonably handle: missing input, invalid user data, not found, conflict, permission denied, duplicate request, timeout, or unavailable dependency.

**Defect**: A programmer bug, broken invariant, impossible condition, or misuse of an internal contract. Defects are not ordinary recovery paths.

**Operational failure (operational error)**: Failure caused by the environment or a dependency: network, disk, unavailable service, rate limit, lock contention, resource exhaustion, malformed external data, or provider behavior. It may be exposed as an expected failure at a boundary, but it still needs enough cause and context for diagnosis.

## Verification and Change

**Claim**: What code says should be true: behavior, invariant, transition, boundary translation, error case, compatibility promise, or performance property. Name the claim before choosing evidence.

**Evidence**: Concrete proof that a claim holds: test, type check, linter, property test, integration run, benchmark, trace, log, manual reproduction, migration dry run, or production observation.

**Characterization test**: A test that records existing behavior before changing poorly understood code. It gives a safe baseline without making accidental internals permanent contracts.

**Compatibility obligation**: A backward-compatibility contract or real reason to preserve, migrate, or support an old shape: public API users, existing data, stable protocols, external integrations, documented contracts, or active deployments.

## Complexity Smells

**Accidental complexity**: Difficulty created by the implementation rather than the problem. Unnecessary layers, speculative generality, indirection mazes, duplicated concepts, hidden state, framework leakage, and ceremony are common sources.

**Indirection maze (helper maze)**: One operation scattered across many helpers, files, classes, or layers. Collapse or regroup until the operation is visible at the right level.

**Overengineering**: Structure, generality, extension points, layers, options, or seams beyond the current force in the problem.

**Over-modeling**: Domain-looking vocabulary for implementation details that callers do not need: parser phases, storage artifacts, framework payloads, optimization crumbs, or test scaffolding.

**Empty domain wrapper**: A domain-looking wrapper with no invariant, identity, operation, proof, boundary, or useful constraint. Add the missing semantic force or use the native type directly.

**Speculative generality**: Options, modes, adapters, providers, strategies, interfaces, config switches, or extension points created before real variation exists. Keep code direct until variation, boundary pressure, or substitution need is real.

**Ceremony**: Names, files, helpers, sections, types, or comments that narrate mechanics without making the important model clearer. Good explicitness reveals decisions; bad explicitness increases surface area.

**Over-mocking (brittle interaction test)**: Tests that prove mocks, spies, call order, or private helper choreography instead of observable behavior. Mock outside systems when useful, but verify the real claim through a real interface.

**Compatibility glue**: Old and new shapes supported together without a real compatibility obligation. If users, data, protocols, or public contracts need it, name the obligation and removal condition; otherwise move to the end-state shape.
