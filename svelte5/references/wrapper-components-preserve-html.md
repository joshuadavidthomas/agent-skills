# Wrapper Components Must Preserve HTML

## The Smell

A wrapper component makes a native element less capable than the element it wraps.

```svelte
<!-- Button.svelte -->
<script lang="ts">
  let { label, onclick }: { label: string; onclick?: () => void } = $props();
</script>

<div class="button" onclick={onclick}>{label}</div>
```

The wrapper lost native button semantics, attributes, keyboard behavior, and form behavior.

## Why It Happens

Design-system code often starts from visuals. React-style component APIs often hide the underlying platform element behind custom props.

## The Svelte Mental Model

A wrapper should preserve the platform contract unless it intentionally narrows it. If it wraps a button, it should behave like a button.

```svelte
<script lang="ts">
  import type { HTMLButtonAttributes } from 'svelte/elements';

  type Props = HTMLButtonAttributes & {
    variant?: 'primary' | 'secondary';
  };

  let { variant = 'primary', children, type = 'button', ...rest }: Props = $props();
</script>

<button {...rest} {type} class={["button", `button-${variant}`, rest.class]}>
  {@render children?.()}
</button>
```

## Migration Strategy

1. Identify the native element being wrapped.
2. Use the matching `svelte/elements` type.
3. Forward relevant native attributes and event handlers.
4. Preserve semantic defaults like `type="button"`.
5. Keep custom props additive, not replacements for native capability.

## When Narrow Wrappers Are Fine

- domain-specific components that intentionally expose a smaller API
- security/accessibility constraints where only a subset is allowed
- internal components used in one controlled context

Even then, preserve semantics for the behavior that remains.

## Where This Habit Comes From

- **React** — component prop APIs often replace native attributes
- **Design systems** — visual variants become the API before semantics are considered
- **CSS frameworks** — classes can make nonsemantic markup look correct

## Official References

- [Svelte docs: TypeScript wrapper components](https://svelte.dev/docs/svelte/typescript#Typing-wrapper-components)
- [Svelte docs: Typing wrapper components](https://svelte.dev/docs/svelte/typescript#Typing-wrapper-components)
