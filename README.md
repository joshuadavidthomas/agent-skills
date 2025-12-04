# agent-skills

A collection of Agent Skills for AI coding assistants, following the [Anthropic Agent Skills specification][agent-skills-docs].

## Available Skills

### crafting-effective-readmes

Guides you through writing READMEs matched to your audience and project type. Different audiences need different information—a contributor to an OSS project needs different context than future-you opening a config folder.

Includes:

- Templates for open source, personal, internal, and config projects
- Section checklist showing which sections matter for each project type
- Style guide covering common mistakes and AI writing patterns to avoid
- Reference materials including the Standard README spec and "Art of README"

### improving-prompts

Apply Anthropic's documented Claude 4.5 best practices to CLAUDE.md, AGENTS.md, custom commands, and skill files. Uses actual guidance from Anthropic instead of inventing improvements.

The key constraint: don't change anything until you understand what specific behavior is failing. Includes a quick reference table mapping common issues ("Claude takes things too literally", "Claude suggests but doesn't act") to specific fixes.

### reducing-entropy

Helps you evaluate designs, review code, and refactor with a bias toward deletion. The core question: "What does the codebase look like *after*?"

Includes reference materials from Rich Hickey, Casey Muratori, and others on simplicity vs. ease, taking things apart, and knowing what's expensive to add later. Loads at least one mindset before starting.

### researching-codebases

Coordinate parallel sub-agents to answer complex codebase questions that span multiple files or require tracing through code.

Includes:

- Agent definitions for code-locator, code-analyzer, code-pattern-finder, and web-searcher
- Scripts for persisting research to `.research/` or `~/.research/`, plus searching and promoting past findings
- Workflow for decomposing questions, spawning agents in parallel, and synthesizing results

Requires installing the agent definitions to your CLI tool—see the [agents README](skills/researching-codebases/agents/README.md) for details.

### writing-clearly-and-concisely

Strunk's rules for clear prose, plus patterns to avoid in AI-generated writing. Use whenever you're writing text humans will read—documentation, commit messages, error messages, explanations.

Includes the full *Elements of Style* (1918) split into sections:

- Elementary rules of usage (grammar, punctuation)
- Elementary principles of composition (active voice, omit needless words)
- Matters of form (headings, quotations)
- Words and expressions commonly misused

Most tasks only need the composition section (~4.5k tokens). Also includes a guide to AI writing patterns that Wikipedia editors developed to detect generated submissions.

## Installation

Manual for now—copy the skills you want to the appropriate location. Automated installation coming eventually.

### Claude Code

Skills go in `~/.claude/skills/` or `.claude/skills/` in your project.

```bash
cp -r skills/reducing-entropy ~/.claude/skills/
```

### OpenCode

OpenCode requires a plugin to load skills. Options:

- [opencode-agent-skills](https://github.com/joshuadavidthomas/opencode-agent-skills) — provides tools for using skills
- [opencode-skills](https://github.com/malhashemi/opencode-skills) — popular community plugin

Both plugins read from `~/.config/opencode/skills/` or `.opencode/skills/` in your project.

```bash
cp -r skills/reducing-entropy ~/.config/opencode/skills/
```

## Usage

Skills are model-invoked—the agent decides when to use them based on your request and the skill's description. You can also explicitly ask for a skill:

> Use the reducing-entropy skill to review this refactor

or reference it by name when relevant to your task.

## Related

- [Agent Skills Documentation][agent-skills-docs]
- [OpenCode Plugins Documentation](https://opencode.ai/docs/plugins)

## License

MIT

[agent-skills-docs]: https://docs.anthropic.com/en/docs/claude-code/skills
