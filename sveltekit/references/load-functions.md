# Load Functions

Load functions are ownership declarations. They answer: who owns this data, can it run in the browser, and should it be available before the page renders?

## Decision Matrix

| Need | Default file | Why |
|---|---|---|
| Database access | `+page.server.ts` / `+layout.server.ts` | server-only resource |
| Secrets/private env | `+page.server.ts` / `+layout.server.ts` | never ship to browser |
| Session-derived data | `+layout.server.ts` or `+page.server.ts` | request-owned server state |
| Public fetch that can rerun on navigation | `+page.ts` | universal data |
| Browser-only data | component effect or guarded universal load | SSR has no browser APIs |
| Shared app shell data | `+layout.server.ts` | inherited by child routes |

## Server load is for trusted data

```ts
// src/routes/profile/+page.server.ts
import type { PageServerLoad } from './$types';
import { db } from '$lib/server/database';

export const load: PageServerLoad = async ({ locals }) => {
	if (!locals.user) {
		throw redirect(303, '/login');
	}

	const user = await db.users.find(locals.user.id);

	return {
		user: {
			id: user.id,
			name: user.name,
			email: user.email,
		},
	};
};
```

Use server load when the data depends on trust: DB access, secrets, private APIs, cookies, sessions, authorization.

## Universal load is for universal work

```ts
// src/routes/posts/+page.ts
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, depends }) => {
	depends('app:posts');
	const posts = await fetch('/api/posts').then((r) => r.json());
	return { posts };
};
```

Universal load runs during SSR and again in the browser during client navigation. It cannot import `$lib/server/*`, cannot assume secrets, and should use SvelteKit's provided `fetch`.

## Server data flows through universal load

```ts
// +page.server.ts
export const load = async () => {
	return { user: await getUser() };
};

// +page.ts
export const load = async ({ data, fetch }) => {
	const stats = await fetch('/api/stats').then((r) => r.json());
	return { ...data, stats };
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
	let { data } = $props();
</script>

<h1>{data.user.name}</h1>
```

## Page controls update route state from events

When page controls reflect URL/query state, derive display values from `data` and update the route from the event that changed the control. Do not watch local state with `$effect` just to call `goto`, `invalidate`, or a navigation helper.

Smell:

```svelte
<script lang="ts">
	let { data } = $props();
	let currentPage = $state(data.query.page);

	$effect(() => {
		updateQuery({ page: currentPage });
	});
</script>

<Select bind:value={currentPage} />
```

Better:

```svelte
<script lang="ts">
	let { data } = $props();
	let currentPage = $derived(data.query.page);
</script>

<Select
	value={currentPage}
	onValueChange={(page) => updateQuery({ page })}
/>
```

If the control is form-shaped, prefer a native form/action or GET form before inventing client-only synchronization.

## The React-shaped smell

Smell:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';

	let user = $state(null);

	onMount(async () => {
		user = await fetch('/api/me').then((r) => r.json());
	});
</script>
```

This treats SvelteKit like an SPA. The page renders without its server-owned data, then patches itself later.

Better:

```ts
// +layout.server.ts or +page.server.ts
export const load = async ({ locals }) => {
	return { user: locals.user };
};
```

Load before render when the route needs the data to exist.

## Agent Smells

- Fetching DB/session-owned data from `onMount`.
- Importing `$lib/server/*` from `+page.ts`.
- Using universal load because it feels more flexible, even though the data is private.
- Returning ORM entities or class instances from load; see [serialization.md](serialization.md).
- Reading `window`/`localStorage` during SSR; see [ssr-hydration.md](ssr-hydration.md).
- Encoding authorization failures as data instead of throwing `redirect()` or `error()`; see [errors-and-redirects.md](errors-and-redirects.md).

## Official References

- [SvelteKit docs: Loading data](https://svelte.dev/docs/kit/load)
