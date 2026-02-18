# sveltekit

SvelteKit application patterns. Covers routing and layouts, data loading (load functions, form actions), authentication (route groups, layout protection, hooks), form validation (server-first with Standard Schema libraries), and remote functions (`command()`, `query()`, `form()`).

The `SKILL.md` teaches all five topics with code examples — enough to answer most questions directly. Topic files provide deep dives, and `references/` contains detailed patterns for each area.

## References in this skill

Deep dives live in topic files and `references/`:
- `structure.md` — Routing, layouts, error boundaries, SSR
- `data-flow.md` — Load functions, form actions, serialization
- `auth.md` — Authentication, hooks, route protection, API routes
- `forms-validation.md` — extractFormData utility, FormErrors class, cross-field validation
- `remote-functions.md` — command(), query(), form() in .remote.ts files
- `references/` — File naming, layout patterns, error handling, SSR/hydration, load functions, form actions, serialization, error/redirect handling, Better Auth, Cloudflare

## Attribution & license notes

This skill synthesizes guidance from:

- [svelte-claude-skills](https://github.com/spences10/svelte-claude-skills) by Scott Spence (MIT)
- [Svelte documentation](https://svelte.dev/docs) (MIT)
- [Modern SvelteKit Tutorial](https://github.com/stolinski/Modern-Svelte-Kit-Tutorial) by Scott Tolinski
