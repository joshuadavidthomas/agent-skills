---
name: sveltekit
description: "SvelteKit guidance — routing, layouts, data loading, form actions, authentication, form validation, remote functions, error handling, and SSR. Use for +page.svelte, +layout.svelte, +server.ts, +page.server.ts, load functions, fail(), redirect(), error(), route groups, protecting routes, sessions, Standard Schema validation (valibot/zod), extractFormData, FormErrors, command(), query(), form() in .remote.ts files. Triggers on: SvelteKit, +page, +layout, +server, +error, load function, form action, hooks.server.ts, route group, progressive enhancement."
---

# SvelteKit

## Topics

| Topic | File |
|-------|------|
| Routing, layouts, error boundaries, SSR | [structure.md](structure.md) |
| Load functions, form actions, serialization | [data-flow.md](data-flow.md) |
| Authentication, hooks, route protection | [auth.md](auth.md) |
| Form validation, extractFormData, FormErrors | [forms-validation.md](forms-validation.md) |
| Remote functions (command/query/form) | [remote-functions.md](remote-functions.md) |

## Structure & Routing

**File types:** `+page.svelte` (page) | `+layout.svelte` (wrapper) | `+error.svelte` (error boundary) | `+server.ts` (API endpoint)

**Routes:** `src/routes/about/+page.svelte` → `/about` | `src/routes/posts/[id]/+page.svelte` → `/posts/123`

Layouts apply to all child routes. Use `(groups)` for layout organization without affecting URLs.

```
src/routes/
├── +layout.svelte              # Root layout (all pages)
├── +page.svelte                # Homepage /
├── (app)/                      # Protected routes (group doesn't affect URL)
│   ├── +layout.server.ts       # Auth check for all (app) routes
│   ├── +layout.svelte          # Nav bar, user info
│   └── dashboard/+page.svelte  # /dashboard
└── (auth)/                     # Public routes
    └── login/+page.svelte      # /login
```

```svelte
<!-- +layout.svelte — must render children in Svelte 5 -->
<script>
  let { children } = $props();
</script>
<nav><!-- Navigation --></nav>
<main>{@render children()}</main>
```

→ Deep dives: [structure.md](structure.md) for file naming, layout nesting, error boundaries, SSR/hydration.

## Data Loading

**Which file?** Server-only (DB, secrets) → `+page.server.ts` | Universal (both sides) → `+page.ts` | API → `+server.ts`

```typescript
// +page.server.ts
import { fail, redirect } from '@sveltejs/kit';

export const load = async ({ locals }) => {
  const user = await db.users.get(locals.userId);
  return { user };  // Must be JSON-serializable
};

export const actions = {
  default: async ({ request }) => {
    const data = await request.formData();
    const email = data.get('email');
    if (!email) return fail(400, { email, missing: true });
    await updateEmail(email);
    throw redirect(303, '/success');
  },
};
```

Key rules:
- **Always `throw redirect()` and `throw error()`** — in SvelteKit 2 these return objects, they don't throw automatically
- Server load output is automatically passed to universal load as `data` parameter
- Don't return class instances or functions from server load (not serializable)
- Form actions always go in `+page.server.ts`

→ Deep dives: [data-flow.md](data-flow.md) for load functions, form actions, serialization rules.

## Authentication

**Route protection happens in layout server files, NOT in hooks.**

Hooks populate `locals.session`/`locals.user`. Layouts check and redirect.

```typescript
// routes/(app)/+layout.server.ts
import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
  if (!locals.session) {
    throw redirect(303, '/login');  // ⚠️ Must throw, not bare call
  }
  return { user: locals.user };
};
```

**⚠️ Layouts do NOT protect API routes.** You must check `locals.session` explicitly in every `+server.ts`:

```typescript
// routes/(app)/api/data/+server.ts
export const GET: RequestHandler = async ({ locals }) => {
  if (!locals.session) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  // ...
};
```

**⚠️ Never silently skip auth in hooks** — if your DB binding is missing, `throw new Error()`, don't `return resolve(event)`. Silent fallthrough means unauthenticated users get through.

→ Deep dives: [auth.md](auth.md) for full hooks setup, TypeScript config, Better Auth and Cloudflare specifics.

## Form Validation

Server-first validation with progressive enhancement. Schema defined once, server validates, client displays errors.

```typescript
// $lib/schemas/profile.ts
import * as v from 'valibot';

export const ProfileSchema = v.object({
  name: v.pipe(v.string(), v.trim(), v.minLength(1, 'Name is required.')),
  email: v.pipe(v.string(), v.trim(), v.toLowerCase(), v.email('Invalid email.')),
});
```

Pattern: `extractFormData()` utility validates request → returns typed data or field-keyed errors → `fail(400, { errors })` → client `FormErrors` class clears errors on input, shows after submit.

→ Deep dives: [forms-validation.md](forms-validation.md) for the full extractFormData utility, FormErrors class, cross-field validation, Field.Set, blur validation, and Zod equivalents.

## Remote Functions

`*.remote.ts` files expose server functions callable from the browser:

```typescript
// actions.remote.ts
import { command } from '$app/server';
import * as v from 'valibot';

export const delete_user = command(
  v.object({ id: v.string() }),
  async ({ id }) => {
    await db.users.delete(id);
    return { success: true };
  },
);
// Client: await delete_user({ id: '123' });
```

**Which function?** One-time action → `command()` | Repeated reads → `query()` | Forms → `form()`

Args and returns must be JSON-serializable. Use `getRequestEvent()` for cookies/headers.

→ Deep dives: [remote-functions.md](remote-functions.md) for complete patterns.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| `redirect()` without `throw` | `throw redirect(303, '/path')` |
| Protecting API routes via layouts | Check `locals.session` in each `+server.ts` |
| Silently skipping auth when DB missing | `throw new Error()` in hooks |
| Auth page inside protected group | Put login in `(auth)/`, not `(app)/` |
| Returning non-serializable from load | Only return plain objects, no classes/functions |
| `<slot />` in layouts | `{@render children()}` (Svelte 5) |

## Reference Index

**Structure:** [File Naming](references/file-naming.md) · [Layout Patterns](references/layout-patterns.md) · [Error Handling](references/error-handling.md) · [SSR & Hydration](references/ssr-hydration.md)

**Data Flow:** [Load Functions](references/load-functions.md) · [Form Actions](references/form-actions.md) · [Serialization](references/serialization.md) · [Error & Redirect Handling](references/error-redirect-handling.md)

**Auth:** [Better Auth](references/better-auth.md) · [Cloudflare](references/cloudflare.md)

**Remote Functions:** [Reference](references/remote-functions-reference.md)
