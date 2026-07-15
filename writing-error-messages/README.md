# writing-error-messages

An agent skill for writing and reviewing human-facing software error messages.

It helps agents replace vague, blamey, or unsafe error copy with messages that explain what happened, preserve trust, and tell the reader what to do next.

## When to use

Use this skill for:

- Product UI errors: banners, modals, toasts, inline failures, error states
- Form validation: missing fields, format errors, constraints, summaries
- Auth and account recovery: login failures, password reset, account activation
- Empty states that are often mistaken for errors
- Retry and support copy: request IDs, support paths, fallback actions
- CLI and developer-facing errors humans need to act on
- API errors that surface directly to people, support teams, or integrators

## Structure

- `SKILL.md` — core runtime guidance: message shape, validation rules, accessibility/placement notes, security/privacy gate, CLI error patterns, and questions to ask before accepting a generic fallback
- `references/source-backed-patterns.md` — source-backed notes from Wix, GOV.UK, Nielsen Norman Group, Atlassian, Microsoft, Shopify, and OWASP
- `references/rewrite-examples.md` — before/after examples and holdout checks for testing future changes

## Core idea

Good error messages answer the reader's immediate questions:

1. What happened?
2. Did I lose anything or create a duplicate?
3. Why did this happen, if it is known and safe to say?
4. What can I do next?
5. What happens if I do nothing?
6. Where can I get help if the fix does not work?

The important exception is security-sensitive copy. In login, password reset, account creation, permission, privacy, fraud, and abuse-prevention flows, more detail can make the product less safe. Those messages should avoid revealing account state, private resource details, or system internals.

## References

This skill synthesizes guidance from:

- [Wix UX: When life gives you lemons, write better error messages](https://wix-ux.com/when-life-gives-you-lemons-write-better-error-messages-46c5223e1a2f)
- [GOV.UK Design System: Error message](https://design-system.service.gov.uk/components/error-message/)
- [GOV.UK Design System: Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/)
- [Nielsen Norman Group: Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- [Atlassian Design: Error messages](https://atlassian.design/content/designing-messages/writing-error-messages)
- [Microsoft Learn: Writing style for Windows apps](https://learn.microsoft.com/en-us/windows/apps/design/style/writing-style)
- [Shopify Polaris: Error messages](https://polaris.shopify.com/content/error-messages)
- [Shopify Polaris: Inline error](https://polaris.shopify.com/components/inline-error)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet)
- [`writing`](../writing/SKILL.md), for general prose discipline

## Scope boundary

This skill covers error-message writing patterns. It does not replace product analytics, engineering error mapping, accessibility implementation details for a specific framework, localization review, legal review, or a threat model for high-risk security flows.
