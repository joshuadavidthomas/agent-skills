# Jujutsu (jj) Configuration

Configuration reference for jj. Covers config file locations, precedence, agent-specific setup, useful aliases, diff/merge tool configuration, signing, and customization.

**Target version: jj 0.36+**

For the full configuration reference, see:
- [references/config-reference.md](references/config-reference.md) — Complete configuration reference (~2100 lines)

**Authority:** jj official docs (config.md).

## Config File Locations and Precedence

Settings load in this order (later overrides earlier):

1. **Built-in** — compiled into jj, not editable
2. **User** — `jj config edit --user` or `jj config path --user`
3. **Repo** — `jj config edit --repo` or `jj config path --repo`
4. **Workspace** — `jj config edit --workspace` or `jj config path --workspace`
5. **Command-line** — `--config name=value` or `--config-file path`

**Authority:** jj official docs (config.md, "Config files and TOML").

User config locations (platform-specific, in precedence order):

- `$HOME/.jjconfig.toml`
- `<PLATFORM>/jj/config.toml` (preferred)
- `<PLATFORM>/jj/conf.d/*.toml` (loaded alphabetically)

Where `<PLATFORM>` is `$XDG_CONFIG_HOME` or `$HOME/.config` on Linux/macOS.

The `JJ_CONFIG` environment variable overrides all default user config locations. It accepts a path to a TOML file, a directory of TOML files, or multiple paths separated by `:` (Unix) or `;` (Windows).

```bash
# Find your config file
jj config path --user

# List all active config with origins
jj config list

# Set a value
jj config set --user ui.pager "less -FRX"
```

## Agent-Specific Configuration

**Authority:** ypares agent-skills (JJ_CONFIG pattern). jj official docs (config.md).

Agents should use a dedicated config file to prevent editor hangs and ensure predictable output:

```toml
# agent-jj-config.toml
[user]
name = "Agent"
email = "agent@example.com"

[ui]
editor = "TRIED_TO_RUN_AN_INTERACTIVE_EDITOR"
diff-formatter = ":git"
paginate = "never"
```

Launch with: `JJ_CONFIG=/path/to/agent-jj-config.toml <agent-harness>`

Key settings for agents:
- **`ui.editor`** — set to a string that will error clearly if jj tries to open an editor
- **`ui.diff-formatter`** — use `:git` for machine-parseable diffs (default `:color-words` is human-oriented)
- **`ui.paginate`** — set to `"never"` to prevent pager from blocking

## Aliases

**Authority:** jj official docs (config.md, "Aliases").

```toml
[aliases]
# Show recent work on your anonymous bookmark
l = ["log", "-r", "(main..@):: | (main..@)-"]

# Show only your commits
mine = ["log", "-r", "mine()"]

# Show conflicted commits
conflicts = ["log", "-r", "conflicted()"]

# Show empty commits (candidates for cleanup)
empties = ["log", "-r", "empty() & mine()"]

# Quick diff of current change
d = ["diff"]
```

Aliases run a single jj command. For multi-command aliases, use `jj util exec`:

```toml
[aliases]
sync = ["util", "exec", "--", "bash", "-c", """
set -euo pipefail
jj git fetch --all-remotes
jj rebase -s 'all:roots(trunk()..mine())' -o 'trunk()'
""", ""]
```

## Revset Aliases

**Authority:** jj official docs (config.md, revsets.md).

```toml
[revset-aliases]
# Customize which commits are immutable
"immutable_heads()" = "builtin_immutable_heads() | release@origin"

# Prevent rewriting other people's commits
"immutable_heads()" = "builtin_immutable_heads() | (trunk().. & ~mine())"
```

Default `jj log` revset:

```toml
[revsets]
log = "main@origin.."
```

## Diff Format

**Authority:** jj official docs (config.md, "Diff format").

```toml
[ui]
# Built-in: ":color-words" (default), ":git", ":summary", ":stat", ":types", ":name-only"
diff-formatter = ":git"

# External tool (e.g. difftastic)
diff-formatter = ["difft", "--color=always", "$left", "$right"]

# Or reference a named tool
diff-formatter = "delta"
```

Use an external pager with a formatter:

```toml
[ui]
pager = "delta"
diff-formatter = ":git"
```

## Merge Tools

**Authority:** jj official docs (config.md, "3-way merge tools").

```toml
[ui]
# Diff editor for jj split, jj squash -i
diff-editor = "meld"     # or ":builtin" (default), "meld-3", "diffedit3"

# Merge editor for jj resolve
merge-editor = "meld"    # or "kdiff3", "vscode", "vimdiff"
```

Custom merge tool configuration:

```toml
[merge-tools.mytool]
program = "/path/to/mytool"
merge-args = ["$left", "$base", "$right", "-o", "$output"]
```

## Commit Signing

**Authority:** jj official docs (config.md, "Commit Signing").

```toml
[signing]
behavior = "own"       # "drop" | "keep" | "own" | "force"
backend = "ssh"        # "gpg" | "ssh" | "none"
key = "ssh-ed25519 AAAAC3..."
# Or path: key = "~/.ssh/id_for_signing.pub"
```

Sign lazily only when pushing (avoids per-commit overhead):

```toml
[signing]
behavior = "drop"
backend = "ssh"
key = "ssh-ed25519 AAAAC3..."

[git]
sign-on-push = true
```

## Auto-Track for Remotes

**Authority:** jj official docs (config.md, "Automatic tracking of bookmarks").

```toml
[remotes.origin]
auto-track-bookmarks = "*"              # Track all bookmarks (default-like)

[remotes.upstream]
auto-track-bookmarks = "main"           # Only track main from upstream
```

Personal prefix pattern (avoids tracking coworkers' bookmarks):

```toml
[remotes.origin]
auto-track-bookmarks = "alice/*"
```

## Template Customization

**Authority:** jj official docs (config.md, templates.md).

```toml
[template-aliases]
# Show shortest unique prefix with minimum 12 chars
'format_short_id(id)' = 'id.shortest(12)'

# Relative timestamps
'format_timestamp(timestamp)' = 'timestamp.ago()'

# Show username instead of full email
'format_short_signature(signature)' = 'signature.email().local()'
```

## Conditional Config

**Authority:** jj official docs (config.md, "Conditional variables").

Apply different settings per repository, hostname, platform, or command:

```toml
# Override email for OSS repos
[[--scope]]
--when.repositories = ["~/oss"]
[--scope.user]
email = "oss@example.org"

# Use delta only for diff/show commands
[[--scope]]
--when.commands = ["diff", "show"]
[--scope.ui]
pager = "delta"
```

Or split into `conf.d/` files with top-level `--when`:

```toml
# In $XDG_CONFIG_HOME/jj/conf.d/work.toml
--when.repositories = ["~/work"]
[user]
email = "me@work.com"
```

## Code Formatting with `jj fix`

**Authority:** jj official docs (config.md, "Code formatting").

```toml
[fix.tools.prettier]
command = ["prettier", "--write", "--stdin-filepath=$path"]
patterns = ["glob:'**/*.{js,ts,jsx,tsx}'"]

[fix.tools.rustfmt]
command = ["rustfmt", "--emit", "stdout"]
patterns = ["glob:'**/*.rs'"]
enabled = false  # Enable per-repo with: jj config set --repo fix.tools.rustfmt.enabled true
```

## Common Mistakes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Config not taking effect | Wrong precedence level | Check with `jj config list`; repo overrides user |
| Editor opens unexpectedly | `ui.editor` not set for agent | Set `ui.editor` to a non-interactive string |
| Pager blocks execution | Pager waiting for input | Set `ui.paginate = "never"` |
| Bookmarks not tracking | `auto-track-bookmarks` too restrictive | Check `remotes.<name>.auto-track-bookmarks` pattern |
| `jj fix` not running | Tool not enabled | Set `fix.tools.<name>.enabled = true` per-repo |
| Dotted TOML keys break | Mixed with headings incorrectly | Put dotted keys before the first `[heading]` |
