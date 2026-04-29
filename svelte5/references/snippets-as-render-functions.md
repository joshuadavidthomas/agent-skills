# Snippets as Render Functions

## The Smell

Treating snippets as renamed slots: untyped, vague holes in a component's markup.

```svelte
<!-- Vague slot-shaped API in Svelte 5 clothes -->
{@render children?.()}
```

This is sometimes fine, but it misses the main power of snippets: parameterized, typed rendering controlled by the parent.

## Why It Happens

Svelte 4 slots, Vue slots, and React `children` all train people to think of child content as a passive hole. Svelte 5 snippets are closer to typed render functions.

## The Svelte Mental Model

A snippet is a function that returns UI. It can accept parameters, close over its definition site, and be passed as a prop.

```svelte
<script lang="ts" generics="T">
  import type { Snippet } from 'svelte';

  let { items, row }: { items: T[]; row: Snippet<[item: T]> } = $props();
</script>

{#each items as item}
  {@render row(item)}
{/each}
```

The component owns iteration/layout. The parent owns how each item renders.

## Migration Strategy

1. Replace default children with `children?: Snippet` only when the component truly accepts arbitrary content.
2. For data-driven UI, pass data into typed snippets instead of making the parent duplicate layout logic.
3. Name snippets by role: `row`, `header`, `empty`, `footer`.
4. Type snippet parameters.
5. Avoid prop names that conflict with implicit `children`.

## When Plain `children` Is Fine

- layout containers
- cards/panels that just frame arbitrary content
- compatibility wrappers around existing slot APIs
- simple app code where typed snippet parameters add no clarity

## Where This Habit Comes From

- **Svelte 4** — named/default slots
- **Vue** — scoped slots, but often without strong typing
- **React** — `children` as arbitrary nested content or render props

## Official References

- [Svelte docs: Snippets](https://svelte.dev/docs/svelte/snippet)
- [Svelte docs: @render](https://svelte.dev/docs/svelte/@render)
