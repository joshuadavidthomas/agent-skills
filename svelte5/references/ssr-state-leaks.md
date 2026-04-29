# SSR State Leaks

## The Smell

Exporting mutable client/application state from a module that can be evaluated on the server.

```ts
// session.svelte.ts
export const session = new SessionState();
```

In an SSR app, this can become shared state across requests/users.

## Why It Happens

Client-only singletons feel natural in SPAs. Svelte 4 stores were often exported from modules. In SvelteKit, the same module may run in a long-lived server process.

## The Svelte Mental Model

Request/user-specific state must be owned by the request, route data, a component tree, or a factory-created instance. Module scope is process scope, not user scope.

```ts
// safe factory
export const createSessionState = () => new SessionState();
```

Then create it in the appropriate component/request context and pass it through props or context.

## Migration Strategy

1. Search for exported mutable instances, writable stores, arrays, maps, caches, or class instances.
2. Ask whether the data is user/request-specific.
3. Replace user-specific singletons with factories or context.
4. Keep true constants and safe immutable config at module scope.
5. For server data, prefer SvelteKit `load`, actions, cookies, and server modules.

## When Module State Is Fine

- constants and immutable config
- build-time data
- process-wide caches that are deliberately shared and safe
- browser-only state guarded to never run during SSR, if the app accepts that constraint

## Where This Habit Comes From

- **SPA React/Vue/Svelte** — browser module singletons are per-tab, not per-server-process
- **Svelte 4** — exported stores were a standard shared-state pattern
- **Node server code** — module caching is normal but dangerous for per-user data

## Official References

- [SvelteKit docs: State management](https://svelte.dev/docs/kit/state-management)
- [Svelte docs: Context](https://svelte.dev/docs/svelte/context)
