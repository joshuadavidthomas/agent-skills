# Bindings and Directives

Use this for `bind:`, `class:`, `style:`, and related directive review.

## Bindings

Bindings create two-way data flow. Use them when the element or child component genuinely owns updates to the value.

```svelte
<input bind:value={name} />
<input type="checkbox" bind:checked={enabled} />
```

For component bindings, the child prop must use `$bindable()`.

```svelte
<script lang="ts">
  let { value = $bindable('') }: { value?: string } = $props();
</script>

<input bind:value />
```

## Common Element Bindings

| Binding | Notes |
|---|---|
| `bind:value` | Inputs, textareas, selects |
| `bind:checked` | Checkbox boolean state |
| `bind:group` | Radio/checkbox groups |
| `bind:files` | File inputs; handle file lifetimes carefully |
| `bind:this` | DOM/component reference; only valid after mount/effect |
| dimension bindings | Read-only layout measurements; beware layout work |

## Function Bindings

Use function bindings when the UI value type differs from the domain value type. This keeps conversion at the boundary instead of adding mirrored state plus `$effect`.

```svelte
<script lang="ts">
  let query = $state({ rowsPerPage: 10 });
</script>

<select
  bind:value={
    () => query.rowsPerPage.toString(),
    (value) => {
      query.rowsPerPage = Number.parseInt(value, 10);
    }
  }
>
  <option value="10">10</option>
  <option value="25">25</option>
</select>
```

If a binding only needs a setter, use `null` for the getter where Svelte supports read-only function bindings.

## Class and Style

Use class directives for simple booleans.

```svelte
<button class:active class:error={status === 'error'}>Save</button>
```

Use `class` composition for variants or forwarded classes.

```svelte
<button class={["button", `button-${variant}`, props.class]}>Save</button>
```

Use `style:` for dynamic individual properties.

```svelte
<div style:width={`${percent}%`} style:color={color} />
```

## Review Checklist

- Is two-way binding necessary, or would a callback prop be clearer?
- Is an effect only converting a bound value? Use a function binding getter/setter instead.
- Does a component prop use `$bindable()` before parent code binds to it?
- Is `bind:this` read only after mount, not during initialization?
- Are file inputs handled without assuming paths or persistent File objects?
- Does `bind:group` use stable values for radios/checkboxes?
- Are class/style expressions readable and aligned with project conventions?

## Common Mistakes

| Mistake | Fix |
|---|---|
| Binding to child prop not marked `$bindable` | Add `$bindable` or use callback prop |
| Mirrored string/number state synchronized by `$effect` | Use a function binding getter/setter |
| Reading `bind:this` immediately | Read in `$effect` or event handler |
| Binding everything by default | Use one-way props plus callbacks unless mutation is intended |
| Complex class ternaries in markup | Extract derived class value or use class composition helper |
| Style string concatenation for many dynamic props | Use `style:` directives or CSS variables |

## Official References

- [Svelte docs: bind:](https://svelte.dev/docs/svelte/bind)
- [Svelte docs: class](https://svelte.dev/docs/svelte/class)
- [Svelte docs: style:](https://svelte.dev/docs/svelte/style)
