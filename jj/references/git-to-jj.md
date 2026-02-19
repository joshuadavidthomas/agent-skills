# Git to Jujutsu Command Mapping

Quick reference for translating Git commands to their jj equivalents. For the full official table, see <https://docs.jj-vcs.dev/latest/git-command-table/>.

## Setup

| Git | jj | Notes |
|-----|-----|-------|
| `git init` | `jj git init` | Add `--no-colocate` to skip `.git` |
| `git clone <url>` | `jj git clone <url>` | |

## Viewing State

| Git | jj | Notes |
|-----|-----|-------|
| `git status` | `jj st` | |
| `git diff` | `jj diff` | Working copy vs parent |
| `git diff <rev>^ <rev>` | `jj diff -r <rev>` | |
| `git diff --from A --to B` | `jj diff --from A --to B` | |
| `git log` | `jj log` | |
| `git log --oneline --graph` | `jj log -r ::@` | |
| `git log --all --graph` | `jj log -r 'all()'` | Or `jj log -r ::` |
| `git show <rev>` | `jj show <rev>` | |
| `git blame <file>` | `jj file annotate <path>` | |
| `git ls-files` | `jj file list` | |

## Making Changes

| Git | jj | Notes |
|-----|-----|-------|
| `git add` | *(automatic)* | jj tracks changes automatically |
| `git commit` | `jj commit -m "msg"` | Or just `jj new -m "next task"` |
| `git commit --amend` | `jj squash` | Squash working copy into parent |
| `git commit --amend --only` | `jj describe @- -m "msg"` | Edit previous commit message |

## Navigating

| Git | jj | Notes |
|-----|-----|-------|
| `git checkout -b topic main` | `jj new main` | |
| `git switch <branch>` | `jj new <bookmark>` | Or `jj edit <rev>` |
| `git stash` | `jj new @-` | Old commit stays as sibling |

## History Rewriting

| Git | jj | Notes |
|-----|-----|-------|
| `git rebase --onto B A` | `jj rebase -s A -o B` | |
| `git rebase -i` | `jj rebase -r C --before B` | For reordering |
| `git cherry-pick <rev>` | `jj duplicate <rev> -o @` | |
| `git revert <rev>` | `jj revert -r <rev> -B @` | |
| `git reset --hard` | `jj abandon` or `jj restore` | `abandon` drops commit; `restore` empties it |
| `git reset --soft HEAD~` | `jj squash --from @-` | Keep diff in working copy |
| `git restore <paths>` | `jj restore <paths>` | |

## Bookmarks (Branches)

| Git | jj | Notes |
|-----|-----|-------|
| `git branch` | `jj bookmark list` | Or `jj b l` |
| `git branch <name>` | `jj bookmark create <name> -r <rev>` | |
| `git branch -f <name> <rev>` | `jj bookmark move <name> --to <rev>` | Or `jj b m` |
| `git branch -d <name>` | `jj bookmark delete <name>` | |

## Remotes

| Git | jj | Notes |
|-----|-----|-------|
| `git push` | `jj git push` | |
| `git push <remote> <branch>` | `jj git push -b <bookmark>` | |
| `git push --all` | `jj git push --all` | |
| `git fetch` | `jj git fetch` | |
| `git pull` | `jj git fetch` | Then merge/rebase if needed |
| `git remote add <name> <url>` | `jj git remote add <name> <url>` | |

## Merging

| Git | jj | Notes |
|-----|-----|-------|
| `git merge A` | `jj new @ A` | Creates merge commit |

## Other

| Git | jj | Notes |
|-----|-----|-------|
| `git rev-parse --show-toplevel` | `jj workspace root` | |
| `git rm --cached <file>` | `jj file untrack <file>` | File must match ignore pattern |
