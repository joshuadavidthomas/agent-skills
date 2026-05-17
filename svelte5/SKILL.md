---
name: svelte5
description: >
  Reviews Svelte components for idiomatic patterns, identifies anti-patterns carried over
  from React/Vue/Svelte 4, and suggests Svelte 5 refactorings. Use when writing or reviewing
  Svelte components, asking "is this idiomatic", "Svelte way", doing Svelte 5 migration, or
  encountering smells like: effect assigns state, prop copied to $state, global store by
  default, $bindable everywhere, clickable div, createEventDispatcher, export let, on:click,
  slot-shaped APIs, lifecycle-driven code, imperative DOM wiring, immutable-update ceremony,
  context value replacement, shadcn-svelte form structure, Field.* components, bits-ui form
  controls, or component APIs that hide ownership. This is the general-purpose entry point
  for Svelte component review; delegates to sveltekit for routes/load/actions/server concerns
  and to focused references for details.
---

# Think in Svelte 5

You already know Svelte syntax. This skill changes your **defaults** — what you reach for first when designing a component, placing state, modeling reactivity, and reviewing UI code.

The core failure mode is Svelte that compiles but thinks like React, Vue, or Svelte 4 — effects standing in for derived values and events, props mirrored into state, global stores by reflex, two-way binding as the default, clickable `div`s, Svelte 4 component APIs in new code.

The component is a small reactive program with visible dependencies. Keep dataflow direct, state ownership obvious, and markup semantic; let the compiler and the DOM do the work.

This skill is the **general-purpose entry point** for Svelte component review; for SvelteKit-level concerns, also use **sveltekit** (see [Cross-References](#cross-references)).

Treat these as strong defaults, not rigid laws: when unsure, choose the approach that makes ownership, dependencies, and user semantics more explicit.

## How Svelte Thinks

### Make reactivity visible

**1. Reactivity is read-tracked.** A `$derived`/`$effect` depends on what it reads while running; if one reruns unexpectedly, inspect its reads, not a dependency array. See [references/read-tracked-reactivity.md](references/read-tracked-reactivity.md).

**2. Derived state is `$derived`, not `$effect`.** Pure functions of other state get derived; effects are for side effects, not keeping variables in sync. See [references/effect-driven-state.md](references/effect-driven-state.md).

```svelte
<!-- ❌ effect writing derived state -->
let doubled = $state(0);
$effect(() => { doubled = count * 2; });

<!-- ✅ derive it -->
let doubled = $derived(count * 2);
```

**3. Effects are escape hatches.** Before `$effect`, check for a derived value, an event handler, or a `bind:` getter/setter. Use it only to touch the outside world — subscriptions, timers, observers, imperative APIs, logging — and return cleanup.

**4. Runes are statically analyzable.** Compiler syntax, not runtime hooks — reusable state becomes `.svelte.ts` classes and factories, not custom hooks. See [references/static-runes.md](references/static-runes.md).

**5. `$state` is a deep proxy, not React state.** Mutate what changed in local arrays and objects; skip the immutable-update ceremony. See [references/deep-state-without-immutable-ceremony.md](references/deep-state-without-immutable-ceremony.md).

### Put state where ownership is clearest

**6. State has an owner.** Local interaction state → component; reusable behavior → `.svelte.ts` class; descendant-shared → context; stores only for the store contract, not every changing value. See [references/state-ownership.md](references/state-ownership.md).

**7. Do not mirror props unless you mean "draft."** Copying props into `$state` creates two sources of truth — derive from props, or make a named editable draft with reset/commit. See [references/prop-mirroring.md](references/prop-mirroring.md).

```svelte
<!-- ❌ prop mirrored into local state -->
let { value } = $props();
let local = $state(value); // stale if parent changes

<!-- ✅ derive from prop -->
let { value } = $props();
let display = $derived(value.toUpperCase());
```

**8. Context shares identity, not provider rerenders.** Put a reactive object/class in context and mutate its properties; replacing plain values won't behave like React Provider updates. See [references/context-identity.md](references/context-identity.md).

**9. Module-level mutable state is suspicious in SSR apps.** In SvelteKit, exported mutable instances leak between requests — use factories, context, or request-owned data. See [references/ssr-state-leaks.md](references/ssr-state-leaks.md).

### Design component APIs around ownership

**10. Props describe inputs; callbacks describe events.** Component events are callback props; avoid `createEventDispatcher` in new code unless preserving an old public API. See [references/component-patterns.md](references/component-patterns.md).

```svelte
<!-- ❌ createEventDispatcher in Svelte 5 -->
const dispatch = createEventDispatcher();
function handleClick() { dispatch('select', item); }

<!-- ✅ callback prop -->
let { onSelect } = $props();
function handleClick() { onSelect?.(item); }
```

**11. Two-way binding is an API commitment.** `$bindable` means the child may mutate parent-owned state — use it for form controls and deliberate controlled components, not as a default. See [references/bindable-by-default.md](references/bindable-by-default.md).

**12. Snippets are render functions, not renamed slots.** Use them when the parent supplies UI; type their parameters and name them by role. See [references/snippets-as-render-functions.md](references/snippets-as-render-functions.md).

**13. Wrapper components should preserve the platform.** Wrapping a `button` means accepting button attributes and keeping `type`, `disabled`, focus, and ARIA intact. See [references/wrapper-components-preserve-html.md](references/wrapper-components-preserve-html.md).

### Let HTML and the compiler work

**14. Native elements before custom behavior.** A `button` already handles keyboard, focus, disabled, and a11y; a clickable `div` rebuilds the platform badly. See [references/semantic-html-first.md](references/semantic-html-first.md).

**15. Design-system fields should preserve form semantics.** In shadcn-svelte or bits-ui forms, use `Field.*` for labels, groups, descriptions, and errors — not raw `div`s, separate `Label` imports, or clickable option rows. See [references/shadcn-svelte-forms.md](references/shadcn-svelte-forms.md).

**16. Components own markup; actions/attachments own DOM behavior.** Renders UI → component. Attaches reusable imperative behavior to an element → action or attachment. See [references/actions-vs-components.md](references/actions-vs-components.md).

**17. Svelte 5 syntax should be consistent.** New code uses `$props`, `onclick`-style attributes, snippets, and callback props; don't mix old syntax outside legacy maintenance. See [references/svelte5-syntax-discipline.md](references/svelte5-syntax-discipline.md).

**18. Type the boundary, not every breath.** Non-trivial components get a `Props` type; type snippets and callbacks; use `svelte/elements` for wrappers; avoid broad `any` at boundaries. See [references/typescript.md](references/typescript.md).

## Running a Review

1. **Detect the version first.** Read `package.json` for the `svelte` major and check `svelte.config.*`. In a Svelte 5 project, flag Svelte 4 patterns (`export let`, `on:event`, `<slot>`, `createEventDispatcher`); in a Svelte 4 project, do not recommend Svelte 5-only syntax unless the task is migration.
2. **Apply the principles above; scan the smell index below.** Open the linked reference before proposing a rewrite.
3. **Judge performance only on evidence or obvious scale.** Key identified `{#each}`, move heavy work out of markup into `$derived`, avoid needless two-way bindings. Most code needs no manual optimization.
4. **Shape the output:** high-impact first (correctness, reactivity, a11y, SSR leaks), then suggested rewrites (smallest useful change), then nice-to-haves. Tie every point to behavior, maintainability, or user impact — not every stylistic nit.

## Code Smell Index

Scan for the smell; the principle above carries the fix.

| Code smell | Reference |
|---|---|
| Old Svelte syntax in new code | [svelte5-syntax-discipline](references/svelte5-syntax-discipline.md) |
| Effect assigns a derived value | [effect-driven-state](references/effect-driven-state.md) |
| Effect responds to a control changing | [effect-driven-state](references/effect-driven-state.md) |
| Effect converts a bound value | [bindings-and-directives](references/bindings-and-directives.md) |
| Effect reruns mysteriously | [read-tracked-reactivity](references/read-tracked-reactivity.md) |
| Rune called inside a helper or hook | [static-runes](references/static-runes.md) |
| Immutable-update ceremony on local state | [deep-state-without-immutable-ceremony](references/deep-state-without-immutable-ceremony.md) |
| Prop copied into local state | [prop-mirroring](references/prop-mirroring.md) |
| Global store by default / owner unclear | [state-ownership](references/state-ownership.md) |
| Context value replaced instead of mutated | [context-identity](references/context-identity.md) |
| Exported mutable singleton in SvelteKit | [ssr-state-leaks](references/ssr-state-leaks.md) |
| `createEventDispatcher` to emit an event | [component-patterns](references/component-patterns.md) |
| `$bindable` by habit | [bindable-by-default](references/bindable-by-default.md) |
| Slot-shaped API (`export let`, `<slot>`) | [snippets-as-render-functions](references/snippets-as-render-functions.md) |
| Clickable `div` / `span` | [semantic-html-first](references/semantic-html-first.md) |
| shadcn-svelte form rebuilt with raw wrappers | [shadcn-svelte-forms](references/shadcn-svelte-forms.md) |
| Wrapper that hides native behavior | [wrapper-components-preserve-html](references/wrapper-components-preserve-html.md) |
| Action that owns markup/state | [actions-vs-components](references/actions-vs-components.md) |
| Dynamic list left unkeyed | [bindings-and-directives](references/bindings-and-directives.md) |
| Broad `any` at the component boundary | [typescript](references/typescript.md) |
| `{@html}` with user content | [template-tags](references/template-tags.md) |
| Component behavior left untested | [testing](references/testing.md) |

## Cross-References

- **sveltekit** — Routes, layouts, `load`, form actions, remote functions, cookies, auth, endpoints, redirects, server errors, app-level SSR/data flow
