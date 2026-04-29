# Remote Functions

Remote functions (`command()`, `query()`, `form()`) let client code call server code through SvelteKit-managed boundaries. They are version/feature-flag dependent; confirm the project supports and enables them before recommending this pattern.

They are not a shortcut around SvelteKit's data model. Treat every remote function as a server boundary: validate input, check auth, and return serializable data.

## Choose by intent

| Intent | Primitive | Default alternative |
|---|---|---|
| Repeated server read from client | `query()` | `load` if the route needs data before render |
| Imperative mutation | `command()` | form action if it is form-shaped |
| Progressive form submission | `form()` | `+page.server.ts` action |

If the data belongs to the route's initial render, prefer `load`. If the user is submitting a normal form, prefer a form action unless remote `form()` clearly improves the design.

## `command()` for imperative mutations

```ts
// users.remote.ts
import { command, getRequestEvent } from '$app/server';
import * as v from 'valibot';

export const deleteUser = command(
	v.object({ id: v.string() }),
	async ({ id }) => {
		const { locals } = getRequestEvent();
		if (!locals.user?.isAdmin) throw new Error('Forbidden');

		await db.users.delete(id);
		return { success: true };
	},
);
```

Do not rely on the client hiding a button. The server function is callable and must enforce policy.

## `query()` for client-triggered reads

```ts
import { query } from '$app/server';
import * as v from 'valibot';

export const searchUsers = query(
	v.object({ q: v.string() }),
	async ({ q }) => {
		const { locals } = getRequestEvent();
		if (!locals.user) throw new Error('Unauthorized');
		return db.users.search(q);
	},
);
```

Do not use `query()` just because React Query would. In SvelteKit, route data often belongs in `load`, where SSR, redirects, errors, and invalidation fit naturally.

## `form()` for remote form workflows

Use `form()` when you want remote-function ergonomics for progressive forms. Keep the same server-first validation mindset as normal form actions.

```ts
import { form } from '$app/server';
import * as v from 'valibot';

export const login = form(
	v.object({
		email: v.pipe(v.string(), v.email()),
		password: v.string(),
	}),
	async ({ email, password }) => {
		const user = await authenticate(email, password);
		if (!user) return { errors: { email: 'Invalid credentials' } };
		return { success: true };
	},
);
```

## Serialization differs from load/action data

Remote functions use SvelteKit's remote transport and can serialize some richer values, such as `Date`, `Map`, `Set`, `RegExp`, and typed arrays. Load/action return data has a stricter route-data shape. Do not copy serialization assumptions between these boundaries without checking. See [serialization.md](serialization.md).

Still avoid functions, symbols, ambient handles, and class instances unless the transport explicitly supports the shape you return.

## Agent Smells

- Recommending remote functions without checking the project's SvelteKit version/feature flag.
- Using `command()` to avoid a normal form action.
- Using `query()` for route data that should load before render.
- Skipping auth because the function is “internal.”
- Using unchecked input because TypeScript types feel sufficient.
- Returning rich server objects instead of explicit response data.
- Recreating client-side RPC habits instead of using SvelteKit route boundaries.

## Official References

- [SvelteKit docs: Remote functions](https://svelte.dev/docs/kit/remote-functions)
- [SvelteKit docs: $app/server](https://svelte.dev/docs/kit/$app-server)
