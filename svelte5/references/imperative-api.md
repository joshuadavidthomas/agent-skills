# Imperative Component API

Most Svelte code should use declarative components. Use the imperative API when embedding Svelte in non-Svelte hosts, tests, custom element integration, or controlled hydration/mounting.

## Core API

```ts
import { mount, unmount } from 'svelte';
import Widget from './Widget.svelte';

const component = mount(Widget, {
  target: document.getElementById('widget')!,
  props: { value: 1 }
});

unmount(component);
```

Use `hydrate` when attaching to server-rendered HTML in custom setups. Use SvelteKit's normal hydration path for SvelteKit apps.

## Tests

In tests, pair `mount` with `flushSync` when needed. See [testing.md](testing.md).

## Custom Elements and `$host`

Use `$host()` inside custom element components when the component needs access to its host element. Confirm the project intentionally compiles the component as a custom element before recommending this pattern.

## Review Checklist

- Is imperative mounting necessary, or would declarative composition be simpler?
- Is every mounted component eventually unmounted?
- Are props typed and updated through the supported API?
- Is `hydrate` only used for matching server-rendered markup?
- Is custom element configuration deliberate, documented, and tested?
- Does host integration preserve accessibility and cleanup external resources?

## Common Mistakes

| Mistake | Fix |
|---|---|
| Imperatively mounting inside a normal Svelte component | Prefer declarative child components |
| Forgetting `unmount` | Keep handle and clean up |
| Hydrating markup that does not match | Ensure server/client markup align |
| Using old class component APIs (`$set`, `$on`, `$destroy`) in Svelte 5 | Use current mount/unmount/callback-prop patterns |

## Official References

- [Svelte docs: Imperative component API](https://svelte.dev/docs/svelte/imperative-component-api)
- [Svelte docs: $host](https://svelte.dev/docs/svelte/$host)
