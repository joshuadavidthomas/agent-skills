# agent-skills

A collection of Agent Skills for AI coding assistants, following the [Anthropic Agent Skills specification][agent-skills-docs].

## Available Skills

### crafting-effective-readmes

Guides you through writing READMEs matched to your audience and project type. Different audiences need different information—a contributor to an OSS project needs different context than future-you opening a config folder.

Uses a structured process to identify task type (creating, adding, updating, or reviewing) and ask relevant questions before drafting.

Includes:

- Templates for open source, personal, internal, and config projects
- Section checklist showing which sections matter for each project type
- Style guide covering common mistakes
- Reference materials: Standard README spec (with examples), "Art of README", and Make a README guide

### improving-prompts

Apply Anthropic's documented Claude 4.5 best practices to CLAUDE.md, AGENTS.md, custom commands, and skill files. Uses actual guidance from Anthropic instead of inventing improvements.

The key constraint: don't change anything until you understand what specific behavior is failing. Provides a quick reference table mapping common issues to fixes, plus defensive tables of rationalizations and red flags to prevent agents from bypassing the requirement for concrete issues.

### reducing-entropy

Helps you evaluate designs, review code, and refactor with a bias toward deletion. The core question: "What does the codebase look like *after*?"

Uses a "Three Questions" framework: What's the smallest codebase that solves this? Does the change result in less total code? What can we delete?

Includes "mindsets" with references of ideas and writings from Rich Hickey (simplicity vs. ease), Simon Willison (PAGNI—what's expensive to add later), and data-oriented design principles. Loads at least one mindset before starting.

### researching-codebases

Coordinate parallel sub-agents to answer complex codebase questions that span multiple files or require tracing through code. Supports checking existing research before starting new investigations.

Includes:

- Agent definitions for code-locator (fast/cheap), code-analyzer (thorough), code-pattern-finder, and web-searcher
- Agent selection guide with cost/performance tradeoffs
- Scripts for managing research memory in `.research/` or `~/.research/`: list, search, read, promote
- Output format specification for research documents

> [!NOTE]
> Requires installing the agent definitions to your CLI tool—see the [agents README](skills/researching-codebases/agents/README.md) for details.

### writing-clearly-and-concisely

Strunk's rules for clear prose, plus patterns to avoid in AI-generated writing. Use whenever you're writing text humans will read—documentation, commit messages, error messages, explanations, UI copy.

Includes the full *Elements of Style* (1918) split into loadable sections covering grammar, composition, form, and word choice.

Also includes a comprehensive guide to AI writing patterns Wikipedia editors developed to detect generated submissions—covering puffery (*pivotal*, *testament*), overused vocabulary (*delve*, *leverage*, *multifaceted*), and formatting tells.

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

## Acknowledgements

This collection includes and adapts work from several sources:

### crafting-effective-readmes

Reference materials include:

- [Art of README](https://github.com/hackergrrl/art-of-readme) by Kira (CC BY 2.0)
- [Standard README](https://github.com/RichardLitt/standard-readme) by Richard Littauer (MIT)
- [Make a README](https://github.com/dguo/make-a-readme) by Danny Guo (MIT)

### improving-prompts

Includes best practices from [Anthropic's Claude documentation](https://docs.anthropic.com).

### reducing-entropy

Reference mindsets summarize and cite works by Rich Hickey, Simon Willison, Luke Plant, Jacob Kaplan-Moss, and others. See individual reference files for source links.

### researching-codebases

Adapted from the [commands and agents](https://github.com/humanlayer/humanlayer/tree/main/.claude) in HumanLayer (Apache 2.0).

### writing-clearly-and-concisely

Adapted from [obra/the-elements-of-style](https://github.com/obra/the-elements-of-style). The 1918 *Elements of Style* text is in the public domain via [Project Gutenberg](https://www.gutenberg.org/files/37134/37134-h/37134-h.htm). The AI writing patterns guide is adapted from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).

## License

Licensed under the MIT license. See the [`LICENSE`](LICENSE) file for more information.

[agent-skills-docs]: https://docs.anthropic.com/en/docs/claude-code/skills
