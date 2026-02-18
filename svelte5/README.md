# svelte5

Svelte 5 reactivity and state management. Covers runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`), class-based state (the idiomatic replacement for `writable`/`readable` stores), context API for sharing state across components, snippets vs slots, and Svelte 4→5 migration.

The `SKILL.md` teaches both runes and class-based state with code examples — enough to answer most questions directly. Topic files provide deep dives, and `references/` contains detailed patterns, migration guides, and common mistakes.

## References in this skill

Deep dives live in topic files and `references/`:
- `runes.md` — Rune patterns, migration, component API
- `class-state.md` — Class patterns, context vs scoped, SSR safety
- `references/runes/` — Reactivity patterns, migration gotchas, component API, snippets vs slots, common mistakes
- `references/class-state/` — Class patterns, context vs scoped, common mistakes, SSR safety

## Attribution & license notes

This skill synthesizes guidance from:

- [svelte-claude-skills](https://github.com/spences10/svelte-claude-skills) by Scott Spence (MIT)
- [Svelte documentation](https://svelte.dev/docs) (MIT)
- [Modern SvelteKit Tutorial](https://github.com/stolinski/Modern-Svelte-Kit-Tutorial) by Scott Tolinski
- [Svelte Stores Streams Effect](https://github.com/bmdavis419/Svelte-Stores-Streams-Effect) by Ben Davis ([video](https://www.youtube.com/watch?v=kMBDsyozllk))
