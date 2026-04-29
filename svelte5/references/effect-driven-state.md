# Effects That Compute State

## The Smell

Using `$effect` to keep one reactive value synchronized with another.

```svelte
<script lang="ts">
  let items = $state<Item[]>([]);
  let visible = $state<Item[]>([]);

  $effect(() => {
    visible = items.filter((item) => !item.hidden);
  });
</script>
```

This creates writable state for something that is not really state.

## Why It Happens

React trains people to think "when X changes, run an effect and set Y." Vue watchers and Svelte 4 reactive statements can also blur the line between computed values and side effects.

## The Svelte Mental Model

If a value can be computed from current inputs, it is not state. It is derived data. Svelte should see that relationship directly.

```svelte
<script lang="ts">
  let items = $state<Item[]>([]);
  const visible = $derived(items.filter((item) => !item.hidden));
</script>
```

`$effect` is for the outside world: subscriptions, timers, observers, imperative libraries, logging, analytics, and APIs that need setup/cleanup.

## Migration Strategy

1. Find what the effect writes.
2. Ask whether that value is a pure function of current props/state.
3. Replace writable state with `$derived` or `$derived.by`.
4. Keep the effect only if it touches something outside Svelte's reactive graph.
5. If the effect remains, return cleanup for resources it creates.

## When `$effect` Is Fine

- subscribing to an external source
- starting/stopping timers
- attaching observers or imperative library instances
- logging, analytics, telemetry
- synchronizing with browser APIs that are not represented in markup

## Where This Habit Comes From

- **React** — `useEffect` is commonly used as a synchronization primitive
- **Vue** — watchers are easy to reach for before computed values
- **Svelte 4** — `$:` mixed derived values and side-effecting reactive statements

## Official References

- [Svelte docs: $derived](https://svelte.dev/docs/svelte/$derived)
- [Svelte docs: $effect](https://svelte.dev/docs/svelte/$effect)
