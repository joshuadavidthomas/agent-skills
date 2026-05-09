# Source-Backed Patterns

Open this when you need source rationale, need to resolve a wording tradeoff, or are auditing a set of error messages.

## Shared Pattern Across Sources

Most sources converge on this shape:

1. Say what happened in user terms.
2. Explain the consequence: saved, not saved, sent, not sent, charged, not charged, unchanged.
3. Give the reason when known and safe.
4. Give a specific next action.
5. Provide a backup path if the fix may fail.
6. Avoid blame, jargon, jokes, and vague CTAs.

Use the full shape for product failures. Use shorter versions for field validation and security-sensitive flows.

## Wix UX

Use for product-failure messages and cross-functional error audits.

Key patterns:

- Bad errors use cutesy tone, technical jargon, blame, or unnecessary generic copy.
- Good errors say what happened and why, reassure the user, show empathy, help them fix it, and give a way out.
- Generic errors are often product or engineering failures, not just writing problems.
- Ask product/engineering what triggered the error and what the user can do.

Useful rewrite direction:

```text
Bad: Whoops! Something went wrong. The third party isn't responding, so we can't fetch your data. Try again later.
Better: Unable to connect your account. Your changes were saved, but we couldn't connect the account because of an issue on our end. Try connecting again. If this keeps happening, contact support.
```

## GOV.UK Design System

Use for form validation, service flows, and accessibility-conscious web UI.

Key patterns:

- Explain what went wrong and how to fix it.
- Match error language to the question or label.
- Use clear, concise, specific, plain English.
- Put errors near fields and include an error summary for forms.
- Preserve user-entered values.
- Avoid premature validation.
- Avoid words such as "forbidden", "illegal", "valid", "invalid", "you forgot", "oops", "sorry", and usually "please".

Good validation patterns:

```text
Enter your National Insurance number
Enter a date in the past
Enter how many hours you work a week
```

Avoid:

```text
Invalid value
This field is required
You forgot to enter your details
```

## Nielsen Norman Group

Use for usability checks and interaction placement.

Key patterns:

- Make errors visible, recognizable, and close to the source.
- Do not rely on color alone.
- Use human-readable language; keep codes as supplemental diagnostics.
- Offer constructive remedies, not just failure statements.
- Avoid blaming users with words like "invalid", "illegal", or "incorrect" when a more helpful fix exists.
- Avoid humor, especially for repeated or high-stakes errors.
- Preserve input and reduce correction effort.

## Atlassian Design

Use for SaaS/product UI messages, toasts, modals, and banners.

Key patterns:

- Explain what happened, the consequence, and how to move forward.
- Include reason, problem, action, and consequence when relevant.
- Do not invent a reason if the system does not know one.
- Keep body copy to 1-2 sentences.
- Use short, scannable titles.
- Use specific CTAs such as "Retry", "Update details", or "Contact support" instead of "OK".
- Prefer "we" over "you" when "you" would imply blame.
- Give the simplest likely fix first, then a backup path.

## Microsoft Learn

Use for friendly, concise app-writing tone.

Key patterns:

- Be friendly, helpful, and concise.
- Do not scare or blame users.
- The app should take responsibility where appropriate.
- Tell users what went wrong, what happens next, and what they can realistically do.
- Reassure users when their data remains available.

Useful pattern:

```text
We couldn't upload the picture. If this happens again, try restarting the app. Your picture will be waiting when you come back.
```

## Shopify Polaris

Use for commerce/product admin flows and inline errors.

Key patterns:

- Make clear what went wrong and how to fix it.
- Be specific with exact numbers, dates, or user data when useful.
- Place inline errors close to what needs fixing.
- Remove inline errors when fixed.
- Use passive voice when it avoids blaming the user.
- Explain backend details only when useful or when no direct fix exists.

Useful patterns:

```text
To save this product, make 2 changes: Enter title; Add weight
Store name is required
Couldn't deposit payout. The bank account we have on file was closed. Update your details, and we'll retry automatically.
```

## OWASP Authentication Cheat Sheet

Use for authentication, password reset, registration, account state, permissions, fraud, and abuse-prevention flows.

Key patterns:

- Do not reveal whether the user ID, email, password, account existence, lock status, or disabled status caused the failure.
- Keep response bodies, status behavior, timing, and other observable signals consistent enough not to leak account state.
- Provide a safe support or recovery path instead of a specific hidden-state explanation.

Safe patterns:

```text
Invalid email or password
If an account exists for that email address, we'll send password reset instructions.
A link to activate your account has been emailed to the address provided.
```

Avoid:

```text
That email exists, but the password is wrong
No account found for this email
This account is locked
```

## Conflict Resolution

When sources disagree:

- Security beats specificity.
- Accessibility and recovery beat brand voice.
- Known facts beat invented causes.
- High-stakes contexts beat humor and warmth.
- Field-level validation can be shorter than product-failure copy.
- Developer-facing errors can include technical details when the reader can act on them.
