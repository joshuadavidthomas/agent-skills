# Deep State Without Immutable Ceremony

## The Smell

Writing React-style immutable updates for local Svelte state even when direct mutation is clearer.

```svelte
<script lang="ts">
  let todos = $state<Todo[]>([]);

  function toggle(id: string) {
    todos = todos.map((todo) => todo.id === id ? { ...todo, done: !todo.done } : todo);
  }
</script>
```

This works, but often obscures intent in Svelte 5.

## Why It Happens

React state updates depend on replacing identity. Vue refs also train people to think through wrappers and update APIs. Svelte 5 `$state` uses deep proxies for arrays and plain objects, so direct local mutation is reactive.

## The Svelte Mental Model

For local deep state, mutate the thing you mean to change.

```svelte
<script lang="ts">
  let todos = $state<Todo[]>([]);

  function toggle(id: string) {
    const todo = todos.find((item) => item.id === id);
    if (todo) todo.done = !todo.done;
  }
</script>
```

The code says what changed, and Svelte tracks it.

## Migration Strategy

1. Find spread/map/filter updates whose only purpose is triggering reactivity.
2. Replace with direct mutation when the state is local and deeply reactive.
3. Keep immutable replacement when crossing identity boundaries or preserving history.
4. Use `$state.raw` only for intentionally non-deep reactive large immutable structures.

## When Immutable Updates Are Fine

- persistent data structures or undo/redo history
- passing data to APIs that rely on identity changes
- large immutable collections where `$state.raw` is deliberate
- codebases with explicit immutability conventions
- derived transformations that naturally return new arrays

## Where This Habit Comes From

- **React** — identity replacement is required for state updates
- **Redux** — immutable reducers and structural sharing are core patterns
- **Vue** — refs/reactive objects can encourage framework-specific update ceremony

## Official References

- [Svelte docs: $state deep state](https://svelte.dev/docs/svelte/$state#Deep-state)
- [Svelte docs: $state.raw](https://svelte.dev/docs/svelte/$state#$state.raw)
