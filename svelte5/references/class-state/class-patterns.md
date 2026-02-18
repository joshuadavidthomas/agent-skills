# Class Patterns: Interface-First Design

## The Pattern

Define an interface for the public API, implement with a class using `$state` fields.

```typescript
// ChatState.svelte.ts
type Message = { role: 'user' | 'assistant'; content: string; id: string };

// 1. Define the public contract
interface ChatState {
	messages: Message[];
	isLoading: boolean;
	sendMessage: (message: string) => void;
}

// 2. Implement with reactive class fields
class ChatStateClass implements ChatState {
	messages = $state<Message[]>([]);
	isLoading = $state(false);

	// Private data (not in interface)
	private responses = ['Response 1', 'Response 2'];

	// Arrow function methods for correct `this` binding
	sendMessage = (message: string) => {
		this.isLoading = true;
		this.messages.push({ role: 'user', content: message, id: crypto.randomUUID() });

		setTimeout(() => {
			this.messages.push({
				role: 'assistant',
				content: this.responses[Math.floor(Math.random() * this.responses.length)],
				id: crypto.randomUUID()
			});
			this.isLoading = false;
		}, 400);
	};
}
```

## Why Interface-First?

| Benefit              | Explanation                                          |
| -------------------- | ---------------------------------------------------- |
| Clear contract       | Consumers see exactly what's available               |
| Encapsulation        | Private fields/methods hidden from interface         |
| Type safety          | TypeScript enforces implementation matches interface |
| Testability          | Easy to mock interface for testing                   |
| Documentation        | Interface is self-documenting API                    |

## Method Patterns

### Arrow Functions (Recommended)

```typescript
class Counter {
	count = $state(0);

	// Arrow functions capture `this` correctly
	increment = () => {
		this.count++;
	};

	// Safe to pass as callback
	// <button onclick={counter.increment}>
}
```

### Regular Methods (Avoid)

```typescript
class Counter {
	count = $state(0);

	// PROBLEM: `this` binding issues when passed as callback
	increment() {
		this.count++;
	}
}

// This breaks:
// <button onclick={counter.increment}> // `this` is undefined!

// Would need explicit binding:
// <button onclick={() => counter.increment()}>
```

## Computed Properties with $derived

```typescript
class TodoState {
	todos = $state<Todo[]>([]);

	// Computed property using getter + $derived
	get completed() {
		return $derived(this.todos.filter((t) => t.done).length);
	}

	// Or as a method
	getCompleted = () => this.todos.filter((t) => t.done).length;
}
```

## Array Mutations

`$state` arrays support **all** mutation methods. Deep reactivity works:

```typescript
class TodoState {
	items = $state<Item[]>([]);

	// All of these trigger reactivity:
	add = (item: Item) => {
		this.items.push(item);          // ✅ Works
	};

	remove = (id: string) => {
		const idx = this.items.findIndex((i) => i.id === id);
		if (idx !== -1) this.items.splice(idx, 1);  // ✅ Works
	};

	// Filter reassignment also works:
	removeAlt = (id: string) => {
		this.items = this.items.filter((i) => i.id !== id);  // ✅ Works
	};

	clear = () => {
		this.items.length = 0;          // ✅ Works (clears array)
	};
}
```

**Both patterns work:** `splice()` for in-place mutation, `filter()` for reassignment.

## Async Methods

```typescript
class DataState {
	data = $state<Item[]>([]);
	isLoading = $state(false);
	error = $state<string | null>(null);

	fetchData = async () => {
		this.isLoading = true;
		this.error = null;

		try {
			const response = await fetch('/api/data');
			this.data = await response.json();
		} catch (e) {
			this.error = e instanceof Error ? e.message : 'Unknown error';
		} finally {
			this.isLoading = false;
		}
	};
}
```

## Timers and Auto-Dismiss

For methods that need delayed actions (like toast auto-dismiss):

```typescript
class ToastState {
	messages = $state<Toast[]>([]);
	private timers = new Map<string, ReturnType<typeof setTimeout>>();

	show = (message: string, type: string, autoDismissMs = 5000): string => {
		const id = crypto.randomUUID();
		this.messages.push({ id, message, type });

		// Set auto-dismiss timer
		const timer = setTimeout(() => this.dismiss(id), autoDismissMs);
		this.timers.set(id, timer);

		return id;  // Return ID for programmatic control
	};

	dismiss = (id: string) => {
		// Clear timer if exists
		const timer = this.timers.get(id);
		if (timer) {
			clearTimeout(timer);
			this.timers.delete(id);
		}

		this.messages = this.messages.filter((t) => t.id !== id);
	};
}
```

**Note:** `setTimeout` in class methods is safe - it only runs client-side after hydration.

## Constructor Parameters

```typescript
interface UserState {
	user: User | null;
	logout: () => void;
}

class UserStateClass implements UserState {
	user = $state<User | null>(null);

	constructor(initialUser: User | null) {
		this.user = initialUser;
	}

	logout = () => {
		this.user = null;
	};
}

// In layout:
export const setUserState = (user: User | null) => {
	return setContext(KEY, new UserStateClass(user));
};
```

## File Naming

| File                     | Runes? | Use Case                 |
| ------------------------ | ------ | ------------------------ |
| `State.svelte.ts`        | Yes    | State classes with runes |
| `State.ts`               | No     | Plain TypeScript         |
| `+page.svelte`           | Yes    | Components               |
| `+page.server.ts`        | No     | Server-only code         |

**Rule:** `.svelte.ts` extension is **required** for `$state`, `$derived`, `$effect` outside `.svelte` files.

## Exporting Types

Export types that consumers need:

```typescript
// ToastState.svelte.ts

// Export the type for consumers
export type Toast = {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info';
};

// Interface can stay internal or be exported
interface ToastState {
	messages: Toast[];
	show: (message: string, type: Toast['type']) => string;
	dismiss: (id: string) => void;
}

// ... class implementation
```

**When to export types:**
- Type is needed by consumers (e.g., for typing variables)
- Type appears in public method signatures
- Type is used in component props
