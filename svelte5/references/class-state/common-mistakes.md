# Common Mistakes: Anti-Patterns and Fixes

## Top Mistakes with Class-Based State

### 1. Wrong File Extension

**WRONG:**

```typescript
// CounterState.ts  <-- Missing .svelte extension!
class CounterState {
	count = $state(0); // ERROR: $state is not defined
}
```

**RIGHT:**

```typescript
// CounterState.svelte.ts  <-- .svelte.ts required for runes
class CounterState {
	count = $state(0); // Works!
}
```

**Why:** Runes (`$state`, `$derived`, `$effect`) only work in `.svelte` and `.svelte.ts` files.

---

### 2. Exporting Module-Level State (SSR Leak)

**WRONG:**

```typescript
// store.svelte.ts
export const appState = new AppStateClass(); // Shared between ALL requests!
```

**RIGHT:**

```typescript
// store.svelte.ts
const KEY = Symbol('app-state');
export const setAppState = () => setContext(KEY, new AppStateClass());
export const getAppState = () => getContext<AppState>(KEY);
```

**Why:** Module-level exports persist between server requests, leaking data between users.

---

### 3. Regular Methods Instead of Arrow Functions

**WRONG:**

```typescript
class Counter {
	count = $state(0);

	increment() {
		this.count++; // `this` is undefined when passed as callback!
	}
}
```

```svelte
<button onclick={counter.increment}>+</button>
<!-- ERROR: Cannot read property 'count' of undefined -->
```

**RIGHT:**

```typescript
class Counter {
	count = $state(0);

	increment = () => {
		this.count++; // Arrow functions capture `this`
	};
}
```

```svelte
<button onclick={counter.increment}>+</button>
<!-- Works! -->
```

**Why:** Arrow functions lexically bind `this`. Regular methods lose `this` when passed as callbacks.

---

### 4. Setting Context in Wrong Location

**WRONG:**

```svelte
<!-- +page.svelte -->
<script>
	import { setCounterState } from './CounterState.svelte';
	setCounterState(); // Only available in THIS page, not siblings!
</script>
```

**RIGHT:**

```svelte
<!-- +layout.svelte -->
<script>
	import { setCounterState } from './CounterState.svelte';
	setCounterState(); // Available to ALL descendant pages
	let { children } = $props();
</script>
{@render children()}
```

**Why:** Context flows DOWN the tree. Set in a common ancestor of all consumers.

---

### 5. Using String Keys (Collision Risk)

**WRONG:**

```typescript
const KEY = 'counter'; // Could collide with other libraries!

export const setCounterState = () => setContext(KEY, new CounterStateClass());
```

**RIGHT:**

```typescript
const KEY = Symbol('counter'); // Guaranteed unique

export const setCounterState = () => setContext(KEY, new CounterStateClass());
```

**Why:** Symbols are guaranteed unique. Strings can collide with other code using the same key.

---

### 6. Using Old Store Syntax

**WRONG (Svelte 4 pattern):**

```typescript
import { writable } from 'svelte/store';

export const count = writable(0);
```

```svelte
<script>
	import { count } from './store';
</script>
<button on:click={() => $count++}>{$count}</button>
```

**RIGHT (Svelte 5 pattern):**

```typescript
// CounterState.svelte.ts
class CounterStateClass {
	count = $state(0);
	increment = () => { this.count++; };
}
```

```svelte
<script>
	import { getCounterState } from './CounterState.svelte';
	const state = getCounterState();
</script>
<button onclick={state.increment}>{state.count}</button>
```

**Why:** Class-based state with runes is more performant and has better TypeScript support than the old store API.

---

### 7. Forgetting to Call getContext

**WRONG:**

```svelte
<script>
	import { CounterState } from './CounterState.svelte';
	const state = CounterState; // This is the CLASS, not an instance!
</script>
```

**RIGHT:**

```svelte
<script>
	import { getCounterState } from './CounterState.svelte';
	const state = getCounterState(); // Call the function!
</script>
```

---

### 8. Not Handling Missing Context

**WRONG:**

```typescript
export const getState = () => getContext<MyState>(KEY);
// Returns undefined if context not set - silent failure
```

**RIGHT:**

```typescript
import { hasContext, getContext } from 'svelte';

export const getState = () => {
	if (!hasContext(KEY)) {
		throw new Error('State not found. Ensure setState() is called in a parent layout.');
	}
	return getContext<MyState>(KEY);
};
```

---

### 9. Directly Exporting $state Variables

**WRONG:**

```typescript
// store.svelte.ts
export let count = $state(0);
// Importing this gives the CURRENT value, not a reactive reference!
```

**RIGHT:**

```typescript
// store.svelte.ts
class Store {
	count = $state(0);
}
// Export via context, not directly
```

**Why:** Exporting raw `$state` only exports the current value at import time, not a reactive reference.

---

### 10. Mixing Svelte 4 and 5 Event Syntax

**WRONG:**

```svelte
<button on:click={state.increment}>{state.count}</button>
<!-- on:click is Svelte 4 -->
```

**RIGHT:**

```svelte
<button onclick={state.increment}>{state.count}</button>
<!-- onclick is Svelte 5 -->
```

---

## Quick Checklist

Before using class-based state:

- [ ] File extension is `.svelte.ts`
- [ ] Using context API (not module-level exports)
- [ ] Methods are arrow functions
- [ ] Context set in layout (not page)
- [ ] Using Symbol for context key
- [ ] Using Svelte 5 syntax (`onclick` not `on:click`)
- [ ] Handling missing context with `hasContext`
