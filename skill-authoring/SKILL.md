---
name: skill-authoring
description: Use when authoring, creating, refining, or troubleshooting agent skills — covers SKILL.md structure, frontmatter syntax, description optimization, and activation testing. Also when building a new skill from scratch, when a skill won't trigger, loads incorrectly, or the agent ignores it entirely. Use when a skill misbehaved in the current session and needs adjustment based on learnings.
---

# Skill Authoring

Use this skill when creating, synthesizing, testing, debugging, or refining agent skills. Route to the matching workflow file below; handle trivial edits inline.

Primary success condition: the resulting skill triggers reliably, gives the agent only the guidance it needs, and is backed by evidence where domain accuracy matters.

Agents discover skills from frontmatter first: `name` and `description` are visible before the body loads. The body loads only after the description matches the task. References, scripts, and assets load only when needed. Write for that loading order.

## Choose the Path

| If the task is... | Do this |
|-------------------|---------|
| Create a small skill from scratch | Read [workflows/create.md](workflows/create.md) |
| Build from docs, project history, examples, failures, or multiple sources | Read [workflows/synthesize.md](workflows/synthesize.md) |
| Check whether a skill activates and behaves correctly | Read [workflows/test.md](workflows/test.md) |
| Diagnose a skill that will not trigger or is ignored | Read [workflows/debug.md](workflows/debug.md) |
| Improve a skill from a concrete session failure | Read [workflows/refine.md](workflows/refine.md) |
| Look up authoring patterns | Read [references/patterns.md](references/patterns.md) |
| Compare good and bad examples | Read [references/examples.md](references/examples.md) |
| Check detailed rules by impact | Read [references/rules.md](references/rules.md) |
| Verify format constraints | Read [spec/specification.md](spec/specification.md) |

Load only the files needed for the current path. Do not read every reference by default.

## Inline Fallback

For small edits that do not need a workflow file:

1. Inspect the existing skill and repository conventions.
2. Make the smallest change that fixes the issue.
3. Validate structure and, when relevant, activation behavior.
4. Report what changed and any open gaps.

Use a workflow file for anything broader than a localized edit.

## Cardinal Rules

| Rule | Why It Matters |
|------|----------------|
| Description has trigger keywords | Without them, the skill never activates |
| Description names capabilities and activation conditions, not steps | Agents may follow description shortcuts instead of loading the body |
| Description uses third person | It is injected as metadata, not spoken by the agent |
| Name matches directory | Required for skill loading |
| Critical instructions appear early | Long content may be skipped or deemphasized |
| `SKILL.md` stays lean | Runtime context is limited |
| References are directly linked from `SKILL.md` | Hidden chains are easy to miss |
| Source-backed guidance beats vibes | Real docs, history, fixes, and failures improve accuracy |
| Precision before addition | More files and prose often reduce reliability |
| Test activation before deployment | A skill that works but never triggers has zero value |
| Use agent-agnostic language by default | Skills should port across LLM agents unless intentionally provider-specific |

## Skill Shape

```
skill-name/
├── SKILL.md              # Required entry point
├── SOURCES.md            # Optional maintainer provenance for synthesized skills
├── references/           # Optional focused docs loaded on demand
├── scripts/              # Optional executable helpers
└── assets/               # Optional templates, schemas, images, static files
```

Use this placement model:

| Content | Put it in |
|---------|-----------|
| Frontmatter and core instructions | `SKILL.md` |
| Detailed optional guidance the agent may need | `references/*.md` |
| Deterministic repeatable operations | `scripts/*` |
| Templates, schemas, static examples | `assets/*` |
| Source inventory, trust level, decisions, gaps, changelog | `SOURCES.md` |

Provenance belongs in `SOURCES.md` unless the agent needs it to perform the task.

## Description Requirements

The description decides whether the skill ever loads. Write it for discovery.

Use this formula:

```yaml
description: Use when [triggering conditions] — [specific capabilities]. Handles [file types, contexts, symptoms, synonyms].
```

Good:

```yaml
description: Use when working with PDF files — extracts text, fills forms, merges documents. Handles .pdf files, scanned PDFs, and form fields.
```

Bad:

```yaml
description: Processes PDFs by first extracting text, then analyzing structure, then outputting results.
```

Include:

- words users actually say
- file types and extensions
- error messages or symptoms
- synonyms and alternate phrasings
- negative/positive trigger distinctions when false positives matter

Exclude:

- step-by-step workflow summaries
- implementation details
- first-person language
- generic claims like "helps with documents"

## Runtime Body Requirements

Write for an agent that can already reason. Do not teach basics. Provide constraints and examples.

Use this structure by default:

1. **Route**: choose path or mode quickly.
2. **Instruct**: imperative steps and decision points.
3. **Show**: one excellent concrete example or template.
4. **Warn**: common mistakes, rationalizations, false positives, or edge cases.
5. **Validate**: exact checks or expected evidence.

Prefer tables, checklists, templates, and input/output examples over explanatory prose.

## Progressive Disclosure

| Layer | What | When Loaded | Target |
|-------|------|-------------|--------|
| 1 | `name` + `description` | Always | Trigger-rich, concise |
| 2 | `SKILL.md` body | When skill triggers | Path choice + core rules |
| 3 | `references/`, `scripts/`, `assets/` | On demand | Focused leaves with direct reasons |

Split content when:

- `SKILL.md` is becoming an encyclopedia
- guidance is optional or domain-specific
- a reference has a clear "open when..." reason
- scripts can make a fragile task deterministic

Do not split content just to look organized.

## Tooling

Scaffold a skill:

```bash
python scripts/init.py my-skill
python scripts/init.py my-skill --router
```

Validate a skill:

```bash
./scripts/validate.sh path/to/skill
```

Or use the official validator:

```bash
pip install skills-ref
skills-ref validate path/to/skill
```

Validation checks structure. It does not prove description quality, source coverage, or behavioral reliability.

## Source Material

The `sources/` directory contains complete skill-authoring approaches from different authors, preserved for deeper study:

| Source | Approach |
|--------|----------|
| `sources/anthropic/` | Official Anthropic skill-creator with init/package scripts |
| `sources/obra/` | TDD-based methodology with pressure testing |
| `sources/everyinc/` | Router patterns and workflow templates |
| `sources/pproenca/` | Granular rules organized by impact level |
| `sources/pytorch/` | Simple single-file approach |
| `sources/getsentry/` | Source-backed skill synthesis, provenance, precision passes, and router-style skill-writer patterns |

For this skill's own provenance and synthesis decisions, read [SOURCES.md](SOURCES.md).

## Output Format

When modifying or reviewing a skill, return a summary, changes made or findings, validation results, and any open gaps.
