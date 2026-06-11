# Plan Template

Every plan is written for an executor with **zero context**: it has not seen the planning session, the codebase exploration, or any sibling plan. Assume it is competent at following explicit instructions and weak at filling gaps, recovering from ambiguity, or knowing when to stop.

Three properties make a plan executable:

1. **Self-contained context** — everything needed is in the file: paths, current-state excerpts, conventions with exemplars, exact commands.
2. **Verification gates** — every step ends with a command and its expected result. The executor never judges whether it succeeded.
3. **Boundaries and escape hatches** — explicit out-of-scope list, and STOP conditions instead of improvisation when reality doesn't match the plan.

Plans specify intent, not implementations. Name what must be true and which files/symbols change. Sketches, pseudocode, signatures, and type shapes are welcome — they pin down intent without pretending to be final code. Don't default to full prose-written implementations (never compiled, stale mid-effort, copied verbatim even when wrong) — but when something must be done one specific way, or the executor plausibly won't get there from intent alone, write it out, anchored to an exemplar `file:line` where one exists.

---

## Template

```markdown
# Plan NNN: <Imperative title — what will be true after this plan lands>

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on.
> If anything in "STOP conditions" occurs, stop and write a handback —
> do not improvise. When done, update this plan's status row in the
> effort README (if one exists).
>
> **Drift check (run first)**: <repo-VCS command diffing the in-scope
> paths from the planned-at revision to the working copy>
> If in-scope files have changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Effort**: S | M | L
- **Risk**: LOW | MED | HIGH
- **Depends on**: NNN-<slug>.md (or "none")
- **Planned at**: revision `<id>`, <YYYY-MM-DD>

## Why this matters

2–5 sentences: the problem, its concrete cost, and what improves when this
lands. Intent is what lets the executor make a correct judgment call when a
detail is off.

## Current state

The facts the executor needs, inlined — never "as discussed":

- The relevant files, each with one line on its role.
- Short excerpts of the code as it exists today (with `file:line` markers),
  enough to confirm it's looking at the right thing.
- The conventions that apply, each with one exemplar:
  "Error handling follows the Result pattern — see `src/lib/result.ts` and
  its use in `src/users/api.ts:40-60`. Match it."

## Commands you will need

| Purpose   | Command          | Expected on success |
|-----------|------------------|---------------------|
| Tests     | `<exact command>`| all pass            |
| Lint      | `<exact command>`| exit 0              |

(Verified during recon, not guessed.)

## Scope

**In scope** (the only files you should modify):
- `path/to/file.ext`

**Out of scope** (do NOT touch, even though they look related):
- `path/to/other.ext` — <one line on why>

## Steps

### Step 1: <imperative title>

What must be true after this step, precisely. Exact files and symbols. A
code shape only if it pins down something ambiguous.

**Verify**: `<command>` → <expected output>

### Step 2: ...

(Each step independently verifiable. Order steps so the codebase is never
broken between them when possible — add the new path, switch callers, then
remove the old path.)

## Test plan

- New tests to write, in which file, covering which cases (list them).
- Which existing test to use as the structural pattern.
- **Verify**: `<test command>` → all pass, including the new tests.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `<command>` → <expected>
- [ ] No files outside the in-scope list are modified

## STOP conditions

Stop if:

- The code at the "Current state" locations doesn't match the excerpts.
- A step's verification fails twice after a reasonable fix attempt.
- The work appears to require touching an out-of-scope file.
- You hit a design fork this plan didn't anticipate.
- The assumption "<key assumption>" turns out to be false.

On stopping, write a **handback** for the planning agent instead of
improvising: the current state of the work, the desired outcome, and any
lingering questions. Descriptive, not prescriptive — describe the fork, do
not pick the branch.

## Maintenance notes

For whoever owns this code after the change lands: what future changes will
interact with it, what a reviewer should scrutinize, and any follow-up
deliberately deferred (and why).
```

---

## Quality bar — check before finishing each plan

- Could a model that has never seen this repo execute this with only the plan file and the repo? If any step needs knowledge from the planning session, inline it.
- Is every verification a command with an expected result, not a judgment ("make sure it works")?
- Does every step name exact files and symbols, not "the relevant module"?
- Are the STOP conditions specific to this plan's actual risks, not boilerplate?
- Is every full-fidelity code block earning its place? Sketches and pseudocode are fine anywhere; exact code should be there because the executor needs that exact shape, not because it was easy to write.
- "Planned at" is filled in and the drift-check paths match the Scope section.
- No secret values anywhere — locations and credential types only.
