---
name: sveltekit
description: >
  Mental-model reset for SvelteKit apps. Use when writing or reviewing routes,
  layouts, load functions, form actions, remote functions, hooks, auth, cookies,
  endpoints, redirects, errors, SSR, progressive enhancement, or app-level data
  flow. Triggers on SvelteKit, +page, +layout, +server, +page.server.ts,
  +layout.server.ts, hooks.server.ts, load, actions, fail(), redirect(), error(),
  cookies, locals, route groups, protected routes, sessions, form actions,
  enhance, remote functions, command(), query(), form(), getRequestEvent(), SSR,
  hydration, and serialization. Use svelte5 for component-level runes, snippets,
  accessibility, actions, transitions, and component API review.
---

# Think in SvelteKit

SvelteKit is not just Svelte with folders. It is an application boundary system: route files define ownership of data, server code stays on the server, form submissions progressively enhance, and redirects/errors are part of control flow.

The core failure mode: writing SvelteKit like a client-side SPA with incidental server helpers. Fetching server-owned data from components. Hiding auth in hooks and assuming layouts protect endpoints. Returning class instances from `load`. Calling `redirect()` without throwing. Building JavaScript-only forms when native forms plus actions would work. These work until SSR, progressive enhancement, caching, or security boundaries matter.

Use this skill for app-level SvelteKit decisions. Use **svelte5** for component internals: runes, snippets, component props, DOM events, accessibility, transitions, and component state.

## How SvelteKit Thinks

### Routes own application boundaries

**1. File names are behavior.** `+page.svelte`, `+layout.server.ts`, `+page.server.ts`, and `+server.ts` are not organization trivia; they decide where code runs and who can call it. See [references/file-naming.md](references/file-naming.md).

**2. Route groups organize policy, not URLs.** `(app)` and `(auth)` are for layout/auth/data boundaries without changing paths. Put protected routes under a protected layout; keep login/signup outside that group. See [references/layout-patterns.md](references/layout-patterns.md).

**3. Layouts protect pages, not endpoints.** A protected `+layout.server.ts` gates child pages. It does not protect sibling or child `+server.ts` endpoints; every endpoint must enforce auth itself. See [references/auth.md](references/auth.md).

### Data flow should reveal ownership

**4. Server-owned data loads on the server.** Database queries, secrets, private APIs, and session-derived data belong in `+page.server.ts` / `+layout.server.ts`, not in component `onMount` or browser fetches. See [references/load-functions.md](references/load-functions.md).

**5. Universal load is for universal work.** Use `+page.ts` only when the code can safely run in both browser and server. If it needs secrets or trusted auth, it is not universal.

**6. Load returns data, not behavior.** Return serializable data from server load. Do not return class instances, functions, database handles, or rich objects that depend on identity. See [references/serialization.md](references/serialization.md).

**7. Redirects and errors are thrown control flow.** In SvelteKit 2, `redirect()` and `error()` return objects; throw them. Bare calls are bugs. See [references/errors-and-redirects.md](references/errors-and-redirects.md).

### Forms are server-first

**8. Form actions are the default mutation boundary.** If a user submits form-shaped data, prefer a native form plus `+page.server.ts` action before inventing a client-only mutation path. See [references/form-actions.md](references/form-actions.md).

**9. Progressive enhancement is enhancement.** The form should work without JavaScript; `use:enhance` improves pending states, focus, invalidation, and UX. It should not be the only way the mutation works.

**10. Validation lives at the boundary.** Validate on the server, return field-shaped errors with `fail`, and let the component display them. Client validation is UX, not authority. See [references/forms-validation.md](references/forms-validation.md).

### Auth is explicit and boring

**11. Hooks populate context; routes enforce policy.** `hooks.server.ts` should parse sessions and populate `locals`. Layout/server loads and endpoints decide what is allowed. Do not silently skip auth if infrastructure is missing. See [references/auth.md](references/auth.md).

**12. Cookies and locals are request state.** Treat them as per-request server data. Do not mirror them into global module state or trust client copies for authorization.

**13. API endpoints are their own security boundary.** Check method, auth, authorization, input validation, and response shape inside each `+server.ts`. A page layout is irrelevant to direct HTTP calls.

### Remote functions are still server boundaries

**14. Remote functions do not remove validation.** `command`, `query`, and `form` still cross a client/server boundary. Validate arguments, check auth, and return serializable data. Remote functions are version/feature-flag dependent; confirm the project has opted in before recommending them. See [references/remote-functions.md](references/remote-functions.md).

**15. Choose the remote primitive by intent.** Use `query` for repeated reads, `command` for imperative mutations, and `form` for form-shaped submissions. Do not use remote functions to bypass SvelteKit's normal page/form model without a reason.

### SSR is the default environment

**16. Browser APIs are conditional.** `window`, `document`, `localStorage`, media APIs, and DOM measurement do not exist during SSR. Use component effects, `browser`, or client-only boundaries deliberately. See [references/ssr-hydration.md](references/ssr-hydration.md).

**17. Hydration mismatches are design feedback.** If server and client render different initial markup, fix the data boundary or defer browser-only rendering intentionally. Do not paper over mismatches with random client checks.

## Common Mistakes (Agent Failure Modes)

- **Fetching server-owned data in `onMount`** → use server `load`.
- **Using universal load for secrets** → move to `+page.server.ts` or `+layout.server.ts`.
- **Returning classes/functions from load** → return serializable plain data.
- **Calling `redirect()` / `error()` without `throw`** → throw them.
- **Protecting endpoints via layouts** → check auth in every `+server.ts`.
- **Doing auth policy in hooks only** → hooks populate `locals`; routes enforce.
- **Silently skipping auth when DB/session infrastructure is missing** → fail closed.
- **Putting login inside the protected route group** → keep auth pages outside protected layouts.
- **Building JS-only forms** → use native forms + actions + progressive enhancement.
- **Trusting client validation** → validate on the server boundary.
- **Using remote functions without auth/validation** → treat them as server endpoints.
- **Using browser APIs during SSR** → gate with effects/browser-only logic.
- **Using svelte5 component advice for app data flow** → load the SvelteKit reference.

## Quick Reference

| Smell | SvelteKit default move | Reference |
|---|---|---|
| Route file choice unclear | Pick by runtime and boundary | [file-naming](references/file-naming.md) |
| Protected page group | `+layout.server.ts` auth check | [auth](references/auth.md) |
| Protected endpoint | auth check inside `+server.ts` | [auth](references/auth.md) |
| DB/secrets in browser code | server load/action/endpoint | [load-functions](references/load-functions.md) |
| Form-shaped mutation | form action | [form-actions](references/form-actions.md) |
| Field validation errors | `fail(400, { errors })` | [forms-validation](references/forms-validation.md) |
| Bare `redirect()` or `error()` | `throw redirect(...)` / `throw error(...)` | [errors-and-redirects](references/errors-and-redirects.md) |
| Rich object returned from load | serializable plain data | [serialization](references/serialization.md) |
| Client-only API in SSR | effect/browser guard | [ssr-hydration](references/ssr-hydration.md) |
| Repeated server read from client | `query()` if remote functions fit | [remote-functions](references/remote-functions.md) |
| Imperative server mutation from client | `command()` with validation/auth | [remote-functions](references/remote-functions.md) |
| Component API/runes issue | use svelte5 | **svelte5** |

## Reference Index

[File Naming](references/file-naming.md) · [Layout Patterns](references/layout-patterns.md) · [Load Functions](references/load-functions.md) · [Form Actions](references/form-actions.md) · [Forms Validation](references/forms-validation.md) · [Auth](references/auth.md) · [Errors/Redirects](references/errors-and-redirects.md) · [Serialization](references/serialization.md) · [SSR/Hydration](references/ssr-hydration.md) · [Remote Functions](references/remote-functions.md) · [Better Auth](references/better-auth.md) · [Cloudflare](references/cloudflare.md)
