# Actions

Actions attach reusable imperative behavior to DOM elements with `use:`. Use them for DOM APIs that do not deserve a component: focus traps, observers, gestures, third-party widgets, and event behavior that must bind to a specific element.

## Pattern

```svelte
<script lang="ts">
  import type { Action } from 'svelte/action';

  const autofocus: Action<HTMLInputElement> = (node) => {
    node.focus();
  };
</script>

<input use:autofocus />
```

For parameters, react to changes and clean up resources.

```ts
import type { Action } from 'svelte/action';

type ClickOutsideParams = {
  enabled?: boolean;
  onoutside: () => void;
};

export const clickOutside: Action<HTMLElement, ClickOutsideParams> = (node, params) => {
  let current = params;

  const onPointerDown = (event: PointerEvent) => {
    if (current.enabled === false) return;
    if (!node.contains(event.target as Node)) current.onoutside();
  };

  document.addEventListener('pointerdown', onPointerDown);

  return {
    update(next) {
      current = next;
    },
    destroy() {
      document.removeEventListener('pointerdown', onPointerDown);
    }
  };
};
```

## Review Checklist

- Does the action return cleanup for listeners, observers, timers, or third-party instances?
- Are parameters updated when reactive inputs change?
- Is the action typed with the specific element type?
- Is this behavior truly DOM-level, or would a component be clearer?
- Does it run only in the browser? Actions are DOM-bound, so avoid server-only assumptions.
- Does it preserve accessibility? Gesture/click helpers must not remove keyboard access.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Adding `document` listeners without cleanup | Return `destroy()` |
| Capturing initial params forever | Implement `update(next)` or use an attachment/effect pattern |
| Using an action for markup/state composition | Use a component |
| Using `any` for node/params | Type with `Action<ElementType, Params>` |
| Reimplementing native behavior | Prefer semantic HTML first |

## Official References

- [Svelte docs: use: actions](https://svelte.dev/docs/svelte/use)
- [Svelte reference: svelte/action](https://svelte.dev/docs/svelte/svelte-action)
