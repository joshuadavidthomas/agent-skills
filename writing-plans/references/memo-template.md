# Memo Template

A memo answers a design fork that surfaced during execution (usually via an executor's handback) or late in planning. It is the planner's researched verdict, written so the affected plans can be spawned or amended from it — and so nobody re-litigates the fork later.

File: `memo-<slug>.md`, alongside the plans it informs.

```markdown
# Memo: <the fork, as a question or short noun phrase>

**Verdict**: <one or two sentences — the decision, stated first.>
**Informs**: plan NNN (amended) / plan NNN (new)
**Written at**: revision `<id>`, <YYYY-MM-DD>

## The fork

<What question came up and where it surfaced — quote or summarize the
handback: current state, desired outcome, the open questions.>

## Evidence

<The research that decides it. Every claim grounded with `file:line`
references in the current tree, or external sources with verified
citations. This section is why the memo exists — a verdict without
evidence is just a vibe.>

## Recommended shape

<The decided direction in enough detail to amend or spawn plans: what must
be true, which files/symbols, exemplars to match. Intent over prescription,
same as plans — code shapes only when load-bearing.>

## Rejected alternatives

- <alternative>: rejected because <evidence-backed one-liner>.
```

After writing the memo: spawn or amend the affected plans, re-anchor their drift checks if the tree moved, and add a reconciliation-log entry in the effort index linking the memo.
