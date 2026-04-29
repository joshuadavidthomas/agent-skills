# Stores in Svelte 5

Runes replace many store use cases, but stores still matter. Do not blindly migrate every `writable`/`readable`.

## Prefer Runes When

- State belongs to a component or descendant tree.
- State has methods and invariants: use a `.svelte.ts` class.
- You want ordinary TypeScript object/class ergonomics.
- The state does not need the store contract.

## Keep Stores When

- Interoperating with libraries that expose or consume Svelte stores.
- Representing external streams, subscriptions, sockets, media queries, or observables.
- You need manual subscription semantics outside Svelte components.
- Existing store APIs are public and stable.
- Derived store composition is already simple and correct.

## Review Checklist

- Is the store module safe in SSR contexts? Avoid request-specific mutable globals.
- Is `$store` auto-subscription used only in `.svelte` components?
- Are subscriptions cleaned up outside components?
- Would a `.svelte.ts` class clarify ownership and behavior?
- Is the code mixing stores and runes for the same state without a clear boundary?
- Is derived data implemented as a store only because of old Svelte 4 habits?

## Migration Direction

Old local store state:

```ts
import { writable } from 'svelte/store';

export const count = writable(0);
```

Often becomes request/local safe state:

```ts
// CounterState.svelte.ts
class CounterState {
  count = $state(0);
  increment = () => { this.count++; };
}

export const createCounterState = () => new CounterState();
```

But external stream stores can remain stores.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Exported writable for per-user SSR state | Use factory/context/request-owned state |
| Manual subscribe without unsubscribe | Store and call the unsubscribe function |
| Store used only for local component state | Use `$state` |
| Rewriting a stable public store API for no gain | Keep the store |
| `$store` used outside component markup/script | Use explicit subscription or interop helpers |

## Official References

- [Svelte docs: Stores](https://svelte.dev/docs/svelte/stores)
- [Svelte reference: svelte/store](https://svelte.dev/docs/svelte/svelte-store)
