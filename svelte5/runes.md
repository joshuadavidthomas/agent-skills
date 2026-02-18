# Svelte 5 Runes

## Quick Start

**Which rune?** Props: `$props()` | Bindable: `$bindable()` |
Computed: `$derived()` | Side effect: `$effect()` | State: `$state()`

**Key rules:** Runes are top-level only. $derived can be overridden
(use `const` for read-only). Don't mix Svelte 4/5 syntax.
Objects/arrays are deeply reactive by default.

## Example

```svelte
<script>
	let count = $state(0); // Mutable state
	const doubled = $derived(count * 2); // Computed (const = read-only)

	$effect(() => {
		console.log(`Count is ${count}`); // Side effect
	});
</script>

<button onclick={() => count++}>
	{count} (doubled: {doubled})
</button>
```

## Reference Files

**Before suggesting code, check these:**

- [references/runes/reactivity-patterns.md](references/runes/reactivity-patterns.md) —
  When to use each rune
- [references/runes/migration-gotchas.md](references/runes/migration-gotchas.md) —
  Svelte 4 → 5 translation
- [references/runes/component-api.md](references/runes/component-api.md) —
  $props, $bindable patterns
- [references/runes/snippets-vs-slots.md](references/runes/snippets-vs-slots.md) —
  New snippet syntax
- [references/runes/common-mistakes.md](references/runes/common-mistakes.md) —
  Anti-patterns with fixes

## Notes

- Event handlers: Use `onclick` not `on:click` in Svelte 5
- Children: Use `{@render children()}` in layouts
- Check Svelte version before suggesting syntax
- **Svelte 5.25+ breaking change:** `$derived` can now be reassigned
  (use `const` for read-only)
