# Debugging Svelte Reactivity

Use this when reactive values update unexpectedly, effects run too often, or dependencies are unclear.

## `$inspect`

Use `$inspect` during development to observe reactive changes.

```svelte
<script lang="ts">
  let count = $state(0);
  let doubled = $derived(count * 2);

  $inspect(count, doubled);
</script>
```

Remove debug instrumentation before shipping unless the project intentionally gates it for development.

## Effects and Dependencies

Effects track the reactive values read while they run. If an effect runs too often, inspect what it reads.

```svelte
$effect(() => {
  // Every reactive value read here becomes a dependency.
  console.log(form.value, form.valid);
});
```

Use `untrack` only when you intentionally need to read a value without making it a dependency. Prefer simpler data flow before reaching for it.

## Review Checklist

- Is `$effect` being used for derived state instead of side effects?
- Does an effect read more reactive values than intended?
- Is cleanup returned for subscriptions, timers, observers, and external APIs?
- Is async work protected against races or stale results?
- Are debug helpers removed or gated?
- Would naming a `$derived` value make the dependency graph clearer?

## Common Mistakes

| Mistake | Fix |
|---|---|
| Adding logs inside effects and leaving them | Use `$inspect` temporarily, then remove |
| Effect updates state that triggers itself | Use `$derived` or restructure dependencies |
| Reading whole objects when only one field matters | Read the specific fields needed |
| Using `untrack` to paper over confusing design | Simplify ownership/data flow first |
| Async effect result overwrites newer state | Use cancellation/stale guards |

## Official References

- [Svelte docs: $inspect](https://svelte.dev/docs/svelte/$inspect)
- [Svelte reference: untrack](https://svelte.dev/docs/svelte/svelte#untrack)
