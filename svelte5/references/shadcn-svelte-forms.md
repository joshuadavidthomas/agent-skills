# shadcn-svelte Form Components

shadcn-svelte and bits-ui form code is still Svelte component code. Keep the same defaults: semantic controls, explicit state ownership, native form behavior, and component APIs that preserve the platform. The shadcn-svelte `Field.*` family gives forms their structure; do not rebuild it with raw layout wrappers and separately imported labels.

## Use `Field.*` for form structure

Import the field namespace and compose fields with it:

```svelte
<script lang="ts">
  import * as Field from '$lib/components/ui/field/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
</script>

<Field.Group>
  <Field.Field>
    <Field.Label for="email">Email</Field.Label>
    <Input id="email" name="email" type="email" />
    <Field.Description>Use your work email.</Field.Description>
    <Field.Error>Enter a valid email address.</Field.Error>
  </Field.Field>
</Field.Group>
```

Do not import `Label` directly for form layout when the project has shadcn-svelte `field` installed. `Field.Label`, `Field.Description`, `Field.Error`, `Field.Set`, and `Field.Group` keep spacing, semantics, and validation display consistent.

## Match the component to the semantic level

| Component | Use for |
|---|---|
| `Field.Group` | Overall form spacing or a stack of fields |
| `Field.Field` | One field/control row, including invalid state |
| `Field.Set` | A related group, like radios, checkboxes, or password fields |
| `Field.Legend` | Group label for a `Field.Set` |
| `Field.Label` | Label for a control, or clickable wrapper for option rows |
| `Field.Description` | Helper text |
| `Field.Error` | Validation message |

Use `Field.Set` for related controls rather than a plain `div` with a visual heading. Use `Field.Legend` for group labels when the label describes the set, not one control.

## Grouped options: label wraps field

For checkbox and radio cards, make each option's `Field.Label` wrap its `Field.Field`. This keeps the whole row clickable without inventing custom click handling.

```svelte
<script lang="ts">
  import { Checkbox } from '$lib/components/ui/checkbox/index.js';
  import * as Field from '$lib/components/ui/field/index.js';

  let selected = $state<string[]>([]);

  function toggle(id: string, checked: boolean) {
    if (checked) {
      selected.push(id);
    } else {
      selected = selected.filter((value) => value !== id);
    }
  }
</script>

<Field.Set>
  <Field.Legend>Events</Field.Legend>
  <Field.Description>Choose the events to notify you about.</Field.Description>

  <div class="grid gap-2">
    {#each options as option (option.id)}
      <Field.Label for="event-{option.id}">
        <Field.Field orientation="horizontal" class="justify-between hover:bg-muted/50">
          <div class="flex flex-col gap-0.5">
            <span class="text-sm font-medium">{option.label}</span>
            <span class="text-xs text-muted-foreground">{option.description}</span>
          </div>
          <Checkbox
            id="event-{option.id}"
            name="events"
            value={option.id}
            checked={selected.includes(option.id)}
            onCheckedChange={(checked) => toggle(option.id, checked === true)}
          />
        </Field.Field>
      </Field.Label>
    {/each}
  </div>

  <Field.Error>Select at least one event.</Field.Error>
</Field.Set>
```

The important shape is `Field.Set` → `Field.Label` → `Field.Field` → control. Avoid a clickable `div`, separate `Label` import, or custom row `onclick`.

## Radio groups use the same shape

```svelte
<script lang="ts">
  import * as Field from '$lib/components/ui/field/index.js';
  import * as RadioGroup from '$lib/components/ui/radio-group/index.js';

  let expiration = $state('7d');
</script>

<Field.Set>
  <Field.Legend>Expiration</Field.Legend>
  <RadioGroup.Root bind:value={expiration} class="grid grid-cols-3 gap-2">
    {#each options as option (option.value)}
      <Field.Label for="expiration-{option.value}">
        <Field.Field orientation="horizontal" class="justify-center hover:bg-muted/50">
          <RadioGroup.Item value={option.value} id="expiration-{option.value}" class="sr-only" />
          <span class="text-sm font-medium">{option.label}</span>
        </Field.Field>
      </Field.Label>
    {/each}
  </RadioGroup.Root>
</Field.Set>
```

## Validation display belongs on the field

When rendering server or client validation errors, attach invalid state to `Field.Field`, `aria-invalid` to the control, and the message to `Field.Error`.

```svelte
<Field.Field data-invalid={errors.email ? true : undefined}>
  <Field.Label for="email">Email</Field.Label>
  <Input
    id="email"
    name="email"
    type="email"
    aria-invalid={errors.email ? true : undefined}
  />
  {#if errors.email}
    <Field.Error>{errors.email}</Field.Error>
  {/if}
</Field.Field>
```

For SvelteKit form actions, server validation, `fail()`, and progressive enhancement, pair this component shape with the `sveltekit` forms-validation reference.

## Smells

- Raw `div` wrappers recreating `Field.Field` padding, border, spacing, or invalid styling.
- Importing `Label` directly for shadcn-svelte form layout instead of `Field.Label`.
- Checkbox/radio option rows with custom `onclick` instead of label-wrapped controls.
- A visible option card not connected to the input with `for`/`id`.
- Rendering validation text in arbitrary paragraphs instead of `Field.Error`.
- Putting invalid state only in color classes, without `aria-invalid` on the control.

## Installation check

If the project does not have the field component, add it with the project's package manager:

```bash
pnpm dlx shadcn-svelte@latest add field
```

Use the same import style as the project (`$lib/components/ui/field`, `$lib/components/ui/field/index.js`, or local aliases). Do not churn imports solely for style consistency unless the file already follows that convention.
