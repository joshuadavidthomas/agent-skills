# Effects as Escape Hatches

Use this when code reaches for `$effect` to synchronize values, react to local UI changes, or patch over a binding mismatch.

## The Smell

`$effect` writes Svelte state or calls app logic because some state changed.

```svelte
<script lang="ts">
  let currentPage = $state(data.query.page);

  $effect(() => {
    navUpdate({ page: currentPage });
  });
</script>

<Select bind:value={currentPage} />
```

This works, but it makes review harder: the reader must understand every reactive value read inside the effect and every write that can trigger it again.

## The Svelte Mental Model

Do not react to state changes when you can react to the thing that changed the state.

Reach for these exits before `$effect`:

1. **Pure computed value** → `$derived` or `$derived.by`
2. **User interaction** → the event handler or component callback that represents the interaction
3. **Binding type conversion** → a `bind:` getter/setter pair
4. **Outside-world synchronization** → `$effect`, with narrow reads and cleanup

`$effect` is an escape hatch for subscriptions, timers, observers, imperative libraries, browser APIs, logging, analytics, and other work outside Svelte's reactive graph.

## Replace Effect-Computed State with `$derived`

Smell:

```svelte
<script lang="ts">
  let rowsPerPageValue = $state(String(data.query.rows));

  $effect(() => {
    rowsPerPageValue = String(data.query.rows);
  });
</script>
```

Better when `data.query.rows` can change:

```svelte
<script lang="ts">
  let rowsPerPageValue = $derived(String(data.query.rows));
</script>
```

If the value is intentionally just an initial draft, make that explicit instead of synchronizing it forever.

```svelte
<script lang="ts">
  // svelte-ignore state_referenced_locally -- initial draft only
  let rowsPerPageDraft = $state(String(data.query.rows));
</script>
```

Use `$derived.by` when the computation needs statements, loops, or early returns.

```svelte
<script lang="ts">
  const total = $derived.by(() => {
    let total = 0;
    for (const item of items) total += item.price;
    return total;
  });
</script>
```

## Replace Effect-Reactions with Events

Smell:

```svelte
<script lang="ts">
  let currentPage = $state(data.query.page);

  $effect(() => {
    navUpdate({ page: currentPage });
  });
</script>

<Select bind:value={currentPage} />
```

Better:

```svelte
<script lang="ts">
  let currentPage = $state(data.query.page);
</script>

<Select
  bind:value={currentPage}
  onValueChange={(page) => navUpdate({ page })}
/>
```

For native controls, put the app work on the native event.

```svelte
<input
  value={query}
  oninput={(event) => {
    query = event.currentTarget.value;
    updateSearch(query);
  }}
/>
```

Use a callback prop for component events in new Svelte 5 APIs.

## Replace Conversion Effects with Function Bindings

Smell:

```svelte
<script lang="ts">
  let query = $state({ rowsPerPage: 10 });
  let rowsPerPageValue = $state(String(query.rowsPerPage));

  $effect(() => {
    const next = Number.parseInt(rowsPerPageValue, 10);
    if (Number.isFinite(next)) query.rowsPerPage = next;
  });
</script>

<Select bind:value={rowsPerPageValue} />
```

Better:

```svelte
<script lang="ts">
  let query = $state({ rowsPerPage: 10 });
</script>

<Select
  bind:value={
    () => query.rowsPerPage.toString(),
    (value) => {
      query.rowsPerPage = Number.parseInt(value, 10);
    }
  }
/>
```

Keep parsing and formatting at the binding boundary instead of creating a second piece of synchronized state.

## Migration Strategy

1. Find what the effect writes or calls.
2. If it writes a pure computed value, replace it with `$derived` / `$derived.by`.
3. If it responds to user input, move the work to the event/callback that changed the value.
4. If it converts between UI and domain types, use a `bind:` getter/setter pair.
5. If the effect remains, narrow its reactive reads, avoid writing dependencies it reads, and return cleanup for resources it creates.

## When `$effect` Is Fine

- subscribing to an external source
- starting/stopping timers
- attaching observers or imperative library instances
- logging, analytics, telemetry
- synchronizing with browser APIs that are not represented in markup
- one-off imperative DOM work that cannot be expressed with markup, an action, or an attachment

If a project already uses a utility such as `watch` from `runed`, an explicit dependency list can reduce footguns for unavoidable effects. Do not add a dependency only to avoid designing the dataflow.

## Where This Habit Comes From

- **React** — `useEffect` is commonly used as a synchronization primitive
- **Vue** — watchers are easy to reach for before computed values or events
- **Svelte 4** — `$:` mixed derived values and side-effecting reactive statements

## Sources

- [Aidan Bleser: A plead to stop using `$effect`](https://aidanbleser.com/blog/posts/dont-use-effect)
- [Svelte docs: $derived](https://svelte.dev/docs/svelte/$derived)
- [Svelte docs: $effect](https://svelte.dev/docs/svelte/$effect)
- [Svelte docs: bind:](https://svelte.dev/docs/svelte/bind)
