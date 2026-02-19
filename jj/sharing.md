# Sharing and Collaboration

Sharing and collaboration workflows in jj — bookmarks, remotes, pushing, pulling, and GitHub/GitLab PR workflows.

**Target version: jj 0.36+**

For full references, see:
- [references/bookmarks.md](references/bookmarks.md) — Complete bookmarks reference
- [references/github.md](references/github.md) — GitHub/GitLab workflow details
- [references/git-compatibility.md](references/git-compatibility.md) — Git interop and colocated workspaces

## Bookmarks (jj's Branches)

Bookmarks are named pointers to commits — jj's equivalent of Git branches. Understanding their behavior is critical because it differs from Git in important ways.

**Authority:** jj official docs (bookmarks.md). steveklabnik jujutsu-tutorial (named-branches chapter).

**Bookmarks do NOT auto-advance.** When you create a new commit with `jj new`, `@` moves but bookmarks stay where they are. This is unlike Git where `HEAD` and the branch pointer advance together.

**Bookmarks DO follow rewrites.** `jj rebase`, `jj squash`, `jj abandon` — if these modify the commit a bookmark points at, the bookmark moves to the rewritten version.

**Bookmarks do NOT follow `jj new` or `jj commit`.** These create new commits; the bookmark stays on the old one.

```bash
# Create a new bookmark on current commit
jj bookmark create feat-auth -r @

# Move an existing bookmark to current commit
jj bookmark set feat-auth -r @

# Delete a bookmark
jj bookmark delete feat-auth

# List all bookmarks (shows tracking status)
jj bookmark list

# Track a remote bookmark
jj bookmark track main@origin
```

Shorthand: `jj b c` = create, `jj b s` = set, `jj b d` = delete.

## Pushing Changes

The canonical push pattern: **describe → set bookmark → push.**

**Authority:** steveklabnik jujutsu-tutorial (remotes chapter, updating-prs chapter).

### Named Bookmark Push (standard)

```bash
# Describe your work
jj describe -m "feat: add auth middleware"

# Set the bookmark
jj bookmark set feat-auth -r @

# Push
jj git push -b feat-auth
```

### Auto-Named Push (one-off PR)

```bash
# Push current commit with auto-generated bookmark name (push-<changeid>)
jj git push -c @
```

### After `jj commit`

`jj commit` finalizes `@` and creates an empty child. Your work is now in `@-`:

```bash
jj commit -m "feat: done with auth"
# Work is at @-, not @
jj git push -c @-
```

### Push Safety

Push is safe by default (like `--force-with-lease`). It rejects if the remote changed since your last fetch. Fetch first to update:

```bash
jj git fetch
jj git push -b feat-auth
```

## Fetching Changes

There is no `jj git pull`. The idiom is **fetch + rebase:**

**Authority:** jj official docs (github.md). steveklabnik jujutsu-tutorial (remotes chapter).

```bash
# Fetch all remotes
jj git fetch

# Rebase your work onto updated trunk
jj rebase -s 'all:roots(trunk()..mine())' -o trunk()
```

### Bookmark Tracking

Tracked bookmarks auto-update on fetch. Untracked bookmarks don't appear in `jj bookmark list` and don't advance.

```bash
# Track a specific remote bookmark
jj bookmark track main@origin

# Auto-track all bookmarks from a remote (in config)
```

```toml
[remotes.origin]
auto-track-bookmarks = "glob:*"
```

## Feature Branch / PR Workflow

**Authority:** steveklabnik jujutsu-tutorial (named-branches chapter, updating-prs chapter).

### Creating a PR

```bash
# 1. Do your work
jj new -m "feat: add user search"
# ... code ...

# 2. Bookmark the commit
jj bookmark create feat-user-search -r @

# 3. Push
jj git push -b feat-user-search

# 4. Open PR normally (via web UI, gh cli, etc.)
```

### Updating a PR via New Commits

```bash
# Add more work on top
jj new -m "feat: add search filters"
# ... code ...

# Move the bookmark forward
jj bookmark set feat-user-search -r @

# Push (jj handles force-push automatically)
jj git push -b feat-user-search
```

### Updating a PR via Rewriting (Amend in Place)

```bash
# Edit the original commit directly
jj edit <change-id>

# Make changes (auto-snapshotted)

# Push — jj force-pushes the rewritten commit, rebases descendants
jj git push -b feat-user-search
```

This is the "amend and push" workflow — no interactive rebase needed.

## Stacked PRs

Create separate bookmarks for each level of the stack, push them all:

**Authority:** steveklabnik jujutsu-tutorial (named-branches chapter — stacking).

```bash
# Build the stack
jj new trunk() -m "refactor: extract auth module"
jj bookmark create pr-1 -r @
# ... code ...

jj new -m "feat: add OAuth support"
jj bookmark create pr-2 -r @
# ... code ...

# Push all at once
jj git push -b pr-1 -b pr-2
```

When the base PR is updated (by review feedback or merge), jj rebases the stack automatically. Repoint bookmarks and push again:

```bash
jj bookmark set pr-1 -r <updated-id>
jj bookmark set pr-2 -r <updated-id>
jj git push -b pr-1 -b pr-2
```

## Independent Parallel PRs

For unrelated work that shouldn't stack:

```bash
# Start two independent lines from trunk
jj new trunk() -m "fix: timezone handling"
jj bookmark create fix-tz -r @
# ... fix ...

jj new trunk() -m "feat: add dark mode"
jj bookmark create feat-dark -r @
# ... code ...

# Push independently
jj git push -b fix-tz -b feat-dark
```

Merging one has zero effect on the other since they share no parent beyond trunk.

## Working with Multiple Remotes

Fork workflow: fetch from upstream, push to origin.

**Authority:** jj official docs (github.md — forked repositories).

```toml
[git]
fetch = ["upstream", "origin"]
push = "origin"
```

```bash
# Add upstream remote
jj git remote add upstream https://github.com/original/repo.git

# Fetch from upstream
jj git fetch --remote upstream

# Rebase onto upstream's main
jj rebase -s 'all:roots(trunk()..mine())' -o 'trunk()'

# Push to your fork
jj git push -b my-feature
```

## Colocated Repos

Most jj repos are colocated (both `.jj/` and `.git/`). The key rule for sharing: **always use `jj git push`, never raw `git push`** — raw push desyncs bookmark tracking.

→ Full colocated repo guide: [git.md](git.md)

## Using GitHub CLI

In non-colocated repos, `gh` needs the git dir:

```bash
GIT_DIR=.jj/repo/store/git gh issue list
GIT_DIR=.jj/repo/store/git gh pr create
```

Or use `direnv` with `.envrc`:

```bash
export GIT_DIR=.jj/repo/store/git
```

In colocated repos, `gh` works normally.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Forget to move bookmark before push | `jj bookmark set <name> -r @` first |
| Pushing empty working copy after `jj commit` | Push `@-` not `@` |
| Using `bookmark move` instead of `set` | `jj bookmark set <name> -r @` is simpler |
| Not fetching before push | `jj git fetch` first |
| Expecting auto-tracking of all remotes | Configure `auto-track-bookmarks` or use `jj bookmark track` |
| Running `git push` in colocated repo | Use `jj git push` instead |

## Agent Checklist (Before Any Push)

1. Verify commit has a description: `jj log -r @`
2. Ensure a bookmark points at it: `jj bookmark list`
3. If not, create/set one: `jj bookmark set <name> -r @`
4. Check for conflicts: `jj st`
5. Push: `jj git push -b <name>`
6. Verify: `jj bookmark list` — no `*` on the pushed bookmark
