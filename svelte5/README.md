# svelte5

Opinionated Svelte 5 specialist skill for writing, reviewing, debugging, and refactoring components.

This is not a replacement for the Svelte docs. It is a mental-model reset in the style of `thinking-in-rust`: it teaches the agent to spot code that works but does not think in Svelte.

## Main skill

- `SKILL.md` — "Think in Svelte 5" manifesto, smells, quick reference, review checklist

## Thinking references

Focused references are organized around recurring smells and better defaults. Use these first; reach for supporting references only when implementing the recommendation needs concrete API detail.

- `references/effect-driven-state.md` — effects used to compute state
- `references/read-tracked-reactivity.md` — dependency tracking by reactive reads
- `references/static-runes.md` — runes as compiler syntax, not hooks/composables
- `references/deep-state-without-immutable-ceremony.md` — local `$state` mutation vs React-style updates
- `references/prop-mirroring.md` — props copied into local state
- `references/state-ownership.md` — component/class/context/store ownership
- `references/context-identity.md` — context as shared object identity
- `references/ssr-state-leaks.md` — module state leaks in SSR apps
- `references/bindable-by-default.md` — overused `$bindable`
- `references/snippets-as-render-functions.md` — snippets as typed render functions, not renamed slots
- `references/semantic-html-first.md` — native elements before custom behavior
- `references/actions-vs-components.md` — markup belongs to components; DOM behavior belongs to actions/attachments
- `references/wrapper-components-preserve-html.md` — wrapper components must preserve native element contracts
- `references/svelte5-syntax-discipline.md` — avoiding half-migrated Svelte 4/Svelte 5 syntax

## Supporting references

Feature-oriented references are flat under `references/` so paths are predictable. They provide concrete patterns after the thinking references establish direction.

- `references/runes-reactivity-patterns.md` — choosing runes, `$state.raw`, `$state.snapshot`, `$effect.pre`
- `references/runes-component-api.md` — `$props`, `$bindable`, generics
- `references/runes-common-mistakes.md` — rune anti-patterns and fixes
- `references/svelte4-to-5-migration.md` — Svelte 4 → 5 migration details
- `references/snippets-vs-slots.md` — slot-to-snippet migration details
- `references/class-state-patterns.md` — class-based state patterns
- `references/class-state-common-mistakes.md` — class-state anti-patterns and fixes
- `references/context-vs-scoped-state.md` — context vs component-scoped state
- `references/class-state-ssr-safety.md` — SSR safety for class-based state
- `references/component-review.md` — review checklist for Svelte components
- `references/component-patterns.md` — props, snippets, events, bindings, markup patterns
- `references/actions.md` — `use:` actions and DOM behavior
- `references/attachments.md` — Svelte 5 attachments
- `references/transitions-animations.md` — transitions, animations, keyed movement
- `references/stores.md` — when stores still fit in Svelte 5
- `references/special-elements.md` — `<svelte:*>` elements and boundaries
- `references/template-tags.md` — `{@html}`, `{@const}`, `{@debug}`, `{#await}`
- `references/bindings-and-directives.md` — `bind:`, `class:`, `style:`
- `references/typescript.md` — component and snippet typing
- `references/testing.md` — component tests, `mount`, `flushSync`
- `references/imperative-api.md` — imperative mounting/hydration/custom elements
- `references/debugging.md` — `$inspect`, `untrack`, dependency debugging

## Scope boundary

Use this skill for component-level Svelte work. Also use `sveltekit` when the task involves routes, layouts, load functions, form actions, remote functions, SSR data flow, cookies, redirects, endpoints, deployment, or authentication.

## Attribution & license notes

This skill synthesizes guidance from:

- [svelte-claude-skills](https://github.com/spences10/svelte-claude-skills) by Scott Spence (MIT)
- [Svelte documentation](https://svelte.dev/docs) (MIT)
- [Modern SvelteKit Tutorial](https://github.com/stolinski/Modern-Svelte-Kit-Tutorial) by Scott Tolinski
- [Svelte Stores Streams Effect](https://github.com/bmdavis419/Svelte-Stores-Streams-Effect) by Ben Davis ([video](https://www.youtube.com/watch?v=kMBDsyozllk))
