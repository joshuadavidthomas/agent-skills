# Workspaces for Parallel Agents

Workspaces provide isolated working copies that share the full revision graph. Each workspace has its own `@` (working-copy commit) and lives in a sibling directory. This is jj's equivalent of `git worktree`.

**Target version: jj 0.36+**

For the complete parallel agent setup guide, see:
- [references/parallel-agents.md](references/parallel-agents.md) — Detailed workflow, decision checklist, troubleshooting, agent instruction templates

**Authority:** jj official docs (working-copy.md, glossary.md).

## When to Use Workspaces

**Use when:**
- 3+ truly independent tasks can run simultaneously
- Tasks touch different files
- Time savings justify setup/cleanup overhead

**Don't use when:**
- Tasks are sequential or dependent
- Only 1–2 tasks (overhead exceeds benefit)
- Tasks modify the same files
- Tasks are small/fast enough to do sequentially

**Authority:** ypares jj-todo-workflow (parallel-agents.md).

## Core Commands

| Command | Purpose |
|---------|---------|
| `jj workspace add <path> --name <name>` | Create workspace |
| `jj workspace forget <name>` | Unregister workspace (commits preserved) |
| `jj workspace list` | Show all workspaces and their `@` |
| `jj workspace update-stale` | Refresh files after external modification |
| `jj workspace root --name <name>` | Print workspace root path |

## Setup Workflow

### 1. Create Workspaces

Workspaces must be **sibling directories**, never subdirectories of the repo (child dirs get tracked by jj):

```bash
jj workspace add ../ws-auth --name auth
jj workspace add ../ws-api --name api
jj workspace add ../ws-docs --name docs
```

### 2. Create Task Commits

```bash
jj new -m "feat: add auth middleware"
jj new trunk() --no-edit -m "feat: add API endpoints"
jj new trunk() --no-edit -m "docs: update API reference"
```

### 3. Assign Agents

Give each agent:
- **Absolute path** to its workspace (agents lose track of relative cwd)
- **Change ID** of its task commit

The agent must run `jj edit <change-id>` before doing any work.

### 4. Monitor Progress

```bash
# See all workspace working copies
jj log -r 'working_copies()'

# Check a specific workspace
jj log -r 'auth@'
```

### 5. Integrate Results

```bash
# Merge all task commits
jj new <auth-id> <api-id> <docs-id> -m "merge: integrate parallel work"

# Check for conflicts
jj st
```

### 6. Clean Up

```bash
jj workspace forget auth
jj workspace forget api
jj workspace forget docs
rm -rf ../ws-auth ../ws-api ../ws-docs
```

`forget` only unregisters the workspace — commits are preserved. You must `rm -rf` the directory manually.

## Agent Instruction Template

When tasking an agent with workspace work, provide:

```
Work in workspace: /absolute/path/to/ws-auth
Your change ID: <change-id>

Before starting:
  cd /absolute/path/to/ws-auth
  jj edit <change-id>

Rules:
  - Always use -m for messages (no editors)
  - Run jj st after every mutation
  - Do not modify files outside your assigned scope
```

**Always use absolute paths.** Agents navigate directories during work; relative paths break.

## Stale Working Copies

When another workspace modifies a commit that affects your workspace, `jj st` warns about a stale working copy.

**Fix:** `jj workspace update-stale`

This is normal and expected. If an operation was lost (`jj op abandon`), `update-stale` creates a recovery commit preserving the workspace's disk state.

**Authority:** jj official docs (working-copy.md — stale working copy section).

## Conflict Mitigation

| Source | Prevention |
|--------|------------|
| Build outputs | Cover in `.gitignore` |
| Shared config files | Assign one agent to own them |
| Lock files | Only one task adds deps, or resolve at integration |
| Same source files | Redesign task boundaries |

Conflicts at integration are normal jj conflicts — edit markers, verify with `jj st`.

## Revset Expressions for Workspaces

| Expression | Meaning |
|------------|---------|
| `working_copies()` | All workspace `@`s |
| `auth@` | Specific workspace's `@` |
| `@` | Current workspace's `@` |

## Common Mistakes

- **Creating workspaces as subdirectories** — child dirs get tracked by jj. Always use sibling directories (`../ws-name`).
- **Using relative paths in agent instructions** — agents navigate; paths break. Always use absolute paths.
- **Forgetting to `jj edit <change-id>`** before starting work — the agent works on the wrong commit.
- **Panicking over "workspace stale" messages** — run `jj workspace update-stale`, it's normal.
- **Thinking `forget` deletes work** — it only unregisters the workspace. Commits remain in the repo.
- **Not deleting workspace directories after `forget`** — `forget` doesn't remove the directory. `rm -rf` it manually.
