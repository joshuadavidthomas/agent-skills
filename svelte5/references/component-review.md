# Svelte Component Review Checklist

Use this when asked for a targeted review of Svelte code. Prioritize concrete issues with suggested rewrites.

## 1. Version and Syntax

Detect the project version before recommending syntax:

- Read `package.json` and check the installed `svelte` major version.
- Look for project conventions: `$props`, `.svelte.ts`, `runes`, `export let`, `on:click`, `<slot>`.
- Check `svelte.config.*` for compiler options or migration settings when present.

If the project uses Svelte 5, flag Svelte 4 patterns:

- `export let` instead of `$props()`
- `on:event` instead of event attributes such as `onclick`
- `<slot>` instead of snippets and `{@render ...}`
- `createEventDispatcher` instead of callback props

Do not recommend Svelte 5-only syntax for a Svelte 4 project unless the task is migration.

## 2. Reactivity Correctness

Look for:

- `$effect` used to compute state that should be `$derived`
- stale local copies of props
- destructuring that loses reactivity outside `$props()` patterns
- async race conditions in effects or event handlers
- missing cleanup for timers, subscriptions, observers, or event listeners
- module-level mutable state that can leak in SSR contexts

Prefer:

```svelte
<script lang="ts">
  let { items }: { items: Item[] } = $props();
  const visibleItems = $derived(items.filter((item) => !item.hidden));
</script>
```

Over:

```svelte
<script lang="ts">
  let visibleItems = $state([]);
  $effect(() => {
    visibleItems = items.filter((item) => !item.hidden);
  });
</script>
```

## 3. Component API

Check whether the API is explicit and typed:

- Define a `Props` type or interface for non-trivial components.
- Use optional props only when the component has a clear default or conditional behavior.
- Use callback props for events: `onchange?: (value: Value) => void`.
- Use `$bindable()` sparingly for two-way binding.
- Type snippets with `Snippet` from `svelte`.
- Avoid boolean prop combinations that create invalid states; prefer variants or discriminated unions.

## 4. Markup and Accessibility

Flag:

- clickable `div`/`span`
- buttons without `type`
- anchors used as buttons or buttons used as links
- unlabeled inputs
- missing `alt` text or meaningless image text
- hidden controls that cannot be reached by keyboard
- custom widgets without keyboard handling, focus management, or ARIA names
- suppressed a11y warnings without justification

Prefer native HTML elements. Add ARIA only when native semantics are insufficient.

## 5. State Placement

Ask where the state should live:

- Component-local state: `let value = $state(...)` in the component.
- Reusable state with behavior: class in `.svelte.ts` plus a factory.
- Descendant-shared state: context helpers with `setContext`/`getContext`.
- Cross-route or server-owned data in SvelteKit: use SvelteKit load/actions/remote functions instead of client globals.

Do not introduce global stores for state that has a single owner.

## Load Related References

When a review finding needs detail, load the matching reference before proposing a rewrite:

- Props/events/snippets: [component-patterns.md](component-patterns.md)
- Actions: [actions.md](actions.md)
- Bindings/classes/styles: [bindings-and-directives.md](bindings-and-directives.md)
- Stores: [stores.md](stores.md)
- TypeScript: [typescript.md](typescript.md)
- Tests: [testing.md](testing.md)
- Debugging reactivity: [debugging.md](debugging.md)

## 6. Maintainability

Look for:

- large components mixing data fetching, state machines, and markup
- repeated conditionals that should become a derived value or child component
- unclear prop names such as `data`, `item`, `flag`
- broad `any` types
- unkeyed `{#each}` blocks where identity matters
- overuse of `$effect` as lifecycle glue

Prefer extracting small components or `.svelte.ts` state only when it reduces duplication or clarifies ownership.

## 7. Performance

Most Svelte code does not need manual optimization. Review performance when there is evidence or obvious scale:

- Add keys to each blocks when list identity matters: `{#each items as item (item.id)}`.
- Avoid expensive work in markup; move it to `$derived`.
- Avoid recreating large derived arrays repeatedly across child components.
- Keep DOM size reasonable for large lists; consider virtualization only for genuinely large lists.
- Avoid unnecessary two-way bindings that cause wide update paths.

## Review Output Shape

For concise reviews, use:

1. **High impact issues** — correctness, reactivity, a11y, SSR leaks.
2. **Suggested rewrites** — show the smallest useful code change.
3. **Nice-to-haves** — naming, extraction, minor cleanup.

Avoid listing every stylistic preference. Tie recommendations to behavior, maintainability, or user impact.

## Official References

- [Svelte docs: Compiler warnings](https://svelte.dev/docs/svelte/compiler-warnings)
- [Svelte docs: Svelte 5 migration guide](https://svelte.dev/docs/svelte/v5-migration-guide)
