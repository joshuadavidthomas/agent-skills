# Svelte 5 Syntax Discipline

## The Smell

Mixing Svelte 4 and Svelte 5 component idioms in the same codebase or file.

```svelte
<script lang="ts">
  export let value: string;
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();
</script>

<button on:click={() => dispatch('change', value)}>
  <slot />
</button>
```

This is not just cosmetic. It usually means the component API and reactivity model were not redesigned for Svelte 5.

## Why It Happens

Migration tools and muscle memory produce mechanical translations. Svelte 4 patterns still work in some contexts, so code can drift into a half-migrated state.

## The Svelte Mental Model

Svelte 5 code should make dataflow explicit with runes and ordinary props/callbacks.

```svelte
<script lang="ts">
  import type { Snippet } from 'svelte';

  type Props = {
    value: string;
    onchange?: (value: string) => void;
    children?: Snippet;
  };

  let { value, onchange, children }: Props = $props();
</script>

<button type="button" onclick={() => onchange?.(value)}>
  {@render children?.()}
</button>
```

Use Svelte 4 syntax deliberately only when maintaining legacy code or public APIs that have not migrated.

## Migration Strategy

1. Check the installed Svelte version and project conventions.
2. Replace `export let` with typed `$props()` destructuring.
3. Replace `on:event` with event attributes such as `onclick`.
4. Replace `createEventDispatcher` with callback props for new APIs.
5. Replace slots with snippets/render tags.
6. Replace reactive `$:` statements with `$derived` or `$effect` according to whether they compute or side-effect.
7. Do not migrate mechanically without rechecking ownership and component API shape.

## When Old Syntax Is Fine

- project is still on Svelte 4
- compatibility layer for a public component API
- incremental migration with clear boundaries
- generated or vendored code that should not be hand-edited

## Where This Habit Comes From

- **Svelte 4** — old component API and reactivity syntax
- **Migration tools** — syntax conversion without design review
- **React/Vue habits** — event emitters and slot-like APIs mapped mechanically into Svelte

## Official References

- [Svelte docs: Svelte 5 migration guide](https://svelte.dev/docs/svelte/v5-migration-guide)
- [Svelte docs: What are runes?](https://svelte.dev/docs/svelte/what-are-runes)
