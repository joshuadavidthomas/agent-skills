# History Rewriting and Investigation

Rewriting history and investigating past changes in jj. Covers squashing, absorbing, rebasing, splitting commits (agent-safe), conflict resolution, investigating history, and cleanup.

**Target version: jj 0.36+**

For full references, see:
- [references/conflicts.md](references/conflicts.md) — Conflict handling details and marker formats
- [references/divergence.md](references/divergence.md) — Divergent changes guide

## Curating Commits

### Squash: Fold Changes Into Parent

`jj squash` moves changes from the working-copy commit into its parent. This is the primary tool for folding work together.

**Authority:** jj official docs. jujutsu-skill (squash workflow).

```bash
# Squash all changes from @ into @-
jj squash

# Squash with a new message for the combined commit
jj squash -m "feat: complete user validation"

# Squash specific files only
jj squash src/auth.rs src/auth_test.rs

# Squash from a specific source into a specific destination
jj squash --from <change-id> --into <target-change-id>
```

**Agent rule:** Always use `-m` when squashing — omitting it opens an editor.

After squashing, `@` becomes empty (all changes moved to parent). Either start new work with `jj new` or abandon the empty commit.

### Absorb: Auto-Distribute Changes

`jj absorb` automatically distributes each hunk in the working copy to the ancestor commit that last modified those lines. It's like smart squash — hunks go to the right place without manual targeting.

**Authority:** jj official docs (git-experts.md — absorb section).

```bash
# Absorb all working-copy changes into appropriate ancestors
jj absorb

# Preview what would happen (dry run not available — use jj undo to reverse)
jj absorb
jj log -r 'ancestors(@, 5)'  # verify the result
jj undo                       # if it wasn't right
```

**When to use absorb vs squash:**
- **absorb** — working copy has changes to lines touched by different ancestor commits
- **squash** — all changes belong in one parent commit, or you need explicit control

### Rebase: Move Commits

`jj rebase` moves commits to a new parent. Descendants are automatically rebased. Conflicts are recorded, not blocking.

**Authority:** jj official docs. ypares working-with-jj.

```bash
# Rebase current commit and descendants onto trunk
jj rebase -s @ -o trunk()

# Rebase a single commit (not its descendants)
jj rebase -r <change-id> -o trunk()

# Rebase a bookmark's branch onto trunk
jj rebase -b my-feature -o trunk()
```

**Flag meanings:**

| Flag | What it rebases |
|------|----------------|
| `-s <rev>` | The revision AND all its descendants |
| `-r <rev>` | Only that single revision (descendants rebase onto its parent) |
| `-b <rev>` | The entire branch containing rev (all commits not on destination) |
| `-o <dest>` | Destination (what to rebase onto). Use `-o`, not deprecated `-d` |

**After rebase:** always `jj st` to check for conflicts. If conflicts appear, see the Conflict Resolution section.

## Splitting Commits

Splitting divides one commit into multiple focused commits. This is common after making a large change that should be multiple atomic commits.

**Authority:** edmundmiller jj-history-investigation. jujutsu-skill (split warning).

### Agent-Safe Splitting

`jj split` without file paths is interactive and will hang. Two safe approaches:

**Approach 1: Split by file paths (non-interactive)**

```bash
# Split specific files out of a commit — the named files go into the first
# commit, everything else stays in the second
jj split -r <change-id> src/auth.rs src/auth_test.rs -m "feat: add auth module"
```

This works when the split boundary aligns with file boundaries.

**Approach 2: The restore workflow (any boundary)**

When you need to split within a file or the boundary is complex, use `jj restore` to carve out changes:

```bash
# 1. Create a new commit on top of the one to split
jj new <change-id> -m "part 2: error handling"

# 2. Restore (copy) only the files you DON'T want in part 2
#    This effectively removes them from the new commit
jj restore --from <change-id>- src/validation.rs

# 3. Now squash what remains of the original into a focused message
jj describe -r <change-id> -m "part 1: input validation"

# 4. Verify both commits
jj show <change-id>
jj show @
```

The restore workflow gives you full control without any interactive prompts.

### Splitting Immutable Commits

Commits with descendants or in shared history are immutable by default. Override with `--ignore-immutable`:

```bash
jj edit <change-id> --ignore-immutable
jj split --ignore-immutable src/module.rs -m "refactor: extract module"
```

**Authority:** edmundmiller jj-history-investigation (immutability override section).

**When `--ignore-immutable` is safe:**
- The commits are local-only (not pushed)
- You own all descendant commits
- No collaborators are affected

**What happens:** all descendant commits are rewritten with new commit IDs. Change IDs stay the same. Bookmarks on affected commits follow the rewrite.

## Conflict Resolution

jj records conflicts in commits instead of blocking operations. A rebase or merge that produces conflicts still succeeds — the conflicted state is stored and you resolve it when ready.

**Authority:** jj official docs (conflicts.md). steveklabnik jujutsu-tutorial (conflicts chapter).

### Identifying Conflicts

```bash
# Check current status for conflicts
jj st

# Find all conflicted commits in your branch
jj log -r 'conflicts() & trunk()..@'

# Show what files are conflicted in a specific commit
jj show <change-id>
```

### The Resolution Workflow

**Method 1: Edit directly (simple conflicts)**

```bash
# Edit the conflicted commit
jj edit <conflicted-change-id>

# Open the conflicted file — it contains conflict markers
# Edit the file to resolve, removing all markers
# jj auto-snapshots when done

# Verify
jj st  # should show no conflicts
```

**Method 2: New commit + squash (complex conflicts, safer)**

```bash
# Create a child commit to work in
jj new <conflicted-change-id>

# Edit files to resolve conflicts
# Verify with jj diff

# Squash the resolution into the conflicted parent
jj squash
```

Method 2 is safer because if the resolution goes wrong, you can `jj abandon @` to start over without affecting the conflicted commit.

**Authority:** steveklabnik jujutsu-tutorial (conflicts chapter — new+squash workflow).

### Understanding Conflict Markers

jj uses a diff-based marker format that's different from Git's:

```text
<<<<<<< conflict 1 of 1
%%%%%%% diff from base to side 1
 unchanged line
-removed in side 1
+added in side 1
+++++++ side 2 content
side 2 full content here
>>>>>>> conflict 1 of 1 ends
```

- `%%%%%%%` — A **diff** to apply (shows what one side changed)
- `+++++++` — A **snapshot** (shows the full content of the other side)
- Resolution: apply the diff mentally to the snapshot, or write the correct combined result

**Alternative styles** can be set via `ui.conflict-marker-style` in config:
- `"snapshot"` — shows full content of each side (no diffs)
- `"git"` — Git-compatible `<<<<`/`====`/`>>>>` markers (2-sided only)

**Authority:** jj official docs (conflicts.md — conflict marker styles).

### Agent Conflict Resolution Rules

1. **Never use `jj resolve`** — it opens an interactive merge tool
2. **Edit conflict markers directly** in the file
3. **Remove ALL marker lines** (`<<<<<<<`, `>>>>>>>`, `%%%%%%%`, `+++++++`)
4. **Verify with `jj st`** — output should show no conflict warnings
5. **Auto-rebase propagation** — resolving a parent conflict automatically re-resolves descendants that inherited it

## Handling Divergent Changes

A divergent change occurs when multiple visible commits share the same change ID. This can happen when a hidden predecessor becomes visible again, or when two processes amend the same change simultaneously.

**Authority:** jj official docs (guides/divergence.md).

Divergent changes show in `jj log` with a `/0`, `/1` offset and a "divergent" label:

```text
@  mzvwutvl/0 ... (divergent)
```

### Resolution Strategies

```bash
# Strategy 1: Abandon the unwanted version
jj abandon <unwanted-commit-id>

# Strategy 2: Give one version a new change ID (keep both)
jj metaedit --update-change-id <commit-id>

# Strategy 3: Squash them together
jj squash --from <source-commit-id> --into <target-commit-id>
```

**Note:** When referring to divergent commits, use their commit ID or change ID with offset (`mzvwutvl/0`), since the change ID alone is ambiguous.

## Investigating History

### Viewing Commits

```bash
# Show a specific commit's changes
jj show <change-id>

# Show with file statistics
jj show <change-id> --stat

# View diff of a specific commit
jj diff -r <change-id>

# View diff of a specific file in a commit
jj diff -r <change-id> src/main.rs

# View file content at a specific revision (without switching)
jj file show -r <change-id> src/main.rs
```

### Tracking Line History

```bash
# Who last changed each line (like git blame)
jj file annotate src/main.rs

# Find the commit that touched a specific file
jj log -r 'files("src/main.rs")'

# Find commits containing specific diff text
jj log -r 'diff_lines("TODO")'

# Search commit messages
jj log -r 'description(substring-i:"auth")'
```

**Authority:** edmundmiller jj-history-investigation (annotate and investigation techniques).

### Viewing Commit Evolution

`jj evolog` shows how a single change evolved over time — every rewrite, amend, and squash:

```bash
# See all versions of a change
jj evolog -r <change-id>

# With patches to see what changed between versions
jj evolog -r <change-id> -p
```

### Operation Log

The operation log records every `jj` operation, enabling full undo:

```bash
# View operation history
jj op log

# Undo the last operation
jj undo

# Restore repo to a specific past state
jj op restore <op-id>
```

`jj undo` can be repeated to step further back. `jj op restore` jumps directly to any point.

## Abandoning and Cleanup

### Abandoning Commits

`jj abandon` removes a commit. Its descendants are rebased onto its parent:

```bash
# Abandon a specific commit
jj abandon <change-id>

# Abandon multiple commits
jj abandon <id1> <id2> <id3>

# Abandon a range
jj abandon 'empty() & trunk()..@'
```

### Cleaning Up Empty Commits

After squashing or rebasing, empty commits may remain. Find and remove them:

```bash
# Find empty commits in your branch
jj log -r 'empty() & trunk()..@'

# Abandon all empty commits in your branch
jj abandon 'empty() & mine() & trunk()..@'
```

**Caution:** Some empty commits are intentional (e.g., merge commits, placeholder commits). Check before bulk-abandoning.

### Reverting Changes

To undo a commit's changes without removing it from history:

```bash
# Create a new commit that reverses the changes
jj revert -r <change-id>
```

## Verification Checklist

After any major history rewrite (split, rebase, large squash):

1. **No conflicts:** `jj log -r 'conflicts() & trunk()..@'` — should return nothing
2. **No unintended empties:** `jj log -r 'empty() & trunk()..@'` — review any results
3. **Commits are focused:** `jj show <id> --stat` for each rewritten commit
4. **Messages are clear:** `jj log -r 'trunk()..@'` — check descriptions
5. **Bookmarks correct:** `jj bookmark list` — verify positions
6. **Status clean:** `jj st` — no unexpected state

## Common Mistakes

- **Using `jj split` without file paths** — hangs waiting for interactive input. Always provide paths or use the restore workflow.
- **Using `jj squash -i`** — interactive, hangs in agent environments. Use `jj squash` (all) or `jj squash <paths>` (specific files).
- **Forgetting `-m` on squash** — opens an editor. Always `jj squash -m "message"`.
- **Not checking for conflicts after rebase** — rebase succeeds even with conflicts. Always `jj st` afterward.
- **Using `--ignore-immutable` on shared history** — rewrites commit IDs, breaking collaborators. Only use on local-only commits.
- **Abandoning merge commits carelessly** — merge commits may carry resolution data. Check with `jj show` first.
- **Not using `jj undo` for recovery** — if a split, squash, or rebase goes wrong, `jj undo` immediately reverses it. Don't try to manually fix broken state.
