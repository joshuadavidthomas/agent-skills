# Context vs Component-Scoped State

## Decision Matrix

| Scenario                               | Pattern           | Why                                      |
| -------------------------------------- | ----------------- | ---------------------------------------- |
| Form state in a single component       | Component-scoped  | No sharing needed                        |
| Chat messages in one page              | Component-scoped  | Isolated to that view                    |
| User session across app                | Context (layout)  | Shared across all routes                 |
| Shopping cart across pages             | Context (layout)  | Persists during navigation               |
| Toast notifications                    | Context (root)    | Global access needed                     |
| Modal/dialog state                     | Context or scoped | Depends on who controls it               |
| Theme/preferences                      | Context (root)    | App-wide setting                         |
| Counter shared between sibling routes  | Context (parent)  | Share via common ancestor                |

## Mental Model: The Component Tree

```
App.svelte (ROOT)              <-- setContext here = available everywhere
├── Header.svelte
├── Main.svelte
│   ├── Dashboard.svelte       <-- setContext here = Dashboard subtree only
│   │   ├── Stats.svelte
│   │   └── Settings.svelte
│   └── Profile.svelte
└── Footer.svelte
```

**Context flows DOWN the tree.** Set in parent, access in descendants.

> **SvelteKit:** Use `+layout.svelte` as your context provider - it wraps all child routes.

## Pattern 1: Component-Scoped State

Each component gets its own isolated instance.

```svelte
<!-- ChatPage.svelte -->
<script>
	import { createChatState } from './ChatState.svelte';

	// New instance for THIS component only
	const chatState = createChatState();
</script>

<Chat state={chatState} />
```

**Characteristics:**
- State resets when component unmounts
- No sharing between components
- Each instance is independent
- Good for: forms, local UI state, isolated features

## Pattern 2: Context-Based Shared State

Single instance shared across component tree.

### Step 1: Create State with Context Helpers

```typescript
// CounterState.svelte.ts
import { getContext, setContext, hasContext } from 'svelte';

interface CounterState {
	count: number;
	increment: () => void;
	decrement: () => void;
}

class CounterStateClass implements CounterState {
	count = $state(0);
	increment = () => { this.count++; };
	decrement = () => { this.count--; };
}

// Use Symbol for guaranteed unique key
const COUNTER_KEY = Symbol('counter-state');

export const setCounterState = () => {
	return setContext(COUNTER_KEY, new CounterStateClass());
};

export const getCounterState = () => {
	if (!hasContext(COUNTER_KEY)) {
		throw new Error('CounterState not found. Call setCounterState in a parent component.');
	}
	return getContext<CounterState>(COUNTER_KEY);
};
```

### Step 2: Set Context in Parent Component

```svelte
<!-- App.svelte (or any parent component) -->
<script>
	import { setCounterState } from './CounterState.svelte';

	// Create and register state for this subtree
	setCounterState();

	let { children } = $props();
</script>

<Header />
<main>{@render children()}</main>
<Footer />
```

> **SvelteKit:** Set context in `+layout.svelte` to share across routes.

### Step 3: Consume in Any Descendant

```svelte
<!-- Counter.svelte (used anywhere in subtree) -->
<script>
	import { getCounterState } from './CounterState.svelte';

	// Gets the SAME instance set in parent layout
	const state = getCounterState();
</script>

<button onclick={state.increment}>{state.count}</button>
```

**Characteristics:**
- Single instance shared across tree
- State persists during navigation within subtree
- All components see same data
- Good for: user sessions, app-wide settings, shared UI state

## Multiple Context Instances

Use different keys for independent stores of same type:

```typescript
const PRIMARY_KEY = Symbol('counter-primary');
const SECONDARY_KEY = Symbol('counter-secondary');

export const setPrimaryCounter = () =>
	setContext(PRIMARY_KEY, new CounterStateClass());

export const setSecondaryCounter = () =>
	setContext(SECONDARY_KEY, new CounterStateClass());

export const getPrimaryCounter = () =>
	getContext<CounterState>(PRIMARY_KEY);

export const getSecondaryCounter = () =>
	getContext<CounterState>(SECONDARY_KEY);
```

## Context with Initial Data (SvelteKit)

When using SvelteKit, you can initialize context with server-loaded data:

```svelte
<!-- +layout.svelte -->
<script>
	import { setUserState } from './UserState.svelte';

	// Data from +layout.server.ts load function
	let { data, children } = $props();

	// Initialize context with server data
	setUserState(data.user);
</script>

{@render children()}
```

```typescript
// UserState.svelte.ts
export const setUserState = (initialUser: User | null) => {
	const state = new UserStateClass();
	state.user = initialUser;
	return setContext(USER_KEY, state);
};
```

## Common Mistake: Wrong Level

```
App.svelte                  <-- setContext here
├── PageA.svelte            <-- getContext works
└── PageB.svelte            <-- getContext works

BUT:

├── PageA.svelte
│   └── setContext here     <-- WRONG: siblings can't access
└── PageB.svelte            <-- getContext fails!
```

**Rule:** Set context in a **common ancestor** of all components that need it.
