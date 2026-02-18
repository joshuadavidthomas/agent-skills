# agent-skills

A collection of skills for agentic LLM tools, following the [Agent Skills specification](https://agentskills.io/specification).

## Installation

### Claude Code

Clone the repo directly to your skills directory:

```bash
git clone https://github.com/joshuadavidthomas/agent-skills.git ~/.claude/skills
```

Or for project-level skills:

```bash
git clone https://github.com/joshuadavidthomas/agent-skills.git .claude/skills
```

### OpenCode

OpenCode v1.0.190+ has native skill loading built in.

- `opencode-skills` is deprecated and no longer needed.
- [`opencode-agent-skills`](https://github.com/joshuadavidthomas/opencode-agent-skills) is still available, but optional, and mainly useful if you want its specific loading behavior.

Install by cloning this repo, then symlink the skills you want:

```bash
git clone https://github.com/joshuadavidthomas/agent-skills.git
cd agent-skills
mkdir -p ~/.config/opencode/skills
ln -s "$PWD/reducing-entropy" ~/.config/opencode/skills/reducing-entropy
```

OpenCode also discovers skills from `.opencode/skills`, `.claude/skills`, and `.agents/skills` in your project.

## Usage

Skills are model-invoked—the agent decides when to use them based on your request and the skill's description. You can also explicitly ask for a skill:

> Use the reducing-entropy skill to review this refactor

or reference it by name when relevant to your task.

## Skills

### [coolify-compose](./coolify-compose/)

Convert Docker Compose files to Coolify templates for both raw-compose and repository deployment modes. Covers Coolify magic variables (`SERVICE_URL_*`, `SERVICE_PASSWORD_*`), health checks, and common conversion/troubleshooting patterns.

### [crafting-effective-readmes](./crafting-effective-readmes/)

Guides you through writing READMEs matched to your audience and project type. Different audiences need different information—a contributor to an OSS project needs different context than future-you opening a config folder.

Uses a structured process to identify task type (creating, adding, updating, or reviewing) and ask relevant questions before drafting.

Includes:

- Templates for open source, personal, internal, and config projects
- Section checklist showing which sections matter for each project type
- Style guide covering common mistakes
- Reference materials: Standard README spec (with examples), "Art of README", and Make a README guide

### [diataxis](./diataxis/)

Apply the Diátaxis framework for documentation structure and writing. Helps classify and produce tutorials, how-to guides, reference, and explanation docs.

### [frontend-design-principles](./frontend-design-principles/)

Design-focused frontend skill for producing intentional, non-generic interfaces. Includes required discovery gates, signature-definition workflow, and self-review checks before presenting UI output.

### [improving-prompts](./improving-prompts/)

Apply Anthropic's documented Claude 4.5 best practices to CLAUDE.md, AGENTS.md, custom commands, and skill files. Uses actual guidance from Anthropic instead of inventing improvements.

The key constraint: don't change anything until you understand what specific behavior is failing. Provides a quick reference table mapping common issues to fixes, plus defensive tables of rationalizations and red flags to prevent agents from bypassing the requirement for concrete issues.

### [reducing-entropy](./reducing-entropy/)

Helps you evaluate designs, review code, and refactor with a bias toward deletion. The core question: "What does the codebase look like *after*?"

Uses a "Three Questions" framework: What's the smallest codebase that solves this? Does the change result in less total code? What can we delete?

Includes "mindsets" with references of ideas and writings from Rich Hickey (simplicity vs. ease), Simon Willison (PAGNI—what's expensive to add later), and data-oriented design principles. Loads at least one mindset before starting.

### [researching-codebases](./researching-codebases/)

Coordinate parallel sub-agents to answer complex codebase questions that span multiple files or require tracing through code. Supports checking existing research before starting new investigations.

Includes:

- Agent definitions for code-locator (fast/cheap), code-analyzer (thorough), code-pattern-finder, and web-searcher
- Agent selection guide with cost/performance tradeoffs
- Scripts for managing research memory in `.research/` or `~/.research/`: list, search, read, promote
- Output format specification for research documents

> [!NOTE]
> Requires installing agent definitions to your CLI tool. If you're using OpenCode native skills, install these separately (or use `opencode-agent-skills` if you prefer plugin-based loading). See the [agents README](researching-codebases/agents/README.md).

### [skill-authoring](./skill-authoring/)

Create and refine agent skills. Covers SKILL.md structure, high-signal descriptions, trigger design, progressive disclosure, and activation/testing practices.

### [svelte5](./svelte5/)

Svelte 5 guidance covering runes (`$state`, `$derived`, `$effect`, `$props`, `$bindable`), class-based state patterns, context API usage, and Svelte 4→5 migration defaults.

### [sveltekit](./sveltekit/)

SvelteKit routing, layouts, data loading, actions, authentication patterns, form validation, and remote functions (`command()`, `query()`, `form()`).

### [writing-clearly-and-concisely](./writing-clearly-and-concisely/)

Strunk's rules for clear prose, plus patterns to avoid in AI-generated writing. Use whenever you're writing text humans will read—documentation, commit messages, error messages, explanations, UI copy.

Includes the full *Elements of Style* (1918) split into loadable sections covering grammar, composition, form, and word choice.

Also includes a comprehensive guide to AI writing patterns Wikipedia editors developed to detect generated submissions—covering puffery (*pivotal*, *testament*), overused vocabulary (*delve*, *leverage*, *multifaceted*), and formatting tells.

### [writing-cli-skills](./writing-cli-skills/)

Guide for building high-quality skills around CLI tools. Emphasizes hands-on tool usage, practical command organization, progressive disclosure, and review checklists.

## Acknowledgements

This collection includes and adapts work from several sources.

### crafting-effective-readmes

Reference materials include:

- [Art of README](https://github.com/hackergrrl/art-of-readme) by Kira (CC BY 2.0)
- [Standard README](https://github.com/RichardLitt/standard-readme) by Richard Littauer (MIT)
- [Make a README](https://github.com/dguo/make-a-readme) by Danny Guo (MIT)

### diataxis

Reference content derived from the [Diátaxis documentation framework](https://diataxis.fr/) ([repo](https://github.com/evildmp/diataxis-documentation-framework)) by [Daniele Procida](https://vurt.eu) ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).

### frontend-design-principles

Adapted from:

- The [frontend-design](https://github.com/anthropics/skills/tree/main/frontend-design) skill in [anthropics/skills](https://github.com/anthropics/skills) (Apache 2.0)
- [Dammyjay93/interface-design](https://github.com/Dammyjay93/interface-design) (MIT, Damola Akinleye)
- [Teaching Claude to Design Better: Improving Anthropic's Frontend Design Skill](https://www.justinwetch.com/blog/improvingclaudefrontend) ([relevant PR](https://github.com/anthropics/skills/pull/210)) by Justin Wetch

### improving-prompts

Includes best practices from [Anthropic's Claude documentation](https://docs.anthropic.com).

### reducing-entropy

Reference mindsets summarize and cite works by Rich Hickey, Simon Willison, Luke Plant, Jacob Kaplan-Moss, and others. See individual reference files for source links.

### researching-codebases

Adapted from the [commands and agents](https://github.com/humanlayer/humanlayer/tree/main/.claude) in HumanLayer (Apache 2.0).

### skill-authoring

Includes best practices from Anthropic's Claude and Agent Skills documentation.

### svelte5 and sveltekit

Reference and guidance adapted from:

- [svelte-claude-skills](https://github.com/spences10/svelte-claude-skills) by Scott Spence (MIT)
- [Svelte documentation](https://svelte.dev/docs) (MIT)
- [Modern SvelteKit Tutorial](https://github.com/stolinski/Modern-Svelte-Kit-Tutorial) by Scott Tolinski
- [Svelte Stores Streams Effect](https://github.com/bmdavis419/Svelte-Stores-Streams-Effect) by Ben Davis ([video](https://www.youtube.com/watch?v=kMBDsyozllk))


### writing-clearly-and-concisely

Adapted from [obra/the-elements-of-style](https://github.com/obra/the-elements-of-style). The 1918 *Elements of Style* text is in the public domain via [Project Gutenberg](https://www.gutenberg.org/files/37134/37134-h/37134-h.htm). The AI writing patterns guide is adapted from Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)).

## License

Licensed under the MIT license. See the [`LICENSE`](LICENSE) file for more information.
