# Context Identity

## The Smell

Putting plain values into context and expecting reassignment to update consumers.

```ts
setContext('count', { count });
```

Or replacing the context object later instead of mutating reactive properties on a stable object.

## Why It Happens

React context trains people to think in providers that re-render with new values. Svelte context is simpler: descendants retrieve a value by key. Reactivity comes from the value you put in context, not from repeatedly providing a new object.

## The Svelte Mental Model

Context shares object identity down the component tree. Put a reactive object/class in context and mutate its properties.

```ts
// CounterState.svelte.ts
import { getContext, setContext } from 'svelte';

class CounterState {
  count = $state(0);
  increment = () => { this.count++; };
}

const KEY = Symbol('counter');
export const setCounterState = () => setContext(KEY, new CounterState());
export const getCounterState = () => getContext<CounterState>(KEY);
```

Consumers all hold the same reactive object.

## Migration Strategy

1. Find context values that are plain snapshots.
2. Replace them with a reactive object or class instance.
3. Keep the context identity stable.
4. Mutate fields on the object rather than replacing the object.
5. Use a `Symbol` or typed context helper to avoid key collisions.

## When Plain Context Values Are Fine

- static config
- dependency injection for services
- theme names or constants that do not change
- functions/callbacks that are stable for the component tree lifetime

## Where This Habit Comes From

- **React** — Provider values are often replaced to trigger consumers
- **Svelte 4** — stores in context were common because stores carried reactivity
- **Vue** — provide/inject patterns can mix snapshots and reactive refs

## Official References

- [Svelte docs: Context](https://svelte.dev/docs/svelte/context)
