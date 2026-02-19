# Jujutsu for Git Experts

Adapted from the [official jj documentation](https://github.com/jj-vcs/jj/blob/main/docs/git-experts.md) (Apache-2.0).

## Colocation — Use Git and jj Side-by-Side

jj and Git repos coexist in the same directory. Use `jj` for what it does better, fall back to `git` when you need to. This makes migration gradual — no "big bang" switch required.

## No Staging Area

jj replaces Git's index with direct commit manipulation. Instead of `git add` / `git rm --cached`, use `jj split` and `jj squash` to move work between commits:

```bash
# Split specific files into a separate commit
jj split file1 file2

# Move changes in file3 into the parent commit
jj squash file3
```

Moving work-in-progress is as easy as moving finished work.

## Safer, Faster History Editing

Amending an older commit in Git takes three steps:

```bash
git add file1 file2
git commit --fixup abc
git rebase -i --autosquash
```

In jj, one command does the same thing and automatically rebases all descendants:

```bash
jj squash --into abc file1 file2
```

## Undo Is More Powerful Than the Reflog

Git's reflog is per-ref and awkward when multiple refs are involved. jj's **operation log** records the state of the entire repository after every command.

- `jj undo` — Reverts the last operation. Repeat to keep stepping backward.
- `jj op log -p` — Shows operations with diffs.
- `--at-operation ID` — Run any command as if the repo were in a previous state.

## The Evolution Log (evolog)

Git's reflog shows how refs moved; jj's **evolog** shows how a single *change* evolved. Every rewrite is recorded. You can find a previous version of any change and `jj restore` it (fully or partially) back.

## `jj absorb` — Automatic Fixup Distribution

`jj absorb` moves each hunk in the working copy into the most recent ancestor commit that last modified those lines. It replaces the `git commit --fixup` + `git rebase --autosquash` cycle for the common case.

When multiple ancestor commits touched the same line, `jj absorb` leaves that hunk in the working copy for you to squash manually.
