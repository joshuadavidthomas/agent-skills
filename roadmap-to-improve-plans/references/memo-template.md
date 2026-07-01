# Memo Template

Use a memo when execution or planning exposes an audit or architecture fork that should not be improvised inside an implementation plan. A memo should answer the fork, preserve the evidence, and update the affected plans.

```markdown
# Memo: <Decision/Fork Title>

**Verdict:** <decision first, in one or two sentences>
**Related plan:** <NNN-title>
**Audit category:** <category>
**Date:** <date>
**Status:** Proposed | Accepted | Rejected | Superseded

## Fork

<What the executor or planner discovered and why the original plan is insufficient.>

## Evidence

- `path:line-line` — <fact>
- `<command>` — <result>

## Architecture Diagnosis

Include for architecture forks; otherwise use “N/A”.

- **Current friction:** <what is costly now>
- **Deepening direction:** <module/interface/depth/seam/adapter/leverage/locality direction>
- **Deletion test:** <result>
- **Recommendation strength:** Strong / Worth exploring / Speculative

## Rejected Alternatives

- <alternative> — <why rejected, with evidence>

## Plan Updates Required

- <plan/index changes to make after decision>
```
