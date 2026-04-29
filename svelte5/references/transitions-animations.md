# Transitions and Animations

Use transitions for elements entering/leaving the DOM and animations for keyed list movement.

## Built-in Transitions

```svelte
<script lang="ts">
  import { fade, fly } from 'svelte/transition';

  let open = $state(false);
</script>

{#if open}
  <aside transition:fly={{ x: 16, duration: 150 }}>
    Panel
  </aside>
{/if}
```

- `transition:` applies on intro and outro.
- `in:` applies only on intro.
- `out:` applies only on outro.
- Transition params should be stable and simple.

## List Animation

Use `animate:` on keyed each blocks when items reorder.

```svelte
<script lang="ts">
  import { flip } from 'svelte/animate';
</script>

{#each items as item (item.id)}
  <div animate:flip>{item.label}</div>
{/each}
```

## Crossfade

Use `crossfade` when items move between two lists or locations. Keep keys stable and unique across both sides.

## Review Checklist

- Are each blocks keyed when using `animate:` or when identity matters?
- Are transitions used for mount/unmount rather than toggling CSS classes manually?
- Are animations short and respectful of user preferences?
- Is expensive JS work inside custom transitions avoided?
- Does the UI still work if transitions are disabled?
- Are transitions causing layout shift or focus loss?

## Common Mistakes

| Mistake | Fix |
|---|---|
| `animate:` on unkeyed each block | Add stable keys |
| Animating large lists by default | Measure first; consider virtualization or reduced motion |
| Using transitions to hide inaccessible state | Keep DOM/focus semantics correct |
| Custom JS transition doing layout work every frame | Prefer CSS/Web Animations where possible |

## Official References

- [Svelte docs: transition:](https://svelte.dev/docs/svelte/transition)
- [Svelte docs: animate:](https://svelte.dev/docs/svelte/animate)
