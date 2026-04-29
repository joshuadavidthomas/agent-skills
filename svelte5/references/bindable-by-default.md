# Bindable by Default

## The Smell

Making component props `$bindable` because it is convenient, not because two-way mutation is the intended API.

```svelte
<script lang="ts">
  let { value = $bindable(''), label = $bindable('') } = $props();
</script>
```

This lets the child mutate parent-owned state broadly and makes ownership harder to reason about.

## Why It Happens

Svelte has excellent binding ergonomics, so it is tempting to use binding as the default communication pattern. Vue's `v-model` and Svelte 4 component bindings reinforce the habit.

## The Svelte Mental Model

Props are inputs. Callback props report events. `$bindable` is a deliberate promise that the child participates in owning a value.

Prefer this for most component events:

```svelte
<script lang="ts">
  let { value, onchange }: { value: string; onchange?: (value: string) => void } = $props();
</script>

<input {value} oninput={(event) => onchange?.(event.currentTarget.value)} />
```

Use `$bindable` when the component is intentionally controlled with binding:

```svelte
<script lang="ts">
  let { value = $bindable('') }: { value?: string } = $props();
</script>

<input bind:value />
```

## Migration Strategy

1. List each `$bindable` prop.
2. Ask whether the child should mutate that value directly.
3. Replace incidental bindings with callback props.
4. Keep `$bindable` for form-control-like components or intentional two-way APIs.
5. Document binding behavior for public components.

## When `$bindable` Is Fine

- input-like components
- selected/open state in controlled UI components
- compatibility with existing Svelte component APIs
- small local component pairs where two-way ownership is genuinely simpler

## Where This Habit Comes From

- **Vue** — `v-model` makes two-way component APIs common
- **Svelte 4** — component `bind:` was idiomatic for many controls
- **Angular** — two-way binding as an application-level default

## Official References

- [Svelte docs: $bindable](https://svelte.dev/docs/svelte/$bindable)
- [Svelte docs: bind: component props](https://svelte.dev/docs/svelte/bind#bind_property-for-components)
