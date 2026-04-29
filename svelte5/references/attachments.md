# Attachments

Attachments are Svelte 5's newer DOM-behavior composition mechanism, used with `{@attach ...}`. Prefer them when the project already uses a Svelte version that supports them and the behavior benefits from Svelte's reactive/effect model.

Actions (`use:`) are still common and valid. Use [actions.md](actions.md) when the codebase uses actions or needs older compatibility.

## When to Use

Use attachments for:

- reusable DOM behavior that needs reactive setup/cleanup
- behavior passed through wrapper components
- composing multiple DOM behaviors without creating extra components

Use a component instead when the behavior owns markup, state, or a visible UI contract.

## Review Checklist

- Confirm the installed Svelte version supports attachments before recommending them.
- Check cleanup for listeners, observers, timers, and third-party instances.
- Keep behavior semantic: attachments should not turn noninteractive elements into inaccessible controls.
- Prefer attachments/actions over ad-hoc `bind:this` plus scattered `$effect` when behavior is reusable.
- Do not migrate stable actions to attachments unless the change removes real complexity.

## Guidance

Because attachments are newer, be conservative in library code or projects with broad version ranges. For app code on current Svelte, they are a good fit for reusable DOM behavior.

## Official References

- [Svelte docs: @attach](https://svelte.dev/docs/svelte/@attach)
