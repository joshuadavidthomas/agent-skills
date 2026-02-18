# SSR Safety (SvelteKit Only)

> **This section applies only to SvelteKit with SSR enabled.**
> Pure Svelte 5 SPAs (or SvelteKit with `ssr: false`) can safely use module-level exports.

## The Problem

In SvelteKit, server-side rendering (SSR) means your code runs on the server for each request. **Module-level state persists between requests**, causing data to leak between users.

```typescript
// CounterState.svelte.ts

// DANGER: This instance is SHARED across ALL server requests!
export const counterState = new CounterStateClass();
```

**What happens:**
1. User A visits → `count` becomes 5
2. User B visits → `count` starts at 5 (leaked from User A!)

## The Rules

### Never Do This

```typescript
// ❌ WRONG: Module-level instance export
export const state = new MyStateClass();

// ❌ WRONG: Module-level $state export
export let count = $state(0);

// ❌ WRONG: Mutating module-level state
let moduleState = { count: 0 };
export function increment() {
	moduleState.count++; // Leaks between requests!
}
```

### Always Do This

```typescript
// ✅ RIGHT: Context-based state
import { setContext, getContext } from 'svelte';

const KEY = Symbol('state');

export const setState = () => {
	return setContext(KEY, new MyStateClass());
};

export const getState = () => {
	return getContext<MyState>(KEY);
};
```

## Why Context is Safe

Context is **component-scoped**, not module-scoped:

```
Request A: +layout.svelte creates Context A
           └── Components get Context A

Request B: +layout.svelte creates Context B (separate!)
           └── Components get Context B
```

Each request gets a fresh layout component instance, which creates a fresh context.

## Safe Patterns

### Pattern 1: Context API (Recommended)

```typescript
// UserState.svelte.ts
import { getContext, setContext } from 'svelte';

interface UserState {
	user: User | null;
	login: (user: User) => void;
	logout: () => void;
}

class UserStateClass implements UserState {
	user = $state<User | null>(null);
	login = (user: User) => { this.user = user; };
	logout = () => { this.user = null; };
}

const USER_KEY = Symbol('user-state');

export const setUserState = () => setContext(USER_KEY, new UserStateClass());
export const getUserState = () => getContext<UserState>(USER_KEY);
```

### Pattern 2: Factory Functions (For Non-Shared State)

```typescript
// createChatState.svelte.ts
export function createChatState() {
	// Fresh instance each call - safe!
	return new ChatStateClass();
}
```

```svelte
<!-- +page.svelte -->
<script>
	import { createChatState } from './createChatState.svelte';

	// Fresh instance for this component
	const chatState = createChatState();
</script>
```

### Pattern 3: Server Locals (For Request Data)

```typescript
// hooks.server.ts
export const handle = async ({ event, resolve }) => {
	// Use locals for request-specific data
	event.locals.user = await getUserFromSession(event.cookies);
	return resolve(event);
};

// +layout.server.ts
export const load = async ({ locals }) => {
	return { user: locals.user };
};
```

## What's Safe at Module Level?

| Safe                          | Why                              |
| ----------------------------- | -------------------------------- |
| Pure functions                | No state to leak                 |
| Type definitions              | No runtime value                 |
| Constants (truly immutable)   | Same value for everyone          |
| Context key symbols           | Just identifiers                 |
| Class definitions (not instances) | Blueprint, not data          |

| Unsafe                        | Why                              |
| ----------------------------- | -------------------------------- |
| Class instances               | Shared mutable state             |
| `$state()` variables          | Reactive state shared            |
| Mutable objects/arrays        | Mutations leak between requests  |
| Counters, accumulators        | Accumulate across requests       |

## Testing for SSR Safety

```typescript
// If you can answer "yes" to these, it's unsafe:
// 1. Does this value persist between function calls?
// 2. Can this value be mutated?
// 3. Is this exported for use in components?

// Example unsafe:
let count = 0;
export const increment = () => count++; // Persists + mutates + exported = UNSAFE

// Example safe:
export const createCounter = () => {
	let count = $state(0);
	return { count, increment: () => count++ };
}; // Fresh each call = SAFE
```

## Client-Only State

If state is truly client-only (never runs on server), you CAN use module-level:

```typescript
// This is safe IF the file is never imported during SSR
import { browser } from '$app/environment';

// Guard the initialization
export const clientOnlyState = browser ? new MyStateClass() : null;
```

But **prefer context anyway** - it's safer and more predictable.

## Quick Reference

| Pattern                     | SSR Safe? | Use Case                      |
| --------------------------- | --------- | ----------------------------- |
| Context + setContext        | Yes       | Shared state across tree      |
| Factory function            | Yes       | Component-local state         |
| `event.locals`              | Yes       | Request-specific server data  |
| Module-level instance       | **NO**    | Never use in SvelteKit        |
| Module-level $state         | **NO**    | Never use in SvelteKit        |
| Exported mutable object     | **NO**    | Never use in SvelteKit        |
