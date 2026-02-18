# SvelteKit Forms with Validation

Server-first validation with progressive enhancement. Schema defined once, server validates, client displays errors.

## Pattern Overview

1. **Define schema once** in `$lib/schemas/` 
2. **Server validates** with `extractFormData()` utility
3. **Return field errors** via `fail()` with field-keyed errors
4. **Client displays** with `FormErrors` class — reactive errors with optimistic clearing
5. **Progressive enhancement** — works without JavaScript

## Schema Definition

```typescript
// $lib/schemas/profile.ts
import * as v from 'valibot';

export const ProfileSchema = v.object({
  name: v.pipe(v.string(), v.trim(), v.minLength(1, 'Name is required.')),
  email: v.pipe(v.string(), v.trim(), v.toLowerCase(), v.email('Invalid email.')),
});

export type ProfileInput = v.InferInput<typeof ProfileSchema>;
```

### Cross-Field Validation (Passwords Match)

Use `v.forward()` to route cross-field errors to specific fields:

```typescript
// $lib/schemas/password.ts
export const ChangePasswordSchema = v.pipe(
  v.object({
    currentPassword: v.pipe(v.string(), v.minLength(1, 'Required.')),
    newPassword: v.pipe(v.string(), v.minLength(8, 'Min 8 characters.')),
    confirmPassword: v.pipe(v.string(), v.minLength(1, 'Required.')),
  }),
  v.forward(
    v.check((input) => input.newPassword === input.confirmPassword, 'Passwords do not match.'),
    ['confirmPassword']
  )
);
```

## Form Data Extraction Utility

Reusable utility that extracts formData and validates against schema:

```typescript
// $lib/server/forms.ts
import { dev } from '$app/environment';
import * as v from 'valibot';

export type FormResult<T> = {
  data: T | undefined;
  errors: Record<string, string> | null;
};

export const extractFormData = async <TInput = unknown, TOutput = TInput>(
  request: Request,
  schema: v.BaseSchema<TInput, TOutput, v.BaseIssue<unknown>>
): Promise<FormResult<TOutput>> => {
  try {
    const formData = await request.formData();
    const result: Record<string, unknown> = {};

    formData.forEach((value, key) => {
      if (result[key] === undefined) {
        result[key] = value;
      } else if (Array.isArray(result[key])) {
        (result[key] as unknown[]).push(value);
      } else {
        result[key] = [result[key], value];
      }
    });

    const validation = v.safeParse(schema, result);

    if (!validation.success) {
      if (dev) {
        console.error('Validation errors:');
        for (const issue of validation.issues) {
          console.error(`- ${issue.path?.[0]?.key}: ${issue.message}`);
        }
      }

      const errors: Record<string, string> = {};
      for (const issue of validation.issues) {
        const path = issue.path?.[0]?.key;
        if (path && typeof path === 'string' && !errors[path]) {
          errors[path] = issue.message;
        }
      }

      if (Object.keys(errors).length === 0 && validation.issues.length > 0) {
        errors._form = validation.issues.map((i) => i.message).join(', ');
      }

      return { data: undefined, errors };
    }

    return { data: validation.output as TOutput, errors: null };
  } catch (error) {
    if (dev) {
      console.error(`Error extracting form data: ${error}`);
    }
    return { data: undefined, errors: { _form: `Error processing form: ${error}` } };
  }
};
```

## Server Action

```typescript
// +page.server.ts
import { fail } from '@sveltejs/kit';
import { extractFormData } from '$lib/server/forms';
import { ProfileSchema } from '$lib/schemas/profile';

export const actions = {
  save: async ({ request }) => {
    const { data, errors } = await extractFormData(request, ProfileSchema);

    if (errors || !data) {
      return fail(400, { ok: false, errors });
    }

    // data is fully typed as ProfileInput
    await saveProfile(data);

    return { ok: true };
  },
};
```

## Client — FormErrors Class

Reactive error state with optimistic clearing. Errors show after submit, clear when user types:

```typescript
// $lib/forms/form-errors.svelte.ts
export class FormErrors {
  #cleared = $state<string[]>([]);
  #getServerErrors: () => Record<string, string | undefined> | null | undefined;

  constructor(getServerErrors: () => Record<string, string | undefined> | null | undefined) {
    this.#getServerErrors = getServerErrors;
  }

  readonly errors = $derived.by(() => {
    const serverErrors = this.#getServerErrors() ?? {};
    return Object.fromEntries(
      Object.entries(serverErrors).filter(([key]) => !this.#cleared.includes(key))
    ) as Record<string, string>;
  });

  clear = (e: Event) => {
    const name = (e.currentTarget as HTMLInputElement).name;
    if (!this.#cleared.includes(name)) {
      this.#cleared = [...this.#cleared, name];
    }
  };

  reset = () => {
    this.#cleared = [];
  };
}
```

Usage:

```svelte
<script lang="ts">
  import { enhance } from '$app/forms';
  import { FormErrors } from '$lib/forms';
  import * as Field from '$lib/components/ui/field';
  import { Input } from '$lib/components/ui/input';
  import { Button } from '$lib/components/ui/button';

  let { form } = $props();

  const formErrors = new FormErrors(() => form?.errors);
</script>

<form method="POST" action="?/save" use:enhance={() => { formErrors.reset(); }}>
  {#if formErrors.errors._form}
    <div class="error">{formErrors.errors._form}</div>
  {/if}

  <Field.Field data-invalid={formErrors.errors.name ? true : undefined}>
    <Field.Label for="name">Name</Field.Label>
    <Input
      id="name"
      name="name"
      aria-invalid={formErrors.errors.name ? true : undefined}
      oninput={formErrors.clear}
    />
    {#if formErrors.errors.name}
      <Field.Error>{formErrors.errors.name}</Field.Error>
    {/if}
  </Field.Field>

  <Field.Field data-invalid={formErrors.errors.email ? true : undefined}>
    <Field.Label for="email">Email</Field.Label>
    <Input
      id="email"
      name="email"
      type="email"
      aria-invalid={formErrors.errors.email ? true : undefined}
      oninput={formErrors.clear}
    />
    {#if formErrors.errors.email}
      <Field.Error>{formErrors.errors.email}</Field.Error>
    {/if}
  </Field.Field>

  <Button type="submit">Save</Button>
</form>
```

This gives good UX without client-side validation:
- Errors show after submit (from server)
- Errors clear when user starts fixing the field
- Next submit brings back any remaining errors

## Grouped Fields with Field.Set

For related fields like password confirmation, use `Field.Set` to group them:

```svelte
<Field.Set>
  <Field.Group>
    <Field.Field data-invalid={formErrors.errors.newPassword ? true : undefined}>
      <Field.Label for="new-password">New password</Field.Label>
      <Input id="new-password" name="newPassword" type="password" oninput={formErrors.clear} />
      <Field.Description>Must be at least 8 characters.</Field.Description>
      {#if formErrors.errors.newPassword}
        <Field.Error>{formErrors.errors.newPassword}</Field.Error>
      {/if}
    </Field.Field>

    <Field.Field data-invalid={formErrors.errors.confirmPassword ? true : undefined}>
      <Field.Label for="confirm-password">Confirm password</Field.Label>
      <Input id="confirm-password" name="confirmPassword" type="password" oninput={formErrors.clear} />
      {#if formErrors.errors.confirmPassword}
        <Field.Error>{formErrors.errors.confirmPassword}</Field.Error>
      {/if}
    </Field.Field>
  </Field.Group>
</Field.Set>
```

The `v.forward()` in the schema routes the "Passwords do not match" error to `confirmPassword`.

## Optional: Blur Validation for Instant Feedback

If you need instant feedback (rare), add client-side blur validation:

```svelte
<script lang="ts">
  import * as v from 'valibot';
  import { FormErrors } from '$lib/forms';

  let { form } = $props();

  const formErrors = new FormErrors(() => form?.errors);

  // Client-side field errors (for blur validation)
  let clientErrors = $state<Record<string, string | null>>({});

  // Merge: client errors take precedence when present
  const errors = $derived({ ...formErrors.errors, ...clientErrors });

  // Field schemas for blur validation
  const fieldSchemas = {
    name: v.pipe(v.string(), v.trim(), v.minLength(1, 'Name is required.')),
    email: v.pipe(v.string(), v.trim(), v.email('Invalid email.')),
  };

  function validateField(field: keyof typeof fieldSchemas, value: string) {
    if (!value) {
      clientErrors[field] = null;
      return;
    }
    const result = v.safeParse(fieldSchemas[field], value);
    clientErrors[field] = result.success ? null : result.issues[0].message;
  }
</script>

<Input
  id="name"
  name="name"
  oninput={formErrors.clear}
  onblur={(e) => validateField('name', e.currentTarget.value)}
/>
```

## Key Points

- **Server is source of truth** — client validation is optional UX enhancement
- **Progressive enhancement** — forms work without JavaScript
- **`extractFormData()` returns typed data** — or field-keyed errors
- **`FormErrors` class** — reactive errors with optimistic clearing on input
- **`_form` key for general errors** — not tied to specific field
- **`data-invalid` on Field.Field** — triggers error styling
- **`aria-invalid` on inputs** — accessibility
- **`v.forward()` routes errors** — cross-field validation to specific fields
- **Conditionally render `Field.Error`** — prevents layout shift when errors clear

## Zod Equivalent

```typescript
import { z } from 'zod';

export const ProfileSchema = z.object({
  name: z.string().trim().min(1, 'Name is required.'),
  email: z.string().trim().email('Invalid email.'),
});

export const ChangePasswordSchema = z
  .object({
    currentPassword: z.string().min(1, 'Required.'),
    newPassword: z.string().min(8, 'Min 8 characters.'),
    confirmPassword: z.string().min(1, 'Required.'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match.',
    path: ['confirmPassword'],
  });

// In extractFormData, use schema.safeParse() instead of v.safeParse()
```
