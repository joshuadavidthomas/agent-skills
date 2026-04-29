# Template Tags and Blocks

This covers Svelte template features that often matter in reviews: `{@const}`, `{@html}`, `{@debug}`, and async blocks.

## `{@const}`

Use `{@const}` for local computed values inside markup blocks when it improves readability.

```svelte
{#each users as user (user.id)}
  {@const displayName = user.name.trim() || user.email}
  <p>{displayName}</p>
{/each}
```

Do not use it to hide expensive work in markup. Move expensive or shared computations to `$derived`.

## `{@html}`

`{@html}` injects raw HTML. Treat it as a security-sensitive code review finding.

```svelte
{@html trustedHtml}
```

Only use it with trusted or sanitized HTML. Never pass raw user input directly.

## `{@debug}`

Use `{@debug value}` for temporary debugging during development. Remove it before shipping unless the project intentionally keeps debug-only code behind a guard.

Prefer `$inspect` for Svelte 5 reactive debugging; see [debugging.md](debugging.md).

## `{#await}`

Use `{#await}` for promise state in component markup. In SvelteKit, prefer `load`/server data flow when data belongs to routing or SSR.

```svelte
{#await promise}
  <p>Loading…</p>
{:then result}
  <ResultView {result} />
{:catch error}
  <p role="alert">Could not load data</p>
{/await}
```

## Review Checklist

- Is `{@html}` sanitized or trusted?
- Would a repeated `{@const}` be clearer as `$derived`?
- Is `{@debug}` leftover development code?
- Does `{#await}` expose loading and error states accessibly?
- Should async data move to SvelteKit `load` instead of component-local promises?

## Common Mistakes

| Mistake | Fix |
|---|---|
| `{@html userInput}` | Sanitize or render as text |
| Expensive computation in `{@const}` inside large each block | Precompute with `$derived` |
| Promise UI has no catch branch | Add error state |
| Debug tags committed accidentally | Remove or guard |

## Official References

- [Svelte docs: @html](https://svelte.dev/docs/svelte/@html)
- [Svelte docs: @const](https://svelte.dev/docs/svelte/@const)
- [Svelte docs: await blocks](https://svelte.dev/docs/svelte/await)
