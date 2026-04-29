# sveltekit

Opinionated SvelteKit specialist skill for writing, reviewing, debugging, and refactoring app-level code.

This is not a replacement for the SvelteKit docs. It is a mental-model reset for the parts that make SvelteKit different from a client-side SPA: route files as boundaries, server-first data flow, form actions, auth policy, remote functions, redirects/errors, serialization, and SSR.

Use `svelte5` for component internals: runes, snippets, component props, DOM events, accessibility, transitions, and component state.

## Main skill

- `SKILL.md` — "Think in SvelteKit" principles, smells, quick reference, and reference router

## References

All supporting material lives under `references/`:

- `references/file-naming.md` — route files as runtime boundaries
- `references/layout-patterns.md` — route groups, layout nesting, shared layout data
- `references/load-functions.md` — server vs universal load ownership
- `references/form-actions.md` — form action mechanics and progressive enhancement
- `references/forms-validation.md` — `extractFormData`, `FormErrors`, cross-field validation
- `references/auth.md` — hooks, locals, route protection, endpoint protection
- `references/errors-and-redirects.md` — `fail()`, `redirect()`, `error()`, `+error.svelte`
- `references/serialization.md` — load/action serialization rules
- `references/ssr-hydration.md` — SSR, browser-only code, hydration mismatch thinking
- `references/remote-functions.md` — `command()`, `query()`, `form()` and their failure modes
- `references/better-auth.md` — Better Auth integration
- `references/cloudflare.md` — Cloudflare, D1, Drizzle, preview deployments, cookies

## Scope boundary

Use this skill for SvelteKit app-level work. Also use `svelte5` when the task is about component-level Svelte: runes, snippets, component API, accessibility, actions, transitions, stores, or component review.

## Attribution & license notes

This skill synthesizes guidance from:

- [svelte-claude-skills](https://github.com/spences10/svelte-claude-skills) by Scott Spence (MIT)
- [Svelte documentation](https://svelte.dev/docs) (MIT)
- [SvelteKit documentation](https://svelte.dev/docs/kit) (MIT)
- [Modern SvelteKit Tutorial](https://github.com/stolinski/Modern-Svelte-Kit-Tutorial) by Scott Tolinski
