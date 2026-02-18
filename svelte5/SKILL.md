---
name: svelte5
description: "Svelte 5 guidance — runes ($state, $derived, $effect, $props, $bindable), class-based state management, reactive patterns, context API, snippets vs slots, and Svelte 4→5 migration. Use for any Svelte 5 reactivity question, component props, sharing state across components, or migrating from writable/readable stores. Triggers on: $state, $derived, $effect, $props, $bindable, runes, Svelte 5, .svelte.ts, writable, readable, stores migration."
---

# Svelte 5

Svelte 5 replaces stores with **runes** (reactive primitives) and **class-based state** (the idiomatic replacement for `writable`/`readable`). Don't mix Svelte 4 and 5 syntax — pick one.

## Topics

| Topic | File |
|-------|------|
| Rune patterns, Svelte 4→5 migration, component API | [runes.md](runes.md) |
| Class patterns, context API, SSR safety | [class-state.md](class-state.md) |

## Runes Quick Reference

**Which rune?** State: `$state()` | Computed: `$derived()` | Side effect: `$effect()` | Props: `$props()` | Bindable: `$bindable()`

Runes are **top-level only** — you can't call them inside functions or blocks.

```svelte
<script>
  let count = $state(0);
  const doubled = $derived(count * 2);

  $effect(() => {
    console.log(`Count is ${count}`);
  });
</script>

<button onclick={() => count++}>
  {count} (doubled: {doubled})
</button>
```

Key behaviors:
- Objects and arrays are **deeply reactive** by default
- `$derived` can be reassigned (Svelte 5.25+) — use `const` for read-only derived values
- Event handlers: `onclick` not `on:click`
- Children: `{@render children()}` not `<slot />`

→ Deep dives: [runes.md](runes.md) for full rune patterns, migration guide, and component API.

## Class-Based State

Classes with `$state` fields are the idiomatic way to manage client-side state. More performant than stores, better TypeScript support, cleaner encapsulation.

**File extension:** `.svelte.ts` required for `$state` outside components.

```typescript
// CounterState.svelte.ts
interface CounterState {
  count: number;
  increment: () => void;
}

class CounterStateClass implements CounterState {
  count = $state(0);
  increment = () => { this.count++; };  // Arrow methods avoid `this` binding issues
}

export const createCounterState = () => new CounterStateClass();
```

```svelte
<script>
  import { createCounterState } from './CounterState.svelte';
  const state = createCounterState();
</script>
<button onclick={state.increment}>{state.count}</button>
```

### Sharing State (Context API)

Local only → instantiate directly. Shared across components → use context:

```typescript
// CounterState.svelte.ts
import { getContext, setContext, hasContext } from 'svelte';

const KEY = Symbol('counter');  // Symbol keys avoid collisions
export const setCounterState = () => setContext(KEY, new CounterStateClass());
export const getCounterState = () => {
  if (!hasContext(KEY)) throw new Error('Counter context not set');
  return getContext<CounterState>(KEY);
};
```

```svelte
<!-- Parent: set context -->
<script>
  import { setCounterState } from './CounterState.svelte';
  setCounterState();
</script>

<!-- Any descendant: consume -->
<script>
  import { getCounterState } from './CounterState.svelte';
  const state = getCounterState();
</script>
```

**⚠️ SvelteKit users:** Never export module-level state instances — causes SSR leaks where state bleeds between requests.

→ Deep dives: [class-state.md](class-state.md) for arrays, timers, async patterns, and context vs scoped decisions.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `on:click={handler}` | `onclick={handler}` (Svelte 5 syntax) |
| `<slot />` | `{@render children()}` |
| `$state` inside a function | Move to top level of `<script>` or class field |
| Exporting module-level `$state` instance | Use factory function or context API |
| `let x = $derived(...)` then reassigning | Use `const` if you want read-only |
| `.ts` extension for reactive files | Must be `.svelte.ts` for `$state` outside components |
| Mixing `writable()`/`readable()` with runes | Pick one — don't mix Svelte 4/5 patterns |

## Reference Index

**Runes:** [Reactivity Patterns](references/runes/reactivity-patterns.md) · [Migration Gotchas](references/runes/migration-gotchas.md) · [Component API](references/runes/component-api.md) · [Snippets vs Slots](references/runes/snippets-vs-slots.md) · [Common Mistakes](references/runes/common-mistakes.md)

**Class State:** [Class Patterns](references/class-state/class-patterns.md) · [Context vs Scoped](references/class-state/context-vs-scoped.md) · [Common Mistakes](references/class-state/common-mistakes.md) · [SSR Safety](references/class-state/ssr-safety.md)
