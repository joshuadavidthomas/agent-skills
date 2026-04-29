# Mirroring Props Into State

## The Smell

Copying a prop into local `$state` without naming a separate ownership model.

```svelte
<script lang="ts">
  let { user }: { user: User } = $props();
  let localUser = $state(user);
</script>
```

Now the component has two sources of truth: the parent's `user` and the child's `localUser`.

## Why It Happens

React patterns like `useState(props.initialValue)` make local copies feel normal. They are fine for explicit initial values, but dangerous when the prop is expected to stay live.

## The Svelte Mental Model

Props are inputs. If the displayed value is a function of props, derive it. If the child needs editable state, name it as a draft and define how it resets or commits.

```svelte
<script lang="ts">
  let { user }: { user: User } = $props();
  const displayName = $derived(user.name.trim() || user.email);
</script>
```

For an actual draft:

```svelte
<script lang="ts">
  let { user, onsave }: { user: User; onsave?: (user: User) => void } = $props();
  let draft = $state(structuredClone(user));

  const reset = () => {
    draft = structuredClone(user);
  };
</script>
```

## Migration Strategy

1. Find local state initialized from props.
2. Decide whether it should remain synchronized with the prop.
3. If yes, replace with `$derived` or use the prop directly.
4. If no, rename it to `draft`, `editing`, or another ownership-revealing name.
5. Add explicit reset/commit behavior.

## When Local Copies Are Fine

- editable form drafts
- optimistic UI that may diverge temporarily
- animation/transient state initialized from a prop
- uncontrolled components that intentionally use an `initialValue` prop

## Where This Habit Comes From

- **React** — `useState(prop)` and controlled/uncontrolled component patterns
- **Vue** — local refs initialized from props
- **Svelte 4** — `$:` statements sometimes papered over unclear ownership

## Official References

- [Svelte docs: $props](https://svelte.dev/docs/svelte/$props)
- [Svelte docs: $derived](https://svelte.dev/docs/svelte/$derived)
