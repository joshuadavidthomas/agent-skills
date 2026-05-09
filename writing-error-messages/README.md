# Sources

## Source Inventory

| Source | Trust | Contribution | Constraints |
|--------|-------|--------------|-------------|
| [Wix UX: When life gives you lemons, write better error messages](https://wix-ux.com/when-life-gives-you-lemons-write-better-error-messages-46c5223e1a2f) | Medium-high | Defines bad patterns: cutesy tone, jargon, blame, unnecessary generic messages. Defines good patterns: what happened, why, reassurance, empathy, fix, way out. Emphasizes cross-functional error handling. | Product-experience article, not a formal design standard. Wix tone allows some "please" usage that stricter systems avoid. |
| [GOV.UK Design System: Error message](https://design-system.service.gov.uk/components/error-message/) | Very high | Validation-message guidance: explain what went wrong and how to fix it; use clear, concise, specific, plain English; avoid blame, jargon, "invalid", "sorry", and "please" in most validation copy. | Optimized for UK government services; stricter tone than some brands. |
| [GOV.UK Design System: Recover from validation errors](https://design-system.service.gov.uk/patterns/validation/) | Very high | Flow guidance: preserve input, show summaries, validate server-side, avoid premature validation, keep messages close to fields. | Mostly form-service guidance; less about system failures outside forms. |
| [Nielsen Norman Group: Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/) | Very high | Usability principles: visible, recognizable, close to problem, constructive, human-readable, nonjudgmental, accessible, avoid premature errors and humor. | Broad principles; exact wording must fit product voice and threat model. |
| [Atlassian Design: Error messages](https://atlassian.design/content/designing-messages/writing-error-messages) | High | Message anatomy: reason, problem, consequence, action, backup path; scannable titles; specific CTA verbs; avoid inventing unknown causes. | Atlassian tone discourages "please" and "sorry" more strongly than some brands. |
| [Microsoft Learn: Writing style for Windows apps](https://learn.microsoft.com/en-us/windows/apps/design/style/writing-style) | High | Friendly, helpful, concise product-writing guidance; app should not scare or blame users; tell what went wrong, what happens next, and what users can do. | Windows app context; use as general style guidance, not source for every platform pattern. |
| [Shopify Polaris: Error messages](https://polaris.shopify.com/content/error-messages) and [Inline error](https://polaris.shopify.com/components/inline-error) | High | Commerce/product examples: clear issue plus fix, exact numbers/dates/user data when useful, place errors close to fields, avoid "invalid", detailed next steps. | Merchant examples need generalization outside commerce. |
| [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet) | Very high | Security exception: auth and recovery messages must avoid account enumeration and sensitive-state disclosure; response details/timing can leak information. | Intentionally conflicts with generic UX advice to be specific. Security-sensitive flows require threat-model judgment. |
| [`writing-clearly-and-concisely`](../writing-clearly-and-concisely/SKILL.md) | High local | Existing repository prose guidance: active voice, positive form, concrete language, omit needless words. | General writing skill; does not handle error-specific security and product-recovery concerns. |

## Synthesis Decisions

- Decision: Make the skill about human-facing software error copy, including UI, forms, CLI, API, and support/retry messages.
  - Supported by: Wix, NN/g, Atlassian, Shopify, Microsoft.
  - Rejected alternative: Limit the skill to web forms only.
  - Reason: User requests for "error messages" commonly span product UI, command-line tools, and API/agent messages.

- Decision: Put the security/privacy exception in the main skill body, not only in provenance.
  - Supported by: OWASP.
  - Rejected alternative: Always require maximum specificity.
  - Reason: Authentication and recovery copy must sometimes be intentionally generic to prevent account enumeration and sensitive disclosure.

- Decision: Include a "When Asked for a Generic Error" challenge section.
  - Supported by: Wix's cross-functional process and CEO quote that generic errors are often product/development failures.
  - Rejected alternative: Treat generic fallback copy as a normal default.
  - Reason: Agents otherwise comply with requests for generic copy without asking whether the system can expose safer, more useful state.

- Decision: Use "what happened / reassurance / why / next action / way out" as the core pattern.
  - Supported by: Wix, Atlassian, Microsoft, Shopify, NN/g.
  - Rejected alternative: A rigid template requiring every slot.
  - Reason: Short validation errors and high-security flows should omit slots that do not apply.

- Decision: Prefer non-blaming phrasing over universal active voice.
  - Supported by: GOV.UK, NN/g, Shopify, Atlassian.
  - Rejected alternative: Require active voice everywhere.
  - Reason: Passive or noun-phrase copy can avoid blaming the reader in field-level messages.

## Coverage and Gaps

- Covered: product failure notifications, form validation, generic fallback copy, auth/account-recovery copy, CLI/developer-facing errors, support/retry paths.
- Gaps: localization/internationalization rules, legal/regulatory copy review, medical/financial high-stakes domain-specific constraints, detailed accessibility implementation.
- Needs validation: real activation behavior against prompts that ask for "toast copy", "empty states", "validation errors", and "CLI error wording".

## Change Log

- 2026-05-08: Created initial source-backed skill from Wix UX article plus GOV.UK, NN/g, Atlassian, Microsoft, Shopify, OWASP, and local writing guidance.
