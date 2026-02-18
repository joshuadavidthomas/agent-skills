# SvelteKit Authentication Patterns

Framework-agnostic patterns for auth in SvelteKit. Works with Better Auth, Lucia, Auth.js, or custom solutions.

**For Better Auth specifics, see [references/better-auth.md](references/better-auth.md).**

## Core Principle

**Route protection happens in layout server files, NOT in hooks.**

Hooks populate `locals.session` and `locals.user`. Layouts check those values and redirect. This separation is intentional — hooks run for every request, layouts run for their route subtree.

## Route Group Pattern

Use SvelteKit route groups to organize protected vs public routes:

```
routes/
├── +layout.svelte              # Global styles, base HTML
├── (app)/                      # Protected routes
│   ├── +layout.server.ts       # Checks session, redirects if missing
│   ├── +layout.svelte          # Nav bar, user info, logout button
│   ├── +page.svelte            # Dashboard (at /)
│   ├── settings/               # /settings
│   └── api/                    # /api/* (protected)
└── (auth)/                     # Public routes  
    ├── +layout.svelte          # Minimal layout (centered form)
    ├── login/                  # /login
    └── register/               # /register
```

Route groups `(name)` don't affect URLs — they're purely organizational. Routes in `(app)/` are still accessed at `/`, `/settings`, etc.

## Protected Layout

```typescript
// routes/(app)/+layout.server.ts
import { redirect } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
  if (!locals.session) {
    throw redirect(303, '/login');
  }

  return {
    user: locals.user,
  };
};
```

### ⚠️ Common Mistake: Missing `throw`

```typescript
// ❌ WRONG - redirect is ignored
if (!locals.session) {
  redirect(303, '/login');
}

// ✅ CORRECT - redirect is thrown
if (!locals.session) {
  throw redirect(303, '/login');
}
```

In SvelteKit 2, `redirect()` returns an object. You must `throw` it.

## Auth Layout (Public Routes)

```typescript
// routes/(auth)/login/+page.server.ts
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
  // Already logged in? Go to dashboard
  if (locals.session) {
    throw redirect(303, '/');
  }
};
```

## API Route Protection

**Layouts do NOT protect API routes.** The `+layout.server.ts` load function only runs for page navigations, not `+server.ts` endpoints.

You must check session explicitly in every API route:

```typescript
// routes/(app)/api/data/+server.ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ locals }) => {
  // ⚠️ Required - layouts don't protect +server.ts
  if (!locals.session) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }

  // ... handle authenticated request
  return json({ data: 'secret' });
};
```

## Hooks Setup

Hooks populate locals. That's it — no protection logic here:

```typescript
// hooks.server.ts
import { building } from '$app/environment';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  // Skip during build
  if (building) {
    return resolve(event);
  }

  // ⚠️ IMPORTANT: Throw if dependencies unavailable
  // Do NOT silently continue - that bypasses auth entirely
  const db = event.platform?.env?.DB;
  if (!db) {
    throw new Error('Database binding not available');
  }

  // Get session from your auth library
  const session = await getSession(event);

  // Only set locals if session exists
  if (session) {
    event.locals.session = session.session;
    event.locals.user = session.user;
  }

  return resolve(event);
};
```

### ⚠️ Critical: Never Silently Skip Auth

```typescript
// ❌ DANGEROUS - silently bypasses auth if DB missing
if (!db) {
  return resolve(event);
}

// ✅ CORRECT - fails loudly, you'll know something's wrong
if (!db) {
  throw new Error('Database binding not available');
}
```

If you silently continue when dependencies are missing, unauthenticated users get through because `locals.session` is never set.

## TypeScript Setup

```typescript
// app.d.ts
declare global {
  namespace App {
    interface Locals {
      session: YourSessionType | null;
      user: YourUserType | null;
    }
  }
}

export {};
```

## Layout Hierarchy

```
routes/
├── +layout.svelte          ← All routes (global styles)
├── (app)/
│   ├── +layout.server.ts   ← Protected routes only (auth check)
│   └── +layout.svelte      ← Protected routes only (nav bar)
└── (auth)/
    └── +layout.svelte      ← Auth routes only (centered layout)
```

Each route group can have its own layout that only applies to routes within it. The root layout applies to everything.

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Routes not protected | `redirect()` without `throw` | Use `throw redirect(303, '/login')` |
| Routes not protected | Hooks silently skip when DB missing | Throw error if DB unavailable |
| API routes exposed | Relying on layout protection | Check `locals.session` in `+server.ts` |
| Redirect loops | Auth page not excluded | Put login in `(auth)/` group, not `(app)/` |
| Session undefined | Hooks not setting locals | Verify hooks.server.ts runs first |
| Layout not applying | Wrong directory structure | Verify `+layout.server.ts` is in `(app)/` |
| Auth works locally, not prod | Missing DB binding or secret | Check wrangler config and secrets |

## References

- [references/better-auth.md](references/better-auth.md) — Better Auth integration, svelteKitHandler, auth client
- [references/cloudflare.md](references/cloudflare.md) — D1, Drizzle, preview deployments, cross-subdomain cookies
