# jj

A consolidated skill for [Jujutsu (jj)](https://github.com/jj-vcs/jj), a Git-compatible version control system. Covers the mental model, agent-specific rules, daily workflows, revsets/filesets/templates, bookmarks and sharing, history rewriting, workspaces for parallel agents, and configuration.

## Structure

- `SKILL.md` — Router: mental model, agent rules, core workflow, essential commands, and routing to deep dives
- `revsets.md` — Revsets, filesets, and templates (the three query languages)
- `sharing.md` — Bookmarks, remotes, pushing, pulling, and GitHub/GitLab PR workflows
- `history.md` — History rewriting and investigation (squash, absorb, rebase, split, conflicts)
- `workspaces.md` — Workspaces for parallel agents (isolated working copies)
- `config.md` — Configuration and customization (precedence, aliases, diff/merge tools, signing)

## References

- `references/git-to-jj.md` — Git-to-jj command mapping table
- `references/git-experts.md` — Why jj improves on Git for power users
- `references/command-gotchas.md` — Flag semantics, quoting, deprecated flags
- `references/revsets.md` — Complete revset language spec
- `references/filesets.md` — Complete fileset language spec
- `references/templates.md` — Complete template language spec
- `references/bookmarks.md` — Complete bookmarks reference
- `references/github.md` — GitHub/GitLab workflow details
- `references/git-compatibility.md` — Git interop and colocated repos
- `references/conflicts.md` — Conflict handling and marker formats
- `references/divergence.md` — Divergent changes guide
- `references/config-reference.md` — Full configuration reference
- `references/parallel-agents.md` — Parallel agent setup guide

## Attribution & License

This skill synthesizes guidance from:

- [Jujutsu](https://github.com/jj-vcs/jj) — the jj VCS itself. Official documentation used for reference material. Licensed under [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0).
- [Steve Klabnik's Jujutsu Tutorial](https://github.com/steveklabnik/jujutsu-tutorial) — narrative tutorial providing mental model and conceptual grounding.
- [jujutsu-skill](https://github.com/danverbraganza/jujutsu-skill) by Dan Verbraganza — agent-specific workflow patterns and environment rules. Licensed under [MIT](https://opensource.org/licenses/MIT).
- [dot-claude jj-workflow](https://github.com/TrevorS/dot-claude) by TrevorS — concise AI-focused daily workflow patterns. Licensed under [ISC](https://opensource.org/licenses/ISC).
- [agent-skills working-with-jj](https://github.com/YPares/agent-skills) by Yves Parès — version-aware (0.36.x) command syntax, `JJ_CONFIG` agent configuration pattern. Licensed under [MIT](https://opensource.org/licenses/MIT).
- [jjtask](https://github.com/Coobaha/jjtask) by Alexander Ryzhikov — anti-patterns and gotchas for agent use. Licensed under [MIT](https://opensource.org/licenses/MIT).
- [sgai](https://github.com/sandgardenhq/sgai) by Sandgarden — Git-to-jj command mapping table (synthesized, not copied). Licensed under modified MIT.
- [dotfiles jj-history-investigation](https://github.com/edmundmiller/dotfiles) by Edmund Miller — history investigation techniques. Licensed under [MIT](https://opensource.org/licenses/MIT).
