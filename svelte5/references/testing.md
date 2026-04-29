# Testing Svelte Components

Prefer behavior-oriented tests. Test what users can observe, not Svelte internals.

## Tooling

Common choices:

- Vitest for unit/component tests in Vite/Svelte projects
- `@testing-library/svelte` for user-facing component interaction tests
- Playwright for end-to-end flows
- Storybook for component states and interaction docs

Follow the project's existing test runner and config.

## Svelte 5 Mounting

Use Svelte's imperative API when directly mounting components in tests.

```ts
import { flushSync, mount, unmount } from 'svelte';
import { expect, test } from 'vitest';
import Counter from './Counter.svelte';

test('increments', () => {
  const component = mount(Counter, {
    target: document.body,
    props: { initial: 0 }
  });

  document.querySelector('button')?.dispatchEvent(new MouseEvent('click', { bubbles: true }));
  flushSync();

  expect(document.body.textContent).toContain('1');
  unmount(component);
});
```

`flushSync` is useful when a test needs pending updates/effects to settle synchronously.

## Review Checklist

- Does the test assert user-visible behavior?
- Does it avoid testing implementation details like internal rune variables?
- Are mounted components unmounted/cleaned up?
- Are async updates awaited or flushed correctly?
- Are accessibility queries preferred over brittle selectors when Testing Library is used?
- Should this be a component test, or an E2E test because routing/network behavior matters?

## Common Mistakes

| Mistake | Fix |
|---|---|
| Testing internal state directly | Interact with UI and assert output |
| Mounted component not unmounted | Call cleanup/unmount |
| Missing `flushSync`/await for updates | Flush or await the rendered change |
| Component test covers SvelteKit routing/auth | Move to SvelteKit/Playwright-level test |
| Snapshots for interactive behavior | Use interaction assertions |

## Official References

- [Svelte docs: Testing](https://svelte.dev/docs/svelte/testing)
- [Testing Library: Svelte Testing Library](https://testing-library.com/docs/svelte-testing-library/intro/)
