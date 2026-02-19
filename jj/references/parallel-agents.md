# Parallel Agents with JJ Workspaces

A guide for running multiple AI agents concurrently using jj workspaces to isolate their working copies.

## The Problem

Multiple agents in the same repo fight over the working copy (`@`). Each agent runs `jj restore`, `jj squash`, and `jj new` operations, causing files to end up in wrong revisions and creating a tangled mess. The fundamental issue: there's only one `@` per workspace.

## Solution: One Workspace Per Agent

JJ workspaces provide isolated working copies backed by a single shared repo:

- Each workspace has its own `@` (working-copy commit)
- Changes in one workspace don't affect another's files
- All workspaces share the same revision graph
- Commits made in any workspace are visible to all others

This maps cleanly to parallel agents: assign each agent its own workspace.

## Complete Workflow

### Step 1: Plan Independent Tasks

Design tasks that touch different files. Tasks that modify the same files will conflict at merge time (which is solvable, but defeats the purpose of parallelization).

Good candidates for parallelization:
- Separate modules or services
- Independent features in different files
- Tests for different components
- Documentation for different areas

Bad candidates:
- Tasks that share config files
- Features that modify the same core module
- Tasks with ordering dependencies

### Step 2: Create Workspaces

From the main repo, create a workspace for each agent:

```bash
# Create named workspaces as siblings of the main repo
jj workspace add ../workspace-feature-a --name feature-a
jj workspace add ../workspace-feature-b --name feature-b
jj workspace add ../workspace-feature-c --name feature-c

# Verify
jj workspace list
```

**Workspace directories must be siblings of the main repo, not subdirectories.** Subdirectories would be tracked by jj, causing circular issues.

Each workspace gets its own `.jj/` directory that links back to the main repo's storage.

### Step 3: Set Up Task Commits

Create commits for each agent to work on:

```bash
# Create task branches from a common parent
jj new -m "feat: implement user service" --no-edit
user_id=$(jj log -r 'latest(description("implement user service"))' --no-graph -T 'change_id.shortest(8)')

jj new -m "feat: implement product service" --no-edit
product_id=$(jj log -r 'latest(description("implement product service"))' --no-graph -T 'change_id.shortest(8)')

jj new -m "feat: implement order service" --no-edit
order_id=$(jj log -r 'latest(description("implement order service"))' --no-graph -T 'change_id.shortest(8)')
```

### Step 4: Launch Agents

Each agent needs explicit instructions with absolute paths:

**Agent instruction template:**

```
You are working in an isolated JJ workspace for parallel execution.

Working directory: /absolute/path/to/workspace-feature-a
Task change-id: <change-id>
Task description: <what to implement>

Before any work:
  cd /absolute/path/to/workspace-feature-a
  jj edit <change-id>

After completing work:
  jj describe -m "feat: <completed description>"
  jj st  # verify clean state

CRITICAL:
- All commands MUST run inside your workspace directory
- Use absolute paths for everything
- Do NOT modify files in other workspaces
- Use `jj st` to verify state after mutations
```

**Why absolute paths?** Agents can lose track of `cwd`. Relative paths like `../workspace-a` break if the agent `cd`s somewhere unexpected. Absolute paths are resilient.

### Step 5: Monitor Progress

From the main workspace, check all agents' work:

```bash
# See working copy status of all workspaces
jj workspace list

# Check a specific workspace's working copy commit
jj log -r 'feature-a@'

# See all workspace commits
jj log -r 'working_copies()'

# Check status from a specific workspace
cd /absolute/path/to/workspace-feature-a && jj st
```

### Step 6: Integrate Results

After all agents finish:

```bash
# Create a merge commit combining all results
jj new <user-id> <product-id> <order-id> -m "feat: integrate all services"

# Resolve any conflicts
jj st
# Edit conflicted files if any, then verify
jj diff
```

### Step 7: Clean Up

```bash
# Remove workspace registrations (changes stay in revisions!)
jj workspace forget feature-a
jj workspace forget feature-b
jj workspace forget feature-c

# Delete workspace directories
rm -rf ../workspace-feature-a
rm -rf ../workspace-feature-b
rm -rf ../workspace-feature-c
```

Forgetting a workspace does NOT lose any commits. It only removes the working-copy association. All revisions remain in the shared repo.

## Stale Workspaces

When you modify a workspace's working-copy commit from another workspace, the affected workspace becomes "stale." This is normal and expected. The agent working in that workspace should run:

```bash
jj workspace update-stale
```

This updates the files on disk to match the current state. If the original operation was lost (e.g., due to `jj op abandon`), the update creates a recovery commit preserving the working copy's contents.

## Conflict Mitigation

**Generated files:** Ensure `.gitignore` covers build outputs (`__pycache__/`, `node_modules/`, `target/`, `.next/`, etc.). Otherwise, each workspace generates its own copies and creates spurious conflicts.

**Shared config:** If tasks must touch shared files (e.g., a router file, package.json), have one agent own those files and others work around them. Or handle the shared file in a sequential step after parallel work completes.

**Lock files:** Package manager lock files (`package-lock.json`, `Cargo.lock`) are a common conflict source. Consider having only one task add dependencies, or resolve lock conflicts in the integration step.

## Decision Checklist

Before using workspaces for parallel agents, verify:

- [ ] **3+ truly independent tasks** — fewer tasks don't justify the overhead
- [ ] **Tasks touch different files** — shared files mean conflicts
- [ ] **No ordering dependencies** — all tasks can start simultaneously
- [ ] **Time savings justify setup** — workspace creation, agent instructions, cleanup take real effort
- [ ] **Conflict strategy planned** — know how you'll handle the integration merge

If any box is unchecked, sequential execution is likely simpler and more reliable.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|
| Agent sees wrong files | Didn't `cd` to workspace | Ensure `cd /absolute/path` before every `jj` command |
| "Workspace not found" errors | Running from wrong directory | Check `cwd` and use `jj workspace list` to verify |
| Stale working copy | Commit modified from another workspace | Run `jj workspace update-stale` |
| Conflicts at merge | Tasks touched same files | Resolve in integration commit; redesign tasks for next time |
| Changes lost after forget | Changes are NOT lost | Commits persist in repo; workspace is just a view |
| Scripts not found | Relative paths in agent instructions | Use absolute paths for all file references |
