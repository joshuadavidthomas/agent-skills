# Better Auth + SvelteKit

## Hooks Setup

```typescript
// hooks.server.ts
import { getAuthForEvent } from '$lib/server/auth';
import { svelteKitHandler } from 'better-auth/svelte-kit';
import { building } from '$app/environment';
import type { Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
  if (building) {
    return resolve(event);
  }

  const auth = getAuthForEvent(event);

  const session = await auth.api.getSession({
    headers: event.request.headers,
  });

  event.locals.session = session?.session ?? null;
  event.locals.user = session?.user ?? null;

  // Handles /api/auth/* routes automatically
  return svelteKitHandler({ event, resolve, auth, building });
};
```

**Key points:**
- `building` from `$app/environment` is required by `svelteKitHandler`
- `svelteKitHandler` handles all `/api/auth/*` routes
- No route protection here — that's in layouts

---

## Auth Config

```typescript
// lib/server/auth.ts
import { betterAuth } from 'better-auth';
import type { RequestEvent } from '@sveltejs/kit';

export function createAuth(db: YourDatabaseType, baseURL: string) {
  return betterAuth({
    baseURL,
    trustedOrigins: [baseURL],
    database: yourDatabaseAdapter(db),
    emailAndPassword: { enabled: true },
    session: {
      expiresIn: 60 * 60 * 24 * 7, // 7 days
      updateAge: 60 * 60 * 24,
      cookieCache: { enabled: true, maxAge: 60 * 5 },
    },
  });
}

export function getAuthForEvent(event: RequestEvent) {
  const db = getDatabase(event);
  return createAuth(db, event.url.origin);  // Dynamic origin
}

export type Auth = ReturnType<typeof createAuth>;
export type Session = Auth['$Infer']['Session'];
export type User = Session['user'];
```

---

## Auth Client

```typescript
// lib/auth-client.ts
import { createAuthClient } from 'better-auth/svelte';

export const authClient = createAuthClient({
  baseURL: typeof window !== 'undefined' ? window.location.origin : '',
});

export const { signIn, signOut, useSession } = authClient;
```

---

## Login Page

```svelte
<script lang="ts">
  import { signIn } from '$lib/auth-client';
  import { goto } from '$app/navigation';

  let email = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleSubmit() {
    error = '';
    loading = true;
    const result = await signIn.email({ email, password });
    loading = false;

    if (result.error) {
      error = result.error.message ?? 'Login failed';
    } else {
      goto('/');
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit}>
  {#if error}<div class="error">{error}</div>{/if}
  <input type="email" bind:value={email} required placeholder="Email" />
  <input type="password" bind:value={password} required placeholder="Password" />
  <button type="submit" disabled={loading}>
    {loading ? 'Logging in...' : 'Login'}
  </button>
</form>
```

---

## Logout

```svelte
<script lang="ts">
  import { signOut } from '$lib/auth-client';
  import { invalidateAll } from '$app/navigation';

  async function handleLogout() {
    await signOut();
    invalidateAll();
  }
</script>

<button onclick={handleLogout}>Logout</button>
```

---

## CLI User Creation

For apps without self-registration. Use Better Auth's exported `hashPassword`:

```typescript
import { hashPassword } from 'better-auth/crypto';

function generateId(): string {
  return crypto.randomUUID().replace(/-/g, '');
}

const hashedPassword = await hashPassword(password);

// Insert into database:
// user: id, name, email, email_verified=true, created_at, updated_at
// account: id, account_id=userId, provider_id='credential', user_id, password, created_at, updated_at
```

**Don't reimplement password hashing** — use the export to guarantee compatibility.

---

## Secrets

```
BETTER_AUTH_SECRET=your-secret-min-32-chars
```

Generate: `openssl rand -base64 32`

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `building` error | Missing import | Import from `$app/environment` |
| Auth routes 404 | Missing svelteKitHandler | Add to hooks.server.ts |
| Session not persisting | Mismatched baseURL | Use `event.url.origin` |
