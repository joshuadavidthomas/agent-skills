# Svelte Component Patterns

Use this for implementation guidance beyond basic runes.

## Props

Use `$props()` with an explicit type for non-trivial components.

```svelte
<script lang="ts">
  type Props = {
    value: string;
    placeholder?: string;
    disabled?: boolean;
  };

  let { value, placeholder = '', disabled = false }: Props = $props();
</script>
```

For rest props, keep the forwarded surface intentional.

```svelte
<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';

  type Props = HTMLButtonAttributes & {
    variant?: 'primary' | 'secondary';
  };

  let { variant = 'primary', children, ...rest }: Props = $props();
</script>

<button {...rest} class={["button", `button-${variant}`, rest.class]}>
  {@render children?.()}
</button>
```

## Bindable Props

Use `$bindable()` only when the child is allowed to mutate parent-owned state.

```svelte
<script lang="ts">
  let { value = $bindable('') }: { value?: string } = $props();
</script>

<input bind:value />
```

Prefer callback props when the parent should decide how to handle a change.

```svelte
<script lang="ts">
  type Props = {
    value: string;
    oninput?: (value: string) => void;
  };

  let { value, oninput }: Props = $props();
</script>

<input {value} oninput={(event) => oninput?.(event.currentTarget.value)} />
```

## Snippets and Children

Svelte 5 uses snippets instead of slots.

```svelte
<script lang="ts">
  import type { Snippet } from 'svelte';

  type Props = {
    children?: Snippet;
    footer?: Snippet<[count: number]>;
  };

  let { children, footer }: Props = $props();
  let count = $state(0);
</script>

<div class="panel">
  {@render children?.()}

  {#if footer}
    <footer>{@render footer(count)}</footer>
  {/if}
</div>
```

## Events

Use event attributes for DOM events and callback props for component events.

```svelte
<button type="button" onclick={save}>Save</button>
```

```svelte
<script lang="ts">
  type Props = {
    onselect?: (id: string) => void;
  };

  let { onselect }: Props = $props();
</script>

<button type="button" onclick={() => onselect?.(id)}>Select</button>
```

Avoid `createEventDispatcher` in new Svelte 5 code unless maintaining an old API.

## Each Blocks

Use keyed each blocks when items have stable identity, local DOM state, transitions, or reordering.

```svelte
{#each todos as todo (todo.id)}
  <TodoItem {todo} />
{/each}
```

Unkeyed each blocks are fine for simple static lists where order and identity do not matter.

## Conditional Markup

Keep markup readable. If conditions repeat, derive a named value.

```svelte
<script lang="ts">
  const canSubmit = $derived(form.valid && !form.pending);
</script>

<button type="submit" disabled={!canSubmit}>Save</button>
```

## Classes and Styling

Use Svelte class directives for simple booleans.

```svelte
<button class:active class:error={status === 'error'}>Save</button>
```

For variant systems, prefer a small helper or array/string composition that stays readable. Keep styling decisions near the component unless the project has a shared design-system convention.

## Actions and DOM APIs

Use actions for reusable imperative DOM behavior.

```svelte
<script lang="ts">
  function autofocus(node: HTMLElement) {
    node.focus();
  }
</script>

<input use:autofocus />
```

Use `$effect` for one-off imperative DOM work that depends on reactive state, and return cleanup when needed.

## Transitions

Use built-in transitions for local UI state. Be careful with transitions in large lists or SSR-sensitive layout assumptions.

```svelte
<script lang="ts">
  import { fade } from 'svelte/transition';

  let open = $state(false);
</script>

{#if open}
  <div transition:fade>Details</div>
{/if}
```

## Forms Inside Components

For plain Svelte forms:

- Keep controlled input state local unless parent coordination is required.
- Use real labels and input types.
- Put validation messages next to fields and connect them with `aria-describedby` when useful.
- Do not use client-only state as a substitute for server validation in SvelteKit.

For SvelteKit form actions, remote functions, progressive enhancement, or server validation, load the `sveltekit` skill.

## Official References

- [Svelte docs: $props](https://svelte.dev/docs/svelte/$props)
- [Svelte docs: Snippets](https://svelte.dev/docs/svelte/snippet)
- [Svelte 5 migration guide: Event changes](https://svelte.dev/docs/svelte/v5-migration-guide#Event-changes)
