# TypeScript Patterns

Use TypeScript to make component APIs explicit. Keep types close to the component unless they are shared API.

## Props

```svelte
<script lang="ts">
  type Props = {
    value: string;
    disabled?: boolean;
    onchange?: (value: string) => void;
  };

  let { value, disabled = false, onchange }: Props = $props();
</script>
```

## Snippets

```svelte
<script lang="ts" generics="T">
  import type { Snippet } from 'svelte';

  type Props<T> = {
    items: T[];
    row: Snippet<[item: T]>;
  };

  let { items, row }: Props<T> = $props();
</script>

{#each items as item}
  {@render row(item)}
{/each}
```

## Wrapper Components

Use `svelte/elements` types when wrapping native elements.

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

## Component Types

Use Svelte's component utility types when accepting or reflecting components.

```ts
import type { Component, ComponentProps } from 'svelte';
import Icon from './Icon.svelte';

type IconProps = ComponentProps<typeof Icon>;
type AnyIcon = Component<IconProps>;
```

## Review Checklist

- Are non-trivial props typed with a named `Props` type?
- Are callback props typed with their payloads and return type?
- Are snippets typed with `Snippet<[...args]>`?
- Are wrapper components using `svelte/elements` instead of broad `any`/`HTMLAttributes` guesses?
- Are generic components actually constrained enough to be useful?
- Are component utility types used rather than hand-written component shapes?

## Common Mistakes

| Mistake | Fix |
|---|---|
| `let props: any = $props()` | Define `Props` |
| Untyped snippets | Import and use `Snippet` |
| Wrapper drops native attributes/events | Extend the right `svelte/elements` type |
| Boolean prop combinations create impossible states | Use variants or discriminated unions |
| Exported internal types become accidental public API | Keep local unless consumers need them |

## Official References

- [Svelte docs: TypeScript](https://svelte.dev/docs/svelte/typescript)
- [Svelte docs: Typing wrapper components](https://svelte.dev/docs/svelte/typescript#Typing-wrapper-components)
