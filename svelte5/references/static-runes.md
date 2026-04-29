# Runes Are Statically Analyzable

## The Smell

Trying to call runes like ordinary helper functions or React hooks.

```ts
function createCounter() {
  let count = $state(0); // wrong place for rune-shaped state
  return { count };
}
```

## Why It Happens

React hooks look like functions and are commonly wrapped in custom hooks. Vue composables also return reactive refs from ordinary functions. Svelte runes are compiler syntax, not runtime APIs.

## The Svelte Mental Model

Runes must appear where the Svelte compiler can analyze them: component top level or class fields / module top level in `.svelte.ts` and `.svelte.js` files. This shapes reusable state design.

Use a class field:

```ts
// CounterState.svelte.ts
class CounterState {
  count = $state(0);
  increment = () => { this.count++; };
}

export const createCounterState = () => new CounterState();
```

## Migration Strategy

1. Find rune calls inside ordinary functions, conditionals, loops, or callbacks.
2. Move component-local state to component top level.
3. Move reusable state to class fields in `.svelte.ts`.
4. Export factories, not mutable singletons.
5. Keep ordinary helper functions pure and pass reactive values into them.

## When Function Factories Are Fine

Factories are fine when they construct classes or plain objects whose rune fields are declared in statically analyzable positions. The factory should not itself call runes in an unanalyzable way.

## Where This Habit Comes From

- **React** — custom hooks encourage reusable reactive logic as functions
- **Vue** — composables return refs/reactive objects from functions
- **Svelte 4** — stores could be created freely in ordinary functions

## Official References

- [Svelte docs: What are runes?](https://svelte.dev/docs/svelte/what-are-runes)
- [Svelte docs: .svelte.js and .svelte.ts files](https://svelte.dev/docs/svelte/svelte-js-files)
