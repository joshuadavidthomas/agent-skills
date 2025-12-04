# Research Document Format

Use this template when saving research to a file.

## Before Writing

Check if the target directory exists:
- Project: `.research/`
- Global: `~/.research/`

Create the directory if it doesn't exist before writing.

## Gathering Metadata

Run the `gather-metadata.py` script to get deterministic metadata. Output is key-value pairs: `date`, `filename_date`, `cwd`, `repository`, `branch`, `commit`.

Add `query` (from user's question) and `tags` (3-6 relevant keywords from content).

## Frontmatter Spec

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| date | ISO 8601 string | When research was conducted | `gather-metadata.py` script |
| query | string | Original research question | From user's prompt |
| repository | string (URL) | Full repo URL | `gather-metadata.py` script |
| branch | string | Git branch at time of research | `gather-metadata.py` script |
| commit | string | Short commit hash | `gather-metadata.py` script |
| cwd | string | Working directory | `gather-metadata.py` script |
| tags | string array | Keywords for searching | Agent determines from content |

## Template

```yaml
---
date: YYYY-MM-DDTHH:MM:SS+TZ
query: "[Original user question]"
repository: [git remote URL or null]
branch: [git branch or null]
commit: [short hash or null]
cwd: [working directory path]
tags: [relevant, keywords, here]
---
```

# Research: [Topic]

## Summary

[2-3 sentence answer to the question]

## Detailed Findings

### [Component/Area 1]

- Finding with reference (`file.ts:123`)
- How it connects to other components

### [Component/Area 2]

...

## Code References

Key locations for future reference:

- `path/to/file.py:45` - Description
- `another/file.ts:12-30` - Description

## Open Questions

[Areas that need further investigation, if any]

## File Naming

Format: `YYYY-MM-DD_topic-slug.md`

Examples:
- `2025-01-15_authentication-flow.md`
- `2025-01-15_payment-webhook-handling.md`

Keep slugs short and descriptive. Use hyphens, lowercase.

## Location Options

Ask user preference when saving:

| Location | Use For |
|----------|---------|
| `.research/` | Project-specific research (may be committed or gitignored) |
| `~/.research/` | Cross-project knowledge, general patterns |

## When to Skip

Don't offer to save for:
- Quick "where is X" answers
- Simple factual responses
- Answers under ~200 words

Do offer to save for:
- Multi-component analysis
- Architectural research
- Anything the user might want to reference later
