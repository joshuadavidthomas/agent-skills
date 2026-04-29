# SSR & Hydration

SvelteKit renders on the server first, then hydrates in the browser. Treat that as the default environment, not an edge case.

## Browser APIs are not route data

`window`, `document`, `localStorage`, layout measurement, media APIs, and DOM observers do not exist during SSR. Keep them out of server load functions.

```ts
// +page.ts
import { browser } from '$app/environment';

export const load = async () => {
	return {
		theme: browser ? localStorage.getItem('theme') : 'light',
	};
};
```

Use this sparingly. If browser-only data does not need to exist before initial render, keep it in the component.

```svelte
<script lang="ts">
	let width = $state<number | null>(null);

	$effect(() => {
		width = window.innerWidth;
	});
</script>
```

Effects do not run during SSR, so browser APIs are safe there.

## Hydration mismatch is design feedback

A mismatch means the server rendered one thing and the browser's first render produced another. Do not reflexively hide the problem with `if (browser)`. Ask which boundary is wrong:

- Should this data come from `+page.server.ts` so server and client agree?
- Should this UI render only after mount because it is genuinely browser-owned?
- Is module-level state leaking between SSR requests?
- Is the component using time/randomness/browser dimensions during initial render?

```svelte
<!-- Smell: server and client may render different initial markup -->
<script lang="ts">
	import { browser } from '$app/environment';
	const label = browser ? localStorage.getItem('label') : 'Loading';
</script>

<h1>{label}</h1>
```

Better: either load stable route data on the server or intentionally render a stable placeholder and update after hydration.

## Disable SSR only as a last resort

```ts
// +page.ts
export const ssr = false;
```

This turns the route into client-rendered app code. Use it for genuinely browser-only surfaces like heavy Canvas/WebGL apps, not to avoid thinking about data ownership.

## Agent Smells

- Using `onMount` fetches for server-owned route data.
- Reading `window` or `document` in `load`.
- Using `browser` checks to hide hydration mismatches without fixing ownership.
- Disabling SSR because a component imports a browser-only library.
- Storing per-request data in module scope.

## Official References

- [SvelteKit docs: State management](https://svelte.dev/docs/kit/state-management)
- [SvelteKit docs: $app/environment](https://svelte.dev/docs/kit/$app-environment)
