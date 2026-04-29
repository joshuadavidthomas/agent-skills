# Layout Patterns

Layouts are route boundaries, not just wrapper components. Use them to express durable app structure: public vs app shell, auth policy, shared server data, and nested UI ownership.

## Prefer route groups over runtime conditionals

If sections need different shells, create different layout branches. Do not make one root layout branch on `page.url.pathname` like a client router.

```text
src/routes/
├── (marketing)/
│   ├── +layout.svelte
│   ├── about/+page.svelte      # /about
│   └── pricing/+page.svelte    # /pricing
└── (app)/
    ├── +layout.server.ts       # auth/data boundary
    ├── +layout.svelte          # app shell
    ├── dashboard/+page.svelte  # /dashboard
    └── settings/+page.svelte   # /settings
```

Groups are invisible in URLs. They exist to make structure and policy explicit.

## Layouts compose downward

```svelte
<!-- src/routes/+layout.svelte -->
<script lang="ts">
	let { children } = $props();
</script>

<nav>Global navigation</nav>
{@render children()}
```

```svelte
<!-- src/routes/(app)/+layout.svelte -->
<script lang="ts">
	let { children, data } = $props();
</script>

<aside>App navigation for {data.user.name}</aside>
<main>{@render children()}</main>
```

The root layout wraps the app layout, which wraps the page. Each level should own a real boundary. If a layout only exists because a component got large, it may just be a component.

## Layout server data flows to children

```ts
// src/routes/(app)/+layout.server.ts
import { redirect } from '@sveltejs/kit';

export const load = async ({ locals }) => {
	if (!locals.session) throw redirect(303, '/login');
	return { user: locals.user };
};
```

The returned `data.user` is available to `(app)/+layout.svelte` and child pages. This is a good place for shared page data and page auth policy.

It is not endpoint protection. `+server.ts` files must check auth themselves. See [auth.md](auth.md).

## Avoid pathname-driven shells

Smell:

```svelte
<script lang="ts">
	import { page } from '$app/state';
	let { children } = $props();
</script>

{#if !page.url.pathname.startsWith('/admin')}
	<header>Public header</header>
{/if}

{@render children()}
```

Better: put admin routes under an `(admin)` group with their own layout. Route structure should reveal the app shape instead of hiding it in conditionals.

## Agent Smells

- One giant root layout with pathname checks for every section.
- Login pages inside the protected `(app)` group.
- Assuming a protected layout protects `+server.ts` endpoints.
- Moving ordinary component state into layout data.
- Creating layouts that do not represent a route boundary.
- Using layout resets when route groups would express the structure more clearly.

## Official References

- [SvelteKit docs: Advanced routing](https://svelte.dev/docs/kit/advanced-routing)
- [SvelteKit docs: Routing](https://svelte.dev/docs/kit/routing)
