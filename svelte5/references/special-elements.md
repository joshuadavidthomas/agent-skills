# Special Elements

Svelte special elements handle document-level behavior, dynamic elements, head content, options, and error boundaries.

## Common Elements

| Element | Use |
|---|---|
| `<svelte:head>` | Document head tags such as title/meta |
| `<svelte:window>` | Window events and bindings |
| `<svelte:document>` | Document events |
| `<svelte:body>` | Body events/classes |
| `<svelte:element>` | Dynamic HTML element name |
| `<svelte:boundary>` | Component error boundary |
| `<svelte:options>` | Component/compiler options |

## Examples

```svelte
<svelte:head>
  <title>{title}</title>
</svelte:head>
```

```svelte
<svelte:window onkeydown={handleKeydown} />
```

```svelte
<svelte:element this={tag} class="prose">
  {@render children?.()}
</svelte:element>
```

## Error Boundaries

Use `<svelte:boundary>` to contain component-level render errors. In SvelteKit, this is different from route-level `+error.svelte` handling.

Review whether the fallback gives users a recovery path and whether errors are logged appropriately.

## Review Checklist

- Is `<svelte:head>` used for document metadata instead of imperative DOM edits?
- Are window/document listeners expressed declaratively when possible?
- Does dynamic `this` come from a constrained set of tag names?
- Does `<svelte:element>` preserve accessibility semantics for each possible tag?
- Are boundary fallbacks useful rather than hiding errors silently?
- Is `<svelte:options>` necessary, or is it stale migration debris?

## Common Mistakes

| Mistake | Fix |
|---|---|
| Manually adding global listeners in effects without cleanup | Prefer special elements or return cleanup |
| Dynamic tag accepts arbitrary user input | Restrict to allowed tags/components |
| Boundary swallows errors with empty fallback | Show recovery UI and log/report |
| Using `<svelte:head>` for per-component styling hacks | Keep head content semantic |

## Official References

- [Svelte docs: Special elements](https://svelte.dev/docs/svelte/svelte-boundary)
