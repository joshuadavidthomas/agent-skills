# File Naming Conventions

## Core Files

| File                | Purpose               | Runs                  | Example                                       |
| ------------------- | --------------------- | --------------------- | --------------------------------------------- |
| `+page.svelte`      | Page component        | Client & Server (SSR) | `/routes/about/+page.svelte` → `/about`       |
| `+page.ts`          | Universal load        | Client & Server       | Data for +page.svelte                         |
| `+page.server.ts`   | Server load & actions | Server only           | DB queries, form actions                      |
| `+layout.svelte`    | Layout wrapper        | Client & Server       | Wraps child routes                            |
| `+layout.ts`        | Layout universal load | Client & Server       | Data for +layout.svelte                       |
| `+layout.server.ts` | Layout server load    | Server only           | Auth, user data                               |
| `+error.svelte`     | Error boundary        | Client & Server       | Shown when error thrown                       |
| `+server.ts`        | API endpoint          | Server only           | `/routes/api/users/+server.ts` → `/api/users` |

## Route Parameters

| Pattern        | Matches        | Example                                                          |
| -------------- | -------------- | ---------------------------------------------------------------- |
| `[id]`         | Single param   | `/posts/[id]/+page.svelte` → `/posts/123`                        |
| `[slug]`       | Single param   | `/blog/[slug]/+page.svelte` → `/blog/hello-world`                |
| `[[optional]]` | Optional param | `/search/[[query]]/+page.svelte` → `/search` or `/search/svelte` |
| `[...rest]`    | Rest params    | `/docs/[...path]/+page.svelte` → `/docs/a/b/c`                   |

## Route Groups

| Pattern       | Purpose                      | URL                                            |
| ------------- | ---------------------------- | ---------------------------------------------- |
| `(group)`     | Group routes (no URL impact) | `/(app)/dashboard/+page.svelte` → `/dashboard` |
| `(marketing)` | Separate layouts             | Different layout for marketing pages           |

## Special Files

- `hooks.server.ts` - Server hooks (handle function, runs on every
  request)
- `hooks.client.ts` - Client hooks (runs in browser)
- `app.html` - HTML template
- `service-worker.ts` - Service worker
- `params/*.ts` - Param validators

## Mindset

File names are behavior. Before adding code, choose the file that matches the runtime boundary. If you are reaching for `onMount` or a client fetch to get route data, ask whether a `+page.server.ts` or `+layout.server.ts` should own it instead.

## Official References

- [SvelteKit docs: Routing](https://svelte.dev/docs/kit/routing)
- [SvelteKit docs: Project structure](https://svelte.dev/docs/kit/project-structure)
