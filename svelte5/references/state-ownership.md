# State Ownership

## The Smell

State is reachable from everywhere, but no component or object clearly owns it.

```ts
// state.ts
export const modalOpen = writable(false);
export const selectedUser = writable<User | null>(null);
```

This may be fine, but often it is Svelte 4 muscle memory: every changing value becomes a global store.

## Why It Happens

React/Redux, Vue/Pinia, and Svelte 4 stores all encourage creating external state containers early. Svelte 5 makes local and reusable state cheap enough that global state should earn its place.

## The Svelte Mental Model

Place state at the smallest owner that can make correct decisions:

1. **One component owns it** → component `$state`.
2. **Reusable behavior owns it** → `.svelte.ts` class plus factory.
3. **A descendant tree shares it** → context.
4. **External stream/store contract matters** → Svelte store.
5. **Server/request owns it** → SvelteKit data flow, not client globals.

## Idiomatic Alternatives

Component-local:

```svelte
<script lang="ts">
  let open = $state(false);
</script>
```

Reusable state object:

```ts
// ModalState.svelte.ts
class ModalState {
  open = $state(false);
  show = () => { this.open = true; };
  hide = () => { this.open = false; };
}

export const createModalState = () => new ModalState();
```

Context for descendants:

```ts
import { getContext, setContext } from 'svelte';

const KEY = Symbol('modal');
export const setModalState = () => setContext(KEY, createModalState());
export const getModalState = () => getContext<ModalState>(KEY);
```

## Migration Strategy

1. List who reads and writes the state.
2. Identify the smallest common owner.
3. Move local-only state back into the component.
4. Move reusable behavior into a `.svelte.ts` class.
5. Use context when many descendants need the same object.
6. Keep stores only when subscription semantics or public API compatibility matter.

## When Global Stores Are Fine

- public library APIs based on the store contract
- external streams or subscriptions
- cross-tree state that is genuinely app-wide and client-only
- interop with code that expects a Svelte store

## Where This Habit Comes From

- **Svelte 4** — stores were the standard answer for shared state
- **React** — context/Redux/Zustand often become default before local ownership is tested
- **Vue** — Pinia/global composables can become the first reach

## Official References

- [Svelte docs: $state](https://svelte.dev/docs/svelte/$state)
- [Svelte docs: Context](https://svelte.dev/docs/svelte/context)
- [Svelte docs: Stores](https://svelte.dev/docs/svelte/stores)
