# Effort Index Template

Written once after the plans, updated as the effort progresses. The index owns exactly four things — goal, status table, dependency notes, and a bounded log. Detail that lives elsewhere (plan files, VCS history, PR descriptions) is linked, never repeated.

```markdown
# <Effort title>

<One paragraph: the goal of this effort, the source material it was planned
from (linked), and the planned-at revision. If the plans cleave into tracks,
name them and why they're sequenced as they are.>

Execute in the order below unless dependencies say otherwise. Each executor:
read the plan fully before starting, honor its STOP conditions, and update
your row when done.

## Execution order & status

(Recommended execution order — may diverge from numeric order; numbers are
never reused or renumbered.)

| Plan | Title | Effort | Depends on | Status |
|------|-------|--------|------------|--------|
| [001](001-<slug>.md) | ... | S | — | TODO |
| [002](002-<slug>.md) | ... | M | 001 | TODO |

Status values: TODO | IN PROGRESS | DONE | BLOCKED (one-line reason) |
SUPERSEDED (one-line pointer to what replaced it)

## Dependency notes

- **001 → 002**: <one or two lines on why the edge exists>.

## Reconciliation log

Newest first. **A few lines per entry, hard cap** — date, what happened,
PR/commit link, deviations worth knowing, next executable plan. No
validation transcripts ("validation passed per the plan's done criteria"
plus the PR link covers it). Anything a *future* plan's executor needs goes
in that plan's file, not here.

- **YYYY-MM-DD**: Plan 001 closed — PR #123. Deviation: <one line>.
  Next: 002.
- **YYYY-MM-DD**: Handback on plan 002 → [memo-<slug>.md](memo-<slug>.md);
  plan 004 added, plan 002 amended.

## Considered and rejected

(So nobody re-plans these.)

- <approach or sub-task>: not done because <one line>.

## Deferred

- <real, but not planned — one line each, with where it's noted>.
```
