This repository is the source of truth for @joshuadavidthomas's reusable agent skills.

## Editing rule

When working in this repository, edit the skill files in this repository only.

Do not edit installed copies under `~/.agents/skills/`, `~/.pi/agent/skills/`, or any other runtime-installed skill directory unless the user explicitly asks to modify the installed copy.

If an installed copy differs from this repository, treat this repository as canonical. Make changes here first, then ask before syncing or copying changes to an installed location.

## Skill README convention

Skill `README.md` files are human-facing orientation pages, not hidden runtime instruction or synthesis scratchpads.

When adding or updating a skill README, follow the style of existing skill READMEs in this repository: briefly explain what the skill is, when to use it, what files/references it contains, attribution/source notes when relevant, and scope boundaries when useful.

Do not dump skill-authoring provenance templates into a skill README by default. Avoid sections like "Synthesis Decisions", "Coverage and Gaps", "Needs validation", "Maintenance Notes", or "Change Log" unless the existing README already uses that maintainer-record style or the user explicitly asks for it.

Put detailed source summaries, rationale, examples, tradeoffs, and regression cases in focused `references/` files linked from `SKILL.md` or the README.
