# Actions vs Components

## The Smell

Using the wrong abstraction layer: a component for invisible DOM behavior, or an action for behavior that owns UI/state.

```svelte
<!-- Component that only imperatively modifies its parent or document -->
<ClickOutsideDetector onoutside={close} />
```

```ts
// Action that starts growing into a hidden component with UI and app state
export const tooltip = (node: HTMLElement, text: string) => { /* creates DOM, tracks state */ };
```

## Why It Happens

React encourages components for nearly everything. jQuery-style habits encourage imperative DOM helpers. Svelte has both components and actions, so choosing the layer matters.

## The Svelte Mental Model

Components own markup. Actions/attachments attach reusable behavior to an existing element.

Use a component when the abstraction renders UI:

```svelte
<Tooltip content="Save changes">
  <button type="button">Save</button>
</Tooltip>
```

Use an action when the abstraction modifies one DOM node's behavior:

```svelte
<div use:clickOutside={{ onoutside: close }}>
  ...
</div>
```

## Migration Strategy

1. Ask: does this abstraction own visible markup?
2. If yes, make it a component.
3. If no, and it attaches behavior to a specific element, make it an action or attachment.
4. Ensure actions clean up listeners, observers, timers, and third-party instances.
5. Ensure components preserve semantic HTML and expose explicit props/callbacks.

## When the Boundary Blurs

- overlays, popovers, and tooltips may need both a component and an action
- third-party widgets may require an action internally wrapped by a component
- attachments may be preferable to actions in current Svelte projects that use them consistently

## Where This Habit Comes From

- **React** — component as the universal abstraction
- **jQuery** — imperative DOM behavior as the default abstraction
- **Vue directives** — directive habits map more closely to Svelte actions

## Official References

- [Svelte docs: use: actions](https://svelte.dev/docs/svelte/use)
- [Svelte docs: @attach](https://svelte.dev/docs/svelte/@attach)
