# jj Command Gotchas

Pitfalls, flag semantics, and version-specific changes that trip up both humans and agents. Targets jj 0.36+.

## Flag Semantics: Source Flags

Source flags select *what* to operate on:

| Flag | Short | Meaning | Example |
|------|-------|---------|---------|
| `--revision` / `--revisions` | `-r` | Exactly the named revision(s) | `jj log -r xyz` |
| `--source` | `-s` | The revision and all its descendants (`REV::`) | `jj rebase -s xyz -o main` |
| `--from` | `-f` | The *contents* of a revision (for diff/move operations) | `jj squash --from @- --into @` |
| `--branch` | `-b` | A topological branch relative to the destination | `jj rebase -b @ -o main` |

## Flag Semantics: Destination Flags

Destination flags select *where* to put the result:

| Flag | Short | Meaning | Example |
|------|-------|---------|---------|
| `--onto` | `-o` | Place as children of the target | `jj rebase -r xyz -o main` |
| `--insert-after` | `-A` | Insert between target and its children | `jj rebase -r xyz -A main` |
| `--insert-before` | `-B` | Insert between target and its parents | `jj rebase -r xyz -B main` |
| `--to` / `--into` | `-t` | Move *contents* into the target revision | `jj squash --into abc` |

`--to` and `--into` are interchangeable. `--into` reads more naturally with `jj squash`.

## The `-r` Short Flag Rule

Many commands only accept the short form `-r`, not `--revision` or `--revisions`:

```bash
# ✅ Correct
jj log -r xyz
jj desc -r xyz -m "message"

# ❌ Error on many commands
jj log --revisions xyz
jj desc --revision xyz
```

**Rule: Always use `-r`.**

Some commands allow omitting `-r` entirely when no paths are involved:

`jj abandon`, `jj describe`, `jj duplicate`, `jj new`, `jj show`, `jj parallelize`

## Deprecated Flags (v0.36+)

| Old | New | Commands affected |
|-----|-----|-------------------|
| `-d` / `--destination` | `-o` / `--onto` | `rebase`, `split`, `revert` |
| `--edit` (on describe) | `--editor` | `describe` |

The old flags still work with a deprecation warning but will be removed.

## Symbol Strictness (v0.32+)

Bare symbols that match multiple change IDs cause an error:

```bash
# ❌ Error if "abc" is ambiguous (matches multiple change IDs)
jj log -r abc

# ✅ Explicit prefix query
jj log -r 'change_id(abc)'
```

Use longer prefixes or the `change_id()` function to disambiguate.

## Fileset Defaults (v0.36+)

Path arguments use **glob patterns by default**:

```bash
# Glob match (default) — matches src/foo.rs, src/bar.rs, etc.
jj diff 'src/*.rs'

# Literal path with special characters
jj diff 'cwd:"src/[special].rs"'
```

Watch out for `[` brackets in patterns — they're interpreted as character classes, not literals.

## Shell Quoting

Revsets contain characters the shell interprets (`()`, `"`, `*`, `|`, `&`). Always quote:

```bash
# ✅ Single quotes (safest)
jj log -r 'description(substring:"fix")'

# ✅ Double quotes with escaping
jj log -r "description(substring:\"fix\")"

# ❌ Unquoted — shell breaks it
jj log -r description(substring:"fix")
```

**Rule: Always single-quote revset expressions.**

## `--no-edit` for Parallel Work

Without `--no-edit`, `jj new` moves the working copy to the new commit:

```bash
# ❌ B becomes child of A (@ moved to A, then to B)
jj new parent -m "A"
jj new parent -m "B"

# ✅ Both are siblings, children of parent (@ unchanged)
jj new --no-edit parent -m "A"
jj new --no-edit parent -m "B"
```

## `jj commit` vs `jj new`

Both create new commits, but they differ:

- `jj commit -m "msg"` — Finalizes the working copy with the given message, then creates a new empty working copy on top.
- `jj new -m "msg"` — Creates a new empty commit with the message on top of `@`. The current working copy's description stays as-is.

Most jj workflows prefer: `jj describe -m "what I did"` → code → `jj new -m "next task"`.

## `jj split` Is Interactive

`jj split` without file arguments opens an interactive diff selector. This hangs in agent environments.

**Agent-safe alternatives:**

```bash
# Split by file paths (non-interactive)
jj split -r <rev> file1.py file2.py

# Move specific files out using restore
jj new -m "part 2"
jj restore --from @- file1.py file2.py
```

## Bookmarks Don't Auto-Advance

Unlike Git branches, jj bookmarks don't move when new commits are created. They *do* follow when a commit is rewritten (rebased, squashed, etc.), but you must explicitly set them before pushing:

```bash
# After creating commits, explicitly set the bookmark
jj bookmark set my-feature -r @

# Then push
jj git push -b my-feature
```

## Common Recovery Commands

| Situation | Command |
|-----------|---------|
| Undo last operation | `jj undo` |
| View operation history | `jj op log` |
| Restore to earlier state | `jj op restore <op-id>` |
| Discard working copy changes | `jj restore` |
| Discard a commit | `jj abandon <rev>` |
| Undo specific commit content | `jj restore --from @- <paths>` |
