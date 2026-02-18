# SvelteKit Auth on Cloudflare Workers

## Platform Bindings

```typescript
// hooks.server.ts
export const handle: Handle = async ({ event, resolve }) => {
  const db = event.platform?.env?.DB;
  
  if (!db) {
    return resolve(event);
  }
  // ...
};
```

---

## D1 + Drizzle

### Connection

```typescript
// lib/server/db.ts
import { drizzle } from 'drizzle-orm/d1';
import * as schema from './schema';

export function createDb(d1: D1Database) {
  return drizzle(d1, { schema });
}
```

### Auth Schema

```typescript
// lib/server/schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const user = sqliteTable('user', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  emailVerified: integer('email_verified', { mode: 'boolean' }).notNull().default(false),
  image: text('image'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const session = sqliteTable('session', {
  id: text('id').primaryKey(),
  expiresAt: integer('expires_at', { mode: 'timestamp' }).notNull(),
  token: text('token').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
  ipAddress: text('ip_address'),
  userAgent: text('user_agent'),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
});

export const account = sqliteTable('account', {
  id: text('id').primaryKey(),
  accountId: text('account_id').notNull(),
  providerId: text('provider_id').notNull(),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  accessToken: text('access_token'),
  refreshToken: text('refresh_token'),
  idToken: text('id_token'),
  accessTokenExpiresAt: integer('access_token_expires_at', { mode: 'timestamp' }),
  refreshTokenExpiresAt: integer('refresh_token_expires_at', { mode: 'timestamp' }),
  scope: text('scope'),
  password: text('password'),
  createdAt: integer('created_at', { mode: 'timestamp' }).notNull(),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).notNull(),
});

export const verification = sqliteTable('verification', {
  id: text('id').primaryKey(),
  identifier: text('identifier').notNull(),
  value: text('value').notNull(),
  expiresAt: integer('expires_at', { mode: 'timestamp' }).notNull(),
  createdAt: integer('created_at', { mode: 'timestamp' }),
  updatedAt: integer('updated_at', { mode: 'timestamp' }),
});
```

### Drizzle Adapter (Better Auth)

```typescript
import { drizzleAdapter } from 'better-auth/adapters/drizzle';

database: drizzleAdapter(createDb(d1), {
  provider: 'sqlite',
  schema: { user, session, account, verification },
}),
```

---

## Wrangler Config

```jsonc
{
  "d1_databases": [
    {
      "binding": "DB",
      "database_name": "my-app-db",
      "database_id": "YOUR_DATABASE_ID",
      "migrations_dir": "migrations"
    }
  ]
}
```

```bash
wrangler d1 create my-app-db
# Copy database_id to wrangler.jsonc
```

---

## Migrations

```bash
# Generate
bunx drizzle-kit generate

# Copy to wrangler format
cp drizzle/*.sql migrations/

# Apply
wrangler d1 migrations apply my-app-db --local   # dev
wrangler d1 migrations apply my-app-db --remote  # prod
```

---

## TypeScript

```typescript
// app.d.ts
/// <reference types="@cloudflare/workers-types" />

declare global {
  namespace App {
    interface Platform {
      env: {
        DB: D1Database;
      };
    }
  }
}
```

---

## Preview Deployments

Preview URLs like `app-abc123.username.workers.dev` need:

### Dynamic Base URL

```typescript
export function getAuthForEvent(event: RequestEvent) {
  return createAuth(db, event.url.origin);  // Not hardcoded
}
```

### Cross-Subdomain Cookies

Share sessions across `app.user.workers.dev` and `app-preview.user.workers.dev`:

```typescript
function getCookieDomain(url: string): string | undefined {
  const hostname = new URL(url).hostname;
  const match = hostname.match(/\.([^.]+\.workers\.dev)$/);
  return match ? '.' + match[1] : undefined;
}

// In auth config:
advanced: {
  ...(cookieDomain && {
    crossSubDomainCookies: {
      enabled: true,
      domain: cookieDomain,
    },
  }),
},
```

---

## Secrets

**Local (`.dev.vars`):**
```
BETTER_AUTH_SECRET=your-secret-min-32-chars
```

**Production:**
```bash
wrangler secret put BETTER_AUTH_SECRET
```

---

## CLI User Creation

```typescript
// scripts/create-user.ts
const { values } = parseArgs({
  options: {
    email: { type: 'string' },
    name: { type: 'string' },
    password: { type: 'string' },
    local: { type: 'boolean' },
    remote: { type: 'boolean' },
  },
});

const dbFlag = values.local ? '--local' : '--remote';
const hashedPassword = await hashPassword(values.password);

execSync(`wrangler d1 execute my-app-db ${dbFlag} --command "INSERT INTO user ..."`, { stdio: 'inherit' });
execSync(`wrangler d1 execute my-app-db ${dbFlag} --command "INSERT INTO account ..."`, { stdio: 'inherit' });
```

---

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| `platform.env` undefined | Missing wrangler config | Check `d1_databases` |
| D1 not available locally | No migrations | `wrangler d1 migrations apply --local` |
| Session lost on preview | Hardcoded URL | Use `event.url.origin` |
| Cookies not shared | No cross-subdomain | Add `crossSubDomainCookies` |
