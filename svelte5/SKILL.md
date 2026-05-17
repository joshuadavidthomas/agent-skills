---
name: svelte5
description: >
  Mental-model reset for Svelte 5. Use when writing or reviewing Svelte components
  to shift from "it works" to "thinks in Svelte." Triggers on Svelte code review,
  "is this idiomatic", "Svelte way", Svelte 5 migration, or smells carried over
  from React/Vue/Svelte 4 — effect assigns state, prop copied to $state, global
  store by default, $bindable everywhere, clickable div, createEventDispatcher,
  export let, on:click, slot-shaped APIs, lifecycle-driven code, imperative DOM
  wiring, immutable-update ceremony, context value replacement, shadcn-svelte form
  structure, Field.* components, bits-ui form controls, or component APIs that hide
  ownership. This is the general-purpose entry point for Svelte component review;
  delegates to sveltekit for routes/load/actions/server concerns and to focused
  references for details.
---

# Think in Svelte 5

You already know Svelte syntax. This skill changes your **defaults** — what you reach for first when designing a component, placing state, modeling reactivity, and reviewing UI code.

The core failure mode: writing Svelte that compiles but thinks like React, Vue, or Svelte 4. Effects that synchronize derived state or react to state changes that had a clear event. Props copied into local state. Global stores for everything. Two-way binding as the default API. Clickable `div`s. `on:click`, `export let`, `<slot>`, and `createEventDispatcher` in new Svelte 5 code. Components that are really DOM actions. Actions that are really components. These work until they don't.

Svelte's strength is that the component is a small reactive program whose dependencies are visible. Write code that lets the compiler and the DOM do the work. Keep dataflow direct, state ownership obvious, and markup semantic.

This skill is the **general-purpose entry point** for Svelte component review. For SvelteKit routes, `load`, form actions, remote functions, cookies, auth, endpoints, redirects, server errors, deployment, or app-level SSR data flow, also use **sveltekit**.

Treat these as strong defaults, not rigid laws: when unsure, choose the approach that makes ownership, dependencies, and user semantics more explicit.

## How Svelte Thinks

### Make reactivity visible

**1. Reactivity is read-tracked.** A `$derived` or `$effect` depends on the reactive values it reads while running. If an effect reruns unexpectedly, inspect what it reads — don't hunt for a dependency array. See [references/read-tracked-reactivity.md](references/read-tracked-reactivity.md).

**2. Derived state is `$derived`, not `$effect`.** If a value is a pure function of other state, derive it. Effects are for side effects, not keeping variables in sync. See [references/effect-driven-state.md](references/effect-driven-state.md).

**3. Effects are escape hatches.** Before writing `$effect`, check whether the code is actually a derived value, an event handler, or a `bind:` getter/setter transform. Reach for `$effect` when you touch the outside world: subscriptions, timers, observers, imperative APIs, logging, analytics. Return cleanup.

**4. Runes are statically analyzable.** They are compiler syntax, not hook-like runtime functions. This is why reusable state often becomes `.svelte.ts` classes and factories instead of custom hooks. See [references/static-runes.md](references/static-runes.md).

**5. `$state` is a deep proxy, not React state.** For local arrays and plain objects, mutate what changed instead of performing immutable-update ceremony just to trigger reactivity. See [references/deep-state-without-immutable-ceremony.md](references/deep-state-without-immutable-ceremony.md).

### Put state where ownership is clearest

**6. State has an owner.** Local interaction state belongs in the component. Reusable state with behavior belongs in a `.svelte.ts` class. Descendant-shared state belongs in context. Stores are for the store contract, not every changing value. See [references/state-ownership.md](references/state-ownership.md).

**7. Do not mirror props unless you mean "draft."** Copying props into `$state` creates two sources of truth. Derive from props, or create an explicitly named editable draft with reset/commit behavior. See [references/prop-mirroring.md](references/prop-mirroring.md).

**8. Context shares identity, not provider rerenders.** Put a reactive object/class in context and mutate its properties; don't expect replacing plain values to behave like React Provider updates. See [references/context-identity.md](references/context-identity.md).

**9. Module-level mutable state is suspicious in SSR apps.** In SvelteKit, exported mutable instances can leak between requests. Use factories, context, or request-owned data. See [references/ssr-state-leaks.md](references/ssr-state-leaks.md).

### Design component APIs around ownership

**10. Props describe inputs; callbacks describe events.** In Svelte 5, component events are usually callback props. Avoid `createEventDispatcher` in new code unless preserving an old public API. See [references/component-patterns.md](references/component-patterns.md).

**11. Two-way binding is an API commitment.** `$bindable` says the child may mutate parent-owned state. Use it for form controls and deliberate controlled components, not as a default. See [references/bindable-by-default.md](references/bindable-by-default.md).

**12. Snippets are render functions, not renamed slots.** Use snippets when the parent supplies UI. Type snippet parameters and name snippets by role. See [references/snippets-as-render-functions.md](references/snippets-as-render-functions.md).

**13. Wrapper components should preserve the platform.** If a component wraps a `button`, accept button attributes, forward relevant props/events, keep `type`, `disabled`, focus, and ARIA semantics intact. See [references/wrapper-components-preserve-html.md](references/wrapper-components-preserve-html.md).

### Let HTML and the compiler work

**14. Native elements before custom behavior.** A `button` already handles keyboard, focus, disabled state, and accessibility semantics. A clickable `div` asks you to rebuild the platform badly. See [references/semantic-html-first.md](references/semantic-html-first.md).

**15. Design-system fields should preserve form semantics.** In shadcn-svelte or bits-ui forms, use `Field.*` for labels, field groups, descriptions, and errors. Do not rebuild field structure with raw `div`s, separate `Label` imports, or clickable option rows. See [references/shadcn-svelte-forms.md](references/shadcn-svelte-forms.md).

**16. Components own markup; actions/attachments own DOM behavior.** If it renders UI, make a component. If it attaches reusable imperative behavior to an element, use an action or attachment. See [references/actions-vs-components.md](references/actions-vs-components.md).

**17. Svelte 5 syntax should be consistent.** In new Svelte 5 code, use `$props`, event attributes like `onclick`, snippets, and callback props. Do not mix old syntax unless maintaining legacy code. See [references/svelte5-syntax-discipline.md](references/svelte5-syntax-discipline.md).

**18. Type the boundary, not every breath.** Give non-trivial components a `Props` type, type snippets and callbacks, and use `svelte/elements` for wrappers. Avoid broad `any` at component boundaries. See [references/typescript.md](references/typescript.md).

## Common Mistakes (Agent Failure Modes)

- **Using `$effect` to compute state** → Use `$derived` / `$derived.by`; reserve effects for the outside world.
- **Using `$effect` to react to user input state** → React to the event itself with `oninput`, `onchange`, `onclick`, or a component callback like `onValueChange`.
- **Using `$effect` for binding type conversion** → Use function bindings with getter/setter pairs.
- **Reading broad objects in effects** → Read the specific dependencies you intend.
- **Calling runes like hooks/composables** → Move runes to component top level or `.svelte.ts` class fields.
- **Mirroring props into `$state`** → Derive from props or name the local state as a draft with commit/reset behavior.
- **Immutable updates by reflex** → Mutate local deep `$state` directly when that expresses the change.
- **Global store by default** → Put state where it is owned: component, `.svelte.ts` class, context, then store only when useful.
- **Exported mutable singleton in SvelteKit** → Use a factory/context/request-owned state to avoid SSR leaks.
- **`$bindable` everywhere** → Prefer callback props unless two-way mutation is the component's intended API.
- **`createEventDispatcher` in new Svelte 5** → Use callback props.
- **`export let`, `on:click`, `<slot>` in new Svelte 5** → Use `$props`, `onclick`, snippets/render tags.
- **Clickable `div` / `span`** → Use native controls or implement full keyboard/ARIA semantics.
- **Wrapper component drops native behavior** → Type and forward native attributes; preserve focus/disabled/button semantics.
- **shadcn-svelte form built from raw `div` + imported `Label`** → Use `Field.Group`, `Field.Field`, `Field.Set`, `Field.Label`, `Field.Description`, and `Field.Error`.
- **Checkbox/radio card uses row `onclick`** → Wrap `Field.Field` in `Field.Label` and connect it to the input id.
- **Unkeyed list with identity, local state, or animation** → Key by stable id.
- **`{@html}` with user content** → Sanitize or render as text.
- **Action that owns markup/state** → Make it a component.
- **Component used only for imperative DOM behavior** → Make it an action or attachment.

## Quick Reference

| Code smell | Svelte default move | Reference |
|---|---|---|
| Effect reruns mysteriously | Inspect reactive reads | [read-tracked-reactivity](references/read-tracked-reactivity.md) |
| Effect assigns derived value | `$derived` / `$derived.by` | [effect-driven-state](references/effect-driven-state.md) |
| Effect responds to a control changing | Event handler or callback prop | [effect-driven-state](references/effect-driven-state.md) |
| Effect converts a bound value | `bind:` getter/setter pair | [bindings-and-directives](references/bindings-and-directives.md) |
| Rune inside helper/hook | Top-level rune or class field | [static-runes](references/static-runes.md) |
| Immutable update ceremony | Direct deep `$state` mutation | [deep-state-without-immutable-ceremony](references/deep-state-without-immutable-ceremony.md) |
| Prop copied into local state | Derive or explicit draft | [prop-mirroring](references/prop-mirroring.md) |
| State owner unclear | Smallest owner wins | [state-ownership](references/state-ownership.md) |
| Context value replacement | Stable reactive object identity | [context-identity](references/context-identity.md) |
| Store used for simple local state | `$state` / class / context | [state-ownership](references/state-ownership.md) |
| Module singleton in SvelteKit | Factory/context/request state | [ssr-state-leaks](references/ssr-state-leaks.md) |
| Child emits event | Callback prop | [component-patterns](references/component-patterns.md) |
| `$bindable` by habit | Callback prop unless two-way API | [bindable-by-default](references/bindable-by-default.md) |
| Slot-shaped API | Typed snippet render function | [snippets-as-render-functions](references/snippets-as-render-functions.md) |
| Click handler on noninteractive element | Native control | [semantic-html-first](references/semantic-html-first.md) |
| shadcn-svelte form structure rebuilt with raw wrappers | Use `Field.*` components | [shadcn-svelte-forms](references/shadcn-svelte-forms.md) |
| Checkbox/radio option row has custom click handling | Label-wrap the `Field.Field` and native control | [shadcn-svelte-forms](references/shadcn-svelte-forms.md) |
| Wrapper hides native behavior | Preserve HTML contract | [wrapper-components-preserve-html](references/wrapper-components-preserve-html.md) |
| Component/action boundary unclear | Markup = component; DOM behavior = action | [actions-vs-components](references/actions-vs-components.md) |
| Old Svelte syntax in new code | Migrate API and dataflow intentionally | [svelte5-syntax-discipline](references/svelte5-syntax-discipline.md) |
| Raw HTML | Sanitize or avoid | [template-tags](references/template-tags.md) |
| Component behavior test | Testing Library / `mount` | [testing](references/testing.md) |

## Cross-References

- **sveltekit** — Routes, layouts, `load`, form actions, remote functions, cookies, auth, endpoints, redirects, server errors, app-level SSR/data flow

## Review Checklist

1. **Project is Svelte 5?** → Use Svelte 5 syntax consistently.
2. **`$effect` writes state?** → Ask if it should be `$derived` / `$derived.by`.
3. **`$effect` reacts to a user-controlled value?** → Move the work to the event that changed it.
4. **`$effect` only converts a bound value?** → Use a `bind:` getter/setter pair.
5. **Effect reruns unexpectedly?** → Inspect what it reads.
6. **Rune called like a hook?** → Move to top-level or `.svelte.ts` class field.
7. **Props copied to state?** → Derive or make an explicit draft.
8. **State owner unclear?** → Move state to component/class/context/store according to ownership.
9. **Store used by habit?** → Check whether the store contract is actually needed.
10. **Module-level mutable state in SvelteKit?** → Treat as SSR leak risk.
11. **`$bindable` prop?** → Confirm two-way mutation is intended.
12. **Dispatcher or old event syntax?** → Prefer callback props and event attributes in Svelte 5.
13. **Slot-style API?** → Prefer typed snippets.
14. **Nonsemantic interactive markup?** → Use native elements first.
15. **shadcn-svelte form?** → Use `Field.*` structure and label-wrapped option rows.
16. **Wrapper component?** → Preserve native attributes, events, and semantics.
17. **List identity matters?** → Key the each block.
18. **Reusable DOM behavior?** → Action/attachment, with cleanup.
19. **Raw HTML?** → Sanitize or avoid.
20. **Performance concern?** → Fix dataflow first, measure before cleverness.
