# SvelteKit Structure

## Quick Start

**File types:** `+page.svelte` (page) | `+layout.svelte` (wrapper) |
`+error.svelte` (error boundary) | `+server.ts` (API endpoint)

**Routes:** `src/routes/about/+page.svelte` → `/about` |
`src/routes/posts/[id]/+page.svelte` → `/posts/123`

**Layouts:** Apply to all child routes. `+layout.svelte` at any level
wraps descendants.

## Example

```
src/routes/
├── +layout.svelte              # Root layout (all pages)
├── +page.svelte                # Homepage /
├── about/+page.svelte          # /about
└── dashboard/
    ├── +layout.svelte          # Dashboard layout (dashboard pages only)
    ├── +page.svelte            # /dashboard
    └── settings/+page.svelte   # /dashboard/settings
```

```svelte
<!-- +layout.svelte -->
<script>
	let { children } = $props();
</script>

<nav><!-- Navigation --></nav>
<main>{@render children()}</main>
<footer><!-- Footer --></footer>
```

## Reference Files

- [references/file-naming.md](references/file-naming.md) — File naming conventions
- [references/layout-patterns.md](references/layout-patterns.md) — Nested layouts
- [references/error-handling.md](references/error-handling.md) — Error boundary placement
- [references/ssr-hydration.md](references/ssr-hydration.md) — SSR and browser-only code

## Notes

- Layouts must render `{@render children()}` in Svelte 5
- Error boundaries (+error.svelte) must be _above_ failing route
- Use `(groups)` for layout organization without affecting URL
- Check `browser` from `$app/environment` for client-only code
