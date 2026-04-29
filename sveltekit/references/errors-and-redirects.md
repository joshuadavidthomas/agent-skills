# Errors, Redirects, and Error Boundaries

SvelteKit treats failures as route control flow. Do not model everything as returned data or client-side navigation.

## The Three Primitives

| Primitive | Use when | Return or throw? | Mental model |
|---|---|---|---|
| `fail()` | Form validation failed | **return** | Stay on the same page with form data/errors |
| `redirect()` | Request should navigate elsewhere | **throw** | Stop this request and send a redirect response |
| `error()` | Route cannot produce valid content | **throw** | Stop this route and render nearest error boundary |

## `fail()` is for recoverable form errors

```ts
// +page.server.ts
import { fail, redirect } from '@sveltejs/kit';

export const actions = {
	default: async ({ request }) => {
		const data = await request.formData();
		const email = data.get('email');

		if (typeof email !== 'string' || !email.includes('@')) {
			return fail(400, {
				values: { email },
				errors: { email: 'Enter a valid email.' },
			});
		}

		await saveEmail(email);
		throw redirect(303, '/success');
	},
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
	let { form } = $props();
</script>

<form method="POST">
	<input name="email" value={form?.values?.email ?? ''} />
	{#if form?.errors?.email}<p>{form.errors.email}</p>{/if}
	<button>Submit</button>
</form>
```

`fail()` is not an exception. Return it from an action so SvelteKit can preserve the current page, expose `form`, and keep progressive enhancement intact.

## `redirect()` is thrown

Use `303` after successful form submissions so the browser follows with a GET.

```ts
import { redirect } from '@sveltejs/kit';

export const load = async ({ locals }) => {
	if (!locals.session) {
		throw redirect(303, '/login');
	}
};
```

Bare `redirect(303, '/login')` is a bug. In SvelteKit 2, `redirect()` returns a redirect object; it does not throw automatically.

## `error()` is thrown

Use `error()` when the route cannot produce content: not found, not authorized, invalid route state, unavailable dependency.

```ts
import { error } from '@sveltejs/kit';

export const load = async ({ params, locals }) => {
	const post = await getPost(params.slug);

	if (!post) throw error(404, 'Post not found');
	if (post.ownerId !== locals.user?.id) throw error(403, 'Forbidden');

	return { post };
};
```

Do not encode fatal route failures as `{ error: ... }` data and make every component branch around them. Let SvelteKit render the error boundary.

## Error Boundary Placement

`+error.svelte` catches errors from routes below it. It must be above the failing layout/page in the route hierarchy.

```text
src/routes/
├── +error.svelte              # catches everything below root
└── dashboard/
    ├── +layout.server.ts      # errors here bubble to root +error.svelte
    ├── +error.svelte          # catches dashboard pages below it
    └── settings/+page.svelte
```

A `+error.svelte` inside `dashboard/` cannot catch an error thrown by `dashboard/+layout.server.ts`, because that boundary is below the failing layout.

```svelte
<!-- +error.svelte -->
<script lang="ts">
	import { page } from '$app/state';
</script>

<h1>{page.status}</h1>
<p>{page.error?.message}</p>
```

## Expected vs Unexpected Errors

Use `error()` for expected route failures you want users to see: 401, 403, 404, domain-specific 400s.

Let unexpected errors throw naturally. Centralize logging/redaction in `handleError`, not in every route.

```ts
// hooks.server.ts
import type { HandleServerError } from '@sveltejs/kit';

export const handleError: HandleServerError = ({ error, event }) => {
	console.error('Unexpected error', { error, path: event.url.pathname });
	return { message: 'Something went wrong.' };
};
```

## Agent Smells

- Returning `redirect(...)` or `error(...)` instead of throwing.
- Throwing `fail(...)` instead of returning it.
- Returning `{ error: 'Not found' }` from `load` and branching in the page.
- Catching all errors and accidentally swallowing redirects.
- Placing `+error.svelte` below the layout that throws.
- Treating status codes as UI state instead of HTTP/route state.

## Official References

- [SvelteKit docs: Errors](https://svelte.dev/docs/kit/errors)
- [SvelteKit docs: Redirects](https://svelte.dev/docs/kit/load#Redirects)
- [SvelteKit docs: Routing +error](https://svelte.dev/docs/kit/routing#error)
