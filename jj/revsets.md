# Revsets, Filesets, and Templates

jj has three domain-specific languages for querying and formatting: **revsets** select commits, **filesets** select files, and **templates** format output. This skill covers practical usage of all three.

**Target version: jj 0.36+**

For full language references, see:
- [references/revsets.md](references/revsets.md) — Complete revset language reference
- [references/filesets.md](references/filesets.md) — Complete fileset language reference
- [references/templates.md](references/templates.md) — Complete template language reference

## Revsets

A revset is an expression that selects a set of commits. Most `jj` commands accept revsets via `-r`.

**Authority:** jj official docs (revsets.md). ypares working-with-jj (revset reference section).

### Symbols

| Symbol | Meaning |
|--------|---------|
| `@` | Working-copy commit |
| `@-` | Parent of working copy |
| `@--` | Grandparent (repeat `-` for depth) |
| `<workspace>@` | Working copy in another workspace |
| `<name>@<remote>` | Remote-tracking bookmark (e.g., `main@origin`) |

**Change IDs vs commit IDs.** Both work as revset symbols. Change IDs (letters k–z) are stable across rewrites — prefer them. Use `change_id(prefix)` or `commit_id(prefix)` to disambiguate from bookmark/tag names.

**Quoting.** Always single-quote revset expressions in shell to prevent interpretation:

```bash
jj log -r 'mine() & ::@'
```

If a symbol contains special characters (like `-`), quote it inside the revset too:

```bash
jj log -r '"my-bookmark"'
```

### Operators

Operators listed from strongest to weakest binding:

| Operator | Meaning | Example |
|----------|---------|---------|
| `x-` | Parents of x | `@-` |
| `x+` | Children of x | `trunk()+` |
| `x::` | Descendants of x (inclusive) | `@::` |
| `::x` | Ancestors of x (inclusive) | `::@` |
| `x::y` | Ancestry path: descendants of x that are ancestors of y | `trunk()::@` |
| `x..` | Not ancestors of x (complement) | `trunk()..` |
| `..x` | Ancestors of x excluding root | `..@` |
| `x..y` | Ancestors of y minus ancestors of x (Git's `x..y`) | `trunk()..@` |
| `~x` | Not in x | `~immutable()` |
| `x & y` | Intersection | `mine() & ::@` |
| `x ~ y` | Difference (in x but not y) | `::@ ~ ::trunk()` |
| `x \| y` | Union | `bookmarks() \| tags()` |

**`::` vs `..` — the key distinction:**

- `trunk()::@` — ancestry path: only commits that are both descendants of trunk AND ancestors of @. Excludes side branches.
- `trunk()..@` — range: all ancestors of @ that aren't ancestors of trunk. Includes side branches merged into @.

For simple linear histories they're equivalent, but `::` is stricter on branchy history.

### Common Functions

| Function | What it selects |
|----------|----------------|
| `mine()` | Commits where author email matches current user |
| `bookmarks()` | All local bookmark targets |
| `bookmarks("main")` | Bookmarks matching glob pattern |
| `remote_bookmarks()` | All remote bookmark targets |
| `tags()` | All tag targets |
| `trunk()` | Head of the default branch (main/master on origin) |
| `description(pattern)` | Commits with matching description |
| `subject(pattern)` | Commits with matching first line of description |
| `author(pattern)` | Commits with matching author name or email |
| `committer_date(pattern)` | Commits with matching committer date |
| `empty()` | Commits modifying no files |
| `merges()` | Merge commits |
| `conflicts()` | Commits with conflicted files |
| `divergent()` | Divergent changes |
| `files(expression)` | Commits modifying paths matching a fileset |
| `diff_lines(text, [files])` | Commits containing matching diff lines |
| `heads(x)` | Commits in x with no descendants in x |
| `roots(x)` | Commits in x with no ancestors in x |
| `ancestors(x, depth)` | Ancestors with depth limit |
| `descendants(x, depth)` | Descendants with depth limit |
| `reachable(srcs, domain)` | All commits reachable from srcs within domain |
| `connected(x)` | Same as `x::x` — connect the dots between commits |
| `latest(x, [count])` | Most recent commits by committer timestamp |
| `present(x)` | Same as x, but returns none() instead of error if missing |
| `exactly(x, count)` | Assert exactly N commits match, error otherwise |

### Built-in Aliases

**Authority:** jj official docs (revsets.md, revsets.toml).

| Alias | Default definition | Purpose |
|-------|-------------------|---------|
| `trunk()` | Head of default branch on default remote | Base branch for comparisons |
| `immutable_heads()` | `trunk() \| tags() \| untracked_remote_bookmarks()` | Define what can't be rewritten |
| `immutable()` | `::(immutable_heads() \| root())` | All immutable commits |
| `mutable()` | `~immutable()` | All mutable commits |
| `visible()` | `::visible_heads()` | All visible commits |

Override `immutable_heads()` in config to protect more or fewer commits. Override `trunk()` if your default branch isn't auto-detected.

### Practical Recipes

```bash
# My recent work
jj log -r 'mine() & trunk()..@'

# Unpushed commits
jj log -r 'remote_bookmarks()..@'

# All commits with "fix" in the description
jj log -r 'description(substring-i:"fix")'

# Find the commit that touched a specific file
jj log -r 'files("src/main.rs")'

# Commits from the last week
jj log -r 'committer_date(after:"1 week ago")'

# Show the stack I'm working on
jj log -r 'reachable(@, mutable())'

# Find merge commits in my branch
jj log -r 'merges() & trunk()..@'

# Conflicted commits anywhere in my branch
jj log -r 'conflicts() & trunk()..@'

# All bookmarks and tags (like git log --simplify-by-decoration)
jj log -r 'tags() | bookmarks()'
```

### String Patterns

String-matching functions (`description()`, `author()`, `bookmarks()`, etc.) accept patterns. The default is glob matching.

**Authority:** jj official docs (revsets.md — string patterns section).

| Prefix | Behavior | Example |
|--------|----------|---------|
| `glob:` | Unix shell wildcards (default) | `description(glob:"fix*")` |
| `substring:` | Contains substring | `description(substring:"TODO")` |
| `exact:` | Exact match | `bookmarks(exact:"main")` |
| `regex:` | Regular expression | `author(regex:"^alice")` |

Append `-i` for case-insensitive: `substring-i:"todo"`, `glob-i:"FIX*"`.

Patterns support logical operators: `~x` (not), `x & y` (both), `x | y` (either).

**Gotcha:** Glob `[` brackets are character classes, not literal. Use `substring:` for text containing brackets:

```bash
# WRONG — [task] is interpreted as character class
jj log -r 'description(glob:"*[task]*")'

# RIGHT — substring treats brackets literally
jj log -r 'description(substring:"[task]")'
```

**Authority:** coobaha jjtask (description glob brackets pitfall).

### Date Patterns

Functions like `author_date()` and `committer_date()` accept date patterns:

```bash
jj log -r 'committer_date(after:"2024-01-01")'
jj log -r 'author_date(before:"yesterday")'
jj log -r 'committer_date(after:"2 days ago") & committer_date(before:"yesterday")'
```

Supported formats: `2024-02-01`, `2024-02-01T12:00:00`, `2 days ago`, `yesterday`, `yesterday 5pm`.

## Filesets

A fileset expression selects files. Many commands accept filesets as positional arguments.

**Authority:** jj official docs (filesets.md).

**In jj 0.36+, the default pattern is `prefix-glob:`** — a path argument matches as a cwd-relative glob that also recurses into directories. A plain filepath still works as expected.

| Pattern | Behavior | Example |
|---------|----------|---------|
| `prefix-glob:` | Glob + recursive directory match (default) | `jj diff src` |
| `cwd:` | cwd-relative prefix (no glob) | `jj diff 'cwd:"file[1].txt"'` |
| `file:` / `cwd-file:` | Exact file path (no directory recursion) | `jj diff 'file:"README.md"'` |
| `glob:` / `cwd-glob:` | Unix glob, cwd-relative | `jj diff 'glob:"*.rs"'` |
| `root:` | Workspace-relative prefix | `jj diff 'root:"src/lib"'` |
| `root-glob:` | Workspace-relative glob | `jj diff 'root-glob:"**/*.py"'` |

Append `-i` for case-insensitive glob: `glob-i:"*.TXT"`.

**Operators:** `~x` (not), `x & y` (both), `x | y` (either), `x ~ y` (difference).

```bash
# All files except Cargo.lock
jj diff '~Cargo.lock'

# Rust files in src/
jj diff 'src & glob:"**/*.rs"'

# Everything except generated files
jj diff '~glob:"**/*.generated.*"'
```

**Quoting.** If the expression has operators or function calls, inner quotes are required for paths with special characters:

```bash
jj diff '~"Foo Bar"'        # Negate a path with spaces
jj diff '"Foo(1)"'           # Path with parentheses
```

## Templates

Templates customize command output via `-T`. They use a functional language with keywords, methods, operators, and functions.

**Authority:** jj official docs (templates.md).

### Quick Patterns

```bash
# One-line commit summary
jj log -r '::@' -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'

# Machine-readable commit + change IDs
jj log --no-graph -T 'commit_id ++ " " ++ change_id ++ "\n"'

# Show just descriptions
jj log --no-graph -r 'trunk()..@' -T 'description'

# Custom format with bookmarks
jj log -T 'change_id.shortest() ++ " " ++ separate(" ", bookmarks, description.first_line()) ++ "\n"'

# JSON output for scripting
jj log --no-graph -r '@' -T 'json(self) ++ "\n"'
```

### Key Functions

| Function | Purpose |
|----------|---------|
| `separate(sep, ...)` | Join non-empty values with separator |
| `coalesce(...)` | First non-empty value |
| `if(cond, then, else)` | Conditional |
| `label(name, content)` | Apply color label |
| `fill(width, content)` | Wrap lines at width |
| `indent(prefix, content)` | Indent non-empty lines |
| `surround(prefix, suffix, content)` | Wrap non-empty content |
| `json(value)` | Serialize as JSON |

### Key Methods

On `Commit`: `.description()`, `.change_id()`, `.commit_id()`, `.author()`, `.bookmarks()`, `.tags()`, `.empty()`, `.conflict()`, `.diff()`, `.mine()`, `.immutable()`

On `ChangeId`/`CommitId`: `.short([len])`, `.shortest([min_len])`

On `String`: `.first_line()`, `.lines()`, `.upper()`, `.lower()`, `.contains()`, `.starts_with()`

On `List`: `.len()`, `.join(sep)`, `.map(|item| expr)`, `.filter(|item| expr)`

### Template Aliases

Define in config for reuse:

```toml
[template-aliases]
'short_log' = 'change_id.shortest() ++ " " ++ separate(" ", bookmarks, description.first_line())'
```

Then use: `jj log -T short_log`.

## Useful Config Aliases

**Authority:** ypares working-with-jj (aliases). jj official docs (revsets.toml).

```toml
[revset-aliases]
# Recent work on current branch
'recent' = 'mine() & trunk()..@'

# Find conflicted commits
'conflicted' = 'conflicts() & mutable()'

# Unpushed work
'unpushed' = 'remote_bookmarks()..@'

# Work in progress (non-empty, mutable, mine)
'wip' = 'mine() & mutable() & ~empty()'
```

## Common Mistakes

- **Unquoted revsets** — `jj log -r mine() & ::@` breaks in shell. Always single-quote: `jj log -r 'mine() & ::@'`.
- **Glob brackets in description()** — `description(glob:"*[fix]*")` treats `[fix]` as a character class. Use `substring:` instead.
- **Ambiguous short IDs** — Since v0.32, bare symbols are stricter. Use `change_id(prefix)` or `bookmarks(name)` to be explicit.
- **Confusing `::` and `..`** — `x::y` is the ancestry path (both descendant of x AND ancestor of y). `x..y` is the range (ancestor of y minus ancestors of x). On linear history they're the same; on branchy history they differ.
- **Forgetting `present()`** — If a bookmark might not exist, wrap in `present()` to avoid errors: `present(bookmarks("feature"))`.
- **Using `..x` expecting root included** — `..x` excludes root. Use `::x` if you need root included.
