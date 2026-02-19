# Git Interop

How jj relates to Git — the colocated repo model, concept mapping, when to use raw `git`, and safety at the boundary.

**Target version: jj 0.36+**

For full references, see:
- [references/git-to-jj.md](references/git-to-jj.md) — Complete command translation table
- [references/git-experts.md](references/git-experts.md) — Why jj improves on Git workflows
- [references/git-compatibility.md](references/git-compatibility.md) — Feature support matrix and colocated repo details

## The Big Picture

jj uses Git as its storage backend. Every jj repo has a Git repo inside it — either visible (colocated) or hidden. Your commits are real Git commits. Your remotes are real Git remotes. Collaborators don't need to know you're using jj.

This means jj inherits Git's network layer, authentication, `.gitignore` support, and compatibility with forges like GitHub/GitLab. It replaces Git's CLI and workflow model, not its data model.

## Colocated Repos

A colocated repo has both `.jj/` and `.git/` in the same directory. This is the default when you run `jj git init` or `jj git clone`.

**Why colocated matters:**
- Build tools, CI, and IDEs that expect `.git/` work normally
- You can mix `jj` and `git` commands (with care)
- `jj` auto-syncs with `.git/` on every command — bookmarks, commits, and refs stay in sync

**"Detached HEAD" is normal.** Git will report detached HEAD in colocated repos. This is expected — jj has no concept of a "current branch." Use `jj log` for the real state, not `git log`.

```bash
# Check colocation status
jj git colocation status

# Convert between modes
jj git colocation enable    # make colocated
jj git colocation disable   # hide .git inside .jj/
```

### Non-Colocated Repos

Created with `jj git init --no-colocate` or `jj git clone --no-colocate`. The Git repo lives inside `.jj/repo/store/git`. You must use `jj git import` and `jj git export` to sync manually. Tools like `gh` CLI need `GIT_DIR=.jj/repo/store/git`.

Prefer colocated repos unless you have a specific reason not to.

## Concept Mapping

| Git concept | jj equivalent | Key difference |
|---|---|---|
| Staging area (`git add`) | No equivalent — working copy auto-commits | Use `jj split` / `jj squash` to move changes between commits |
| Branches | Bookmarks | Don't auto-advance on new commits; must be set explicitly |
| `HEAD` / current branch | `@` (working copy commit) | Always exists, always points to a real commit |
| Detached HEAD | Normal state | jj doesn't track a "current bookmark" |
| Reflog | Operation log (`jj op log`) | Tracks entire repo state, not per-ref |
| `git stash` | `jj new @-` | Old working copy stays as a sibling commit |
| `git commit --amend` | `jj squash` or `jj describe` | Descendants auto-rebase |
| `git rebase -i` | `jj rebase -r`, `jj squash --into` | No interactive mode needed; each operation is atomic |
| `git cherry-pick` | `jj duplicate` | |
| `git revert` | `jj revert` | |
| `git worktree` | `jj workspace` | Native support, no Git worktrees involved |
| Merge conflicts block work | Conflicts can be committed | Resolve later; conflicts are data, not errors |

## Setting Up

```bash
# New repo (colocated by default)
jj git init

# Clone from remote
jj git clone https://github.com/org/repo.git

# Add jj to an existing Git repo
cd existing-git-repo
jj git init

# Non-colocated (Git hidden inside .jj/)
jj git init --no-colocate
```

After `jj git init` in an existing Git repo, all Git history is available to jj immediately. Existing branches become bookmarks.

## When to Use Raw `git`

jj handles most daily work. Use raw `git` for features jj doesn't support:

| Feature | jj support | What to do |
|---|---|---|
| Submodules | No | Use `git submodule` commands |
| Git LFS | No | Use `git lfs` commands |
| Annotated tags | No (lightweight only) | Use `git tag -a` |
| `.gitattributes` | No | Edit the file directly; jj won't interpret it |
| Pre-commit hooks | No | Run `git` hook tools directly, or use `pre-commit run --all-files` |
| Partial/shallow clones | Limited | Use `git clone --depth` then `jj git init` |
| `git bisect` (legacy) | Use `jj bisect` | jj has native bisect support |

**After any mutating `git` command in a colocated repo, run any `jj` command** (even `jj st`) to re-sync state. jj auto-imports on every command.

## Mixing Commands Safely

**Safe to mix (colocated repos):**
- Read-only `git` commands (`git log`, `git show`, `git diff`, `git blame`) — always safe
- `git fetch` — safe, but prefer `jj git fetch` since it auto-tracks bookmarks
- `git stash` — works but unnecessary; `jj new @-` is the jj idiom

**Use with care:**
- `git commit`, `git rebase`, `git merge` — work but can cause divergent change IDs or bookmark conflicts. Prefer jj equivalents.
- `git switch` / `git checkout` — may be needed before mutating git commands since jj leaves Git in detached HEAD state

**Avoid:**
- `git push` — use `jj git push`; raw `git push` desyncs bookmark tracking
- `git reset` — use `jj abandon`, `jj restore`, or `jj op restore` instead

### Recovery from Mixed-Command Issues

If mixing `jj` and `git` commands causes confusion (divergent change IDs, bookmark conflicts):

```bash
# See what happened
jj op log

# Undo the last jj operation (includes the auto-import of git changes)
jj undo

# Or restore to a known-good state
jj op restore <op-id>
```

## Import and Export

In colocated repos, import/export is automatic on every `jj` command. In non-colocated repos, you manage it:

```bash
# Import changes made in Git into jj
jj git import

# Export changes made in jj to Git
jj git export
```

**What gets synced:**
- Commits (both directions)
- Branch/bookmark pointers (both directions)
- Tags (import only — jj reads Git tags)
- Remote tracking refs (import only)

**What doesn't sync:**
- Git's staging area (ignored by jj)
- Git merge conflict state (ignored)
- Unfinished `git rebase` state (ignored)

## Git Auth

jj delegates all network operations to Git. Your existing Git authentication (SSH keys, credential helpers, `.netrc`, `GIT_ASKPASS`) works unchanged. If `git push` works, `jj git push` works.

## Agent Rules at the Git Boundary

1. **Always prefer `jj` commands** over `git` equivalents in jj repos
2. **Use `jj git push`**, never raw `git push`
3. **After raw `git` mutations**, run `jj st` to re-sync
4. **Don't panic at "detached HEAD"** — it's normal in colocated repos
5. **For unsupported features** (submodules, LFS, hooks), use `git` directly and document why
