# Reactivity Is Read-Tracked

## The Smell

Debugging Svelte effects as if they had an explicit dependency array or reran because something was written somewhere nearby.

```svelte
<script lang="ts">
  $effect(() => {
    console.log(form); // reads the whole object
  });
</script>
```

The effect may rerun more broadly than intended because of what it reads.

## Why It Happens

React makes dependencies explicit with arrays. Some systems are write-tracked or subscription-based. Svelte tracks dependencies by reactive reads during a derived/effect execution.

## The Svelte Mental Model

A `$derived` or `$effect` depends on the reactive values it reads while running. If it reruns unexpectedly, inspect the reads.

```svelte
<script lang="ts">
  $effect(() => {
    console.log(form.valid, form.pending);
  });
</script>
```

Read only what the effect actually needs. Name derived values when that clarifies the graph.

## Migration Strategy

1. Find effects that read broad objects or call helpers with hidden reactive reads.
2. Inline or name the specific reactive values needed.
3. Move pure computations to `$derived`.
4. Use `$inspect` temporarily to observe changes.
5. Reach for `untrack` only when you intentionally need a read that is not a dependency.

## When Broad Reads Are Fine

- debug-only logging
- serialization/snapshot effects that intentionally depend on the whole object
- small local objects where broad dependency is clearer than field-by-field tracking

## Where This Habit Comes From

- **React** — explicit dependency arrays encourage thinking about listed variables, not reads
- **MobX/Vue** — similar tracking exists, but habits vary around refs/computed/watchers
- **Svelte 4** — `$:` dependencies were compiler-discovered but less explicit than runes

## Official References

- [Svelte docs: $derived dependencies](https://svelte.dev/docs/svelte/$derived#Understanding-dependencies)
- [Svelte docs: $effect dependencies](https://svelte.dev/docs/svelte/$effect#Understanding-dependencies)
