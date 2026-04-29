# Semantic HTML First

## The Smell

Building interaction out of generic elements and patching accessibility back in later.

```svelte
<div class="button" onclick={save}>Save</div>
```

This looks simple but lacks keyboard behavior, button semantics, disabled behavior, and correct accessibility defaults.

## Why It Happens

Component frameworks make all elements feel equally programmable. Design systems sometimes encourage styling-first thinking where semantics are an afterthought.

## The Svelte Mental Model

Svelte is close to HTML. Let HTML do the platform work. Use native elements first, then enhance.

```svelte
<button type="button" onclick={save}>Save</button>
```

A native element carries behavior, semantics, keyboard support, and browser integration that custom markup must otherwise recreate.

## Migration Strategy

1. Find interactive noninteractive elements: `div`, `span`, `li` with click/key handlers.
2. Replace with `button`, `a`, `input`, `select`, `textarea`, or another semantic element.
3. Add `type="button"` unless the button submits a form.
4. Pair labels and controls.
5. Treat Svelte a11y warnings as review findings, not noise.

## When Custom Interaction Is Fine

- genuinely custom widgets with full keyboard and ARIA behavior
- canvas/SVG interactions where native controls do not apply
- compatibility with third-party DOM structures, if wrapped carefully

Custom interaction must handle focus, keyboard, roles, names, disabled state, and screen-reader behavior deliberately.

## Where This Habit Comes From

- **React** — JSX makes `div onClick` mechanically easy
- **CSS/design-system culture** — visual role can overshadow semantic role
- **jQuery-era code** — behavior attached after markup rather than expressed by markup

## Official References

- [Svelte docs: Accessibility warnings](https://svelte.dev/docs/svelte/compiler-warnings#a11y_autofocus)
- [MDN: HTML elements reference](https://developer.mozilla.org/en-US/docs/Web/HTML/Element)
